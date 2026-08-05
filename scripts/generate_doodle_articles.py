"""
Generates the remaining doodle breed JSON files into breed-data/.
Run once: python3 scripts/generate_doodle_articles.py

Outputs:
- 4 main breed JSONs (bernedoodle, cavapoo, sheepadoodle, aussiedoodle)
- 18 supporting articles (grooming/costs/checklist for all 6 doodle breeds)
- 1 roundup (best-doodle-breeds-for-families)

goldendoodle.json and labradoodle.json main JSONs are already written by hand.
This script only emits the remaining 23 files.
"""
import json
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "breed-data")

P = 'style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0 0 20px 0;"'
P_LAST = 'style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:0;"'
H3 = 'style="font-size:0.95em;font-weight:700;color:#1a1a1a;margin:0 0 10px 0;"'
A = 'style="color:#1a1a1a;font-weight:700;"'
TH = 'style="padding:10px 12px;text-align:left;font-weight:700;color:#1a1a1a;background:#f6f6f1;border-bottom:1px solid #d0d0d0;"'
TD_LIGHT = 'style="padding:10px 12px;color:#6b7177;background:#f8f8f8;"'
TD_DARK = 'style="padding:10px 12px;color:#6b7177;background:#f6f6f1;"'
TD_LIGHT_BOLD = 'style="padding:10px 12px;font-weight:700;color:#1a1a1a;background:#f8f8f8;vertical-align:top;"'
TD_DARK_BOLD = 'style="padding:10px 12px;font-weight:700;color:#1a1a1a;background:#f6f6f1;vertical-align:top;"'
TR_BORDER = 'style="border-bottom:1px solid #e8e8e8;"'
TABLE = 'style="width:100%;border-collapse:collapse;font-size:0.88em;"'
TOTAL_LABEL = 'style="padding:10px 12px;font-weight:700;color:#1a1a1a;background:#f0f0f0;"'
TOTAL_VALUE = 'style="padding:10px 12px;font-weight:700;color:#008060;background:#f0f0f0;"'

PLACEHOLDER_IMG = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Goldendoodle_standing_in_grass.jpg/660px-Goldendoodle_standing_in_grass.jpg"


def health_row(name, body, dark):
    name_style = TD_DARK_BOLD if dark else TD_LIGHT_BOLD
    body_style = TD_DARK if dark else TD_LIGHT
    return f'<tr {TR_BORDER}><td {name_style}>{name}</td><td {body_style}>{body}</td></tr>'


def cost_row(label, first, ongoing, dark):
    style = TD_DARK if dark else TD_LIGHT
    return f'<tr {TR_BORDER}><td {style}>{label}</td><td {style}>{first}</td><td {style}>{ongoing}</td></tr>'


def build_health_table(intro_para, rows):
    body_rows = "".join(rows)
    table = (
        f'<p {P}>{intro_para}</p>'
        f'<table {TABLE}>'
        f'<thead><tr><th {TH}>Condition</th><th {TH}>What It Means</th></tr></thead>'
        f'<tbody>{body_rows}</tbody></table>'
    )
    return table


def build_cost_table(rows, total_first, total_ongoing, footnote):
    body_rows = "".join(rows)
    table = (
        f'<table {TABLE}>'
        f'<thead><tr><th {TH}>Expense</th><th {TH}>First Year</th><th {TH}>Annual (ongoing)</th></tr></thead>'
        f'<tbody>{body_rows}'
        f'<tr><td {TOTAL_LABEL}>Estimated Total</td>'
        f'<td {TOTAL_VALUE}>{total_first}</td>'
        f'<td {TOTAL_VALUE}>{total_ongoing}</td></tr>'
        f'</tbody></table>'
        f'<p style="font-size:0.82em;color:#6b7177;margin:14px 0 0 0;">{footnote}</p>'
    )
    return table


# ---------------------------------------------------------------------------
# Per-breed data for the 4 remaining main breeds
# ---------------------------------------------------------------------------

