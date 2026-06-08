import tempfile
import unittest
from pathlib import Path

from agent_reliability_lab.cli import main


class CliTests(unittest.TestCase):
    def test_demo_command_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            code = main(["demo", "--output", str(output)])
            self.assertEqual(code, 0)
            self.assertTrue((output / "scorecard.json").exists())


if __name__ == "__main__":
    unittest.main()
