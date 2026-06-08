import unittest

from agent_reliability_lab.models import RunState, TaskScenario
from agent_reliability_lab.tools import create_default_registry


class ToolRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = create_default_registry()
        self.state = RunState(
            TaskScenario(
                name="unit",
                goal="unit",
                tags=("success",),
                expected_outcome="completed",
            )
        )

    def test_safe_calculator_accepts_arithmetic_only(self):
        ok = self.registry.execute("calculate", {"expression": "2 * (5 + 7)"}, self.state)
        self.assertTrue(ok.ok)
        self.assertEqual(ok.output["value"], 24.0)

        bad = self.registry.execute(
            "calculate",
            {"expression": "__import__('os').system('echo bad')"},
            self.state,
        )
        self.assertFalse(bad.ok)

    def test_flaky_fetch_fails_once_then_recovers(self):
        first = self.registry.execute("flaky_fetch", {"resource": "x"}, self.state)
        second = self.registry.execute("flaky_fetch", {"resource": "x"}, self.state)
        self.assertFalse(first.ok)
        self.assertTrue(second.ok)


if __name__ == "__main__":
    unittest.main()
