"""Weekly SEO auto-fix: propose meta-description rewrites as a PR.

Pulls GSC CTR opportunities (via seo_report), keeps only pages whose
source lives in this repo (breed-data/<slug>.json under
/blogs/dog-breeds/), asks Claude to rewrite the SERP meta description
to lift CTR for the page's best query, writes a minimal one-field
edit per file, and opens ONE pull request. Merging the PR is the
approval; a separate deploy workflow pushes merged changes to Shopify.

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
META_MAX = 160


def _slug_of(page_url):
    path = re.sub(r"^https?://[^/]+", "", page_url)
    if "/blogs/dog-breeds/" not in path:
        return None
    return path.rstrip("/").split("/")[-1] or None


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
        slug = _slug_of(page)
        if not slug or not os.path.isfile(
                os.path.join(BREED_DIR, f"{slug}.json")):
            if "/blogs/dog-breeds/" not in page:  # not ours to edit
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
    return ranked[:MAX_FIXES], ext, state


def _anthropic(name, excerpt, old_desc, query):
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None
    prompt = (
        "Rewrite the Google search meta description for a dog blog "
        "article so it earns more clicks for a specific query.\n\n"
        f"Article title: {name}\n"
        f"Article summary: {excerpt}\n"
        f"Current meta description: {old_desc}\n"
        f"Target search query: {query}\n\n"
        "Rules: 140-158 characters; one line; American English; "
        "directly speak to the query intent; specific and compelling "
        "but never clickbait; no fabricated facts, numbers, or claims; "
        "no surrounding quotes. Output ONLY the new meta description."
    )
    body = json.dumps({
        "model": ANTHROPIC_MODEL, "max_tokens": 256,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                 body, method="POST")
    req.add_header("x-api-key", key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    text = "".join(b.get("text", "") for b in resp.get("content", []))
    text = " ".join(text.strip().strip('"').split())
    if not text or len(text) > META_MAX + 15:
        return None
    return text


def _apply_edit(slug, new_desc):
    """Surgical replace of only meta_description; minimal diff."""
    path = os.path.join(BREED_DIR, f"{slug}.json")
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    data = json.loads(raw)
    old = data.get("meta", {}).get("meta_description")
    if old is None:
        return None
    old_tok = json.dumps(old, ensure_ascii=False)
    new_tok = json.dumps(new_desc, ensure_ascii=False)
    if raw.count(old_tok) != 1:
        return None  # ambiguous; skip rather than risk a messy diff
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(raw.replace(old_tok, new_tok, 1))
    return old


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
    picks, external, state = candidates(token)
    dry = os.environ.get("SEO_AUTOFIX_DRY") == "1" \
        or not os.environ.get("GITHUB_TOKEN")

    if dry:
        print(f"[dry-run] {len(picks)} repo candidates, "
              f"{len(external)} external opportunities")
        for c in picks:
            print(f"  · {c['slug']}  «{c['query']}»  pos {c['position']:.1f}"
                  f" · {c['impressions']} impr · CTR {c['ctr']*100:.2f}%")
        for p, v in external[:5]:
            print(f"  (ext) {p}  «{v['query']}»  {v['impressions']} impr")

    rows, today = [], date.today().isoformat()
    for c in picks:
        path = os.path.join(BREED_DIR, f"{c['slug']}.json")
        meta = json.load(open(path, encoding="utf-8"))["meta"]
        new = _anthropic(meta.get("name", c["slug"]),
                         meta.get("excerpt", ""),
                         meta.get("meta_description", ""), c["query"])
        if not new:
            continue
        if dry:
            rows.append((c, meta.get("meta_description", ""), new))
            continue
        old = _apply_edit(c["slug"], new)
        if old is None:
            continue
        state[c["slug"]] = today
        rows.append((c, old, new))

    if not rows:
        print("No actionable fixes this run.")
        return

    if dry:
        for c, old, new in rows:
            print(f"\n{c['slug']}  «{c['query']}»  "
                  f"pos {c['position']:.1f} · {c['impressions']} impr · "
                  f"CTR {c['ctr']*100:.2f}%")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
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
         *[f"breed-data/{c['slug']}.json" for c, _, _ in rows])
    _git("commit", "-m",
         f"seo-autofix: {len(rows)} meta-description rewrites ({today})")
    _git("push", "-f", "origin", branch)

    tbl = ["| 页面 | 目标查询 | 曝光 | 排名 | 旧描述 → 新描述 |",
           "|---|---|---|---|---|"]
    for c, old, new in rows:
        tbl.append(f"| `{c['slug']}` | {c['query']} | {c['impressions']} | "
                   f"{c['position']:.1f} | ~~{old[:80]}~~ → **{new}** |")
    appx = "\n".join(
        f"- [ ] `{p}` — 「{v['query']}」({v['impressions']} 曝光，"
        f"第 {v['position']:.1f} 名) — 不在仓库，需到 Shopify 手动改"
        for p, v in external)
    body = (
        f"自动生成的 SEO meta description 优化（{today}）。\n\n"
        "**审核 = 合并。** 合并到 main 后会自动只对这些 slug 跑 "
        "`generate.py --update` 推到 Shopify。逐条看下面新旧对比，不满意"
        "就直接在本 PR 改文件或关掉。\n\n" + "\n".join(tbl) +
        ("\n\n### 仓库外机会（自动改不到，手动处理）\n\n" + appx
         if appx else ""))
    url = _open_pr(branch, f"🔎 SEO 自动优化 · {len(rows)} 条 · {today}", body)
    print(f"PR opened: {url}")


if __name__ == "__main__":
    main()
