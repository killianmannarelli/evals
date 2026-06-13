#!/usr/bin/env python3
"""Surface the agent's TRAJECTORY tool-results from a rehydrated task json into a
readable trajectory.md, so auditors can ground "connected-service" golds in the
ACTUAL environment responses the agent received (skill/API results, DB reads).

Why this exists: the inline RESPONSE blob carries the agent's tool calls + the
environment's tool RESULTS (e.g. a Ticketmaster skill returning the real orders),
but the SOT bundle only staged the input files — so auditors wrongly marked those
values "unverifiable" (Rule 19c) and passed rubrics whose golds contradict the
environment. The tool-RESULTS are ground truth about the environment and ARE a
valid grounding source. (desired_outcome / Pass@K are still excluded.)

    python3 dump_trajectory.py --task <path/to/tasks/TID.json> --out <sot/TID/trajectory.md>
"""
import argparse, json, sys
from pathlib import Path

# keys whose subtrees are NOT admissible grounding and must be skipped
EXCLUDE_KEYS = {"desired_outcome", "passatk", "pass_at_k", "annotations"}


def find_trajectories(obj, out):
    """Collect every list found under a 'trajectory' key (the agent's turn trace)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in EXCLUDE_KEYS:
                continue
            if k == "trajectory" and isinstance(v, list) and v:
                out.append(v)
            else:
                find_trajectories(v, out)
    elif isinstance(obj, list):
        for v in obj:
            find_trajectories(v, out)


def turn_text(turn):
    """Extract role + any text/result payloads from one trajectory turn."""
    if not isinstance(turn, dict):
        return None
    msg = turn.get("message", turn)
    role = msg.get("role") or turn.get("role") or "?"
    chunks = []
    content = msg.get("content")
    if isinstance(content, str):
        chunks.append(content)
    elif isinstance(content, list):
        for c in content:
            if isinstance(c, dict):
                if c.get("text"):
                    chunks.append(c["text"])
                elif c.get("type") == "tool_use":
                    chunks.append(f"[tool_call {c.get('name','?')}] {json.dumps(c.get('input', {}))[:2000]}")
            elif isinstance(c, str):
                chunks.append(c)
    # tool results often live in details.aggregated
    det = msg.get("details") or {}
    if isinstance(det, dict) and det.get("aggregated"):
        agg = det["aggregated"]
        chunks.append(agg if isinstance(agg, str) else json.dumps(agg)[:4000])
    tool = msg.get("name") or msg.get("tool_name")
    head = f"### {role}" + (f" · {tool}" if tool else "")
    body = "\n".join(ch.strip() for ch in chunks if ch and ch.strip())
    return f"{head}\n{body}" if body else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = json.load(open(a.task))
    r = d.get("response")
    if isinstance(r, str):
        try: r = json.loads(r)
        except Exception: r = {}
    trajs = []
    find_trajectories(r or {}, trajs)
    # de-dup identical trajectories (the blob repeats them across steps)
    seen, uniq = set(), []
    for t in trajs:
        key = json.dumps(t)[:5000]
        if key not in seen:
            seen.add(key); uniq.append(t)
    blocks = []
    for ti, traj in enumerate(uniq):
        for turn in traj:
            tt = turn_text(turn)
            if tt:
                blocks.append(tt)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    if not blocks:
        out.write_text("(no agent trajectory tool-results found in this attempt)\n")
        print(f"{d.get('task_id','?')}: no trajectory turns surfaced", file=sys.stderr)
        return 0
    header = ("# Agent trajectory — tool calls + ENVIRONMENT tool-results\n"
              "# Ground truth for 'connected-service' values (skill/API/DB results the agent received).\n"
              "# This is admissible grounding. desired_outcome / Pass@K are excluded.\n\n")
    out.write_text(header + "\n\n".join(blocks))
    print(f"{d.get('task_id','?')}: wrote {len(blocks)} trajectory turns -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
