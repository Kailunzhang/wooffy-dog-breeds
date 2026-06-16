"""One-shot: optimize the Portuguese Water Dog grooming guide for AI
Overview citation. Adds:
  1. Quick Answer block at top of intro
  2. Schedule-by-life-stage table inside intro
  3. Common Mistakes + What Pro Grooming Should Include sections in special
  4. 5 new FAQ entries

Idempotent via marker WOOFFY_AI_OVERVIEW_v1.

Run:
    python3 scripts/seo_ai_overview_pwd.py
    echo YES | python3 scripts/generate.py portuguese-water-dog-grooming-guide --update
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "breed-data" / "portuguese-water-dog-grooming-guide.json"

MARKER = "<!-- WOOFFY_AI_OVERVIEW_v1 -->"
QA_MARKER = "<!-- WOOFFY_QUICK_ANSWER_v1 -->"
INTERNAL = "<!-- WOOFFY_INTERNAL_LINKS_v1 -->"


QUICK_ANSWER = f"""{MARKER}
{QA_MARKER}
<div class="quick-answer" style="background:#f8f8f8;padding:16px 22px;border-left:4px solid #1a1a1a;margin:0 0 28px 0;border-radius:6px;">
<p style="margin:0;font-size:1.05em;line-height:1.6;"><strong>Quick Answer:</strong> Portuguese Water Dogs need a professional trim every <strong>6 to 8 weeks</strong>, plus brushing 3&ndash;4 times per week (daily for longer curly coats), bathing every 3&ndash;4 weeks, weekly ear cleaning, and nail trims every 3&ndash;4 weeks. The single-layer curly coat has no undercoat to shed, so loose hairs tangle into the coat and mat tightly without regular grooming. Most pet owners choose the retriever clip (uniform 1&ndash;1.5 inches all over) for easier upkeep between appointments.</p>
</div>
"""


SCHEDULE_TABLE = """
<h3>Grooming Schedule by Life Stage</h3>
<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:0.95em;">
<thead><tr style="background:#f0f0f0;text-align:left;"><th style="padding:10px;border:1px solid #ddd;">Life stage</th><th style="padding:10px;border:1px solid #ddd;">Home brushing</th><th style="padding:10px;border:1px solid #ddd;">Professional trim</th><th style="padding:10px;border:1px solid #ddd;">Bathing</th></tr></thead>
<tbody>
<tr><td style="padding:10px;border:1px solid #ddd;"><strong>Puppy (3&ndash;6 mo)</strong></td><td style="padding:10px;border:1px solid #ddd;">5&times;/week, short positive sessions</td><td style="padding:10px;border:1px solid #ddd;">First trim at 4 mo; light puppy clip</td><td style="padding:10px;border:1px solid #ddd;">Monthly</td></tr>
<tr><td style="padding:10px;border:1px solid #ddd;"><strong>Adult coat-in (6&ndash;18 mo)</strong></td><td style="padding:10px;border:1px solid #ddd;">Daily &mdash; coat is changing</td><td style="padding:10px;border:1px solid #ddd;">Every 6 weeks</td><td style="padding:10px;border:1px solid #ddd;">Every 3 weeks</td></tr>
<tr><td style="padding:10px;border:1px solid #ddd;"><strong>Adult mature (1.5&plus; yr)</strong></td><td style="padding:10px;border:1px solid #ddd;">3&ndash;4&times;/week</td><td style="padding:10px;border:1px solid #ddd;">Every 6&ndash;8 weeks</td><td style="padding:10px;border:1px solid #ddd;">Every 3&ndash;4 weeks</td></tr>
<tr><td style="padding:10px;border:1px solid #ddd;"><strong>Senior (7&plus; yr)</strong></td><td style="padding:10px;border:1px solid #ddd;">3&times;/week, gentle handling</td><td style="padding:10px;border:1px solid #ddd;">Every 8&ndash;10 weeks</td><td style="padding:10px;border:1px solid #ddd;">Every 4&ndash;5 weeks</td></tr>
</tbody>
</table>
<p>The 6&ndash;8 week professional trim cadence is the breed standard. Going beyond 8 weeks causes mats that tighten against the skin and may require a full shave-down to resolve.</p>
"""


COMMON_MISTAKES = f"""
{MARKER}
<h3>Common Grooming Mistakes That Cost Owners Money</h3>
<p>The five mistakes that show up most often in veterinary skin-clinic visits and groomer complaints, all preventable:</p>
<ol>
<li><strong>Brushing the surface but not the skin.</strong> The slicker brush has to reach the base of the coat. Mats form against the skin first, then grow outward. If you only brush the top layer, the coat looks fine while the dog has tight mats underneath that develop into hot spots and skin infections.</li>
<li><strong>Skipping the ear-canal hair removal.</strong> PWDs grow hair inside the ear canal. If your groomer is not removing it at every appointment, water and debris get trapped &mdash; this is the single most common cause of chronic ear infections in the breed. Ask explicitly: &ldquo;Did you pluck the ears today?&rdquo;</li>
<li><strong>Letting the coat go past 8 weeks.</strong> A retriever clip looks fine for 7 weeks, then mats form quickly in week 8&ndash;10. The cost of dematting at the groomer ($30&ndash;$80 add-on) plus the dog's discomfort is much higher than just staying on schedule.</li>
<li><strong>Using human shampoo or detergent-based dog shampoos.</strong> The PWD's single-layer coat dries out quickly. Use a moisturizing dog shampoo designed for curly coats; rinse thoroughly to avoid skin irritation; follow with a leave-in conditioner spray during brushing.</li>
<li><strong>Shaving the coat in summer &ldquo;to help with heat.&rdquo;</strong> A PWD's coat does not insulate like a double-coated breed and shaving it does not cool the dog &mdash; it exposes skin to sun. Keep the standard retriever clip year-round; if heat is a concern, increase swimming and shade access, not shaving.</li>
</ol>

