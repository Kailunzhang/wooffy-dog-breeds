"""Patch internal cross-links for the 5 v2 comparison articles + relevant main
breed pages.

Two-way:
  1. Each v2 comparison gets a "Compare More Breeds" section.
  2. Affected main breed pages get an additional "More Comparisons" block
     (uses 'comparison-links v2' sentinel so the prior v1 block stays intact).

Idempotent via sentinels.
Usage: python3 scripts/patch_comparison_cross_links_v2.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"

CMP_SENTINEL = "<!-- comparison-related-section v2 -->"
BREED_SENTINEL = "<!-- comparison-links v2 -->"

COMPARISON_RELATED: dict[str, list[tuple[str, str]]] = {
    "rottweiler-vs-cane-corso": [
        ("rottweiler", "Rottweiler full breed guide"),
        ("cane-corso", "Cane Corso full breed guide"),
        ("rottweiler-vs-doberman-pinscher", "Rottweiler vs Doberman: family-friendly alternative"),
        ("cane-corso-vs-presa-canario", "Cane Corso vs Presa Canario: the Iberian mastiff option"),
        ("best-guard-dog-breeds", "Best Guard Dog Breeds (full roundup)"),
    ],
    "cane-corso-vs-presa-canario": [
        ("cane-corso", "Cane Corso full breed guide"),
        ("rottweiler-vs-cane-corso", "Rottweiler vs Cane Corso: family-integratable option"),
        ("best-guard-dog-breeds", "Best Guard Dog Breeds"),
        ("best-watchdog-breeds", "Best Watchdog Breeds"),
        ("most-protective-dog-breeds", "Most Protective Dog Breeds"),
    ],
    "german-shepherd-vs-doberman": [
        ("german-shepherd-dog", "German Shepherd full breed guide"),
        ("doberman-pinscher", "Doberman Pinscher full breed guide"),
        ("rottweiler-vs-doberman-pinscher", "Rottweiler vs Doberman: the heavier alternative"),
        ("best-watchdog-breeds", "Best Watchdog Breeds"),
        ("most-loyal-dog-breeds", "Most Loyal Dog Breeds"),
    ],
    "rottweiler-vs-doberman-pinscher": [
        ("rottweiler", "Rottweiler full breed guide"),
        ("doberman-pinscher", "Doberman Pinscher full breed guide"),
        ("rottweiler-vs-cane-corso", "Rottweiler vs Cane Corso: the larger guardian option"),
        ("german-shepherd-vs-doberman", "German Shepherd vs Doberman: heavier alternative"),
        ("best-guard-dog-breeds", "Best Guard Dog Breeds"),
    ],
    "border-collie-vs-australian-shepherd": [
        ("border-collie", "Border Collie full breed guide"),
        ("australian-shepherd", "Australian Shepherd full breed guide"),
        ("best-herding-dog-breeds", "Best Herding Dog Breeds (full roundup)"),
        ("easiest-dogs-to-train", "Easiest Dogs to Train (both rank highly)"),
        ("most-intelligent-dog-breeds", "Most Intelligent Dog Breeds"),
    ],
}

BREED_COMPARES_V2: dict[str, list[tuple[str, str]]] = {
    "rottweiler": [
        ("rottweiler-vs-cane-corso", "Rottweiler vs Cane Corso"),
        ("rottweiler-vs-doberman-pinscher", "Rottweiler vs Doberman Pinscher"),
    ],
    "cane-corso": [
        ("rottweiler-vs-cane-corso", "Rottweiler vs Cane Corso"),
        ("cane-corso-vs-presa-canario", "Cane Corso vs Presa Canario"),
    ],
    "german-shepherd-dog": [
        ("german-shepherd-vs-doberman", "German Shepherd vs Doberman"),
    ],
    "doberman-pinscher": [
        ("rottweiler-vs-doberman-pinscher", "Rottweiler vs Doberman"),
        ("german-shepherd-vs-doberman", "German Shepherd vs Doberman"),
    ],
    "border-collie": [
        ("border-collie-vs-australian-shepherd", "Border Collie vs Australian Shepherd"),
    ],
    "australian-shepherd": [
        ("border-collie-vs-australian-shepherd", "Border Collie vs Australian Shepherd"),
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
    print("=== v2 comparison articles: add 'related' sections ===")
    for slug, links in COMPARISON_RELATED.items():
        ok, msg = patch_comparison(slug, links)
        marker = "OK " if ok else "skip"
        print(f"  [{marker}] {slug}: {msg}")
    print("\n=== Main breeds: append v2 'More Comparisons' blocks ===")
    for slug, links in BREED_COMPARES_V2.items():
        ok, msg = patch_main_breed(slug, links)
        marker = "OK " if ok else "skip"
        print(f"  [{marker}] {slug}: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
