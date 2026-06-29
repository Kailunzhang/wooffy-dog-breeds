"""Generate 2:3 vertical Pinterest pins (1000x1500) from article hero images.

Two templates (hybrid per user spec):

  Feature pin (cost / roundup / guide / comparison):
    Top 60%: hero image filled, cropped to 1000x900
    Bottom 40%: white background with
      - small uppercase gray label (e.g. "FIRST-YEAR COST")
      - big orange number/hook (e.g. "$2,500-$5,000")
      - bold black title (e.g. "Goldendoodle Cost Breakdown")
      - bottom rule: thin orange line + "WOOFFY" wordmark

  Breed pin (main breed page):
    Image fills 1000x1500 (cropped to 2:3 from center)
    Bottom-right overlay: small white card with
      "WOOFFY" wordmark + orange divider + thewooffy.com

Swiss-inspired: Helvetica-class (Arial Bold), black + single orange,
right angles, tight letter spacing.

Run as a test pass (no args) to generate 2 sample pins:
    python3 scripts/pinterest_pin_designer.py
"""
from __future__ import annotations

import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"
OUT_DIR = ROOT / "pinterest-assets"
HERO_CACHE = ROOT / "pinterest-assets" / "_hero-cache"

PIN_W = 1000
PIN_H = 1500

COLOR_BLACK = (26, 26, 26)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (107, 113, 119)
COLOR_ORANGE = (255, 106, 26)

FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_REGULAR = "C:/Windows/Fonts/Arial.ttf"


@dataclass
class PinConfig:
    slug: str
    template: Literal["feature", "breed"]
    label: str = ""
    hook: str = ""
    title: str = ""
    pin_index: int = 1


def fetch_hero(slug: str) -> Image.Image:
    HERO_CACHE.mkdir(parents=True, exist_ok=True)
    cache = HERO_CACHE / f"{slug}.png"
    if cache.exists():
        return Image.open(cache).convert("RGB")
    data = json.loads((BREED_DATA / f"{slug}.json").read_text(encoding="utf-8"))
    url = data["images"]["hero"]["url"]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    img.save(cache, "PNG")
    return img


def crop_to_aspect(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Crop from center to target aspect, then resize."""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))
    return img.resize((target_w, target_h), Image.LANCZOS)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        candidate = (current + " " + w).strip()
        if text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def render_feature_pin(cfg: PinConfig) -> Image.Image:
    canvas = Image.new("RGB", (PIN_W, PIN_H), COLOR_WHITE)
    hero = fetch_hero(cfg.slug)
    image_block = crop_to_aspect(hero, PIN_W, 900)
    canvas.paste(image_block, (0, 0))

    draw = ImageDraw.Draw(canvas)
    text_block_top = 900
    text_block_bottom = PIN_H
    pad = 60
    inner_w = PIN_W - 2 * pad

    label = (cfg.label or "").upper()
    if label:
        f_label = ImageFont.truetype(FONT_BOLD, 26)
        spaced = " ".join(label)
        _, lh = text_size(draw, spaced, f_label)
        draw.text((pad, text_block_top + 50), spaced, font=f_label, fill=COLOR_GRAY)
        next_y = text_block_top + 50 + lh + 20
    else:
        next_y = text_block_top + 70

    if cfg.hook:
        for size in (160, 140, 120, 100, 88, 76):
            f_hook = ImageFont.truetype(FONT_BOLD, size)
            if text_size(draw, cfg.hook, f_hook)[0] <= inner_w:
                break
        _, hh = text_size(draw, cfg.hook, f_hook)
        draw.text((pad, next_y), cfg.hook, font=f_hook, fill=COLOR_ORANGE)
        next_y += hh + 26

    if cfg.title:
        f_title = ImageFont.truetype(FONT_BOLD, 44)
        lines = wrap_text(cfg.title, f_title, inner_w, draw)
        for ln in lines[:3]:
            _, th = text_size(draw, ln, f_title)
            draw.text((pad, next_y), ln, font=f_title, fill=COLOR_BLACK)
            next_y += th + 8

    rule_y = text_block_bottom - 90
    draw.rectangle((pad, rule_y, pad + 60, rule_y + 3), fill=COLOR_ORANGE)
    f_wm = ImageFont.truetype(FONT_BOLD, 26)
    f_url = ImageFont.truetype(FONT_REGULAR, 20)
    draw.text((pad, rule_y + 16), "WOOFFY", font=f_wm, fill=COLOR_BLACK)
    url_text = "thewooffy.com"
    uw, _ = text_size(draw, url_text, f_url)
    draw.text((PIN_W - pad - uw, rule_y + 22), url_text, font=f_url, fill=COLOR_GRAY)

    return canvas


def render_breed_pin(cfg: PinConfig) -> Image.Image:
    hero = fetch_hero(cfg.slug)
    canvas = crop_to_aspect(hero, PIN_W, PIN_H)

    draw = ImageDraw.Draw(canvas)
    card_w, card_h = 320, 110
    margin = 40
    card_x = PIN_W - card_w - margin
    card_y = PIN_H - card_h - margin
    shadow = Image.new("RGBA", (card_w + 30, card_h + 30), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle((10, 10, card_w + 10, card_h + 10), fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    canvas.paste(shadow, (card_x - 15, card_y - 15), shadow)
    draw.rectangle((card_x, card_y, card_x + card_w, card_y + card_h), fill=COLOR_WHITE)
    f_wm = ImageFont.truetype(FONT_BOLD, 32)
    f_url = ImageFont.truetype(FONT_REGULAR, 18)
    draw.text((card_x + 24, card_y + 18), "WOOFFY", font=f_wm, fill=COLOR_BLACK)
    div_y = card_y + 60
    draw.rectangle((card_x + 24, div_y, card_x + 64, div_y + 3), fill=COLOR_ORANGE)
    draw.text((card_x + 24, card_y + 72), "thewooffy.com", font=f_url, fill=COLOR_GRAY)
    return canvas


def render(cfg: PinConfig, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    if cfg.template == "feature":
        img = render_feature_pin(cfg)
    else:
        img = render_breed_pin(cfg)
    out_path = out_dir / f"{cfg.slug}-pin-{cfg.pin_index}.png"
    img.save(out_path, "PNG", optimize=True)
    return out_path


def main() -> int:
    test_pins = [
        PinConfig(
            slug="dog-food-on-a-budget-2026",
            template="feature",
            label="dog food inflation",
            hook="+143%",
            title="How to Feed Your Dog Well on a Budget in 2026",
            pin_index=1,
        ),
        PinConfig(
            slug="golden-retriever",
            template="breed",
            pin_index=1,
        ),
    ]
    for cfg in test_pins:
        try:
            path = render(cfg, OUT_DIR)
            print(f"  OK    {cfg.template:8s} {cfg.slug:42s}  -> {path}")
        except Exception as e:
            print(f"  FAIL  {cfg.slug}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
