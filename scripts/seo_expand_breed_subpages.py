"""Expand thin breed sub-pages: grooming-guide and puppy-checklist
articles that came out of the templated generator at 300-500 words.

Two expansion templates, selected by slug suffix:
  - *-grooming-guide  -> Grooming-specific expansion (~900 words)
  - *-puppy-checklist -> First-90-days expansion (~900 words)

Idempotent via marker WOOFFY_SUBPAGE_EXPANSION_v1.

Usage:
    python3 scripts/seo_expand_breed_subpages.py            # thin (<500 w)
    python3 scripts/seo_expand_breed_subpages.py --all-thin # <800 w
    python3 scripts/seo_expand_breed_subpages.py --slug X   # single (testing)

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

MARKER = "<!-- WOOFFY_SUBPAGE_EXPANSION_v1 -->"
INTERNAL_LINKS_MARKER = "<!-- WOOFFY_INTERNAL_LINKS_v1 -->"

HTML_TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def wc(html: str) -> int:
    t = HTML_TAG.sub(" ", html or "")
    t = WS.sub(" ", t).strip()
    return len(t.split())


def breed_name_from_meta(meta: dict, slug: str) -> str:
    """Derive 'Beagle' from name 'Beagle Grooming Guide' or 'Beagle Puppy Checklist'."""
    g = (meta.get("group") or "").strip()
    if g and g not in ("Breed Guides", "Breed Name"):
        return g
    name = (meta.get("name") or "").strip()
    for suf in (
        " Grooming Guide: Coat Care & Trim Schedule",
        " Grooming Guide: Coat Care & Trim",
        " Grooming Guide: Curly Coat Care",
        " Grooming Guide",
        " Puppy Checklist: First 90 Days at Home",
        " Puppy Checklist: First 90 Days",
        " Puppy Checklist: 90 Days",
        " Puppy Checklist",
    ):
        if name.endswith(suf):
            return name[: -len(suf)].strip()
    # Fallback: strip the slug-derived suffix
    short = slug
    for suf in ("-grooming-guide", "-puppy-checklist"):
        if short.endswith(suf):
            short = short[: -len(suf)]
            break
    return " ".join(w.capitalize() for w in short.split("-"))


def build_grooming_expansion(breed: str) -> str:
    return f"""{MARKER}

<h2 style="margin-top:36px;">How to Read Your {breed}'s Coat Type</h2>
<p>Coat type drives every grooming decision &mdash; how often to brush, which tools to use, whether to bathe weekly or monthly, and how often a professional groomer needs to be involved. The {breed}'s coat falls into one of four broad categories, each with its own routine:</p>
<ul>
<li><strong>Single-coat smooth or short.</strong> One layer of hair, minimal undercoat. Sheds year-round at a steady rate but rarely "blows" coat. Easy to maintain at home with a rubber curry brush.</li>
<li><strong>Double-coat (most spitz and northern breeds).</strong> Soft dense undercoat under a longer guard-hair outer layer. Sheds heavily twice a year &mdash; spring and fall &mdash; in week-long "coat blow" events. Requires an undercoat rake or de-shedding tool during these periods.</li>
<li><strong>Wiry or broken-coat (most terriers).</strong> Coarse outer hair with a softer undercoat. The wire texture is maintained by either <em>hand-stripping</em> (preserves color and texture) or clipping (faster and cheaper but softens the coat over time).</li>
<li><strong>Curly or wool coat (Poodles, Bichons, doodles).</strong> Continuously growing hair that does not shed in a typical way. Requires the most frequent professional grooming &mdash; a full groom every 4&ndash;8 weeks &mdash; and daily brushing to prevent mats.</li>
</ul>

