// Node tests for the dog breed quiz scoring (no installs: node:test + node:assert).
//
// Loads the WQ-SCORING block from the BUILT page (pages/breed-quiz-FINAL.html), so run
// `py scripts/build_breed_quiz.py --fixture` (or with real data) first.
//
//   node --test scripts/test_breed_quiz.mjs                    # fixture data
//   node scripts/test_breed_quiz.mjs breed-quiz-data.json      # any data file
//   WQ_DATA=breed-quiz-data.json node --test scripts/test_breed_quiz.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PAGE_PATH = resolve(ROOT, 'pages/breed-quiz-FINAL.html');
const argData = process.argv[2] && process.argv[2].endsWith('.json') ? process.argv[2] : null;
const DATA_PATH = resolve(ROOT, argData || process.env.WQ_DATA || 'pages/breed-quiz-fixture.json');

const PAGE = readFileSync(PAGE_PATH, 'utf8');
const DATA = JSON.parse(readFileSync(DATA_PATH, 'utf8'));
const BREEDS = DATA.breeds;
const IS_FULL = BREEDS.length >= 100;
const SAMPLE_SIZE = 4000;

function loadScoring(html) {
  const start = html.indexOf('// WQ-SCORING-START');
  const end = html.indexOf('// WQ-SCORING-END');
  assert.ok(start !== -1 && end > start, 'scoring markers not found in built page');
  return new Function(html.slice(start, end) + '\nreturn WQ;')();
}
const WQ = loadScoring(PAGE);

const BASE = {
  home: 'small', kids: 'none', pets: ['none'], alone: 'short', act: 'moderate', exp: 'some',
  coat: 'any', groom: 'pro', noise: 'any', climate: ['mild'], size: ['any'], pri: ['none'], budget: null
};
const answers = (over) => ({ ...BASE, ...over });
const run = (over) => WQ.rank(BREEDS, answers(over));
const top = (r, n) => r.list.slice(0, n).map((x) => x.b);
const names = (bs) => bs.map((b) => b.n).join(', ');
const mid = (b) => (b.cost ? (b.cost[0] + b.cost[1]) / 2 : null);

// Seeded PRNG so the sampled invariants are reproducible.
function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}
function randomAnswers(rand) {
  const a = {};
  for (const k of WQ.KEYS) {
    const opts = WQ.ALLOWED[k];
    if (!WQ.MULTI[k]) {
      a[k] = WQ.OPTIONAL[k] && rand() < 0.4 ? null : opts[Math.floor(rand() * opts.length)];
      continue;
    }
    const ex = WQ.EXCLUSIVE[k];
    if (rand() < 0.3) { a[k] = [ex]; continue; }
    const pool = opts.filter((o) => o !== ex);
    let picked = pool.filter(() => rand() < 0.35);
    if (WQ.MAX_PICKS[k]) picked = picked.slice(0, WQ.MAX_PICKS[k]);
    a[k] = picked.length ? picked : [pool[Math.floor(rand() * pool.length)]];
  }
  return a;
}
function sample(n, seed = 42) {
  const rand = rng(seed);
  return Array.from({ length: n }, () => randomAnswers(rand));
}

// ---------------------------------------------------------------- personas

test('P1 apartment + first dog + kids under 6 + allergies: only allergy-flagged, kid-safe, beginner-friendly', () => {
  const r = run({ home: 'apt', exp: 'first', kids: 'young', coat: 'allergy' });
  assert.ok(r.list.length >= 1, 'no results');
  for (const x of r.list) {
    assert.equal(x.b.f.allergy, true, `${x.b.n} is not allergy-flagged`);
    assert.ok(x.b.sc.kids > 1, `${x.b.n} kids=${x.b.sc.kids}`);
  }
  for (const b of top(r, 3)) assert.ok(b.sc.beginner >= 3 && b.sc.kids >= 3, `weak top-3 pick: ${b.n}`);
});

test('P2 very active hiker on land, experienced: top 3 are all high-energy', () => {
  const r = run({ home: 'land', act: 'very', exp: 'pro' });
  for (const b of top(r, 3)) assert.ok(b.sc.energy >= 4, `low-energy breed in top 3: ${b.n}`);
});

