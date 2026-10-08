"""Assemble breed-quiz-data.json for the breed selector quiz page.

Joins the reviewed trait scores (breed-quiz-scores.json) with page metadata
already in the repo: breed name, AKC group, hero image, first-year cost range
(calculator-data.json, summed exactly as the cost calculator does at its default
settings so the quiz and calculator never disagree), cost-guide URL, and AKC
2025 popularity rank (parsed from
the top-100 table on most-popular-dog-breeds). Manual corrections live in
breed-quiz-overrides.json so every change to a score stays documented.

Usage:
    py scripts/assemble_breed_quiz_data.py            # writes breed-quiz-data.json
    py scripts/assemble_breed_quiz_data.py --check    # validate only
"""

import argparse
import json
import os
import re
import sys
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORES_PATH = os.path.join(ROOT, "breed-quiz-scores.json")
OVERRIDES_PATH = os.path.join(ROOT, "breed-quiz-overrides.json")
OUT_PATH = os.path.join(ROOT, "breed-quiz-data.json")
BREED_DIR = os.path.join(ROOT, "breed-data")
BLOG_BASE = "/blogs/dog-breeds"

DIMS = ("energy", "apartment", "beginner", "trainability", "kids", "dogs", "small_pets",
        "alone", "shedding", "grooming", "barking", "heat", "cold", "strangers", "watchdog")
FLAGS = {"allergy_friendly": "allergy", "brachycephalic": "brachy", "heavy_drool": "drool"}
RANGE_FIELDS = ("weight_lbs", "exercise_min")
MAX_HIGHLIGHT_CHARS = 80
MAX_CAVEAT_CHARS = 120
# AKC ranks some breeds as one entry across sizes; our pages split them.
AKC_SHARED_RANK = {"miniature-poodle": "standard-poodle"}
CALC_LINE_ITEMS = ("p", "v", "s", "u", "g")  # puppy, vet, spay/neuter, setup, grooming
CALC_MONTHLY_ITEMS = ("f", "i")              # food, insurance (per month)


def load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def normalize_group(group: str | None) -> str:
    """'Herding Group' / 'Herding' -> 'Herding'; 'Terrier (UKC)' -> 'Terrier'."""
    g = re.sub(r"\s*\(.*?\)", "", group or "").strip()
    g = re.sub(r"\s+Group$", "", g)
    return g or "Other"


def parse_akc_ranks() -> dict[str, int]:
    """Map breed slug -> AKC 2025 rank from the top-100 table rows."""
    page = load_json(os.path.join(BREED_DIR, "most-popular-dog-breeds.json"))
    blob = json.dumps(page, ensure_ascii=False)
    rows = re.findall(r'>#(\d+)</td><td[^>]*>(?:<a href=\\"/blogs/dog-breeds/([a-z0-9-]+)\\")?', blob)
    if len(rows) != 100:
        raise SystemExit(f"AKC table parse found {len(rows)} rows, expected 100")
    ranks = {}
    for rank, slug in rows:
        if slug and slug not in ranks:
            ranks[slug] = int(rank)
    return ranks


def calculator_first_year(entry: dict | None) -> list[int] | None:
    """First-year [low, high] the calculator shows by default: breeder puppy,
    suburb pricing, insurance on, professional grooming."""
    if not entry:
        return None
    return [sum(entry[k][i] for k in CALC_LINE_ITEMS) + sum(entry[k][i] * 12 for k in CALC_MONTHLY_ITEMS)
            for i in (0, 1)]


def apply_overrides(breeds: dict[str, dict], overrides: list[dict]) -> None:
    for o in overrides:
        slug, field, value = o["slug"], o["field"], o["value"]
        if slug not in breeds:
            raise SystemExit(f"override for unknown breed: {slug}")
        b = breeds[slug]
        if field in DIMS:
            b["scores"][field] = value
        elif field in FLAGS:
            b["flags"][field] = value
        elif field in RANGE_FIELDS + ("highlights", "caveats"):
            b[field] = value
        else:
            raise SystemExit(f"override has unknown field: {slug}.{field}")


