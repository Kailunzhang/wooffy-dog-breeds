"""Build the dog breed quiz Shopify page from breed-quiz-data.json.

Reads pages/breed-quiz-template.html, validates the breed data, and writes:
  pages/breed-quiz-FINAL.html    fragment to paste into the Shopify Page body (HTML mode)
  pages/breed-quiz-preview.html  standalone doc with a mock Shopify shell for local testing

Usage:
    py scripts/build_breed_quiz.py                 # uses breed-quiz-data.json
    py scripts/build_breed_quiz.py --fixture       # uses pages/breed-quiz-fixture.json
    py scripts/build_breed_quiz.py --data path.json
"""

import argparse
import datetime as dt
import html
import json
import os
import re
import statistics
import sys
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, "pages")
TEMPLATE = os.path.join(PAGES, "breed-quiz-template.html")
DEFAULT_DATA = os.path.join(ROOT, "breed-quiz-data.json")
FIXTURE_DATA = os.path.join(PAGES, "breed-quiz-fixture.json")
OUT_FINAL = os.path.join(PAGES, "breed-quiz-FINAL.html")
OUT_PREVIEW = os.path.join(PAGES, "breed-quiz-preview.html")

DIMS = ("energy", "apartment", "beginner", "trainability", "kids", "dogs", "small_pets",
        "alone", "shedding", "grooming", "barking", "heat", "cold", "strangers", "watchdog")
FLAGS = ("allergy", "brachy", "drool")
SIZE_BANDS = (("Toy", "under 12 lb", 0, 12), ("Small", "12\u201325 lb", 12, 25),
              ("Medium", "25\u201350 lb", 25, 50), ("Large", "50\u201390 lb", 50, 90),
              ("Giant", "90+ lb", 90, 10_000))
MIN_BREEDS_PER_BUDGET_ROW = 2
SIZE_WARN_BYTES = 250_000
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FAQ_RE = re.compile(r"<!-- WQ-FAQ-START -->(.*?)<!-- WQ-FAQ-END -->", re.S)
FAQ_ITEM_RE = re.compile(r'<div class="wq-faq">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>', re.S)
PLACEHOLDER_RE = re.compile(r"__WQ_[A-Z_]+__")
IMG_BASE = "https://cdn.shopify.com/s/files/1/0554/5253/2790/files/"
BLOG_PREFIX = "/blogs/dog-breeds/"
CHECKLIST_SUFFIX = "-puppy-checklist"


class DataError(ValueError):
    pass


def is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_range(errors: list[str], where: str, v: Any) -> None:
    ok = isinstance(v, list) and len(v) == 2 and all(is_num(x) for x in v) and 0 < v[0] <= v[1]
    if not ok:
        errors.append(f"{where} must be [lo, hi] with 0 < lo <= hi, got {v!r}")


def check_str_list(errors: list[str], where: str, v: Any, lo: int, hi: int) -> None:
    if not isinstance(v, list) or not lo <= len(v) <= hi or not all(isinstance(x, str) and x.strip() for x in v):
        errors.append(f"{where} must be a list of {lo}-{hi} non-empty strings, got {v!r}")


