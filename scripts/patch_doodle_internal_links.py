"""Inject doodle internal-link sections into 5 roundups + golden-retriever
to fix the hub-and-spoke orphan problem identified in the SEO audit.

Idempotent: skips files that already contain the sentinel marker.
Usage: python3 scripts/patch_doodle_internal_links.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"

SENTINEL = "<!-- doodle-internal-links v1 -->"
GR_SENTINEL = "<!-- doodle-internal-links-gr-v1 -->"

DOODLE_BLURB = {
    "goldendoodle":  "Golden Retriever x Poodle. Friendly, trainable, often low-shedding.",
    "labradoodle":   "Labrador Retriever x Poodle. The original designer doodle, energetic and adaptable.",
    "bernedoodle":   "Bernese Mountain Dog x Poodle. Gentle-giant temperament with reduced shedding.",
    "cavapoo":       "Cavalier King Charles Spaniel x Poodle. Small, calm, excellent for apartments.",
    "sheepadoodle":  "Old English Sheepdog x Poodle. Playful and sturdy with a panda coat.",
    "aussiedoodle":  "Australian Shepherd x Poodle. High-energy, brilliant, often heterochromatic eyes.",
}
DOODLE_DISPLAY = {
    "goldendoodle": "Goldendoodle",
    "labradoodle": "Labradoodle",
    "bernedoodle": "Bernedoodle",
    "cavapoo": "Cavapoo",
    "sheepadoodle": "Sheepadoodle",
    "aussiedoodle": "Aussiedoodle",
}

ROUNDUP_PATCHES: dict[str, tuple[list[str], str]] = {
    "best-family-dog-breeds": (
        ["goldendoodle", "labradoodle", "bernedoodle", "cavapoo"],
        "Doodle hybrids - Poodle crosses bred specifically for low-shedding family-friendly companions - "
        "have become some of the most popular family dogs in America over the past decade. "
        "Four are particularly well suited to households with children:",
    ),
    "best-hypoallergenic-dog-breeds": (
        ["goldendoodle", "labradoodle", "bernedoodle", "cavapoo", "sheepadoodle", "aussiedoodle"],
        "Doodle hybrids are the modern low-allergen choice for households that want a friendly retriever- or "
        "herding-type temperament with a Poodle coat. Coat outcomes vary by generation - F1B and multigen "
        "produce the most reliably low-shedding dogs, while F1 outcomes are unpredictable. All six doodle "
        "hybrids covered on Wooffy:",
    ),
    "best-dogs-for-first-time-owners": (
        ["goldendoodle", "cavapoo"],
        "Two designer crossbreeds are particularly well suited to first-time owners. Both combine high "
        "trainability with calm, people-oriented temperaments:",
    ),
    "best-large-dog-breeds": (
        ["bernedoodle", "sheepadoodle"],
        "Two designer crossbreeds at the larger end of the doodle spectrum belong in any large-breed "
        "conversation. Standard versions of both regularly exceed 70 lbs:",
    ),
    "most-popular-dog-breeds": (
        ["goldendoodle", "labradoodle"],
        "Two designer crossbreeds rival the top purebreds in popularity. Both have remained in the most "
        "frequently searched dog breeds for over a decade:",
    ),
}

GR_PARAGRAPH = (
    GR_SENTINEL
    + "<h3 style=\"font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 12px 0;\">"
      "Considering a Goldendoodle Instead?</h3>"
    + "<p style=\"font-size:0.95em;line-height:1.7;color:#6b7177;margin:0;\">"
      "The <a href=\"/blogs/dog-breeds/goldendoodle\" style=\"color:#000;font-weight:600;\">Goldendoodle</a> "
      "is the most popular Golden Retriever cross - combining the Golden's family-friendly temperament with "
      "the Poodle's low-shedding coat. Many prospective Golden owners ultimately choose a Goldendoodle to "
      "mitigate Golden cancer risk and shedding, though coat outcomes vary by generation (F1 vs F1B vs "
      "multigen). See the Goldendoodle breed guide for the trade-offs.</p>"
)


def detect_card_section(data: dict) -> str | None:
    """Return the section key with the highest count of breed-anchor links (>=4)."""
    best_key: str | None = None
    best_count = 0
    for k, v in data.get("sections", {}).items():
        if not isinstance(v, dict):
            continue
        html = v.get("html", "") or ""
        n = len(re.findall(r'href="/blogs/dog-breeds/(?!best-|most-|easiest-|quietest-|longest-|rarest-|low-|dog-)', html))
        if n > best_count:
            best_count = n
            best_key = k
    return best_key if best_count >= 4 else None


def build_doodle_block(doodles: list[str], intro: str) -> str:
    items = "".join(
        f'<li><a href="/blogs/dog-breeds/{slug}" style="color:#000;font-weight:600;">'
        f'{DOODLE_DISPLAY[slug]}</a> &mdash; {DOODLE_BLURB[slug]}</li>'
        for slug in doodles
    )
    return (
        f"{SENTINEL}"
        f'<h3 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 12px 0;">'
        f"Also Worth Considering: Designer Crossbreeds</h3>"
        f'<p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 12px 0;">{intro}</p>'
        f'<ul style="font-size:0.95em;line-height:1.8;color:#6b7177;margin:0 0 16px 0;padding-left:20px;">'
        f"{items}</ul>"
        f'<p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0;">'
        f"See our full <a href=\"/blogs/dog-breeds/best-doodle-breeds-for-families\" "
        f"style=\"color:#000;font-weight:600;\">Best Doodle Breeds for Families</a> "
        f"guide for in-depth coverage of all six doodle hybrids.</p>"
    )


def patch_roundup(slug: str, doodles: list[str], intro: str) -> tuple[bool, str]:
    p = BD / f"{slug}.json"
    if not p.exists():
        return False, f"missing {p}"
    data = json.loads(p.read_text(encoding="utf-8"))
    sec_key = detect_card_section(data)
    if not sec_key:
        return False, "no breed-card section detected"
    sec = data["sections"][sec_key]
    if SENTINEL in sec.get("html", ""):
        return False, "already patched (sentinel present)"
    block = build_doodle_block(doodles, intro)
    sec["html"] = sec.get("html", "") + block
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, f"patched section {sec_key!r}; +{len(block)} chars"


def patch_golden_retriever() -> tuple[bool, str]:
    p = BD / "golden-retriever.json"
    if not p.exists():
        return False, "missing golden-retriever.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    secs = data.get("sections", {})
    target: str | None = None
    for candidate in ("finding", "right_for_you"):
        if candidate in secs:
            target = candidate
            break
    if target is None:
        keys = list(secs.keys())
        if not keys:
            return False, "no sections found"
        target = keys[-1]
    sec = secs[target]
    if GR_SENTINEL in sec.get("html", ""):
        return False, "already patched"
    sec["html"] = sec.get("html", "") + GR_PARAGRAPH
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, f"patched section {target!r}; +{len(GR_PARAGRAPH)} chars"


def main() -> int:
    print("=== Patching 5 roundups ===")
    for slug, (doodles, intro) in ROUNDUP_PATCHES.items():
        ok, msg = patch_roundup(slug, doodles, intro)
        marker = "OK " if ok else "skip"
        print(f"  [{marker}] {slug}: {msg}")
    print("\n=== Patching golden-retriever ===")
    ok, msg = patch_golden_retriever()
    marker = "OK " if ok else "skip"
    print(f"  [{marker}] golden-retriever: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
