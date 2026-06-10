#!/usr/bin/env python3
"""Resolve qc-auditor-openclaw runtime settings.

Resolution order (first found wins per key; missing keys inherit downward):
  1. <cwd>/.claude/qc-auditor-openclaw.local.md         (per-run override)
  2. <skill_dir>/qc-auditor-openclaw.local.md           (shipped default)
  3. DEFAULTS below                                     (hard-coded fallback)

Reads the YAML frontmatter (between the first two `---` lines). No PyYAML dependency:
a minimal scalar/bool/int/list parser handles the flat schema this skill uses.

Usage:
  python3 load_settings.py                 # pretty table -> stderr, JSON -> stdout
  python3 load_settings.py --shell         # also emit `export QCO_<KEY>=<val>` lines to stdout
  python3 load_settings.py --cwd <dir>     # resolve the per-run override relative to <dir>
  python3 load_settings.py --get gate_script   # print one resolved value (for scripting)
"""
import argparse, json, os, sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_BASENAME = "qc-auditor-openclaw.local.md"

# Hard-coded fallback — mirrors the shipped skill-local file. Keep in sync.
DEFAULTS = {
    "enabled": True,
    "default_layer": "L10",
    "default_status": "pending",
    "spec_version": "V6",
    "spec_query_id": 304995,
    "spec_static_fallback": "~/Downloads/openclaw_mm_rubrics_spec.md",
    "gate_script": "preaudit_checks_v2.py",
    "gate_version": "v2.2",
    "spot_check_pattern_active": True,
    "swarm_mode": "hybrid_3plus1",
    "generalists": 3,
    "rubric_specialist": True,
    "tests_specialist": False,
    "batch_size": 28,
    "tests_in_scope": False,
    "process_targeting_advisory": True,
    "fetch_artifacts": "auto",
    "auto_attempter": False,
    "index_to_vault": True,
    "vault_path": "~/Documents/Obsidian",
}

# Validation: enums + types. Invalid values warn to stderr and fall back to DEFAULTS[key].
ENUMS = {
    "default_layer": {"L-1", "L0", "L1", "L10", "L11", "L12"},
    "default_status": {"pending", "completed", "any"},
    "gate_script": {"preaudit_checks.py", "preaudit_checks_v2.py"},
    "gate_version": {"v2.1", "v2.2"},
    "swarm_mode": {"hybrid_3plus1", "combined"},
    "fetch_artifacts": {"auto", "true", "false", True, False},
}
BOOL_KEYS = {"enabled", "spot_check_pattern_active", "rubric_specialist", "tests_specialist",
             "tests_in_scope", "process_targeting_advisory", "auto_attempter", "index_to_vault"}
INT_KEYS = {"spec_query_id", "generalists", "batch_size"}
PATH_KEYS = {"spec_static_fallback", "vault_path"}


def _coerce(val):
    """Coerce a raw frontmatter scalar string into bool / int / list / str."""
    s = val.strip()
    if s == "":
        return ""
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if s.startswith("[") and s.endswith("]"):  # inline list: [a, b, c]
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [x.strip().strip('"').strip("'") for x in inner.split(",")]
    if (s[0] == s[-1]) and s[0] in ("'", '"'):  # quoted string
        return s[1:-1]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        f = float(s)
        return f
    except ValueError:
        pass
    return s  # bare string


def parse_frontmatter(path):
    """Return {key: coerced_value} from the first `---`-delimited block, or {} if none/missing."""
    if not path or not os.path.isfile(path):
        return {}
    out = {}
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        st = line.strip()
        if not st or st.startswith("#"):  # blank or comment
            continue
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        raw = raw.split(" #", 1)[0]  # strip trailing inline comment
        if key:
            out[key] = _coerce(raw)
    return out


