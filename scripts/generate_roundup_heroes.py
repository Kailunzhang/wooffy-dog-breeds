"""Generate dedicated hero images for the 35 roundup articles + fix the
golden-retriever-outdoor-space Q&A hero.

Each roundup gets one custom hero image themed to its topic. The Q&A article
reuses the existing golden-retriever adult-portrait CDN URL.

Usage:
  python scripts/generate_roundup_heroes.py            # generate + upload + patch JSONs
  python scripts/generate_roundup_heroes.py --push     # also push --update to live Shopify
"""

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi  # type: ignore  # noqa: E402
import shopify_files_upload as sfu  # type: ignore  # noqa: E402

OUT_DIR = ROOT / "sample-images" / "roundup-heroes"
BREED_DATA = ROOT / "breed-data"
STATE_PATH = ROOT / "batch_state.json"


STYLE_TAIL = (
    "the dog is the absolute single subject perfectly centered with full body and all four legs visible, "
    "soft natural daylight, shallow depth of field with sharp focus on the dog, "
    "professional pet photography, photorealistic, magazine cover quality, no humans, no text"
)

ROUNDUP_PROMPTS: dict[str, str] = {
    "best-dogs-for-active-people":
        f"A vibrant German Shorthaired Pointer mid-leap across a sunlit grass meadow, full-body action shot, golden-hour light, blurred green forest background, {STYLE_TAIL}",
    "best-dogs-for-cold-climates":
        f"A majestic Siberian Husky with thick black-and-white double coat standing alert in deep fresh snow, breath visible in cold air, full body in profile, soft winter daylight, blurred snowy forest background, {STYLE_TAIL}",
    "best-dogs-for-first-time-owners":
        f"A friendly Cavalier King Charles Spaniel sitting calmly on a soft sunlit lawn, gentle expression, full body, warm afternoon light, blurred garden background, {STYLE_TAIL}",
    "best-dogs-for-hiking":
        f"An athletic Australian Shepherd standing on a rocky mountain trail, full body in profile, expansive blurred mountain valley background, golden-hour light, {STYLE_TAIL}",
    "best-dogs-for-hot-climates":
        f"A lean Vizsla standing on a sunlit sandy path, short rust-golden coat catching warm light, full body, blurred dry-grass landscape background, {STYLE_TAIL}",
    "best-dogs-for-seniors":
        f"A calm Bichon Frise sitting on a soft pastel cushion in a sunny indoor scene, fluffy white coat, full body, soft window light, blurred warm interior background, {STYLE_TAIL}",
    "best-dogs-for-small-apartments":
        f"A French Bulldog with bat ears sitting on a hardwood floor in a sunlit modern apartment, full body, soft window light, blurred minimalist living-room background, {STYLE_TAIL}",
    "best-family-dog-breeds":
        f"A friendly Golden Retriever sitting on a sunny grass lawn with a relaxed welcoming expression, full body in profile, warm afternoon light, blurred suburban backyard background, {STYLE_TAIL}",
    "best-gentle-giant-dog-breeds":
        f"A massive Great Dane standing tall on a quiet grass field, full body in profile showing impressive height, soft late-afternoon light, blurred treeline background, {STYLE_TAIL}",
    "best-guard-dog-breeds":
        f"A powerful Doberman Pinscher standing alert with watchful gaze on a stone path, full body in profile, dramatic side-light at dusk, blurred misty background, {STYLE_TAIL}",
    "best-gun-dog-breeds":
        f"A focused English Setter in pointing stance on tall grass meadow, silky coat with feathering visible, full body in profile, warm golden-hour light, blurred reedy field background, {STYLE_TAIL}",
    "best-herding-dog-breeds":
        f"A focused Border Collie locked in classic herding crouch on grass field, full body, intense gaze, golden-hour light, blurred pasture background, {STYLE_TAIL}",
    "best-hound-dog-breeds":
        f"A Beagle with characteristic tricolor coat and droopy ears walking on a forest path, full body in profile, dappled forest light, blurred woodland background, {STYLE_TAIL}",
    "best-hunting-dog-breeds":
        f"A Labrador Retriever standing alert at the edge of a calm lake, full body in profile, mist on the water, soft early-morning light, blurred reedy lakeshore background, {STYLE_TAIL}",
    "best-hypoallergenic-dog-breeds":
        f"An elegant Standard Poodle in a refined sporting clip standing on a clean indoor wooden floor, full body in profile, bright soft window light, blurred minimal interior background, {STYLE_TAIL}",
    "best-large-dog-breeds":
        f"An impressive Bernese Mountain Dog with tri-color coat standing in a sunlit alpine meadow, full body in profile, warm afternoon light, blurred mountain valley background, {STYLE_TAIL}",
    "best-non-sporting-dog-breeds":
        f"A Dalmatian with classic black spots standing on a clean garden path, full body in profile, bright daylight, blurred green-hedge background, {STYLE_TAIL}",
    "best-small-dog-breeds":
        f"A tiny Yorkshire Terrier with long silky steel-blue-and-tan coat sitting on a soft pastel cushion, full body, soft natural daylight, blurred warm indoor background, {STYLE_TAIL}",
    "best-sporting-dog-breeds":
        f"A poised English Springer Spaniel with feathered liver-and-white coat standing in tall meadow grass, full body in profile, golden-hour light, blurred field background, {STYLE_TAIL}",
    "best-terrier-breeds":
        f"A spirited Jack Russell Terrier standing alertly on a rustic wooden barn floor with confident expression, full body in profile, warm side-light from a window, blurred warm farmhouse background, {STYLE_TAIL}",
    "best-toy-dog-breeds":
        f"A Pomeranian with fluffy orange fox-like double coat sitting on a soft cream rug, full body, soft natural daylight, blurred warm interior background, {STYLE_TAIL}",
    "best-watchdog-breeds":
        f"An alert German Shepherd standing watch on a stone porch at golden hour, full body in profile, dramatic side-light, blurred suburban background, {STYLE_TAIL}",
    "best-working-dog-breeds":
        f"A powerful Rottweiler standing confidently on a grass field, short black-and-mahogany coat, full body in profile, warm late-afternoon light, blurred countryside background, {STYLE_TAIL}",
    "dog-breeds-by-group":
        f"A noble Golden Retriever standing on a sunlit grass meadow representing the diversity of dog breeds, full body in profile, warm afternoon light, blurred natural background, {STYLE_TAIL}",
    "dog-breeds-by-size":
        f"A Great Dane and a Chihuahua side by side on a clean studio floor showing dramatic size contrast, both in full body, soft even daylight, blurred warm-cream background, "
        f"both dogs are the dominant subjects perfectly centered with full bodies and all legs visible, "
        f"soft natural daylight, shallow depth of field with sharp focus on the dogs, "
        f"professional pet photography, photorealistic, magazine cover quality, no humans, no text",
    "dog-breeds-good-with-cats":
        f"A calm Cavalier King Charles Spaniel sitting peacefully on a sunlit windowsill, full body in profile, soft window light, blurred warm interior background, {STYLE_TAIL}",
    "easiest-dogs-to-train":
        f"A focused Border Collie sitting alert with intelligent gaze on grass field, full body in profile, golden-hour light, blurred pasture background, {STYLE_TAIL}",
    "longest-living-dog-breeds":
        f"A Chihuahua with apple-dome head sitting on a soft pastel cushion, full body, soft natural light, blurred warm indoor background, {STYLE_TAIL}",
    "low-maintenance-dog-breeds":
        f"A sleek Whippet standing on a clean grass lawn, short smooth coat catching soft light, full body in profile, bright daylight, blurred minimal park background, {STYLE_TAIL}",
    "most-expensive-dog-breeds":
        f"A regal Tibetan Mastiff with dramatic black-and-tan lion-like mane standing on a stone terrace, full body in profile, golden-hour light, blurred mountain valley background, {STYLE_TAIL}",
    "most-intelligent-dog-breeds":
        f"A Border Collie locked in focused herding stance on grass field, intense intelligent gaze, full body, golden-hour light, blurred pasture background, {STYLE_TAIL}",
    "most-loyal-dog-breeds":
        f"A loyal German Shepherd sitting alertly on a stone path with watchful gaze, full body in profile, warm afternoon light, blurred suburban background, {STYLE_TAIL}",
    "most-popular-dog-breeds":
        f"A Labrador Retriever with classic yellow coat sitting on a sunlit grass lawn, friendly relaxed expression, full body in profile, warm afternoon light, blurred suburban backyard background, {STYLE_TAIL}",
    "quietest-dog-breeds":
        f"A calm Greyhound lying gracefully on a soft cream rug indoors, lean elegant body fully visible, soft window light, blurred minimalist warm interior background, {STYLE_TAIL}",
    "rarest-dog-breeds":
        f"An exotic Xoloitzcuintli with smooth dark gray-black hairless skin and bat-like ears standing on a sunlit garden path, full body in profile, soft golden-hour light, blurred natural background, {STYLE_TAIL}",
}


