"""Enhance the legacy /us-the-most-popular-dog-breeds-of-2022 article in place.

What it does:
- Builds a new body_html with: intro, top-10 spotlight cards (HD images +
  internal links), full ranking table (positions 1-100 with internal links
  where breed pages exist), trend commentary, FAQ + JSON-LD schema, related
  reading.
- Preserves the URL, title, and 2023 publish date.
"""

import os
import sys
import json
import glob
import re
import urllib.request
from dotenv import load_dotenv

load_dotenv()
STORE   = os.environ["SHOPIFY_STORE"]
TOKEN   = os.environ["SHOPIFY_TOKEN"]
BLOG_ID = os.environ["SHOPIFY_BLOG_ID"]
ARTICLE_ID = 564584579126
BLOG_BASE  = "/blogs/dog-breeds"

# AKC 2023 most-popular ranking - verbatim from the original article (positions 1-100)
RANKING = [
    "French Bulldogs", "Labrador Retrievers", "Golden Retrievers", "German Shepherd Dogs",
    "Poodles", "Bulldogs", "Rottweilers", "Beagles", "Dachshunds", "German Shorthaired Pointers",
    "Pembroke Welsh Corgis", "Australian Shepherds", "Yorkshire Terriers",
    "Cavalier King Charles Spaniels", "Doberman Pinschers", "Boxers", "Miniature Schnauzers",
    "Cane Corso", "Great Danes", "Shih Tzu", "Siberian Huskies", "Bernese Mountain Dogs",
    "Pomeranians", "Boston Terriers", "Havanese", "English Springer Spaniels",
    "Shetland Sheepdogs", "Brittanys", "Cocker Spaniels", "Border Collies",
    "Miniature American Shepherds", "Belgian Malinois", "Vizslas", "Chihuahuas", "Pugs",
    "Basset Hounds", "Mastiffs", "Maltese", "Collies", "English Cocker Spaniels",
    "Rhodesian Ridgebacks", "Newfoundlands", "Shiba Inu", "Weimaraners",
    "West Highland White Terriers", "Portuguese Water Dogs", "Bichons Frises",
    "Australian Cattle Dogs", "Dalmatians", "Bloodhounds", "Papillons",
    "Chesapeake Bay Retrievers", "Samoyeds", "Whippets", "Akitas", "St. Bernards",
    "Wirehaired Pointing Griffons", "Giant Schnauzers", "German Wirehaired Pointers",
    "Scottish Terriers", "Bullmastiffs", "Cardigan Welsh Corgis", "Italian Greyhounds",
    "Bull Terriers", "Airedale Terriers", "Soft Coated Wheaten Terriers", "Alaskan Malamutes",
    "Chinese Shar-Pei", "Great Pyrenees", "Cairn Terriers", "Irish Setters",
    "Miniature Pinschers", "Russell Terriers", "Old English Sheepdogs",
    "Staffordshire Bull Terriers", "Lagotti Romagnoli", "Biewer Terriers",
    "Dogues de Bordeaux", "Anatolian Shepherd Dogs", "Chinese Cresteds",
    "Nova Scotia Duck Tolling Retrievers", "Boykin Spaniels", "Greater Swiss Mountain Dogs",
    "Cotons de Tulear", "Rat Terriers", "Lhasa Apsos", "American Staffordshire Terriers",
    "Dogo Argentinos", "Irish Wolfhounds", "Keeshonden", "Basenjis", "Chow Chows",
    "English Setters", "Standard Schnauzers", "Border Terriers", "Pekingese",
    "Brussels Griffons", "Bouviers des Flandres", "Gordon Setters", "Norwegian Elkhounds",
    "Borzois", "Wire Fox Terriers",
]

# Manual overrides for AKC display names that don't auto-map to a slug
MANUAL_SLUGS = {
    "Poodles":               "standard-poodle",
    "Bichons Frises":        "bichon-frise",
    "Lagotti Romagnoli":     "lagotto-romagnolo",
    "Keeshonden":            "keeshond",
    "Cotons de Tulear":      "coton-de-tulear",
    "Dogues de Bordeaux":    "dogue-de-bordeaux",
    "Bouviers des Flandres": "bouvier-des-flandres",
    "Brittanys":             "brittany",
    "Borzois":               "borzoi",
}


