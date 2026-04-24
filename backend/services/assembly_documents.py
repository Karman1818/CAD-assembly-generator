from __future__ import annotations

import math
import os
import textwrap
from typing import Any, Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


SVG_NS = "http://www.w3.org/2000/svg"
OVERVIEW_SIZE = (1400, 900)
PAGE_SIZE = (1654, 2339)  # A4 at ~150 DPI
BACKGROUND = "#f5f1e8"
INK = "#1f2937"
MUTED = "#64748b"
PANEL_FILL = "#f4a261"
CONNECTOR_FILL = "#2a9d8f"
OTHER_FILL = "#8d99ae"
HIGHLIGHT = "#e76f51"


def _safe_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in name)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    preferred = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in preferred:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, width: int) -> List[str]:
    wrapped = textwrap.wrap(text, width=width)
    return wrapped or [text]


def _dimensions(part: Dict[str, Any]) -> Tuple[float, float, float]:
    dims = [float(value) for value in part.get("dimensions", [0, 0, 0])]
    while len(dims) < 3:
        dims.append(0.0)
    return dims[0], dims[1], dims[2]


def _part_kind(part: Dict[str, Any]) -> str:
    return str(part.get("type", "other"))


def _part_area_weight(part: Dict[str, Any]) -> float:
    x, y, z = sorted(_dimensions(part))
    thickness = max(x, 1.0)
    face = max(y * z, 1.0)
    if _part_kind(part) == "connector":
        return max(part.get("quantity", 1), 1) * 0.5
    return face / max(thickness, 1.0)


def _part_fill(kind: str, highlight: bool = False) -> str:
    if highlight:
        return HIGHLIGHT
    if kind == "panel":
        return PANEL_FILL
    if kind == "connector":
        return CONNECTOR_FILL
    return OTHER_FILL


def _panel_points(width: float, height: float, x: float, y: float) -> List[Tuple[float, float]]:
    skew = min(width * 0.14, 26.0)
    return [
        (x + skew, y),
        (x + width, y),
        (x + width - skew, y + height),
        (x, y + height),
    ]


def _connector_points(width: float, height: float, x: float, y: float) -> List[Tuple[float, float]]:
    radius = min(width, height) / 2.0
    cx = x + width / 2.0
    cy = y + height / 2.0
    points = []
    for idx in range(6):
        angle = math.pi / 3.0 * idx - math.pi / 6.0
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def _shape_points(part: Dict[str, Any], x: float, y: float, width: float, height: float) -> List[Tuple[float, float]]:
    if _part_kind(part) == "panel":
        return _panel_points(width, height, x, y)
    if _part_kind(part) == "connector":
        return _connector_points(width, height, x, y)
    return [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]


def _normalize_card_size(part: Dict[str, Any], max_width: float = 180.0, max_height: float = 120.0) -> Tuple[float, float]:
    dims = sorted(_dimensions(part))
    if _part_kind(part) == "connector":
        edge = max(44.0, min(90.0, 38.0 + math.log(max(part.get("quantity", 1), 1) + 1) * 18.0))
        return edge, edge

    width = max(dims[2], 20.0)
    height = max(dims[1], 20.0)
    scale = min(max_width / width, max_height / height)
    return max(width * scale, 50.0), max(height * scale, 34.0)


def _layout_cards(parts: Sequence[Dict[str, Any]], start_x: float, start_y: float, cols: int, gap_x: float, gap_y: float) -> List[Dict[str, Any]]:
    placements: List[Dict[str, Any]] = []
    col = 0
    row = 0
    for part in parts:
        width, height = _normalize_card_size(part)
        x = start_x + col * gap_x
        y = start_y + row * gap_y
        placements.append({"part": part, "x": x, "y": y, "w": width, "h": height})
        col += 1
        if col >= cols:
            col = 0
            row += 1
    return placements


def _svg_polygon(points: Sequence[Tuple[float, float]], fill: str, opacity: float, stroke: str = INK, stroke_width: int = 3) -> str:
    pairs = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polygon points="{pairs}" fill="{fill}" fill-opacity="{opacity:.3f}" stroke="{stroke}" stroke-width="{stroke_width}" />'


def _svg_text(x: float, y: float, value: str, size: int, fill: str = INK, weight: int = 600, anchor: str = "start") -> str:
    safe = (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
        f'font-weight="{weight}" text-anchor="{anchor}" font-family="Arial, sans-serif">{safe}</text>'
    )


