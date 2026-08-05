"""Build (or rebuild) lightweight hub pages for the small blogs:
dog-health, dog-training, life-with-dogs.

Fetches each blog's LIVE article list from Shopify, groups articles by
keyword rules (first match wins; unmatched fall into the last group), and
writes a hub article JSON per blog. Rerun any time articles are added:

    python scripts/build_blog_hub_pages.py
    echo YES | python scripts/generate.py dog-health-guides dog-training-guides life-with-dogs-guides --update
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
BD = os.path.join(ROOT, "breed-data")
HERO_SEED = os.path.join(
    "C:/Users/kailu/AppData/Local/Temp/claude/C--Users-kailu",
    "e909ce54-ab0a-40e7-acc8-539b75b3b0c8/scratchpad/hub_heroes.json",
)


def load_env() -> dict:
    env = {}
    with open(os.path.join(ROOT, ".env"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


# blog_handle -> hub config. groups = [(title, [keywords...]), ...];
# an empty keyword list is the catch-all and must come last.
HUBS = {
    "dog-health": {
        "blog_id_env": "SHOPIFY_DOG_HEALTH_BLOG_ID",
        "slug": "dog-health-guides",
        "hero_key": "dog-health-hub",
        "name": "Dog Health Guides: Start Here",
        "title_tag": "Dog Health Guides: Care, Puppies & More",
        "excerpt": "All Wooffy dog health guides in one place — a growing library on keeping your dog healthy.",
        "meta_description": ("Browse every Wooffy dog health guide in one place — daily care, "
                             "puppy health, and more. A growing, vet-informed library."),
        "intro": ("Everything we have published on keeping your dog healthy, in one place. "
                  "This library is growing &mdash; check back for new guides."),
        "groups": [("All Health Guides", [])],
    },
    "dog-training": {
        "blog_id_env": "SHOPIFY_DOG_TRAINING_BLOG_ID",
        "slug": "dog-training-guides",
        "hero_key": "dog-training-hub",
        "name": "Dog Training Guides: Start Here",
        "title_tag": "Dog Training Guides: Crates, Puppies & More",
        "excerpt": "All Wooffy dog training guides in one place — crate training, puppy behavior, and enrichment.",
        "meta_description": ("Browse every Wooffy dog training guide — crate training from 101 to "
                             "separation anxiety, puppy behavior fixes, and indoor enrichment ideas."),
        "intro": ("Every training guide we have published, organized so you can start in the "
                  "right place &mdash; from crate training basics to puppy behavior fixes."),
        "groups": [
            ("Crate Training", ["crate"]),
            ("Puppy & Behavior", ["puppy", "potty", "peeing", "behavior", "anxiety"]),
            ("Activities & Enrichment", []),
        ],
    },
    "life-with-dogs": {
        "blog_id_env": "SHOPIFY_LIFE_WITH_DOGS_BLOG_ID",
        "slug": "life-with-dogs-guides",
        "hero_key": "life-with-dogs-hub",
        "name": "Life with Dogs: Start Here",
        "title_tag": "Life with Dogs: Names, Homes & Lifestyle",
        "excerpt": "All Wooffy lifestyle guides in one place — dog names, modern dog houses, and living well with your dog.",
        "meta_description": ("Browse every Wooffy life-with-dogs guide — dog name ideas, modern "
                             "indoor dog houses and crates, and tips for living well with your dog."),
        "intro": ("Stories and guides about sharing your home and life with a dog &mdash; "
                  "from picking a name to designing a dog-friendly modern home."),
        "groups": [
            ("Dog Names", ["names"]),
            ("Places to Go: Parks, Hikes & Beaches", ["park", "hike", "beach", "trail"]),
            ("Home, Crates & Dog Houses", ["house", "crate", "kennel", "indoor dog"]),
            ("Lifestyle & Family", []),
        ],
    },
}


def fetch_articles(store: str, token: str, blog_id: str) -> list[dict]:
    url = (f"https://{store}/admin/api/2024-01/blogs/{blog_id}/articles.json"
           f"?limit=250&fields=title,handle,published_at")
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
    data = json.load(urllib.request.urlopen(req))
    return [a for a in data["articles"] if a.get("published_at")]


def build_hub(handle: str, cfg: dict, arts: list[dict], hero) -> str:
    hub_slug = cfg["slug"]
    arts = [a for a in arts if a["handle"] != hub_slug]
    grouped: dict[str, list] = {t: [] for t, _ in cfg["groups"]}
    for a in arts:
        low = a["title"].lower()
        for title, kws in cfg["groups"]:
            if not kws or any(k in low for k in kws):
                grouped[title].append(a)
                break
    sections = []
    for title, _ in cfg["groups"]:
        items = grouped[title]
        if not items:
            continue
        rows = "".join(
            f'<a class="wfy-breed" href="/blogs/{handle}/{a["handle"]}">'
            f'<span class="wfy-bname">{a["title"]}</span></a>'
            for a in sorted(items, key=lambda x: x["title"]))
        sections.append(f'<h2 class="wfy-letter">{title} '
                        f'<span class="wfy-secn">{len(items)}</span></h2>'
                        f'<div class="wfy-grid">{rows}</div>')

    body = f"""<meta charset="utf-8">
