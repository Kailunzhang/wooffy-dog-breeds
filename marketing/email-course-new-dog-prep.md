# Wooffy "New Dog Prep" Email Course (4 emails)

Status: draft for owner review. Nothing has been sent and Shopify has not been changed.
Written 2026-10-09 for Wooffy (thewooffy.com), from Mike & Alice (and Tank). Revised the same day after verification: Shopify Flow setup, 2-week timing, and three wording fixes.

---

## Setup (recommended: a Shopify Flow workflow)

Build the course as a custom workflow in the Shopify Flow app. Shopify Messaging's own automations come from pre-built templates, and its only welcome templates ("Welcome new subscribers with a discount email" and "Welcome new subscribers with a discount series") include a discount, which this course doesn't offer. Shopify's help center says to build custom automations in Flow.

```
Trigger    Customer tags added
Condition  Tags contains wooffy-quiz   OR   Tags contains wooffy-calc
   AND     Customer > Email marketing consent > Marketing state is SUBSCRIBED
Then       Send Marketing Email   -> Email 1   (day 0)
           Wait 3 days
           Send Marketing Email   -> Email 2   (day 3)
           Wait 5 days
           Send Marketing Email   -> Email 3   (day 8)
           Wait 6 days
           Send Marketing Email   -> Email 4   (day 14)
```

| Setting | Value |
|---|---|
| Trigger | **Customer tags added**. It starts a workflow when one or more tags are added to a customer. |
| Tag condition | Tags contain `wooffy-quiz` **OR** tags contain `wooffy-calc`. Use the trigger's own **Tags** field, which lists only the tags just added. If you test the customer's full tag list instead, any later tag on a past signup (for example a new `breed-` tag from a second visit) would start the course again. |
| Consent condition (AND) | The customer's email marketing consent state is `SUBSCRIBED`. |
| Email action | **Send Marketing Email**, from the Shopify Messaging connector in Flow. Shopify describes it as sending "an email message to customers subscribed to email marketing" using a Shopify Messaging email template. Use one action per email, four in all. |
| Timing | Email 1 right away, then waits of 3, 5 and 6 days. The emails land on days 0, 3, 8 and 14, which matches the forms' "2-week" promise. |
| Who gets it | People who signed up on the breed quiz (tag `wooffy-quiz`) or the first-year cost calculator (tag `wooffy-calc`). Most are choosing their first dog. The forms also add `newsletter` and, when a breed is known, `breed-<slug>`. |
| Reply-to | An inbox you read. Every P.S. asks people to reply, and the site already lists wooffy@thewooffy.com. |
| Greeting | "Hi there," (see the note below) |

**Why Flow and this trigger.** The form adds the tag every time someone signs up, so the course also reaches people who were already subscribed from the footer or checkout. Those people never fire "Customer subscribed to email marketing" again, so a subscribe-triggered automation would skip them.

**Don't add an "Add customer tags" action to this workflow.** Shopify warns that using it with the Customer tags added trigger makes the workflow run forever and might get your workflows throttled.

**Someone who uses both tools gets the course twice**, because their second signup adds a new tag (`wooffy-calc` after `wooffy-quiz`, or the other way round). To prevent that, put a second condition step right after the first: Customer > Tags does not contain `wooffy-quiz` **OR** Customer > Tags does not contain `wooffy-calc`. It only passes while a customer has one of the two tags. Check it in the live test, since it relies on the customer's tags already including the one just added.

**Alternative: a Shopify Messaging template.** Start from "Welcome new subscribers with a discount series", open Edit workflow, and delete the discount and reminder steps. This route has three catches:
- The help center doesn't say whether you can add a tag condition or a fourth email, so check both in the admin before you build it.
- Its trigger, "Customer subscribed to email marketing", skips people who were already subscribed.
- A live test has to confirm the `wooffy-` tags are already on the customer when that trigger fires. Otherwise the tag condition never matches.

**Avoid a double welcome.** Most signups on these forms are new email subscribers, so any welcome automation that's already on (check Marketing > Automations) sends to them as well as this course. Either turn that automation off, or give it a condition that skips customers tagged `wooffy-quiz` or `wooffy-calc`. That exclusion only works if the tags are already there when it fires, so check it in the live test.

**Greeting note.** I ran three searches of the Shopify developer docs (Shopify MCP `search_docs_chunks`) for Shopify Messaging personalization or Liquid variables such as `{{ customer.first_name }}`. None of them turned up any Shopify Messaging docs. The results only covered checkout and customer-account UI extensions. So these emails use "Hi there," and no merge tag. Both signup forms also collect only an email address, so a first-name tag would come out blank for nearly everyone.

