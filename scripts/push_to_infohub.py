#!/usr/bin/env python3
"""Append L0 + L1 audit_results.csv to the InfoHub 'Evals' tab.

Sheet: 1MOa-semWY_Z-uskBD9bwzGKrMHrHjXwERda9bv2_9QU
Tab:   Evals

Auth resolution (first that's set wins):
  GOOGLE_APPLICATION_CREDENTIALS  path to a service-account JSON.
                                  The SA must be granted Editor on the sheet.
                                  Signed via openssl subprocess (no Python
                                  cryptography lib needed).
  OAUTH_TOKEN_JSON                path to user OAuth token JSON with at least
                                  the spreadsheets scope. drive.file only
                                  works if the file is in the app's grant.

Per ~/.claude memory (reference_drive_upload_oauth.md):
  - SA cannot create files in My Drive (no quota), but CAN write to a sheet
    that has been shared with it as an editor.
  - drive.file write-by-id works only when the user opened the file via the
    Picker for this OAuth client.

Pure stdlib. Tested under Python 3.11.
"""
import base64
import csv
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SHEET_ID = "1MOa-semWY_Z-uskBD9bwzGKrMHrHjXwERda9bv2_9QU"
TAB = "Evals"
SPREADSHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"

DEFAULT_CSVS = [
    "results/L0_audit_results.csv",
    "results/L1_audit_results.csv",
]


def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def sa_access_token(sa_path):
    sa = json.load(open(os.path.expanduser(sa_path)))
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT", "kid": sa["private_key_id"]}
    claims = {
        "iss": sa["client_email"],
        "scope": SPREADSHEETS_SCOPE,
        "aud": sa["token_uri"],
        "iat": now,
        "exp": now + 3600,
    }
    signing_input = (
        b64u(json.dumps(header, separators=(",", ":")).encode())
        + b"."
        + b64u(json.dumps(claims, separators=(",", ":")).encode())
    )
    key_path = "/tmp/.sa_key.pem"
    with open(key_path, "w") as f:
        f.write(sa["private_key"])
    os.chmod(key_path, 0o600)
    try:
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_path],
            input=signing_input,
            capture_output=True,
            check=True,
        )
    finally:
        try:
            os.unlink(key_path)
        except OSError:
            pass
    jwt = signing_input + b"." + b64u(proc.stdout)
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt.decode(),
    }).encode()
    req = urllib.request.Request(
        sa["token_uri"],
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["access_token"], sa["client_email"]


def oauth_access_token(token_path):
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
        return json.loads(r.read())["access_token"], "(user OAuth)"


def get_access_token():
    sa = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if sa:
        return sa_access_token(sa)
    oauth = os.environ.get("OAUTH_TOKEN_JSON")
    if oauth:
        return oauth_access_token(oauth)
    raise SystemExit(
        "Set GOOGLE_APPLICATION_CREDENTIALS or OAUTH_TOKEN_JSON. See module docstring."
    )


def load_rows(csv_paths):
    header = None
    rows = []
    for p in csv_paths:
        with open(p, newline="") as f:
            r = csv.reader(f)
            this_header = next(r)
            if header is None:
                header = this_header
            elif this_header != header:
                raise SystemExit(f"header mismatch in {p}")
            rows.extend(r)
    return header, rows


def append(access, rows):
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
            "Authorization": f"Bearer {access}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        print(f"HTTP {e.code}: {msg}", file=sys.stderr)
        if e.code == 404:
            print(
                "\n404 = the auth principal can't see the sheet. For an SA, "
                "share the sheet with the SA's client_email as Editor. For "
                "OAuth drive.file, open the sheet in the matching browser "
                "session first.",
                file=sys.stderr,
            )
        raise


def main():
    csv_paths = sys.argv[1:] or DEFAULT_CSVS
    header, rows = load_rows(csv_paths)
    print(f"Loaded {len(rows)} rows from {len(csv_paths)} CSV(s); header has {len(header)} columns")
    access, principal = get_access_token()
    print(f"Auth OK ({principal})")
    result = append(access, rows)
    u = result.get("updates", {})
    print(
        f"Appended: range={u.get('updatedRange')}  "
        f"rows={u.get('updatedRows')}  cells={u.get('updatedCells')}"
    )


if __name__ == "__main__":
    main()
