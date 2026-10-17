import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import writer  # noqa: E402
from sample_article import good_article  # noqa: E402
from selector import TopicProposal  # noqa: E402

TOPIC = TopicProposal("puppy-night-whining-guide", "Puppy whining at night", "angle",
                      "training", False, ["t3_a"], "hot")


def test_valid_article_passes():
    assert writer.validate_article(good_article(), {"golden-retriever"}) == []


def test_phone_number_and_reddit_mentions_are_rejected():
    art = good_article()
    art["sections"]["care"]["html"] += "<p>Call (888) 426-4435 now, as seen on Reddit.</p>"
    problems = writer.validate_article(art, {"golden-retriever"})
    assert "contains a phone number" in problems
    assert "mentions reddit/forum/usernames" in problems


def test_dosing_language_short_text_and_bad_related_slug_are_rejected():
    art = good_article(words_per_section=100)
    art["faq"][0]["a"] = "Give a dose of 5 mg/kg"
    art["related"] = [["does-not-exist", "x"]]
    problems = writer.validate_article(art, {"golden-retriever"})
    assert any(p.startswith("too short") for p in problems)
    assert "contains dosing language" in problems
    assert "related slug does not exist: does-not-exist" in problems


def test_missing_section_is_reported():
    art = good_article()
    del art["sections"]["special"]
    assert "section special incomplete" in writer.validate_article(art, set())


def test_parse_json_strips_fences():
    assert writer.parse_json("```json\n{\"a\": 1}\n```") == {"a": 1}


def test_assemble_matches_breed_data_schema():
    art = good_article()
    data = writer.assemble(TOPIC, art, blog_handle="dog-training", hero_url="https://cdn/x.png",
                           hero_alt="alt", related_html="<div>related</div>", source_ids=["t3_a"],
                           now=datetime(2026, 10, 12, 14, 0, tzinfo=timezone.utc))
    meta = data["meta"]
    assert meta["slug"] == meta["shopify_handle"] == "puppy-night-whining-guide"
    assert meta["blog_handle"] == "dog-training"
    assert meta["size_category"] == "Guide" and meta["published"] is True
    assert meta["published_at"] == "2026-10-12T14:00:00Z"
    assert data["images"]["hero"] == {"url": "https://cdn/x.png", "alt": "alt"}
    assert data["sections"]["special"]["html"].endswith("<div>related</div>")
    assert data["sections"]["care"]["html"] == art["sections"]["care"]["html"]
    assert data["source"]["reddit_ids"] == ["t3_a"]
    json.dumps(data)  # must be serialisable


def test_related_candidates_matches_slugs_by_keyword(tmp_path):
    (tmp_path / "puppy-sleep-schedule.json").write_text(json.dumps({"meta": {"name": "Puppy Sleep"}}))
    (tmp_path / "golden-retriever.json").write_text(json.dumps({"meta": {"name": "Golden"}}))
    (tmp_path / "broken.json").write_text("{not json")
    rel = writer.related_candidates(tmp_path, TOPIC)
    assert rel == [("puppy-sleep-schedule", "Puppy Sleep")]


def test_related_candidates_ranks_topic_guides_above_breed_pages_and_caps_them(tmp_path):
    for breed in ("akita", "beagle", "corgi", "dachshund"):
        (tmp_path / f"{breed}-puppy-checklist.json").write_text(json.dumps({"meta": {"name": breed}}))
    (tmp_path / "puppy-night-whining-help.json").write_text(json.dumps({"meta": {"name": "Whining"}}))
    rel = writer.related_candidates(tmp_path, TOPIC)
    assert rel[0] == ("puppy-night-whining-help", "Whining")
    assert sum(1 for slug, _ in rel if slug.endswith("-puppy-checklist")) == writer.MAX_BREED_PAGES


def test_article_prompt_mentions_topic_sources_and_related():
    prompt = writer.build_article_prompt(TOPIC, ["How do I stop whining"],
                                         [("puppy-sleep-schedule", "Puppy Sleep")], "2026-10-12")
    assert "slug: puppy-night-whining-guide" in prompt
    assert "- How do I stop whining" in prompt
    assert "- puppy-sleep-schedule: Puppy Sleep" in prompt


# ---------------------------------------------------------------- Claude call


class _Resp:
    def __init__(self, body: dict, status: int = 200):
        self._body, self.status_code, self.text = body, status, json.dumps(body)

    def json(self) -> dict:
        return self._body


