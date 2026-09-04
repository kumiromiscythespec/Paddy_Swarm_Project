"""Render the coupon review sheet with Pillow and direct STL projection."""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


LANE = Path(__file__).resolve().parents[1]
STL_DIR = LANE / "stl"
REPORT = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
OUTPUT = LANE / "docs" / "BH_V007_neck_collar_coupon_visual_review.png"
FILES = {
    "N-A": "BH_V007_NA_neck_collar_coupon_ID26p2_G18_T4p0_H9_PETG.stl",
    "N-B": "BH_V007_NB_neck_collar_coupon_ID26p2_G20_T4p0_H9_PETG.stl",
    "N-C": "BH_V007_NC_neck_collar_coupon_ID26p2_G20_T3p5_H9_PETG.stl",
}
COLORS = {"N-A": (245, 158, 11), "N-B": (37, 99, 235), "N-C": (16, 185, 129)}
FONT_REGULAR = Path("C:/Windows/Fonts/segoeui.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/seguisb.ttf")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def load_binary_stl(path: Path) -> list[tuple[tuple[float, float, float], list[tuple[float, float, float]]]]:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    triangles = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        normal = tuple(values[0:3])
        vertices = [tuple(values[index:index + 3]) for index in (3, 6, 9)]
        triangles.append((normal, vertices))
        offset += 50
    return triangles


def project(vertex: tuple[float, float, float], view: str) -> tuple[float, float, float]:
    x, y, z = vertex
    if view == "side":
        return y, -z, x
    return 0.866 * (x - y), -(0.5 * (x + y) + 1.12 * z), x + y + 0.25 * z


def shade(base: tuple[int, int, int], normal: tuple[float, float, float], view: str) -> tuple[int, int, int]:
    nx, ny, nz = normal
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    light = abs(nx) / length if view == "side" else abs(0.45 * nx + 0.45 * ny + 0.77 * nz) / length
    factor = 0.58 + 0.42 * light
    return tuple(min(255, round(value * factor + 18)) for value in base)


def draw_mesh(draw, box, triangles, base_color, view: str = "iso") -> None:
    x0, y0, x1, y1 = box
    projected = []
    all_points = []
    for normal, vertices in triangles:
        points = [project(vertex, view) for vertex in vertices]
        projected.append((sum(point[2] for point in points) / 3.0, normal, points))
        all_points.extend(points)
    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)
    scale = min((x1 - x0 - 36) / (max_x - min_x), (y1 - y0 - 36) / (max_y - min_y))
    offset_x = (x0 + x1) / 2.0 - (min_x + max_x) * scale / 2.0
    offset_y = (y0 + y1) / 2.0 - (min_y + max_y) * scale / 2.0
    for _, normal, points in sorted(projected, key=lambda item: item[0]):
        polygon = [(offset_x + point[0] * scale, offset_y + point[1] * scale) for point in points]
        draw.polygon(polygon, fill=shade(base_color, normal, view), outline=(30, 41, 59))


def centered_text(draw, xy, text, text_font, fill=(15, 23, 42)) -> None:
    x, y = xy
    bbox = draw.textbbox((0, 0), text, font=text_font)
    draw.text((x - (bbox[2] - bbox[0]) / 2, y), text, font=text_font, fill=fill)


