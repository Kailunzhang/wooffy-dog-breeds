"""Link every breed first-year-cost page to the three puppy-buying guides.

People reading "how much does an X puppy cost" are the readers most exposed to
puppy scams and bad breeders, so each cost page gets one small "Before you buy"
box right after its first cost table (fallback: end of the first section):
    /blogs/dog-breeds/puppy-scams
    /blogs/dog-breeds/how-to-find-a-responsible-breeder
    /blogs/dog-breeds/adopt-or-shop-dog

Idempotent via <!-- WOOFFY_BUYING_LINKS_v1 --> ... <!-- /WOOFFY_BUYING_LINKS_v1 -->.
Dry-run by default.

Run:
    python3 scripts/inject_buying_links.py                  # dry-run
    python3 scripts/inject_buying_links.py --apply          # write JSONs
    python3 scripts/inject_buying_links.py --remove --apply # strip the boxes
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
MARK = "<!-- WOOFFY_BUYING_LINKS_v1 -->"
END = "<!-- /WOOFFY_BUYING_LINKS_v1 -->"
BLOCK_RE = re.compile(re.escape(MARK) + r".*?" + re.escape(END), re.DOTALL)


def box(breed: str) -> str:
    return (
        f'{MARK}<div class="wfy-buying" style="border-left:4px solid #1a1a1a;background:#f8f8f8;'
        f'padding:14px 18px;margin:24px 0;border-radius:6px;">'
        f'<p style="margin:0 0 6px;"><strong>Before you pay for {"an" if breed[:1].upper() in "AEIOU" else "a"} '
        f'{breed} puppy</strong></p>'
        '<ul style="margin:0;">'
        '<li><a href="/blogs/dog-breeds/puppy-scams">How to spot a puppy scam</a> &mdash; '
        'deposit-first sellers, surprise &ldquo;shipping&rdquo; fees and stolen photos</li>'
        '<li><a href="/blogs/dog-breeds/how-to-find-a-responsible-breeder">How to find a responsible '
        'breeder</a> &mdash; and check their health testing yourself</li>'
        '<li><a href="/blogs/dog-breeds/adopt-or-shop-dog">Adopt or buy?</a> &mdash; costs and '
        'trade-offs side by side</li>'
        f'</ul></div>{END}'
    )


def insert(sections: dict, breed: str) -> bool:
    """Place the box after the first cost table; fall back to the end of the first section."""
    keys = [k for k, v in sections.items() if isinstance(v, dict) and isinstance(v.get("html"), str)]
    for k in keys:
        h = BLOCK_RE.sub("", sections[k]["html"])
        i = h.find("</table>")
        if i == -1:
            continue
        at = i + len("</table>")
        tail = h[at:]
        if tail.lstrip().startswith("</div>"):
            at += len(tail) - len(tail.lstrip()) + len("</div>")
        sections[k]["html"] = h[:at] + box(breed) + h[at:]
        return True
    if keys:
        k = keys[0]
        sections[k]["html"] = BLOCK_RE.sub("", sections[k]["html"]) + box(breed)
        return True
    return False


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args(argv)
    changed = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*-first-year-costs.json"))):
        raw = open(path, encoding="utf-8").read()
        d = json.loads(raw)
        if (d.get("meta") or {}).get("published", True) is False:
            continue
        secs = d.get("sections")
        if not isinstance(secs, dict):
            continue
        for v in secs.values():
            if isinstance(v, dict) and isinstance(v.get("html"), str):
                v["html"] = BLOCK_RE.sub("", v["html"])
        if not args.remove:
            base = os.path.basename(path)[: -len("-first-year-costs.json")]
            main_path = os.path.join(DATA_DIR, f"{base}.json")
            breed = (json.load(open(main_path, encoding="utf-8")).get("meta") or {}).get("name") \
                if os.path.exists(main_path) else base.replace("-", " ").title()
            insert(secs, breed)
        out = json.dumps(d, ensure_ascii=False, indent=2) + ("\n" if raw.endswith("\n") else "")
        if out != raw:
            changed.append(os.path.basename(path)[:-5])
            if args.apply:
                open(path, "w", encoding="utf-8", newline="\n").write(out)
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    with open(os.path.join(ROOT, "output", "buying_changed_slugs.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(changed) + ("\n" if changed else ""))
    print(f"{'changed' if args.apply else 'would change'}: {len(changed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