<h2 style="margin-top:36px;">The Weekly Home Grooming Routine</h2>
<p>Even breeds that visit a professional groomer regularly need home care between appointments. A realistic weekly routine for the {breed} covers five tasks:</p>
<ol>
<li><strong>Brushing (1&ndash;7 times per week depending on coat type).</strong> Choose the right tool: bristle brush for short coats, slicker brush for medium and long coats, undercoat rake for double coats, pin brush for silky coats. Brush in the direction of hair growth and section the coat for thorough coverage.</li>
<li><strong>Nail trim (every 2&ndash;4 weeks).</strong> Nails should not touch the floor when the dog is standing. Use a guillotine clipper or a Dremel-style grinder. Stop short of the quick (the pink interior of the nail) to avoid bleeding.</li>
<li><strong>Ear check and clean (weekly for drop-ear breeds, monthly for prick-ear breeds).</strong> Use a veterinary ear cleaner, never water or alcohol. Wipe gently with cotton; never insert a swab into the ear canal.</li>
<li><strong>Tooth brushing (3+ times per week).</strong> Use enzymatic toothpaste designed for dogs. Periodontal disease affects more than 80 percent of dogs over 3 years old; home brushing is the single most cost-effective preventive measure.</li>
<li><strong>Paw and skin check (weekly).</strong> Look between toes for embedded grass seeds, check pad condition, look for hot spots, lumps, or fleas. The grooming session is the most efficient time to catch skin issues early.</li>
</ol>

<h2 style="margin-top:36px;">Professional Grooming: What It Costs and How Often</h2>
<p>Professional grooming costs vary considerably by coat type, breed size, and geographic market. For the {breed}, typical price ranges and visit frequencies:</p>
<ul>
<li><strong>Bath and blowout (short or smooth coat):</strong> $35&ndash;$65, every 4&ndash;8 weeks if used at all. Most owners with short-coat breeds do this at home.</li>
<li><strong>Standard full groom (medium-coat or double-coat):</strong> $55&ndash;$95, every 6&ndash;10 weeks. Includes bath, blow-dry, brush-out, nail trim, ear cleaning, and minor trimming.</li>
<li><strong>Breed-specific or hand-stripping (terriers, show coats):</strong> $80&ndash;$150, every 8&ndash;12 weeks. The premium reflects expertise and time required.</li>
<li><strong>Continuously-growing or curly coat full groom:</strong> $70&ndash;$130, every 4&ndash;8 weeks. Doodles, poodles, and bichons are at the high end of frequency.</li>
</ul>
<p>What to look for in a groomer: experience with the {breed} specifically, willingness to use a quiet drying area instead of cage dryers, certification from the National Dog Groomers Association of America (NDGAA) or similar, and a clear contract on what is and is not included in the quoted price. Avoid groomers who decline to let you tour the back of the shop.</p>

<h2 style="margin-top:36px;">Common Grooming Mistakes That Cause Skin Problems</h2>
<ul>
<li><strong>Over-bathing.</strong> Most dogs do not need a bath more than once a month. Frequent washing strips the natural oils that protect the skin barrier, causing dryness, itching, and sometimes secondary infections.</li>
<li><strong>Human shampoo on dog skin.</strong> Human skin pH is around 5.5; dog skin pH is closer to 7. Human shampoo is too acidic and disrupts the canine skin barrier. Always use a dog-specific shampoo.</li>
<li><strong>Misusing the undercoat rake or Furminator.</strong> These tools cut hair, not just remove loose hair. Over-aggressive use on a single-coat breed strips the protective topcoat. Use only on double-coated breeds and only during shedding seasons.</li>
<li><strong>Missing mats until they tighten against the skin.</strong> A small mat is easy to brush out; a mat that has tightened against the skin can only be safely removed by shaving the entire area. Severe mats are a welfare issue and can hide skin infections, hot spots, or even maggot infestations in summer.</li>
<li><strong>Skipping ear care after swims.</strong> Water trapped in the ear canal is the leading cause of ear infections in dogs that swim. Flush with an ear-drying solution after every swim or bath.</li>
</ul>

<h2 style="margin-top:36px;">Seasonal Coat Changes</h2>
<p>Most double-coated breeds blow their undercoat twice a year &mdash; once in spring as the heavy winter coat is shed for a lighter summer coat, and once in fall as the heavier winter coat grows in. During these 2&ndash;4 week periods, expect <strong>three to four times the normal amount of loose hair</strong> and daily brushing requirements. Single-coat breeds shed at a steady year-round rate without the dramatic seasonal events. Hot months may also produce slightly more shedding regardless of coat type as the body sheds extra insulation.</p>

