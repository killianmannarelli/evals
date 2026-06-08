"""
events.py — Tiny helper for appending JSONL progress events to a state dir.

The web UI server tails `<state_dir>/events.jsonl` over SSE so the page can
render live progress as Claude runs the audit. Every call to `emit()` produces
exactly one line: a JSON object with a `phase` and `ts`, plus whatever extra
fields the caller passes.

This module is import-safe even when the web UI isn't running — if no state
dir is configured (`QC_AUDITOR_STATE_DIR` env var unset, and no explicit
`state_dir=` arg), `emit()` is a no-op. That way the existing CLI scripts
can call it unconditionally without breaking when invoked outside the UI.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


_ENV_KEY = "QC_AUDITOR_STATE_DIR"


def _resolve_state_dir(explicit: str | os.PathLike[str] | None) -> Path | None:
    if explicit is not None:
        return Path(explicit)
    env = os.environ.get(_ENV_KEY)
    if env:
        return Path(env)
    return None


def emit(phase: str, *, state_dir: str | os.PathLike[str] | None = None, **fields: Any) -> None:
    """Append one JSONL event to `<state_dir>/events.jsonl`. No-op if no state dir."""
    sd = _resolve_state_dir(state_dir)
    if sd is None:
        return
    sd.mkdir(parents=True, exist_ok=True)
    record = {"phase": phase, "ts": time.time(), **fields}
    line = json.dumps(record, default=str)
    # Append with a single write call so concurrent emitters don't tear lines.
    with (sd / "events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def write_state(state: dict, *, state_dir: str | os.PathLike[str] | None = None) -> None:
    """Atomically replace `<state_dir>/state.json` with the given dict."""
    sd = _resolve_state_dir(state_dir)
    if sd is None:
        return
    sd.mkdir(parents=True, exist_ok=True)
    tmp = sd / "state.json.tmp"
    tmp.write_text(json.dumps(state, indent=2, default=str))
    tmp.replace(sd / "state.json")


def read_state(state_dir: str | os.PathLike[str] | None = None) -> dict:
    sd = _resolve_state_dir(state_dir)
    if sd is None:
        return {}
    f = sd / "state.json"
    if not f.is_file():
        return {}
    try:
        return json.loads(f.read_text())
    except json.JSONDecodeError:
        return {}
