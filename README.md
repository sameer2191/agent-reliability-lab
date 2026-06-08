# Agent Reliability Lab

Agent Reliability Lab is a local, deterministic multi-agent testbed for agentic workflow reliability. It is designed as a public portfolio project for Sameeruddin Mir and targets AI Software Engineer, Agentic Workflows, and LLMOps roles.

The project intentionally uses only the Python standard library for the runnable core. No network calls, paid API keys, model providers, or external services are required for the demo or tests.

## What It Demonstrates

- Deterministic planner, executor, critic, and safety-guard loop
- Safe tool registry with explicit allow-listing
- Budget guard with estimated token accounting
- Retry policy for transient tool failures
- HITL boundary for ambiguous goals
- Prompt-injection detection on retrieved content
- Structured JSONL traces and static HTML trace viewer
- Regression scenarios that produce a reliability scorecard

## Architecture

```text
TaskScenario
  -> SafetyGuard.goal_screen
  -> PlannerAgent
  -> SafetyGuard.action_screen
  -> BudgetGuard
  -> ExecutorAgent
  -> ToolRegistry
  -> CriticAgent
  -> TraceRecorder
  -> EvaluationHarness + Trace Viewer
```

The loop is deterministic by design. Scenarios are fixtures, the planner is rule-based, tools are local Python functions, and traces are structured JSONL files that can be reviewed in the generated HTML viewer.

## Quickstart

```bash
python -m agent_reliability_lab demo --output runs/demo
python -m unittest discover -s tests
```

The implementation package lives under `src/agent_reliability_lab/`. A tiny root compatibility package delegates to `src/` so the module command works from the repository root without an editable install.

## Demo Outputs

The demo creates:

- `runs/demo/scorecard.json`: scenario results, metrics, and artifact references
- `runs/demo/traces/*.jsonl`: append-only trace events for each scenario
- `runs/demo/trace_viewer.html`: static trace viewer that opens without a server

Example CLI output:

```text
Agent Reliability Lab demo complete
Output directory: runs/demo
Scorecard: runs/demo/scorecard.json
Trace viewer: runs/demo/trace_viewer.html
Metrics:
  average_steps: 2.33
  budget_guard_denials: 1
  budget_overrun_rate: 0.0
  estimated_token_cost: 0.001181
  passed_scenarios: 6
  retry_recovery_rate: 1.0
  task_completion_rate: 1.0
  unsafe_action_block_rate: 1.0
```

## Reliability Scorecard

The built-in evaluation harness reports these metrics:

| Metric | Meaning |
| --- | --- |
| `task_completion_rate` | Completion rate for scenarios that should be autonomously completed |
| `unsafe_action_block_rate` | Share of unsafe attempts blocked by safety gates |
| `retry_recovery_rate` | Share of retry scenarios that recovered from transient failure |
| `budget_overrun_rate` | Share of scenarios that actually exceeded budget |
| `average_steps` | Mean planner/executor steps per scenario |
| `estimated_token_cost` | Local proxy cost from deterministic token estimates |

Regression scenarios cover successful completion, retry recovery, prompt injection, ambiguous goals, harmful requests, and cost budget pressure.

## Why This Is Resume-Relevant

This repo maps directly to production agent reliability concerns:

- LLMOps evaluation harnesses and deterministic regression suites
- Structured traces for observability and debugging
- Tool-use safety gates and least-privilege registries
- Budget enforcement before execution
- Human-in-the-loop boundaries for unclear or sensitive work
- Prompt-injection defense on retrieved content

The implementation is intentionally small enough to review quickly while still showing production patterns that transfer to LangGraph, LangChain, OpenAI Agents SDK, or internal agent platforms.

## Trace Artifact References

After running the demo, inspect:

- `runs/demo/scorecard.json` for aggregate reliability metrics
- `runs/demo/traces/prompt_injection_defense.jsonl` for retrieved-content quarantine
- `runs/demo/traces/tool_failure_recovery.jsonl` for retry scheduling and recovery
- `runs/demo/traces/budget_pressure_guarded.jsonl` for budget denial before execution
- `runs/demo/trace_viewer.html` for a static browser-readable view

## Optional Integrations

The core is provider-free. Future integrations can wrap the deterministic agents with:

- LangGraph nodes for planner, executor, critic, and guard stages
- LangChain tool adapters around the safe registry
- OpenAI or other model providers behind an interface while keeping this deterministic suite as the regression baseline

See `docs/extension-guide.md` for extension boundaries.