def validate_breed(i: int, b: Any) -> list[str]:
    if not isinstance(b, dict):
        return [f"breeds[{i}] is not an object"]
    w = f"breeds[{i}] ({b.get('s', '?')})"
    required = ("s", "n", "g", "img", "w", "ex", "sc", "f", "cost", "hi", "cv", "url", "cost_url", "akc")
    missing = [k for k in required if k not in b]
    if missing:
        return [f"{w} missing field(s): {', '.join(missing)}"]
    errors: list[str] = []
    if not isinstance(b["s"], str) or not SLUG_RE.match(b["s"]):
        errors.append(f"{w}.s is not a valid slug: {b['s']!r}")
    for k in ("n", "g", "url"):
        if not isinstance(b[k], str) or not b[k].strip():
            errors.append(f"{w}.{k} must be a non-empty string")
    if not isinstance(b["img"], str) or not (b["img"] == "" or b["img"].startswith("https://")):
        errors.append(f"{w}.img must be an https URL or empty, got {b['img']!r}")
    if isinstance(b["url"], str) and not b["url"].startswith("/blogs/"):
        errors.append(f"{w}.url must start with /blogs/, got {b['url']!r}")
    check_range(errors, f"{w}.w", b["w"])
    check_range(errors, f"{w}.ex", b["ex"])
    sc = b["sc"]
    if not isinstance(sc, dict):
        errors.append(f"{w}.sc must be an object")
    else:
        for d in DIMS:
            v = sc.get(d)
            if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 5:
                errors.append(f"{w}.sc.{d} must be an integer 1-5, got {v!r}")
        extra = set(sc) - set(DIMS)
        if extra:
            errors.append(f"{w}.sc has unknown dimension(s): {sorted(extra)}")
    f = b["f"]
    if not isinstance(f, dict) or any(not isinstance(f.get(k), bool) for k in FLAGS):
        errors.append(f"{w}.f must have boolean {', '.join(FLAGS)}, got {f!r}")
    if b["cost"] is not None:
        check_range(errors, f"{w}.cost", b["cost"])
    check_str_list(errors, f"{w}.hi", b["hi"], 1, 3)
    check_str_list(errors, f"{w}.cv", b["cv"], 0, 2)
    if b["cost_url"] is not None and not (isinstance(b["cost_url"], str) and b["cost_url"].startswith("/blogs/")):
        errors.append(f"{w}.cost_url must be null or start with /blogs/, got {b['cost_url']!r}")
    ck = b.get("ck_url")  # optional: puppy-checklist guide URL
    if ck is not None and not (isinstance(ck, str) and ck.startswith(BLOG_PREFIX) and len(ck) > len(BLOG_PREFIX)):
        errors.append(f"{w}.ck_url must be null or start with {BLOG_PREFIX}, got {ck!r}")
    akc = b["akc"]
    if akc is not None and (not isinstance(akc, int) or isinstance(akc, bool) or akc < 1):
        errors.append(f"{w}.akc must be null or a positive integer, got {akc!r}")
    return errors


def validate(data: Any) -> None:
    if not isinstance(data, dict):
        raise DataError("top level must be an object")
    errors: list[str] = []
    try:
        dt.date.fromisoformat(data.get("version"))
    except (TypeError, ValueError):
        errors.append(f"version must be YYYY-MM-DD, got {data.get('version')!r}")
    breeds = data.get("breeds")
    if not isinstance(breeds, list) or not breeds:
        raise DataError("breeds must be a non-empty list")
    if data.get("count") != len(breeds):
        errors.append(f"count={data.get('count')!r} but breeds has {len(breeds)} entries")
    for i, b in enumerate(breeds):
        errors.extend(validate_breed(i, b))
    slugs = [b.get("s") for b in breeds if isinstance(b, dict)]
    dupes = sorted({s for s in slugs if slugs.count(s) > 1})
    if dupes:
        errors.append(f"duplicate slugs: {dupes}")
    if errors:
        raise DataError(f"{len(errors)} problem(s):\n  " + "\n  ".join(errors[:60]))


def fmt_money(n: float) -> str:
    return f"${round(n):,}"


def budget_rows(breeds: list[dict]) -> str:
    """Median first-year cost range per size band, grouping each breed by its midpoint weight."""
    rows = []
    for name, rng, lo, hi in SIZE_BANDS:
        costs = [b["cost"] for b in breeds if b["cost"] and lo <= (b["w"][0] + b["w"][1]) / 2 < hi]
        if len(costs) >= MIN_BREEDS_PER_BUDGET_ROW:
            value = f"{fmt_money(statistics.median(c[0] for c in costs))}&ndash;{fmt_money(statistics.median(c[1] for c in costs))}"
        else:
            value = "Not enough data yet"
        rows.append(f"<tr><td><strong>{name}</strong> ({rng})</td><td>{value}</td><td>{len(costs)}</td></tr>")
    return "".join(rows)


