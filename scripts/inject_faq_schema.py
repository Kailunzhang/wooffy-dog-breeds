"""Add FAQPage JSON-LD to nutrition pages that already have a visible FAQ.

2026-07-15 audit Phase A. The "can dogs eat X" pages render a visible
"Frequently Asked Questions" block (<h3>Q?</h3><p>A</p> pairs) but carry NO
FAQPage JSON-LD (0/30). This extracts the EXISTING on-page Q&As and emits a
matching FAQPage schema block — pure markup of content already on the page,
NO fabricated Q&As. Pages without a real FAQ (quinoa, sunflower-seeds, salmon,
blueberries, chicken-breast) are skipped — they need Q&As authored first
(Phase B), which must not be invented mechanically for YMYL content.

Idempotent via sentinel. Requires >=3 extracted Q&A pairs to emit.

Run:
    python3 scripts/inject_faq_schema.py --dry-run
    python3 scripts/inject_faq_schema.py
    echo YES | python3 scripts/generate.py <changed-slugs> --update
"""
from __future__ import annotations

import glob
import html
import json
import os
import re
import sys

BD = os.path.join(os.path.dirname(__file__), "..", "breed-data")
SENTINEL = "<!-- wooffy-faqpage v1 -->"
FAQ_MARK = re.compile(r"frequently asked questions", re.I)
QA = re.compile(r"<h3[^>]*>\s*(.*?\?)\s*</h3>\s*<p[^>]*>(.*?)</p>", re.I | re.S)


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)          # strip tags
    s = html.unescape(s)                    # &mdash; -> em dash, &amp; -> & ...
    return re.sub(r"\s+", " ", s).strip()


def extract(body: str) -> list[tuple[str, str]]:
    m = FAQ_MARK.search(body)
    if not m:
        return []
    region = body[m.end():]
    # stop at the Sources footer if present so we only grab FAQ Q&As
    cut = region.lower().find("sources &amp; further reading")
    if cut == -1:
        cut = region.lower().find("sources & further reading")
    if cut != -1:
        region = region[:cut]
    pairs = []
    for q, a in QA.findall(region):
        q, a = clean(q), clean(a)
        if q and a and len(a) > 15:
            pairs.append((q, a))
    return pairs


def build_block(pairs: list[tuple[str, str]]) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in pairs
        ],
    }
    j = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")
    return f'{SENTINEL}<script type="application/ld+json">{j}</script>'


def main() -> int:
    sys.stderr.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv[1:]
    changed, skipped = [], []
    for path in sorted(glob.glob(os.path.join(BD, "can-dogs-*.json"))):
        slug = os.path.basename(path)[:-5]
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        body = d.get("body_html")
        if body is None:
            continue
        if SENTINEL in body:
            print(f"  [ok  ] {slug}: already has FAQ schema", file=sys.stderr)
            continue
        pairs = extract(body)
        if len(pairs) < 3:
            skipped.append(slug)
            print(f"  [skip] {slug}: only {len(pairs)} Q&As (needs authored FAQ, Phase B)", file=sys.stderr)
            continue
        changed.append(slug)
        print(f"  [{'DRY' if dry else 'ADD'}] {slug}: +FAQPage schema ({len(pairs)} Q&As)", file=sys.stderr)
        if not dry:
            d["body_html"] = body + build_block(pairs)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"\n{'Would add' if dry else 'Added'} FAQ schema to {len(changed)} pages; "
          f"skipped {len(skipped)} (no extractable FAQ)", file=sys.stderr)
    if changed and not dry:
        print("Slugs to push (STDOUT):", file=sys.stderr)
        print(" ".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
