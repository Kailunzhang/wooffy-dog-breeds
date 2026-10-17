"""Write the article with Claude and validate it against Wooffy house rules.

The output JSON mirrors the hub-style guides already in breed-data
(see scripts/generate_reddit_trend_batch_2.py): meta + images + three
sections (intro / care / special) + faq. Related-reading links are NOT
written by the model; it returns slugs and we render them with
wooffy_links so every link is verified to exist.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

from selector import TopicProposal

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_OUTPUT_TOKENS = 20000  # style-heavy HTML runs ~9k tokens per guide; 12k got cut off once
MAX_JSON_RETRIES = 1
CUT_OFF_NUDGE = ("\n\nYour previous reply was cut off before the JSON closed. Make it shorter "
                 "and return one complete JSON object only.")
BAD_JSON_NUDGE = ("\n\nYour previous reply was not valid JSON. Return one complete, valid JSON "
                  "object only, with no text before or after it.")
MIN_WORDS = 1300
MAX_WORDS = 2600
MIN_FAQ = 5

P_STYLE = 'style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 20px 0;"'
H3_STYLE = 'style="font-size:1.15em;font-weight:700;color:#1a1a1a;margin:24px 0 12px 0;"'
LIST_STYLE = 'style="font-size:0.95em;line-height:1.8;color:#6b7177;padding-left:22px;margin:0 0 20px 0;"'
CALLOUT_STYLE = ('style="background:#eff6ff;border-left:4px solid #3b82f6;padding:14px 18px;'
                 'margin:0 0 24px 0;border-radius:6px;"')
PLACEHOLDER_HERO = (
    "https://cdn.shopify.com/s/files/1/0554/5253/2790/files/"
    "keep-double-coated-dogs-cool-in-summer-hero.png?v=1782088032"
)
GUIDE_STYLE = ("professional pet photography, soft natural daylight, magazine-"
               "quality, photorealistic, no humans visible, no text")

_TAG = re.compile(r"<[^>]+>")
_PHONE = re.compile(r"(?<!\d)(?:\+?1[\s().-]*)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)")
_REDDIT = re.compile(r"\b(?:u/|r/|reddit|redditor|subreddit)", re.IGNORECASE)
_BLOCK_WORDS = re.compile(r"\b(?:mg/kg|dosage of|dose of)\b", re.IGNORECASE)

HOUSE_RULES = f"""You write for thewooffy.com, a US dog-owner site. Rules:
- Audience: first-time and everyday US dog owners. Plain English, warm, direct, no fluff, no hype.
- Length: 1,500-2,200 words across three sections, plus 6-7 FAQ pairs (40-90 words each).
- Structure: section "intro" (why this matters, what the guide answers), "care" (the main how-to or explainer, with <h3> subheads, lists and at most one simple table), "special" (mistakes to avoid, when to call a vet or trainer, a short decision checklist).
- HTML only inside section html: <p {P_STYLE}>, <h3 {H3_STYLE}>, <ul {LIST_STYLE}>, <ol {LIST_STYLE}>, <table style=\\"width:100%;border-collapse:collapse;margin:8px 0 20px 0;font-size:0.92em;\\"> with cells padded 10px and 1px #ddd borders, and one optional callout <div {CALLOUT_STYLE}>. Use &ldquo; &rdquo; &rsquo; &mdash; entities, never raw quotes or em dashes inside html strings.
- Health, nutrition, toxins, medication: give general guidance only, never doses, never diagnoses. For emergencies write exactly "contact your veterinarian or an animal poison control center right away". NEVER include any phone number.
- Attribute facts to named bodies (AVMA, AKC, ASPCA, FDA, AAFCO, veterinary behaviorists) without inventing statistics; use ranges and "typically" when unsure. Do not fabricate studies or numbers.
- Never mention Reddit, forums, usernames, or quote anyone. The forum thread is only your signal of what owners ask.
- Training advice is force-free and fear-free (no prong/shock/alpha advice).
- Do not recommend specific products by brand; categories are fine.
- Return JSON only, no markdown fence."""


def existing_slugs(breed_data: Path) -> set[str]:
    return {p.stem for p in breed_data.glob("*.json")}


_BREED_PAGE = re.compile(r"-(?:grooming-guide|first-year-costs|puppy-checklist)$")
_GENERIC_WORDS = {"puppy", "dogs", "guide", "best", "breeds", "with", "your", "what", "when", "how"}
MAX_BREED_PAGES = 2


def related_candidates(breed_data: Path, topic: TopicProposal, limit: int = 14) -> list[tuple[str, str]]:
    """Keyword match so the model can pick related reading from real slugs.

    Per-breed pages (164 checklists, 164 cost guides...) all match generic
    words like "puppy", so they are capped at MAX_BREED_PAGES and ranked
    below topic guides; generic words count less than specific ones.
    """
    words = {w for w in re.findall(r"[a-z]+", (topic.slug + " " + topic.title).lower()) if len(w) > 3}
    scored: list[tuple[float, int, str, str]] = []
    for path in breed_data.glob("*.json"):
        stem = path.stem
        score = sum(0.25 if w in _GENERIC_WORDS else 1.0 for w in words if w in stem)
        if not score:
            continue
        try:
            name = json.loads(path.read_text(encoding="utf-8")).get("meta", {}).get("name", stem)
        except (OSError, ValueError):
            name = stem
        scored.append((score, 1 if _BREED_PAGE.search(stem) else 0, stem, name))
    scored.sort(key=lambda t: (t[1], -t[0], t[2]))
    picked: list[tuple[str, str]] = []
    breed_pages = 0
    for _, is_breed, stem, name in scored:
        if is_breed:
            if breed_pages >= MAX_BREED_PAGES:
                continue
            breed_pages += 1
        picked.append((stem, name))
        if len(picked) >= limit:
            break
    return picked


def build_article_prompt(topic: TopicProposal, sources: list[str],
                         related: list[tuple[str, str]], today: str) -> str:
    rel = "\n".join(f"- {slug}: {name}" for slug, name in related) or "- (none)"
    src = "\n".join(f"- {s}" for s in sources) or "- (none)"
    return f"""TOPIC
