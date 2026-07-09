"""Shared foundation for eval-pipeline: config, Redash, bundle parsing, reward, Sheets.

Everything tunable lives in config/*.yaml — this module only reads it. No project-specific
constants are hardcoded here except the well-known Redash table/paths.
"""
from __future__ import annotations
import io, json, os, re, time, zipfile, urllib.request, warnings, glob
from pathlib import Path

warnings.filterwarnings("ignore")  # silence py3.9 EOL / urllib3 FutureWarnings

# ── paths ───────────────────────────────────────────────────────────────────
PKG = Path(__file__).resolve().parent.parent          # eval-pipeline/
CONFIG = PKG / "config"
RUNS = PKG / "runs"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def load_config() -> dict:
    """Merge config/pipeline.yaml + taxonomy.yaml + thresholds.yaml into one dict."""
    import yaml
    cfg = {}
    for name in ("pipeline", "taxonomy", "thresholds"):
        with open(CONFIG / f"{name}.yaml") as fh:
            cfg[name] = yaml.safe_load(fh)
    return cfg


def expand(p: str) -> str:
    return os.path.expanduser(p) if p else p


# ── Redash ────────────────────────────────────────────────────────────────────
def _req(method, path, body=None, base="https://redash.scale.com"):
    key = os.environ["REDASH_KEY"]
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(base + path, data=data, method=method,
                               headers={"Authorization": f"Key {key}",
                                        "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())


def redash_run(sql, ds_id=30, timeout=300):
    r = _req("POST", "/api/query_results", {"query": sql, "data_source_id": ds_id, "max_age": 0})
    if "query_result" in r:
        return r["query_result"]["data"]
    jid = r["job"]["id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(4)
        j = _req("GET", f"/api/jobs/{jid}")["job"]
        if j["status"] == 3:
            return _req("GET", f"/api/query_results/{j['query_result_id']}")["query_result"]["data"]
        if j["status"] == 4:
            raise RuntimeError("Redash query failed: " + str(j.get("error")))
    raise TimeoutError("Redash query timed out")


def rows_of(data):
    """Normalize Redash result rows to lowercase-keyed dicts."""
    out = []
    for r in data["rows"]:
        out.append({k.lower(): v for k, v in r.items()})
    return out


# ── bundle download + parse ───────────────────────────────────────────────────
def download(url: str, timeout=180) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# grading artifacts (NOT the mock services' own **/test_*.py infra tests)
_GRADING = {
    "rubric": "tests/rubric.json",
    "visual_rubrics": "visual_rubrics.json",   # optional; some editing tasks
    "test_code": "tests/test_outputs.py",
    "test_weights": "tests/test_weights.json",
    "task_toml": "task.toml",
    "instruction": "instruction.md",
}


def parse_bundle(zip_bytes: bytes) -> dict:
    """Extract the grading artifacts from a bundle zip. Returns raw text/parsed per key.
    `visual_rubrics` is searched anywhere in the tree (some tasks nest it)."""
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = z.namelist()
    root = ""
    for n in names:
        if n.endswith("task.toml"):
            root = n[: -len("task.toml")]
            break
    out = {"root": root, "names_count": len(names)}
    def read(member):
        for cand in (root + member, member):
            if cand in names:
                return z.read(cand).decode("utf-8", "replace")
        return None
    for key, member in _GRADING.items():
        raw = read(member)
        out[key + "_raw"] = raw
    # visual_rubrics may live at a non-standard path — search
    if not out.get("visual_rubrics_raw"):
        vr = next((n for n in names if n.endswith("visual_rubrics.json")), None)
        if vr:
            out["visual_rubrics_raw"] = z.read(vr).decode("utf-8", "replace")
    # parse JSON fields
    out["rubric"] = _try_json(out.get("rubric_raw")) or []
    out["visual_rubrics"] = _try_json(out.get("visual_rubrics_raw"))
    tw = _try_json(out.get("test_weights_raw")) or {}
    out["test_weights"] = _flatten_test_weights(tw)
    return out


def _try_json(s):
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def _flatten_test_weights(tw):
    if isinstance(tw, dict) and "tests" in tw:
        return {t.get("test_name"): t.get("weight") for t in tw["tests"] if isinstance(t, dict)}
    return tw if isinstance(tw, dict) else {}


# ── reward (replicates customer mean_reward + weighted_score) ──────────────────
def compute_reward(pak) -> dict:
    """From metadata.passAtKResults compute mean_reward (raw rubric pass rate over rollouts),
    weighted_score (weight-adjusted rubric+test reward, penalties subtracting), n_runs, and
    per-criterion pass rate (title -> fraction of runs passed)."""
    if isinstance(pak, str):
        pak = _try_json(pak)
    if not isinstance(pak, dict):
        return {"mean_reward": None, "weighted_score": None, "n_runs": 0, "crit_pass_rate": {}}
    runs = pak.get("runs") or {}
    run_list = list(runs.values()) if isinstance(runs, dict) else list(runs)
    raw_fracs, weighted, crit_hits, crit_tot = [], [], {}, {}
    for run in run_list:
        rr = (run or {}).get("rubric_results") or {}
        crits = rr.get("criteria") if isinstance(rr, dict) else None
        crits = crits or []
        tr = (run or {}).get("test_results") or {}
        cases = tr.get("cases") if isinstance(tr, dict) else None
        cases = cases or []
        # raw rubric pass fraction
        if crits:
            npass = sum(1 for c in crits if str(c.get("result", "")).upper().startswith("PASS"))
            raw_fracs.append(npass / len(crits))
            for c in crits:
                t = c.get("title", "")
                crit_tot[t] = crit_tot.get(t, 0) + 1
                if str(c.get("result", "")).upper().startswith("PASS"):
                    crit_hits[t] = crit_hits.get(t, 0) + 1
        # weighted reward over pooled rubric + test items (eval-guide formula)
        num = den = 0.0
        for item in list(crits) + list(cases):
            w = item.get("weight")
            if w is None:
                continue
            passed = str(item.get("result", "")).upper().startswith("PASS")
            if w >= 0:
                den += w
                if passed:
                    num += w
            else:                       # penalty guard: subtract when the bad thing happened (failed)
                if not passed:
                    num += w
        if den > 0:
            weighted.append(max(0.0, num / den))
    def mean(xs):
        return round(sum(xs) / len(xs), 4) if xs else None
    return {
        "mean_reward": mean(raw_fracs),
        "weighted_score": mean(weighted),
        "n_runs": len(run_list),
        "crit_pass_rate": {t: round(crit_hits.get(t, 0) / crit_tot[t], 3) for t in crit_tot},
    }


# ── Google Sheets ─────────────────────────────────────────────────────────────
def sheets():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    sa = os.environ.get("GOOGLE_SA_JSON") or str(PKG.parent / "creds" / "sa.json")
    creds = service_account.Credentials.from_service_account_file(
        sa, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return build("sheets", "v4", credentials=creds).spreadsheets()


def write_new_tab(spreadsheet_id, tab_base, header, rows):
    """Create a NEW tab (auto-versioned on name collision) and write header+rows. Never
    overwrites an existing tab (sheet-safety rule)."""
    ss = sheets()
    titles = {s["properties"]["title"] for s in ss.get(spreadsheetId=spreadsheet_id).execute()["sheets"]}
    tab = tab_base
    n = 1
    while tab in titles:
        n += 1
        tab = f"{tab_base} v{n}"
    res = ss.batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": [{"addSheet": {"properties": {
        "title": tab, "gridProperties": {"rowCount": len(rows) + 5, "columnCount": len(header)}}}}]}).execute()
    gid = res["replies"][0]["addSheet"]["properties"]["sheetId"]
    ss.values().update(spreadsheetId=spreadsheet_id, range=f"'{tab}'!A1",
                       valueInputOption="RAW", body={"values": [header] + rows}).execute()
    return tab, gid


