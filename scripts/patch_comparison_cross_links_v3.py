"""Patch internal cross-links for the 5 v3 comparison articles + relevant main
breed pages.

Two-way:
  1. Each v3 comparison gets a "Compare More Breeds" section.
  2. Affected main breed pages get an additional "More Comparisons" block
     (uses 'comparison-links v3' sentinel so prior v1/v2 blocks stay intact).

Idempotent via sentinels.
Usage: python3 scripts/patch_comparison_cross_links_v3.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"

CMP_SENTINEL = "<!-- comparison-related-section v3 -->"
BREED_SENTINEL = "<!-- comparison-links v3 -->"

COMPARISON_RELATED: dict[str, list[tuple[str, str]]] = {
    "bernese-mountain-dog-vs-saint-bernard": [
        ("bernese-mountain-dog", "Bernese Mountain Dog full breed guide"),
        ("saint-bernard", "Saint Bernard full breed guide"),
        ("newfoundland-vs-saint-bernard", "Newfoundland vs Saint Bernard: the water specialist alternative"),
        ("bernedoodle", "Bernedoodle (the longer-lived Bernese cross)"),
        ("best-large-dog-breeds", "Best Large Dog Breeds (full roundup)"),
    ],
    "sheepadoodle-vs-bernedoodle": [
        ("sheepadoodle", "Sheepadoodle full breed guide"),
        ("bernedoodle", "Bernedoodle full breed guide"),
        ("bernedoodle-vs-goldendoodle", "Bernedoodle vs Goldendoodle: the most popular Doodle comparison"),
        ("goldendoodle-vs-labradoodle", "Goldendoodle vs Labradoodle: the original Doodle showdown"),
        ("best-doodle-breeds-for-families", "Best Doodle Breeds for Families (full roundup)"),
    ],
    "newfoundland-vs-saint-bernard": [
        ("newfoundland", "Newfoundland full breed guide"),
        ("saint-bernard", "Saint Bernard full breed guide"),
        ("bernese-mountain-dog-vs-saint-bernard", "Bernese vs Saint Bernard: the more active Swiss giant"),
        ("best-large-dog-breeds", "Best Large Dog Breeds"),
        ("best-family-dog-breeds", "Best Family Dog Breeds (both rank highly as nanny dogs)"),
    ],
    "vizsla-vs-weimaraner": [
        ("vizsla", "Vizsla full breed guide"),
        ("weimaraner", "Weimaraner full breed guide"),
        ("german-shorthaired-pointer", "German Shorthaired Pointer (a related sporting comparison)"),
        ("best-sporting-dog-breeds", "Best Sporting Dog Breeds (full roundup)"),
        ("best-hunting-dog-breeds", "Best Hunting Dog Breeds"),
    ],
    "mastiff-vs-cane-corso": [
        ("mastiff", "English Mastiff full breed guide"),
        ("cane-corso", "Cane Corso full breed guide"),
        ("rottweiler-vs-cane-corso", "Rottweiler vs Cane Corso: family-friendlier guardian"),
        ("cane-corso-vs-presa-canario", "Cane Corso vs Presa Canario: Mediterranean mastiff sibling"),
        ("bullmastiff", "Bullmastiff (the middle-ground option)"),
        ("best-guard-dog-breeds", "Best Guard Dog Breeds"),
    ],
}

BREED_COMPARES_V3: dict[str, list[tuple[str, str]]] = {
    "bernese-mountain-dog": [
        ("bernese-mountain-dog-vs-saint-bernard", "Bernese Mountain Dog vs Saint Bernard"),
    ],
    "saint-bernard": [
        ("bernese-mountain-dog-vs-saint-bernard", "Bernese Mountain Dog vs Saint Bernard"),
        ("newfoundland-vs-saint-bernard", "Newfoundland vs Saint Bernard"),
    ],
    "sheepadoodle": [
        ("sheepadoodle-vs-bernedoodle", "Sheepadoodle vs Bernedoodle"),
    ],
    "bernedoodle": [
        ("sheepadoodle-vs-bernedoodle", "Sheepadoodle vs Bernedoodle"),
    ],
    "newfoundland": [
        ("newfoundland-vs-saint-bernard", "Newfoundland vs Saint Bernard"),
    ],
    "vizsla": [
        ("vizsla-vs-weimaraner", "Vizsla vs Weimaraner"),
    ],
    "weimaraner": [
        ("vizsla-vs-weimaraner", "Vizsla vs Weimaraner"),
    ],
    "mastiff": [
        ("mastiff-vs-cane-corso", "Mastiff vs Cane Corso"),
    ],
    "cane-corso": [
        ("mastiff-vs-cane-corso", "Mastiff vs Cane Corso"),
    ],
}


def style_h3(text: str) -> str:
    return f'<h3 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 12px 0;">{text}</h3>'


def style_link_li(slug: str, text: str) -> str:
    return (
        f'<li style="margin-bottom:6px;"><a href="/blogs/dog-breeds/{slug}" '
        f'style="color:#000;font-weight:600;">{text}</a></li>'
    )


def patch_comparison(slug: str, links: list[tuple[str, str]]) -> tuple[bool, str]:
    p = BD / f"{slug}.json"
    if not p.exists():
        return False, "not found"
    d = json.loads(p.read_text(encoding="utf-8"))
    sections = d.setdefault("sections", {})
    if "related" in sections and CMP_SENTINEL in sections["related"].get("html", ""):
        return False, "already patched"
    items = "".join(style_link_li(s, t) for s, t in links)
    sections["related"] = {
        "label": "Related Reading",
        "heading": "Compare More Breeds",
        "html": (
            f'{CMP_SENTINEL}'
            f'<p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 16px 0;">'
            f'Other Wooffy guides that help refine this decision:</p>'
            f'<ul style="font-size:0.95em;line-height:1.8;color:#6b7177;margin:0;padding-left:20px;">'
            f'{items}</ul>'
        ),
    }
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, f"added 'related' section with {len(links)} links"


def patch_main_breed(slug: str, links: list[tuple[str, str]]) -> tuple[bool, str]:
    p = BD / f"{slug}.json"
    if not p.exists():
        return False, "not found"
    d = json.loads(p.read_text(encoding="utf-8"))
    sections = d.get("sections", {})
    if not sections:
        return False, "no sections"
    keys = list(sections.keys())
    target_key = keys[-1]
    target = sections[target_key]
    if not isinstance(target, dict):
        return False, f"last section {target_key!r} not a dict"
    if BREED_SENTINEL in target.get("html", ""):
        return False, "already patched"
    items = "".join(style_link_li(s, t) for s, t in links)
    block = (
        f'{BREED_SENTINEL}'
        f'{style_h3("More Comparisons")}'
        f'<ul style="font-size:0.95em;line-height:1.8;color:#6b7177;margin:0;padding-left:20px;">'
        f'{items}</ul>'
    )
    target["html"] = target.get("html", "") + block
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, f"appended to section {target_key!r}; +{len(block)} chars"


def main() -> int:
    print("=== v3 comparison articles: add 'related' sections ===")
    for slug, links in COMPARISON_RELATED.items():
        ok, msg = patch_comparison(slug, links)
        marker = "OK " if ok else "skip"
        print(f"  [{marker}] {slug}: {msg}")
    print("\n=== Main breeds: append v3 'More Comparisons' blocks ===")
    for slug, links in BREED_COMPARES_V3.items():
        ok, msg = patch_main_breed(slug, links)
        marker = "OK " if ok else "skip"
        print(f"  [{marker}] {slug}: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
