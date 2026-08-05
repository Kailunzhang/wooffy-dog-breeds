import json, os

# Load all needed breed data
breeds_needed = [
    'border-collie', 'standard-poodle', 'german-shepherd-dog', 'golden-retriever',
    'doberman-pinscher', 'shetland-sheepdog', 'labrador-retriever', 'papillon',
    'rottweiler', 'australian-cattle-dog', 'australian-shepherd', 'english-springer-spaniel',
    'chihuahua', 'dachshund', 'maltese', 'beagle', 'yorkshire-terrier', 'pomeranian',
    'miniature-pinscher', 'havanese', 'parson-russell-terrier', 'shih-tzu', 'toy-fox-terrier',
    'vizsla', 'dalmatian', 'basenji', 'greyhound', 'italian-greyhound', 'weimaraner',
    'ibizan-hound', 'saluki', 'pharaoh-hound', 'siberian-husky', 'alaskan-malamute',
    'rhodesian-ridgeback', 'boxer', 'great-dane', 'mastiff', 'saint-bernard',
    'bernese-mountain-dog', 'great-pyrenees', 'cane-corso', 'pug', 'pekingese',
    'bulldog', 'chow-chow', 'shiba-inu', 'boston-terrier', 'keeshond', 'schipperke',
    'american-eskimo-dog', 'tibetan-spaniel', 'collie', 'akita', 'basset-hound',
    'bloodhound', 'cavalier-king-charles-spaniel', 'cocker-spaniel', 'bichon-frise',
    'whippet', 'newfoundland', 'otterhound', 'norwegian-elkhound', 'komondor',
    'xoloitzcuintli', 'american-water-spaniel', 'harrier', 'skye-terrier', 'finnish-spitz',
    'tibetan-mastiff', 'samoyed', 'portuguese-water-dog', 'irish-wolfhound',
    'french-bulldog', 'airedale-terrier', 'west-highland-white-terrier'
]

B = {}
for slug in breeds_needed:
    fpath = f'breed-data/{slug}.json'
    if not os.path.exists(fpath):
        print(f'MISSING: {slug}')
        continue
    with open(fpath, encoding='utf-8') as f:
        d = json.load(f)
    img = d.get('images', {})
    if isinstance(img, dict):
        hero = img.get('hero', {})
    elif isinstance(img, list) and img:
        hero = img[0] if isinstance(img[0], dict) else {}
    else:
        hero = {}
    stats = d.get('stats', {})
    if isinstance(stats, dict):
        if isinstance(stats.get('size'), dict):
            size_val = stats['size'].get('value', '')
            lifespan_val = stats.get('lifespan', {}).get('value', '') if isinstance(stats.get('lifespan'), dict) else stats.get('lifespan', '')
            exercise_val = stats.get('exercise', {}).get('value', '') if isinstance(stats.get('exercise'), dict) else stats.get('energy_level', '')
        else:
            lifespan_val = stats.get('lifespan', '')
            size_val = stats.get('weight', '')
            exercise_val = stats.get('energy_level', '')
    else:
        size_val = lifespan_val = exercise_val = ''
    B[slug] = {
        'img_url': hero.get('url', ''),
        'img_alt': hero.get('alt', slug.replace('-', ' ').title()),
        'size': size_val,
        'lifespan': lifespan_val,
        'exercise': exercise_val,
    }

print(f'Loaded {len(B)} breeds')


def card(slug, name, desc, size_tag=None, trait_tag=None, lifespan_tag=None):
    info = B.get(slug, {})
    img_url = info.get('img_url', '')
    img_alt = info.get('img_alt', name)
    s_tag = size_tag or info.get('size', 'Medium') or 'Medium'
    l_tag = lifespan_tag or info.get('lifespan', '') or ''
    t_tag = trait_tag or info.get('exercise', '') or ''
    return (
        '<div style="background:#ffffff;border:1px solid rgba(0,0,0,0.08);border-radius:12px;overflow:hidden;">'
        f'<a href="/blogs/dog-breeds/{slug}" class="wf-card-img" style="display:block;"><img src="{img_url}" alt="{img_alt}" style="width:100%;aspect-ratio:3/2;height:auto;object-fit:cover;display:block;"></a>'
        '<div style="padding:16px;">'
        f'<h3 style="font-size:1em;font-weight:700;color:#1a1a1a;margin:0 0 8px 0;">{name}</h3>'
        '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">'
        f'<span style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.65em;background:#f0f0f0;border-radius:20px;padding:3px 10px;color:#555;">{s_tag}</span>'
        f'<span style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.65em;background:#f0f0f0;border-radius:20px;padding:3px 10px;color:#555;">{t_tag}</span>'
        f'<span style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.65em;background:#f0f0f0;border-radius:20px;padding:3px 10px;color:#555;">{l_tag} lifespan</span>'
        '</div>'
        f'<p style="font-size:0.85em;line-height:1.6;color:#6b7177;margin:0 0 12px 0;">{desc}</p>'
        f'<a href="/blogs/dog-breeds/{slug}" style="font-size:0.8em;font-weight:600;color:#000000;text-decoration:underline;text-underline-offset:3px;">Full guide \u2192</a>'
        '</div></div>'
    )


def grid(cards):
    return '<style>@media (max-width:640px){.wf-breed-grid{grid-template-columns:1fr !important;}}</style><div class="wf-breed-grid" style="display:grid;grid-template-columns:repeat(2,1fr);gap:20px;">' + ''.join(cards) + '</div>'


def save(slug, data):
    path = f'breed-data/{slug}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(path, encoding='utf-8') as f:
        json.load(f)
    print(f'  SAVED & VALIDATED: {slug}.json')


