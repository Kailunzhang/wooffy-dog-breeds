#!/usr/bin/env python3
"""
One-time script to obtain a Shopify offline access token via OAuth Authorization Code Grant.
Run once, then the token is written to .env as SHOPIFY_TOKEN.
"""

import json
import os
import re
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SHOP = "thewooffy.myshopify.com"
CLIENT_ID = "9c49670f7a0d9375c7d6fc31a47b8e80"
SCOPES = "write_content,read_content,write_files,read_files"
REDIRECT_URI = "http://localhost:8000/callback"
PORT = 8000
ENV_FILE = Path(__file__).parent.parent / ".env"

# ---------------------------------------------------------------------------
# Load client secret from .env
# ---------------------------------------------------------------------------
def load_env(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def update_env(path: Path, key: str, value: str) -> None:
    """Insert or replace a key=value line in the .env file."""
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    new_line = f"{key}={value}"
    if pattern.search(content):
        content = pattern.sub(new_line, content)
    else:
        if content and not content.endswith("\n"):
            content += "\n"
        content += new_line + "\n"
    path.write_text(content, encoding="utf-8")

# ---------------------------------------------------------------------------
# OAuth flow state (shared with HTTP handler via closure)
# ---------------------------------------------------------------------------
_state = secrets.token_urlsafe(32)
_result: dict = {}  # filled by the callback handler
_client_secret: str = ""


class CallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default access logs

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self._respond(404, "Not found")
            return

        params = urllib.parse.parse_qs(parsed.query)

        # --- error from Shopify ---
        if "error" in params:
            error = params["error"][0]
            desc = params.get("error_description", ["(no description)"])[0]
            self._respond(400, f"<h2>Error from Shopify</h2><pre>{error}: {desc}</pre>")
            _result["error"] = f"{error}: {desc}"
            self._shutdown()
            return

        # --- state validation ---
        got_state = params.get("state", [None])[0]
        if got_state != _state:
            self._respond(400, "<h2>State mismatch — possible CSRF</h2>")
            _result["error"] = "state mismatch"
            self._shutdown()
            return

        code = params.get("code", [None])[0]
        if not code:
            self._respond(400, "<h2>Missing code parameter</h2>")
            _result["error"] = "missing code"
            self._shutdown()
            return

        # --- exchange code for token ---
        token_url = f"https://{SHOP}/admin/oauth/access_token"
        payload = json.dumps({
            "client_id": CLIENT_ID,
            "client_secret": _client_secret,
            "code": code,
        }).encode()
        req = urllib.request.Request(
            token_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            self._respond(500, f"<h2>Token exchange failed ({e.code})</h2><pre>{body}</pre>")
            _result["error"] = f"HTTP {e.code}: {body}"
            self._shutdown()
            return

        if "access_token" not in data:
            self._respond(500, f"<h2>Unexpected response</h2><pre>{json.dumps(data, indent=2)}</pre>")
            _result["error"] = json.dumps(data)
            self._shutdown()
            return

        _result["access_token"] = data["access_token"]
        _result["scope"] = data.get("scope", "")
        _result["token_type"] = data.get("token_type", "")

        self._respond(
            200,
            """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.box{text-align:center;padding:2rem;border-radius:8px;background:#f0fdf4;border:1px solid #86efac}</style>
</head><body>
<div class="box">
  <div style="font-size:3rem">✅</div>
  <h2 style="color:#15803d">授权成功</h2>
  <p>Access token 已写入 <code>.env</code>,可以关闭此页面。</p>
</div>
</body></html>""",
        )
        self._shutdown()

    def _respond(self, code: int, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _shutdown(self):
        # Schedule server shutdown from a new thread so the response is sent first
        import threading
        threading.Timer(0.5, self.server.shutdown).start()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global _client_secret

    env = load_env(ENV_FILE)
    _client_secret = env.get("SHOPIFY_CLIENT_SECRET", "")
    if not _client_secret:
        print(
            f"[ERROR] SHOPIFY_CLIENT_SECRET not found in {ENV_FILE}\n"
            "Please add it first:\n  SHOPIFY_CLIENT_SECRET=your_secret_here",
            file=sys.stderr,
        )
        sys.exit(1)

    # Build authorization URL
    auth_params = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": _state,
    })
    auth_url = f"https://{SHOP}/admin/oauth/authorize?{auth_params}"

    print(f"[*] Starting local server on http://localhost:{PORT}")
    print(f"[*] Opening browser for Shopify authorization...")
    print(f"    If the browser doesn't open, visit:\n    {auth_url}\n")

    server = HTTPServer(("localhost", PORT), CallbackHandler)
    webbrowser.open(auth_url)

    # Serve until the callback shuts it down
    server.serve_forever()

    # --- handle result ---
    if "error" in _result:
        print(f"\n[ERROR] {_result['error']}", file=sys.stderr)
        sys.exit(1)

    token = _result["access_token"]
    update_env(ENV_FILE, "SHOPIFY_TOKEN", token)
    print(f"[✓] Access token obtained!")
    print(f"    Scope   : {_result['scope']}")
    print(f"    Written to: {ENV_FILE}")


if __name__ == "__main__":
    main()
