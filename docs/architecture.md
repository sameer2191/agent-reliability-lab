# Architecture

Agent Reliability Lab is organized around a deterministic agent loop. It is not a chatbot and does not call an LLM. The point is to make reliability behavior easy to test, replay, and explain.

## Components

| Component | File | Responsibility |
| --- | --- | --- |
| `TaskScenario` | `src/agent_reliability_lab/models.py` | Defines a regression fixture, expected outcome, budget, and tags |
| `PlannerAgent` | `src/agent_reliability_lab/agents.py` | Chooses the next action using deterministic rules |
| `SafetyGuard` | `src/agent_reliability_lab/safety.py` | Screens goals, tool calls, and retrieved observations |
| `BudgetGuard` | `src/agent_reliability_lab/budget.py` | Estimates token spend and blocks projected over-budget work |
| `ExecutorAgent` | `src/agent_reliability_lab/agents.py` | Runs safe, budget-approved tools with retry policy |
| `ToolRegistry` | `src/agent_reliability_lab/tools.py` | Provides an allow-list of local standard-library tools |
| `CriticAgent` | `src/agent_reliability_lab/agents.py` | Reviews observations and updates memory/state |
| `TraceRecorder` | `src/agent_reliability_lab/tracing.py` | Writes structured JSONL events for every major decision |
| `EvaluationHarness` | `src/agent_reliability_lab/evals.py` | Runs scenarios, computes metrics, and generates artifacts |

## Control Flow

1. The scenario enters the loop with a goal, expected outcome, and budget.
2. The safety guard screens the goal before planning.
3. The planner emits a structured `PlannedAction`.
4. Tool actions pass through the action safety guard.
5. The budget guard estimates and approves or blocks the work.
6. The executor calls a registered local tool and applies retry policy when eligible.
7. The critic inspects observations for prompt-injection markers and updates state.
8. The loop stops on completion, blocked unsafe action, HITL boundary, budget block, failed tool, or max-step exhaustion.

## Why Deterministic

Production teams need agent tests that can run in CI without waiting on provider availability, rate limits, model drift, or secrets. This project keeps the core deterministic so it can act as a stable regression baseline before adding real LLM adapters.
