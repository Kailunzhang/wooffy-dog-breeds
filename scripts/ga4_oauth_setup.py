"""One-time helper: get a long-lived GA4 OAuth refresh token.

Run locally once:

    python3 scripts/ga4_oauth_setup.py path/to/oauth_client.json

It opens a browser, you sign in as the GA4 admin account and approve,
then it prints GA4_OAUTH_CLIENT_ID / GA4_OAUTH_CLIENT_SECRET /
GA4_OAUTH_REFRESH_TOKEN to paste into GitHub secrets. Nothing is saved.
"""

import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit("Install the helper dep first:\n"
             "  python3 -m pip install --user google-auth-oauthlib")

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
]


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 scripts/ga4_oauth_setup.py <oauth_client.json>")
    client_file = sys.argv[1]
    flow = InstalledAppFlow.from_client_secrets_file(client_file, SCOPES)
    creds = flow.run_local_server(
        port=0, access_type="offline", prompt="consent"
    )
    if not creds.refresh_token:
        sys.exit("No refresh token returned. Re-run; ensure you approve the "
                 "consent screen fully.")
    print("\n=== Copy these into GitHub repo secrets ===\n")
    print(f"GA4_OAUTH_CLIENT_ID={creds.client_id}")
    print(f"GA4_OAUTH_CLIENT_SECRET={creds.client_secret}")
    print(f"GA4_OAUTH_REFRESH_TOKEN={creds.refresh_token}")
    print("\n(Keep these private - they grant read access to your GA4.)")


if __name__ == "__main__":
    main()
