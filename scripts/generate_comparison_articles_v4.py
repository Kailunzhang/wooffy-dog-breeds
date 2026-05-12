"""Comparison articles batch v4 - 3-signal-validated picks PLUS 4 new content
section types based on content critique:

  - quick_answers      (AI-extractable short Q&A pairs for ChatGPT/Perplexity)
  - mikes_take         (first-person voice from Kailun Zhang)
  - mistakes           (Mistake Index - 3-5 common buyer mistakes per breed)
  - breeder_vetting    (specific questions to ask + red flags)

Plus a "Last updated May 2026" timestamp in each intro section.

Articles in this batch:
  golden-retriever-vs-german-shepherd
  cane-corso-vs-great-dane
  bernedoodle-vs-aussiedoodle
  vizsla-vs-german-shorthaired-pointer
  great-dane-vs-doberman

Writes breed-data/{slug}.json files. Run scripts/generate.py --publish to push.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"
PLACEHOLDER_HERO = "https://cdn.shopify.com/s/files/1/0554/5253/2790/files/comparison-goldendoodle-vs-labradoodle-hero.png"

UPDATED_LINE = (
    '<p style="font-size:0.8em;color:#999;margin:24px 0 0 0;text-align:right;">'
    'Last updated May 2026 - by Kailun Zhang</p>'
)


def style_p(text: str) -> str:
    return f'<p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 20px 0;">{text}</p>'


def style_h3(text: str) -> str:
    return f'<h3 style="font-size:1.15em;font-weight:700;color:#1a1a1a;margin:24px 0 12px 0;">{text}</h3>'


def comparison_table(rows, headers):
    th = (
        '<div style="overflow-x:auto;margin:0 0 20px 0;">'
        '<table style="width:100%;border-collapse:collapse;font-size:0.9em;line-height:1.6;">'
        '<thead><tr style="border-bottom:2px solid #1a1a1a;">'
        + "".join(f'<th style="text-align:left;padding:10px 8px;color:#1a1a1a;font-weight:700;">{h}</th>' for h in headers)
        + '</tr></thead><tbody>'
    )
    body = "".join(
        f'<tr style="border-bottom:1px solid #e8e8e8;">'
        f'<td style="padding:10px 8px;color:#1a1a1a;font-weight:600;">{a}</td>'
        f'<td style="padding:10px 8px;color:#6b7177;">{b}</td>'
        f'<td style="padding:10px 8px;color:#6b7177;">{c}</td>'
        f'</tr>'
        for a, b, c in rows
    )
    return th + body + "</tbody></table></div>"


def _make_meta(name, slug, group, tagline, tags, excerpt, meta_description):
    return {
        "name": name, "slug": slug, "shopify_handle": slug,
        "group": group, "size_category": "Comparison",
        "tagline": tagline, "tags": tags,
        "published": True, "published_at": None,
        "excerpt": excerpt, "meta_description": meta_description,
    }


def build_quick_answers(qa_pairs):
    items = "".join(
        f'<div style="margin-bottom:14px;">'
        f'<p style="font-size:0.9em;font-weight:700;color:#1a1a1a;margin:0 0 4px 0;">Q: {q}</p>'
        f'<p style="font-size:0.9em;color:#6b7177;line-height:1.6;margin:0;">A: {a}</p>'
        f'</div>'
        for q, a in qa_pairs
    )
    return (
        '<p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 16px 0;">'
        'Short answers to the questions most people ask before comparing these two:</p>'
        + items
    )


def build_mistakes(left_breed, left_mistakes, right_breed, right_mistakes):
    def render_list(items):
        return "".join(
            f'<li style="margin-bottom:10px;">'
            f'<strong style="color:#1a1a1a;">{title}.</strong> '
            f'<span style="color:#6b7177;">{detail}</span></li>'
            for title, detail in items
        )
    return (
        style_p("These are the most common buyer mistakes Wooffy sees come up repeatedly in owner forums and rescue intake stories. Knowing them ahead of time is the cheapest way to avoid 3-5 years of regret.")
        + style_h3(f"Mistakes new {left_breed} owners often make")
        + f'<ul style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 24px 0;padding-left:20px;">{render_list(left_mistakes)}</ul>'
        + style_h3(f"Mistakes new {right_breed} owners often make")
        + f'<ul style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0;padding-left:20px;">{render_list(right_mistakes)}</ul>'
    )


def build_mikes_take(text_html):
    return (
        '<div style="background:#faf7f0;border-left:4px solid #1a1a1a;padding:20px 24px;'
        'margin:0 0 24px 0;border-radius:4px;">'
        '<p style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.7em;'
        'font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);'
        'margin:0 0 12px 0;">A first-time owner\'s take</p>'
        + text_html
        + '</div>'
    )


def build_breeder_vetting(left_breed, left_questions, right_breed, right_questions, red_flags):
    def render_questions(items):
        return "".join(f'<li style="margin-bottom:8px;color:#6b7177;">{q}</li>' for q in items)
    return (
        style_p("Both breeds have committed reputable breeders and a wide pool of backyard breeders with no health testing. The questions below separate the two.")
        + style_h3(f"Ask any {left_breed} breeder")
        + f'<ol style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 20px 0;padding-left:24px;">{render_questions(left_questions)}</ol>'
        + style_h3(f"Ask any {right_breed} breeder")
        + f'<ol style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 20px 0;padding-left:24px;">{render_questions(right_questions)}</ol>'
        + style_h3("Red flags - walk away if you see any of these")
        + f'<ul style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0;padding-left:20px;">{render_questions(red_flags)}</ul>'
    )


# ── 1. golden-retriever-vs-german-shepherd ───────────────────────────────────

def build_golden_vs_gsd():
    headers = ("Attribute", "Golden Retriever", "German Shepherd")
    rows = [
        ("Origin", "Scotland, 1860s - retrieving waterfowl", "Germany, 1899 - herding sheep"),
        ("Size", "55-75 lbs, 20-24 in", "65-90 lbs, 22-26 in"),
        ("Lifespan", "10-12 years", "9-13 years"),
        ("Coat", "Long flowing golden double coat", "Medium double coat in black-and-tan saddle"),
        ("Shedding", "Heavy year-round + seasonal blows", "Heavy year-round + seasonal blows"),
        ("Energy level", "Moderate-high", "High"),
        ("Trainability", "Excellent - eager, food-motivated", "Excellent - among top working intelligences"),
        ("Stranger reception", "Friendly with everyone", "Reserved, slow to warm"),
        ("Protective instinct", "Low - greets strangers as friends", "Strong - natural watchdog"),
        ("Main health risks", "Cancer (~60% lifetime), hip dysplasia", "Hip/elbow dysplasia, DM, bloat"),
        ("Cost (reputable)", "$1,500-$3,000", "$1,500-$3,500"),
        ("Best for", "Calm family households wanting friendly companion", "Active families wanting protective working partner"),
    ]
    quick_answers = build_quick_answers([
        ("Which is better with strangers?", "Golden Retriever - friendly with everyone. German Shepherds are reserved and protective by breed standard. If you have frequent visitors, Golden is the easier fit."),
        ("Which sheds more?", "Both shed heavily. Goldens lose more loose hair year-round due to longer coat; GSDs blow coat dramatically twice a year. Net effect over a year is similar."),
        ("Which lives longer?", "GSD averages slightly longer (9-13 vs Golden's 10-12), primarily because Goldens face exceptional cancer rates (~60% lifetime). Lean weight management extends both."),
        ("Which is better for first-time owners?", "Golden Retriever, clearly. Goldens are more forgiving of new-owner mistakes. GSDs require firm consistency and early socialization; mismatched handling produces reactive or anxious dogs."),
        ("Which has higher cancer risk?", "Golden Retriever. Approximately 60% of Goldens die of cancer (Morris Animal Foundation Golden Retriever Lifetime Study) - the highest documented rate of any breed. GSD cancer rates are elevated above mixed-breed but well below Golden's."),
    ])
    mistakes = build_mistakes(
        "Golden Retriever",
        [
            ("Buying without checking cancer rates", "Goldens have one of the highest lifetime cancer rates of any breed (~60%). Enrolling in pet insurance before the first vet visit is the single highest-ROI decision."),
            ("Choosing 'rare color' Goldens (white, mahogany red, English cream)", "Many extreme colors come from breeders selecting for visual novelty over health testing. Stick to OFA-tested breeders regardless of color preference."),
            ("Underestimating shedding", "Goldens shed year-round AND blow coat twice a year. Households with shedding-sensitive members regret the choice; budget for 2-3x weekly brushing."),
            ("Skipping early field/water exposure", "Goldens were bred to retrieve waterfowl. Without exposure to fetch games and swimming, many adult Goldens develop low-grade restlessness."),
        ],
        "German Shepherd",
        [
            ("Buying the dramatic sloped-back show-line dog", "American Show Line GSDs have controversial back slopes that contribute to hip and spine issues. West German Working Line or West German Show Line have moderate angulation."),
            ("Skipping early socialization 'because they're smart'", "Intelligence is not socialization. Under-socialized GSDs develop reactive, fearful, or aggressive behavior with strangers. Puppy class by 12 weeks is non-negotiable."),
            ("Buying a working-line dog for pet life", "Czech, DDR, and West German working-line GSDs need 90+ minutes of structured work daily. As pet dogs in average homes they develop neurotic behaviors."),
            ("Not budgeting for hip/elbow issues", "Hip and elbow dysplasia is statistically likely even with OFA-tested parents. Pet insurance covering orthopedic surgery from puppyhood is essential."),
            ("Not preparing for DM (Degenerative Myelopathy)", "DM affects ~5% of GSDs and is more common in older dogs. DNA testing of both parents identifies risk; preparing emotionally and financially for end-of-life mobility loss matters."),
        ],
    )
    mikes_take = build_mikes_take(
        style_p("When my friend was deciding between these two, what tipped him toward Golden was a specific moment: he visited a Golden breeder where the 9-year-old grand-sire was asleep on the floor while toddlers climbed on him. He couldn't picture the same scene with the local GSD breeder's dogs - the adult GSDs there were polite but watchful, not soft-asleep-with-toddlers.")
        + style_p("Neither dog is wrong. The Golden's softness comes with the cancer reality (his uncle's first Golden died at 7 of hemangiosarcoma; he knew this going in). The GSD's watchful intelligence comes with the responsibility of structured training - if you'll skip puppy class, get a Golden.")
    )
    breeder_vetting = build_breeder_vetting(
        "Golden Retriever",
        [
            'Show me OFA hip and elbow certificates for both parents (Fair or higher).',
            'OFA cardiac clearance on both parents - any heart murmurs detected?',
            'CAER eye exam on both parents - any abnormalities?',
            'PRA-prcd DNA test results on both parents - clear or carrier?',
            'How old are the grandparents and what are their causes of death?',
            'Do you participate in the Morris Animal Foundation Golden Retriever Lifetime Study?',
        ],
        "German Shepherd",
        [
            'OFA hip and elbow certificates for both parents (Good or Excellent preferred).',
            'DM (Degenerative Myelopathy) DNA test results on both parents.',
            'Which line do you breed (American Show, West German Show, West German Working, Czech, DDR)?',
            'How do you assess temperament before placing puppies?',
            'Can I meet the dam in person? May I see the actual whelping setup?',
            'What is your puppy-back guarantee for genetic conditions?',
        ],
        [
            'Cannot or will not provide written OFA certificates from a 3rd-party registry.',
            'Has multiple litters available year-round - reputable breeders have at most 1-2 litters per year.',
            'Charges premium pricing for "rare" colors or sizes (mini, teacup, white) - these are red flags.',
            'Refuses to let you visit the parents in person or won\'t share parents\' OFA database links.',
            'Says "hybrid vigor" or "we don\'t need testing because our line is healthy".',
            'Sells puppies before 8 weeks old, or to anyone who passes a credit-card check without a screening interview.',
        ],
    )
    sections = {
        "intro": {"label":"Overview","heading":"Golden Retriever vs German Shepherd: The Quick Answer",
            "html": style_p("Both are top-10 most popular breeds in the US for similar reasons: high trainability, excellent with families, and proven companions over generations. The decisive practical differences: <strong>stranger reception</strong> (Golden greets visitors as friends; GSD is reserved by breed standard), <strong>protective instinct</strong> (Golden has almost none; GSD is a natural watchdog), <strong>cancer rate</strong> (Golden's ~60% lifetime rate is among the highest of any breed; GSD is meaningfully lower), and <strong>training intensity required</strong> (Golden tolerates first-time-owner mistakes; GSD requires firm consistency and early socialization).")
            + style_p("For most family-pet purposes, Golden is the easier match. For households specifically wanting a protective companion with working capability, GSD is the more capable choice. Both are heavy shedders, both need 60-90 minutes of daily exercise, and both face significant orthopedic risk.")
            + UPDATED_LINE},
        "quick_answers": {"label":"Quick Answers","heading":"5 Questions Most People Ask First","html": quick_answers},
        "side_by_side": {"label":"Side by Side","heading":"Specs Compared","html": comparison_table(rows, headers)},
        "temperament": {"label":"Personality","heading":"Temperament: Friendly to All vs Reserved by Design",
            "html": style_h3("Golden Retriever: friendly with everyone")
            + style_p("The Golden's defining temperament trait is friendliness directed outward - they greet strangers as friends, accept other dogs at the park, and have no natural watchdog instinct. This is wonderful for households with frequent visitors and social children; it is the wrong temperament if you specifically want a protective dog.")
            + style_h3("German Shepherd: protective by breed standard")
            + style_p("Properly bred GSDs are reserved with strangers, watchful around their family, and slow to fully accept new people. This is correct breed temperament, not a flaw. With proper socialization they integrate well with friendly visitors but always retain alertness.")},
        "health": {"label":"Health","heading":"Health: The Cancer Gap Is the Single Biggest Difference",
            "html": style_h3("Golden Retriever - cancer is the killer")
            + style_p("Per the Morris Animal Foundation Golden Retriever Lifetime Study, approximately 60% of Goldens die of cancer - the highest documented rate of any breed. Hemangiosarcoma and lymphoma are the most common forms.")
            + style_h3("German Shepherd - hips and DM are the major concerns")
            + style_p("Cancer rates are elevated above mixed-breed baseline but well below Golden's. The major risks: hip and elbow dysplasia (especially in dramatic sloped-back show lines), degenerative myelopathy (DM - DNA testable), and bloat/GDV.")},
        "mikes_take": {"label":"Personal Take","heading":"What I'd Tell a Friend Choosing Between These Two","html": mikes_take},
        "mistakes": {"label":"Common Mistakes","heading":"Mistake Index: Buyer Errors to Avoid","html": mistakes},
        "breeder_vetting": {"label":"Breeder Vetting","heading":"How to Vet a Breeder for Either Breed","html": breeder_vetting},
        "cost": {"label":"Cost","heading":"Cost: Similar Range, Different Risks",
            "html": comparison_table([
                ("Puppy (reputable)","$1,500-$3,000","$1,500-$3,500"),
                ("First-year total","$3,500-$6,500","$3,500-$6,500"),
                ("Annual ongoing","$2,000-$3,800","$2,200-$3,800"),
                ("Pet insurance","$550-$1,100/yr","$700-$1,400/yr"),
                ("End-of-life condition cost","$5,000-$15,000+ (cancer)","$3,000-$8,000+ (orthopedic/DM)"),
            ], headers)
            + style_p("For Goldens: pet insurance enrolled before the first vet visit is critical given the cancer risk profile. For GSDs: budget for orthopedic interventions (hip replacement surgery $5,000-$8,000 per side).")},
        "decision": {"label":"Decision","heading":"Which Should You Choose?",
            "html": style_h3("Choose Golden Retriever if you...")
            + style_p("Have frequent visitors or social children. Are a first-time dog owner. Prefer a softer temperament. Have access to a GANA-style breeder ecosystem. Can budget for cancer monitoring and treatment.")
            + style_h3("Choose German Shepherd if you...")
            + style_p("Want a protective companion. Are committed to early socialization and consistent training. Have prior experience with intelligent working breeds.")
            + style_h3("Choose neither if you...")
            + style_p("Want a low-shedding dog. Live in an apartment. Want a low-energy companion. Consider <a href=\"/blogs/dog-breeds/standard-poodle\">Standard Poodle</a>, <a href=\"/blogs/dog-breeds/goldendoodle\">Goldendoodle</a>, or <a href=\"/blogs/dog-breeds/labrador-retriever\">Labrador</a>.")},
    }
    faq = [
        {"q":"Which is smarter, Golden Retriever or German Shepherd?","a":"German Shepherd, by Stanley Coren's working obedience ranking - GSDs are #3 of all breeds; Goldens are #4. Both are at the high end of working intelligence; the gap is small."},
        {"q":"Do Golden Retrievers really get cancer 60% of the time?","a":"Yes. Per the Morris Animal Foundation Golden Retriever Lifetime Study, approximately 60% of Goldens die of cancer. The most common forms are hemangiosarcoma, lymphoma, mast cell tumor, and osteosarcoma."},
        {"q":"Are German Shepherds aggressive?","a":"Properly bred and socialized GSDs are not aggressive - they are reserved with strangers (correct breed temperament) and protective of family. Poor breeding, lack of socialization, or harsh training can produce reactive behavior."},
        {"q":"Which is better for families with toddlers?","a":"Golden Retriever, generally. The breed's gentle default temperament makes them more tolerant of toddler unpredictability. GSDs can absolutely be excellent with toddlers but require more deliberate socialization."},
        {"q":"What about Goldendoodle as an alternative?","a":"Worth considering. <a href=\"/blogs/dog-breeds/goldendoodle\">Goldendoodle</a> offers Golden temperament with reduced shedding and partially reduced cancer risk via hybrid vigor."},
    ]
    return {
        "meta": _make_meta(
            "Golden Retriever vs German Shepherd","golden-retriever-vs-german-shepherd","Working & Family Breed Comparisons",
            "Golden Retriever vs German Shepherd: friendly with everyone vs protective by breed standard. The honest comparison covering cancer risk, training, and which fits your home.",
            ["comparison","golden-retriever","german-shepherd","family-dog","working-dog","dog-breeds"],
            "Golden Retriever vs German Shepherd compared: temperament, cancer (60% Golden) vs orthopedic GSD risk, training, family fit, mistakes to avoid.",
            "Golden vs GSD: friendly vs protective, cancer (60%) vs hip/DM risk, training, family fit. Which is right?",
        ),
        "stats":{"size":{"emoji":"📏","label":"Size","value":"Medium-Large"},"weight":{"emoji":"⚖️","label":"Weight","value":"55-90 lbs"},"lifespan":{"emoji":"📅","label":"Lifespan","value":"9-13 yrs"},"exercise":{"emoji":"🏃","label":"Exercise","value":"60-90 min"},"grooming":{"emoji":"✂️","label":"Grooming","value":"Heavy shedding"},"training":{"emoji":"🎓","label":"Training","value":"Excellent (both)"},"with_kids":{"emoji":"👨‍👩‍👧","label":"With Kids","value":"Excellent (both)"},"beginners":{"emoji":"🌱","label":"Beginners","value":"Golden: Yes / GSD: Caution"}},
        "images":{"hero":{"url": PLACEHOLDER_HERO,"alt":"Golden Retriever and German Shepherd side by side, family and working breed comparison"}},
        "sections": sections, "faq": faq,
    }


# ── 2. cane-corso-vs-great-dane ──────────────────────────────────────────────

def build_corso_vs_dane():
    headers = ("Attribute", "Cane Corso", "Great Dane")
    rows = [
        ("Origin", "Italy - Roman war/farm guardian", "Germany - boar hunter, refined as companion"),
        ("Size", "85-115 lbs, 23-28 in", "120-200 lbs, 28-34 in"),
        ("Lifespan", "9-12 years", "7-10 years"),
        ("Energy level", "Moderate-high", "Low-moderate"),
        ("Trainability", "Difficult - experienced handler", "Moderate - eager but slow learner"),
        ("Family-friendliness", "Reserved with strangers", "Excellent - gentle giant"),
        ("Bite force (approx PSI)", "~700 PSI", "~238 PSI"),
        ("Main health risks", "Hip dysplasia, bloat, entropion/ectropion", "Bloat (35-40% lifetime), DCM, hip dysplasia"),
        ("Cost (reputable)", "$2,000-$4,500", "$1,500-$3,000"),
        ("Best for", "Experienced owners wanting working guardian", "Calm households wanting gentle giant"),
    ]
    quick_answers = build_quick_answers([
        ("Which is bigger?", "Great Dane, by a wide margin. Adult male Great Danes hit 150-200 lbs and 30+ inches tall. Cane Corsos are 'only' 85-115 lbs."),
        ("Which is more protective?", "Cane Corso. Great Danes are not natural guard dogs - their gentle temperament makes them poor protectors. Cane Corsos retain working-guardian instincts."),
        ("Which lives longer?", "Cane Corso, by 1-3 years (9-12 vs Dane's 7-10). The Dane's enormous size drives shorter lifespan via cardiac, orthopedic, and cancer risk."),
        ("Which is better for first-time owners?", "Great Dane. The calm temperament is more forgiving than the Corso's intensity. Cane Corso is genuinely an experienced-owner breed."),
        ("Can either live in an apartment?", "Great Dane can - lower energy makes 30-minute walks plus indoor lounging work. Cane Corso almost never works due to higher exercise needs."),
    ])
    mistakes = build_mistakes(
        "Cane Corso",
        [
            ("Buying as a first dog or 'cool-looking big dog'", "Cane Corsos require expert handling - confident corrections, early socialization, and ongoing training into adulthood."),
            ("Inadequate fencing and prey drive management", "Corsos have high prey drive including cats, rabbits, and small dogs. A 4-foot fence is not enough."),
            ("Skipping professional training by age 12 weeks", "Corsos test boundaries throughout adolescence (8-24 months). Without structured training, behavioral issues compound."),
            ("Buying from breeders who don't temperament-test", "Quality Corso breeders evaluate puppy temperament before placement. A breeder who lets you 'pick the cute one' is selling you a future behavior problem."),
        ],
        "Great Dane",
        [
            ("Choosing the biggest puppy or heaviest line", "Larger Great Danes have shorter lifespans. Selecting from breeders whose adults reach 150-170 lbs gives a meaningful longevity advantage."),
            ("Skipping prophylactic gastropexy", "Bloat/GDV affects 35-40% of Great Danes lifetime. Prophylactic gastropexy at spay/neuter prevents life-threatening gastric torsion. $300-$800 once."),
            ("Not budgeting for the cardiac reality", "DCM affects elevated percentage. Annual cardiac echo from age 2 onward catches it early enough for medical management."),
            ("Underestimating food costs", "Adult Great Danes eat 6-10 cups of premium kibble daily. Annual food cost runs $1,500-$2,500."),
            ("Inadequate vehicle for transportation", "Standard sedans don't fit an adult Great Dane. SUV or truck with crate space is required."),
        ],
    )
    mikes_take = build_mikes_take(
        style_p("The honest pitch for each: Great Dane is what you choose if you want a 200-pound dog who behaves like a 30-pound dog - calm, patient, content to lounge. Cane Corso is what you choose if you want a 100-pound dog who behaves like a 150-pound working partner - reserved, watchful, with you when you work.")
        + style_p("The mistake is buying either expecting the other. Great Dane buyers who wanted a guardian end up with a friendly couch potato. Cane Corso buyers who wanted a family pet end up with a dog that refuses to settle when company visits. Pick the temperament you actually want.")
    )
    breeder_vetting = build_breeder_vetting(
        "Cane Corso",
        [
            'OFA hip and elbow certificates for both parents.',
            'OFA cardiac clearance on both parents.',
            'CAER eye exam on both parents - especially entropion screening.',
            'Temperament evaluation methodology - how do you assess puppies before placement?',
            'Can I see the dam interacting with strangers, kids, and other dogs?',
            'What is your puppy-back policy if the dog develops aggression issues?',
        ],
        "Great Dane",
        [
            'OFA hip certificates for both parents.',
            'OFA cardiac clearance with current echocardiogram.',
            'Will you commit to prophylactic gastropexy as part of spay/neuter?',
            'How old are the grandparents and what were their causes of death?',
            'What is the typical adult weight range in your line? (Lower is better.)',
            'Do you screen for Wobbler\'s syndrome?',
        ],
        [
            'Breeder says "we don\'t test because our line is healthy".',
            'Markets Cane Corso as a "family pet" without temperament evaluation requirements.',
            'Sells Great Dane puppies weighing 25+ lbs at 8 weeks (too-fast growth).',
            'Will not show you parents in person.',
            'Charges premium for "European bloodline" without documentation.',
            'Sells puppies before 8 weeks old.',
        ],
    )
    sections = {
        "intro": {"label":"Overview","heading":"Cane Corso vs Great Dane: The Quick Answer",
            "html": style_p("Both are large Molosser-derived breeds with impressive physical presence. The decisive practical differences: <strong>size</strong> (Great Dane is 30-80 lbs heavier), <strong>temperament purpose</strong> (Dane is gentle-giant family dog; Corso is active working guardian), <strong>protective instinct</strong> (Corso has working-guardian temperament; Dane is famously friendly with strangers), and <strong>training difficulty</strong> (Dane is moderate; Corso requires experienced handling).")
            + style_p("For family-pet purposes, Great Dane is the dramatically easier match despite its size. For households specifically wanting a serious guardian, Cane Corso is the right answer.")
            + UPDATED_LINE},
        "quick_answers": {"label":"Quick Answers","heading":"5 Questions Most People Ask First","html": quick_answers},
        "side_by_side": {"label":"Side by Side","heading":"Specs Compared","html": comparison_table(rows, headers)},
        "temperament": {"label":"Personality","heading":"Temperament: Gentle Giant vs Working Guardian",
            "html": style_h3("Great Dane: gentle, friendly, surprisingly low-energy")
            + style_p("The Great Dane 'gentle giant' reputation is accurate. Modern Danes are calm, patient with children, friendly with strangers, and low-energy indoors. Not natural guardians - their size is a deterrent but their temperament is not protective.")
            + style_h3("Cane Corso: reserved, watchful, working drive")
            + style_p("Cane Corsos retain working-guardian temperament. They are deeply bonded to family but reserved bordering on suspicious with strangers. Require active engagement (60-90 min daily exercise + mental work).")},
        "health": {"label":"Health","heading":"Health: Both Below-Average Lifespan",
            "html": style_h3("Great Dane main risks")
            + style_p("<strong>Bloat/GDV</strong> affects 35-40% of Great Danes lifetime - the highest rate of any breed. Prophylactic gastropexy is standard. <strong>DCM</strong> at elevated rates. <strong>Wobbler's syndrome</strong>. Lifespan averages 7-10 years.")
            + style_h3("Cane Corso main risks")
            + style_p("<strong>Hip dysplasia</strong>. <strong>Bloat/GDV</strong>. <strong>Entropion and ectropion</strong> (eyelid abnormalities). Lifespan averages 9-12 years.")},
        "mikes_take": {"label":"Personal Take","heading":"What I'd Tell a Friend Choosing Between These Two","html": mikes_take},
        "mistakes": {"label":"Common Mistakes","heading":"Mistake Index: Buyer Errors to Avoid","html": mistakes},
        "breeder_vetting": {"label":"Breeder Vetting","heading":"How to Vet a Breeder for Either Breed","html": breeder_vetting},
        "cost": {"label":"Cost","heading":"Cost: Both Expensive Long-Term",
            "html": comparison_table([
                ("Puppy (reputable)","$2,000-$4,500","$1,500-$3,000"),
                ("First-year total","$4,000-$7,500","$5,000-$8,500"),
                ("Annual ongoing","$2,400-$4,200","$2,800-$5,000"),
                ("Food (giant breed)","$800-$1,400/yr","$1,500-$2,500/yr"),
            ], headers)},
        "decision": {"label":"Decision","heading":"Which Should You Choose?",
            "html": style_h3("Choose Great Dane if you...")
            + style_p("Want a low-energy gentle giant. Have space for a 150-200 lb dog. Are emotionally prepared for the 7-10 year lifespan. Want a friendly-with-strangers breed.")
            + style_h3("Choose Cane Corso if you...")
            + style_p("Are an experienced large-breed owner. Want an active guardian. Don't have small pets. Have a secure yard. Are committed to ongoing training.")
            + style_h3("Compare with related options")
            + style_p("See also <a href=\"/blogs/dog-breeds/mastiff-vs-cane-corso\">Mastiff vs Cane Corso</a>, <a href=\"/blogs/dog-breeds/rottweiler-vs-cane-corso\">Rottweiler vs Cane Corso</a>, or <a href=\"/blogs/dog-breeds/great-dane-vs-doberman\">Great Dane vs Doberman</a>.")},
    }
    faq = [
        {"q":"Which is more aggressive?","a":"Bite statistics suggest Cane Corso more frequently than Great Dane. Neither breed is inherently dangerous with proper training and socialization. Corso's higher prey drive and reactive temperament makes incidents more likely with poor training."},
        {"q":"Can a Great Dane really live in an apartment?","a":"Surprisingly yes in many cases. The breed's low energy means a 30-45 minute walk plus indoor lounging satisfies their exercise needs."},
        {"q":"Which has more impressive presence?","a":"Different dimensions. Great Dane wins on height (tower-like). Cane Corso wins on muscular density and bite-force capability."},
        {"q":"Do Great Danes really get bloat that often?","a":"Yes. Per veterinary studies, Great Danes are the #1 highest-risk breed - lifetime rate is estimated at 35-40% without preventive measures."},
        {"q":"What about Mastiff or Rottweiler as related options?","a":"Worth considering. See <a href=\"/blogs/dog-breeds/mastiff-vs-cane-corso\">Mastiff vs Cane Corso</a> and <a href=\"/blogs/dog-breeds/rottweiler-vs-cane-corso\">Rottweiler vs Cane Corso</a>."},
    ]
    return {
        "meta": _make_meta(
            "Cane Corso vs Great Dane","cane-corso-vs-great-dane","Giant Breed Comparisons",
            "Cane Corso vs Great Dane: working guardian vs gentle giant compared. Size, temperament, family fit, lifespan, and which large breed fits your home.",
            ["comparison","cane-corso","great-dane","guard-dog","giant-breed","mastiff","dog-breeds"],
            "Cane Corso vs Great Dane compared: 100 vs 200 lbs, working guardian vs gentle giant, bloat risk, family fit, cost. Which large breed is right?",
            "Cane Corso vs Great Dane: size, temperament, family fit, lifespan, bloat risk. Which is right?",
        ),
        "stats":{"size":{"emoji":"📏","label":"Size","value":"Large-Giant"},"weight":{"emoji":"⚖️","label":"Weight","value":"85-200 lbs"},"lifespan":{"emoji":"📅","label":"Lifespan","value":"7-12 yrs"},"exercise":{"emoji":"🏃","label":"Exercise","value":"30-90 min"},"grooming":{"emoji":"✂️","label":"Grooming","value":"Low (both)"},"training":{"emoji":"🎓","label":"Training","value":"Dane: Mod / Corso: Expert"},"with_kids":{"emoji":"👨‍👩‍👧","label":"With Kids","value":"Dane: Excellent / Corso: Caution"},"beginners":{"emoji":"🌱","label":"Beginners","value":"Dane: Yes / Corso: No"}},
        "images":{"hero":{"url": PLACEHOLDER_HERO,"alt":"Cane Corso and Great Dane side by side, large breed comparison"}},
        "sections": sections, "faq": faq,
    }


# ── 3. bernedoodle-vs-aussiedoodle ───────────────────────────────────────────

def build_berne_vs_aussie():
    headers = ("Attribute","Bernedoodle","Aussiedoodle")
    rows = [
        ("Parent breeds","Bernese Mountain Dog x Poodle","Australian Shepherd x Poodle"),
        ("Size (Standard)","70-90 lbs, 23-29 in","45-70 lbs, 18-23 in"),
        ("Lifespan","12-15 yrs Standard / 14-17 yrs Mini","12-15 years"),
        ("Signature coloring","Tri-color (black + white + rust)","Merle (blue or red) most iconic"),
        ("Energy level","Low-moderate - calmer","High - more active"),
        ("Trainability","Easy - sometimes stubborn","Easy - very eager and clever"),
        ("Family-friendliness","Excellent - gentle with kids","Excellent - but more nippy/herdy"),
        ("Main health risks","Hip dysplasia, cancer (Bernese side)","MDR1, hip dysplasia, cataracts, double-merle risk"),
        ("Cost (reputable)","$2,500-$5,500","$2,000-$4,500"),
        ("Best for","Calm families with young kids","Active families with school-age kids"),
    ]
    quick_answers = build_quick_answers([
        ("Which is calmer?", "Bernedoodle, clearly. Bernese contributes calm temperament; Aussie contributes herding-breed energy."),
        ("Which is smarter?", "Aussiedoodle, slightly. Australian Shepherds rank in top 10 most intelligent; Bernese are moderately intelligent."),
        ("Which is better with kids?", "Bernedoodle, by a clear margin. Aussiedoodles can be nippy at running children (herding instinct)."),
        ("Which sheds less?", "Both shed similarly when bred from F1B or multigen lines. F1 puppies can shed more."),
        ("Which lives in an apartment better?", "Bernedoodle Mini. Aussiedoodles need 60-120 min daily exercise plus mental work."),
    ])
    mistakes = build_mistakes(
        "Bernedoodle",
        [
            ("Buying F1 without understanding shedding lottery", "F1 Bernedoodles inherit Bernese coat genetics ~50% of the time. F1B or multigen produce reliably low-shedding coats."),
            ("Not asking about cancer history from Bernese side", "Bernese have one of the highest cancer rates of any breed. Ask for longevity history of Bernese grandparents."),
            ("Buying from non-ABDC affiliated breeder", "The Bernedoodle Association of North America (ABDC) sets health-testing standards."),
            ("Underestimating Standard size at maturity", "Standard Bernedoodles hit 80-90 lbs. Budget for giant-breed food and vet costs."),
            ("Not committing to professional grooming", "Coats mat severely without professional grooming every 6-8 weeks."),
        ],
        "Aussiedoodle",
        [
            ("Buying from a merle-to-merle breeding", "Double-merle puppies have severe deafness and blindness rates. Reputable breeders never breed two merles together."),
            ("Underestimating the energy requirement", "Aussiedoodles need 60-120 min intense daily exercise plus mental work."),
            ("Apartment living without exercise commitment", "Living in a 2-bedroom with one daily walk produces a neurotic dog."),
            ("Not asking about MDR1 testing", "MDR1 mutation can make common veterinary drugs (ivermectin, loperamide) fatal. DNA test on both parents is essential."),
            ("Buying for 'smart dog' without committing to mental work", "Smart dogs without jobs find their own jobs, usually destructive."),
        ],
    )
    mikes_take = build_mikes_take(
        style_p("If you're choosing between these two and have young children, get the Bernedoodle. Aussiedoodles are wonderful dogs for school-age kids who can play structured games and don't trigger herding instincts with random running and screaming. With toddlers, the Aussiedoodle's herding nips - even when 'just play' - become a real management challenge.")
        + style_p("If you don't have kids and want a smart agility partner, Aussiedoodle wins. Match the dog to the actual household activity level, not the look you want.")
    )
    breeder_vetting = build_breeder_vetting(
        "Bernedoodle",
        [
            'OFA hip and elbow certificates for both parents.',
            'OFA cardiac clearance on both parents.',
            'Longevity history of Bernese grandparents - past age 9?',
            'Are you a member of the Bernedoodle Association of North America (ABDC)?',
            'Which generation is the puppy (F1, F1B, F2, multigen)?',
        ],
        "Aussiedoodle",
        [
            'OFA hip certificates for both parents.',
            'MDR1 DNA test results on both parents.',
            'Collie Eye Anomaly (CEA) DNA test on the Aussie parent.',
            'What are the coat colors of both parents? (No merle-to-merle breeding.)',
            'Do you start socialization, crate exposure at 4 weeks?',
        ],
        [
            'Breeds merle-to-merle Aussiedoodles (lethal-white puppies).',
            'Markets "rare merle" at premium prices.',
            'Multiple Doodle varieties on offer simultaneously.',
            'Will not share OFA database links.',
            'Claims puppies are "hypoallergenic" without explaining F1 coat variability.',
            'Sells puppies before 8 weeks old.',
        ],
    )
    sections = {
        "intro":{"label":"Overview","heading":"Bernedoodle vs Aussiedoodle: The Quick Answer",
            "html": style_p("Both are popular Doodle hybrid breeds. The decisive practical differences: <strong>energy level</strong> (Aussiedoodle is significantly more energetic), <strong>temperament with kids</strong> (Bernedoodle is famously gentle; Aussiedoodle can be nippy due to herding instinct), <strong>size</strong> (Bernedoodle Standard is 20-30 lbs heavier), and <strong>signature look</strong> (Bernedoodle's tri-color vs Aussiedoodle's merle).")
            + UPDATED_LINE},
        "quick_answers":{"label":"Quick Answers","heading":"5 Questions Most People Ask First","html": quick_answers},
        "side_by_side":{"label":"Side by Side","heading":"Specs Compared","html": comparison_table(rows, headers)},
        "temperament":{"label":"Personality","heading":"Temperament: Gentle Giant vs Working Brain",
            "html": style_h3("Bernedoodle: gentle, patient, calmer-paced")
            + style_p("Bernedoodles inherit Bernese Mountain Dog's calm demeanor. Notably gentle with young children, less reactive to noise.")
            + style_h3("Aussiedoodle: smart, agile, herding-driven")
            + style_p("Aussiedoodles inherit Australian Shepherd working drive and intelligence. They learn faster, excel at agility, but herd children (nipping at heels of running kids).")},
        "health":{"label":"Health","heading":"Health: Hybrid Vigor With Different Specific Risks",
            "html": style_h3("Bernedoodle-specific")
            + style_p("<strong>Cancer</strong> risk from Bernese side. <strong>Addison's disease</strong> from Poodle side. <strong>Sebaceous adenitis</strong>.")
            + style_h3("Aussiedoodle-specific")
            + style_p("<strong>MDR1 mutation</strong> (drug sensitivity, DNA testable) - critical. <strong>Collie Eye Anomaly</strong>. <strong>Double-merle risk</strong> in puppies from poorly-bred litters.")},
        "mikes_take":{"label":"Personal Take","heading":"What I'd Tell a Friend Choosing Between These Two","html": mikes_take},
        "mistakes":{"label":"Common Mistakes","heading":"Mistake Index: Buyer Errors to Avoid","html": mistakes},
        "breeder_vetting":{"label":"Breeder Vetting","heading":"How to Vet a Breeder for Either Doodle","html": breeder_vetting},
        "cost":{"label":"Cost","heading":"Cost: Bernedoodle Slightly Higher",
            "html": comparison_table([
                ("Puppy (reputable)","$2,500-$5,500","$2,000-$4,500"),
                ("First-year total","$5,000-$9,500","$4,000-$7,500"),
                ("Annual ongoing","$2,400-$4,200","$2,200-$3,800"),
            ], headers)},
        "decision":{"label":"Decision","heading":"Which Should You Choose?",
            "html": style_h3("Choose Bernedoodle if you...")
            + style_p("Want a calmer Doodle. Have young children. Prefer tri-color look. Live in cool climate.")
            + style_h3("Choose Aussiedoodle if you...")
            + style_p("Want smart, agile companion for active outdoor life. Have school-age children. Love merle look. Can commit to 60-120 min daily exercise + mental work.")
            + style_h3("Compare with related options")
            + style_p("See also <a href=\"/blogs/dog-breeds/sheepadoodle-vs-bernedoodle\">Sheepadoodle vs Bernedoodle</a>, <a href=\"/blogs/dog-breeds/bernedoodle-vs-goldendoodle\">Bernedoodle vs Goldendoodle</a>, or <a href=\"/blogs/dog-breeds/best-doodle-breeds-for-families\">Best Doodle Breeds for Families</a>.")},
    }
    faq = [
        {"q":"Which is better for first-time owners?","a":"Bernedoodle, slightly. Calmer temperament is more forgiving."},
        {"q":"Are merle Aussiedoodles healthy?","a":"Single-merle Aussiedoodles are healthy. The risk is merle-to-merle breeding which produces ~25% double-merle puppies with deafness/blindness."},
        {"q":"Do Bernedoodles really live longer than Bernese?","a":"Yes, substantially. Hybrid vigor extends lifespan from Bernese's 7-10 years to Bernedoodle's 12-15 years (Standard) or 14-17 (Mini)."},
        {"q":"What's the difference between F1, F1B, and multigen?","a":"F1 = 50% Poodle, variable coats. F1B = 75% Poodle, reliably low-shedding. Multigen = third-gen+, most consistent."},
        {"q":"What about Sheepadoodle or Goldendoodle instead?","a":"Both worth considering. See <a href=\"/blogs/dog-breeds/sheepadoodle-vs-bernedoodle\">Sheepadoodle vs Bernedoodle</a> and <a href=\"/blogs/dog-breeds/best-doodle-breeds-for-families\">doodle comparison</a>."},
    ]
    return {
        "meta": _make_meta(
            "Bernedoodle vs Aussiedoodle","bernedoodle-vs-aussiedoodle","Doodle Comparisons",
            "Bernedoodle vs Aussiedoodle: gentle giant vs working brain. Energy level, family fit, merle risk, and which Doodle fits your home.",
            ["comparison","doodle","bernedoodle","aussiedoodle","designer-crossbreed","family-dog","dog-breeds"],
            "Bernedoodle vs Aussiedoodle compared: energy, family fit, merle risk, MDR1, cost. Which Doodle fits your household?",
            "Bernedoodle vs Aussiedoodle: energy, family fit, merle risk. Which doodle is right?",
        ),
        "stats":{"size":{"emoji":"📏","label":"Size","value":"Medium-Large"},"weight":{"emoji":"⚖️","label":"Weight","value":"10-90 lbs"},"lifespan":{"emoji":"📅","label":"Lifespan","value":"12-17 yrs"},"exercise":{"emoji":"🏃","label":"Exercise","value":"45-120 min"},"grooming":{"emoji":"✂️","label":"Grooming","value":"High (both)"},"training":{"emoji":"🎓","label":"Training","value":"Easy (both)"},"with_kids":{"emoji":"👨‍👩‍👧","label":"With Kids","value":"Bernedoodle: Excellent / Aussie: School-age+"},"beginners":{"emoji":"🌱","label":"Beginners","value":"Yes (both)"}},
        "images":{"hero":{"url": PLACEHOLDER_HERO,"alt":"Bernedoodle and Aussiedoodle side by side, doodle breed comparison"}},
        "sections": sections, "faq": faq,
    }


# ── 4. vizsla-vs-german-shorthaired-pointer ──────────────────────────────────

def build_vizsla_vs_gsp():
    headers = ("Attribute","Vizsla","German Shorthaired Pointer")
    rows = [
        ("Origin","Hungary - upland game pointer","Germany 17th c. - versatile hunting dog"),
        ("Size","44-65 lbs, 21-24 in","45-70 lbs, 21-25 in"),
        ("Lifespan","12-14 years","12-14 years"),
        ("Coat","Short smooth rust-golden (uniform)","Short with dense undercoat, liver ticking"),
        ("Shedding","Low-moderate","Moderate (denser undercoat)"),
        ("Energy level","Very high","Very high - more independent stamina"),
        ("Velcro tendency","Extreme - 'velcro dog'","High but more independent"),
        ("Separation anxiety","High risk","Moderate risk"),
        ("Prey drive","High","Very high"),
        ("Main health risks","Hip dysplasia, epilepsy, lymphosarcoma","Hip dysplasia, cardiac issues, vWD"),
        ("Cost (reputable)","$1,500-$3,500","$1,500-$3,000"),
        ("Best for","Active families wanting velcro companion","Active outdoor families wanting versatile hunter"),
    ]
    quick_answers = build_quick_answers([
        ("How are these two different?", "Both are short-coated European pointing breeds. Vizslas are leaner, more velcro, uniform rust-golden. GSPs are slightly larger, more independent, with liver coat and ticking."),
        ("Which sheds less?", "Vizsla. Single short coat vs GSP's denser undercoat."),
        ("Which is better for first-time owners?", "Vizsla, slightly. Softer, more sensitive temperament."),
        ("Which is more 'velcro'?", "Vizsla. Famously close-following - prefers physical contact at all times."),
        ("Which is better for hunting?", "GSP, traditionally. Versatile gun dog - pointing, retrieving, water work."),
    ])
    mistakes = build_mistakes(
        "Vizsla",
        [
            ("Buying without understanding separation anxiety", "Extreme velcro dogs develop severe separation anxiety at high rates."),
            ("Choosing harsh training methods", "Vizslas are exceptionally sensitive to corrections. Positive reinforcement only."),
            ("Skipping early field/scent exposure", "Vizslas have working-dog drive that needs an outlet."),
            ("Underestimating exercise needs", "60-120 minutes daily of structured exercise is the minimum."),
        ],
        "German Shorthaired Pointer",
        [
            ("Buying as a couch dog", "GSPs are working hunters who need 90-150 minutes of daily exercise."),
            ("Underestimating prey drive", "GSPs have very high prey drive - cats, rabbits, small dogs can trigger chase."),
            ("Apartment living without daily field exercise", "GSPs are not apartment dogs."),
            ("Not asking about working-line vs show-line", "Match the line to your activity level."),
            ("Skipping early socialization with smaller pets", "GSPs raised with cats can integrate; adult intros are high-risk."),
        ],
    )
    mikes_take = build_mikes_take(
        style_p("The differentiator: do you want a hunter or a friend? GSP is a working hunter who happens to be a wonderful family dog. Vizsla is a family member who happens to have hunting genes.")
        + style_p("Practical: if you hunt birds, get a GSP. If you don't, both work but Vizsla integrates more naturally into pure-pet life. The Vizsla's extreme velcro is endearing if you're home with the dog and crushing if you work in an office.")
    )
    breeder_vetting = build_breeder_vetting(
        "Vizsla",
        [
            'OFA hip and elbow certificates for both parents.',
            'Eye exam (CAER) on both parents.',
            'Hypothyroidism panel on both parents.',
            'How is the dam handling visitors and new situations?',
            'Are you involved in field trials or hunt tests?',
        ],
        "German Shorthaired Pointer",
        [
            'OFA hip certificates for both parents.',
            'Von Willebrand disease DNA test on both parents.',
            'Cardiac clearance on both parents.',
            'CAER eye exam on both parents.',
            'What line is the puppy from (working/show)?',
        ],
        [
            "Breeder doesn't evaluate puppy temperament.",
            'Sells "calm Vizsla" or "low-energy GSP" - both breeds are inherently high-energy.',
            'Multiple litters per year.',
            "Will not share parents' health certificates.",
            'Markets puppies as "rare colors" at premium prices.',
            'Sells puppies before 8 weeks old.',
        ],
    )
    sections = {
        "intro":{"label":"Overview","heading":"Vizsla vs German Shorthaired Pointer: The Quick Answer",
            "html": style_p("Both are short-coated European pointing breeds with similar appearance, exercise needs, and temperament. The decisive differences: <strong>coat shedding</strong> (Vizsla less), <strong>velcro intensity</strong> (Vizsla extreme; GSP independent), <strong>color</strong> (rust gold vs liver ticking), <strong>working orientation</strong> (Vizsla integrates into pet life; GSP retains stronger hunting drive).")
            + UPDATED_LINE},
        "quick_answers":{"label":"Quick Answers","heading":"5 Questions Most People Ask First","html": quick_answers},
        "side_by_side":{"label":"Side by Side","heading":"Specs Compared","html": comparison_table(rows, headers)},
        "temperament":{"label":"Personality","heading":"Temperament: Velcro Soul vs Independent Hunter",
            "html": style_h3("Vizsla: extreme velcro, sensitive")
            + style_p("Vizslas form intensely close bonds. Sensitive to handler emotional tone - harsh corrections shut them down.")
            + style_h3("GSP: independent worker, loving family member")
            + style_p("GSPs share the velcro tendency at more manageable level. Bred to work independently in field conditions.")},
        "health":{"label":"Health","heading":"Health: Similar Profile",
            "html": style_h3("Vizsla-specific")
            + style_p("<strong>Epilepsy</strong>. <strong>Hypothyroidism</strong>. <strong>Lymphosarcoma</strong>.")
            + style_h3("GSP-specific")
            + style_p("<strong>Subaortic stenosis</strong> (cardiac). <strong>Von Willebrand disease</strong>.")},
        "mikes_take":{"label":"Personal Take","heading":"What I'd Tell a Friend Choosing Between These Two","html": mikes_take},
        "mistakes":{"label":"Common Mistakes","heading":"Mistake Index: Buyer Errors to Avoid","html": mistakes},
        "breeder_vetting":{"label":"Breeder Vetting","heading":"How to Vet a Breeder for Either Breed","html": breeder_vetting},
        "cost":{"label":"Cost","heading":"Cost: Similar Range",
            "html": comparison_table([
                ("Puppy (reputable)","$1,500-$3,500","$1,500-$3,000"),
                ("First-year total","$3,500-$6,000","$3,500-$6,000"),
                ("Annual ongoing","$2,000-$3,500","$2,000-$3,500"),
            ], headers)},
        "decision":{"label":"Decision","heading":"Which Should You Choose?",
            "html": style_h3("Choose Vizsla if you...")
            + style_p("Are home most of the day. Prefer minimal shedding. Sensitive to harsh training. Don't hunt.")
            + style_h3("Choose GSP if you...")
            + style_p("Active outdoor family. Hunt or want versatile working dog. Have older children. Need slightly more independent breed.")
            + style_h3("Compare with Vizsla vs Weimaraner")
            + style_p("Also see <a href=\"/blogs/dog-breeds/vizsla-vs-weimaraner\">Vizsla vs Weimaraner</a> for related sporting comparison.")},
    }
    faq = [
        {"q":"Can I tell a Vizsla and GSP apart?","a":"Color is the easiest tell. Vizsla is uniform rust gold. GSP is liver or liver-and-white with ticking pattern."},
        {"q":"Which is easier for first-time owners?","a":"Vizsla, slightly. Softer temperament more forgiving of mistakes."},
        {"q":"Do GSPs have separation anxiety like Vizslas?","a":"Less severely than Vizslas, but yes some GSPs do."},
        {"q":"Are these dogs hypoallergenic?","a":"Neither. Both shed less than long-coated breeds but produce dander."},
        {"q":"What about Weimaraner as an alternative?","a":"Worth considering. See <a href=\"/blogs/dog-breeds/vizsla-vs-weimaraner\">Vizsla vs Weimaraner</a>."},
    ]
    return {
        "meta": _make_meta(
            "Vizsla vs German Shorthaired Pointer","vizsla-vs-german-shorthaired-pointer","Sporting Breed Comparisons",
            "Vizsla vs GSP: two short-coated European pointing breeds compared. Velcro soul vs independent hunter, coat, temperament, and which fits your home.",
            ["comparison","vizsla","german-shorthaired-pointer","sporting-dog","pointing-breed","dog-breeds"],
            "Vizsla vs GSP compared: coat shedding, velcro intensity, separation anxiety, working orientation, family fit, mistakes to avoid.",
            "Vizsla vs GSP: coat, velcro, separation anxiety, hunting drive. Which sporting breed is right?",
        ),
        "stats":{"size":{"emoji":"📏","label":"Size","value":"Medium-Large"},"weight":{"emoji":"⚖️","label":"Weight","value":"44-70 lbs"},"lifespan":{"emoji":"📅","label":"Lifespan","value":"12-14 yrs"},"exercise":{"emoji":"🏃","label":"Exercise","value":"60-150 min"},"grooming":{"emoji":"✂️","label":"Grooming","value":"Low (both)"},"training":{"emoji":"🎓","label":"Training","value":"Excellent (both)"},"with_kids":{"emoji":"👨‍👩‍👧","label":"With Kids","value":"Excellent (both)"},"beginners":{"emoji":"🌱","label":"Beginners","value":"Active owners only"}},
        "images":{"hero":{"url": PLACEHOLDER_HERO,"alt":"Vizsla and German Shorthaired Pointer side by side, European pointing breed comparison"}},
        "sections": sections, "faq": faq,
    }


# ── 5. great-dane-vs-doberman ────────────────────────────────────────────────

def build_dane_vs_doberman():
    headers = ("Attribute","Great Dane","Doberman Pinscher")
    rows = [
        ("Origin","Germany - boar hunting, refined as companion","Germany - tax collector personal protection (1890s)"),
        ("Size","120-200 lbs, 28-34 in","60-100 lbs, 24-28 in"),
        ("Lifespan","7-10 years","10-13 years"),
        ("Shedding","Moderate year-round","Low - one of lowest short-coat shedders"),
        ("Energy level","Low-moderate","High"),
        ("Protective instinct","Low - 'gentle giant'","Strong - vocal alert, reactive"),
        ("Stranger reception","Friendly, accepting","Reserved, vocally alert"),
        ("Heat tolerance","Poor","Poor - no insulating coat"),
        ("Main health risks","Bloat (35-40% lifetime), DCM, Wobbler's","DCM (50-60% lifetime), vWD, Wobbler's"),
        ("Cost (reputable)","$1,500-$3,000","$1,800-$3,500"),
        ("Best for","Calm households wanting gentle giant","Active owners wanting protective companion"),
    ]
    quick_answers = build_quick_answers([
        ("Which is bigger?", "Great Dane, by a large margin. Adult Danes hit 150-200 lbs. Dobermans are 60-100 lbs."),
        ("Which is more protective?", "Doberman. Great Danes are friendly gentle giants - poor natural guards."),
        ("Which lives longer?", "Doberman, by 2-3 years on average. Size drives the Dane's shorter lifespan."),
        ("Which is easier for first-time owners?", "Great Dane, despite the size. Calm temperament more forgiving than Doberman's reactive temperament."),
        ("Which is better for apartment living?", "Both can work better than their size suggests. Great Dane's low energy makes lounging viable; Doberman's smaller size and low shedding help."),
    ])
    mistakes = build_mistakes(
        "Great Dane",
        [
            ("Choosing the heaviest line or biggest puppy", "Larger Great Danes have shorter lifespans. Lines selecting for 150-170 lb adults live measurably longer."),
            ("Skipping prophylactic gastropexy", "Bloat/GDV affects 35-40% lifetime. Prophylactic gastropexy at spay/neuter prevents twisting. $300-$800 one-time."),
            ("Not budgeting for cardiac monitoring", "DCM affects elevated percentage. Annual cardiac echo from age 2 catches early-stage DCM."),
            ("Inadequate vehicle and home setup", "Standard sedans don't fit adult Great Danes. SUV or truck with crate space required."),
            ("Underestimating food costs", "$1,500-$2,500/year for premium giant-breed food."),
        ],
        "Doberman Pinscher",
        [
            ("Skipping annual cardiac echo from age 3", "DCM affects 50-60% of Dobermans lifetime - the highest of any breed. Without screening, sudden cardiac death is common."),
            ("Buying without breeder cardiac certifications", "Reputable Doberman breeders provide cardiac certificates on both parents."),
            ("Confusing European vs American lines", "European Dobermans (working) have firmer temperaments. American show Dobermans are calmer."),
            ("Underestimating velcro / separation anxiety", "Dobermans bond intensely and develop separation anxiety more than most breeds."),
            ("Inadequate cold-weather preparation", "Dobermans have almost no body fat. Need sweaters in cold-weather walks."),
        ],
    )
    mikes_take = build_mikes_take(
        style_p("The choice is mostly about lifestyle. Doberman is a 'partner dog' - intense bonding, active outdoor companion, vigilant when family is at risk. Great Dane is a 'presence dog' - the size is the feature, gentle nature is the family-fit benefit, and the deal is accepting 7-10 year lifespan.")
        + style_p("Two scenarios I'd push back on: Doberman in a household where the dog is alone 9 hours daily (velcro temperament + separation anxiety produces a neurotic dog), and Great Dane bought without prior research on bloat/gastropexy.")
    )
    breeder_vetting = build_breeder_vetting(
        "Great Dane",
        [
            'OFA hip certificates for both parents.',
            'OFA cardiac clearance with current echocardiogram.',
            'How old are grandparents and what were their causes of death?',
            'What is the typical adult weight in your line?',
            'Will you commit to prophylactic gastropexy?',
        ],
        "Doberman Pinscher",
        [
            'OFA hip and elbow certificates for both parents.',
            'Annual cardiac echocardiogram + Holter monitor results on both parents.',
            'Von Willebrand disease DNA test on both parents.',
            'Thyroid panel on both parents.',
            'European or American line?',
        ],
        [
            "Doberman breeder doesn't do annual cardiac screening - non-negotiable.",
            'Sells Great Dane puppies weighing 30+ lbs at 8 weeks.',
            'Markets "European bloodline" without documentation.',
            'Multiple litters per year.',
            'Will not show parents in person.',
            'Sells puppies before 8 weeks old.',
        ],
    )
    sections = {
        "intro":{"label":"Overview","heading":"Great Dane vs Doberman: The Quick Answer",
            "html": style_p("Both are German breeds with impressive physical presence and protective potential. The decisive differences: <strong>size</strong> (Dane is 60-100 lbs heavier), <strong>energy level</strong> (Doberman has 2-3x the daily exercise requirement), <strong>protective instinct</strong> (Doberman is the protector; Dane is gentle and accepting), and <strong>health risk profile</strong> (Dane faces bloat + cardiomyopathy; Doberman faces DCM + von Willebrand).")
            + style_p("For pure family-pet purposes wanting an impressive but calm companion, Great Dane is the easier match. For households wanting an active protective partner, Doberman is the right answer.")
            + UPDATED_LINE},
        "quick_answers":{"label":"Quick Answers","heading":"5 Questions Most People Ask First","html": quick_answers},
        "side_by_side":{"label":"Side by Side","heading":"Specs Compared","html": comparison_table(rows, headers)},
        "temperament":{"label":"Personality","heading":"Temperament: Gentle Giant vs Vigilant Athlete",
            "html": style_h3("Great Dane: friendly, calm, low-energy")
            + style_p("Modern Danes are calm, patient, friendly with strangers, content with moderate exercise. Not natural protectors despite size.")
            + style_h3("Doberman: vocally alert, intense bonding")
            + style_p("Dobermans alert vocally to anything unusual. Form intense velcro bonds. High daily exercise needs (60-120 min).")},
        "health":{"label":"Health","heading":"Health: Different Cardiac Realities",
            "html": style_h3("Great Dane main risks")
            + style_p("<strong>Bloat/GDV</strong> 35-40% lifetime - highest of any breed. <strong>DCM</strong>. <strong>Wobbler's syndrome</strong>.")
            + style_h3("Doberman main risks")
            + style_p("<strong>DCM</strong> affects 50-60% lifetime - highest of any breed. Annual echocardiogram from age 3 essential. <strong>Von Willebrand disease</strong>.")},
        "mikes_take":{"label":"Personal Take","heading":"What I'd Tell a Friend Choosing Between These Two","html": mikes_take},
        "mistakes":{"label":"Common Mistakes","heading":"Mistake Index: Buyer Errors to Avoid","html": mistakes},
        "breeder_vetting":{"label":"Breeder Vetting","heading":"How to Vet a Breeder for Either Breed","html": breeder_vetting},
        "cost":{"label":"Cost","heading":"Cost: Both Expensive Long-Term",
            "html": comparison_table([
                ("Puppy (reputable)","$1,500-$3,000","$1,800-$3,500"),
                ("First-year total","$5,000-$8,500","$3,800-$6,800"),
                ("Annual ongoing","$2,800-$5,000","$2,400-$4,200"),
                ("Food (giant vs large)","$1,500-$2,500/yr","$700-$1,200/yr"),
                ("Annual cardiac screening","Recommended","Essential from age 3"),
            ], headers)},
        "decision":{"label":"Decision","heading":"Which Should You Choose?",
            "html": style_h3("Choose Great Dane if you...")
            + style_p("Want a low-energy gentle giant. Have space for 150-200 lb dog. Emotionally prepared for 7-10 year lifespan. Cool climate.")
            + style_h3("Choose Doberman if you...")
            + style_p("Want a protective partner. Active outdoor lifestyle. Can commit to annual cardiac screening. Moderate/warm climate (indoor primary).")
            + style_h3("Compare with related options")
            + style_p("See <a href=\"/blogs/dog-breeds/rottweiler-vs-doberman-pinscher\">Rottweiler vs Doberman</a>, <a href=\"/blogs/dog-breeds/cane-corso-vs-great-dane\">Cane Corso vs Great Dane</a>, or <a href=\"/blogs/dog-breeds/german-shepherd-vs-doberman\">German Shepherd vs Doberman</a>.")},
    }
    faq = [
        {"q":"Can a Great Dane really live in an apartment?","a":"Surprisingly yes. Low energy means 30-45 minute walk plus indoor lounging satisfies exercise needs."},
        {"q":"Which has more health issues?","a":"Both face elevated cardiac disease (Dane: DCM + bloat; Doberman: ~50-60% lifetime DCM). Lifetime medical cost is similar."},
        {"q":"Are Dobermans really vicious?","a":"No - dated reputation. Modern Dobermans are vigilant family dogs, vocally alert but stable when properly socialized."},
        {"q":"Do Dobermans really have 50% DCM rates?","a":"Yes. Per cardiology studies, lifetime DCM prevalence is approximately 50-60% - the highest of any breed."},
        {"q":"What about Rottweiler as an alternative?","a":"Worth considering. <a href=\"/blogs/dog-breeds/rottweiler\">Rottweiler</a> sits between the two - calmer than Doberman, more protective than Dane."},
    ]
    return {
        "meta": _make_meta(
            "Great Dane vs Doberman Pinscher","great-dane-vs-doberman","Guard & Giant Breed Comparisons",
            "Great Dane vs Doberman: gentle giant vs vigilant athlete. Size, family fit, cardiac risks, and which breed is right for your home.",
            ["comparison","great-dane","doberman-pinscher","giant-breed","guard-dog","family-dog","dog-breeds"],
            "Great Dane vs Doberman compared: 150 vs 70 lbs, gentle giant vs protective athlete, DCM risk, family fit, mistakes to avoid.",
            "Great Dane vs Doberman: size, temperament, DCM risk, family fit. Which is right?",
        ),
        "stats":{"size":{"emoji":"📏","label":"Size","value":"Large-Giant"},"weight":{"emoji":"⚖️","label":"Weight","value":"60-200 lbs"},"lifespan":{"emoji":"📅","label":"Lifespan","value":"7-13 yrs"},"exercise":{"emoji":"🏃","label":"Exercise","value":"30-120 min"},"grooming":{"emoji":"✂️","label":"Grooming","value":"Low (both)"},"training":{"emoji":"🎓","label":"Training","value":"Dane: Mod / Doberman: Excellent"},"with_kids":{"emoji":"👨‍👩‍👧","label":"With Kids","value":"Excellent (both)"},"beginners":{"emoji":"🌱","label":"Beginners","value":"Caution (both)"}},
        "images":{"hero":{"url": PLACEHOLDER_HERO,"alt":"Great Dane and Doberman Pinscher side by side, large breed comparison"}},
        "sections": sections, "faq": faq,
    }


def main() -> int:
    articles = [
        build_golden_vs_gsd(),
        build_corso_vs_dane(),
        build_berne_vs_aussie(),
        build_vizsla_vs_gsp(),
        build_dane_vs_doberman(),
    ]
    written = []
    for art in articles:
        slug = art["meta"]["slug"]
        p = BD / f"{slug}.json"
        p.write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")
        total = sum(len(v.get("html", "")) for v in art["sections"].values())
        print(f"  {p.name:<48} {total:>6} chars + {len(art['faq'])} FAQs")
        written.append(slug)
    print(f"\nWrote {len(written)} v4 comparison articles with new content sections.")
    print(f"Run:  echo YES | python3 scripts/generate.py {' '.join(written)} --publish")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
