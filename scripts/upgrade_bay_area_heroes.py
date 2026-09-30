"""Give the five Bay Area local guides proper hero images (2026-09-30).

best-dog-parks-south-bay had no featured image at all (never set at publish);
the other four had 500px heroes (the beaches one 500x91). Every guide already
shows CC-licensed Wikimedia Commons photos in its body with visible credits, so
the hero reuses one of those photos at 1600px:
  - start from the photo that matches the current hero (or the first body photo),
  - skip panoramas/slivers (aspect outside 1.2-2.0) and fall through to the next,
  - alt text carries the author/licence credit, same format as before.

Run:
    python3 scripts/upgrade_bay_area_heroes.py           # dry-run: print picks
    python3 scripts/upgrade_bay_area_heroes.py --apply   # upload + patch JSONs
    echo YES | python3 scripts/generate.py <slugs> --update
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import shopify_files_upload as sfu  # noqa: E402
from generate_halloween_eggplant_heroes import patch_json  # noqa: E402

SLUGS = ["best-dog-parks-south-bay", "best-dog-parks-san-francisco",
         "best-off-leash-dog-parks-east-bay", "dog-friendly-hikes-east-bay",
         "top-9-dog-friendly-beaches-in-san-francisco-bay-area"]
OUT_DIR = ROOT / "sample-images" / "bay-area-heroes"
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "WooffyHeroUpgrade/1.0 (https://thewooffy.com; wooffy@thewooffy.com)"}
WIDTH = 1600
MIN_ASPECT, MAX_ASPECT = 1.2, 2.0


def body_photos(body: str) -> list[dict]:
    """Body <img> tags with the Commons file and credit that follow each one."""
    out = []
    for m in re.finditer(r"<img[^>]+>", body):
        tail = body[m.end():m.end() + 1200]
        commons = re.search(r'href="(https://commons\.wikimedia\.org/wiki/File:[^"]+)"', tail)
        tail_text = html.unescape(re.sub(r"<[^>]+>", "", tail))
        credit = re.search(r"Photo:\s*(.+?)\s*·\s*(CC [^·]+?)\s*·", tail_text)
        alt = re.search(r'alt="([^"]*)"', m.group(0))
        src = re.search(r'src="([^"]+)"', m.group(0))
        if commons and credit:
            out.append({"file": urllib.parse.unquote(commons.group(1).split("/wiki/")[1]),
                        "author": credit.group(1).strip(), "license": credit.group(2).strip(),
                        "alt": alt.group(1) if alt else "", "src": src.group(1) if src else ""})
    return out


def commons_info(file_title: str) -> dict | None:
    q = urllib.parse.urlencode({"action": "query", "titles": file_title, "prop": "imageinfo",
                                "iiprop": "url|size", "iiurlwidth": WIDTH, "format": "json"})
    with urllib.request.urlopen(urllib.request.Request(f"{API}?{q}", headers=UA), timeout=30) as r:
        pages = json.load(r)["query"]["pages"]
    info = next(iter(pages.values())).get("imageinfo")
    return info[0] if info else None


def pick(slug: str, used: set[str]) -> tuple[dict, dict] | None:
    """First suitable body photo not already used as another guide's hero."""
    d = json.loads((ROOT / "breed-data" / f"{slug}.json").read_text(encoding="utf-8"))
    photos = body_photos(d.get("body_html", ""))
    hero_name = (((d.get("images") or {}).get("hero") or {}).get("url") or "").split("/")[-1].split("?")[0]
    photos.sort(key=lambda p: 0 if hero_name and p["src"].split("/")[-1].split("?")[0] == hero_name else 1)
    for p in photos:
        if p["file"] in used:
            continue
        info = commons_info(p["file"])
        if not info or not info.get("width") or not info.get("height"):
            continue
        aspect = info["width"] / info["height"]
        if MIN_ASPECT <= aspect <= MAX_ASPECT and info["width"] >= 1200:
            return p, info
    return None


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    env = sfu.load_env()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    for slug in SLUGS:
        chosen = pick(slug, used)
        if chosen is None:
            print(f"[{slug}] no suitable Commons photo found")
            continue
        p, info = chosen
        used.add(p["file"])
        place = p["alt"].split(" — ")[0] or p["file"]
        alt = (f"{place} — from Wooffy's Bay Area dog guide "
               f"(photo: {p['author']}, {p['license']}, Wikimedia Commons)")
        print(f"[{slug}] {p['file']}  {info['width']}x{info['height']}  -> {info.get('thumburl', '')[:90]}")
        if not apply:
            continue
        ext = ".png" if info["thumburl"].lower().endswith(".png") else ".jpg"
        dest = OUT_DIR / f"{slug}-hero{ext}"
        with urllib.request.urlopen(urllib.request.Request(info["thumburl"], headers=UA), timeout=60) as r:
            dest.write_bytes(r.read())
        cdn = sfu.upload_one(env["SHOPIFY_STORE"], env["SHOPIFY_TOKEN"], dest, alt=alt)
        patch_json(slug, cdn, alt)
        print(f"[{slug}] hero -> {cdn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
