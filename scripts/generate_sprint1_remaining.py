"""One-shot: build pinterest-sprint-1-remaining.md.

Cross-references the 40 Sprint 1 pins against the 13 confirmed posted
(identified by title from the user's 2026-08-26 profile screenshot) and
emits the rest in ready-to-paste form. Three entries whose hero images
resemble the two unidentified vizsla pins in the screenshot are flagged
as SUSPECT for the user to eyeball-skip.

Run:  py scripts/generate_sprint1_remaining.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from pinterest_pin_copy import PIN_CONFIGS, article_url, load_article  # noqa: E402

OUT = ROOT / "pinterest-sprint-1-remaining.md"

# Confirmed posted per the 2026-08-26 profile screenshot (title-matched).
POSTED = {
    "cavalier-king-charles-spaniel-first-year-costs-a",
    "cavalier-king-charles-spaniel-first-year-costs-b",
    "nova-scotia-duck-tolling-retriever-first-year-costs-a",
    "nova-scotia-duck-tolling-retriever-first-year-costs-b",
    "fluffy-dog-breeds-a",
    "fluffy-dog-breeds-b",
    "best-dogs-for-cold-climates-a",
    "best-dogs-for-cold-climates-b",
    "bernese-mountain-dog-vs-saint-bernard-a",
    "bernese-mountain-dog-vs-saint-bernard-b",
    "alaskan-malamute-grooming-guide-a",
    "alaskan-malamute-grooming-guide-b",
    "best-dogs-for-hot-climates-b",
}

# Screenshot shows two vizsla-hero pins whose titles were not readable;
# these are the candidates. User should skip any they recognize.
SUSPECT = {
    "best-dogs-for-hot-climates-a",
    "best-dogs-for-active-people-a",
    "best-dogs-for-active-people-b",
}


def render(n, total, pin_key, slug, cfg, display_name, hero, blog, flag=""):
    link = article_url(slug, blog, cfg["campaign"], pin_key.rsplit("-", 1)[-1])
    t, d = cfg["title"], cfg["description"]
    return [
        "---", "",
        f"## {flag}Pin {n}/{total} - {display_name[:60]} ({pin_key.rsplit('-', 1)[-1].upper()})",
        f"- **Board**: `{cfg['board']}`",
        "- **Image**:", "```", hero, "```",
        "- **Link**:", "```", link, "```",
        f"### Title ({len(t)}c)", "```", t, "```",
        f"### Description ({len(d)}c)", "```", d, "```", "",
    ]


def main() -> int:
    remaining, suspect = [], []
    for cfg in PIN_CONFIGS:
        slug = cfg["slug"]
        for var in ("a", "b"):
            key = f"{slug}-{var}"
            if key in POSTED:
                continue
            loaded = load_article(slug)
            if loaded is None:
                continue
            name, hero, blog = loaded
            entry = (key, slug, cfg[var], name, hero, blog)
            (suspect if key in SUSPECT else remaining).append(entry)

    total = len(remaining) + len(suspect)
    lines = [
        "# Pinterest Sprint 1 - REMAINING PINS (2026-08-26)",
        "",
        f"40 total - 13 confirmed posted (from your profile screenshot) = "
        f"{total} below. The last {len(suspect)} are flagged SUSPECT: the "
        "screenshot shows two vizsla-hero pins with unreadable titles - if "
        "you recognize one as already posted, skip it.",
        "",
        "Cadence: 5/day, spread boards, evenings ET. Comparisons and costs "
        "first (your validated strongest angles).",
        "",
    ]
    n = 0
    for key, slug, cfg, name, hero, blog in remaining:
        n += 1
        lines += render(n, total, key, slug, cfg, name, hero, blog)
    for key, slug, cfg, name, hero, blog in suspect:
        n += 1
        lines += render(n, total, key, slug, cfg, name, hero, blog,
                        flag="[SUSPECT - may already be posted] ")
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(remaining)} confirmed-remaining + "
          f"{len(suspect)} suspect = {total} pins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
