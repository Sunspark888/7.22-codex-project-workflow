#!/usr/bin/env python3
"""Render verified platform cover variants from one approved square key visual."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from source_credit import score_credit, credit_cover


VARIANTS = {
    "主视觉_1x1": (1080, 1080),
    "小红书_4x3": (1440, 1080),
    "抖音_3x4": (1080, 1440),
    "快手_3x4": (1080, 1440),
    "视频号_3x4": (1080, 1440),
}


def fail(message: str) -> None:
    raise ValueError(message)


def resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def atomic_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".rendering.png")
    image.save(temporary, format="PNG", compress_level=6)
    with Image.open(temporary) as check:
        check.load()
        if check.size != image.size:
            fail(f"PNG size mismatch: {temporary}")
    os.replace(temporary, path)


def atomic_json(data: Any, path: Path) -> None:
    temporary = path.with_name(path.name + ".rendering")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def cover_fill(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    x = (resized.width - size[0]) // 2
    y = (resized.height - size[1]) // 2
    return resized.crop((x, y, x + size[0], y + size[1]))


def load_font(path: Path | None, size: int) -> ImageFont.FreeTypeFont:
    if path is not None:
        return ImageFont.truetype(str(path), size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)


def contains_non_ascii(text: str) -> bool:
    return any(ord(character) > 127 for character in text)


def draw_centered(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.FreeTypeFont, width: int, size: int) -> None:
    box = draw.textbbox((0, 0), text, font=font, stroke_width=max(1, size // 24))
    x = (width - (box[2] - box[0])) / 2
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 245),
              stroke_width=max(1, size // 24), stroke_fill=(5, 10, 18, 220))


def render(source: Image.Image, size: tuple[int, int], headline: str, subtitle: str, font_path: Path | None) -> tuple[Image.Image, list[int]]:
    width, height = size
    background = cover_fill(source, size).filter(ImageFilter.GaussianBlur(round(min(size) * 0.035)))
    background = ImageEnhance.Color(background).enhance(0.72)
    veil = Image.new("RGBA", size, (5, 12, 24, 72))
    canvas = Image.alpha_composite(background.convert("RGBA"), veil).convert("RGB")

    # Keep the complete approved square artwork visible; extensions, not crops, absorb aspect-ratio changes.
    reserve = 0 if not (headline or subtitle) else round(height * 0.12)
    square = min(round(width * 0.92), round((height - reserve) * 0.88))
    artwork = source.copy()
    artwork.thumbnail((square, square), Image.Resampling.LANCZOS)
    x = (width - square) // 2
    y = max(round(height * 0.05), (height - reserve - square) // 2)
    canvas.paste(artwork, (x + (square-artwork.width)//2, y + (square-artwork.height)//2))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((x - 3, y - 3, x + square + 3, y + square + 3), radius=8,
                           outline=(226, 238, 255, 175), width=max(2, round(width / 540)))

    text_y = y + square + round(height * 0.025)
    if headline:
        text_size = max(32, round(min(size) * 0.048))
        draw_centered(draw, headline, text_y, load_font(font_path, text_size), width, text_size)
        text_y += round(text_size * 1.35)
    if subtitle:
        text_size = max(24, round(min(size) * 0.030))
        draw_centered(draw, subtitle, text_y, load_font(font_path, text_size), width, text_size)
    return canvas, [x, y, square, square]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        manifest_path = args.manifest.resolve()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        credit = score_credit(data)
        base = manifest_path.parent
        cfg = data.get("social_cover") or {}
        if not cfg.get("enabled", True):
            print(json.dumps({"status": "skipped", "reason": "social_cover.enabled is false"}, ensure_ascii=False))
            return 0
        source_path = resolve(base, cfg.get("source") or data.get("cover") or data["assets"]["cover"])
        output_dir = resolve(base, cfg.get("output_dir", "output/covers"))
        overwrite = bool(cfg.get("overwrite", False))
        headline = str(cfg.get("headline", "")).strip()
        subtitle = str(cfg.get("subtitle", "")).strip()
        font_path = resolve(base, cfg["font_file"]) if cfg.get("font_file") else None
        if font_path is not None and not font_path.is_file():
            fail(f"Font file missing: {font_path}")
        if (contains_non_ascii(headline) or contains_non_ascii(subtitle)) and font_path is None:
            fail("Non-ASCII cover text requires social_cover.font_file with Chinese glyph support")
        if not source_path.is_file():
            fail(f"Cover source missing: {source_path}")
        with Image.open(source_path) as opened:
            opened.load()
            source = opened.convert("RGB")
        song = str((data.get("project") or {}).get("song", "作品")).strip() or "作品"
        records = []
        for label, size in cfg.get("variants", VARIANTS).items():
            if len(size) != 2 or any(not isinstance(v, int) or v <= 0 for v in size):
                fail("Cover variant size must be two positive integer pixels")
            output = output_dir / f"{song}_封面_{label}.png"
            if output.exists() and not overwrite:
                fail(f"Output exists and overwrite is false: {output}")
            image, artwork_box = render(source, size, headline, subtitle, font_path)
            image = credit_cover(image, data, base)
            atomic_png(image, output)
            records.append({
                "variant": label, "path": str(output), "width": size[0], "height": size[1],
                "artwork_safe_box": artwork_box,
            })
        report = {
            "status": "passed", "source": str(source_path),
            "headline": headline, "subtitle": subtitle, "outputs": records,
            "source_credit": credit,
            "note": "Confirm each current app crop preview before publishing.",
        }
        report_path = output_dir / "covers.qc.json"
        atomic_json(report, report_path)
        print(json.dumps({"status": "built", "report": str(report_path), "outputs": records}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, json.JSONDecodeError, OSError) as error:
        print(f"ERROR: {error}", file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
