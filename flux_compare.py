"""One-off head-to-head comparison: regenerate the 4 Labrador prompts via FLUX.1 [dev]
so the user can compare against the existing Nano Banana Pro version at
sample-images/labrador-retriever/.

Outputs to sample-images/labrador-retriever-flux/.
"""

import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import generate_breed_images as gbi  # type: ignore  # noqa: E402

APP_ID = "fal-ai/flux/dev"
QUEUE_BASE = f"https://queue.fal.run/{APP_ID}"
OUT_DIR = ROOT / "sample-images" / "labrador-retriever-flux"


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
        body_txt = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {url}: {body_txt}") from e


def submit(key: str, prompt: str) -> tuple[str, str, str]:
    body = {
        "prompt": prompt,
        "image_size": {"width": 1264, "height": 848},
        "num_images": 1,
        "num_inference_steps": 28,
        "enable_safety_checker": False,
    }
    res = http_json("POST", QUEUE_BASE, key, body)
    rid = res.get("request_id")
    status_url = res.get("status_url") or f"{QUEUE_BASE}/requests/{rid}/status"
    response_url = res.get("response_url") or f"{QUEUE_BASE}/requests/{rid}"
    if not rid:
        raise RuntimeError(f"no request_id: {res}")
    return rid, status_url, response_url


def poll(key: str, status_url: str, response_url: str, label: str, max_wait: int = 240) -> dict:
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


def run_one(key: str, label: str, prompt: str) -> Path:
    print(f"[{label}] FLUX submitting", flush=True)
    rid, status_url, response_url = submit(key, prompt)
    print(f"[{label}] request_id={rid}", flush=True)
    result = poll(key, status_url, response_url, label)
    images = result.get("images") or []
    if not images:
        raise RuntimeError(f"[{label}] no images: {result}")
    url = images[0].get("url")
    ext = ".png" if url.lower().split("?")[0].endswith(".png") else ".jpg"
    dest = OUT_DIR / f"{label}{ext}"
    download(url, dest)
    print(f"[{label}] saved -> {dest}", flush=True)
    return dest


def main() -> int:
    key = gbi.load_fal_key()
    traits = json.loads((ROOT / "breed_traits.json").read_text(encoding="utf-8"))
    lab = next(t for t in traits if t["slug"] == "labrador-retriever")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompts = gbi.build_prompts(lab["name"], lab["coat"], lab["grooming_action"], lab["puppy_coat"])

    results: list[tuple[str, Path | Exception]] = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(run_one, key, label, p): label for label, p in prompts}
        for fut in as_completed(futures):
            label = futures[fut]
            try:
                results.append((label, fut.result()))
            except Exception as e:
                results.append((label, e))

    print("\n=== summary ===")
    rc = 0
    for label, r in sorted(results):
        if isinstance(r, Exception):
            print(f"FAIL {label}: {r}"); rc = 1
        else:
            print(f"OK   {label}: {r}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
