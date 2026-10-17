import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import hero  # noqa: E402
import run  # noqa: E402
import writer  # noqa: E402
from sample_article import good_article  # noqa: E402


def test_resolve_blog_prefers_cluster_blog_when_env_present():
    env = {"SHOPIFY_BLOG_ID": "1", "SHOPIFY_DOG_NUTRITION_BLOG_ID": "2"}
    assert run.resolve_blog("nutrition", env) == "dog-nutrition"
    assert run.resolve_blog("breeds", env) == "dog-breeds"


def test_resolve_blog_falls_back_to_dog_breeds_when_env_missing():
    env = {"SHOPIFY_BLOG_ID": "1", "SHOPIFY_LIFE_WITH_DOGS_BLOG_ID": "0"}
    assert run.resolve_blog("life", env) == "dog-breeds"
    assert run.resolve_blog("training", env) == "dog-breeds"
    assert run.resolve_blog("unknown-cluster", env) == "dog-breeds"


def test_state_roundtrip_and_seen_cap(tmp_path):
    path = tmp_path / "state.json"
    state = run.load_state(path)
    assert state == {"picked": [], "seen_ids": []}
    state["seen_ids"] = [f"t3_{i}" for i in range(run.SEEN_LIMIT + 50)]
    state["picked"].append({"date": "2026-10-12", "slug": "a-b", "title": "t",
                            "reddit_ids": [], "published": True, "url": ""})
    run.save_state(state, path)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert len(loaded["seen_ids"]) == run.SEEN_LIMIT
    assert loaded["seen_ids"][-1] == f"t3_{run.SEEN_LIMIT + 49}"
    assert loaded["picked"][0]["slug"] == "a-b"


def test_recent_topics_respects_window():
    state = {"picked": [
        {"date": "2026-10-01", "slug": "new-one"},
        {"date": "2026-06-01", "slug": "old-one"},
    ]}
    assert run.recent_topics(state, date(2026, 10, 12)) == ["new-one"]


def test_shopify_recent_handles_returns_empty_without_creds():
    assert run.shopify_recent_handles({}) == []
    assert run.shopify_recent_handles({"SHOPIFY_STORE": "x.myshopify.com"}) == []


def test_shopify_recent_handles_collects_each_configured_blog(monkeypatch):
    calls = []

    class Resp:
        status_code = 200

        def __init__(self, blog):
            self._blog = blog

        def json(self):
            return {"articles": [{"handle": f"{self._blog}-topic"}, {"handle": "shared-topic"}]}

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append((url, params["created_at_min"][:4]))
        return Resp(url.rsplit("/blogs/", 1)[1].split("/")[0])

    import requests
    monkeypatch.setattr(requests, "get", fake_get)
    env = {"SHOPIFY_STORE": "x.myshopify.com", "SHOPIFY_TOKEN": "t",
           "SHOPIFY_BLOG_ID": "11", "SHOPIFY_DOG_NUTRITION_BLOG_ID": "22",
           "SHOPIFY_LIFE_WITH_DOGS_BLOG_ID": "0"}
    handles = run.shopify_recent_handles(env)
    assert handles == ["11-topic", "22-topic", "shared-topic"]
    assert len(calls) == 2 and all(y == "2026" for _, y in calls)


def test_manual_topic_builds_slug():
    topic = run.manual_topic("Crate Training a Rescue Dog at Night!", "training", True)
    assert topic.slug == "crate-training-a-rescue-dog-at-night"
    assert topic.cluster == "training" and topic.ymyl is True


def test_hero_falls_back_without_key():
    result = hero.make_hero("slug", "prompt", "alt", store="s", token="t", fal_key="")
    assert result.is_fallback and result.url == hero.PLACEHOLDER_HERO and result.error == "no FAL key"


def test_parse_args_defaults():
    args = run.parse_args([])
    assert not args.dry_run and args.window == "day" and "dogs" in args.subs
    args = run.parse_args(["--dry-run", "--no-hero", "--topic", "x", "--cluster", "health"])
    assert args.dry_run and args.no_hero and args.cluster == "health"


def test_write_article_retries_truncated_reply_and_reports_usage(monkeypatch):
    article = dict(good_article(), related=[])
    replies = iter([writer.ClaudeReply('{"name": "cut off mid', "max_tokens", 12000),
                    writer.ClaudeReply(json.dumps(article), "end_turn", 9000)])
    monkeypatch.setattr(writer, "call_claude", lambda *a, **k: next(replies))
    topic = run.manual_topic("Puppy blues guide", "life", False)
    args = run.parse_args(["--topic", "Puppy blues guide"])

    result, problems, review, usage = run.write_article(args, {"ANTHROPIC_API_KEY": "k"}, topic, [])

    assert result["name"] == article["name"]
    assert problems == [] and review["verdict"] == "pass"
    assert "12000 tok (max_tokens)" in usage and "9000 tok (end_turn)" in usage


def test_write_article_requires_a_review_verdict_and_normalises_it(monkeypatch):
    article = dict(good_article(), related=[])
    replies = iter([writer.ClaudeReply(json.dumps(article), "end_turn", 9000),
                    writer.ClaudeReply('{"issues": ["no verdict key"]}', "end_turn", 20),
                    writer.ClaudeReply('{"verdict": " Block ", "issues": ["unsafe"]}', "end_turn", 20)])
    monkeypatch.setattr(writer, "call_claude", lambda *a, **k: next(replies))
    topic = run.manual_topic("Puppy blues guide", "life", True)
    args = run.parse_args(["--topic", "Puppy blues guide", "--ymyl"])

    _, _, review, usage = run.write_article(args, {"ANTHROPIC_API_KEY": "k"}, topic, [])

    assert review == {"verdict": "block", "issues": ["unsafe"]}
    assert usage.count("审核") == 2  # the verdict-less reply was retried, not treated as a pass
