"""Bulk schema fixer for breed-data JSONs that use the old flat schema.
Fixes three issues per main breed:
  1) flat stats -> nested {emoji,label,value}
  2) sections.right_for_you html -> good_fit + not_fit lists
  3) related_breeds [str] -> [{name,slug,note}]
Idempotent: skips files already in the new shape.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
BD = ROOT / 'breed-data'

ENERGY_TO_EXERCISE = {
    'Low':       '30–60 min',
    'Moderate':  '60–90 min',
    'High':      '90+ min',
    'Very High': '2+ hrs/day',
}
TRAIN_MAP = {
    'Easy':              'Easy',
    'Moderate':          'Moderate',
    'Easy to Moderate':  'Easy–Moderate',
    'Difficult':         'Challenging',
    'Very Difficult':    'Very Challenging',
}


def parse_weight_lbs(weight_str):
    """Return middle of weight range in lbs, or None."""
    nums = re.findall(r'\d+', weight_str or '')
    if not nums:
        return None
    nums = [int(n) for n in nums]
    return sum(nums) / len(nums)


def derive_size(weight_str, height_str):
    w = parse_weight_lbs(weight_str)
    if w is not None:
        if w >= 100: return 'Giant'
        if w >= 55:  return 'Large'
        if w >= 25:  return 'Medium'
        if w >= 12:  return 'Small'
        return 'Toy'
    # fallback by height
    nums = re.findall(r'\d+', height_str or '')
    if nums:
        h = sum(int(n) for n in nums) / len(nums)
        if h >= 26: return 'Large'
        if h >= 18: return 'Medium'
        if h >= 11: return 'Small'
        return 'Toy'
    return 'Medium'


def derive_beginners(training, energy):
    if training in ('Easy', 'Easy to Moderate') and energy in ('Low', 'Moderate'):
        return 'Yes'
    if training in ('Difficult', 'Very Difficult'):
        return 'No'
    return 'Caution'


def normalize_stats(flat):
    weight = flat.get('weight', '')
    height = flat.get('height', '')
    lifespan = (flat.get('lifespan', '') or '').replace(' years', ' yrs')
    energy = flat.get('energy_level', 'Moderate')
    grooming = flat.get('grooming_needs', 'Moderate')
    trainability = flat.get('trainability', 'Moderate')

    return {
        'size':      {'emoji': '\U0001F4CF', 'label': 'Size',      'value': derive_size(weight, height)},
        'weight':    {'emoji': '⚖️', 'label': 'Weight',  'value': weight},
        'lifespan':  {'emoji': '\U0001F4C5', 'label': 'Lifespan',  'value': lifespan},
        'exercise':  {'emoji': '\U0001F3C3', 'label': 'Exercise',  'value': ENERGY_TO_EXERCISE.get(energy, '60–90 min')},
        'grooming':  {'emoji': '✂️', 'label': 'Grooming','value': grooming},
        'training':  {'emoji': '\U0001F393', 'label': 'Training',  'value': TRAIN_MAP.get(trainability, trainability)},
        'with_kids': {'emoji': '\U0001F468‍\U0001F469‍\U0001F467',
                      'label': 'With Kids', 'value': 'Good' if flat.get('good_with_kids') else 'Caution'},
        'beginners': {'emoji': '\U0001F331', 'label': 'Beginners',
                      'value': derive_beginners(trainability, energy)},
    }


GOOD_TRIGGERS = [
    # Generic: anything that includes "great"/"good"/"right"/"ideal" + "if you" / "for you"
    r'<strong>[^<]*\b(?:great\s+match|good\s+match|great\s+fit|right\s+for\s+you|ideal\s+for\s+you|might\s+be\s+ideal|might\s+be\s+a\s+great|may\s+be\s+right|might\s+be\s+right|is\s+probably\s+right|is\s+a\s+good\s+match|is\s+right\s+for\s+you|is\s+a\s+great\s+fit|is\s+best\s+for|may\s+be\s+a\s+great|might\s+suit\s+you)[^<]*[:\s]*</strong>',
]
BAD_TRIGGERS = [
    r'<strong>[^<]*\b(?:not\s+a\s+good\s+match|may\s+not\s+be\s+right|may\s+NOT\s+be\s+right|is\s+not\s+right|not\s+right\s+for\s+you|is\s+likely\s+not|is\s+not\s+for\s+you|is\s+not\s+the\s+right|not\s+suitable\s+for|might\s+not\s+be\s+the\s+right|not\s+the\s+right\s+breed|not\s+the\s+right\s+choice|not\s+for\s+you|may\s+not\s+suit|might\s+not\s+suit|not\s+a\s+great\s+match|less\s+suitable|may\s+NOT\s+be\s+a\s+good|not\s+appropriate|not\s+ideal)[^<]*[:\s]*</strong>',
]


def extract_block(html, trigger_patterns):
    """Find the block of text/list immediately after the first matching trigger."""
    for pat in trigger_patterns:
        m = re.search(pat, html, flags=re.IGNORECASE)
        if not m:
            continue
        start = m.end()
        # Take up to next <strong> or end of <p>... or end of html
        rest = html[start:]
        end_strong = rest.find('<strong>')
        if end_strong == -1:
            end_strong = len(rest)
        chunk = rest[:end_strong]
        return chunk
    return None


def items_from_chunk(chunk):
    """Try <li> first, then sentence-split."""
    if not chunk:
        return []
    li_items = re.findall(r'<li[^>]*>(.*?)</li>', chunk, flags=re.DOTALL | re.IGNORECASE)
    items = [re.sub(r'<[^>]+>', '', it).strip() for it in li_items]
    items = [it for it in items if it]
    if items:
        return items
    # Sentence-split: strip tags, split on '. '
    text = re.sub(r'<[^>]+>', ' ', chunk)
    text = re.sub(r'\s+', ' ', text).strip()
    # Trim leading colon residue
    text = text.lstrip(': ').strip()
    raw = [s.strip() for s in re.split(r'(?<=[\.!?])\s+(?=[A-Z])', text) if s.strip()]
    out = []
    for s in raw:
        s = s.rstrip('.').strip()
        if 8 < len(s) < 200:
            out.append(s)
    return out


GENERIC_FALLBACK_GOOD = [
    'Owners who can match the breed\'s exercise and training needs',
    'Households committed to early socialization and consistent boundaries',
    'People who enjoy daily engagement and active companionship with their dog',
    'Homes with the appropriate space and lifestyle for the breed\'s energy level',
    'Owners who have researched the breed and understand its temperament',
]
GENERIC_FALLBACK_BAD = [
    'Households unable to commit to the breed\'s daily exercise needs',
    'Owners wanting a low-maintenance or hands-off pet',
    'First-time dog owners unfamiliar with this breed type',
    'Living situations that don\'t match the breed\'s space requirements',
    'Anyone unprepared for the grooming or training time the breed demands',
]


GOOD_PARA_HINTS = ('excellent choice', 'good match', 'right for', 'suits ', 'great fit',
                   'is a wonderful', 'is best suited', 'thrives', 'rewards owners', 'recommended for',
                   'broadly suitable', 'works well for', 'outstanding choice', 'ideal companion',
                   'wonderful choice', 'a great breed for')
BAD_PARA_HINTS = ('is not', 'less suitable', 'not the right', 'not suitable', 'not recommended',
                  'should be avoided', 'is not for', 'unsuitable', 'not appropriate',
                  'cannot be', 'not ideal for', 'should not')

# Phrases that mark the start of "not for" content within a single paragraph
BAD_INLINE_MARKERS = re.compile(
    r'\b(?:is not|It is not|is not the|not the right|not suitable|not appropriate|'
    r'not ideal|less suitable|not recommended|should not|not for owners|not for households)\b',
    flags=re.IGNORECASE,
)


def split_paragraph_to_items(text, prefix=None):
    """Take a prose paragraph, split into clauses by ', ' / sentence boundary, return as items."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    # Strip the leading sentence intro ("It is not the right choice for owners who...")
    # Specifically pull the predicate after "for ", "if you ", or "to "
    raw = re.split(r'(?<=[\.;])\s+', text)
    items = []
    for sent in raw:
        sent = sent.strip().rstrip('.;,')
        if len(sent) < 12 or len(sent) > 220: continue
        # Try to split conjunction "for X, Y, and Z" type lists into sub-items
        m = re.search(r'(?:right for|suitable for|choice for|best suited for|not for|not suitable for|not the right choice for|less suitable for|not recommended for)\s+(.*)', sent, flags=re.IGNORECASE)
        if m:
            sub = m.group(1)
            # Mask anything in parens so we don't shred lists like "(birds, cats)"
            masked = re.sub(r'\([^)]*\)', lambda mm: mm.group(0).replace(',', ''), sub)
            parts = re.split(r',\s*(?:or|and)?\s*|\s+or\s+', masked)
            for p in parts:
                p = p.replace('', ',').strip().rstrip('.;,')
                if 8 < len(p) < 180:
                    items.append(p[0].upper() + p[1:] if p else p)
            continue
        items.append(sent)
    # Dedup preserving order
    seen, out = set(), []
    for it in items:
        k = it.lower()[:60]
        if k not in seen:
            seen.add(k); out.append(it)
    return out


