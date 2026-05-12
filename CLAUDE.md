# Wooffy Dog Breeds — Project Context

## Project Overview

Shopify blog at **thewooffy.myshopify.com**, blog ID `81943265334`, path `/blogs/dog-breeds/`.

Publishing 158 dog breeds × 4 articles each = 632 breed articles, plus 17 roundup articles = **649 total articles**.

Each breed has 4 files:
- `[breed].json` — main guide (meta.group = AKC group, meta.size_category = breed's size)
- `[breed]-grooming-guide.json`
- `[breed]-first-year-costs.json`
- `[breed]-puppy-checklist.json`

Supporting articles use: `meta.group = "Breed Name"`, `meta.size_category = "Guide"`

Roundups use: `meta.group = "Breed Guides"`, `meta.size_category = "Roundup"`

---

## Key Commands

```bash
# Publish new articles
echo YES | python3 scripts/generate.py [slug1] [slug2] ... --publish

# Update already-published articles
echo YES | python3 scripts/generate.py [slug1] [slug2] ... --update

# Generate HTML only (no Shopify)
python3 scripts/generate.py [slug1] [slug2]
```

Credentials are in `.env` (gitignored): `SHOPIFY_STORE`, `SHOPIFY_TOKEN`, `SHOPIFY_BLOG_ID`.

---

## Publishing Schedule

**Rule: maximum 30 articles per day. Publish only the current day's batch.**

Start date: Apr 15, 2026. Day number = (today − Apr 15).day_count + 1

| Day | Date | Breeds (7) | Roundups | Articles |
|-----|------|-----------|----------|----------|
| 1 | Apr 15 | German Shorthaired Pointer, Cocker Spaniel, Dachshund, Doberman Pinscher, Miniature Schnauzer, Chihuahua, Australian Shepherd | best-dogs-for-active-people, best-dogs-for-first-time-owners | 30 ✅ |
| 2 | Apr 16 | Akita, Bernese Mountain Dog, Boxer, Great Dane, Mastiff, Bull Terrier, American Staffordshire Terrier | best-large-dog-breeds, best-guard-dog-breeds | 30 ✅ |
| 3 | Apr 17 | Great Pyrenees, Newfoundland, Saint Bernard, Samoyed, Soft Coated Wheaten Terrier, Staffordshire Bull Terrier, West Highland White Terrier | best-dogs-for-cold-climates, best-terrier-breeds | 30 ✅ |
| 4 | Apr 18 | Cane Corso, Alaskan Malamute, Portuguese Water Dog, English Springer Spaniel, Vizsla, Weimaraner, Italian Greyhound | best-hunting-dog-breeds, best-hypoallergenic-dog-breeds | 30 ✅ |
| 5 | Apr 19 | Pomeranian, Pug, Yorkshire Terrier, Havanese, Boston Terrier, Bulldog, Standard Poodle | best-small-dog-breeds, best-dogs-for-seniors | 30 ✅ |
| 6 | Apr 20 | Chow Chow, Dalmatian, Shiba Inu, Australian Cattle Dog, Belgian Malinois, Border Collie, Cardigan Welsh Corgi | — | 28 ✅ |
| 7 | Apr 21 | Collie, Miniature American Shepherd, Old English Sheepdog, Shetland Sheepdog, Rhodesian Ridgeback, Brittany, Irish Setter | best-herding-dog-breeds, best-sporting-dog-breeds | 30 ✅ |
| 8 | Apr 22 | German Wirehaired Pointer, Chesapeake Bay Retriever, Flat-Coated Retriever, Nova Scotia Duck Tolling Retriever, English Cocker Spaniel, Lagotto Romagnolo, Pointer | — | 28 ✅ |
| 9 | Apr 23 | English Setter, Gordon Setter, American Water Spaniel, Clumber Spaniel, Afghan Hound, Basenji, Bloodhound | — | 28 ✅ |
| 10 | Apr 24 | Field Spaniel, Irish Water Spaniel, Welsh Springer Spaniel, Wirehaired Pointing Griffon, Spinone Italiano, Borzoi, Irish Wolfhound | best-gun-dog-breeds | 29 |
| 11 | Apr 25 | Saluki, American Foxhound, Black and Tan Coonhound, Bluetick Coonhound, Harrier, Norwegian Elkhound, Ibizan Hound | — | 28 |
| 12 | Apr 26 | Otterhound, Pharaoh Hound, Redbone Coonhound, Scottish Deerhound, Anatolian Shepherd Dog, Bullmastiff, Dogue de Bordeaux | best-hound-dog-breeds | 29 |
| 13 | Apr 27 | Giant Schnauzer, Greater Swiss Mountain Dog, Leonberger, Neapolitan Mastiff, Standard Schnauzer, Tibetan Mastiff, German Pinscher | — | 28 |
| 14 | Apr 28 | Airedale Terrier, Border Terrier, Cairn Terrier, Miniature Bull Terrier, Parson Russell Terrier, Russell Terrier, Australian Terrier | best-gentle-giant-dog-breeds | 29 |
| 15 | Apr 29 | Bedlington Terrier, Irish Terrier, Kerry Blue Terrier, Lakeland Terrier, Scottish Terrier, Brussels Griffon, Chinese Crested | — | 28 |
| 16 | Apr 30 | Miniature Pinscher, Papillon, Pekingese, Japanese Chin, American Eskimo Dog, Chinese Shar-Pei, Coton de Tulear | — | 28 |
| 17 | May 1 | Lhasa Apso, Affenpinscher, Silky Terrier, Toy Fox Terrier, Keeshond, Finnish Spitz, Norfolk Terrier | — | 28 |
| 18 | May 2 | Norwich Terrier, Skye Terrier, Welsh Terrier, Wire Fox Terrier, Lowchen, Schipperke, Tibetan Spaniel | — | 28 |
| 19 | May 3 | Tibetan Terrier, Xoloitzcuintli, Komondor, Bearded Collie, Bouvier des Flandres, Beauceron, Belgian Sheepdog | — | 28 |
| 20 | May 4 | Belgian Tervuren, Briard, Entlebucher Mountain Dog, Finnish Lapphund, Icelandic Sheepdog, Polish Lowland Sheepdog, Puli | — | 28 |
| 21 | May 5 | Spanish Water Dog, Swedish Vallhund | best-watchdog-breeds, most-popular-dog-breeds | 10 |

**Current status: Days 1–10 complete (386 articles published). Next: Day 11 on Apr 25.**

---

## Slug Reference

To get slugs for a breed, use the breed name lowercased with hyphens, e.g. `field-spaniel`, `irish-water-spaniel`. Supporting articles append `-grooming-guide`, `-first-year-costs`, `-puppy-checklist`.

### Day 10 slugs (Apr 24)
```
field-spaniel field-spaniel-grooming-guide field-spaniel-first-year-costs field-spaniel-puppy-checklist
irish-water-spaniel irish-water-spaniel-grooming-guide irish-water-spaniel-first-year-costs irish-water-spaniel-puppy-checklist
welsh-springer-spaniel welsh-springer-spaniel-grooming-guide welsh-springer-spaniel-first-year-costs welsh-springer-spaniel-puppy-checklist
wirehaired-pointing-griffon wirehaired-pointing-griffon-grooming-guide wirehaired-pointing-griffon-first-year-costs wirehaired-pointing-griffon-puppy-checklist
spinone-italiano spinone-italiano-grooming-guide spinone-italiano-first-year-costs spinone-italiano-puppy-checklist
borzoi borzoi-grooming-guide borzoi-first-year-costs borzoi-puppy-checklist
irish-wolfhound irish-wolfhound-grooming-guide irish-wolfhound-first-year-costs irish-wolfhound-puppy-checklist
best-gun-dog-breeds
```

### Day 11 slugs (Apr 25)
```
saluki saluki-grooming-guide saluki-first-year-costs saluki-puppy-checklist
american-foxhound american-foxhound-grooming-guide american-foxhound-first-year-costs american-foxhound-puppy-checklist
black-and-tan-coonhound black-and-tan-coonhound-grooming-guide black-and-tan-coonhound-first-year-costs black-and-tan-coonhound-puppy-checklist
bluetick-coonhound bluetick-coonhound-grooming-guide bluetick-coonhound-first-year-costs bluetick-coonhound-puppy-checklist
harrier harrier-grooming-guide harrier-first-year-costs harrier-puppy-checklist
norwegian-elkhound norwegian-elkhound-grooming-guide norwegian-elkhound-first-year-costs norwegian-elkhound-puppy-checklist
ibizan-hound ibizan-hound-grooming-guide ibizan-hound-first-year-costs ibizan-hound-puppy-checklist
```

### Day 12 slugs (Apr 26)
```
otterhound otterhound-grooming-guide otterhound-first-year-costs otterhound-puppy-checklist
pharaoh-hound pharaoh-hound-grooming-guide pharaoh-hound-first-year-costs pharaoh-hound-puppy-checklist
redbone-coonhound redbone-coonhound-grooming-guide redbone-coonhound-first-year-costs redbone-coonhound-puppy-checklist
scottish-deerhound scottish-deerhound-grooming-guide scottish-deerhound-first-year-costs scottish-deerhound-puppy-checklist
anatolian-shepherd-dog anatolian-shepherd-dog-grooming-guide anatolian-shepherd-dog-first-year-costs anatolian-shepherd-dog-puppy-checklist
bullmastiff bullmastiff-grooming-guide bullmastiff-first-year-costs bullmastiff-puppy-checklist
dogue-de-bordeaux dogue-de-bordeaux-grooming-guide dogue-de-bordeaux-first-year-costs dogue-de-bordeaux-puppy-checklist
best-hound-dog-breeds
```

### Day 13 slugs (Apr 27)
```
giant-schnauzer giant-schnauzer-grooming-guide giant-schnauzer-first-year-costs giant-schnauzer-puppy-checklist
greater-swiss-mountain-dog greater-swiss-mountain-dog-grooming-guide greater-swiss-mountain-dog-first-year-costs greater-swiss-mountain-dog-puppy-checklist
leonberger leonberger-grooming-guide leonberger-first-year-costs leonberger-puppy-checklist
neapolitan-mastiff neapolitan-mastiff-grooming-guide neapolitan-mastiff-first-year-costs neapolitan-mastiff-puppy-checklist
standard-schnauzer standard-schnauzer-grooming-guide standard-schnauzer-first-year-costs standard-schnauzer-puppy-checklist
tibetan-mastiff tibetan-mastiff-grooming-guide tibetan-mastiff-first-year-costs tibetan-mastiff-puppy-checklist
german-pinscher german-pinscher-grooming-guide german-pinscher-first-year-costs german-pinscher-puppy-checklist
```

### Day 14 slugs (Apr 28)
```
airedale-terrier airedale-terrier-grooming-guide airedale-terrier-first-year-costs airedale-terrier-puppy-checklist
border-terrier border-terrier-grooming-guide border-terrier-first-year-costs border-terrier-puppy-checklist
cairn-terrier cairn-terrier-grooming-guide cairn-terrier-first-year-costs cairn-terrier-puppy-checklist
miniature-bull-terrier miniature-bull-terrier-grooming-guide miniature-bull-terrier-first-year-costs miniature-bull-terrier-puppy-checklist
parson-russell-terrier parson-russell-terrier-grooming-guide parson-russell-terrier-first-year-costs parson-russell-terrier-puppy-checklist
russell-terrier russell-terrier-grooming-guide russell-terrier-first-year-costs russell-terrier-puppy-checklist
australian-terrier australian-terrier-grooming-guide australian-terrier-first-year-costs australian-terrier-puppy-checklist
best-gentle-giant-dog-breeds
```

### Day 15 slugs (Apr 29)
```
bedlington-terrier bedlington-terrier-grooming-guide bedlington-terrier-first-year-costs bedlington-terrier-puppy-checklist
irish-terrier irish-terrier-grooming-guide irish-terrier-first-year-costs irish-terrier-puppy-checklist
kerry-blue-terrier kerry-blue-terrier-grooming-guide kerry-blue-terrier-first-year-costs kerry-blue-terrier-puppy-checklist
lakeland-terrier lakeland-terrier-grooming-guide lakeland-terrier-first-year-costs lakeland-terrier-puppy-checklist
scottish-terrier scottish-terrier-grooming-guide scottish-terrier-first-year-costs scottish-terrier-puppy-checklist
brussels-griffon brussels-griffon-grooming-guide brussels-griffon-first-year-costs brussels-griffon-puppy-checklist
chinese-crested chinese-crested-grooming-guide chinese-crested-first-year-costs chinese-crested-puppy-checklist
```

### Day 16 slugs (Apr 30)
```
miniature-pinscher miniature-pinscher-grooming-guide miniature-pinscher-first-year-costs miniature-pinscher-puppy-checklist
papillon papillon-grooming-guide papillon-first-year-costs papillon-puppy-checklist
pekingese pekingese-grooming-guide pekingese-first-year-costs pekingese-puppy-checklist
japanese-chin japanese-chin-grooming-guide japanese-chin-first-year-costs japanese-chin-puppy-checklist
american-eskimo-dog american-eskimo-dog-grooming-guide american-eskimo-dog-first-year-costs american-eskimo-dog-puppy-checklist
chinese-shar-pei chinese-shar-pei-grooming-guide chinese-shar-pei-first-year-costs chinese-shar-pei-puppy-checklist
coton-de-tulear coton-de-tulear-grooming-guide coton-de-tulear-first-year-costs coton-de-tulear-puppy-checklist
```

### Day 17 slugs (May 1)
```
lhasa-apso lhasa-apso-grooming-guide lhasa-apso-first-year-costs lhasa-apso-puppy-checklist
affenpinscher affenpinscher-grooming-guide affenpinscher-first-year-costs affenpinscher-puppy-checklist
silky-terrier silky-terrier-grooming-guide silky-terrier-first-year-costs silky-terrier-puppy-checklist
toy-fox-terrier toy-fox-terrier-grooming-guide toy-fox-terrier-first-year-costs toy-fox-terrier-puppy-checklist
keeshond keeshond-grooming-guide keeshond-first-year-costs keeshond-puppy-checklist
finnish-spitz finnish-spitz-grooming-guide finnish-spitz-first-year-costs finnish-spitz-puppy-checklist
norfolk-terrier norfolk-terrier-grooming-guide norfolk-terrier-first-year-costs norfolk-terrier-puppy-checklist
```

### Day 18 slugs (May 2)
```
norwich-terrier norwich-terrier-grooming-guide norwich-terrier-first-year-costs norwich-terrier-puppy-checklist
skye-terrier skye-terrier-grooming-guide skye-terrier-first-year-costs skye-terrier-puppy-checklist
welsh-terrier welsh-terrier-grooming-guide welsh-terrier-first-year-costs welsh-terrier-puppy-checklist
wire-fox-terrier wire-fox-terrier-grooming-guide wire-fox-terrier-first-year-costs wire-fox-terrier-puppy-checklist
lowchen lowchen-grooming-guide lowchen-first-year-costs lowchen-puppy-checklist
schipperke schipperke-grooming-guide schipperke-first-year-costs schipperke-puppy-checklist
tibetan-spaniel tibetan-spaniel-grooming-guide tibetan-spaniel-first-year-costs tibetan-spaniel-puppy-checklist
```

### Day 19 slugs (May 3)
```
tibetan-terrier tibetan-terrier-grooming-guide tibetan-terrier-first-year-costs tibetan-terrier-puppy-checklist
xoloitzcuintli xoloitzcuintli-grooming-guide xoloitzcuintli-first-year-costs xoloitzcuintli-puppy-checklist
komondor komondor-grooming-guide komondor-first-year-costs komondor-puppy-checklist
bearded-collie bearded-collie-grooming-guide bearded-collie-first-year-costs bearded-collie-puppy-checklist
bouvier-des-flandres bouvier-des-flandres-grooming-guide bouvier-des-flandres-first-year-costs bouvier-des-flandres-puppy-checklist
beauceron beauceron-grooming-guide beauceron-first-year-costs beauceron-puppy-checklist
belgian-sheepdog belgian-sheepdog-grooming-guide belgian-sheepdog-first-year-costs belgian-sheepdog-puppy-checklist
```

### Day 20 slugs (May 4)
```
belgian-tervuren belgian-tervuren-grooming-guide belgian-tervuren-first-year-costs belgian-tervuren-puppy-checklist
briard briard-grooming-guide briard-first-year-costs briard-puppy-checklist
entlebucher-mountain-dog entlebucher-mountain-dog-grooming-guide entlebucher-mountain-dog-first-year-costs entlebucher-mountain-dog-puppy-checklist
finnish-lapphund finnish-lapphund-grooming-guide finnish-lapphund-first-year-costs finnish-lapphund-puppy-checklist
icelandic-sheepdog icelandic-sheepdog-grooming-guide icelandic-sheepdog-first-year-costs icelandic-sheepdog-puppy-checklist
polish-lowland-sheepdog polish-lowland-sheepdog-grooming-guide polish-lowland-sheepdog-first-year-costs polish-lowland-sheepdog-puppy-checklist
puli puli-grooming-guide puli-first-year-costs puli-puppy-checklist
```

### Day 21 slugs (May 5 → now Apr 29)
```
spanish-water-dog spanish-water-dog-grooming-guide spanish-water-dog-first-year-costs spanish-water-dog-puppy-checklist
swedish-vallhund swedish-vallhund-grooming-guide swedish-vallhund-first-year-costs swedish-vallhund-puppy-checklist
best-watchdog-breeds most-popular-dog-breeds
```

---

## New SEO Roundup Articles (Days 22–36)

15 new roundup articles added to extend the publishing schedule beyond the original 21 days.

| Day | Date | Slugs |
|-----|------|-------|
| 22 | Apr 30 | most-intelligent-dog-breeds, easiest-dogs-to-train |
| 23 | May 1 | longest-living-dog-breeds, best-dogs-for-hot-climates, best-dogs-for-hiking |
| 24 | May 2 | best-working-dog-breeds, best-toy-dog-breeds, best-non-sporting-dog-breeds |
| 25 | May 3 | most-loyal-dog-breeds, dog-breeds-good-with-cats, quietest-dog-breeds |
| 26 | May 4 | rarest-dog-breeds, most-expensive-dog-breeds |
| 27 | May 5 | dog-breeds-by-size, dog-breeds-by-group |

### Day 22 slugs (Apr 30)
```
most-intelligent-dog-breeds easiest-dogs-to-train
```

### Day 23 slugs (May 1)
```
longest-living-dog-breeds best-dogs-for-hot-climates best-dogs-for-hiking
```

### Day 24 slugs (May 2)
```
best-working-dog-breeds best-toy-dog-breeds best-non-sporting-dog-breeds
```

### Day 25 slugs (May 3)
```
most-loyal-dog-breeds dog-breeds-good-with-cats quietest-dog-breeds
```

### Day 26 slugs (May 4)
```
rarest-dog-breeds most-expensive-dog-breeds
```

### Day 27 slugs (May 5)
```
dog-breeds-by-size dog-breeds-by-group
```

---

## Doodle Designer-Breed Series (Days 28–29)

6 doodle hybrid-breed guides plus 1 roundup added May 10. All marked `published: false` until the user reviews and triggers publishing. Hero/secondary images use a Wikipedia placeholder — replace before publish via the HD image pipeline or manual upload.

| Day | Date | Breeds (4–6) | Roundup | Articles |
|-----|------|--------------|---------|----------|
| 28 | May 11 | Goldendoodle, Labradoodle, Bernedoodle, Cavapoo | — | 16 |
| 29 | May 12 | Sheepadoodle, Aussiedoodle | best-doodle-breeds-for-families | 9 |

### Day 28 slugs (May 11)
```
goldendoodle goldendoodle-grooming-guide goldendoodle-first-year-costs goldendoodle-puppy-checklist
labradoodle labradoodle-grooming-guide labradoodle-first-year-costs labradoodle-puppy-checklist
bernedoodle bernedoodle-grooming-guide bernedoodle-first-year-costs bernedoodle-puppy-checklist
cavapoo cavapoo-grooming-guide cavapoo-first-year-costs cavapoo-puppy-checklist
```

### Day 29 slugs (May 12)
```
sheepadoodle sheepadoodle-grooming-guide sheepadoodle-first-year-costs sheepadoodle-puppy-checklist
aussiedoodle aussiedoodle-grooming-guide aussiedoodle-first-year-costs aussiedoodle-puppy-checklist
best-doodle-breeds-for-families
```

Generator: `scripts/generate_doodle_articles.py` regenerates the 23 templated files from `BREEDS` and `SUPPORTING` dicts (the 2 hand-written main breeds, goldendoodle.json and labradoodle.json, are not in the generator).

---

## Known Issues & Fixes

### Image URL validation
Shopify will fail with 422 if a hero image URL returns 404. Always verify Wikipedia Commons URLs before publishing. The correct URL format is:
```
https://upload.wikimedia.org/wikipedia/commons/thumb/[x]/[xx]/[filename]/330px-[filename]
```
Where `[x]/[xx]` is the first character and first two characters of the MD5 hash of the filename.

To compute: `python3 -c "import hashlib; f='Filename.jpg'; h=hashlib.md5(f.encode()).hexdigest(); print(f'{h[0]}/{h[:2]}')"`

### JSON structure requirements
All supporting articles (grooming, costs, checklist) must have:
- `meta.name` (not `meta.title`)
- `meta.slug`
- `meta.excerpt` (not `meta.description`)
- `meta.meta_description`
- `meta.tags` (list)
- `images` as a dict: `{"hero": {"url": "...", "alt": "..."}}`  (NOT a list)

### Double quotes in HTML strings
Any `"` inside HTML stored in JSON strings must be escaped as `&quot;`.

### Roundup breed card format
Roundup breed cards are in `sections.care.html`. Each card follows the format in `breed-data/best-large-dog-breeds.json` (reference file). Stats fields in breed JSON use nested dicts: `stats.size.value`, `stats.lifespan.value`.

---

## Files
- `breed-data/` — all JSON source files (653 files)
- `scripts/generate.py` — main publish/update script
- `published_log.json` — dict of published handles (gitignored)
- `PUBLISHING_SCHEDULE.md` — full original schedule
- `fix_roundups.py` — one-time script used to fix roundup breed cards
