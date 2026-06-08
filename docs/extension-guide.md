# Extension Guide

The runnable core should remain offline, deterministic, and standard-library only. Extensions can be added around it without weakening the regression baseline.

## Add a Scenario

1. Add a `TaskScenario` in `src/agent_reliability_lab/evals.py`.
2. Add planner behavior in `PlannerAgent.plan` if the scenario needs a new path.
3. Add or update tests in `tests/`.
4. Run:

```bash
python -m agent_reliability_lab demo --output runs/demo
python -m unittest discover -s tests
```

## Add a Tool

1. Implement a pure Python handler in `tools.py`.
2. Register it in `create_default_registry`.
3. Assign a realistic `cost_tokens` estimate.
4. Decide whether it is retryable.
5. Add safety coverage if the tool introduces new risk.

Tools should be deterministic and should not call network services in the default demo.

## Add a Real LLM Adapter

Keep the current deterministic suite as the CI baseline. If adding a provider-backed planner:

- Put provider code behind an interface.
- Keep secrets out of the repo.
- Make network tests opt-in.
- Preserve local deterministic tests.
- Compare provider behavior against the same scenario contract.

## LangGraph or LangChain Mapping

The current components map cleanly to graph nodes:

- planner node: `PlannerAgent`
- safety node: `SafetyGuard`
- budget node: `BudgetGuard`
- executor node: `ExecutorAgent`
- critic node: `CriticAgent`
- observer node: `TraceRecorder`

The deterministic harness can remain the regression suite while real graph execution becomes an integration layer.
