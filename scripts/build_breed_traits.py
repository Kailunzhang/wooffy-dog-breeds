"""Build breed_traits.json from _published_breeds_meta.json.

Each entry: {slug, name, category, coat, grooming_action, puppy_coat}.

Strategy:
  1. Detect coat category from appearance keywords (wiry/curly/hairless/corded/silky/double-coat/smooth/etc.)
  2. Map category -> default grooming_action template (no humans, tools-on-table)
  3. Apply manual OVERRIDES for known breeds (curated coat + puppy_coat per breed)

Usage: python scripts/build_breed_traits.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_PUB = ROOT / "_published_breeds_meta.json"
META_UNPUB = ROOT / "_unpublished_breeds_meta.json"
OUT = ROOT / "breed_traits.json"


CATEGORY_GROOMING: dict[str, str] = {
    "smooth_short": "with a rubber curry brush and bristle grooming brush laid out on the table beside the dog",
    "thick_double": "with a slicker brush, undercoat rake, and steel comb laid out on the table beside the dog",
    "feathered_medium": "with a slicker brush, pin brush, and steel comb laid out on the table beside the dog",
    "wiry_terrier": "with a stripping comb, slicker brush, and steel comb laid out on the table beside the dog",
    "wirehaired_sporting": "with a stripping comb, slicker brush, and beard comb laid out on the table beside the dog",
    "curly_poodle": "with professional grooming scissors, a slicker brush, and steel comb laid out on the table beside the dog",
    "long_silky": "with a long pin brush, steel comb, and detangling spray bottle laid out on the table beside the dog",
    "hairless": "with skin-care items — a soft microfiber cloth and bottle of dog-safe moisturizer — laid out on the table beside the dog",
    "corded": "with a wide-tooth grooming comb and detangling spray laid out on the table beside the dog (the cords are tended by hand, never brushed)",
    "wheaten_silky": "with a slicker brush, steel comb, and grooming scissors laid out on the table beside the dog",
}


def detect_category(appearance: str, name: str) -> str:
    a = appearance.lower()
    n = name.lower()

    if "hairless" in a and "xolo" in n:
        return "hairless"
    if "corded" in a or "cords" in a or "komondor" in n or n == "puli":
        return "corded"
    if "wheaten" in n or "soft coated wheaten" in n:
        return "wheaten_silky"

    if "wiry" in a or "wire-haired" in a or "wirehaired" in a or ("harsh" in a and "outer coat" in a):
        if any(k in n for k in ["wirehaired", "wire", "spinone", "wolfhound", "griffon"]):
            return "wirehaired_sporting"
        return "wiry_terrier"

    if any(k in a for k in ["curly", "tight curl", "tight, curly", "dense curly"]) or any(k in n for k in [
        "poodle", "bichon", "lagotto", "portuguese water", "irish water", "american water spaniel", "bedlington"
    ]):
        return "curly_poodle"

    if any(k in n for k in ["afghan", "yorkshire", "maltese", "shih tzu", "havanese", "lhasa", "silky terrier"]):
        return "long_silky"

    if "double coat" in a and ("thick" in a or "dense" in a or "wooly" in a or "woolly" in a):
        return "thick_double"
    if any(k in n for k in [
        "husky", "malamute", "samoyed", "akita", "newfoundland", "saint bernard", "great pyrenees",
        "tibetan mastiff", "norwegian elkhound", "bernese mountain", "chow chow", "old english sheepdog",
        "bearded collie",
    ]):
        return "thick_double"

    if "feather" in a or "feathering" in a:
        return "feathered_medium"
    if any(k in n for k in [
        "retriever", "setter", "spaniel", "collie", "shepherd dog", "corgi", "sheltie", "shetland", "papillon",
    ]):
        return "feathered_medium"

    if "short" in a and any(k in a for k in ["smooth", "close", "fine", "sleek", "dense"]):
        return "smooth_short"

    return "smooth_short"


# Curated coat + puppy_coat per breed. Heuristic-only entries fall back to a generic category phrase.
OVERRIDES: dict[str, dict] = {
    "afghan-hound": {"coat": "long flowing silky cream-and-red with a saddle of shorter hair", "puppy_coat": "soft cream-and-red puppy coat"},
    "akita": {"category": "thick_double", "coat": "thick double coat in red, white, brindle, or pinto with a curled tail", "puppy_coat": "fluffy soft puppy double coat"},
    "alaskan-malamute": {"coat": "thick gray-and-white double coat with plumed tail over the back", "puppy_coat": "fluffy gray-and-white puppy double coat"},
    "american-foxhound": {"coat": "short tricolor (black, white, tan) hound coat", "puppy_coat": "smooth tricolor puppy coat"},
    "american-staffordshire-terrier": {"coat": "short glossy brindle or fawn with a powerful muscular frame", "puppy_coat": "smooth short brindle puppy coat"},
    "american-water-spaniel": {"coat": "tight wavy liver-brown curls", "puppy_coat": "soft curly liver-brown puppy coat"},
    "anatolian-shepherd-dog": {"category": "smooth_short", "coat": "short fawn coat with a black mask, large athletic frame", "puppy_coat": "soft fawn puppy coat with a dark mask"},
    "australian-cattle-dog": {"coat": "short blue-mottled or red-speckled double coat", "puppy_coat": "fluffy white puppy coat (markings develop over weeks)"},
    "australian-shepherd": {"category": "feathered_medium", "coat": "medium-length blue merle or red merle with white markings", "puppy_coat": "soft blue merle puppy coat"},
    "basenji": {"coat": "short fine red-and-white coat, tightly curled tail", "puppy_coat": "smooth short red-and-white puppy coat"},
    "basset-hound": {"coat": "short tricolor coat, long droopy ears, low-slung wrinkled body", "puppy_coat": "smooth tricolor puppy coat with oversized ears"},
    "beagle": {"coat": "short tricolor (black, white, tan) coat", "puppy_coat": "smooth tricolor puppy coat"},
    "belgian-malinois": {"coat": "short fawn-mahogany coat with a black mask", "puppy_coat": "soft fawn puppy coat with a black mask"},
    "bernese-mountain-dog": {"coat": "long tri-color (black, rust, white) double coat", "puppy_coat": "fluffy tri-color puppy double coat"},
    "bichon-frise": {"coat": "dense curly powder-puff white", "puppy_coat": "soft fluffy white curly puppy coat"},
    "black-and-tan-coonhound": {"coat": "short glossy black-and-tan coat with long pendulous ears", "puppy_coat": "smooth black-and-tan puppy coat"},
    "bloodhound": {"coat": "short black-and-tan coat with extraordinarily loose wrinkled skin", "puppy_coat": "smooth wrinkled black-and-tan puppy coat"},
    "bluetick-coonhound": {"coat": "short blue-mottled (steel-blue ticking on white) coat", "puppy_coat": "smooth blue-ticked puppy coat"},
    "border-collie": {"coat": "medium-length black-and-white double coat with feathering", "puppy_coat": "soft fluffy black-and-white puppy coat"},
    "borzoi": {"category": "long_silky", "coat": "long silky white-and-tan flowing coat", "puppy_coat": "soft long white-and-tan puppy coat"},
    "boston-terrier": {"coat": "short smooth tuxedo (black-and-white) coat with bat ears", "puppy_coat": "smooth tuxedo puppy coat"},
    "boxer": {"coat": "short fawn or brindle coat with white markings, square flat face", "puppy_coat": "smooth fawn puppy coat"},
    "brittany": {"coat": "medium wavy orange-and-white coat with feathering", "puppy_coat": "soft orange-and-white puppy coat"},
    "bull-terrier": {"coat": "short white coat with the iconic egg-shaped head profile", "puppy_coat": "smooth white puppy coat with the egg-shaped head"},
    "bulldog": {"coat": "short fawn-and-white coat, broad wrinkled head, stocky low frame", "puppy_coat": "smooth wrinkled fawn-and-white puppy coat"},
    "bullmastiff": {"coat": "short fawn coat with a black mask, large symmetrical frame", "puppy_coat": "soft fawn puppy coat with a dark mask"},
    "cane-corso": {"coat": "short stiff black or gray double coat, large muscular frame", "puppy_coat": "soft black or gray puppy coat"},
    "cardigan-welsh-corgi": {"category": "thick_double", "coat": "medium-length brindle or sable double coat, long-bodied low-set frame", "puppy_coat": "fluffy brindle puppy coat with oversized ears"},
    "cavalier-king-charles-spaniel": {"coat": "silky medium-length Blenheim (chestnut-and-white) coat with feathered ears", "puppy_coat": "soft Blenheim puppy coat"},
    "chesapeake-bay-retriever": {"coat": "wavy oily brown water-resistant double coat", "puppy_coat": "soft brown puppy coat"},
    "chihuahua": {"category": "smooth_short", "coat": "short smooth fawn coat with apple-dome head and large erect ears", "puppy_coat": "smooth fawn puppy coat with oversized ears"},
    "chow-chow": {"coat": "thick rough red double coat with a lion-like mane and blue-black tongue", "puppy_coat": "fluffy red puppy double coat"},
    "clumber-spaniel": {"coat": "dense flat silky white coat with lemon markings, heavy long-bodied build", "puppy_coat": "soft white-with-lemon puppy coat"},
    "cocker-spaniel": {"coat": "silky golden flowing coat with feathered long ears", "puppy_coat": "soft golden puppy coat with long ears"},
    "collie": {"coat": "long sable-and-white flowing double coat with a wedge head", "puppy_coat": "fluffy sable-and-white puppy coat"},
    "dachshund": {"category": "smooth_short", "coat": "short smooth rich red coat, long body and short legs", "puppy_coat": "smooth short red puppy coat"},
    "dalmatian": {"coat": "short white coat covered in distinctive black spots", "puppy_coat": "smooth white puppy coat (spots developing)"},
    "doberman-pinscher": {"coat": "short sleek black-and-rust coat, athletic muscular frame", "puppy_coat": "smooth black-and-rust puppy coat"},
    "dogue-de-bordeaux": {"coat": "short fawn coat with the largest head proportionally of any breed, deep wrinkles", "puppy_coat": "soft wrinkled fawn puppy coat"},
    "english-cocker-spaniel": {"coat": "silky flat blue roan coat with long feathered ears", "puppy_coat": "soft blue roan puppy coat"},
    "english-setter": {"coat": "long silky orange-belton (white with orange ticking) coat with feathering", "puppy_coat": "soft orange-belton puppy coat"},
    "english-springer-spaniel": {"coat": "medium wavy liver-and-white coat with long feathered ears", "puppy_coat": "soft liver-and-white puppy coat"},
    "field-spaniel": {"coat": "dense flat silky liver-brown coat with feathering on legs and ears", "puppy_coat": "soft liver-brown puppy coat"},
    "flat-coated-retriever": {"coat": "flat dense glossy black coat with light feathering", "puppy_coat": "soft black puppy coat"},
    "french-bulldog": {"coat": "short fawn coat, large bat ears, flat brachycephalic face, compact heavy-boned frame", "puppy_coat": "smooth fawn puppy coat with oversized bat ears"},
    "german-pinscher": {"coat": "short sleek black-and-rust coat, square athletic frame", "puppy_coat": "smooth black-and-rust puppy coat"},
    "german-shepherd-dog": {"category": "thick_double", "coat": "medium black-and-tan saddle pattern double coat", "puppy_coat": "soft black-and-tan puppy coat with floppy ears"},
    "german-shorthaired-pointer": {"coat": "short dense liver-roan coat (liver and white ticking)", "puppy_coat": "smooth liver-roan puppy coat"},
    "german-wirehaired-pointer": {"coat": "harsh wiry liver-and-white coat with prominent beard and eyebrows", "puppy_coat": "soft liver-and-white puppy coat (before the wiry adult coat develops)"},
    "golden-retriever": {"coat": "rich golden long flowing double coat with feathering", "puppy_coat": "fluffy soft golden puppy coat"},
    "gordon-setter": {"coat": "long silky black-and-tan coat with feathering, substantial muscular build", "puppy_coat": "soft black-and-tan puppy coat"},
    "great-dane": {"category": "smooth_short", "coat": "short sleek fawn coat with a black mask, towering elegant frame", "puppy_coat": "smooth fawn puppy coat with oversized paws"},
    "great-pyrenees": {"coat": "long thick weather-resistant white double coat", "puppy_coat": "fluffy white puppy double coat"},
    "greyhound": {"coat": "very short fine fawn coat, narrow aerodynamic body, tucked abdomen", "puppy_coat": "smooth short fawn puppy coat"},
    "harrier": {"coat": "short dense tricolor (black, tan, white) hound coat", "puppy_coat": "smooth tricolor puppy coat"},
    "havanese": {"coat": "long silky wavy multi-color coat (cream, gold, black combinations)", "puppy_coat": "soft wavy multi-color puppy coat"},
    "ibizan-hound": {"coat": "short fine red-and-white coat with large erect bat-like ears and amber eyes", "puppy_coat": "smooth red-and-white puppy coat with oversized erect ears"},
    "irish-setter": {"coat": "rich mahogany long silky coat with flowing feathering", "puppy_coat": "soft mahogany puppy coat"},
    "irish-water-spaniel": {"coat": "dense crisp tight liver-colored curls covering the body", "puppy_coat": "soft curly liver puppy coat"},
    "irish-wolfhound": {"coat": "rough harsh wiry gray coat, towering massively tall frame", "puppy_coat": "soft gray puppy coat (before adult wire develops)"},
    "italian-greyhound": {"coat": "very short fine fawn coat, miniature sighthound build", "puppy_coat": "smooth fawn puppy coat"},
    "labrador-retriever": {"coat": "short dense yellow water-resistant double coat with otter tail", "puppy_coat": "soft yellow puppy coat"},
    "lagotto-romagnolo": {"coat": "dense tight off-white-and-orange curly coat", "puppy_coat": "soft curly off-white puppy coat"},
    "maltese": {"coat": "long silky pure white single coat (no undercoat)", "puppy_coat": "soft white puppy coat"},
    "mastiff": {"coat": "short dense fawn coat with a black mask, massively heavy-boned frame", "puppy_coat": "soft fawn puppy coat with a dark mask"},
    "miniature-american-shepherd": {"coat": "medium-length blue merle double coat with white and copper markings", "puppy_coat": "soft blue merle puppy coat"},
    "miniature-poodle": {"coat": "dense apricot curly coat in a refined elegant cut", "puppy_coat": "soft apricot curly puppy coat"},
    "miniature-schnauzer": {"coat": "wiry salt-and-pepper coat with prominent beard and bushy eyebrows", "puppy_coat": "soft salt-and-pepper puppy coat (before the wiry adult coat develops)"},
    "neapolitan-mastiff": {"coat": "short dense blue-gray coat with abundance of loose wrinkled skin", "puppy_coat": "soft wrinkled blue-gray puppy coat"},
    "newfoundland": {"coat": "long dense flat black water-resistant double coat", "puppy_coat": "fluffy black puppy double coat"},
    "norwegian-elkhound": {"coat": "thick gray double coat with darker face and saddle, curled tail over back", "puppy_coat": "fluffy gray puppy double coat"},
    "nova-scotia-duck-tolling-retriever": {"coat": "medium-length golden-red double coat with white markings, fox-like build", "puppy_coat": "soft golden-red puppy coat"},
    "old-english-sheepdog": {"coat": "profuse shaggy gray-and-white double coat covering the eyes", "puppy_coat": "fluffy gray-and-white puppy coat"},
    "pembroke-welsh-corgi": {"category": "thick_double", "coat": "medium-length red-and-white double coat, long-bodied with very short legs", "puppy_coat": "fluffy red-and-white puppy coat with oversized ears"},
    "pharaoh-hound": {"coat": "short fine rich tan coat with large erect ears and amber eyes", "puppy_coat": "smooth rich tan puppy coat with oversized erect ears"},
    "pointer": {"coat": "short smooth liver-and-white coat, lean athletic frame", "puppy_coat": "smooth liver-and-white puppy coat"},
    "pomeranian": {"category": "thick_double", "coat": "soft dense orange double coat fanning out into a fox-like ruff", "puppy_coat": "fluffy orange puppy coat"},
    "portuguese-water-dog": {"coat": "dense black tight-curled single-layer coat", "puppy_coat": "soft black curly puppy coat"},
    "pug": {"coat": "short smooth fawn coat with deep wrinkles and curled tail, brachycephalic flat face", "puppy_coat": "smooth fawn puppy coat with curled tail and wrinkled face"},
    "rhodesian-ridgeback": {"coat": "short wheaten coat with the distinctive reverse-growing dorsal ridge", "puppy_coat": "smooth wheaten puppy coat"},
    "rottweiler": {"coat": "short dense black-and-mahogany double coat, large heavily-built frame", "puppy_coat": "smooth black-and-mahogany puppy coat"},
    "saint-bernard": {"coat": "long red-and-white coat with broad flat head and deep jowls", "puppy_coat": "fluffy red-and-white puppy coat"},
    "saluki": {"coat": "smooth cream-and-tan sighthound coat with feathered ears and tail", "puppy_coat": "soft cream-and-tan puppy coat"},
    "samoyed": {"category": "thick_double", "coat": "thick cloud-like pure white double coat with a smiling expression", "puppy_coat": "fluffy pure white puppy double coat"},
    "shetland-sheepdog": {"coat": "long sable-and-white double coat with mane and frill (miniature collie look)", "puppy_coat": "fluffy sable-and-white puppy coat"},
    "shiba-inu": {"category": "thick_double", "coat": "thick red double coat with urajiro (white markings on cheeks/chest), curled tail", "puppy_coat": "fluffy red puppy double coat"},
    "shih-tzu": {"coat": "long flowing silky multi-color double coat (gold, white, brindle)", "puppy_coat": "soft puppy coat with flat brachycephalic face"},
    "siberian-husky": {"coat": "thick black-and-white double coat with blue or bicolor eyes, wolf-like profile", "puppy_coat": "fluffy black-and-white puppy double coat"},
    "soft-coated-wheaten-terrier": {"coat": "soft silky wavy wheaten (warm gold) single coat", "puppy_coat": "soft wheaten puppy coat"},
    "spinone-italiano": {"coat": "harsh wiry white-and-orange coat with shaggy beard and eyebrows, large frame", "puppy_coat": "soft white-and-orange puppy coat"},
    "staffordshire-bull-terrier": {"coat": "short smooth red coat, broad-skulled muscular compact frame", "puppy_coat": "smooth red puppy coat"},
    "standard-poodle": {"coat": "dense black curly coat in an elegant continental or sporting clip", "puppy_coat": "soft black curly puppy coat"},
    "tibetan-mastiff": {"coat": "very thick black-and-tan double coat with a dramatic lion-like mane", "puppy_coat": "fluffy black-and-tan puppy double coat"},
    "vizsla": {"coat": "short uniform rust-golden coat, lean athletic frame", "puppy_coat": "smooth rust-golden puppy coat"},
    "weimaraner": {"coat": "short sleek silver-gray coat, tall lean elegant frame", "puppy_coat": "smooth silver-gray puppy coat with pale blue eyes"},
    "welsh-springer-spaniel": {"coat": "silky flat rich-red-and-white coat with feathering", "puppy_coat": "soft red-and-white puppy coat"},
    "west-highland-white-terrier": {"category": "wiry_terrier", "coat": "hard dense pure white double coat with a full-face mane", "puppy_coat": "soft white puppy coat"},
    "whippet": {"coat": "very short smooth brindle-and-white coat, lean aerodynamic frame", "puppy_coat": "smooth brindle-and-white puppy coat"},
    "wirehaired-pointing-griffon": {"coat": "harsh wiry steel-gray coat with brown markings, bushy mustache and eyebrows", "puppy_coat": "soft steel-gray puppy coat (before the wiry adult coat develops)"},
    "yorkshire-terrier": {"coat": "long fine silky steel-blue-and-tan single coat (resembles human hair)", "puppy_coat": "soft black-and-tan puppy coat (color matures over months)"},

    # ── Unpublished breeds (Phase 1) ─────────────────────────────────────────
    "affenpinscher": {"category": "wiry_terrier", "coat": "scruffy wiry black coat with monkey-like beard and bushy eyebrows", "puppy_coat": "soft black puppy coat"},
    "airedale-terrier": {"category": "wiry_terrier", "coat": "dense wiry black saddle and tan body with a beard and bushy eyebrows", "puppy_coat": "soft fluffy black-and-tan puppy coat (still soft, before the wiry adult coat develops)"},
    "american-eskimo-dog": {"category": "thick_double", "coat": "thick pure white double coat with a fluffy ruff", "puppy_coat": "fluffy white puppy double coat"},
    "australian-terrier": {"category": "wiry_terrier", "coat": "harsh wiry blue-and-tan coat with a soft topknot", "puppy_coat": "soft blue-and-tan puppy coat"},
    "bearded-collie": {"category": "thick_double", "coat": "long shaggy gray-and-white double coat with a full beard", "puppy_coat": "fluffy gray-and-white puppy coat"},
    "beauceron": {"category": "smooth_short", "coat": "short black-and-tan double coat with double dewclaws on rear legs, large athletic frame", "puppy_coat": "smooth black-and-tan puppy coat"},
    "bedlington-terrier": {"category": "curly_poodle", "coat": "crisp curly low-shedding lamb-like coat with a fluffy lighter topknot", "puppy_coat": "soft fluffy crisp curly puppy coat"},
    "belgian-sheepdog": {"category": "thick_double", "coat": "long jet-black double coat with abundant ruff and feathering", "puppy_coat": "fluffy black puppy coat"},
    "belgian-tervuren": {"category": "thick_double", "coat": "long mahogany-fawn double coat with black overlay and feathering", "puppy_coat": "fluffy mahogany puppy coat"},
    "border-terrier": {"category": "wiry_terrier", "coat": "harsh wiry grizzle-and-tan coat with otter-like head", "puppy_coat": "soft grizzle-and-tan puppy coat"},
    "bouvier-des-flandres": {"category": "wiry_terrier", "coat": "harsh wiry tousled black coat with prominent beard and bushy eyebrows, large athletic frame", "puppy_coat": "soft black puppy coat"},
    "briard": {"category": "long_silky", "coat": "long flowing tawny double coat with shaggy beard and eyebrows covering the eyes", "puppy_coat": "soft tawny puppy coat"},
    "brussels-griffon": {"category": "wiry_terrier", "coat": "rough wiry red coat with full beard and pushed-in monkey-like face", "puppy_coat": "soft red puppy coat"},
    "cairn-terrier": {"category": "wiry_terrier", "coat": "shaggy harsh wiry wheaten coat (Toto-style)", "puppy_coat": "soft wheaten puppy coat"},
    "chinese-crested": {"category": "hairless", "coat": "smooth pinkish hairless skin with feathered crest, ankle plumes, and plumed tail (hairless variety)", "puppy_coat": "smooth pink puppy skin with soft tufted crest"},
    "chinese-shar-pei": {"category": "smooth_short", "coat": "short bristly fawn coat with deep characteristic loose wrinkles and hippopotamus-like muzzle", "puppy_coat": "deeply wrinkled fawn puppy coat (extreme wrinkles)"},
    "coton-de-tulear": {"category": "long_silky", "coat": "long cotton-soft pure white coat", "puppy_coat": "soft fluffy white puppy coat"},
    "entlebucher-mountain-dog": {"category": "smooth_short", "coat": "short tricolor (black, rust, white) Swiss mountain dog coat with athletic compact frame", "puppy_coat": "smooth tricolor puppy coat"},
    "finnish-lapphund": {"category": "thick_double", "coat": "thick long black double coat with profuse ruff and curled tail", "puppy_coat": "fluffy black puppy double coat"},
    "finnish-spitz": {"category": "thick_double", "coat": "fox-red double coat with curled tail over the back, fox-like face", "puppy_coat": "fluffy red puppy coat"},
    "giant-schnauzer": {"category": "wiry_terrier", "coat": "harsh wiry black or salt-and-pepper coat with prominent beard and bushy eyebrows, large powerful frame", "puppy_coat": "soft black puppy coat"},
    "greater-swiss-mountain-dog": {"category": "thick_double", "coat": "short tricolor (black, rust, white) double coat, large powerful Swiss mountain frame", "puppy_coat": "soft tricolor puppy coat"},
    "icelandic-sheepdog": {"category": "thick_double", "coat": "thick tan-and-white double coat with curled tail, spitz-type build", "puppy_coat": "fluffy tan-and-white puppy coat"},
    "irish-terrier": {"category": "wiry_terrier", "coat": "harsh wiry rich red coat with beard and eyebrows", "puppy_coat": "soft red puppy coat"},
    "japanese-chin": {"category": "long_silky", "coat": "long silky black-and-white coat with flat brachycephalic face", "puppy_coat": "soft black-and-white puppy coat"},
    "keeshond": {"category": "thick_double", "coat": "thick gray-and-cream double coat with characteristic spectacle markings around the eyes", "puppy_coat": "fluffy gray puppy coat"},
    "kerry-blue-terrier": {"category": "curly_poodle", "coat": "soft dense wavy blue-gray coat with beard", "puppy_coat": "soft blue-gray puppy coat (born black, clears to blue over months)"},
    "komondor": {"category": "corded", "coat": "long white corded mop-like coat", "puppy_coat": "fluffy soft white pre-cord puppy fur"},
    "lakeland-terrier": {"category": "wiry_terrier", "coat": "harsh wiry blue-and-tan coat with beard and eyebrows", "puppy_coat": "soft blue-and-tan puppy coat"},
    "leonberger": {"category": "thick_double", "coat": "long lion-like golden-mahogany double coat with dark mask, large gentle giant frame", "puppy_coat": "fluffy golden puppy coat"},
    "lhasa-apso": {"category": "long_silky", "coat": "long flowing silky golden double coat reaching the floor", "puppy_coat": "soft golden puppy coat"},
    "lowchen": {"category": "long_silky", "coat": "long silky white-and-cream coat in characteristic 'little lion' clip", "puppy_coat": "soft white-and-cream puppy coat"},
    "miniature-bull-terrier": {"category": "smooth_short", "coat": "short white coat with the iconic egg-shaped head profile (smaller than standard Bull Terrier)", "puppy_coat": "smooth white puppy coat with the egg-shaped head"},
    "miniature-pinscher": {"category": "smooth_short", "coat": "short sleek black-and-rust coat with hackney-trotting toy frame", "puppy_coat": "smooth black-and-rust puppy coat"},
    "norfolk-terrier": {"category": "wiry_terrier", "coat": "harsh wiry red coat with folded drop ears", "puppy_coat": "soft red puppy coat"},
    "norwich-terrier": {"category": "wiry_terrier", "coat": "harsh wiry red coat with prick ears", "puppy_coat": "soft red puppy coat"},
    "otterhound": {"category": "wirehaired_sporting", "coat": "rough harsh wiry grizzle coat, large bear-like build, long droopy ears", "puppy_coat": "soft grizzle puppy coat"},
    "papillon": {"category": "long_silky", "coat": "long silky black-and-white coat with butterfly-shaped fringed erect ears", "puppy_coat": "soft black-and-white puppy coat with oversized fringed ears"},
    "parson-russell-terrier": {"category": "smooth_short", "coat": "short white-with-tan coat (predominantly white body, athletic working terrier frame)", "puppy_coat": "smooth white-with-tan puppy coat"},
    "pekingese": {"category": "long_silky", "coat": "long flowing thick gold-and-white double coat with lion-like mane and flat brachycephalic face", "puppy_coat": "fluffy gold-and-white puppy coat"},
    "polish-lowland-sheepdog": {"category": "thick_double", "coat": "long shaggy gray-and-white double coat covering the eyes", "puppy_coat": "fluffy gray-and-white puppy coat"},
    "puli": {"category": "corded", "coat": "long black corded mop-like coat", "puppy_coat": "fluffy soft black pre-cord puppy fur"},
    "redbone-coonhound": {"category": "smooth_short", "coat": "short solid mahogany-red hound coat with long pendulous ears", "puppy_coat": "smooth red puppy coat"},
    "russell-terrier": {"category": "smooth_short", "coat": "short white-with-tan coat (Jack Russell type, athletic compact frame)", "puppy_coat": "smooth white-with-tan puppy coat"},
    "schipperke": {"category": "thick_double", "coat": "thick black double coat with profuse ruff, fox-like face, naturally tailless", "puppy_coat": "fluffy black puppy coat"},
    "scottish-deerhound": {"category": "wirehaired_sporting", "coat": "harsh wiry blue-gray coat, towering Greyhound-like sighthound silhouette", "puppy_coat": "soft blue-gray puppy coat"},
    "scottish-terrier": {"category": "wiry_terrier", "coat": "harsh wiry black coat with characteristic beard and eyebrows, short legs", "puppy_coat": "soft black puppy coat"},
    "silky-terrier": {"category": "long_silky", "coat": "long fine silky steel-blue-and-tan coat (resembles miniature Yorkie)", "puppy_coat": "soft black-and-tan puppy coat"},
    "skye-terrier": {"category": "long_silky", "coat": "long flowing silver-blue coat reaching the ground with drop ears", "puppy_coat": "soft silver-blue puppy coat"},
    "spanish-water-dog": {"category": "curly_poodle", "coat": "dense corded or curled brown coat (often clipped uniformly)", "puppy_coat": "soft curly brown puppy coat"},
    "standard-schnauzer": {"category": "wiry_terrier", "coat": "harsh wiry salt-and-pepper coat with prominent beard and bushy eyebrows", "puppy_coat": "soft salt-and-pepper puppy coat"},
    "swedish-vallhund": {"category": "thick_double", "coat": "short gray-and-tan double coat, low-bodied corgi-like Spitz frame", "puppy_coat": "fluffy gray-and-tan puppy coat"},
    "tibetan-spaniel": {"category": "long_silky", "coat": "medium silky golden double coat with feathered tail, flat-faced", "puppy_coat": "soft golden puppy coat"},
    "tibetan-terrier": {"category": "long_silky", "coat": "long flowing silky double coat (white, gold, or black) covering the eyes", "puppy_coat": "fluffy puppy coat"},
    "toy-fox-terrier": {"category": "smooth_short", "coat": "short tricolor (black, white, tan) toy frame", "puppy_coat": "smooth tricolor puppy coat"},
    "welsh-terrier": {"category": "wiry_terrier", "coat": "harsh wiry black-and-tan coat with beard and eyebrows", "puppy_coat": "soft black-and-tan puppy coat"},
    "wire-fox-terrier": {"category": "wiry_terrier", "coat": "harsh wiry white-with-tan-markings coat with prominent beard and eyebrows", "puppy_coat": "soft white-with-tan puppy coat"},
    "xoloitzcuintli": {"category": "hairless", "coat": "smooth dark gray-black hairless skin with almond eyes and bat-like ears (hairless variety)", "puppy_coat": "smooth dark gray-black hairless puppy skin"},
}


def main() -> int:
    if not META_PUB.exists():
        print(f"missing {META_PUB}; run the published-meta dump first")
        return 1

    breeds = json.loads(META_PUB.read_text(encoding="utf-8"))
    if META_UNPUB.exists():
        unpub = json.loads(META_UNPUB.read_text(encoding="utf-8"))
        seen = {b["slug"] for b in breeds}
        breeds += [b for b in unpub if b["slug"] not in seen]
    rows: list[dict] = []
    skipped: list[str] = []

    for b in breeds:
        slug = b["slug"]
        if not b.get("appearance"):
            skipped.append(slug)
            continue

        ov = OVERRIDES.get(slug, {})
        category = ov.get("category") or detect_category(b["appearance"], b["name"])
        grooming_action = CATEGORY_GROOMING[category]
        coat = ov.get("coat") or f"{category.replace('_',' ')} coat"
        puppy_coat = ov.get("puppy_coat") or f"soft {coat} puppy coat"
        grooming_action = ov.get("grooming_action", grooming_action)

        rows.append({
            "slug": slug,
            "name": b["name"],
            "category": category,
            "coat": coat,
            "grooming_action": grooming_action,
            "puppy_coat": puppy_coat,
        })

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT.name} with {len(rows)} breeds; skipped {len(skipped)}: {skipped[:5]}{'...' if len(skipped)>5 else ''}")

    from collections import Counter
    hist = Counter(r["category"] for r in rows)
    print("\ncategory distribution:")
    for cat, n in hist.most_common():
        print(f"  {cat:20} {n}")

    missing_overrides = [r["slug"] for r in rows if r["slug"] not in OVERRIDES]
    if missing_overrides:
        print(f"\nbreeds without curated coat override (using fallback phrase): {len(missing_overrides)}")
        for s in missing_overrides:
            print(f"  - {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