def submit_and_run(key: str, slug: str, prompt: str) -> Path:
    print(f"[{slug}] generating...", flush=True)
    return gbi.run_one(key, slug, prompt, OUT_DIR)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store, token = env.get("SHOPIFY_STORE", ""), env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    slugs = sorted(ROUNDUP_PROMPTS.keys())
    paths: dict[str, Path] = {}
    BATCH = 6
    for i in range(0, len(slugs), BATCH):
        chunk = slugs[i:i + BATCH]
        print(f"\n--- batch {i // BATCH + 1}: {len(chunk)} ---")
        with ThreadPoolExecutor(max_workers=BATCH) as ex:
            futures = {ex.submit(submit_and_run, fal_key, s, ROUNDUP_PROMPTS[s]): s for s in chunk}
            for fut in as_completed(futures):
                s = futures[fut]
                try:
                    paths[s] = fut.result()
                except Exception as e:
                    print(f"  FAIL {s}: {e}", flush=True)
        time.sleep(1)

    cdn_urls: dict[str, str] = {}
    for s in slugs:
        if s not in paths:
            continue
        unique = OUT_DIR / f"roundup-{s}-hero.png"
        if paths[s] != unique and unique.exists():
            unique.unlink()
        if paths[s] != unique:
            paths[s].rename(unique)
        url = sfu.upload_one(store, token, unique, alt=f"{s} hero")
        cdn_urls[s] = url

    changed_slugs: list[str] = []
    for s, url in cdn_urls.items():
        p = BREED_DATA / f"{s}.json"
        if not p.exists():
            print(f"  WARN: missing {p}")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        hero = d.setdefault("images", {}).setdefault("hero", {})
        old = hero.get("url", "")
        hero["url"] = url
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        changed_slugs.append(s)
        print(f"  patched {s}: {old[:60]} -> {url[:80]}")

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    gr_url = state.get("golden-retriever", {}).get("image_urls", {}).get("01-adult-portrait")
    qa_path = BREED_DATA / "golden-retriever-outdoor-space.json"
    if gr_url and qa_path.exists():
        d = json.loads(qa_path.read_text(encoding="utf-8"))
        hero = d.setdefault("images", {}).setdefault("hero", {})
        old = hero.get("url", "")
        hero["url"] = gr_url
        qa_path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        changed_slugs.append("golden-retriever-outdoor-space")
        print(f"  patched golden-retriever-outdoor-space: {old[:60]} -> {gr_url[:80]}")

    print(f"\n=== summary ===")
    print(f"generated: {len(paths)}/{len(slugs)}")
    print(f"uploaded:  {len(cdn_urls)}")
    print(f"patched:   {len(changed_slugs)}")

    if not args.push:
        print("\n(JSONs written — pass --push to push --update to live Shopify)")
        return 0

    if not changed_slugs:
        print("nothing to push.")
        return 0
    chunk_size = 20
    for i in range(0, len(changed_slugs), chunk_size):
        chunk = changed_slugs[i:i + chunk_size]
        print(f"\n--- push chunk {i // chunk_size + 1}: {len(chunk)} ---")
        cmd = ["python", str(ROOT / "scripts" / "generate.py"), *chunk, "--update"]
        proc = subprocess.run(cmd, input="YES\n", text=True, cwd=str(ROOT))
        if proc.returncode != 0:
            print(f"chunk failed (exit={proc.returncode})")
            return 1
    print("\ndone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
