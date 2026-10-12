import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import hero  # noqa: E402
import run  # noqa: E402


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
