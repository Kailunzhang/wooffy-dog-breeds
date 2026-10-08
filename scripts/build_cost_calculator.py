"""Build the first-year dog cost calculator Shopify page from calculator-data.json.

Reads pages/cost-calculator-template.html, validates the breed cost data, and writes:
  pages/cost-calculator-FINAL.html    fragment to paste into the Shopify Page body (HTML mode)
  pages/cost-calculator-preview.html  standalone doc with a mock Dawn shell for local testing

Read-only inputs: calculator-data.json (the numbers) and costs-dataset.json (only the "est"
flags, which mark items filled in from size-group medians). Neither file is modified.

Usage:
    py scripts/build_cost_calculator.py
"""

import html
import json
import os
import re
import statistics
import sys
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, "pages")
TEMPLATE = os.path.join(PAGES, "cost-calculator-template.html")
DATA_PATH = os.path.join(ROOT, "calculator-data.json")
DATASET_PATH = os.path.join(ROOT, "costs-dataset.json")
OUT_FINAL = os.path.join(PAGES, "cost-calculator-FINAL.html")
OUT_PREVIEW = os.path.join(PAGES, "cost-calculator-preview.html")

PAIR_FIELDS = ("p", "v", "s", "f", "i", "g", "u", "t", "a")
# costs-dataset.json "est" names -> calculator-data.json short keys
EST_KEYS = {"puppy": "p", "vet_year1": "v", "spay_neuter": "s", "food_monthly": "f",
            "insurance_monthly": "i", "grooming_annual": "g", "setup_onetime": "u",
            "total_year1": "t", "annual_ongoing": "a"}
SHOWN_EST = {"v", "s", "f", "i", "g", "u", "a"}  # "t" is never displayed
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDER_RE = re.compile(r"__CALC_[A-Z_]+__")
FAQ_RE = re.compile(r"<!-- WF-FAQ-START -->(.*?)<!-- WF-FAQ-END -->", re.S)
FAQ_ITEM_RE = re.compile(r'<div class="wf-faq">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>', re.S)
RESCUE_SUSPECT_HIGH = 1000  # an adoption fee above this usually means a retired breeder dog, not a rescue
SIZE_WARN_BYTES = 120_000
COMPARE = ("chihuahua", "great-dane")
DEFAULT_BREED = "golden-retriever"


class DataError(ValueError):
    pass


def is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_pair(v: Any) -> bool:
    return isinstance(v, list) and len(v) == 2 and all(is_num(x) for x in v) and 0 <= v[0] <= v[1]


def validate(data: Any) -> list[str]:
    """Raise DataError on anything that would break the page; return warnings for rescue fees."""
    if not isinstance(data, dict) or not data:
        raise DataError("top level must be a non-empty object of slug -> breed")
    errors: list[str] = []
    warnings: list[str] = []
    for slug, b in data.items():
        if not SLUG_RE.match(slug):
            errors.append(f"{slug!r} is not a valid slug")
        if not isinstance(b, dict):
            errors.append(f"{slug}: not an object")
            continue
        if not isinstance(b.get("n"), str) or not b["n"].strip():
            errors.append(f"{slug}.n must be a non-empty string")
        for k in PAIR_FIELDS:
            if not is_pair(b.get(k)):
                errors.append(f"{slug}.{k} must be [low, high] numbers with 0 <= low <= high, got {b.get(k)!r}")
        for x in b.get("x") or []:
            if not (isinstance(x, list) and len(x) == 3 and isinstance(x[0], str) and x[0].strip()
                    and is_pair(x[1:])):
                errors.append(f"{slug}.x entries must be [label, low, high], got {x!r}")
        if b.get("sv") and b.get("s") != [0, 0]:
            errors.append(f"{slug}: spay is in the vet line (sv) but s is {b.get('s')!r}, not [0, 0]")
        r = b.get("r")
        if r is None:
            continue
        if not is_pair(r) or r[1] <= 0:
            warnings.append(f"{slug}.r = {r!r} is unusable; the page shows the general US rescue range instead")
        elif r[1] > RESCUE_SUSPECT_HIGH:
            warnings.append(f"{slug}.r = {r!r} has a high end above ${RESCUE_SUSPECT_HIGH:,}; recheck the guide")
    for s in (DEFAULT_BREED,) + COMPARE:
        if s not in data:
            errors.append(f"required breed {s!r} is missing")
    if errors:
        raise DataError(f"{len(errors)} problem(s):\n  " + "\n  ".join(errors[:60]))
    return warnings


def load_est_flags(path: str) -> dict[str, list[str]]:
    if not os.path.exists(path):
        print(f"WARNING: {os.path.relpath(path, ROOT)} not found; '(estimate)' labels will not show", file=sys.stderr)
        return {}
    with open(path, encoding="utf-8") as f:
        dataset = json.load(f)
    out: dict[str, list[str]] = {}
    for slug, rec in dataset.items():
        keys = sorted({EST_KEYS[e] for e in (rec.get("est") or []) if EST_KEYS.get(e) in SHOWN_EST})
        if keys:
            out[slug] = keys
    return out


