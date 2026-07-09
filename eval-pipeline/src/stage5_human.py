"""stage5_human — THE human-first output tab.

One tab a reviewer reads top-to-bottom: a color-coded GLOBAL verdict (FAIL/NON-FAIL/PASS),
a one-line headline, prioritized plain-English feedback, the recommended fix, reward, and the
per-lens evidence (DRAWER audit / CDQ / linters) collapsed to the right. A summary banner sits
on row 1.

Source = report.json (stage4: the worst-wins verdict over linters ∪ CDQ ∪ DRAWER, plus deduped
findings that already carry `fix` and are answer-key-redacted) enriched with drawer.json (spec
band, confidence, agreement, why). Writes a NEW tab (never overwrites — sheet-safety rule).
"""
from __future__ import annotations
import argparse, collections, json
from datetime import datetime, timezone
from pathlib import Path
from src import common
from src.stage4_assemble import _redact   # answer-key redaction (drawer.json is raw / un-redacted)

LLM_CHECKS = {"cdq_static", "audit_hybrid31"}
VNORM = {"fail": "FAIL", "non-fail": "NON-FAIL", "pass": "PASS",
         "Fail": "FAIL", "Non-Fail": "NON-FAIL", "Pass": "PASS"}
VRANK = {"FAIL": 0, "NON-FAIL": 1, "PASS": 2}
HEADER = ["Global verdict", "Task ID", "Headline", "What's wrong (prioritized)",
          "Recommended fix", "Reward", "DRAWER audit", "CDQ", "Linter flags",
          "Category · Subcategory · Modality", "Open the task"]
WIDTHS = [98, 185, 300, 470, 380, 92, 340, 96, 200, 175, 230]


def _first_sentence(s, cap=220):
    s = " ".join(str(s or "").split())
    if not s:
        return ""
    for end in (". ", "? ", "! "):
        i = s.find(end)
        if 0 < i < cap:
            return s[:i + 1]
    return s[:cap] + ("…" if len(s) > cap else "")


def _label(f, human):
    """Human label: prefer the DRAWER CSV dimension title, then the taxonomy human label,
    then a title-cased token."""
    if f.get("flag_dimension"):
        return f["flag_dimension"]
    dt = f.get("defect_type", "")
    return human.get(dt, dt.replace("_", " ").title() or "Issue")


def _row(t, drawer, human, viewer):
    findings = sorted(t.get("findings", []), key=lambda f: 0 if f.get("tier") == "action_required" else 1)
    gv = VNORM.get(t.get("verdict", ""), str(t.get("verdict") or "").upper() or "PASS")

    top = next((f for f in findings if f.get("tier") == "action_required"),
               findings[0] if findings else None)
    headline = (f"{_label(top, human)}: {_first_sentence(top.get('explanation'))}"
                if top else "No blocking issues found.")

    whats = "\n".join(f"• [{_label(f, human)}] {f.get('explanation','')}" for f in findings) or "—"

    fixes, seen = [], set()
    for f in findings:
        fx = (f.get("fix") or "").strip()
        if fx and fx not in seen:
            seen.add(fx); fixes.append(f"• {fx}")
    fix_txt = "\n".join(fixes) or "—"

    mr = t.get("mean_reward")
    reward = "—" if mr is None else (f"{mr:.2f}" + ("  ⚠ low" if t.get("low_reward") else ""))

    dm = drawer.get(t["task_id"])
    if dm:
        bands = " · ".join(sorted({fl.get("category", "") for fl in dm.get("flags", []) if fl.get("category")}))
        drawer_txt = _redact(
            f"{VNORM.get(dm.get('verdict',''), dm.get('verdict',''))}  (confidence {dm.get('confidence','?')})\n"
            f"{dm.get('agreement','')}\n"
            + (f"Bands: {bands}\n" if bands else "")
            + (dm.get("why", ""))).strip()
    else:
        drawer_txt = "— (not audited)"

    cdq = [f for f in findings if f.get("check") == "cdq_static"]
    cdq_v = "FAIL" if any(f.get("tier") == "action_required" for f in cdq) else ("NON-FAIL" if cdq else "PASS")
    cdq_txt = cdq_v + (f"  ({len(cdq)})" if cdq else "")

    lint = [f for f in findings if f.get("check") not in LLM_CHECKS]
    lint_txt = " · ".join(f"{f['check']}:{f['defect_type']}" for f in lint) or "—"

    meta = " · ".join(x for x in [t.get("category"), t.get("subcategory"), t.get("mm_input")] if x)
    return [gv, t["task_id"], headline, whats, fix_txt, reward, drawer_txt, cdq_txt, lint_txt,
            meta, viewer + (t.get("attempt_id") or "")]


