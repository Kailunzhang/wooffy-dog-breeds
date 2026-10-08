"""Authority citations on the 172 main breed guides (GEO_PLAN W2.5).

Appends a "Sources & Further Reading" block to the end of each main
guide's health section: the breed's AKC page (UKC for the APBT, the two
parent breeds' AKC pages for designer crosses), up to MAX_CONDITIONS
condition pages matching conditions the health section actually names,
and two general references (OFA CHIC testing requirements, Merck
Veterinary Manual dog-owner section). Same conventions as
add_ymyl_citations.py: dofollow, target=_blank rel=noopener, sentinel
comment for idempotency.

Two-step, because this repo's cloud container cannot reach the web:

  1. --verify   (run on a machine with internet)
     Fetches every candidate URL, records HTTP status and final URL in
     geo/citation-urls.json. Re-run any time; --force re-checks all.
  2. --apply
     Inserts ONLY URLs whose cached check is status 200 and whose final
     URL still contains the expected token (so a redirect to a search or
     home page never passes). Dry run without --apply.

Usage:
    python3 scripts/geo_breed_citations.py --verify            # on your machine
    python3 scripts/geo_breed_citations.py --report            # unverified / failed URLs
    python3 scripts/geo_breed_citations.py                     # dry run
    python3 scripts/geo_breed_citations.py --apply
    echo YES | python3 scripts/generate.py <slugs> --update --touch-updated
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BD = os.path.join(ROOT, "breed-data")
CACHE = os.path.join(ROOT, "geo", "citation-urls.json")
SENTINEL = "<!-- geo-breed-citations v1 -->"
MAX_CONDITIONS = 3
UA = "Mozilla/5.0 (compatible; WooffyCitationCheck/1.0; +https://thewooffy.com)"

AKC = "https://www.akc.org/dog-breeds/{slug}/"
# our slug -> AKC slug, where they differ
AKC_SLUG = {
    "standard-poodle": "poodle-standard",
    "miniature-poodle": "poodle-miniature",
    "toy-poodle": "poodle-toy",
    "saint-bernard": "st-bernard",
}
# designer crosses -> AKC slugs of the two parent breeds
PARENTS = {
    "goldendoodle": ("golden-retriever", "poodle-standard"),
    "mini-goldendoodle": ("golden-retriever", "poodle-miniature"),
    "labradoodle": ("labrador-retriever", "poodle-standard"),
    "bernedoodle": ("bernese-mountain-dog", "poodle-standard"),
    "cavapoo": ("cavalier-king-charles-spaniel", "poodle-miniature"),
    "cockapoo": ("cocker-spaniel", "poodle-miniature"),
    "maltipoo": ("maltese", "poodle-toy"),
    "sheepadoodle": ("old-english-sheepdog", "poodle-standard"),
    "aussiedoodle": ("australian-shepherd", "poodle-standard"),
}
UKC = {"american-pit-bull-terrier": ("https://www.ukcdogs.com/american-pit-bull-terrier", "pit-bull")}
NO_BREED_PAGE = {"mixed-breed-dogs"}

# (keywords in the health text) -> (url, link name, description, token the final URL must contain)
CONDITIONS = [
    (("hip dysplasia",), "https://www.akc.org/expert-advice/health/hip-dysplasia-in-dogs/",
     "AKC: Hip Dysplasia in Dogs", "symptoms, diagnosis and treatment", "hip-dysplasia"),
    (("elbow dysplasia",), "https://www.akc.org/expert-advice/health/elbow-dysplasia-in-dogs/",
     "AKC: Elbow Dysplasia in Dogs", "causes and management", "elbow"),
    (("progressive retinal atrophy", " pra"), "https://www.akc.org/expert-advice/health/progressive-retinal-atrophy/",
     "AKC: Progressive Retinal Atrophy", "inherited eye disease and genetic testing", "retinal"),
    (("bloat", "gastric dilatation"), "https://www.akc.org/expert-advice/health/bloat-in-dogs/",
     "AKC: Bloat (GDV) in Dogs", "warning signs and prevention", "bloat"),
    (("hypothyroid",), "https://www.akc.org/expert-advice/health/hypothyroidism-in-dogs/",
     "AKC: Hypothyroidism in Dogs", "symptoms and treatment", "hypothyroid"),
    (("patellar luxation", "luxating patella"), "https://www.akc.org/expert-advice/health/luxating-patella-dog/",
     "AKC: Luxating Patella in Dogs", "grades, surgery and outlook", "patella"),
    (("epilep",), "https://www.akc.org/expert-advice/health/epilepsy-in-dogs/",
     "AKC: Epilepsy in Dogs", "seizure types and management", "epilep"),
    (("brachycephalic",), "https://vcahospitals.com/know-your-pet/brachycephalic-airway-syndrome-in-dogs",
     "VCA: Brachycephalic Airway Syndrome", "airway risks in flat-faced breeds", "brachycephalic"),
    (("dilated cardiomyopathy", " dcm"), "https://www.akc.org/expert-advice/nutrition/dilated-cardiomyopathy-dogs-update/",
     "AKC: Dilated Cardiomyopathy (DCM) in Dogs", "predisposed breeds, diet link and screening", "cardiomyopathy"),
    (("von willebrand",), "https://vcahospitals.com/know-your-pet/von-willebrands-disease-in-dogs",
     "VCA: Von Willebrand's Disease in Dogs", "inherited bleeding disorder and DNA testing", "willebrand"),
    (("ivdd", "intervertebral"), "https://www.akc.org/expert-advice/health/intervertebral-disk-disease-dogs/",
     "AKC: Intervertebral Disc Disease (IVDD)", "back injury risk and treatment", "intervertebral"),
    (("degenerative myelopathy",), "https://www.akc.org/expert-advice/health/degenerative-myelopathy-in-dogs/",
     "AKC: Degenerative Myelopathy", "progressive spinal disease", "myelopathy"),
    (("cataract",), "https://www.akc.org/expert-advice/health/cataracts-in-dogs-what-to-know/",
     "AKC: Cataracts in Dogs", "signs and surgery", "cataract"),
    (("ear infection",), "https://www.akc.org/expert-advice/health/dog-ear-infections/",
     "AKC: Ear Infections in Dogs", "causes, treatment and prevention", "ear-infection"),
    (("osteosarcoma",), "https://www.akc.org/expert-advice/health/osteosarcoma-in-dogs/",
     "AKC: Osteosarcoma in Dogs", "bone cancer in large breeds", "osteosarcoma"),
    (("deaf",), "https://www.akc.org/expert-advice/health/deafness-in-dogs/",
     "AKC: Deafness in Dogs", "congenital deafness and BAER testing", "deaf"),
    (("mitral valve",), "https://www.akc.org/expert-advice/health/valvular-disease-in-small-breed-dogs/",
     "AKC: Valvular (Mitral) Disease in Small-Breed Dogs", "heart murmurs and heart failure risk", "valvular"),
    (("addison",), "https://www.akc.org/expert-advice/health/addisons-disease-in-dogs/",
     "AKC: Addison's Disease in Dogs", "symptoms and lifelong treatment", "addison"),
    (("allerg",), "https://www.akc.org/expert-advice/health/dog-allergies-symptoms-treatment/",
     "AKC: Dog Allergies", "symptoms and treatment", "allerg"),
]
GENERAL = [
    ("https://ofa.org/chic-programs/browse-by-breed/", "OFA CHIC",
     "breed-specific health tests a responsible breeder should show", "chic"),
    ("https://www.merckvetmanual.com/dog-owners", "Merck Veterinary Manual",
     "dog owner reference for the conditions above", "dog-owners"),
]


# ---------------------------------------------------------------- data
def load(slug):
    with open(os.path.join(BD, f"{slug}.json"), encoding="utf-8") as f:
        return json.load(f)


def save(slug, data):
    with open(os.path.join(BD, f"{slug}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def is_main(slug, data):
    m = data.get("meta") or {}
    sc = (m.get("size_category") or "").lower()
    if "body_html" in data or "-vs-" in slug or sc in ("guide", "roundup", "comparison"):
        return False
    return not slug.endswith(("-grooming-guide", "-first-year-costs", "-puppy-checklist"))


def main_slugs():
    out = []
    for p in sorted(glob.glob(os.path.join(BD, "*.json"))):
        slug = os.path.splitext(os.path.basename(p))[0]
        if is_main(slug, load(slug)):
            out.append(slug)
    return out


def load_cache():
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(cache.items())), f, indent=1, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------- candidates
def breed_sources(slug, name):
    """[(url, link name, description, token)] for the breed page(s)."""
    if slug in NO_BREED_PAGE:
        return []
    if slug in UKC:
        url, token = UKC[slug]
        return [(url, f"UKC: {name}", "official breed standard", token)]
    if slug in PARENTS:
        out = []
        for p in PARENTS[slug]:
            pretty = p.replace("poodle-", "poodle (") .replace("-", " ").title()
            pretty = pretty + ")" if "Poodle (" in pretty else pretty
            out.append((AKC.format(slug=p), f"AKC: {pretty}", "parent breed profile and health", p))
        return out
    a = AKC_SLUG.get(slug, slug)
    return [(AKC.format(slug=a), f"AKC: {name}", "official breed standard, history and health", a)]


def condition_sources(health_html):
    text = " " + re.sub(r"<[^>]+>", " ", health_html or "").lower() + " "
    out = []
    for kws, url, link, desc, token in CONDITIONS:
        if any(k in text for k in kws):
            out.append((url, link, desc, token))
        if len(out) >= MAX_CONDITIONS:
            break
    return out


def candidates(slug, data):
    name = (data.get("meta") or {}).get("name", slug)
    health = (data.get("sections") or {}).get("health") or {}
    return breed_sources(slug, name) + condition_sources(health.get("html", "")) + GENERAL


# ---------------------------------------------------------------- verify
def check(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read(2048)
            return {"status": r.status, "final_url": r.geturl()}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "final_url": e.geturl() or url}
    except Exception as e:  # DNS, TLS, timeout
        return {"status": 0, "final_url": url, "error": str(e)[:120]}


def verified(cache, url, token):
    row = cache.get(url)
    return bool(row) and row.get("status") == 200 and token.lower() in (row.get("final_url") or "").lower()


# ---------------------------------------------------------------- render
def li(url, name, desc):
    return (f'<li style="margin-bottom:8px;"><a href="{url}" target="_blank" rel="noopener" '
            f'style="color:#1a1a1a;font-weight:600;text-decoration:underline;text-underline-offset:3px;">'
            f'{name}</a> — {desc}</li>')


def build_block(sources):
    items = "".join(li(u, n, d) for u, n, d, _ in sources)
    return (f'{SENTINEL}<div style="margin-top:32px;padding-top:20px;border-top:1px solid #e8e8e8;">'
            f'<h3 style="font-size:1.1em;font-weight:700;color:#1a1a1a;margin:0 0 12px 0;">Sources &amp; Further Reading</h3>'
            f'<ul style="font-size:0.9em;line-height:1.8;color:#6b7177;padding-left:20px;margin:0;">{items}</ul></div>')


# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--verify", action="store_true", help="fetch every candidate URL and cache the result")
    ap.add_argument("--force", action="store_true", help="with --verify: re-check cached URLs too")
    ap.add_argument("--report", action="store_true", help="list URLs that are unchecked or failed")
    ap.add_argument("--apply", action="store_true", help="write the citation blocks into the JSON files")
    ap.add_argument("--slug", action="append")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    slugs = args.slug or main_slugs()
    cache = load_cache()
    per_slug = {s: candidates(s, load(s)) for s in slugs}
    all_urls = {}
    for srcs in per_slug.values():
        for url, _, _, token in srcs:
            all_urls[url] = token

    if args.verify:
        todo = [u for u in all_urls if args.force or u not in cache]
        print(f"checking {len(todo)} URLs ({len(all_urls) - len(todo)} cached)")
        for i, url in enumerate(todo, 1):
            row = check(url)
            row["checked"] = date.today().isoformat()
            cache[url] = row
            ok = verified(cache, url, all_urls[url])
            print(f"  [{i}/{len(todo)}] {'OK ' if ok else 'BAD'} {row['status']:>3} {url}"
                  + ("" if ok or row["status"] != 200 else f"  -> {row['final_url']}"))
            save_cache(cache)
            time.sleep(0.5)
        good = sum(1 for u, t in all_urls.items() if verified(cache, u, t))
        print(f"\n{good}/{len(all_urls)} candidate URLs verified; cache: geo/citation-urls.json")
        return 0

    if args.report:
        bad = [(u, cache.get(u)) for u, t in all_urls.items() if not verified(cache, u, t)]
        for u, row in bad:
            print(f"{(row or {}).get('status', '-')!s:>4}  {u}" + (f"  -> {row['final_url']}" if row and row.get("final_url") != u else ""))
        print(f"\n{len(bad)}/{len(all_urls)} candidate URLs not verified")
        return 0

    done = skipped = thin = 0
    for slug in slugs:
        data = load(slug)
        health = (data.get("sections") or {}).get("health")
        if not health or not health.get("html"):
            skipped += 1
            continue
        if SENTINEL in health["html"]:
            skipped += 1
            continue
        srcs = [s for s in per_slug[slug] if verified(cache, s[0], s[3])]
        if len(srcs) < 2:
            thin += 1
            if not args.quiet:
                print(f"SKIP {slug}: only {len(srcs)} verified source(s) of {len(per_slug[slug])} candidates")
            continue
        if not args.quiet:
            print(f"{slug}: " + "; ".join(n for _, n, _, _ in srcs))
        if args.apply:
            health["html"] = health["html"].rstrip() + build_block(srcs)
            save(slug, data)
        done += 1
    verb = "wrote" if args.apply else "would write"
    print(f"\n{verb} citations on {done} guides; already done/no health section {skipped}; "
          f"too few verified sources {thin}")
    if thin and not cache:
        print("no URL checks cached yet: run --verify on a machine with internet access first")
    elif thin:
        print("run --report to see which URLs failed verification")
    return 0


if __name__ == "__main__":
    sys.exit(main())