def embed_data(data: dict, est: dict[str, list[str]]) -> dict:
    """Page data: drop the unused stated total, null out unusable rescue fees, add estimate flags."""
    out = {}
    for slug, b in data.items():
        c = {k: b[k] for k in ("n",) + PAIR_FIELDS if k != "t"}
        r = b.get("r")
        c["r"] = r if is_pair(r) and r[1] > 0 else None
        if est.get(slug):
            c["e"] = est[slug]
        if b.get("sv"):
            c["sv"] = 1  # spay/neuter priced inside the guide's vet line
        if b.get("x"):
            c["x"] = b["x"]  # guide items with no calculator row, listed in a note
        out[slug] = c
    return out


def default_total(b: dict) -> tuple[float, float]:
    """Mirror of compute() in the template at default settings (suburb, breeder, insurance, pro grooming)."""
    lo = b["p"][0] + b["v"][0] + b["s"][0] + b["f"][0] * 12 + b["i"][0] * 12 + b["g"][0] + b["u"][0]
    hi = b["p"][1] + b["v"][1] + b["s"][1] + b["f"][1] * 12 + b["i"][1] * 12 + b["g"][1] + b["u"][1]
    return lo, hi


def money(n: float) -> str:
    return f"${round(n):,}"


def money_range(lo: float, hi: float) -> str:
    return f"{money(lo)}\u2013{money(hi)}"


def stat_values(data: dict) -> dict[str, str]:
    totals = {s: default_total(b) for s, b in data.items()}
    lo_slug = min(totals, key=lambda s: (totals[s][0], totals[s][1]))
    hi_slug = max(totals, key=lambda s: (totals[s][1], totals[s][0]))
    med = statistics.median
    breeds = list(data.values())
    ins_lo = statistics.mean(b["i"][0] for b in breeds)
    ins_hi = statistics.mean(b["i"][1] for b in breeds)
    return {
        "__CALC_COUNT__": str(len(data)),
        "__CALC_DANE__": money_range(*totals[COMPARE[1]]),
        "__CALC_MIN_NAME__": html.escape(data[lo_slug]["n"]),
        "__CALC_MIN__": money_range(*totals[lo_slug]),
        "__CALC_MAX_NAME__": html.escape(data[hi_slug]["n"]),
        "__CALC_MAX__": money_range(*totals[hi_slug]),
        "__CALC_PUPPY_MED__": money_range(med(b["p"][0] for b in breeds), med(b["p"][1] for b in breeds)),
        "__CALC_INS_AVG__": money_range(ins_lo, ins_hi),
        "__CALC_INS_YEAR__": money_range(round(ins_lo * 12, -1), round(ins_hi * 12, -1)),
        "__CALC_ONGOING_MED__": money_range(med(b["a"][0] for b in breeds), med(b["a"][1] for b in breeds)),
    }


