"""One-time Pinterest OAuth flow to obtain refresh_token.

Prerequisite: Pinterest Developer App created at
https://developers.pinterest.com/apps/ with:
  - Redirect URI: https://thewooffy.com/?pinterest-auth=1
  - Scopes requested (during user grant): boards:read, boards:write,
                                          pins:read, pins:write,
                                          user_accounts:read

The .env must contain PINTEREST_APP_ID and PINTEREST_APP_SECRET BEFORE
running this script. After running, the script appends/updates
PINTEREST_REFRESH_TOKEN and PINTEREST_ACCESS_TOKEN in .env.

Run:
    python3 scripts/pinterest_oauth_setup.py
"""
from __future__ import annotations

import base64
import re
import sys
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"

REDIRECT_URI = "https://thewooffy.com/?pinterest-auth=1"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"
TOKEN_ENDPOINT = "https://api.pinterest.com/v5/oauth/token"


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if not ENV_PATH.exists():
        sys.exit(f".env not found at {ENV_PATH}. Create one with PINTEREST_APP_ID and PINTEREST_APP_SECRET first.")
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def write_env_keys(updates: dict[str, str]) -> None:
    """Append or update keys in .env (preserves other lines)."""
    existing_lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    keys_to_update = set(updates.keys())
    new_lines: list[str] = []
    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        k = stripped.split("=", 1)[0].strip()
        if k in keys_to_update:
            new_lines.append(f"{k}={updates[k]}")
            keys_to_update.discard(k)
        else:
            new_lines.append(line)
    for k in keys_to_update:
        new_lines.append(f"{k}={updates[k]}")
    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def build_auth_url(app_id: str) -> str:
    params = {
        "client_id": app_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": "wooffy-pinterest-setup",
    }
    return "https://www.pinterest.com/oauth/?" + urllib.parse.urlencode(params)


def extract_code(pasted: str) -> str | None:
    match = re.search(r"[?&]code=([^&\s]+)", pasted)
    return urllib.parse.unquote(match.group(1)) if match else None


def exchange_code(app_id: str, app_secret: str, code: str) -> dict:
    basic = base64.b64encode(f"{app_id}:{app_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    resp = requests.post(TOKEN_ENDPOINT, headers=headers, data=data, timeout=30)
    if resp.status_code != 200:
        sys.exit(
            f"Token exchange failed (HTTP {resp.status_code}):\n  {resp.text}\n"
            f"Common causes: wrong redirect URI (must match Pinterest App settings exactly), "
            f"code already used (re-run from auth URL), expired code (use within 5 min)."
        )
    return resp.json()


def main() -> int:
    env = load_env()
    app_id = env.get("PINTEREST_APP_ID")
    app_secret = env.get("PINTEREST_APP_SECRET")
    if not app_id or not app_secret:
        sys.exit(
            "Missing PINTEREST_APP_ID or PINTEREST_APP_SECRET in .env.\n\n"
            "Pinterest Developer App setup checklist:\n"
            "  1. Go to https://developers.pinterest.com/apps/ and create an app.\n"
            "  2. App settings:\n"
            f"       Redirect URI: {REDIRECT_URI}\n"
            f"       Requested scopes: {SCOPES}\n"
            "  3. Copy the app_id and app_secret from the app dashboard.\n"
            "  4. Add to .env:\n"
            "       PINTEREST_APP_ID=...\n"
            "       PINTEREST_APP_SECRET=...\n"
            "  5. Re-run this script."
        )

    auth_url = build_auth_url(app_id)
    print()
    print("=" * 70)
    print("STEP 1 - Open this URL in your browser (already-logged-into-Pinterest):")
    print("=" * 70)
    print()
    print(auth_url)
    print()
    print("=" * 70)
    print("STEP 2 - Click 'Connect' to grant access.")
    print("Pinterest will redirect to:")
    print(f"    {REDIRECT_URI}&code=XXXXXX&state=wooffy-pinterest-setup")
    print()
    print("STEP 3 - Copy the FULL URL from your browser address bar")
    print("(the page may 404, that is fine; the code is in the URL).")
    print("Then paste it below and press Enter:")
    print("=" * 70)
    print()
    pasted = input("Paste redirect URL: ").strip()
    code = extract_code(pasted)
    if not code:
        sys.exit("Could not find ?code=... in the pasted URL. Re-run the script.")
    print(f"Extracted code: {code[:12]}...")
    print()
    print("Exchanging code for tokens...")
    tokens = exchange_code(app_id, app_secret, code)

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in", "?")
    refresh_expires_in = tokens.get("refresh_token_expires_in", "?")
    if not access_token or not refresh_token:
        sys.exit(f"Token response missing expected fields: {tokens}")

    write_env_keys({
        "PINTEREST_ACCESS_TOKEN": access_token,
        "PINTEREST_REFRESH_TOKEN": refresh_token,
    })
    print()
    print("Success.")
    if str(expires_in).isdigit():
        print(f"  Access token expires in:  {expires_in}s (~{int(expires_in)/86400:.1f} days)")
    else:
        print(f"  Access token expires in:  {expires_in}")
    if str(refresh_expires_in).isdigit():
        print(f"  Refresh token expires in: {refresh_expires_in}s (~{int(refresh_expires_in)/86400:.1f} days)")
    else:
        print(f"  Refresh token expires in: {refresh_expires_in}")
    print(f"  Written to: {ENV_PATH}")
    print()
    print("Next steps:")
    print("  1. python3 scripts/pinterest_api.py setup-boards     # creates 8 boards + saves IDs")
    print("  2. python3 scripts/pinterest_api.py publish --batch=3  # dry-run, posts 3 pins")
    print("  3. Add PINTEREST_APP_ID, PINTEREST_APP_SECRET, PINTEREST_REFRESH_TOKEN")
    print("     as GitHub Repository Secrets (Settings > Secrets and variables > Actions)")
    print("     so the daily cron workflow can run unattended.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
