"""Deterministic token budget accounting."""

from __future__ import annotations

import json
from typing import Any

from .models import PlannedAction, RunState
from .tools import ToolDefinition


class BudgetGuard:
    """Prevents planned tool work from exceeding a scenario token budget."""

    token_cost_rate = 0.000001

    def estimate(self, action: PlannedAction, tool: ToolDefinition | None) -> int:
        payload = json.dumps(action.args, sort_keys=True)
        text_units = max(1, (len(action.reason) + len(payload)) // 4)
        tool_units = tool.cost_tokens if tool else 25
        return text_units + tool_units + 8

    def can_spend(
        self,
        state: RunState,
        action: PlannedAction,
        tool: ToolDefinition | None,
    ) -> tuple[bool, int, str]:
        estimate = self.estimate(action, tool)
        projected = state.estimated_tokens + estimate
        if projected > state.scenario.budget_tokens:
            return (
                False,
                estimate,
                f"Projected token use {projected} exceeds budget {state.scenario.budget_tokens}",
            )
        return True, estimate, "Budget check passed"

    def commit(self, state: RunState, tokens: int) -> None:
        state.estimated_tokens += tokens
        state.estimated_token_cost = round(
            state.estimated_token_cost + tokens * self.token_cost_rate,
            6,
        )
        if state.estimated_tokens > state.scenario.budget_tokens:
            state.budget_overruns += 1


def summarize_budget(state: RunState) -> dict[str, Any]:
    return {
        "budget_tokens": state.scenario.budget_tokens,
        "estimated_tokens": state.estimated_tokens,
        "estimated_token_cost": state.estimated_token_cost,
        "budget_denials": state.budget_denials,
        "budget_overruns": state.budget_overruns,
    }