def json_for_script(obj: Any) -> str:
    """JSON that is safe to inline in a <script> element (no '</script>' or '<!--' breakouts)."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return (s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
             .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def faq_items(fragment: str) -> list[tuple[str, str]]:
    block = FAQ_RE.search(fragment)
    if not block:
        raise SystemExit("template is missing the WF-FAQ-START/END markers")
    items = [(html.unescape(re.sub(r"<[^>]+>", "", q)).strip(), html.unescape(re.sub(r"<[^>]+>", "", a)).strip())
             for q, a in FAQ_ITEM_RE.findall(block.group(1))]
    if not 3 <= len(items) <= 5:
        raise SystemExit(f"expected 3-5 FAQ items, found {len(items)}")
    return items


def jsonld(faq: list[tuple[str, str]], count: int) -> str:
    graph = [
        {
            "@type": "WebApplication",
            "name": "Wooffy First-Year Dog Cost Calculator",
            "description": (f"Estimate a dog's first-year costs for {count} breeds and doodle mixes: puppy or "
                            "adoption fee, vet care, spay/neuter, food, insurance, grooming and setup."),
            "url": "https://thewooffy.com/pages/dog-cost-calculator",
            "applicationCategory": "FinanceApplication",
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


def build_fragment(template: str, data: dict, est: dict[str, list[str]]) -> str:
    if template.count("__CALC_DATA__") != 1 or template.count("__CALC_JSONLD__") != 1:
        raise SystemExit("template must contain __CALC_DATA__ and __CALC_JSONLD__ exactly once")
    out = template
    for key, value in stat_values(data).items():
        out = out.replace(key, value)
    out = out.replace("__CALC_JSONLD__", jsonld(faq_items(out), len(data)))
    out = out.replace("__CALC_DATA__", json_for_script(embed_data(data, est)))
    left = sorted(set(PLACEHOLDER_RE.findall(out)))
    if left:
        raise SystemExit(f"unreplaced placeholder(s): {left}")
    if out.count('id="wf-calc"') != 1:
        raise SystemExit("expected exactly one #wf-calc root in the output")
    return out


PREVIEW_SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PREVIEW - First-Year Dog Cost Calculator | Wooffy</title>
<style>
/* Mock Dawn theme CSS with the rules that most often collide with page embeds. */
html{font-size:62.5%;}
body{margin:0;font-family:"Assistant",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;font-size:1.6rem;line-height:1.8;letter-spacing:0.06rem;color:rgba(18,18,18,0.75);background:#ffffff;}
a{color:#121212;}
button{font-family:inherit;text-transform:uppercase;letter-spacing:0.1rem;background:#121212;color:#ffffff;border:1px solid #121212;padding:0 3rem;min-height:4.5rem;min-width:12rem;box-shadow:0 0 0 .1rem #121212;}
button:after{content:"";position:absolute;inset:0;box-shadow:0 0 0 .2rem rgba(18,18,18,.5);}
select,input{font-size:1.6rem;border:1px solid #121212;border-radius:0;height:4.5rem;padding:0 1.5rem;}
h1,h2,h3{font-family:Georgia,serif;font-weight:400;color:#121212;letter-spacing:0.06rem;}
h1{font-size:4rem;} h2{font-size:3.2rem;} h3{font-size:2.4rem;}
*:focus-visible{outline:.2rem solid rgba(18,18,18,.5);outline-offset:.3rem;box-shadow:0 0 0 .3rem #fff,0 0 .5rem .4rem rgba(18,18,18,.3);}
.shop-header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 20px;border-bottom:1px solid #e8e8e8;background:#ffffff;}
.shop-header .logo{font-weight:800;font-size:2.2rem;color:#121212;text-decoration:none;}
.shop-header nav{display:flex;gap:16px;font-size:1.4rem;flex-wrap:wrap;}
.page-width{max-width:120rem;margin:0 auto;padding:0 1.5rem;}
.main-page-title{margin:3rem 0 2rem;line-height:1.2;}
.rte{word-break:break-word;}
.rte:after{clear:both;content:"";display:block;}
.rte>p:first-child{margin-top:0;}
.rte p{margin:0 0 1.5rem;}
.rte h2,.rte h3{margin:3rem 0 1.5rem;}
.rte ul,.rte ol{padding-left:2rem;margin:0 0 1.5rem;list-style:disc;}
.rte li{list-style:inherit;margin-bottom:0.8rem;}
.rte li:last-child{margin-bottom:0;}
.rte a{color:#c2185b;text-underline-offset:0.3rem;text-decoration-thickness:0.1rem;transition:text-decoration-thickness .1s ease;}
.rte a:hover{color:#121212;text-decoration-thickness:0.2rem;}
.rte table{table-layout:fixed;border-collapse:collapse;border:1px solid #121212;}
.rte img{height:auto;max-width:100%;border-radius:20px;}
.shop-footer{margin-top:60px;padding:40px 20px;background:#f3f3f3;font-size:1.4rem;text-align:center;}
@media (min-width:750px){.page-width{padding:0 5rem;}}
@media (min-width:990px){.page-width--narrow{max-width:72.6rem;padding:0;}}
</style>
<script>
  /* Preview-only analytics stubs: record events so the visual check can confirm them. */
  window.__calcEvents = [];
  window.gtag = function () { window.__calcEvents.push(['gtag'].concat(Array.prototype.slice.call(arguments))); };
  window.Shopify = { analytics: { publish: function (n, p) { window.__calcEvents.push(['shopify', n, p]); } } };
</script>
</head>
<body>
<header class="shop-header"><a class="logo" href="#">Wooffy</a><nav><a href="#">Dog Breeds</a><a href="#">Shop</a><a href="#">About</a></nav></header>
<main class="page-width page-width--narrow">
<h1 class="main-page-title">First-Year Dog Cost Calculator</h1>
<div class="rte scroll-trigger animate--slide-in">
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
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    try:
        warnings = validate(data)
    except DataError as e:
        raise SystemExit(f"INVALID DATA in {os.path.relpath(DATA_PATH, ROOT)}: {e}")
    est = load_est_flags(DATASET_PATH)

    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()
    fragment = build_fragment(template, data, est)
    write(OUT_FINAL, fragment)
    write(OUT_PREVIEW, PREVIEW_SHELL.replace("__FRAGMENT__", fragment))

    size = len(fragment.encode("utf-8"))
    flagged = sum(1 for s in data if est.get(s))
    print(f"data: {len(data)} breeds, {flagged} with '(estimate)' items")
    for w in warnings:
        print(f"WARNING: {w}")
    print(f"wrote {os.path.relpath(OUT_FINAL, ROOT)} ({size:,} bytes)")
    print(f"wrote {os.path.relpath(OUT_PREVIEW, ROOT)} ({os.path.getsize(OUT_PREVIEW):,} bytes)")
    if size > SIZE_WARN_BYTES:
        print(f"ERROR: fragment is {size:,} bytes, over the {SIZE_WARN_BYTES:,}-byte budget", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