slug: {topic.slug}
working title: {topic.title}
angle: {topic.angle}
cluster: {topic.cluster}
date: {today}

WHAT OWNERS ARE ASKING TODAY (signal only, paraphrased titles; do not quote or cite):
{src}

RELATED ARTICLES YOU MAY LINK (pick 3-5 slugs from this list only):
{rel}

Return this JSON object:
{{
  "name": "final H1 title, 50-70 chars, no clickbait",
  "title_tag": "SEO title, max 60 chars",
  "meta_description": "max 155 chars",
  "excerpt": "one sentence, max 160 chars",
  "tagline": "one sentence under the title",
  "tags": ["5-8 lowercase tags"],
  "sections": {{
    "intro":   {{"label": "2-3 words", "heading": "...", "html": "..."}},
    "care":    {{"label": "2-3 words", "heading": "...", "html": "..."}},
    "special": {{"label": "2-3 words", "heading": "...", "html": "..."}}
  }},
  "faq": [{{"q": "...", "a": "..."}}],
  "related": [["slug", "link text"]],
  "hero_prompt": "one sentence describing a photorealistic hero image for this guide, no text in image, no humans",
  "hero_alt": "descriptive alt text ending with the guide topic"
}}"""


@dataclass(frozen=True)
class ClaudeReply:
    """One Messages API reply: its text, why it stopped, and how long it was."""
    text: str
    stop_reason: str
    output_tokens: int


def call_claude(api_key: str, model: str, system: str, user: str,
                max_tokens: int = MAX_OUTPUT_TOKENS) -> ClaudeReply:
    resp = requests.post(
        API_URL,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": model, "max_tokens": max_tokens, "system": system,
              "messages": [{"role": "user", "content": user}]},
        timeout=600,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Claude API {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    text = "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text")
    usage = body.get("usage") or {}
    return ClaudeReply(text, str(body.get("stop_reason") or ""), int(usage.get("output_tokens") or 0))


def _parse_reply(reply: ClaudeReply, required: tuple[str, ...]) -> tuple[dict | None, str]:
    """Return (parsed object, "") or (None, why the reply cannot be used)."""
    tail = f"after {reply.output_tokens} tokens ({reply.stop_reason})"
    if reply.stop_reason == "max_tokens":
        return None, f"output cut off {tail}"
    try:
        data = parse_json(reply.text)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON {tail}: {exc}"
    if not isinstance(data, dict):
        return None, f"JSON is not an object {tail}"
    missing = [key for key in required if key not in data]
    if missing:
        return None, f"JSON missing {', '.join(missing)} {tail}"
    return data, ""


def generate_json(api_key: str, model: str, system: str, user: str,
                  max_tokens: int = MAX_OUTPUT_TOKENS, required: tuple[str, ...] = (),
                  retries: int = MAX_JSON_RETRIES) -> tuple[dict, list[ClaudeReply]]:
    """Ask Claude for a JSON object and parse it, retrying when the reply is unusable.

    Unusable: cut off at max_tokens, not valid JSON, not an object, missing a
    `required` key, or lost to a timeout / connection error. Returns the parsed
    object plus every reply made, so callers can report token usage.
    """
    replies: list[ClaudeReply] = []
    problems: list[str] = []
    prompt = user
    for _ in range(max(retries, 0) + 1):
        try:
            reply = call_claude(api_key, model, system, prompt, max_tokens=max_tokens)
        except (requests.Timeout, requests.ConnectionError) as exc:
            problems.append(f"{type(exc).__name__} while calling Claude")
            print(f"  Claude call failed: {problems[-1]}", flush=True)
            continue  # same prompt again
        replies.append(reply)
        data, problem = _parse_reply(reply, required)
        if data is not None:
            return data, replies
        problems.append(problem)
        print(f"  Claude reply unusable: {problem}", flush=True)
        prompt = user + (CUT_OFF_NUDGE if reply.stop_reason == "max_tokens" else BAD_JSON_NUDGE)
    raise RuntimeError(f"Claude JSON unusable after {len(problems)} attempts: " + " | ".join(problems))


def usage_line(calls: list[tuple[str, ClaudeReply]]) -> str:
    """One email line such as '文章 9120 tok (end_turn) | 审核 180 tok (end_turn)'."""
    return " | ".join(f"{label} {r.output_tokens} tok ({r.stop_reason})" for label, r in calls)


def parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def article_text(article: dict) -> str:
    parts = [sec.get("html", "") for sec in (article.get("sections") or {}).values()]
    parts += [f"{f.get('q','')} {f.get('a','')}" for f in (article.get("faq") or [])]
    return _TAG.sub(" ", " ".join(parts))


def word_count(article: dict) -> int:
    return len(article_text(article).split())


def validate_article(article: dict, known_slugs: set[str]) -> list[str]:
    """Return a list of problems; empty list means the article may ship."""
    problems: list[str] = []
    for key in ("name", "title_tag", "meta_description", "excerpt", "sections", "faq", "hero_prompt", "hero_alt"):
        if not article.get(key):
            problems.append(f"missing {key}")
    sections = article.get("sections") or {}
    for key in ("intro", "care", "special"):
        sec = sections.get(key) or {}
        if not (sec.get("label") and sec.get("heading") and sec.get("html")):
            problems.append(f"section {key} incomplete")
    if len(article.get("faq") or []) < MIN_FAQ:
        problems.append(f"fewer than {MIN_FAQ} FAQ entries")
    words = word_count(article)
    if words < MIN_WORDS:
        problems.append(f"too short: {words} words")
    if words > MAX_WORDS:
        problems.append(f"too long: {words} words")
    text = article_text(article) + " " + json.dumps(article.get("faq", []))
    if _PHONE.search(text):
        problems.append("contains a phone number")
    if _REDDIT.search(text):
        problems.append("mentions reddit/forum/usernames")
    if _BLOCK_WORDS.search(text):
        problems.append("contains dosing language")
    if len(article.get("title_tag", "")) > 70:
        problems.append("title_tag over 70 chars")
    if len(article.get("meta_description", "")) > 170:
        problems.append("meta_description over 170 chars")
    for item in article.get("related") or []:
        if not (isinstance(item, list) and len(item) == 2):
            problems.append("related entry malformed")
        elif item[0] not in known_slugs:
            problems.append(f"related slug does not exist: {item[0]}")
    return problems


REVIEW_SYSTEM = (
    "You are a US veterinarian and a certified force-free dog trainer reviewing "
    "a consumer article before publication. Flag anything medically wrong, "
    "dangerous, dose-specific, diagnostic, fear/force-based, or that overstates "
    "certainty. Answer with JSON only: "
    '{"verdict": "pass" | "fix" | "block", "issues": ["..."]}. '
    "Use \"block\" only for advice that could harm a dog if followed; use "
    "\"fix\" for problems a rewrite can solve; \"pass\" if safe to publish."
)


def build_review_prompt(article: dict) -> str:
    return "ARTICLE JSON:\n" + json.dumps(article, ensure_ascii=False)


def build_revision_prompt(article: dict, issues: list[str], problems: list[str]) -> str:
    notes = "\n".join(f"- {i}" for i in issues + problems)
    return ("Revise the article JSON below to fix every note. Keep the same JSON "
            "shape, keys and style rules. Return JSON only.\n\nNOTES:\n" + notes +
            "\n\nARTICLE JSON:\n" + json.dumps(article, ensure_ascii=False))


def assemble(topic: TopicProposal, article: dict, *, blog_handle: str,
             hero_url: str, hero_alt: str, related_html: str,
             source_ids: list[str], now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    published_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    sections = {k: dict(v) for k, v in article["sections"].items()}
    sections["special"]["html"] = sections["special"]["html"] + related_html
    return {
        "meta": {
            "name": article["name"],
            "slug": topic.slug,
            "shopify_handle": topic.slug,
            "blog_handle": blog_handle,
            "group": "Trending Guides",
            "size_category": "Guide",
            "tagline": article.get("tagline", ""),
            "tags": list(article.get("tags") or []),
            "published": True,
            "published_at": published_at,
            "excerpt": article["excerpt"],
            "meta_description": article["meta_description"],
            "title_tag": article["title_tag"],
        },
        "images": {"hero": {"url": hero_url, "alt": hero_alt}},
        "sections": sections,
        "faq": list(article.get("faq") or []),
        "source": {
            "pipeline": "reddit_trends",
            "selected_at": published_at,
            "cluster": topic.cluster,
            "reddit_ids": list(source_ids),
            "angle": topic.angle,
        },
    }
