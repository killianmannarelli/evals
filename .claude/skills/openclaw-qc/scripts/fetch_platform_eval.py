#!/usr/bin/env python3
"""
fetch_platform_eval.py  —  OpenClaw MM Task Viewer scraper (platform-vs-audit comparison)

For every task in <workspace>/tasks/, read its attempt_id, fetch the public
server-rendered viewer page

    {viewer_base}/attempt/<attempt_id>/index.html

and extract the PLATFORM eval: overall score (total/max/pct), category/universe,
and per-criterion rows (number, full rubric-id UUID, text, weight, importance,
type, eval target, awarded/not-awarded). Writes one
<workspace>/platform_eval/<task_id>.json per task.

Why scrape the HTML and not the JSON: the viewer's machine endpoint
({viewer_base}/responses/<task>_<attempt>.json) is 401-protected, but
index.html is public and fully server-rendered (all data inline). If the whole
site is later put behind Vercel Deployment Protection, pass --bypass-token
(Vercel protection-bypass automation token) or --cookie.

The per-criterion `rubric_id8` (first 8 hex of the UUID) matches the
`criterion_id` our audit findings cite, so downstream (compile_report.py) can
align the two evals criterion-for-criterion and flag divergences — e.g. the
platform AWARDING a criterion this audit flagged as a penalize-correct defect
(the rubric propagating its own bug into the score).

Usage:
  python3 fetch_platform_eval.py --workspace <ws> \
      [--viewer-base https://openclaw-viewer-mm.vercel.app] \
      [--bypass-token <vercel_automation_bypass_secret>] \
      [--cookie '<raw Cookie header>']
"""
import argparse, glob, html, json, os, re, sys, urllib.request, urllib.error

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
DEFAULT_BASE = "https://openclaw-viewer-mm.vercel.app"

SCORE_RE = re.compile(r'<span class="pill score">\s*(\d+)\s*/\s*(\d+)\s*\((\d+)%\)\s*</span>')
UNIVERSE_RE = re.compile(r'<span class="universe">([^<]+)</span>')
CATEGORY_RE = re.compile(r'<span class="category">([^<]+)</span>')
ROW_RE = re.compile(r'<tr class="rubric-row state-(?P<state>[a-z_]+)"\s+data-rubric-id="(?P<rid>[0-9a-f\-]+)">(?P<body>.*?)</tr>', re.S)
TD_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.S)
TEXT_RE = re.compile(r'<span class="rubric-text">(.*?)</span>', re.S)
AWARD_RE = re.compile(r'award award-(\w+)')

# ── embedded audit drawer (the viewer ships a full spec-grounded rubric audit) ──
DRAWER_RE = re.compile(r'fail\s+(\d+)\s*·\s*non_fail\s+(\d+)\s*·\s*info\s+(\d+)')
AUDIT_DIM_RE = re.compile(
    r'<li class="audit-finding sev-(?P<sev>[a-z_]+)"[^>]*?data-dimension="(?P<dim>[^"]*)"[^>]*?(?:data-finding-id="(?P<fid>[^"]*)")?[^>]*>(?P<body>.*?)</li>', re.S)
AUDIT_DIMNAME_RE = re.compile(r'audit-dim-name">(.*?)<')
AUDIT_SUMMARY_RE = re.compile(r'audit-summary">(.*?)</p>', re.S)
AUDIT_CODECHIP_RE = re.compile(r'audit-code-chip">(.*?)<')
AUDIT_DETAILS_RE = re.compile(r'audit-details">(.*?)</p>', re.S)
AUDIT_CRIT_RE = re.compile(
    r'<details class="rubric-audit-block sev-(?P<sev>[a-z_]+)"[^>]*?(?:data-finding-id="(?P<fid>[^"]*)")?[^>]*>(?P<body>.*?)</details>', re.S)
AUDIT_ICLASS_RE = re.compile(r'audit-iclass ic-(\w+)')
AUDIT_RULECHIP_RE = re.compile(r'audit-rule-chip">(.*?)<')
AUDIT_INLINE_RE = re.compile(r'audit-inline-summary">(.*?)</span>', re.S)


def strip_tags(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip())


def fetch(url, bypass_token=None, cookie=None, timeout=30):
    if bypass_token:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}x-vercel-protection-bypass={bypass_token}&x-vercel-set-bypass-cookie=true"
    headers = {"User-Agent": UA}
    if bypass_token:
        headers["x-vercel-protection-bypass"] = bypass_token
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def parse(html):
    out = {"score": None, "universe": None, "category": None, "criteria": []}
    m = SCORE_RE.search(html)
    if m:
        total, mx, pct = int(m.group(1)), int(m.group(2)), int(m.group(3))
        out["score"] = {"total": total, "max": mx, "pct": pct}
    u = UNIVERSE_RE.search(html)
    if u:
        out["universe"] = strip_tags(u.group(1))
    c = CATEGORY_RE.search(html)
    if c:
        out["category"] = strip_tags(c.group(1))
    for rm in ROW_RE.finditer(html):
        body = rm.group("body")
        tds = TD_RE.findall(body)
        cells = [strip_tags(t) for t in tds]
        txtm = TEXT_RE.search(body)
        text = strip_tags(txtm.group(1)) if txtm else (cells[1] if len(cells) > 1 else "")
        am = AWARD_RE.search(body)
        rid = rm.group("rid")
        # cells layout: [num, criterion(text/button), weight, importance, type, eval_target, award]
        num = cells[0] if cells else ""
        weight = cells[2] if len(cells) > 2 else ""
        importance = cells[3] if len(cells) > 3 else ""
        ctype = cells[4] if len(cells) > 4 else ""
        evtarget = cells[5] if len(cells) > 5 else ""
        out["criteria"].append({
            "num": num,
            "rubric_id": rid,
            "rubric_id8": rid.replace("-", "")[:8],
            "text": text,
            "weight": weight,
            "importance": importance,
            "type": ctype,
            "eval_target": evtarget,
            "state": rm.group("state"),            # awarded | not_awarded
            "awarded": rm.group("state") == "awarded",
            "award_polarity": am.group(1) if am else None,  # positive | negative | ...
        })
    return out


