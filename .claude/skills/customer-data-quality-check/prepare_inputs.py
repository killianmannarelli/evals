#!/usr/bin/env python3
"""Prepare loader-A inputs for the customer-data-quality-check eval.

Input : a CSV with (at least) two columns — a task id and the
        ``environment_docker_file`` URL for that task.
Output: one ``batch_NNN.json`` per task (a JSON list with a single record) plus
        a ``manifest.json``, in the exact shape the eval's static reviewer reads.
        Each task's ``environment/`` tree is extracted to disk so ``task_dir``
        points at a real, agent-visible directory.

Everything the static side needs lives inside the ``environment_docker_file``
zip, so no other source (delivery JSONL, pass@k, rollouts) is required.

Usage:
    python3 prepare_inputs.py --csv tasks.csv --output-dir ./qa_inputs

CSV column names are auto-detected (task_id / taskid / TASK_ID and
environment_docker_file / env_url / url). Override with --id-col / --url-col.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

# Files we pull out of each bundle, keyed by their path *relative to the bundle
# root* (the dir that contains task.toml — often the zip root itself).
REL_INSTRUCTION_MD = "instruction.md"
REL_INSTRUCTION_JSONL = "instructions.jsonl"
REL_TASK_TOML = "task.toml"
REL_RUBRIC = "tests/rubric.json"
REL_TEST_CODE = "tests/test_outputs.py"
REL_TEST_SH = "tests/test.sh"
REL_TEST_WEIGHTS = "tests/test_weights.json"
ENV_SUBDIR = "environment/"

_ID_CANDIDATES = ["task_id", "taskid", "task", "id"]
_URL_CANDIDATES = ["environment_docker_file", "env_url", "environment", "url", "docker_file"]


def _pick_col(fieldnames: list[str], candidates: list[str], override: str | None) -> str:
    if override:
        if override not in fieldnames:
            sys.exit(f"--column '{override}' not in CSV headers {fieldnames}")
        return override
    lower = {f.lower().strip(): f for f in fieldnames}
    for c in candidates:
        if c in lower:
            return lower[c]
    sys.exit(f"Could not auto-detect a column among {candidates} in {fieldnames}. "
             f"Pass it explicitly.")


def download(url: str) -> bytes:
    if url.startswith("scale-cds://"):
        sys.exit(f"URL needs dashboard signing first (transform_obj_s3_url): {url}\n"
                 f"Resolve scale-cds:// URLs to signed https URLs before running.")
    req = urllib.request.Request(url, headers={"User-Agent": "loader-a/1.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read()


def _detect_root(names: list[str]) -> str:
    """Return the prefix (incl. trailing slash, or '') that precedes task.toml."""
    for n in names:
        if n == REL_TASK_TOML:
            return ""
        if n.endswith("/" + REL_TASK_TOML):
            return n[: -len(REL_TASK_TOML)]
    # Fall back: no task.toml — assume flat root.
    return ""


def _read(z: zipfile.ZipFile, root: str, rel: str) -> str | None:
    """Read a bundle member by its root-relative path; tolerant of layout."""
    target = root + rel
    try:
        return z.read(target).decode("utf-8", "replace")
    except KeyError:
        pass
    # Fallback: match by suffix anywhere in the archive.
    for n in z.namelist():
        if n == rel or n.endswith("/" + rel):
            return z.read(n).decode("utf-8", "replace")
    return None


def _parse_rubrics(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    data = json.loads(raw)
    out = []
    for i, item in enumerate(data, start=1):
        criterion = item.get("criteria") or item.get("criterion") or ""
        out.append({
            "id": i,
            "criterion": criterion,
            # Keep sign as-is: a negative weight is a penalty rubric.
            "weight": item.get("weight"),
        })
    return out


def _parse_test_weights(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    data = json.loads(raw)
    tests = data.get("tests", []) if isinstance(data, dict) else []
    return {t["test_name"]: t.get("weight") for t in tests if "test_name" in t}


def _prompt_from_jsonl(raw: str) -> str:
    lines = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            lines.append(ln)
            continue
        role = obj.get("role", "user")
        content = obj.get("content", obj)
        lines.append(f"[{role}] {content if isinstance(content, str) else json.dumps(content)}")
    return "\n\n".join(lines)


def _extract_subtree(z: zipfile.ZipFile, root: str, subdir: str, dest_base: Path) -> list[str]:
    """Extract members under root+subdir into dest_base/<rel-after-root>. Returns written paths."""
    prefix = root + subdir
    written: list[str] = []
    for n in z.namelist():
        if not n.startswith(prefix) or n.endswith("/"):
            continue
        if "__MACOSX" in n or n.endswith(".pyc"):
            continue
        rel = n[len(root):]  # keep the leading "environment/..." / "conversation_history/..."
        out = dest_base / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        with z.open(n) as src:
            out.write_bytes(src.read())
        written.append(str(out))
    return written


def process_task(task_id: str, url: str, output_dir: Path, index: int,
                 carryover: dict[str, Any] | None = None) -> dict[str, Any]:
    z = zipfile.ZipFile(io.BytesIO(download(url)))
    names = z.namelist()
    root = _detect_root(names)

    # task_name: prefer task.toml's id, fall back to the CSV id.
    toml_raw = _read(z, root, REL_TASK_TOML) or ""
    toml_id = None
    for line in toml_raw.splitlines():
        if line.strip().startswith("task_id"):
            toml_id = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
    task_name = toml_id or task_id

    prompt = _read(z, root, REL_INSTRUCTION_MD)
    if prompt is None:
        jsonl = _read(z, root, REL_INSTRUCTION_JSONL)
        prompt = _prompt_from_jsonl(jsonl) if jsonl else ""

    rubrics = _parse_rubrics(_read(z, root, REL_RUBRIC))
    test_code = _read(z, root, REL_TEST_CODE)
    test_sh = _read(z, root, REL_TEST_SH)
    test_weights = _parse_test_weights(_read(z, root, REL_TEST_WEIGHTS))

    task_base = (output_dir / "task_dirs" / task_name).resolve()
    task_dir = task_base / "environment"
    _extract_subtree(z, root, ENV_SUBDIR, task_base)
    # Best-effort: the delivered sample trajectory(ies) for the optional single-trace runtime scan.
    sample_traces = _extract_subtree(z, root, "conversation_history/", task_base)

    tests_block: dict[str, Any] = {}
    if test_code:
        tests_block["test_code"] = test_code
    if test_sh:
        tests_block["test_sh"] = test_sh
    if test_weights:
        tests_block["test_weights"] = test_weights

    record: dict[str, Any] = {
        "task_name": task_name,
        "prompt_text": prompt or "",
        "rubrics": rubrics,
        "task_dir": str(task_dir),
        "has_pytest_tests": bool(test_code),
    }
    if tests_block:
        record["tests"] = tests_block
    if sample_traces:
        record["sample_traces"] = sample_traces
    # Passthrough columns (e.g. attempt_id, review_level): carried into the record so the
    # final CSV can echo them. They are NOT eval inputs and are ignored by every reviewer.
    if carryover:
        record["carryover"] = carryover

    batch_path = output_dir / f"batch_{index:03d}.json"
    batch_path.write_text(json.dumps([record], indent=2) + "\n")
    return record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True, type=Path, help="input CSV")
    ap.add_argument("--output-dir", required=True, type=Path, help="where to write batch_NNN.json")
    ap.add_argument("--id-col", default=None, help="override task-id column name")
    ap.add_argument("--url-col", default=None, help="override environment_docker_file column name")
    args = ap.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with args.csv.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            sys.exit("CSV has no header row.")
        id_col = _pick_col(reader.fieldnames, _ID_CANDIDATES, args.id_col)
        url_col = _pick_col(reader.fieldnames, _URL_CANDIDATES, args.url_col)
        rows = [r for r in reader if (r.get(url_col) or "").strip()]
        # Every other column is passthrough metadata (attempt_id, review_level, …) —
        # ignored by the eval, echoed into the output CSV.
        passthrough_cols = [c for c in reader.fieldnames if c not in (id_col, url_col)]

    print(f"Found {len(rows)} task(s). id_col='{id_col}' url_col='{url_col}' "
          f"passthrough={passthrough_cols or '[]'}")
    written = 0
    failures: list[tuple[str, str]] = []
    for i, row in enumerate(rows):
        tid = (row.get(id_col) or "").strip().strip('"').strip("'")
        url = (row.get(url_col) or "").strip().strip('"').strip("'")
        carryover = {c: (row.get(c) or "").strip() for c in passthrough_cols}
        try:
            rec = process_task(tid, url, args.output_dir, i, carryover=carryover)
            ok = bool(rec["prompt_text"].strip()) and bool(rec["rubrics"])
            print(f"  [{'ok' if ok else 'THIN'}] batch_{i:03d}  {rec['task_name']}  "
                  f"rubrics={len(rec['rubrics'])} tests={len(rec.get('tests',{}).get('test_weights',{}))}")
            written += 1
        except Exception as exc:  # noqa: BLE001
            failures.append((tid, str(exc)))
            print(f"  [FAIL] {tid}: {exc}")

    manifest = {"task_count": written}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nWrote {written} batch file(s) + manifest.json -> {args.output_dir}")
    if failures:
        print(f"{len(failures)} failure(s):")
        for tid, err in failures:
            print(f"  {tid}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