**How to paste.** Linked words look like `[text](URL)`. Paste the text into the editor, then add each URL to its words. `[BUTTON]` marks where the primary button goes. Keep Shopify Messaging's standard footer on. It handles the unsubscribe link and the store address.

**Rules these emails follow.** They link only to live Wooffy pages (see the link table at the end). They contain no Amazon or affiliate links, no discounts and no vet-endorsement claims. Every fact or number comes from the page it links to.

### Live test before you rely on it

Both forms now post to Shopify's customer form at `/contact` with hidden tags (`newsletter`, `wooffy-quiz` or `wooffy-calc`, plus `breed-<slug>` when known). Work through this list in order once the updated quiz and calculator pages are live.

1. **Form copy matches this course.** Both forms should read "Free 2-week New Dog Prep email course" and "Choosing a breeder or rescue, the first-week shopping list and routine, and real first-year costs." No "3-week" and no "training basics": none of these emails covers training.
2. **No double welcome.** In Marketing > Automations, check whether a welcome automation is already on. If one is, turn it off or exclude the `wooffy-quiz` and `wooffy-calc` tags from it (see "Avoid a double welcome" above).
3. **Build and turn on the Flow workflow.** Paste the four emails, check every button and link, then turn the workflow on. Flow only runs workflows that are on, so steps 4 to 8 need it on.
4. **One real signup per page.** Use an address you control that isn't a customer yet, once on the live quiz and once on the live calculator (a second address, or a `+` alias). After Shopify sends you back, the thank-you message should show.
5. **Spam protection is attached.** In the browser's DevTools Network tab, open the POST to `/contact` and check its form data includes `h-captcha-response`. If it's missing on either page, fix that before go-live.
6. **Customer record.** In Customers, each test customer should show email marketing as Subscribed and carry `newsletter`, `wooffy-quiz` or `wooffy-calc`, and the `breed-` tag if a breed was chosen. If consent shows Pending (double opt-in), the consent condition will skip that person, so sort that out before go-live.
7. **The workflow ran.** In the workflow's run history, each signup should show a run. Email 1 should arrive and the run should be waiting 3 days. If a brand-new customer produced no run, the trigger isn't firing for form signups; stop and recheck before going further.
8. **An address that already exists.** Sign up with a third address that's already a subscribed customer (for example, one that joined through the footer form). Check that the `wooffy-` tag was added, a run started and Email 1 arrived. Also sign the same address up a second time on the same tool: no second run should start. If you added the both-tools guard, sign the quiz address up on the calculator too: no second run.
9. **Leave it on and watch.** Check the first real runs over the next two weeks, and confirm Email 4 goes out on day 14.

**Note on linked pages.** The emails themselves have no Amazon or affiliate links. But two pages they link to carry Amazon affiliate links with disclosures: the Golden Retriever puppy checklist (Email 3's button) and the Labrador Retriever puppy checklist (in Email 3's body), each with 6. The other linked pages, including the Labrador cost guide, have none.

---

## Email 1: Welcome, and how to use your results

- **Send:** immediately
- **Subject:** Your dog shortlist: what to do next
- **Preview text:** Three breeds, four checks, and why meeting the dogs matters most.
- **Primary button:** Find your breeds in the A–Z → https://thewooffy.com/blogs/dog-breeds/dog-breeds-a-z
- **Secondary links (in body):**
  - Take the breed quiz → https://thewooffy.com/pages/dog-breed-quiz
  - cost calculator → https://thewooffy.com/pages/dog-cost-calculator
  - How to choose a breed: the 6 factors that matter → https://thewooffy.com/blogs/dog-breeds/choosing-the-perfect-dog-breed-factors-to-consider-before-bringing-a-new-companion-home

**Body:**

Hi there,

Thanks for trying the Wooffy breed quiz or cost calculator. We're Mike and Alice, and we run Wooffy with our dog, Tank. Over the next two weeks we'll send three more short emails: breeder vs. rescue, your first week at home, and what the first year really costs.

Today, let's turn your results into a real shortlist.

