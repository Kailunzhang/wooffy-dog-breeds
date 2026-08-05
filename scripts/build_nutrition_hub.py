"""Build (or rebuild) the "What Can Dogs Eat?" pillar page for /blogs/dog-nutrition.

Reads every dog-nutrition article in breed-data/, pulls each food's verdict
one-liner from its own Quick Answer (no fabrication), and renders a grouped,
badge-annotated directory: NEVER-FEED callout + category sections.

Rerun whenever foods are added:
    python scripts/build_nutrition_hub.py            # rebuild JSON
    echo YES | python scripts/generate.py what-can-dogs-eat --update

New foods missing from FOODS below land in a "New additions" section and are
listed on stderr so the table gets curated.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
BD = os.path.join(ROOT, "breed-data")
HUB_SLUG = "what-can-dogs-eat"
HERO_SEED = os.path.join(
    "C:/Users/kailu/AppData/Local/Temp/claude/C--Users-kailu",
    "e909ce54-ab0a-40e7-acc8-539b75b3b0c8/scratchpad/hub_heroes.json",
)

SAFE, LIMIT, AVOID = "safe", "limit", "avoid"
BADGE = {SAFE: ("&#9989;", "Safe"), LIMIT: ("&#9888;&#65039;", "Limit"),
         AVOID: ("&#128683;", "Avoid")}

# slug -> (display name, category, badge). Curated 2026-07-16.
FOODS = {
    # Fruits
    "can-dogs-eat-apples": ("Apples", "Fruits", SAFE),
    "can-dogs-eat-bananas": ("Bananas", "Fruits", SAFE),
    "can-dogs-eat-blueberries": ("Blueberries", "Fruits", SAFE),
    "can-dogs-eat-cantaloupe": ("Cantaloupe", "Fruits", SAFE),
    "can-dogs-eat-cherries": ("Cherries", "Fruits", AVOID),
    "can-dogs-eat-cranberries": ("Cranberries", "Fruits", SAFE),
    "can-dogs-eat-grapes": ("Grapes & Raisins", "Fruits", AVOID),
    "can-dogs-eat-mango": ("Mango", "Fruits", SAFE),
    "can-dogs-eat-oranges": ("Oranges", "Fruits", SAFE),
    "can-dogs-eat-peaches": ("Peaches", "Fruits", SAFE),
    "can-dogs-eat-pineapple": ("Pineapple", "Fruits", SAFE),
    "can-dogs-eat-raspberries": ("Raspberries", "Fruits", SAFE),
    "can-dogs-eat-strawberries": ("Strawberries", "Fruits", SAFE),
    "can-dogs-eat-watermelon": ("Watermelon", "Fruits", SAFE),
    "can-dogs-eat-avocado": ("Avocado", "Fruits", AVOID),
    "can-dogs-eat-coconut": ("Coconut", "Fruits", LIMIT),
    # Vegetables
    "can-dogs-eat-asparagus": ("Asparagus", "Vegetables", SAFE),
    "can-dogs-eat-bell-peppers": ("Bell Peppers", "Vegetables", SAFE),
    "can-dogs-eat-broccoli": ("Broccoli", "Vegetables", SAFE),
    "can-dogs-eat-butternut-squash-a-nutritious-addition-to-your-dogs-diet":
        ("Butternut Squash", "Vegetables", SAFE),
    "can-dogs-eat-cabbage": ("Cabbage", "Vegetables", SAFE),
    "carrots-for-dogs": ("Carrots", "Vegetables", SAFE),
    "can-dogs-eat-cauliflower": ("Cauliflower", "Vegetables", SAFE),
    "can-dogs-eat-celery": ("Celery", "Vegetables", SAFE),
    "can-dogs-eat-corn": ("Corn", "Vegetables", SAFE),
    "can-dogs-eat-cucumber": ("Cucumber", "Vegetables", SAFE),
    "can-dogs-eat-eggplant": ("Eggplant", "Vegetables", SAFE),
    "can-dogs-eat-garlic": ("Garlic", "Vegetables", AVOID),
    "can-dogs-eat-green-beans": ("Green Beans", "Vegetables", SAFE),
    "can-dogs-eat-kale": ("Kale", "Vegetables", LIMIT),
    "can-dogs-eat-mushrooms": ("Mushrooms", "Vegetables", LIMIT),
    "can-dogs-eat-onions": ("Onions", "Vegetables", AVOID),
    "can-dogs-eat-peas": ("Peas", "Vegetables", SAFE),
    "can-dogs-eat-potatoes": ("Potatoes", "Vegetables", SAFE),
    "why-pumpkin-is-good-for-dogs": ("Pumpkin", "Vegetables", SAFE),
    "can-dogs-eat-spinach": ("Spinach", "Vegetables", LIMIT),
    "can-dogs-eat-sweet-potatoes": ("Sweet Potatoes", "Vegetables", SAFE),
    "can-dogs-eat-tomatoes": ("Tomatoes", "Vegetables", LIMIT),
    "can-dogs-eat-zucchini": ("Zucchini", "Vegetables", SAFE),
    # Meat, Fish & Eggs
    "can-dogs-eat-bacon": ("Bacon", "Meat, Fish & Eggs", AVOID),
    "can-dogs-eat-beef": ("Beef", "Meat, Fish & Eggs", SAFE),
    "can-dogs-eat-chicken-breast": ("Chicken Breast", "Meat, Fish & Eggs", SAFE),
    "can-dogs-eat-eggs": ("Eggs", "Meat, Fish & Eggs", SAFE),
    "can-dogs-eat-ham": ("Ham", "Meat, Fish & Eggs", AVOID),
    "can-dogs-eat-pork": ("Pork", "Meat, Fish & Eggs", SAFE),
    "can-dogs-eat-raw-meat": ("Raw Meat", "Meat, Fish & Eggs", AVOID),
    "can-dogs-eat-salmon": ("Salmon", "Meat, Fish & Eggs", SAFE),
    "can-dogs-eat-shrimp": ("Shrimp", "Meat, Fish & Eggs", SAFE),
    "can-dogs-eat-tuna": ("Tuna", "Meat, Fish & Eggs", LIMIT),
    "can-dogs-eat-turkey": ("Turkey", "Meat, Fish & Eggs", SAFE),
    # Dairy
    "can-dogs-eat-cheese": ("Cheese", "Dairy", SAFE),
    "can-dogs-eat-ice-cream": ("Ice Cream", "Dairy", AVOID),
    "can-dogs-drink-milk": ("Milk", "Dairy", LIMIT),
    "can-dogs-eat-yogurt": ("Yogurt", "Dairy", SAFE),
    # Grains & Starches
    "can-dogs-eat-bread": ("Bread", "Grains & Starches", LIMIT),
    "can-dogs-eat-oatmeal": ("Oatmeal", "Grains & Starches", SAFE),
    "can-dogs-eat-pasta": ("Pasta", "Grains & Starches", SAFE),
    "can-dogs-eat-popcorn": ("Popcorn", "Grains & Starches", SAFE),
    "can-dogs-eat-quinoa": ("Quinoa", "Grains & Starches", SAFE),
    "can-dogs-eat-rice": ("Rice", "Grains & Starches", SAFE),
    # Nuts & Seeds
    "can-dogs-have-almond-butter": ("Almond Butter", "Nuts & Seeds", LIMIT),
    "can-dogs-eat-almonds": ("Almonds", "Nuts & Seeds", AVOID),
    "can-dogs-eat-cashews": ("Cashews", "Nuts & Seeds", SAFE),
    "can-dogs-eat-peanut-butter": ("Peanut Butter", "Nuts & Seeds", SAFE),
    "can-dogs-eat-pumpkin-seeds": ("Pumpkin Seeds", "Nuts & Seeds", SAFE),
    "can-dogs-eat-sunflower-seeds": ("Sunflower Seeds", "Nuts & Seeds", LIMIT),
    "can-dogs-eat-walnuts": ("Walnuts", "Nuts & Seeds", AVOID),
    # Sweets & Other
    "can-dogs-eat-chocolate": ("Chocolate", "Sweets & Other", AVOID),
    "can-dogs-eat-honey": ("Honey", "Sweets & Other", LIMIT),
}

CATEGORY_ORDER = ["Fruits", "Vegetables", "Meat, Fish & Eggs", "Dairy",
                  "Grains & Starches", "Nuts & Seeds", "Sweets & Other",
                  "New additions"]

# Genuinely toxic foods highlighted in the top callout. Safety assertion below.
TOXIC_CALLOUT = ["can-dogs-eat-chocolate", "can-dogs-eat-grapes",
                 "can-dogs-eat-onions", "can-dogs-eat-garlic",
                 "can-dogs-eat-avocado"]


def one_liner(body_html: str) -> str:
    m = re.search(r"<strong>Quick Answer:</strong>(.*?)</p>", body_html, re.S)
    if not m:
        return ""
    txt = re.sub(r"<[^>]+>", "", m.group(1))
    txt = re.sub(r"\s+", " ", txt).strip()
    first = re.split(r"(?<=[.!])\s", txt)[0]
    return first[:170]


def main() -> int:
    sys.stderr.reconfigure(encoding="utf-8")
    articles = {}
    for p in sorted(glob.glob(os.path.join(BD, "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        m = d.get("meta", {})
        if m.get("blog_handle") != "dog-nutrition":
            continue
        slug = m.get("shopify_handle")
        if slug == HUB_SLUG:
            continue
        articles[slug] = one_liner(d.get("body_html", ""))

    for slug in TOXIC_CALLOUT:
        assert FOODS[slug][2] == AVOID, f"safety: {slug} must be AVOID"

    uncurated = sorted(set(articles) - set(FOODS))
    if uncurated:
        print(f"WARNING: {len(uncurated)} uncurated foods placed in "
              f"'New additions': {uncurated}", file=sys.stderr)

    rows_by_cat: dict[str, list] = {}
    counts = {SAFE: 0, LIMIT: 0, AVOID: 0}
    for slug, line in articles.items():
        name, cat, badge = FOODS.get(slug, (slug.replace("can-dogs-eat-", "")
                                            .replace("-", " ").title(),
                                            "New additions", LIMIT))
        counts[badge] += 1
        rows_by_cat.setdefault(cat, []).append((name, slug, badge, line))

    chips, sections = [], []
    for cat in CATEGORY_ORDER:
        if cat not in rows_by_cat:
            continue
        cid = "cat-" + re.sub(r"[^a-z]+", "-", cat.lower()).strip("-")
        chips.append(f'<a class="wfy-chip" href="#{cid}">{cat}</a>')
        rows = "".join(
            f'<a class="wfy-food" href="/blogs/dog-nutrition/{slug}">'
            f'<span class="wfy-fbadge">{BADGE[b][0]}</span>'
            f'<span class="wfy-fbody"><span class="wfy-fname">{n}</span>'
            f'<span class="wfy-fline">{line}</span></span></a>'
            for n, slug, b, line in sorted(rows_by_cat[cat]))
        sections.append(
            f'<h2 class="wfy-letter" id="{cid}">{cat} '
            f'<span class="wfy-secn">{len(rows_by_cat[cat])}</span></h2>'
            f'<div class="wfy-foodgrid">{rows}</div>')

    toxic_links = " &middot; ".join(
        f'<a href="/blogs/dog-nutrition/{s}">{FOODS[s][0]}</a>'
        for s in TOXIC_CALLOUT)
    total = len(articles)

    body = f"""<meta charset="utf-8">
