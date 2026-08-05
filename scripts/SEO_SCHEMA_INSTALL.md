# Fix #03 — single Article + single Organization per page (AS-BUILT 2026-07-14)

**Status: DONE and verified live** on theme **"Website v042026"** (the live theme;
"Pre-Sale Website" is a draft and was NOT the one to edit).

## What was actually wrong
There is **no Booster SEO app** installed (the `booster-apps-common.liquid`
snippet is the **TYDAL email-popup** app — leave it alone). The duplicate
structured data came from the **Dawn theme's own native schema** plus two
custom snippets:

- **2 Article nodes:** `snippets/seo-article-freshness.liquid` (`#freshness`)
  **and** `sections/main-article.liquid`'s `{{ article | structured_data }}`.
- **2 Organization nodes:** `sections/header.liquid`'s native Organization
  (no `@id`, `sameAs` full of empty strings) **and**
  `snippets/seo-brand-context.liquid` (the rich one, `@id … /#organization`).

## The fix (all in the live theme's code)
1. **Keep** `snippets/seo-brand-context.liquid` — it is now the single, rich
   Organization (alternateName, knowsAbout, clean sameAs).
2. **Add** `snippets/seo-schema.liquid` (this repo's copy) — emits, on **article
   pages only**, one `@graph` of `WebSite + BlogPosting + BreadcrumbList`, with
   `dateModified = article.updated_at` (fresh), images forced `https`, and
   `author`/`publisher` referencing `{{ shop.url }}/#organization`.
3. In `layout/theme.liquid`, after `{{ content_for_header }}`:
   - `{% render 'seo-brand-context' %}` (kept)
   - `{% render 'seo-schema' %}` (added)
   - removed `{% render 'seo-article-freshness' %}`
4. In `sections/main-article.liquid`, commented out `{{ article | structured_data }}`.
5. In `sections/header.liquid`, commented out the native Organization
   `<script type="application/ld+json">` block (kept the index-only WebSite block).

## Verified live
`affenpinscher`, `crate-training`, `can-dogs-eat-grapes` each render exactly:
**1 Organization + 1 WebSite + 1 BlogPosting + 1 BreadcrumbList** (+ FAQPage where
the article has FAQs), all with fresh `dateModified`. This also cleared the
duplicate-Organization, missing-BreadcrumbList, and http-image audit findings.

## Re-verify anytime
```
py wooffy_seo_audit.py --limit 20   # or crawl and check article_ld_count == 1
```
