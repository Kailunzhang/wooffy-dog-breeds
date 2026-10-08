"""Rewrite templated section headings as the question a reader would ask (GEO_PLAN W2.3).

Answer engines match a passage to a query largely through its heading, so
"How much exercise and grooming does a Golden Retriever need?" is picked
up where "Care Requirements" is not. This script rewrites section
headings per article type and section key, from the breed name only; it
never touches section body text.

Rules:
  - a heading that already ends with "?" is left alone
  - mikes_take (first-person sections) and anything not in TEMPLATES is left alone
  - the previous heading is kept in sections.<key>.heading_prev for rollback
  - supporting articles take the breed name from the main guide's meta.name
  - roundups get "What are the <name>?" only when the name starts with a
    superlative (best/most/easiest/quietest/longest/rarest)

The TOC in generate.py shows the short section label (not the question)
for question headings, so the sidebar stays compact.

Usage:
    python3 scripts/geo_question_headings.py                 # dry run, all types
    python3 scripts/geo_question_headings.py --type main     # one type
    python3 scripts/geo_question_headings.py --apply         # write JSON
    python3 scripts/geo_question_headings.py --revert --apply  # restore heading_prev
    echo YES | python3 scripts/generate.py <slugs> --update --touch-updated
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BD = os.path.join(ROOT, "breed-data")
SUFFIXES = (("-grooming-guide", "grooming"), ("-first-year-costs", "costs"), ("-puppy-checklist", "checklist"))
ROUNDUP_PREFIXES = ("best ", "most ", "easiest ", "quietest ", "longest ", "rarest ")

# {type: {section_key: template}}  — {a} = a/an, {Breed} = breed name
TEMPLATES = {
    "main": {
        "intro":       "What is {a} {Breed}?",
        "appearance":  "What does {a} {Breed} look like?",
        "temperament": "What is the temperament of {a} {Breed}?",
        "care":        "How much exercise and grooming does {a} {Breed} need?",
        "health":      "What health problems are common in the {Breed}?",
        "cost":        "How much does {a} {Breed} cost?",
        "finding":     "Where can you find {a} {Breed} puppy or rescue?",
    },
    "grooming": {
        "intro": "What kind of coat does {a} {Breed} have?",
        "care":  "How often should you groom {a} {Breed}?",
    },
    "costs": {
        "intro":  "How much does {a} {Breed} cost in the first year?",
        "care":   "What are the ongoing costs of {a} {Breed}?",
        "cost":   "What does the first year with {a} {Breed} cost, month by month?",
        "health": "What health costs are specific to the {Breed}?",
    },
    "checklist": {
        "intro": "What do you need before bringing home {a} {Breed} puppy?",
        "care":  None,   # chosen by content: supplies list vs first-week vet plan
    },
}
CHECKLIST_CARE = {
    "supplies": "What supplies does {a} {Breed} puppy need?",
    "firstweek": "What should the first week with {a} {Breed} puppy look like?",
}


def load(slug):
    with open(os.path.join(BD, f"{slug}.json"), encoding="utf-8") as f:
        return json.load(f)


def save(slug, data):
    with open(os.path.join(BD, f"{slug}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def article_type(slug, data):
    m = data.get("meta") or {}
    sc = (m.get("size_category") or "").lower()
    if "body_html" in data:
        return "guide"
    if "-vs-" in slug or sc == "comparison":
        return "comparison"
    if sc == "roundup" or m.get("group") == "Breed Guides":
        return "roundup"
    for suf, kind in SUFFIXES:
        if slug.endswith(suf):
            return kind
    return "guide" if sc == "guide" else "main"


def breed_name(slug, atype, data):
    if atype == "main":
        return (data.get("meta") or {}).get("name", "")
    for suf, kind in SUFFIXES:
        if atype == kind and slug.endswith(suf):
            base = slug[: -len(suf)]
            path = os.path.join(BD, f"{base}.json")
            if os.path.exists(path):
                return (load(base).get("meta") or {}).get("name", "")
    return ""


def article(word):
    return "an" if word[:1].lower() in "aeiou" else "a"


def fill(template, name):
    return template.format(a=article(name), Breed=name)


def new_heading(atype, key, sec, name, data):
    """Return the question heading for this section, or None to leave it."""
    old = (sec.get("heading") or "").strip()
    if not old or old.rstrip().endswith("?") or key == "mikes_take":
        return None
    if atype == "roundup":
        title = (data.get("meta") or {}).get("name", "").strip()
        is_list = sec.get("label") == "The Breeds" or (key == "care" and re.match(r"^(Top\s+)?\d+\s", old))
        if is_list and title.lower().startswith(ROUNDUP_PREFIXES):
            return f"What are the {title.lower()}?"   # roundup titles are common nouns
        return None
    if not name:
        return None
    tmpl = TEMPLATES.get(atype, {}).get(key)
    if atype == "checklist" and key == "care":
        text = (old + " " + re.sub(r"<[^>]+>", " ", sec.get("html", "")[:400])).lower()
        tmpl = CHECKLIST_CARE["supplies"] if ("suppl" in old.lower() or "gear" in old.lower() or "checklist" in old.lower()) \
            else CHECKLIST_CARE["firstweek"] if ("vet" in text or "first week" in text or "week one" in text) \
            else CHECKLIST_CARE["supplies"]
    if not tmpl:
        return None
    return fill(tmpl, name)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--type", choices=("main", "grooming", "costs", "checklist", "roundup"))
    ap.add_argument("--slug", action="append")
    ap.add_argument("--apply", action="store_true", help="write the JSON files")
    ap.add_argument("--revert", action="store_true", help="restore heading_prev instead of rewriting")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    slugs = args.slug or sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(BD, "*.json")))
    changed_files = 0
    changed = Counter()
    seen = Counter()
    for slug in slugs:
        data = load(slug)
        atype = article_type(slug, data)
        if atype in ("guide", "comparison") or (args.type and atype != args.type):
            continue
        name = breed_name(slug, atype, data)
        sections = data.get("sections") or {}
        touched = False
        for key, sec in sections.items():
            if not isinstance(sec, dict):
                continue
            if args.revert:
                if sec.get("heading_prev"):
                    sec["heading"] = sec.pop("heading_prev")
                    touched = True
                    changed[f"{atype}.{key}"] += 1
                continue
            q = new_heading(atype, key, sec, name, data)
            seen[f"{atype}.{key}"] += 1
            if not q or q == sec.get("heading"):
                continue
            if not args.quiet:
                print(f"{slug} [{key}]\n    {sec.get('heading')}\n  → {q}")
            if "heading_prev" not in sec:
                sec["heading_prev"] = sec["heading"]
            sec["heading"] = q
            touched = True
            changed[f"{atype}.{key}"] += 1
        if touched:
            changed_files += 1
            if args.apply:
                save(slug, data)
    verb = "wrote" if args.apply else "would change"
    print(f"\n{verb} {sum(changed.values())} headings in {changed_files} articles")
    for k, n in sorted(changed.items()):
        print(f"  {k:<22}{n:>5} / {seen[k]}")
    if not args.apply and changed:
        print("dry run; add --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
