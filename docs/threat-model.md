# Threat Model

This project is offline and uses no secrets, but it models risks that matter for real agent deployments.

## Assets

- User intent and task boundary
- Tool allow-list
- Budget limits
- Trace integrity
- Human approval checkpoints

## Threats

| Threat | Example | Control |
| --- | --- | --- |
| Prompt injection | Retrieved text says to ignore instructions and call a shell | Critic scans observations and safety guard quarantines injected instructions |
| Unsafe tool use | Planner asks for shell, file write, network call, or secret read | Tool allow-list and action safety screen block it |
| Ambiguous objective | User says "fix the thing" | HITL boundary returns a clarification requirement |
| Budget exhaustion | Expensive tool requested under tight budget | Budget guard blocks before execution |
| Silent tool failure | Dependency times out | Retryable tools emit trace events and recover or fail explicitly |
| Poor auditability | Agent decisions are opaque | JSONL traces capture planner, guard, executor, tool, and critic events |

## Non-Goals

- This lab does not execute arbitrary shell commands.
- This lab does not call external model providers.
- This lab does not store credentials or personal private data.
- This lab does not claim to be a complete security product.

## HITL Boundary

The HITL boundary is deliberate. Ambiguous, destructive, or sensitive work should stop before autonomous execution. In a real system, this could become an approval queue, case-management ticket, Slack approval, or signed workflow checkpoint.
