from __future__ import annotations

from html import escape
from typing import Callable

from concept_geometry import (
    ConceptBox,
    authority_component_boxes,
    side_rect,
    top_rect,
)


WIDTH = 1200
HEIGHT = 820


def _text(
    x: float,
    y: float,
    value: str,
    css_class: str = "label",
    *,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x:g}" y="{y:g}" class="{css_class}" '
        f'text-anchor="{anchor}">{escape(value)}</text>'
    )


def _rect(
    x: float,
    y: float,
    width: float,
    height: float,
    css_class: str,
    label: str | None = None,
    *,
    rx: float = 4,
) -> str:
    body = (
        f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
        f'rx="{rx:g}" class="{css_class}"/>'
    )
    if label is not None:
        body += _text(
            x + width / 2,
            y + height / 2 + 5,
            label,
            "part-label",
            anchor="middle",
        )
    return body


def _line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    css_class: str = "line",
    *,
    marker: str | None = None,
) -> str:
    marker_attr = (
        f' marker-end="url(#{marker})"' if marker is not None else ""
    )
    return (
        f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
        f'class="{css_class}"{marker_attr}/>'
    )


def _poly(points: str, css_class: str) -> str:
    return f'<polygon points="{points}" class="{css_class}"/>'


def _common_legend() -> str:
    entries = (
        ("aluminum", "ALUMINUM STRUCTURAL MEMBER"),
        ("printed", "PRINTED — POSITIONING / SACRIFICIAL"),
        ("metal", "METAL FASTENER / SUPPORT / PIN"),
        ("float", "FLOAT MODULE — SCHEMATIC"),
        ("secondary", "SECONDARY LATCH ONLY"),
        ("hold", "HOLD / UNRESOLVED"),
    )
    items = []
    for index, (css_class, label) in enumerate(entries):
        y = 630 + index * 27
        items.append(_rect(870, y - 15, 24, 18, css_class, rx=1))
        items.append(_text(906, y, label, "legend"))
    return "".join(items)


def _document(title: str, subtitle: str, body: str) -> bytes:
    content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title>
<desc id="desc">{escape(subtitle)} Color is paired with labels, outlines, and line styles.</desc>
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" class="arrow-fill"/></marker>
  <marker id="load-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" class="load-fill"/></marker>
  <pattern id="printed-hatch" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M0,8 L8,0" class="hatch"/></pattern>