BREEDS = {
    "bernedoodle": {
        "name": "Bernedoodle",
        "weight": "25–90 lbs (Mini, Medium, Standard)",
        "size_value": "Small to Large",
        "size_category": "Small to Large Breed",
        "lifespan": "12–18 yrs",
        "exercise": "45–75 min",
        "tagline": "The Bernedoodle — Bernese Mountain Dog crossed with Poodle — was designed in 2003 by Sherry Rupke to capture the Bernese's gentle, family-oriented temperament while addressing the Bernese's heavy shedding and famously short lifespan. Done well, the Bernedoodle often lives 4–6 years longer than a purebred Berner and sheds dramatically less.",
        "excerpt": "Bernedoodles combine the Bernese Mountain Dog's calm, gentle temperament with the Poodle's low-shedding coat and longer lifespan. Lifespan extension is the breed's most-cited benefit — but only with health-tested parents from both lineages.",
        "meta_description": "Bernedoodle breed guide: lifespan extension explained, F1 vs F1B vs multigen, tri-color coat genetics, Bernese cancer risk, hip dysplasia, exercise needs, grooming costs, and choosing a tested breeder.",
        "tags_extra": ["medium-breed", "family-friendly", "low-shedding", "doodle", "gentle"],
        "intro": [
            "The Bernedoodle is a deliberate crossbreed between a Bernese Mountain Dog and a Standard, Mini, or Toy Poodle, first developed in 2003 by Sherry Rupke at SwissRidge Kennels in Ontario. The breeding goal was specific and unusual among the Doodles: address the Bernese Mountain Dog's two best-known weaknesses — heavy shedding and a tragically short lifespan (often only 7–9 years, with cancer as the dominant cause of death). Cross-breeding with the longer-lived, lower-shedding Poodle was intended to mitigate both.",
            "Bernedoodles come in three sizes depending on Poodle parent: <strong>Tiny / Toy</strong> (Toy Poodle parent, 10–24 lbs), <strong>Mini</strong> (Mini Poodle parent, 25–49 lbs), and <strong>Standard</strong> (Standard Poodle parent, 50–90 lbs). Standard Bernedoodles are the closest in size and presence to a purebred Bernese; Minis and Tinys are increasingly popular for smaller homes. Generations follow the usual Doodle convention: F1 (Berner × Poodle, variable coats), F1B (F1 × Poodle, more reliably low-shedding), multigen (third-generation+, most consistent).",
            "The signature look most associated with the Bernedoodle is the tri-color coat — black, white, and rust — that mirrors the Bernese. Tri-color is genetically recessive, and not every Bernedoodle will display it; some are bi-color (black and white), sable, merle, or solid colors. The coat is typically wavy or curly and ranges from minimally-shedding (F1B and multigen) to moderately-shedding (some F1s)."
        ],
        "appearance": [
            "Size varies from 10 lb Tiny Bernedoodles to 90 lb Standards. <strong>Standard</strong> Bernedoodles stand 23–29 inches and weigh 50–90 lbs — substantial, sturdy dogs. <strong>Mini</strong> Bernedoodles stand 18–22 inches and weigh 25–49 lbs. <strong>Tiny / Toy</strong> Bernedoodles stand 12–17 inches and weigh 10–24 lbs. Confirm the parents' sizes when evaluating a puppy.",
            "Coat is wavy or curly and ranges from low-shedding (most common) to minimally-shedding (F1B and multigen). The tri-color pattern — black with white markings and rust accents over the eyes and on the cheeks/legs — is the most sought-after but not guaranteed; a tri-color parent does not guarantee tri-color puppies. Other patterns include bi-color (black and white), sable, merle (rare and requires careful breeding to avoid double-merle health issues), and solid colors. The coat requires the same intensive grooming as other Doodles regardless of color."
        ],
        "temperament": [
            "Bernedoodles tend to inherit the Bernese Mountain Dog's calm, gentle, family-oriented disposition combined with the Poodle's intelligence and trainability. They are typically more laid-back than Goldendoodles or Labradoodles — less exhaustingly enthusiastic, more content to settle in the room with the family. The Bernese's reputation for being deeply bonded to children carries through; Standard Bernedoodles are often described as exceptional family dogs.",
            "The flip side of the Bernese temperament is a tendency toward stubbornness and a slower training maturation. Most Bernedoodles are trainable but on their own timeline — not as immediately compliant as a Lab or Golden. Patient, consistent positive reinforcement from puppyhood is essential. Some Bernedoodles inherit a reserved or aloof attitude toward strangers (Bernese trait); proper early socialization between 8–16 weeks is important.",
            "With children: excellent, often gentle and patient especially with young children. With other animals: generally excellent. With strangers: friendly but sometimes reserved at first. Separation anxiety is documented but typically less severe than in Goldendoodles."
        ],
        "mikes_take": [
            "If a family asks me about getting a Bernese Mountain Dog, my honest advice is increasingly: consider a Bernedoodle from a tested breeder instead. The Bernese is one of the most beautiful and gentle breeds in the world, but the 7–9 year average lifespan and the cancer rate (50%+ of Bernese die of cancer per breed-club studies) is a real heartbreak that many families don't recover from. A well-bred Bernedoodle frequently lives 4–6 years longer and retains most of the temperament that makes the Bernese so beloved.",
            "The catch — same as every Doodle — is that the breeder matters enormously. The lifespan benefit only materializes when both parents are health-tested and longevity is being actively selected for. A Bernedoodle bred from an untested Bernese Mountain Dog and an untested Poodle is not meaningfully healthier than a purebred Berner — the cancer genes and orthopedic risks pass through both parents. Buy from a breeder who can show you OFA clearances on both parents, who tracks the longevity of dogs they've previously placed, and who can document several generations of health data.",
            "The grooming reality is the same as the other Doodles. Professional grooming every 6–8 weeks ($80–$150) is non-negotiable, plus 2–3 brushing sessions per week at home. The Bernese's affinity for cool weather carries through — most Bernedoodles do better in moderate or cold climates than in heat."
        ],
        "care_exercise": "45–75 minutes daily for Standards; 30–45 minutes for Minis. Bernedoodles are less driven than Lab- or Australian Shepherd-based Doodles — they need real activity but are content to be settled at home between walks. Hiking, swimming, and moderate-paced play suit the breed.",
        "care_mental": "Daily training sessions, puzzle feeders, and scent work. The Poodle side contributes intelligence; the Bernese side contributes a slightly slower, more deliberate working style. Consistency matters more than intensity.",
        "care_grooming": "Professional grooming every 6–8 weeks. Brushing 2–3 times per week at home, daily during the 8–14 month coat transition. The coat is typically wavy or curly and mats aggressively without regular brushing.",
        "health_intro": "Bernedoodles share inherited health risks with both parent breeds. The Bernese Mountain Dog has one of the shortest average lifespans of any breed, driven heavily by cancer rates; the lifespan extension claim for the Bernedoodle is real but depends entirely on health-tested foundation stock.",
        "health_rows_data": [
            ("Cancer", "Bernese Mountain Dogs have very high cancer rates (~50% of deaths in studies). Histiocytic sarcoma is the most breed-specific cancer in the Bernese lineage. Crossing with Poodle reduces but does not eliminate this risk. Cancer is the leading cause of death in middle-aged and senior Bernedoodles. Choosing a breeder who tracks parent longevity is the most actionable preventive."),
            ("Hip and Elbow Dysplasia", "Both parent breeds carry elevated rates. OFA or PennHIP screening on both parents is essential. Ask for specific ratings (Excellent, Good, Fair) — not just &quot;hips have been cleared.&quot;"),
            ("Degenerative Myelopathy (DM)", "Progressive spinal cord disease causing rear-end weakness and paralysis in older dogs. DNA test available — the Bernese parent should be tested clear or carrier. Documented at elevated rates in Bernese."),
            ("Progressive Retinal Atrophy (PRA)", "Inherited retinal degeneration leading to blindness. Present in Poodles. DNA test available — Poodle parent should be tested."),
            ("Bloat / GDV", "Deep-chested Standard Bernedoodles are at GDV risk. Prophylactic gastropexy at spay/neuter is worth discussing."),
            ("Von Willebrand's Disease", "Inherited bleeding disorder from the Poodle side. DNA test available. Important to know before any surgical procedure."),
        ],
        "health_ask": "OFA hip and elbow, OFA cardiac, CAER eye exam, PRA DNA test, DM DNA test on the Bernese parent, vWD DNA test on the Poodle parent. Ask the breeder for the longevity records of dogs from previous litters.",
        "cost_puppy": ("$2,500–$5,500", "Reputable Standard Bernedoodles from health-tested breeders are at the high end of Doodle pricing — the limited supply of ethically bred Berner foundation stock keeps prices high."),
        "cost_food_year1": "$600–$1,000",
        "cost_food_ongoing": "$600–$1,000",
        "cost_groom_year1": "$600–$1,200",
        "cost_groom_ongoing": "$600–$1,200",
        "cost_insurance_year1": "$700–$1,400",
        "cost_insurance_ongoing": "$700–$1,400",
        "cost_setup": "$300–$600",
        "cost_total_first": "$5,200–$10,500",
        "cost_total_ongoing": "$2,250–$4,200",
        "cost_footnote": "Histiocytic sarcoma treatment, if it develops, runs $8,000–$25,000+. Insurance enrolled before the first vet visit is the single highest-value financial decision for this breed.",
        "good_fit": [
            "Families that want the gentle Bernese temperament without the 7-year heartbreak",
            "Active but not high-octane households — Bernedoodles need exercise but are not endurance athletes",
            "Cooler climates — Bernedoodles inherit Bernese sensitivity to heat",
            "Owners willing to invest in tested breeders ($3,000+ puppy) to realize the lifespan benefit",
            "Households that want a calm, family-oriented dog with low-shedding coat"
        ],
        "not_fit": [
            "Owners shopping primarily on price — bargain Bernedoodles often inherit cancer and orthopedic risks at full strength",
            "Hot or humid climates without air-conditioning — Bernedoodles overheat readily",
            "Households that want a high-energy dog for serious running or dog sports",
            "Owners who cannot commit to OFA-clearance verification on both parents",
            "People not prepared for the grooming cost as a permanent annual budget item"
        ],
        "finding_breeder": "$2,500–$5,500 from reputable breeders. The Bernedoodle Association of America (BAA) and the United Bernedoodle Registry maintain breeder directories. SwissRidge Kennels (originator) and member breeders publish health protocols. Required: OFA hip and elbow on both parents, OFA cardiac, CAER eye exam, PRA and DM DNA tests, vWD test on the Poodle parent. The single most valuable question to ask a Bernedoodle breeder is: &quot;What is the longevity record of dogs from previous litters?&quot; A breeder tracking this data is breeding for the lifespan benefit; a breeder who can't answer is not.",
        "finding_rescue": "Doodle Rescue Collective and IDOG Rescue both place Bernedoodles. Adult dogs offer known coat, size, and temperament, and a clearer health picture than a puppy.",
        "faqs": [
            ("Do Bernedoodles really live longer than Bernese Mountain Dogs?", "On average, yes — when bred from health-tested parents. Bernese Mountain Dogs average 7–9 years due to very high cancer rates (50%+ of deaths in breed studies). Well-bred Bernedoodles often live 12–15 years, sometimes 16–18 for smaller sizes. The lifespan benefit depends entirely on the breeder selecting for longevity and health-testing both parents. A Bernedoodle from untested parents may not significantly outlive a purebred Bernese."),
            ("What is a tri-color Bernedoodle?", "A tri-color Bernedoodle has the classic Bernese Mountain Dog coloration: predominantly black with white markings on the chest, paws, and face, plus rust-colored accents over the eyes and on the cheeks and legs. It is the most sought-after Bernedoodle color but genetically recessive — even two tri-color parents may produce non-tri-color puppies. Expect a $500–$1,500 premium for tri-color puppies from many breeders."),
            ("Are Bernedoodles good for hot climates?", "Not particularly. The Bernese Mountain Dog was bred for the Swiss Alps, and Bernedoodles often inherit heat sensitivity even though the Poodle parent handles warmth better. In hot or humid climates, Bernedoodles need air-conditioned indoor time, exercise restricted to cool morning or evening hours, and constant access to shade and water. They thrive in moderate-to-cool climates."),
            ("Is the Mini Bernedoodle as healthy as the Standard?", "Mixed evidence. Mini Bernedoodles inherit some lifespan benefit from the smaller Poodle parent (small dogs typically live longer than large dogs) but may also inherit additional health concerns from the smaller Poodle. The Toy/Tiny Bernedoodle market is also more saturated with profit-driven breeding, so tested parents are harder to verify. Stick with breeders who can document health testing on both parents regardless of size.")
        ],
        "related_breeds": [
            ("Goldendoodle", "goldendoodle", "Golden Retriever × Poodle — similar family-dog concept, more energy, similar coat care"),
            ("Sheepadoodle", "sheepadoodle", "Old English Sheepdog × Poodle — similar large-and-gentle profile, more herding instinct"),
            ("Standard Poodle", "standard-poodle", "The Poodle parent — reliably non-shedding, longer-lived, predictable temperament"),
            ("Bernese Mountain Dog", "bernese-mountain-dog", "The other purebred parent — gentle and beautiful but short-lived with high cancer rates")
        ],
    },
    "cavapoo": {
        "name": "Cavapoo",
        "weight": "9–25 lbs",
        "size_value": "Small",
        "size_category": "Small Breed",
        "lifespan": "12–15 yrs",
        "exercise": "30–45 min",
        "tagline": "The Cavapoo — Cavalier King Charles Spaniel crossed with a Miniature or Toy Poodle — is one of the most popular small Doodles, prized for its small size, affectionate temperament, and (often) low-shedding coat. The serious risk this breed inherits from the Cavalier parent is mitral valve disease, a genetic heart condition that affects more than half of Cavaliers by age 5. Choosing a breeder who heart-tests the Cavalier parent is non-negotiable.",
        "excerpt": "Cavapoos are small, affectionate, low-shedding family dogs — wonderful with children and apartment-friendly. The breed inherits a serious heart-disease risk from the Cavalier parent (mitral valve disease), making heart-tested breeding stock essential.",
        "meta_description": "Cavapoo breed guide: Cavalier mitral valve disease (MVD) risk, syringomyelia, F1 vs F1B coats, apartment suitability, exercise needs, grooming costs, and choosing a breeder who heart-tests the Cavalier parent.",
        "tags_extra": ["small-breed", "family-friendly", "apartment-friendly", "low-shedding", "doodle"],
        "intro": [
            "The Cavapoo (also called Cavoodle in Australia) is a deliberate crossbreed between a Cavalier King Charles Spaniel and a Miniature or Toy Poodle, popular since the 1990s and now one of the most common small Doodle breeds in the world. The cross was designed to combine the Cavalier's famously affectionate, child-friendly temperament with the Poodle's low-shedding coat and reduced exposure to certain Cavalier health risks.",
            "The lifespan-and-health goal is meaningful in this cross. The purebred Cavalier has one of the most concerning health profiles of any breed: more than 50% of Cavaliers develop mitral valve disease (MVD), a progressive heart condition, by age 5, and the average Cavalier lifespan is just 10–11 years. Cross-breeding with the heart-healthier Poodle dilutes some of this risk — but only when the Cavalier parent is itself heart-cleared. An untested Cavalier parent can pass MVD on regardless of the Poodle cross.",
            "Generations follow the same Doodle convention. F1 (Cavalier × Poodle) is the most common and produces variable coats. F1B (F1 × Poodle) is more reliably low-shedding. Multigen is most consistent. Most Cavapoos are F1; ask the breeder for the specific generation and the health testing done on both parents."
        ],
        "appearance": [
            "Small, compact, and rounded. Adult Cavapoos typically weigh 9–25 lbs and stand 9–14 inches at the shoulder. The Toy Poodle parent produces smaller Cavapoos; the Miniature Poodle parent produces the upper end of the range. Within litters, size variation of 3–5 lbs is normal.",
            "Coats are wavy or curly. F1B and multigen Cavapoos lean curlier and shed minimally; some F1s have wavier coats with more shedding. Colors include cream, apricot, red, chocolate, black, sable, tri-color (Blenheim-pattern from the Cavalier side), and parti combinations. The dark eyes and rounded muzzle give the Cavapoo its distinctive teddy-bear appearance."
        ],
        "temperament": [
            "Cavapoos are famously affectionate, gentle, and people-oriented. They inherit the Cavalier's reputation as a lap dog and constant companion combined with the Poodle's playful intelligence. They are excellent with children, generally great with other pets, and well-suited to apartment living and senior owners.",
            "The flip side of the deeply social temperament is intense bonding and separation anxiety. Cavapoos do not tolerate long alone-time well; they were bred to be companions and they fall apart when isolated for 8+ hours. This is the single most common owner complaint about the breed.",
            "With children: excellent, often described as one of the best small-breed choices for families. With other animals: very good. With strangers: friendly. They are not guard dogs in any sense — they will greet visitors as new friends. Training is straightforward but requires patience for housebreaking, which can take longer than with larger breeds."
        ],
        "mikes_take": [
            "The Cavapoo is one of the best small-breed family dog choices available — for the right household. The temperament is genuinely lovely, the size is apartment-friendly, and well-bred F1B or multigen Cavapoos are reliably low-shedding. The breed has become hugely popular for real, defensible reasons.",
            "Mitral valve disease is the issue that keeps me up about this breed. MVD is the leading cause of death in purebred Cavaliers, with onset often in the early years of life. The Cavapoo cross dilutes this risk, but only if the Cavalier parent itself has been heart-cleared by a board-certified veterinary cardiologist within 12 months of breeding. This is not the same as a routine vet listening with a stethoscope. Ask specifically: &quot;Has the Cavalier parent been examined by a veterinary cardiologist for MVD within the last year, and can I see the report?&quot; If the answer is no, walk away.",
            "Syringomyelia (SM) is the other Cavalier-specific concern. It is a neurological condition caused by skull malformation; affected dogs scratch at their necks and shoulders persistently and may eventually need lifelong pain management. MRI screening of breeding stock is the gold standard but is expensive and not all breeders do it. Ask whether the Cavalier parent has been MRI-screened.",
            "Cavapoos are not the breed for households with frequent extended absences. Plan for daycare, dog walkers, or a household where someone is home most of the time."
        ],
        "care_exercise": "30–45 minutes daily — moderate-pace walks, indoor play, short hikes. Cavapoos enjoy activity but are not athletes; they are equally content settled on the couch with their family.",
        "care_mental": "Daily training sessions, puzzle feeders, gentle trick training. The Poodle side wants engagement; the Cavalier side wants companionship. Both are well-served by short, frequent training games.",
        "care_grooming": "Professional grooming every 6–8 weeks. Brushing 2–3 times per week at home, paying special attention to behind the ears and around the eyes (where mats form fastest in small Doodles). Eye and tear-stain cleaning daily.",
        "health_intro": "Cavapoos inherit the most consequential health concerns of any Doodle. The Cavalier King Charles Spaniel has one of the highest documented prevalences of inherited disease of any breed — particularly mitral valve disease (MVD) and syringomyelia (SM). The Poodle cross helps but does not eliminate these risks. Verified health testing on the Cavalier parent is the single most important variable.",
        "health_rows_data": [
            ("Mitral Valve Disease (MVD)", "Progressive heart valve degeneration, the leading cause of death in purebred Cavaliers. More than 50% of Cavaliers develop MVD by age 5, and over 90% by age 10. Cross-breeding with Poodle reduces but does not eliminate this risk. The Cavalier parent must have a current (within 12 months) heart clearance from a board-certified veterinary cardiologist. Lifetime management of MVD can cost $3,000–$10,000+ in medication and monitoring."),
            ("Syringomyelia (SM)", "Neurological condition caused by Chiari-like skull malformation (the skull is too small for the brain). Causes pain, persistent scratching at the neck and shoulders (without contact), and in severe cases neurological deficits. MRI screening is the only definitive diagnostic. Ask whether the Cavalier parent has been MRI-screened — most breeders do not, but the best ones do."),
            ("Hip Dysplasia", "Less common in small Cavapoos but documented. OFA screening on both parents recommended."),
            ("Patellar Luxation", "Kneecap dislocation, common in small breeds including Cavapoos. Examination by a veterinarian is the standard screening."),
            ("Progressive Retinal Atrophy (PRA)", "From the Poodle side. DNA test available — the Poodle parent should be tested clear or carrier."),
            ("Episodic Falling Syndrome", "Cavalier-specific muscle disorder causing collapse episodes. DNA test available; ask whether the Cavalier parent has been tested."),
        ],
        "health_ask": "Heart clearance on the Cavalier parent from a board-certified veterinary cardiologist within 12 months (this is the single most important test). Plus: OFA hip on both parents, patellar exam, CAER eye exam, PRA DNA test, episodic falling DNA test, and ideally MRI clearance for syringomyelia.",
        "cost_puppy": ("$2,000–$4,500", "Cavapoos from health-tested breeders fall in the standard Doodle range. The premium for breeders who do MRI clearances is significant but worth it."),
        "cost_food_year1": "$300–$500",
        "cost_food_ongoing": "$300–$500",
        "cost_groom_year1": "$500–$1,000",
        "cost_groom_ongoing": "$500–$1,000",
        "cost_insurance_year1": "$400–$900",
        "cost_insurance_ongoing": "$400–$900",
        "cost_setup": "$250–$500",
        "cost_total_first": "$3,800–$8,200",
        "cost_total_ongoing": "$1,500–$3,000",
        "cost_footnote": "MVD treatment, if it develops, adds $1,500–$4,000/year for medication and cardiac monitoring. Insurance enrolled before the first vet visit — and before any MVD diagnosis — covers this. Do not delay enrollment.",
        "good_fit": [
            "Apartment dwellers and small-home families wanting a low-shedding small breed",
            "Households where someone is home most of the day",
            "Families with children (especially Cavapoos placed in homes with older, gentle children)",
            "Senior owners wanting an affectionate, low-exercise companion",
            "Owners willing to pay a premium for a heart-cleared Cavalier parent"
        ],
        "not_fit": [
            "Households where the dog will be alone 8+ hours daily — separation anxiety is severe in this breed",
            "Owners shopping by price — untested Cavalier parents pass MVD on regardless of price",
            "Households not prepared for ongoing cardiology monitoring",
            "Families with very rough young children — Cavapoos are small and can be injured",
            "Owners who want a low-grooming dog — even small Doodles need regular professional grooming"
        ],
        "finding_breeder": "$2,000–$4,500 from reputable breeders. The Cavapoo Club of America and Cavoodle Club of Australia maintain breeder directories. The non-negotiable test is a current heart clearance on the Cavalier parent from a board-certified veterinary cardiologist (the AVCA-trained specialist, not the regular vet). The breeder should also be able to show OFA hip clearances, patellar examination, CAER eye exam, and PRA DNA testing on the Poodle parent. Breeders willing to invest in MRI clearance for syringomyelia are operating at the highest tier.",
        "finding_rescue": "Cavapoo-specific rescue is limited but growing. Doodle Rescue Collective and Cavalier King Charles Spaniel rescue networks occasionally place Cavapoos. Adult dogs that have already been heart-screened are a strong choice.",
        "faqs": [
            ("What is mitral valve disease and why does it matter for Cavapoos?", "Mitral valve disease (MVD) is a progressive degeneration of the heart's mitral valve, leading to heart failure. It is the leading cause of death in purebred Cavalier King Charles Spaniels, with more than 50% affected by age 5 and over 90% by age 10. The Cavapoo cross with Poodle reduces but does not eliminate this risk. The single most important screening for a Cavapoo breeder is a current heart clearance on the Cavalier parent from a board-certified veterinary cardiologist (not a regular vet). Without this, you have no meaningful protection against inheriting the disease."),
            ("Do Cavapoos get separation anxiety?", "Yes — at very high rates. The Cavalier was bred specifically as a companion dog, and Cavapoos inherit this intense need for human company. Cavapoos left alone 8+ hours daily commonly develop barking, destructive chewing, house-soiling, and pacing behaviors. They are best suited to homes where someone is present most of the time, or where daycare or a dog walker provides midday companionship."),
            ("Are Cavapoos hypoallergenic?", "F1B and multigen Cavapoos with curly coats are reliably low-shedding. F1 Cavapoos vary — about half shed noticeably. No dog is truly hypoallergenic. For allergy-sensitive families, request an F1B or multigen with a confirmed curly coat, and spend time with the specific puppy or an adult sibling before committing."),
            ("How big does a Cavapoo get?", "9–25 lbs depending on the Poodle parent size. A Toy Poodle parent produces Cavapoos at the small end (9–15 lbs); a Mini Poodle parent produces Cavapoos at the upper end (18–25 lbs). The breeder should be able to give a reliable estimate based on parent sizes. Within litters, size variation of 3–5 lbs is normal.")
        ],
        "related_breeds": [
            ("Goldendoodle", "goldendoodle", "Larger version of the family-dog concept, more exercise, equally social"),
            ("Bichon Frise", "bichon-frise", "Similar small, low-shedding, affectionate purebred — more predictable genetics"),
            ("Miniature Poodle", "miniature-poodle", "The Poodle parent — reliably non-shedding, longer-lived, more energetic"),
            ("Cavalier King Charles Spaniel", "cavalier-king-charles-spaniel", "The Cavalier parent — same temperament but significantly higher MVD risk")
        ],
    },
    "sheepadoodle": {
        "name": "Sheepadoodle",
        "weight": "30–85 lbs (Mini or Standard)",
        "size_value": "Medium to Large",
        "size_category": "Medium to Large Breed",
        "lifespan": "12–15 yrs",
        "exercise": "60–90 min",
        "tagline": "The Sheepadoodle — Old English Sheepdog crossed with a Standard or Mini Poodle — is a large, distinctive black-and-white Doodle with high energy, strong herding instinct, and a coat that demands serious grooming. Done well, it is one of the most loyal and family-oriented large Doodles.",
        "excerpt": "Sheepadoodles combine the Old English Sheepdog's gentle herding temperament with the Poodle's low-shedding coat. Their distinctive black-and-white panda coloring and large size make them popular family dogs — but the exercise and grooming demands are real.",
        "meta_description": "Sheepadoodle breed guide: F1 vs F1B vs multigen, herding instinct in family settings, panda coat genetics, hip dysplasia risk, exercise needs, intensive grooming costs, and choosing a tested breeder.",
        "tags_extra": ["medium-breed", "large-breed", "family-friendly", "low-shedding", "doodle"],
        "intro": [
            "The Sheepadoodle is a deliberate crossbreed between an Old English Sheepdog (OES) and a Standard or Mini Poodle. Originally bred experimentally in the 1960s by the U.S. Army as a potential military dog, the Sheepadoodle re-emerged as a popular Doodle in the 2000s as families sought larger, gentle Doodles with distinctive coloring.",
            "The defining visual feature of most Sheepadoodles is the panda coat: a black-and-white pattern that mimics the Old English Sheepdog's blue-and-white but with crisper boundaries. Solid black, solid white, and merle Sheepadoodles also occur. Generations follow the standard Doodle convention: F1 (OES × Poodle), F1B (F1 × Poodle, more reliably low-shedding), multigen (most consistent).",
            "Sheepadoodles come in two main sizes. <strong>Mini Sheepadoodles</strong> (Mini Poodle parent) weigh 30–55 lbs. <strong>Standard Sheepadoodles</strong> (Standard Poodle parent) weigh 55–85 lbs. The Standard size carries the full Old English Sheepdog presence — substantial, sturdy, and visually striking."
        ],
        "appearance": [
            "Large and substantial in the Standard size; medium in the Mini. <strong>Standard Sheepadoodles</strong> stand 18–24 inches and weigh 55–85 lbs. <strong>Mini Sheepadoodles</strong> stand 15–20 inches and weigh 30–55 lbs. The build is square, well-boned, and athletic — reflecting both the OES's working build and the Poodle's athleticism.",
            "Coat is typically wavy or curly. The signature panda coloring — black with white markings on the chest, face, paws, and tail tip — is the most common and most sought-after pattern. Solid black, solid white, blue merle, and tri-color also occur. The coat is dense and grows continuously like the Poodle's; professional grooming every 4–6 weeks is required, more frequent than for many other Doodles because of coat density. Mats form aggressively without diligent brushing."
        ],
        "temperament": [
            "Sheepadoodles inherit the Old English Sheepdog's gentle, family-oriented, slightly clownish disposition combined with the Poodle's intelligence. They tend to be calmer than Goldendoodles and Labradoodles but still need real daily activity. The OES heritage as a herding dog occasionally manifests as nudging children or other pets toward where the dog thinks they should be — usually charming, occasionally annoying.",
            "Most Sheepadoodles are sensitive dogs that bond intensely with their family. They respond best to positive reinforcement training and can shut down if treated harshly. The Old English Sheepdog reputation for being good with children carries through — Standard Sheepadoodles are often described as exceptionally patient and gentle with kids.",
            "With children: excellent — patient, playful, often instinctively careful with toddlers. With other animals: generally excellent. With strangers: friendly but sometimes initially reserved. The herding instinct may cause some Sheepadoodles to chase moving children or pets; redirect this with consistent training rather than punishment."
        ],
        "mikes_take": [
            "Sheepadoodles are one of the most family-friendly large Doodles, often calmer than Goldendoodles and Labradoodles while retaining the trainability and low-shedding coat. If a family wants a large, gentle, family-oriented Doodle and can commit to the grooming requirements, the Sheepadoodle is an excellent choice.",
            "The grooming reality is more intensive than for most other Doodles. The Old English Sheepdog coat is famously dense, and that density carries through to the Sheepadoodle. Professional grooming every 4–6 weeks (not every 6–8 weeks) is typical, plus 3–4 brushing sessions per week at home. The coat transition period at 8–14 months is brutal if not actively managed. Many Sheepadoodle owners eventually accept a shorter pet clip rather than the long, fluffy show-style coat — it's much more practical.",
            "The breeder testing requirements are the same as for any large Doodle. OFA hips and elbows on both parents, OFA cardiac, CAER eye exam, PRA DNA test on the Poodle parent, and DM DNA test on the OES parent. Walk away from any breeder who skips these. Old English Sheepdogs have specific health concerns — hip dysplasia, deafness, autoimmune conditions — that the cross dilutes but does not eliminate."
        ],
        "care_exercise": "60–90 minutes daily for Standard Sheepadoodles; 45–60 minutes for Minis. Sheepadoodles need real activity — they are not low-energy dogs despite the calm appearance. Hiking, swimming, and herding-style games suit the breed.",
        "care_mental": "Daily training sessions, puzzle feeders, and herding-style activities (treibball, fetch with directional cues). The herding intelligence wants a job; without one, Sheepadoodles can develop problem behaviors.",
        "care_grooming": "Professional grooming every 4–6 weeks — more frequent than for most other Doodles because the OES coat is unusually dense. Brushing 3–4 times per week at home, daily during coat transition. The line-brushing technique used for Poodles is essential.",
        "health_intro": "Sheepadoodles share inherited health risks with both parent breeds. The Old English Sheepdog has documented risks for hip dysplasia, deafness, and autoimmune conditions. The Poodle contributes its own profile. Health-tested parents are the most reliable mitigation.",
        "health_rows_data": [
            ("Hip and Elbow Dysplasia", "Both parent breeds carry elevated rates. OFA or PennHIP screening on both parents is essential. Ask for specific ratings."),
            ("Deafness", "Old English Sheepdogs have elevated rates of congenital deafness, often associated with white pigmentation around the ears. BAER hearing tests on puppies are recommended for Sheepadoodles with predominantly white heads."),
            ("Autoimmune Hemolytic Anemia (AIHA)", "Documented at elevated rates in Old English Sheepdogs. Difficult to predict via testing; ask the breeder about incidence in their lines."),
            ("Progressive Retinal Atrophy (PRA)", "From the Poodle side. DNA test available — the Poodle parent should be tested clear or carrier."),
            ("Degenerative Myelopathy (DM)", "Progressive spinal cord disease. DNA test available — both parents can be tested."),
            ("Bloat / GDV", "Deep-chested Standard Sheepadoodles are at GDV risk. Prophylactic gastropexy at spay/neuter is strongly recommended."),
        ],
        "health_ask": "OFA hip and elbow, OFA cardiac, CAER eye exam, PRA DNA test, DM DNA test, BAER hearing test for predominantly white puppies. Ask about incidence of AIHA and other autoimmune conditions in the breeder's lines.",
        "cost_puppy": ("$2,000–$4,500", "Reputable Sheepadoodles fall in the standard Doodle range. Panda-colored puppies often command a premium."),
        "cost_food_year1": "$600–$1,000",
        "cost_food_ongoing": "$600–$1,000",
        "cost_groom_year1": "$700–$1,400",
        "cost_groom_ongoing": "$700–$1,400",
        "cost_insurance_year1": "$600–$1,200",
        "cost_insurance_ongoing": "$600–$1,200",
        "cost_setup": "$300–$600",
        "cost_total_first": "$4,700–$9,400",
        "cost_total_ongoing": "$2,250–$4,100",
        "cost_footnote": "Sheepadoodle grooming costs are at the high end of the Doodle range due to coat density. Hip surgery, if needed, runs $4,000–$8,000 per joint. Insurance enrolled before the first vet visit covers both.",
        "good_fit": [
            "Active families wanting a large, gentle, low-shedding family dog",
            "Households that can commit to 60–90 minutes of daily exercise",
            "Owners who can budget for grooming every 4–6 weeks (more frequent than for other Doodles)",
            "Families with children — Sheepadoodles are often excellent with kids",
            "Owners willing to invest in health-tested breeders for hip, eye, and DM clearances"
        ],
        "not_fit": [
            "Households wanting a low-maintenance grooming experience — Sheepadoodle coats are demanding",
            "Apartment dwellers without dedicated outdoor exercise plans",
            "Owners shopping primarily on price — untested breeders pass orthopedic and autoimmune risks through unchecked",
            "Hot or humid climates without air-conditioning — the dense coat traps heat",
            "Households not prepared for the herding instinct manifesting as nudging or chasing"
        ],
        "finding_breeder": "$2,000–$4,500 from reputable breeders. There is no major Sheepadoodle breed club, so vet breeders carefully by their willingness to provide written health clearances. Required: OFA hip and elbow on both parents, OFA cardiac, CAER eye exam, PRA DNA test, DM DNA test, BAER hearing test on predominantly white puppies. Ask the breeder about autoimmune conditions in their lines — Old English Sheepdog AIHA is a real concern and ethical breeders track it.",
        "finding_rescue": "Doodle Rescue Collective and Old English Sheepdog rescue networks occasionally place Sheepadoodles. Adult dogs offer known coat, size, and temperament — significant advantages over puppy unpredictability.",
        "faqs": [
            ("Why are Sheepadoodles grooming costs higher than other Doodles?", "The Old English Sheepdog coat is unusually dense, and that density carries through to the Sheepadoodle. Professional grooming every 4–6 weeks (versus 6–8 weeks for most other Doodles) is typical, and home brushing needs to be 3–4 times per week (versus 2–3 for other Doodles). At $80–$150 per appointment, this is $700–$1,400/year, at the high end of the Doodle range. Many owners eventually switch to a shorter pet clip for practicality."),
            ("What is the panda coat in Sheepadoodles?", "The panda coat is the classic black-and-white Sheepadoodle pattern: predominantly black with white markings on the chest, face, paws, and tail tip — visually similar to a giant panda. It is the most popular and most sought-after Sheepadoodle color. Many breeders charge a premium for panda puppies. The pattern is influenced by Old English Sheepdog genetics; not every litter produces panda puppies."),
            ("Do Sheepadoodles try to herd children?", "Some do, yes. The Old English Sheepdog was historically a drover (livestock-moving dog), and the herding instinct can persist in Sheepadoodles. This often manifests as nudging children with the nose, circling around them, or attempting to keep groups of children together. Most herding-instinct behavior is gentle and can be redirected with consistent training. If your Sheepadoodle is nipping at heels, that should be trained out with positive reinforcement starting in puppyhood."),
            ("Are Sheepadoodles good with hot weather?", "Not particularly. The dense double-influenced coat traps heat, and Sheepadoodles often inherit Old English Sheepdog heat sensitivity. In hot or humid climates, plan for air-conditioned indoor time, exercise restricted to cool morning or evening hours, and constant access to shade and water. A shorter pet clip helps significantly with heat tolerance.")
        ],
        "related_breeds": [
            ("Bernedoodle", "bernedoodle", "Similar large, calm, low-shedding family-dog concept with different coloring"),
            ("Goldendoodle", "goldendoodle", "More energetic and bouncy, less herding instinct, similar size range"),
            ("Standard Poodle", "standard-poodle", "The Poodle parent — reliably non-shedding, less dense coat, similar exercise needs"),
            ("Old English Sheepdog", "old-english-sheepdog", "The OES parent — heavy shedder, dense coat, similar gentle temperament")
        ],
    },
    "aussiedoodle": {
        "name": "Aussiedoodle",
        "weight": "25–70 lbs (Mini or Standard)",
        "size_value": "Medium to Large",
        "size_category": "Medium to Large Breed",
        "lifespan": "10–15 yrs",
        "exercise": "75–120 min",
        "tagline": "The Aussiedoodle — Australian Shepherd crossed with a Standard or Mini Poodle — is the highest-energy Doodle and the most demanding to live with. The Aussie's working drive combines with the Poodle's intelligence to produce a dog that thinks constantly, moves constantly, and needs a serious job. Under-stimulated Aussiedoodles develop problem behaviors quickly.",
        "excerpt": "Aussiedoodles combine the Australian Shepherd's intelligence and athleticism with the Poodle's low-shedding coat. They are the most demanding Doodles to live with — high-energy, sharply intelligent, and prone to behavioral problems when under-exercised or under-stimulated.",
        "meta_description": "Aussiedoodle breed guide: highest-energy Doodle, MDR1 drug sensitivity, merle coat genetics, blue merle and red merle, Australian Shepherd herding drive, exercise demands, and choosing a tested breeder.",
        "tags_extra": ["medium-breed", "high-energy", "intelligent", "low-shedding", "doodle"],
        "intro": [
            "The Aussiedoodle is a deliberate crossbreed between an Australian Shepherd and a Standard or Mini Poodle, popular since the early 2000s among families wanting the Aussie's striking looks and intelligence with the Poodle's low-shedding coat. The cross combines two of the most intelligent breeds in the world, producing a dog that is exceptional in capable hands and overwhelming in unprepared ones.",
            "Aussiedoodles come in two main sizes. <strong>Mini Aussiedoodles</strong> (Mini Poodle parent or Toy Aussie parent) weigh 25–45 lbs. <strong>Standard Aussiedoodles</strong> (Standard Poodle parent) weigh 45–70 lbs. Generations follow the standard Doodle convention; F1B and multigen are more reliably low-shedding than F1.",
            "The Australian Shepherd is fundamentally a working herding dog — bred for stockyards, ranches, and long days of physically and mentally demanding work. That working drive does not vanish in the cross with Poodle (also a working breed). Aussiedoodles need significantly more exercise and mental engagement than other Doodles. A family looking for a calm couch companion should look at almost any other Doodle."
        ],
        "appearance": [
            "Athletic and well-proportioned. <strong>Standard Aussiedoodles</strong> stand 18–23 inches and weigh 45–70 lbs. <strong>Mini Aussiedoodles</strong> stand 14–17 inches and weigh 25–45 lbs. Build is square, athletic, and built for sustained activity.",
            "Coat is wavy or curly. The signature feature of many Aussiedoodles is the merle pattern — a mottled, marbled coat in blue merle (gray-blue with black patches), red merle (copper with brown patches), or rare phantom merle. White markings on the chest, face, paws, and tail tip are common. Solid colors also occur: black, red, chocolate, sable. Eyes are often striking — blue, amber, or heterochromia (one of each color) are common. The merle pattern requires careful breeder selection; merle × merle breeding produces double-merle puppies with severe health problems including blindness and deafness. Responsible breeders never breed merle to merle."
        ],
        "temperament": [
            "Aussiedoodles are intensely intelligent, highly trainable, and demanding. They want to work; they want to learn; they want to be doing something. In the hands of an experienced owner who provides daily mental and physical challenges, Aussiedoodles are extraordinary dogs — capable in agility, obedience, herding, scent work, therapy work, and any structured activity. In the hands of an unprepared owner, they become anxious, destructive, and difficult.",
            "The herding instinct is the strongest of any Doodle. Aussiedoodles will attempt to herd children, other dogs, cats, and sometimes adults — circling, nipping at heels, or staring intensely. This instinct can be channeled but rarely eliminated. Training must address it explicitly from puppyhood.",
            "With children: good with proper training and socialization, but the herding instinct must be managed. With other animals: generally good, though strong prey drive may emerge with cats and small pets. With strangers: variable — some Aussiedoodles are friendly, others are reserved or wary. Proper socialization between 8–16 weeks is essential. The Aussie genetic contribution toward stranger-wariness is real; this is the only Doodle that sometimes functions as a watchdog."
        ],
        "mikes_take": [
            "I love Aussiedoodles when they are the right match for the home, and they break my heart when they aren't. The intelligence and trainability are genuine — these dogs can do almost anything you train them to do. But the energy and engagement requirements are real and non-negotiable. An Aussiedoodle that gets a 20-minute walk and is alone for 8 hours is a dog headed for trouble.",
            "Before getting an Aussiedoodle, honestly assess whether you can provide: 75–120 minutes of real daily exercise (not a casual walk), 30–60 minutes of daily training or structured mental work, and a household where someone is genuinely engaged with the dog through the day. If those aren't realistic, choose almost any other Doodle.",
            "MDR1 gene mutation is the breed-specific health issue that most owners don't know about. About half of Australian Shepherds carry the MDR1 mutation, which causes severe and potentially fatal adverse reactions to several common drugs including ivermectin (in some heartworm preventives), loperamide (Imodium), and several anesthetics. The Poodle does not carry MDR1, so cross-breeding dilutes the risk, but Aussiedoodles can inherit the mutation from the Aussie parent. The DNA test is cheap (~$50) and essential — ask the breeder for the MDR1 result on the Aussie parent, and get your puppy tested if not already.",
            "Merle × merle breeding produces double-merle puppies with severe health problems (often deaf and/or blind). Any breeder who advertises or produces merle × merle litters is not breeding responsibly. Walk away."
        ],
        "care_exercise": "75–120 minutes daily — running, hiking, dog sports, fetch, swimming. Aussiedoodles are athletes; they need real activity, not casual walks. This is the most demanding exercise requirement of any Doodle.",
        "care_mental": "30–60 minutes of daily training, puzzle work, or structured mental engagement. Aussiedoodles excel in agility, obedience, scent work, treibball, and trick training. They are unhappy without mental challenges and develop problem behaviors when under-stimulated.",
        "care_grooming": "Professional grooming every 6–8 weeks. Brushing 2–3 times per week at home, daily during the 8–14 month coat transition. The coat is typically wavy or curly and mats aggressively without regular brushing.",
        "health_intro": "Aussiedoodles share inherited health risks with both parent breeds. The MDR1 drug sensitivity gene is the most actionable concern — it is testable and significantly affects veterinary care decisions. Merle coat genetics require careful breeder management.",
        "health_rows_data": [
            ("MDR1 Drug Sensitivity", "Mutation in the MDR1 gene causes severe reactions to common drugs including ivermectin, loperamide (Imodium), and certain anesthetics. About half of Australian Shepherds carry the mutation. The Poodle does not. Aussiedoodles can inherit the mutation; DNA testing is cheap and essential. Tell every vet your Aussiedoodle has been tested or is unknown — it affects sedation, surgical, and medication choices."),
            ("Hip and Elbow Dysplasia", "Both parent breeds carry elevated rates. OFA or PennHIP screening on both parents is essential."),
            ("Progressive Retinal Atrophy (PRA)", "Inherited retinal degeneration leading to blindness. Present in both Aussies and Poodles. DNA test available."),
            ("Collie Eye Anomaly (CEA)", "Inherited eye condition documented in Australian Shepherds. DNA test available — the Aussie parent should be tested clear or carrier."),
            ("Double Merle Health Problems", "When two merle dogs are bred together, puppies often inherit the double-merle gene combination causing deafness, blindness, and other severe health issues. Responsible breeders never breed merle × merle. Walk away from any breeder who does."),
            ("Epilepsy", "Documented at elevated rates in Australian Shepherds. No DNA test available; ask about incidence in the breeder's lines."),
        ],
        "health_ask": "MDR1 DNA test on the Australian Shepherd parent (and on the puppy if not done — get this done). OFA hip and elbow on both parents, OFA cardiac, CAER eye exam, PRA DNA test, CEA DNA test on the Aussie parent. Confirm the breeder has never bred merle × merle.",
        "cost_puppy": ("$1,800–$4,500", "Reputable Aussiedoodles fall in the standard Doodle range. Blue merle and red merle puppies often command a premium."),
        "cost_food_year1": "$500–$900",
        "cost_food_ongoing": "$500–$900",
        "cost_groom_year1": "$600–$1,200",
        "cost_groom_ongoing": "$600–$1,200",
        "cost_insurance_year1": "$500–$1,200",
        "cost_insurance_ongoing": "$500–$1,200",
        "cost_setup": "$400–$800",
        "cost_total_first": "$4,300–$9,500",
        "cost_total_ongoing": "$1,950–$3,800",
        "cost_footnote": "Setup costs are higher than for other Doodles because of additional training investment (group classes, dog sport equipment). Hip surgery, if needed, runs $4,000–$8,000 per joint.",
        "good_fit": [
            "Experienced dog owners with time and energy for daily training and exercise",
            "Households that genuinely want to participate in dog sports (agility, obedience, herding trials)",
            "Active singles or couples without long workday absences",
            "Owners excited by an intelligent, intensely engaged dog",
            "Households that have specifically considered and accepted the herding instinct"
        ],
        "not_fit": [
            "First-time dog owners — the intelligence-and-energy combination is overwhelming for inexperienced handlers",
            "Households where the dog will be alone 6+ hours daily without structured enrichment",
            "Families with very young children where the herding instinct could lead to nipping",
            "Owners wanting a calm, low-exercise companion",
            "Households not prepared to verify MDR1 testing and avoid merle × merle breeding"
        ],
        "finding_breeder": "$1,800–$4,500 from reputable breeders. There is no major Aussiedoodle breed club, so vet breeders carefully by their willingness to provide written health clearances. Required: MDR1 DNA test on the Aussie parent (non-negotiable), OFA hip and elbow on both parents, OFA cardiac, CAER eye exam, PRA DNA test, CEA DNA test. Confirm explicitly that the breeder does not breed merle × merle litters. Ask about epilepsy and autoimmune conditions in the breeder's lines.",
        "finding_rescue": "Doodle Rescue Collective and Australian Shepherd rescue networks regularly place Aussiedoodles. Many surrendered Aussiedoodles are 1–3-year-old dogs whose owners underestimated the exercise and mental engagement requirements. Adult rescues with known temperament and energy level are an excellent choice for households unsure whether they can handle a young Aussiedoodle.",
        "faqs": [
            ("Are Aussiedoodles too much dog for a first-time owner?", "Often, yes. The combination of intelligence, energy, and herding instinct makes Aussiedoodles demanding even for experienced owners. First-time dog owners who specifically want an Aussiedoodle should commit before getting the dog to: enrolling in puppy class and continuing through advanced obedience, providing 75–120 minutes of daily activity, and learning to manage herding behavior. If any of those commitments feels uncertain, a calmer Doodle (Bernedoodle, Cavapoo, Goldendoodle) is a better starting point."),
            ("What is the MDR1 gene and why is it important?", "MDR1 is a gene mutation that causes severe, potentially fatal reactions to several common veterinary drugs — ivermectin (in some heartworm preventives), loperamide (Imodium), and certain anesthetics. About half of Australian Shepherds carry the mutation. The DNA test costs about $50 and is essential for Aussiedoodles. If your dog tests positive (homozygous or heterozygous), tell every vet you encounter — it affects sedation, surgery, and emergency drug choices. A test result is one of the most actionable pieces of health information you can have for this breed."),
            ("What is the difference between blue merle and red merle Aussiedoodles?", "Both are merle patterns — mottled, marbled coats — differing only in base color. Blue merle is gray-blue with darker (black) patches. Red merle is copper or rust with darker (brown) patches. Both are striking and command premium pricing. Both require the same careful breeder management — never breeding merle × merle to avoid double-merle puppies with severe health problems."),
            ("Do Aussiedoodles shed?", "F1B and multigen Aussiedoodles with curly coats shed minimally. F1 Aussiedoodles vary widely — some have curly Poodle-type coats and shed little; others have straighter Aussie-type coats and shed moderately. The Aussie parent is a heavy seasonal shedder, so the coat-type lottery is more consequential here than for some other Doodles. For low-shedding goals, request an F1B or multigen with confirmed curly coat.")
        ],
        "related_breeds": [
            ("Labradoodle", "labradoodle", "Less intense, slightly easier to live with, similar energy needs"),
            ("Standard Poodle", "standard-poodle", "The Poodle parent — similar intelligence, more reliable coat, fewer health surprises"),
            ("Australian Shepherd", "australian-shepherd", "The Aussie parent — same intelligence and energy with heavy shedding"),
            ("Border Collie", "border-collie", "Comparable working intelligence, even higher energy, heavier shedding")
        ],
    },
}