def faq_items(template: str) -> list[tuple[str, str]]:
    block = FAQ_RE.search(template)
    if not block:
        raise SystemExit("template is missing the WQ-FAQ-START/END markers")
    items = [(html.unescape(q).strip(), html.unescape(re.sub(r"<[^>]+>", "", a)).strip())
             for q, a in FAQ_ITEM_RE.findall(block.group(1))]
    if not 4 <= len(items) <= 7:
        raise SystemExit(f"expected 4-7 FAQ items, found {len(items)}")
    return items


def json_for_script(obj: Any) -> str:
    """JSON that is safe to inline in a <script> element (no '</script>' or '<!--' breakouts)."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return (s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
             .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def jsonld(faq: list[tuple[str, str]], count: int) -> str:
    graph = [
        {
            "@type": "WebApplication",
            "name": "Wooffy Dog Breed Quiz",
            "description": (f"Answer 12 quick questions, plus an optional budget question, about your home, schedule and family to see which of {count} "
                            "dog breeds fit you best, with reasons, trade-offs and first-year costs."),
            "applicationCategory": "LifestyleApplication",
            "operatingSystem": "Any",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "publisher": {"@type": "Organization", "name": "Wooffy", "url": "https://thewooffy.com"},
        },
        {
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for q, a in faq],
        },
    ]
    return json_for_script({"@context": "https://schema.org", "@graph": graph})


def pretty_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def standard_checklist_url(slug: str) -> str:
    return f"{BLOG_PREFIX}{slug}{CHECKLIST_SUFFIX}"


def compact(data: dict) -> dict:
    """Smaller embed: scores as arrays in DIMS order, shared CDN prefix stripped, and a ck_url that follows
    the standard /blogs/dog-breeds/<slug>-puppy-checklist pattern (or is null) stored as ck 1/0 (the page
    expands all three; any other ck_url is embedded as-is)."""
    out = []
    for b in data["breeds"]:
        c = dict(b)
        c["sc"] = [b["sc"][d] for d in DIMS]
        if c["img"].startswith(IMG_BASE):
            c["img"] = c["img"][len(IMG_BASE):]
        if "ck_url" in c and c["ck_url"] in (None, standard_checklist_url(b["s"])):
            c["ck"] = 1 if c.pop("ck_url") else 0
        out.append(c)
    return {"version": data["version"], "count": len(out), "dims": list(DIMS), "img_base": IMG_BASE,
            "ck_base": BLOG_PREFIX, "ck_suffix": CHECKLIST_SUFFIX, "breeds": out}


def build_fragment(template: str, data: dict) -> str:
    breeds = data["breeds"]
    embedded = compact(data)
    out = (template
           .replace("__WQ_DATA__", json_for_script(embedded))
           .replace("__WQ_JSONLD__", jsonld(faq_items(template), len(breeds)))
           .replace("__WQ_BUDGET_ROWS__", budget_rows(breeds))
           .replace("__WQ_UPDATED__", pretty_date(data["version"]))
           .replace("__WQ_COUNT__", str(len(breeds))))
    left = sorted(set(PLACEHOLDER_RE.findall(out)))
    if left:
        raise SystemExit(f"unreplaced placeholder(s): {left}")
    for marker in ("// WQ-SCORING-START", "// WQ-SCORING-END", 'id="wq-root"'):
        if out.count(marker) != 1:
            raise SystemExit(f"expected exactly one {marker!r} in the output")
    return out


PREVIEW_SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PREVIEW - Which Dog Breed Is Right for Me? | Wooffy</title>
<style>
/* Mock Shopify theme CSS (Dawn-like) with rules that commonly collide with page embeds. */
html{font-size:62.5%;}
body{margin:0;font-family:"Assistant",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;font-size:1.6rem;line-height:1.8;letter-spacing:0.06rem;color:rgba(18,18,18,0.75);background:#ffffff;}
a{color:#121212;}
button{font-family:inherit;text-transform:uppercase;letter-spacing:0.1rem;background:#121212;color:#ffffff;border:1px solid #121212;padding:0 3rem;min-height:4.5rem;min-width:12rem;}
select,input{font-size:1.6rem;border:1px solid #121212;border-radius:0;height:4.5rem;}
h1,h2,h3{font-family:Georgia,serif;font-weight:400;color:#121212;letter-spacing:0.06rem;}
h1{font-size:4rem;} h2{font-size:3.2rem;} h3{font-size:2.4rem;}
.shop-header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 20px;border-bottom:1px solid #e8e8e8;position:sticky;top:0;background:#ffffff;z-index:5;}
.shop-header .logo{font-weight:800;font-size:2.2rem;color:#121212;text-decoration:none;}
.shop-header nav{display:flex;gap:16px;font-size:1.4rem;flex-wrap:wrap;}
.page-width{max-width:120rem;margin:0 auto;padding:0 1.5rem;}
.main-page-title{margin:3rem 0 2rem;line-height:1.2;}
.rte{word-break:break-word;}
.rte p{margin:0 0 1.5rem;}
.rte h2,.rte h3{margin:3rem 0 1.5rem;}
.rte ul,.rte ol{padding-left:2rem;margin:0 0 1.5rem;list-style:disc;}
.rte li{list-style:inherit;margin-bottom:0.8rem;}
.rte img{height:auto;max-width:100%;border:1px solid rgba(18,18,18,0.1);border-radius:20px;box-shadow:0 4px 10px rgba(0,0,0,0.2);margin:2rem 0;}
.rte a{color:#c2185b;text-underline-offset:0.3rem;text-decoration-thickness:0.1rem;}
.rte table{table-layout:fixed;border-collapse:collapse;border:1px solid #121212;}
.rte td,.rte th{border:1px solid #121212;padding:0.5rem 1rem;}
.shop-footer{margin-top:60px;padding:40px 20px;background:#f3f3f3;font-size:1.4rem;text-align:center;}
@media (min-width:750px){.page-width{padding:0 5rem;}}
</style>
<script>
  /* Preview-only analytics stub: records events so the visual check can confirm them. */
  window.__wqEvents = [];
  window.gtag = function () { window.__wqEvents.push(Array.prototype.slice.call(arguments)); };
</script>
</head>
<body>
<header class="shop-header"><a class="logo" href="#">Wooffy</a><nav><a href="#">Dog Breeds</a><a href="#">Shop</a><a href="#">About</a></nav></header>
<main class="page-width">
<h1 class="main-page-title">Which Dog Breed Is Right for Me? Find Your Best Matches</h1>
<div class="rte">
__FRAGMENT__
</div>
</main>
<footer class="shop-footer">Mock theme footer &middot; local preview only</footer>
</body>
</html>
"""


