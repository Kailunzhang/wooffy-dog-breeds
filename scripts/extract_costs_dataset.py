"""Extract a structured cost dataset from the 158 first-year-costs articles.

Why API extraction instead of regex: the 2026-07 de-templatization
rewrote each article with free structure - probe showed three surviving
formats (clean <li> lists, <table> layouts, prose-embedded ranges) and
regex coverage would be full of holes. Claude API extraction gives 100%
coverage with normalized fields at ~$0.01-0.02/page (~$2-4 total).

The dataset feeds:
  1. The interactive first-year cost calculator page (Shopify)
  2. Citable per-breed statistics (GEO / AI-citation asset)
  3. Future growth-chart cross-references

Modes:
  --extract [--limit N]   API extraction, checkpointed per breed
                          (costs-extract-state.json), resume-safe
  --validate              sanity checks: totals vs sum-of-parts,
                          range ordering, cross-breed outliers
  --emit                  write final costs-dataset.json (+ compact
                          calculator-data.json for the web page)

Requires ANTHROPIC_API_KEY in .env (already present).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from detemplatize_rewrite import (  # noqa: E402
    TAG,
    call_claude,
    load_env,
    parse_rewrite,
)

BREED_DATA = ROOT / "breed-data"
STATE_PATH = ROOT / "costs-extract-state.json"
DATASET_PATH = ROOT / "costs-dataset.json"
CALC_DATA_PATH = ROOT / "calculator-data.json"

MODEL = "claude-haiku-4-5-20251001"  # extraction is mechanical; haiku is plenty

EXTRACT_SYSTEM = """You extract structured cost data from a dog-breed first-year-cost article. Output ONLY valid JSON (no fences) with this exact shape - every money field is [low, high] integers in USD:

{
 "puppy": [lo, hi],
 "rescue": [lo, hi] | null,
 "vet_year1": [lo, hi],
 "spay_neuter": [lo, hi],
 "food_monthly": [lo, hi],
 "insurance_monthly": [lo, hi],
 "grooming_annual": [lo, hi],
 "setup_onetime": [lo, hi],
 "total_year1": [lo, hi],
 "annual_ongoing": [lo, hi],
 "citable_stat": "one sentence with the article's real numbers, e.g. 'A Golden Retriever costs $3,500-$6,200 in the first year, with food for a 65-75 lb adult running $65-$95/month.'",
 "missing": ["fields you could not find"]
}

Field definitions:
- puppy: purchase price from a reputable breeder
- rescue: adoption-route fee if the article states one, else null
- vet_year1: first-year routine vet incl. vaccine series (NOT emergencies)
- food_monthly / insurance_monthly: monthly; if the article only gives annual, divide by 12 and round
- grooming_annual: annual grooming spend (pro visits x rate; a low-end 0 is fine for pure-DIY coats)
- setup_onetime: ONLY these four items - crate + bowls/collar/leash + grooming tools + puppy class - component lows summed and highs summed. Never fold food, fencing, furniture, or training beyond one puppy class into setup; if the article gives one big combined 'setup' figure, decompose to just those four items.
- spay_neuter: if the article mentions the procedure without its own price (e.g. folded into a vet bundle), return null - never [0,0]
- total_year1: the article's stated first-year total (with insurance if stated)
- annual_ongoing: stated ongoing annual cost after year one

