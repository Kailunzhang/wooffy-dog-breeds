"""Patch internal cross-links for the 5 v4 comparison articles + relevant main
breed pages.

Two-way:
  1. Each v4 comparison gets a "Compare More Breeds" section.
  2. Affected main breed pages get an additional "More Comparisons" block
     (uses 'comparison-links v4' sentinel so prior v1/v2/v3 blocks stay intact).

Idempotent via sentinels.
Usage: python3 scripts/patch_comparison_cross_links_v4.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"

CMP_SENTINEL = "<!-- comparison-related-section v4 -->"
BREED_SENTINEL = "<!-- comparison-links v4 -->"

COMPARISON_RELATED: dict[str, list[tuple[str, str]]] = {
    "golden-retriever-vs-german-shepherd": [
        ("golden-retriever", "Golden Retriever full breed guide"),
        ("german-shepherd-dog", "German Shepherd full breed guide"),
        ("labrador-retriever-vs-golden-retriever", "Lab vs Golden Retriever: the friendlier alternative"),
        ("german-shepherd-vs-doberman", "German Shepherd vs Doberman: working breed comparison"),
        ("best-family-dog-breeds", "Best Family Dog Breeds (full roundup)"),
    ],
    "cane-corso-vs-great-dane": [
        ("cane-corso", "Cane Corso full breed guide"),
        ("great-dane", "Great Dane full breed guide"),
        ("mastiff-vs-cane-corso", "Mastiff vs Cane Corso: heavier mastiff alternative"),
        ("rottweiler-vs-cane-corso", "Rottweiler vs Cane Corso: family-friendlier guardian"),
        ("great-dane-vs-doberman", "Great Dane vs Doberman: the protective alternative"),
        ("best-large-dog-breeds", "Best Large Dog Breeds"),
    ],
    "bernedoodle-vs-aussiedoodle": [
        ("bernedoodle", "Bernedoodle full breed guide"),
        ("aussiedoodle", "Aussiedoodle full breed guide"),
        ("sheepadoodle-vs-bernedoodle", "Sheepadoodle vs Bernedoodle: doodle comparison"),
        ("bernedoodle-vs-goldendoodle", "Bernedoodle vs Goldendoodle: the most popular doodle pairing"),
        ("best-doodle-breeds-for-families", "Best Doodle Breeds for Families (full roundup)"),
    ],
    "vizsla-vs-german-shorthaired-pointer": [
        ("vizsla", "Vizsla full breed guide"),
        ("german-shorthaired-pointer", "German Shorthaired Pointer full breed guide"),
        ("vizsla-vs-weimaraner", "Vizsla vs Weimaraner: gray ghost alternative"),
        ("best-sporting-dog-breeds", "Best Sporting Dog Breeds (full roundup)"),
        ("best-hunting-dog-breeds", "Best Hunting Dog Breeds"),
    ],
    "great-dane-vs-doberman": [
        ("great-dane", "Great Dane full breed guide"),
        ("doberman-pinscher", "Doberman Pinscher full breed guide"),
        ("cane-corso-vs-great-dane", "Cane Corso vs Great Dane: guardian comparison"),
        ("rottweiler-vs-doberman-pinscher", "Rottweiler vs Doberman: the bigger alternative"),
        ("german-shepherd-vs-doberman", "German Shepherd vs Doberman: working breed comparison"),
        ("best-guard-dog-breeds", "Best Guard Dog Breeds"),
    ],
}

BREED_COMPARES_V4: dict[str, list[tuple[str, str]]] = {
    "golden-retriever": [
        ("golden-retriever-vs-german-shepherd", "Golden Retriever vs German Shepherd"),
    ],
    "german-shepherd-dog": [
        ("golden-retriever-vs-german-shepherd", "Golden Retriever vs German Shepherd"),
    ],
    "cane-corso": [
        ("cane-corso-vs-great-dane", "Cane Corso vs Great Dane"),
    ],
    "great-dane": [
        ("cane-corso-vs-great-dane", "Cane Corso vs Great Dane"),
        ("great-dane-vs-doberman", "Great Dane vs Doberman"),
    ],
    "bernedoodle": [
        ("bernedoodle-vs-aussiedoodle", "Bernedoodle vs Aussiedoodle"),
    ],
    "aussiedoodle": [
        ("bernedoodle-vs-aussiedoodle", "Bernedoodle vs Aussiedoodle"),
    ],
    "vizsla": [
        ("vizsla-vs-german-shorthaired-pointer", "Vizsla vs German Shorthaired Pointer"),
    ],
    "german-shorthaired-pointer": [
        ("vizsla-vs-german-shorthaired-pointer", "Vizsla vs German Shorthaired Pointer"),
    ],
    "doberman-pinscher": [
        ("great-dane-vs-doberman", "Great Dane vs Doberman"),
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
    print("=== v4 comparison articles: add 'related' sections ===")
    for slug, links in COMPARISON_RELATED.items():
        ok, msg = patch_comparison(slug, links)
        marker = "OK " if ok else "skip"
        print(f"  [{marker}] {slug}: {msg}")
    print("\n=== Main breeds: append v4 'More Comparisons' blocks ===")
    for slug, links in BREED_COMPARES_V4.items():
        ok, msg = patch_main_breed(slug, links)
        marker = "OK " if ok else "skip"
        print(f"  [{marker}] {slug}: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