def write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--data", help="path to breed-quiz data JSON (default: breed-quiz-data.json)")
    src.add_argument("--fixture", action="store_true", help="build from pages/breed-quiz-fixture.json")
    args = parser.parse_args()

    path = FIXTURE_DATA if args.fixture else (args.data or DEFAULT_DATA)
    if not os.path.exists(path):
        hint = "" if args.data or args.fixture else " (use --fixture to build against the test fixture)"
        raise SystemExit(f"data file not found: {path}{hint}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    try:
        validate(data)
    except DataError as e:
        raise SystemExit(f"INVALID DATA in {path}: {e}")

    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()
    fragment = build_fragment(template, data)
    write(OUT_FINAL, fragment)
    write(OUT_PREVIEW, PREVIEW_SHELL.replace("__FRAGMENT__", fragment))

    size = len(fragment.encode("utf-8"))
    print(f"data: {os.path.relpath(path, ROOT)}  version {data['version']}  {len(data['breeds'])} breeds"
          f"{'  [FIXTURE]' if data.get('fixture') else ''}")
    print(f"wrote {os.path.relpath(OUT_FINAL, ROOT)} ({size:,} bytes)")
    print(f"wrote {os.path.relpath(OUT_PREVIEW, ROOT)}")
    if size > SIZE_WARN_BYTES:
        print(f"ERROR: fragment is {size:,} bytes, over the {SIZE_WARN_BYTES:,}-byte budget", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
