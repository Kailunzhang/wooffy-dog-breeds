"""Generate 4 HD sample images for a breed via fal.ai Nano Banana Pro.

Sample run: Golden Retriever. Reads FAL_KEY from ~/.claude.json.
Outputs to sample-images/<slug>/ as 01-adult.png, 02-grooming.png, 03-lifestyle.png, 04-puppy.png.
"""

import json
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

APP_ID = "fal-ai/nano-banana-pro"
QUEUE_BASE = f"https://queue.fal.run/{APP_ID}"


def load_fal_key() -> str:
    cfg = Path.home() / ".claude.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    key = data.get("mcpServers", {}).get("fal-ai", {}).get("env", {}).get("FAL_KEY")
    if not key:
        sys.exit("FAL_KEY not found in ~/.claude.json mcpServers.fal-ai.env")
    return key


def build_prompts(breed: str, coat: str, grooming_action: str, puppy_coat: str) -> list[tuple[str, str]]:
    return [
        ("01-adult-portrait", (
            f"Full-body photograph of an adult {breed}, {coat} coat, "
            f"standing alert in a natural outdoor setting — sunlit grass meadow with soft wildflowers, "
            f"warm golden-hour light from the side, three-quarter side angle showing the entire body "
            f"from nose to tail with all four legs clearly visible, "
            f"the dog is the absolute single subject and perfectly centered in the frame, "
            f"sharp focus on the dog, blurred natural background with shallow depth of field, "
            f"professional pet photography, photorealistic, magazine cover quality, "
            f"no humans, no text"
        )),
        ("02-grooming", (
            f"Full-body photograph of an adult {breed}, {coat} coat, "
            f"standing calmly on a wooden grooming table in a bright indoor home-studio setting, "
            f"{grooming_action}, "
            f"absolutely no humans visible anywhere in the frame — no people, no hands, no arms, "
            f"only the dog and the grooming tools, "
            f"the dog is the absolute single subject perfectly centered in the frame "
            f"with the entire body from nose to tail visible, "
            f"soft warm natural daylight from a window, blurred neutral indoor home background, "
            f"sharp focus on the dog, professional grooming photography, photorealistic, no text"
        )),
        ("03-lifestyle", (
            f"Full-body photograph of an adult {breed}, {coat} coat, "
            f"joyfully running on soft green grass in a sunny backyard, mid-action with all four legs "
            f"visible and tail flowing, an owner kneeling far in the soft-focus background "
            f"(back view only, small in the frame, never dominant, no face shown), "
            f"the dog is the absolute single dominant subject perfectly centered in the frame, "
            f"warm afternoon natural light, sharp focus on the dog with shallow depth of field, "
            f"lifestyle pet photography, photorealistic, magazine quality, no text"
        )),
        ("04-puppy", (
            f"Full-body photograph of an eight-week-old {breed} puppy with {puppy_coat}, "
            f"standing on soft green grass with tiny daisies, looking curiously toward the camera, "
            f"the puppy is the absolute single subject perfectly centered in the frame "
            f"with the entire body from nose to tail and all four paws visible, "
            f"soft natural daylight, shallow depth of field with blurred natural background, "
            f"professional puppy portrait, photorealistic, adorable but not cartoonish, "
            f"no humans, no text"
        )),
    ]


def http_json(method: str, url: str, key: str, body: dict | None = None, timeout: int = 60) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Key {key}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {url}: {err_body}") from e


def submit(key: str, prompt: str) -> str:
    body = {
        "prompt": prompt,
        "aspect_ratio": "3:2",
        "num_images": 1,
    }
    res = http_json("POST", QUEUE_BASE, key, body)
    rid = res.get("request_id")
    if not rid:
        raise RuntimeError(f"no request_id in submit response: {res}")
    return rid


def poll(key: str, request_id: str, label: str, max_wait: int = 240) -> dict:
    status_url = f"{QUEUE_BASE}/requests/{request_id}/status"
    response_url = f"{QUEUE_BASE}/requests/{request_id}"
    start = time.time()
    while True:
        s = http_json("GET", status_url, key)
        st = s.get("status")
        if st == "COMPLETED":
            return http_json("GET", response_url, key)
        if st in ("FAILED", "CANCELLED", "ERROR"):
            raise RuntimeError(f"[{label}] generation {st}: {s}")
        if time.time() - start > max_wait:
            raise TimeoutError(f"[{label}] still {st} after {max_wait}s")
        print(f"  [{label}] {st} ...", flush=True)
        time.sleep(4)


def download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as resp:
        dest.write_bytes(resp.read())


def run_one(key: str, label: str, prompt: str, out_dir: Path) -> Path:
    print(f"[{label}] submitting", flush=True)
    rid = submit(key, prompt)
    print(f"[{label}] request_id={rid}", flush=True)
    result = poll(key, rid, label)
    images = result.get("images") or []
    if not images:
        raise RuntimeError(f"[{label}] no images in result: {result}")
    img_url = images[0].get("url")
    if not img_url:
        raise RuntimeError(f"[{label}] no url on image[0]: {images[0]}")
    ext = ".png" if img_url.lower().split("?")[0].endswith(".png") else ".jpg"
    dest = out_dir / f"{label}{ext}"
    download(img_url, dest)
    print(f"[{label}] saved -> {dest}", flush=True)
    return dest


BREEDS_TO_RUN: list[dict] = [
    {
        "slug": "airedale-terrier",
        "name": "Airedale Terrier",
        "coat": "dense wiry black saddle and tan body with a beard and bushy eyebrows",
        "grooming_action": "with a wire stripping comb, slicker brush, and steel comb laid out on the table beside the dog",
        "puppy_coat": "soft fluffy black-and-tan puppy coat (still soft, before the wiry adult coat develops)",
    },
]


def main() -> int:
    key = load_fal_key()
    base = Path("C:/Users/kailu/Claude_Projects/wooffy-dog-breeds/sample-images")

    overall: list[tuple[str, str, str | Path | Exception]] = []

    for cfg in BREEDS_TO_RUN:
        slug = cfg["slug"]
        out_dir = base / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        prompts = build_prompts(cfg["name"], cfg["coat"], cfg["grooming_action"], cfg["puppy_coat"])
        print(f"\n>>> {slug} — submitting 4 images")

        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(run_one, key, label, p, out_dir): label for label, p in prompts}
            for fut in as_completed(futures):
                label = futures[fut]
                try:
                    overall.append((slug, label, fut.result()))
                except Exception as e:
                    overall.append((slug, label, e))

    print("\n=== summary ===")
    rc = 0
    for slug, label, r in sorted(overall):
        if isinstance(r, Exception):
            print(f"FAIL {slug} {label}: {r}")
            rc = 1
        else:
            print(f"OK   {slug} {label}: {r}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
