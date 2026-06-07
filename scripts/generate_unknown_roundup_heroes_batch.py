"""Batch-generate HD heroes for 15 "X dog breeds" roundup articles
whose original Shopify CDN hero URLs are 404, blocking initial publish.

Each roundup gets a theme-matched hero (Japanese -> Shiba Inu, Black ->
black Lab, Curly -> Lagotto Romagnolo, etc.) via fal.ai Nano Banana Pro,
following the brand "outdoor lifestyle photography" style established
in generate_breed_images.py.

Sequential to respect fal.ai concurrency. After this, run:
    echo YES | python3 scripts/generate.py <slug> --publish
for each (these articles do not exist on Shopify yet).

One-shot run:
    python3 scripts/generate_unknown_roundup_heroes_batch.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi  # noqa: E402
import shopify_files_upload as sfu    # noqa: E402

OUT_DIR = ROOT / "sample-images" / "roundup-heroes"
BREED_DATA = ROOT / "breed-data"

STYLE_TAIL = (
    "the dog is the absolute single subject perfectly centered with full "
    "body and all four legs visible, soft natural daylight, shallow depth "
    "of field with sharp focus on the dog, professional pet photography, "
    "photorealistic, magazine cover quality, no humans, no text"
)


TARGETS: list[tuple[str, str, str]] = [
    ("black-dog-breeds",
     "An adult black Labrador Retriever with a glossy black coat standing "
     "alert on a sunlit grass lawn",
     "Black Labrador Retriever — representative photograph for our roundup "
     "of the best black dog breeds, from Labs to Newfoundlands."),
    ("calmest-dog-breeds",
     "A calm adult Bernese Mountain Dog resting peacefully on a wooden "
     "porch in warm golden-hour light",
     "Calm Bernese Mountain Dog — featured in our roundup of the calmest "
     "dog breeds for relaxed households."),
    ("chinese-dog-breeds",
     "An adult Chinese Shar-Pei with the distinctive wrinkled coat "
     "standing in a quiet courtyard with soft natural light",
     "Chinese Shar-Pei — featured in our roundup of ancient Chinese dog "
     "breeds, from the Shar-Pei to the Pekingese."),
    ("curly-haired-dog-breeds",
     "An adult Lagotto Romagnolo with the breed's distinctive tight curls "
     "standing in a sunlit field",
     "Lagotto Romagnolo — featured in our roundup of the best curly-haired "
     "dog breeds, including Poodles and Bichon Frises."),
    ("fluffy-dog-breeds",
     "An adult Samoyed with thick white fluffy double coat standing in "
     "fresh snow under bright daylight",
     "Fluffy Samoyed in snow — featured in our roundup of the fluffiest "
     "dog breeds, from Pomeranians to Newfoundlands."),
    ("friendliest-dog-breeds",
     "An adult Golden Retriever with a warm friendly expression sitting "
     "on green grass in a sunlit park",
     "Friendly Golden Retriever — featured in our roundup of the "
     "friendliest dog breeds for families and social households."),
    ("german-dog-breeds",
     "An adult German Shepherd standing alert in a sunlit alpine meadow "
     "with mountains softly out of focus in the background",
     "German Shepherd — featured in our roundup of native German dog "
     "breeds, including the Dachshund and Rottweiler."),
    ("giant-dog-breeds",
     "An adult Great Dane standing tall on a green lawn beside a small "
     "garden fence to show scale",
     "Great Dane — featured in our roundup of the world's giant dog "
     "breeds, from Mastiffs to Irish Wolfhounds."),
    ("healthiest-dog-breeds",
     "A healthy active adult Australian Cattle Dog running on green grass "
     "in afternoon sunlight",
     "Healthy active Australian Cattle Dog — featured in our roundup of "
     "the healthiest, longest-living dog breeds."),
    ("irish-dog-breeds",
     "An adult Irish Wolfhound standing on rolling green Irish hills "
     "with soft afternoon light",
     "Irish Wolfhound on Irish hills — featured in our roundup of native "
     "Irish dog breeds, from the Wolfhound to the Setter."),
    ("japanese-dog-breeds",
     "An adult Shiba Inu with the characteristic red coat and curled tail "
     "in a serene Japanese garden setting with soft natural light",
     "Shiba Inu in a Japanese garden — featured in our roundup of native "
     "Japanese dog breeds, the Nihon Ken."),
    ("long-haired-dog-breeds",
     "An adult Afghan Hound with a flowing silky long coat standing in "
     "an elegant outdoor portrait pose",
     "Afghan Hound with flowing long coat — featured in our roundup of "
     "the most elegant long-haired dog breeds."),
    ("medium-sized-dog-breeds",
     "An adult Border Collie standing alert on a green lawn at a balanced "
     "medium build to represent the size category",
     "Medium-sized Border Collie — featured in our roundup of the best "
     "medium-sized dog breeds for active households."),
    ("short-haired-dog-breeds",
     "An adult Vizsla with the breed's distinctive short golden-rust coat "
     "standing in a sunlit grass field",
     "Vizsla with a short rust coat — featured in our roundup of the "
     "best short-haired dog breeds for low-shedding households."),
    ("white-dog-breeds",
     "An adult pure white Samoyed with the breed's signature smile "
     "standing on a soft neutral background",
     "Pure white Samoyed — featured in our roundup of the most "
     "beautiful all-white dog breeds."),
]


def build_prompt(specific: str) -> str:
    return f"{specific}, {STYLE_TAIL}"


def patch_json(slug: str, cdn_url: str, alt_text: str) -> tuple[str, str]:
    path = BREED_DATA / f"{slug}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    hero = data.setdefault("images", {}).setdefault("hero", {})
    old = hero.get("url", "")
    hero["url"] = cdn_url
    hero["alt"] = alt_text
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return old, cdn_url


def main() -> int:
    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store = env.get("SHOPIFY_STORE", "")
    token = env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results: list[tuple[str, str | None, str | None]] = []
    for slug, specific, alt_text in TARGETS:
        json_path = BREED_DATA / f"{slug}.json"
        if not json_path.exists():
            print(f"[{slug}] SKIP: no JSON")
            results.append((slug, None, "no-json"))
            continue
        try:
            print(f"\n>>> [{slug}] generating hero via fal.ai...")
            prompt = build_prompt(specific)
            src = gbi.run_one(fal_key, slug, prompt, OUT_DIR)
            unique = OUT_DIR / f"roundup-{slug}-hero.png"
            if src != unique:
                if unique.exists():
                    unique.unlink()
                src.rename(unique)
            print(f"[{slug}] uploading to Shopify Files...")
            cdn_url = sfu.upload_one(store, token, unique, alt=alt_text)
            print(f"[{slug}] CDN URL: {cdn_url}")
            old, new = patch_json(slug, cdn_url, alt_text)
            print(f"[{slug}] patched JSON")
            results.append((slug, cdn_url, None))
        except Exception as e:
            print(f"[{slug}] ERROR: {e}")
            results.append((slug, None, str(e)[:200]))

    print("\n=== summary ===")
    ok = sum(1 for _, u, _ in results if u)
    fail = sum(1 for _, u, _ in results if not u)
    print(f"  ok={ok}  fail={fail}")
    for slug, url, err in results:
        status = "OK  " if url else "FAIL"
        print(f"  {status}  {slug}")
    if ok:
        slugs = " ".join(s for s, u, _ in results if u)
        print(f"\nNext: echo YES | python3 scripts/generate.py {slugs} --publish")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
