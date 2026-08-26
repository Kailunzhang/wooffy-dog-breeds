"""One-shot: build pinterest-sprint-2.md - 20 pin copies for manual posting.

Targets the 2026-08-26 digest's new traffic stars: bichon cluster,
corgi grooming, nutrition star pages, goldendoodle costs, and the
comparison angle Sprint 1 validated at ~7% outbound CTR.

Run:  py scripts/generate_sprint2_pins.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"
OUT = ROOT / "pinterest-sprint-2.md"

BR = "\n\n"

PINS = [
 ("bichon-frise-first-year-costs", "a", "Puppy Costs & Budget", "s2-costs",
  "Bichon Frise Cost: What the First Year Really Runs",
  "Bichon Frise first-year budget: puppy price, the professional grooming schedule this coat genuinely requires (every 4-6 weeks), vet, food for a 12-18 lb companion, and what year two settles into." + BR + "#bichonfrise #puppycost #dogbudget #smalldogs #firsttimedogowner"),
 ("bichon-frise-first-year-costs", "b", "Dog Breed Guides", "s2-costs",
  "Before You Buy a Bichon: The Grooming Line Item Nobody Mentions",
  "The Bichon Frise looks affordable until you price the coat: professional grooming every 4-6 weeks is non-negotiable for this breed. Full honest first-year budget with the real recurring costs." + BR + "#bichon #bichonfrise #doggrooming #puppybudget #toydogs"),
 ("bichon-frise-grooming-guide", "a", "Dog Care & Grooming", "s2-groom",
  "Bichon Grooming: The 4-6 Week Cycle That Keeps the Cloud White",
  "That powder-puff coat is a commitment: daily brushing, tear-stain care, and a professional trim cycle. The complete Bichon grooming routine - what to DIY, what to leave to the groomer, and what it costs." + BR + "#bichonfrise #doggrooming #bichongrooming #whitedog #dogcare"),
 ("bichon-frise-grooming-guide", "b", "Dog Care & Grooming", "s2-groom",
  "Why Bichon Coats Mat (And the Brushing Routine That Prevents It)",
  "Bichon fur traps loose hair instead of shedding it - skip three days of brushing and mats form near the skin. The prevention routine, the right tools, and the tear-stain fix." + BR + "#bichon #matteddog #doggrooming #dogtips #smalldogs"),
 ("bichon-frise", "a", "Dog Breed Guides", "s2-breed",
  "Bichon Frise: The Apartment Dog That Does Not Shed on Your Couch",
  "Cheerful, small, low-shedding, and genuinely good in apartments - the Bichon Frise breed guide: temperament, the real grooming commitment, health outlook, and who this dog is (and is not) for." + BR + "#bichonfrise #apartmentdogs #hypoallergenic #smalldogbreeds #dogbreeds"),
 ("pembroke-welsh-corgi-grooming-guide", "a", "Dog Care & Grooming", "s2-groom",
  "Corgi Shedding Is Not a Joke: The Routine That Controls It",
  "Pembroke Welsh Corgis shed year-round and blow coat twice a year. The undercoat-rake routine, bath-and-blowout schedule, and the tools that actually keep fur off your floor." + BR + "#corgi #corgigrooming #dogshedding #pembrokewelshcorgi #dogcare"),
 ("pembroke-welsh-corgi-grooming-guide", "b", "Dog Breed Guides", "s2-groom",
  "Thinking About a Corgi? Meet the Undercoat First",
  "Everyone sees the corgi butt; nobody warns you about the undercoat. What weekly grooming really looks like for a Pembroke, which tools work, and when to book a pro deshed." + BR + "#corgi #corgilife #doggrooming #dogtips #newdogowner"),
 ("can-dogs-eat-cherries", "a", "Dog Health", "s2-food",
  "Can Dogs Eat Cherries? The Pit Is the Problem",
  "Cherry flesh is safe in small amounts - the pit, stem, and leaves carry cyanogenic compounds and choking risk. How to serve cherries safely, how much is too much, and the symptoms that mean call your vet." + BR + "#candogseat #dogsafety #dognutrition #dogtreats #pethealth"),
 ("can-dogs-eat-peaches", "a", "Dog Health", "s2-food",
  "Can Dogs Eat Peaches? Yes - With One Big Caveat",
  "Fresh peach flesh is a safe summer treat; the pit is a cyanide-and-obstruction double hazard, and canned peaches carry too much sugar. Serving sizes by dog size + safe prep in 30 seconds." + BR + "#candogseat #peaches #dognutrition #summerdog #dogtreats"),
 ("can-dogs-eat-cantaloupe", "a", "Dog Health", "s2-food",
  "Can Dogs Eat Cantaloupe? A Simple Serving Guide",
  "Cantaloupe is low-calorie, hydrating, and safe for most dogs - the rind and seeds are not. Portion guide by dog size, diabetic-dog cautions, and 3 easy ways to serve it on hot days." + BR + "#cantaloupe #candogseat #doghealth #dogtreats #dognutrition"),
 ("can-dogs-eat-zucchini", "a", "Dog Health", "s2-food",
  "Can Dogs Eat Zucchini? One of the Safest Veggies to Share",
  "Zucchini is low-calorie, vitamin-rich, and safe raw or cooked - one of the best training-treat vegetables for dogs watching their weight. Portions by size + the seasoning mistake to avoid." + BR + "#zucchini #candogseat #dognutrition #healthydog #dogtreats"),
 ("goldendoodle-first-year-costs", "a", "Puppy Costs & Budget", "s2-costs",
  "Goldendoodle Cost 2026: $2,000-$5,000 Puppy + What Year One Adds",
  "The doodle price tag is just the entry fee: mandatory professional grooming every 6-8 weeks, vet, food, training. The full honest Goldendoodle first-year budget, by generation (F1, F1B, multigen)." + BR + "#goldendoodle #doodlecost #puppyprice #goldendoodlepuppy #dogbudget"),
 ("goldendoodle-first-year-costs", "b", "Doodle Dogs", "s2-costs",
  "Why Goldendoodles Cost More Than Golden Retrievers to Own",
  "Same size, bigger budget: the doodle coat needs professional grooming a Golden never does - $600-$1,200 a year, forever. Full cost comparison inside, plus where doodle budgets actually save." + BR + "#goldendoodle #doodlelife #dogcost #goldenretriever #puppybudget"),
 ("xoloitzcuintli-first-year-costs", "a", "Puppy Costs & Budget", "s2-costs",
  "Xoloitzcuintli Price: What the Ancient Hairless Dog Costs",
  "Rare breed, moderate budget: Xolo puppy price from ethical breeders, why grooming costs almost nothing but skincare does not, and the full first-year number most Xolo articles skip." + BR + "#xoloitzcuintli #xolo #hairlessdog #rarebreeds #puppycost"),
 ("shiba-inu", "a", "Dog Breed Guides", "s2-breed",
  "Shiba Inu Truths: Independent, Clean, and Not for Everyone",
  "The Shiba is cat-like, fastidious, dramatic about baths, and famously stubborn on recall. An honest breed guide: temperament, the scream, shedding seasons, and who genuinely matches this dog." + BR + "#shibainu #shiba #dogbreeds #shibalife #japanesedog"),
 ("cane-corso-vs-presa-canario", "a", "Best Dogs For...", "s2-vs",
  "Presa Canario vs Cane Corso: Size, Bite Force, Legality",
  "Two serious guardian mastiffs, one big decision: temperament and drive, 100+ lb size classes, training demands, insurance and breed-ban legality by region. The honest comparison before you commit." + BR + "#canecorso #presacanario #guarddog #mastiff #dogcomparison"),
 ("great-dane-vs-doberman", "a", "Best Dogs For...", "s2-vs",
  "Great Dane vs Doberman: Gentle Giant or Velcro Athlete?",
  "Both turn heads, but they are opposite dogs to live with: 140 lb couch companion vs 90 lb working athlete. Size, exercise, the DCM heart risk both breeds share, lifespan, and family fit." + BR + "#greatdane #doberman #dogcomparison #largedogs #guarddogs"),
 ("rottweiler-vs-cane-corso", "a", "Best Dogs For...", "s2-vs",
  "Rottweiler vs Cane Corso: Which Guardian Fits a First Owner?",
  "Prey drive, trainability, and experience requirements separate these two power breeds more than size does. The honest comparison - including which one needs an expert handler." + BR + "#rottweiler #canecorso #guarddogs #dogcomparison #powerbreeds"),
 ("cavapoo-vs-cockapoo", "a", "Doodle Dogs", "s2-vs",
  "Cavapoo vs Cockapoo: The Small Doodle Face-Off",
  "Both small, both adorable, different dogs: size ranges, coat and shedding odds, health watch-lists (MVD vs ears), price, and apartment fit. Which small doodle actually matches your home?" + BR + "#cavapoo #cockapoo #doodledogs #smalldogs #doodlepuppy"),
 ("papillon-first-year-costs", "a", "Puppy Costs & Budget", "s2-costs",
  "Papillon Price: $1,200-$2,500 for the Smartest Toy Dog",
  "Ranked among the most intelligent breeds at 6-10 lbs: Papillon puppy price, tiny food bills, the dental-care line item toy breeds cannot skip, and the honest first-year total." + BR + "#papillon #toydogs #puppycost #smartdog #smalldogbreeds"),
]


def main() -> int:
    lines = [
        "# Wooffy Pinterest Sprint 2 - 20 Pins (2026-08-26)",
        "",
        "Targets the 8/26 digest traffic stars: bichon cluster / corgi grooming /",
        "nutrition star pages / goldendoodle costs / comparisons (Sprint 1's",
        "strongest angle at ~7% outbound CTR). Same manual workflow as Sprint 1:",
        "save image from hero URL, paste title + description + link, 5 pins/day,",
        "spread across boards.",
        "",
    ]
    missing = []
    n = 0
    for slug, var, board, camp, title, desc in PINS:
        p = BREED_DATA / f"{slug}.json"
        if not p.exists():
            missing.append(slug)
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        hero = (d.get("images") or {}).get("hero", {}).get("url", "")
        blog = d["meta"].get("blog_handle") or "dog-breeds"
        link = (f"https://thewooffy.com/blogs/{blog}/{slug}"
                f"?utm_source=pinterest&utm_medium=social&utm_campaign={camp}"
                f"&utm_content={slug}-{var}")
        assert len(title) <= 100, f"title too long: {slug} ({len(title)})"
        assert len(desc) <= 500, f"desc too long: {slug} ({len(desc)})"
        n += 1
        lines += [
            "---", "",
            f"## Pin {n}/20 - {d['meta'].get('name', slug)[:60]} ({var.upper()})",
            f"- **Board**: `{board}`",
            "- **Image**:", "```", hero, "```",
            "- **Link**:", "```", link, "```",
            f"### Title ({len(title)}c)", "```", title, "```",
            f"### Description ({len(desc)}c)", "```", desc, "```", "",
        ]
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"pinterest-sprint-2.md: {n}/20 pins written; missing: {missing or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