<style>
.wfy-intro {{ background:#141412; color:#EDEAE2; text-align:center; padding:34px 22px 38px; margin:0 0 26px; }}
.wfy-intro .wfy-count {{ display:flex; flex-wrap:wrap; justify-content:center; gap:6px 0;
  font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:#CFCBC2; margin:0 auto 14px; }}
.wfy-intro .wfy-count span {{ white-space:nowrap; }}
.wfy-intro .wfy-count span + span::before {{ content:"\\00B7"; margin:0 10px; color:#8F8B82; }}
.wfy-intro p {{ max-width:64ch; margin:0 auto; font-size:15.5px; line-height:1.65; color:#EDEAE2; }}
.wfy-toxic {{ border:2px solid #1A1A1A; padding:16px 20px; margin:0 0 26px; font-size:15px; line-height:1.6; }}
.wfy-toxic strong {{ letter-spacing:.04em; }}
.wfy-chips {{ display:flex; flex-wrap:wrap; gap:6px; justify-content:center; margin:0 0 8px; }}
.wfy-chip {{ display:inline-block; padding:6px 12px; border:1px solid #D9D5CB; color:#1A1A1A;
  text-decoration:none; font-size:13px; }}
.wfy-chip:hover {{ background:#EFEAE0; border-color:#1A1A1A; }}
.wfy-letter {{ border-top:1px solid #E6E2D8; padding-top:22px; margin:26px 0 12px; scroll-margin-top:90px; }}
.wfy-secn {{ font-size:12px; color:#6F6A61; margin-left:6px; }}
.wfy-foodgrid {{ display:grid; grid-template-columns:1fr 1fr; gap:0 30px; }}
.wfy-food {{ display:flex; gap:10px; align-items:flex-start; padding:10px 2px;
  border-bottom:1px solid #E6E2D8; text-decoration:none; color:#1A1A1A; }}
.wfy-food:hover {{ background:#EFEAE0; }}
.wfy-fbadge {{ flex:0 0 auto; font-size:15px; line-height:1.5; }}
.wfy-fbody {{ display:flex; flex-direction:column; gap:2px; }}
.wfy-fname {{ font-weight:600; font-size:15.5px; }}
.wfy-fline {{ font-size:13px; color:#6F6A61; line-height:1.5; }}
@media (max-width:700px) {{ .wfy-foodgrid {{ grid-template-columns:1fr; }} }}
</style>
<div class="wfy-intro">
<p class="wfy-count"><span>{total} foods</span><span>vet-fact-checked</span><span>&#9989; {counts[SAFE]} safe</span><span>&#9888;&#65039; {counts[LIMIT]} limit</span><span>&#128683; {counts[AVOID]} avoid</span></p>
<p>Every &ldquo;can dogs eat&hellip;?&rdquo; question we have answered, in one place. Each verdict below
comes straight from the full guide &mdash; tap any food for serving sizes, risks, and preparation.</p>
</div>
<div class="wfy-toxic"><strong>&#128683; NEVER FEED:</strong> {toxic_links}.
If your dog eats any of these, contact your veterinarian or an animal poison control center right away.</div>
<nav class="wfy-chips" aria-label="Jump to category">{"".join(chips)}</nav>
{"".join(sections)}
<p style="margin-top:34px;">These are general guidelines &mdash; check with your vet for your dog's needs.
Looking for your dog's breed instead? Browse the
<a href="/blogs/dog-breeds/dog-breeds-a-z">Dog Breeds A&ndash;Z directory</a>.</p>
"""

    out_path = os.path.join(BD, f"{HUB_SLUG}.json")
    hero = None
    if os.path.exists(out_path):
        hero = json.load(open(out_path, encoding="utf-8")).get("images", {}).get("hero")
    if not hero and os.path.exists(HERO_SEED):
        hero = json.load(open(HERO_SEED, encoding="utf-8")).get("what-can-dogs-eat-hub")
    article = {
        "meta": {
            "blog_handle": "dog-nutrition",
            "shopify_handle": HUB_SLUG, "slug": HUB_SLUG,
            "name": "What Can Dogs Eat? The Complete Food Safety Guide",
            "title_tag": f"What Can Dogs Eat? {total} Foods, Vet-Checked",
            "excerpt": f"Every food verdict in one place — {total} human foods rated safe, limit, or avoid for dogs.",
            "meta_description": (f"Can dogs eat that? {total} human foods rated safe, limit or avoid — "
                                 "vet-fact-checked verdicts with serving guidance, from apples to walnuts."),
            "tags": ["diet", "directory"],
            "published": True,
            "published_at": "2026-07-16T12:00:00Z",
        },
        "images": {"hero": hero} if hero else {},
        "body_html": body,
    }
    tt = article["meta"]["title_tag"]
    assert len(tt) <= 51, f"title_tag {len(tt)} > 51"
    json.dump(article, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"wrote {out_path}", file=sys.stderr)
    print(f"foods={total} safe={counts[SAFE]} limit={counts[LIMIT]} "
          f"avoid={counts[AVOID]} | title_tag {len(tt)} chars | hero={'Y' if hero else 'NONE'}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
