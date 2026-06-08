"""Command-line interface for the reliability lab."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .evals import EvaluationHarness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent_reliability_lab",
        description="Run deterministic local multi-agent reliability scenarios.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser(
        "demo",
        help="Run built-in scenarios and generate scorecard plus trace viewer.",
    )
    demo.add_argument(
        "--output",
        default="runs/demo",
        help="Output directory for scorecard, JSONL traces, and HTML viewer.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "demo":
        output_dir = Path(args.output)
        summary = EvaluationHarness().run(output_dir)
        metrics = summary["metrics"]
        print("Agent Reliability Lab demo complete")
        print(f"Output directory: {output_dir}")
        print(f"Scorecard: {output_dir / 'scorecard.json'}")
        print(f"Trace viewer: {output_dir / 'trace_viewer.html'}")
        print("Metrics:")
        for key in sorted(metrics):
            print(f"  {key}: {metrics[key]}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
