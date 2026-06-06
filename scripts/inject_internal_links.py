"""Inject a "Related Reading" section into every breed-data article's
body_html, fixing the site-wide internal-link orphan problem (99.5% of
articles had zero incoming internal links as of 2026-06-05).

Relation selection (5 links per article):
  - Main breed: 3 siblings (grooming + cost + checklist) + 1 same-group
    breed + 1 relevant roundup
  - Supporting (grooming/cost/checklist): 3 siblings (other content
    types for same breed) + 1 same-type article for a different breed
    + 1 relevant roundup
  - Roundup: up to 3 breeds mentioned in the roundup body + 2 other
    roundups (deterministic but varied selection)
  - Nutrition: 5 other dog-nutrition articles
  - Comparison: 2 main breeds from the "-vs-" slug + 2 other comparisons
    + 1 relevant roundup (best-effort)

Cross-breed and cross-roundup picks use a stable hash of the source slug
so link equity is spread across the catalog instead of concentrating on
the first alphabetical match.

Idempotent: pages already containing the marker are skipped.

Usage:
  python3 scripts/inject_internal_links.py           # dry-run, 6 samples
  python3 scripts/inject_internal_links.py --all     # dry-run all 748
  python3 scripts/inject_internal_links.py --apply   # write to JSONs
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DIR = ROOT / "breed-data"

MARKER = "<!-- WOOFFY_INTERNAL_LINKS_v1 -->"
SECTION_TITLE = "Related Reading"
LINKS_PER_ARTICLE = 5

ROUNDUP_PREFIXES = ("best-", "most-", "easiest-", "quietest-", "longest-",
                    "rarest-", "low-", "dog-breeds-")
SUPPORTING_SUFFIXES = {
    "grooming": "-grooming-guide",
    "cost": "-first-year-costs",
    "checklist": "-puppy-checklist",
}


def detect_article_type(slug: str, meta: dict) -> str:
    if meta.get("blog") == "dog-nutrition":
        return "nutrition"
    if meta.get("size_cat") == "Roundup" or any(slug.startswith(p) for p in ROUNDUP_PREFIXES):
        return "roundup"
    if "-vs-" in slug:
        return "comparison"
    for atype, suffix in SUPPORTING_SUFFIXES.items():
        if slug.endswith(suffix):
            return atype
    return "main"


def breed_of(slug: str, atype: str) -> str | None:
    if atype == "main":
        return slug
    if atype in SUPPORTING_SUFFIXES:
        return slug[: -len(SUPPORTING_SUFFIXES[atype])]
    return None


def stable_picks(seed: str, candidates: list[str], n: int) -> list[str]:
    """Deterministic but distributed pick of n distinct candidates."""
    if not candidates:
        return []
    cands = sorted(candidates)
    if n >= len(cands):
        return cands
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    start = h % len(cands)
    stride = max(1, (len(cands) // (n + 1)) or 1)
    out: list[str] = []
    used: set[str] = set()
    for i in range(len(cands)):
        idx = (start + i * stride) % len(cands)
        c = cands[idx]
        if c not in used:
            used.add(c)
            out.append(c)
            if len(out) >= n:
                break
    return out


def load_articles() -> dict[str, dict]:
    articles: dict[str, dict] = {}
    for jpath in BREED_DIR.glob("*.json"):
        slug = jpath.stem
        try:
            d = json.loads(jpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        m = d.get("meta", {})
        articles[slug] = {
            "name": m.get("name", slug),
            "blog": m.get("blog_handle", "dog-breeds"),
            "group": m.get("group", ""),
            "size_cat": m.get("size_category", ""),
            "tags": m.get("tags", []),
            "path": jpath,
            "_data": d,
            "_raw": jpath.read_text(encoding="utf-8"),
        }
    return articles


def mentioned_breeds_in_roundup(roundup_slug: str,
                                 articles: dict[str, dict]) -> list[str]:
    """For a roundup, scan its body_html / sections HTML for slugs matching
    known main-breed articles. Returns ordered list, no duplicates."""
    a = articles.get(roundup_slug)
    if not a:
        return []
    raw_html = a["_data"].get("body_html", "") or ""
    for sec in (a["_data"].get("sections") or {}).values():
        raw_html += " " + (sec.get("html") or "")
    raw_html_lower = raw_html.lower()
    main_slugs = [s for s in articles
                  if detect_article_type(s, articles[s]) == "main"]
    found = []
    for s in main_slugs:
        breed_words = s.replace("-", " ")
        if breed_words.lower() in raw_html_lower:
            found.append(s)
    return found


def related_for(slug: str, articles: dict[str, dict],
                roundup_slugs: list[str], nutrition_slugs: list[str],
                comparison_slugs: list[str]) -> list[str]:
    if slug not in articles:
        return []
    meta = articles[slug]
    atype = detect_article_type(slug, meta)
    out: list[str] = []

    if atype in ("main", "grooming", "cost", "checklist"):
        breed = breed_of(slug, atype)
        for suf in ("", "-grooming-guide", "-first-year-costs",
                    "-puppy-checklist"):
            cand = f"{breed}{suf}" if suf else breed
            if cand and cand != slug and cand in articles:
                out.append(cand)
        same_type = [
            s for s in articles
            if detect_article_type(s, articles[s]) == atype
            and s != slug
            and breed_of(s, atype) != breed
        ]
        if not same_type and atype == "main":
            same_type = [
                s for s in articles
                if detect_article_type(s, articles[s]) == "main"
                and s != slug
                and articles[s]["group"] == meta["group"]
                and articles[s]["group"]
            ]
            if not same_type:
                same_type = [
                    s for s in articles
                    if detect_article_type(s, articles[s]) == "main"
                    and s != slug
                ]
        picks = stable_picks(slug + "_xb", same_type, 1)
        if picks:
            out.append(picks[0])
        picks = stable_picks(slug + "_rd", roundup_slugs, 1)
        if picks and picks[0] != slug:
            out.append(picks[0])

    elif atype == "nutrition":
        other_nutrition = [s for s in articles
                           if articles[s]["blog"] == "dog-nutrition"
                           and s != slug]
        out.extend(stable_picks(slug + "_nu", other_nutrition,
                                LINKS_PER_ARTICLE))

    elif atype == "roundup":
        mentioned = mentioned_breeds_in_roundup(slug, articles)
        if mentioned:
            out.extend(stable_picks(slug + "_men", mentioned, 3))
        other_roundups = [s for s in roundup_slugs if s != slug]
        out.extend(stable_picks(slug + "_or", other_roundups, 2))

    elif atype == "comparison":
        if "-vs-" in slug:
            parts = slug.split("-vs-")
            for p in parts:
                p = p.strip("-")
                if p in articles:
                    out.append(p)
        other_comp = [s for s in comparison_slugs if s != slug]
        out.extend(stable_picks(slug + "_oc", other_comp, 2))
        picks = stable_picks(slug + "_rd", roundup_slugs, 1)
        if picks:
            out.append(picks[0])

    seen: set[str] = set()
    deduped: list[str] = []
    for s in out:
        if s and s not in seen and s in articles:
            seen.add(s)
            deduped.append(s)
    return deduped[:LINKS_PER_ARTICLE]


def build_blog_url(slug: str, articles: dict[str, dict]) -> str:
    blog = articles[slug]["blog"] or "dog-breeds"
    return f"https://thewooffy.com/blogs/{blog}/{slug}"


def render_section(slug: str, related: list[str],
                   articles: dict[str, dict]) -> str:
    items = "".join(
        f'<li><a href="{build_blog_url(r, articles)}">'
        f'{articles[r]["name"]}</a></li>'
        for r in related
    )
    return (
        f"\n{MARKER}\n"
        f'<section class="related-reading">\n'
        f"<h2>{SECTION_TITLE}</h2>\n"
        f"<ul>{items}</ul>\n"
        f"</section>"
    )


def inject(raw: str, section_html: str) -> tuple[str, str] | None:
    """Append section_html to either body_html or the last sections.*.html
    field. Returns (new_raw, mode) where mode is 'body_html' or 'sections',
    or None if the file has neither (or already contains the marker).
    """
    if MARKER in raw:
        return None

    section_escaped = (section_html
                       .replace("\\", "\\\\")
                       .replace("\"", "\\\"")
                       .replace("\n", "\\n"))

    # Path A: explicit body_html field with non-empty content (nutrition,
    # comparison, doodle articles).
    m = re.search(
        r'("body_html"\s*:\s*")((?:[^"\\]|\\.)*?)(")',
        raw, re.DOTALL,
    )
    if m and m.group(2):
        body_open, body_value, body_close = m.group(1), m.group(2), m.group(3)
        new_body = body_value + section_escaped
        new_raw = raw[:m.start()] + body_open + new_body + body_close + raw[m.end():]
        return new_raw, "body_html"

    # Path B: section-rendered breed articles. Append to the LAST html field
    # in file order, which (because Python/JSON preserve insertion order and
    # the file is laid out top-down) is the last visible section.
    html_matches = list(re.finditer(
        r'("html"\s*:\s*")((?:[^"\\]|\\.)*?)(")',
        raw, re.DOTALL,
    ))
    if html_matches:
        m = html_matches[-1]
        body_open, body_value, body_close = m.group(1), m.group(2), m.group(3)
        new_body = body_value + section_escaped
        new_raw = raw[:m.start()] + body_open + new_body + body_close + raw[m.end():]
        return new_raw, "sections"

    return None


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    all_mode = "--all" in argv or apply

    articles = load_articles()
    roundup_slugs = [s for s in articles
                     if detect_article_type(s, articles[s]) == "roundup"]
    nutrition_slugs = [s for s in articles
                       if articles[s]["blog"] == "dog-nutrition"]
    comparison_slugs = [s for s in articles
                        if detect_article_type(s, articles[s]) == "comparison"]

    print(f"Loaded {len(articles)} articles "
          f"(roundups={len(roundup_slugs)}, "
          f"nutrition={len(nutrition_slugs)}, "
          f"comparison={len(comparison_slugs)})")
    print("=" * 100)

    if not all_mode:
        SAMPLES = [
            "yorkshire-terrier-first-year-costs",
            "yorkshire-terrier",
            "best-family-dog-breeds",
            "can-dogs-eat-quinoa",
            "boxer-grooming-guide",
            "bernedoodle-vs-goldendoodle",
        ]
        slugs = [s for s in SAMPLES if s in articles]
    else:
        slugs = sorted(articles.keys())

    stats = {"would_inject_body_html": 0, "would_inject_sections": 0,
             "already_injected": 0, "no_body": 0, "no_related": 0,
             "applied": 0, "errors": 0}

    for slug in slugs:
        raw = articles[slug]["_raw"]
        if MARKER in raw:
            stats["already_injected"] += 1
            if not all_mode:
                print(f"\n--- {slug} (already injected, skipping) ---")
            continue
        related = related_for(slug, articles, roundup_slugs,
                              nutrition_slugs, comparison_slugs)
        if not related:
            stats["no_related"] += 1
            continue
        section_html = render_section(slug, related, articles)
        if not all_mode:
            atype = detect_article_type(slug, articles[slug])
            print(f"\n--- {slug}  ({atype}) ---")
            for r in related:
                print(f"  -> {r}  «{articles[r]['name'][:70]}»")
        result = inject(raw, section_html)
        if result is None:
            stats["no_body"] += 1
            continue
        new_raw, mode = result
        stats[f"would_inject_{mode}"] += 1
        if apply:
            articles[slug]["path"].write_text(
                new_raw, encoding="utf-8", newline="\n",
            )
            stats["applied"] += 1

    print("\n" + "=" * 100)
    print(f"Stats: {json.dumps(stats, indent=2)}")
    total_would = stats["would_inject_body_html"] + stats["would_inject_sections"]
    if not apply and total_would > 0:
        print(f"\nDry-run done. Re-run with --apply to write changes "
              f"({total_would} files would be modified).")
    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