def validate(slug: str, b: dict) -> list[str]:
    errors = []
    for d in DIMS:
        v = b["scores"].get(d)
        if not isinstance(v, int) or not 1 <= v <= 5:
            errors.append(f"{slug}.{d}={v!r}")
    for f in FLAGS:
        if not isinstance(b["flags"].get(f), bool):
            errors.append(f"{slug}.{f} not boolean")
    for r in RANGE_FIELDS:
        lo, hi = b.get(r, [None, None])
        if not (isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and 0 < lo <= hi):
            errors.append(f"{slug}.{r}={b.get(r)!r}")
    if not 1 <= len(b.get("highlights", [])) <= 3:
        errors.append(f"{slug}.highlights count={len(b.get('highlights', []))}")
    for h in b.get("highlights", []):
        if len(h) > MAX_HIGHLIGHT_CHARS:
            errors.append(f"{slug}.highlight too long: {h!r}")
    if len(b.get("caveats", [])) > 2:
        errors.append(f"{slug}.caveats count={len(b['caveats'])}")
    for c in b.get("caveats", []):
        if len(c) > MAX_CAVEAT_CHARS:
            errors.append(f"{slug}.caveat too long: {c!r}")
    return errors


def build_entry(slug: str, b: dict, calc: dict, ranks: dict[str, int]) -> dict:
    page = load_json(os.path.join(BREED_DIR, f"{slug}.json"))
    meta = page["meta"]
    hero = page["images"]["hero"]["url"]
    cost = calculator_first_year(calc.get(slug))
    cost_file = os.path.join(BREED_DIR, f"{slug}-first-year-costs.json")
    cost_url = None
    if os.path.exists(cost_file):
        cost_handle = load_json(cost_file).get("meta", {}).get("shopify_handle")
        cost_url = f"{BLOG_BASE}/{cost_handle}" if cost_handle else None
    return {
        "s": slug,
        "n": meta["name"],
        "g": normalize_group(meta.get("group")),
        "img": hero,
        "w": [round(x) for x in b["weight_lbs"]],
        "ex": [round(x) for x in b["exercise_min"]],
        "sc": {d: b["scores"][d] for d in DIMS},
        "f": {short: b["flags"][long] for long, short in FLAGS.items()},
        "cost": cost,
        "hi": b["highlights"],
        "cv": b["caveats"],
        "url": f"{BLOG_BASE}/{meta.get('shopify_handle', slug)}",
        "cost_url": cost_url,
        "akc": ranks.get(slug) or ranks.get(AKC_SHARED_RANK.get(slug, "")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="validate without writing")
    args = parser.parse_args()

    scores = load_json(SCORES_PATH)
    breeds = scores["breeds"]
    overrides = load_json(OVERRIDES_PATH) if os.path.exists(OVERRIDES_PATH) else []
    apply_overrides(breeds, overrides)

    errors = [e for slug, b in breeds.items() for e in validate(slug, b)]
    if errors:
        print(f"{len(errors)} validation error(s):", *errors[:40], sep="\n  ")
        sys.exit(1)

    calc = load_json(os.path.join(ROOT, "calculator-data.json"))
    ranks = parse_akc_ranks()
    entries = [build_entry(slug, breeds[slug], calc, ranks) for slug in sorted(breeds)]
    print(f"{len(entries)} breeds valid; {len(overrides)} override(s); "
          f"{sum(1 for e in entries if e['cost'])} with cost; {sum(1 for e in entries if e['akc'])} with AKC rank")
    if args.check:
        return

    data = {"version": scores["version"], "count": len(entries), "breeds": entries}
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {OUT_PATH} ({os.path.getsize(OUT_PATH):,} bytes)")


if __name__ == "__main__":
    main()
