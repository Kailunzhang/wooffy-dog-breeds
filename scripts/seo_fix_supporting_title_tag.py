"""Recompute title_tag for all supporting pages to fit the SERP width.

Background: the 2026-07-14 full-site Scrapling audit found 71% of titles
render over 60 chars. Root cause here: the previous templates appended
keyword-stuffed appositive lists ("Grooming Guide: Brushing, Bathing,
Coat Care") that duplicate the on-page H2s and add no ranking value,
and the length budget was 65 chars — but the theme appends " - Wooffy"
(9 chars) to every ``title_tag``, so a 58-char tag renders as a 67-char
``<title>`` that Google truncates.

Fix: emit the clean head-intent form only — "{breed} Grooming Guide" —
and budget MAX_TITLE_LEN so tag + " - Wooffy" stays <=60. This script
now RECOMPUTES every supporting page and overwrites any title_tag that
differs from the clean form (it no longer skips pages that already have
one — that is exactly how the bloated titles slipped through before).

Per-type template (single clean form; the appositive lists are dropped):
  grooming-guide:    "{breed} Grooming Guide"
  first-year-costs:  "{breed} First-Year Costs"
  puppy-checklist:   "{breed} Puppy Checklist"

Breed name is resolved from the sibling main-breed JSON's ``meta.name``
(e.g., for ``shih-tzu-puppy-checklist.json`` we read ``shih-tzu.json``).
This gives properly-cased multi-word names like "German Shepherd Dog"
without guesswork.

Run:
    python3 scripts/seo_fix_supporting_title_tag.py --dry-run   # preview only
    python3 scripts/seo_fix_supporting_title_tag.py             # write local JSON
    # The list of changed slugs is printed to STDOUT (last block) -
    # capture and feed to:
    echo YES | python3 scripts/generate.py <slugs...> --update
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

TEMPLATES: dict[str, list[str]] = {
    "grooming-guide": ["{breed} Grooming Guide"],
    "first-year-costs": ["{breed} First-Year Costs"],
    "puppy-checklist": ["{breed} Puppy Checklist"],
}


def detect_suffix(stem: str) -> str | None:
    for suffix in TEMPLATES:
        if stem.endswith("-" + suffix):
            return suffix
    return None


def resolve_breed_name(stem: str, suffix: str) -> str | None:
    """Return the breed display name from the sibling main-breed JSON.

    Falls back to title-casing the slug prefix when no main JSON exists.
    """
    main_stem = stem[: -(len(suffix) + 1)]
    main_path = BREED_DATA / f"{main_stem}.json"
    if main_path.exists():
        try:
            main = json.loads(main_path.read_text(encoding="utf-8"))
            name = (main.get("meta", {}).get("name") or "").strip()
            if name:
                return name
        except (json.JSONDecodeError, OSError):
            pass
    return " ".join(part.capitalize() for part in main_stem.split("-"))


def pick_title(breed_name: str, suffix: str) -> str:
    for tmpl in TEMPLATES[suffix]:
        candidate = tmpl.format(breed=breed_name)
        if len(candidate) <= MAX_TITLE_LEN:
            return candidate
    return f"{breed_name} {suffix.replace('-', ' ').title()}"


def main() -> int:
    dry_run = "--dry-run" in sys.argv[1:]
    changed: list[tuple[str, str, str]] = []  # (stem, old, new)
    already_ok = 0
    skipped_not_supporting = 0

    for path in sorted(BREED_DATA.glob("*.json")):
        suffix = detect_suffix(path.stem)
        if suffix is None:
            skipped_not_supporting += 1
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"[parse-error] {path.name}: {e}", file=sys.stderr)
            continue

        meta = data.get("meta", {})
        breed_name = resolve_breed_name(path.stem, suffix)
        if not breed_name:
            print(f"  [skip] {path.stem}: no breed name resolvable", file=sys.stderr)
            continue

        new_title = pick_title(breed_name, suffix)
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
    print(f"  Would change / changed:        {len(changed)}", file=sys.stderr)
    print(f"  Already correct:               {already_ok}", file=sys.stderr)
    print(f"  Skipped (not supporting page): {skipped_not_supporting}", file=sys.stderr)
    print(file=sys.stderr)
    print("=== First 12 changes (old -> new) ===", file=sys.stderr)
    for stem, old, new in changed[:12]:
        shown_old = old if old else "(empty)"
        print(
            f"  {stem:50s}\n      {len(old):>2}  {shown_old}"
            f"\n      {len(new):>2}  {new}",
            file=sys.stderr,
        )
    if len(changed) > 12:
        print(f"  ... and {len(changed) - 12} more", file=sys.stderr)

    if changed and not dry_run:
        print(file=sys.stderr)
        print("Slugs to push (STDOUT):", file=sys.stderr)
        print(" ".join(s for s, _, _ in changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
