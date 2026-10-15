"""The Amazon injector must treat reddit-trend guides as a "guide" page kind."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))  # scripts/

import inject_amazon_links as amz  # noqa: E402

CATALOG = {
    "meta": {"store_tag": "wooffy-20", "tags_by_kind": {"guide": "test-20"}},
    "coat_map": {},
    "entries": [
        {"asin": "B000TEST00", "name": "Test Exercise Pen", "type": "exercise_pen",
         "fit": {"life_stage": "any"}, "page_types": ["checklist"],
         "anchors": [r"\bplaypen\b"], "exclude_if": ["skip the playpen"],
         "blurb": "Folds flat."},
        {"asin": "B000TEST01", "name": "Test Slicker", "type": "slicker_brush",
         "fit": {"life_stage": "adult"}, "page_types": ["grooming"],
         "anchors": [r"\bslicker\b"], "blurb": "Brush."},
        {"asin": "B000TEST02", "name": "Test Stuffable (X-Large)", "type": "stuffable_toy",
         "fit": {"wmin": 60, "wmax": None, "life_stage": "any"}, "page_types": ["checklist"],
         "anchors": [r"\bfood-stuffed toy\b"], "blurb": "Big."},
        {"asin": "B000TEST03", "name": "Test Stuffable (Medium)", "type": "stuffable_toy",
         "fit": {"wmin": 15, "wmax": 35, "life_stage": "any"}, "page_types": ["checklist"],
         "anchors": [r"\bfood-stuffed toy\b"], "blurb": "Medium."},
    ],
    "size_variants": [
        {"group": "test_stuffable", "type": "stuffable_toy", "non_breed_default": "B000TEST03",
         "members": [{"asin": "B000TEST02", "wmin": 60, "wmax": None},
                     {"asin": "B000TEST03", "wmin": 15, "wmax": 35}]},
    ],
}

P = 'style="font-size:0.95em;"'


def guide_doc(text: str) -> dict:
    return {
        "meta": {"name": "Guide", "slug": "how-to-settle-a-puppy", "size_category": "Guide",
                 "published": True},
        "source": {"pipeline": "reddit_trends"},
        "sections": {"intro": {"label": "a", "heading": "b", "html": f"<p {P}>Intro paragraph here.</p>"},
                     "care": {"label": "c", "heading": "d", "html": f"<p {P}>{text}</p>"}},
        "faq": [],
    }


def run(tmp_path, doc: dict):
    (tmp_path / "amazon-catalog.json").write_text(json.dumps(CATALOG), encoding="utf-8")
    data_dir = tmp_path / "breed-data"
    data_dir.mkdir()
    path = data_dir / f"{doc['meta']['slug']}.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    catalog, rules, extra, weights = amz.load_rules(str(tmp_path / "amazon-catalog.json"))
    return path, amz.process(str(path), catalog, weights, extra, rules)


def test_guide_places_anchor_match_regardless_of_page_types(tmp_path):
    path, res = run(tmp_path, guide_doc("Set up a playpen in a quiet room."))
    assert res["kind"] == "guide"
    assert [p["asin"] for p in res["placed"]] == ["B000TEST00"]
    html = dict((tuple(p), h) for p, h in res["fields"])[("sections", "care", "html")]
    assert "amazon.com/dp/B000TEST00/?tag=test-20" in html
    assert amz.MARK in html


def test_guide_respects_exclude_if(tmp_path):
    _, res = run(tmp_path, guide_doc("You can skip the playpen entirely."))
    assert res["placed"] == []


def test_guide_uses_non_breed_default_size_and_skips_other_sizes(tmp_path):
    # one product per paragraph: place() appends at most one link to a given <p>
    _, res = run(tmp_path, guide_doc(f"A food-stuffed toy helps your puppy settle.</p><p {P}>A playpen helps too."))
    assert sorted(p["asin"] for p in res["placed"]) == ["B000TEST00", "B000TEST03"]


def test_inject_one_strips_stale_blocks_when_nothing_matches(tmp_path):
    (tmp_path / "amazon-catalog.json").write_text(json.dumps(CATALOG), encoding="utf-8")
    data_dir = tmp_path / "breed-data"
    data_dir.mkdir()
    doc = guide_doc("Nothing to sell here.")
    doc["sections"]["care"]["html"] += f'{amz.MARK}<span>old link</span>{amz.END}'
    path = data_dir / "how-to-settle-a-puppy.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert amz.inject_one(str(path), str(tmp_path / "amazon-catalog.json")) == []
    assert amz.MARK not in path.read_text(encoding="utf-8")


def test_non_trend_guide_is_ignored(tmp_path):
    doc = guide_doc("Set up a playpen.")
    del doc["source"]
    _, res = run(tmp_path, doc)
    assert res is None


def test_inject_one_writes_file_and_adds_disclosure(tmp_path):
    (tmp_path / "amazon-catalog.json").write_text(json.dumps(CATALOG), encoding="utf-8")
    data_dir = tmp_path / "breed-data"
    data_dir.mkdir()
    path = data_dir / "how-to-settle-a-puppy.json"
    path.write_text(json.dumps(guide_doc("A playpen helps.")), encoding="utf-8")
    placed = amz.inject_one(str(path), str(tmp_path / "amazon-catalog.json"))
    assert [p["type"] for p in placed] == ["exercise_pen"]
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert "Amazon Associate" in saved["sections"]["intro"]["html"]
    assert "B000TEST00" in saved["sections"]["care"]["html"]
