"""One-off / occasional importer: pull every article in a Shopify blog
into breed-data/<slug>.json so seo_autofix can manage them.

Usage:
    python3 scripts/import_blog.py dog-nutrition
    python3 scripts/import_blog.py dog-training

Writes a passthrough-mode JSON for each article (raw body_html is kept
verbatim; generate.py will ship it back to Shopify unchanged unless
SEO meta fields are edited). Existing files are overwritten.

Reads SHOPIFY_STORE + SHOPIFY_TOKEN from .env. The token must have
read_content / read_articles scopes (the existing publish token does).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parent.parent
BREED_DIR: Path = ROOT / "breed-data"
ENV_PATH: Path = ROOT / ".env"

API_VERSION: str = "2024-01"

# Hardcoded blog handle -> id map (looked up via Admin GraphQL once).
# Extend as new blogs are nominated.
BLOG_IDS: dict[str, int] = {
    "dog-breeds": 81943265334,
    "dog-nutrition": 81942970422,
    "dog-training": 81943232566,
    "life-with-dogs": 78648574006,
    "dog-health": 81943363638,
}


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


def api_get(store: str, token: str, path: str) -> dict:
    url = f"https://{store}/admin/api/{API_VERSION}{path}"
    req = urllib.request.Request(url)
    req.add_header("X-Shopify-Access-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Shopify API {e.code} on {url}: {e.read().decode()[:300]}")


def html_to_text(html: str, limit: int = 250) -> str:
    text = re.sub(r"<[^>]+>", "", html or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def build_record(article: dict, metafields: dict[str, str],
                 blog_handle: str) -> dict:
    handle = article["handle"]
    title = article["title"]
    body_html = article.get("body_html") or ""
    summary_html = article.get("summary_html") or ""
    tags_raw = article.get("tags") or ""
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    image = article.get("image") or {}

    return {
        "meta": {
            "blog_handle": blog_handle,
            "shopify_handle": handle,
            "shopify_article_id": str(article["id"]),
            "name": title,
            "title_tag": metafields.get("title_tag", "").strip(),
            "slug": handle,
            "excerpt": html_to_text(summary_html),
            "meta_description": metafields.get("description_tag", "").strip(),
            "tags": tags,
            "published": bool(article.get("published_at")),
            "published_at": article.get("published_at"),
        },
        "images": {
            "hero": {
                "url": image.get("src") or "",
                "alt": image.get("alt") or title,
            },
        },
        "body_html": body_html,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.exit("Usage: python3 scripts/import_blog.py <blog-handle>")
    blog_handle = argv[1].strip()
    if blog_handle not in BLOG_IDS:
        sys.exit(f"Unknown blog handle {blog_handle!r}. "
                 f"Known: {sorted(BLOG_IDS)}")
    blog_id = BLOG_IDS[blog_handle]

    env = load_env(ENV_PATH)
    store = env.get("SHOPIFY_STORE")
    token = env.get("SHOPIFY_TOKEN")
    if not store or not token:
        sys.exit("SHOPIFY_STORE / SHOPIFY_TOKEN missing from .env")

    BREED_DIR.mkdir(exist_ok=True)
    print(f"Importing blog {blog_handle!r} (id={blog_id}) "
          f"from {store} ...")

    fields = "id,handle,title,summary_html,body_html,published_at,tags,image"
    data = api_get(store, token,
                   f"/blogs/{blog_id}/articles.json?limit=250&fields={fields}")
    articles = data.get("articles", [])
    print(f"  fetched {len(articles)} articles")

    for art in articles:
        mf_resp = api_get(store, token,
                          f"/articles/{art['id']}/metafields.json"
                          f"?namespace=global")
        metafields = {m["key"]: m.get("value", "")
                      for m in mf_resp.get("metafields", [])}

        record = build_record(art, metafields, blog_handle)
        out_path = BREED_DIR / f"{art['handle']}.json"
        out_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        title_tag_len = len(metafields.get("title_tag", ""))
        desc_len = len(metafields.get("description_tag", ""))
        body_len = len(record["body_html"])
        print(f"  wrote breed-data/{out_path.name}  "
              f"(body {body_len}B · title_tag {title_tag_len}c · "
              f"meta_desc {desc_len}c)")

    print(f"Done. {len(articles)} files in {BREED_DIR}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
