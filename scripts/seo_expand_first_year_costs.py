"""Expand thin first-year-costs articles with ~900 words of generic-
but-quality narrative content.

These articles were templated and came out at 140-500 words; the cost
line items alone do not rank well or serve users. We append four new
H2-led sections plus an expanded FAQ to the `sections.special.html`
content, inserted BEFORE the existing Related Reading block so the
internal links stay at the bottom of the rendered article.

Idempotent via marker WOOFFY_COSTS_EXPANSION_v1.

Usage:
    python3 scripts/seo_expand_first_year_costs.py            # CRITICAL only (<300 w)
    python3 scripts/seo_expand_first_year_costs.py --high     # CRITICAL + HIGH (<500 w)
    python3 scripts/seo_expand_first_year_costs.py --all-thin # <800 w
    python3 scripts/seo_expand_first_year_costs.py --slug X   # one article (testing)

After running, push to Shopify with:
    echo YES | python3 scripts/generate.py <slug1> <slug2> ... --update
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"

MARKER = "<!-- WOOFFY_COSTS_EXPANSION_v1 -->"
INTERNAL_LINKS_MARKER = "<!-- WOOFFY_INTERNAL_LINKS_v1 -->"

HTML_TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def wc(html: str) -> int:
    t = HTML_TAG.sub(" ", html or "")
    t = WS.sub(" ", t).strip()
    return len(t.split())


def breed_name_from_meta(meta: dict) -> str:
    """Derive 'Icelandic Sheepdog' from name 'Icelandic Sheepdog First Year Costs'."""
    name = (meta.get("name") or "").strip()
    g = (meta.get("group") or "").strip()
    if g and g not in ("Breed Guides", "Breed Name"):
        return g
    for suf in (" First Year Costs", " First-Year Costs"):
        if name.endswith(suf):
            return name[: -len(suf)].strip()
    return name


def build_expansion(breed: str) -> str:
    """Return ~930 words of generic-but-quality expansion HTML."""
    return f"""{MARKER}

<h2 style="margin-top:36px;">Where Your First-Year Budget Actually Goes</h2>
<p>Most first-time {breed} owners under-budget for veterinary care and over-budget for food. The line items above add up to a real number, but the proportions surprise most new owners:</p>
<ul>
<li><strong>Acquisition (puppy price or adoption fee): 35&ndash;55% of year one.</strong> The largest single line item, and the only one that does not repeat.</li>
<li><strong>Veterinary care and preventives: 15&ndash;25%.</strong> Puppy vaccinations, spay/neuter, microchip, first dental check, monthly heartworm and flea prevention.</li>
<li><strong>Food: 10&ndash;15%.</strong> Frequently overestimated. A 30&ndash;50 lb dog typically costs $30&ndash;$70 per month on a quality kibble.</li>
<li><strong>One-time setup (crate, leashes, bowls, beds, training): 10&ndash;20%.</strong> Largely paid in the first three months.</li>
<li><strong>Insurance, grooming, training classes: 5&ndash;15%.</strong> The flexible budget &mdash; spend more on whichever the breed or your situation requires.</li>
</ul>

<h2 style="margin-top:36px;">The Hidden Costs Most New Owners Don't Budget For</h2>
<p>The line items in a typical first-year cost article cover the predictable expenses. The unpredictable ones are what push some households over budget by 20&ndash;40 percent. Build a buffer for these:</p>
<ul>
<li><strong>One emergency vet visit ($300&ndash;$1,500+).</strong> The statistical likelihood that a first-year puppy needs at least one unscheduled vet visit is high &mdash; ingested objects, GI upset, minor injuries, ear infections. Plan as if at least one will happen.</li>
<li><strong>Training escalation if behavior problems emerge.</strong> A basic puppy class is $100&ndash;$200. A private trainer for reactive or anxious behavior runs $80&ndash;$200 per session and is often a 6&ndash;10 session program. Budget contingency: $500&ndash;$1,500.</li>
<li><strong>Boarding, daycare, or a dog walker.</strong> If you travel or work long days, $25&ndash;$60 per day adds up fast. A single one-week trip can be $300&ndash;$500.</li>
<li><strong>Pet deposits and pet rent.</strong> If you rent, expect a non-refundable pet deposit of $250&ndash;$500 plus monthly pet rent of $25&ndash;$75.</li>
<li><strong>Replaced household items.</strong> Chewed shoes, scratched doors, the rug. Most puppy households spend $200&ndash;$600 replacing things in year one.</li>
<li><strong>Prescription food or chronic-condition costs.</strong> If your {breed} develops a food allergy, skin condition, or anything chronic, prescription food and ongoing meds can run $50&ndash;$150 per month.</li>
</ul>

