"""Weekly SEO auto-fix: propose title + meta-description rewrites as a PR.

Pulls GSC CTR opportunities (via seo_report), filters scraper-noise
queries, keeps only pages whose source lives in this repo
(breed-data/<slug>.json under /blogs/dog-breeds/), asks Claude to
rewrite BOTH the SERP title (meta.name) and meta description to lift
CTR for the page's best query, writes a surgical two-field edit per
file (skipping any page where a token isn't uniquely placed), and
opens ONE pull request. Merging the PR is the approval; a separate
deploy workflow pushes merged changes to Shopify.

Never auto-merges. Caps fixes/run. Skips pages fixed within the
cooldown. State in seo_autofix_state.json.

Env: GA4_OAUTH_* + GSC_SITE_URL (GSC, via seo_report),
     ANTHROPIC_API_KEY (+ optional ANTHROPIC_MODEL),
     GITHUB_TOKEN + GITHUB_REPOSITORY (provided by Actions).
Set SEO_AUTOFIX_DRY=1 to select + print without git/PR.
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_report as seo  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BREED_DIR = os.path.join(REPO, "breed-data")
STATE_PATH = os.path.join(REPO, "seo_autofix_state.json")

MAX_FIXES = 5
MIN_IMPR = 80              # 28-day impressions to qualify
MAX_POS = 20.0             # a better snippet can still help on page 2
CTR_RATIO = 0.6            # ctr below 60% of positional norm = opportunity
COOLDOWN_DAYS = 21
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
TITLE_MIN, TITLE_MAX = 30, 75   # lenient; Google shows ~55-60 chars
META_MIN, META_MAX = 120, 170   # 120 mobile-safe, 158 desktop, buffer ok

# Cannibalization detection (a query where >=2 thewooffy URLs compete with
# material impressions and no single URL dominates). Surfaced in the PR for
# human judgment (canonical / consolidation) - autofix cannot resolve these.
CANNI_MIN_IMPR_PER_URL = 20
CANNI_MAX_DOMINANCE = 0.80   # skip if top URL holds more than this share
MAX_CANNI = 6

# Scraper / branded / dated junk queries to ignore — wastes LLM calls
# and produces weird titles. Tune as more noise appears in GSC.
_NOISE_BRANDS = ("highland canine", "akc.org", "petfinder",
                 "rover.com", "wisdom panel", "embark vet")
_NOISE_YEAR = re.compile(r"\b20\d{2}\b")


def _query_ok(q):
    s = (q or "").lower().strip()
    if len(s.split()) > 8:
        return False
    if _NOISE_YEAR.search(s):
        return False
    return not any(b in s for b in _NOISE_BRANDS)


# Blogs whose articles are stored in this repo (breed-data/<slug>.json) and
# can therefore be auto-edited. Pages outside these blogs become "external"
# opportunities the human must handle in Shopify.
SUPPORTED_BLOGS = ("dog-breeds", "dog-nutrition")


def _slug_of(page_url):
    path = re.sub(r"^https?://[^/]+", "", page_url)
    for blog in SUPPORTED_BLOGS:
        if f"/blogs/{blog}/" in path:
            return path.rstrip("/").split("/")[-1] or None
    return None


def _load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def candidates(token):
    end = date.today() - timedelta(days=seo.DATA_LAG_DAYS)
    start = end - timedelta(days=seo.CONTEXT_DAYS - 1)
    rows = seo._q(token, start, end, ["query", "page"], 5000)
    state = _load_state()
    cutoff = (datetime.now(timezone.utc).replace(tzinfo=None)
              - timedelta(days=COOLDOWN_DAYS)).date()

    best, external = {}, {}
    for r in rows:
        q, page = r["keys"]
        pos, impr, ctr = r["position"], r["impressions"], r["ctr"]
        if impr < MIN_IMPR or pos > MAX_POS:
            continue
        if ctr >= CTR_RATIO * seo._exp_ctr(pos):
            continue
        if not _query_ok(q):
            continue
        slug = _slug_of(page)
        if not slug or not os.path.isfile(
                os.path.join(BREED_DIR, f"{slug}.json")):
            # Outside our supported blogs OR missing local file ->
            # surface as external opportunity for manual handling.
            if not any(f"/blogs/{b}/" in page for b in SUPPORTED_BLOGS):
                cur = external.get(page)
                if not cur or impr > cur["impressions"]:
                    external[page] = {"query": q, "impressions": impr,
                                      "position": pos}
            continue
        last = state.get(slug)
        if last and datetime.fromisoformat(last).date() > cutoff:
            continue
        cur = best.get(slug)
        if not cur or impr > cur["impressions"]:
            best[slug] = {"slug": slug, "page": page, "query": q,
                          "impressions": impr, "position": pos, "ctr": ctr}
    ranked = sorted(best.values(), key=lambda x: -x["impressions"])
    ext = sorted(external.items(), key=lambda kv: -kv[1]["impressions"])[:10]
    return ranked[:MAX_FIXES], ext, state, rows


def _cannibalization(rows: list) -> list[dict]:
    """Detect queries where >=2 thewooffy.com URLs compete with material
    impressions and no single URL dominates. Returned for human judgment
    (canonical / noindex / content consolidation) - autofix can't fix
    these via title+meta alone.

    Each entry: {"query": str, "total": int,
                 "urls": [{"page", "impressions", "position", "clicks"}]}
    Sorted by total impressions descending, capped at MAX_CANNI.
    """
    by_query: dict[str, list[dict]] = {}
    for r in rows:
        q, page = r["keys"]
        if not _query_ok(q):
            continue
        if "thewooffy.com" not in page:
            continue
        if r["impressions"] < CANNI_MIN_IMPR_PER_URL:
            continue
        by_query.setdefault(q, []).append({
            "page": page,
            "impressions": r["impressions"],
            "position": r["position"],
            "clicks": r["clicks"],
        })

    out: list[dict] = []
    for q, urls in by_query.items():
        if len(urls) < 2:
            continue
        urls.sort(key=lambda u: -u["impressions"])
        total = sum(u["impressions"] for u in urls)
        if total and urls[0]["impressions"] / total > CANNI_MAX_DOMINANCE:
            continue   # one URL dominates -> not really cannibalized
        out.append({"query": q, "urls": urls, "total": total})

    out.sort(key=lambda c: -c["total"])
    return out[:MAX_CANNI]


def _title_safe(new_title, old_title):
    """Reject titles that drop the article's primary subject word
    (anti-drift guard: e.g., never turn 'Goldendoodle' into something
    that doesn't contain it). Lenient on very short old titles."""
    candidates = [w for w in re.findall(r"[A-Za-z]+", old_title or "")
                  if len(w) >= 4]
    if not candidates:
        return True
    longest = max(candidates, key=len)
    return longest.lower() in (new_title or "").lower()


def _rewrite(excerpt, old_title, old_desc, query):
    """Ask Claude for a (title, meta_description) pair targeting the
    query. Returns the pair, or None on any failure / out-of-spec output.
    """
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None
    prompt = (
        "You are rewriting a dog blog article's Google SERP snippet "
        "(page title + meta description) to earn more clicks for a "
        "specific search query.\n\n"
        f"Current title: {old_title}\n"
        f"Current meta description: {old_desc}\n"
        f"Article summary: {excerpt}\n"
        f"Target search query: {query}\n\n"
        "Rules:\n"
        f"- title: {TITLE_MIN}-{TITLE_MAX} chars; keep the article's "
        "primary subject (e.g., the breed name) verbatim; weave the "
        "query (or a close natural variant) in near the front; "
        "specific and click-worthy, never clickbait; American "
        "English; no surrounding quotes; no trailing brand suffix.\n"
        f"- meta_description: {META_MIN}-{META_MAX} chars; speak "
        "directly to the query intent; specific and compelling, "
        "never clickbait; no fabricated facts, numbers, or claims; "
        "no surrounding quotes.\n"
        "- Do not invent facts not in the summary.\n\n"
        'Output ONLY a single-line JSON object, no commentary:\n'
        '{"title": "...", "meta_description": "..."}'
    )
    body = json.dumps({
        "model": ANTHROPIC_MODEL, "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                 body, method="POST")
    req.add_header("x-api-key", key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    text = "".join(b.get("text", "") for b in resp.get("content", [])).strip()
    # Strip ```json ... ``` fences if Claude wrapped its output.
    if text.startswith("```"):
        text = re.sub(r"^```[A-Za-z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        obj = json.loads(text)
        title = " ".join(str(obj["title"]).strip().strip('"').split())
        desc = " ".join(str(obj["meta_description"]).strip().strip('"').split())
    except Exception as e:
        print(f"    ! LLM parse failed ({e}); raw: {text[:140]!r}")
        return None
    if not (TITLE_MIN <= len(title) <= TITLE_MAX):
        print(f"    ! title {len(title)}ch outside [{TITLE_MIN},{TITLE_MAX}]"
              f": {title!r}")
        return None
    if not (META_MIN <= len(desc) <= META_MAX):
        print(f"    ! meta {len(desc)}ch outside [{META_MIN},{META_MAX}]"
              f": {desc!r}")
        return None
    if not _title_safe(title, old_title):
        print(f"    ! anti-drift: new title lost subject of "
              f"{old_title!r}: {title!r}")
        return None
    return title, desc


def _apply_edit(slug, new_title, new_desc):
    """Surgical replace of meta.name + meta.meta_description (+ optionally
    meta.title_tag, when present). Minimal diff. Skips (returns None) if
    either of the required fields is missing or its JSON-encoded token
    isn't uniquely placed in the raw file.

    title_tag is the SERP-displayed title metafield (Shopify
    global.title_tag); when set (e.g. imported nutrition articles) we sync
    it to the new title so Google actually shows the rewritten copy.
    """
    path = os.path.join(BREED_DIR, f"{slug}.json")
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    data = json.loads(raw)
    meta = data.get("meta", {})
    old_title = meta.get("name")
    old_desc = meta.get("meta_description")
    if old_title is None or old_desc is None:
        return None
    o_t = json.dumps(old_title, ensure_ascii=False)
    n_t = json.dumps(new_title, ensure_ascii=False)
    o_d = json.dumps(old_desc, ensure_ascii=False)
    n_d = json.dumps(new_desc, ensure_ascii=False)
    if raw.count(o_t) != 1 or raw.count(o_d) != 1:
        return None
    new_raw = raw.replace(o_t, n_t, 1).replace(o_d, n_d, 1)

    # Optional sync: SERP title_tag metafield -> new title.
    old_title_tag = meta.get("title_tag")
    if old_title_tag and old_title_tag != new_title:
        o_tt = json.dumps(old_title_tag, ensure_ascii=False)
        n_tt = json.dumps(new_title, ensure_ascii=False)
        if new_raw.count(o_tt) == 1:
            new_raw = new_raw.replace(o_tt, n_tt, 1)
        # else: title_tag token not uniquely placeable; leave it, the
        # required name+meta edits still apply. (Quiet skip is fine —
        # this field is best-effort.)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_raw)
    return old_title, old_desc


def _git(*args):
    subprocess.run(["git", *args], cwd=REPO, check=True)


def _open_pr(branch, title, body):
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]
    payload = json.dumps({"title": title, "head": branch, "base": "main",
                          "body": body}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls", payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "wooffy-seo-bot")
    return json.loads(urllib.request.urlopen(req).read()).get("html_url")


def main():
    token = seo._access_token()
    picks, external, state, rows = candidates(token)
    canni = _cannibalization(rows)
    dry = os.environ.get("SEO_AUTOFIX_DRY") == "1" \
        or not os.environ.get("GITHUB_TOKEN")

    if dry:
        print(f"[dry-run] {len(picks)} repo candidates, "
              f"{len(external)} external opportunities, "
              f"{len(canni)} cannibalization candidates")
        for c in picks:
            print(f"  · {c['slug']}  «{c['query']}»  pos {c['position']:.1f}"
                  f" · {c['impressions']} impr · CTR {c['ctr']*100:.2f}%")
        for p, v in external[:5]:
            print(f"  (ext) {p}  «{v['query']}»  {v['impressions']} impr")
        for cn in canni:
            print(f"  (canni) «{cn['query']}»  total {cn['total']} impr "
                  f"across {len(cn['urls'])} URLs")

    rows, today = [], date.today().isoformat()
    for c in picks:
        print(f"\n→ {c['slug']}  «{c['query']}»  pos {c['position']:.1f}"
              f" · CTR {c['ctr']*100:.2f}%")
        path = os.path.join(BREED_DIR, f"{c['slug']}.json")
        meta = json.load(open(path, encoding="utf-8"))["meta"]
        old_title = meta.get("name", "")
        old_desc = meta.get("meta_description", "")
        new = _rewrite(meta.get("excerpt", ""), old_title, old_desc,
                       c["query"])
        if not new:
            continue
        new_title, new_desc = new
        if dry:
            rows.append((c, old_title, old_desc, new_title, new_desc))
            continue
        edited = _apply_edit(c["slug"], new_title, new_desc)
        if edited is None:
            print(f"    ! apply_edit skipped (ambiguous token or missing "
                  f"meta field)")
            continue
        state[c["slug"]] = today
        rows.append((c, edited[0], edited[1], new_title, new_desc))

    if not rows:
        print("No actionable fixes this run.")
        if canni:
            print(f"({len(canni)} cannibalization candidate(s) detected — "
                  f"see dry-run output above; PR was not opened because "
                  f"no title/meta rewrites passed validation.)")
        return

    if dry:
        for c, ot, od, nt, nd in rows:
            print(f"\n{c['slug']}  «{c['query']}»  "
                  f"pos {c['position']:.1f} · {c['impressions']} impr · "
                  f"CTR {c['ctr']*100:.2f}%")
            print(f"  TITLE  OLD: {ot}")
            print(f"         NEW: {nt}")
            print(f"  META   OLD: {od}")
            print(f"         NEW: {nd}")
        print(f"\n[dry-run] {len(rows)} edits; "
              f"{len(external)} external (manual) opportunities.")
        return

    with open(STATE_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    branch = f"seo-autofix/{today}"
    _git("config", "user.email", "seo-bot@users.noreply.github.com")
    _git("config", "user.name", "wooffy-seo-bot")
    _git("checkout", "-B", branch)
    _git("add", "seo_autofix_state.json",
         *[f"breed-data/{c['slug']}.json" for c, *_ in rows])
    _git("commit", "-m",
         f"seo-autofix: {len(rows)} title+meta rewrites ({today})")
    _git("push", "-f", "origin", branch)

    blocks = []
    for i, (c, ot, od, nt, nd) in enumerate(rows, 1):
        blocks.append(
            f"### {i}. `{c['slug']}` · 「{c['query']}」"
            f"（{c['impressions']} 曝光 · 第 {c['position']:.1f} 名 · "
            f"CTR {c['ctr']*100:.2f}%）\n\n"
            f"- **Title** ~~{ot}~~ → **{nt}**\n"
            f"- **Meta** ~~{od}~~ → **{nd}**"
        )
    appx = "\n".join(
        f"- [ ] `{p}` — 「{v['query']}」({v['impressions']} 曝光，"
        f"第 {v['position']:.1f} 名) — 不在仓库，需到 Shopify 手动改"
        for p, v in external)

    canni_section = ""
    if canni:
        parts = []
        for i, cn in enumerate(canni, 1):
            urls_md = "\n".join(
                f"- `{u['page'].replace('https://www.thewooffy.com','').replace('https://thewooffy.com','')}`"
                f" · 第 {u['position']:.1f} 名 · {u['impressions']} 曝光 · "
                f"{u['clicks']} 点击"
                for u in cn["urls"]
            )
            parts.append(
                f"#### {i}. 「{cn['query']}」"
                f"（总 {cn['total']} 曝光 · {len(cn['urls'])} 个 URL）"
                f"\n\n{urls_md}"
            )
        canni_section = (
            "\n\n---\n### 🔀 内部相残（一个查询词被多页争夺，"
            "需人工判断 canonical / noindex / 内容合并）\n\n"
            + "\n\n".join(parts)
        )

    body = (
        f"自动生成的 SEO 标题 + meta description 优化（{today}）。\n\n"
        "**审核 = 合并。** 合并到 main 后会自动只对这些 slug 跑 "
        "`generate.py --update` 推到 Shopify。逐条看下面新旧对比，不满意"
        "就在本 PR 直接改文件或关掉。\n\n" + "\n\n".join(blocks)
        + canni_section
        + ("\n\n---\n### 仓库外机会（自动改不到，手动处理）\n\n" + appx
           if appx else ""))
    url = _open_pr(branch, f"🔎 SEO 自动优化 · {len(rows)} 条 · {today}", body)
    print(f"PR opened: {url}")


if __name__ == "__main__":
    main()
