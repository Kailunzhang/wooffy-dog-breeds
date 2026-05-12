"""Fix the 6 doodle main JSONs' secondary images so each placement uses the
correct shot (lifestyle / grooming / puppy) instead of all-adult-portrait.

batch_generate.py:patch_breed_jsons does filename-heuristic matching on the
OLD URL to pick which of the 4 CDN URLs to use as a replacement. Since all 3
placeholder URLs in each doodle JSON were identical, all 3 got mapped to the
default LABEL_ADULT. This script re-maps by `placement` instead.

One-shot run: python3 scripts/fix_doodle_secondary_images.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "batch_state.json"
BREED_DATA = ROOT / "breed-data"

DOODLES = ["goldendoodle", "labradoodle", "bernedoodle", "cavapoo", "sheepadoodle", "aussiedoodle"]

PLACEMENT_TO_LABEL = {
    "before_temperament": "03-lifestyle",
    "before_care": "02-grooming",
    "before_finding": "04-puppy",
}


def main() -> int:
    state = json.loads(STATE.read_text(encoding="utf-8"))

    for slug in DOODLES:
        if slug not in state:
            print(f"  {slug}: missing from batch_state.json - skipping")
            continue
        urls = state[slug].get("image_urls", {})
        if not all(label in urls for label in PLACEMENT_TO_LABEL.values()):
            print(f"  {slug}: incomplete image_urls - skipping")
            continue

        path = BREED_DATA / f"{slug}.json"
        if not path.exists():
            print(f"  {slug}: {path} missing - skipping")
            continue

        data = json.loads(path.read_text(encoding="utf-8"))
        secondary = data.get("images", {}).get("secondary", [])
        if not isinstance(secondary, list):
            print(f"  {slug}: no secondary[] - skipping")
            continue

        changed = 0
        for entry in secondary:
            placement = entry.get("placement")
            label = PLACEMENT_TO_LABEL.get(placement)
            if not label:
                continue
            new_url = urls[label]
            if entry.get("url") != new_url:
                entry["url"] = new_url
                changed += 1

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {slug}: updated {changed} secondary URLs")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
