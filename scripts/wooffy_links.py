"""Single source of truth for internal-link URLs on thewooffy.com.

Why this exists
---------------
Articles live in TWO Shopify blogs:
  - dog-breeds blog (the main one, 751 articles)
  - dog-nutrition blog ("can dogs eat X" articles, 30 articles)

The URL format is ``/blogs/<blog_handle>/<slug>``. If a generator script
hard-codes ``/blogs/dog-breeds/`` for every internal link, links to
nutrition articles 404 silently. This happened on 2026-06-24
(see git commit 6489e53 fixing 9 broken links across 3 articles).

This module makes that mistake impossible:

  - ``article_url(slug)`` looks up the correct blog_handle from the
    article's own JSON file and raises ``UnknownSlugError`` if the slug
    doesn't exist on the site.
  - ``related_links_html(items)`` builds the standard "Related Reading"
    block using ``article_url`` for every entry.

Usage in a generator script::

    from wooffy_links import related_links_html

    html = ... + related_links_html([
        ("goldendoodle",        "Goldendoodle Breed Guide"),
        ("can-dogs-eat-eggs",   "Can Dogs Eat Eggs?"),   # nutrition blog
        ("german-shepherd-dog", "German Shepherd"),       # correct slug
    ])
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"
SITE_ORIGIN = "https://thewooffy.com"
DEFAULT_BLOG = "dog-breeds"
INTERNAL_LINK_MARKER = "<!-- WOOFFY_INTERNAL_LINKS_v1 -->"


class UnknownSlugError(ValueError):
    """Raised when a slug doesn't have a corresponding JSON file in breed-data/."""


@lru_cache(maxsize=1)
def slug_to_blog_handle() -> dict[str, str]:
    """Return ``{slug: blog_handle}`` for every article in ``breed-data/``.

    Cached for the life of the process. Re-import or call ``.cache_clear()``
    if you've added new JSONs and need a refresh in a long-running script.
    """
    result: dict[str, str] = {}
    for path in sorted(BREED_DATA.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        meta = data.get("meta") or {}
        slug = (meta.get("slug") or path.stem).strip()
        blog = (meta.get("blog_handle") or DEFAULT_BLOG).strip()
        result[slug] = blog
    return result


def article_url(slug: str, *, absolute: bool = True) -> str:
    """Return the canonical public URL for an internal article slug.

    Raises ``UnknownSlugError`` if no JSON file in ``breed-data/`` declares
    this slug. This is the whole point of the helper: a broken internal link
    becomes a noisy generator-script failure instead of a silent 404 in
    production.

    Pass ``absolute=False`` to get a relative path (``/blogs/.../slug``)
    instead of a full URL.
    """
    blog = slug_to_blog_handle().get(slug)
    if blog is None:
        raise UnknownSlugError(
            f"Unknown article slug: {slug!r}. "
            f"No matching JSON in {BREED_DATA}. "
            f"Did you mean a different slug, or do you need to create the article first?"
        )
    base = SITE_ORIGIN if absolute else ""
    return f"{base}/blogs/{blog}/{slug}"


def related_links_html(
    items: list[tuple[str, str]],
    *,
    heading: str = "Related Reading",
    css_class: str = "related-reading",
) -> str:
    """Build the standard 'Related Reading' HTML block.

    ``items`` is a list of ``(slug, link_text)`` tuples. Every slug is
    resolved via ``article_url``; an unknown slug raises immediately so
    you fix it before the article ships.
    """
    li_lines = "".join(
        f'<li><a href="{article_url(slug)}">{label}</a></li>' for slug, label in items
    )
    return (
        f"\n{INTERNAL_LINK_MARKER}\n"
        f'<section class="{css_class}">\n'
        f"<h2>{heading}</h2>\n"
        f"<ul>{li_lines}</ul>\n"
        f"</section>"
    )
