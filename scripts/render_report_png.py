#!/usr/bin/env python3
"""Render report.json into the campaign's fixed 900x1200 PNG poster."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError as exc:
    raise SystemExit("Pillow is required to render report.png. Install pillow in the Marvis runtime.") from exc


WIDTH, HEIGHT = 900, 1200
MARGIN = 64


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--personality-image", help="Defaults to the matching source illustration bundled with the Skill.")
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


def rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def blend(color_a: str | tuple[int, int, int], color_b: str | tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    left = rgb(color_a) if isinstance(color_a, str) else color_a
    right = rgb(color_b) if isinstance(color_b, str) else color_b
    return tuple(round(left[index] * (1 - amount) + right[index] * amount) for index in range(3))


def wrap(draw: ImageDraw.ImageDraw, text: str, selected_font, max_width: int) -> list[str]:
    lines: list[str] = []
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


def draw_lines(draw, xy, text, selected_font, fill, max_width, line_height, max_lines=2):
    x, y = xy
    lines = wrap(draw, text, selected_font, max_width)[:max_lines]
    if len(wrap(draw, text, selected_font, max_width)) > max_lines and lines:
        lines[-1] = lines[-1][:-1] + "…"
    for line in lines:
        draw.text((x, y), line, font=selected_font, fill=fill)
        y += line_height
    return y


def mascot_cutout(path: Path, background: tuple[int, int, int]) -> Image.Image:
    source = Image.open(path).convert("RGB")
    # The source files include a bottom type caption. The poster already carries that title.
    source = source.crop((0, 0, source.width, round(source.height * 0.855)))
    source.thumbnail((330, 330), Image.Resampling.LANCZOS)
    rgba = source.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, _ = pixels[x, y]
            minimum, maximum = min(red, green, blue), max(red, green, blue)
            if minimum > 247 and maximum - minimum < 10:
                pixels[x, y] = (*background, 0)
            elif minimum > 232 and maximum - minimum < 14:
                alpha = round((247 - minimum) / 15 * 210)
                pixels[x, y] = (red, green, blue, max(0, min(210, alpha)))
    return rgba


def confidence_label(value: str) -> str:
    return {"high": "高置信", "medium": "中置信", "low": "低置信"}.get(value, "低置信")


def main():
    args = parse_args()
    report_path = Path(args.report).expanduser().resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    image_path = (
        Path(args.personality_image).expanduser().resolve()
        if args.personality_image
        else Path(__file__).resolve().parent.parent / "assets" / "personalities" / Path(report["personality_image"]).name
    )
    if not image_path.exists():
        raise SystemExit(f"Personality image not found: {image_path}")

    background = rgb(report["colors"]["bg"])
    accent = rgb(report["colors"]["accent"])
    ink = rgb(report["colors"]["text"])
    pale_accent = blend(accent, background, 0.78)
    hairline = blend(accent, background, 0.84)
    card_fill = blend(accent, background, 0.9)
    track_fill = blend(accent, background, 0.8)

    canvas = Image.new("RGB", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(canvas)

    # Oversized type watermark anchors the first viewport without competing with the title.
    watermark_layer = Image.new("RGBA", (WIDTH, 235), (0, 0, 0, 0))
    watermark_draw = ImageDraw.Draw(watermark_layer)
    watermark_draw.text((465, 70), report["type"], font=font(145, True), fill=(*accent, 24))
    canvas.paste(watermark_layer, (0, 0), watermark_layer)
    draw = ImageDraw.Draw(canvas)

    draw.text((MARGIN, 48), "你的 Marvis 工作版 MBTI", font=font(19, True), fill=accent)
    draw.text((MARGIN, 132), report["type"], font=font(51), fill=blend(accent, background, 0.42))
    draw.text((198, 128), report["name"], font=font(52, True), fill=ink)

    draw.rectangle((MARGIN, 253, MARGIN + 6, 301), fill=accent)
    draw_lines(draw, (MARGIN + 26, 252), report["tagline"], font(25, True), ink, WIDTH - 2 * MARGIN - 26, 36, max_lines=2)

    draw.text((MARGIN, 351), "三条铁证 · 你的电脑说的", font=font(15, True), fill=blend(accent, background, 0.2))
    evidence_y = 399
    evidence_width = 455
    for item in report["evidence"]:
        draw.ellipse((MARGIN + 2, evidence_y + 8, MARGIN + 12, evidence_y + 18), fill=blend(accent, background, 0.2))
        sentence = f"{item['title']}：{item['text']}"
        draw_lines(draw, (MARGIN + 27, evidence_y), sentence, font(18), ink, evidence_width - 27, 28, max_lines=2)
        draw.line((MARGIN + 27, evidence_y + 64, MARGIN + evidence_width, evidence_y + 64), fill=hairline, width=1)
        evidence_y += 78

    mascot = mascot_cutout(image_path, background)
    mascot_x = WIDTH - MARGIN - mascot.width
    mascot_y = 358
    canvas.paste(mascot, (mascot_x, mascot_y), mascot)
    draw = ImageDraw.Draw(canvas)

    axes_y = 657
    draw.text((MARGIN, axes_y), "四维结果", font=font(16, True), fill=blend(accent, background, 0.18))
    y = axes_y + 38
    badge_size = 44
    bar_x = 279
    bar_width = 452
    for axis in report["axes"]:
        draw.rounded_rectangle((MARGIN, y, MARGIN + badge_size, y + badge_size), radius=8, fill=accent)
        badge_box = draw.textbbox((0, 0), axis["letter"], font=font(24, True))
        draw.text((MARGIN + (badge_size - (badge_box[2] - badge_box[0])) / 2, y + 6), axis["letter"], font=font(24, True), fill=background)
        draw.text((MARGIN + 60, y + 9), axis["label"], font=font(17), fill=ink)
        track_y = y + 16
        draw.rounded_rectangle((bar_x, track_y, bar_x + bar_width, track_y + 14), radius=7, fill=track_fill)
        fill_width = max(14, round(bar_width * axis["score"] / 100))
        draw.rounded_rectangle((bar_x, track_y, bar_x + fill_width, track_y + 14), radius=7, fill=accent)
        draw.text((748, y + 3), str(axis["score"]), font=font(25, True), fill=ink)
        draw.text((798, y + 13), confidence_label(axis["confidence"]), font=font(11), fill=blend(ink, background, 0.36))
        y += 59

    stats_y = 954
    card_gap = 12
    card_width = (WIDTH - 2 * MARGIN - card_gap * 3) // 4
    for index, stat in enumerate(report.get("stats", [])):
        x = MARGIN + index * (card_width + card_gap)
        draw.rounded_rectangle((x, stats_y, x + card_width, stats_y + 88), radius=8, fill=card_fill)
        draw.text((x + 16, stats_y + 13), stat["value"], font=font(28, True), fill=ink)
        draw.text((x + 16, stats_y + 54), stat["label"], font=font(12), fill=blend(ink, background, 0.34))

    footer_y = 1110
    draw.line((MARGIN, footer_y, WIDTH - MARGIN, footer_y), fill=hairline, width=1)
    draw.ellipse((MARGIN, footer_y + 29, MARGIN + 40, footer_y + 69), fill=blend(accent, background, 0.76))
    draw.ellipse((MARGIN + 13, footer_y + 38, MARGIN + 27, footer_y + 52), fill=accent)
    draw.rounded_rectangle((MARGIN + 9, footer_y + 51, MARGIN + 31, footer_y + 62), radius=5, fill=accent)
    draw.text((MARGIN + 53, footer_y + 27), "Marvis 本地知识库", font=font(13, True), fill=ink)
    draw.text((MARGIN + 53, footer_y + 49), report["privacy_copy"], font=font(11), fill=blend(ink, background, 0.28))
    tag_box = (WIDTH - MARGIN - 208, footer_y + 28, WIDTH - MARGIN, footer_y + 68)
    draw.rounded_rectangle(tag_box, radius=8, fill=card_fill)
    draw.text((tag_box[0] + 15, tag_box[1] + 10), report["campaign_tag"], font=font(12, True), fill=accent)

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)
    print(json.dumps({"report_png": str(output_path), "width": WIDTH, "height": HEIGHT}, ensure_ascii=False))


if __name__ == "__main__":
    main()
