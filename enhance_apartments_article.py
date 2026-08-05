"""
Enhance the legacy /21-great-dog-breeds-for-small-apartments article in place.

What it does:
- Builds a new body_html with: intro, comparison table, "what to look for",
  TOC, 21 breed cards (HD image clickable to breed page + apartment tagline +
  short summary + "Read full guide" link), FAQ, related reading, Wooffy House CTA.
- PUTs the new body to Shopify so the URL, post date, and SEO signals stay.

Run:
  python3 enhance_apartments_article.py            # dry run, writes preview HTML
  python3 enhance_apartments_article.py --push     # push to Shopify
"""

import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
STORE   = os.environ["SHOPIFY_STORE"]
TOKEN   = os.environ["SHOPIFY_TOKEN"]
BLOG_ID = os.environ["SHOPIFY_BLOG_ID"]
ARTICLE_ID = 564906426422
BLOG_BASE  = "/blogs/dog-breeds"

# (rank, slug, apartment_tagline, apartment_fit_score_1to5)
BREEDS = [
    (1,  "bichon-frise",                  "Quiet, low-shedding, content with a daily walk — built for small spaces.",        5),
    (2,  "cavalier-king-charles-spaniel", "Calm, affectionate lapdog who matches your energy level instead of demanding more.",    5),
    (3,  "maltese",                       "Tiny indoor companion under 7 lbs, gentle and easy to live with.",                     5),
    (4,  "miniature-poodle",              "Smart, low-shedding, easy to train in tight quarters.",                                 5),
    (5,  "affenpinscher",                 "Compact toy with big personality — doesn't need a yard.",                          4),
    (6,  "pekingese",                     "Low-energy companion who'd rather nap on the couch than run.",                          5),
    (7,  "havanese",                      "Small, social, low-shedding velcro dog.",                                               5),
    (8,  "pug",                           "Quiet, low-exercise, happy as long as you're nearby.",                                  5),
    (9,  "shih-tzu",                      "Bred to be a palace lapdog — apartment life is in the DNA.",                       5),
    (10, "basset-hound",                  "Low energy and surprisingly couch-loving — just check noise rules (the bays).",   3),
    (11, "boston-terrier",                "Compact tuxedo, low-shedding, moderate exercise.",                                      5),
    (12, "chihuahua",                     "Pocket-sized, indoor-happy, minimal walking range needed.",                             5),
    (13, "yorkshire-terrier",             "Tiny, hypoallergenic-style coat, content indoors.",                                     5),
    (14, "bulldog",                       "Couch potato in a 50-lb package — surprisingly apartment-friendly.",               4),
    (15, "french-bulldog",                "Quiet, low-energy, doesn't need a yard.",                                               5),
    (16, "shiba-inu",                     "Cat-clean and quiet — fastidiously tidy indoors.",                                 4),
    (17, "italian-greyhound",             "Sprinter outdoors, statue indoors — a true apartment dog.",                        5),
    (18, "coton-de-tulear",               "Soft cotton coat, gentle, low-bark.",                                                   5),
    (19, "whippet",                       "Calm, quiet, sleeps 18 hours a day — a surprise apartment dog.",                   5),
    (20, "american-eskimo-dog",           "Bright and alert; the smaller and miniature varieties slot into flats well.",           4),
    (21, "greyhound",                     "Couch potato sprinter — short bursts, then naps all day.",                         4),
]

