"""One-shot fix for the 5 breed groups that failed to publish on Days 12-13.
Tasks:
  1) Replace dead Wikipedia hero URLs in each breed's main + 3 supports.
  2) Convert flat stats dicts to the nested {emoji,label,value} schema.
  3) Re-publish via scripts/generate.py --publish.
"""
import json, sys, subprocess, io
from pathlib import Path

ROOT = Path(__file__).parent
BD = ROOT / 'breed-data'

# Bad URL -> Good URL (verified 200 OK on Wikimedia)
URL_FIXES = {
    'https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Anatolian_Shepherd_Dog_Male.jpg/330px-Anatolian_Shepherd_Dog_Male.jpg':
        'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Anatolian_Shepherd_Dog_01.jpg/330px-Anatolian_Shepherd_Dog_01.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Bullmastiff_edited2.jpg/330px-Bullmastiff_edited2.jpg':
        'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Bullmastiff_edited.JPG/330px-Bullmastiff_edited.JPG',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Dogue_de_Bordeaux_profil.jpg/330px-Dogue_de_Bordeaux_profil.jpg':
        'https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/French_Mastiff_female_4.jpg/330px-French_Mastiff_female_4.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/German_Pinscher_Bonni_vom_Adelssitz_2014.jpg/330px-German_Pinscher_Bonni_vom_Adelssitz_2014.jpg':
        'https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Bvdb-duitse_pincher.jpg/330px-Bvdb-duitse_pincher.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/000_Beagle_header.jpg/330px-000_Beagle_header.jpg':
        'https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Beagle_600.jpg/330px-Beagle_600.jpg',
}

# Per-main-breed size (derived from weight) and beginners assessment
SIZE_BY_BREED = {
    'anatolian-shepherd-dog': ('Giant', 'No'),
    'bullmastiff':            ('Giant', 'No'),
    'dogue-de-bordeaux':      ('Giant', 'No'),
    'tibetan-mastiff':        ('Giant', 'No'),
    'german-pinscher':        ('Medium', 'No'),
}

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


def normalize_stats(slug, flat):
    """Map flat stats to the nested {emoji,label,value} schema used by generate.py."""
    size, beginners = SIZE_BY_BREED[slug]
    weight = flat.get('weight', '')
    lifespan = flat.get('lifespan', '').replace(' years', ' yrs')
    exercise = ENERGY_TO_EXERCISE.get(flat.get('energy_level', 'Moderate'), '60–90 min')
    grooming = flat.get('grooming_needs', 'Moderate')
    training = TRAIN_MAP.get(flat.get('trainability', 'Moderate'), flat.get('trainability', 'Moderate'))
    with_kids = 'Good' if flat.get('good_with_kids') else 'Caution'

    return {
        'size':      {'emoji': '\U0001F4CF', 'label': 'Size',      'value': size},
        'weight':    {'emoji': '⚖️', 'label': 'Weight',  'value': weight},
        'lifespan':  {'emoji': '\U0001F4C5', 'label': 'Lifespan',  'value': lifespan},
        'exercise':  {'emoji': '\U0001F3C3', 'label': 'Exercise',  'value': exercise},
        'grooming':  {'emoji': '✂️', 'label': 'Grooming','value': grooming},
        'training':  {'emoji': '\U0001F393', 'label': 'Training',  'value': training},
        'with_kids': {'emoji': '\U0001F468‍\U0001F469‍\U0001F467',
                      'label': 'With Kids', 'value': with_kids},
        'beginners': {'emoji': '\U0001F331', 'label': 'Beginners', 'value': beginners},
    }


def fix_file(path: Path, normalize_main_stats=False):
    """Read JSON, fix URLs (string replace), optionally normalize stats, write back."""
    raw = path.read_text(encoding='utf-8')
    new = raw
    for bad, good in URL_FIXES.items():
        new = new.replace(bad, good)

    data = json.loads(new)
    changed_stats = False
    if normalize_main_stats:
        slug = path.stem
        if slug in SIZE_BY_BREED:
            stats = data.get('stats')
            if stats and 'height' in stats:  # flat schema marker
                data['stats'] = normalize_stats(slug, stats)
                changed_stats = True

    if new != raw or changed_stats:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True
    return False


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    targets_main = [
        'anatolian-shepherd-dog', 'bullmastiff', 'dogue-de-bordeaux',
        'tibetan-mastiff', 'german-pinscher',
    ]
    targets_supports = []
    for b in ['anatolian-shepherd-dog', 'bullmastiff', 'dogue-de-bordeaux', 'german-pinscher']:
        for suf in ['-grooming-guide', '-first-year-costs', '-puppy-checklist']:
            targets_supports.append(b + suf)
    other = ['best-hound-dog-breeds']

    for slug in targets_main:
        if fix_file(BD / f'{slug}.json', normalize_main_stats=True):
            print(f'  fixed: {slug}')
    for slug in targets_supports + other:
        if fix_file(BD / f'{slug}.json'):
            print(f'  fixed: {slug}')

if __name__ == '__main__':
    main()
