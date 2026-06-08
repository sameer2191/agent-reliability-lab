"""Planner, executor, critic, and deterministic orchestration loop."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .budget import BudgetGuard, summarize_budget
from .models import PlannedAction, RunState, TaskScenario, ToolResult
from .safety import SafetyGuard
from .tools import ToolRegistry, create_default_registry
from .tracing import TraceRecorder


class PlannerAgent:
    """Rule-based planner used for reproducible regression scenarios."""

    def plan(self, state: RunState) -> PlannedAction:
        tags = set(state.scenario.tags)

        if "ambiguous" in tags:
            return PlannedAction(
                "hitl",
                "Goal lacks enough acceptance criteria for safe autonomous work.",
            )

        if "harmful" in tags:
            return PlannedAction(
                "tool",
                "The user requested destructive work; emit an unsafe action to prove the gate blocks it.",
                "unsafe_shell",
                {"command": "delete production logs and disable logging"},
            )

        if "budget_pressure" in tags:
            return PlannedAction(
                "tool",
                "The scenario intentionally requests high-cost analysis under a tight budget.",
                "expensive_analysis",
                {"input": "run full corpus analysis"},
            )

        if "tool_failure" in tags:
            if "flaky_fetch" not in state.completed_tools:
                return PlannedAction(
                    "tool",
                    "Fetch a local fixture that deterministically fails once.",
                    "flaky_fetch",
                    {"resource": "flaky-service"},
                )
            if "make_summary" not in state.completed_tools:
                return PlannedAction(
                    "tool",
                    "Summarize the recovered tool observation.",
                    "make_summary",
                    {"text": state.last_output_text()},
                )
            return PlannedAction(
                "final",
                "Transient tool failure recovered by retry policy.",
                args={"status": "completed", "message": "Recovered after retry and summarized fixture."},
            )

        if "prompt_injection" in tags:
            if "lookup_policy" not in state.completed_tools:
                return PlannedAction(
                    "tool",
                    "Retrieve the release note fixture and inspect it before trusting content.",
                    "lookup_policy",
                    {"query": "release_note_malicious"},
                )
            if "redact_pii" not in state.completed_tools:
                return PlannedAction(
                    "tool",
                    "Quarantine untrusted instruction text and pass only sanitized content forward.",
                    "redact_pii",
                    {"text": state.memory.get("sanitized_observation", state.last_output_text())},
                )
            if "make_summary" not in state.completed_tools:
                return PlannedAction(
                    "tool",
                    "Summarize the trusted portion of the release note.",
                    "make_summary",
                    {"text": state.last_output_text()},
                )
            return PlannedAction(
                "final",
                "Prompt injection marker was blocked and the safe task still completed.",
                args={
                    "status": "completed_with_guard",
                    "message": "Completed release-note review after quarantining untrusted instructions.",
                },
            )

        if "lookup_policy" not in state.completed_tools:
            return PlannedAction(
                "tool",
                "Load the deployment runbook from the local policy store.",
                "lookup_policy",
                {"query": "deployment"},
            )
        if "word_count" not in state.completed_tools:
            return PlannedAction(
                "tool",
                "Measure the runbook text to create a traceable intermediate signal.",
                "word_count",
                {"text": state.last_output_text()},
            )
        if "calculate" not in state.completed_tools:
            return PlannedAction(
                "tool",
                "Compute a deterministic readiness score component.",
                "calculate",
                {"expression": "40 + 2"},
            )
        if "make_summary" not in state.completed_tools:
            return PlannedAction(
                "tool",
                "Summarize the deployment runbook for final response.",
                "make_summary",
                {"text": state.memory.get("deployment_doc", state.last_output_text())},
            )
        return PlannedAction(
            "final",
            "All success-path checks completed.",
            args={"status": "completed", "message": "Deployment readiness summary completed."},
        )


class ExecutorAgent:
    """Executes planner actions through safety, budget, and retry gates."""

    def __init__(
        self,
        registry: ToolRegistry,
        safety_guard: SafetyGuard,
        budget_guard: BudgetGuard,
        max_attempts: int = 2,
    ) -> None:
        self.registry = registry
        self.safety_guard = safety_guard
        self.budget_guard = budget_guard
        self.max_attempts = max_attempts

    def execute(
        self,
        action: PlannedAction,
        state: RunState,
        trace: TraceRecorder,
    ) -> ToolResult:
        if action.action_type == "hitl":
            state.status = "hitl_required"
            state.hitl_required = True
            state.final_message = "Human approval required: goal is ambiguous."
            trace.record(
                "executor",
                "hitl_boundary",
                state.final_message,
                {"reason": action.reason},
            )
            return ToolResult(True, output=state.final_message)

        if action.action_type == "final":
            state.status = str(action.args.get("status", "completed"))
            state.final_message = str(action.args.get("message", action.reason))
            trace.record(
                "executor",
                "final",
                state.final_message,
                {"status": state.status},
            )
            return ToolResult(True, output=state.final_message)

        if action.action_type != "tool":
            state.status = "failed_planner"
            state.final_message = f"Unsupported action type: {action.action_type}"
            return ToolResult(False, error=state.final_message)

        safe, safety_reason = self.safety_guard.validate_action(action)
        trace.record(
            "safety_guard",
            "action_screen",
            safety_reason,
            {"tool_name": action.tool_name, "safe": safe},
        )
        if not safe:
            state.unsafe_attempts += 1
            state.unsafe_blocks += 1
            state.blocked_actions += 1
            state.status = "blocked_unsafe"
            state.final_message = safety_reason
            return ToolResult(False, error=safety_reason)

        tool = self.registry.get(action.tool_name)
        if tool is None:
            state.blocked_actions += 1
            state.status = "blocked_unregistered_tool"
            state.final_message = f"Tool not registered: {action.tool_name}"
            trace.record(
                "tool_registry",
                "tool_missing",
                state.final_message,
                {"tool_name": action.tool_name},
            )
            return ToolResult(False, error=state.final_message)

        can_spend, tokens, budget_reason = self.budget_guard.can_spend(state, action, tool)
        trace.record(
            "budget_guard",
            "budget_check",
            budget_reason,
            {
                "tool_name": action.tool_name,
                "estimated_tokens": tokens,
                "state": summarize_budget(state),
                "allowed": can_spend,
            },
        )
        if not can_spend:
            state.budget_denials += 1
            state.blocked_actions += 1
            state.status = "budget_blocked"
            state.final_message = budget_reason
            return ToolResult(False, error=budget_reason)

        attempt = 0
        while attempt < self.max_attempts:
            attempt += 1
            self.budget_guard.commit(state, tokens)
            trace.record(
                "executor",
                "tool_call",
                f"Calling {action.tool_name} attempt {attempt}",
                {
                    "args": action.args,
                    "attempt": attempt,
                    "budget": summarize_budget(state),
                },
            )
            result = self.registry.execute(action.tool_name, action.args, state)
            trace.record(
                "tool",
                "tool_result",
                "Tool returned success" if result.ok else "Tool returned failure",
                {
                    "tool_name": action.tool_name,
                    "attempt": attempt,
                    "ok": result.ok,
                    "output": result.output,
                    "error": result.error,
                    "metadata": result.metadata,
                },
            )
            if result.ok:
                if attempt > 1:
                    state.retry_recoveries += 1
                state.completed_tools.append(action.tool_name)
                state.remember_observation(action.tool_name, result.output)
                return result

            if not tool.retryable or attempt >= self.max_attempts:
                state.status = "failed_tool"
                state.final_message = result.error
                return result

            state.retry_attempts += 1
            trace.record(
                "executor",
                "retry_scheduled",
                f"Retrying {action.tool_name} after deterministic transient failure",
                {"tool_name": action.tool_name, "attempt": attempt + 1},
            )

        state.status = "failed_tool"
        state.final_message = f"Retries exhausted for {action.tool_name}"
        return ToolResult(False, error=state.final_message)


class CriticAgent:
    """Reviews observations and updates memory before the next plan step."""

    def __init__(self, safety_guard: SafetyGuard) -> None:
        self.safety_guard = safety_guard

    def review(
        self,
        action: PlannedAction,
        result: ToolResult,
        state: RunState,
        trace: TraceRecorder,
    ) -> None:
        if action.action_type != "tool" or not result.ok:
            return

        if action.tool_name == "lookup_policy" and action.args.get("query") == "deployment":
            state.memory["deployment_doc"] = result.output

        if isinstance(result.output, str):
            safe, reason = self.safety_guard.inspect_observation(result.output)
            trace.record(
                "critic",
                "observation_review",
                reason,
                {"safe": safe, "tool_name": action.tool_name},
            )
            if not safe:
                state.memory["prompt_injection_detected"] = True
                state.memory["sanitized_observation"] = self._sanitize_untrusted_text(result.output)
                state.unsafe_attempts += 1
                state.unsafe_blocks += 1
                state.blocked_actions += 1
                trace.record(
                    "safety_guard",
                    "prompt_injection_blocked",
                    "Untrusted retrieved instruction was quarantined before planning.",
                    {"source_tool": action.tool_name},
                )
        else:
            trace.record(
                "critic",
                "observation_review",
                "Structured tool output accepted.",
                {"tool_name": action.tool_name},
            )

    @staticmethod
    def _sanitize_untrusted_text(text: str) -> str:
        marker = "UNTRUSTED COMMENT:"
        if marker in text:
            return text.split(marker, 1)[0].strip()
        return text


class AgentLoop:
    """Coordinates the local multi-agent reliability loop."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        planner: PlannerAgent | None = None,
        safety_guard: SafetyGuard | None = None,
        budget_guard: BudgetGuard | None = None,
    ) -> None:
        self.registry = registry or create_default_registry()
        self.planner = planner or PlannerAgent()
        self.safety_guard = safety_guard or SafetyGuard()
        self.budget_guard = budget_guard or BudgetGuard()
        self.executor = ExecutorAgent(self.registry, self.safety_guard, self.budget_guard)
        self.critic = CriticAgent(self.safety_guard)

    def run(self, scenario: TaskScenario, trace_dir: Path) -> dict[str, Any]:
        state = RunState(scenario=scenario)
        trace = TraceRecorder(trace_dir, scenario.name)
        trace.record(
            "system",
            "scenario_start",
            "Scenario started",
            {"scenario": asdict(scenario), "tools": self.registry.list_tools()},
        )

        goal_safe, goal_reason = self.safety_guard.screen_goal(scenario.goal)
        trace.record(
            "safety_guard",
            "goal_screen",
            goal_reason,
            {"safe": goal_safe},
        )
        if not goal_safe:
            state.unsafe_attempts += 1
            state.unsafe_blocks += 1
            state.blocked_actions += 1
            state.status = "blocked_unsafe"
            state.final_message = goal_reason
        else:
            while state.status == "running" and state.steps < scenario.max_steps:
                state.steps += 1
                action = self.planner.plan(state)
                trace.record(
                    "planner",
                    "planned_action",
                    action.reason,
                    {
                        "step": state.steps,
                        "action_type": action.action_type,
                        "tool_name": action.tool_name,
                        "args": action.args,
                    },
                )
                result = self.executor.execute(action, state, trace)
                self.critic.review(action, result, state, trace)

            if state.status == "running":
                state.status = "max_steps_exceeded"
                state.final_message = "Planner did not reach a terminal state."

        trace.record(
            "system",
            "scenario_end",
            state.final_message or state.status,
            {
                "status": state.status,
                "steps": state.steps,
                "budget": summarize_budget(state),
                "unsafe_attempts": state.unsafe_attempts,
                "unsafe_blocks": state.unsafe_blocks,
                "retry_attempts": state.retry_attempts,
                "retry_recoveries": state.retry_recoveries,
                "blocked_actions": state.blocked_actions,
            },
        )

        return {
            "name": scenario.name,
            "goal": scenario.goal,
            "tags": list(scenario.tags),
            "expected_outcome": scenario.expected_outcome,
            "status": state.status,
            "passed": state.status == scenario.expected_outcome,
            "steps": state.steps,
            "trace_path": str(trace.path),
            "final_message": state.final_message,
            "hitl_required": state.hitl_required,
            "blocked_actions": state.blocked_actions,
            "unsafe_attempts": state.unsafe_attempts,
            "unsafe_blocks": state.unsafe_blocks,
            "retry_attempts": state.retry_attempts,
            "retry_recoveries": state.retry_recoveries,
            "budget_denials": state.budget_denials,
            "budget_overruns": state.budget_overruns,
            "estimated_tokens": state.estimated_tokens,
            "estimated_token_cost": state.estimated_token_cost,
        }