<h2 style="margin-top:36px;">Frequently Asked Questions</h2>
<h3>How often should I bathe my {breed}?</h3>
<p>For most coat types, once every 4 to 8 weeks is appropriate. Working breeds in dirty conditions or breeds with skin allergies may need a medicated bath weekly under veterinary guidance. Healthy dogs without skin issues should not be bathed more than monthly &mdash; the natural skin oils are protective.</p>
<h3>Is it cheaper to groom my {breed} at home?</h3>
<p>Yes, for the equipment-amortized cost. A starter home grooming kit (slicker brush, nail grinder, ear cleaner, dog-specific shampoo, towels) is $80&ndash;$150 and lasts years. Per-session this is far cheaper than a $70&ndash;$130 professional groom every 6&ndash;8 weeks. The time tradeoff is real: a thorough home groom of a medium-coat dog takes 60&ndash;90 minutes.</p>
<h3>What if my {breed} hates being groomed?</h3>
<p>Most grooming aversion comes from one or more bad early experiences. Reintroduce grooming gradually using positive reinforcement: a few seconds of brushing followed by a high-value treat, daily, building up duration over weeks. For severe aversion, a fear-free certified groomer or a veterinary behaviorist can help.</p>
<h3>Should I let a groomer shave my {breed} in summer?</h3>
<p>Almost never. A double-coated dog's coat insulates against heat as well as cold; shaving removes that insulation and exposes skin to sunburn. The undercoat may not grow back evenly. The correct hot-weather management is regular brushing to remove loose undercoat and provision of shade and water &mdash; not shaving.</p>
<h3>How do I find a good groomer for my {breed}?</h3>
<p>Ask a breed-specific Facebook group or your veterinarian for a referral. NDGAA certification is a useful but not required signal. Visit the shop before booking, ask about drying methods (cage dryers can cause heat injury in brachycephalic and double-coated dogs), and request the groomer who has the most experience with your specific breed.</p>
"""


def build_checklist_expansion(breed: str) -> str:
    return f"""{MARKER}

<h2 style="margin-top:36px;">The First 48 Hours at Home</h2>
<p>The first two days set the tone for the next year. Most new {breed} owners do too much too fast: large welcome parties, exposure to strangers, an unrestricted run of the house. The puppy's nervous system is still adjusting to the loss of its littermates and the introduction of an entirely new environment. Slow is the right pace.</p>
<ul>
<li><strong>Designate one quiet room.</strong> The first day or two, restrict the puppy to a single room with the crate, a water bowl, and a few toys. Visitors should sit on the floor and let the puppy approach on its own terms.</li>
<li><strong>Crate introduction begins immediately.</strong> Place the open crate in the room with a soft blanket and a high-value chew. Most puppies will explore it within an hour. Do not force the puppy in; let it choose to enter.</li>
<li><strong>First meal at the right time.</strong> Feed the same food brand and amount the breeder or shelter was feeding for at least the first week. Sudden diet changes are a common cause of stress diarrhea.</li>
<li><strong>Schedule the first vet appointment.</strong> Most contracts require a vet visit within 72 hours; the appointment also serves as a baseline weight, health check, and review of the vaccination schedule.</li>
<li><strong>Decide on potty location and bring the puppy there frequently.</strong> A puppy needs to potty after every meal, every nap, every play session, and every 1&ndash;2 hours during waking hours. Take the puppy to the same spot every time.</li>
</ul>