def parse_paragraphs_fallback(html):
    """Fallback: split each <p>…</p> into good/bad halves at the first 'is not' style marker."""
    paras = re.findall(r'<p[^>]*>(.*?)</p>', html, flags=re.DOTALL | re.IGNORECASE)
    good, bad = [], []
    for p in paras:
        plain = re.sub(r'<[^>]+>', ' ', p)
        m = BAD_INLINE_MARKERS.search(plain)
        if m:
            good_part = plain[:m.start()].strip()
            bad_part = plain[m.start():].strip()
            # If good part is too short, the whole paragraph is bad
            if len(good_part) < 30:
                bad.extend(split_paragraph_to_items(bad_part))
            else:
                good.extend(split_paragraph_to_items(good_part))
                bad.extend(split_paragraph_to_items(bad_part))
        else:
            lower = plain.lower()
            if any(h in lower for h in GOOD_PARA_HINTS):
                good.extend(split_paragraph_to_items(plain))
    return good, bad


def parse_right_for_you(rfy):
    html = rfy.get('html', '') or ''
    good_chunk = extract_block(html, GOOD_TRIGGERS)
    bad_chunk = extract_block(html, BAD_TRIGGERS)
    good = items_from_chunk(good_chunk)[:5]
    bad = items_from_chunk(bad_chunk)[:5]
    # If primary parse weak, try paragraph-classification fallback
    if len(good) < 3 or len(bad) < 3:
        g2, b2 = parse_paragraphs_fallback(html)
        if len(good) < 3 and g2:
            good = g2[:5]
        if len(bad) < 3 and b2:
            bad = b2[:5]
    if len(good) < 3:
        good = (good + GENERIC_FALLBACK_GOOD)[:5]
    if len(bad) < 3:
        bad = (bad + GENERIC_FALLBACK_BAD)[:5]
    return good, bad