# ─── 11. quietest-dog-breeds ──────────────────────────────────────────────
cards_11 = [
    card('basenji', 'Basenji',
         "The Basenji is famously the \"barkless dog\" \u2014 due to its unusually shaped larynx, it cannot produce a typical bark, instead making a melodious yodel called a \"barroo.\" For owners who need a truly quiet dog, the Basenji is the obvious first choice.",
         size_tag='Small\u2013Medium', trait_tag='Barkless'),
    card('greyhound', 'Greyhound',
         'Retired racing Greyhounds are renowned for their calm, gentle temperament and extremely low barking tendencies. Despite their athletic past, they are quiet homebodies who spend most of their time lounging and rarely vocalize unnecessarily.',
         size_tag='Large', trait_tag='Calm & Quiet'),
    card('shih-tzu', 'Shih Tzu',
         'Shih Tzus are much quieter than their small-breed peers, particularly when raised in calm households. Their gentle, adaptable temperament means they rarely feel the need to bark at every noise, making them a good choice for apartments.',
         size_tag='Small', trait_tag='Gentle'),
    card('cavalier-king-charles-spaniel', 'Cavalier King Charles Spaniel',
         'Cavaliers are among the quietest spaniels and one of the most reliably calm small dogs. They were bred purely for companionship and have a soft, adaptable temperament that rarely produces excessive barking.',
         size_tag='Small', trait_tag='Gentle Companion'),
    card('whippet', 'Whippet',
         'Whippets are one of the quietest medium-sized breeds \u2014 elegant, gentle dogs who are more likely to cuddle on the couch than bark at passing traffic. Their sensitive temperament makes them easy to live with in close quarters.',
         size_tag='Medium', trait_tag='Quiet & Gentle'),
    card('italian-greyhound', 'Italian Greyhound',
         'Like their larger Greyhound relatives, Italian Greyhounds are generally quiet dogs who rarely bark without reason. Their sensitive, gentle nature means they prefer a calm household and tend to reflect the noise level of their environment.',
         size_tag='Toy', trait_tag='Sensitive & Quiet'),
    card('bernese-mountain-dog', 'Bernese Mountain Dog',
         'Despite their large size, Berners are calm, even-tempered dogs who rarely bark excessively. They are naturally gentle and tend to alert bark only when genuinely warranted, making them surprisingly quiet companions for their impressive stature.',
         size_tag='Large', trait_tag='Calm'),
    card('great-dane', 'Great Dane',
         'Great Danes are gentle giants with a calm, dignified demeanor. Despite their imposing size and deep bark, they rarely bark frequently \u2014 most are remarkably quiet in day-to-day life and only vocalize when something genuinely warrants attention.',
         size_tag='Giant', trait_tag='Dignified'),
    card('maltese', 'Maltese',
         'While some small breeds are notorious barkers, well-trained Maltese are among the quieter toy breeds. Their gentle, loving temperament makes them more interested in being close to their owner than alerting to every noise.',
         size_tag='Small', trait_tag='Gentle'),
    card('newfoundland', 'Newfoundland',
         'Newfoundlands are known for their exceptionally calm, patient temperament \u2014 they are among the quietest giant breeds and rarely bark excessively. Their deep, resonant bark when they do vocalize is all the deterrent most situations require.',
         size_tag='Giant', trait_tag='Patient & Calm'),
]

save('quietest-dog-breeds', {
    "meta": {
        "name": "Quietest Dog Breeds",
        "slug": "quietest-dog-breeds",
        "shopify_handle": "quietest-dog-breeds",
        "group": "Breed Guides",
        "size_category": "Roundup",
        "tags": ["quietest dog breeds", "dogs that don't bark", "low-barking dogs"],
        "published": True,
        "published_at": "2026-05-16T16:00:00Z",
        "excerpt": "Whether you live in an apartment, have noise-sensitive neighbors, or simply prefer a peaceful household, these 10 dog breeds are known for their notably quiet, calm natures.",
        "meta_description": "Discover the 10 quietest dog breeds, from the barkless Basenji to the gentle Great Dane. Find low-barking dogs perfect for apartments and quiet households."
    },
    "images": {"hero": {"url": B['basenji']['img_url'], "alt": "Quietest Dog Breeds"}},
    "sections": {
        "intro": {
            "label": "Overview",
            "heading": "Quietest Dog Breeds",
            "html": "<p>Barking is natural dog behavior, but its frequency and intensity vary enormously between breeds. Dogs that were historically bred to alert hunters or farmers to intruders \u2014 like Beagles, Miniature Schnauzers, and many terriers \u2014 have a strong genetic tendency to vocalize. Dogs bred for calm companionship, independent work in remote terrain, or racing tend to be much quieter. If you live in an apartment, have close neighbors, or simply prefer a quieter household, breed selection is one of the most important factors in your daily noise level.</p><p>It's important to note that even the quietest breeds can develop barking habits if they are bored, anxious, or inadequately exercised. A quiet breed raised in an environment of insufficient stimulation will still bark. The breeds on this list simply start with a much lower baseline tendency to vocalize and are easier to keep quiet with proper care.</p>"
        },
        "care": {
            "label": "Breeds",
            "heading": "10 Quietest Dog Breeds",
            "html": grid(cards_11)
        },
        "special": {
            "label": "Tips",
            "heading": "Managing Barking in Any Breed",
            "html": "<p>Even with a naturally quiet breed, training and environment management play important roles. Never reward barking with attention, even negative attention \u2014 any response reinforces the behavior. Instead, redirect quietly or wait for silence before interacting. Teaching a \"quiet\" command on cue is far more effective than trying to suppress barking reactively.</p><p>Ensure your dog gets adequate exercise and mental stimulation. A bored dog \u2014 of any breed \u2014 finds outlets for its energy, and barking is one of the easiest. Puzzle feeders, training sessions, and regular outdoor activity address the root cause of most excessive barking. For anxiety-related barking, consult a veterinary behaviorist rather than attempting to suppress the symptom without addressing the underlying cause.</p>"
        }
    },
    "faq": [
        {"q": "What dog breed barks the least?", "a": "The Basenji is the only breed that literally cannot produce a normal bark, making it the anatomically quietest. Among breeds that can bark, Greyhounds, Whippets, and Newfoundlands are among the least vocally active. The Cavalier King Charles Spaniel and Shih Tzu are among the quietest small breeds."},
        {"q": "Do quiet dogs make good apartment dogs?", "a": "Yes \u2014 low-barking breeds are excellent apartment dogs, provided their other needs are also met. A quiet breed that requires two hours of vigorous exercise per day is still not an ideal apartment dog. The best apartment dogs combine low barking with moderate exercise needs \u2014 breeds like the Cavalier King Charles Spaniel, Shih Tzu, and Italian Greyhound fit this profile well."},
        {"q": "Can you train a dog to stop barking?", "a": "Yes, though the ease depends on the breed and the reason for barking. Alert-barking and demand-barking respond well to training: ignore the behavior, reward silence, and teach a specific \"quiet\" command. Anxiety-driven or compulsive barking requires addressing the underlying cause, which may involve behavior modification, environmental management, and sometimes medication prescribed by a veterinarian."},
        {"q": "What small dogs are quiet?", "a": "Among small breeds, the Basenji, Italian Greyhound, Cavalier King Charles Spaniel, Shih Tzu, and well-trained Maltese are the quietest options. Small dogs as a category tend to bark more than large breeds \u2014 it is an important consideration when selecting a small dog for apartment living. Terriers and spitz breeds are particularly prone to barking regardless of size."}
    ]
})


