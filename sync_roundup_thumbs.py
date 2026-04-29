#!/usr/bin/env python3
"""
Sync roundup card thumbnails with each breed's canonical hero URL.

Source of truth: breed-data/[slug].json -> images.hero.url
Targets:         every roundup's sections.{care|special}.html <img> in breed cards

If a breed's own hero is also dead, repair it via the Wikipedia pageimage API
and patch the breed JSON too.

Usage:
    python3 sync_roundup_thumbs.py                # dry-run
    python3 sync_roundup_thumbs.py --apply        # write JSON changes
    python3 sync_roundup_thumbs.py --apply --push # also push --update to Shopify
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "breed-data"
LOG = ROOT / "sync_roundup_thumbs.log"
UA = "wooffy-thumb-sync/1.0 (https://thewooffy.com)"

# Card pattern: <img src="..." alt="..." ...>  ...  <a href="/blogs/dog-breeds/<slug>"
CARD = re.compile(
    r'(<img\s+src=")(?P<url>[^"]+)("\s+alt="[^"]+"[^>]*>)'
    r'(?P<between>.*?)'
    r'(<a\s+href="/blogs/dog-breeds/)(?P<slug>[a-z0-9-]+)(")',
    re.DOTALL,
)


def head_ok(url, cache, timeout=6):
    if url in cache:
        return cache[url]
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ok = 200 <= r.status < 400
    except urllib.error.HTTPError as e:
        ok = 200 <= e.code < 400
    except Exception:
        ok = False
    cache[url] = ok
    return ok


def wiki_pageimage(breed_name, size=1200, timeout=10):
    title = breed_name.replace(" ", "_")
    url = (
        "https://en.wikipedia.org/w/api.php?action=query&format=json"
        f"&prop=pageimages&piprop=thumbnail&pithumbsize={size}"
        f"&titles={urllib.parse.quote(title)}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        for _pid, page in data.get("query", {}).get("pages", {}).items():
            src = page.get("thumbnail", {}).get("source")
            if src:
                return src
    except Exception:
        pass
    return None


def slug_to_name(slug):
    return " ".join(w.capitalize() for w in slug.split("-"))


# Matches Wikimedia Commons file URLs in either thumb or original form.
# Captures: (base, hashpath, filename) and ignores any existing /Npx-... suffix.
_WIKI_FILE = re.compile(
    r"^(https://upload\.wikimedia\.org/wikipedia/commons/)"
    r"(?:thumb/)?"
    r"([0-9a-f]/[0-9a-f]{2}/)"
    r"([^/]+?\.(?:jpg|jpeg|png|JPG|JPEG|PNG))"
    r"(?:/\d+px-[^/]+)?$"
)


def upgrade_resolution(url, target_px=1200):
    """Rewrite a Wikimedia Commons URL to a target_px-wide thumb. Non-Wikimedia URLs pass through."""
    m = _WIKI_FILE.match(url)
    if not m:
        return url
    base, hashpath, filename = m.groups()
    return f"{base}thumb/{hashpath}{filename}/{target_px}px-{filename}"


def find_card_section(sections):
    for k in ("care", "special"):
        v = sections.get(k)
        if isinstance(v, dict) and CARD.search(v.get("html", "")):
            return k
    for k, v in sections.items():
        if isinstance(v, dict) and CARD.search(v.get("html", "")):
            return k
    return None


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(p, d):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    apply_changes = "--apply" in sys.argv
    push = "--push" in sys.argv

    head_cache = {}
    breed_hero_cache = {}
    log_lines = []
    breed_jsons_patched = []

    def resolve_breed_hero(slug):
        if slug in breed_hero_cache:
            return breed_hero_cache[slug]
        path = DATA / f"{slug}.json"
        if not path.exists():
            log_lines.append(f"[no-json] {slug}: breed-data/{slug}.json not found")
            breed_hero_cache[slug] = None
            return None
        d = load_json(path)
        cur = d.get("images", {}).get("hero", {}).get("url")
        if cur and head_ok(cur, head_cache):
            breed_hero_cache[slug] = cur
            return cur
        new_url = wiki_pageimage(slug_to_name(slug))
        if new_url and head_ok(new_url, head_cache):
            d.setdefault("images", {}).setdefault("hero", {})["url"] = new_url
            if apply_changes:
                save_json(path, d)
                breed_jsons_patched.append(slug)
            log_lines.append(
                f"[breed-hero-fixed] {slug}: {cur or '(none)'} -> {new_url}"
            )
            breed_hero_cache[slug] = new_url
            return new_url
        log_lines.append(
            f"[unfixable] {slug}: own hero dead ({cur}) and Wikipedia API gave no usable image"
        )
        breed_hero_cache[slug] = None
        return None

    roundups = []
    for fn in sorted(os.listdir(DATA)):
        if not fn.endswith(".json"):
            continue
        try:
            d = load_json(DATA / fn)
        except Exception as e:
            log_lines.append(f"[parse-error] {fn}: {e}")
            continue
        if d.get("meta", {}).get("size_category") == "Roundup":
            roundups.append((fn, d))

    modified_roundups = []
    total_card_changes = 0

    for fn, d in roundups:
        sec_key = find_card_section(d.get("sections", {}))
        if not sec_key:
            log_lines.append(f"[no-cards] {fn}")
            continue
        html = d["sections"][sec_key]["html"]
        local_changes = []

        def repl(m):
            cur_url = m.group("url")
            slug = m.group("slug")
            target = resolve_breed_hero(slug)
            if not target:
                return m.group(0)
            target = upgrade_resolution(target)
            if target == cur_url:
                return m.group(0)
            local_changes.append((slug, cur_url, target))
            return (
                m.group(1) + target + m.group(3) + m.group("between")
                + m.group(5) + slug + m.group(7)
            )

        new_html = CARD.sub(repl, html)
        if local_changes:
            d["sections"][sec_key]["html"] = new_html
            modified_roundups.append(fn)
            total_card_changes += len(local_changes)
            for slug, old, new in local_changes:
                log_lines.append(
                    f"[card] {fn} -> {slug}: {old[:80]} => {new[:80]}"
                )
            if apply_changes:
                save_json(DATA / fn, d)

    summary = (
        f"\n=== Summary ===\n"
        f"Roundups scanned:        {len(roundups)}\n"
        f"Roundups changed:        {len(modified_roundups)}\n"
        f"Card thumbs replaced:    {total_card_changes}\n"
        f"Breed JSON heroes fixed: {len(breed_jsons_patched)}\n"
        f"Mode:                    {'APPLY' if apply_changes else 'DRY-RUN'}\n"
    )
    print("\n".join(log_lines))
    print(summary)
    LOG.write_text("\n".join(log_lines) + summary, encoding="utf-8")
    print(f"Log written to: {LOG}")

    if push and apply_changes and modified_roundups:
        slugs = " ".join(Path(fn).stem for fn in modified_roundups)
        cmd = f"echo YES | python3 scripts/generate.py {slugs} --update"
        print(f"\nPushing to Shopify:\n  {cmd}")
        rc = os.system(cmd)
        print(f"generate.py exit code: {rc}")
    elif push and not apply_changes:
        print("\n--push has no effect without --apply (dry-run mode).")


if __name__ == "__main__":
    main()
