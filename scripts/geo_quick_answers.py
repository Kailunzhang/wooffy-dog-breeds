"""Generate meta.quick_answer for breed-cluster articles (GEO_PLAN W2.1).

The quick answer is a 50-80 word direct answer rendered by
generate.py's build_quick_answer() right under the intro heading. Every
number in it comes from data the page or the repo already holds; nothing
is invented and no API is called.

Types implemented:
  main    172 breed guides: stats (size, group, weight, lifespan, exercise,
          grooming, training, kids, beginners) + first-year cost range from
          costs-dataset.json when the breed is in it.
  costs   164 first-year-cost pages: costs-dataset.json[slug].citable_stat.
          ** Do not --apply before the cost-title A/B read-out (2026-10-29);
          ** push test and control pages together afterwards.
Types grooming / checklist / roundup / comparison are planned (see
GEO_PLAN.md 2.1) and not implemented yet.

Articles whose intro already carries a hand-built quick answer (v1 marker)
are skipped. Existing meta.quick_answer values are kept unless --overwrite.

Usage:
    python3 scripts/geo_quick_answers.py --type main             # dry run: print answers
    python3 scripts/geo_quick_answers.py --type main --apply     # write meta.quick_answer
    python3 scripts/geo_quick_answers.py --type main --slug akita --slug pug
    echo YES | python3 scripts/generate.py <slugs...> --update   # push to Shopify
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BD = os.path.join(ROOT, "breed-data")
COSTS = os.path.join(ROOT, "costs-dataset.json")
SUFFIXES = ("-grooming-guide", "-first-year-costs", "-puppy-checklist")


# ---------------------------------------------------------------- helpers
def load(slug: str) -> dict:
    with open(os.path.join(BD, f"{slug}.json"), encoding="utf-8") as f:
        return json.load(f)


def save(slug: str, data: dict) -> None:
    with open(os.path.join(BD, f"{slug}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def all_slugs() -> list[str]:
    return sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(BD, "*.json")))


def article_type(slug: str, data: dict) -> str:
    m = data.get("meta") or {}
    sc = (m.get("size_category") or "").lower()
    if "body_html" in data:
        return "guide"
    if "-vs-" in slug or sc == "comparison":
        return "comparison"
    if sc == "roundup" or m.get("group") == "Breed Guides":
        return "roundup"
    for suf, kind in zip(SUFFIXES, ("grooming", "costs", "checklist")):
        if slug.endswith(suf):
            return kind
    return "guide" if sc == "guide" else "main"


def has_v1_box(data: dict) -> bool:
    intro = (data.get("sections") or {}).get("intro") or {}
    return "WOOFFY_QUICK_ANSWER" in (intro.get("html") or "")


def word_count(text: str) -> int:
    return len(text.split())


def norm_dash(s: str) -> str:
    return s.replace("–", "-").replace("—", "-")


def lower_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s else s


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


# ---------------------------------------------------------------- main guides
BEGINNER_YES = ("yes",)
BEGINNER_MAYBE = ("caution", "with research", "manageable", "with patience", "with guidance",
                  "with commitment", "research required", "yes, with research", "yes, if active",
                  "yes*", "possible", "with preparation", "with experience", "if active")
BEGINNER_NO = ("no", "not ideal", "not recommended", "experts only", "experienced only", "not for beginners")
KIDS_GOOD = ("excellent", "very good", "good", "good with family", "generally good", "gentle", "great")
KIDS_CAREFUL = ("caution", "with supervision", "older kids", "older children", "family only",
                "experienced only", "supervision", "best with older")


def _match(value: str, table: tuple[str, ...]) -> bool:
    v = value.lower().strip()
    return any(v == t or v.startswith(t) or t in v for t in table)


def beginner_sentence(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if _match(v, BEGINNER_NO):
        return "It is not recommended for first-time owners."
    if _match(v, BEGINNER_MAYBE):
        return "First-time owners can manage one with research and commitment."
    if _match(v, BEGINNER_YES):
        return "It is a realistic choice for a first-time owner."
    return ""


def kids_phrase(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if _match(v, KIDS_CAREFUL):
        return "best with older children and supervision"
    if _match(v, KIDS_GOOD):
        return "good with kids"
    return ""


def clean_group(group: str) -> str:
    g = re.sub(r"\s*\(.*?\)", "", group or "").replace(" Group", "").strip()
    return g.lower()


def clean_size(size: str, size_category: str) -> str:
    s = (size or "").strip()
    if not s or s.lower() == "varies" or "/" in s:
        s = (size_category or "").replace(" Breed", "").strip()
    s = norm_dash(s).replace(" to ", "-").lower()
    return s


def exercise_phrase(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    v = re.sub(r"\s*/\s*day$", "", v)
    # Only plain durations ("60–90 min", "2+ hrs", "About 60 min") read well
    # inside the sentence; anything else ("Sprint + rest") gets a label.
    if re.fullmatch(r"(?i)(about\s+)?\d[\d\u2013\-+ ]*(min|mins|minutes|hrs?|hours?)", v):
        v = re.sub(r"^About\s+", "about ", v)
        return f"Plan on {v} of exercise a day."
    return f"Exercise needs: {lower_first(v)}."


def grooming_phrase(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    core = re.sub(r"\s*\(.*?\)", "", v).strip()
    core = re.sub(r"(?i)\bmod\b", "moderate", core)
    note = re.search(r"\((.*?)\)", v)
    s = f"Grooming is {core.lower()}"
    if note:
        s += f" ({note.group(1)})"
    return s


def training_phrase(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    core = re.sub(r"\s*\(.*?\)", "", v).strip().lower()
    note = re.search(r"\((.*?)\)", v)
    s = f"training is {core}"
    if note:
        s += f" ({note.group(1)})"
    return s


def main_answer(slug: str, data: dict, costs: dict) -> str | None:
    m = data.get("meta") or {}
    st = data.get("stats") or {}
    if not st:
        return None
    name = m.get("name") or slug.replace("-", " ").title()
    val = lambda k: (st.get(k) or {}).get("value", "")  # noqa: E731
    size = clean_size(val("size"), m.get("size_category", ""))
    group = clean_group(m.get("group", ""))
    if not group:
        kind = f"{size} dog"
    elif size == group:                       # "Toy" size in the Toy group
        kind = f"{group}-group dog"
    elif group in ("terrier", "hound"):
        kind = f"{size} {group}"
    elif "crossbreed" in group:
        kind = f"{size} designer crossbreed"
    else:
        kind = f"{size} {group} dog"
    kind = re.sub(r"\s+", " ", kind).strip()
    parts = [f"The {name} is {_article(kind)} {kind}"]
    weight, life = val("weight"), val("lifespan")
    tail = []
    if weight:
        tail.append(f"weighing {weight}")
    if life:
        tail.append(f"living {life.replace('yrs', 'years')}")
    if tail:
        parts[0] += ", " + " and ".join(tail)
    parts[0] += "."
    ex = exercise_phrase(val("exercise"))
    if ex:
        parts.append(ex)
    g, t = grooming_phrase(val("grooming")), training_phrase(val("training"))
    if g and t:
        parts.append(f"{g}; {t}.")
    elif g or t:
        parts.append((g or t[:1].upper() + t[1:]) + ".")
    kids = kids_phrase(val("with_kids"))
    beg = beginner_sentence(val("beginners"))
    if kids and beg:
        parts.append(f"It is {kids}. {beg}")
    elif kids:
        parts.append(f"It is {kids}.")
    elif beg:
        parts.append(beg)
    c = costs.get(slug) or {}
    y1 = c.get("total_year1")
    if y1 and len(y1) == 2 and all(isinstance(x, (int, float)) for x in y1):
        parts.append(f"Budget about ${int(y1[0]):,}–${int(y1[1]):,} for the first year.")
    return " ".join(parts)


# ---------------------------------------------------------------- cost pages
def costs_answer(slug: str, data: dict, costs: dict) -> str | None:
    base = slug[: -len("-first-year-costs")]
    row = costs.get(base) or {}
    stat = (row.get("citable_stat") or "").strip()
    if not stat:
        return None
    ongoing = row.get("annual_ongoing")
    if ongoing and len(ongoing) == 2 and all(isinstance(x, (int, float)) for x in ongoing) \
            and "ongoing" not in stat.lower() and "after the first year" not in stat.lower():
        stat += f" After the first year, expect roughly ${int(ongoing[0]):,}\u2013${int(ongoing[1]):,} a year in ongoing costs."
    return stat


GENERATORS = {"main": main_answer, "costs": costs_answer}


# ---------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--type", required=True, choices=("main", "costs", "grooming", "checklist", "roundup", "comparison"))
    ap.add_argument("--slug", action="append", help="restrict to these slugs (repeatable)")
    ap.add_argument("--apply", action="store_true", help="write meta.quick_answer into the JSON files")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing meta.quick_answer")
    ap.add_argument("--quiet", action="store_true", help="only print the summary line")
    args = ap.parse_args(argv)

    if args.type not in GENERATORS:
        sys.exit(f"--type {args.type} is planned but not implemented yet (see GEO_PLAN.md 2.1)")
    with open(COSTS, encoding="utf-8") as f:
        costs = json.load(f)
    gen = GENERATORS[args.type]

    slugs = args.slug or all_slugs()
    done = skipped = kept = short = long_ = 0
    for slug in slugs:
        data = load(slug)
        if article_type(slug, data) != args.type:
            continue
        if has_v1_box(data):
            skipped += 1
            if not args.quiet:
                print(f"SKIP {slug}: intro already has a hand-built quick answer")
            continue
        if data["meta"].get("quick_answer") and not args.overwrite:
            kept += 1
            continue
        text = gen(slug, data, costs)
        if not text:
            skipped += 1
            if not args.quiet:
                print(f"SKIP {slug}: no source data")
            continue
        n = word_count(text)
        short += n < 40
        long_ += n > 90
        if not args.quiet:
            flag = "  [SHORT]" if n < 40 else ("  [LONG]" if n > 90 else "")
            print(f"{slug} ({n} words){flag}\n  {text}")
        if args.apply:
            data["meta"]["quick_answer"] = text
            save(slug, data)
        done += 1
    verb = "wrote" if args.apply else "would write"
    print(f"\n{verb} {done} quick answers (type={args.type}); kept existing {kept}; skipped {skipped}; "
          f"under 40 words {short}; over 90 words {long_}")
    if not args.apply and done:
        print("dry run only; add --apply to write meta.quick_answer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
