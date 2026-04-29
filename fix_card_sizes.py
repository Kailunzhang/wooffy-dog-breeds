#!/usr/bin/env python3
"""
Resize every Wikimedia Commons image URL across roundups and breed heroes
to the largest thumb size the source actually supports (capped at 1200px).

Solves: prior bulk 1200px upgrade produced HTTP 400 for any source image whose
original width is below 1200px. Wikimedia rejects oversized thumb requests.

Usage:
    python3 fix_card_sizes.py                # dry-run
    python3 fix_card_sizes.py --apply        # write JSON changes
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "breed-data"
LOG = ROOT / "fix_card_sizes.log"
UA = "wooffy-fix/1.1 (https://thewooffy.com)"
TARGET_PX = 1200
BATCH = 40

WIKI_FILE_RE = re.compile(
    r"^(https://upload\.wikimedia\.org/wikipedia/commons/)"
    r"(?:thumb/)?"
    r"([0-9a-f]/[0-9a-f]{2}/)"
    r"([^/\"]+?\.(?:jpg|jpeg|png|JPG|JPEG|PNG))"
    r"(?:/\d+px-[^/\"]+)?$"
)

CARD_IMG = re.compile(
    r'<img\s+src="(https://upload\.wikimedia\.org/wikipedia/commons/[^"]+)"'
)


def parse(url):
    m = WIKI_FILE_RE.match(url)
    return m.groups() if m else None


def fetch_thumb_urls(filenames, target_px=TARGET_PX):
    """Ask Commons API for the canonical thumbnail URL at target_px.
    For sources smaller than target, the API returns the original URL form
    (no /thumb/Npx-/ path). For larger sources, returns a valid thumb URL.
    Either way, the returned URL is guaranteed-servable by Wikimedia's
    'allowed thumbnail steps' rule."""
    out = {}
    fns = sorted(filenames)
    for i in range(0, len(fns), BATCH):
        batch = fns[i:i + BATCH]
        decoded = [urllib.parse.unquote(f) for f in batch]
        titles = "|".join(f"File:{t}" for t in decoded)
        url = (
            "https://commons.wikimedia.org/w/api.php?action=query&format=json"
            f"&prop=imageinfo&iiprop=url|size&iiurlwidth={target_px}"
            "&titles=" + urllib.parse.quote(titles, safe="|:")
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())
        except Exception as e:
            print(f"  [api-error batch {i}] {e}")
            continue

        api = {}
        for _pid, page in data.get("query", {}).get("pages", {}).items():
            ii = page.get("imageinfo")
            if not ii:
                continue
            title = page.get("title", "").replace("File:", "")
            api[title] = ii[0].get("thumburl") or ii[0].get("url")

        for fn, dec in zip(batch, decoded):
            for c in (dec, dec.replace("_", " ")):
                if c in api:
                    out[fn] = api[c]
                    break
        time.sleep(0.3)
    return out


def rewrite(url, thumbs_by_fn):
    parsed = parse(url)
    if not parsed:
        return None
    _base, _hashpath, filename = parsed
    return thumbs_by_fn.get(filename)


def load(p):
    return json.load(open(p, encoding="utf-8"))


def save(p, d):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")


# Only fix breed JSONs that were touched by prior buggy runs. Avoid rewriting
# untouched supporting articles (grooming/costs/checklist) on a site-wide scale.
TOUCHED_BREED_SLUGS = {
    "mastiff", "tibetan-mastiff", "pharaoh-hound", "yorkshire-terrier",
    "australian-cattle-dog", "ibizan-hound", "neapolitan-mastiff",
    "saluki", "shiba-inu",
}


def main():
    apply_changes = "--apply" in sys.argv

    by_file_urls = {}
    file_targets = {}

    for fn in sorted(os.listdir(DATA)):
        if not fn.endswith(".json"):
            continue
        p = DATA / fn
        try:
            d = load(p)
        except Exception:
            continue
        meta = d.get("meta", {})
        is_roundup = meta.get("size_category") == "Roundup"
        slug = meta.get("slug", "")
        # Scope: all roundups (had card thumbs touched) + only the 9 breed JSONs we touched
        if not is_roundup and slug not in TOUCHED_BREED_SLUGS:
            continue
        urls = set()
        hero = d.get("images", {}).get("hero", {}).get("url")
        if hero and parse(hero):
            urls.add(hero)
        if is_roundup:
            for k in ("care", "special"):
                v = d.get("sections", {}).get(k)
                if not isinstance(v, dict):
                    continue
                for u in CARD_IMG.findall(v.get("html", "") or ""):
                    if parse(u):
                        urls.add(u)
        if urls:
            file_targets[str(p)] = urls
            for u in urls:
                fname = parse(u)[2]
                by_file_urls.setdefault(fname, set()).add(u)

    print(f"Files containing Wikimedia URLs: {len(file_targets)}")
    print(f"Unique source files: {len(by_file_urls)}")

    print("Querying Commons API for canonical thumb URLs...")
    thumbs = fetch_thumb_urls(set(by_file_urls.keys()))
    print(f"Got URLs for {len(thumbs)}/{len(by_file_urls)} files.")
    missing = [f for f in by_file_urls if f not in thumbs]
    if missing:
        print(f"  Missing: {missing[:10]}{'...' if len(missing) > 10 else ''}")

    replacements = {}
    for u_set in by_file_urls.values():
        for old in u_set:
            new = rewrite(old, thumbs)
            if new and new != old:
                replacements[old] = new
    print(f"URL rewrites planned: {len(replacements)}")

    files_changed = []
    log_lines = []
    for path, _urls in file_targets.items():
        d = load(path)
        modified = False

        hero = d.get("images", {}).get("hero", {}).get("url")
        if hero and hero in replacements:
            d["images"]["hero"]["url"] = replacements[hero]
            modified = True
            log_lines.append(f"[hero] {os.path.basename(path)}: {hero[:90]} -> {replacements[hero][:90]}")

        if d.get("meta", {}).get("size_category") == "Roundup":
            for k in ("care", "special"):
                v = d.get("sections", {}).get(k)
                if not isinstance(v, dict):
                    continue
                html = v.get("html", "") or ""
                new_html = html
                for old, new in replacements.items():
                    if old in new_html:
                        new_html = new_html.replace(old, new)
                if new_html != html:
                    v["html"] = new_html
                    modified = True
                    log_lines.append(f"[card] {os.path.basename(path)} sec={k}")

        if modified:
            files_changed.append(path)
            if apply_changes:
                save(path, d)

    summary = (
        f"\n=== Summary ===\n"
        f"Files changed:    {len(files_changed)}\n"
        f"URL rewrites:     {len(replacements)}\n"
        f"Mode:             {'APPLY' if apply_changes else 'DRY-RUN'}\n"
    )
    print("\n".join(log_lines[:60]))
    if len(log_lines) > 60:
        print(f"  ... ({len(log_lines) - 60} more — see log)")
    print(summary)
    LOG.write_text("\n".join(log_lines) + summary, encoding="utf-8")
    print(f"Log: {LOG}")

    roundup_slugs = []
    breed_slugs = []
    for p in files_changed:
        try:
            d = load(p)
            slug = d.get("meta", {}).get("slug")
            if not slug:
                continue
            if d.get("meta", {}).get("size_category") == "Roundup":
                roundup_slugs.append(slug)
            else:
                breed_slugs.append(slug)
        except Exception:
            pass
    if roundup_slugs:
        print(f"\nAffected roundup slugs ({len(roundup_slugs)}):")
        print(" ".join(roundup_slugs))
    if breed_slugs:
        print(f"\nAffected breed slugs ({len(breed_slugs)}):")
        print(" ".join(breed_slugs))


if __name__ == "__main__":
    main()