# Short pitch shown under each breed (1-2 sentences). Stored here so the apartment-context
# framing stays consistent rather than reusing each breed JSON's generic intro.
BREED_PITCH = {
    "bichon-frise":                  "A cheerful, curly-coated companion bred for centuries to be a tidy lap dog. Low shedding plus a soft, friendly bark makes them one of the easiest apartment fits.",
    "cavalier-king-charles-spaniel": "A gentle, sweet-natured spaniel that adapts to your pace. Happy with a brisk walk and a soft seat next to you.",
    "maltese":                       "Under 7 lbs of silky-coated charm. Bred to be a portable companion to royalty — no surprise they thrive in small spaces.",
    "miniature-poodle":              "All the smarts of a Standard Poodle in a 10–15 lb package. Hypoallergenic-style coat, eager to learn, and trainable for elevators, hallways, and shared lobbies.",
    "affenpinscher":                 "Pint-sized terrier-cousin with a clownish personality. Gets daily exercise needs from indoor play and short walks.",
    "pekingese":                     "Dignified, slow-paced, and low-effort. Famous for being calmly indifferent — ideal for quiet buildings.",
    "havanese":                      "Cuba's national dog: cheerful, low-shedding, and bonded to family. Adapts to apartments effortlessly.",
    "pug":                           "Charming brachycephalic clown with very modest exercise needs. Heat sensitive — indoor AC suits them perfectly.",
    "shih-tzu":                      "Literally bred to live in palace rooms. Calm, sociable, and content with two short walks a day.",
    "basset-hound":                  "Low to the ground, low energy, and built to lounge. Heads up: their hound bay is loud — verify your building allows it.",
    "boston-terrier":                "American-born tuxedo dog. Compact, polite, and perfectly suited to small homes and shared walls.",
    "chihuahua":                     "The smallest AKC breed. Indoor exercise often covers their daily needs.",
    "yorkshire-terrier":             "Toy terrier with a silky, single-layer coat. Bold personality fits small spaces — just train against alert-barking.",
    "bulldog":                       "Surprisingly couch-bound for their bulk. Short walks, long naps, and air conditioning are all they really ask for.",
    "french-bulldog":                "America's most popular breed for a reason — quiet, affectionate, and content in a one-bedroom flat.",
    "shiba-inu":                     "Cat-like cleanliness and a quiet demeanor indoors. Expect a structured walk plan and you're set.",
    "italian-greyhound":             "Slim, refined toy sighthound. Sprints in short bursts outdoors, statues himself on the couch indoors.",
    "coton-de-tulear":               "Soft cotton-like coat and a soft personality. Companion-bred and apartment-ready.",
    "whippet":                       "Often called \"velcro greyhounds.\" One sprint a day, then a nap on every soft surface in your apartment.",
    "american-eskimo-dog":           "Sharp, alert spitz that comes in toy, miniature, and standard. Toy/Mini are great in flats; Standard needs more room.",
    "greyhound":                     "Retired racers are famously calm. Two short walks plus a couch — the rest of the day is sleep.",
}


def load_breed(slug):
    with open(f"breed-data/{slug}.json", encoding="utf-8") as f:
        return json.load(f)


def stat_value(stats_dict, key):
    v = stats_dict.get(key)
    if isinstance(v, dict):
        return v.get("value", "")
    return str(v) if v else ""


def stars(n):
    return "★" * n + "☆" * (5 - n)


def build_intro_html():
    return (
        "<p>Living in a small apartment doesn't mean compromising on a furry companion. "
        "Many breeds genuinely thrive in compact homes — and the difference between a great fit "
        "and a stressful match comes down to size, energy needs, bark tendency, and how well the "
        "breed adapts to indoor life.</p>"
        "<p>Below are 21 dog breeds that consistently do well in apartments, "
        "with HD photos, quick stats, and a one-line take on why each one works. "
        "Click any breed to read its full guide.</p>"
    )


