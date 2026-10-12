"""Hero image for a trend article: fal.ai nano-banana-pro -> Shopify Files CDN.

Reuses the root generate_breed_images.py (submit/poll/download) and
scripts/shopify_files_upload.py. If no FAL key is available or anything
fails, the caller gets the shared placeholder hero and ``is_fallback``
so the daily email can say the image still needs replacing (this is the
stale-hero failure mode the breed cron already had).
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from writer import GUIDE_STYLE, PLACEHOLDER_HERO  # noqa: E402

OUT_DIR = ROOT / "output" / "reddit-trends" / "heroes"


@dataclass
class HeroResult:
    url: str
    alt: str
    is_fallback: bool
    error: str = ""


def load_fal_key() -> str:
    """FAL_KEY env (GitHub Actions) or the local ~/.claude.json MCP config."""
    key = os.environ.get("FAL_KEY", "").strip()
    if key:
        return key
    cfg = Path.home() / ".claude.json"
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return (data.get("mcpServers", {}).get("fal-ai", {}).get("env", {}).get("FAL_KEY") or "").strip()


def make_hero(slug: str, prompt: str, alt: str, *, store: str, token: str,
              fal_key: str | None = None, upload: bool = True) -> HeroResult:
    fal_key = load_fal_key() if fal_key is None else fal_key
    if not fal_key:
        return HeroResult(PLACEHOLDER_HERO, alt, True, "no FAL key")
    try:
        import generate_breed_images as gbi  # noqa: WPS433
        import shopify_files_upload as sfu  # noqa: WPS433

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        full_prompt = f"{prompt.rstrip('.')}, {GUIDE_STYLE}"
        local = gbi.run_one(fal_key, f"{slug}-hero", full_prompt, OUT_DIR)
        if not upload:
            return HeroResult(str(local), alt, False)
        cdn_url = sfu.upload_one(store, token, local, alt=alt)
        return HeroResult(cdn_url, alt, False)
    except Exception as exc:  # noqa: BLE001 - any hero failure must not block publishing
        return HeroResult(PLACEHOLDER_HERO, alt, True, f"{type(exc).__name__}: {exc}")
