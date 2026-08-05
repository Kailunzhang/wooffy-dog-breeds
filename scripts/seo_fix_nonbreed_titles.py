"""Shorten the 50 non-breed title_tags that render over 60 chars.

2026-07-14 audit fix #04. The breed main/supporting titles were fixed by
seo_fix_main_breed_title_tag.py / seo_fix_supporting_title_tag.py. This
handles the remaining hand-authored titles — comparisons (-vs-), roundups
(best/topic breed lists), nutrition ("Can Dogs Eat X?"), and editorial
guides — which are one-offs, not a template, so each new title is authored
by hand below. Every rewrite keeps the primary keyword and (for nutrition)
the Yes/No answer, and fits <=51 chars so the theme's " - Wooffy" suffix
keeps the rendered <title> at or under 60.

Run:
    python3 scripts/seo_fix_nonbreed_titles.py --dry-run   # preview only
    python3 scripts/seo_fix_nonbreed_titles.py             # write local JSON
    echo YES | python3 scripts/generate.py <slugs...> --update
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"
MAX_TITLE_LEN = 51  # + " - Wooffy" (9) => <=60 rendered

# slug -> new title_tag (each authored to keep keyword + answer, <=51 chars)
NEW_TITLES: dict[str, str] = {
    # --- comparisons: keep "A vs B", trim attribute list ---
    "belgian-malinois-vs-german-shepherd": "Belgian Malinois vs German Shepherd: Which?",
    "bernese-mountain-dog-vs-saint-bernard": "Bernese Mountain Dog vs St Bernard: Size, Cost",
    "chihuahua-vs-pomeranian": "Chihuahua vs Pomeranian: Size, Coat & Temper",
    "french-bulldog-vs-pug": "French Bulldog vs Pug: Size, Health & Cost",
    "labrador-retriever-vs-german-shepherd": "Lab vs German Shepherd: Family, Training, Cost",
    "siberian-husky-vs-alaskan-malamute": "Husky vs Malamute: Size, Energy & Exercise",
    # --- roundups: keep "{X} Dog Breeds", trim subtitle ---
    "black-dog-breeds": "Black Dog Breeds: 10 Stunning All-Black Dogs",
    "calmest-dog-breeds": "Calmest Dog Breeds: 10 Laid-Back Companions",
    "chinese-dog-breeds": "Chinese Dog Breeds: 10 Ancient Native Breeds",
    "curly-haired-dog-breeds": "Curly-Haired Dog Breeds: 10 Curly & Wavy Coats",
    "fluffy-dog-breeds": "Fluffy Dog Breeds: 10 Softest, Fluffiest Dogs",
    "friendliest-dog-breeds": "Friendliest Dog Breeds: 10 Social Family Dogs",
    "german-dog-breeds": "German Dog Breeds: 10 Native Breeds Explained",
    "giant-dog-breeds": "Giant Dog Breeds: 10 of the World's Largest",
    "healthiest-dog-breeds": "Healthiest Dog Breeds: 10 Long-Lived & Hardy",
    "irish-dog-breeds": "Irish Dog Breeds: 9 Native Breeds Explained",
    "japanese-dog-breeds": "Japanese Dog Breeds: The 6 Nihon Ken Explained",
    "long-haired-dog-breeds": "Long-Haired Dog Breeds: 10 Flowing-Coat Dogs",
    "medium-sized-dog-breeds": "Medium-Sized Dog Breeds: 10 Best 30-60 lb Dogs",
    "most-loyal-dog-breeds": "Most Loyal Dog Breeds: 10 Devoted Companions",
    "short-haired-dog-breeds": "Short-Haired Dog Breeds: 10 Low-Shed Coats",
    "white-dog-breeds": "White Dog Breeds: 10 Pure-White Beauties",
    # --- nutrition: keep "Can Dogs Eat X?" + Yes/No answer ---
    "can-dogs-eat-apples": "Can Dogs Eat Apples? Yes, Minus Seeds & Core",
    "can-dogs-eat-avocado": "Can Dogs Eat Avocado? Mostly No - Here's Why",
    "can-dogs-eat-bananas": "Can Dogs Eat Bananas? Yes, in Moderation",
    "can-dogs-eat-blueberries": "Can Dogs Eat Blueberries? Yes, a Safe Treat",
    "can-dogs-eat-bread": "Can Dogs Eat Bread? Plain Yes, Raw Dough No",
    "can-dogs-eat-broccoli": "Can Dogs Eat Broccoli? Yes, in Small Amounts",
    "can-dogs-eat-butternut-squash-a-nutritious-addition-to-your-dogs-diet": "Can Dogs Eat Butternut Squash? Yes, Cooked",
    "can-dogs-eat-cheese": "Can Dogs Eat Cheese? Yes, in Moderation",
    "can-dogs-eat-chocolate": "Can Dogs Eat Chocolate? No - It's Toxic",
    "can-dogs-eat-eggs": "Can Dogs Eat Eggs? Yes, When Cooked",
    "can-dogs-eat-grapes": "Can Dogs Eat Grapes? No - Toxic, Kidney Risk",
    "can-dogs-eat-onions": "Can Dogs Eat Onions? No - They're Toxic",
    "can-dogs-eat-oranges": "Can Dogs Eat Oranges? Yes, in Small Amounts",
    "can-dogs-eat-peanut-butter": "Can Dogs Eat Peanut Butter? Yes, No Xylitol",
    "can-dogs-eat-pineapple": "Can Dogs Eat Pineapple? Yes, Fresh & Plain",
    "can-dogs-eat-quinoa": "Can Dogs Eat Quinoa? Yes, Cooked & Plain",
    "can-dogs-eat-rice": "Can Dogs Eat Rice? Yes, a Bland-Diet Staple",
    "can-dogs-eat-strawberries": "Can Dogs Eat Strawberries? Yes, in Moderation",
    "can-dogs-eat-sunflower-seeds": "Can Dogs Eat Sunflower Seeds? Yes, Shelled",
    "can-dogs-eat-sweet-potatoes": "Can Dogs Eat Sweet Potatoes? Yes, Cooked",
    "can-dogs-eat-tomatoes": "Can Dogs Eat Tomatoes? Ripe Yes, Green No",
    "can-dogs-eat-watermelon": "Can Dogs Eat Watermelon? Yes, Seedless",
    "can-dogs-eat-yogurt": "Can Dogs Eat Yogurt? Yes, Plain & Small",
    # --- editorial guides ---
    "dog-food-on-a-budget-2026": "Dog Food on a Budget 2026: Feed Well for Less",
    "doodle-breeding-ethics-2026": "Doodle Breeding Ethics 2026: Red Flags to Avoid",
    "keep-double-coated-dogs-cool-in-summer": "Keep Double-Coated Dogs Cool - Don't Shave",
    "smart-dog-collar-buyer-guide-2026": "Smart Dog Collar Guide 2026: Fi, Halo, Tractive",
    "when-is-pavement-too-hot-for-dogs": "When Is Pavement Too Hot for Dog Paws? 7-Sec Test",
}


def main() -> int:
    dry_run = "--dry-run" in sys.argv[1:]

    # validate lengths up front
    too_long = [(s, t, len(t)) for s, t in NEW_TITLES.items() if len(t) > MAX_TITLE_LEN]
    if too_long:
        print(f"ABORT: {len(too_long)} title(s) exceed {MAX_TITLE_LEN} chars:", file=sys.stderr)
        for s, t, n in too_long:
            print(f"  {n}  {s}: {t}", file=sys.stderr)
        return 1

    changed: list[tuple[str, str, str]] = []
    missing: list[str] = []
    already_ok = 0

    for slug, new_title in NEW_TITLES.items():
        path = BREED_DATA / f"{slug}.json"
        if not path.exists():
            missing.append(slug)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data.get("meta", {})
        old_title = (meta.get("title_tag") or "").strip()
        if old_title == new_title:
            already_ok += 1
            continue
        changed.append((slug, old_title, new_title))
        if not dry_run:
            meta["title_tag"] = new_title
            data["meta"] = meta
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
                newline="\n",
            )

    mode = "DRY-RUN (no files written)" if dry_run else "WROTE local JSON"
    print(f"=== Summary [{mode}] ===", file=sys.stderr)
    print(f"  Would change / changed:  {len(changed)}", file=sys.stderr)
    print(f"  Already correct:         {already_ok}", file=sys.stderr)
    print(f"  Missing JSON (skipped):  {len(missing)}", file=sys.stderr)
    if missing:
        for s in missing:
            print(f"    [missing] {s}", file=sys.stderr)
    print(file=sys.stderr)
    print("=== Changes (rendered len -> new title) ===", file=sys.stderr)
    for slug, old, new in changed:
        print(f"  {len(new) + 9:>3}  {slug}", file=sys.stderr)
        print(f"       {old}", file=sys.stderr)
        print(f"    -> {new}", file=sys.stderr)

    if changed and not dry_run:
        print(file=sys.stderr)
        print("Slugs to push (STDOUT):", file=sys.stderr)
        print(" ".join(s for s, _, _ in changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