test('P3 workday alone + apartment + quiet: no poor-alone, loud or apartment-unfit breed in top 3', () => {
  const a = answers({ home: 'apt', alone: 'work', noise: 'quiet' });
  const r = WQ.rank(BREEDS, a);
  const fits = (b) => b.sc.alone >= 3 && b.sc.barking <= 3 && b.sc.apartment >= 3;
  const possible = r.list.filter((x) => fits(x.b)).length;
  for (const b of top(r, Math.min(2, possible))) assert.ok(fits(b), `top 2 has ${b.n}`);
  // Any compromise pick in the top 3 must carry a heads-up that names the mismatch.
  for (const x of r.list.slice(0, 3)) {
    if (x.b.sc.alone <= 1) assert.ok(WQ.headsUps(x.b, a, x.parts).some((t) => /alone/.test(t)), `${x.b.n}: no alone heads-up`);
    assert.ok(x.b.sc.alone >= 2 || x.pct < 70, `${x.b.n} (alone=${x.b.sc.alone}) labelled ${WQ.label(x.pct)}`);
  }
  assert.ok(WQ.conflicts(a, r).some((c) => c.k === 'alone'), 'missing midday-walker tip');
});

test('P4 dogs + cats + small pets, toy/small only: never small_pets<=1, sizes respected', () => {
  const r = run({ pets: ['dogs', 'cats', 'small'], size: ['toy', 'small'] });
  assert.ok(r.list.length >= 3, `only ${r.list.length} results`);
  for (const x of r.list) {
    assert.ok(x.b.sc.small_pets > 1, `${x.b.n} small_pets=${x.b.sc.small_pets}`);
    if (!r.relaxedSize) assert.ok(WQ.fractionInside(x.b.w, ['toy', 'small']) > 0, `${x.b.n} outside size`);
  }
});

test('P5 hot climate: no flat-faced breed in top 3 unless nothing else fits', () => {
  const r = run({ climate: ['hot'] });
  const nonBrachy = r.list.filter((x) => !x.b.f.brachy).length;
  const brachyTop = top(r, 3).filter((b) => b.f.brachy);
  if (nonBrachy >= 3) assert.equal(brachyTop.length, 0, `brachy in top 3: ${names(brachyTop)}`);
  for (const b of top(r, 3)) assert.ok(b.sc.heat >= 3, `heat-intolerant ${b.n} in top 3`);
});

test('P6 watchful guardian + experienced + land, large/giant: top picks are strong watchdogs', () => {
  const r = run({ home: 'land', exp: 'pro', act: 'active', pri: ['guardian'], size: ['large', 'giant'] });
  assert.ok(top(r, 1)[0].sc.watchdog >= 4, `top 1 is ${top(r, 1)[0].n}`);
  assert.ok(top(r, 3).filter((b) => b.sc.watchdog >= 4).length >= 2, `top 3: ${names(top(r, 3))}`);
});

test('P7 minimal grooming + minimal hair: conflict flagged, top 3 low-shed and low-groom', () => {
  const a = answers({ coat: 'minimal', groom: 'minimal' });
  const r = WQ.rank(BREEDS, a);
  assert.ok(WQ.conflicts(a, r).some((c) => c.k === 'coat-groom'), 'coat/grooming conflict not flagged');
  for (const b of top(r, 3)) assert.ok(b.sc.shedding <= 3 && b.sc.grooming <= 3, `top 3 has ${b.n}`);
});

test('P8 first dog + easygoing + apartment: no hard-to-handle or very high-energy breed in top 5', () => {
  const r = run({ exp: 'first', act: 'relaxed', home: 'apt' });
  for (const b of top(r, 5)) assert.ok(b.sc.beginner >= 2 && b.sc.energy <= 4, `top 5 has ${b.n}`);
  for (const b of top(r, 3)) assert.ok(b.sc.beginner >= 3, `top 3 has ${b.n}`);
});

test('P9 cold winters + very active: top 3 handle cold and have energy', () => {
  const r = run({ climate: ['cold'], act: 'very', exp: 'pro', home: 'land' });
  for (const b of top(r, 3)) assert.ok(b.sc.cold >= 3 && b.sc.energy >= 4, `top 3 has ${b.n}`);
});