Rules:
- Use ONLY numbers present in the article. Never invent or fill from general knowledge.
- A genuinely absent field gets null and an entry in "missing".
- Ignore emergency-vet, boarding, pet-rent, and lifetime figures."""


def costs_paths() -> list[Path]:
    return sorted(BREED_DATA.glob("*-first-year-costs.json"))


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def breed_slug_of(path: Path) -> str:
    return path.stem.replace("-first-year-costs", "")


def breed_display_name(breed_slug: str) -> str:
    main = BREED_DATA / f"{breed_slug}.json"
    if main.exists():
        try:
            name = json.loads(main.read_text(encoding="utf-8"))["meta"].get("name")
            if name:
                return name.strip()
        except (json.JSONDecodeError, OSError, KeyError):
            pass
    return " ".join(w.capitalize() for w in breed_slug.split("-"))


def adult_weight(breed_slug: str) -> str:
    main = BREED_DATA / f"{breed_slug}.json"
    if main.exists():
        try:
            stats = json.loads(main.read_text(encoding="utf-8")).get("stats") or {}
            w = stats.get("weight") or stats.get("size") or {}
            if isinstance(w, dict) and w.get("value"):
                return str(w["value"])
        except (json.JSONDecodeError, OSError):
            pass
    return ""


def cmd_extract(limit: int) -> int:
    env = load_env()
    api_key = env.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY missing from .env")
    state = load_state()
    paths = [p for p in costs_paths()
             if state.get(breed_slug_of(p), {}).get("status") != "done"]
    if limit:
        paths = paths[:limit]
    print(f"Extracting {len(paths)} breeds (model={MODEL})")

    ok = failed = 0
    for i, p in enumerate(paths, 1):
        slug = breed_slug_of(p)
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            html = " ".join(
                s.get("html", "") for s in (d.get("sections") or {}).values()
                if isinstance(s, dict)
            )
            text = re.sub(r"\s+", " ", TAG.sub(" ", html))
            w = adult_weight(slug)
            user = (
                f"BREED: {breed_display_name(slug)}"
                + (f" (adult weight: {w})" if w else "")
                + f"\n\nARTICLE TEXT:\n{text[:9000]}"
            )
            raw = call_claude(api_key, MODEL, EXTRACT_SYSTEM, user)
            data = parse_rewrite(raw)
            for req in ("puppy", "total_year1", "citable_stat"):
                if req not in data:
                    raise RuntimeError(f"missing field {req}")
            state[slug] = {
                "status": "done",
                "data": data,
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            ok += 1
            t1 = data.get("total_year1") or [None, None]
            print(f"  [{i}/{len(paths)}] OK   {slug:40s} year1={t1}")
        except Exception as e:
            state[slug] = {"status": "failed", "error": str(e)[:200],
                           "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            failed += 1
            print(f"  [{i}/{len(paths)}] FAIL {slug}: {str(e)[:120]}", file=sys.stderr)
        save_state(state)
        time.sleep(0.3)
    print(f"\nok={ok} failed={failed}  total done="
          f"{sum(1 for v in state.values() if v.get('status') == 'done')}/{len(costs_paths())}")
    return 0 if failed == 0 else 1


def _pair_ok(v) -> bool:
    return (isinstance(v, list) and len(v) == 2
            and all(isinstance(x, (int, float)) for x in v) and v[0] <= v[1])


def cmd_validate() -> int:
    state = load_state()
    done = {k: v["data"] for k, v in state.items() if v.get("status") == "done"}
    print(f"validating {len(done)} breeds")
    issues = 0
    for slug, d in sorted(done.items()):
        probs = []
        for f in ("puppy", "vet_year1", "spay_neuter", "food_monthly",
                  "insurance_monthly", "grooming_annual", "setup_onetime",
                  "total_year1", "annual_ongoing"):
            v = d.get(f)
            if v is not None and not _pair_ok(v):
                probs.append(f"bad pair {f}={v}")
        try:
            parts_lo = (d["puppy"][0] + d["vet_year1"][0] + d["spay_neuter"][0]
                        + d["food_monthly"][0] * 12 + d["setup_onetime"][0])
            if parts_lo > d["total_year1"][1] * 1.15:
                probs.append(f"parts_lo {parts_lo} >> total_hi {d['total_year1'][1]}")
        except (TypeError, KeyError):
            probs.append("cannot cross-check total (missing parts)")
        if d.get("missing"):
            probs.append(f"missing: {d['missing']}")
        if probs:
            issues += 1
            print(f"  {slug}: " + "; ".join(str(p) for p in probs))
    print(f"\nbreeds with issues: {issues}/{len(done)}")
    return 0


SIZE_BUCKETS = [(15, "toy"), (30, "small"), (60, "medium"), (90, "large"), (999, "giant")]
FILL_FIELDS = ("puppy", "vet_year1", "spay_neuter", "food_monthly",
               "insurance_monthly", "grooming_annual", "setup_onetime",
               "total_year1", "annual_ongoing")


def weight_bucket(weight_str: str) -> str:
    nums = [int(n) for n in re.findall(r"\d+", weight_str or "")]
    if not nums:
        return "medium"
    mid = sum(nums[:2]) / min(len(nums), 2)
    for cap, name in SIZE_BUCKETS:
        if mid <= cap:
            return name
    return "giant"


def cmd_emit() -> int:
    state = load_state()
    dataset = {}
    for slug, v in sorted(state.items()):
        if v.get("status") != "done":
            continue
        d = dict(v["data"])
        d["name"] = breed_display_name(slug)
        d["weight"] = adult_weight(slug)
        d["bucket"] = weight_bucket(d["weight"])
        d["article_url"] = f"https://thewooffy.com/blogs/dog-breeds/{slug}-first-year-costs"
        dataset[slug] = d

    # ---- fill missing fields from size-bucket medians (marked in "est") ----
    def med(pairs):
        los = sorted(p[0] for p in pairs)
        his = sorted(p[1] for p in pairs)
        return [los[len(los) // 2], his[len(his) // 2]]

    bucket_medians: dict[str, dict[str, list]] = {}
    for bucket in ("toy", "small", "medium", "large", "giant"):
        bucket_medians[bucket] = {}
        for f in FILL_FIELDS:
            pairs = [d[f] for d in dataset.values()
                     if d["bucket"] == bucket and _pair_ok(d.get(f))]
            if pairs:
                bucket_medians[bucket][f] = med(pairs)

    # outlier guards: absurd setup or zeroed spay fall back to bucket medians
    for slug, d in dataset.items():
        bm = bucket_medians[d["bucket"]]
        su = d.get("setup_onetime")
        if _pair_ok(su) and "setup_onetime" in bm and su[1] > bm["setup_onetime"][1] * 2:
            d["setup_onetime"] = None  # forces median fill + est flag below
        if d.get("spay_neuter") == [0, 0]:
            d["spay_neuter"] = None

    filled_total = 0
    for slug, d in dataset.items():
        est = []
        for f in FILL_FIELDS:
            if not _pair_ok(d.get(f)):
                fb = bucket_medians[d["bucket"]].get(f)
                if fb is None:  # bucket empty for this field - global median
                    pairs = [x[f] for x in dataset.values() if _pair_ok(x.get(f))]
                    fb = med(pairs) if pairs else [0, 0]
                d[f] = list(fb)
                est.append(f)
        # recompute total from parts when it was estimated (more honest than
        # borrowing another breed's stated total)
        if "total_year1" in est:
            d["total_year1"] = [
                d["puppy"][0] + d["vet_year1"][0] + d["spay_neuter"][0]
                + d["food_monthly"][0] * 12 + d["insurance_monthly"][0] * 12
                + d["grooming_annual"][0] + d["setup_onetime"][0],
                d["puppy"][1] + d["vet_year1"][1] + d["spay_neuter"][1]
                + d["food_monthly"][1] * 12 + d["insurance_monthly"][1] * 12
                + d["grooming_annual"][1] + d["setup_onetime"][1],
            ]
        d["est"] = est
        filled_total += len(est)
    print(f"filled {filled_total} missing fields via size-bucket medians")
    DATASET_PATH.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    compact = {}
    for slug, d in dataset.items():
        compact[slug] = {
            "n": d["name"],
            "p": d.get("puppy"), "r": d.get("rescue"),
            "v": d.get("vet_year1"), "s": d.get("spay_neuter"),
            "f": d.get("food_monthly"), "i": d.get("insurance_monthly"),
            "g": d.get("grooming_annual"), "u": d.get("setup_onetime"),
            "t": d.get("total_year1"), "a": d.get("annual_ongoing"),
        }
    CALC_DATA_PATH.write_text(
        json.dumps(compact, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8")
    print(f"emitted {len(dataset)} breeds -> {DATASET_PATH.name} + {CALC_DATA_PATH.name}"
          f" ({CALC_DATA_PATH.stat().st_size // 1024}KB compact)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if a.extract:
        return cmd_extract(a.limit)
    if a.validate:
        return cmd_validate()
    if a.emit:
        return cmd_emit()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