<h2 style="margin-top:36px;">Ways to Reduce First-Year Costs Without Cutting Corners</h2>
<p>Cost-cutting on a {breed} should never come at the expense of vet care, training, or quality of food. The places where smart owners legitimately save:</p>
<ol>
<li><strong>Adopt from a breed-specific rescue.</strong> National breed clubs maintain rescue networks. An adopted adult {breed} typically costs $250&ndash;$600 versus $1,500&ndash;$4,000+ from a breeder, and is often already spayed/neutered and up to date on vaccines.</li>
<li><strong>Group puppy class over private training.</strong> A group class at a positive-methods training club is $100&ndash;$200 for six weeks and covers most foundational obedience. Reserve private training for specific issues a group setting cannot address.</li>
<li><strong>Buy food in larger bags and store properly.</strong> A 30-pound bag of premium kibble is roughly 30 percent cheaper per pound than a 5-pound bag. Store in an airtight container in a cool dry place; quality kibble keeps 6 weeks once opened.</li>
<li><strong>Use prescription discount services for chronic meds.</strong> GoodRx Pet, Chewy Pharmacy, and Costco Pet Pharmacy frequently beat the vet's in-house pharmacy by 30&ndash;60 percent.</li>
<li><strong>Use wellness plans for routine, insurance for emergencies.</strong> Many clinics offer a $30&ndash;$50 per month wellness plan that bundles annual exams, vaccines, and dental cleanings. Separate emergency insurance kicks in for catastrophic costs.</li>
<li><strong>Compare three insurance quotes before enrolling.</strong> Premiums for the same coverage can vary 40 percent across companies. Read the exclusion list carefully &mdash; many policies exclude breed-typical hereditary conditions.</li>
</ol>

<h2 style="margin-top:36px;">Year Two and Beyond: How Costs Shift</h2>
<p>Year-one costs are atypical. Once your {breed} is past the puppy stage, the annual cost structure changes meaningfully:</p>
<ul>
<li><strong>One-time costs disappear.</strong> The puppy price, crate, bowls, initial vaccine series, spay/neuter, and most of the setup gear are paid for. Year two saves $1,500&ndash;$3,000 versus year one.</li>
<li><strong>Insurance premiums creep up.</strong> Expect a 3&ndash;8 percent premium increase per year, plus a larger bump at age 6&ndash;7 when the dog is reclassified as senior.</li>
<li><strong>Vet costs decline through middle age, then rise.</strong> Years 2&ndash;6 are typically the cheapest medically. Year 7+ frequently brings senior bloodwork, dental cleanings, and emerging chronic conditions.</li>
<li><strong>Food costs are roughly flat.</strong> Adult kibble is similarly priced to puppy kibble.</li>
<li><strong>Training continues but at lower intensity.</strong> Maintenance training and the occasional reactivity tune-up replace the foundational classes.</li>
</ul>
<p>A realistic lifetime budget for a medium-sized breed including the {breed} is $20,000&ndash;$30,000 over a 12&ndash;14 year lifespan, with year one being roughly 15&ndash;20 percent of the total.</p>

