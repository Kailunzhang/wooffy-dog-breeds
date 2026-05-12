"""Replace generic image alt text with descriptive alts for SEO + accessibility.

Reads breed_traits.json (coat/puppy_coat/grooming_action per breed) and writes
new alts into each breed JSON's images.hero.alt + images.secondary[*].alt.

Skips roundups (their existing alts are descriptive of the topic).

Phase 1 only - local mutation, no Shopify push. Run a follow-up batch script
or generate.py --update to propagate to Shopify.

Usage: python3 scripts/generate_descriptive_alts.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"
TRAITS_PATH = ROOT / "breed_traits.json"

ROUNDUP_PREFIXES = ("best-", "most-", "easiest-", "quietest-", "longest-", "rarest-", "low-", "dog-breeds-")
SUFFIXES = ("-grooming-guide", "-first-year-costs", "-puppy-checklist")

HERO_TEMPLATES = {
    "main":               "Adult {name} with {coat}, professional pet photograph",
    "-grooming-guide":    "{name} being groomed, showing the {coat} texture",
    "-first-year-costs":  "Adult {name} relaxing at home in a family setting",
    "-puppy-checklist":   "Eight-week-old {name} puppy with {puppy_coat}",
}

SECONDARY_TEMPLATES = {
    "before_temperament": "{name} relaxing at home in a sunlit family setting",
    "before_care":        "{name} being brushed and groomed at home",
    "before_finding":     "Eight-week-old {name} puppy looking curiously at the camera",
}


def is_roundup(slug: str) -> bool:
    return any(slug.startswith(p) for p in ROUNDUP_PREFIXES)


def article_kind(slug: str) -> tuple[str, str]:
    """Return (kind, base_slug). kind in {'roundup','main','-grooming-guide',...}"""
    if is_roundup(slug):
        return "roundup", slug
    for suf in SUFFIXES:
        if slug.endswith(suf):
            return suf, slug[: -len(suf)]
    return "main", slug


def compute_hero_alt(slug: str, name: str, traits: dict[str, dict]) -> str | None:
    kind, base = article_kind(slug)
    if kind == "roundup":
        return None
    t = traits.get(base, {})
    coat = t.get("coat") or "a glossy coat"
    puppy_coat = t.get("puppy_coat") or "a soft puppy coat"
    bname = t.get("name") or name
    tmpl = HERO_TEMPLATES["main" if kind == "main" else kind]
    return tmpl.format(name=bname, coat=coat, puppy_coat=puppy_coat)


def compute_secondary_alts(slug: str, name: str, traits: dict[str, dict]) -> dict[str, str]:
    """Only for main breed articles. Maps placement -> new alt."""
    kind, base = article_kind(slug)
    if kind != "main":
        return {}
    t = traits.get(base, {})
    bname = t.get("name") or name
    return {placement: tmpl.format(name=bname) for placement, tmpl in SECONDARY_TEMPLATES.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    traits_list = json.loads(TRAITS_PATH.read_text(encoding="utf-8"))
    traits = {t["slug"]: t for t in traits_list}
    print(f"Loaded {len(traits)} breed_traits entries.")

    files = sorted(f for f in os.listdir(BD) if f.endswith(".json"))
    hero_changed = 0
    secondary_changed = 0
    roundup_skipped = 0
    no_traits = 0
    sample = []

    for fn in files:
        p = BD / fn
        d = json.loads(p.read_text(encoding="utf-8"))
        slug = fn[:-5]
        name = d.get("meta", {}).get("name", "")

        if is_roundup(slug):
            roundup_skipped += 1
            continue

        new_hero = compute_hero_alt(slug, name, traits)
        if new_hero is None:
            no_traits += 1
            continue

        images = d.setdefault("images", {})
        hero = images.setdefault("hero", {})
        if hero.get("alt") != new_hero:
            hero["alt"] = new_hero
            hero_changed += 1
            if len(sample) < 5:
                sample.append((slug, new_hero))

        secs = compute_secondary_alts(slug, name, traits)
        if secs:
            secondary = images.get("secondary")
            if isinstance(secondary, list):
                for entry in secondary:
                    placement = entry.get("placement")
                    new_alt = secs.get(placement)
                    if new_alt and entry.get("alt") != new_alt:
                        entry["alt"] = new_alt
                        secondary_changed += 1

        if not args.dry_run:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nResults:")
    print(f"  hero alts changed:      {hero_changed}")
    print(f"  secondary alts changed: {secondary_changed}")
    print(f"  roundups skipped:       {roundup_skipped}")
    print(f"  no traits (skipped):    {no_traits}")
    if sample:
        print(f"\nSample hero alt changes:")
        for slug, alt in sample:
            print(f"  {slug:<42} -> {alt!r}")
    if args.dry_run:
        print("\n(dry-run, nothing written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