# ─── 12. rarest-dog-breeds ──────────────────────────────────────────────────
cards_12 = [
    card('otterhound', 'Otterhound',
         'With fewer than 1,000 individuals worldwide, the Otterhound is one of the rarest dog breeds in existence \u2014 rarer than many endangered wild animals. Bred in England to hunt otters, they have a shaggy double coat, webbed feet, and a booming deep voice.',
         size_tag='Large', trait_tag='Endangered Breed'),
    card('norwegian-elkhound', 'Norwegian Elkhound',
         "One of Scandinavia's oldest breeds, the Norwegian Elkhound has hunted elk, bear, and moose alongside Vikings for thousands of years. They are rare outside Scandinavia and remain working hunting dogs in their homeland.",
         size_tag='Medium', trait_tag='Ancient Hunter'),
    card('komondor', 'Komondor',
         'The Komondor\'s extraordinary corded white coat \u2014 which can take years to develop \u2014 is one of the most distinctive in the dog world. Bred as a Hungarian livestock guardian, they are rare globally and require experienced, committed owners.',
         size_tag='Large', trait_tag='Livestock Guardian'),
    card('xoloitzcuintli', 'Xoloitzcuintli',
         "Mexico's ancient hairless dog \u2014 pronounced \"show-low-eets-QUEENT-lee\" \u2014 is one of the oldest and rarest breeds in the world, with a history spanning 3,000 years of Aztec civilization. Both hairless and coated varieties exist in three sizes.",
         size_tag='Toy/Mini/Standard', trait_tag='Ancient Heritage'),
    card('pharaoh-hound', 'Pharaoh Hound',
         'The national dog of Malta is one of the oldest sighthound breeds in the world, with origins traceable to ancient Egypt. Their most remarkable trait is blushing \u2014 their ears and nose turn rosy pink when they are excited.',
         size_tag='Medium', trait_tag='Rare & Ancient'),
    card('ibizan-hound', 'Ibizan Hound',
         'Native to the Balearic Islands of Spain, the Ibizan Hound has been used for hunting rabbits since Phoenician traders brought their ancestors to the islands centuries ago. Both smooth and wire-coated varieties exist, and both are extremely rare.',
         size_tag='Large', trait_tag='Ancient Sighthound'),
    card('american-water-spaniel', 'American Water Spaniel',
         "One of the few breeds native to the United States, the American Water Spaniel was developed in the Great Lakes region for waterfowl hunting. Despite being Wisconsin's state dog, it remains one of the rarest spaniels in the world.",
         size_tag='Medium', trait_tag='American Native'),
    card('harrier', 'Harrier',
         'The Harrier is a scenthound developed in England for hare hunting \u2014 essentially a larger Beagle. They are extremely rare even in their country of origin, with very small numbers registered globally each year.',
         size_tag='Medium', trait_tag='Rare Scenthound'),
    card('skye-terrier', 'Skye Terrier',
         "Scotland's elegant long-bodied terrier is critically rare, with very few puppies born each year. Famous for Greyfriars Bobby \u2014 a Skye Terrier who guarded his owner's grave for 14 years \u2014 the breed faces an uncertain future without dedicated breeders.",
         size_tag='Medium', trait_tag='Critically Rare'),
    card('finnish-spitz', 'Finnish Spitz',
         "Finland's national dog was bred to hunt birds and small game in boreal forests. Their fox-like appearance, golden-red coat, and distinctive \"yodeling\" bark set them apart. They remain rare outside Finland and Nordic countries.",
         size_tag='Medium', trait_tag='National Treasure'),
]

