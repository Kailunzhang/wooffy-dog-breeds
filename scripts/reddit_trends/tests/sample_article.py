"""A minimal article JSON that passes writer.validate_article; shared by the test modules."""


def good_article(words_per_section: int = 500) -> dict:
    body = " ".join(["word"] * words_per_section)

    def sec(n: int) -> dict:
        return {"label": "Label", "heading": f"Heading {n}", "html": f"<p>{body}</p>"}

    return {
        "name": "Puppy Whining at Night: A Calm Step-by-Step Plan",
        "title_tag": "Puppy Whining at Night: What to Do",
        "meta_description": "A calm plan for puppy night whining.",
        "excerpt": "Why puppies whine at night and what actually helps.",
        "tagline": "tag",
        "tags": ["puppy", "sleep"],
        "sections": {"intro": sec(1), "care": sec(2), "special": sec(3)},
        "faq": [{"q": f"Q{i}?", "a": "Answer " * 20} for i in range(6)],
        "related": [["golden-retriever", "Golden Retriever Guide"]],
        "hero_prompt": "A sleeping puppy in a crate",
        "hero_alt": "Sleeping puppy in a crate at night",
    }
