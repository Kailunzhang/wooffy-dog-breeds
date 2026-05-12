"""Generate split-frame hero images for the 5 v3 comparison articles via fal.ai.

One-shot run: python3 scripts/generate_comparison_heroes_v3.py
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi
import shopify_files_upload as sfu

OUT_DIR = ROOT / "sample-images" / "comparison-heroes-v3"
BREED_DATA = ROOT / "breed-data"

STYLE_TAIL = (
    "both dogs are the dominant subjects with full bodies clearly visible, "
    "soft natural daylight, shallow depth of field with sharp focus on both dogs, "
    "professional pet photography, photorealistic, magazine cover quality, no humans, no text"
)

PROMPTS: dict[str, tuple[str, str]] = {
    "bernese-mountain-dog-vs-saint-bernard": (
        f"Two Swiss giant dogs standing side by side on a sunlit grass meadow with mountains in "
        f"the background: on the left, a Bernese Mountain Dog with long tri-color coat (black, "
        f"rust, white markings); on the right, a Saint Bernard with red-and-white short coat and "
        f"heavy build. Both standing alert in three-quarter angle, side-by-side comparison "
        f"composition, warm afternoon light, blurred alpine background, {STYLE_TAIL}",
        "Bernese Mountain Dog and Saint Bernard side by side, Swiss giant breed comparison",
    ),
    "sheepadoodle-vs-bernedoodle": (
        f"Two large doodle dogs standing side by side on a clean studio cream-colored floor: "
        f"on the left, a Sheepadoodle with dense wavy black-and-white panda coat; on the right, "
        f"a Bernedoodle with wavy tri-color coat (black with white chest and rust accents over "
        f"the eyes). Both standing alert in three-quarter angle, side-by-side comparison "
        f"composition, even soft studio lighting, {STYLE_TAIL}",
        "Sheepadoodle and Bernedoodle side by side, large doodle breed comparison",
    ),
    "newfoundland-vs-saint-bernard": (
        f"Two giant rescue breed dogs standing side by side on a sunlit lakeshore: on the left, "
        f"a black Newfoundland with thick water-resistant double coat; on the right, a Saint "
        f"Bernard with red-and-white coat and heavy build. Both standing alert in three-quarter "
        f"angle, side-by-side comparison composition, warm afternoon light, blurred lake "
        f"background, {STYLE_TAIL}",
        "Newfoundland and Saint Bernard side by side, giant rescue breed comparison",
    ),
    "vizsla-vs-weimaraner": (
        f"Two short-coated European pointing breed dogs standing alert side by side on a sunlit "
        f"grass meadow: on the left, a Vizsla with uniform rust-golden coat and matching eyes; "
        f"on the right, a Weimaraner with distinctive silver-gray coat and amber eyes. Both "
        f"standing alert in three-quarter angle showing the size contrast (Weimaraner larger), "
        f"side-by-side comparison composition, warm afternoon light, blurred field background, "
        f"{STYLE_TAIL}",
        "Vizsla and Weimaraner side by side, European pointing breed comparison",
    ),
    "mastiff-vs-cane-corso": (
        f"Two Molosser-derived guardian dogs standing side by side on a sunlit stone courtyard: "
        f"on the left, an enormous English Mastiff with fawn coat, black mask, wrinkled face, "
        f"and massive build; on the right, a more athletic Cane Corso with short brindle coat "
        f"and muscular leaner build. Both standing alert in three-quarter angle showing dramatic "
        f"size contrast, side-by-side comparison composition, warm afternoon light, blurred "
        f"natural background, {STYLE_TAIL}",
        "English Mastiff and Cane Corso side by side, Molosser guardian breed comparison",
    ),
}


def gen_and_upload(fal_key: str, store: str, token: str, slug: str, prompt: str, alt: str) -> tuple[str, str, str]:
    print(f"[{slug}] generating...", flush=True)
    src_path = gbi.run_one(fal_key, slug, prompt, OUT_DIR)
    unique = OUT_DIR / f"comparison-{slug}-hero.png"
    if src_path != unique:
        if unique.exists():
            unique.unlink()
        src_path.rename(unique)
    print(f"[{slug}] uploading...", flush=True)
    cdn_url = sfu.upload_one(store, token, unique, alt=alt)
    return slug, cdn_url, alt


def main() -> int:
    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store = env.get("SHOPIFY_STORE", "")
    token = env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(PROMPTS)} v3 comparison hero images (~${len(PROMPTS) * 0.16:.2f})...")
    results: dict[str, tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(gen_and_upload, fal_key, store, token, s, p, a): s for s, (p, a) in PROMPTS.items()}
        for fut in as_completed(futures):
            s = futures[fut]
            try:
                slug, url, alt = fut.result()
                results[slug] = (url, alt)
            except Exception as e:
                print(f"  FAIL {s}: {e}", flush=True)

    print(f"\nPatching {len(results)} comparison JSONs...")
    for slug, (url, alt) in results.items():
        p = BREED_DATA / f"{slug}.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        hero = d.setdefault("images", {}).setdefault("hero", {})
        old = hero.get("url", "")
        hero["url"] = url
        hero["alt"] = alt
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {slug}: {old[:50]}... -> {url[:70]}...")

    print(f"\nDone. {len(results)}/{len(PROMPTS)} succeeded")
    return 0 if len(results) == len(PROMPTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