save('rarest-dog-breeds', {
    "meta": {
        "name": "Rarest Dog Breeds",
        "slug": "rarest-dog-breeds",
        "shopify_handle": "rarest-dog-breeds",
        "group": "Breed Guides",
        "size_category": "Roundup",
        "tags": ["rarest dog breeds", "rare dogs", "uncommon dog breeds"],
        "published": True,
        "published_at": "2026-05-17T16:00:00Z",
        "excerpt": "Some of the world's most fascinating dog breeds are also the hardest to find. From the critically endangered Otterhound to the ancient Xoloitzcuintli, these 10 rare breeds are as unique as they are uncommon.",
        "meta_description": "Discover the 10 rarest dog breeds in the world, from Otterhounds to Finnish Spitz. Learn about critically rare and endangered dog breeds with fascinating histories."
    },
    "images": {"hero": {"url": B['otterhound']['img_url'], "alt": "Rarest Dog Breeds"}},
    "sections": {
        "intro": {
            "label": "Overview",
            "heading": "Rarest Dog Breeds in the World",
            "html": "<p>While breeds like the Labrador Retriever and French Bulldog are registered in the hundreds of thousands each year, other breeds \u2014 many with histories stretching thousands of years \u2014 exist in populations so small they face genuine risk of extinction. The Otterhound, for example, has fewer than 1,000 individuals worldwide \u2014 fewer than many endangered wild species. These rare breeds often represent irreplaceable genetic diversity, unique working abilities, and deep cultural heritage.</p><p>Owning a rare breed comes with unique considerations: finding a reputable breeder may require significant time and travel, genetic health information may be limited, and veterinary specialists may have little experience with breed-specific conditions. But for dedicated enthusiasts, rare breeds offer a profound connection to canine history and the opportunity to be part of preserving something truly irreplaceable.</p>"
        },
        "care": {
            "label": "Breeds",
            "heading": "10 Rarest Dog Breeds",
            "html": grid(cards_12)
        },
        "special": {
            "label": "Conservation",
            "heading": "Preserving Rare Dog Breeds",
            "html": "<p>Many rare dog breeds are classified as \"vulnerable native breeds\" by kennel clubs in their countries of origin. The UK Kennel Club, for example, identifies breeds with fewer than 300 annual registrations as vulnerable, and several on this list fall well below that threshold. Breed preservation efforts focus on maintaining genetic diversity while preserving the original working type and temperament for which each breed was developed.</p><p>If you are considering a rare breed, connecting with the dedicated parent breed club in your country is the most important first step. These clubs maintain breeder registries, health testing protocols, and breed preservation programs. Supporting ethical breeders of rare breeds is one of the most direct ways to ensure these fascinating dogs remain part of our world for future generations.</p>"
        }
    },
    "faq": [
        {"q": "What is the rarest dog breed in the world?", "a": "The Otterhound is widely considered the rarest recognized dog breed in the world, with an estimated global population of fewer than 1,000 individuals and only a handful of dedicated breeders worldwide. Other critically rare breeds include the Skye Terrier, Cesky Terrier, and Harrier, all of which register very few puppies annually even in their countries of origin."},
        {"q": "Why are some dog breeds becoming extinct?", "a": "Most rare breeds face decline because the working role they were developed for no longer exists. Otterhounds were bred for otter hunting, which was banned in the UK in 1978. Skye Terriers were bred for badger hunting in specific Scottish terrain. As these specialized working roles disappeared, so did the practical motivation to breed these dogs. Only the efforts of dedicated breed enthusiasts maintain these populations."},
        {"q": "Are rare dog breeds more expensive?", "a": "Yes, rare breeds are typically more expensive than common breeds due to limited availability of reputable breeders and the additional expense of health testing in small populations. Wait lists of one to three years are common for the rarest breeds. The Xoloitzcuintli, Komondor, and Pharaoh Hound can cost significantly more than their more common counterparts."},
        {"q": "Can I adopt a rare dog breed from a shelter?", "a": "It is possible but very unlikely to find truly rare breeds in shelters. Breed-specific rescues for rare breeds do exist and maintain lists of dogs in need of homes \u2014 these are worth contacting if you are interested in a particular rare breed. More commonly, rare breed owners who can no longer keep their dogs contact the parent breed club, which maintains informal rehoming networks."}
    ]
})


# ─── 13. most-expensive-dog-breeds ──────────────────────────────────────────
cards_13 = [
    card('tibetan-mastiff', 'Tibetan Mastiff',
         'The Tibetan Mastiff holds the record for the world\'s most expensive dog sale \u2014 a red Tibetan Mastiff puppy sold for $1.5 million in China in 2014. Even typical puppies from reputable breeders cost $3,000\u2013$10,000, driven by their ancient heritage, imposing size, and rarity.',
         size_tag='Giant', trait_tag='Record-Holder'),
    card('chow-chow', 'Chow Chow',
         'Chow Chows command premium prices due to their distinctive appearance, ancient lineage, and the careful health testing required in responsible breeding programs. Quality puppies from health-tested parents typically cost $2,000\u2013$8,500.',
         size_tag='Large', trait_tag='Premium Breed'),
    card('rottweiler', 'Rottweiler',
         'Working-line Rottweilers from European imports with titles in Schutzhund or IGP command the highest prices, sometimes exceeding $10,000. Even companion-quality Rottweilers from health-tested, titled parents regularly cost $2,500\u2013$5,000.',
         size_tag='Large', trait_tag='Working Line Premium'),
    card('akita', 'Akita',
         'Japanese Akitas \u2014 the original type, distinct from American Akitas \u2014 are particularly expensive and rare outside Japan. Both varieties from quality breeders cost $2,000\u2013$4,500, with show and breeding quality dogs considerably more.',
         size_tag='Large', trait_tag='Japanese Heritage'),
    card('samoyed', 'Samoyed',
         'The Samoyed\'s stunning white coat, cheerful temperament, and rarity make them one of the most expensive medium-large breeds. Quality puppies from health-tested, titled parents typically cost $3,000\u2013$8,000, reflecting significant investment in health testing.',
         size_tag='Medium', trait_tag='Rare & Beautiful'),
    card('great-dane', 'Great Dane',
         'Despite being relatively common, Great Danes from quality breeders with comprehensive health testing for heart conditions and bloat cost $1,500\u2013$3,500. Their ongoing costs \u2014 food, medical care, supplies \u2014 are among the highest of any breed.',
         size_tag='Giant', trait_tag='High Lifetime Cost'),
    card('bernese-mountain-dog', 'Bernese Mountain Dog',
         "Berners are expensive to purchase ($2,500\u2013$5,000) and to own, largely due to their health challenges \u2014 they are prone to cancer and have a shorter lifespan than most large breeds. Comprehensive health testing from reputable breeders adds to purchase price but reduces lifetime veterinary costs.",
         size_tag='Large', trait_tag='Health-Tested'),
    card('portuguese-water-dog', 'Portuguese Water Dog',
         "The Portuguese Water Dog became globally famous when President Obama's family owned two. Hypoallergenic, intelligent, and rare, they cost $2,500\u2013$5,000 from quality breeders with limited availability and often long wait lists.",
         size_tag='Medium', trait_tag='Hypoallergenic'),
    card('irish-wolfhound', 'Irish Wolfhound',
         "The world's tallest dog breed commands premium prices of $2,500\u2013$5,000 due to their rarity, the expense of health testing for heart and bone conditions, and the significant costs of raising giant breed puppies to adoption age.",
         size_tag='Giant', trait_tag='Tallest Breed'),
    card('cane-corso', 'Cane Corso',
         'Working-line and show-quality Cane Corsos from reputable Italian lineage breeders cost $2,500\u2013$6,000. Import puppies from titled Italian parents can be significantly more. Their popularity has also driven the price of average family pets above most comparable breeds.',
         size_tag='Large', trait_tag='Premium Molosser'),
]