test('P10 budget under $3k: top 5 cost less on average than the field', () => {
  const r = run({ budget: '3k' });
  const costed = (bs) => bs.map(mid).filter((x) => x !== null);
  const avg = (xs) => xs.reduce((s, x) => s + x, 0) / xs.length;
  const t5 = costed(top(r, 5)), all = costed(r.list.map((x) => x.b));
  if (t5.length && all.length) assert.ok(avg(t5) <= avg(all), `top-5 avg ${avg(t5)} > field ${avg(all)}`);
});

test('P11 kids under 6 + giant only: size relaxes when too few, never returns kids<=1', () => {
  const a = answers({ kids: 'young', size: ['giant'] });
  const r = WQ.rank(BREEDS, a);
  const strict = BREEDS.filter((b) => !WQ.filterReason(b, a, false));
  if (strict.length < WQ.MIN_RESULTS) {
    assert.equal(r.relaxedSize, true, 'size should have been relaxed');
    assert.ok(WQ.conflicts(a, r).some((c) => c.k === 'size'), 'user not told about widened size');
  }
  assert.ok(r.list.length >= Math.min(3, BREEDS.filter((b) => b.sc.kids > 1).length));
  for (const x of r.list) assert.ok(x.b.sc.kids > 1, `${x.b.n} kids=${x.b.sc.kids}`);
});

test('P12 allergies + giant only: allergy filter is never relaxed', () => {
  const r = run({ coat: 'allergy', size: ['giant'] });
  for (const x of r.list) assert.equal(x.b.f.allergy, true, `${x.b.n} not allergy-flagged`);
});

test('P13 adoption description reads naturally', () => {
  const d = WQ.describeDog(answers({ size: ['medium'], act: 'moderate', coat: 'allergy', pets: ['cats'], kids: 'young' }));
  assert.equal(d, 'a medium, moderate-energy, low-shedding dog that has done well with kids and cats');
  assert.equal(WQ.describeDog(answers({ act: 'active' })), 'an active dog');
});

// ---------------------------------------------------------------- invariants

const SAMPLES = sample(SAMPLE_SIZE);

test('INV hard filters hold for every sampled answer set', () => {
  for (const a of SAMPLES) {
    const r = WQ.rank(BREEDS, a);
    for (const x of r.list) {
      if (a.coat === 'allergy') assert.equal(x.b.f.allergy, true, 'allergy relaxed');
      if (a.kids === 'young') assert.ok(x.b.sc.kids > 1, 'kids<=1 with kids under 6');
      if (a.pets.includes('cats') || a.pets.includes('small')) assert.ok(x.b.sc.small_pets > 1, 'small_pets<=1 with cats');
    }
  }
});

test('INV at least 3 results whenever 3+ breeds pass the non-size must-haves', () => {
  for (const a of SAMPLES) {
    const r = WQ.rank(BREEDS, a);
    const possible = BREEDS.filter((b) => !WQ.filterReason(b, a, true)).length;
    assert.ok(r.list.length >= Math.min(3, possible), `${r.list.length} results, ${possible} possible: ${WQ.encode(a)}`);
  }
});

test('INV match % is an integer in 0..99 and the list is sorted', () => {
  for (const a of SAMPLES.slice(0, 1000)) {
    const r = WQ.rank(BREEDS, a);
    r.list.forEach((x, i) => {
      assert.ok(Number.isInteger(x.pct) && x.pct >= 0 && x.pct <= 99, `pct=${x.pct}`);
      if (i) assert.ok(r.list[i - 1].pct >= x.pct, 'not sorted');
    });
  }
});

test('INV results are deterministic and independent of input order', () => {
  const rand = rng(7);
  for (const a of SAMPLES.slice(0, 300)) {
    const key = (list) => WQ.rank(list, a).list.map((x) => x.b.s + ':' + x.pct).join();
    const one = key(BREEDS);
    assert.equal(one, key(BREEDS));
    assert.equal(one, key(BREEDS.slice().sort(() => rand() - 0.5)));
  }
});

test('INV URL hash encode/decode round-trips and rejects junk', () => {
  for (const a of SAMPLES.slice(0, 500)) assert.deepEqual(WQ.decode(WQ.encode(a)), a);
  const junk = ['', 'x', 'apt.young', '<script>',
    'apt.young.dogs_none.rare.relaxed.first.any.pro.any.mild.any.none.-',
    'apt.young.dogs.rare.relaxed.first.any.pro.any.mild.any.train_kids_calm.-',
    'apt.young.dogs.rare.zzz.first.any.pro.any.mild.any.none.-',
    'apt.young.dogs.rare.relaxed.first.any.pro.any.-.any.none.-'];
  for (const j of junk) assert.equal(WQ.decode(j), null, `accepted ${j}`);
});