def _format(spreadsheet_id, gid, ncols, widths, ndata):
    ss = common.sheets()
    LIGHT = {"red": 0.93, "green": 0.94, "blue": 0.96}
    reqs = [
        # Freeze the banner + header ROWS only. (No column freeze: a merged full-width banner
        # can't straddle a frozen-column boundary; the verdict is col A + color-coded anyway.)
        {"updateSheetProperties": {"properties": {"sheetId": gid, "gridProperties": {
            "frozenRowCount": 2, "frozenColumnCount": 0}},
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}},
        {"mergeCells": {"range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": 1,
            "startColumnIndex": 0, "endColumnIndex": ncols}, "mergeType": "MERGE_ALL"}},
        {"repeatCell": {"range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 11},
                "backgroundColor": LIGHT, "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(textFormat,backgroundColor,verticalAlignment,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": gid, "startRowIndex": 1, "endRowIndex": 2},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "wrapStrategy": "WRAP",
                "verticalAlignment": "MIDDLE", "backgroundColor": LIGHT}},
            "fields": "userEnteredFormat(textFormat,wrapStrategy,verticalAlignment,backgroundColor)"}},
        {"repeatCell": {"range": {"sheetId": gid, "startRowIndex": 2, "endRowIndex": ndata + 2},
            "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}},
            "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": gid, "startRowIndex": 2, "endRowIndex": ndata + 2,
            "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE",
                "textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,textFormat)"}},
    ]
    for i in range(ncols):
        w = widths[i] if i < len(widths) else 160
        reqs.append({"updateDimensionProperties": {"range": {"sheetId": gid, "dimension": "COLUMNS",
            "startIndex": i, "endIndex": i + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})
    ss.batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()


def main(cfg, run_dir, tab=None):
    run_dir = Path(run_dir)
    report = json.load(open(run_dir / "report.json"))
    drawer = json.load(open(run_dir / "drawer.json")) if (run_dir / "drawer.json").exists() else {}
    human = cfg["taxonomy"].get("human_label", {})
    sc = cfg["pipeline"]["sheets"]
    viewer = sc["viewer_base"]
    tab = tab or f"eval {run_dir.name} (human)"

    rows = [_row(t, drawer, human, viewer) for t in report["tasks"]]
    rows.sort(key=lambda r: (VRANK.get(r[0], 3), 0 if "⚠" in r[5] else 1, r[1]))

    blob = json.dumps(rows)
    leaks = [x for x in ("why_rubric_is_correct", "/private/tmp", "REDASH_KEY", "claude-502") if x in blob]
    if leaks:
        raise SystemExit(f"stage5_human: REFUSING to write — leaks {leaks}")

    tot = report["totals"]
    nlow = tot.get("low_reward_tasks", sum(1 for r in rows if "⚠" in r[5]))
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    banner = ([f"{run_dir.name}   ·   {tot['fail']} FAIL / {tot['non_fail']} NON-FAIL / {tot['pass']} PASS"
               f"   ·   {tot['total_findings']} findings   ·   {nlow} low-reward   ·   generated {stamp}"]
              + [""] * (len(HEADER) - 1))

    tab_name, gid = common.write_new_tab(sc["spreadsheet_id"], tab, banner, [HEADER] + rows)
    _format(sc["spreadsheet_id"], gid, len(HEADER), WIDTHS, len(rows))
    common.color_verdict_column(sc["spreadsheet_id"], gid, 0, 2, 2 + len(rows))
    vc = collections.Counter(r[0] for r in rows)
    print(f"stage5_human: wrote {tab_name!r} (gid={gid}) — {len(rows)} tasks · {dict(vc)}")
    return tab_name, gid


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--tab")
    a = ap.parse_args()
    main(common.load_config(), a.run_dir, a.tab)
