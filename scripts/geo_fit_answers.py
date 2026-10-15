"""Direct "is this breed right for me?" answers on the 172 main guides (GEO_PLAN W2.4 / fit gap).

The 2026-10-15 citation audit scored 0/15 on fit questions ("is a border
collie good for first time owners", "are golden retrievers good apartment
dogs", "is a great dane good with kids"). The guides hold the facts (stats,
the good-fit / not-fit lists, the temperament, care and first-person
sections) but never answer those questions in one place.

This script asks Claude to write four short, direct answers per breed
using ONLY the page's own text, and stores them in
sections.right_for_you.fit_answers = [{"q": ..., "a": ...}, ...].
generate.py renders them at the top of the "Is a … right for you?"
section and adds them to the page's FAQPage JSON-LD.

Guardrails:
  - every number in an answer must already appear in the source text
  - 15-70 words, opens with a verdict (Yes / No / It depends / Only if …)
  - a question the page cannot support is returned as null and skipped
  - resumable: pages that already have fit_answers are skipped (--overwrite
    to redo); results are written per page as they come back

Cost: ~3-4k input + ~300 output tokens per page on claude-opus-5-5,
roughly $3-5 for all 172.

Usage:
    python3 scripts/geo_fit_answers.py --dry-run            # show the panel of pages
    python3 scripts/geo_fit_answers.py --limit 3            # try three
    python3 scripts/geo_fit_answers.py                      # all remaining
    python3 scripts/geo_fit_answers.py --slug akita --overwrite
Env: ANTHROPIC_API_KEY (or .env).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BD = os.path.join(ROOT, "breed-data")
API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-opus-5-5"

QUESTIONS = [
    ("first_time", "Is {a} {Breed} a good dog for first-time owners?"),
    ("apartment", "Can {a} {Breed} live in an apartment?"),
    ("kids", "Is {a} {Breed} good with kids?"),
    ("exercise", "How much exercise does {a} {Breed} need?"),
]
VERDICT = re.compile(r"^(Yes|No|Not|It depends|Only|Usually|Rarely|Sometimes|Mostly|Generally|With|Expect|Plan|About|Around|At least|A lot|Less|More|Moderately|Very|Possibly|Probably)\b", re.I)

SYSTEM = (
    "You write short, factual answers for a dog-breed guide's 'Is this breed right for you?' section. "
    "Use ONLY the facts in the page excerpts you are given; never add numbers, health claims or breed "
    "facts that are not in them. Each answer: 15-70 words, starts with a direct verdict (Yes / No / "
    "It depends / Only if ...), then one or two concrete reasons taken from the page, in plain "
    "second-person prose that a consumer AI assistant could quote. If the page genuinely does not "
    "support an answer to a question, return null for it instead of guessing. "
    "Respond with a single JSON object and nothing else."
)


def load_env():
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip() or load_env().get("ANTHROPIC_API_KEY", "")
    if not key:
        sys.exit("ANTHROPIC_API_KEY not set (env or .env)")
    return key


def load(slug):
    with open(os.path.join(BD, f"{slug}.json"), encoding="utf-8") as f:
        return json.load(f)


def save(slug, data):
    with open(os.path.join(BD, f"{slug}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def is_main(slug, data):
    m = data.get("meta") or {}
    sc = (m.get("size_category") or "").lower()
    if "body_html" in data or "-vs-" in slug or sc in ("guide", "roundup", "comparison"):
        return False
    return not slug.endswith(("-grooming-guide", "-first-year-costs", "-puppy-checklist"))


def strip(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def article(name):
    return "an" if name[:1].lower() in "aeiou" else "a"


def source_text(data):
    """The page facts the model may use, as plain text."""
    m, s = data["meta"], data.get("sections") or {}
    parts = [f"Breed: {m['name']}"]
    st = data.get("stats") or {}
    if st:
        parts.append("Stats: " + "; ".join(f"{v.get('label', k)}: {v.get('value')}" for k, v in st.items()))
    r = s.get("right_for_you") or {}
    if r.get("good_fit"):
        parts.append("Great fit if you: " + " | ".join(r["good_fit"]))
    if r.get("not_fit"):
        parts.append("Not the best fit if you: " + " | ".join(r["not_fit"]))
    for key in ("temperament", "care", "mikes_take", "intro"):
        sec = s.get(key) or {}
        if sec.get("html"):
            parts.append(f"{key.replace('_', ' ').title()}: " + strip(sec["html"])[:2500])
    for fq in (data.get("faq") or [])[:6]:
        parts.append(f"FAQ: {fq.get('q')} {fq.get('a')}")
    qa = (m.get("quick_answer") or "").strip()
    if qa:
        parts.append("Quick answer: " + qa)
    return "\n\n".join(parts)


def build_prompt(data):
    name = data["meta"]["name"]
    a = article(name)
    qs = "\n".join(f'- "{key}": {tmpl.format(a=a, Breed=name)}' for key, tmpl in QUESTIONS)
    return (
        f"PAGE EXCERPTS\n{source_text(data)}\n\nQUESTIONS (answer each as a JSON string, or null)\n{qs}\n\n"
        'Output exactly: {"first_time": ..., "apartment": ..., "kids": ..., "exercise": ...}'
    )


def call_claude(key, model, prompt):
    body = json.dumps({
        "model": model,
        "max_tokens": 900,
        "system": SYSTEM,
        "output_config": {"effort": "low"},
        "fallbacks": "default",
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    delay = 5.0
    for attempt in range(5):
        req = urllib.request.Request(API_URL, data=body, method="POST")
        req.add_header("x-api-key", key)
        req.add_header("anthropic-version", "2023-06-01")
        req.add_header("anthropic-beta", "server-side-fallback-2026-07-01")
        req.add_header("content-type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                resp = json.loads(r.read())
            if resp.get("stop_reason") == "refusal":
                raise RuntimeError("refusal")
            return "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:300]
            if e.code in (408, 409, 429) or e.code >= 500:
                print(f"    HTTP {e.code}, retry in {delay:.0f}s", file=sys.stderr)
                time.sleep(delay); delay = min(delay * 2, 90)
                continue
            raise RuntimeError(f"API {e.code}: {text}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"    connection error, retry in {delay:.0f}s: {e}", file=sys.stderr)
            time.sleep(delay); delay = min(delay * 2, 90)
    raise RuntimeError("API: gave up after retries")


def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[A-Za-z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    return json.loads(text)


NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def validate(answer, source):
    """Return a reason string if the answer must be rejected, else None."""
    if not isinstance(answer, str) or not answer.strip():
        return "empty"
    a = answer.strip()
    n = len(a.split())
    if n < 15 or n > 70:
        return f"{n} words"
    if not VERDICT.match(a):
        return "no verdict opener"
    src_nums = set(NUM.findall(source))
    extra = [x for x in NUM.findall(a) if x not in src_nums]
    if extra:
        return f"numbers not in source: {extra}"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--slug", action="append")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--overwrite", action="store_true", help="redo pages that already have fit_answers")
    ap.add_argument("--dry-run", action="store_true", help="list the pages that would be processed; no API calls")
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args(argv)

    slugs = args.slug or sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(BD, "*.json")))
    todo = []
    for slug in slugs:
        data = load(slug)
        if not is_main(slug, data):
            continue
        r = (data.get("sections") or {}).get("right_for_you") or {}
        if r.get("fit_answers") and not args.overwrite:
            continue
        todo.append(slug)
    if args.limit:
        todo = todo[: args.limit]
    if args.dry_run:
        print("\n".join(todo)); print(f"\n{len(todo)} pages to process (model {args.model})")
        return 0
    if not todo:
        print("nothing to do (all main guides already have fit_answers)")
        return 0

    key = api_key()
    done = failed = 0
    rejected = []
    for i, slug in enumerate(todo, 1):
        data = load(slug)
        name = data["meta"]["name"]
        print(f"[{i}/{len(todo)}] {slug}")
        try:
            obj = parse_json(call_claude(key, args.model, build_prompt(data)))
        except (RuntimeError, ValueError) as e:
            print(f"    FAILED: {e}", file=sys.stderr); failed += 1
            continue
        src = source_text(data)
        out = []
        for qkey, tmpl in QUESTIONS:
            ans = obj.get(qkey)
            if ans is None:
                continue
            why = validate(ans, src)
            if why:
                rejected.append((slug, qkey, why)); print(f"    reject {qkey}: {why}")
                continue
            out.append({"q": tmpl.format(a=article(name), Breed=name), "a": ans.strip()})
        if len(out) < 2:
            print(f"    only {len(out)} usable answers; not written"); failed += 1
            continue
        data["sections"]["right_for_you"]["fit_answers"] = out
        save(slug, data)
        done += 1
        for item in out:
            print(f"    {item['q']}\n      {item['a'][:110]}")
        time.sleep(args.sleep)
    print(f"\nwrote fit answers on {done} guides; failed {failed}; rejected answers {len(rejected)}")
    changed = [s for s in todo if (load(s)["sections"]["right_for_you"]).get("fit_answers")]
    print("slugs with fit answers (STDOUT last line):")
    print(" ".join(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
