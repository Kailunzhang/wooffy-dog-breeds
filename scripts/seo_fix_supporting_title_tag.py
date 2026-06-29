"""Batch-add title_tag to all supporting pages that have it empty.

Background: 6/28 GSC digest surfaced two supporting pages
(shih-tzu-puppy-checklist, wirehaired-pointing-griffon-grooming-guide)
with rank drops driven by the same root cause as the 6/24 main-breed
batch — empty title_tag so Shopify falls back to the bare meta.name.

Audit shows 464 of 492 supporting articles (grooming-guide /
first-year-costs / puppy-checklist) still have empty title_tag.
This is the same systematic bug; this script applies the same fix
pattern at scale.

Per-type templates (priority order, picks first that fits 65 chars):
  grooming-guide:    "{breed} Grooming Guide: Brushing, Bathing, Coat Care"
                     "{breed} Grooming Guide: Brushing & Coat Care"
                     "{breed} Grooming Guide"
  first-year-costs:  "{breed} First-Year Costs: Puppy, Vet, Food, Setup"
                     "{breed} First-Year Costs: Vet, Food, Setup"
                     "{breed} First-Year Costs"
  puppy-checklist:   "{breed} Puppy Checklist: Supplies, Week 1 Plan & Setup"
                     "{breed} Puppy Checklist: Supplies & Week 1 Plan"
                     "{breed} Puppy Checklist"

Breed name is resolved from the sibling main-breed JSON's ``meta.name``
(e.g., for ``shih-tzu-puppy-checklist.json`` we read ``shih-tzu.json``).
This gives properly-cased multi-word names like "German Shepherd Dog"
without guesswork.

Run:
    python3 scripts/seo_fix_supporting_title_tag.py
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
MAX_TITLE_LEN = 65

TEMPLATES: dict[str, list[str]] = {
    "grooming-guide": [
        "{breed} Grooming Guide: Brushing, Bathing, Coat Care",
        "{breed} Grooming Guide: Brushing & Coat Care",
        "{breed} Grooming Guide",
    ],
    "first-year-costs": [
        "{breed} First-Year Costs: Puppy, Vet, Food, Setup",
        "{breed} First-Year Costs: Vet, Food, Setup",
        "{breed} First-Year Costs",
    ],
    "puppy-checklist": [
        "{breed} Puppy Checklist: Supplies, Week 1 Plan & Setup",
        "{breed} Puppy Checklist: Supplies & Week 1 Plan",
        "{breed} Puppy Checklist",
    ],
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
    changed: list[tuple[str, str]] = []
    skipped_has_title = 0
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
        if (meta.get("title_tag") or "").strip():
            skipped_has_title += 1
            continue

        breed_name = resolve_breed_name(path.stem, suffix)
        if not breed_name:
            print(f"  [skip] {path.stem}: no breed name resolvable", file=sys.stderr)
            continue

        new_title = pick_title(breed_name, suffix)
        meta["title_tag"] = new_title
        data["meta"] = meta
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
        changed.append((path.stem, new_title))

    print("=== Summary ===", file=sys.stderr)
    print(f"  Changed:                       {len(changed)}", file=sys.stderr)
    print(f"  Skipped (had title_tag):       {skipped_has_title}", file=sys.stderr)
    print(f"  Skipped (not supporting page): {skipped_not_supporting}", file=sys.stderr)
    print(file=sys.stderr)
    print("=== First 10 changed ===", file=sys.stderr)
    for stem, title in changed[:10]:
        print(f"  {stem:55s}  -> {title}", file=sys.stderr)
    if len(changed) > 10:
        print(f"  ... and {len(changed) - 10} more", file=sys.stderr)

    if changed:
        print(file=sys.stderr)
        print("Slugs to push (STDOUT):", file=sys.stderr)
        print(" ".join(s for s, _ in changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
