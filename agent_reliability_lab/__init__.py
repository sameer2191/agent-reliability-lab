"""Compatibility package for running from a fresh clone.

The implementation package lives under src/agent_reliability_lab. This shim
extends the package search path so `python -m agent_reliability_lab` works from
the repository root without requiring an editable install.
"""

from pathlib import Path


_SRC_PACKAGE = Path(__file__).resolve().parents[1] / "src" / "agent_reliability_lab"
if _SRC_PACKAGE.exists():
    __path__.insert(0, str(_SRC_PACKAGE))  # type: ignore[name-defined]

__version__ = "0.1.0"