<h2 style="margin-top:36px;">The First Week: Sleep, Feeding, and Potty Schedule</h2>
<p>Most new owners are exhausted by day four because they underestimate how often a young puppy wakes and needs attention. A realistic schedule for a {breed} puppy under 12 weeks:</p>
<ul>
<li><strong>Feeding:</strong> 3&ndash;4 meals per day for puppies under 4 months, dropping to 3 meals at 4&ndash;6 months and 2 meals at 6 months. Measured portions, same times each day.</li>
<li><strong>Sleep:</strong> 18&ndash;20 hours per day. Sleep should be uninterrupted; do not wake a sleeping puppy.</li>
<li><strong>Potty trips:</strong> immediately on waking, after every meal, after every play session, before bed, and every 1&ndash;2 hours otherwise. Puppies under 12 weeks usually need one or two overnight trips.</li>
<li><strong>Crate at night:</strong> in the bedroom for the first 2&ndash;4 weeks. The puppy sleeps better near a familiar smell, and you can hear it cue for a potty break before an accident.</li>
<li><strong>Play and training sessions:</strong> 3&ndash;5 short sessions per day, 5 minutes each. Puppies have short attention spans; many short sessions outperform one long session.</li>
</ul>
<p>Accidents in the first week are normal and not a sign of failure. Clean with an enzymatic cleaner (Nature's Miracle, Anti-Icky-Poo) &mdash; not a household cleaner &mdash; to fully eliminate the scent that draws the puppy back.</p>

<h2 style="margin-top:36px;">The First 30 Days: Vet, Vaccines, and the Socialization Window</h2>
<p>The socialization critical period for puppies runs from approximately 3 to 14 weeks of age. Experiences during this window shape lifelong behavioral patterns; missed socialization windows are difficult and sometimes impossible to fully recover. By the end of the first 30 days, your {breed} should have had positive (puppy-led, treat-reinforced) exposure to:</p>
<ul>
<li><strong>10+ different people:</strong> men, women, children, hats, glasses, different ethnicities, different gaits.</li>
<li><strong>5+ different surfaces:</strong> grass, gravel, hardwood, tile, sand, metal grate, slippery vinyl.</li>
<li><strong>3+ different environments:</strong> car rides to pet-friendly stores, vet office (for treats, not just appointments), friends' homes.</li>
<li><strong>5+ household sounds:</strong> vacuum, blender, doorbell, sirens (use a recording at low volume), dropped pans.</li>
<li><strong>Other vaccinated, friendly adult dogs:</strong> not all puppies &mdash; puppy social groups vary in quality. Limit early exposure to known healthy adult dogs.</li>
</ul>
<p>First-round vaccinations (DHPP, sometimes Bordetella) typically begin at 6&ndash;8 weeks and continue every 3&ndash;4 weeks until 16 weeks. The rabies vaccine is added at 12&ndash;16 weeks. Heartworm prevention starts around 8 weeks.</p>

<h2 style="margin-top:36px;">Setup Mistakes That Cost the Most to Fix Later</h2>
<ul>
<li><strong>Free-roaming the house too early.</strong> A puppy with unsupervised access to a large area will potty in unobserved corners, chew valuable items, and develop bad habits faster than you can correct them. Use baby gates and ex-pens.</li>
<li><strong>Inconsistent crate use.</strong> The crate should be the puppy's safe space, used positively, not as punishment. A puppy that has had even one bad crate experience (left too long, locked in when scared) will resist the crate for months.</li>
<li><strong>Skipping leash training in the yard.</strong> Walks on a leash require a foundation that most puppies do not have by default. Start in the yard with no distractions, then move to the sidewalk only after the puppy is responsive on leash indoors.</li>
<li><strong>Ignoring early resource guarding signals.</strong> A puppy that stiffens or growls when you reach for its food or toys is communicating an early-stage concern. Address with hand-feeding and the "trade up" game, not with punishment, which escalates the behavior.</li>
<li><strong>Postponing professional training to "when the puppy is older."</strong> Foundational training is most effective during the 8&ndash;16 week window. A good puppy class started before 4 months of age pays for itself many times over in adult behavior.</li>
</ul>

<h2 style="margin-top:36px;">What to Expect at 3, 6, and 12 Months</h2>
<ul>
<li><strong>3 months:</strong> Most puppies have completed primary vaccinations and can begin attending puppy classes. Reliable potty training is in progress but rarely complete. Sleep is consolidating to 14&ndash;16 hours per day.</li>
<li><strong>6 months:</strong> Adolescence begins. Expect a regression in previously learned behaviors and a sudden interest in chewing furniture. Spay or neuter is often discussed (timing varies by breed and veterinarian). Feeding drops to 2 meals per day.</li>
<li><strong>12 months:</strong> Most small breeds are fully grown; medium and large breeds will continue growing for another 6&ndash;12 months. Hyperactivity peaks for many breeds at 12&ndash;18 months before settling. Adult food is appropriate at this point.</li>
</ul>

<h2 style="margin-top:36px;">Frequently Asked Questions</h2>
<h3>How long until my {breed} is fully potty trained?</h3>
<p>Most puppies are reliably potty-trained between 4 and 8 months of age, with full reliability (no accidents in unfamiliar environments) by 12 months. Small breeds and breeds with small bladders sometimes take longer.</p>
<h3>Should I let my {breed} sleep in bed with me?</h3>
<p>Personal preference, but with one caveat: a young puppy that begins sleeping in your bed will not transition easily to its own bed later. Start where you want to end up. Most trainers recommend the crate in the bedroom for the first few months, then transitioning to whatever long-term arrangement you prefer.</p>
<h3>When can my puppy go to the dog park?</h3>
<p>Wait until at least two weeks after the final puppy vaccine (typically 18&ndash;20 weeks). Even then, dog parks are not the right socialization environment for most young puppies &mdash; the dogs are unfamiliar, behaviors are unpredictable, and a single bad encounter can shape lifelong reactivity. Controlled puppy classes and known adult dogs are safer.</p>
<h3>What should I feed my {breed} puppy?</h3>
<p>A complete and balanced puppy food formulated for the appropriate size category (small, medium, large breed). Large- and giant-breed puppies should be fed a breed-size-specific food because the calcium-phosphorus ratio is critical for proper bone development. Continue with the breeder's food for the first week, then transition gradually over 7&ndash;10 days.</p>
<h3>Can I take my puppy outside before all vaccinations are complete?</h3>
<p>Yes &mdash; and modern veterinary guidance increasingly emphasizes that the risk of under-socialization outweighs the risk of disease exposure for most healthy puppies in non-high-risk environments. The American Veterinary Society of Animal Behavior (AVSAB) explicitly recommends socialization before vaccine completion in controlled environments (carry the puppy, choose clean spaces, avoid dog parks and unknown dogs).</p>
"""


def expand_one(path: Path) -> tuple[bool, str, int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data.get("meta") or {}
    slug = (meta.get("slug") or path.stem).lower()
    sections = data.get("sections") or {}
    special = sections.get("special") or {}
    html = special.get("html") or ""
    if not html:
        return (False, "no sections.special.html", 0, 0)
    if MARKER in html:
        return (False, "already expanded", wc(html), wc(html))

    breed = breed_name_from_meta(meta, slug)
    if not breed:
        return (False, "no breed name", 0, 0)

    if slug.endswith("-grooming-guide"):
        expansion = build_grooming_expansion(breed)
    elif slug.endswith("-puppy-checklist"):
        expansion = build_checklist_expansion(breed)
    else:
        return (False, f"unsupported slug suffix: {slug}", 0, 0)

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


def collect_targets(threshold: int, slug: str | None) -> list[Path]:
    if slug:
        return [BREED_DATA / f"{slug}.json"]
    out: list[Path] = []
    for pattern in ("*-grooming-guide.json", "*-puppy-checklist.json"):
        for path in sorted(BREED_DATA.glob(pattern)):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            sections = data.get("sections") or {}
            total = sum(
                wc((s or {}).get("html") or "")
                for s in sections.values() if isinstance(s, dict)
            )
            total += wc(data.get("body_html") or "")
            if total < threshold:
                out.append(path)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--all-thin", action="store_true", help="<800 words")
    g.add_argument("--slug", help="single slug to expand (no .json)")
    args = ap.parse_args()

    if args.slug:
        threshold = 9999
    elif args.all_thin:
        threshold = 800
    else:
        threshold = 500

    targets = collect_targets(threshold, args.slug)
    print(f"Threshold: <{threshold}  Targets: {len(targets)}", file=sys.stderr)

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
