"""Generate split-frame hero images for the 5 v4 comparison articles via fal.ai.

One-shot run: python3 scripts/generate_comparison_heroes_v4.py
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

OUT_DIR = ROOT / "sample-images" / "comparison-heroes-v4"
BREED_DATA = ROOT / "breed-data"

STYLE_TAIL = (
    "both dogs are the dominant subjects with full bodies clearly visible, "
    "soft natural daylight, shallow depth of field with sharp focus on both dogs, "
    "professional pet photography, photorealistic, magazine cover quality, no humans, no text"
)

PROMPTS: dict[str, tuple[str, str]] = {
    "golden-retriever-vs-german-shepherd": (
        f"Two iconic family/working dogs standing side by side on a sunlit grass meadow: "
        f"on the left, a Golden Retriever with rich golden long flowing double coat and "
        f"friendly expression; on the right, a German Shepherd with classic black-and-tan "
        f"saddle pattern and watchful expression. Both standing alert in three-quarter angle, "
        f"similar size, side-by-side comparison composition, warm afternoon light, "
        f"blurred natural background, {STYLE_TAIL}",
        "Golden Retriever and German Shepherd side by side, family and working breed comparison",
    ),
    "cane-corso-vs-great-dane": (
        f"Two large breeds standing side by side on a sunlit stone courtyard: on the left, "
        f"a muscular athletic Cane Corso with short brindle coat; on the right, a towering "
        f"Great Dane (significantly taller) with fawn coat and elegant build. Both standing "
        f"alert in three-quarter angle showing dramatic size contrast (Dane much taller), "
        f"side-by-side comparison composition, warm afternoon light, blurred natural "
        f"background, {STYLE_TAIL}",
        "Cane Corso and Great Dane side by side, large breed comparison",
    ),
    "bernedoodle-vs-aussiedoodle": (
        f"Two doodle dogs standing side by side on a clean studio cream-colored floor: on "
        f"the left, a Bernedoodle with wavy tri-color coat (black with white chest and rust "
        f"accents); on the right, an Aussiedoodle with wavy blue merle coat (mottled gray-blue "
        f"with black patches). Both standing alert in three-quarter angle, side-by-side "
        f"comparison composition, even soft studio lighting, {STYLE_TAIL}",
        "Bernedoodle and Aussiedoodle side by side, doodle breed comparison",
    ),
    "vizsla-vs-german-shorthaired-pointer": (
        f"Two short-coated European pointing dogs standing alert side by side on a sunlit "
        f"grass meadow: on the left, a Vizsla with uniform rust-golden coat and matching "
        f"eyes; on the right, a German Shorthaired Pointer with liver-and-white ticked coat. "
        f"Both standing alert in three-quarter angle, side-by-side comparison composition, "
        f"warm afternoon light, blurred field background, {STYLE_TAIL}",
        "Vizsla and German Shorthaired Pointer side by side, European pointing breed comparison",
    ),
    "great-dane-vs-doberman": (
        f"Two German breeds standing side by side on a sunlit grass meadow: on the left, "
        f"a towering Great Dane with fawn coat and elegant tall build; on the right, "
        f"a sleek lean Doberman Pinscher with black-and-rust short coat and athletic build. "
        f"Both standing alert in three-quarter angle showing the dramatic size contrast "
        f"(Dane much taller), side-by-side comparison composition, warm afternoon light, "
        f"blurred natural background, {STYLE_TAIL}",
        "Great Dane and Doberman Pinscher side by side, large breed comparison",
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

    print(f"Generating {len(PROMPTS)} v4 comparison hero images (~${len(PROMPTS) * 0.16:.2f})...")
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
