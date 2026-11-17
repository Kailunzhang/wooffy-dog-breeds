"""One tool sentence + inline Amazon link for breed main guides that do not name a tool.

Owner-approved 2026-11-16. A breed main guide (kind "main" in inject_amazon_links.py)
whose care section never names a linkable grooming tool gets one short sentence that
names the breed's primary home tool, followed by the compact inline link. The tool is
not guessed: it is the first core tool that is already linked on the breed's own
grooming guide, so the main page and the grooming guide always agree and size / coat
fit has already been checked there.

The sentence and the link are wrapped together in the WOOFFY_AMZ_v1 markers, so
`inject_amazon_links.py --remove` strips both and restores the original text exactly.
"""
from __future__ import annotations

import hashlib
import html
import os
import re

CORE_TYPES = ("undercoat_rake", "slicker_brush", "pin_brush", "deshedding_tool")
SENTENCES = {
    "undercoat_rake": ["An undercoat rake is the tool that does most of the work on this coat.",
                       "For the undercoat, an undercoat rake is the tool to own."],
    "slicker_brush": ["A slicker brush is the everyday tool for this coat.",
                      "For brushing at home, a slicker brush is the tool to own."],
    "pin_brush": ["A pin brush is the everyday tool for this coat.",
                  "For brushing at home, a pin brush is the tool to own."],
    "deshedding_tool": ["A de-shedding tool does most of the work when the coat sheds."],
}
ASIN_RE = re.compile(r"amazon\.com/dp/([A-Z0-9]{10})")
H3_RE = re.compile(r"<h3[^>]*>\s*Grooming[^<]*</h3>\s*", re.I)
ELEM_RE = re.compile(r"<(p|li)\b[^>]*>(.*?)</\1>", re.S)
LIST_RE = re.compile(r"<(ul|ol)\b[^>]*>(.*?)</\1>", re.S)
BRUSH_RE = re.compile(r"\bbrush", re.I)
SEE_RE = re.compile(r"\s*See (?:the |our )?(?:<a\b[^>]*grooming-guide|dedicated grooming guide)", re.I)
RAKING_RE = re.compile(r"undercoat rak", re.I)
SKIP_RE = re.compile(r"hairless|no brushing|does not need brushing|doesn't need brushing", re.I)
TAG_RE = re.compile(r"<[^>]+>")


def _plain(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", s or ""))).strip()


def guide_tool(slug: str, data_dir: str, by_asin: dict, care_text: str = "") -> dict | None:
    """First core grooming tool already linked on the breed's grooming guide.

    When the main page itself talks about undercoat raking and the guide links a rake,
    the rake wins, so the added sentence never contradicts the paragraph it joins.
    """
    path = os.path.join(data_dir, f"{slug}-grooming-guide.json")
    if not os.path.exists(path):
        return None
    raw = open(path, encoding="utf-8").read()
    tools = [by_asin[a] for a in ASIN_RE.findall(raw)
             if a in by_asin and not by_asin[a].get("skip") and by_asin[a]["type"] in CORE_TYPES]
    if not tools:
        return None
    if RAKING_RE.search(care_text):
        rake = next((p for p in tools if p["type"] == "undercoat_rake"), None)
        if rake:
            return rake
    return tools[0]


def pick_sentence(slug: str, typ: str) -> str:
    options = SENTENCES[typ]
    return options[int(hashlib.md5(slug.encode("utf-8")).hexdigest(), 16) % len(options)]


def find_target(care: str) -> tuple[int, int] | None:
    """(start, end) of the inner HTML of the element that talks about brushing."""
    h3 = H3_RE.search(care)
    if h3:
        rest = care[h3.end():].lstrip()
        offset = len(care) - len(rest)
        if rest.startswith("<p"):
            m = ELEM_RE.match(rest)
            if m and m.group(1) == "p":
                return offset + m.start(2), offset + m.end(2)
        if rest.startswith(("<ul", "<ol")):
            lst = LIST_RE.match(rest)
            if lst:
                items = list(ELEM_RE.finditer(rest, lst.start(2), lst.end(2)))
                pick = next((m for m in items if BRUSH_RE.search(_plain(m.group(2)))), None)
                if pick:
                    return offset + pick.start(2), offset + pick.end(2)
        return None
    for m in ELEM_RE.finditer(care):
        if BRUSH_RE.search(_plain(m.group(2))):
            return m.start(2), m.end(2)
    return None


def build_block(care: str, slug: str, product: dict, url: str, mark: str, end: str) -> tuple[str, str] | None:
    """Return (new care html, text before the insertion) or None when there is no safe spot."""
    span = find_target(care)
    if span is None:
        return None
    inner = care[span[0]:span[1]]
    if mark in inner or SKIP_RE.search(_plain(inner)):
        return None
    see = None
    for see in SEE_RE.finditer(inner):
        pass
    pos = see.start() if see else len(inner)
    before = _plain(inner[:pos])
    if not before:
        return None
    lead = " " if before[-1] in ".!?" else ". "
    sentence = pick_sentence(slug, product["type"])
    block = (f'{mark}{lead}{sentence} <span class="wfy-aff">(One option: <a href="{url}" '
             f'rel="sponsored nofollow noopener" target="_blank">{html.escape(product["name"])} on Amazon</a>.)</span>{end}')
    at = span[0] + pos
    return care[:at] + block + care[at:], before[-140:]


def apply(slug: str, fields: list, catalog: list[dict], data_dir: str, mark: str, end: str,
          url_for) -> tuple[list, dict] | None:
    """Add the sentence block to the care field. Returns (fields, placed item) or None."""
    by_asin = {p["asin"]: p for p in catalog}
    care_text = _plain(" ".join(h for key, h in fields if "care" in key))
    product = guide_tool(slug, data_dir, by_asin, care_text)
    if product is None:
        return None
    for i, (key, h) in enumerate(fields):
        if "care" not in key:
            continue
        built = build_block(h, slug, product, url_for(product), mark, end)
        if built is None:
            return None
        new_fields = list(fields)
        new_fields[i] = (key, built[0])
        return new_fields, {"asin": product["asin"], "name": product["name"], "type": product["type"],
                            "where": "gear sentence: " + built[1]}
    return None
