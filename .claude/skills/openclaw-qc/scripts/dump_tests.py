#!/usr/bin/env python3
"""Surface the task's unit tests (verifier.py) from the rehydrated task JSON into
sot/<tid>/unit_tests.py, so grounded auditors can evaluate the Tests-Correctness
dimension (a test whose logic contradicts the prompt/inputs and wrongly fails a
correct response is an incorrect test). Mirrors dump_trajectory.py.

Usage: python3 dump_tests.py --task <ws>/tasks/<tid>.json --out <ws>/sot/<tid>/unit_tests.py
"""
import argparse, json, re

def _walk_strings(o):
    if isinstance(o, dict):
        for v in o.values(): yield from _walk_strings(v)
    elif isinstance(o, list):
        for v in o: yield from _walk_strings(v)
    elif isinstance(o, str):
        yield o

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = json.load(open(a.task))
    # Candidate = a string that looks like the verifier.py source: most `def test_`
    # blocks, has imports, isn't a prose summary. Prefer the workspace_verification file.
    best = ""
    best_score = -1
    for s in _walk_strings(d):
        n = s.count("def test_")
        if n == 0:
            continue
        # source-like signals; penalize prose ("✅", "the attached file")
        score = n * 100 + s.count("\nimport ") + s.count("assert ")
        if "✅" in s or "the attached file" in s or "Line count" in s:
            score -= 500
        if score > best_score:
            best_score, best = score, s
    if best_score < 0:
        open(a.out, "w").write("(no unit tests found in this attempt)\n")
        print(f"no unit tests found -> {a.out}")
        return
    # strip a fenced code block wrapper if present
    m = re.search(r"```(?:python)?\n(.*?)```", best, re.S)
    body = m.group(1) if m else best
    open(a.out, "w").write(body)
    print(f"wrote unit tests ({body.count('def test_')} test fns, {len(body)} chars) -> {a.out}")

if __name__ == "__main__":
    main()
