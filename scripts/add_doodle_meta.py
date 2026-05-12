"""Inject 6 doodle entries into _unpublished_breeds_meta.json.

One-shot script. Idempotent — skips entries that already exist by slug.
Run once: python3 scripts/add_doodle_meta.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "_unpublished_breeds_meta.json"

DOODLES: list[dict[str, str]] = [
    {
        "slug": "goldendoodle",
        "name": "Goldendoodle",
        "group": "Designer Crossbreed",
        "appearance": (
            "Size varies enormously by Poodle parent. Mini Goldendoodles (Mini Poodle parent) typically weigh 15-35 lbs "
            "and stand 14-17 inches at the shoulder. Standard Goldendoodles (Standard Poodle parent) typically weigh "
            "50-90 lbs and stand 20-24 inches. Coat type is the most variable feature: straight (more Golden Retriever), "
            "wavy (intermediate), or curly (more Poodle). F1B and multigen dogs are more reliably wavy or curly. Colors "
            "include cream, apricot, red, chocolate, black, and parti (multiple colors). The teddy-bear face and "
            "expressive dark eyes are characteristic."
        ),
    },
    {
        "slug": "labradoodle",
        "name": "Labradoodle",
        "group": "Designer Crossbreed",
        "appearance": (
            "Size depends on the Poodle parent. Miniature Labradoodles (Mini Poodle parent) typically weigh 15-25 lbs. "
            "Standard Labradoodles (Standard Poodle parent) typically weigh 50-85 lbs and stand 21-24 inches. Coat types "
            "are categorized as hair (Labrador-type, sheds), fleece (soft and wavy, low-shedding), or wool (curly and "
            "dense, minimal-shedding). Australian Labradoodle breeders work specifically toward fleece and wool coats. "
            "Colors include cream, gold, apricot, red, chocolate, black, parchment, lavender, and parti combinations."
        ),
    },
    {
        "slug": "bernedoodle",
        "name": "Bernedoodle",
        "group": "Designer Crossbreed",
        "appearance": (
            "Standard Bernedoodles stand 23-29 inches and weigh 50-90 lbs. Mini Bernedoodles stand 18-22 inches and "
            "weigh 25-49 lbs. Tiny/Toy Bernedoodles weigh 10-24 lbs. Coat is wavy or curly and ranges from low-shedding "
            "to minimally-shedding. The signature tri-color pattern - black with white markings and rust accents over "
            "the eyes and on the cheeks and legs - mirrors the Bernese Mountain Dog. Other patterns include bi-color "
            "(black and white), sable, merle, and solid colors. Substantial, sturdy build."
        ),
    },
    {
        "slug": "cavapoo",
        "name": "Cavapoo",
        "group": "Designer Crossbreed",
        "appearance": (
            "Small, compact, and rounded. Adult Cavapoos typically weigh 9-25 lbs and stand 9-14 inches at the shoulder. "
            "The Toy Poodle parent produces smaller Cavapoos; the Miniature Poodle parent produces the upper end of the "
            "range. Coats are wavy or curly, with F1B and multigen Cavapoos leaning curlier. Colors include cream, "
            "apricot, red, chocolate, black, sable, tri-color (Blenheim-pattern from the Cavalier side), and parti "
            "combinations. Dark eyes and rounded teddy-bear muzzle give the breed its distinctive look."
        ),
    },
    {
        "slug": "sheepadoodle",
        "name": "Sheepadoodle",
        "group": "Designer Crossbreed",
        "appearance": (
            "Standard Sheepadoodles stand 18-24 inches and weigh 55-85 lbs. Mini Sheepadoodles stand 15-20 inches and "
            "weigh 30-55 lbs. The build is square, well-boned, and athletic. Coat is typically wavy or curly. The "
            "signature panda coloring - black with white markings on the chest, face, paws, and tail tip - is the most "
            "common and most sought-after pattern. Solid black, solid white, blue merle, and tri-color also occur. The "
            "coat is dense and grows continuously like the Poodle's; coat density is higher than other Doodles."
        ),
    },
    {
        "slug": "aussiedoodle",
        "name": "Aussiedoodle",
        "group": "Designer Crossbreed",
        "appearance": (
            "Standard Aussiedoodles stand 18-23 inches and weigh 45-70 lbs. Mini Aussiedoodles stand 14-17 inches and "
            "weigh 25-45 lbs. Build is square, athletic, and built for sustained activity. Coat is wavy or curly. The "
            "signature feature is the merle pattern - a mottled, marbled coat in blue merle (gray-blue with black "
            "patches), red merle (copper with brown patches), or rare phantom merle. White markings on the chest, face, "
            "paws, and tail tip are common. Solid colors also occur: black, red, chocolate, sable. Eyes are often "
            "striking - blue, amber, or heterochromia (one of each color)."
        ),
    },
]


def main() -> int:
    if not META.exists():
        print(f"missing {META}")
        return 1
    data: list[dict] = json.loads(META.read_text(encoding="utf-8"))
    existing_slugs = {b["slug"] for b in data}

    added: list[str] = []
    skipped: list[str] = []
    for d in DOODLES:
        if d["slug"] in existing_slugs:
            skipped.append(d["slug"])
            continue
        data.append(d)
        added.append(d["slug"])

    META.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"added: {added}")
    print(f"skipped (already present): {skipped}")
    print(f"total entries now: {len(data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