save('most-expensive-dog-breeds', {
    "meta": {
        "name": "Most Expensive Dog Breeds",
        "slug": "most-expensive-dog-breeds",
        "shopify_handle": "most-expensive-dog-breeds",
        "group": "Breed Guides",
        "size_category": "Roundup",
        "tags": ["most expensive dog breeds", "expensive dogs", "dog breed prices"],
        "published": True,
        "published_at": "2026-05-18T16:00:00Z",
        "excerpt": "From the record-breaking Tibetan Mastiff to the hypoallergenic Portuguese Water Dog, these 10 breeds command the highest purchase prices \u2014 and often the highest lifetime costs \u2014 in the dog world.",
        "meta_description": "Discover the 10 most expensive dog breeds, from Tibetan Mastiffs to Irish Wolfhounds. Learn what drives premium prices and total lifetime costs for these rare, sought-after breeds."
    },
    "images": {"hero": {"url": B['tibetan-mastiff']['img_url'], "alt": "Most Expensive Dog Breeds"}},
    "sections": {
        "intro": {
            "label": "Overview",
            "heading": "Most Expensive Dog Breeds",
            "html": "<p>Dog prices vary enormously based on breed rarity, quality of health testing, lineage, breeder reputation, and regional demand. The most expensive breeds combine genuine rarity, significant investment in health testing, and high demand from serious enthusiasts. A Tibetan Mastiff puppy can cost as much as a new car; even mid-range expensive breeds like Bernese Mountain Dogs and Samoyeds command $3,000\u2013$8,000 from quality breeders.</p><p>It's important to distinguish between purchase price and lifetime cost. Some breeds that are relatively affordable to purchase \u2014 like French Bulldogs \u2014 have enormous lifetime veterinary costs due to structural health problems. The breeds on this list combine high initial cost with often significant ongoing expenses in food, veterinary care, and health monitoring. Understanding the full financial commitment before acquiring any of these breeds is essential.</p>"
        },
        "care": {
            "label": "Breeds",
            "heading": "10 Most Expensive Dog Breeds",
            "html": grid(cards_13)
        },
        "special": {
            "label": "Considerations",
            "heading": "The True Cost of an Expensive Dog Breed",
            "html": "<p>Purchase price is only the beginning of the financial commitment for most expensive breeds. Giant breeds like the Irish Wolfhound, Great Dane, and Tibetan Mastiff cost significantly more to feed, medicate, and board than average dogs. A single bag of food that lasts a small dog a month may last a giant breed a week. Veterinary costs for giant breeds are also higher \u2014 medications are often dosed by weight, and procedures like surgeries cost more.</p><p>Health testing is one of the primary drivers of reputable breeder prices. Responsible breeders test for hips, elbows, eyes, hearts, and breed-specific conditions before breeding \u2014 tests that can cost hundreds to thousands of dollars per breeding pair. Puppies from health-tested parents may cost more upfront but typically have lower lifetime veterinary expenses than those from untested parents. Always ask breeders for health clearances before purchasing any dog, especially expensive breeds with known health challenges.</p>"
        }
    },
    "faq": [
        {"q": "What is the most expensive dog breed in the world?", "a": "The Tibetan Mastiff holds the record for the highest price ever paid for a dog \u2014 a red puppy sold for $1.5 million in China in 2014. In the Western market, typical Tibetan Mastiff puppies from reputable breeders cost $3,000\u2013$10,000. Other consistently expensive breeds include the Samoyed, Chow Chow, and working-line Rottweiler."},
        {"q": "Why are some dog breeds so expensive?", "a": "Several factors drive breed prices: rarity (fewer breeders means less supply), quality of health testing (comprehensive testing is expensive), lineage (imported or titled parents command premiums), demand (fashionable or newly popularized breeds spike in price), and breeding difficulty (large litters of small, easy-whelping breeds cost less per puppy than small litters from giant breeds requiring veterinary assistance)."},
        {"q": "Is an expensive dog worth the cost?", "a": "That depends entirely on your priorities. A well-bred dog from a reputable breeder with comprehensive health testing is genuinely worth more \u2014 you are paying for reduced risk of heritable health conditions, predictable temperament, and ongoing breeder support. Purchasing the cheapest available puppy of an expensive breed often means buying from poor conditions with no health guarantees, potentially costing far more in veterinary bills."},
        {"q": "What dog has the highest lifetime cost?", "a": "Giant breeds tend to have the highest lifetime costs due to food, medication dosing by weight, and susceptibility to certain expensive conditions. Great Danes, Irish Wolfhounds, and Saint Bernards may cost $20,000\u2013$30,000 over their lifetime when all expenses are included. Brachycephalic breeds like French Bulldogs and Bulldogs also have very high lifetime costs due to recurring respiratory, skin, and orthopedic health issues."}
    ]
})


# ─── 14. dog-breeds-by-size ──────────────────────────────────────────────────
# Special format: grouped by size category
def card_labeled(slug, name, desc, size_tag, trait_tag, lifespan_tag=''):
    info = B.get(slug, {})
    img_url = info.get('img_url', '')
    img_alt = info.get('img_alt', name)
    l_tag = lifespan_tag or info.get('lifespan', '') or ''
    return (
        '<div style="background:#ffffff;border:1px solid rgba(0,0,0,0.08);border-radius:12px;overflow:hidden;">'
        f'<a href="/blogs/dog-breeds/{slug}" class="wf-card-img" style="display:block;"><img src="{img_url}" alt="{img_alt}" style="width:100%;aspect-ratio:3/2;height:auto;object-fit:cover;display:block;"></a>'
        '<div style="padding:16px;">'
        f'<h3 style="font-size:1em;font-weight:700;color:#1a1a1a;margin:0 0 8px 0;">{name}</h3>'
        '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">'
        f'<span style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.65em;background:#f0f0f0;border-radius:20px;padding:3px 10px;color:#555;">{size_tag}</span>'
        f'<span style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.65em;background:#f0f0f0;border-radius:20px;padding:3px 10px;color:#555;">{trait_tag}</span>'
        f'<span style="font-family:\'figmaMono\',\'SF Mono\',monospace;font-size:0.65em;background:#f0f0f0;border-radius:20px;padding:3px 10px;color:#555;">{l_tag} lifespan</span>'
        '</div>'
        f'<p style="font-size:0.85em;line-height:1.6;color:#6b7177;margin:0 0 12px 0;">{desc}</p>'
        f'<a href="/blogs/dog-breeds/{slug}" style="font-size:0.8em;font-weight:600;color:#000000;text-decoration:underline;text-underline-offset:3px;">Full guide \u2192</a>'
        '</div></div>'
    )

