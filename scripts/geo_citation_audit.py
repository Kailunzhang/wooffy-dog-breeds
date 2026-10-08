"""AI answer-engine citation audit for thewooffy.com (GEO KPI #1).

Week-1 deliverable of GEO_PLAN.md (W0.2). Asks each question in
geo/query_panel.json to an AI answer engine with web search enabled and
records which sources the answer cites, so we can track the share of
questions where thewooffy.com is cited, month over month, and which
competitor domains win the rest.

Engines are pluggable; only `claude` is implemented today (Claude with the
Anthropic web search tool, using the ANTHROPIC_API_KEY the repo already
has). The run format is engine-neutral so a ChatGPT or Perplexity engine
can be added later and compared on the same panel.

Cost: one Claude request per question, web search capped at MAX_USES.
At $10 per 1,000 searches plus tokens, the 60-question panel is a few
dollars per run.

Outputs (all under geo/citations/):
  <date>-<engine>.json   full per-question results (resume-safe: re-running
                         the same day skips questions already answered)
  latest.md              readable snapshot of the most recent run
  history.jsonl          one summary row per run, for month-over-month

Usage:
    python3 scripts/geo_citation_audit.py --dry-run          # show the panel, no API calls
    python3 scripts/geo_citation_audit.py --limit 3          # try 3 questions
    python3 scripts/geo_citation_audit.py                    # full panel
    python3 scripts/geo_citation_audit.py --group costs      # one group only
    python3 scripts/geo_citation_audit.py --from-run geo/citations/2026-10-08-claude.json  # re-render
Env: ANTHROPIC_API_KEY (or .env at the repo root).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "geo" / "query_panel.json"
OUT_DIR = ROOT / "geo" / "citations"
LATEST_PATH = OUT_DIR / "latest.md"
HISTORY_PATH = OUT_DIR / "history.jsonl"

SITE_DOMAIN = "thewooffy.com"
API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-5-5"
MAX_USES = 3                 # web searches per question
MAX_PAUSE_RESUMES = 3        # pause_turn continuations per question
MAX_TOKENS = 2048
SYSTEM_PROMPT = (
    "You are a general-purpose assistant answering a dog owner's question. "
    "Search the web, then answer concisely (under 200 words) the way a "
    "consumer AI assistant would, citing the sources you relied on. Do not "
    "favor or avoid any particular website."
)


# ---------------------------------------------------------------- helpers
def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip() or load_env().get("ANTHROPIC_API_KEY", "")
    if not key:
        sys.exit("ANTHROPIC_API_KEY not set (env or .env)")
    return key


def domain(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def is_site(url: str) -> bool:
    d = domain(url)
    return d == SITE_DOMAIN or d.endswith("." + SITE_DOMAIN)


# ---------------------------------------------------------------- engine: claude
def _post(key: str, body: dict, timeout: int = 180) -> dict:
    """POST to the Messages API with retries on 429/5xx/connection errors."""
    data = json.dumps(body).encode("utf-8")
    delay = 5.0
    for attempt in range(6):
        req = urllib.request.Request(API_URL, data=data, method="POST")
        req.add_header("x-api-key", key)
        req.add_header("anthropic-version", API_VERSION)
        req.add_header("content-type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:300]
            if e.code in (408, 409, 429) or e.code >= 500:
                retry_after = e.headers.get("retry-after")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else delay
                print(f"    HTTP {e.code}, retry in {wait:.0f}s: {text}", file=sys.stderr)
                time.sleep(wait)
                delay = min(delay * 2, 120)
                continue
            raise RuntimeError(f"API {e.code}: {text}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"    connection error, retry in {delay:.0f}s: {e}", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 120)
    raise RuntimeError("API: gave up after retries")


def ask_claude(key: str, query: str, model: str) -> dict:
    """One question -> the full list of assistant content blocks + usage."""
    tools = [{
        "type": "web_search_20260209",
        "name": "web_search",
        "max_uses": MAX_USES,
        "allowed_callers": ["direct"],  # flat response blocks, no dynamic filtering
        "user_location": {"type": "approximate", "country": "US", "timezone": "America/Los_Angeles"},
    }]
    messages = [{"role": "user", "content": query}]
    content: list = []
    usage_tot: Counter = Counter()
    stop = None
    for _ in range(MAX_PAUSE_RESUMES + 1):
        resp = _post(key, {
            "model": model,
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "output_config": {"effort": "low"},
            "tools": tools,
            "messages": messages,
        })
        blocks = resp.get("content", [])
        content.extend(blocks)
        u = resp.get("usage", {}) or {}
        usage_tot["input_tokens"] += u.get("input_tokens", 0)
        usage_tot["output_tokens"] += u.get("output_tokens", 0)
        usage_tot["web_search_requests"] += (u.get("server_tool_use") or {}).get("web_search_requests", 0)
        stop = resp.get("stop_reason")
        if stop != "pause_turn":
            break
        # Resume: send the paused assistant turn back unchanged.
        messages = messages + [{"role": "assistant", "content": blocks}]
    return {"content": content, "usage": dict(usage_tot), "stop_reason": stop, "model": resp.get("model", model)}


def parse_answer(raw: dict) -> dict:
    """Extract answer text, cited URLs, searched URLs and errors from the blocks."""
    text_parts, cited, results, errors, queries = [], [], [], [], []

    def walk(blocks):
        for b in blocks:
            t = b.get("type")
            if t == "text":
                text_parts.append(b.get("text", ""))
                for c in b.get("citations") or []:
                    if c.get("url"):
                        cited.append({"url": c["url"], "title": c.get("title", ""), "cited_text": c.get("cited_text", "")})
            elif t == "server_tool_use" and b.get("name") == "web_search":
                queries.append((b.get("input") or {}).get("query", ""))
            elif t == "web_search_tool_result":
                c = b.get("content")
                if isinstance(c, dict):          # error object, not a result list
                    errors.append(c.get("error_code", "unknown"))
                elif isinstance(c, list):
                    for r in c:
                        if r.get("type") == "web_search_result" and r.get("url"):
                            results.append({"url": r["url"], "title": r.get("title", ""), "page_age": r.get("page_age")})
            elif isinstance(b.get("content"), list):   # nested (code-execution) blocks
                walk(b["content"])

    walk(raw.get("content", []))
    seen, cited_unique = set(), []
    for c in cited:
        if c["url"] not in seen:
            seen.add(c["url"]); cited_unique.append(c)
    seen, results_unique = set(), []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"]); results_unique.append(r)
    site_cited = [c["url"] for c in cited_unique if is_site(c["url"])]
    site_in_results = [r["url"] for r in results_unique if is_site(r["url"])]
    return {
        "answer": re.sub(r"\s+", " ", "".join(text_parts)).strip()[:1200],
        "search_queries": queries,
        "cited": cited_unique,
        "cited_domains": sorted({domain(c["url"]) for c in cited_unique}),
        "results": results_unique,
        "site_cited": bool(site_cited),
        "site_cited_urls": site_cited,
        "site_in_results": bool(site_in_results),
        "site_result_urls": site_in_results,
        "errors": errors,
        "stop_reason": raw.get("stop_reason"),
        "usage": raw.get("usage", {}),
    }


ENGINES = {"claude": ask_claude}


# ---------------------------------------------------------------- run + report
def load_panel(group: str | None, limit: int | None) -> list[dict]:
    panel = json.loads(PANEL_PATH.read_text(encoding="utf-8"))
    qs = [q for q in panel["queries"] if not group or q["group"] == group]
    return qs[:limit] if limit else qs


def run_path(day: str, engine: str) -> Path:
    return OUT_DIR / f"{day}-{engine}.json"


def summarize(run: dict) -> dict:
    rows = run["results"]
    by_group: dict[str, dict] = defaultdict(lambda: {"n": 0, "cited": 0, "in_results": 0})
    comp = Counter()
    target_hit = 0
    for r in rows:
        g = by_group[r["group"]]
        g["n"] += 1
        g["cited"] += r["site_cited"]
        g["in_results"] += r["site_in_results"]
        for d in r["cited_domains"]:
            if d != SITE_DOMAIN:
                comp[d] += 1
        if any(f"/{r['target']}" in u for u in r["site_cited_urls"]):
            target_hit += 1
    n = len(rows)
    cited = sum(r["site_cited"] for r in rows)
    in_res = sum(r["site_in_results"] for r in rows)
    searches = sum((r.get("usage") or {}).get("web_search_requests", 0) for r in rows)
    return {
        "date": run["date"], "engine": run["engine"], "model": run.get("model"),
        "questions": n,
        "site_cited": cited, "site_cited_pct": round(100.0 * cited / n, 1) if n else 0.0,
        "site_in_results": in_res, "site_in_results_pct": round(100.0 * in_res / n, 1) if n else 0.0,
        "target_page_cited": target_hit,
        "by_group": {g: {**v, "cited_pct": round(100.0 * v["cited"] / v["n"], 1)} for g, v in sorted(by_group.items())},
        "top_competitors": comp.most_common(15),
        "web_searches": searches,
        "errors": sum(len(r.get("errors") or []) for r in rows),
    }


def render_md(run: dict, s: dict) -> str:
    L = [
        "# AI citation audit",
        "",
        f"Run: {s['date']} · engine `{s['engine']}` · model `{s['model']}` · {s['questions']} questions · "
        f"{s['web_searches']} web searches. Generated by `scripts/geo_citation_audit.py`; history in `geo/citations/history.jsonl`.",
        "",
        "| Metric | Value |", "|--------|------:|",
        f"| Questions where {SITE_DOMAIN} is cited | {s['site_cited']} / {s['questions']} ({s['site_cited_pct']}%) |",
        f"| …where the intended target page is the one cited | {s['target_page_cited']} |",
        f"| Questions where {SITE_DOMAIN} appeared in search results (cited or not) | {s['site_in_results']} ({s['site_in_results_pct']}%) |",
        f"| Search-tool errors | {s['errors']} |",
        "", "## By group", "", "| Group | Questions | Cited | Cited % | In results |", "|-------|--:|--:|--:|--:|",
    ]
    for g, v in s["by_group"].items():
        L.append(f"| {g} | {v['n']} | {v['cited']} | {v['cited_pct']} | {v['in_results']} |")
    L += ["", "## Domains cited instead (top 15)", "", "| Domain | Questions |", "|--------|--:|"]
    L += [f"| {d} | {n} |" for d, n in s["top_competitors"]] or ["| (none) | 0 |"]
    L += ["", "## Per question", "", "| id | Question | Wooffy cited | Cited domains |", "|----|----------|:--:|---------------|"]
    for r in run["results"]:
        mark = "✅" if r["site_cited"] else ("👀" if r["site_in_results"] else "❌")
        L.append(f"| {r['id']} | {r['query']} | {mark} | {', '.join(r['cited_domains']) or '—'} |")
    L += ["", "✅ cited · 👀 in search results but not cited · ❌ absent", ""]
    return "\n".join(L)


def write_history(s: dict) -> None:
    kept = []
    if HISTORY_PATH.exists():
        for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not (row.get("date") == s["date"] and row.get("engine") == s["engine"]):
                kept.append(line)
    kept.append(json.dumps(s, separators=(",", ":"), ensure_ascii=False))
    HISTORY_PATH.write_text("\n".join(kept) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--engine", choices=sorted(ENGINES), default="claude")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--group", help="only this panel group")
    ap.add_argument("--limit", type=int, help="only the first N questions")
    ap.add_argument("--date", default=date.today().isoformat(), help="run date (YYYY-MM-DD)")
    ap.add_argument("--sleep", type=float, default=1.0, help="seconds between questions")
    ap.add_argument("--dry-run", action="store_true", help="print the panel; no API calls")
    ap.add_argument("--no-write", action="store_true", help="do not write files")
    ap.add_argument("--from-run", metavar="FILE", help="re-render reports from a saved run file")
    args = ap.parse_args(argv)

    if args.from_run:
        run = json.loads(Path(args.from_run).read_text(encoding="utf-8"))
    else:
        panel = load_panel(args.group, args.limit)
        if args.dry_run:
            for q in panel:
                print(f"{q['id']:<14}{q['group']:<10}{q['query']:<60} -> {q['target']}")
            print(f"\n{len(panel)} questions; engine={args.engine} model={args.model} max_uses={MAX_USES}")
            return 0
        key = api_key()
        path = run_path(args.date, args.engine)
        run = {"date": args.date, "engine": args.engine, "model": args.model, "results": []}
        if path.exists() and not args.no_write:
            run = json.loads(path.read_text(encoding="utf-8"))
        done = {r["id"] for r in run["results"]}
        ask = ENGINES[args.engine]
        for i, q in enumerate(panel, 1):
            if q["id"] in done:
                continue
            print(f"[{i}/{len(panel)}] {q['id']}  {q['query']}")
            try:
                raw = ask(key, q["query"], args.model)
            except RuntimeError as e:
                print(f"    FAILED: {e}", file=sys.stderr)
                continue
            parsed = parse_answer(raw)
            run["model"] = raw.get("model", args.model)
            run["results"].append({**q, **parsed})
            mark = "cited" if parsed["site_cited"] else ("in results" if parsed["site_in_results"] else "absent")
            print(f"    wooffy: {mark}; cited: {', '.join(parsed['cited_domains']) or '-'}"
                  + (f"; errors: {parsed['errors']}" if parsed["errors"] else ""))
            if not args.no_write:
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(run, indent=1, ensure_ascii=False), encoding="utf-8")
            time.sleep(args.sleep)
        order = {q["id"]: i for i, q in enumerate(panel)}
        run["results"].sort(key=lambda r: order.get(r["id"], 10**6))

    s = summarize(run)
    print()
    print(f"{SITE_DOMAIN} cited in {s['site_cited']}/{s['questions']} ({s['site_cited_pct']}%); "
          f"in results {s['site_in_results']}; target page cited {s['target_page_cited']}; "
          f"searches {s['web_searches']}")
    for g, v in s["by_group"].items():
        print(f"  {g:<10} {v['cited']}/{v['n']}  ({v['cited_pct']}%)")
    print("  top competitors:", ", ".join(f"{d} {n}" for d, n in s["top_competitors"][:8]) or "-")
    if not args.no_write and (args.from_run or not args.group and not args.limit):
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_PATH.write_text(render_md(run, s), encoding="utf-8")
        write_history(s)
        print(f"\nwrote {LATEST_PATH.relative_to(ROOT)} and updated {HISTORY_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