def main() -> None:
    image = Image.new("RGB", (1800, 1100), (248, 250, 252))
    draw = ImageDraw.Draw(image)
    meshes = {name: load_binary_stl(STL_DIR / filename) for name, filename in FILES.items()}
    comparison = REPORT["comparison_existing_v007_to_candidates"]
    openings = comparison["opening_clear_mm"]
    deflection = comparison["theoretical_opening_deflection"]

    centered_text(draw, (900, 24), "BH_V007 Neck Collar Reinforcement Coupon Study", font(34, True))
    subtitles = {
        "N-A": "G18 / T4.0 / H9",
        "N-B": "G20 / T4.0 / H9  •  FIRST PRINT",
        "N-C": "G20 / T3.5 / H9",
    }
    panel_boxes = {"N-A": (35, 115, 575, 585), "N-B": (630, 115, 1170, 585), "N-C": (1225, 115, 1765, 585)}
    for name, box in panel_boxes.items():
        draw.rounded_rectangle(box, radius=18, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
        centered_text(draw, ((box[0] + box[2]) // 2, box[1] + 14), name, font(27, True))
        centered_text(draw, ((box[0] + box[2]) // 2, box[1] + 52), subtitles[name], font(18))
        draw_mesh(draw, (box[0] + 10, box[1] + 88, box[2] - 10, box[3] - 12), meshes[name], COLORS[name])

    side_box = (35, 630, 575, 1010)
    draw.rounded_rectangle(side_box, radius=18, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    centered_text(draw, (305, 646), "N-B side view", font(23, True))
    centered_text(draw, (305, 679), "R8 saddle + two 4 × 14 gussets", font(16))
    draw_mesh(draw, (55, 715, 555, 995), meshes["N-B"], COLORS["N-B"], "side")

    chart_box = (630, 630, 1170, 1010)
    draw.rounded_rectangle(chart_box, radius=18, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    centered_text(draw, (900, 648), "Opening / expansion to phi26.2", font(21, True))
    keys = ["existing_V007", "N-A", "N-B", "N-C"]
    labels = ["Old", "N-A", "N-B", "N-C"]
    colors = [(100, 116, 139), COLORS["N-A"], COLORS["N-B"], COLORS["N-C"]]
    baseline = 945
    chart_top = 715
    max_value = 26.2
    for index, key in enumerate(keys):
        cx = 690 + index * 123
        opening = openings[key]
        expansion = deflection[key]["total_required_gap_expansion_mm"]
        open_h = (baseline - chart_top) * opening / max_value
        exp_h = (baseline - chart_top) * expansion / max_value
        draw.rectangle((cx, baseline - open_h, cx + 38, baseline), fill=colors[index])
        draw.rectangle((cx + 43, baseline - exp_h, cx + 81, baseline), fill=(203, 213, 225))
        centered_text(draw, (cx + 40, 954), labels[index], font(15, True))
        centered_text(draw, (cx + 18, baseline - open_h - 24), f"{opening:.1f}", font(13))
        centered_text(draw, (cx + 62, baseline - exp_h - 24), f"{expansion:.1f}", font(13))
    draw.line((670, baseline, 1140, baseline), fill=(71, 85, 105), width=2)
    draw.rectangle((676, 692, 694, 710), fill=(37, 99, 235))
    draw.text((702, 689), "finished gap", font=font(13), fill=(51, 65, 85))
    draw.rectangle((814, 692, 832, 710), fill=(203, 213, 225))
    draw.text((840, 689), "required expansion", font=font(13), fill=(51, 65, 85))

    table_box = (1225, 630, 1765, 1010)
    draw.rounded_rectangle(table_box, radius=18, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    centered_text(draw, (1495, 648), "B-rep comparison", font(22, True))
    rows = [
        ("Finished gap", "18.000", "20.001", "20.001"),
        ("Ring thickness", "4.0", "4.0", "3.5"),
        ("Root section", "134.0", "134.0", "134.0"),
        ("vs old root", "+36.81%", "+36.81%", "+36.81%"),
        ("Tip travel each", "4.100", "3.100", "3.100"),
        ("Physical", "PENDING", "PENDING", "PENDING"),
    ]
    col_x = [1248, 1442, 1544, 1646, 1746]
    top = 705
    row_h = 43
    headers = ["metric", "N-A", "N-B", "N-C"]
    for idx, header in enumerate(headers):
        left, right = col_x[idx], col_x[idx + 1]
        draw.rectangle((left, top, right, top + row_h), fill=(226, 232, 240), outline=(203, 213, 225))
        centered_text(draw, ((left + right) // 2, top + 10), header, font(14, True))
    for row_index, row in enumerate(rows, start=1):
        y = top + row_h * row_index
        for col_index, value in enumerate(row):
            left, right = col_x[col_index], col_x[col_index + 1]
            fill = (248, 250, 252) if row_index % 2 else (255, 255, 255)
            draw.rectangle((left, y, right, y + row_h), fill=fill, outline=(226, 232, 240))
            centered_text(draw, ((left + right) // 2, y + 11), value, font(13, col_index == 0))

    centered_text(
        draw,
        (900, 1048),
        "CAD 27 PASS / 0 FAIL  •  Old V007 root physical FAIL retained  •  6 physical states PENDING  •  Production collar unchanged",
        font(17),
        (51, 65, 85),
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
