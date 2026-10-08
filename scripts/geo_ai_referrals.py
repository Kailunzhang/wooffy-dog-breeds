"""AI answer-engine referral tracker for thewooffy.com (GEO KPI #2).

Week-1 deliverable of GEO_PLAN.md (W0.1). Pulls GA4 sessions whose
sessionSource is an AI answer engine (ChatGPT, Perplexity, Copilot,
Gemini, Claude, Grok, ...; the table lives in traffic_watch.AI_LABEL),
and records:

  - 28-day and 7-day totals, week-over-week change, share of all sessions
  - per-engine totals
  - the landing pages AI engines send people to (which articles get cited)
  - a daily series for the last 28 days

One dated row is appended to geo/ai-referrals.jsonl (a re-run on the same
date replaces that day's row) and a readable snapshot is written to
geo/ai-referrals-latest.md. The daily-digest workflow runs this after the
email and commits the two files, so the history accumulates in git.

Google AI Overviews / AI Mode clicks carry a plain google.com referrer and
are NOT separable here; they show up inside Organic Search.

Env (same as traffic_watch.py): GA4_PROPERTY_ID plus either
GA4_OAUTH_CLIENT_ID / GA4_OAUTH_CLIENT_SECRET / GA4_OAUTH_REFRESH_TOKEN or
GA4_SA_JSON.

Usage:
    python3 scripts/geo_ai_referrals.py                 # fetch, print, write
    python3 scripts/geo_ai_referrals.py --no-write      # print only
    python3 scripts/geo_ai_referrals.py --json          # summary as JSON
    python3 scripts/geo_ai_referrals.py --dump raw.json # also save raw GA4 rows
    python3 scripts/geo_ai_referrals.py --from-dump raw.json  # offline re-render
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import traffic_watch as tw  # noqa: E402  (brings the GA4 client + AI table)

HISTORY_PATH = ROOT / "geo" / "ai-referrals.jsonl"
LATEST_PATH = ROOT / "geo" / "ai-referrals-latest.md"
TOP_PAGES = 15


def fetch(client, prop) -> dict:
    """Raw GA4 rows. Every AI query is filtered server-side on sessionSource."""
    flt = tw.ai_source_filter()

    def ai(dims, start, end, limit=500):
        return tw._run(client, prop, dims, ["sessions"], start, end,
                       order_metric="sessions", limit=limit, dim_filter=flt)

    total_daily = tw._run(client, prop, ["date"], ["sessions"],
                          "28daysAgo", "yesterday")
    return {
        "fetched": date.today().isoformat(),
        "total_daily": [(r[0], int(r[1])) for r in total_daily],
        "ai_28": [(r[0], int(r[1])) for r in ai(["sessionSource"], "28daysAgo", "yesterday")],
        "ai_7": [(r[0], int(r[1])) for r in ai(["sessionSource"], "7daysAgo", "yesterday")],
        "ai_prev": [(r[0], int(r[1])) for r in ai(["sessionSource"], "14daysAgo", "8daysAgo")],
        "ai_pages": [(r[0], r[1], int(r[2]))
                     for r in ai(["sessionSource", "landingPage"], "28daysAgo", "yesterday")],
        "ai_daily": [(r[0], r[1], int(r[2]))
                     for r in ai(["date", "sessionSource"], "28daysAgo", "yesterday", limit=2000)],
    }


def _by_engine(rows) -> dict[str, int]:
    out: dict[str, int] = {}
    for src, n in rows:
        lab = tw._ai_label(src)
        if lab:
            out[lab] = out.get(lab, 0) + int(n)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def summarize(raw: dict) -> dict:
    eng28 = _by_engine(raw["ai_28"])
    eng7 = _by_engine(raw["ai_7"])
    total28 = sum(eng28.values())
    now7 = sum(eng7.values())
    prev7 = sum(_by_engine(raw["ai_prev"]).values())
    all28 = sum(n for _, n in raw["total_daily"]) or 1

    pages: dict[str, dict] = {}
    for src, page, n in raw["ai_pages"]:
        lab = tw._ai_label(src)
        if not lab:
            continue
        p = pages.setdefault(page, {"sessions": 0, "engines": {}})
        p["sessions"] += n
        p["engines"][lab] = p["engines"].get(lab, 0) + n
    top_pages = [{"page": k, **v} for k, v in
                 sorted(pages.items(), key=lambda kv: -kv[1]["sessions"])[:TOP_PAGES]]

    daily: dict[str, dict] = {d: {"date": d, "total": 0, "engines": {}} for d, _ in raw["total_daily"]}
    for d, src, n in raw["ai_daily"]:
        lab = tw._ai_label(src)
        if not lab:
            continue
        row = daily.setdefault(d, {"date": d, "total": 0, "engines": {}})
        row["total"] += n
        row["engines"][lab] = row["engines"].get(lab, 0) + n

    return {
        "date": raw.get("fetched") or date.today().isoformat(),
        "window_end": "yesterday",
        "total28": total28,
        "share28_pct": round(100.0 * total28 / all28, 2),
        "all_sessions28": all28,
        "now7": now7,
        "prev7": prev7,
        "wow_pct": round(100.0 * tw._pct(now7, prev7), 1),
        "engines28": eng28,
        "engines7": eng7,
        "top_pages": top_pages,
        "daily": sorted(daily.values(), key=lambda r: r["date"]),
    }


def render_md(s: dict) -> str:
    lines = [
        "# AI answer-engine referrals (GA4)",
        "",
        f"Snapshot: {s['date']} (windows end yesterday). "
        "Generated by `scripts/geo_ai_referrals.py`; history in `geo/ai-referrals.jsonl`.",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| AI sessions, last 28 days | {s['total28']} |",
        f"| Share of all sessions (28 d) | {s['share28_pct']}% |",
        f"| AI sessions, last 7 days | {s['now7']} |",
        f"| AI sessions, previous 7 days | {s['prev7']} |",
        f"| Week over week | {s['wow_pct']:+.1f}% |",
        "",
        "## By engine (28 days)",
        "",
        "| Engine | Sessions | Last 7 d |",
        "|--------|---------:|---------:|",
    ]
    for eng, n in s["engines28"].items():
        lines.append(f"| {eng} | {n} | {s['engines7'].get(eng, 0)} |")
    if not s["engines28"]:
        lines.append("| (none yet) | 0 | 0 |")
    lines += ["", f"## Pages AI engines send people to (28 days, top {TOP_PAGES})", "",
              "| Page | Sessions | Engines |", "|------|---------:|---------|"]
    for p in s["top_pages"]:
        eng = ", ".join(f"{k} {v}" for k, v in sorted(p["engines"].items(), key=lambda kv: -kv[1]))
        lines.append(f"| {p['page']} | {p['sessions']} | {eng} |")
    if not s["top_pages"]:
        lines.append("| (none yet) | 0 | |")
    lines += ["", "## Daily (28 days)", "", "| Date | AI sessions | Engines |", "|------|-----------:|---------|"]
    for r in s["daily"]:
        eng = ", ".join(f"{k} {v}" for k, v in sorted(r["engines"].items(), key=lambda kv: -kv[1]))
        lines.append(f"| {r['date']} | {r['total']} | {eng} |")
    lines += ["", "Google AI Overviews / AI Mode clicks arrive as google.com referrals and are "
              "not separable here; they sit inside Organic Search.", ""]
    return "\n".join(lines)


def print_table(s: dict) -> None:
    print(f"AI referrals  {s['date']}  28d={s['total28']} ({s['share28_pct']}% of {s['all_sessions28']})"
          f"  7d={s['now7']} vs prev {s['prev7']} ({s['wow_pct']:+.1f}%)")
    print()
    print(f"{'engine':<14}{'28d':>6}{'7d':>6}")
    for eng, n in s["engines28"].items():
        print(f"{eng:<14}{n:>6}{s['engines7'].get(eng, 0):>6}")
    if not s["engines28"]:
        print("(no AI-referred sessions in the window)")
    print()
    print("top landing pages from AI engines (28d):")
    for p in s["top_pages"][:10]:
        print(f"  {p['sessions']:>4}  {p['page']}")
    if not s["top_pages"]:
        print("  (none)")


def write_history(s: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    kept = []
    if HISTORY_PATH.exists():
        for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("date") != s["date"]:
                kept.append(line)
    compact = {k: v for k, v in s.items() if k != "daily"}  # daily is re-fetched each run
    kept.append(json.dumps(compact, separators=(",", ":"), ensure_ascii=False))
    HISTORY_PATH.write_text("\n".join(kept) + "\n", encoding="utf-8")
    LATEST_PATH.write_text(render_md(s), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--no-write", action="store_true", help="print only; do not touch geo/")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON")
    ap.add_argument("--dump", metavar="FILE", help="save the raw GA4 rows to FILE")
    ap.add_argument("--from-dump", metavar="FILE", help="render from a saved --dump instead of GA4")
    args = ap.parse_args(argv)

    if args.from_dump:
        raw = json.loads(Path(args.from_dump).read_text(encoding="utf-8"))
    else:
        client, prop = tw._client_and_property()
        raw = fetch(client, prop)
        if args.dump:
            Path(args.dump).write_text(json.dumps(raw, indent=1), encoding="utf-8")

    s = summarize(raw)
    if args.json:
        print(json.dumps(s, indent=2, ensure_ascii=False))
    else:
        print_table(s)
    if not args.no_write:
        write_history(s)
        if not args.json:
            print(f"\nwrote {LATEST_PATH.relative_to(ROOT)} and updated {HISTORY_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
