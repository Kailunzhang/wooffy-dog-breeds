import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import selector  # noqa: E402
from feeds import Post  # noqa: E402


def make_post(pid: str, title: str, text: str = "x" * 200, sub: str = "dogs") -> Post:
    return Post(id=pid, subreddit=sub, title=title, url="https://example.invalid/" + pid,
                published="2026-10-12T00:00:00+00:00", text=text, is_text_post=len(text) >= 150)


def test_prefilter_drops_excluded_seen_and_photo_posts():
    posts = [
        make_post("t3_a", "My dog is struggling to sleep at night"),
        make_post("t3_b", "Megathread: Why Does My Dog Do That?"),
        make_post("t3_c", "Need help: lost dog in Oakland"),
        make_post("t3_d", "Look at this good boy", text="short"),
        make_post("t3_e", "Crate training regression at 6 months"),
        make_post("t3_f", "Please donate to my vet bill"),
    ]
    kept = selector.prefilter(posts, seen_ids={"t3_e"})
    assert [p.id for p in kept] == ["t3_a"]


def test_prefilter_keeps_longest_text_first_and_caps_count():
    posts = [make_post(f"t3_{i}", f"Question number {i} about puppies", text="x" * (150 + i))
             for i in range(selector.MAX_CANDIDATES + 10)]
    kept = selector.prefilter(posts, seen_ids=set())
    assert len(kept) == selector.MAX_CANDIDATES
    assert kept[0].id == f"t3_{selector.MAX_CANDIDATES + 9}"


def test_selection_prompt_contains_candidates_and_existing_slugs():
    prompt = selector.build_selection_prompt(
        [make_post("t3_a", "How do I stop night whining")],
        ["golden-retriever", "puppy-sleep-schedule"],
        ["crate-training-at-night"],
    )
    assert "t3_a | r/dogs | How do I stop night whining" in prompt
    assert "golden-retriever, puppy-sleep-schedule" in prompt
    assert "crate-training-at-night" in prompt


def test_parse_selection_validates_slugs_and_clusters():
    raw = "```json\n" + json.dumps({"proposals": [
        {"slug": "Bad Slug!", "title": "nope"},
        {"slug": "puppy-night-whining-guide", "title": "Puppy whining at night",
         "angle": "a", "cluster": "weird", "ymyl": "yes", "source_ids": ["t3_a"], "reason": "r"},
    ]}) + "\n```"
    proposals = selector.parse_selection(raw)
    assert len(proposals) == 1
    assert proposals[0].slug == "puppy-night-whining-guide"
    assert proposals[0].cluster == "life"
    assert proposals[0].ymyl is True
    assert proposals[0].source_ids == ["t3_a"]


def test_choose_skips_existing_slugs():
    proposals = [
        selector.TopicProposal("golden-retriever", "dup", "", "breeds", False, [], ""),
        selector.TopicProposal("new-topic-here", "fresh", "", "life", False, [], ""),
    ]
    chosen = selector.choose(proposals, {"golden-retriever"})
    assert chosen is not None and chosen.slug == "new-topic-here"
    assert selector.choose(proposals[:1], {"golden-retriever"}) is None


def test_parse_selection_accepts_an_already_parsed_object():
    data = {"proposals": [{"slug": "puppy-blues-first-weeks", "title": "Puppy blues", "angle": "a",
                           "cluster": "life", "ymyl": False, "source_ids": ["t3_x"], "reason": "r"}]}
    assert [p.slug for p in selector.parse_selection(data)] == ["puppy-blues-first-weeks"]