def parse_audit(html):
    """Extract the embedded rubric-quality audit the viewer ships in its drawer.
    This is a full spec-grounded audit (dimension-level verdicts + per-criterion
    findings) and is treated as the AUTHORITATIVE reference eval (2026-06-07)."""
    au = {"drawer": None, "dimension_findings": [], "criterion_findings": [], "embedded_verdict": None}
    dm = DRAWER_RE.search(html)
    if dm:
        au["drawer"] = {"fail": int(dm.group(1)), "non_fail": int(dm.group(2)), "info": int(dm.group(3))}
    for m in AUDIT_DIM_RE.finditer(html):
        body = m.group("body")
        au["dimension_findings"].append({
            "severity": m.group("sev"),
            "dimension": m.group("dim"),
            "finding_id": m.group("fid"),
            "dim_name": strip_tags((AUDIT_DIMNAME_RE.search(body) or [None, ""])[1]) if AUDIT_DIMNAME_RE.search(body) else "",
            "summary": strip_tags((AUDIT_SUMMARY_RE.search(body).group(1)) if AUDIT_SUMMARY_RE.search(body) else ""),
            "code": strip_tags((AUDIT_CODECHIP_RE.search(body).group(1)) if AUDIT_CODECHIP_RE.search(body) else ""),
            "detail": strip_tags((AUDIT_DETAILS_RE.search(body).group(1)) if AUDIT_DETAILS_RE.search(body) else ""),
        })
    for m in AUDIT_CRIT_RE.finditer(html):
        body = m.group("body")
        au["criterion_findings"].append({
            "severity": m.group("sev"),
            "finding_id": m.group("fid"),
            "iclass": (AUDIT_ICLASS_RE.search(body).group(1) if AUDIT_ICLASS_RE.search(body) else ""),
            "rule": strip_tags((AUDIT_RULECHIP_RE.search(body).group(1)) if AUDIT_RULECHIP_RE.search(body) else ""),
            "summary": strip_tags((AUDIT_INLINE_RE.search(body).group(1)) if AUDIT_INLINE_RE.search(body) else ""),
            "detail": strip_tags((AUDIT_DETAILS_RE.search(body).group(1)) if AUDIT_DETAILS_RE.search(body) else ""),
        })
    has_fail = any(f["severity"] == "fail" for f in au["dimension_findings"])
    has_nf = any(f["severity"] in ("non_fail", "nonfail") for f in au["dimension_findings"]) or \
        any(f["severity"] in ("fail", "non_fail") for f in au["criterion_findings"])
    au["embedded_verdict"] = "Fail" if has_fail else ("Non-Fail" if has_nf else "Pass")
    return au


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--viewer-base", default=DEFAULT_BASE)
    ap.add_argument("--bypass-token", default=os.environ.get("OPENCLAW_VIEWER_BYPASS"))
    ap.add_argument("--cookie", default=os.environ.get("OPENCLAW_VIEWER_COOKIE"))
    args = ap.parse_args()

    print("QC Auditor (OpenClaw) — created by Killian Mannarelli.", file=sys.stderr)
    tasks_dir = os.path.join(args.workspace, "tasks")
    out_dir = os.path.join(args.workspace, "platform_eval")
    os.makedirs(out_dir, exist_ok=True)

    task_files = sorted(glob.glob(os.path.join(tasks_dir, "*.json")))
    ok = fail = 0
    for tf in task_files:
        tid = os.path.basename(tf)[:-5]
        try:
            d = json.load(open(tf))
        except Exception as e:
            print(f"  {tid}: cannot read task json ({e})", file=sys.stderr); fail += 1; continue
        aid = d.get("attempt_id") or (d.get("meta") or {}).get("attempt_id")
        if not aid:
            print(f"  {tid}: no attempt_id; skipping", file=sys.stderr); fail += 1; continue
        url = f"{args.viewer_base}/attempt/{aid}/index.html"
        rec = {"task_id": tid, "attempt_id": aid, "viewer_url": url,
               "score": None, "universe": None, "category": None, "criteria": [], "error": None}
        try:
            html = fetch(url, args.bypass_token, args.cookie)
            rec.update(parse(html))
            rec["embedded_audit"] = parse_audit(html)
            sc = rec["score"]
            print(f"  {tid}: {sc['total']}/{sc['max']} ({sc['pct']}%) · {len(rec['criteria'])} criteria"
                  if sc else f"  {tid}: parsed (no score pill found) · {len(rec['criteria'])} criteria",
                  file=sys.stderr)
            ok += 1
        except urllib.error.HTTPError as e:
            rec["error"] = f"HTTP {e.code}"
            note = " (site is protection-gated — pass --bypass-token or --cookie)" if e.code == 401 else ""
            print(f"  {tid}: HTTP {e.code}{note}", file=sys.stderr); fail += 1
        except Exception as e:
            rec["error"] = str(e)
            print(f"  {tid}: {e}", file=sys.stderr); fail += 1
        json.dump(rec, open(os.path.join(out_dir, tid + ".json"), "w"), indent=2)

    print(f"platform_eval: {ok} fetched, {fail} failed -> {out_dir}", file=sys.stderr)
    # non-zero only if EVERYTHING failed (so the pipeline still completes on partial)
    sys.exit(1 if ok == 0 and task_files else 0)


if __name__ == "__main__":
    main()
