"""De-templatize duplicated articles via Claude API rewriting.

Background (2026-07-05 full-corpus audit, numbers/breed-names normalized):
  - costs cluster: 164 articles, 56% avg boilerplate sentences,
    median pair-similarity 53%, worst articles 92-94% templated.
  - grooming cluster: bimodal - a subset is up to 72% templated.
  - checklist: a few doodle-batch pairs share structure.
  - All other types (main-breed/roundup/guide/nutrition/comparison)
    measured 0-2% boilerplate - no action needed.

This is the profile Google's "scaled content abuse" policy targets.
Rule-based synonym spinning would make it worse (that IS spun content);
the fix is genuine per-breed rewriting with breed-specific facts.

Three modes:

  --audit
      Recompute per-article templated-fraction for costs/grooming/
      checklist clusters. Write detemplatize-targets.json (articles
      over threshold) and per-cluster top boilerplate sentences
      (fed to the rewrite prompt as forbidden phrases).

  --rewrite [--limit N] [--model MODEL]
      For each target article: load its JSON + the sibling main-breed
      JSON (breed facts), call Claude API to rewrite sections.*.html
      and faq with hard constraints, validate output, write back.
      Checkpoints to detemplatize-state.json after every article -
      safe to kill and re-run. Requires ANTHROPIC_API_KEY in .env
      or environment.

  --verify
      Re-run the similarity audit on rewritten clusters and print
      the post-rewrite numbers.

After rewriting, push with:
    echo YES | python3 scripts/generate.py <slugs...> --update
(slug list is in detemplatize-state.json / printed after --rewrite)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"
ENV_PATH = ROOT / ".env"
TARGETS_PATH = ROOT / "detemplatize-targets.json"
STATE_PATH = ROOT / "detemplatize-state.json"

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5"
MAX_OUTPUT_TOKENS = 16000  # 2,000-4,000 words of inline-styled HTML JSON
MIN_WORDS_AFTER = 1700     # validation floor (sections only, FAQ adds more)

# Articles with templated fraction above this go on the rewrite list.
TEMPLATED_THRESHOLD = 0.25
# costs cluster is force-included wholesale (56% avg boilerplate).
FORCE_ALL = {"costs"}

TAG = re.compile(r"<[^>]+>")
NUM = re.compile(r"\d[\d,\.]*")
WS = re.compile(r"\s+")


# ---------------------------------------------------------------- shared

def load_env() -> dict[str, str]:
    env = dict(os.environ)
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def classify(stem: str, meta: dict) -> str:
    if stem.endswith("-grooming-guide"):
        return "grooming"
    if stem.endswith("-first-year-costs"):
        return "costs"
    if stem.endswith("-puppy-checklist"):
        return "checklist"
    if (meta.get("size_category") or "").endswith(" Breed"):
        return "main-breed"
    if (meta.get("size_category") or "") == "Roundup":
        return "roundup"
    if "-vs-" in stem:
        return "comparison"
    if (meta.get("blog_handle") or "") == "dog-nutrition":
        return "nutrition"
    return "guide"


def article_text(data: dict) -> str:
    blobs = []
    if data.get("body_html"):
        blobs.append(data["body_html"])
    for s in (data.get("sections") or {}).values():
        if isinstance(s, dict) and s.get("html"):
            blobs.append(s["html"])
    return TAG.sub(" ", " ".join(blobs))


def breed_words_for(stem: str) -> set[str]:
    base = (
        stem.replace("-grooming-guide", "")
        .replace("-first-year-costs", "")
        .replace("-puppy-checklist", "")
    )
    return set(base.split("-"))


def norm_sentences(text: str, breed_words: set[str]) -> list[str]:
    sents = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in sents:
        s = s.strip().lower()
        if len(s.split()) < 6:
            continue
        s = NUM.sub("#", s)
        for w in breed_words:
            s = s.replace(w, "BREED")
        out.append(WS.sub(" ", s))
    return out


def shingle_set(text: str, breed_words: set[str], n: int = 5) -> set[str]:
    words = NUM.sub("#", text.lower()).split()
    words = ["BREED" if w.strip(".,!?()") in breed_words else w for w in words]
    return set(" ".join(words[i : i + n]) for i in range(len(words) - n + 1))


def load_clusters() -> dict[str, list[Path]]:
    clusters: dict[str, list[Path]] = defaultdict(list)
    for p in sorted(BREED_DATA.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        clusters[classify(p.stem, d.get("meta", {}))].append(p)
    return clusters


def cluster_stats(paths: list[Path]) -> tuple[dict[str, float], list[str]]:
    """Return ({stem: templated_fraction}, top_boilerplate_sentences)."""
    sent_map: dict[str, set[int]] = defaultdict(set)
    art_sents: dict[int, list[str]] = {}
    stems: dict[int, str] = {}
    for i, p in enumerate(paths):
        bw = breed_words_for(p.stem)
        d = json.loads(p.read_text(encoding="utf-8"))
        ss = norm_sentences(article_text(d), bw)
        art_sents[i] = ss
        stems[i] = p.stem
        for s in set(ss):
            sent_map[s].add(i)
    thresh = max(3, int(len(paths) * 0.10))
    boiler = {s: arts for s, arts in sent_map.items() if len(arts) >= thresh}
    frac = {}
    for i, ss in art_sents.items():
        frac[stems[i]] = (
            sum(1 for s in ss if s in boiler) / len(ss) if ss else 0.0
        )
    top_boiler = [
        s for s, _ in sorted(boiler.items(), key=lambda kv: -len(kv[1]))[:30]
    ]
    return frac, top_boiler


# ---------------------------------------------------------------- audit

def cmd_audit() -> int:
    clusters = load_clusters()
    targets: dict[str, dict] = {}
    boiler_by_cluster: dict[str, list[str]] = {}
    for t in ("costs", "grooming", "checklist"):
        paths = clusters.get(t, [])
        frac, top_boiler = cluster_stats(paths)
        boiler_by_cluster[t] = top_boiler
        for stem, f in frac.items():
            if t in FORCE_ALL or f >= TEMPLATED_THRESHOLD:
                targets[stem] = {"cluster": t, "templated_fraction": round(f, 3)}
    by_cluster: dict[str, int] = defaultdict(int)
    for v in targets.values():
        by_cluster[v["cluster"]] += 1
    TARGETS_PATH.write_text(
        json.dumps(
            {"targets": targets, "boilerplate": boiler_by_cluster},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(targets)} targets -> {TARGETS_PATH}")
    for c, n in sorted(by_cluster.items()):
        print(f"  {c}: {n}")
    return 0


# ---------------------------------------------------------------- rewrite

REWRITE_SYSTEM = """You are an expert pet-content editor rewriting articles for a dog-breed website (thewooffy.com). Your job is to make each article read as an individually-written piece, NOT a template. You will be given:
1. The current article (JSON: sections with HTML + FAQ list)
2. Facts about this specific breed (size, group, coat, temperament, known health issues)
3. A list of FORBIDDEN boilerplate sentences that appear across many sister articles - your rewrite must not reuse these phrasings or close paraphrases of them.