// "Not reliably hypoallergenic" / "no guarantee" are disclaimers, not claims.
const NEGATED = /\b(not|no|never|isn't|aren't|nothing)\b[^.]{0,30}\b(hypoallergenic|guarantee)/i;
const isOverclaim = (t) => /perfect/i.test(t) || (/hypoallergenic|guarantee/i.test(t) && !NEGATED.test(t));

test('INV every shown card has 1-3 reasons and at most 2 computed heads-ups plus 1 guide caveat, with no overclaims', () => {
  for (const a of SAMPLES.slice(0, 800)) {
    const r = WQ.rank(BREEDS, a);
    for (const x of r.list.slice(0, 10)) {
      const why = WQ.reasons(x.b, a, x.parts), warn = WQ.headsUps(x.b, a, x.parts);
      const caveats = warn.filter((t) => x.b.cv.includes(t));
      assert.ok(why.length >= 1 && why.length <= 3, `${x.b.n}: ${why.length} reasons`);
      assert.ok(caveats.length <= 1, `${x.b.n}: ${caveats.length} caveats`);
      assert.ok(warn.length - caveats.length <= 2, `${x.b.n}: ${warn.length - caveats.length} computed heads-ups`);
      if (caveats.length) assert.equal(warn[warn.length - 1], caveats[0], `${x.b.n}: caveat must come after the computed heads-ups`);
      for (const t of why.concat(warn)) assert.ok(!isOverclaim(t), `overclaim: ${t}`);
    }
  }
});

test('INV no card gives a reason and a heads-up that contradict each other', () => {
  const CLASHES = [
    ['Forgiving for a first-time owner', 'Can be a handful for a first-time owner'],
    ['Patient with young children', 'Best with older, dog-savvy kids'],
    ['Settles well in an apartment', 'Not an easy fit for apartment life'],
    ['Quick to learn', 'Can be harder to train than you’d like'],
    ['Copes better than most with time alone', 'Doesn’t like long stretches alone; plan a midday walker'],
    ['Handles a few hours on its own', 'Can struggle even with a few hours alone'],
    ['Known for being great with kids', 'Not the most kid-focused breed'],
    ['Friendly with new people', 'Can be reserved with strangers'],
    ['Alert, watchful guardian', 'More friendly than watchful'],
    ['Usually gets along with other dogs', 'Can be choosy about other dogs'],
    ['Lower chase instinct than many breeds', 'Chase instinct; supervise around cats and small pets'],
    // Pairs the review found (old and new wording).
    ['Easy to keep', 'Takes more upkeep than a low-maintenance breed'],
    ['Easy to keep', 'Needs more exercise than a low-maintenance breed'],
    ['Easy to keep', 'Takes more coat care than a low-maintenance breed'],
    ['Easy coat care', 'Takes more coat care than a low-maintenance breed'],
    ['Picks up training quickly', 'Strong-willed; plan on steady training'],
    ['Quick to learn', 'Strong-willed; plan on steady training'],
    ['Weekly brushing keeps the coat tidy', 'Coat needs more grooming than you planned'],
    ['Easy coat care', 'Coat needs more grooming than you planned'],
    ['Keeps up on long walks and hikes', 'Calmer than you may want for long, active days'],
    ['Built for running and trail days', 'Calmer than you may want for long, active days'],
    ['Settles well in an apartment', 'Vocal, high-energy escape artist that needs a secure yard and consistent training'],
    ['Content with about an hour of activity a day', 'Vocal, high-energy escape artist that needs a secure yard and consistent training'],
    ['Settles well in an apartment', 'Very vocal: barking can bother close neighbors and thin apartment walls'],
    ['Weekly brushing keeps the coat tidy', 'Rough coat needs brushing 3–4 times a week, plus heavy seasonal shedding'],
    ['Forgiving for a first-time owner', 'Not a beginner dog: needs experienced handling, early socialization and 6-foot fencing'],
  ];
  for (const a of SAMPLES.slice(0, 1500)) {
    const r = WQ.rank(BREEDS, a);
    for (const x of r.list.slice(0, 10)) {
      const why = WQ.reasons(x.b, a, x.parts), warn = WQ.headsUps(x.b, a, x.parts);
      for (const [good, bad] of CLASHES) {
        assert.ok(!(why.includes(good) && warn.includes(bad)), `${x.b.n}: "${good}" + "${bad}"`);
      }
    }
  }
});

