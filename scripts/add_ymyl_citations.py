"""Add authoritative outbound citations to the YMYL nutrition pages (E-E-A-T).

2026-07-15 audit fix. The ~28 "can dogs eat X" food-safety pages made direct
safety/toxicity claims with ZERO outbound authority links. This appends a
"Sources & Further Reading" block of real, verified-live authority citations
(AKC, ASPCA Animal Poison Control, Pet Poison Helpline) to each page's
body_html. Toxic-food pages also link the ASPCA 24/7 poison-control line.

All URLs were verified 200 before inclusion. Links are dofollow (outbound
citations to authorities are a positive E-E-A-T signal), target=_blank,
rel=noopener. Idempotent via a sentinel comment.

NOTE: this does NOT add a "Reviewed by [Name], DVM" byline — that requires a
real veterinarian to have reviewed the content and must not be fabricated.

Run:
    python3 scripts/add_ymyl_citations.py --dry-run
    python3 scripts/add_ymyl_citations.py
    echo YES | python3 scripts/generate.py <slugs...> --update
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"
SENTINEL = "<!-- ymyl-citations v1 -->"

# (url, source_name, descriptor) — all verified 200 on 2026-07-15
AKC = (
    "https://www.akc.org/expert-advice/nutrition/human-foods-dogs-can-and-cant-eat/",
    "American Kennel Club",
    "which human foods dogs can and can't eat",
)
ASPCA_AVOID = (
    "https://www.aspca.org/pet-care/animal-poison-control/people-foods-avoid-feeding-your-pets",
    "ASPCA Animal Poison Control",
    "people foods to avoid feeding pets",
)
ASPCA_POISON = (
    "https://www.aspca.org/pet-care/animal-poison-control",
    "ASPCA Poison Control",
    "24/7 emergency guidance, (888) 426-4435",
)

# pages whose subject is toxic / high-risk get the emergency poison-control line
TOXIC = {
    "can-dogs-eat-grapes",
    "can-dogs-eat-chocolate",
    "can-dogs-eat-onions",
    "can-dogs-eat-avocado",
}

NUTRITION_SLUGS = [
    "can-dogs-eat-apples", "can-dogs-eat-avocado", "can-dogs-eat-bananas",
    "can-dogs-eat-blueberries", "can-dogs-eat-bread", "can-dogs-eat-broccoli",
    "can-dogs-eat-butternut-squash-a-nutritious-addition-to-your-dogs-diet",
    "can-dogs-eat-cheese", "can-dogs-eat-chicken-breast", "can-dogs-eat-chocolate",
    "can-dogs-eat-eggplant", "can-dogs-eat-eggs", "can-dogs-eat-grapes",
    "can-dogs-eat-onions", "can-dogs-eat-oranges", "can-dogs-eat-peanut-butter",
    "can-dogs-eat-pineapple", "can-dogs-eat-quinoa", "can-dogs-eat-raw-meat",
    "can-dogs-eat-rice", "can-dogs-eat-salmon", "can-dogs-eat-strawberries",
    "can-dogs-eat-sunflower-seeds", "can-dogs-eat-sweet-potatoes",
    "can-dogs-eat-tomatoes", "can-dogs-eat-watermelon", "can-dogs-eat-yogurt",
    "can-dogs-have-almond-butter",
]


def li(url: str, name: str, desc: str) -> str:
    return (
        f'<li style="margin-bottom:8px;"><a href="{url}" target="_blank" rel="noopener" '
        f'style="color:#1a1a1a;font-weight:600;text-decoration:underline;text-underline-offset:3px;">'
        f'{name}</a> — {desc}</li>'
    )


def build_block(slug: str) -> str:
    sources = [AKC, ASPCA_AVOID]
    if slug in TOXIC:
        sources.append(ASPCA_POISON)
    items = "".join(li(*s) for s in sources)
    return (
        f'{SENTINEL}'
        f'<div style="margin-top:48px;padding-top:32px;border-top:1px solid #e8e8e8;">'
        f'<p style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.7em;font-weight:400;'
        f'letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Sources</p>'
        f'<h2 style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">'
        f'Sources &amp; Further Reading</h2>'
        f'<ul style="font-size:0.9em;line-height:1.8;color:#6b7177;padding-left:20px;margin:0;">{items}</ul>'
        f'</div>'
    )


def main() -> int:
    dry_run = "--dry-run" in sys.argv[1:]
    changed: list[str] = []
    for slug in NUTRITION_SLUGS:
        p = BD / f"{slug}.json"
        if not p.exists():
            print(f"  [miss] {slug}", file=sys.stderr)
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        body = d.get("body_html")
        if body is None:
            print(f"  [skip] {slug}: no body_html", file=sys.stderr)
            continue
        if SENTINEL in body:
            print(f"  [ok  ] {slug}: already has citations", file=sys.stderr)
            continue
        n_src = 3 if slug in TOXIC else 2
        changed.append(slug)
        if not dry_run:
            d["body_html"] = body + build_block(slug)
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{'DRY' if dry_run else 'ADD'}] {slug}: +{n_src} citations", file=sys.stderr)

    print(f"\n{'Would add' if dry_run else 'Added'} citations to {len(changed)} pages", file=sys.stderr)
    if changed and not dry_run:
        print("Slugs to push (STDOUT):", file=sys.stderr)
        print(" ".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
