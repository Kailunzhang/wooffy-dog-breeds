"""Daily orchestrator: feeds -> topic -> article -> review -> hero -> publish -> email.

Usage:
    python3 scripts/reddit_trends/run.py              # full run (publishes)
    python3 scripts/reddit_trends/run.py --dry-run    # everything except Shopify
    python3 scripts/reddit_trends/run.py --topic "crate training a rescue dog at night"
    python3 scripts/reddit_trends/run.py --no-hero --dry-run

Env (same names as the other workflows): SHOPIFY_STORE, SHOPIFY_TOKEN,
SHOPIFY_BLOG_ID, SHOPIFY_<HANDLE>_BLOG_ID (optional per blog),
ANTHROPIC_API_KEY, FAL_KEY (optional), GMAIL_USER, GMAIL_APP_PASSWORD,
ALERT_EMAIL_TO (optional). Reads .env in the repo root as a fallback.

State: reddit-trends-state.json in the repo root (committed by the workflow).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import smtplib
import subprocess
import sys
import traceback
from datetime import date, timedelta
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import feeds  # noqa: E402
import hero as hero_mod  # noqa: E402
import selector  # noqa: E402
import writer  # noqa: E402
from wooffy_links import related_links_html  # noqa: E402

BREED_DATA = ROOT / "breed-data"
STATE_PATH = ROOT / "reddit-trends-state.json"
DRAFT_DIR = ROOT / "output" / "reddit-trends"
SEEN_LIMIT = 3000
RECENT_DAYS = 60
MAX_REVISIONS = 1

# cluster -> preferred blog, with fallback to dog-breeds when the env var is missing
CLUSTER_BLOG = {
    "nutrition": "dog-nutrition",
    "health": "dog-health",
    "training": "dog-training",
    "life": "life-with-dogs",
    "gear": "life-with-dogs",
    "adoption": "life-with-dogs",
    "breeds": "dog-breeds",
}


# ------------------------------------------------------------------ env/state

def load_env() -> dict[str, str]:
    env = dict(os.environ)
    dotenv = ROOT / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    return env


def blog_env_var(handle: str) -> str:
    if handle == "dog-breeds":
        return "SHOPIFY_BLOG_ID"
    return "SHOPIFY_" + handle.upper().replace("-", "_") + "_BLOG_ID"


def resolve_blog(cluster: str, env: dict[str, str]) -> str:
    handle = CLUSTER_BLOG.get(cluster, "dog-breeds")
    if env.get(blog_env_var(handle), "").strip() not in ("", "0"):
        return handle
    return "dog-breeds"


def load_state(path: Path = STATE_PATH) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"picked": [], "seen_ids": []}


def save_state(state: dict, path: Path = STATE_PATH) -> None:
    state["seen_ids"] = state["seen_ids"][-SEEN_LIMIT:]
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def recent_topics(state: dict, today: date, days: int = RECENT_DAYS) -> list[str]:
    cutoff = (today - timedelta(days=days)).isoformat()
    return [p["slug"] for p in state.get("picked", []) if p.get("date", "") >= cutoff]


def shopify_recent_handles(env: dict[str, str], days: int = 30, limit: int = 50) -> list[str]:
    """Handles of articles created recently in every configured blog.

    Second line of defence against duplicates: the repo state can be lost
    (a failed commit-back step published the same topic twice on
    2026-10-13/14), but the live store always knows what went out.
    """
    store, token = env.get("SHOPIFY_STORE", "").strip(), env.get("SHOPIFY_TOKEN", "").strip()
    if not (store and token):
        return []
    import requests  # noqa: WPS433 - optional dependency path

    since = (date.today() - timedelta(days=days)).isoformat() + "T00:00:00Z"
    handles: list[str] = []
    for handle in set(CLUSTER_BLOG.values()):
        blog_id = env.get(blog_env_var(handle), "").strip()
        if blog_id in ("", "0"):
            continue
        try:
            resp = requests.get(
                f"https://{store}/admin/api/2024-01/blogs/{blog_id}/articles.json",
                params={"limit": limit, "created_at_min": since, "fields": "handle"},
                headers={"X-Shopify-Access-Token": token}, timeout=30)
            if resp.status_code == 200:
                handles += [a["handle"] for a in resp.json().get("articles", []) if a.get("handle")]
            else:
                print(f"  shopify recent ({handle}): HTTP {resp.status_code}", flush=True)
        except requests.RequestException as exc:
            print(f"  shopify recent ({handle}): {exc}", flush=True)
    return sorted(set(handles))


def manual_topic(text: str, cluster: str, ymyl: bool) -> selector.TopicProposal:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:70]
    return selector.TopicProposal(slug=slug, title=text, angle=text, cluster=cluster,
                                  ymyl=ymyl, source_ids=[], reason="manual override")


# ------------------------------------------------------------------ steps

def pick_topic(args, env, state, today):
    """Return (topic | None, candidate posts, failed feeds)."""
    known = writer.existing_slugs(BREED_DATA)
    if args.topic:
        return manual_topic(args.topic, args.cluster, args.ymyl), [], {}
    print("Fetching feeds…", flush=True)
    fetched = feeds.fetch_all(args.subs.split(","), window=args.window,
                              gap=0 if args.fast else feeds.SECONDS_BETWEEN_FEEDS)
    cands = selector.prefilter(fetched.posts, set(state["seen_ids"]))
    print(f"{len(fetched.posts)} posts, {len(cands)} candidates after prefilter, "
          f"{len(fetched.failed)} feeds failed", flush=True)
    if not cands:
        return None, [], fetched.failed
    live_recent = shopify_recent_handles(env)
    recent = sorted(set(recent_topics(state, today)) | set(live_recent))
    print(f"{len(live_recent)} recent live handles from Shopify, {len(recent)} recent topics total", flush=True)
    prompt = selector.build_selection_prompt(cands, sorted(known | set(live_recent)), recent)
    raw = writer.call_claude(env["ANTHROPIC_API_KEY"], args.model, selector.SELECTION_SYSTEM,
                             prompt, max_tokens=2000)
    topic = selector.choose(selector.parse_selection(raw), known | set(live_recent))
    return topic, cands, fetched.failed


def write_article(args, env, topic, cands):
    """Return (article dict, validation problems, review dict)."""
    known = writer.existing_slugs(BREED_DATA)
    by_id = {p.id: p for p in cands}
    sources = [by_id[i].title for i in topic.source_ids if i in by_id] or [topic.title]
    related = writer.related_candidates(BREED_DATA, topic)
    key, model = env["ANTHROPIC_API_KEY"], args.model
    article = writer.parse_json(writer.call_claude(
        key, model, writer.HOUSE_RULES,
        writer.build_article_prompt(topic, sources, related, date.today().isoformat())))
    review = {"verdict": "pass", "issues": []}
    for _ in range(MAX_REVISIONS + 1):
        problems = writer.validate_article(article, known)
        if topic.ymyl or args.review:
            review = writer.parse_json(writer.call_claude(
                key, model, writer.REVIEW_SYSTEM, writer.build_review_prompt(article), max_tokens=2000))
        issues = list(review.get("issues", [])) if review.get("verdict") != "pass" else []
        if (not problems and not issues) or review.get("verdict") == "block":
            break
        print(f"  revising: {problems + issues}", flush=True)
        article = writer.parse_json(writer.call_claude(
            key, model, writer.HOUSE_RULES, writer.build_revision_prompt(article, issues, problems)))
    return article, writer.validate_article(article, known), review


def publish(slug: str) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), slug, "--publish"],
                          input="YES\n", capture_output=True, text=True, cwd=str(ROOT))
    out = proc.stdout + proc.stderr
    print(out, flush=True)
    ok = proc.returncode == 0 and ("Published ->" in out or "Updated ->" in out)
    url = next((line.split("-> ", 1)[1].split()[0] for line in out.splitlines() if "-> https://" in line), "")
    return ok, url


def send_email(env: dict[str, str], subject: str, body: str) -> None:
    to = env.get("ALERT_EMAIL_TO", "").strip()
    user = env.get("GMAIL_USER", "").strip()
    pw = env.get("GMAIL_APP_PASSWORD", "").strip()
    if not (to and user and pw):
        print("[no email creds - printing summary]\n" + body)
        return
    msg = MIMEMultipart()
    msg["From"], msg["To"], msg["Subject"] = user, to, Header(subject, "utf-8")
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.sendmail(user, [to], msg.as_string())
    print(f"Sent summary to {to}")


# ------------------------------------------------------------------ main

def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="write the JSON but do not publish or upload")
    ap.add_argument("--no-hero", action="store_true", help="skip fal.ai and use the placeholder hero")
    ap.add_argument("--topic", help="skip Reddit and write this topic")
    ap.add_argument("--cluster", default="life", choices=selector.CLUSTERS)
    ap.add_argument("--ymyl", action="store_true", help="force the vet/trainer review pass")
    ap.add_argument("--review", action="store_true", help="run the review pass even for non-YMYL topics")
    ap.add_argument("--subs", default=",".join(feeds.DEFAULT_SUBREDDITS))
    ap.add_argument("--window", default="day", choices=("day", "week"))
    ap.add_argument("--fast", action="store_true", help="no sleep between feeds (tests only)")
    ap.add_argument("--model", default=os.environ.get("REDDIT_TRENDS_MODEL", writer.DEFAULT_MODEL))
    return ap.parse_args(argv)


def build_article_file(topic, article, hero, env):
    blog_handle = resolve_blog(topic.cluster, env)
    known = writer.existing_slugs(BREED_DATA)
    rel = [tuple(r) for r in article.get("related") or [] if r and r[0] in known]
    rel_html = related_links_html(rel) if rel else ""
    data = writer.assemble(topic, article, blog_handle=blog_handle, hero_url=hero.url,
                           hero_alt=hero.alt, related_html=rel_html, source_ids=topic.source_ids)
    return data, blog_handle


def main(argv=None) -> int:
    args = parse_args(argv)
    env = load_env()
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    today = date.today()
    state = load_state()
    report: list[str] = [f"Wooffy 每日热点文章 {today.isoformat()}"]
    status = "no-topic"
    try:
        if not env.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY missing")
        topic, cands, failed = pick_topic(args, env, state, today)
        if failed:
            report.append("抓取失败的板块: " + ", ".join(f"r/{k} ({v})" for k, v in failed.items()))
        state["seen_ids"].extend(p.id for p in cands)
        if topic is None:
            report.append("今天没有可用选题（候选为空或全部已覆盖），未生成文章。")
            save_state(state)
            send_email(env, f"[Wooffy 热点] {today} 无选题", "\n\n".join(report))
            return 0
        report.append(f"选题: {topic.title}\nslug: {topic.slug}\n簇: {topic.cluster}  YMYL: {topic.ymyl}\n原因: {topic.reason}")
        if topic.source_ids:
            report.append("来源帖: " + ", ".join(f"https://redd.it/{i.replace('t3_', '')}" for i in topic.source_ids))

        print(f"Writing article for {topic.slug}…", flush=True)
        article, problems, review = write_article(args, env, topic, cands)
        blocked = review.get("verdict") == "block" or bool(problems)
        if review.get("issues"):
            report.append("审核意见: " + " | ".join(review["issues"]))
        if problems:
            report.append("校验问题: " + " | ".join(problems))

        hero = hero_mod.HeroResult(writer.PLACEHOLDER_HERO, article.get("hero_alt", topic.title), True, "skipped")
        if not args.no_hero and not blocked and not args.dry_run:
            hero = hero_mod.make_hero(topic.slug, article["hero_prompt"], article["hero_alt"],
                                      store=env.get("SHOPIFY_STORE", ""), token=env.get("SHOPIFY_TOKEN", ""))
        report.append(f"配图: {'占位图（需替换）' if hero.is_fallback else hero.url}" + (f"  [{hero.error}]" if hero.error else ""))

        data, blog_handle = build_article_file(topic, article, hero, env)
        data["meta"]["published"] = not blocked
        DRAFT_DIR.mkdir(parents=True, exist_ok=True)
        draft_path = DRAFT_DIR / f"{today.isoformat()}-{topic.slug}.json"
        draft_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        report.append(f"字数: {writer.word_count(article)}  草稿: {draft_path.relative_to(ROOT)}")

        url = ""
        if args.dry_run:
            status = "dry-run"
            report.append("dry-run：未发布。")
        else:
            (BREED_DATA / f"{topic.slug}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            if blocked:
                status = "blocked"
                report.append("审核未通过：已保存为未发布草稿（published:false），没有上线。")
            else:
                ok, url = publish(topic.slug)
                status = "published" if ok else "publish-failed"
                report.append(f"发布: {'成功 ' + url if ok else '失败，见 Actions 日志'}  博客: {blog_handle}")
        state["picked"].append({"date": today.isoformat(), "slug": topic.slug, "title": article["name"],
                                "reddit_ids": topic.source_ids, "published": status == "published", "url": url})
        if not args.dry_run:  # a rehearsal must not hide today's posts from the real run
            save_state(state)
    except Exception:  # noqa: BLE001 - always email the failure
        status = "error"
        report.append("运行出错:\n" + traceback.format_exc()[-1500:])
    report.append("删除/下线：Shopify 后台 → 博客文章 → 搜 slug → 删除；或把 breed-data/<slug>.json 的 published 改为 false 后 --update。")
    send_email(env, f"[Wooffy 热点] {today} {status}", "\n\n".join(report))
    return 0 if status in ("published", "dry-run", "no-topic", "blocked") else 1


if __name__ == "__main__":
    raise SystemExit(main())
