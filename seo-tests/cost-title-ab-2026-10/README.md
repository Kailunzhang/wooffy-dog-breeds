# Cost-page title A/B test (started 2026-10-01)

Hypothesis: searchers type "<breed> price", but 160/164 cost pages are titled
"<Breed> First-Year Costs". A price-intent title ("<Breed> Price: $A–$B Puppy +
First-Year Costs", range copied from the page's own cost table) should lift CTR.

- `baseline_cost_pages_28d_2026-10-01.csv`: GSC per-page clicks / impressions /
  CTR / position, last 28 days to 2026-09-29 (1,287 clicks, 301,685 impressions).
- `ab_groups.json`: pages sorted by impressions, paired, one of each pair to
  test (80) and control (80) by md5 hash. Test 144K impr / pos 6.95; control
  139K / pos 7.11. Four pages already titled with "price" are excluded.
- Only `meta.title_tag` and `meta.meta_description` change, test group only.

Read-out: from ~2026-10-29, pull the same GSC per-page 28-day table and compare
CTR change (after vs baseline) test vs control at similar positions. If test
wins, apply the same pattern to the control group.

## Status
- **Test titles live: 2026-10-01** (80/80 test pages pushed; control untouched,
  verified e.g. borzoi still "Borzoi First-Year Costs"). Three test pages use the
  no-number fallback because their own price figures conflict: beagle, boxer,
  flat-coated-retriever.
- Read-out window: 28 days ending ~2026-10-29 or later (allow a few days for
  Google to recrawl titles before counting).
