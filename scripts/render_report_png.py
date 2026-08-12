#!/usr/bin/env python3
"""Render report.json into a standalone 900x1200 PNG using Pillow."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError as exc:
    raise SystemExit("Pillow is required to render report.png. Install the Python pillow package in the Marvis runtime.") from exc


WIDTH, HEIGHT = 900, 1200
MARGIN = 54


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--personality-image", help="Defaults to the image named in report.json beside the report file.")
    return parser.parse_args()


def font_path() -> str:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    raise SystemExit("No usable CJK font found for report.png rendering.")


def font(size: int, bold: bool = False):
    path = font_path()
    try:
        return ImageFont.truetype(path, size=size, index=1 if bold and path.endswith(".ttc") else 0)
    except OSError:
        return ImageFont.truetype(path, size=size)


def wrap(draw: ImageDraw.ImageDraw, text: str, selected_font, max_width: int) -> list[str]:
    lines = []
    current = ""
    for char in text:
        candidate = current + char
        if current and draw.textbbox((0, 0), candidate, font=selected_font)[2] > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_text_lines(draw, xy, text, selected_font, fill, max_width, spacing=6, max_lines=None):
    x, y = xy
    lines = wrap(draw, text, selected_font, max_width)
    if max_lines:
        lines = lines[:max_lines]
    line_height = selected_font.size + spacing
    for line in lines:
        draw.text((x, y), line, font=selected_font, fill=fill)
        y += line_height
    return y


def main():
    args = parse_args()
    report_path = Path(args.report).expanduser().resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    image_path = Path(args.personality_image).expanduser().resolve() if args.personality_image else report_path.parent / report["personality_image"]
    if not image_path.exists():
        raise SystemExit(f"Personality image not found: {image_path}")

    bg = report["colors"]["bg"]
    accent = report["colors"]["accent"]
    ink = report["colors"]["text"]
    canvas = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((24, 24, WIDTH - 24, HEIGHT - 24), outline=accent, width=1)

    draw.text((MARGIN, 50), "YOUR MARVIS WORK MBTI", font=font(17, True), fill=accent)
    draw.rounded_rectangle((MARGIN, 88, MARGIN + 138, 128), radius=3, fill="#FFFFFF", outline=accent, width=1)
    draw.text((MARGIN + 14, 98), report["camp"], font=font(16, True), fill=ink)
    draw.text((MARGIN, 156), report["type"], font=font(54, True), fill=accent)
    draw.text((MARGIN, 218), report["name"], font=font(39, True), fill=ink)
    draw_text_lines(draw, (MARGIN, 278), report["tagline"], font(20), ink, 500, spacing=7, max_lines=2)

    personality = Image.open(image_path).convert("RGB")
    personality = ImageOps.fit(personality, (240, 240), method=Image.Resampling.LANCZOS)
    canvas.paste(personality, (WIDTH - MARGIN - 240, 54))
    draw.rectangle((WIDTH - MARGIN - 240, 54, WIDTH - MARGIN, 294), outline=accent, width=1)

    section_y = 365
    draw.text((MARGIN, section_y), "电脑出卖了你", font=font(17, True), fill=accent)
    y = section_y + 42
    for index, item in enumerate(report["evidence"], start=1):
        draw.line((MARGIN, y - 10, WIDTH - MARGIN, y - 10), fill=accent, width=1)
        draw.text((MARGIN, y + 4), f"0{index}", font=font(15, True), fill=accent)
        draw.text((MARGIN + 62, y), item["title"], font=font(18, True), fill=ink)
        draw_text_lines(draw, (MARGIN + 62, y + 30), item["text"], font(14), ink, WIDTH - 2 * MARGIN - 62, spacing=5, max_lines=2)
        y += 94

    axes_y = 752
    draw.text((MARGIN, axes_y), "四维工作人格", font=font(17, True), fill=accent)
    y = axes_y + 50
    bar_x = 230
    bar_width = 380
    for axis in report["axes"]:
        draw.text((MARGIN, y), axis["letter"], font=font(29, True), fill=accent)
        draw.text((MARGIN + 42, y + 7), axis["label"], font=font(15), fill=ink)
        draw.rounded_rectangle((bar_x, y + 13, bar_x + bar_width, y + 25), radius=6, fill="#E5E0D4")
        draw.rounded_rectangle((bar_x, y + 13, bar_x + round(bar_width * axis["score"] / 100), y + 25), radius=6, fill=accent)
        draw.text((bar_x + bar_width + 18, y - 1), str(axis["score"]), font=font(25, True), fill=ink)
        draw.text((bar_x + bar_width + 62, y + 8), axis["confidence_copy"], font=font(12), fill=ink)
        y += 60

    footer_y = 1082
    draw.line((MARGIN, footer_y, WIDTH - MARGIN, footer_y), fill=accent, width=2)
    draw.text((MARGIN, footer_y + 25), report["campaign_tag"], font=font(17, True), fill=ink)
    draw.text((MARGIN, footer_y + 55), report["privacy_copy"], font=font(12), fill=ink)
    draw.multiline_text((WIDTH - MARGIN - 100, footer_y + 28), "MARVIS\nWORK CLONE", font=font(12, True), fill=accent, align="right")

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)
    print(json.dumps({"report_png": str(output_path), "width": WIDTH, "height": HEIGHT}, ensure_ascii=False))


if __name__ == "__main__":
    main()
