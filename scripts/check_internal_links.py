"""Validate every internal link across all thewooffy.com articles.

Scans ``breed-data/*.json`` and reports any ``href`` pointing to a
``thewooffy.com`` URL whose blog-handle or slug doesn't match an actual
article. Exits 1 if any are found (suitable for CI / pre-deploy hook).

Run:
    python3 scripts/check_internal_links.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from wooffy_links import BREED_DATA, slug_to_blog_handle  # noqa: E402

# Matches both absolute (https://thewooffy.com/blogs/X/Y) and relative (/blogs/X/Y)
INTERNAL_LINK_RE = re.compile(
    r"""href=["'](?:https?://thewooffy\.com)?/blogs/([a-z0-9-]+)/([a-z0-9-]+)""",
    re.IGNORECASE,
)


def collect_html_blobs(data: dict) -> list[str]:
    blobs: list[str] = []
    if data.get("body_html"):
        blobs.append(data["body_html"])
    for sec in (data.get("sections") or {}).values():
        if isinstance(sec, dict) and sec.get("html"):
            blobs.append(sec["html"])
    for f in data.get("faq") or []:
        if isinstance(f, dict) and f.get("a"):
            blobs.append(f["a"])
    return blobs


def main() -> int:
    canonical = slug_to_blog_handle()
    broken_by_article: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    broken_targets: Counter[tuple[str, str]] = Counter()
    total_links = 0

    for path in sorted(BREED_DATA.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        article_slug = (data.get("meta", {}).get("slug") or path.stem)
        for html in collect_html_blobs(data):
            for match in INTERNAL_LINK_RE.finditer(html):
                used_blog = match.group(1).lower()
                target_slug = match.group(2).lower()
                total_links += 1
                correct = canonical.get(target_slug)
                if correct is None:
                    reason = "TARGET_NOT_EXIST"
                elif used_blog != correct:
                    reason = f"WRONG_BLOG (should be {correct!r})"
                else:
                    continue
                broken_by_article[article_slug].append(
                    (used_blog, target_slug, reason)
                )
                broken_targets[(used_blog, target_slug)] += 1

    print(f"Scanned {total_links} internal links across {len(canonical)} articles.")
    if not broken_by_article:
        print("OK: 0 broken internal links.")
        return 0

    broken_count = sum(len(v) for v in broken_by_article.values())
    print(
        f"FAIL: {broken_count} broken link(s) in "
        f"{len(broken_by_article)} article(s).\n"
    )
    for article in sorted(broken_by_article):
        items = broken_by_article[article]
        print(f"  [{article}] ({len(items)} broken):")
        for used_blog, slug, reason in items:
            print(f"    /blogs/{used_blog}/{slug}  ->  {reason}")
        print()

    print("Most-referenced broken targets:")
    for (blog, slug), count in broken_targets.most_common(10):
        print(f"  {count:>3d}x /blogs/{blog}/{slug}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
