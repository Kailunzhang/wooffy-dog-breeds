"""Strip <a> tags from FAQ answers in all article JSONs that have them.

Background: 11 "X vs Y" comparison articles contain <a href="..."> links
inside FAQ answers (cross-referencing other breeds). Something in the
live rendering pipeline (Booster Apps SEO and/or theme link transform)
injects target="_blank" rel="noopener noreferrer" into every anchor
tag — including when the FAQ answer HTML is re-serialized into the
FAQPage JSON-LD schema. The injected attributes are NOT escaped, which
produces a JSON syntax error inside the JSON-LD string, which causes
Google to reject the FAQPage schema entirely ("Unparsable structured
data" in GSC URL Inspection).

Fix: strip all <a> tags from FAQ answers (preserve inner text). The
FAQ schema does not render hyperlinks in rich results anyway, and the
breed name is preserved in the visible answer text. Cross-link signal
is still present in the article body and Related Reading block.

Idempotent: only modifies entries where '<a ' appears in the answer.

Run:
    python3 scripts/seo_fix_faq_anchor_escaping.py
    echo YES | python3 scripts/generate.py <list_of_slugs> --update
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"

ANCHOR_RE = re.compile(r"<a\b[^>]*>(.*?)</a>", re.S | re.I)


def strip_anchors(answer: str) -> str:
    return ANCHOR_RE.sub(r"\1", answer)


def main() -> int:
    changed: list[str] = []
    for path in sorted(BREED_DATA.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[parse-error] {path.name}: {e}", file=sys.stderr)
            continue

        faq = data.get("faq", [])
        if not faq:
            continue

        touched = False
        for entry in faq:
            if not isinstance(entry, dict):
                continue
            answer = entry.get("a") or ""
            if "<a " not in answer:
                continue
            new_answer = strip_anchors(answer)
            if new_answer != answer:
                entry["a"] = new_answer
                touched = True

        if touched:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
                newline="\n",
            )
            changed.append(path.stem)
            print(f"  FIXED  {path.stem}")

    print(f"\nChanged: {len(changed)} articles")
    if changed:
        print("\nSlugs to push:")
        print(" ".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