test('INV breed checker shows one line per topic (kids answer + kids priority merge)', () => {
  for (const over of [{ kids: 'young', pri: ['kids'] }, { kids: 'older', pri: ['kids', 'train'] }]) {
    const a = answers(over);
    const r = WQ.rank(BREEDS, a);
    for (const x of r.list) {
      const lines = WQ.checkNotes(x.b, a, x.parts).gaps.filter((g) => /kid/i.test(g.t));
      assert.ok(lines.length <= 1, `${x.b.n}: ${lines.map((g) => g.t).join(' | ')}`);
    }
  }
});

test('INV variety: no breed dominates first place; breeds reach someone’s top 5', () => {
  const first = new Map(), top5 = new Set(), topPct = [];
  for (const a of SAMPLES) {
    const r = WQ.rank(BREEDS, a);
    if (!r.list.length) continue;
    topPct.push(r.list[0].pct);
    first.set(r.list[0].b.s, (first.get(r.list[0].b.s) || 0) + 1);
    r.list.slice(0, 5).forEach((x) => top5.add(x.b.s));
  }
  const total = [...first.values()].reduce((s, x) => s + x, 0);
  const ranked = [...first.entries()].sort((x, y) => y[1] - x[1]);
  const [leader, count] = ranked[0];
  const share = count / total;
  const unreachable = BREEDS.filter((b) => !top5.has(b.s)).map((b) => b.s);
  console.log(`  first-place leaders: ${ranked.slice(0, 6).map(([s, c]) => `${s} ${(100 * c / total).toFixed(1)}%`).join(', ')}`);
  console.log(`  ${BREEDS.length - unreachable.length}/${BREEDS.length} breeds reach a top 5` +
    (unreachable.length ? `; never in top 5: ${unreachable.slice(0, 30).join(', ')}` : ''));
  topPct.sort((x, y) => x - y);
  const q = (f) => topPct[Math.floor(f * (topPct.length - 1))];
  console.log(`  #1 match %: p10 ${q(0.1)}, median ${q(0.5)}, p90 ${q(0.9)} (random answer sets)`);
  const maxShare = IS_FULL ? 0.12 : 0.3;
  assert.ok(share <= maxShare, `${leader} wins ${(share * 100).toFixed(1)}% of first places (limit ${maxShare * 100}%)`);
  if (!IS_FULL) assert.equal(unreachable.length, 0, `never in top 5: ${unreachable.join(', ')}`);
});

// ---------------------------------------------------------------- heads-up relevance (review fixes)

const cardsOf = (a, n = 10) => WQ.rank(BREEDS, a).list.slice(0, n).map((x) => ({ x, ...WQ.cardNotes(x.b, a, x.parts) }));
const overlap = (p, q) => p.filter((k) => q.includes(k));
const caveatsOn = (c) => c.warn.filter((t) => c.x.b.cv.includes(t));
const computedOn = (c) => c.warn.filter((t) => !c.x.b.cv.includes(t));

test('INV a guide caveat never repeats the topic of a computed heads-up or a reason on the same card', () => {
  for (const a of SAMPLES.slice(0, 1500)) {
    for (const c of cardsOf(a)) {
      for (const t of caveatsOn(c)) {
        const tp = WQ.topicsOf(t);
        for (const h of computedOn(c)) assert.deepEqual(overlap(tp, WQ.topicsOf(h)), [], `${c.x.b.n}: caveat "${t}" repeats "${h}"`);
        for (const w of c.why) assert.deepEqual(overlap(tp, WQ.topicsOf(w)), [], `${c.x.b.n}: caveat "${t}" vs reason "${w}"`);
      }
    }
  }
});

test('INV computed heads-ups on a card cover different topics', () => {
  for (const a of SAMPLES.slice(0, 1000)) {
    for (const c of cardsOf(a)) {
      const h = computedOn(c);
      if (h.length === 2) assert.deepEqual(overlap(WQ.topicsOf(h[0]), WQ.topicsOf(h[1])), [], `${c.x.b.n}: "${h[0]}" + "${h[1]}"`);
    }
  }
});