<h3>What Professional Grooming Should Include</h3>
<p>A complete PWD grooming appointment should cover all of these. If your groomer skips items, find a different one:</p>
<ul>
<li>Full body brush-out and de-mat check before bathing</li>
<li>Bath with curly-coat-specific shampoo, thorough rinse</li>
<li>High-velocity dryer to fully dry the coat (residual moisture causes mats)</li>
<li>Clip or scissor work in the chosen style (retriever, lion, modified)</li>
<li>Ear cleaning AND ear-canal hair removal (plucking)</li>
<li>Nail trim and grinding</li>
<li>Anal gland expression (optional, only if needed)</li>
<li>Sanitary trim (around the rear and underbelly)</li>
<li>Foot-pad trim (hair between the toes)</li>
</ul>
<p>Expect a 2.5&ndash;3.5 hour appointment for a full groom. Quality groomers do not rush PWDs &mdash; the coat requires careful work.</p>
"""


NEW_FAQS = [
    {
        "q": "What is the difference between curly and wavy Portuguese Water Dog coats?",
        "a": "Both are accepted in the breed standard. The curly coat is tighter and lies in compact ringlets close to the body; the wavy coat falls in longer loose waves with a slight sheen. The grooming routine is essentially the same for both — brushing 3–4 times per week and trimming every 6–8 weeks — but curly coats mat slightly faster and may benefit from daily brushing."
    },
    {
        "q": "How much does Portuguese Water Dog grooming cost per appointment?",
        "a": "Professional grooming for a Portuguese Water Dog costs $60–$100 per appointment in most US markets, or $80–$130 in higher-cost coastal cities. With trims every 6–8 weeks, expect an annual professional grooming budget of $450–$800. Mobile groomers or breed-specialist groomers typically charge at the higher end. Add $30–$80 if the dog requires dematting due to skipped brushing."
    },
    {
        "q": "When should a Portuguese Water Dog puppy get its first haircut?",
        "a": "Around 4 months of age. The first appointment should be a light positive introduction — bath, blow-dry, nail trim, and a very minor trim — not a full breed clip. The goal is socialization to the grooming process, not perfect coat work. Plan a second visit at 5–6 months for the first real trim, then transition to the regular 6–8 week schedule."
    },
    {
        "q": "Can I groom a Portuguese Water Dog at home?",
        "a": "Maintenance grooming yes; full professional-quality clips usually no. Brushing, bathing, ear cleaning, nail trimming, and minor sanitary trims are realistic at home. Full breed clips (lion or retriever) require professional clippers, blades, scissors, and skill — most owners outsource this. A reasonable hybrid is a professional clip every 6–8 weeks with home brushing and bathing between appointments."
    },
    {
        "q": "What is the best brush for a Portuguese Water Dog?",
        "a": "A medium slicker brush combined with a wide-tooth metal comb is the standard tool kit. Slicker brushes lift the coat and remove tangles; the metal comb checks for mats at the skin level. Avoid Furminator-style de-shedding tools — they are designed for double-coated breeds and damage the PWD's single-layer coat by cutting hair shafts."
    },
]


def main() -> int:
    d = json.loads(TARGET.read_text(encoding="utf-8"))
    intro_html = d["sections"]["intro"]["html"]
    special_html = d["sections"]["special"]["html"]

    if MARKER in intro_html or MARKER in special_html:
        print("SKIP: already optimized (marker present)")
        return 0

    intro_html = QUICK_ANSWER + intro_html + SCHEDULE_TABLE
    d["sections"]["intro"]["html"] = intro_html

    if INTERNAL in special_html:
        special_html = special_html.replace(
            INTERNAL, COMMON_MISTAKES + "\n" + INTERNAL, 1)
    else:
        special_html = special_html + COMMON_MISTAKES
    d["sections"]["special"]["html"] = special_html

    existing_q = {f.get("q", "").strip().lower() for f in d.get("faq", []) if isinstance(f, dict)}
    faq = d.get("faq", [])
    for f in NEW_FAQS:
        if f["q"].strip().lower() not in existing_q:
            faq.append(f)
    d["faq"] = faq

    TARGET.write_text(
        json.dumps(d, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    print("OK. New sizes:")
    for k in ("intro", "care", "special"):
        print(f"  sections.{k}.html: {len(d['sections'][k]['html'])} chars")
    print(f"  faq entries: {len(d['faq'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