def _draw_shape(draw: ImageDraw.ImageDraw, part: Dict[str, Any], placement: Dict[str, Any], highlight: bool, opacity: float) -> None:
    points = _shape_points(part, placement["x"], placement["y"], placement["w"], placement["h"])
    fill = _part_fill(_part_kind(part), highlight)
    rgba = ImageColorHelper.hex_with_alpha(fill, opacity)
    outline = ImageColorHelper.hex_with_alpha(INK, opacity)
    draw.polygon(points, fill=rgba, outline=outline)


class ImageColorHelper:
    @staticmethod
    def hex_with_alpha(value: str, opacity: float) -> Tuple[int, int, int, int]:
        value = value.lstrip("#")
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        a = max(0, min(255, int(opacity * 255)))
        return (r, g, b, a)


def _render_cards_svg(placements: Sequence[Dict[str, Any]], highlight: bool, opacity: float) -> List[str]:
    fragments: List[str] = []
    for placement in placements:
        part = placement["part"]
        points = _shape_points(part, placement["x"], placement["y"], placement["w"], placement["h"])
        fragments.append(_svg_polygon(points, _part_fill(_part_kind(part), highlight), opacity))
        fragments.append(_svg_text(placement["x"], placement["y"] + placement["h"] + 24, str(part["id"]).upper(), 18))
        fragments.append(
            _svg_text(
                placement["x"],
                placement["y"] + placement["h"] + 48,
                f"x{part.get('quantity', 1)}  {part.get('label', part.get('type', 'part'))}",
                16,
                fill=MUTED,
                weight=500,
            )
        )
    return fragments


def _render_cards_png(
    draw: ImageDraw.ImageDraw,
    placements: Sequence[Dict[str, Any]],
    highlight: bool,
    opacity: float,
    image: Image.Image,
) -> None:
    for placement in placements:
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        _draw_shape(overlay_draw, placement["part"], placement, highlight, opacity)
        image.alpha_composite(overlay)

        draw.text(
            (placement["x"], placement["y"] + placement["h"] + 12),
            str(placement["part"]["id"]).upper(),
            fill=INK,
            font=_font(22, bold=True),
        )
        draw.text(
            (placement["x"], placement["y"] + placement["h"] + 42),
            f"x{placement['part'].get('quantity', 1)}  {placement['part'].get('label', placement['part'].get('type', 'part'))}",
            fill=MUTED,
            font=_font(18),
        )


