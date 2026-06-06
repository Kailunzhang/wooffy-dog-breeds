"""One-off: add a <meta name="robots" content="noindex,follow"> tag to
the /blogs/dog-nutrition index page via a surgical edit to
layout/theme.liquid. SEO task: stop the nutrition blog index page from
cannibalizing the can-dogs-eat-eggplant article (GSC view 14 showed
both URLs ranking for the same query, the index at pos 39.9 stealing
~16% of the query's impressions from the article at pos 15.8).

Idempotent: detects whether the conditional block is already present
(via a unique marker string) and no-ops on re-run.

The edit is a 4-line conditional inserted right after the canonical
link in the head section. Only the /blogs/dog-nutrition index URL
becomes noindex -- all nutrition articles (incl. the eggplant one)
stay fully indexable because `template == 'blog'` only matches the
blog index template, not 'article'.

Usage:
    python3 scripts/add_noindex_nutrition_blog.py           # dry-run
    python3 scripts/add_noindex_nutrition_blog.py --apply   # push via GraphQL
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parent.parent
ENV_PATH: Path = ROOT / ".env"
API_VERSION = "2024-10"
THEME_GID = "gid://shopify/OnlineStoreTheme/151012311094"
TARGET_FILENAME = "layout/theme.liquid"

# Marker uniquely identifies the inserted block (used for idempotency).
INSERT_MARKER = "SEO: noindex thin blog index pages that cannibalize their articles"

# The surgical insertion. Goes immediately after the canonical link.
INSERT_BLOCK = (
    "\n"
    "    {%- comment -%} SEO: noindex thin blog index pages that "
    "cannibalize their articles {%- endcomment -%}\n"
    "    {%- if template == 'blog' and blog.handle == 'dog-nutrition' -%}\n"
    "      <meta name=\"robots\" content=\"noindex,follow\">\n"
    "    {%- endif -%}\n"
)

# Anchor we splice after. Must appear exactly once in the file.
ANCHOR = '    <link rel="canonical" href="{{ canonical_url }}">\n'


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def gql(store: str, token: str, query: str,
        variables: dict | None = None) -> dict:
    url = f"https://{store}/admin/api/{API_VERSION}/graphql.json"
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("X-Shopify-Access-Token", token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Shopify GraphQL {e.code}: {e.read().decode()[:400]}")
    if "errors" in body and body["errors"]:
        sys.exit(f"GraphQL errors: {json.dumps(body['errors'])[:600]}")
    return body["data"]


FETCH_QUERY = """
query($id: ID!) {
  theme(id: $id) {
    id
    name
    role
    files(filenames: ["layout/theme.liquid"], first: 1) {
      nodes {
        filename
        size
        body { ... on OnlineStoreThemeFileBodyText { content } }
      }
    }
  }
}
"""

UPSERT_MUTATION = """
mutation($themeId: ID!, $files: [OnlineStoreThemeFilesUpsertFileInput!]!) {
  themeFilesUpsert(themeId: $themeId, files: $files) {
    upsertedThemeFiles { filename size }
    userErrors { code field message }
  }
}
"""


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    env = load_env(ENV_PATH)
    store = env.get("SHOPIFY_STORE")
    token = env.get("SHOPIFY_TOKEN")
    if not store or not token:
        sys.exit("SHOPIFY_STORE / SHOPIFY_TOKEN missing in .env")

    mode = "APPLY (will push via GraphQL)" if apply else "DRY-RUN (no writes)"
    print(f"Mode: {mode}\n")

    data = gql(store, token, FETCH_QUERY, {"id": THEME_GID})
    theme = data["theme"]
    if theme is None:
        sys.exit(f"Theme {THEME_GID} not found")
    nodes = theme["files"]["nodes"]
    if not nodes:
        sys.exit(f"{TARGET_FILENAME} not present in theme")
    file_node = nodes[0]
    original = file_node["body"]["content"]
    old_len = len(original)

    print(f"Theme: {theme['name']} ({theme['role']})")
    print(f"File:  {TARGET_FILENAME}  ({old_len} chars)")

    if INSERT_MARKER in original:
        print("\nNoindex block already present -- no-op (idempotent).")
        return 0

    if original.count(ANCHOR) != 1:
        sys.exit(
            f"\nERROR: anchor line not found exactly once "
            f"(found {original.count(ANCHOR)} times). "
            f"Theme structure may have changed; aborting to avoid "
            f"corrupting the file."
        )

    new_content = original.replace(ANCHOR, ANCHOR + INSERT_BLOCK, 1)
    new_len = len(new_content)
    delta = new_len - old_len
    print(f"\nDelta: +{delta} chars (new size: {new_len})")
    print("\nInserted block (after the canonical link):")
    print("-" * 60)
    print(INSERT_BLOCK)
    print("-" * 60)

    if not apply:
        print("\nDRY-RUN done. Re-run with --apply to push.")
        return 0

    variables = {
        "themeId": THEME_GID,
        "files": [{
            "filename": TARGET_FILENAME,
            "body": {"type": "TEXT", "value": new_content},
        }],
    }
    result = gql(store, token, UPSERT_MUTATION, variables)
    upsert = result["themeFilesUpsert"]
    if upsert["userErrors"]:
        sys.exit(f"\nuserErrors: {json.dumps(upsert['userErrors'])}")
    pushed = upsert["upsertedThemeFiles"]
    print(f"\nPUSHED. Server confirms: {json.dumps(pushed)}")
    print(
        "\nNext: verify by curling the live URL after the CDN propagates:\n"
        "  curl -sL https://thewooffy.com/blogs/dog-nutrition | "
        "grep -i 'noindex'"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
