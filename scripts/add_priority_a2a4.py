"""Phase A2 + A4 for the priority nutrition pages.

A2 (liftable opener): eggplant & butternut have a Quick Answer box but NO
question-form H2. Insert <h2 id="short-answer">Can Dogs Eat X?</h2> right above
the Quick Answer so Google has a clear question->answer anchor. (quinoa /
sunflower / almond already have a question-form H2, so they are left alone.)

A4 (HowTo schema): quinoa and butternut each already render a real numbered
preparation <ol>. Extract those existing steps into HowTo JSON-LD — markup of
content already on the page, no fabricated steps.

Idempotent via sentinels. No new health claims are authored.

Run:
    python3 scripts/add_priority_a2a4.py --dry-run
    python3 scripts/add_priority_a2a4.py
    echo YES | python3 scripts/generate.py <changed-slugs> --update
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

BD = os.path.join(os.path.dirname(__file__), "..", "breed-data")
H2_SENT = "<!-- wooffy-a2-h2 v1 -->"
HOWTO_SENT = "<!-- wooffy-howto v1 -->"

QUINOA = "can-dogs-eat-quinoa"
BUTTERNUT = "can-dogs-eat-butternut-squash-a-nutritious-addition-to-your-dogs-diet"
EGGPLANT = "can-dogs-eat-eggplant"

# A2: slug -> the {X} for "Can Dogs Eat {X}?"
A2 = {EGGPLANT: "Eggplant", BUTTERNUT: "Butternut Squash"}
# A4: slug -> (regex anchoring the prep heading, HowTo name)
A4 = {
    QUINOA: (r"How to Prepare Quinoa", "How to Prepare Quinoa for Your Dog"),
    BUTTERNUT: (r"How to Safely Prepare Butternut Squash", "How to Safely Prepare Butternut Squash for Your Dog"),
}


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def add_h2(body: str, x: str) -> str | None:
    if H2_SENT in body:
        return None
    h2 = f'{H2_SENT}<h2 id="short-answer">Can Dogs Eat {x}?</h2>'
    marker = "<!-- WOOFFY_QUICK_ANSWER_v1 -->"
    if marker in body:
        return body.replace(marker, h2 + marker, 1)
    # fallback: after the leading <meta charset> line
    m = re.search(r"<meta[^>]*>", body)
    idx = m.end() if m else 0
    return body[:idx] + h2 + body[idx:]


def add_howto(body: str, heading_re: str, name: str) -> str | None:
    if HOWTO_SENT in body:
        return None
    m = re.search(heading_re, body, re.I)
    if not m:
        return None
    ol = re.search(r"<ol[^>]*>(.*?)</ol>", body[m.end():], re.S | re.I)
    if not ol:
        return None
    lis = re.findall(r"<li[^>]*>(.*?)</li>", ol.group(1), re.S | re.I)
    steps = []
    for li in lis:
        strong = re.search(r"<strong[^>]*>(.*?)</strong>", li, re.S | re.I)
        text = clean(li)
        if len(text) < 12:
            continue
        step = {"@type": "HowToStep", "text": text}
        if strong:
            step["name"] = clean(strong.group(1)).rstrip(":")
        steps.append(step)
    if len(steps) < 2:
        return None
    schema = {"@context": "https://schema.org", "@type": "HowTo", "name": name, "step": steps}
    j = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")
    return body + f'{HOWTO_SENT}<script type="application/ld+json">{j}</script>'


def main() -> int:
    sys.stderr.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv[1:]
    changed: set[str] = set()

    for slug in sorted({QUINOA, BUTTERNUT, EGGPLANT}):
        path = os.path.join(BD, f"{slug}.json")
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        body = orig = d["body_html"]
        note = []
        if slug in A2:
            nb = add_h2(body, A2[slug])
            if nb:
                body = nb; note.append("A2:+question-H2")
            else:
                note.append("A2:skip(sentinel)")
        if slug in A4:
            nb = add_howto(body, *A4[slug])
            if nb:
                body = nb; note.append("A4:+HowTo")
            else:
                note.append("A4:skip(no steps/sentinel)")
        if body != orig:
            changed.add(slug)
            if not dry:
                d["body_html"] = body
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
        print(f"  [{'DRY' if dry else 'ADD'}] {slug}: {', '.join(note)}", file=sys.stderr)

    print(f"\n{'Would change' if dry else 'Changed'} {len(changed)} pages", file=sys.stderr)
    if changed and not dry:
        print("Slugs to push (STDOUT):", file=sys.stderr)
        print(" ".join(sorted(changed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
