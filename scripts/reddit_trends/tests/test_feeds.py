import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import feeds  # noqa: E402

FIXTURE = (HERE / "fixtures" / "dogs_top_day.xml").read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, status: int, text: str = "", headers: dict | None = None):
        self.status_code = status
        self.text = text
        self.headers = headers or {}


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, timeout=None):
        self.calls.append(url)
        return self._responses.pop(0)


def test_parse_feed_returns_every_entry_with_clean_text():
    posts = feeds.parse_feed(FIXTURE, "dogs")
    assert len(posts) == 21
    assert all(p.id.startswith("t3_") for p in posts)
    assert all(p.subreddit == "dogs" for p in posts)
    longest = max(posts, key=lambda p: len(p.text))
    assert "submitted by" not in longest.text
    assert "/u/" not in longest.text
    assert "<" not in longest.text


def test_text_posts_are_separated_from_photo_posts():
    posts = feeds.parse_feed(FIXTURE, "dogs")
    text_posts = [p for p in posts if p.is_text_post]
    assert 5 <= len(text_posts) < len(posts)
    assert any("sleep at night" in p.title.lower() for p in text_posts)


def test_content_to_text_strips_reddit_trailer():
    raw = ("&lt;table&gt;&lt;tr&gt;&lt;td&gt;Hello &lt;b&gt;world&lt;/b&gt; "
           "submitted by /u/someone [link] [comments]&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;")
    assert feeds.content_to_text(raw) == "Hello world"


def test_fetch_feed_retries_after_429_using_reset_header():
    session = FakeSession([
        FakeResponse(429, headers={"x-ratelimit-reset": "7"}),
        FakeResponse(200, FIXTURE),
    ])
    waits = []
    xml = feeds.fetch_feed("dogs", session, sleep=waits.append)
    assert xml.startswith("<?xml")
    assert waits == [10.0]
    assert len(session.calls) == 2


def test_fetch_feed_rejects_blocked_html_page():
    session = FakeSession([FakeResponse(200, "<body class=theme-beta>blocked</body>")])
    with pytest.raises(RuntimeError, match="not XML"):
        feeds.fetch_feed("dogs", session, sleep=lambda s: None)


def test_fetch_all_isolates_failures_and_spaces_requests():
    session = FakeSession([
        FakeResponse(200, FIXTURE),
        FakeResponse(403),
        FakeResponse(200, FIXTURE),
    ])
    waits = []
    result = feeds.fetch_all(["dogs", "puppy101", "DogAdvice"], session=session,
                             sleep=waits.append, gap=65)
    assert len(result.posts) == 42
    assert list(result.failed) == ["puppy101"]
    assert waits == [65, 65]
