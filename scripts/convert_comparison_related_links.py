"""Make the comparison pages' related cross-links actually render.

2026-07-15 audit HIGH fix. The patch_comparison_cross_links_v1..v4 scripts wrote
the "Compare More Breeds" links into ``sections["related"]`` — but generate.py's
generate_html() never renders a ``related`` section (it renders the top-level
``related_breeds`` key via build_related). So on the live site every -vs-
comparison page has a dangling "#related" TOC anchor and ZERO contextual
article links (the audit's "26 orphaned comparison pages").

This converts, for each -vs- comparison JSON:
  sections["related"]  ->  top-level  related_breeds = [{slug, name, note}]
and removes the now-empty sections["related"] (kills the dangling TOC anchor).
generate_html then renders them as the "Similar Breeds / Explore More" block.

Run:
    python3 scripts/convert_comparison_related_links.py --dry-run
    python3 scripts/convert_comparison_related_links.py
    echo YES | python3 scripts/generate.py <slugs...> --update
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"

LINK_RE = re.compile(r'href="/blogs/dog-breeds/([a-z0-9-]+)"[^>]*>([^<]+)</a>')


def convert(path: Path, dry_run: bool) -> tuple[str, int]:
    d = json.loads(path.read_text(encoding="utf-8"))
    sections = d.get("sections", {})
    rel = sections.get("related")
    if not isinstance(rel, dict):
        return "no related section", 0
    html = rel.get("html", "")
    pairs = LINK_RE.findall(html)
    if not pairs:
        return "related section had no links", 0
    # dedupe preserving order, drop self-links
    self_slug = path.stem
    seen: set[str] = set()
    related_breeds: list[dict[str, str]] = []
    for slug, text in pairs:
        if slug == self_slug or slug in seen:
            continue
        seen.add(slug)
        related_breeds.append({"slug": slug, "name": text.strip(), "note": ""})
    if not related_breeds:
        return "only self-links", 0
    if not dry_run:
        d["related_breeds"] = related_breeds
        sections.pop("related", None)
        d["sections"] = sections
        path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return "OK", len(related_breeds)


def main() -> int:
    dry_run = "--dry-run" in sys.argv[1:]
    files = sorted(BD.glob("*-vs-*.json"))
    changed: list[str] = []
    print(f"=== {'DRY-RUN' if dry_run else 'APPLY'} — {len(files)} comparison files ===", file=sys.stderr)
    for p in files:
        msg, n = convert(p, dry_run)
        if msg == "OK":
            changed.append(p.stem)
            print(f"  [OK ] {p.stem:44} {n} links -> related_breeds", file=sys.stderr)
        else:
            print(f"  [skip] {p.stem:44} {msg}", file=sys.stderr)
    print(f"\nConverted: {len(changed)} / {len(files)}", file=sys.stderr)
    if changed and not dry_run:
        print("Slugs to push (STDOUT):", file=sys.stderr)
        print(" ".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