**1. Pick three breeds.** Not ten. Three is enough to compare honestly. Still deciding? [Take the breed quiz](https://thewooffy.com/pages/dog-breed-quiz). It takes about two minutes.

**2. Read each breed's full guide.** Go straight to the "Right for You?" section. That's where the trade-offs are: exercise, time alone, grooming and barking.

**3. Price all three.** Run each one through the [cost calculator](https://thewooffy.com/pages/dog-cost-calculator). Coat alone can move the total, since curly, low-shedding coats need a professional groom every 6–8 weeks.

**4. Meet the dogs.** Before you decide, spend time with adult dogs of each breed through owners you know, breed clubs, or shelters and rescues. The dog in front of you tells you more than any list, ours included.

Want the bigger picture first? Read [How to choose a breed: the 6 factors that matter](https://thewooffy.com/blogs/dog-breeds/choosing-the-perfect-dog-breed-factors-to-consider-before-bringing-a-new-companion-home).

[BUTTON] Find your breeds in the A–Z

Talk soon,
Mike & Alice (and Tank)
Wooffy

P.S. Hit reply and tell us which breeds made your shortlist — we read every email.

---

## Email 2: Breeder vs. rescue, and how to spot a bad seller

- **Send:** day 3 (3 days after Email 1)
- **Subject:** Breeder or rescue? How to tell who's legit
- **Preview text:** Both can be great choices. The real risk is a seller you can't check.
- **Primary button:** Adopt or buy? Compare both → https://thewooffy.com/blogs/dog-breeds/adopt-or-shop-dog
- **Secondary links (in body):**
  - How to find a responsible breeder → https://thewooffy.com/blogs/dog-breeds/how-to-find-a-responsible-breeder
  - Puppy scams: how to spot a fake seller → https://thewooffy.com/blogs/dog-breeds/puppy-scams
  - mixed-breed dog guide → https://thewooffy.com/blogs/dog-breeds/mixed-breed-dogs

**Body:**

Hi there,

Once you have a shortlist, the next question is where your dog comes from. Our honest take: adopting and buying from a breeder can both be responsible choices. The bigger risk is a source you can't check.

**A responsible breeder:**
- health-tests both parents and gives you their registered names, so you can check the results on ofa.org
- lets you meet the mother where the puppies are raised
- asks you as many questions as you ask them
- puts a return-to-breeder clause in a written contract

**Adopting?** Ask why the dog is there, for its vet records, how it does with kids, other pets and strangers, and whether they'll take it back if things don't work out. Our [mixed-breed dog guide](https://thewooffy.com/blogs/dog-breeds/mixed-breed-dogs) explains why shelter breed labels often get it wrong.

**Walk away if:**
- the price is far below the breed's usual range
- you can't visit, or do a live video call that you direct
- they push for a deposit before you can read the contract, or their first question is how soon you can pay
- they only take Zelle, payment apps, gift cards, wires or crypto
- new "shipping," "crate" or "insurance" fees appear after you pay

Get deposit terms in writing, and pay in a way you can dispute, like a credit card.

More: [How to find a responsible breeder](https://thewooffy.com/blogs/dog-breeds/how-to-find-a-responsible-breeder) and [Puppy scams: how to spot a fake seller](https://thewooffy.com/blogs/dog-breeds/puppy-scams).

[BUTTON] Adopt or buy? Compare both

Mike & Alice (and Tank)
Wooffy

P.S. Hit reply and tell us which breeds made your shortlist — we read every email.

---

## Email 3: The first week (what to buy, puppy-proofing, first vet visit)

- **Send:** day 8 (5 days after Email 2)
- **Subject:** Before day one: your new-dog checklist
- **Preview text:** What to buy, what to move out of reach, and when to book the first vet visit.
- **Primary button:** See a full puppy checklist → https://thewooffy.com/blogs/dog-breeds/golden-retriever-puppy-checklist
- **Secondary links (in body):**
  - A–Z breed directory → https://thewooffy.com/blogs/dog-breeds/dog-breeds-a-z
  - Crate Training 101 → https://thewooffy.com/blogs/dog-training/crate-training
  - Labrador Retriever checklist → https://thewooffy.com/blogs/dog-breeds/labrador-retriever-puppy-checklist

**Body:**

Hi there,

Whether your dog comes home next week or next spring, a calm first week starts before pickup day. Here's what our puppy checklists come back to again and again.

**Have ready before day one:**
- a crate (with a divider if your puppy will grow a lot) and a bed
- bowls, plus the food your breeder or shelter has been using. Switch slowly later, over 7–10 days.
- a collar, a 6-foot leash, and an ID tag with your phone number
- a baby gate or pen, chew toys, and an enzyme cleaner for accidents

**Puppy-proof.** Secure electrical cords, move toxic plants out of reach, and pick small objects up off the floor.

**Book the first vet visit now.** Our Golden Retriever and [Labrador Retriever checklists](https://thewooffy.com/blogs/dog-breeds/labrador-retriever-puppy-checklist) say to book it within the first 3 days. Bring every record from your breeder or shelter, confirm the vaccine schedule, and ask about flea, tick and heartworm prevention. If you plan to get pet insurance, apply before that visit. More on why next week.

**Keep week one quiet.** Let your puppy explore one room at a time. Take them out after waking, eating and playing. Decide where they'll sleep long-term before night one. [Crate Training 101](https://thewooffy.com/blogs/dog-training/crate-training) helps with that.

Most breeds on Wooffy have their own puppy checklist. Find yours from its guide in the [A–Z breed directory](https://thewooffy.com/blogs/dog-breeds/dog-breeds-a-z).

[BUTTON] See a full puppy checklist

Mike & Alice (and Tank)
Wooffy

P.S. Hit reply and tell us which breeds made your shortlist — we read every email.

---

## Email 4: Real first-year costs, budgeting and insurance basics

- **Send:** day 14 (6 days after Email 3)
- **Subject:** What a dog's first year really costs
- **Preview text:** How to budget for year one, plus pet insurance basics in plain English.
- **Primary button:** Price your first year → https://thewooffy.com/pages/dog-cost-calculator
- **Secondary links (in body):**
  - how we estimate dog costs → https://thewooffy.com/pages/how-we-estimate-dog-costs
  - a Labrador's first-year budget → https://thewooffy.com/blogs/dog-breeds/labrador-retriever-first-year-costs
  - the dog teenage phase → https://thewooffy.com/blogs/dog-training/dog-teenage-phase

**Body:**

Hi there,

This is the last email in the course, and it covers the part adoption photos leave out: money.

Year one is usually the most expensive. You're paying for the dog itself, buying all the gear at once, and covering puppy vaccines and spay/neuter. See [a Labrador's first-year budget](https://thewooffy.com/blogs/dog-breeds/labrador-retriever-first-year-costs) for a real example. Here's a simple plan:

1. **Price your top breed with your real choices:** breeder or rescue, city or small town, professional grooming or DIY, insurance or not.
2. **Get real quotes.** Our numbers are planning ranges, not quotes ([how we estimate dog costs](https://thewooffy.com/pages/how-we-estimate-dog-costs)). Call two or three local vets.
3. **Leave room for surprises.** The calculator covers routine vet care, not emergencies, and emergencies can exceed the ranges shown.

**Pet insurance basics** (we don't recommend any company):
- Policies won't cover conditions that show signs before you enroll or during the waiting period. If you plan to insure, compare quotes early.
- Check whether hereditary conditions are covered. Some policies exclude them or charge extra.
- Compare the annual limit and the deductible, not just the monthly price.
- Get quotes for your dog's age and ZIP code.

One more thing to plan for: around 6 months, [the dog teenage phase](https://thewooffy.com/blogs/dog-training/dog-teenage-phase) usually starts.

Thanks for reading along. Whether you choose a puppy, an adult rescue, or decide to wait, we hope you feel ready.

[BUTTON] Price your first year

Mike & Alice (and Tank)
Wooffy

P.S. Hit reply and tell us which breeds made your shortlist — we read every email.

---

## Where each claim comes from

| Email | Claim | Linked page that says it |
|---|---|---|
| 1 | Quiz takes about 2 minutes | /pages/dog-breed-quiz |
| 1 | "Is a [Breed] Right for You?" section in breed guides | breed guides via A–Z (172 guides have the section) |
| 1 | Curly, low-shedding coats need a professional groom every 6–8 weeks | choosing guide (Factor 4: grooming) |
| 2 | Shelter breed labels often get breed wrong | mixed-breed-dogs |
| 1 | Shortlist a few breeds, then research deeper | choosing guide ("shortlist 3-4 breeds") |
| 1 | Meet adult dogs of each breed before deciding (also the preview text) | choosing guide ("meet at least one adult of the breed in person"; meeting an adult shows what you're signing up for) |
| 2 | Breeder checks (OFA lookup, meet mother, questions, return clause) | how-to-find-a-responsible-breeder |
| 2 | Both routes can be responsible; bigger risk is a bad source | adopt-or-shop-dog |
| 2 | Rescue questions (why here, vet records, kids/pets/strangers, take back) | adopt-or-shop-dog |
| 2 | Red flags (price, no visit/live video, payment types, fee ladder) | puppy-scams, how-to-find-a-responsible-breeder |
| 2 | Deposit red flags: pushed before you can read the contract; first question is how soon you can pay | how-to-find-a-responsible-breeder ("Can I read the contract before I pay anything?" Worry about "after the deposit"; red-flag table: "First question is how soon you can pay a deposit") |
| 2 | Deposit terms in writing; pay by a method you can dispute | how-to-find-a-responsible-breeder, puppy-scams |
| 3 | Supplies, puppy-proofing, what to bring and ask at the first vet visit, insurance before first visit, week-one routine | golden-retriever-puppy-checklist, labrador-retriever-puppy-checklist |
| 3 | Book the first vet visit within the first 3 days | golden-retriever-puppy-checklist ("within the first 3 days"), labrador-retriever-puppy-checklist ("within 3 days of arrival") |
| 4 | Why year one costs more | labrador-retriever-first-year-costs |
| 4 | Ranges aren't quotes; call 2–3 local vets; quotes by age and ZIP; calculator excludes emergencies; emergencies can exceed ranges | /pages/how-we-estimate-dog-costs |
| 4 | Pre-enrollment and waiting-period exclusions; hereditary coverage | /pages/dog-cost-calculator (insurance note, citing NAIC model act) |
| 4 | Check annual limit and deductible | labrador-retriever-first-year-costs |
| 4 | Teenage phase usually starts around 6 months | /blogs/dog-training/dog-teenage-phase |

## Word and character counts

Body word counts include the greeting, the sign-off (with "Wooffy") and the P.S. Link text counts as words. URLs and the `[BUTTON]` line don't count. Recounted after the 2026-10-09 revision.

| Email | Subject (chars) | Preview (chars) | Body words without P.S. | Body words with P.S. | Within limits |
|---|---|---|---|---|---|
| 1 | 35 / 50 | 65 / 90 | 197 | 212 / 150–250 | Yes |
| 2 | 42 / 50 | 69 / 90 | 234 | 249 / 150–250 | Yes (near the cap: cut a word for every word you add) |
| 3 | 38 / 50 | 77 / 90 | 229 | 244 / 150–250 | Yes |
| 4 | 36 / 50 | 71 / 90 | 229 | 244 / 150–250 | Yes |

## Link table

Every URL used above, checked with curl (normal browser User-Agent, no redirects followed, about one request every 1.5–2 seconds).

Pages I looked at and left out:
- `/blogs/dog-health/new-puppy-parents-guide` returns 200, but it's a 2022 legacy post with typos.
- `/blogs/dog-breeds/tagged/checklist` returns 200, but it's 26 pages sorted by date, so it's a poor landing page.
- `/blogs/dog-breeds/dog-training-guides` returned **404**. The training hub lives under another blog path.

All 14 URLs returned 200 with no redirect. The verification pass re-checked all 14 between 03:06:24 and 03:06:44 UTC on 2026-10-10 (2026-10-09 PT): still 200, no redirects. The 2026-10-09 revision changed no URLs.

| URL | HTTP status | Date checked |
|---|---|---|
| https://thewooffy.com/blogs/dog-breeds/dog-breeds-a-z | 200 | 2026-10-09 (02:54:50 UTC on 2026-10-10) |
| https://thewooffy.com/pages/dog-breed-quiz | 200 | 2026-10-09 (02:54:52 UTC on 2026-10-10) |
| https://thewooffy.com/pages/dog-cost-calculator | 200 | 2026-10-09 (02:54:54 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-breeds/choosing-the-perfect-dog-breed-factors-to-consider-before-bringing-a-new-companion-home | 200 | 2026-10-09 (02:54:56 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-breeds/adopt-or-shop-dog | 200 | 2026-10-09 (02:54:58 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-breeds/how-to-find-a-responsible-breeder | 200 | 2026-10-09 (02:55:00 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-breeds/puppy-scams | 200 | 2026-10-09 (02:55:01 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-breeds/mixed-breed-dogs | 200 | 2026-10-09 (02:55:03 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-breeds/golden-retriever-puppy-checklist | 200 | 2026-10-09 (02:55:05 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-training/crate-training | 200 | 2026-10-09 (02:55:07 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-breeds/labrador-retriever-puppy-checklist | 200 | 2026-10-09 (02:55:09 UTC on 2026-10-10) |
| https://thewooffy.com/pages/how-we-estimate-dog-costs | 200 | 2026-10-09 (02:55:11 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-breeds/labrador-retriever-first-year-costs | 200 | 2026-10-09 (02:55:13 UTC on 2026-10-10) |
| https://thewooffy.com/blogs/dog-training/dog-teenage-phase | 200 | 2026-10-09 (02:55:14 UTC on 2026-10-10) |