test('INV caveats only show when they apply (no pet, kid, toddler, heat, cold or alone caveat that does not apply)', () => {
  const GATED = ['pets', 'kids', 'toddler', 'heat', 'cold', 'alone'];
  for (const a of SAMPLES.slice(0, 1500)) {
    for (const c of cardsOf(a)) {
      for (const t of caveatsOn(c)) {
        for (const k of WQ.topicsOf(t)) {
          if (GATED.includes(k)) assert.ok(WQ.topicApplies(k, c.x.b, a), `${c.x.b.n}: "${t}" (${k}) shown for ${WQ.encode(a)}`);
        }
        if (c.x.b.f.brachy) assert.ok(!WQ.topicsOf(t).includes('brachy'), `${c.x.b.n}: flat-face caveat duplicates the card note`);
      }
    }
  }
});

test('INV "Calmer than you may want" only for a 2+ level energy gap, never beside high-energy praise', () => {
  const HIGH = /high[- ]energy|tireless|energetic|built for running|not a couch dog|vigorous/i;
  for (const a of SAMPLES.slice(0, 1500)) {
    for (const c of cardsOf(a)) {
      if (!c.warn.includes('Calmer than you may want for long, active days')) continue;
      assert.ok(WQ.ENERGY_CAP[a.act] - c.x.b.sc.energy >= 2, `${c.x.b.n}: energy ${c.x.b.sc.energy} vs ${a.act}`);
      for (const t of c.why.concat(c.warn)) assert.ok(!HIGH.test(t), `${c.x.b.n}: "Calmer" beside "${t}"`);
    }
  }
});

test('INV the exercise heads-up compares minutes with the answer and shows the breed range', () => {
  for (const a of SAMPLES.slice(0, 1500)) {
    for (const c of cardsOf(a)) {
      const t = c.warn.find((w) => /min of exercise a day, more than you planned/.test(w));
      if (!t) continue;
      assert.ok(c.x.b.ex[1] > WQ.USER_MAX_MIN[a.act], `${c.x.b.n}: ${c.x.b.ex} min is not more than planned (${a.act})`);
      if (/^Needs /.test(t)) assert.ok(t.includes(WQ.span(c.x.b.ex[0], c.x.b.ex[1], 'min')), `${c.x.b.n}: "${t}" doesn't show the range`);
    }
  }
});

test('INV the experience heads-up talks about handling, not training', () => {
  for (const a of SAMPLES.slice(0, 800)) {
    for (const c of cardsOf(a)) assert.ok(!c.warn.includes('Strong-willed; plan on steady training'), 'old wording still shown');
  }
});

test('INV "Check a specific breed" lists every 4+ point deduction, and its caveat adds a new topic', () => {
  const NO_TEXT = ['avail'];
  for (const a of SAMPLES.slice(0, 300)) {
    const r = WQ.rank(BREEDS, a);
    for (const x of r.list.slice(0, 40)) {
      const n = WQ.checkNotes(x.b, a, x.parts);
      const big = Object.keys(x.parts).filter((k) => x.parts[k] >= 4 && !NO_TEXT.includes(k));
      // A weak-gated part with no milder wording (dogs, smallpets) is always weak when it reaches 4.
      // Same-topic deductions share one line, so every point is listed but lines can be fewer.
      const listed = n.gaps.reduce((t, g) => t + g.pts, 0);
      const owed = big.reduce((t, k) => t + Math.round(x.parts[k]), 0);
      assert.ok(n.gaps.length <= big.length && listed === owed, `${x.b.n}: listed ${n.gaps.map((g) => g.t)} (${listed} pts) for parts ${big} (${owed} pts)`);
      if (n.caveat) for (const g of n.gaps) assert.deepEqual(overlap(WQ.topicsOf(n.caveat), WQ.topicsOf(g.t)), [], `${x.b.n}: caveat repeats "${g.t}"`);
    }
  }
});

// ---------------------------------------------------------------- sizes and ranges (review fixes)