def normalize_related(slug, related_list):
    out = []
    for rel in related_list:
        if isinstance(rel, dict):
            out.append(rel)
            continue
        if not isinstance(rel, str):
            continue
        rp = BD / f'{rel}.json'
        name = rel.replace('-', ' ').title()
        if rp.exists():
            try:
                rd = json.loads(rp.read_text(encoding='utf-8'))
                name = rd.get('meta', {}).get('name', name)
            except Exception:
                pass
        out.append({'name': name, 'slug': rel, 'note': f'Related breed worth comparing'})
    return out


def fix_main(slug):
    path = BD / f'{slug}.json'
    if not path.exists():
        return False, 'JSON_MISSING'
    d = json.loads(path.read_text(encoding='utf-8'))
    changed = []

    stats = d.get('stats')
    if stats and ('height' in stats or 'energy_level' in stats):
        d['stats'] = normalize_stats(stats)
        changed.append('stats')

    rfy = d.get('sections', {}).get('right_for_you')
    if rfy and 'good_fit' not in rfy:
        good, bad = parse_right_for_you(rfy)
        rfy['good_fit'] = good
        rfy['not_fit'] = bad
        rfy.pop('html', None)
        changed.append('right_for_you')

    rb = d.get('related_breeds')
    if rb and isinstance(rb[0], str):
        d['related_breeds'] = normalize_related(slug, rb)
        changed.append('related_breeds')

    if changed:
        path.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding='utf-8')
    return bool(changed), ','.join(changed) if changed else 'no-op'


def fix_support(slug):
    """Supports should not carry stats / related_breeds; canonical schema has them null.
    Remove them if they exist with the old flat shape."""
    path = BD / f'{slug}.json'
    if not path.exists():
        return False, 'JSON_MISSING'
    d = json.loads(path.read_text(encoding='utf-8'))
    changed = []
    if d.get('stats') and isinstance(d['stats'], dict) and ('height' in d['stats'] or 'energy_level' in d['stats']):
        d.pop('stats', None)
        changed.append('stats-removed')
    rb = d.get('related_breeds')
    if rb and isinstance(rb, list) and rb and isinstance(rb[0], str):
        d.pop('related_breeds', None)
        changed.append('related_breeds-removed')
    if changed:
        path.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding='utf-8')
    return bool(changed), ','.join(changed) if changed else 'no-op'


TARGETS = [
    'cairn-terrier','miniature-bull-terrier','parson-russell-terrier','russell-terrier','australian-terrier',
    'kerry-blue-terrier','lakeland-terrier','scottish-terrier','brussels-griffon','chinese-crested',
    'miniature-pinscher','papillon','pekingese','japanese-chin','american-eskimo-dog','chinese-shar-pei','coton-de-tulear',
    'silky-terrier','toy-fox-terrier','finnish-spitz','norfolk-terrier',
    'norwich-terrier','skye-terrier','welsh-terrier','wire-fox-terrier','lowchen','schipperke','tibetan-spaniel',
    'bearded-collie','bouvier-des-flandres','beauceron','belgian-sheepdog',
    'belgian-tervuren','briard','entlebucher-mountain-dog','finnish-lapphund','icelandic-sheepdog','polish-lowland-sheepdog','puli',
    'swedish-vallhund',
]

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    fixed = 0
    for slug in TARGETS:
        ok, msg = fix_main(slug)
        marker = 'FIXED' if ok else '-----'
        print(f'  [{marker}] {slug}: {msg}')
        if ok: fixed += 1
    print(f'\nMains fixed: {fixed}/{len(TARGETS)}')

    sup_fixed = 0
    sup_total = 0
    for slug in TARGETS:
        for suf in ['-grooming-guide', '-first-year-costs', '-puppy-checklist']:
            sup_total += 1
            ok, msg = fix_support(slug + suf)
            if ok:
                sup_fixed += 1
                print(f'  [SUP] {slug+suf}: {msg}')
    print(f'Supports cleaned: {sup_fixed}/{sup_total}')
