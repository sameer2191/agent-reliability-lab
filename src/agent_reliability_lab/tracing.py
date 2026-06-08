"""Structured JSONL tracing for deterministic local runs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    allowed = []
    for char in value.lower():
        if char.isalnum():
            allowed.append(char)
        elif char in {" ", "-", "_"}:
            allowed.append("_")
    slug = "".join(allowed).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "scenario"


class TraceRecorder:
    """Append-only trace writer with simple structured events."""

    def __init__(self, trace_dir: Path, scenario_name: str) -> None:
        trace_dir.mkdir(parents=True, exist_ok=True)
        self.scenario_name = scenario_name
        self.path = trace_dir / f"{slugify(scenario_name)}.jsonl"
        self._counter = 0
        self.path.write_text("", encoding="utf-8")

    def record(
        self,
        actor: str,
        event_type: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        self._counter += 1
        event = {
            "event_id": self._counter,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scenario": self.scenario_name,
            "actor": actor,
            "event_type": event_type,
            "message": message,
            "data": data or {},
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def load_trace(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                events.append(json.loads(line))
    return events