</defs>
<style>
  text {{ font-family: "Segoe UI", Arial, sans-serif; fill: #172033; }}
  .title {{ font-size: 25px; font-weight: 700; }}
  .subtitle {{ font-size: 13px; fill: #475569; }}
  .label {{ font-size: 14px; }}
  .small {{ font-size: 11px; }}
  .part-label {{ font-size: 12px; font-weight: 700; }}
  .legend {{ font-size: 11px; font-weight: 600; }}
  .step {{ font-size: 12px; font-weight: 600; }}
  .aluminum {{ fill: #c7d8ef; stroke: #1f4c7c; stroke-width: 2.5; }}
  .printed {{ fill: url(#printed-hatch), #f8dcaa; stroke: #955b00; stroke-width: 2.5; }}
  .metal {{ fill: #d8dee8; stroke: #263545; stroke-width: 3; }}
  .cbox {{ fill: #ffe0ad; stroke: #92400e; stroke-width: 2.5; }}
  .bbox {{ fill: #c8ead3; stroke: #17613a; stroke-width: 2.5; }}
  .battery {{ fill: #e2d3f4; stroke: #603b8e; stroke-width: 2.5; }}
  .float {{ fill: #cdeef3; stroke: #0f6674; stroke-width: 2.5; }}
  .secondary {{ fill: #fce7f3; stroke: #9d174d; stroke-width: 2.5; stroke-dasharray: 7 4; }}
  .hold {{ fill: #fff4d6; stroke: #a16207; stroke-width: 2.5; stroke-dasharray: 8 5; }}
  .line {{ stroke: #334155; stroke-width: 2; fill: none; }}
  .assembly-arrow {{ stroke: #174ea6; stroke-width: 3; fill: none; }}
  .removal-arrow {{ stroke: #7c2d12; stroke-width: 3; stroke-dasharray: 7 4; fill: none; }}
  .load-path {{ stroke: #9f1239; stroke-width: 4; fill: none; }}
  .centerline {{ stroke: #64748b; stroke-width: 1.5; stroke-dasharray: 10 5 2 5; }}
  .forbidden {{ stroke: #b91c1c; stroke-width: 7; fill: none; }}
  .arrow-fill {{ fill: #174ea6; }}
  .load-fill {{ fill: #9f1239; }}
  .hatch {{ stroke: #955b00; stroke-width: 1; }}
  .panel {{ fill: #f8fafc; stroke: #cbd5e1; stroke-width: 1.5; }}
  .verify {{ fill: #e7f8ec; stroke: #18733c; stroke-width: 2.5; }}
  .warning {{ fill: #fff1f2; stroke: #be123c; stroke-width: 2; }}
</style>
{_text(45, 42, title, "title")}
{_text(45, 67, subtitle, "subtitle")}
{body}
{_common_legend()}
{_text(45, 785, "FRONT (-Y)  |  REAR (+Y)  |  LEFT (+X)  |  RIGHT (-X)  |  TOP (+Z)  |  BOTTOM (-Z)", "legend")}
{_text(600, 812, "NOT MANUFACTURING APPROVED", "title", anchor="middle")}
</svg>
"""
    return content.replace("\r\n", "\n").encode("utf-8")


def render_exploded(manifest: dict, *_args) -> bytes:
    body = [
        _line(425, 595, 425, 100, "centerline"),
        _rect(280, 545, 290, 28, "aluminum", "FPB ALUMINUM T-SLOT FRAME"),
        _rect(310, 486, 60, 24, "printed", "A1"),
        _rect(480, 486, 60, 24, "printed", "A2"),
        _rect(286, 421, 278, 42, "metal", "METAL LOWER-FRAME CRADLE — CONCEPT HOLD"),
        _rect(320, 335, 210, 64, "cbox", "CBOX 130×140×105"),
        _rect(305, 244, 240, 68, "bbox", "BBOX 150×220×150"),
        _rect(340, 165, 170, 52, "battery", "BATTERY CASSETTE"),
        _rect(75, 420, 135, 68, "float", "LEFT FLOAT"),
        _rect(640, 420, 135, 68, "float", "RIGHT FLOAT"),
        _rect(214, 439, 52, 28, "printed", "F1 SLIDE"),
        _rect(584, 439, 52, 28, "printed", "F2 SLIDE"),
        _line(425, 535, 425, 510, "assembly-arrow", marker="arrow"),
        _line(425, 476, 425, 464, "assembly-arrow", marker="arrow"),
        _line(425, 420, 425, 401, "assembly-arrow", marker="arrow"),
        _line(425, 334, 425, 313, "assembly-arrow", marker="arrow"),
        _line(425, 243, 425, 218, "assembly-arrow", marker="arrow"),
        _line(210, 455, 282, 455, "assembly-arrow", marker="arrow"),
        _line(640, 455, 568, 455, "assembly-arrow", marker="arrow"),
        _line(540, 356, 605, 356, "removal-arrow", marker="arrow"),
        _text(610, 352, "REMOVAL +Z after metal lock release", "small"),
        _rect(244, 438, 13, 30, "metal", "PIN", rx=1),
        _rect(593, 438, 13, 30, "metal", "PIN", rx=1),
        _text(75, 518, "AI-05 → AI-06 → AI-07", "part-label"),
        _text(590, 518, "AI-05 → AI-06 → AI-07", "part-label"),
        _text(585, 238, "AI-03 independent rear support", "label"),
        _text(585, 261, "BBOX IS NOT CANTILEVERED FROM CBOX", "small"),
        _text(585, 335, "AI-02 CBOX saddle + visible metal clamp", "label"),
        _rect(50, 90, 190, 72, "warning", "PRIMARY STRUCTURAL"),
        _text(60, 180, "Printed parts position and wear.", "small"),
        _text(60, 197, "Metal parts close the load path.", "small"),
    ]
    return _document(
        "Exploded Assembly Isometric — interface concept",
        "Exploded schematic separates structural metal, positioning prints, removable pins, and secondary-only latches.",
        "".join(body),
    )


def render_sequence(
    manifest: dict, load_paths: list[dict], steps: list[dict]
) -> bytes:
    body: list[str] = []
    for index, step in enumerate(steps):
        column = index % 3
        row = index // 3
        x = 45 + column * 270
        y = 100 + row * 122
        css_class = "verify" if step["step"] == 12 else "panel"
        body.append(_rect(x, y, 245, 92, css_class))
        body.append(
            _text(x + 12, y + 23, f"{step['step']}. {step['action']}", "step")
        )
        body.append(
            _text(
                x + 12,
                y + 44,
                " / ".join(step["interfaces"]),
                "small",
            )
        )
        body.append(_text(x + 12, y + 65, step["verify"], "small"))
        if index < len(steps) - 1:
            if column < 2:
                body.append(
                    _line(
                        x + 245,
                        y + 46,
                        x + 268,
                        y + 46,
                        "assembly-arrow",
                        marker="arrow",
                    )
                )
            else:
                body.append(
                    _line(
                        x + 122,
                        y + 92,
                        x + 122,
                        y + 118,
                        "assembly-arrow",
                        marker="arrow",
                    )
                )
    body.extend(
        [
            _rect(45, 600, 770, 118, "hold"),
            _text(60, 626, "DISASSEMBLY: reverse steps 12 → 1", "part-label"),
            _text(
                60,
                650,
                "Mud state: brush open channels; pull visible R-pin; use two-sided drift access.",
                "label",
            ),
            _text(
                60,
                674,
                "Release state must be visible before moving the next load-bearing module.",
                "label",
            ),
            _text(
                60,
                698,
                "Physical muddy-glove verification remains HOLD.",
                "part-label",
            ),
        ]
    )
    return _document(
        "Assembly Sequence — 12 steps maximum",
        "The sequence makes INSERT, SLIDE, LOCK, and VERIFY explicit and keeps disassembly human-accessible.",
        "".join(body),
    )


def _authority_box_map(
    context,
    projection: Callable,
    *,
    show_battery: bool = True,
) -> list[str]:
    parts: list[str] = []
    for box in authority_component_boxes(context):
        if not show_battery and box.component_id == "V22939-BATTERY-CASSETTE":
            continue
        x, y, width, height = projection(
            box.minimum_xyz_mm, box.maximum_xyz_mm
        )
        short = (
            box.component_id.replace("V22939-", "")
            .replace("FPB-FRONT-XMEMBER", "FRONT XMEMBER")
            .replace("FPB-RAIL-L", "LEFT RAIL")
            .replace("FPB-RAIL-R", "RIGHT RAIL")
            .replace("BATTERY-CASSETTE", "BATTERY")
        )
        parts.append(_rect(x, y, width, height, box.visual_class, short))
    return parts


def render_top(manifest: dict, load_paths: list[dict], steps: list[dict], context) -> bytes:
    body = _authority_box_map(context, top_rect)
    body.extend(
        [
            _rect(85, 224, 92, 240, "float", "LEFT FLOAT"),
            _rect(683, 224, 92, 240, "float", "RIGHT FLOAT"),
            _rect(185, 340, 45, 100, "printed", "F1"),
            _rect(630, 340, 45, 100, "printed", "F2"),
            _rect(300, 385, 40, 44, "printed", "A1"),
            _rect(520, 385, 40, 44, "printed", "A2"),
            _rect(325, 250, 38, 44, "printed", "B1"),
            _rect(497, 250, 38, 44, "printed", "B2"),
            _line(130, 355, 184, 355, "assembly-arrow", marker="arrow"),
            _line(730, 355, 676, 355, "assembly-arrow", marker="arrow"),
            _text(100, 337, "1 INSERT", "part-label"),
            _text(100, 485, "2 SLIDE +Y", "part-label"),
            _text(690, 337, "1 INSERT", "part-label"),
            _text(690, 485, "2 SLIDE +Y", "part-label"),
            _rect(215, 374, 12, 66, "metal", "PIN", rx=1),
            _rect(633, 374, 12, 66, "metal", "PIN", rx=1),
            _text(45, 105, "AI-01 metal corner brackets reserved at FRONT", "label"),
            _text(45, 125, "AI-02 CBOX saddle / AI-03 independent BBOX support", "label"),
            _text(45, 145, "AI-04 anti-separation aligns boxes; no BBOX vertical load", "label"),
            _rect(45, 540, 770, 62, "hold"),
            _text(
                60,
                565,
                "SLOT-ZONE AUDIT: no new rail anchors; BOTTOM_SLOT lower adapter only.",
                "part-label",
            ),
            _text(
                60,
                588,
                "Rail TOP remains reserved for motor/input/output/servo zones.",
                "label",
            ),
        ]
    )
    return _document(
        "Connection Map — Top",
        "Authority envelopes are dimensioned; floats, saddles, and rear bridge are explicitly schematic.",
        "".join(body),
    )


def render_side(manifest: dict, load_paths: list[dict], steps: list[dict], context) -> bytes:
    body = _authority_box_map(context, side_rect)
    body.extend(
        [
            _rect(170, 630, 590, 22, "metal", "LOWER-FRAME CRADLE — CONCEPT HOLD"),
            _rect(185, 597, 150, 22, "printed", "CBOX SADDLE A1/A2"),
            _rect(340, 597, 250, 22, "printed", "BBOX SADDLE B1/B2"),
            _rect(585, 575, 175, 28, "hold", "INDEPENDENT REAR BRIDGE"),
            _rect(50, 505, 110, 80, "float", "FLOAT"),
            _rect(155, 520, 62, 45, "printed", "SLIDE"),
            _rect(199, 513, 13, 60, "metal", "PIN", rx=1),
            _line(105, 545, 155, 545, "assembly-arrow", marker="arrow"),
            _line(195, 500, 195, 470, "removal-arrow", marker="arrow"),
            _text(55, 490, "1 INSERT / 2 SLIDE", "part-label"),
            _text(215, 490, "3 LOCK / 4 VERIFY", "part-label"),
            _line(340, 235, 340, 595, "load-path", marker="load-arrow"),
            _line(590, 180, 590, 573, "load-path", marker="load-arrow"),
            _text(350, 350, "CBOX LOAD → METAL CRADLE", "part-label"),
            _text(600, 330, "BBOX LOAD → INDEPENDENT BRIDGE", "part-label"),
            _rect(45, 675, 770, 55, "hold"),
            _text(
                60,
                698,
                "Rear bridge attachment, member section, stiffness, and implement clearance remain HOLD.",
                "part-label",
            ),
            _text(
                60,
                719,
                "No manufacturing geometry is inferred from this side schematic.",
                "label",
            ),
        ]
    )
    return _document(
        "Connection Map — Left Side",
        "Side view shows independent vertical load paths and upward module removal after visible lock release.",
        "".join(body),
    )


def render_load_paths(
    manifest: dict, load_paths: list[dict], steps: list[dict]
) -> bytes:
    body: list[str] = []
    for row_index, record in enumerate(load_paths):
        y = 105 + row_index * 125
        body.append(
            _text(45, y + 35, record["component"], "part-label")
        )
        nodes = record["nodes"]
        usable_width = 705
        node_width = min(130, usable_width / len(nodes) - 14)
        for index, node in enumerate(nodes):
            x = 145 + index * (node_width + 14)
            material = node["material"]
            css_class = (
                "printed"
                if "PRINTED" in material
                else (
                    "metal"
                    if "METAL" in material or "ALUMINUM" in material
                    else "panel"
                )
            )
            body.append(
                _rect(
                    x,
                    y,
                    node_width,
                    72,
                    css_class,
                )
            )
            body.append(
                _text(
                    x + node_width / 2,
                    y + 25,
                    node["name"],
                    "small",
                    anchor="middle",
                )
            )
            body.append(
                _text(
                    x + node_width / 2,
                    y + 48,
                    node["role"],
                    "small",
                    anchor="middle",
                )
            )
            if index < len(nodes) - 1:
                body.append(
                    _line(
                        x + node_width,
                        y + 36,
                        x + node_width + 13,
                        y + 36,
                        "load-path",
                        marker="load-arrow",
                    )
                )
        if "HOLD" in record["status"]:
            body.append(_text(145, y + 94, record["status"], "part-label"))
    body.extend(
        [
            _rect(45, 620, 770, 80, "warning"),
            _text(
                60,
                647,
                "ELECTRICAL CONNECTOR CARRIES ZERO STRUCTURAL LOAD",
                "part-label",
            ),
            _text(
                60,
                672,
                "Printed thumb latch is absent from every primary load path.",
                "label",
            ),
            _text(
                60,
                694,
                "BBOX path bypasses CBOX and terminates at an independent metal bridge.",
                "label",
            ),
        ]
    )
    return _document(
        "Structural Load Paths",
        "Each heavy component reaches metal primary structure; printed elements are named as positioning or sacrificial bearings.",
        "".join(body),
    )


def render_cbox(manifest: dict, *_args) -> bytes:
    body = [
        _rect(235, 160, 360, 230, "cbox", "CBOX — AUTHORITY ENVELOPE"),
        _poly("210,405 280,405 300,455 190,455", "printed"),
        _poly("550,405 620,405 660,455 530,455", "printed"),
        _text(245, 440, "A1 KEYED SADDLE", "part-label", anchor="middle"),
        _text(595, 440, "A2 KEYED SADDLE", "part-label", anchor="middle"),
        _rect(190, 475, 470, 44, "metal", "METAL LOWER-FRAME CRADLE"),
        _rect(198, 385, 28, 95, "metal", "CLAMP", rx=2),
        _rect(624, 385, 28, 95, "metal", "CLAMP", rx=2),
        _line(415, 125, 415, 155, "assembly-arrow", marker="arrow"),
        _line(690, 280, 690, 190, "removal-arrow", marker="arrow"),
        _text(390, 112, "ASSEMBLY -Z", "part-label"),
        _text(700, 230, "REMOVAL +Z", "part-label"),
        _line(415, 390, 415, 472, "load-path", marker="load-arrow"),
        _text(430, 430, "LOAD → SADDLE BEARING → METAL CRADLE", "label"),
        _rect(45, 565, 770, 112, "hold"),
        _text(60, 592, "PRIMARY STRUCTURAL: visible metal clamps + cradle", "part-label"),
        _text(60, 618, "POSITIONING ONLY: printed saddles, asymmetric FRONT/LEFT/RIGHT keys", "part-label"),
        _text(60, 644, "Mud/water: open bottom and lateral relief; no hidden fasteners", "label"),
        _text(60, 668, "Cradle section, authority attachment, clamp geometry, and torque remain HOLD.", "label"),
    ]
    return _document(
        "AI-02 — CBOX Saddle Interface",
        "The printed saddle positions the CBOX; metal clamps and cradle form the proposed primary path.",
        "".join(body),
    )


def render_bbox(manifest: dict, *_args) -> bytes:
    body = [
        _rect(250, 125, 350, 300, "bbox", "BBOX — AUTHORITY ENVELOPE"),
        _rect(300, 200, 250, 170, "battery", "BATTERY CASSETTE"),
        _poly("225,440 300,440 320,485 205,485", "printed"),
        _poly("550,440 625,440 670,485 530,485", "printed"),
        _rect(190, 505, 500, 48, "hold", "INDEPENDENT METAL REAR SUPPORT — HOLD"),
        _rect(210, 420, 28, 90, "metal", "CLAMP", rx=2),
        _rect(642, 420, 28, 90, "metal", "CLAMP", rx=2),
        _line(425, 425, 425, 503, "load-path", marker="load-arrow"),
        _text(450, 470, "BBOX LOAD BYPASSES CBOX", "part-label"),
        _rect(45, 600, 770, 98, "warning"),
        _text(60, 627, "AI-03 MANUFACTURING SHAPE = HOLD", "part-label"),
        _text(
            60,
            651,
            "Rear support hardpoints, section, stiffness, fasteners, and frame tie are not authoritative.",
            "label",
        ),
        _text(
            60,
            675,
            "This is a load-path contract only. BBOX may not cantilever from CBOX.",
            "label",
        ),
        _line(160, 240, 225, 240, "forbidden"),
        _line(160, 310, 225, 310, "forbidden"),
        _text(52, 278, "NO CBOX-ONLY SUPPORT", "part-label"),
    ]
    return _document(
        "AI-03 — BBOX Independent Support Interface",
        "Rear support is deliberately shown as unresolved concept geometry because authority does not define its hardpoints.",
        "".join(body),
    )


def render_float(manifest: dict, *_args) -> bytes:
    body = [
        _rect(55, 215, 190, 165, "float", "FLOAT MODULE"),
        _poly("230,255 370,255 410,295 370,335 230,335", "printed"),
        _text(315, 300, "SLIDE TONGUE", "part-label", anchor="middle"),
        _rect(450, 230, 220, 130, "printed", "LOWER ADAPTER + RECEIVER"),
        _rect(500, 365, 120, 42, "metal", "T-NUT + M5 CANDIDATE"),
        _rect(430, 425, 260, 54, "aluminum", "FPB RAIL BOTTOM_SLOT"),
        _line(245, 295, 444, 295, "assembly-arrow", marker="arrow"),
        _text(280, 275, "1 INSERT  →  2 SLIDE +Y", "part-label"),
        _rect(613, 215, 18, 170, "metal", "6 mm PIN", rx=2),
        _rect(627, 205, 35, 22, "metal", "R-PIN", rx=2),
        _text(665, 245, "3 LOCK", "part-label"),
        _rect(520, 250, 70, 30, "verify", "WINDOW"),
        _text(665, 275, "4 VERIFY", "part-label"),
        _line(668, 302, 725, 302, "removal-arrow", marker="arrow"),
        _text(730, 307, "REMOVE R-PIN, THEN MAIN PIN", "small"),
        _rect(45, 545, 770, 120, "hold"),
        _text(60, 572, "PRIMARY STRUCTURAL: metal pin → adapter → T-nut → BOTTOM_SLOT", "part-label"),
        _text(60, 598, "POSITIONING: keyed slide; pin bores align only at positive stop", "part-label"),
        _text(60, 624, "Mud/water: open-ended channel, downward drains, two-sided drift access", "label"),
        _text(60, 650, "Slide clearance and pin tolerance remain FIT TEST ONLY / HOLD.", "label"),
    ]
    return _document(
        "AI-05 / AI-06 / AI-07 — Float Slide and Pin",
        "The float sequence visibly separates insertion, sliding, primary metal locking, and verification.",
        "".join(body),
    )


def render_thumb(manifest: dict, *_args) -> bytes:
    body = [
        _rect(135, 145, 500, 55, "secondary", "LIGHTWEIGHT SERVICE COVER"),
        _poly("570,198 635,198 635,340 610,340 610,235 570,235", "secondary"),
        _text(655, 265, "PRINTED THUMB LATCH", "part-label"),
        _rect(135, 340, 500, 55, "panel", "RIGID COVER FLANGE / POSITIVE STOP"),
        _rect(520, 245, 65, 42, "verify", "VERIFY WINDOW"),
        _line(610, 120, 610, 190, "assembly-arrow", marker="arrow"),
        _text(635, 150, "PRESS -Z", "part-label"),
        _line(685, 330, 685, 245, "removal-arrow", marker="arrow"),
        _text(700, 290, "THUMB PRESS + LIFT", "part-label"),
        _rect(45, 465, 770, 165, "warning"),
        _text(60, 495, "SECONDARY LATCH ONLY — AI-08", "title"),
        _text(60, 530, "ALLOWED: lightweight cover, inspection lid, pin-loss cover", "label"),
        _text(60, 558, "FORBIDDEN: float, CBOX, BBOX, frame, motor, PTO primary fixing", "part-label"),
        _text(60, 586, "Failure may release only the lightweight cover.", "label"),
        _line(640, 500, 770, 600, "forbidden"),
        _line(770, 500, 640, 600, "forbidden"),
    ]
    return _document(
        "AI-08 — Thumb Latch Secondary-Only Interface",
        "The thumb latch is limited to a lightweight service cover and never appears in a heavy structural load path.",
        "".join(body),
    )


def render_all(
    manifest: dict,
    load_paths: list[dict],
    steps: list[dict],
    context,
) -> dict[str, bytes]:
    renderers = {
        "exploded_assembly_isometric.svg": render_exploded,
        "assembly_sequence.svg": render_sequence,
        "connection_map_top.svg": lambda m, p, s: render_top(
            m, p, s, context
        ),
        "connection_map_side.svg": lambda m, p, s: render_side(
            m, p, s, context
        ),
        "load_path_diagram.svg": render_load_paths,
        "cbox_saddle_interface.svg": render_cbox,
        "bbox_support_interface.svg": render_bbox,
        "float_slide_pin_interface.svg": render_float,
        "thumb_latch_secondary_only.svg": render_thumb,
    }
    return {
        name: renderer(manifest, load_paths, steps)
        for name, renderer in renderers.items()
    }