# ---------------------------------------------------------------------------
# Supporting article content per breed (grooming, costs, checklist).
# ---------------------------------------------------------------------------

SUPPORTING = {
    "goldendoodle": {
        "groom_brushing_per_week": "3–4 times per week",
        "groom_pro_interval": "6–8 weeks",
        "groom_specific": (
            "<p>The Goldendoodle coat varies enormously between individual dogs. Straight (Golden-type) coats shed and brush like a Golden Retriever. Wavy and curly coats grow continuously like a Poodle's and mat aggressively without diligent brushing. Most Goldendoodles fall in the wavy or curly category, especially F1B and multigen dogs. Identify your specific dog's coat type with your groomer at the first appointment, and follow the maintenance plan for that coat type — not a generic one.</p>"
            "<p>The puppy-to-adult coat transition at 8–14 months is the highest matting-risk period of a Goldendoodle's life. The puppy coat sheds out while the adult coat grows in, and the two tangle together aggressively. Daily brushing during the transition prevents mats that otherwise require shaving down. New owners are commonly surprised by this period — build brushing tolerance from the first week so the routine is familiar when the coat demands it.</p>"
        ),
        "groom_clip": "kennel clip (short all over, easy maintenance), teddy bear clip (longer with rounded face), or modified Goldendoodle clip (medium length with softened lines)",
        "costs_puppy": "$2,000–$5,000",
        "costs_pro_interval": "6–8 weeks",
        "costs_specific_health": "Cancer (Golden lineage) and hip dysplasia are the two most expensive potential conditions. Insurance enrolled before the first vet visit covers both — do not delay enrollment.",
        "puppy_specific_setup": "Identifying a Poodle-experienced groomer before the puppy comes home is non-negotiable. The Goldendoodle coat develops into the adult curly form at 8–14 months, and a groomer without Poodle experience will not achieve a correct clip.",
        "puppy_specific_health": "Discuss prophylactic gastropexy at the first vet visit for Standard-size puppies. Ask the breeder for OFA hip clearances on both parents — verify in writing.",
    },
    "labradoodle": {
        "groom_brushing_per_week": "2–3 times per week",
        "groom_pro_interval": "6–8 weeks",
        "groom_specific": (
            "<p>Labradoodle coats are categorized as hair (Labrador-type, shed), fleece (soft and wavy, low-shedding), or wool (curly and dense, minimal-shedding). Most Labradoodles fall in the fleece or wool category. Hair-type coats need only routine brushing; fleece and wool coats need regular professional grooming every 6–8 weeks plus 2–3 brushing sessions at home per week.</p>"
            "<p>The Australian Labradoodle coat is bred for fleece or wool consistency and tends to be more predictable than the F1 American Labradoodle coat. Whichever type, identify your dog's coat at the first grooming appointment and follow the maintenance plan for it. The 8–14 month coat transition period is the highest matting-risk window — daily brushing during this phase prevents mats that otherwise require shaving.</p>"
        ),
        "groom_clip": "kennel clip, teddy bear clip, or Australian Labradoodle clip (medium length showing the natural waves or curls)",
        "costs_puppy": "$2,000–$4,500",
        "costs_pro_interval": "6–8 weeks",
        "costs_specific_health": "Hip dysplasia and orthopedic conditions are the most expensive likely health concerns. Pet insurance enrolled before the first vet visit is the most cost-effective protection.",
        "puppy_specific_setup": "Decide F1 vs Australian Labradoodle before searching for breeders. Identify a Poodle-experienced groomer before the puppy comes home — the wavy and curly coats require Poodle-style grooming technique.",
        "puppy_specific_health": "Discuss prophylactic gastropexy at the first vet visit for Standard-size puppies. Ask about MDR1 status if the puppy will potentially be prescribed ivermectin-based heartworm prevention (rare but worth confirming).",
    },
    "bernedoodle": {
        "groom_brushing_per_week": "3–4 times per week",
        "groom_pro_interval": "6–8 weeks",
        "groom_specific": (
            "<p>Bernedoodle coats are usually wavy or curly. The wavy coat is the most common in F1 Bernedoodles; F1B and multigen Bernedoodles lean curlier. Both coat types require professional grooming every 6–8 weeks plus 3–4 brushing sessions per week at home. The coat is denser than a Goldendoodle's, which means more time per brushing session.</p>"
            "<p>The tri-color coat (black, white, and rust) requires the same maintenance as solid-color Bernedoodles — the color does not affect coat care, only appearance. The puppy-to-adult coat transition at 8–14 months is the highest matting-risk period; brush daily during the transition. The Bernese parent's heritage as a cool-weather dog means many Bernedoodles benefit from a shorter pet clip in summer for heat tolerance.</p>"
        ),
        "groom_clip": "kennel clip, teddy bear clip, or modified Bernedoodle clip (medium length that shows the tri-color pattern)",
        "costs_puppy": "$2,500–$5,500",
        "costs_pro_interval": "6–8 weeks",
        "costs_specific_health": "Cancer (Bernese lineage, especially histiocytic sarcoma) is the most expensive potential condition. Insurance enrolled before the first vet visit is the single highest-value financial decision for this breed.",
        "puppy_specific_setup": "Ask the breeder for documented longevity records of dogs from previous litters — this is the most informative signal of whether the lifespan-extension benefit will materialize. Identify a Poodle-experienced groomer before the puppy comes home.",
        "puppy_specific_health": "Discuss prophylactic gastropexy at the first vet visit for Standard-size puppies. Ask the breeder for DM (degenerative myelopathy) DNA test results on the Bernese parent.",
    },
    "cavapoo": {
        "groom_brushing_per_week": "2–3 times per week",
        "groom_pro_interval": "6–8 weeks",
        "groom_specific": (
            "<p>Cavapoo coats are wavy or curly. F1B and multigen Cavapoos lean curlier and shed minimally. F1 Cavapoos vary more. All coat types require professional grooming every 6–8 weeks plus 2–3 brushing sessions at home per week. Pay special attention to behind the ears, around the eyes, and under the legs — mats form fastest in these friction areas for small Doodles.</p>"
            "<p>Eye and tear-stain care is a daily Cavapoo task. The Cavalier-influenced face shape produces some tear staining; gentle daily wiping with a damp cloth or tear-stain wipe prevents discoloration and skin irritation. Ear canal hair grows like a Poodle's and needs removal at every professional appointment.</p>"
        ),
        "groom_clip": "puppy clip (short all over), teddy bear clip (rounded face), or Cavapoo clip (slightly longer, soft appearance)",
        "costs_puppy": "$2,000–$4,500",
        "costs_pro_interval": "6–8 weeks",
        "costs_specific_health": "Mitral valve disease (MVD) from the Cavalier side is the most consequential potential health cost — lifetime management can run $3,000–$10,000+. Insurance enrolled before the first vet visit and before any MVD diagnosis is essential.",
        "puppy_specific_setup": "Verify the Cavalier parent has a current heart clearance from a board-certified veterinary cardiologist before purchase. Identify a small-dog-experienced groomer before the puppy comes home.",
        "puppy_specific_health": "Cardiac auscultation at every annual vet visit from year one onward. Ask the breeder about syringomyelia MRI clearances if available. Pet insurance enrollment before the first vet visit is non-negotiable for this breed.",
    },
    "sheepadoodle": {
        "groom_brushing_per_week": "3–4 times per week",
        "groom_pro_interval": "4–6 weeks",
        "groom_specific": (
            "<p>The Sheepadoodle coat is unusually dense — denser than most other Doodles — because of the Old English Sheepdog heritage. This means more frequent professional grooming (every 4–6 weeks, not every 6–8 weeks) and more time per home brushing session. Wavy and curly coats both mat aggressively without diligent maintenance.</p>"
            "<p>Line brushing — parting the coat section by section and brushing from skin outward — is essential for the dense Sheepadoodle coat. Surface brushing misses mats forming close to the skin. Many Sheepadoodle owners eventually settle on a shorter pet clip rather than the long, fluffy show-style coat, both for practicality and for heat tolerance in warmer months.</p>"
        ),
        "groom_clip": "kennel clip (short all over, the most practical), teddy bear clip, or modified Sheepadoodle clip (medium length that shows the panda pattern)",
        "costs_puppy": "$2,000–$4,500",
        "costs_pro_interval": "4–6 weeks",
        "costs_specific_health": "Hip dysplasia and autoimmune hemolytic anemia (AIHA) from the OES side are the most consequential potential conditions. Insurance enrolled before the first vet visit covers both.",
        "puppy_specific_setup": "Identify a groomer experienced with dense Doodle coats before the puppy comes home — many groomers underestimate Sheepadoodle coat density. Confirm BAER hearing test result for predominantly white puppies.",
        "puppy_specific_health": "Discuss prophylactic gastropexy at the first vet visit for Standard-size puppies. Ask the breeder about AIHA incidence in their lines.",
    },
    "aussiedoodle": {
        "groom_brushing_per_week": "2–3 times per week",
        "groom_pro_interval": "6–8 weeks",
        "groom_specific": (
            "<p>Aussiedoodle coats are wavy or curly. F1B and multigen Aussiedoodles lean curlier and shed minimally. F1 Aussiedoodles vary widely — some have curly Poodle-type coats; others have straighter Aussie-type coats that shed more heavily and seasonally. Identify your dog's coat type at the first grooming appointment and follow the maintenance plan for it.</p>"
            "<p>The merle coat pattern (blue merle or red merle) does not require any special coat care — the pattern is purely visual. The puppy-to-adult coat transition at 8–14 months is the highest matting-risk period; daily brushing during the transition prevents mats that otherwise require shaving down.</p>"
        ),
        "groom_clip": "kennel clip, teddy bear clip, or Aussiedoodle clip (medium length showing the merle pattern when present)",
        "costs_puppy": "$1,800–$4,500",
        "costs_pro_interval": "6–8 weeks",
        "costs_specific_health": "Orthopedic conditions (hips, elbows) are the most expensive likely health concerns. MDR1-related adverse drug reactions, while rare with awareness, can be costly to manage if not anticipated.",
        "puppy_specific_setup": "Enroll in puppy class before the puppy comes home — the Aussiedoodle benefits more from early structured training than almost any other Doodle. Identify a Poodle-experienced groomer before pickup.",
        "puppy_specific_health": "MDR1 DNA test is essential — request the test result on the Aussie parent and have the puppy tested if not already done. Tell every vet your Aussiedoodle's MDR1 status; it affects sedation, surgery, and medication choices.",
    },
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build_main_breed_json(slug, data):
    name = data["name"]
    intro_html = "".join(f'<p {P}>{p}</p>' for p in data["intro"][:-1])
    intro_html += f'<p {P_LAST}>{data["intro"][-1]}</p>'
    appearance_html = f'<p {P}>{data["appearance"][0]}</p>' + f'<p {P_LAST}>{data["appearance"][1]}</p>'
    temperament_html = "".join(f'<p {P}>{p}</p>' for p in data["temperament"][:-1]) + f'<p {P_LAST}>{data["temperament"][-1]}</p>'
    mikes_html = "".join(f'<p {P}>{p}</p>' for p in data["mikes_take"][:-1]) + f'<p {P_LAST}>{data["mikes_take"][-1]}</p>'

    care_html = (
        f'<h3 {H3}>Exercise</h3><p {P}>{data["care_exercise"]}</p>'
        f'<h3 {H3}>Mental Stimulation</h3><p {P}>{data["care_mental"]}</p>'
        f'<h3 {H3}>Grooming</h3><p {P_LAST}>{data["care_grooming"]} See the <a href="/blogs/dog-breeds/{slug}-grooming-guide" {A}>{name} grooming guide</a>.</p>'
    )

    health_rows = [health_row(n, b, i % 2 == 1) for i, (n, b) in enumerate(data["health_rows_data"])]
    health_html = build_health_table(data["health_intro"], health_rows) + f'<p style="font-size:0.82em;color:#6b7177;margin:14px 0 0 0;"><strong style="color:#1a1a1a;">Ask breeders for (both parents):</strong> {data["health_ask"]}</p>'

    cost_rows = [
        cost_row("Puppy (reputable breeder)", data["cost_puppy"][0], "—", False),
        cost_row("Food", data["cost_food_year1"], data["cost_food_ongoing"], True),
        cost_row("Vet (routine + puppy series)", "$500–$900", "$350–$600", False),
        cost_row(f'Professional grooming (every {SUPPORTING[slug]["groom_pro_interval"]})', data["cost_groom_year1"], data["cost_groom_ongoing"], True),
        cost_row("Pet insurance", data["cost_insurance_year1"], data["cost_insurance_ongoing"], False),
        cost_row("Setup (crate, supplies, training)", data["cost_setup"], "—", True),
    ]
    cost_html = build_cost_table(cost_rows, data["cost_total_first"], data["cost_total_ongoing"], data["cost_footnote"] + f' See the <a href="/blogs/dog-breeds/{slug}-first-year-costs" {A}>full {name} first-year cost breakdown</a>.')

    finding_html = (
        f'<h3 {H3}>Buying from a Breeder</h3><p {P}>{data["finding_breeder"]}</p>'
        f'<h3 {H3}>Rescue</h3><p {P}>{data["finding_rescue"]}</p>'
        f'<p style="font-size:0.95em;line-height:1.7;color:#6b7177;margin:16px 0 0 0;">Before your {name} puppy comes home, complete the <a href="/blogs/dog-breeds/{slug}-puppy-checklist" {A}>{name} puppy checklist</a> — insurance enrollment, identifying an experienced groomer, and training class registration are the three critical pre-arrival steps.</p>'
    )

    return {
        "meta": {
            "name": name,
            "slug": slug,
            "shopify_handle": slug,
            "group": "Designer Crossbreed",
            "size_category": data["size_category"],
            "tagline": data["tagline"],
            "tags": ["designer-crossbreed"] + data["tags_extra"] + ["dog-breeds"],
            "published": False,
            "published_at": None,
            "excerpt": data["excerpt"],
            "meta_description": data["meta_description"],
        },
        "stats": {
            "size": {"emoji": "📏", "label": "Size", "value": data["size_value"]},
            "weight": {"emoji": "⚖️", "label": "Weight", "value": data["weight"]},
            "lifespan": {"emoji": "📅", "label": "Lifespan", "value": data["lifespan"]},
            "exercise": {"emoji": "🏃", "label": "Exercise", "value": data["exercise"]},
            "grooming": {"emoji": "✂️", "label": "Grooming", "value": "High (professional required)"},
            "training": {"emoji": "🎓", "label": "Training", "value": "Easy"},
            "with_kids": {"emoji": "👨‍👩‍👧", "label": "With Kids", "value": "Excellent"},
            "beginners": {"emoji": "🌱", "label": "Beginners", "value": "Yes" if slug != "aussiedoodle" else "Not recommended"},
        },
        "images": {
            "hero": {"url": PLACEHOLDER_IMG, "alt": name},
            "secondary": [
                {"placement": "before_temperament", "url": PLACEHOLDER_IMG, "alt": f"{name} at home with family", "caption": f"Life with a {name} — what daily ownership actually looks and costs.", "cta": "See first-year costs →", "link": f"/blogs/dog-breeds/{slug}-first-year-costs"},
                {"placement": "before_care", "url": PLACEHOLDER_IMG, "alt": f"{name} coat care", "caption": "Coat care is a real ongoing commitment.", "cta": "See full grooming guide →", "link": f"/blogs/dog-breeds/{slug}-grooming-guide"},
                {"placement": "before_finding", "url": PLACEHOLDER_IMG, "alt": f"{name} puppy", "caption": f"Bringing home a {name} puppy.", "cta": "See the puppy checklist →", "link": f"/blogs/dog-breeds/{slug}-puppy-checklist"},
            ],
        },
        "sections": {
            "intro": {"label": "Overview", "heading": f"What Is a {name}?", "html": intro_html},
            "appearance": {"label": "Physical", "heading": f"What {name}s Look Like", "html": appearance_html},
            "temperament": {"label": "Personality", "heading": "Temperament", "html": temperament_html},
            "mikes_take": {"label": "A Realistic Take", "heading": f"What I'd Tell a Friend Thinking About a {name}", "html": mikes_html},
            "care": {"label": "Daily Life", "heading": "Care Requirements", "html": care_html},
            "health": {"label": "Wellness", "heading": "Health &amp; Common Conditions", "html": health_html},
            "cost": {"label": "Budget", "heading": "Cost of Ownership", "html": cost_html},
            "right_for_you": {"label": "Fit Assessment", "heading": f"Is a {name} Right for You?", "good_fit": data["good_fit"], "not_fit": data["not_fit"]},
            "finding": {"label": "Next Steps", "heading": f"Finding Your {name}", "html": finding_html},
        },
        "faq": [{"q": q, "a": a} for q, a in data["faqs"]],
        "related_breeds": [{"name": n, "slug": s, "note": note} for n, s, note in data["related_breeds"]],
    }


def build_grooming_guide(slug, breed_name, data):
    s = SUPPORTING[slug]
    return {
        "meta": {
            "group": breed_name,
            "shopify_handle": f"{slug}-grooming-guide",
            "size_category": "Guide",
            "published": False,
            "published_at": None,
            "name": f"{breed_name} Grooming Guide: Coat Care, Brushing Schedules, and Professional Trim Frequency",
            "slug": f"{slug}-grooming-guide",
            "excerpt": f"How to groom a {breed_name}'s wavy or curly coat — why professional grooming every {s['groom_pro_interval']} matters, how to brush properly at home, and what happens if you skip it.",
            "meta_description": f"How to groom a {breed_name}: professional grooming every {s['groom_pro_interval']}, line-brushing technique, the 8–14 month coat transition, practical pet clips, and what happens without regular grooming.",
            "tags": [breed_name, "Guide", "Dog Guides"],
        },
        "images": {"hero": {"url": PLACEHOLDER_IMG, "alt": breed_name}},
        "sections": {
            "intro": {
                "label": "The Coat",
                "heading": f"The {breed_name} Coat: Low-Shedding, High-Maintenance",
                "html": (
                    f"<p>The {breed_name} coat is the result of crossing a Poodle's continuously growing, low-shedding curls with the other parent breed's coat. The result is a wavy or curly coat that sheds far less than most breeds — but grows continuously and mats aggressively without diligent grooming. Professional grooming every {s['groom_pro_interval']} is not optional for this breed; it is basic coat maintenance.</p>"
                    f"<p>A {breed_name} that goes 10–12 weeks without professional grooming can develop dense pelted mats so close to the skin that a full shave-down is the only humane way to clear them. Mats pull the skin, hide skin infections, and can become painful. The grooming schedule is a permanent ongoing commitment.</p>"
                    f"<h3>Basic Grooming Schedule</h3><ul><li><strong>Brushing:</strong> {s['groom_brushing_per_week']}; daily during the 8–14 month coat transition</li><li><strong>Professional grooming:</strong> Every {s['groom_pro_interval']} — strictly</li><li><strong>Bathing:</strong> Every 3–4 weeks</li><li><strong>Ear cleaning:</strong> Weekly — hair grows in the ear canal</li><li><strong>Nail trimming:</strong> Every 3–4 weeks</li><li><strong>Teeth brushing:</strong> Daily</li></ul>"
                ),
            },
            "care": {
                "label": "Brushing and At-Home Care",
                "heading": f"How to Brush a {breed_name} Properly",
                "html": (
                    "<h3>Line Brushing: The Required Technique</h3>"
                    f"<p>Surface brushing a {breed_name}'s coat is not sufficient. Mats form close to the skin, and brushing only the outer layer misses them until they are tight and difficult to remove. Use line brushing: part the coat horizontally, hold the section above out of the way, and use a slicker brush to work from the skin outward in short strokes. Move the part upward section by section. Finish with a metal comb — if it passes through without snagging, the section is done. If it snags, keep brushing.</p>"
                    "<h3>Priority Areas</h3><p>Mats form fastest in friction areas: behind the ears, under the armpits, around the collar, and at the junction of the legs and body. Pay extra attention to these areas at every brushing.</p>"
                    + s["groom_specific"]
                    + "<h3>Ear Canal Hair</h3><p>Hair grows in the ear canal and traps moisture and debris. Have your groomer remove this hair at every professional appointment. Clean ears weekly. Ear infections are common when ear-canal hair is not managed.</p>"
                ),
            },
            "special": {
                "label": "Professional Grooming",
                "heading": "Clip Styles and What Happens If You Skip",
                "html": (
                    "<h3>Practical Clip Options</h3>"
                    f"<p>Most {breed_name} owners choose one of: {s['groom_clip']}. Discuss with your groomer what clip length matches your willingness to brush at home — a shorter clip needs less maintenance.</p>"
                    "<h3>What Happens Without Regular Grooming</h3>"
                    f"<p>A {breed_name} coat neglected for 3+ months develops pelted mats — mats so tight and dense against the skin they form a felt-like layer. Pelting is painful, can hide skin infections, and cannot be brushed out — the only humane option is shaving down to the skin. The coat takes 6–12 months to regrow. Regular professional grooming every {s['groom_pro_interval']} prevents this entirely.</p>"
                    f"<h3>Annual Grooming Cost</h3><p>Professional grooming at $80–$150 per appointment every {s['groom_pro_interval']} runs $500–$1,400 per year. This is a fixed, ongoing cost of {breed_name} ownership.</p>"
                ),
            },
        },
        "faq": [
            {"q": f"How often does a {breed_name} need professional grooming?", "a": f"Every {s['groom_pro_interval']}, without exception. The wavy or curly coat grows continuously and develops dense painful mats within 10–12 weeks without professional trimming. Budget $500–$1,400 per year for professional grooming as a permanent ongoing cost. Shorter clips require less at-home brushing between appointments; longer clips require more."},
            {"q": f"What is the puppy-to-adult coat transition in {breed_name}s?", "a": "Around 8–14 months, the soft puppy coat transitions to the adult wavy or curly coat. During this 4–8 week phase, mats form more aggressively than at any other time — the two coat types interact and tangle together. Daily brushing is typically required during the transition. Keeping the coat shorter during this period significantly reduces the challenge."},
            {"q": f"What are the practical clip options for a pet {breed_name}?", "a": f"Most pet owners choose a kennel clip (short all over, easy maintenance) or a teddy bear clip (longer with a rounded face). Discuss with your groomer what clip length matches your willingness to brush at home between appointments. A shorter clip needs less maintenance than a longer one."},
        ],
    }


def build_first_year_costs(slug, breed_name, data):
    s = SUPPORTING[slug]
    return {
        "meta": {
            "name": f"{breed_name} First Year Costs",
            "slug": f"{slug}-first-year-costs",
            "shopify_handle": f"{slug}-first-year-costs",
            "group": breed_name,
            "size_category": "Guide",
            "tags": [slug, "costs", "first-year"],
            "published": False,
            "published_at": None,
            "excerpt": f"{breed_name} first-year costs run {data['cost_total_first']} including purchase price. Professional grooming every {s['groom_pro_interval']} is the breed's primary recurring cost beyond food and insurance.",
            "meta_description": f"{breed_name} first year costs: puppy price {s['costs_puppy']}, mandatory professional grooming every {s['groom_pro_interval']}, vet bills including OFA screening, insurance considerations, and total first-year expense estimates.",
        },
        "images": {"hero": {"url": PLACEHOLDER_IMG, "alt": f"{breed_name} first year costs"}},
        "sections": {
            "intro": {
                "label": "Upfront Costs",
                "heading": f"What Does a {breed_name} Cost to Acquire?",
                "html": (
                    f"<p><strong>Puppy from a reputable breeder: {s['costs_puppy']}.</strong> Reputable {breed_name} breeders invest in OFA health testing, genetic panels, prenatal care, and puppy socialization. The price reflects this investment. Lower-priced {breed_name}s often come from breeders who skip these costs — which is exactly why they often produce dogs with serious health and temperament problems.</p>"
                    "<p><strong>Rescue adoption: $200–$600</strong> through Doodle Rescue Collective, IDOG Rescue, or breed-specific rescue networks. Many surrendered Doodles are 1–3-year-old dogs whose owners underestimated grooming, exercise, or training requirements. Adult rescues offer known coat type, known temperament, and known size.</p>"
                    "<p><strong>Initial setup costs: $300–$700</strong></p><ul><li>Crate (sized for adult dog): $80–$200</li><li>Bed: $60–$140</li><li>Collar, harness, leash: $60–$120</li><li>Grooming tools (slicker brush, pin brush, metal comb): $50–$110</li><li>Bowls: $30–$70</li></ul>"
                ),
            },
            "care": {
                "label": "First Year Recurring",
                "heading": "First Year Ongoing Expenses",
                "html": (
                    f"<p><strong>Food: {data['cost_food_year1']} for the first year.</strong> High-quality dry food appropriate for size. Budget monthly.</p>"
                    f"<p><strong>Veterinary care (first year): $500–$900</strong></p><ul><li>Initial wellness exam and puppy vaccination series: $150–$350</li><li>Spay or neuter: $200–$500 — discuss prophylactic gastropexy at this appointment for Standard-size dogs</li><li>Heartworm and parasite prevention: $120–$240/year</li><li>Routine bloodwork and screening: $80–$200</li></ul>"
                    f"<p><strong>Pet insurance: {data['cost_insurance_year1']}/year.</strong> Strongly recommended. {s['costs_specific_health']}</p>"
                    f"<p><strong>Professional grooming: {data['cost_groom_year1']}/year.</strong> At $80–$150 per session every {s['costs_pro_interval']}, professional grooming is a fixed, permanent expense. The coat grows continuously and must be clipped — it is not optional maintenance. Owners who learn to clip at home reduce this cost but require quality clippers and practice.</p>"
                ),
            },
            "special": {
                "label": "Total & Ongoing",
                "heading": "First Year Total and Long-Term Costs",
                "html": (
                    f"<p><strong>First year total estimate: {data['cost_total_first']}</strong> (including purchase price). Professional grooming and insurance are the primary ongoing cost drivers.</p>"
                    f"<p><strong>Annual ongoing costs after year one: {data['cost_total_ongoing']}</strong></p><ul><li>Food: {data['cost_food_ongoing']}</li><li>Routine vet care and preventives: $350–$600</li><li>Pet insurance: {data['cost_insurance_ongoing']}</li><li>Professional grooming: {data['cost_groom_ongoing']}</li></ul>"
                    f"<p>Over a {data['lifespan']} lifespan, total ownership cost excluding purchase price is typically $20,000–$50,000 — driven significantly by mandatory professional grooming over a long life. The grooming cost accumulated over the dog's lifetime makes home grooming skill acquisition the most impactful long-term cost reduction available to {breed_name} owners.</p>"
                ),
            },
        },
        "faq": [
            {"q": f"Why are {breed_name}s so expensive?", "a": "Two reasons. First, demand has dramatically exceeded supply for over a decade. Second, ethical breeding requires significant investment — OFA testing on both parents, genetic panels, stud fees, prenatal care, and puppy socialization can cost $3,000–$5,000 per litter before any profit. Lower-priced Doodles often come from breeders who skip these costs, which is why they're cheaper — and exactly why they often produce dogs with health and temperament problems. A higher initial price from a tested breeder is dramatically cheaper than discovering hip dysplasia at age 3."},
            {"q": f"Can I reduce {breed_name} grooming costs by clipping at home?", "a": "Yes — significantly. Quality clippers ($150–$350), the correct blade sizes, and scissors are the tool investment. Learning a basic pet clip is achievable with practice and YouTube tutorials. Many owners learn to clip their own dog and reduce professional grooming to periodic trim-outs. The cumulative savings over the dog's lifetime can be $5,000–$15,000."},
            {"q": "Is pet insurance worth it?", "a": "For Doodles, yes. Most large Doodle breeds have meaningful orthopedic risks (hip dysplasia, $4,000–$8,000 per joint to repair) and several have breed-specific health risks that insurance can offset. Enroll before the first vet visit — insurance enrolled after a diagnosis typically excludes that condition as a pre-existing exclusion. Monthly premiums of $40–$100 are typical for Doodles."},
        ],
    }


def build_puppy_checklist(slug, breed_name, data):
    s = SUPPORTING[slug]
    return {
        "meta": {
            "name": f"{breed_name} Puppy Checklist",
            "slug": f"{slug}-puppy-checklist",
            "shopify_handle": f"{slug}-puppy-checklist",
            "group": breed_name,
            "size_category": "Guide",
            "tags": [slug, "puppy", "checklist"],
            "published": False,
            "published_at": None,
            "excerpt": f"Everything you need before your {breed_name} puppy comes home — find a Poodle-experienced groomer before pickup, discuss breed-specific health screening, enroll in training class early, and start brushing immediately.",
            "meta_description": f"{breed_name} puppy checklist: find an experienced groomer before pickup, breed-specific health discussion, training class registration, insurance enrollment, and first-week vet priorities.",
        },
        "images": {"hero": {"url": PLACEHOLDER_IMG, "alt": f"{breed_name} puppy checklist"}},
        "sections": {
            "intro": {
                "label": "Before Puppy Comes Home",
                "heading": f"Preparing for Your {breed_name} Puppy",
                "html": (
                    "<ul>"
                    f"<li><strong>Find an experienced groomer before pickup:</strong> {s['puppy_specific_setup']} The {breed_name} requires professional clipping every {s['groom_pro_interval']}, and a groomer without Poodle-style experience will not achieve a correct clip. Book the first appointment before the puppy arrives.</li>"
                    "<li><strong>Crate (sized for adult dog):</strong> Select for adult size. The crate is both a training tool and a resting space from day one.</li>"
                    "<li><strong>Orthopedic bed:</strong> Supportive bedding in the crate and in the primary rest area.</li>"
                    "<li><strong>Collar, harness, leash:</strong> Flat collar for ID, front-clip harness for walks during training.</li>"
                    "<li><strong>Grooming tools:</strong> Slicker brush, pin brush, wide-tooth metal comb for home maintenance between professional appointments. Start brushing immediately — the coat transitions to the adult coat at 8–14 months, and the transition period is the highest mat-risk phase. Build brushing tolerance while the coat is still easy.</li>"
                    "<li><strong>Pet insurance enrollment:</strong> Before the first vet visit. Most breed-specific health risks are covered if enrolled before any diagnosis. Do not delay.</li>"
                    "<li><strong>Training class registration:</strong> Enroll in puppy class starting at 8–10 weeks. Register before the puppy comes home so you have a confirmed spot.</li>"
                    "</ul>"
                ),
            },
            "care": {
                "label": "First Week Setup",
                "heading": "First Week: Vet Visit Priorities",
                "html": (
                    "<ul>"
                    f"<li><strong>Breed-specific health discussion:</strong> {s['puppy_specific_health']}</li>"
                    "<li><strong>Complete puppy vaccination series:</strong> Core vaccines at 8, 12, and 16 weeks. Confirm schedule.</li>"
                    "<li><strong>Microchipping:</strong> Essential — microchip at or before the first appointment.</li>"
                    "<li><strong>Exercise restriction guidance:</strong> Large-breed growth plates close at 12–18 months. Sustained running and jumping before that point risks orthopedic damage. Ask for puppy-specific exercise guidelines.</li>"
                    "<li><strong>Heartworm and flea prevention plan:</strong> Discuss prevention regimen appropriate for your region.</li>"
                    "<li><strong>Spay/neuter timing:</strong> Discuss with your vet. For Standard-size dogs, waiting until 12–18 months for growth plate closure is increasingly the recommendation, but discuss based on your specific dog.</li>"
                    "</ul>"
                ),
            },
            "special": {
                "label": "Training",
                "heading": "Starting Training Right",
                "html": (
                    f"<p>The {breed_name} is highly trainable — both parent breeds rank among the most intelligent dogs. Training is a genuinely pleasurable experience with this breed: the dog learns quickly, retains commands reliably, and responds enthusiastically to positive reinforcement.</p>"
                    "<p><strong>Begin training from day one.</strong> A Doodle puppy is capable of learning basic commands at 8 weeks. Keep sessions short (5–10 minutes), varied, and positive. End every session on a success.</p>"
                    "<p><strong>Enroll in puppy class immediately.</strong> Social confidence, basic obedience, and recall should be introduced in a structured class setting beginning at 8–10 weeks.</p>"
                    "<p><strong>Coat handling from the first day.</strong> Build tolerance for brushing, ear handling, paw touch, and face care from the first week, always with treats. The grooming routine that begins now continues for the dog's life.</p>"
                    "<p><strong>Recall training is a priority.</strong> Train recall with high-value rewards and consistent reinforcement. Use a long line in open areas until recall is proofed in many settings.</p>"
                    "<p><strong>Separation conditioning.</strong> Many Doodles are prone to separation anxiety. Build alone-time tolerance gradually starting from the first week — short absences that the puppy successfully tolerates, building up over weeks. Never come home to a distressed puppy; use a webcam to monitor.</p>"
                ),
            },
        },
        "faq": [
            {"q": "Why is insurance enrollment so urgent before the first vet visit?", "a": "Pet insurance enrolled before any diagnosis covers the breed's typical health risks. Insurance enrolled after a diagnosis typically excludes that condition as a pre-existing exclusion. For Doodles with documented orthopedic and breed-specific genetic risks, the window for full coverage is before the first vet visit reveals a problem. Do not delay enrollment."},
            {"q": "When does the puppy coat change to the adult coat?", "a": "Typically between 8 and 14 months of age. The transition period is the highest-risk phase for matting — the incoming adult coat and the remaining puppy coat tangle together. Brushing every 1–2 days during the transition prevents the serious mats that form when the coat change is neglected. Building a consistent brushing routine from puppyhood makes this manageable; neglecting brushing during this period commonly results in a matted coat requiring shaving."},
            {"q": "What grooming clip should I ask for as a pet owner?", "a": "A practical pet clip — kennel clip, teddy bear clip, or similar — keeps the coat at a uniform manageable length over most of the body. Discuss with your groomer what maintenance interval and clip length you prefer before the first appointment. Most pet owners settle on a shorter clip for practicality."},
        ],
    }


# ---------------------------------------------------------------------------
# Roundup builder
# ---------------------------------------------------------------------------

def build_roundup():
    breeds_for_roundup = [
        ("Goldendoodle", "goldendoodle", "Medium to Large", "60–90 min", "10–15 yrs lifespan",
         "Golden Retriever crossed with Standard or Mini Poodle, the Goldendoodle is the most popular family Doodle. Friendly, trainable, and often low-shedding, they are excellent with children. Choose a tested breeder — health outcomes vary enormously."),
        ("Labradoodle", "labradoodle", "Medium to Large", "60–90 min", "12–14 yrs lifespan",
         "The original Doodle, Labrador Retriever crossed with a Poodle. Energetic and water-loving. The Australian Labradoodle (multigen) is dramatically more consistent than the F1 American Labradoodle for coat and temperament."),
        ("Bernedoodle", "bernedoodle", "Medium to Large", "45–75 min", "12–18 yrs lifespan",
         "Bernese Mountain Dog crossed with a Poodle. Calmer than most Doodles, often beautifully tri-colored, and frequently lives 4–6 years longer than a purebred Bernese — but only with health-tested parents."),
        ("Cavapoo", "cavapoo", "Small", "30–45 min", "12–15 yrs lifespan",
         "Cavalier King Charles Spaniel crossed with a Mini or Toy Poodle. Small, affectionate, apartment-friendly. The Cavalier mitral valve disease risk is the most consequential health concern — verify cardiologist heart clearance on the Cavalier parent."),
        ("Sheepadoodle", "sheepadoodle", "Medium to Large", "60–90 min", "12–15 yrs lifespan",
         "Old English Sheepdog crossed with a Standard or Mini Poodle. Distinctive panda coloring, gentle temperament, and substantial size. Grooming is more demanding than for most other Doodles because of OES coat density."),
        ("Aussiedoodle", "aussiedoodle", "Medium to Large", "75–120 min", "10–15 yrs lifespan",
         "Australian Shepherd crossed with a Standard or Mini Poodle. The highest-energy Doodle, sharply intelligent, often merle-coated. Not recommended for first-time dog owners. MDR1 drug-sensitivity gene testing is essential."),
    ]

    cards = []
    for name, slug, size, exercise, lifespan, desc in breeds_for_roundup:
        cards.append(
            f'<div style="background:#ffffff;border:1px solid rgba(0,0,0,0.08);border-radius:12px;overflow:hidden;">'
            f'<a href="/blogs/dog-breeds/{slug}" class="wf-card-img" style="display:block;"><img src="{PLACEHOLDER_IMG}" alt="{name}" style="width:100%;aspect-ratio:3/2;height:auto;object-fit:cover;display:block;"></a>'
            f'<div style="padding:16px;">'
            f'<h3 style="font-size:1em;font-weight:700;color:#1a1a1a;margin:0 0 8px 0;">{name}</h3>'
            f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">'
            f'<span style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.65em;background:#f0f0f0;border-radius:20px;padding:3px 10px;color:#555;">{size}</span>'
            f'<span style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.65em;background:#f0f0f0;border-radius:20px;padding:3px 10px;color:#555;">{exercise}</span>'
            f'<span style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.65em;background:#f0f0f0;border-radius:20px;padding:3px 10px;color:#555;">{lifespan}</span>'
            f'</div>'
            f'<p style="font-size:0.85em;line-height:1.6;color:#6b7177;margin:0 0 12px 0;">{desc}</p>'
            f'<a href="/blogs/dog-breeds/{slug}" style="font-size:0.8em;font-weight:600;color:#000000;text-decoration:underline;text-underline-offset:3px;">Full guide →</a>'
            f'</div></div>'
        )
    cards_html = '<style>@media (max-width:640px){.wf-breed-grid{grid-template-columns:1fr !important;}}</style><div class="wf-breed-grid" style="display:grid;grid-template-columns:repeat(2,1fr);gap:20px;">' + "".join(cards) + '</div>'

    return {
        "meta": {
            "name": "Best Doodle Breeds for Families",
            "slug": "best-doodle-breeds-for-families",
            "shopify_handle": "best-doodle-breeds-for-families",
            "group": "Breed Guides",
            "size_category": "Roundup",
            "tags": ["doodle", "family-dogs", "designer-crossbreed", "low-shedding"],
            "published": False,
            "published_at": None,
            "excerpt": "The Doodle category has become the most popular family-dog choice in North America for good reasons — friendly temperament, low-shedding coats, and trainability. This guide covers the six most-asked-about Doodles: Goldendoodle, Labradoodle, Bernedoodle, Cavapoo, Sheepadoodle, and Aussiedoodle.",
            "meta_description": "The six best Doodle breeds for families: Goldendoodle, Labradoodle, Bernedoodle, Cavapoo, Sheepadoodle, and Aussiedoodle compared on temperament, exercise, grooming, lifespan, and breeder considerations.",
        },
        "images": {"hero": {"url": PLACEHOLDER_IMG, "alt": "Best Doodle Breeds for Families"}},
        "sections": {
            "intro": {
                "label": "Overview",
                "heading": "Best Doodle Breeds for Families",
                "html": (
                    "<p>The Doodle category — Poodle crosses with other popular family breeds — has become the most popular family-dog choice in North America over the last twenty years. The reasons are real: when bred well, Doodles combine the trainability and friendly temperament of the non-Poodle parent with the low-shedding coat and intelligence of the Poodle parent. The breed category is not without its critics (Wally Conron, who created the original Labradoodle, has publicly regretted starting the trend), and the unregulated breeding market has produced both excellent dogs and serious heartbreak.</p>"
                    "<p>Two themes apply to every Doodle on this list. First, <strong>the breeder matters more than the breed</strong>. A Doodle from a health-tested breeder who screens for the inherited diseases of both parent breeds is a dramatically different animal from a Doodle bought on price from an unverified breeder. Pay for OFA hip clearances, eye exams, and breed-specific DNA testing on both parents — the upfront premium is small compared to the cost of orthopedic surgery or chronic disease management at age 3. Second, <strong>generations matter for coat outcomes</strong>. F1 (first generation, parent-breed × Poodle) produces variable coats; F1B (F1 × Poodle) is more reliably low-shedding; multigen (third-generation+) is most consistent.</p>"
                    "<p>This guide covers the six most-asked-about Doodles for families. Each varies in size, energy level, grooming demands, and health profile. Read the individual breed guide for the one that interests you before contacting a breeder — the right breeder questions to ask are different for each.</p>"
                ),
            },
            "care": {
                "label": "Breeds",
                "heading": "Top Doodle Breeds for Families",
                "html": cards_html,
            },
            "special": {
                "label": "Considerations",
                "heading": "How to Choose the Right Doodle",
                "html": (
                    "<p><strong>Size and energy first.</strong> The biggest mismatch between Doodle owner and Doodle is energy level. The Aussiedoodle and Standard Labradoodle need 60–120 minutes of real daily exercise; under-exercised, they develop serious problem behaviors. The Cavapoo and Mini Bernedoodle need 30–45 minutes and are content with moderate activity. Match the breed to your actual lifestyle, not the lifestyle you hope to have.</p>"
                    "<p><strong>Grooming budget.</strong> All Doodles require professional grooming every 4–8 weeks plus 2–4 brushing sessions per week at home. Sheepadoodles need the most frequent grooming because of coat density. Annual professional grooming costs $500–$1,400 per dog, every year, for the life of the dog. If this is not in the budget, choose a different breed category — there are no low-grooming Doodles.</p>"
                    "<p><strong>Breeder verification.</strong> The single most important question for any Doodle breeder is: &quot;Can I see written OFA hip clearances and breed-specific health test results for both parents?&quot; A responsible breeder produces these immediately. A breeder who hedges or appeals to &quot;hybrid vigor&quot; as a substitute for testing is not breeding responsibly. For Cavapoos specifically, the Cavalier parent must have a current heart clearance from a board-certified veterinary cardiologist — this is non-negotiable.</p>"
                    "<p><strong>Separation anxiety planning.</strong> Doodles bond intensely with their family and are documented to develop separation anxiety at elevated rates. Households where the dog will be alone 8+ hours daily should either choose a less social breed or commit to dog walker, daycare, or webcam-monitored separation conditioning from puppyhood.</p>"
                ),
            },
        },
        "faq": [
            {"q": "Which Doodle is best for first-time dog owners?", "a": "The Goldendoodle and Bernedoodle are the most beginner-friendly Doodles — trainable, forgiving, and generally well-mannered. The Cavapoo is also good for first-time owners who specifically want a smaller dog and can be home most of the time. The Aussiedoodle is the most demanding and is generally not recommended for first-time owners due to its intelligence and energy requirements."},
            {"q": "Which Doodle sheds the least?", "a": "F1B and multigen Doodles in any breed line are more reliably low-shedding than F1. Within the breed lines, the Cavapoo and Aussiedoodle with curly coats (F1B or multigen) tend to shed the least, followed by Goldendoodle F1B and Labradoodle wool-coat varieties. No Doodle is fully hypoallergenic — all dogs produce allergen proteins. For maximum allergy reduction, an F1B with a confirmed curly coat is the safest choice, and spending time with the specific puppy before commitment is essential."},
            {"q": "Why do Doodles cost so much?", "a": "Two reasons. Demand has exceeded supply for two decades. And ethical breeding requires significant investment — OFA testing on both parents, genetic panels, stud fees, prenatal care, and puppy socialization can cost $3,000–$5,000 per litter before profit. Lower-priced Doodles often come from breeders who skip these costs, which is why the cheaper end of the market produces dogs with disproportionate health and temperament problems. Pay for a tested breeder — it is dramatically cheaper than a $5,000 hip surgery at age 4."},
            {"q": "Are Doodles AKC-recognized?", "a": "No. The AKC does not recognize any of the Doodle hybrids as official breeds because they are not stable breeding populations with consistent traits. Some Doodle-specific registries exist — the Goldendoodle Association of North America (GANA), Australian Labradoodle Association of America (ALAA), and Bernedoodle Association of America (BAA) — and these maintain breeder directories with health-testing standards. Lack of AKC recognition does not affect whether a Doodle makes a great family dog, but it does mean that breed standards and consistent traits are not enforced across the category."},
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUT, exist_ok=True)
    written = []

    for slug, data in BREEDS.items():
        path = os.path.join(OUT, f"{slug}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(build_main_breed_json(slug, data), f, indent=2, ensure_ascii=False)
        written.append(path)

    all_breeds = {
        "goldendoodle": "Goldendoodle",
        "labradoodle": "Labradoodle",
        "bernedoodle": "Bernedoodle",
        "cavapoo": "Cavapoo",
        "sheepadoodle": "Sheepadoodle",
        "aussiedoodle": "Aussiedoodle",
    }
    supplemental = {
        "goldendoodle": {
            "cost_total_first": "$4,500–$8,800",
            "cost_total_ongoing": "$2,050–$3,900",
            "cost_food_year1": "$500–$900",
            "cost_food_ongoing": "$500–$900",
            "cost_groom_year1": "$600–$1,200",
            "cost_groom_ongoing": "$600–$1,200",
            "cost_insurance_year1": "$600–$1,200",
            "cost_insurance_ongoing": "$600–$1,200",
            "lifespan": "10–15 yrs",
        },
        "labradoodle": {
            "cost_total_first": "$4,300–$9,100",
            "cost_total_ongoing": "$1,850–$3,700",
            "cost_food_year1": "$500–$900",
            "cost_food_ongoing": "$500–$900",
            "cost_groom_year1": "$500–$1,100",
            "cost_groom_ongoing": "$500–$1,100",
            "cost_insurance_year1": "$500–$1,100",
            "cost_insurance_ongoing": "$500–$1,100",
            "lifespan": "12–14 yrs",
        },
    }
    cost_data_lookup = dict(BREEDS)
    cost_data_lookup.update(supplemental)

    for slug, name in all_breeds.items():
        data = cost_data_lookup[slug]
        for builder, suffix in [
            (build_grooming_guide, "grooming-guide"),
            (build_first_year_costs, "first-year-costs"),
            (build_puppy_checklist, "puppy-checklist"),
        ]:
            path = os.path.join(OUT, f"{slug}-{suffix}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(builder(slug, name, data), f, indent=2, ensure_ascii=False)
            written.append(path)

    path = os.path.join(OUT, "best-doodle-breeds-for-families.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(build_roundup(), f, indent=2, ensure_ascii=False)
    written.append(path)

    print(f"Wrote {len(written)} files:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
