"""Insert labeled Amazon affiliate links where an article already recommends the item.

Placement rules (owner-approved, 2026-09-29):
  - Only grooming guides, puppy checklists, first-year cost pages, plus the
    explicit `extra_slugs` listed per product in amazon-catalog.json.
  - A product is placed only if one of its `anchors` appears in the article and
    none of its `exclude_if` patterns do; size variants pick the band that
    contains the breed's mid-point adult weight.
  - At most MAX_PER_PAGE products per page, one per product type.
  - No crates (none are in the catalog). No prices, ratings or Amazon images.
  - Every changed page gets one disclosure line at the top.
  - Links are full product URLs (amazon.com/dp/ASIN) carrying the tracking ID for
    the page type from amazon-catalog.json meta.tags_by_kind (2026-10-08), so the
    Associates "Tracking ID" report attributes sales to grooming / checklist / costs.

Everything inserted is wrapped in <!-- WOOFFY_AMZ_v1 --> ... <!-- /WOOFFY_AMZ_v1 -->
so --remove restores the original HTML exactly. Dry-run by default.

Run:
    python3 scripts/inject_amazon_links.py                  # dry-run, writes plan
    python3 scripts/inject_amazon_links.py --apply          # write JSONs
    python3 scripts/inject_amazon_links.py --remove --apply # strip all blocks
    echo YES | python3 scripts/generate.py <changed-slugs> --update
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "breed-data")
CATALOG = os.path.join(ROOT, "amazon-catalog.json")

MARK = "<!-- WOOFFY_AMZ_v1 -->"
END = "<!-- /WOOFFY_AMZ_v1 -->"
BLOCK_RE = re.compile(re.escape(MARK) + r".*?" + re.escape(END), re.DOTALL)
MAX_PER_PAGE = {"grooming": 3, "checklist": 4, "costs": 3, "extra": 3}
STAGES = {"checklist": {"puppy", "any"}, "grooming": {"adult", "any"},
          "costs": {"any", "puppy"}, "extra": {"adult", "any", "puppy", "senior"}}
DISCLOSURE = (f'{MARK}<p class="wfy-aff-note" style="font-size:13px;color:#6b6b6b;margin:0 0 16px;">'
              "<em>This guide contains affiliate links. As an Amazon Associate, Wooffy earns "
              f"from qualifying purchases.</em></p>{END}")
TYPE_SUFFIX = {"-grooming-guide": "grooming", "-puppy-checklist": "checklist",
               "-first-year-costs": "costs"}


def plain(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def page_kind(slug: str) -> str | None:
    for suf, kind in TYPE_SUFFIX.items():
        if slug.endswith(suf):
            return kind
    return None


def breed_weights() -> dict[str, tuple[float, float]]:
    out = {}
    for f in glob.glob(os.path.join(DATA_DIR, "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        w = ((d.get("stats") or {}).get("weight") or {}).get("value") or ""
        nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", w.replace(",", ""))]
        if nums:
            out[os.path.basename(f)[:-5]] = (min(nums), max(nums))
    return out


def html_fields(d: dict) -> list[tuple[list, str]]:
    """(path, html) for every editable HTML field, in reading order."""
    fields = []
    secs = d.get("sections")
    if isinstance(secs, dict):
        for k, v in secs.items():
            if isinstance(v, dict) and isinstance(v.get("html"), str):
                fields.append((["sections", k, "html"], v["html"]))
    if isinstance(d.get("body_html"), str):
        fields.append((["body_html"], d["body_html"]))
    return fields


def set_path(d: dict, path: list, value: str) -> None:
    node = d
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value


# One product per family per page; families rotate between equivalent picks.
FAMILY = {"leash_heavy_duty": "leash", "leash_standard": "leash", "leash_hands_free": "leash",
          "flea_tick_collar": "flea_tick", "flea_tick_topical": "flea_tick"}
ROTATE = {"enzymatic_cleaner", "fish_oil", "dry_food"}


class Rules:
    """Placement rules shipped inside amazon-catalog.json (meta / coat_map / alternatives)."""

    def __init__(self, catalog: dict, coats: dict[str, str]):
        meta = catalog.get("meta") or {}
        self.contain_types = set(meta.get("contain_types") or [])
        self.store_tag = meta.get("store_tag") or "wooffy-20"
        self.tags = dict(meta.get("tags_by_kind") or {})
        self.multi_size = set(meta.get("multi_size_breeds") or [])
        cmap = catalog.get("coat_map") or {}
        self.coat = {slug: cmap.get(cat) for slug, cat in coats.items()}
        self.rake_first: set[str] = set()
        for alt in catalog.get("alternatives") or []:
            if alt.get("type") == "brush_order":
                self.rake_first |= set(alt.get("slugs") or [])


def fits(prod: dict, kind: str, breed: str | None, weights, rules: Rules) -> bool:
    fit = prod.get("fit") or {}
    if fit.get("life_stage", "any") not in STAGES[kind]:
        return False
    coats = fit.get("coat") or ["any"]
    if breed and "any" not in coats and rules.coat.get(breed) and rules.coat[breed] not in coats:
        return False
    lo, hi = fit.get("wmin"), fit.get("wmax")
    if not weights or (lo is None and hi is None):
        return True
    if prod["type"] in rules.contain_types:
        if breed in rules.multi_size:
            return False
        return (lo is None or weights[0] >= lo) and (hi is None or weights[1] <= hi)
    mid = sum(weights) / 2
    return (lo is None or mid >= lo) and (hi is None or mid <= hi)


def stable_index(key: str, n: int) -> int:
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % n


def candidates(slug: str, kind: str, text: str, catalog: list[dict], breed, weights,
               rules: Rules) -> list[dict]:
    out = []
    for p in catalog:
        if p.get("skip") or slug in (p.get("exclude_slugs") or []):
            continue
        if kind == "extra":
            if slug not in (p.get("extra_slugs") or []):
                continue
        elif kind not in (p.get("page_types") or []):
            continue
        if not fits(p, kind, breed, weights, rules):
            continue
        # exclude_if is written for breed pages; hand-picked pages were reviewed by hand
        if kind != "extra" and any(re.search(x, text, re.I) for x in p.get("exclude_if") or []):
            continue
        hit = next((a for a in p.get("anchors") or [] if re.search(a, text, re.I)), None)
        if hit is None:
            continue
        prio = (p.get("extra_slug_priority") or {}).get(slug, p.get("priority", 3))
        out.append({**p, "_anchor": hit, "_prio": prio})
    if slug in rules.rake_first and any(p["type"] == "undercoat_rake" for p in out):
        out = [p for p in out if p["type"] != "slicker_brush"]
    by_family: dict[str, list[dict]] = {}
    for p in out:
        by_family.setdefault(FAMILY.get(p["type"], p["type"]), []).append(p)
    families = []
    for fam, group in by_family.items():
        group.sort(key=lambda p: (p["_prio"], p["asin"]))
        if fam in ROTATE:
            best = [p for p in group if p["_prio"] == group[0]["_prio"]] if fam == "dry_food" else group
            first = best[stable_index(slug + fam, len(best))]
            group = [first] + [p for p in group if p is not first]
        families.append(group)
    families.sort(key=lambda g: (g[0]["_prio"], g[0]["asin"]))
    return families  # each family: options in preference order (fallbacks after the first)


def product_url(p: dict, kind: str, rules: "Rules") -> str:
    """Full product URL with the page-type tracking ID; amzn.to short link as fallback."""
    if not p.get("asin"):
        return p["short"]
    return f'https://www.amazon.com/dp/{p["asin"]}/?tag={rules.tags.get(kind, rules.store_tag)}'


def snippet(p: dict, coat: str | None, kind: str, rules: "Rules") -> str:
    blurb = (p.get("blurb_by_coat") or {}).get(coat or "", p["blurb"]).strip()
    cav = (p.get("caveat_by_kind") or {}).get(kind, p.get("caveat") or "").strip()
    caveat = f" {html.escape(cav)}" if cav else ""
    return (f'{MARK}<br><span class="wfy-aff">One option: <a href="{product_url(p, kind, rules)}" '
            f'rel="sponsored nofollow noopener" target="_blank">{html.escape(p["name"])} on Amazon</a>. '
            f'{html.escape(blurb)}{caveat}</span>{END}')


# Element-level rejects (2026-09-29 placement verification, rules R03/R04/R12).
GLOBAL_ELEMENT_EXCLUDE = [r"^\W*(👍|⚠)"]
TIMELINE_RE = re.compile(
    r"^\W*months?\s*(\d|one|two|three|four|five|six|seven|eight|nine|ten)\b"
    r"|\bmonths?\s+(1|one)\s*(through|to|–|-)\s*(3|three)\b|\bfirst (three|3) months\b"
    r"|^\W*by month\b|\binitial (setup|supplies)\b", re.I)
ABBREV_RE = re.compile(r"\b(e\.g|i\.e|vs|approx|etc|lb|oz|in|ft)\.", re.I)
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])[\"”’)]?\s+(?=[A-Z0-9\"“‘($])")
BLOCK_TAG_RE = re.compile(r"<(li|p|h2|h3)\b[^>]*>(.*?)</\1>", re.DOTALL)


def last_sentence(text: str) -> str:
    protected = ABBREV_RE.sub(lambda m: m.group(0).replace(".", "․"), text)
    return SENT_SPLIT_RE.split(protected.strip())[-1].replace("․", ".")


def element_ok(p: dict, kind: str, text: str, prev: str, rules: "Rules") -> bool:
    anchors = p.get("anchors") or []
    if not any(re.search(a, text, re.I) for a in anchors):
        return False
    if any(re.search(x, text, re.I) for x in GLOBAL_ELEMENT_EXCLUDE + (p.get("element_exclude") or [])):
        return False
    if any(re.search(x, text, re.I) or re.search(x, prev, re.I)
           for x in p.get("element_exclude_with_prev") or []):
        return False
    tail_has_anchor = any(re.search(a, last_sentence(text), re.I) for a in anchors)
    if any(re.search(x, text, re.I) for x in p.get("element_exclude_unless_last") or []) \
            and not tail_has_anchor:
        return False
    if kind == "extra" and p.get("element_require_extra") and \
            not any(re.search(x, text, re.I) for x in p["element_require_extra"]):
        return False
    if kind == "costs":
        if len(text) > 200 and not tail_has_anchor:
            return False
        if p["type"] in rules.contain_types and TIMELINE_RE.search(text):
            return False
    return True


def place(fields: list[tuple[list, str]], p: dict, kind: str, coat: str | None,
          rules: "Rules") -> tuple[int, str, str] | None:
    """Append the product to the first <li>/<p> that recommends it and passes element rules."""
    prev = ""
    for i, (_, h) in enumerate(fields):
        for m in BLOCK_TAG_RE.finditer(h):
            text = html.unescape(plain(m.group(2)))
            if m.group(1) in ("li", "p") and MARK not in m.group(0) \
                    and element_ok(p, kind, text, prev, rules):
                close = m.end() - len(f"</{m.group(1)}>")
                return i, h[:close] + snippet(p, coat, kind, rules) + h[close:], text[:140]
            prev = text
    return None


def process(path: str, catalog: list[dict], weights: dict, extra: set[str],
            rules: Rules) -> dict | None:
    slug = os.path.basename(path)[:-5]
    kind = page_kind(slug) or ("extra" if slug in extra else None)
    if kind is None:
        return None
    d = json.load(open(path, encoding="utf-8"))
    if (d.get("meta") or {}).get("published", True) is False:
        return None
    fields = [(pth, BLOCK_RE.sub("", h)) for pth, h in html_fields(d)]
    faq = plain(json.dumps(d.get("faq") or [], ensure_ascii=False))
    text = html.unescape(" ".join(plain(h) for _, h in fields) + " " + faq)
    base = re.sub(r"-(grooming-guide|puppy-checklist|first-year-costs)$", "", slug)
    breed = base if base in weights else None
    families = candidates(slug, kind, text, catalog, breed, weights.get(base), rules)
    coat = rules.coat.get(breed) if breed else None
    placed = []
    for options in families:
        if len(placed) >= MAX_PER_PAGE[kind]:
            break
        for p in options:
            edit = place(fields, p, kind, coat, rules)
            if edit is None:
                continue
            i, new_html, where = edit
            fields[i] = (fields[i][0], new_html)
            placed.append({"asin": p["asin"], "name": p["name"], "type": p["type"], "where": where})
            break
    if not placed:
        return {"slug": slug, "kind": kind, "placed": [], "fields": fields, "doc": d}
    fields[0] = (fields[0][0], with_disclosure(fields[0][1]))
    return {"slug": slug, "kind": kind, "placed": placed, "fields": fields, "doc": d}


def with_disclosure(h: str) -> str:
    """Put the disclosure after the first paragraph or list (article-card excerpts are cut
    from the start of the body), but never after the first affiliate link."""
    ends = [(h.find(tag), tag) for tag in ("</p>", "</ul>", "</ol>") if h.find(tag) != -1]
    first_link = h.find(MARK)
    if ends:
        pos, tag = min(ends)
        if first_link == -1 or pos < first_link:
            at = pos + len(tag)
            return h[:at] + DISCLOSURE + h[at:]
    # The first link sits inside the opening list: split the list just before that item.
    li = h.rfind("<li", 0, first_link) if first_link != -1 else -1
    opener = max(h.rfind("<ul", 0, li), h.rfind("<ol", 0, li)) if li != -1 else -1
    if opener != -1 and h.find("<li", opener) < li:
        tag = h[opener + 1:opener + 3]
        return h[:li] + f"</{tag}>{DISCLOSURE}<{tag}>" + h[li:]
    return DISCLOSURE + h


def write(path: str, doc: dict, fields: list[tuple[list, str]]) -> bool:
    raw = open(path, encoding="utf-8").read()
    for pth, h in fields:
        set_path(doc, pth, h)
    out = json.dumps(doc, ensure_ascii=False, indent=2) + ("\n" if raw.endswith("\n") else "")
    if out == raw:
        return False
    open(path, "w", encoding="utf-8").write(out)
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--remove", action="store_true", help="strip all WOOFFY_AMZ_v1 blocks")
    ap.add_argument("--catalog", default=CATALOG)
    ap.add_argument("--plan", default=os.path.join(ROOT, "output", "amazon_plan.json"))
    args = ap.parse_args(argv)

    catalog: list[dict] = []
    rules = Rules({}, {})
    if not args.remove:
        raw_cat = json.load(open(args.catalog, encoding="utf-8"))
        catalog = raw_cat["entries"] if isinstance(raw_cat, dict) else raw_cat
        traits = json.load(open(os.path.join(ROOT, "breed_traits.json"), encoding="utf-8"))
        rules = Rules(raw_cat if isinstance(raw_cat, dict) else {},
                      {t["slug"]: t.get("category") for t in traits})
    extra = {s for p in catalog for s in (p.get("extra_slugs") or [])}
    weights = breed_weights()
    changed, plan = [], []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*.json"))):
        if args.remove:
            d = json.load(open(path, encoding="utf-8"))
            fields = [(pth, BLOCK_RE.sub("", h)) for pth, h in html_fields(d)]
            if any(MARK in h for _, h in html_fields(d)):
                if args.apply:
                    write(path, d, fields)
                changed.append(os.path.basename(path)[:-5])
            continue
        res = process(path, catalog, weights, extra, rules)
        if res is None:
            continue
        plan.append({k: res[k] for k in ("slug", "kind", "placed")})
        original = [h for _, h in html_fields(json.load(open(path, encoding="utf-8")))]
        if [h for _, h in res["fields"]] != original:
            changed.append(res["slug"])
            if args.apply:
                write(path, res["doc"], res["fields"])

    if not args.remove:
        os.makedirs(os.path.dirname(args.plan), exist_ok=True)
        json.dump(plan, open(args.plan, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        placed = [x for p in plan for x in p["placed"]]
        by_kind: dict[str, int] = {}
        for p in plan:
            if p["placed"]:
                by_kind[p["kind"]] = by_kind.get(p["kind"], 0) + 1
        print(f"pages with links: {sum(1 for p in plan if p['placed'])} {by_kind}; links: {len(placed)}")
        print(f"plan -> {args.plan}")
    print(f"{'changed' if args.apply else 'would change'}: {len(changed)}")
    with open(os.path.join(ROOT, "output", "amazon_changed_slugs.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(changed) + ("\n" if changed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