<h2 style="margin-top:36px;">Frequently Asked Questions</h2>
<h3>Is pet insurance worth it for a {breed}?</h3>
<p>For most owners, yes &mdash; particularly when enrolled while the dog is young and healthy. Insurance is most valuable as catastrophic coverage for the one big emergency that would otherwise force a hard decision between treatment and finance. Compare three insurers, read the hereditary-condition exclusion list, and choose a policy that covers the breed's known issues. Wellness plans are a separate decision; many owners pair a wellness plan from the clinic with emergency insurance from a third party.</p>
<h3>What is the cheapest year of {breed} ownership?</h3>
<p>Years 3 through 6 are typically the cheapest. The puppy expenses are done, the dog is past the chewing and accident-prone phase, and senior costs have not yet started. Expect roughly $1,400&ndash;$2,800 in annual ongoing costs during these middle years.</p>
<h3>How much should I keep in an emergency fund for my {breed}?</h3>
<p>Most veterinary financial advisers recommend $1,500&ndash;$3,000 in a dedicated pet emergency fund, in addition to insurance. The two cover different risks: insurance pays the catastrophic bill, the emergency fund covers the deductible and the upfront payment most clinics require before treatment begins.</p>
<h3>Can I budget for a {breed} on a fixed income?</h3>
<p>Yes, but plan honestly. The average monthly cost of an adult medium-breed dog (food, preventives, insurance, miscellaneous) is roughly $80&ndash;$160 outside of one-time annual costs. Add a $50&ndash;$80 monthly buffer for vet and emergencies. If $130&ndash;$240 monthly is uncomfortable on your budget, consider whether a more compact, lower-maintenance breed or adoption of an adult dog with a known history would serve better.</p>
<h3>Why are first-year costs so much higher than later years?</h3>
<p>Three reasons. First, the acquisition cost &mdash; whether breeder price or adoption fee &mdash; is paid only once. Second, the puppy vaccine series, spay/neuter surgery, and microchip are all year-one items. Third, the one-time setup (crate, beds, bowls, leashes, baby gates, training classes) is concentrated in the first three months. Once these are paid, ongoing annual costs settle into a much lower steady state.</p>
"""


def expand_one(path: Path) -> tuple[bool, str, int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data.get("meta") or {}
    sections = data.get("sections") or {}
    special = sections.get("special") or {}
    html = special.get("html") or ""
    if not html:
        return (False, "no sections.special.html", 0, 0)
    if MARKER in html:
        return (False, "already expanded", wc(html), wc(html))

    breed = breed_name_from_meta(meta)
    if not breed:
        return (False, "no breed name", 0, 0)

    expansion = build_expansion(breed)
    old_wc = wc(html)

    if INTERNAL_LINKS_MARKER in html:
        new_html = html.replace(
            INTERNAL_LINKS_MARKER,
            expansion + "\n" + INTERNAL_LINKS_MARKER,
            1,
        )
    else:
        new_html = html.rstrip() + "\n\n" + expansion

    new_wc = wc(new_html)
    special["html"] = new_html
    sections["special"] = special
    data["sections"] = sections

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n",
    )
    return (True, "expanded", old_wc, new_wc)


def collect_targets(mode: str, slug: str | None) -> list[Path]:
    if slug:
        return [BREED_DATA / f"{slug}.json"]
    out: list[Path] = []
    for path in sorted(BREED_DATA.glob("*-first-year-costs.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        sections = data.get("sections") or {}
        total = sum(wc((s or {}).get("html") or "") for s in sections.values()
                    if isinstance(s, dict))
        total += wc(data.get("body_html") or "")
        if mode == "critical" and total < 300:
            out.append(path)
        elif mode == "high" and total < 500:
            out.append(path)
        elif mode == "all-thin" and total < 800:
            out.append(path)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--high", action="store_true", help="<500 words")
    g.add_argument("--all-thin", action="store_true", help="<800 words")
    g.add_argument("--slug", help="single slug to expand (no .json)")
    args = ap.parse_args()

    if args.slug:
        mode = "slug"
    elif args.all_thin:
        mode = "all-thin"
    elif args.high:
        mode = "high"
    else:
        mode = "critical"

    targets = collect_targets(mode, args.slug)
    print(f"Mode: {mode}  Targets: {len(targets)}", file=sys.stderr)

    changed, skipped = [], []
    for path in targets:
        try:
            ok, msg, old, new = expand_one(path)
        except Exception as e:
            print(f"[{path.stem}] ERROR: {e}", file=sys.stderr)
            skipped.append((path.stem, str(e)))
            continue
        if ok:
            print(f"  EXPAND  {path.stem:55s}  {old} -> {new} words")
            changed.append(path.stem)
        else:
            print(f"  skip    {path.stem:55s}  {msg}")
            skipped.append((path.stem, msg))

    print(f"\nChanged: {len(changed)}  Skipped: {len(skipped)}", file=sys.stderr)
    if changed:
        print("\nSlugs to push:", file=sys.stderr)
        print(" ".join(changed))
    return 0 if changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
