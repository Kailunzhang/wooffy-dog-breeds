"""Add newly published breed main pages to the Dog Breeds A-Z directory.

breed-data/dog-breeds-a-z.json lists every breed guide by letter:
    <a class="wfy-breed" href="/blogs/dog-breeds/<slug>"><span class="wfy-bname">Name</span>
    <span class="wfy-btag">Group &middot; Size</span></a>
This script parses the existing entries, adds the given slugs (tag derived from
meta.group / meta.size_category the same way the existing tags read), re-sorts,
and rebuilds the letter chips, letter sections and the count line. Everything
outside that block (intro, nutrition links, footer) is left untouched.

Rebuilding with no new slugs reproduces the current HTML byte-for-byte (checked
on every run), so the format cannot drift.

Run:
    python3 scripts/add_breeds_to_az.py <slug> [<slug> ...]           # dry-run
    python3 scripts/add_breeds_to_az.py <slug> [<slug> ...] --apply   # write JSON
    echo YES | python3 scripts/generate.py dog-breeds-a-z --update
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "breed-data")
HUB = os.path.join(DATA_DIR, "dog-breeds-a-z.json")
SPOKES = ("-grooming-guide", "-first-year-costs", "-puppy-checklist")

ENTRY_RE = re.compile(
    r'<a class="wfy-breed" href="/blogs/dog-breeds/([a-z0-9-]+)"><span class="wfy-bname">([^<]+)</span>'
    r'<span class="wfy-btag">([^<]+)</span></a>')
BLOCK_RE = re.compile(r'<nav class="wfy-chips".*?</nav>\n(?:<h2 class="wfy-letter".*?</div>)+', re.DOTALL)
COUNT_RE = re.compile(r"(<p class=\"wfy-count\">)(\d+)( breed guides)")
INTRO_OLD = ("and jump straight to its complete guide &mdash; temperament, grooming,\n"
             "first-year costs, and puppy checklist.")
INTRO_NEW = ("and jump straight to its complete guide &mdash; temperament, health and\n"
             "costs, plus grooming, first-year cost and puppy-checklist guides for most breeds.")


def tag_for(meta: dict) -> str:
    group = (meta.get("group") or "").replace(" Group", "")
    group = {"Designer Crossbreed": "Designer"}.get(group, group)
    size = (meta.get("size_category") or "").replace(" Breed", "")
    size = size.replace(" to ", "–").replace("-", "–")
    return f"{group} &middot; {size}"


def render(entries: list[tuple[str, str, str]]) -> str:
    by_letter: dict[str, list[tuple[str, str, str]]] = {}
    for e in sorted(entries, key=lambda e: e[1].lower()):
        by_letter.setdefault(e[1][0].upper(), []).append(e)
    chips = "".join(f'<a class="wfy-chip" href="#breeds-{L}">{L}</a>' for L in by_letter)
    sections = "".join(
        f'<h2 class="wfy-letter" id="breeds-{L}">{L}</h2><div class="wfy-grid">'
        + "".join(f'<a class="wfy-breed" href="/blogs/dog-breeds/{s}"><span class="wfy-bname">{n}</span>'
                  f'<span class="wfy-btag">{t}</span></a>' for s, n, t in items)
        + "</div>"
        for L, items in by_letter.items())
    return f'<nav class="wfy-chips" aria-label="Jump to letter">{chips}</nav>\n{sections}'


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    slugs = [a for a in argv if not a.startswith("--")]
    raw = open(HUB, encoding="utf-8").read()
    hub = json.loads(raw)
    body = hub["body_html"]
    block = BLOCK_RE.search(body)
    if not block:
        sys.exit("A-Z block not found")
    entries = ENTRY_RE.findall(block.group(0))
    if render(entries) != block.group(0):
        sys.exit("round-trip check failed: the A-Z markup changed shape; update this script first")
    known = {e[0] for e in entries}
    added, main_only = [], False
    for slug in slugs:
        path = os.path.join(DATA_DIR, f"{slug}.json")
        if slug in known or not os.path.exists(path):
            print(f"[{slug}] skip: {'already listed' if slug in known else 'no breed-data file'}")
            continue
        meta = json.load(open(path, encoding="utf-8"))["meta"]
        if meta.get("published") is False and apply:
            print(f"[{slug}] skip: not published yet")
            continue
        entries.append((slug, meta["name"], tag_for(meta)))
        added.append(slug)
        main_only |= not all(os.path.exists(os.path.join(DATA_DIR, f"{slug}{s}.json")) for s in SPOKES)
        print(f"[{slug}] + {meta['name']}  ({tag_for(meta)})")
    if not added:
        print("nothing to add")
        return 0
    body = body[:block.start()] + render(entries) + body[block.end():]
    body = COUNT_RE.sub(lambda m: f"{m.group(1)}{len(entries)}{m.group(3)}", body, count=1)
    if main_only:
        body = body.replace(INTRO_OLD, INTRO_NEW)
    hub["body_html"] = body
    print(f"{'wrote' if apply else 'would write'}: {len(entries)} breeds (+{len(added)})")
    if apply:
        out = json.dumps(hub, ensure_ascii=False, indent=2) + ("\n" if raw.endswith("\n") else "")
        open(HUB, "w", encoding="utf-8", newline="\n").write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
