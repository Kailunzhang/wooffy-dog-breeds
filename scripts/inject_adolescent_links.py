"""Point every breed puppy checklist at the four adolescent-dog guides.

A puppy checklist ends with the "First Week Plan"; the natural next step is the
teenage months, so each checklist gets one small box just before its Related
Reading block (<!-- WOOFFY_INTERNAL_LINKS_v1 -->), falling back to the end of
the section:
    /blogs/dog-training/dog-teenage-phase
    /blogs/dog-training/how-to-teach-a-dog-recall
    /blogs/dog-training/leash-reactive-dog
    /blogs/dog-health/when-to-spay-or-neuter-a-dog

Idempotent via <!-- WOOFFY_ADOLESCENT_LINKS_v1 --> ... <!-- /WOOFFY_ADOLESCENT_LINKS_v1 -->.
Dry-run by default. Same pattern as scripts/inject_buying_links.py.

Run:
    python3 scripts/inject_adolescent_links.py                      # dry-run
    python3 scripts/inject_adolescent_links.py --apply              # write JSONs
    python3 scripts/inject_adolescent_links.py --exclude a b --apply
    python3 scripts/inject_adolescent_links.py --remove --apply     # strip the boxes
    echo YES | python3 scripts/generate.py <changed-slugs> --update
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "breed-data")
MARK = "<!-- WOOFFY_ADOLESCENT_LINKS_v1 -->"
END = "<!-- /WOOFFY_ADOLESCENT_LINKS_v1 -->"
BLOCK_RE = re.compile(re.escape(MARK) + r".*?" + re.escape(END) + r"\n?", re.DOTALL)
ANCHOR = "<!-- WOOFFY_INTERNAL_LINKS_v1 -->"
SUFFIX = "-puppy-checklist"


def box(breed: str) -> str:
    return (
        f'{MARK}<div class="wfy-teen" style="border-left:4px solid #1a1a1a;background:#f8f8f8;'
        f'padding:14px 18px;margin:24px 0;border-radius:6px;">'
        f'<p style="margin:0 0 6px;"><strong>Next up: your {breed}&rsquo;s teenage months</strong> '
        f'(roughly 6 months to 2 years)</p>'
        '<ul style="margin:0;">'
        '<li><a href="/blogs/dog-training/dog-teenage-phase">The dog teenage phase</a> &mdash; '
        'why a good puppy can suddenly &ldquo;forget&rdquo; cues, and what helps</li>'
        '<li><a href="/blogs/dog-training/how-to-teach-a-dog-recall">How to teach a reliable recall</a> '
        '&mdash; start before adolescence makes it harder</li>'
        '<li><a href="/blogs/dog-training/leash-reactive-dog">Leash reactivity</a> &mdash; what to do if '
        'barking or lunging on leash starts</li>'
        '<li><a href="/blogs/dog-health/when-to-spay-or-neuter-a-dog">When to spay or neuter</a> '
        '&mdash; the best age depends on size and breed</li>'
        f'</ul></div>{END}\n'
    )


def breed_name(slug: str) -> str:
    main = os.path.join(DATA_DIR, f"{slug[:-len(SUFFIX)]}.json")
    if os.path.exists(main):
        name = (json.load(open(main, encoding="utf-8")).get("meta") or {}).get("name")
        if name:
            return name
    return slug[:-len(SUFFIX)].replace("-", " ").title()


def insert(html: str, breed: str) -> str:
    html = BLOCK_RE.sub("", html)
    i = html.find(ANCHOR)
    return html[:i] + box(breed) + html[i:] if i != -1 else html + box(breed)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--exclude", nargs="*", default=[])
    args = ap.parse_args(argv)
    changed = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, f"*{SUFFIX}.json"))):
        slug = os.path.basename(path)[:-5]
        if slug in args.exclude:
            continue
        raw = open(path, encoding="utf-8").read()
        d = json.loads(raw)
        if (d.get("meta") or {}).get("published", True) is False:
            continue
        sec = (d.get("sections") or {}).get("special")
        if not (isinstance(sec, dict) and isinstance(sec.get("html"), str)):
            print(f"[{slug}] skip: no special section")
            continue
        sec["html"] = BLOCK_RE.sub("", sec["html"]) if args.remove else insert(sec["html"], breed_name(slug))
        out = json.dumps(d, ensure_ascii=False, indent=2) + ("\n" if raw.endswith("\n") else "")
        if out != raw:
            changed.append(slug)
            if args.apply:
                open(path, "w", encoding="utf-8", newline="\n").write(out)
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    with open(os.path.join(ROOT, "output", "adolescent_changed_slugs.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(changed) + ("\n" if changed else ""))
    print(f"{'changed' if args.apply else 'would change'}: {len(changed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
