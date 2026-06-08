import tempfile
import unittest
from pathlib import Path

from agent_reliability_lab.evals import EvaluationHarness


class EvaluationHarnessTests(unittest.TestCase):
    def test_demo_harness_generates_scorecard_and_traces(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "demo"
            summary = EvaluationHarness().run(output)

            self.assertEqual(summary["scenario_count"], 6)
            self.assertEqual(summary["metrics"]["passed_scenarios"], 6)
            self.assertEqual(summary["metrics"]["task_completion_rate"], 1.0)
            self.assertEqual(summary["metrics"]["unsafe_action_block_rate"], 1.0)
            self.assertEqual(summary["metrics"]["retry_recovery_rate"], 1.0)
            self.assertEqual(summary["metrics"]["budget_overrun_rate"], 0.0)
            self.assertTrue((output / "scorecard.json").exists())
            self.assertTrue((output / "trace_viewer.html").exists())
            self.assertEqual(len(list((output / "traces").glob("*.jsonl"))), 6)

    def test_budget_pressure_is_blocked_not_overrun(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = EvaluationHarness().run(Path(tmp))
            budget_case = next(
                item
                for item in summary["results"]
                if item["name"] == "budget_pressure_guarded"
            )
            self.assertEqual(budget_case["status"], "budget_blocked")
            self.assertEqual(budget_case["budget_overruns"], 0)
            self.assertGreaterEqual(budget_case["budget_denials"], 1)


if __name__ == "__main__":
    unittest.main()
