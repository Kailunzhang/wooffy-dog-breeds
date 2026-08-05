"""Phase C: break the breed->nutrition internal-link island.

The 754-page breed cluster currently sends only ~3 links into the 30 nutrition
pages, so site authority never flows to them (audit HIGH). The existing
inject_internal_links.py "Related Reading" block links breed->breed only and is
skip-idempotent (won't regenerate). So this is a SEPARATE, additive injector
(its own marker) that appends a small "Dog Nutrition Guides" block of 2
nutrition links to every breed-cluster + roundup page, distributed evenly
(stable_picks) so every nutrition page — including the under-linked priority
pages (butternut 6 / sunflower 3 / almond 3 inbound) — gains dozens of inbound.

Reuses inject_internal_links's article loader / stable_picks / URL helpers.
Idempotent via <!-- WOOFFY_NUTRITION_LINKS_v1 -->. Dry-run by default.

Run:
    python3 scripts/inject_nutrition_links.py            # dry-run + impact
    python3 scripts/inject_nutrition_links.py --apply    # write JSONs
    echo YES | python3 scripts/generate.py <changed-slugs> --update
"""
from __future__ import annotations

import collections
import re
import sys

import inject_internal_links as base

MARKER = "<!-- WOOFFY_NUTRITION_LINKS_v1 -->"
NUT_PER = 2
TARGET_TYPES = {"main", "grooming", "cost", "checklist", "roundup"}


def render(picks: list[str], articles: dict) -> str:
    items = "".join(
        f'<li><a href="{base.build_blog_url(r, articles)}">{articles[r]["name"]}</a></li>'
        for r in picks
    )
    return (
        f"\n{MARKER}\n"
        f'<section class="dog-nutrition-links">\n'
        f"<h2>Dog Nutrition Guides</h2>\n"
        f"<ul>{items}</ul>\n"
        f"</section>"
    )


def inject(raw: str, section_html: str) -> tuple[str, str] | None:
    if MARKER in raw:
        return None
    esc = section_html.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    m = re.search(r'("body_html"\s*:\s*")((?:[^"\\]|\\.)*?)(")', raw, re.DOTALL)
    if m and m.group(2):
        return raw[:m.start()] + m.group(1) + m.group(2) + esc + m.group(3) + raw[m.end():], "body_html"
    hs = list(re.finditer(r'("html"\s*:\s*")((?:[^"\\]|\\.)*?)(")', raw, re.DOTALL))
    if hs:
        m = hs[-1]
        return raw[:m.start()] + m.group(1) + m.group(2) + esc + m.group(3) + raw[m.end():], "sections"
    return None


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    articles = base.load_articles()
    nutrition_slugs = [s for s in articles if articles[s]["blog"] == "dog-nutrition"]

    changed: list[str] = []
    inbound: collections.Counter = collections.Counter()
    stats = {"changed": 0, "already": 0, "skipped_type": 0, "no_body": 0}

    for slug in sorted(articles):
        atype = base.detect_article_type(slug, articles[slug])
        if atype not in TARGET_TYPES:
            stats["skipped_type"] += 1
            continue
        raw = articles[slug]["_raw"]
        if MARKER in raw:
            stats["already"] += 1
            continue
        picks = base.stable_picks(slug + "_nutlink", nutrition_slugs, NUT_PER)
        picks = [p for p in picks if p in articles]
        if not picks:
            continue
        result = inject(raw, render(picks, articles))
        if result is None:
            stats["no_body"] += 1
            continue
        new_raw, _ = result
        changed.append(slug)
        for p in picks:
            inbound[p] += 1
        if apply:
            articles[slug]["path"].write_text(new_raw, encoding="utf-8", newline="\n")
            stats["changed"] += 1

    print(f"{'APPLIED' if apply else 'DRY-RUN'}: {len(changed)} breed-cluster pages "
          f"{'got' if apply else 'would get'} a nutrition-links block", file=sys.stderr)
    print(f"stats: {stats}", file=sys.stderr)
    print("\ninbound links each nutrition page gains (priority pages flagged):", file=sys.stderr)
    PRI = {"can-dogs-eat-quinoa", "can-dogs-eat-sunflower-seeds",
           "can-dogs-eat-butternut-squash-a-nutritious-addition-to-your-dogs-diet",
           "can-dogs-have-almond-butter", "can-dogs-eat-eggplant"}
    for s, c in sorted(inbound.items(), key=lambda x: -x[1]):
        flag = "  <== PRIORITY" if s in PRI else ""
        print(f"  +{c:>3}  {s}{flag}", file=sys.stderr)
    if apply and changed:
        print("\nSlugs to push (STDOUT):", file=sys.stderr)
        print(" ".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
