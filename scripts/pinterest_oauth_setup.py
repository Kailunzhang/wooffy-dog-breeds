"""One-time Pinterest OAuth flow to obtain refresh_token.

Uses a local HTTP server to auto-capture the OAuth callback - no manual
URL copy-paste needed. Same pattern as ``gcloud auth login`` and ``gh
auth login``.

Prerequisite: Pinterest Developer App created at
https://developers.pinterest.com/apps/ with:
  - Redirect URI: http://localhost:8765/callback
    (Pinterest allows http+localhost; the port matters and must match
    exactly.)
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
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"

CALLBACK_HOST = "localhost"
CALLBACK_PORT = 8765
CALLBACK_PATH = "/callback"
REDIRECT_URI = f"http://{CALLBACK_HOST}:{CALLBACK_PORT}{CALLBACK_PATH}"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"
TOKEN_ENDPOINT = "https://api.pinterest.com/v5/oauth/token"
STATE = "wooffy-pinterest-setup"


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if not ENV_PATH.exists():
        sys.exit(
            f".env not found at {ENV_PATH}. Create one with PINTEREST_APP_ID "
            f"and PINTEREST_APP_SECRET first."
        )
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def write_env_keys(updates: dict[str, str]) -> None:
    """Append or update keys in .env (preserves other lines)."""
    existing_lines = (
        ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    )
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
        "state": STATE,
    }
    return "https://www.pinterest.com/oauth/?" + urllib.parse.urlencode(params)


SUCCESS_HTML = b"""<!doctype html>
<html><head><meta charset="utf-8"><title>Pinterest OAuth - Success</title>
<style>
body { font-family: -apple-system, system-ui, sans-serif; max-width: 560px;
       margin: 80px auto; padding: 0 24px; color: #1a1a1a; }
h1 { font-size: 24px; }
p { font-size: 16px; line-height: 1.6; color: #444; }
code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
</style></head>
<body>
<h1>Pinterest authorization captured</h1>
<p>You can close this tab. The terminal will continue automatically.</p>
</body></html>
"""

ERROR_HTML = b"""<!doctype html>
<html><head><meta charset="utf-8"><title>Pinterest OAuth - Error</title></head>
<body><h1>Authorization failed</h1>
<p>The callback URL did not contain a code parameter. Check the terminal
for details and re-run the script.</p></body></html>
"""


class CallbackHandler(BaseHTTPRequestHandler):
    """Captures the single OAuth callback request."""

    captured_code: Optional[str] = None
    captured_error: Optional[str] = None

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]
        if code:
            CallbackHandler.captured_code = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(SUCCESS_HTML)))
            self.end_headers()
            self.wfile.write(SUCCESS_HTML)
        else:
            CallbackHandler.captured_error = error or "no-code"
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(ERROR_HTML)))
            self.end_headers()
            self.wfile.write(ERROR_HTML)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass  # suppress default access log


def wait_for_callback() -> str:
    """Bind localhost:CALLBACK_PORT, serve one request, return the code."""
    try:
        server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), CallbackHandler)
    except OSError as exc:
        sys.exit(
            f"Cannot bind {CALLBACK_HOST}:{CALLBACK_PORT}: {exc}\n"
            f"Another process is using this port. Stop it (or change "
            f"CALLBACK_PORT in this script + update Pinterest App redirect "
            f"URI to match)."
        )
    print(f"Local callback server listening on {REDIRECT_URI}")
    print("Waiting for Pinterest to redirect after you click 'Connect'...")
    while (
        CallbackHandler.captured_code is None
        and CallbackHandler.captured_error is None
    ):
        server.handle_request()
    server.server_close()
    if CallbackHandler.captured_error is not None:
        sys.exit(f"OAuth callback returned error: {CallbackHandler.captured_error}")
    assert CallbackHandler.captured_code is not None
    return CallbackHandler.captured_code


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
            f"Common causes: wrong redirect URI (must match Pinterest App "
            f"settings EXACTLY, including port), code already used (re-run), "
            f"or expired code (use within 5 min)."
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
    print("Pinterest OAuth - one-time setup")
    print("=" * 70)
    print()
    print("Required Pinterest App redirect URI (must match exactly):")
    print(f"  {REDIRECT_URI}")
    print()
    print("Opening this URL in your default browser:")
    print(f"  {auth_url}")
    print()
    print("If the browser does NOT open automatically, copy the URL above")
    print("and open it manually. Make sure you are logged in to the right")
    print("Pinterest Business account first.")
    print()
    print("After you click 'Connect' on the Pinterest page, the browser")
    print("will redirect back here automatically - no copy-paste needed.")
    print("=" * 70)
    print()

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    code = wait_for_callback()
    print(f"Captured code: {code[:12]}...")
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
    print("  2. python3 scripts/pinterest_api.py publish --batch=3  # posts 3 pins")
    print("  3. Add PINTEREST_APP_ID, PINTEREST_APP_SECRET, PINTEREST_REFRESH_TOKEN")
    print("     as GitHub Repository Secrets so the daily cron runs unattended.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
