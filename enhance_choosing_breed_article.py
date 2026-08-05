"""Enhance the legacy /choosing-the-perfect-dog-breed... stub article.

Rewrites the body into a 6-factor decision guide where each factor links
to relevant Wooffy roundups. Adds a quick-pick decision matrix, FAQ, JSON-LD
schema, and related reading.

Preserves the URL, title, and 2023 publish date.
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
ARTICLE_ID = 564645560374
BLOG_BASE  = "/blogs/dog-breeds"


def link(slug, label):
    return f'<a href="{BLOG_BASE}/{slug}" style="color:#1a1a1a;font-weight:700;text-decoration:underline;text-underline-offset:3px;">{label}</a>'


def build_intro():
    return (
        "<p>Bringing home a new dog is one of the highest-leverage decisions you'll "
        "make as a household. The wrong match leads to stress, returns, and heartbreak. "
        "The right match is a 10-15 year companion who fits your home like it was made "
        "for them.</p>"
        "<p>This guide walks through the six factors that actually decide breed fit - "
        "and links you straight to the relevant Wooffy roundups for each one. Read it "
        "in order, then use the quick-pick matrix at the bottom to shortlist 3-4 breeds "
        "to research deeper.</p>"
    )


def build_factor(num, heading, body_paragraphs, links_block):
    paragraphs = "".join(f'<p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 14px 0;">{p}</p>' for p in body_paragraphs)
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Factor {num}</p>
  <h2 id="factor-{num}" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">{heading}</h2>
  {paragraphs}
  {links_block}
</div>"""


def starter_links_block(items):
    li = "".join(
        f'    <li style="margin-bottom:6px;">{link(slug, label)} - <span style="color:#6b7177;">{note}</span></li>\n'
        for slug, label, note in items
    )
    return f"""<div style="background:#f8f8f8;border-radius:8px;padding:18px 22px;margin-top:16px;">
    <p style="font-size:0.78em;color:#1a1a1a;font-weight:700;margin:0 0 10px 0;text-transform:uppercase;letter-spacing:0.5px;">Start here</p>
    <ul style="font-size:0.92em;line-height:1.6;color:#6b7177;padding-left:18px;margin:0;">
{li}    </ul>
  </div>"""


def build_lifestyle_factor():
    return build_factor(
        1, "1. Match Your Lifestyle",
        [
            "Be honest about how active you actually are - not how active you wish you were. A breed that needs two hours of running daily will be miserable with a desk-job owner who walks 30 minutes after work. Conversely, a low-energy breed paired with a marathon runner won't keep up.",
            "Also assess your home: apartment vs. house with yard, kids in the household, allergy concerns, other pets, how often you travel, and how many hours the dog will be alone. Each of these constrains the realistic shortlist.",
        ],
        starter_links_block([
            ("21-great-dog-breeds-for-small-apartments", "Best Apartment Dogs",        "If you live in a small space"),
            ("best-dogs-for-active-people",              "Best Dogs for Active People", "If you run, hike, or train daily"),
            ("best-dogs-for-first-time-owners",          "Best for First-Time Owners",  "If this is your first dog"),
            ("best-dogs-for-seniors",                    "Best Dogs for Seniors",       "If you want a calm companion"),
        ])
    )


def build_size_factor():
    return build_factor(
        2, "2. Size and Exercise Needs",
        [
            "A dog's adult size determines food cost, gear cost, vet cost, and how easily they fit in your space - but exercise needs matter even more. A 70-lb Greyhound is calmer indoors than a 12-lb Jack Russell.",
            "Match the breed's daily exercise requirement to the realistic minimum you can commit to every day, including bad weather and busy weeks. If you can do 30 minutes a day, choose a breed designed for 30 minutes; don't pick a 2-hour breed and hope to keep up.",
        ],
        starter_links_block([
            ("best-small-dog-breeds",       "Best Small Dog Breeds",       "Toy and small companions"),
            ("best-large-dog-breeds",       "Best Large Dog Breeds",       "Big-but-manageable companions"),
            ("best-gentle-giant-dog-breeds","Best Gentle Giants",          "When bigger really is better"),
            ("dog-breeds-by-size",          "All Breeds, Sorted by Size",  "Toy / Small / Medium / Large / Giant"),
        ])
    )


def build_temperament_factor():
    return build_factor(
        3, "3. Temperament and Personality",
        [
            "Each breed has predictable temperament tendencies - working drive, sociability, alertness, independence. These show up regardless of how you train.",
            "Decide what you actually want: a velcro companion who follows you everywhere, an independent thinker who's fine alone, a watchful alert-barker, a quiet roommate. Mismatch here is the #1 reason new owners feel buyer's remorse.",
        ],
        starter_links_block([
            ("most-loyal-dog-breeds",        "Most Loyal Dog Breeds",       "Velcro companions"),
            ("most-intelligent-dog-breeds",  "Most Intelligent Breeds",     "Smart - which can be a feature or a bug"),
            ("easiest-dogs-to-train",        "Easiest Dogs to Train",       "If you want fast, reliable training"),
            ("quietest-dog-breeds",          "Quietest Dog Breeds",         "If you have neighbors close by"),
            ("best-watchdog-breeds",         "Best Watchdog Breeds",        "Alert without aggression"),
        ])
    )