def _api_body(text: str, stop_reason: str = "end_turn", output_tokens: int = 42) -> dict:
    return {"content": [{"type": "text", "text": text}],
            "stop_reason": stop_reason, "usage": {"output_tokens": output_tokens}}


def test_call_claude_returns_stop_reason_and_output_tokens(monkeypatch):
    monkeypatch.setattr(writer.requests, "post",
                        lambda *a, **k: _Resp(_api_body('{"a": 1}', "max_tokens", 12000)))
    reply = writer.call_claude("key", "model", "sys", "user")
    assert reply.text == '{"a": 1}'
    assert reply.stop_reason == "max_tokens"
    assert reply.output_tokens == 12000


def _fake_calls(monkeypatch, replies: list, prompts: list[str]):
    pending = iter(replies)

    def fake(key, model, system, user, max_tokens=writer.MAX_OUTPUT_TOKENS):
        prompts.append(user)
        item = next(pending)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(writer, "call_claude", fake)


def test_generate_json_retries_when_a_parsable_reply_was_cut_off(monkeypatch):
    prompts: list[str] = []
    _fake_calls(monkeypatch, [writer.ClaudeReply('{"a": 0}', "max_tokens", 20000),
                              writer.ClaudeReply('{"a": 1}', "end_turn", 50)], prompts)
    data, used = writer.generate_json("key", "model", "sys", "prompt")
    assert data == {"a": 1}  # a cut-off reply is not trusted even when it happens to parse
    assert [r.output_tokens for r in used] == [20000, 50]
    assert prompts[0] == "prompt"
    assert prompts[1].startswith("prompt") and "cut off" in prompts[1]


def test_generate_json_nudges_for_invalid_json_without_claiming_a_cut_off(monkeypatch):
    prompts: list[str] = []
    _fake_calls(monkeypatch, [writer.ClaudeReply("Here you go: {", "end_turn", 5),
                              writer.ClaudeReply('{"a": 1}', "end_turn", 50)], prompts)
    data, _ = writer.generate_json("key", "model", "sys", "prompt")
    assert data == {"a": 1}
    assert "not valid JSON" in prompts[1] and "cut off" not in prompts[1]


def test_generate_json_retries_after_a_timeout_with_the_same_prompt(monkeypatch):
    prompts: list[str] = []
    _fake_calls(monkeypatch, [writer.requests.Timeout("slow"),
                              writer.ClaudeReply('{"a": 1}', "end_turn", 50)], prompts)
    data, used = writer.generate_json("key", "model", "sys", "prompt")
    assert data == {"a": 1} and len(used) == 1
    assert prompts == ["prompt", "prompt"]


def test_generate_json_rejects_replies_missing_required_keys(monkeypatch):
    _fake_calls(monkeypatch, [writer.ClaudeReply('{"issues": []}', "end_turn", 5)] * 2, [])
    with pytest.raises(RuntimeError, match="missing verdict"):
        writer.generate_json("key", "model", "sys", "prompt", required=("verdict",))


def test_generate_json_rejects_json_that_is_not_an_object(monkeypatch):
    _fake_calls(monkeypatch, [writer.ClaudeReply("[1, 2]", "end_turn", 5)] * 2, [])
    with pytest.raises(RuntimeError, match="not an object"):
        writer.generate_json("key", "model", "sys", "prompt")


def test_generate_json_error_lists_every_attempt_with_its_tokens(monkeypatch):
    _fake_calls(monkeypatch, [writer.ClaudeReply('{"x": "open', "max_tokens", 20000)] * 2, [])
    expected = r"2 attempts: output cut off after 20000 tokens \(max_tokens\) \| output cut off"
    with pytest.raises(RuntimeError, match=expected):
        writer.generate_json("key", "model", "sys", "prompt")


def test_generate_json_retries_on_invalid_json_then_gives_up(monkeypatch):
    monkeypatch.setattr(writer, "call_claude",
                        lambda *a, **k: writer.ClaudeReply("not json at all", "end_turn", 5))
    with pytest.raises(RuntimeError, match="2 attempts"):
        writer.generate_json("key", "model", "sys", "prompt")


def test_output_token_cap_has_headroom_over_a_long_article():
    # Published guides run ~23k chars of style-heavy HTML (~9k tokens); 12k was too tight.
    assert writer.MAX_OUTPUT_TOKENS >= 20000


def test_usage_line_lists_each_call():
    calls = [("文章", writer.ClaudeReply("", "end_turn", 9120)),
             ("审核", writer.ClaudeReply("", "end_turn", 180))]
    assert writer.usage_line(calls) == "文章 9120 tok (end_turn) | 审核 180 tok (end_turn)"
