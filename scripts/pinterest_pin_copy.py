"""Generate Pinterest pin copy for Sprint 1 (Top 20 articles x 2 pin angles).

Per user request 2026-06-28: use existing blog hero images directly
(no PIL pin design step). This script only generates the COPY -
title, description, hashtags, UTM-tagged destination link, and the
hero-image URL the user uploads from.

For each pin, output is wrapped in markdown code blocks so the user
can one-click-select-all and paste into Pinterest's Create Pin UI.

Output: ``pinterest-sprint-1.md`` in repo root.

Pinterest limits (2026):
  - Title: max 100 chars
  - Description: max 500 chars (best 200-400)
  - Hashtags: 3-5 best practice (Pinterest deprecates heavy hashtag use)
  - Schedule horizon: 14 days max for native scheduler

Run:
    python3 scripts/pinterest_pin_copy.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"
OUTPUT = ROOT / "pinterest-sprint-1.md"

SITE_ORIGIN = "https://thewooffy.com"


def article_url(slug: str, blog_handle: str, utm_campaign: str, variant: str) -> str:
    return (
        f"{SITE_ORIGIN}/blogs/{blog_handle}/{slug}"
        f"?utm_source=pinterest&utm_medium=social"
        f"&utm_campaign={utm_campaign}&utm_content={slug}-{variant}"
    )


PIN_CONFIGS: list[dict] = [
    # Tier 1: proven GA4 traffic
    {
        "slug": "alaskan-malamute-grooming-guide",
        "a": {
            "title": "Alaskan Malamute Grooming: How to Manage Heavy Double-Coat Shedding",
            "description": "Alaskan Malamutes blow their double coat 2x a year - and it is intense. Brushing routine, undercoat rake vs slicker, professional vs DIY grooming, and the bathing schedule that actually works for this Arctic breed.\n\n#alaskanmalamute #doggrooming #doublecoat #dogshedding #dogcare",
            "board": "Dog Care & Grooming",
            "campaign": "grooming-guide",
        },
        "b": {
            "title": "Alaskan Malamute Sheds A LOT - Here's What You're Signing Up For",
            "description": "Thinking of getting an Alaskan Malamute? The shedding is no joke. Two coat-blowing seasons per year, daily brushing during peak, fur tumbleweeds in every corner. Here is the honest breakdown of what coat care really looks like.\n\n#alaskanmalamute #malamute #dogshedding #northerndogs #doglover",
            "board": "Dog Breed Guides",
            "campaign": "grooming-guide",
        },
    },
    {
        "slug": "best-dogs-for-hot-climates",
        "a": {
            "title": "10 Best Dog Breeds for Hot Climates: Heat-Tolerant Breeds That Thrive",
            "description": "Sun, humidity, 95F+ summers - these 10 breeds are built to handle it. Single-coat, short-haired, and Mediterranean-origin dogs that thermoregulate well in heat. Plus the breeds you should NOT bring to a hot climate.\n\n#dogbreeds #hotweatherdogs #summerdogs #dogcare #besttopadog",
            "board": "Best Dogs For...",
            "campaign": "roundup-climate",
        },
        "b": {
            "title": "Best Dogs for Hot Weather: Why Huskies & Berneses Don't Make This List",
            "description": "Hot-climate living needs the right breed. Single-coat, lean, short-muzzled (but not flat-faced!) breeds win. 10 thermoregulation-friendly picks plus a warning list of breeds that suffer in heat.\n\n#hotweatherdogs #dogbreeds #climatedogs #summerdogcare #dogowner",
            "board": "Best Dogs For...",
            "campaign": "roundup-climate",
        },
    },
    {
        "slug": "nova-scotia-duck-tolling-retriever-first-year-costs",
        "a": {
            "title": "Nova Scotia Duck Tolling Retriever Price: $1,500-$3,000 Puppy + Year 1",
            "description": "Toller puppy price: $1,500-$3,000 from a reputable breeder (rescue $400-$700). First-year total $3,000-$6,500 including vet, food, training, gear, and grooming. Full 2026 cost breakdown for the smallest retriever in the AKC.\n\n#tollers #ducktolling #dogbudget #firsttimedogowner #puppycost",
            "board": "Puppy Costs & Budget",
            "campaign": "first-year-costs",
        },
        "b": {
            "title": "Is a Toller Worth $3,000? Real 2026 Cost Breakdown",
            "description": "Beyond the puppy price tag - what does the first year of owning a Nova Scotia Duck Tolling Retriever actually cost? Vet visits, food bills, training class, gear, and the hidden costs of an active sporting breed.\n\n#nsdtr #toller #dogcost #sportingdog #dogowner",
            "board": "Dog Breed Guides",
            "campaign": "first-year-costs",
        },
    },
    {
        "slug": "best-dogs-for-cold-climates",
        "a": {
            "title": "10 Best Dog Breeds for Cold Climates: Huskies, Malamutes, Samoyeds",
            "description": "Cold-hardy breeds bred for snow and ice. Husky, Malamute, Samoyed, Saint Bernard, Bernese, Tibetan Mastiff - full guide to dogs that thrive in winter climates with thick double coats and large paws.\n\n#colddogs #huskydog #winterdogs #snowdogs #dogbreeds",
            "board": "Best Dogs For...",
            "campaign": "roundup-climate",
        },
        "b": {
            "title": "If You Live Somewhere Cold, These Are the Right Dog Breeds",
            "description": "Living in snow country? These 10 breeds are evolutionarily wired for cold - historical Arctic and mountain dogs that love -20F walks. Bonus: care tips for winter paw protection.\n\n#wintervibes #huskypuppy #malamute #snowdogs #dogwinter",
            "board": "Best Dogs For...",
            "campaign": "roundup-climate",
        },
    },
    # Tier 2: GSC striking-distance
    {
        "slug": "bernese-mountain-dog-vs-saint-bernard",
        "a": {
            "title": "Bernese Mountain Dog vs St Bernard: 90 vs 140 lb, Cost, Drool, Lifespan",
            "description": "Both gentle giants - but they differ on size (90 vs 140 lb), drool level, exercise needs, cost, and shedding. Side-by-side 2026 comparison to pick the right giant for your family before you commit.\n\n#bernesemountaindog #saintbernard #dogcomparison #giantdogbreeds #familydog",
            "board": "Best Dogs For...",
            "campaign": "comparison",
        },
        "b": {
            "title": "Bernese or Saint Bernard? The Quick Decision Guide",
            "description": "Choosing between two of the most lovable giant breeds. Drool ($$ on towels), shedding, exercise needs, cost, lifespan. The straight comparison that saves you 3 weeks of research.\n\n#bernese #saintbernard #gentlegiants #largedogs #dogchoice",
            "board": "Best Dogs For...",
            "campaign": "comparison",
        },
    },
    {
        "slug": "fluffy-dog-breeds",
        "a": {
            "title": "10 Fluffy Dog Breeds: Samoyed, Pomeranian, Chow Chow & More",
            "description": "Cloud-like coats and teddy-bear faces. From the snow-white Samoyed to the pocket-sized Pomeranian - 10 of the fluffiest dogs in the world, with grooming time, shedding level, and family-fit details for each.\n\n#fluffydogs #dogbreeds #samoyed #pomeranian #cuteanimals",
            "board": "Dog Breed Guides",
            "campaign": "roundup-fluffy",
        },
        "b": {
            "title": "If You Love Fluffy Dogs, You'll Want These 10 Breeds",
            "description": "Fluffy dogs win on cuteness. They also win on grooming hours. Here are 10 of the fluffiest breeds with realistic care commitments - Bichon, Keeshond, Eurasier, and 7 more that turn heads on walks.\n\n#fluffypuppy #cutedog #petsofpinterest #dogphoto #dogbreeds",
            "board": "Dog Breed Guides",
            "campaign": "roundup-fluffy",
        },
    },
    {
        "slug": "cavalier-king-charles-spaniel-first-year-costs",
        "a": {
            "title": "Cavalier King Charles Spaniel Cost: $2,000-$3,500 First Year Budget",
            "description": "Cavalier puppy + vet + food + grooming + MVD/SM-screening = full first-year cost breakdown for one of the most beloved toy breeds. What to budget, what to skip, and what to spend extra on for this royal pup.\n\n#cavalierkingcharlesspaniel #cavalierpuppy #dogcost #puppybudget #toydogs",
            "board": "Puppy Costs & Budget",
            "campaign": "first-year-costs",
        },
        "b": {
            "title": "Before You Buy a Cavalier: The First-Year Cost Most People Underestimate",
            "description": "Cavaliers are budget-friendly to buy but health-screening (MVD, syringomyelia) can shift the math. Here is the honest 2026 first-year budget for a Cavalier King Charles Spaniel including what insurance does and does not cover.\n\n#cavalier #ckcs #puppycosts #dogowner #toydog",
            "board": "Puppy Costs & Budget",
            "campaign": "first-year-costs",
        },
    },
    {
        "slug": "cavalier-king-charles-spaniel",
        "a": {
            "title": "Cavalier King Charles Spaniel: Temperament, Health Risks & Care Guide",
            "description": "The royal lapdog - gentle, affectionate, and devoted. Complete breed guide covering temperament, MVD heart disease screening, syringomyelia awareness, grooming routine, and family-fit. Everything to know before you buy.\n\n#cavalierkingcharlesspaniel #toydogs #dogbreeds #ckcs #lapdog",
            "board": "Dog Breed Guides",
            "campaign": "breed-guide",
        },
        "b": {
            "title": "Is a Cavalier King Charles Spaniel Right for You?",
            "description": "Affectionate, soft, low-energy companion. But Cavaliers come with serious health considerations (heart, brain) that responsible buyers should know. Full breed guide with realistic ownership outlook.\n\n#cavalier #ckcs #toybreeds #familydog #lapdog",
            "board": "Dog Breed Guides",
            "campaign": "breed-guide",
        },
    },
    # Tier 3: recent HD-hero Reddit-trend content
    {
        "slug": "dog-food-on-a-budget-2026",
        "a": {
            "title": "Dog Food Prices Are Up 143%: 8 Honest Ways to Save Without Cutting Nutrition",
            "description": "Petflation is real - pet food up 143% since 2020. Here is how to feed your dog well on a tighter budget: AAFCO label decoded, budget vs premium reality, what 'grain-free' marketing gets wrong, and 8 actionable cost-cutting tactics.\n\n#dogfood #dogowner #budgetdog #dognutrition #pethealth",
            "board": "Puppy Costs & Budget",
            "campaign": "budget-food",
        },
        "b": {
            "title": "Best Dog Food on a Budget: What Vets Actually Recommend (2026)",
            "description": "Skip the boutique brands - veterinary nutritionists often recommend mid-tier Purina/Royal Canin/Hill's over expensive premium. Why, and how to choose a quality kibble for under $70/bag. Plus when fresh-food add-ons actually save money.\n\n#dogfood #dognutrition #vetapproved #budgetdog #dogcare",
            "board": "Puppy Costs & Budget",
            "campaign": "budget-food",
        },
    },
    {
        "slug": "smart-dog-collar-buyer-guide-2026",
        "a": {
            "title": "Fi vs Halo vs Tractive: Honest 2026 Smart Dog Collar Buyer Guide",
            "description": "GPS trackers, virtual fences, activity monitors - which smart collar is worth $649 vs $60? Fi Series 3, Halo Collar 4, Tractive GPS, Apple AirTag setups compared with real prices, subscription costs, and use cases.\n\n#smartcollar #ficollar #dogtracker #gpscollar #dogtech",
            "board": "Dog Tech & Gear",
            "campaign": "smart-collar",
        },
        "b": {
            "title": "Best Smart Dog Collar in 2026: Don't Get Subscription-Trapped",
            "description": "Hardware is one cost - monthly subscription is the real lifetime expense. $10/month for 10 years = $1,200. Honest comparison of Fi, Halo, Tractive, and AirTag so you don't pay for features you do not use.\n\n#dogcollar #gpstracker #petsafety #smartpet #dogtech",
            "board": "Dog Tech & Gear",
            "campaign": "smart-collar",
        },
    },
    {
        "slug": "doodle-breeding-ethics-2026",
        "a": {
            "title": "The Doodle Boom Is Hurting Doodles: How to Find Ethical Breeders in 2026",
            "description": "Doodle shelter intake is at multi-year highs. 8 breeder red flags, 6 vetting questions, and the rescue networks that need adopters. Plus the case for adoption over breeder purchases in the current oversupply market.\n\n#doodlebreeds #goldendoodle #ethicalbreeding #dogrescue #adoptdontshop",
            "board": "Doodle Dogs",
            "campaign": "doodle-ethics",
        },
        "b": {
            "title": "8 Red Flags in a Doodle Breeder (And 6 Questions to Ask)",
            "description": "If a doodle breeder always has puppies available, hides health-testing data, or refuses video tours, walk away. Here are the 8 red flags + 6 vetting questions that separate ethical breeders from puppy mills.\n\n#doodlebreeds #responsiblebreeding #goldendoodle #dogowner #puppybuying",
            "board": "Doodle Dogs",
            "campaign": "doodle-ethics",
        },
    },
    {
        "slug": "keep-double-coated-dogs-cool-in-summer",
        "a": {
            "title": "How to Keep Your Husky or Bernese Cool in Summer (Without Shaving)",
            "description": "Double-coated breeds - Husky, Malamute, Bernese, Samoyed - overheat fast in summer. Brushing routine, cooling mat strategy, ice tricks, when to skip walks, and the early warning signs of heat stroke.\n\n#dogcare #summerdogs #huskysafety #doublecoat #dogsummer",
            "board": "Seasonal Dog Care",
            "campaign": "summer-care",
        },
        "b": {
            "title": "Shaving Your Double-Coated Dog Is Actually a BAD Idea - Here's Why",
            "description": "Shaving a Husky, Malamute, Samoyed, or Bernese in summer can damage the coat permanently AND make heat intolerance worse. Here is what the double coat actually does + safer summer cooling strategies.\n\n#dogsummer #huskycare #malamute #samoyed #dogcare",
            "board": "Seasonal Dog Care",
            "campaign": "summer-care",
        },
    },
    {
        "slug": "dog-tick-prevention-lyme-disease-guide",
        "a": {
            "title": "Tick Prevention for Dogs: 4 Methods Compared + Lyme Risk Map",
            "description": "Topical, oral, collar, vaccine - which tick prevention is right for your dog? Plus the 2026 Lyme disease risk map and the proper way to remove a tick (and what to do if you find one).\n\n#dogticks #lyme #dogsafety #petprevention #outdoordog",
            "board": "Dog Health",
            "campaign": "tick-prevention",
        },
        "b": {
            "title": "Lyme Disease in Dogs: Warning Signs + Tick Prevention That Actually Works",
            "description": "Most owners do not recognize the early signs of canine Lyme until it is advanced. Here are the warning signs, the diagnostic timeline, the treatment protocol, and the tick prevention methods that genuinely work.\n\n#dogsafety #ticks #lymedisease #dogowner #vethealth",
            "board": "Dog Health",
            "campaign": "tick-prevention",
        },
    },
    # Tier 4: Pinterest-favorable evergreen
    {
        "slug": "goldendoodle",
        "a": {
            "title": "Goldendoodle Breed Guide: Temperament, Care, Cost & Grooming (2026)",
            "description": "Friendly, intelligent, typically low-shedding. The Goldendoodle combines Golden Retriever warmth with Poodle smarts. Full 2026 breed guide covering temperament, grooming routine, first-year costs ($2,500-$5,000), and family-fit.\n\n#goldendoodle #doodlebreeds #familydog #puppy #doglover",
            "board": "Doodle Dogs",
            "campaign": "breed-guide-doodle",
        },
        "b": {
            "title": "Is a Goldendoodle the Right Dog for You?",
            "description": "Goldendoodle: pros, cons, and the realistic picture nobody on Instagram shows you. Coat-shedding probability, exercise needs, separation anxiety risk, and the right breeder vetting checklist.\n\n#goldendoodle #doodle #puppy #familydog #hypoallergenic",
            "board": "Doodle Dogs",
            "campaign": "breed-guide-doodle",
        },
    },
    {
        "slug": "most-loyal-dog-breeds",
        "a": {
            "title": "10 Most Loyal Dog Breeds: German Shepherd, Akita, Labrador & More",
            "description": "Loyalty is not just a feel-good trait - these 10 breeds have proven historic bonds to their humans. German Shepherds, Akitas, Labradors, Boxers, Border Collies and 5 more, with what makes each loyal in their own way.\n\n#loyaldogs #dogbreeds #germanshepherd #akita #doglovers",
            "board": "Best Dogs For...",
            "campaign": "roundup-loyalty",
        },
        "b": {
            "title": "Most Loyal Dog Breeds (Honorable Mention: Cane Corso)",
            "description": "Bonded-for-life breeds. The classic 10 plus the Cane Corso - a fiercely devoted Italian guardian breed gaining popularity in the US. Find the right loyal companion for your home.\n\n#canecorso #dogbreeds #loyaldog #protectiondog #dogowner",
            "board": "Best Dogs For...",
            "campaign": "roundup-loyalty",
        },
    },
    {
        "slug": "best-dogs-for-first-time-owners",
        "a": {
            "title": "10 Best Dog Breeds for First-Time Owners (Easy to Train, Forgiving)",
            "description": "First-time dog ownership? These 10 breeds set you up for success - Labs, Golden Retrievers, Cavaliers, Bichons, and other breeds known for trainability and forgiveness of beginner mistakes.\n\n#firsttimedogowner #dogbreeds #bestdogs #puppy #beginnerdog",
            "board": "Best Dogs For...",
            "campaign": "roundup-first-time",
        },
        "b": {
            "title": "If You've Never Had a Dog Before, Start With One of These Breeds",
            "description": "Forgiving, trainable, social. The 10 best dog breeds for first-time owners - what makes each one beginner-friendly and which ones to skip even though they look perfect on Instagram.\n\n#firstdog #newpuppy #beginnerdog #dogadvice #familydog",
            "board": "Best Dogs For...",
            "campaign": "roundup-first-time",
        },
    },
    {
        "slug": "best-small-dog-breeds",
        "a": {
            "title": "10 Best Small Dog Breeds for Apartments and Small Spaces",
            "description": "Small in size, big in personality. Yorkies, Cavaliers, Bichons, Maltese, and 6 more small breeds that thrive in apartments. Exercise needs, barking tendencies, and family-fit for each.\n\n#smalldogs #apartmentdogs #smalldogbreeds #toydogs #urbandog",
            "board": "Best Dogs For...",
            "campaign": "roundup-small",
        },
        "b": {
            "title": "Small Dog Breeds That Won't Annoy Your Neighbors",
            "description": "Small does not always mean quiet. Here are the small breeds with low-barking tendencies - apartment-friendly small dogs that get along with neighbors as well as families.\n\n#smalldogs #apartmentliving #quietdog #dogchoice #lapdog",
            "board": "Best Dogs For...",
            "campaign": "roundup-small",
        },
    },
    {
        "slug": "golden-retriever",
        "a": {
            "title": "Golden Retriever Breed Guide: Temperament, Health, Care & Cost",
            "description": "America's favorite family dog. Friendly, intelligent, gentle - but high-maintenance grooming and prone to specific health issues (hips, cancer). Full 2026 breed guide for prospective Golden Retriever owners.\n\n#goldenretriever #familydog #dogbreeds #goldenpuppy #doglover",
            "board": "Dog Breed Guides",
            "campaign": "breed-guide",
        },
        "b": {
            "title": "Why the Golden Retriever Is Still the #1 Family Dog in 2026",
            "description": "Decades on, the Golden Retriever still tops American family-dog rankings. Temperament, grooming reality, health screenings, and what to expect from puppy to senior. Plus the lines/breeders worth trusting.\n\n#goldenretriever #familydog #bestbreed #goldenretrieverpuppy #dogphoto",
            "board": "Dog Breed Guides",
            "campaign": "breed-guide",
        },
    },
    {
        "slug": "best-dogs-for-active-people",
        "a": {
            "title": "10 Best Dog Breeds for Active People: Hiking, Running, Sport Companions",
            "description": "Built for the trail, the gym, and the long-haul. Border Collies, Vizslas, Australian Shepherds, German Shorthaired Pointers - 10 breeds that match active lifestyles. Exercise needs and matching tips.\n\n#activedog #hikingwithdogs #runningdog #dogbreeds #sportingdog",
            "board": "Best Dogs For...",
            "campaign": "roundup-active",
        },
        "b": {
            "title": "If You Run 5K+, These Are the Right Dogs to Run With",
            "description": "Distance running with your dog needs the right breed. Sustained-endurance dogs (Vizsla, GSP, Border Collie) vs sprinters that look athletic but cannot go the distance. Honest breed-by-breed running guide.\n\n#runningdog #athleticdog #activedogs #sportsdog #dogcompanion",
            "board": "Best Dogs For...",
            "campaign": "roundup-active",
        },
    },
    {
        "slug": "most-popular-dog-breeds",
        "a": {
            "title": "Most Popular Dog Breeds in America 2026: AKC Top 10 & Why",
            "description": "French Bulldog, Labrador, Golden Retriever - the AKC's top 10 most popular breeds in the US, what each one offers, and what each costs to own. A snapshot of what Americans actually choose.\n\n#popularbreeds #dogbreeds #frenchbulldog #labrador #goldenretriever",
            "board": "Best Dogs For...",
            "campaign": "roundup-popular",
        },
        "b": {
            "title": "Top 10 Dog Breeds Americans Actually Choose (2026 Edition)",
            "description": "Latest AKC rankings - the breeds Americans bring home most. Why French Bulldogs unseated the Labrador, why Goldens hold their spot, and which breeds are climbing fastest in 2026.\n\n#dogbreeds #popular #akc #toptenbreeds #familydog",
            "board": "Best Dogs For...",
            "campaign": "roundup-popular",
        },
    },
]


def load_article(slug: str) -> tuple[str, str, str] | None:
    """Return (display_name, hero_url, blog_handle) for an article slug."""
    p = BREED_DATA / f"{slug}.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    meta = data.get("meta", {})
    name = (meta.get("name") or slug).strip()
    blog = (meta.get("blog_handle") or "dog-breeds").strip()
    hero = (data.get("images") or {}).get("hero", {}).get("url", "")
    if not hero:
        return None
    return name, hero, blog


def render_pin(idx: int, total: int, slug: str, display_name: str,
                hero_url: str, blog_handle: str, variant_key: str, pin_cfg: dict) -> str:
    link = article_url(slug, blog_handle, pin_cfg["campaign"], variant_key)
    title = pin_cfg["title"]
    desc = pin_cfg["description"]
    board = pin_cfg["board"]
    lines = [
        f"---",
        f"",
        f"## Pin {idx} of {total} - {display_name} (variant {variant_key.upper()})",
        f"",
        f"- **Board**: `{board}`",
        f"- **Image source**: download from this URL (or save from the article hero on Wooffy):",
        f"",
        f"  ```",
        f"  {hero_url}",
        f"  ```",
        f"",
        f"- **Destination link (paste into Pinterest 'Add destination link')**:",
        f"",
        f"  ```",
        f"  {link}",
        f"  ```",
        f"",
        f"### Title  ({len(title)} chars / 100 max)",
        f"```",
        f"{title}",
        f"```",
        f"",
        f"### Description  ({len(desc)} chars / 500 max)",
        f"```",
        f"{desc}",
        f"```",
        f"",
    ]
    return "\n".join(lines)


def main() -> int:
    rendered: list[str] = []
    pin_idx = 0
    total = sum(2 for _ in PIN_CONFIGS)
    missing: list[str] = []
    for cfg in PIN_CONFIGS:
        slug = cfg["slug"]
        loaded = load_article(slug)
        if loaded is None:
            missing.append(slug)
            print(f"  [skip] {slug}: no JSON or no hero URL", file=sys.stderr)
            continue
        display_name, hero_url, blog_handle = loaded
        for variant_key in ("a", "b"):
            pin_idx += 1
            rendered.append(render_pin(
                pin_idx, total, slug, display_name, hero_url, blog_handle,
                variant_key, cfg[variant_key],
            ))

    header = [
        "# Wooffy Pinterest Sprint 1 - 40 Pins from Top 20 Articles",
        "",
        f"Total pins: **{pin_idx}** (target 40).",
        "Visual approach (per user spec): use existing blog hero images directly. No PIL pin design needed.",
        "",
        "## Workflow per pin",
        "",
        "1. Open the **Image source** URL in a browser, right-click - Save Image (or copy URL).",
        "2. Pinterest - top-right **+** - **Create Pin**.",
        "3. Upload the saved image.",
        "4. Paste the **Title** (<=100 chars).",
        "5. Paste the **Description** (<=500 chars, hashtags already included).",
        "6. Paste the **Destination link** (already UTM-tagged for GA4).",
        "7. Pick the suggested **Board**.",
        "8. **Schedule** for a future time (Pinterest native scheduler: 14-day horizon).",
        "",
        "## Recommended posting cadence",
        "",
        "- Days 1-3: 5 pins/day (15 total) - seed the account",
        "- Days 4-7: 6-8 pins/day (25 total) - fill remaining schedule slots",
        "- Spread across multiple boards within a day (Pinterest dislikes spamming one board)",
        "- Best Pinterest posting times: 8-11pm ET (US evening browsing)",
        "",
        "## Boards to create on Pinterest (if not already)",
        "",
        "- Dog Breed Guides - breed-specific pages",
        "- Best Dogs For... - roundup articles (climate, family, etc.)",
        "- Dog Care & Grooming - grooming guides",
        "- Puppy Costs & Budget - first-year cost & food budget guides",
        "- Doodle Dogs - goldendoodle, labradoodle, doodle ethics",
        "- Dog Tech & Gear - smart collars, GPS",
        "- Dog Health - tick prevention, brachycephalic, etc.",
        "- Seasonal Dog Care - summer cool, winter prep",
        "",
        f"## GA4 tracking",
        "",
        "Every destination link is tagged with `utm_source=pinterest&utm_medium=social`.",
        "Filter GA4 - Reports - Acquisition - Traffic acquisition - Session source/medium = `pinterest / social`",
        "to see real-time inbound Pinterest traffic and which campaign/article performs best.",
        "",
    ]
    if missing:
        header.append("")
        header.append("**Missing articles (skipped):** " + ", ".join(missing))

    OUTPUT.write_text("\n".join(header) + "\n\n" + "\n".join(rendered),
                      encoding="utf-8", newline="\n")
    print(f"Generated {pin_idx} pin entries -> {OUTPUT}")
    print(f"  Boards: 8 distinct")
    print(f"  Articles: {pin_idx // 2}")
    print(f"  Missing/skipped: {len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