def build_grooming_factor():
    return build_factor(
        4, "4. Grooming and Maintenance",
        [
            "Coat type drives time and money. Short single coats (Boxer, Beagle) are nearly maintenance-free. Double coats (Husky, Golden) shed seasonally and heavily. Curly/wavy hypoallergenic-style coats (Poodle, Bichon, Doodles) need professional grooming every 6-8 weeks - that's $60-150 each visit.",
            "Be honest about whether you'll actually brush a long-coated breed daily. Mat-prone coats neglected for 2 weeks turn into a $400 shave-down at the groomer.",
        ],
        starter_links_block([
            ("best-hypoallergenic-dog-breeds", "Best Hypoallergenic Breeds", "Low-shedding picks for sensitive owners"),
            ("low-maintenance-dog-breeds",     "Low-Maintenance Breeds",     "Minimal grooming time required"),
        ])
    )


def build_health_factor():
    return build_factor(
        5, "5. Health Considerations",
        [
            "Every breed has predictable health risks - hip dysplasia in larger breeds, brachycephalic syndrome in flat-faced breeds, cardiac issues in Cavaliers and Dobermans, eye conditions in Collies. These are not deal-breakers but they affect lifetime cost and quality of life.",
            "Before committing, check the breed's longevity and expected vet costs, and choose a reputable breeder who screens parents for the relevant conditions.",
        ],
        starter_links_block([
            ("longest-living-dog-breeds", "Longest-Living Dog Breeds", "Plan for 12-18 years together"),
            ("rarest-dog-breeds",         "Rarest Dog Breeds",         "Niche picks - factor breeder access"),
        ])
    )


def build_research_factor():
    return build_factor(
        6, "6. Research and Real-World Exposure",
        [
            "After narrowing to 3-4 candidate breeds, do this before buying: read each breed's full Wooffy guide, talk to two owners (online forums and local meetups), visit a breed-specific event or show, and meet at least one adult of the breed in person.",
            "Most online breed descriptions paint the dog at its best. Meeting an adult tells you what you're really signing up for - the bark, the energy bursts, the size at full growth, the daily reality.",
        ],
        starter_links_block([
            ("most-popular-dog-breeds",                  "Most Popular Dog Breeds",      "Where to start with mainstream picks"),
            ("dog-breeds-by-group",                      "All Breeds by AKC Group",      "Working / Sporting / Toy / Hound / Herding / etc."),
            ("us-the-most-popular-dog-breeds-of-2022",   "AKC 2023 Top-100 Ranking",     "Full ranking with deep links"),
        ])
    )


def build_quick_pick():
    rows = [
        ("Apartment + first-time owner",        ("21-great-dog-breeds-for-small-apartments", "Apartment-friendly"), ("best-dogs-for-first-time-owners", "First-time owner")),
        ("House + active outdoors",             ("best-dogs-for-active-people", "Active people"),                  ("best-dogs-for-hiking", "Hiking partners")),
        ("Family with young kids",              ("best-family-dog-breeds", "Family-friendly"),                     ("best-large-dog-breeds", "Large gentle breeds")),
        ("Allergies in the household",          ("best-hypoallergenic-dog-breeds", "Hypoallergenic"),              ("best-small-dog-breeds", "Small low-shedders")),
        ("Want a watchful, protective dog",     ("best-watchdog-breeds", "Watchdog breeds"),                       ("best-guard-dog-breeds", "Guard breeds")),
        ("Cold climate / lots of outdoor time", ("best-dogs-for-cold-climates", "Cold-climate"),                   ("best-working-dog-breeds", "Working breeds")),
        ("Hot climate / short coats only",      ("best-dogs-for-hot-climates", "Hot-climate"),                     ("best-sporting-dog-breeds", "Sporting breeds")),
        ("Quiet building / no barking",         ("quietest-dog-breeds", "Quietest breeds"),                        ("best-toy-dog-breeds", "Toy breeds")),
        ("Senior household",                    ("best-dogs-for-seniors", "Best for seniors"),                     ("low-maintenance-dog-breeds", "Low-maintenance")),
    ]
    cells = ""
    for situation, (s1, l1), (s2, l2) in rows:
        cells += (
            '<tr style="border-bottom:1px solid #e8e8e8;">'
            f'<td style="padding:10px 12px;color:#1a1a1a;font-weight:700;">{situation}</td>'
            f'<td style="padding:10px 12px;">{link(s1, l1)}</td>'
            f'<td style="padding:10px 12px;">{link(s2, l2)}</td>'
            "</tr>"
        )
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Quick Pick</p>
  <h2 id="quick-pick" style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">Quick-Pick: Match Your Situation</h2>
  <p style="font-size:0.9em;color:#6b7177;margin:0 0 16px 0;">Find the row that best describes your household, then click both linked roundups for a fast shortlist.</p>
  <div style="overflow-x:auto;">
    <table style="width:100%;font-size:0.92em;border-collapse:collapse;min-width:560px;">
      <thead>
        <tr>
          <th style="padding:10px 12px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Your situation</th>
          <th style="padding:10px 12px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Start with</th>
          <th style="padding:10px 12px;text-align:left;font-weight:700;color:#1a1a1a;background:#f8f8f8;border-bottom:2px solid #d8d8d8;">Then explore</th>
        </tr>
      </thead>
      <tbody>
        {cells}
      </tbody>
    </table>
  </div>