test('SIZE single weights on a boundary land in one band; true two-band ranges count for both', () => {
  assert.deepEqual(WQ.bandsFor([12, 12]), ['small']);
  assert.deepEqual(WQ.bandsFor([50, 90]), ['large']);
  assert.deepEqual(WQ.bandsFor([40, 70]), ['medium', 'large']);
  assert.equal(WQ.sizeLabel([12, 12]), 'Small');
  for (const b of BREEDS) assert.ok(WQ.bandsFor(b.w).length >= 1, `${b.n} (${b.w}) has no size band`);
  assert.equal(WQ.span(30, 30, 'min'), 'about 30 min');
  assert.equal(WQ.span(12, 18, 'lb'), '12–18 lb');
  assert.equal(WQ.moneyRange([2000, 2000]), '$2,000');
});

test('SIZE widening adds one size step at a time and names exactly the sizes it added', () => {
  let widened = 0;
  for (const a of SAMPLES) {
    const r = WQ.rank(BREEDS, a);
    if (!r.relaxedSize) continue;
    widened++;
    const sel = a.size.filter((v) => v !== 'any');
    assert.ok(BREEDS.filter((b) => !WQ.filterReason(b, a, false)).length < WQ.MIN_RESULTS, 'widened although enough breeds fit');
    let steps = 1;
    while (steps < WQ.BANDS.length && WQ.widenBands(sel, steps).join() !== r.sizeBands.join()) steps++;
    assert.ok(steps < WQ.BANDS.length, `size bands ${r.sizeBands} are not a widening of ${sel}`);
    if (steps > 1) {
      const fewer = BREEDS.filter((b) => !WQ.filterReason(b, a, WQ.widenBands(sel, steps - 1))).length;
      assert.ok(fewer < WQ.MIN_RESULTS, `widened ${steps} steps although ${steps - 1} gave ${fewer} breeds`);
    }
    for (const x of r.list) assert.ok(WQ.fractionInside(x.b.w, r.sizeBands) > 0, `${x.b.n} outside ${r.sizeBands}`);
    assert.ok(r.addedSizes.length >= 1, 'widened but named no size');
    const note = WQ.conflicts(a, r).find((c) => c.k === 'size');
    for (const id of r.addedSizes) {
      assert.ok(!sel.includes(id) && r.sizeBands.includes(id), `added ${id}`);
      assert.ok(note.d.includes(id), `note doesn't name ${id}: ${note.d}`);
    }
  }
  console.log(`  ${widened} sampled answer sets widened the size range`);
});

test('SIZE giant + allergies widens to large before anything smaller', () => {
  const a = answers({ coat: 'allergy', size: ['giant'] });
  const r = WQ.rank(BREEDS, a);
  if (!r.relaxedSize) return;
  if (BREEDS.filter((b) => !WQ.filterReason(b, a, ['large', 'giant'])).length >= WQ.MIN_RESULTS) {
    assert.deepEqual(r.addedSizes, ['large']);
    for (const x of r.list) assert.ok(WQ.fractionInside(x.b.w, ['large', 'giant']) > 0, `${x.b.n} is smaller than large`);
  }
});

test('P14 weekly brushers: pro-groomed coats no longer fill the top of the list', () => {
  const r = run({ home: 'yard', kids: 'young', pets: ['cats'], exp: 'first', coat: 'some', groom: 'weekly', noise: 'some', pri: ['kids', 'train'] });
  const proCoats = top(r, 5).filter((b) => b.sc.grooming >= 5).length;
  assert.ok(proCoats <= 2, `top 5 has ${proCoats} pro-groom coats: ${names(top(r, 5))}`);
});

// ---------------------------------------------------------------- built page

test('PAGE has no leftover placeholders, one root, valid embedded data, under 250 KB', () => {
  assert.ok(!/__WQ_[A-Z_]+__/.test(PAGE), 'placeholder left in page');
  assert.equal((PAGE.match(/id="wq-root"/g) || []).length, 1);
  assert.ok(!/<(html|head|body)[\s>]/i.test(PAGE), 'fragment must not contain html/head/body');
  const m = PAGE.match(/<script type="application\/json" id="wq-data">([\s\S]*?)<\/script>/);
  assert.ok(m, 'data script missing');
  const embedded = JSON.parse(m[1]);
  assert.equal(embedded.breeds.length, embedded.count);
  const bytes = Buffer.byteLength(PAGE, 'utf8');
  assert.ok(bytes < 250000, `page is ${bytes} bytes`);
});

