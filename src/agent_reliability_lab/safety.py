"""Safety guardrails for goals, tool calls, and retrieved observations."""

from __future__ import annotations

from .models import PlannedAction


class SafetyGuard:
    """Simple deterministic guard that blocks unsafe local behavior."""

    harmful_terms = {
        "delete production",
        "hide it",
        "exfiltrate",
        "steal",
        "credential",
        "credentials",
        "secret",
        "secrets",
        "disable logging",
        "bypass approval",
    }
    injection_terms = {
        "ignore previous instructions",
        "ignore prior instructions",
        "developer message",
        "unsafe_shell",
        "system prompt",
        "reveal credentials",
    }
    unsafe_tools = {
        "unsafe_shell",
        "network_request",
        "delete_file",
        "write_file",
        "read_secret",
    }

    def screen_goal(self, goal: str) -> tuple[bool, str]:
        lowered = goal.lower()
        for term in sorted(self.harmful_terms):
            if term in lowered:
                return False, f"Goal contains blocked harmful intent: {term}"
        return True, "Goal passed deterministic safety screen"

    def validate_action(self, action: PlannedAction) -> tuple[bool, str]:
        if action.tool_name in self.unsafe_tools:
            return False, f"Tool is outside the allow-list: {action.tool_name}"
        payload = f"{action.tool_name} {action.args}".lower()
        for term in sorted(self.harmful_terms | self.injection_terms):
            if term in payload:
                return False, f"Tool arguments contain blocked content: {term}"
        return True, "Tool call passed safety validation"

    def inspect_observation(self, text: str) -> tuple[bool, str]:
        lowered = text.lower()
        for term in sorted(self.injection_terms):
            if term in lowered:
                return False, f"Retrieved content contains prompt-injection marker: {term}"
        return True, "Observation passed prompt-injection inspection"