# ── finding helper ────────────────────────────────────────────────────────────
def finding(check, defect_type, tier, explanation, fix="", rubric_ids=None, test_names=None, evidence=""):
    return {
        "check": check, "defect_type": defect_type, "tier": tier,
        "rubric_ids": rubric_ids or [], "test_names": test_names or [],
        "explanation": explanation, "fix": fix, "evidence": evidence,
    }


def format_tab(spreadsheet_id, gid, ncols, widths=None, nrows=200):
    """Make a written tab readable: wrap text, freeze header + col A, bold header, set column
    widths. Called after write_new_tab so tabs never come out with cut-off columns."""
    ss = sheets()
    reqs = [
        {"updateSheetProperties": {"properties": {"sheetId": gid, "gridProperties": {
            "frozenRowCount": 1, "frozenColumnCount": 1}},
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}},
        {"repeatCell": {"range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "wrapStrategy": "WRAP",
                     "verticalAlignment": "MIDDLE"}},
            "fields": "userEnteredFormat(textFormat,wrapStrategy,verticalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": gid, "startRowIndex": 1, "endRowIndex": nrows + 1},
            "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}},
            "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)"}},
    ]
    for i in range(ncols):
        w = (widths[i] if widths and i < len(widths) else 160)
        reqs.append({"updateDimensionProperties": {"range": {"sheetId": gid, "dimension": "COLUMNS",
            "startIndex": i, "endIndex": i + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})
    ss.batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()