def build_name_to_slug() -> dict:
    mp = {}
    for fp in glob.glob("breed-data/*.json"):
        slug = os.path.splitext(os.path.basename(fp))[0]
        if any(slug.endswith(suf) for suf in ("-grooming-guide", "-first-year-costs", "-puppy-checklist")):
            continue
        with open(fp, encoding="utf-8") as f:
            b = json.load(f)
        if b.get("meta", {}).get("size_category") == "Roundup":
            continue
        nm = b.get("meta", {}).get("name")
        if nm:
            mp[nm.lower()] = slug
    return mp


def norm(name: str) -> str:
    n = name.lower().replace("'", "").strip()
    n = re.sub(r"\s+", " ", n)
    return n


def resolve_slug(display: str, name_map: dict):
    if display in MANUAL_SLUGS:
        return MANUAL_SLUGS[display]
    nn = norm(display)
    for cand in (nn, nn.rstrip("s"), nn.replace(" dogs", "").replace(" dog", "")):
        if cand in name_map:
            return name_map[cand]
    first = nn.split()[0] if nn else ""
    for k, v in name_map.items():
        if k.startswith(first) and all(w in k for w in nn.split() if w not in ("dog", "dogs")):
            return v
    return None


def load_breed(slug: str):
    p = f"breed-data/{slug}.json"
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def stat_value(stats_dict, key):
    v = stats_dict.get(key)
    if isinstance(v, dict):
        return v.get("value", "")
    return str(v) if v else ""


def build_intro():
    return (
        "<p>Each year the American Kennel Club publishes the official ranking of "
        "America's most popular dog breeds, based on registrations. The 2023 list "
        "tells a clear story: the <strong>French Bulldog</strong> dethroned the "
        "Labrador Retriever after the Lab held the #1 spot for over 30 years - a "
        "remarkable shift driven by urbanization, apartment living, and the breed's "
        "compact, affectionate nature.</p>"
        "<p>Below is the complete top-100 ranking with HD photos, quick stats, and "
        "deep links to each breed's full guide. Use the table or click any breed "
        "to explore further.</p>"
    )


def build_trends_section(name_map):
    items = [
        ("French Bulldog (#1)",     "french-bulldog",
         "Up from #14 in 2012 - a 1,000%+ surge in registrations driven by their compact, apartment-friendly build."),
        ("Labrador Retriever (#2)", "labrador-retriever",
         "Held the #1 spot for over 30 years. Still America's most versatile family dog."),
        ("Golden Retriever (#3)",   "golden-retriever",
         "The quintessential family dog. Sweet, eager-to-please, and consistently in the top 5."),
        ("German Shepherd Dog (#4)","german-shepherd-dog",
         "Working-line stalwart. Police, military, service, and family dog all in one package."),
        ("Cane Corso (#18)",        "cane-corso",
         "Climbing fast in the rankings as guard-breed interest rises in U.S. households."),
    ]
    rows = ""
    for label, slug, note in items:
        rows += (
            '<div style="margin-bottom:18px;">'
            f'<strong style="color:#1a1a1a;"><a href="{BLOG_BASE}/{slug}" style="color:#1a1a1a;text-decoration:underline;text-underline-offset:3px;">{label}</a>.</strong> '
            f'<span style="color:#6b7177;">{note}</span></div>'
        )
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">2023 Trends</p>
  <h2 id="trends" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">What's Driving the Rankings</h2>
  {rows}