Rewrite requirements:
- PRESERVE all factual claims, dollar amounts, and numeric ranges exactly as given. Do not invent new prices.
- PRESERVE the JSON structure: same section keys; 'label' and 'heading' may be lightly edited; 'html' fully rewritten.
- PRESERVE HTML conventions: keep the original's inline-style formatting approach (style attributes on <p>/<h3>/<ul>/<table> etc.); structure may change form.
- PRESERVE any <a href> links exactly (same URLs; anchor text may be rephrased).
- VARY structure: do not follow the original's paragraph order slavishly; reorganize where it improves flow.
- INJECT breed specificity: weave the provided breed facts into the narrative (coat type changes grooming cost/effort; size changes food cost; known health conditions change vet/insurance considerations). At least 30% of the rewritten text should be breed-specific in a way that would NOT make sense pasted into a different breed's article.
- Total length: 2,200-3,500 words across all sections. This is an EXPANSION rewrite, not a compression. Never pad with fluff - expand with substance using the EXPANSION GUIDANCE provided in the user message. Add <h3> subheadings (with the original's inline-style conventions) to structure the longer sections.
- Tables: where the original has a table, keep a table (may restructure); where a cost/schedule breakdown would clarify, add one.
- FAQ: rewrite each answer's phrasing, keep facts; you may rephrase questions; expand answers to 60-120 words each; add 1-2 new breed-specific FAQ entries.
- Tone: expert but warm, practical, first-hand. No fluff, no 'in conclusion', no 'it's important to note'.

Output ONLY valid JSON with this exact shape (no markdown fences):
{"sections": {"<key>": {"label": "...", "heading": "...", "html": "..."}, ...}, "faq": [{"q": "...", "a": "..."}, ...]}"""


EXPANSION_GUIDANCE = {
    "costs": """EXPANSION GUIDANCE for first-year-cost articles (reach 2,200-3,500 words with substance, not padding):
- Month-by-month first-year cost timeline (months 1-3 setup-heavy, 4-6 vaccines/training, 7-12 steady state) with this breed's specifics
- Breed-specific health cost scenarios: use the known health conditions from BREED FACTS - what does screening/treatment for THOSE conditions cost, and how does it shape insurance choice for this breed
- Food cost math tied to this breed's adult weight: cups per day, bag size economics, puppy vs adult formula transition timing
- Grooming line item tied to this breed's actual coat: DIY tool kit one-time cost vs professional schedule annual cost
- Budget path vs premium path: two realistic first-year totals for this breed, itemized
- One-time vs recurring cost table
- 3-4 breed-specific money-saving tactics that do NOT compromise welfare (and 1-2 false economies to avoid for this breed specifically)
- Regional variation note (urban vs suburban US pricing)
- Rescue/adoption route cost comparison for this breed if plausible""",
    "grooming": """EXPANSION GUIDANCE for grooming-guide articles (reach 2,200-3,500 words with substance, not padding):
- Coat development timeline: puppy coat -> adult coat transition for THIS coat type, and how grooming changes at each stage
- Seasonal calendar: what shedding/coat care looks like across the year for this breed
- Complete tool list with technique: which brush/comb/tool, why for this coat, how to use it, what it costs
- Step-by-step bath protocol for this coat type (frequency, water temp, shampoo type, drying - especially drying time/method for this coat)
- DIY vs professional groomer: realistic schedule and annual cost for this breed, what to ask the groomer for
- Ears/nails/teeth/paws routine specific to this breed's known issues
- 3-5 common grooming mistakes owners of THIS breed make and the consequence of each
- Matting/blowout/stripping specifics if relevant to this coat type; skip irrelevant techniques""",
}


def build_user_prompt(data: dict, breed_facts: dict, forbidden: list[str],
                      cluster: str) -> str:
    payload = {
        "sections": data.get("sections") or {},
        "faq": data.get("faq") or [],
    }
    guidance = EXPANSION_GUIDANCE.get(cluster, "")
    return (
        f"BREED FACTS:\n{json.dumps(breed_facts, ensure_ascii=False, indent=1)}\n\n"
        f"{guidance}\n\n"
        f"FORBIDDEN BOILERPLATE (do not reuse these phrasings):\n"
        + "\n".join(f"- {s[:160]}" for s in forbidden[:20])
        + f"\n\nCURRENT ARTICLE JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def breed_facts_for(stem: str) -> dict:
    base = (
        stem.replace("-grooming-guide", "")
        .replace("-first-year-costs", "")
        .replace("-puppy-checklist", "")
    )
    main = BREED_DATA / f"{base}.json"
    facts: dict = {"breed_slug": base}
    if main.exists():
        try:
            d = json.loads(main.read_text(encoding="utf-8"))
            m = d.get("meta", {})
            facts["name"] = m.get("name")
            facts["akc_group"] = m.get("group")
            facts["size_category"] = m.get("size_category")
            facts["tagline"] = m.get("tagline")
            stats = d.get("stats") or {}
            for k in ("size", "weight", "lifespan", "coat", "shedding",
                      "energy", "trainability", "bark_level"):
                v = stats.get(k)
                if isinstance(v, dict) and v.get("value"):
                    facts[k] = v["value"]
            secs = d.get("sections") or {}
            for key in ("special", "care", "intro"):
                s = secs.get(key)
                if isinstance(s, dict) and s.get("html"):
                    txt = TAG.sub(" ", s["html"])
                    facts[f"main_article_{key}_excerpt"] = WS.sub(" ", txt)[:900]
        except (json.JSONDecodeError, OSError):
            pass
    return facts


def call_claude(api_key: str, model: str, system: str, user: str) -> str:
    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=300,
    )
    if resp.status_code == 429:
        raise RuntimeError("rate-limited")
    if resp.status_code != 200:
        raise RuntimeError(f"API {resp.status_code}: {resp.text[:300]}")
    blocks = resp.json().get("content", [])
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


def parse_rewrite(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def validate_rewrite(original: dict, rewritten: dict) -> str | None:
    """Return error string or None if OK."""
    secs_o = original.get("sections") or {}
    secs_r = rewritten.get("sections") or {}
    if set(secs_r.keys()) != set(secs_o.keys()):
        return f"section keys mismatch: {sorted(secs_r)} vs {sorted(secs_o)}"
    for k, s in secs_r.items():
        if not isinstance(s, dict) or not (s.get("html") or "").strip():
            return f"section {k} empty"
    faq_r = rewritten.get("faq")
    if not isinstance(faq_r, list) or len(faq_r) < max(1, len(original.get("faq") or []) - 1):
        return "faq missing or shrunk"
    for f in faq_r:
        if not isinstance(f, dict) or not f.get("q") or not f.get("a"):
            return "faq entry malformed"
    text = TAG.sub(" ", " ".join(s.get("html", "") for s in secs_r.values()))
    wc = len(text.split())
    if wc < MIN_WORDS_AFTER:
        return f"too short after rewrite: {wc} words (need {MIN_WORDS_AFTER}+)"
    links_o = set(re.findall(r'href="([^"]+)"', json.dumps(secs_o)))
    links_r = set(re.findall(r'href="([^"]+)"', json.dumps(secs_r)))
    missing = links_o - links_r
    if missing:
        return f"links dropped: {sorted(missing)[:3]}"
    return None


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def cmd_rewrite(limit: int, model: str) -> int:
    env = load_env()
    api_key = env.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit(
            "ANTHROPIC_API_KEY not found in .env or environment.\n"
            "Add a line to .env:  ANTHROPIC_API_KEY=sk-ant-...\n"
            "(You already have one in GitHub Secrets for seo-autofix; "
            "or create a new key at console.anthropic.com)"
        )
    if not TARGETS_PATH.exists():
        sys.exit("Run --audit first to produce detemplatize-targets.json")
    tconf = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    targets: dict = tconf["targets"]
    boiler: dict = tconf["boilerplate"]
    state = load_state()

    pending = [
        (stem, info)
        for stem, info in sorted(
            targets.items(), key=lambda kv: -kv[1]["templated_fraction"]
        )
        if state.get(stem, {}).get("status") != "done"
    ]
    if limit:
        pending = pending[:limit]
    print(f"Rewriting {len(pending)} articles (model={model})")

    ok = failed = 0
    for idx, (stem, info) in enumerate(pending, 1):
        path = BREED_DATA / f"{stem}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            wc_before = len(article_text(data).split())
            facts = breed_facts_for(stem)
            forbidden = boiler.get(info["cluster"], [])
            user = build_user_prompt(data, facts, forbidden, info["cluster"])
            rewritten = None
            for attempt in (1, 2):
                try:
                    raw = call_claude(api_key, model, REWRITE_SYSTEM, user)
                    rewritten = parse_rewrite(raw)
                    err = validate_rewrite(data, rewritten)
                    if err is None:
                        break
                    if attempt == 2:
                        raise RuntimeError(f"validation failed: {err}")
                    user += (
                        f"\n\nYOUR PREVIOUS ATTEMPT FAILED VALIDATION: {err}. "
                        f"Fix this and output the full corrected JSON."
                    )
                except (json.JSONDecodeError, RuntimeError) as e:
                    if attempt == 2:
                        raise
                    if "rate-limited" in str(e):
                        time.sleep(30)
            data["sections"] = rewritten["sections"]
            data["faq"] = rewritten["faq"]
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
                newline="\n",
            )
            wc_after = len(article_text(data).split())
            state[stem] = {
                "status": "done",
                "cluster": info["cluster"],
                "words_before": wc_before,
                "words_after": wc_after,
                "model": model,
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            ok += 1
            print(f"  [{idx}/{len(pending)}] OK    {stem}  {wc_before}w -> {wc_after}w")
        except Exception as e:
            state[stem] = {"status": "failed", "error": str(e)[:300],
                           "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            failed += 1
            print(f"  [{idx}/{len(pending)}] FAIL  {stem}: {str(e)[:160]}", file=sys.stderr)
        save_state(state)
        time.sleep(0.5)

    done_total = sum(1 for v in state.values() if v.get("status") == "done")
    print(f"\nThis run: ok={ok} failed={failed}")
    print(f"Total done: {done_total}/{len(targets)}")
    if done_total:
        print("\nNext: push with generate.py --update (slug list in detemplatize-state.json)")
    return 0 if failed == 0 else 1


# ---------------------------------------------------------------- verify

def cmd_verify() -> int:
    clusters = load_clusters()
    random.seed(42)
    for t in ("costs", "grooming", "checklist"):
        paths = clusters.get(t, [])
        frac, _ = cluster_stats(paths)
        avg = sum(frac.values()) / max(len(frac), 1)
        worst = sorted(frac.items(), key=lambda kv: -kv[1])[:3]
        texts = {}
        for p in paths:
            bw = breed_words_for(p.stem)
            texts[p.stem] = (article_text(json.loads(p.read_text(encoding="utf-8"))), bw)
        stems = list(texts)
        sims = []
        seen = set()
        max_pairs = min(150, len(stems) * (len(stems) - 1) // 2)
        while len(seen) < max_pairs:
            a, b = random.sample(stems, 2)
            key = (min(a, b), max(a, b))
            if key in seen:
                continue
            seen.add(key)
            sa = shingle_set(*texts[a])
            sb = shingle_set(*texts[b])
            if sa and sb:
                sims.append(len(sa & sb) / len(sa | sb))
        sims.sort()
        med = sims[len(sims) // 2] * 100 if sims else 0
        mx = sims[-1] * 100 if sims else 0
        print(f"{t:<10} boiler={avg*100:.0f}%  pair-sim med/max={med:.0f}%/{mx:.0f}%  "
              f"worst: {', '.join(f'{s[:34]}({f*100:.0f}%)' for s, f in worst)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="De-templatize duplicated Wooffy articles")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--rewrite", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="max articles this run")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()
    if args.audit:
        return cmd_audit()
    if args.rewrite:
        return cmd_rewrite(args.limit, args.model)
    if args.verify:
        return cmd_verify()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