def build_comparison_table(rows):
    cells = ""
    for rank, slug, name, size, weight, exercise, grooming, fit in rows:
        cells += (
            '<tr style="border-bottom:1px solid #e8e8e8;">'
            f'<td style="padding:8px 10px;color:#6b7177;">{rank}</td>'
            f'<td style="padding:8px 10px;color:#1a1a1a;font-weight:700;"><a href="{BLOG_BASE}/{slug}" style="color:#1a1a1a;text-decoration:none;">{name}</a></td>'
            f'<td style="padding:8px 10px;color:#6b7177;">{size}</td>'
            f'<td style="padding:8px 10px;color:#6b7177;">{weight}</td>'
            f'<td style="padding:8px 10px;color:#6b7177;">{exercise}</td>'
            f'<td style="padding:8px 10px;color:#6b7177;">{grooming}</td>'
            f'<td style="padding:8px 10px;color:#1a1a1a;letter-spacing:1px;">{stars(fit)}</td>'
            "</tr>"
        )
    return f"""<div style="margin:32px 0;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">At a Glance</p>
  <h2 id="comparison" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">Quick Comparison: All 21 Breeds</h2>
  <div style="overflow-x:auto;">
    <table style="width:100%;font-size:0.88em;border-collapse:collapse;min-width:640px;">
      <thead>
        <tr>
          <th style="padding:10px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">#</th>
          <th style="padding:10px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Breed</th>
          <th style="padding:10px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Size</th>
          <th style="padding:10px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Weight</th>
          <th style="padding:10px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Exercise</th>
          <th style="padding:10px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Grooming</th>
          <th style="padding:10px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Apartment Fit</th>
        </tr>
      </thead>
      <tbody>
        {cells}
      </tbody>
    </table>
  </div>
</div>"""


def build_what_to_look_for():
    items = [
        ("Size and weight",        "Most buildings have a 25–50 lb weight cap. Always check your lease before falling for a 70-lb couch potato."),
        ("Exercise needs",         "A breed that needs 2+ hours of running daily will be unhappy in 600 sq ft. Look for breeds whose daily exercise can be covered with a couple of brisk walks."),
        ("Bark tendency",          "Thin walls + alert-barker = neighbor complaints. Choose breeds known for being quiet, or commit to early bark training."),
        ("Coat and shedding",      "Heavy shedders coat upholstery in days. Low-shedding or single-coat breeds are easier in close quarters."),
        ("Adaptability",           "Some breeds (Cavaliers, Frenchies, Greyhounds) are happiest matching your energy. Others need a job. Match temperament to your routine."),
        ("Building rules",         "Many buildings restrict specific breeds (Bulldogs, Pit-type breeds, Rottweilers, etc.). Read the lease fine print before adopting."),
    ]
    body = "".join(
        f'<div style="margin-bottom:18px;"><strong style="color:#1a1a1a;">{title}.</strong> <span style="color:#6b7177;">{text}</span></div>'
        for title, text in items
    )
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Buyer's Guide</p>
  <h2 id="what-to-look-for" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">What to Look For in an Apartment Dog</h2>
  {body}
</div>"""


def build_toc(rows):
    items = "".join(
        f'<li style="margin-bottom:6px;"><a href="#breed-{slug}" style="color:#1a1a1a;text-decoration:underline;text-underline-offset:3px;">{rank}. {name}</a></li>'
        for rank, slug, name, *_ in rows
    )
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Jump To</p>
  <h2 id="toc" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">The 21 Breeds</h2>
  <ol style="font-size:0.95em;line-height:1.6;color:#6b7177;padding-left:20px;margin:0;columns:2;column-gap:32px;">
    {items}
  </ol>
</div>"""


def build_breed_card(rank, slug, name, hero_url, size, weight, exercise, grooming, tagline, pitch):
    breed_url = f"{BLOG_BASE}/{slug}"
    stats_line = f"{size} · {weight} · Exercise: {exercise} · Grooming: {grooming}"
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <h2 id="breed-{slug}" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">
    {rank}. <a href="{breed_url}" style="color:#1a1a1a;text-decoration:none;">{name}</a>
  </h2>
  <a href="{breed_url}" style="text-decoration:none;color:inherit;display:block;">
    <figure style="margin:0 0 16px 0;">
      <img src="{hero_url}" alt="{name}" loading="lazy"
        style="width:100%;height:auto;border-radius:8px;display:block;box-shadow:rgba(0,0,0,0.07) 0px 8px 24px;">
    </figure>
  </a>
  <p style="font-size:0.78em;color:#6b7177;margin:0 0 12px 0;font-family:'figmaMono','SF Mono',monospace;letter-spacing:0.3px;">{stats_line}</p>
  <p style="font-size:0.95em;color:#1a1a1a;font-weight:600;margin:0 0 12px 0;">Apartment fit: <span style="font-weight:400;">{tagline}</span></p>
  <p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 16px 0;">{pitch}</p>
  <a href="{breed_url}" style="display:inline-block;font-size:0.88em;color:#1a1a1a;font-weight:700;text-decoration:underline;text-underline-offset:3px;">Read the full {name} guide →</a>
