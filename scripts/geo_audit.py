"""GEO coverage audit for every article in breed-data/.

Week-1 deliverable of GEO_PLAN.md (W0.3). Scans the JSON sources (not the
live site) and reports, per article type and overall, how many articles
carry the four on-page signals AI answer engines select for:

  quick_answer   a direct-answer block at the top: meta.quick_answer, the
                 WOOFFY_QUICK_ANSWER marker, or a .quick-answer element
  sources        an authority citation: the ymyl-citations sentinel, a
                 "Sources" heading, or a link to an authority domain
                 (AUTHORITY_DOMAINS below)
  question_heads at least half of the article's section headings are
                 phrased as questions (end with "?")
  visible_date   a visible "Last updated ..." line in the body text, or
                 meta.content_updated (which generate.py renders as one)

Two informational columns are also reported: faq3 (>= 3 FAQ pairs, from
the `faq` list, the FAQPage JSON-LD, or inline <h3>question?</h3> pairs) and
intro_numbers (a digit appears in the first 80 words of the intro, a
proxy for "the opening answer carries a concrete figure").

Nothing is written to Shopify. The report goes to stdout and to
geo_audit_report.md; one dated summary row is appended to
geo/audit-history.jsonl so week-over-week progress can be charted.

Usage:
    python3 scripts/geo_audit.py                     # report + history row
    python3 scripts/geo_audit.py --type costs        # one article type only
    python3 scripts/geo_audit.py --missing sources   # list slugs lacking a signal
    python3 scripts/geo_audit.py --json              # machine-readable to stdout
    python3 scripts/geo_audit.py --no-write          # stdout only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"
REPORT_PATH = ROOT / "geo_audit_report.md"
HISTORY_PATH = ROOT / "geo" / "audit-history.jsonl"

SIGNALS = ("quick_answer", "sources", "question_heads", "visible_date")
INFO = ("faq3", "intro_numbers")
TYPES = ("main", "grooming", "costs", "checklist", "roundup", "comparison", "guide")

# Outbound domains that count as an authority citation. Order is irrelevant.
AUTHORITY_DOMAINS = (
    "akc.org", "aspca.org", "vcahospitals.com", "merckvetmanual.com",
    "ofa.org", "petpoisonhelpline.com", "avma.org", "aaha.org",
    "ukcdogs.com", "thekennelclub.org.uk", "fci.be", "ncbi.nlm.nih.gov",
    "cornell.edu", "ucdavis.edu", "tufts.edu", "rvc.ac.uk",
)

HTML_TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
QUICK_ANSWER = re.compile(r"WOOFFY_QUICK_ANSWER|class=\"[^\"]*\bquick-answer\b", re.I)
SOURCES_HEADING = re.compile(r"<h[2-4][^>]*>\s*(?:sources|references|further reading)\b", re.I)
SOURCES_SENTINEL = re.compile(r"<!--\s*ymyl-citations", re.I)
HREF = re.compile(r'href="(https?://[^"]+)"', re.I)
VISIBLE_DATE = re.compile(r"last\s+(?:updated|reviewed)\b", re.I)
HEADING_TAG = re.compile(r"<h[23][^>]*>(.*?)</h[23]>", re.I | re.S)
DIGIT = re.compile(r"\d")
INLINE_Q = re.compile(r"<h3[^>]*>[^<]*\?\s*</h3>", re.I)
SCHEMA_Q = re.compile(r'"@type"\s*:\s*"Question"', re.I)
AUTHORITY_RE = re.compile(
    r"https?://(?:[a-z0-9-]+\.)*(?:" + "|".join(re.escape(d) for d in AUTHORITY_DOMAINS) + r")(?:/|\"|$)",
    re.I,
)


def strip_html(html: str) -> str:
    return WS.sub(" ", HTML_TAG.sub(" ", html or "")).strip()


def classify(slug: str, data: dict) -> str:
    """Map an article to one of TYPES from its slug and meta."""
    meta = data.get("meta") or {}
    size_cat = (meta.get("size_category") or "").lower()
    if "body_html" in data:
        return "guide"
    if "-vs-" in slug or size_cat == "comparison":
        return "comparison"
    if size_cat == "roundup" or (meta.get("group") == "Breed Guides"):
        return "roundup"
    for suffix, kind in (("-grooming-guide", "grooming"),
                         ("-first-year-costs", "costs"),
                         ("-puppy-checklist", "checklist")):
        if slug.endswith(suffix):
            return kind
    if size_cat == "guide":
        return "guide"
    return "main"


def all_html(data: dict) -> str:
    if data.get("body_html"):
        return data["body_html"]
    sections = data.get("sections") or {}
    return "\n".join((s.get("html") or "") for s in sections.values() if isinstance(s, dict))


def headings(data: dict) -> list[str]:
    """Section headings: sections.*.heading for structured articles, h2/h3 for body_html."""
    if data.get("body_html"):
        return [strip_html(h) for h in HEADING_TAG.findall(data["body_html"])]
    out = []
    for key, s in (data.get("sections") or {}).items():
        if isinstance(s, dict) and s.get("heading"):
            out.append(strip_html(s["heading"]))
    return out


def intro_text(data: dict) -> str:
    if data.get("body_html"):
        return strip_html(data["body_html"])
    intro = (data.get("sections") or {}).get("intro") or {}
    return strip_html(intro.get("html", "")) if isinstance(intro, dict) else ""


def audit_article(slug: str, data: dict) -> dict:
    meta = data.get("meta") or {}
    html = all_html(data)
    heads = headings(data)
    question_heads = [h for h in heads if h.rstrip().endswith("?")]
    authority_links = sorted({m.group(0).rstrip('"/') for m in AUTHORITY_RE.finditer(html)})
    first80 = " ".join(intro_text(data).split()[:80])
    faq_count = max(len(data.get("faq") or []), len(SCHEMA_Q.findall(html)), len(INLINE_Q.findall(html)))
    return {
        "slug": slug,
        "type": classify(slug, data),
        "quick_answer": bool((meta.get("quick_answer") or "").strip()) or bool(QUICK_ANSWER.search(html)),
        "sources": bool(SOURCES_SENTINEL.search(html) or SOURCES_HEADING.search(html) or authority_links),
        "authority_links": len(authority_links),
        "headings": len(heads),
        "question_headings": len(question_heads),
        "question_heads": bool(heads) and len(question_heads) * 2 >= len(heads),
        # generate.py renders meta.content_updated as a visible "Last updated"
        # line, so the JSON field counts even though the text is not in the html.
        "visible_date": bool(VISIBLE_DATE.search(strip_html(html))) or bool((meta.get("content_updated") or "").strip()),
        "faq3": faq_count >= 3,
        "intro_numbers": bool(DIGIT.search(first80)),
    }


def load_articles() -> list[dict]:
    rows = []
    for path in sorted(BREED_DATA.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"skip {path.name}: {exc}", file=sys.stderr)
            continue
        if not isinstance(data, dict) or "meta" not in data:
            continue
        rows.append(audit_article(path.stem, data))
    return rows


def summarize(rows: list[dict]) -> dict:
    by_type: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)
    cols = SIGNALS + INFO

    def block(group: list[dict]) -> dict:
        n = len(group)
        out = {"articles": n}
        for c in cols:
            k = sum(1 for r in group if r[c])
            out[c] = {"count": k, "pct": round(100.0 * k / n, 1) if n else 0.0}
        total_heads = sum(r["headings"] for r in group)
        q_heads = sum(r["question_headings"] for r in group)
        out["heading_question_share_pct"] = round(100.0 * q_heads / total_heads, 1) if total_heads else 0.0
        return out

    return {
        "date": date.today().isoformat(),
        "total": block(rows),
        "by_type": {t: block(by_type[t]) for t in TYPES if by_type.get(t)},
    }


def render_report(summary: dict, rows: list[dict]) -> str:
    cols = SIGNALS + INFO
    lines = [
        "# Wooffy GEO Coverage Audit",
        "",
        f"Date: {summary['date']}  ",
        f"Articles scanned: {summary['total']['articles']}  ",
        "Source: `breed-data/*.json` (JSON sources, not the live site). "
        "Generated by `scripts/geo_audit.py`.",
        "",
        "Signal definitions: see the docstring of `scripts/geo_audit.py`. "
        "`question_heads` passes when at least half of an article's section headings end with `?`.",
        "",
        "## Overall",
        "",
        "| Signal | Articles | % |",
        "|--------|---------:|--:|",
    ]
    for c in cols:
        v = summary["total"][c]
        lines.append(f"| {c} | {v['count']} | {v['pct']} |")
    lines.append(f"| headings phrased as questions (share of all headings) | — | {summary['total']['heading_question_share_pct']} |")
    lines += ["", "## By article type (% of articles)", "",
              "| Type | Articles | " + " | ".join(cols) + " |",
              "|------|---------:|" + "|".join("--:" for _ in cols) + "|"]
    for t, b in summary["by_type"].items():
        lines.append(f"| {t} | {b['articles']} | " + " | ".join(str(b[c]["pct"]) for c in cols) + " |")

    lines += ["", "## Largest gaps (articles missing the signal, by type)", ""]
    for c in SIGNALS:
        missing = Counter(r["type"] for r in rows if not r[c])
        if not missing:
            lines.append(f"- **{c}**: none missing")
            continue
        parts = ", ".join(f"{t} {n}" for t, n in sorted(missing.items(), key=lambda kv: -kv[1]))
        lines.append(f"- **{c}**: {sum(missing.values())} missing ({parts})")
    lines += ["", "List the slugs behind any row with "
              "`python3 scripts/geo_audit.py --missing <signal> [--type <type>]`.", ""]
    return "\n".join(lines)


def print_table(summary: dict) -> None:
    cols = SIGNALS + INFO
    w = max(len(c) for c in cols)
    print(f"GEO coverage audit  {summary['date']}  articles={summary['total']['articles']}")
    print()
    head = f"{'type':<11}{'n':>5}  " + "  ".join(f"{c:>{w}}" for c in cols)
    print(head)
    print("-" * len(head))
    for t, b in list(summary["by_type"].items()) + [("TOTAL", summary["total"])]:
        print(f"{t:<11}{b['articles']:>5}  " + "  ".join(f"{b[c]['pct']:>{w}.1f}" for c in cols))
    print()
    print(f"share of all headings phrased as questions: {summary['total']['heading_question_share_pct']}%")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--type", choices=TYPES, help="restrict to one article type")
    ap.add_argument("--missing", choices=SIGNALS + INFO, help="list slugs lacking this signal and exit")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON instead of a table")
    ap.add_argument("--no-write", action="store_true",
                    help="do not write geo_audit_report.md or append to geo/audit-history.jsonl")
    args = ap.parse_args(argv)

    rows = load_articles()
    if args.type:
        rows = [r for r in rows if r["type"] == args.type]
    if not rows:
        print("no articles matched", file=sys.stderr)
        return 1

    if args.missing:
        for r in rows:
            if not r[args.missing]:
                print(r["slug"])
        return 0

    summary = summarize(rows)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_table(summary)

    if not args.no_write and not args.type:
        REPORT_PATH.write_text(render_report(summary, rows), encoding="utf-8")
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        # one row per day: a re-run on the same date replaces that day's row
        kept = []
        if HISTORY_PATH.exists():
            for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip() and json.loads(line).get("date") != summary["date"]:
                    kept.append(line)
        kept.append(json.dumps(summary, separators=(",", ":")))
        HISTORY_PATH.write_text("\n".join(kept) + "\n", encoding="utf-8")
        if not args.json:
            print(f"\nwrote {REPORT_PATH.relative_to(ROOT)} and appended {HISTORY_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. `--missing ... | head`
        sys.exit(0)
