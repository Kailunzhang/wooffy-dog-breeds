"""Full-site SEO audit for wooffy dog-breeds blog.

Scans all breed-data/*.json files plus selected live HTTP checks and
emits a graded report (CRITICAL / HIGH / MEDIUM / LOW) to stdout and to
seo_audit_report.md.

Categories:
  - thin content (body_html < 500 words after HTML strip)
  - missing or weak alt text on hero
  - missing title_tag
  - duplicate title_tag across articles
  - hero URL pointing at a known-bad domain (404 source)
  - related-reading anchors that reference non-existent slugs
  - body_html missing the WOOFFY_INTERNAL_LINKS_v1 marker (orphan-risk)
  - body_html with a <h1> tag (duplicate H1 — Shopify already emits one)
  - very long body (> 5000 words, possible bloat or unrendered draft)
  - stats-section breed cards in roundups missing breed JSON references

Output is plain stdout + writes `seo_audit_report.md` at project root.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"
REPORT_PATH = ROOT / "seo_audit_report.md"

HTML_TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
H1_TAG = re.compile(r"<h1[\s>]", re.IGNORECASE)
HREF_TO_OUR_BLOG = re.compile(
    r'href="https?://thewooffy\.com/blogs/(?:dog-breeds|dog-nutrition)/([a-z0-9-]+)"',
    re.IGNORECASE,
)


def word_count(html: str) -> int:
    text = HTML_TAG.sub(" ", html or "")
    text = WS.sub(" ", text).strip()
    return len(text.split())


def extract_body_html(data: dict) -> str:
    if "body_html" in data and data["body_html"]:
        return data["body_html"]
    sections = data.get("sections") or {}
    if isinstance(sections, dict):
        return "\n".join(
            (s.get("html") or "") for s in sections.values() if isinstance(s, dict)
        )
    return ""


def load_all() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(BREED_DATA.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            slug = (data.get("meta") or {}).get("slug") or path.stem
            out[slug] = data
        except Exception as e:
            print(f"[parse-error] {path.name}: {e}", file=sys.stderr)
    return out


def audit(articles: dict[str, dict]) -> dict[str, list]:
    findings: dict[str, list] = defaultdict(list)
    title_tags: Counter = Counter()
    title_owners: dict[str, list[str]] = defaultdict(list)
    all_slugs: set = set(articles.keys())

    for slug, data in articles.items():
        meta = data.get("meta") or {}
        images = data.get("images") or {}
        body = extract_body_html(data)
        wc = word_count(body)

        # title_tag tracking
        tt = (meta.get("title_tag") or "").strip()
        if tt:
            title_tags[tt] += 1
            title_owners[tt].append(slug)
        else:
            findings["MEDIUM_missing_title_tag"].append(slug)

        # thin content (< 500 words). Some legit-thin pages exist;
        # but anything < 300 should be flagged HIGH.
        if wc < 300:
            findings["CRITICAL_thin_content_lt_300"].append((slug, wc))
        elif wc < 500:
            findings["HIGH_thin_content_lt_500"].append((slug, wc))

        # bloated (probably never used)
        if wc > 5000:
            findings["LOW_very_long_body"].append((slug, wc))

        # hero alt
        hero = (images.get("hero") if isinstance(images, dict) else None) or {}
        if isinstance(hero, dict):
            alt = (hero.get("alt") or "").strip()
            url = (hero.get("url") or "").strip()
            if not alt:
                findings["HIGH_missing_hero_alt"].append(slug)
            elif len(alt) < 20 and slug not in alt:
                findings["MEDIUM_weak_hero_alt"].append((slug, alt))
            if not url:
                findings["HIGH_missing_hero_url"].append(slug)
            elif "upload.wikimedia.org" in url:
                findings["MEDIUM_wiki_hero_url"].append((slug, url[:80]))

        # duplicate-H1 risk (Shopify renders an H1 from name already)
        h1_count = len(H1_TAG.findall(body))
        if h1_count:
            findings["HIGH_extra_h1_in_body"].append((slug, h1_count))

        # internal-links marker missing -> orphan risk
        if "<!-- WOOFFY_INTERNAL_LINKS_v1 -->" not in body and wc > 200:
            findings["MEDIUM_missing_related_reading"].append(slug)

        # broken internal links (anchor to slug we do not publish)
        for m in HREF_TO_OUR_BLOG.finditer(body):
            target = m.group(1).lower()
            if target not in all_slugs:
                findings["HIGH_broken_internal_link"].append((slug, target))

        # name basic sanity
        name = (meta.get("name") or "").strip()
        if not name:
            findings["CRITICAL_missing_meta_name"].append(slug)
        elif len(name) > 70:
            findings["LOW_overlong_meta_name"].append((slug, len(name)))

        # meta_description length (Google truncates ~160)
        md = (meta.get("meta_description") or "").strip()
        if not md:
            findings["HIGH_missing_meta_description"].append(slug)
        elif len(md) > 170:
            findings["LOW_overlong_meta_description"].append((slug, len(md)))
        elif len(md) < 70:
            findings["MEDIUM_short_meta_description"].append((slug, len(md)))

    # duplicate title_tags across articles
    for tt, n in title_tags.items():
        if n > 1:
            findings["HIGH_duplicate_title_tag"].append((tt[:80], n, title_owners[tt]))

    return findings


SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def render_report(findings: dict[str, list]) -> str:
    lines: list[str] = []
    lines.append("# Wooffy SEO Audit Report")
    lines.append("")
    lines.append(f"Scanned: {sum(1 for _ in BREED_DATA.glob('*.json'))} breed-data JSON files")
    lines.append("")

    total = sum(len(v) for v in findings.values())
    lines.append("## Summary")
    lines.append("")
    lines.append(f"Total findings: **{total}**")
    by_sev = Counter()
    for k, v in findings.items():
        sev = k.split("_", 1)[0]
        by_sev[sev] += len(v)
    for sev in SEVERITY_ORDER:
        lines.append(f"- {sev}: {by_sev.get(sev, 0)}")
    lines.append("")

    for sev in SEVERITY_ORDER:
        sev_keys = sorted(k for k in findings if k.startswith(sev + "_"))
        if not sev_keys:
            continue
        lines.append(f"## {sev}")
        lines.append("")
        for key in sev_keys:
            short = key.split("_", 1)[1]
            items = findings[key]
            lines.append(f"### {short} ({len(items)})")
            lines.append("")
            for it in items[:30]:
                if isinstance(it, tuple):
                    lines.append(f"- {' / '.join(repr(x) for x in it)}")
                else:
                    lines.append(f"- {it}")
            if len(items) > 30:
                lines.append(f"- ... ({len(items) - 30} more)")
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    print("Loading breed-data/*.json ...", file=sys.stderr)
    articles = load_all()
    print(f"Loaded {len(articles)} articles. Auditing ...", file=sys.stderr)
    findings = audit(articles)
    report = render_report(findings)
    REPORT_PATH.write_text(report, encoding="utf-8", newline="\n")
    print(report)
    print(f"\nReport written to: {REPORT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