</div>"""


FAQS = [
    ("What's the quietest dog breed for apartments?",
     "Basenjis (which don't bark in the typical sense), Whippets, Greyhounds, and Cavalier King Charles Spaniels are some of the quietest popular options. Pugs and French Bulldogs are also relatively quiet apart from snoring."),
    ("Are big dogs OK in apartments?",
     "Yes — if their energy is moderate. Greyhounds, Whippets, and Bulldogs can be excellent apartment dogs because they sleep most of the day. The bigger problem is usually building weight limits, not the dog."),
    ("Which apartment dogs need the least exercise?",
     "Pugs, Bulldogs, Pekingese, Shih Tzus, and Cavaliers all do well on 30 minutes a day or less of structured walking, plus indoor play."),
    ("Are Pugs and Bulldogs really good apartment dogs?",
     "Yes, with one caveat: brachycephalic (short-nosed) breeds are heat sensitive and shouldn't be exercised in hot weather. Air conditioning and indoor play handle most of their needs."),
    ("Best hypoallergenic dogs for apartments?",
     "Bichon Frise, Maltese, Miniature Poodle, Havanese, Coton de Tulear, and Yorkshire Terrier all shed minimally. \"Hypoallergenic\" is shorthand — no dog is 100% allergen-free, but these produce far less dander."),
    ("How long can apartment dogs be left alone?",
     "Adult dogs of most breeds can handle 4–6 hours alone if exercised before and after. Young puppies need much shorter intervals. If you work long days, plan for a midday walker or doggy daycare."),
    ("Do small dogs bark more than big dogs?",
     "Sometimes — small breeds like Chihuahuas and Yorkshire Terriers can be alert-barkers. With consistent training from puppyhood, this is manageable. Big calm breeds like Greyhounds tend to be quieter by default."),
]


def build_faq_schema():
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in FAQS
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'


def build_faq():
    items = ""
    for i, (q, a) in enumerate(FAQS):
        border_bottom = ";border-bottom:1px solid #e8e8e8" if i == len(FAQS) - 1 else ""
        items += f"""
  <details style="border-top:1px solid #e8e8e8{border_bottom};">
    <summary style="padding:18px 0;font-size:0.95em;font-weight:700;color:#1a1a1a;display:flex;justify-content:space-between;align-items:center;list-style:none;user-select:none;cursor:pointer;">
      {q}
      <span class="faq-icon" style="font-size:1.4em;font-weight:300;color:#6b7177;flex-shrink:0;margin-left:16px;line-height:1;">+</span>
    </summary>
    <p style="font-size:0.9em;font-weight:400;line-height:1.7;color:#6b7177;margin:0 0 18px 0;padding-right:24px;">{a}</p>
  </details>"""
    return f"""<style>