</div>"""


FAQS = [
    ("How do I choose the right dog breed for me?",
     "Work through the 6 factors above in order: lifestyle, size/exercise, temperament, grooming, health, and real-world research. After each factor, narrow your list. By the end you should have 3-4 candidate breeds to research deeply."),
    ("What's the most important factor in picking a breed?",
     "Honest assessment of your daily routine. The biggest predictor of buyer's remorse is choosing a breed whose exercise or temperament needs don't match how you actually live - not how you intend to live."),
    ("Should I get a puppy or adopt an adult?",
     "Adults are usually easier - their size, temperament, and energy level are already known. Puppies offer a longer relationship and total customization of habits, but require massive time investment in the first year. Both paths can work; the choice comes down to your time budget."),
    ("How do I know if a breeder is reputable?",
     "Reputable breeders health-test parents for breed-specific conditions, raise puppies in the home (not a kennel), let you visit and meet the parents, ask you screening questions, take dogs back at any point in life, and have waiting lists. If a breeder can ship a puppy this week with no questions asked, walk away."),
    ("How long should I research before getting a dog?",
     "At minimum a few weeks. Read 2-3 deep breed guides, talk to two current owners, meet an adult of the breed in person, and let yourself sleep on the decision. Impulse adoptions are the most common source of returns to shelters."),
    ("Are mixed-breed dogs a good option?",
     "Yes - and often a great one. Mixed-breed dogs from shelters are typically lower-cost, often healthier (hybrid vigor), and you can usually meet the adult dog before committing. Trade-off: predicting size, temperament, and grooming needs is harder."),
    ("What if I pick the wrong breed?",
     "Most breed-mismatch issues are fixable with training and lifestyle adjustment. If they aren't, contact the breeder (reputable ones take dogs back) or a breed-specific rescue - never surrender to a general shelter. Better to plan well now than rehome later."),
]


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


def build_faq_schema():
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'


def build_related():
    items = [
        ("most-popular-dog-breeds",                  "Most Popular Dog Breeds",      "If you want to start with mainstream picks"),
        ("dog-breeds-by-group",                      "Browse by AKC Group",          "Working / Sporting / Toy / Herding / etc."),
        ("dog-breeds-by-size",                       "Browse by Size",               "Toy / Small / Medium / Large / Giant"),
        ("21-great-dog-breeds-for-small-apartments", "21 Best Apartment Dogs",       "Specifically for small spaces"),
        ("best-family-dog-breeds",                   "Best Family Dog Breeds",       "Households with kids"),
    ]
    li = "".join(
        f'    <li><a href="{BLOG_BASE}/{slug}" style="color:#1a1a1a;font-weight:700;text-decoration:underline;text-underline-offset:3px;">{name}</a> - {note}</li>\n'
        for slug, name, note in items
    )
    return f"""<div style="margin-bottom:48px;padding-top:32px;border-top:1px solid #e8e8e8;">
  <p style="font-family:'figmaMono','SF Mono',monospace;font-size:0.7em;font-weight:400;letter-spacing:0.54px;text-transform:uppercase;color:rgba(0,0,0,0.45);margin:0 0 8px 0;">Explore More</p>
  <h2 style="font-size:1.5em;font-weight:700;color:#1a1a1a;margin:0 0 16px 0;line-height:1.2;">Related Reading</h2>
  <ul style="font-size:0.95em;font-weight:400;line-height:1.9;color:#6b7177;padding-left:20px;margin:0;">
{li}  </ul>
</div>"""


def build_full_body():
    return (
        build_intro()
        + build_lifestyle_factor()
        + build_size_factor()
        + build_temperament_factor()
        + build_grooming_factor()
        + build_health_factor()
        + build_research_factor()
        + build_quick_pick()
        + build_faq()
        + build_related()
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
        with open("output/choosing-breed-preview.html", "w", encoding="utf-8") as f:
            f.write(body)
        print("Wrote preview to output/choosing-breed-preview.html (use --push to apply)")


if __name__ == "__main__":
    main()
