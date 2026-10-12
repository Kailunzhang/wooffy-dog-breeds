"""Fetch and parse Reddit's public Atom feeds.

Reddit serves ``https://www.reddit.com/r/<sub>/top/.rss?t=day`` without
authentication but rate-limits unauthenticated clients to roughly one
request per minute (``x-ratelimit-remaining: 0`` after a single hit,
``x-ratelimit-reset`` ~60s). So every feed fetch sleeps before the next
one and a 429 is retried after the reset window. Only titles and the
poster's own text are read; nothing from Reddit is reproduced in the
articles (see writer.py house rules).
"""
from __future__ import annotations

import html
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)
ATOM_NS = "{http://www.w3.org/2005/Atom}"

DEFAULT_SUBREDDITS = (
    "dogs",
    "puppy101",
    "DogAdvice",
    "Dogtraining",
    "OpenDogTraining",
    "reactivedogs",
    "DogFood",
)
# Reddit's unauthenticated window is ~60s. 65s keeps a little margin.
SECONDS_BETWEEN_FEEDS = 65
MAX_RETRIES = 2
MIN_TEXT_CHARS = 150  # below this the entry is a photo/link post

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
# Reddit appends "submitted by /u/x [link] [comments]" to every entry body.
_BOILERPLATE = re.compile(r"submitted by\s+/u/\S+.*$", re.IGNORECASE | re.DOTALL)


@dataclass
class Post:
    id: str
    subreddit: str
    title: str
    url: str
    published: str
    text: str
    is_text_post: bool

    def snippet(self, limit: int = 280) -> str:
        return self.text[:limit] + ("…" if len(self.text) > limit else "")


@dataclass
class FetchResult:
    posts: list[Post] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)


def feed_url(subreddit: str, window: str = "day") -> str:
    return f"https://www.reddit.com/r/{subreddit}/top/.rss?t={window}"


def content_to_text(raw_html: str) -> str:
    """Reddit wraps the self-text in a <table>; strip tags and the trailer."""
    unescaped = html.unescape(raw_html or "")
    text = _TAG.sub(" ", unescaped)
    text = _BOILERPLATE.sub("", text)
    return _WS.sub(" ", text).strip()


def parse_feed(xml_text: str, subreddit: str) -> list[Post]:
    root = ET.fromstring(xml_text)
    posts: list[Post] = []
    for entry in root.iter(f"{ATOM_NS}entry"):
        post_id = (entry.findtext(f"{ATOM_NS}id") or "").strip()
        title = html.unescape((entry.findtext(f"{ATOM_NS}title") or "").strip())
        link = entry.find(f"{ATOM_NS}link")
        url = link.get("href", "") if link is not None else ""
        published = (entry.findtext(f"{ATOM_NS}published") or "").strip()
        text = content_to_text(entry.findtext(f"{ATOM_NS}content") or "")
        if not post_id or not title:
            continue
        posts.append(Post(
            id=post_id,
            subreddit=subreddit,
            title=title,
            url=url,
            published=published,
            text=text,
            is_text_post=len(text) >= MIN_TEXT_CHARS,
        ))
    return posts


def _reset_seconds(resp: requests.Response) -> float:
    try:
        return float(resp.headers.get("x-ratelimit-reset", "60"))
    except ValueError:
        return 60.0


def fetch_feed(subreddit: str, session: requests.Session, *,
               window: str = "day", sleep=time.sleep) -> str:
    url = feed_url(subreddit, window)
    last_error = "unknown"
    for attempt in range(MAX_RETRIES + 1):
        resp = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        if resp.status_code == 200 and resp.text.lstrip().startswith("<?xml"):
            return resp.text
        if resp.status_code == 429 and attempt < MAX_RETRIES:
            wait = _reset_seconds(resp) + 3
            print(f"  r/{subreddit}: 429, waiting {wait:.0f}s", flush=True)
            sleep(wait)
            continue
        last_error = f"HTTP {resp.status_code}"
        if resp.status_code == 200:
            last_error = "HTTP 200 but not XML (blocked page)"
        break
    raise RuntimeError(f"r/{subreddit}: {last_error}")


def fetch_all(subreddits=DEFAULT_SUBREDDITS, *, session: requests.Session | None = None,
              window: str = "day", sleep=time.sleep,
              gap: float = SECONDS_BETWEEN_FEEDS) -> FetchResult:
    """Fetch every feed with error isolation; one bad sub never aborts the run."""
    session = session or requests.Session()
    result = FetchResult()
    for i, sub in enumerate(subreddits):
        if i and gap:
            sleep(gap)
        try:
            xml_text = fetch_feed(sub, session, window=window, sleep=sleep)
            posts = parse_feed(xml_text, sub)
            print(f"  r/{sub}: {len(posts)} entries", flush=True)
            result.posts.extend(posts)
        except (requests.RequestException, RuntimeError, ET.ParseError) as exc:
            print(f"  r/{sub}: FAILED {exc}", flush=True)
            result.failed[sub] = str(exc)
    return result
