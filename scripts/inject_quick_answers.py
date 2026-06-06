"""Inject a "Quick Answer" box at the TOP of each nutrition article's
body_html. Goal: featured-snippet eligibility on Google + clean
extractable answer for LLM citations (ChatGPT, Gemini, Bing Copilot).

Format: a visually distinct 50-80 word direct-answer box, marked with
<!-- WOOFFY_QUICK_ANSWER_v1 --> for idempotency. Placed immediately
after any <meta> tag at the start of body_html so it is the first
visible content.

Idempotent: skips articles that already contain the marker.

Usage:
  python3 scripts/inject_quick_answers.py           # dry-run
  python3 scripts/inject_quick_answers.py --apply   # write to JSONs
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DIR = ROOT / "breed-data"

MARKER = "<!-- WOOFFY_QUICK_ANSWER_v1 -->"

# (slug, plain-text Quick Answer 50-80 words)
ANSWERS: list[tuple[str, str]] = [
    ("can-dogs-eat-quinoa",
     "Yes, dogs can eat quinoa in moderation when it is cooked plain "
     "and rinsed thoroughly before cooking to remove bitter saponins. "
     "Quinoa is a complete protein with all nine essential amino acids "
     "plus fiber, magnesium, and iron. Avoid feeding quinoa to dogs "
     "with kidney disease or a history of calcium oxalate stones."),
    ("can-dogs-eat-blueberries",
     "Yes, dogs can eat blueberries safely as a low-calorie treat. "
     "Wash them thoroughly and serve fresh or frozen, whole or mashed "
     "into food. Blueberries are rich in antioxidants, vitamin C, and "
     "fiber. Limit to a small handful for medium-sized dogs to avoid "
     "digestive upset, and skip for dogs with diabetes."),
    ("can-dogs-eat-butternut-squash-a-nutritious-addition-to-your-dogs-diet",
     "Yes, dogs can eat butternut squash when it is cooked plain and "
     "served in small amounts. It provides fiber, vitamin A, and "
     "beta-carotene that support digestion and immune health. Always "
     "remove the skin and seeds and never feed raw squash, which is "
     "hard to digest. Avoid recipes with butter, salt, or seasoning."),
    ("can-dogs-eat-chicken-breast",
     "Yes, plain cooked chicken breast is safe and beneficial for "
     "dogs as a lean protein source for muscle maintenance. Cook it "
     "thoroughly with no oil, salt, garlic, or seasoning and remove "
     "all bones before serving. Skip chicken for dogs with a "
     "diagnosed poultry allergy or chronic itchy skin condition."),
    ("can-dogs-eat-eggplant",
     "Eggplant is generally safe for dogs in small cooked amounts but "
     "is not necessary in their diet. Skip raw eggplant, which is "
     "hard to digest, and never serve dishes prepared with garlic, "
     "onion, or heavy seasoning. Avoid eggplant entirely for dogs "
     "with kidney issues or arthritis due to its oxalate content."),
    ("can-dogs-eat-salmon",
     "Yes, cooked salmon is safe and rich in omega-3 fatty acids that "
     "support a dog's skin, coat, joints, and brain. Always cook the "
     "fish thoroughly to kill parasites, debone it carefully, and "
     "serve plain. Never feed raw salmon — it can transmit fatal "
     "salmon poisoning disease (Neorickettsia helminthoeca)."),
    ("can-dogs-eat-sunflower-seeds",
     "Sunflower seeds are safe in tiny amounts only when they are "
     "shelled, unsalted, and plain. Whole seeds with shells can "
     "damage the digestive tract. Avoid salted, roasted, or flavored "
     "varieties. Not a recommended regular treat because the high "
     "fat content can contribute to weight gain or trigger pancreatitis."),
    ("can-dogs-have-almond-butter",
     "Plain unsweetened almond butter is safe for dogs in tiny "
     "amounts as an occasional treat (no more than half a teaspoon "
     "for small dogs). Always verify the ingredient list contains no "
     "xylitol, which is highly toxic to dogs. Skip almond butter for "
     "dogs with a history of pancreatitis due to its high fat content."),
    ("carrots-for-dogs",
     "Yes, carrots are an excellent low-calorie treat for dogs and a "
     "natural source of fiber, beta-carotene, and potassium. Serve "
     "raw as a crunchy chew that helps clean teeth, or cooked plain "
     "for easier digestion. Cut into appropriately sized pieces to "
     "prevent choking, especially for small breeds and puppies."),
    ("why-pumpkin-is-good-for-dogs",
     "Plain cooked pumpkin or pure pumpkin puree (never pumpkin pie "
     "filling) is highly beneficial for dogs. Its soluble fiber helps "
     "with both diarrhea and constipation, and it is rich in vitamin "
     "A and antioxidants. Start with one to two teaspoons per ten "
     "pounds of body weight and adjust based on tolerance."),
]


def render_box(answer_text: str) -> str:
    return (
        f"\n{MARKER}\n"
        f'<div class="quick-answer" style="background:#f8f8f8;'
        f'padding:16px 22px;border-left:4px solid #1a1a1a;'
        f'margin:0 0 28px 0;border-radius:6px;">\n'
        f'<p style="margin:0;font-size:1.05em;line-height:1.6;">'
        f'<strong>Quick Answer:</strong> {answer_text}'
        f'</p>\n'
        f'</div>\n'
    )


def inject(raw: str, box_html: str) -> str | None:
    if MARKER in raw:
        return None
    m = re.search(
        r'("body_html"\s*:\s*")((?:[^"\\]|\\.)*?)(")',
        raw, re.DOTALL,
    )
    if not m:
        return None
    body_open, body_value, body_close = m.group(1), m.group(2), m.group(3)
    box_escaped = (box_html
                   .replace("\\", "\\\\")
                   .replace("\"", "\\\"")
                   .replace("\n", "\\n"))
    meta_match = re.match(r"(<meta charset=\\\"utf-8\\\">\\n)", body_value)
    if meta_match:
        prefix = body_value[: meta_match.end()]
        suffix = body_value[meta_match.end():]
        new_body = prefix + box_escaped + suffix
    else:
        new_body = box_escaped + body_value
    return raw[:m.start()] + body_open + new_body + body_close + raw[m.end():]


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    stats = {"would": 0, "already": 0, "skipped": 0, "applied": 0}
    for slug, answer in ANSWERS:
        path = BREED_DIR / f"{slug}.json"
        if not path.exists():
            print(f"[{slug}] SKIP: JSON missing")
            stats["skipped"] += 1
            continue
        raw = path.read_text(encoding="utf-8")
        if MARKER in raw:
            print(f"[{slug}] already injected")
            stats["already"] += 1
            continue
        box = render_box(answer)
        new_raw = inject(raw, box)
        if new_raw is None:
            print(f"[{slug}] SKIP: body_html not found / parse fail")
            stats["skipped"] += 1
            continue
        if apply:
            path.write_text(new_raw, encoding="utf-8", newline="\n")
            print(f"[{slug}] APPLIED ({len(answer)} chars)")
            stats["applied"] += 1
        else:
            print(f"[{slug}] WOULD inject "
                  f"({len(answer)} chars: {answer[:60]}...)")
            stats["would"] += 1
    print(f"\nStats: {json.dumps(stats, indent=2)}")
    if not apply and stats["would"] > 0:
        print("\nRe-run with --apply to write changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
