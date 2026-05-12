"""Patch internal cross-links between comparison articles and main breed pages.

Two-way:
  1. Each comparison article gets a "Compare More Breeds" section linking back
     to the two compared breeds + related comparisons + relevant roundups.
  2. Each compared main breed page gets a "Compare with Other Breeds" subsection
     appended to its last section, linking to relevant comparisons.

Idempotent via sentinels.
Usage: python3 scripts/patch_comparison_cross_links.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"

CMP_SENTINEL = "<!-- comparison-related-section v1 -->"
BREED_SENTINEL = "<!-- comparison-links v1 -->"

COMPARISON_RELATED: dict[str, list[tuple[str, str]]] = {
    "goldendoodle-vs-labradoodle": [
        ("goldendoodle", "Goldendoodle full breed guide"),
        ("labradoodle", "Labradoodle full breed guide"),
        ("standard-poodle-vs-goldendoodle", "Standard Poodle vs Goldendoodle: which is more reliably low-shedding"),
        ("bernedoodle-vs-goldendoodle", "Bernedoodle vs Goldendoodle: gentler temperament option"),
        ("best-doodle-breeds-for-families", "Best Doodle Breeds for Families (full roundup)"),
    ],
    "labrador-retriever-vs-golden-retriever": [
        ("labrador-retriever", "Labrador Retriever full breed guide"),
        ("golden-retriever", "Golden Retriever full breed guide"),
        ("goldendoodle-vs-labradoodle", "Goldendoodle vs Labradoodle (the doodle alternatives)"),
        ("best-family-dog-breeds", "Best Family Dog Breeds (full roundup)"),
        ("best-hunting-dog-breeds", "Best Hunting Dog Breeds (both excel here)"),
    ],
    "bernedoodle-vs-goldendoodle": [
        ("bernedoodle", "Bernedoodle full breed guide"),
        ("goldendoodle", "Goldendoodle full breed guide"),
        ("goldendoodle-vs-labradoodle", "Goldendoodle vs Labradoodle (the other top doodle comparison)"),
        ("best-doodle-breeds-for-families", "Best Doodle Breeds for Families"),
        ("best-large-dog-breeds", "Best Large Dog Breeds (for the Standard Bernedoodle)"),
    ],
    "cavapoo-vs-cockapoo": [
        ("cavapoo", "Cavapoo full breed guide"),
        ("cavalier-king-charles-spaniel", "Cavalier King Charles Spaniel (the purebred parent)"),
        ("cocker-spaniel", "Cocker Spaniel (the Cockapoo's purebred parent)"),
        ("standard-poodle", "Standard Poodle (the shared parent breed)"),
        ("best-small-dog-breeds", "Best Small Dog Breeds (full roundup)"),
    ],
    "standard-poodle-vs-goldendoodle": [
        ("standard-poodle", "Standard Poodle full breed guide"),
        ("goldendoodle", "Goldendoodle full breed guide"),
        ("goldendoodle-vs-labradoodle", "Goldendoodle vs Labradoodle"),
        ("best-hypoallergenic-dog-breeds", "Best Hypoallergenic Dog Breeds (both feature here)"),
    ],
}

BREED_COMPARES: dict[str, list[tuple[str, str]]] = {
    "goldendoodle": [
        ("goldendoodle-vs-labradoodle", "Goldendoodle vs Labradoodle"),
        ("standard-poodle-vs-goldendoodle", "Standard Poodle vs Goldendoodle"),
        ("bernedoodle-vs-goldendoodle", "Bernedoodle vs Goldendoodle"),
    ],
    "labradoodle": [
        ("goldendoodle-vs-labradoodle", "Goldendoodle vs Labradoodle"),
    ],
    "bernedoodle": [
        ("bernedoodle-vs-goldendoodle", "Bernedoodle vs Goldendoodle"),
    ],
    "cavapoo": [
        ("cavapoo-vs-cockapoo", "Cavapoo vs Cockapoo"),
    ],
    "standard-poodle": [
        ("standard-poodle-vs-goldendoodle", "Standard Poodle vs Goldendoodle"),
    ],
    "labrador-retriever": [
        ("labrador-retriever-vs-golden-retriever", "Labrador vs Golden Retriever"),
        ("goldendoodle-vs-labradoodle", "Goldendoodle vs Labradoodle (the doodle alternative)"),
    ],
    "golden-retriever": [
        ("labrador-retriever-vs-golden-retriever", "Labrador vs Golden Retriever"),
    ],
    "cocker-spaniel": [
        ("cavapoo-vs-cockapoo", "Cavapoo vs Cockapoo"),
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
        f'{style_h3("Compare with Other Breeds")}'
        f'<p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 12px 0;">'
        f'Choosing between two breeds? Head-to-head comparisons:</p>'
        f'<ul style="font-size:0.95em;line-height:1.8;color:#6b7177;margin:0;padding-left:20px;">'
        f'{items}</ul>'
    )
    target["html"] = target.get("html", "") + block
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, f"appended to section {target_key!r}; +{len(block)} chars"


def main() -> int:
    print("=== Comparison articles: add 'related' sections ===")
    for slug, links in COMPARISON_RELATED.items():
        ok, msg = patch_comparison(slug, links)
        marker = "OK " if ok else "skip"
        print(f"  [{marker}] {slug}: {msg}")
    print("\n=== Main breeds: append Compare-with subsections ===")
    for slug, links in BREED_COMPARES.items():
        ok, msg = patch_main_breed(slug, links)
        marker = "OK " if ok else "skip"
        print(f"  [{marker}] {slug}: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