size_section_html = (
    '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Giant Breeds (70+ lbs)</h2>'
    + grid([
        card_labeled('great-dane', 'Great Dane',
                     'The tallest dog breed in the world, Great Danes can stand over 32 inches at the shoulder. Despite their imposing stature, they are gentle, friendly giants who get along well with children and other dogs.',
                     'Giant', '7\u201310 yrs'),
        card_labeled('mastiff', 'Mastiff',
                     'The heaviest dog breed, English Mastiffs can weigh over 230 lbs. Originally Roman war dogs, today they are gentle, loyal guardians with a calm, devoted temperament suited to experienced owners.',
                     'Giant', '6\u201310 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Large Breeds (50\u201370 lbs)</h2>'
    + grid([
        card_labeled('labrador-retriever', 'Labrador Retriever',
                     "The world's most popular dog breed for decades, Labs combine a friendly, outgoing temperament with athleticism and intelligence. They excel as family dogs, service dogs, and sporting companions.",
                     'Large', '10\u201312 yrs'),
        card_labeled('german-shepherd-dog', 'German Shepherd',
                     'The premier working dog globally, German Shepherds are used by police, military, and search-and-rescue teams worldwide. They are highly intelligent, loyal, and versatile in virtually every canine discipline.',
                     'Large', '9\u201313 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Medium Breeds (25\u201350 lbs)</h2>'
    + grid([
        card_labeled('beagle', 'Beagle',
                     'One of the most popular medium breeds in the world, Beagles are friendly, curious, and excellent family dogs. Their sturdy build, moderate exercise needs, and cheerful temperament make them adaptable to many lifestyles.',
                     'Medium', '12\u201315 yrs'),
        card_labeled('border-collie', 'Border Collie',
                     'The world\'s most intelligent dog breed is also one of its most athletic. Border Collies are built for all-day work in demanding terrain and thrive with active owners who can meet their substantial exercise and mental stimulation needs.',
                     'Medium', '12\u201315 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Small Breeds (10\u201325 lbs)</h2>'
    + grid([
        card_labeled('french-bulldog', 'French Bulldog',
                     "One of the world's most popular small breeds, French Bulldogs are affectionate, low-energy, and exceptionally adaptable to apartment living. Their bat ears and compact frame are instantly recognizable worldwide.",
                     'Small', '10\u201312 yrs'),
        card_labeled('cocker-spaniel', 'Cocker Spaniel',
                     'The American Cocker Spaniel is an elegant, gentle sporting dog that transitions seamlessly between field work and family life. Their silky coat and soft eyes make them one of the most beautiful small breeds.',
                     'Small-Medium', '10\u201314 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Toy Breeds (Under 10 lbs)</h2>'
    + grid([
        card_labeled('chihuahua', 'Chihuahua',
                     "The world's smallest dog breed is also one of its longest-lived and most personality-packed. Chihuahuas are fiercely loyal, surprisingly brave, and make exceptional companions for adults who appreciate their bold character.",
                     'Toy', '14\u201317 yrs'),
        card_labeled('yorkshire-terrier', 'Yorkshire Terrier',
                     'Yorkies combine toy breed portability with genuine terrier attitude. Bold, curious, and deeply affectionate with their family, they are one of the most popular toy breeds worldwide and remarkably long-lived.',
                     'Toy', '13\u201316 yrs'),
    ])
)

save('dog-breeds-by-size', {
    "meta": {
        "name": "Dog Breeds by Size",
        "slug": "dog-breeds-by-size",
        "shopify_handle": "dog-breeds-by-size",
        "group": "Breed Guides",
        "size_category": "Roundup",
        "tags": ["dog breeds by size", "dog size categories", "giant dogs large dogs small dogs"],
        "published": True,
        "published_at": "2026-05-19T16:00:00Z",
        "excerpt": "Size is one of the most practical factors in choosing the right dog. This guide breaks down dog breeds from tiny Toy breeds under 10 lbs to giant breeds over 100 lbs, with representative examples from each category.",
        "meta_description": "Explore dog breeds by size, from Toy Chihuahuas to Giant Mastiffs. A complete guide to dog size categories with representative breeds and key traits for each."
    },
    "images": {"hero": {"url": B['great-dane']['img_url'], "alt": "Dog Breeds by Size"}},
    "sections": {
        "intro": {
            "label": "Overview",
            "heading": "Dog Breeds by Size",
            "html": "<p>Size is one of the most consequential decisions when choosing a dog. It affects everything from where you can live (many apartments have weight limits), to how much you spend on food and veterinary care, to the type of exercise you can do together, to how long you can expect to share your life with your companion. Giant breeds often live only 7\u201310 years while toy breeds routinely reach 14\u201318. A 200-pound Mastiff requires a very different lifestyle than a 6-pound Chihuahua, even if both want the same thing: to be with you.</p><p>This guide organizes common dog breeds by size category \u2014 from Toy breeds under 10 pounds to Giant breeds over 70 \u2014 with representative examples from each group. Size categories are guidelines, not strict standards; actual weights vary within breeds and between individual dogs.</p>"
        },
        "care": {
            "label": "Breeds by Size",
            "heading": "Dog Breeds Organized by Size",
            "html": size_section_html
        },
        "special": {
            "label": "Choosing",
            "heading": "Choosing the Right Size Dog",
            "html": "<p>The right dog size depends on your living situation, activity level, and the type of relationship you want with your dog. Large and giant breeds generally need more space, cost more to feed and medicate, and have shorter lifespans than small breeds. They often make excellent active companions and natural deterrents but require more physical management, especially when young. Small and toy breeds are more affordable to maintain, live longer, and adapt better to apartment living, but can be more fragile and some have a tendency to bark more.</p><p>Consider your long-term situation as well. A 90-lb Labrador is manageable when you're 30 and active; the same dog may be challenging to handle when you're older or if your mobility changes. Many people find that medium breeds \u2014 25\u201350 lbs \u2014 hit a sweet spot of companionship, manageability, cost, and lifespan that suits a wide range of lifestyles.</p>"
        }
    },
    "faq": [
        {"q": "How are dog breeds categorized by size?", "a": "Standard size categories are: Toy (under 10 lbs), Small (10\u201325 lbs), Medium (25\u201350 lbs), Large (50\u201370 lbs), and Giant (over 70 lbs). These are general guidelines \u2014 different kennel clubs and breeders may use slightly different thresholds. Many breeds span multiple categories, as there is natural variation within breeds and some breeds like the Poodle come in multiple officially recognized sizes."},
        {"q": "What size dog is best for apartments?", "a": "Toy and small breeds are generally easiest to keep in apartments due to their lower space and exercise requirements. However, breed temperament matters more than size \u2014 a calm, low-energy Basset Hound or Greyhound may be a better apartment dog than a high-energy Jack Russell Terrier despite the size difference. Always check your building's weight restrictions and noise tolerance policies before choosing any breed."},
        {"q": "Do bigger dogs need more exercise than smaller dogs?", "a": "Not always \u2014 it depends more on the breed's energy level than its size. A small Jack Russell Terrier or Border Terrier may need more exercise than a large Basset Hound or Saint Bernard. In general, working and sporting breeds regardless of size have higher exercise needs than companion and guard breeds. A giant Great Dane needs moderate exercise while a medium Siberian Husky needs significantly more."},
        {"q": "Do smaller dogs live longer than larger dogs?", "a": "Yes \u2014 there is a well-documented inverse relationship between dog size and lifespan. Toy breeds like Chihuahuas and Yorkshire Terriers routinely live 14\u201317 years. Large breeds like Labrador Retrievers average 10\u201312 years. Giant breeds like Great Danes and Irish Wolfhounds often live only 7\u201310 years. The reason is not fully understood but appears related to more rapid aging and greater susceptibility to age-related diseases in larger dogs."}
    ]
})


# ─── 15. dog-breeds-by-group ──────────────────────────────────────────────────
group_section_html = (
    '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Sporting Group \u2014 Bred to Hunt with Guns</h2>'
    + grid([
        card_labeled('golden-retriever', 'Golden Retriever',
                     'The beloved Golden Retriever was developed in Scotland as a bird-flushing and retrieving dog. Today it is one of the most popular family and service dogs in the world, combining field ability with an exceptional temperament.',
                     'Sporting', '10\u201312 yrs'),
        card_labeled('labrador-retriever', 'Labrador Retriever',
                     "The world's most popular breed for decades, Labs were bred to retrieve waterfowl in the cold waters of Newfoundland. Their gentle mouth, swimming ability, and trainability made them the world's most versatile working dog.",
                     'Sporting', '10\u201312 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Hound Group \u2014 Bred to Track Prey</h2>'
    + grid([
        card_labeled('beagle', 'Beagle',
                     'One of the most popular scenthounds, Beagles were bred to hunt rabbits and hare in packs. Their extraordinary nose and cheerful, sociable temperament have made them beloved family dogs and the top choice for detection work at airports.',
                     'Hound', '12\u201315 yrs'),
        card_labeled('greyhound', 'Greyhound',
                     'The fastest dog breed in the world, capable of reaching 45 mph. Greyhounds are the oldest sighthound type, with depictions in ancient Egyptian art. Most available as pets are retired racing dogs who make surprisingly gentle, calm companions.',
                     'Hound', '10\u201314 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Working Group \u2014 Bred for Guarding and Tasks</h2>'
    + grid([
        card_labeled('german-shepherd-dog', 'German Shepherd',
                     'The definitive working dog, German Shepherds serve in police, military, search-and-rescue, and service roles globally. Their intelligence, trainability, and loyalty define what a working breed can achieve.',
                     'Working', '9\u201313 yrs'),
        card_labeled('rottweiler', 'Rottweiler',
                     'Descended from Roman cattle-driving dogs, Rottweilers were historically used for herding, carting, and guarding. Today they serve in police and protection roles while also making devoted family companions with experienced owners.',
                     'Working', '9\u201310 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Terrier Group \u2014 Bred to Hunt Vermin</h2>'
    + grid([
        card_labeled('airedale-terrier', 'Airedale Terrier',
                     'The King of Terriers is the largest of all terrier breeds, originally bred in Yorkshire to hunt otter and rat. Intelligent, confident, and versatile, Airedales have served in police and military roles in addition to being spirited family companions.',
                     'Terrier', '11\u201314 yrs'),
        card_labeled('west-highland-white-terrier', 'West Highland White Terrier',
                     "The Westie is one of the most popular terriers \u2014 confident, friendly, and adaptable without losing terrier spirit. Originally bred to hunt foxes and badgers in Scottish Highland terrain, they bring genuine toughness in a bright-white compact package.",
                     'Terrier', '12\u201316 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Toy Group \u2014 Bred for Companionship</h2>'
    + grid([
        card_labeled('chihuahua', 'Chihuahua',
                     "The world's smallest breed and one of the longest-lived, Chihuahuas are bold, loyal companions with personalities that far exceed their size. Their ancient Mexican heritage and distinctive appearance make them one of the most recognizable dogs in the world.",
                     'Toy', '14\u201317 yrs'),
        card_labeled('yorkshire-terrier', 'Yorkshire Terrier',
                     'Yorkies were originally developed in Yorkshire as rat-catching working terriers before becoming Victorian parlor dogs. Today they combine glamour and terrier attitude in a pocket-sized, long-lived package beloved worldwide.',
                     'Toy', '13\u201316 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Non-Sporting Group \u2014 Diverse Companions</h2>'
    + grid([
        card_labeled('bulldog', 'Bulldog',
                     "England's iconic breed has evolved from bull-baiting dog to one of the most affectionate, patient family companions in the world. Their stocky frame, wrinkled face, and gentle personality make them universally recognizable.",
                     'Non-Sporting', '8\u201310 yrs'),
        card_labeled('standard-poodle', 'Standard Poodle',
                     'One of the most intelligent and athletic breeds, the Standard Poodle excels in agility, hunting, service work, and obedience. Their hypoallergenic coat and exceptional trainability have made them favorites of families and professional trainers alike.',
                     'Non-Sporting', '10\u201318 yrs'),
    ])
    + '<h2 style="font-size:1.2em;font-weight:700;color:#1a1a1a;margin:32px 0 16px 0;">Herding Group \u2014 Bred to Control Livestock</h2>'
    + grid([
        card_labeled('border-collie', 'Border Collie',
                     "The world's most intelligent breed was developed on the border of England and Scotland to herd sheep with minimal direction. Their legendary work ethic, trainability, and athleticism have made them the top breed in agility and obedience competition.",
                     'Herding', '12\u201315 yrs'),
        card_labeled('australian-shepherd', 'Australian Shepherd',
                     'Despite the name, Aussies were developed in the American West as versatile ranch dogs. Their agility, intelligence, and tireless work ethic make them exceptional performance dogs, and their striking merle coats add to their appeal.',
                     'Herding', '12\u201315 yrs'),
    ])
)

save('dog-breeds-by-group', {
    "meta": {
        "name": "Dog Breeds by Group",
        "slug": "dog-breeds-by-group",
        "shopify_handle": "dog-breeds-by-group",
        "group": "Breed Guides",
        "size_category": "Roundup",
        "tags": ["dog breeds by group", "AKC breed groups", "dog breed categories"],
        "published": True,
        "published_at": "2026-05-20T16:00:00Z",
        "excerpt": "The AKC organizes dog breeds into seven groups based on their original purpose. Understanding these groups is one of the most useful tools for predicting a breed's temperament, energy level, and training needs.",
        "meta_description": "Explore dog breeds organized by AKC group, from Sporting and Hound to Herding and Toy. Learn what each group was bred for and find representative breeds from every category."
    },
    "images": {"hero": {"url": B['golden-retriever']['img_url'], "alt": "Dog Breeds by Group"}},
    "sections": {
        "intro": {
            "label": "Overview",
            "heading": "Dog Breeds by AKC Group",
            "html": "<p>The American Kennel Club organizes its 200+ recognized breeds into seven groups based on the original purpose each breed was developed for: Sporting, Hound, Working, Terrier, Toy, Non-Sporting, and Herding. Understanding these group classifications is one of the most practical tools for predicting a breed's natural tendencies, energy level, trainability, and compatibility with your lifestyle. A dog bred to run all day in the field will have fundamentally different needs than one bred to sit on a royal lap.</p><p>Group membership doesn't determine everything \u2014 individual temperament, early socialization, and training shape every dog significantly. But groupings provide an invaluable starting point for understanding what drives a breed's behavior and what they were built to do. A Beagle that follows its nose obsessively is not misbehaving \u2014 it is doing exactly what thousands of years of selective breeding prepared it for.</p>"
        },
        "care": {
            "label": "Breeds by Group",
            "heading": "Dog Breeds Organized by AKC Group",
            "html": group_section_html
        },
        "special": {
            "label": "Guide",
            "heading": "How to Use Breed Groups to Choose Your Dog",
            "html": "<p>Breed groups are your single best tool for narrowing down the type of dog that suits your lifestyle. If you are very active and want a dog to work out with, look first at the Sporting and Herding groups. If you want a loyal, protective companion and have experience with dogs, explore the Working group. If you want a lower-maintenance companion for apartment or urban living, the Toy and Non-Sporting groups offer the widest range of options.</p><p>Be aware that group instincts can be stronger than training. A Beagle will always want to follow its nose; a Border Collie will always want to herd; a Terrier will always want to dig and chase. Selecting a breed whose natural instincts align with your tolerance and lifestyle is far more sustainable than trying to train out deeply ingrained working behaviors. The best owners channel their dog's natural drives rather than fighting them.</p>"
        }
    },
    "faq": [
        {"q": "What are the 7 AKC dog breed groups?", "a": "The American Kennel Club organizes recognized breeds into seven groups: Sporting (gun dogs bred to find and retrieve game), Hound (dogs that hunt by sight or scent), Working (dogs bred for guarding, hauling, and rescue), Terrier (dogs bred to hunt and control vermin), Toy (small companion dogs), Non-Sporting (a diverse catch-all group), and Herding (dogs bred to control livestock). A Miscellaneous class also exists for breeds awaiting full recognition."},
        {"q": "What dog group is easiest to train?", "a": "The Herding and Sporting groups generally produce the most trainable breeds, as they were developed to work closely with human handlers and respond to direction. German Shepherds (Herding), Border Collies (Herding), Golden Retrievers (Sporting), and Labrador Retrievers (Sporting) consistently top trainability rankings. Terrier and Hound group breeds tend to be more independent and can be harder to motivate with conventional obedience training."},
        {"q": "What is the difference between Sporting and Working groups?", "a": "The Sporting group comprises dogs bred to assist hunters in finding and retrieving game birds \u2014 pointers, setters, retrievers, and spaniels. The Working group comprises dogs bred for non-hunting tasks: guarding property and livestock, hauling sleds and carts, rescue work, and military service. Both groups contain athletic, intelligent breeds, but Working dogs tend to be larger, more powerful, and more protective by nature."},
        {"q": "Why is the Poodle in the Non-Sporting group?", "a": "The Standard Poodle was originally a water retriever, which would logically place it in the Sporting group. However, when the AKC established its group classifications, Poodles had already been established primarily as companion and show dogs in America, leading to their placement in the Non-Sporting group. The inconsistency is historical rather than logical \u2014 other countries' kennel clubs classify Poodles differently."}
    ]
})

print('Files 11-15 done.')
print('ALL 15 ROUNDUP FILES COMPLETE!')
