"""Daily Reddit-trend article pipeline for thewooffy.com.

Reads public Atom feeds of dog subreddits (no API key, ~1 request/min
allowed), asks Claude to pick one topic that the site does not cover yet,
writes a hub-style guide in the breed-data JSON schema, generates a hero
image, publishes through scripts/generate.py and emails a summary.

Entry point: ``python3 scripts/reddit_trends/run.py`` (see run.py --help).
"""
