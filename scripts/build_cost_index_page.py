"""Build the "Dog Breed Cost Index" page from costs-dataset.json (GEO_PLAN W3.1).

One page with every breed's purchase price, first-year total, ongoing
annual cost, monthly food, monthly insurance and yearly grooming, plus
medians by size bucket, most / least expensive lists, a methodology
section and a schema.org Dataset block. Everything on the page is
computed from costs-dataset.json, which was extracted from Wooffy's own
first-year cost guides, so the page is a citable primary source.

Writes breed-data/dog-breed-cost-index.json (regenerate any time the
dataset changes) and geo/dog-breed-cost-index.csv (the downloadable copy;
upload it to Shopify Files and set CSV_URL below to publish the link).

Usage:
    python3 scripts/build_cost_index_page.py            # print summary only
    python3 scripts/build_cost_index_page.py --write    # write JSON + CSV
    echo YES | python3 scripts/generate.py dog-breed-cost-index --update --touch-updated
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
from datetime import date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATASET = os.path.join(ROOT, "costs-dataset.json")
OUT_JSON = os.path.join(ROOT, "breed-data", "dog-breed-cost-index.json")
OUT_CSV = os.path.join(ROOT, "geo", "dog-breed-cost-index.csv")

SLUG = "dog-breed-cost-index"
YEAR = 2026
PAGE_URL = f"https://thewooffy.com/blogs/dog-breeds/{SLUG}"
CALCULATOR_URL = "https://thewooffy.com/pages/dog-cost-calculator"
CSV_URL = ""   # set to the Shopify Files URL once geo/dog-breed-cost-index.csv is uploaded
# Placeholder hero until a dedicated one is generated (HD image pipeline).
HERO = {
    "url": "https://cdn.shopify.com/s/files/1/0554/5253/2790/files/roundup-most-expensive-dog-breeds-hero.png?v=1777583618",
    "alt": "Dog breed cost index: first-year and annual ownership costs for 164 breeds, compared",
}
BUCKETS = [("toy", "Toy"), ("small", "Small"), ("medium", "Medium"), ("large", "Large"), ("giant", "Giant")]
MUTED = "font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 14px 0;"
TH = ("font-family:'figmaMono','SF Mono',monospace;font-size:0.62em;font-weight:400;letter-spacing:0.54px;"
      "text-transform:uppercase;color:rgba(0,0,0,0.5);text-align:left;padding:10px 8px;border-bottom:2px solid #e8e8e8;white-space:nowrap;")
TD = "padding:9px 8px;border-bottom:1px solid #eee;font-size:0.88em;color:#1a1a1a;white-space:nowrap;"
TDL = TD.replace("white-space:nowrap;", "")


def money(v):
    return f"${int(round(v)):,}"


def rng(pair):
    return f"{money(pair[0])}–{money(pair[1])}"


def mid(pair):
    return (pair[0] + pair[1]) / 2


def median_range(rows, key):
    lo = statistics.median(r[key][0] for r in rows)
    hi = statistics.median(r[key][1] for r in rows)
    return [lo, hi]


def cost_url(slug):
    return f"/blogs/dog-breeds/{slug}-first-year-costs"


def load_rows():
    data = json.load(open(DATASET, encoding="utf-8"))
    rows = []
    for slug, v in data.items():
        if not isinstance(v, dict) or "total_year1" not in v:
            continue
        rows.append({"slug": slug, **v})
    rows.sort(key=lambda r: r["name"].lower())
    return rows


def build(rows):
    n = len(rows)
    today = date.today().isoformat()
    all_puppy = median_range(rows, "puppy")
    all_y1 = median_range(rows, "total_year1")
    all_ongoing = median_range(rows, "annual_ongoing")
    by_bucket = {b: [r for r in rows if r["bucket"] == b] for b, _ in BUCKETS}
    bucket_y1 = {b: median_range(rs, "total_year1") for b, rs in by_bucket.items() if rs}
    ratio = mid(bucket_y1["giant"]) / mid(bucket_y1["toy"])
    most = sorted(rows, key=lambda r: -mid(r["total_year1"]))[:10]
    least = sorted(rows, key=lambda r: mid(r["total_year1"]))[:10]
    cheapest_puppy = sorted(rows, key=lambda r: mid(r["puppy"]))[:5]
    priciest_puppy = sorted(rows, key=lambda r: -mid(r["puppy"]))[:5]

    def link(r):
        return f'<a href="{cost_url(r["slug"])}" style="color:#1a1a1a;font-weight:600;text-decoration:underline;text-underline-offset:3px;">{r["name"]}</a>'

    quick = (
        f"Across the {n} breeds in Wooffy's cost guides, a puppy from a reputable breeder typically costs "
        f"{rng(all_puppy)} (median range), the first year of ownership runs {rng(all_y1)}, and each year after that "
        f"about {rng(all_ongoing)}. Size is the biggest driver: giant breeds cost roughly {ratio:.1f}× as much in year one as toy breeds. "
        f"The most expensive first year is the {most[0]['name']} ({rng(most[0]['total_year1'])}); the least expensive is the "
        f"{least[0]['name']} ({rng(least[0]['total_year1'])})."
    )

    # ---- intro
    intro_html = (
        f'<p style="{MUTED}">This index puts the numbers from all {n} of our first-year cost guides side by side: what a puppy costs to buy, '
        f'what the first year adds up to once vet visits, spay or neuter, food, insurance, grooming and setup are counted, and what a typical year costs after that. '
        f'Every figure is a low–high range in US dollars for a dog bought from a reputable, health-testing breeder; rescue adoption is usually far cheaper up front '
        f'(see each breed\'s guide for its rescue range).</p>'
        f'<p style="{MUTED}">Use the <a href="{CALCULATOR_URL}" style="color:#1a1a1a;font-weight:600;text-decoration:underline;text-underline-offset:3px;">first-year cost calculator</a> '
        f'to adjust these ranges for your own region, food choice and insurance plan. Figures last compiled {today}.</p>'
    )

    # ---- by size table
    size_rows = ""
    for b, label in BUCKETS:
        rs = by_bucket[b]
        if not rs:
            continue
        size_rows += (f'<tr><td style="{TDL}"><strong>{label}</strong> ({len(rs)} breeds)</td>'
                      f'<td style="{TD}">{rng(median_range(rs, "puppy"))}</td>'
                      f'<td style="{TD}">{rng(median_range(rs, "total_year1"))}</td>'
                      f'<td style="{TD}">{rng(median_range(rs, "annual_ongoing"))}</td>'
                      f'<td style="{TD}">{rng(median_range(rs, "food_monthly"))}</td>'
                      f'<td style="{TD}">{rng(median_range(rs, "insurance_monthly"))}</td></tr>')
    by_size_html = (
        f'<p style="{MUTED}">Median ranges across the breeds in each size bucket. Food and insurance scale almost directly with body weight, '
        f'which is why a giant breed\'s ongoing costs are roughly double a toy breed\'s even before any size-related health care.</p>'
        f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;margin:0 0 8px 0;">'
        f'<thead><tr><th style="{TH}">Size</th><th style="{TH}">Puppy price</th><th style="{TH}">First year</th>'
        f'<th style="{TH}">Each year after</th><th style="{TH}">Food / month</th><th style="{TH}">Insurance / month</th></tr></thead>'
        f'<tbody>{size_rows}</tbody></table></div>'
    )

    # ---- highlights
    def ol(items, key):
        return "<ol style=\"font-size:0.95em;line-height:1.8;color:#6b7177;padding-left:22px;margin:0 0 20px 0;\">" + "".join(
            f'<li>{link(r)} — {rng(r[key])}</li>' for r in items) + "</ol>"
    highlights_html = (
        f'<h3 style="font-size:1.1em;font-weight:700;color:#1a1a1a;margin:0 0 10px 0;">Most expensive first year</h3>{ol(most, "total_year1")}'
        f'<h3 style="font-size:1.1em;font-weight:700;color:#1a1a1a;margin:0 0 10px 0;">Least expensive first year</h3>{ol(least, "total_year1")}'
        f'<h3 style="font-size:1.1em;font-weight:700;color:#1a1a1a;margin:0 0 10px 0;">Highest and lowest puppy prices</h3>'
        f'<p style="{MUTED}">Highest: ' + ", ".join(f'{link(r)} ({rng(r["puppy"])})' for r in priciest_puppy) +
        f'. Lowest: ' + ", ".join(f'{link(r)} ({rng(r["puppy"])})' for r in cheapest_puppy) + '.</p>'
    )

    # ---- full table
    body_rows = ""
    for r in rows:
        body_rows += (f'<tr><td style="{TDL}">{link(r)}</td><td style="{TD}">{r["bucket"].title()}</td>'
                      f'<td style="{TD}">{rng(r["puppy"])}</td><td style="{TD}">{rng(r["total_year1"])}</td>'
                      f'<td style="{TD}">{rng(r["annual_ongoing"])}</td><td style="{TD}">{rng(r["food_monthly"])}</td>'
                      f'<td style="{TD}">{rng(r["insurance_monthly"])}</td><td style="{TD}">{rng(r["grooming_annual"])}</td></tr>')
    csv_note = (f' <a href="{CSV_URL}" style="color:#1a1a1a;font-weight:600;text-decoration:underline;text-underline-offset:3px;">Download the index as CSV</a>.'
                if CSV_URL else "")
    table_html = (
        f'<p style="{MUTED}">All {n} breeds, alphabetical. Each breed name links to its full cost guide with the line-item breakdown and rescue pricing.{csv_note}</p>'
        f'<div style="overflow-x:auto;"><table class="wooffy-cost-index" style="width:100%;border-collapse:collapse;margin:0;">'
        f'<thead><tr><th style="{TH}">Breed</th><th style="{TH}">Size</th><th style="{TH}">Puppy price</th><th style="{TH}">First year</th>'
        f'<th style="{TH}">Each year after</th><th style="{TH}">Food / mo</th><th style="{TH}">Insurance / mo</th><th style="{TH}">Grooming / yr</th></tr></thead>'
        f'<tbody>{body_rows}</tbody></table></div>'
    )

    # ---- methodology + Dataset schema
    dataset = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "@id": f"{PAGE_URL}#dataset",
        "name": f"Wooffy Dog Breed Cost Index {YEAR}",
        "description": (f"Purchase price, first-year total, ongoing annual cost, monthly food, monthly insurance and yearly grooming "
                        f"cost ranges (USD) for {n} dog breeds, compiled from Wooffy's breed-by-breed first-year cost guides."),
        "url": PAGE_URL,
        "creator": {"@type": "Organization", "@id": "https://thewooffy.com/#organization", "name": "Wooffy"},
        "dateModified": today,
        "temporalCoverage": str(YEAR),
        "spatialCoverage": "United States",
        "keywords": ["dog breed cost", "dog ownership cost", "puppy price", "first year dog cost", "dog breed prices"],
        "variableMeasured": [
            {"@type": "PropertyValue", "name": "Puppy purchase price (USD, low–high)"},
            {"@type": "PropertyValue", "name": "First-year total cost (USD, low–high)"},
            {"@type": "PropertyValue", "name": "Ongoing annual cost (USD, low–high)"},
            {"@type": "PropertyValue", "name": "Food cost per month (USD, low–high)"},
            {"@type": "PropertyValue", "name": "Pet insurance per month (USD, low–high)"},
            {"@type": "PropertyValue", "name": "Professional grooming per year (USD, low–high)"},
        ],
    }
    if CSV_URL:
        dataset["distribution"] = [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": CSV_URL}]
    schema_json = json.dumps(dataset, ensure_ascii=False).replace("</", "<\\/")
    est_count = sum(1 for r in rows if r.get("est"))
    methodology_html = (
        f'<script type="application/ld+json">{schema_json}</script>'
        f'<p style="{MUTED}">The figures come from Wooffy\'s {n} breed-specific first-year cost guides, each researched and written for that breed. '
        f'In July {YEAR} we extracted every guide\'s line items into one structured dataset and checked that each first-year total matched the sum of its parts; '
        f'22 totals that did not were corrected in October {YEAR}. The index is regenerated from that dataset whenever a guide is updated.</p>'
        f'<p style="{MUTED}">What the columns mean: <strong>Puppy price</strong> is the typical range from a reputable breeder who runs the breed\'s recommended health tests. '
        f'<strong>First year</strong> adds the first-year vet schedule, spay or neuter, food, insurance, grooming and one-time setup (crate, bed, bowls, leash). '
        f'<strong>Each year after</strong> is food, routine vet care, insurance and grooming for an adult dog. Emergencies, training classes, boarding and dog walkers are excluded. '
        f'Where a guide gave no explicit figure for a line (for example spay or neuter), a regional estimate is used; this affects {est_count} breeds and is noted on each guide.</p>'
        f'<p style="{MUTED}">You are welcome to cite or reproduce these figures with a link to this page. For a per-breed estimate adjusted to your situation, use the '
        f'<a href="{CALCULATOR_URL}" style="color:#1a1a1a;font-weight:600;text-decoration:underline;text-underline-offset:3px;">first-year cost calculator</a>.</p>'
    )

    faq = [
        {"q": "How much does a dog cost in the first year?",
         "a": f"Across {n} breeds, the median first-year range is {rng(all_y1)}, including the puppy, vet care, spay or neuter, food, insurance, grooming and setup. "
              f"Toy breeds median {rng(bucket_y1['toy'])}; giant breeds median {rng(bucket_y1['giant'])}."},
        {"q": "What is the cheapest dog breed to own?",
         "a": f"By first-year cost, the least expensive breeds in this index are the {least[0]['name']} ({rng(least[0]['total_year1'])}), "
              f"{least[1]['name']} ({rng(least[1]['total_year1'])}) and {least[2]['name']} ({rng(least[2]['total_year1'])}). "
              f"Small, short-coated breeds with modest grooming needs sit at the bottom of the index."},
        {"q": "What is the most expensive dog breed to own?",
         "a": f"The {most[0]['name']} has the highest first-year range in this index at {rng(most[0]['total_year1'])}, followed by the "
              f"{most[1]['name']} ({rng(most[1]['total_year1'])}) and {most[2]['name']} ({rng(most[2]['total_year1'])}). "
              f"Giant size, high puppy prices and professional grooming drive the top of the list."},
        {"q": "How much does a dog cost per year after the first year?",
         "a": f"The median ongoing range is {rng(all_ongoing)} a year for food, routine vet care, insurance and grooming. "
              f"It scales with size: roughly {rng(median_range(by_bucket['toy'], 'annual_ongoing'))} for toy breeds and "
              f"{rng(median_range(by_bucket['giant'], 'annual_ongoing'))} for giant breeds."},
        {"q": "Where do these numbers come from?",
         "a": f"From Wooffy's own {n} first-year cost guides, extracted into one dataset in July {YEAR} and cross-checked so every total equals its line items. "
              f"Ranges are US dollars for a puppy from a reputable breeder; emergencies and optional services are excluded."},
    ]

    article = {
        "meta": {
            "name": f"Dog Breed Cost Index {YEAR}",
            "slug": SLUG,
            "shopify_handle": SLUG,
            "group": "Breed Guides",
            "size_category": "Roundup",
            "tagline": f"Purchase price, first-year total and yearly cost for {n} breeds, from Wooffy's own cost guides.",
            "tags": ["dog breed cost", "dog ownership cost", "puppy price", "first year dog cost", "dog-breeds"],
            "published": True,
            "excerpt": f"Every breed's puppy price, first-year total and yearly cost in one table: {n} breeds compared, with medians by size and the most and least expensive breeds to own.",
            "meta_description": f"Dog breed cost index {YEAR}: puppy price, first-year total and annual cost for {n} breeds in one table, plus medians by size and the most and least expensive breeds.",
            "title_tag": f"Dog Breed Cost Index {YEAR}: {n} Breeds Compared",
            "quick_answer": quick,
            "author": "Kailun Zhang",
        },
        "images": {"hero": HERO},
        "sections": {
            "intro": {"label": "Overview", "heading": f"What does a dog cost in {YEAR}?", "html": intro_html},
            "by_size": {"label": "By size", "heading": "How much does a dog cost by size?", "html": by_size_html},
            "highlights": {"label": "Highlights", "heading": "Which dog breeds cost the most and least to own?", "html": highlights_html},
            "full_index": {"label": "The index", "heading": f"Full cost index: all {n} breeds", "html": table_html},
            "methodology": {"label": "Methodology", "heading": "Where do these numbers come from?", "html": methodology_html},
        },
        "faq": faq,
    }
    summary = {"breeds": n, "puppy": all_puppy, "year1": all_y1, "ongoing": all_ongoing, "giant_vs_toy": round(ratio, 2),
               "most": [(r["name"], r["total_year1"]) for r in most[:3]], "least": [(r["name"], r["total_year1"]) for r in least[:3]]}
    return article, summary


def write_csv(rows):
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["breed", "size", "puppy_low", "puppy_high", "first_year_low", "first_year_high", "annual_ongoing_low",
                    "annual_ongoing_high", "food_monthly_low", "food_monthly_high", "insurance_monthly_low", "insurance_monthly_high",
                    "grooming_annual_low", "grooming_annual_high", "guide_url"])
        for r in rows:
            w.writerow([r["name"], r["bucket"], *r["puppy"], *r["total_year1"], *r["annual_ongoing"], *r["food_monthly"],
                        *r["insurance_monthly"], *r["grooming_annual"], r["article_url"]])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="write breed-data JSON and geo CSV")
    args = ap.parse_args(argv)
    rows = load_rows()
    article, summary = build(rows)
    print(json.dumps(summary, ensure_ascii=False))
    print("quick answer:", article["meta"]["quick_answer"])
    if args.write:
        existing = {}
        if os.path.exists(OUT_JSON):
            existing = json.load(open(OUT_JSON, encoding="utf-8")).get("meta", {})
        for keep in ("published_at", "content_updated"):   # survive regeneration
            if existing.get(keep):
                article["meta"][keep] = existing[keep]
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(article, f, indent=2, ensure_ascii=False); f.write("\n")
        write_csv(rows)
        print(f"wrote {os.path.relpath(OUT_JSON, ROOT)} and {os.path.relpath(OUT_CSV, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
