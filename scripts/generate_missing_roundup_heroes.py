"""Generate hero images for the 10 unpublished roundups whose JSONs reference
non-existent Shopify CDN URLs, blocking publish.

One-shot run: python3 scripts/generate_missing_roundup_heroes.py
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi
import shopify_files_upload as sfu

OUT_DIR = ROOT / "sample-images" / "roundup-heroes"
BREED_DATA = ROOT / "breed-data"

STYLE_TAIL = (
    "the dog is the absolute single subject perfectly centered with full body and all four legs visible, "
    "soft natural daylight, shallow depth of field with sharp focus on the dog, "
    "professional pet photography, photorealistic, magazine cover quality, no humans, no text"
)

PROMPTS: dict[str, str] = {
    "best-dog-breeds-for-anxiety":
        f"A calm Golden Retriever resting peacefully on a soft cream rug in a sunlit cozy living room, "
        f"gentle expression with kind eyes, full body in three-quarter profile, warm window light, "
        f"blurred warm interior background, {STYLE_TAIL}",
    "best-dogs-for-kids":
        f"A friendly Cavalier King Charles Spaniel sitting happily on a sunny grass lawn, wagging tail, "
        f"silky Blenheim coat catching warm afternoon light, full body in three-quarter profile, "
        f"blurred suburban backyard background, {STYLE_TAIL}",
    "best-service-dog-breeds":
        f"A focused yellow Labrador Retriever standing alert and attentive on a clean wooden floor, "
        f"full body in profile showing the working-dog bearing, soft warm window light, "
        f"blurred minimal interior background, {STYLE_TAIL}",
    "best-therapy-dog-breeds":
        f"A gentle Golden Retriever lying relaxed on a soft sunlit cushion with a kind expression, "
        f"full body visible, warm afternoon light, blurred soft interior background, {STYLE_TAIL}",
    "dog-breeds-that-can-be-left-alone":
        f"A confident Basenji standing alert on a clean modern wooden floor, short red-and-white coat, "
        f"curled tail, full body in profile, soft window light, blurred minimalist apartment background, {STYLE_TAIL}",
    "dog-breeds-that-dont-bark":
        f"A quiet Basenji sitting calmly with a thoughtful expression on a soft cream rug, "
        f"the iconic curled tail visible, short red-and-white coat, full body, "
        f"soft natural daylight, blurred warm interior background, {STYLE_TAIL}",
    "dog-breeds-with-blue-eyes":
        f"A striking Siberian Husky portrait showing piercing ice-blue eyes and thick black-and-white coat, "
        f"full body sitting alert on snowy grass, full body in three-quarter angle, "
        f"soft natural daylight, blurred snowy meadow background, {STYLE_TAIL}",
    "low-shedding-dog-breeds":
        f"An elegant Standard Poodle in a refined sporting clip standing on a clean wooden floor, "
        f"dense apricot curly coat, full body in profile, bright soft window light, "
        f"blurred minimal interior background, {STYLE_TAIL}",
    "most-affectionate-dog-breeds":
        f"A loving Cavalier King Charles Spaniel sitting with a soft warm expression on a sunlit cushion, "
        f"silky Blenheim chestnut-and-white coat, large dark expressive eyes, full body, "
        f"soft window light, blurred warm interior background, {STYLE_TAIL}",
    "most-protective-dog-breeds":
        f"A vigilant German Shepherd standing tall and alert on a stone path at golden hour, "
        f"black-and-tan saddle coat, full body in profile with watchful gaze, "
        f"warm afternoon light, blurred suburban background, {STYLE_TAIL}",
}


def gen_and_upload(fal_key: str, store: str, token: str, slug: str, prompt: str) -> tuple[str, str]:
    print(f"[{slug}] generating...", flush=True)
    src_path = gbi.run_one(fal_key, slug, prompt, OUT_DIR)
    unique = OUT_DIR / f"roundup-{slug}-hero.png"
    if src_path != unique:
        if unique.exists():
            unique.unlink()
        src_path.rename(unique)
    print(f"[{slug}] uploading...", flush=True)
    cdn_url = sfu.upload_one(store, token, unique, alt=f"{slug} hero")
    return slug, cdn_url


def main() -> int:
    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store = env.get("SHOPIFY_STORE", "")
    token = env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(PROMPTS)} hero images via fal.ai (~${len(PROMPTS) * 0.16:.2f})...")
    results: dict[str, str] = {}
    BATCH = 5
    slugs = list(PROMPTS.keys())
    for i in range(0, len(slugs), BATCH):
        chunk = slugs[i:i + BATCH]
        print(f"\n--- batch {i // BATCH + 1}: {len(chunk)} ---")
        with ThreadPoolExecutor(max_workers=BATCH) as ex:
            futures = {ex.submit(gen_and_upload, fal_key, store, token, s, PROMPTS[s]): s for s in chunk}
            for fut in as_completed(futures):
                s = futures[fut]
                try:
                    slug, url = fut.result()
                    results[slug] = url
                except Exception as e:
                    print(f"  FAIL {s}: {e}", flush=True)
        time.sleep(1)

    print(f"\nPatching {len(results)} JSONs...")
    for slug, url in results.items():
        p = BREED_DATA / f"{slug}.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        old = d.setdefault("images", {}).setdefault("hero", {}).get("url", "")
        d["images"]["hero"]["url"] = url
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {slug}: {old[:50]}... -> {url[:70]}...")

    print(f"\nDone. {len(results)}/{len(PROMPTS)} succeeded")
    return 0 if len(results) == len(PROMPTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