</div>"""


def build_top10_card(rank, slug, breed):
    name = breed["meta"]["name"]
    hero = breed["images"]["hero"]["url"]
    size = stat_value(breed["stats"], "size")
    weight = stat_value(breed["stats"], "weight")
    exercise = stat_value(breed["stats"], "exercise")
    grooming = stat_value(breed["stats"], "grooming")
    breed_url = f"{BLOG_BASE}/{slug}"
    stats_line = f"{size} · {weight} · Exercise: {exercise} · Grooming: {grooming}"
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <h2 id="top-{rank}" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">
    <span style="color:#6b7177;font-weight:400;">#{rank}</span> <a href="{breed_url}" style="color:#1a1a1a;text-decoration:none;">{name}</a>
  </h2>
  <a href="{breed_url}" style="text-decoration:none;color:inherit;display:block;">
    <figure style="margin:0 0 16px 0;">
      <img src="{hero}" alt="{name}" loading="lazy"
        style="width:100%;height:auto;border-radius:8px;display:block;box-shadow:rgba(0,0,0,0.07) 0px 8px 24px;">
    </figure>
  </a>
  <p style="font-size:0.78em;color:#6b7177;margin:0 0 12px 0;font-family:'figmaMono','SF Mono',monospace;letter-spacing:0.3px;">{stats_line}</p>
  <a href="{breed_url}" style="display:inline-block;font-size:0.88em;color:#1a1a1a;font-weight:700;text-decoration:underline;text-underline-offset:3px;">Read the full {name} guide →</a>
</div>"""


def build_top10_section(name_map):
    cards = ""
    for i, display in enumerate(RANKING[:10], start=1):
        slug = resolve_slug(display, name_map)
        if not slug:
            continue
        breed = load_breed(slug)
        if not breed:
            continue
        cards += build_top10_card(i, slug, breed)
    return f"""<div style="margin-bottom:32px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Top 10 Spotlight</p>
  <h2 id="top-10" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">The Top 10 Most Popular Breeds of 2023</h2>
</div>
{cards}"""


def build_full_ranking_table(name_map):
    cells = ""
    for rank, display in enumerate(RANKING, start=1):
        slug = resolve_slug(display, name_map)
        if slug:
            cell_name = f'<a href="{BLOG_BASE}/{slug}" style="color:#1a1a1a;font-weight:700;text-decoration:none;">{display}</a>'
        else:
            cell_name = f'<span style="color:#6b7177;">{display}</span>'
        cells += (
            '<tr style="border-bottom:1px solid #e8e8e8;">'
            f'<td style="padding:8px 12px;color:#6b7177;width:60px;">#{rank}</td>'
            f'<td style="padding:8px 12px;">{cell_name}</td>'
            "</tr>"
        )
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Full Ranking</p>
  <h2 id="full-list" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">Most Popular Dog Breeds of 2023 - Full Top 100</h2>
  <p style="font-size:0.9em;color:#6b7177;margin:0 0 16px 0;">Click any breed to read its full Wooffy guide.</p>
  <div style="overflow-x:auto;">
    <table style="width:100%;font-size:0.92em;border-collapse:collapse;">
      <thead>
        <tr>
          <th style="padding:10px 12px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Rank</th>
          <th style="padding:10px 12px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Breed</th>
        </tr>
      </thead>
      <tbody>
        {cells}
      </tbody>
    </table>
  </div>