.wooffy-faq summary::-webkit-details-marker{{display:none;}}
.wooffy-faq details[open] .faq-icon{{transform:rotate(45deg);}}
.wooffy-faq .faq-icon{{transition:transform 0.22s ease;display:inline-block;}}
</style>
<div class="wooffy-faq" style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">FAQ</p>
  <h2 id="faq" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 4px 0;line-height:1.2;">Frequently Asked Questions</h2>
{items}
</div>"""


def build_related():
    items = [
        ("best-small-dog-breeds",          "Best Small Dog Breeds",          "All small breeds, ranked"),
        ("best-dogs-for-first-time-owners", "Best Dogs for First-Time Owners", "Easier-to-train, easier-to-live-with picks"),
        ("best-hypoallergenic-dog-breeds", "Best Hypoallergenic Dog Breeds", "Low-shedding breeds for sensitive owners"),
        ("quietest-dog-breeds",            "Quietest Dog Breeds",            "Low-bark picks for shared walls"),
        ("best-dogs-for-seniors",          "Best Dogs for Seniors",          "Calm, low-maintenance companions"),
    ]
    li = "".join(
        f'    <li><a href="{BLOG_BASE}/{slug}" style="color:#1a1a1a;font-weight:700;text-decoration:underline;text-underline-offset:3px;">{name}</a> — {note}</li>\n'
        for slug, name, note in items
    )
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Explore More</p>
  <h2 style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">Related Reading</h2>
  <ul style="font-size:0.95em;font-weight:400;line-height:1.9;color:#6b7177;padding-left:20px;margin:0;">
{li}  </ul>
</div>"""


def build_wooffy_house_cta():
    return """<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">From Wooffy</p>
  <h2 style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">Wooffy House: Designed for Apartment-Dwelling Dogs</h2>
  <p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 16px 0;">Apartment dogs need a calm, defined space of their own. <strong style="color:#1a1a1a;">Wooffy House</strong> was built specifically for small spaces — a quiet retreat that doubles as bed, den, and a place that's clearly theirs. No yard required.</p>
  <a href="https://thewooffy.com/products/wooffy-house" style="display:inline-block;background:#000000;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:50px;font-weight:500;font-size:0.85em;letter-spacing:-0.14px;">Explore Wooffy House</a>
</div>"""


def build_conclusion():
    return """<div style="margin-bottom:32px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Final Word</p>
  <h2 style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">Pick the Match, Not the Picture</h2>
  <p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0;">The best apartment dog isn't always the smallest — it's the one whose energy, bark tendency, and adaptability actually fit your routine. Use the comparison table above to shortlist three or four, then read each breed's full guide before deciding. Your future self (and your neighbors) will thank you.</p>
</div>"""


def build_full_body():
    rows = []
    for rank, slug, _tagline, _fit in BREEDS:
        b = load_breed(slug)
        name = b["meta"]["name"]
        size = stat_value(b["stats"], "size")
        weight = stat_value(b["stats"], "weight")
        exercise = stat_value(b["stats"], "exercise")
        grooming = stat_value(b["stats"], "grooming")
        rows.append((rank, slug, name, size, weight, exercise, grooming, _fit))

    cards = ""
    for (rank, slug, tagline, fit), row in zip(BREEDS, rows):
        b = load_breed(slug)
        name = b["meta"]["name"]
        hero_url = b["images"]["hero"]["url"]
        _, _, _, size, weight, exercise, grooming, _ = row
        cards += build_breed_card(rank, slug, name, hero_url, size, weight, exercise, grooming, tagline, BREED_PITCH[slug])

    return (
        build_intro_html()
        + build_comparison_table(rows)
        + build_what_to_look_for()
        + build_toc(rows)
        + cards
        + build_faq()
        + build_related()
        + build_wooffy_house_cta()
        + build_conclusion()
        + build_faq_schema()
    )


def push_to_shopify(body_html):
    url = f"https://{STORE}/admin/api/2024-01/articles/{ARTICLE_ID}.json"
    payload = {"article": {"id": ARTICLE_ID, "body_html": body_html}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("X-Shopify-Access-Token", TOKEN)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
    a = result["article"]
    print(f"Updated -> https://{STORE}/blogs/dog-breeds/{a['handle']}  (id={a['id']})")
    print(f"  body_html length: {len(a['body_html'])} chars")


def main():
    body = build_full_body()
    print(f"Built body_html: {len(body)} chars")
    if "--push" in sys.argv:
        push_to_shopify(body)
    else:
        os.makedirs("output", exist_ok=True)
        with open("output/21-apartments-preview.html", "w", encoding="utf-8") as f:
            f.write(body)
        print("Wrote preview to output/21-apartments-preview.html (use --push to apply)")


if __name__ == "__main__":
    main()