test('PAGE FAQPage JSON-LD matches the visible FAQ text', () => {
  const m = PAGE.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
  const faq = JSON.parse(m[1])['@graph'].find((g) => g['@type'] === 'FAQPage');
  assert.ok(faq.mainEntity.length >= 4 && faq.mainEntity.length <= 6, `${faq.mainEntity.length} FAQ items`);
  const visible = PAGE.replace(/<[^>]+>/g, ' ').replace(/&rsquo;/g, '’').replace(/&ldquo;/g, '“')
    .replace(/&rdquo;/g, '”').replace(/&amp;/g, '&').replace(/\s+/g, ' ');
  for (const q of faq.mainEntity) {
    assert.ok(visible.includes(q.name), `question not visible: ${q.name}`);
    assert.ok(visible.includes(q.acceptedAnswer.text), `answer not visible: ${q.name}`);
  }
});

test('PAGE CSS is fully scoped under #wq-root and classes use the wq- prefix', () => {
  const css = (PAGE.match(/<style>([\s\S]*?)<\/style>/) || [])[1].replace(/\/\*[\s\S]*?\*\//g, '');
  const selectors = [...css.matchAll(/([^{}]+)\{/g)].map((x) => x[1].trim()).filter((s) => s && !s.startsWith('@'));
  for (const group of selectors) {
    for (const s of group.split(',')) assert.ok(s.trim().startsWith('#wq-root'), `unscoped selector: ${s.trim()}`);
  }
  const classes = [...PAGE.matchAll(/class="([^"'+]+)/g)].flatMap((x) => x[1].trim().split(/\s+/)).filter(Boolean);
  for (const c of classes) assert.ok(c.startsWith('wq-'), `class without wq- prefix: ${c}`);
});

test('PAGE copy avoids hype and unsupported claims', () => {
  const text = PAGE.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, ' ');
  assert.ok(!/perfect match|ultimate|guarantee|vet[- ]reviewed|vet[- ]approved/i.test(text), 'hype or unsupported claim in copy');
});

test('PAGE embedded (compacted) data expands back to the source data exactly', () => {
  const m = PAGE.match(/<script type="application\/json" id="wq-data">([\s\S]*?)<\/script>/);
  const emb = JSON.parse(m[1]);
  const expanded = emb.breeds.map((b) => ({
    ...b,
    sc: Object.fromEntries(emb.dims.map((d, i) => [d, b.sc[i]])),
    img: b.img && !/^https?:\/\//.test(b.img) ? emb.img_base + b.img : b.img
  }));
  if (emb.version === DATA.version && emb.count === BREEDS.length) assert.deepEqual(expanded, BREEDS);
});

test('PAGE copy discloses the fixed deductions, cites the primary studies and matches the question count', () => {
  const text = PAGE.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, ' ').replace(/&rsquo;/g, '’').replace(/\s+/g, ' ');
  assert.ok(/12 quick questions\s*, plus an optional budget question/.test(text), 'lede question count');
  assert.ok(/outside the AKC top 100 lose 3 points/.test(text), 'rare-breed deduction not disclosed');
  assert.ok(/5-point deduction for breathing-related health risks/.test(text), 'flat-face deduction not disclosed');
  assert.ok(/exactly the same score, the one in the AKC top 50 is listed first/.test(text), 'tie-break wording');
  assert.ok(!/Popularity only breaks exact ties/i.test(text), 'tie-break claim contradicts the 3-point availability cut');
  assert.ok(!/next size up or down/.test(text), 'widening copy says up OR down, but code adds both neighbors');
  assert.ok(!/may spread less dander/.test(text), 'unsupported dander claim still present');
  assert.ok(!/aaha\.org/.test(PAGE), 'dead AAHA link still present');
  assert.ok(PAGE.includes('https://pubmed.ncbi.nlm.nih.gov/21819763/') && PAGE.includes('https://pubmed.ncbi.nlm.nih.gov/22728082/'), 'primary studies not linked');
  assert.ok(!/50&ndash;90 lb dog shows up/.test(PAGE), 'false two-band example');
  const ld = JSON.parse(PAGE.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
  assert.ok(/12 quick questions, plus an optional budget question/.test(ld['@graph'][0].description), 'JSON-LD question count');
  assert.ok(/Meta description: Answer 12 quick questions, plus an optional budget question/.test(PAGE), 'meta comment');
});