def validate(merged, warn):
    """Type/enum-check each key; on failure, warn and revert to DEFAULTS[key]."""
    for k, v in list(merged.items()):
        if k not in DEFAULTS:
            warn(f"unknown setting '{k}' ignored")
            merged.pop(k, None)
            continue
        if k in BOOL_KEYS and not isinstance(v, bool):
            warn(f"'{k}'={v!r} is not a bool -> default {DEFAULTS[k]!r}")
            merged[k] = DEFAULTS[k]
        elif k in INT_KEYS and not isinstance(v, int):
            warn(f"'{k}'={v!r} is not an int -> default {DEFAULTS[k]!r}")
            merged[k] = DEFAULTS[k]
        elif k in ENUMS and v not in ENUMS[k]:
            warn(f"'{k}'={v!r} not in {sorted(map(str, ENUMS[k]))} -> default {DEFAULTS[k]!r}")
            merged[k] = DEFAULTS[k]
    if merged.get("generalists", 1) < 1:
        warn("'generalists' < 1 -> default 3")
        merged["generalists"] = 3
    if merged.get("batch_size", 1) < 1:
        warn("'batch_size' < 1 -> default 28")
        merged["batch_size"] = 28
    # coherence nudge (warn only, don't mutate): spot_check flag should track gate version
    if merged.get("spot_check_pattern_active") and merged.get("gate_version") == "v2.1":
        warn("spot_check_pattern_active=true but gate_version=v2.1 (v2.1 has no spot-check exemptions)")
    for k in PATH_KEYS:
        if isinstance(merged.get(k), str):
            merged[k + "_expanded"] = os.path.expanduser(merged[k])
    return merged


def resolve(cwd):
    cwd_file = os.path.join(cwd, ".claude", SETTINGS_BASENAME)
    skill_file = os.path.join(SKILL_DIR, SETTINGS_BASENAME)
    sources = []
    merged = dict(DEFAULTS)
    # apply skill-local over DEFAULTS, then cwd over skill-local
    for path, label in [(skill_file, "skill"), (cwd_file, "cwd")]:
        fm = parse_frontmatter(path)
        if fm:
            sources.append({"label": label, "path": path, "keys": sorted(fm.keys())})
            merged.update(fm)
    return merged, sources, cwd_file, skill_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--shell", action="store_true", help="also emit `export QCO_<KEY>=<val>` lines")
    ap.add_argument("--get", metavar="KEY", help="print one resolved value and exit")
    args = ap.parse_args()

    warnings = []
    merged, sources, cwd_file, skill_file = resolve(args.cwd)
    merged = validate(merged, warnings.append)

    if args.get:
        v = merged.get(args.get, "")
        print(v if not isinstance(v, bool) else str(v).lower())
        return

    # provenance + warnings -> stderr (human-facing)
    print("qc-auditor-openclaw settings resolved:", file=sys.stderr)
    if not sources:
        print(f"  (no settings file found; using hard-coded DEFAULTS)\n  looked: {cwd_file}\n          {skill_file}",
              file=sys.stderr)
    for s in sources:
        print(f"  [{s['label']}] {s['path']}  ({len(s['keys'])} keys)", file=sys.stderr)
    for w in warnings:
        print(f"  ⚠️  {w}", file=sys.stderr)
    enabled = merged.get("enabled", True)
    sm = merged.get("swarm_mode")
    topo = ("combined: 1 auditor+master/task" if sm == "combined"
            else f"{merged.get('generalists')} generalists + "
                 f"{'1 rubric specialist' if merged.get('rubric_specialist') else '0 specialist'}"
                 f"{' + 1 tests specialist' if merged.get('tests_specialist') else ''} + 1 master")
    print(f"  → enabled={enabled} · layer={merged.get('default_layer')}/{merged.get('default_status')} · "
          f"gate={merged.get('gate_script')} ({merged.get('gate_version')}) · {topo} · "
          f"vault_index={merged.get('index_to_vault')}", file=sys.stderr)

    # machine-facing
    if args.shell:
        for k, v in merged.items():
            if k.endswith("_expanded"):
                continue
            val = str(v).lower() if isinstance(v, bool) else (json.dumps(v) if isinstance(v, list) else str(v))
            print(f"export QCO_{k.upper()}={json.dumps(val) if ' ' in val else val}")
    else:
        print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
