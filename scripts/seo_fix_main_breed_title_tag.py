"""Batch-add title_tag to all main breed pages that have it empty.

Background: GSC report on 2026-06-24 surfaced cavalier-king-charles-
spaniel cannibalization — the COST supporting page was ranking #3 for
the bare breed query because the MAIN breed page had empty title_tag
while the cost page had an explicit one. Google was reading the cost
page as the more SEO-intentional result.

This pattern likely affects 158 main breed pages. Fix: set an explicit
title_tag on each, using a generic-but-strong template that signals
"this is the breed overview" and matches bare-query informational
intent.

Detection: a main breed page has `meta.size_category` ending with
" Breed" (Small Breed / Medium Breed / Large Breed / Giant Breed /
Toy Breed). Supporting articles use `meta.size_category = "Guide"`,
roundups use "Roundup", comparisons "Comparison", hubs "Guide". So
the " Breed" suffix uniquely identifies main breed pages.

Template (in priority order, picks first that fits the budget):
    1. `{name}: Temperament, Care, Health, Cost`     (preferred)
    2. `{name}: Temperament, Health, Cost`           (drops "Care")
    3. `{name}: Temperament, Health`                 (drops "Cost")
    4. `{name} Breed Guide`                          (fallback)

2026-07-14 audit fix: the theme appends " - Wooffy" (9 chars) to every
title_tag, so the budget is 51 (not 65) to keep the rendered <title>
<=60. Long breed names now correctly fall back to a shorter template
instead of rendering an over-length title. This script also RECOMPUTES
and overwrites any main-breed title_tag that differs from the target
(it no longer skips pages that already have one).

Run:
    python3 scripts/seo_fix_main_breed_title_tag.py --dry-run   # preview only
    python3 scripts/seo_fix_main_breed_title_tag.py             # write local JSON
    echo YES | python3 scripts/generate.py <list_of_changed_slugs> --update
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"

# The theme appends " - Wooffy" (9 chars) to every title_tag, so budget the
# tag at <=51 to keep the rendered <title> at or under 60 chars.
BRAND_SUFFIX_LEN = 9
MAX_TITLE_LEN = 60 - BRAND_SUFFIX_LEN  # 51

TEMPLATES = [
    "{name}: Temperament, Care, Health, Cost",
    "{name}: Temperament, Health, Cost",
    "{name}: Temperament, Health",
    "{name} Breed Guide",
]


def pick_title(breed_name: str) -> str:
    for tmpl in TEMPLATES:
        candidate = tmpl.format(name=breed_name)
        if len(candidate) <= MAX_TITLE_LEN:
            return candidate
    return breed_name


def is_main_breed_page(meta: dict) -> bool:
    size_cat = (meta.get("size_category") or "").strip()
    return size_cat.endswith(" Breed")


def main() -> int:
    dry_run = "--dry-run" in sys.argv[1:]
    changed: list[tuple[str, str, str]] = []  # (stem, old, new)
    already_ok = 0
    skipped_not_main = 0

    for path in sorted(BREED_DATA.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[parse-error] {path.name}: {e}", file=sys.stderr)
            continue

        meta = data.get("meta", {})
        if not is_main_breed_page(meta):
            skipped_not_main += 1
            continue

        breed_name = (meta.get("name") or "").strip()
        if not breed_name:
            print(f"  [skip] {path.stem}: no meta.name", file=sys.stderr)
            continue

        new_title = pick_title(breed_name)
        old_title = (meta.get("title_tag") or "").strip()
        if old_title == new_title:
            already_ok += 1
            continue

        changed.append((path.stem, old_title, new_title))
        if not dry_run:
            meta["title_tag"] = new_title
            data["meta"] = meta
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
                newline="\n",
            )

    mode = "DRY-RUN (no files written)" if dry_run else "WROTE local JSON"
    print(f"=== Summary [{mode}] ===", file=sys.stderr)
    print(f"  Would change / changed:   {len(changed)}", file=sys.stderr)
    print(f"  Already correct:          {already_ok}", file=sys.stderr)
    print(f"  Skipped (not main breed): {skipped_not_main}", file=sys.stderr)
    print(file=sys.stderr)
    print("=== Changes (old -> new) ===", file=sys.stderr)
    for slug, old, new in changed:
        shown_old = old if old else "(empty)"
        print(
            f"  {slug:46s}\n      {len(old):>2}  {shown_old}"
            f"\n      {len(new):>2}  {new}",
            file=sys.stderr,
        )

    if changed and not dry_run:
        print(file=sys.stderr)
        print("Slugs to push:", file=sys.stderr)
        print(" ".join(s for s, _, _ in changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