def build_overview_assets(job_id: str, parts: Sequence[Dict[str, Any]], storage_dir: str) -> Dict[str, str]:
    parts_sorted = sorted(parts, key=_part_area_weight, reverse=True)
    placements = _layout_cards(parts_sorted, start_x=96, start_y=260, cols=4, gap_x=300, gap_y=220)

    svg_fragments = [
        f'<svg xmlns="{SVG_NS}" width="{OVERVIEW_SIZE[0]}" height="{OVERVIEW_SIZE[1]}" viewBox="0 0 {OVERVIEW_SIZE[0]} {OVERVIEW_SIZE[1]}">',
        f'<rect width="100%" height="100%" fill="{BACKGROUND}" />',
        '<rect x="40" y="40" width="1320" height="820" rx="36" fill="#fffaf3" stroke="#d6d3d1" stroke-width="3" />',
        _svg_text(86, 118, "Assembly Overview", 44),
        _svg_text(88, 162, "Generated visual reference for AI planning and PDF export", 22, fill=MUTED, weight=500),
        _svg_text(88, 215, f"Unique parts: {len(parts_sorted)}", 20, fill=MUTED, weight=500),
    ]
    svg_fragments.extend(_render_cards_svg(placements, highlight=False, opacity=0.92))
    svg_fragments.append("</svg>")

    overview_svg_name = f"{job_id}_overview.svg"
    overview_svg_path = os.path.join(storage_dir, overview_svg_name)
    with open(overview_svg_path, "w", encoding="utf-8") as file_obj:
        file_obj.write("\n".join(svg_fragments))

    image = Image.new("RGBA", OVERVIEW_SIZE, ImageColorHelper.hex_with_alpha(BACKGROUND, 1.0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((40, 40, 1360, 860), radius=36, fill="#fffaf3", outline="#d6d3d1", width=3)
    draw.text((86, 74), "Assembly Overview", fill=INK, font=_font(42, bold=True))
    draw.text((88, 128), "Generated visual reference for AI planning and PDF export", fill=MUTED, font=_font(22))
    draw.text((88, 176), f"Unique parts: {len(parts_sorted)}", fill=MUTED, font=_font(20))
    _render_cards_png(draw, placements, highlight=False, opacity=0.92, image=image)

    overview_png_name = f"{job_id}_overview.png"
    overview_png_path = os.path.join(storage_dir, overview_png_name)
    image.convert("RGB").save(overview_png_path)

    return {
        "overviewSvgUrl": f"/api/files/{overview_svg_name}",
        "overviewPngUrl": f"/api/files/{overview_png_name}",
        "overviewSvgPath": overview_svg_path,
        "overviewPngPath": overview_png_path,
    }


def enrich_step_visuals(job_id: str, instructions: Dict[str, Any], storage_dir: str) -> Dict[str, Any]:
    parts_map = {part["id"]: part for part in instructions.get("parts_list", [])}
    previously_added: List[str] = []

    for step in instructions.get("steps", []):
        context_parts = [parts_map[part_id] for part_id in previously_added if part_id in parts_map]
        new_parts = [parts_map[item["part_id"]] for item in step.get("parts_used", []) if item["part_id"] in parts_map]
        step["context_part_ids"] = list(previously_added)

        context_layout = _layout_cards(context_parts[:6], start_x=84, start_y=182, cols=3, gap_x=250, gap_y=180)
        new_layout = _layout_cards(new_parts[:6], start_x=84, start_y=500, cols=3, gap_x=340, gap_y=200)

        svg_name = f"{job_id}_step_{step['step_number']:02d}.svg"
        svg_path = os.path.join(storage_dir, svg_name)
        svg_fragments = [
            f'<svg xmlns="{SVG_NS}" width="{OVERVIEW_SIZE[0]}" height="{OVERVIEW_SIZE[1]}" viewBox="0 0 {OVERVIEW_SIZE[0]} {OVERVIEW_SIZE[1]}">',
            f'<rect width="100%" height="100%" fill="{BACKGROUND}" />',
            '<rect x="40" y="40" width="1320" height="820" rx="36" fill="#fffaf3" stroke="#d6d3d1" stroke-width="3" />',
            _svg_text(92, 112, f"Step {step['step_number']}: {step['title']}", 38),
            _svg_text(94, 154, step["description"], 20, fill=MUTED, weight=500),
            _svg_text(92, 214, "Existing context", 24, fill=MUTED, weight=700),
            '<line x1="92" y1="448" x2="1288" y2="448" stroke="#cbd5e1" stroke-width="3" stroke-dasharray="14 12" />',
            _svg_text(92, 486, "New parts in this step", 28, fill=HIGHLIGHT, weight=800),
        ]
        svg_fragments.extend(_render_cards_svg(context_layout, highlight=False, opacity=0.28))
        svg_fragments.extend(_render_cards_svg(new_layout, highlight=True, opacity=0.94))
        svg_fragments.append(_svg_text(1230, 486, f"Added: {len(new_parts)}", 20, fill=HIGHLIGHT, weight=700, anchor="end"))
        svg_fragments.append("</svg>")

        with open(svg_path, "w", encoding="utf-8") as file_obj:
            file_obj.write("\n".join(svg_fragments))

        png_name = f"{job_id}_step_{step['step_number']:02d}.png"
        png_path = os.path.join(storage_dir, png_name)
        image = Image.new("RGBA", OVERVIEW_SIZE, ImageColorHelper.hex_with_alpha(BACKGROUND, 1.0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((40, 40, 1360, 860), radius=36, fill="#fffaf3", outline="#d6d3d1", width=3)
        draw.text((92, 76), f"Step {step['step_number']}: {step['title']}", fill=INK, font=_font(38, bold=True))

        desc_y = 132
        for line in _wrap_text(step["description"], 74)[:3]:
            draw.text((94, desc_y), line, fill=MUTED, font=_font(20))
            desc_y += 28

        draw.text((92, 194), "Existing context", fill=MUTED, font=_font(24, bold=True))
        draw.line((92, 448, 1288, 448), fill="#cbd5e1", width=3)
        draw.text((92, 470), "New parts in this step", fill=HIGHLIGHT, font=_font(28, bold=True))
        draw.text((1160, 470), f"Added: {len(new_parts)}", fill=HIGHLIGHT, font=_font(20, bold=True))
        _render_cards_png(draw, context_layout, highlight=False, opacity=0.28, image=image)
        _render_cards_png(draw, new_layout, highlight=True, opacity=0.94, image=image)
        image.convert("RGB").save(png_path)

        step["sceneSvgUrl"] = f"/api/files/{svg_name}"
        step["scenePngUrl"] = f"/api/files/{png_name}"
        step["sceneSvgPath"] = svg_path
        step["scenePngPath"] = png_path

        for item in step.get("parts_used", []):
            if item["part_id"] not in previously_added:
                previously_added.append(item["part_id"])

    return instructions


def export_instructions_pdf(job_id: str, instructions: Dict[str, Any], storage_dir: str) -> str:
    pages: List[Image.Image] = []
    title = instructions.get("title", "Assembly Instructions")

    cover = Image.new("RGB", PAGE_SIZE, "#fffaf3")
    draw = ImageDraw.Draw(cover)
    draw.rectangle((80, 80, PAGE_SIZE[0] - 80, PAGE_SIZE[1] - 80), outline="#d6d3d1", width=4)
    draw.text((140, 180), title, fill=INK, font=_font(62, bold=True))
    draw.text((144, 278), "Technical Schools CAD Assembly Generator", fill=MUTED, font=_font(30))
    draw.text((144, 340), f"Generated steps: {len(instructions.get('steps', []))}", fill=MUTED, font=_font(24))

    overview_path = instructions.get("overviewPngPath")
    if overview_path and os.path.exists(overview_path):
        preview = Image.open(overview_path).convert("RGB")
        preview.thumbnail((PAGE_SIZE[0] - 260, 900))
        px = (PAGE_SIZE[0] - preview.width) // 2
        py = 520
        cover.paste(preview, (px, py))

    footer = "This PDF was generated automatically from extracted CAD parts and assembly planning."
    draw.text((144, PAGE_SIZE[1] - 220), footer, fill=MUTED, font=_font(22))
    pages.append(cover)

    bom = Image.new("RGB", PAGE_SIZE, "#ffffff")
    draw = ImageDraw.Draw(bom)
    draw.text((120, 120), "Bill Of Materials", fill=INK, font=_font(50, bold=True))
    draw.text((122, 190), "Grouped parts extracted from the STEP file", fill=MUTED, font=_font(24))
    y = 280
    for idx, part in enumerate(instructions.get("parts_list", []), start=1):
        if y > PAGE_SIZE[1] - 160:
            pages.append(bom)
            bom = Image.new("RGB", PAGE_SIZE, "#ffffff")
            draw = ImageDraw.Draw(bom)
            draw.text((120, 120), "Bill Of Materials (cont.)", fill=INK, font=_font(44, bold=True))
            y = 230

        dims = " x ".join(f"{value:.1f}" for value in _dimensions(part))
        line = f"{idx:02d}. {part['id']}  |  {part.get('label', part.get('type', 'part'))}  |  qty {part.get('quantity', 1)}  |  {dims} mm"
        draw.rounded_rectangle((110, y - 20, PAGE_SIZE[0] - 110, y + 70), radius=18, fill="#f8fafc", outline="#e2e8f0")
        draw.text((140, y), line, fill=INK, font=_font(24))
        y += 110
    pages.append(bom)

    for step in instructions.get("steps", []):
        page = Image.new("RGB", PAGE_SIZE, "#ffffff")
        draw = ImageDraw.Draw(page)
        draw.text((120, 120), f"Step {step['step_number']}", fill=HIGHLIGHT, font=_font(32, bold=True))
        draw.text((120, 176), step["title"], fill=INK, font=_font(48, bold=True))

        text_y = 252
        for line in _wrap_text(step["description"], 80):
            draw.text((124, text_y), line, fill=MUTED, font=_font(24))
            text_y += 34

        scene_path = step.get("scenePngPath")
        if scene_path and os.path.exists(scene_path):
            scene = Image.open(scene_path).convert("RGB")
            scene.thumbnail((PAGE_SIZE[0] - 220, 1150))
            sx = (PAGE_SIZE[0] - scene.width) // 2
            sy = 420
            page.paste(scene, (sx, sy))

        parts_caption = ", ".join(
            f"{item['part_id']} x{item.get('quantity_in_step', 1)}"
            for item in step.get("parts_used", [])
        ) or "No explicit parts listed"
        draw.text((120, PAGE_SIZE[1] - 220), f"Parts added: {parts_caption}", fill=INK, font=_font(22, bold=True))
        pages.append(page)

    pdf_name = f"{job_id}_instructions.pdf"
    pdf_path = os.path.join(storage_dir, pdf_name)
    pages[0].save(pdf_path, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    return pdf_path
