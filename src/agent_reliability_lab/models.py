"""Shared data models for the local agent lab."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TaskScenario:
    """A deterministic regression scenario for the agent loop."""

    name: str
    goal: str
    tags: tuple[str, ...]
    expected_outcome: str
    budget_tokens: int = 900
    max_steps: int = 8


@dataclass(frozen=True)
class PlannedAction:
    """A planner decision that the executor can evaluate."""

    action_type: str
    reason: str
    tool_name: str = ""
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """A safe tool execution result."""

    ok: bool
    output: Any = None
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunState:
    """Mutable state shared across planner, executor, critic, and guards."""

    scenario: TaskScenario
    memory: dict[str, Any] = field(default_factory=dict)
    observations: list[dict[str, Any]] = field(default_factory=list)
    completed_tools: list[str] = field(default_factory=list)
    blocked_actions: int = 0
    unsafe_attempts: int = 0
    unsafe_blocks: int = 0
    retry_attempts: int = 0
    retry_recoveries: int = 0
    budget_denials: int = 0
    budget_overruns: int = 0
    estimated_tokens: int = 0
    estimated_token_cost: float = 0.0
    steps: int = 0
    status: str = "running"
    final_message: str = ""
    hitl_required: bool = False

    def remember_observation(self, tool_name: str, output: Any) -> None:
        self.observations.append({"tool": tool_name, "output": output})
        self.memory["last_output"] = output

    def last_output_text(self) -> str:
        output = self.memory.get("last_output", "")
        if isinstance(output, str):
            return output
        return repr(output)