</div>"""


FAQS = [
    ("What's the most popular dog breed in America?",
     "As of 2023, the French Bulldog is the most popular dog breed in the United States, having dethroned the Labrador Retriever after the Lab held the top spot for over 30 years. The shift reflects urbanization and the Frenchie's apartment-friendly compact build."),
    ("Why did the French Bulldog overtake the Labrador?",
     "Frenchies thrive in apartments and small homes, have moderate exercise needs, are low-shedding, and have a quiet, affectionate temperament - all traits aligned with how Americans live today. Their popularity surged 1,000%+ since 2012."),
    ("Are popular breeds always the best choice?",
     "Not necessarily. Popularity reflects what owners are buying, not which breeds are easiest, healthiest, or best for your specific lifestyle. Always match the breed to your home, schedule, and energy level - not the other way around."),
    ("Which breeds are climbing the rankings fastest?",
     "Cane Corso, Belgian Malinois, and several working/guard breeds have been climbing as households re-prioritize protection. Among small breeds, Havanese, Pomeranians, and Mini American Shepherds are also rising."),
    ("How can I find a specific breed's rank?",
     "Use the full Top-100 table above to find any specific breed's rank. The list is ordered exactly as published by the AKC for 2023 registrations."),
    ("How does the AKC measure popularity?",
     "By new registrations of purebred dogs in the AKC's pedigree database. It does not include mixed-breed dogs, dogs registered with other clubs, or unregistered purebreds - so the ranking reflects AKC purebred trends specifically."),
    ("Where can I read more about each breed?",
     "Click any linked breed name in the table to read its full Wooffy guide - covering temperament, care, costs, and how to find a healthy puppy or rescue."),
]


def build_faq():
    items = ""
    for i, (q, a) in enumerate(FAQS):
        border_bottom = ";border-bottom:1px solid #e8e8e8" if i == len(FAQS) - 1 else ""
        items += f"""
  <details style="border-top:1px solid #e8e8e8{border_bottom};">
    <summary style="padding:18px 0;font-size:0.95em;font-weight:700;color:#1a1a1a;display:flex;justify-content:space-between;align-items:center;list-style:none;user-select:none;cursor:pointer;">
      {q}
      <span class="faq-icon" style="font-size:1.4em;font-weight:300;color:#6b7177;flex-shrink:0;margin-left:16px;line-height:1;">+</span>
    </summary>
    <p style="font-size:0.9em;font-weight:400;line-height:1.7;color:#6b7177;margin:0 0 18px 0;padding-right:24px;">{a}</p>
  </details>"""
    return f"""<style>
.wooffy-faq summary::-webkit-details-marker{{display:none;}}
.wooffy-faq details[open] .faq-icon{{transform:rotate(45deg);}}
.wooffy-faq .faq-icon{{transition:transform 0.22s ease;display:inline-block;}}
</style>
<div class="wooffy-faq" style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">FAQ</p>
  <h2 id="faq" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 4px 0;line-height:1.2;">Frequently Asked Questions</h2>
{items}
</div>"""


def build_faq_schema():
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'


def build_related():
    items = [
        ("most-popular-dog-breeds",                      "Most Popular Dog Breeds (Updated)",  "Our editorial pick of must-know breeds"),
        ("best-family-dog-breeds",                       "Best Family Dog Breeds",             "Top picks for households with kids"),
        ("21-great-dog-breeds-for-small-apartments",     "21 Best Apartment Dogs",             "Smaller and quieter favorites"),
        ("best-large-dog-breeds",                        "Best Large Dog Breeds",              "Gentle giants and big working breeds"),
        ("best-small-dog-breeds",                        "Best Small Dog Breeds",              "Toy and small companions"),
    ]
    li = "".join(
        f'    <li><a href="{BLOG_BASE}/{slug}" style="color:#1a1a1a;font-weight:700;text-decoration:underline;text-underline-offset:3px;">{name}</a> - {note}</li>\n'
        for slug, name, note in items
    )
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Explore More</p>
  <h2 style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">Related Reading</h2>
  <ul style="font-size:0.95em;font-weight:400;line-height:1.9;color:#6b7177;padding-left:20px;margin:0;">
{li}  </ul>
</div>"""


def build_full_body():
    name_map = build_name_to_slug()
    return (
        build_intro()
        + build_trends_section(name_map)
        + build_top10_section(name_map)
        + build_full_ranking_table(name_map)
        + build_faq()
        + build_related()
        + build_faq_schema()
    )


def push_to_shopify(body_html):
    url = f"https://{STORE}/admin/api/2024-01/articles/{ARTICLE_ID}.json"
    payload = {"article": {"id": ARTICLE_ID, "body_html": body_html}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("X-Shopify-Access-Token", TOKEN)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
    a = result["article"]
    print(f"Updated -> https://{STORE}/blogs/dog-breeds/{a['handle']}  (id={a['id']})")
    print(f"  body_html length: {len(a['body_html'])} chars")


def main():
    body = build_full_body()
    print(f"Built body_html: {len(body)} chars")
    if "--push" in sys.argv:
        push_to_shopify(body)
    else:
        os.makedirs("output", exist_ok=True)
        with open("output/popular-breeds-preview.html", "w", encoding="utf-8") as f:
            f.write(body)
        print("Wrote preview to output/popular-breeds-preview.html (use --push to apply)")


if __name__ == "__main__":
    main()