<style>
.wfy-intro {{ background:#141412; color:#EDEAE2; text-align:center; padding:32px 22px 36px; margin:0 0 24px; }}
.wfy-intro .wfy-count {{ font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:#CFCBC2; margin:0 auto 14px; }}
.wfy-intro p {{ max-width:62ch; margin:0 auto; font-size:15.5px; line-height:1.65; color:#EDEAE2; }}
.wfy-letter {{ border-top:1px solid #E6E2D8; padding-top:22px; margin:24px 0 10px; }}
.wfy-secn {{ font-size:12px; color:#6F6A61; margin-left:6px; }}
.wfy-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:0 30px; }}
.wfy-breed {{ display:flex; padding:10px 2px; border-bottom:1px solid #E6E2D8;
  text-decoration:none; color:#1A1A1A; transition:color .13s ease; }}
.wfy-breed:hover {{ color:#E4572E; }}
.wfy-bname {{ font-size:15.5px; line-height:1.45; text-decoration:underline;
  text-decoration-color:#D9D4C8; text-underline-offset:3px; text-decoration-thickness:1px;
  transition:text-decoration-color .13s ease; }}
.wfy-breed:hover .wfy-bname {{ text-decoration-color:#E4572E; }}
@media (max-width:700px) {{ .wfy-grid {{ grid-template-columns:1fr; }} }}
</style>
<div class="wfy-intro">
<p class="wfy-count">{len(arts)} guides &middot; growing library</p>
<p>{cfg["intro"]}</p>
</div>
{"".join(sections)}
<p style="margin-top:32px;">You may also like the
<a href="/blogs/dog-breeds/dog-breeds-a-z">Dog Breeds A&ndash;Z directory</a> and the
<a href="/blogs/dog-nutrition/what-can-dogs-eat">What Can Dogs Eat? food guide</a>.</p>
"""
    article = {
        "meta": {
            "blog_handle": handle,
            "shopify_handle": hub_slug, "slug": hub_slug,
            "name": cfg["name"],
            "title_tag": cfg["title_tag"],
            "excerpt": cfg["excerpt"],
            "meta_description": cfg["meta_description"],
            "tags": ["directory"],
            "published": True,
            "published_at": "2026-07-16T12:00:00Z",
        },
        "images": {"hero": hero} if hero else {},
        "body_html": body,
    }
    assert len(cfg["title_tag"]) <= 51, f"{hub_slug}: title_tag > 51"
    out = os.path.join(BD, f"{hub_slug}.json")
    json.dump(article, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{hub_slug}: {len(arts)} articles, hero={'Y' if hero else 'NONE'}"


def main() -> int:
    sys.stderr.reconfigure(encoding="utf-8")
    env = load_env()
    store, token = env.get("SHOPIFY_STORE", ""), env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")
    seed = json.load(open(HERO_SEED, encoding="utf-8")) if os.path.exists(HERO_SEED) else {}

    for handle, cfg in HUBS.items():
        blog_id = env.get(cfg["blog_id_env"], "")
        if not blog_id:
            print(f"[{handle}] SKIP: {cfg['blog_id_env']} not in .env", file=sys.stderr)
            continue
        arts = fetch_articles(store, token, blog_id)
        out = os.path.join(BD, f"{cfg['slug']}.json")
        hero = None
        if os.path.exists(out):
            hero = json.load(open(out, encoding="utf-8")).get("images", {}).get("hero")
        if not hero:
            hero = seed.get(cfg["hero_key"])
        print("[ok]", build_hub(handle, cfg, arts, hero), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
