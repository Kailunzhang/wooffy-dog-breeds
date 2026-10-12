"""Turn today's Reddit posts into ONE article topic the site does not have.

Two stages:
1. ``prefilter`` — pure Python. Drops photo posts, megathreads, grief,
   lost/found, rehoming, fundraising and anything already seen.
2. ``build_selection_prompt`` / ``parse_selection`` — Claude ranks the
   survivors against the list of existing article slugs and proposes up
   to three evergreen guide topics. ``choose`` takes the first proposal
   whose slug is new.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict

from feeds import Post

EXCLUDE_PATTERNS = [
    r"\bmegathread\b",
    r"\beuthan",
    r"\brip\b",
    r"passed away",
    r"\bcrossed the rainbow\b",
    r"\blost (my )?dog\b",
    r"\bfound (a |this )?dog\b",
    r"\brehom",
    r"\bgofundme\b",
    r"\bdonat",
    r"\bfundrais",
    r"\bstartup\b",
    r"\bsurvey\b",
    r"\bgiveaway\b",
    r"\bfor sale\b",
]
_EXCLUDE = re.compile("|".join(EXCLUDE_PATTERNS), re.IGNORECASE)
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,11}$")

CLUSTERS = ("training", "health", "nutrition", "life", "gear", "breeds", "adoption")
MAX_CANDIDATES = 60


@dataclass
class TopicProposal:
    slug: str
    title: str
    angle: str
    cluster: str
    ymyl: bool
    source_ids: list[str]
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def is_excluded(post: Post) -> bool:
    return bool(_EXCLUDE.search(post.title)) or bool(_EXCLUDE.search(post.text[:400]))


def prefilter(posts: list[Post], seen_ids: set[str]) -> list[Post]:
    keep: list[Post] = []
    for post in posts:
        if post.id in seen_ids or not post.is_text_post or is_excluded(post):
            continue
        if len(post.title) < 12:
            continue
        keep.append(post)
    # Longer self-text usually means a richer question; keep the prompt bounded.
    keep.sort(key=lambda p: len(p.text), reverse=True)
    return keep[:MAX_CANDIDATES]


SELECTION_SYSTEM = (
    "You are the content editor of thewooffy.com, a US dog-owner site with "
    "breed guides, first-year cost guides, grooming guides, puppy checklists, "
    "nutrition ('can dogs eat X') and life-with-dogs guides. You read today's "
    "most-upvoted dog-forum questions and pick evergreen guide topics the "
    "site does not have yet. You never reproduce forum text; you only use it "
    "as a signal of what owners are asking. Answer with JSON only."
)


def build_selection_prompt(cands: list[Post], existing_slugs: list[str],
                           recent_topics: list[str]) -> str:
    lines = [
        "TODAY'S TOP FORUM QUESTIONS (id | subreddit | title | snippet):",
    ]
    for p in cands:
        lines.append(f"- {p.id} | r/{p.subreddit} | {p.title} | {p.snippet(220)}")
    lines += [
        "",
        f"TOPICS ALREADY PUBLISHED IN THE LAST 60 DAYS: {', '.join(recent_topics) or 'none'}",
        "",
        "EXISTING ARTICLE SLUGS ON THE SITE (do not duplicate these topics):",
        ", ".join(sorted(existing_slugs)),
        "",
        "TASK: propose up to 3 article topics, best first. Each must:",
        "- be an evergreen how-to or explainer a US dog owner would Google "
        "(not a one-off story, not breed-identification, not a product review)",
        "- be clearly NOT already covered by an existing slug",
        "- be answerable responsibly without giving veterinary diagnoses",
        "- be supported by at least one of today's questions (list their ids)",
        "",
        "Return JSON: {\"proposals\": [{\"slug\": \"kebab-case-5-to-9-words\", "
        "\"title\": \"...\", \"angle\": \"one sentence on what the guide covers\", "
        f"\"cluster\": one of {list(CLUSTERS)}, \"ymyl\": true if health/nutrition/"
        "medication/toxins, \"source_ids\": [\"t3_...\"], \"reason\": \"why it is hot "
        "today\"}]}",
    ]
    return "\n".join(lines)


def _strip_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw


def parse_selection(raw: str) -> list[TopicProposal]:
    data = json.loads(_strip_fence(raw))
    proposals: list[TopicProposal] = []
    for item in data.get("proposals", []):
        slug = str(item.get("slug", "")).strip().lower()
        cluster = str(item.get("cluster", "life")).strip().lower()
        if not _SLUG.match(slug):
            continue
        if cluster not in CLUSTERS:
            cluster = "life"
        proposals.append(TopicProposal(
            slug=slug,
            title=str(item.get("title", "")).strip(),
            angle=str(item.get("angle", "")).strip(),
            cluster=cluster,
            ymyl=bool(item.get("ymyl", False)),
            source_ids=[str(s) for s in item.get("source_ids", [])],
            reason=str(item.get("reason", "")).strip(),
        ))
    return proposals


def choose(proposals: list[TopicProposal], existing_slugs: set[str]) -> TopicProposal | None:
    for prop in proposals:
        if prop.slug in existing_slugs or not prop.title:
            continue
        return prop
    return None
