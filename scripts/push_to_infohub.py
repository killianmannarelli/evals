#!/usr/bin/env python3
"""Append L0 + L1 audit_results.csv to the InfoHub 'Evals' tab.

Sheet: 1MOa-semWY_Z-uskBD9bwzGKrMHrHjXwERda9bv2_9QU
Tab:   Evals

Per ~/.claude memory (reference_drive_upload_oauth.md):
- Use the user's OAuth creds with drive.file scope (preferred).
- drive.file: write-by-id works, read-by-id 404s -- skip any probe.
- The sheet must be in the OAuth app's drive.file grant (the user opened it via
  Picker or the app created it). If the token doesn't see it, broaden scope or
  re-grant in the browser.

Usage:
    OAUTH_TOKEN_JSON=~/path/to/oauth_token.json python3 push_to_infohub.py

Pure-stdlib: no google-api-python-client dependency.
"""
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SHEET_ID = "1MOa-semWY_Z-uskBD9bwzGKrMHrHjXwERda9bv2_9QU"
TAB = "Evals"

# CSV files to push, in order. The header is taken from the first; the rest
# must match column-for-column.
DEFAULT_CSVS = [
    "results/L0_audit_results.csv",
    "results/L1_audit_results.csv",
]


def refresh_token(token_path):
    tok = json.load(open(os.path.expanduser(token_path)))
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": tok["refresh_token"],
        "client_id": tok["client_id"],
        "client_secret": tok["client_secret"],
    }).encode()
    req = urllib.request.Request(
        tok.get("token_uri", "https://oauth2.googleapis.com/token"),
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["access_token"]


def load_rows(csv_paths):
    header = None
    rows = []
    for p in csv_paths:
        with open(p, newline="") as f:
            reader = csv.reader(f)
            this_header = next(reader)
            if header is None:
                header = this_header
            elif this_header != header:
                raise SystemExit(f"header mismatch in {p}:\n  {header}\n  {this_header}")
            for r in reader:
                rows.append(r)
    return header, rows


def append(access_token, rows):
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
        f"/values/{urllib.parse.quote(TAB)}!A1:append"
        f"?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"
    )
    body = json.dumps({"values": rows}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} from Sheets append:", file=sys.stderr)
        print(e.read().decode(), file=sys.stderr)
        if e.code == 404:
            print(
                "\n404 usually means this OAuth client's drive.file grant "
                "doesn't include the sheet. Open the sheet in a browser "
                "session linked to the same client, or use a token with the "
                "https://www.googleapis.com/auth/spreadsheets scope.",
                file=sys.stderr,
            )
        raise


def main():
    token_path = os.environ.get("OAUTH_TOKEN_JSON", "~/.config/gcloud/oauth_token.json")
    csv_paths = sys.argv[1:] or DEFAULT_CSVS
    header, rows = load_rows(csv_paths)
    print(f"Loaded {len(rows)} rows from {len(csv_paths)} CSV(s); "
          f"header has {len(header)} columns", flush=True)
    access = refresh_token(token_path)
    print("Token refreshed via refresh_token grant", flush=True)
    result = append(access, rows)
    u = result.get("updates", {})
    print(
        f"Appended OK: {u.get('updatedRange')}  "
        f"rows={u.get('updatedRows')}  cells={u.get('updatedCells')}"
    )


if __name__ == "__main__":
    main()
