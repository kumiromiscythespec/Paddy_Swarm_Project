#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paddy Swarm Common Rover v2.27.2 Retrofit Summer Float Shell G2
================================================================

A revised non-destructive add-on "turtle shell" kit for Paddy Swarm Common
Rover v2.27.

Why G2 exists
-------------
G1 proved that a simple 45-degree roof can be generated, but it looked more like
open roof panels than a turtle-shell/dome and the side-float concept was not
clear enough.  G2 changes the concept to:

- faceted 45-degree turtle-shell roof panels over BBOX/CBOX,
- optional rear cap for the CBOX/rear side,
- open PTO/front side with only a splash visor,
- separate side sponson floats that mount through adapters instead of wrapping
  directly around gearboxes,
- E-stop doghouse kept high and separate from water-prone flat top holes,
- one large part per plate_group where possible, for easier dense/plate control.

Critical policy
---------------
- v2.27 base rover continues as-is.  Do not stop current BBOX/CBOX printing.
- Do not drill into BBOX/CBOX for the first retrofit test.
- Keep shell and side floats away from DRC/DRIVE gearboxes and tire sweep.
- E-stop must remain visible and pushable with the shell installed.
- This is NOT a waterproof guarantee.  Use dummy weights for water tests first.

Expected commands
-----------------
python paddy_swarm_v2272_summer_float_shell_g2_cadquery.py --out rover_v2272_sfs_g2_out --make-zip
python paddy_swarm_v2272_summer_float_shell_g2_cadquery.py --metadata-only --out rover_v2272_sfs_g2_meta --make-zip
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import textwrap
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional, Tuple

VERSION = "v2.27.2-sfs-g2"
KIT_NAME = "Paddy Swarm Retrofit Summer Float Shell G2"

REF = {
    "target_base_rover": "Paddy Swarm Common Rover v2.27",
    "a1_nominal_plate_mm": [256, 256],
    "keepout_gearbox_clearance_mm": 10.0,
    "keepout_tire_sweep_clearance_mm": 12.0,
    "printed_box_body_reference_mm": [150.0, 200.0, 120.0],
    "printed_box_lid_reference_mm": [166.0, 216.0, 16.0],
}

ROOF = {
    "length": 236.0,
    "top_width": 92.0,
    "side_run": 42.0,
    "side_rise": 42.0,
    "skirt_height": 18.0,
    "panel_t": 3.2,
    "edge_t": 4.0,
    "rib_t": 4.0,
    "m3_clearance": 3.6,
}

FLOAT = {
    "length": 238.0,
    "width": 42.0,
    "height": 36.0,
    "chamfer": 12.0,
    "mount_tab_w": 12.0,
    "mount_tab_h": 18.0,
    "m3_clearance": 3.6,
}

DOGHOUSE = {
    "panel_w": 90.0,
    "panel_h": 66.0,
    "panel_t": 4.0,
    "estop_hole_d": 23.5,
    "angle_deg": 24.0,
    "base_w": 106.0,
    "base_l": 60.0,
    "base_t": 5.0,
    "hood_depth": 24.0,
    "hood_t": 4.0,
    "m3_clearance": 3.6,
}


@dataclass(frozen=True)
class PartSpec:
    part_id: str
    description: str
    material: str
    group: str
    qty: int
    plate_group: str
    filename_stl: str
    filename_step: str
    bbox_mm: Tuple[float, float, float]
    notes: str


PARTS = [
    PartSpec(
        "PS-RV2272-SFS-ROOF-F",
        "front/BBOX faceted 45-degree turtle shell roof; PTO side remains open",
        "PETG/PLA", "RIGID", 1, "SFS-G2-P01-ROOF-F",
        "PS-RV2272-SFS-ROOF-F.stl", "PS-RV2272-SFS-ROOF-F.step",
        (188.0, 236.0, 66.0),
        "Open at PTO/front. Use with optional front splash visor only; do not block PTO/E-stop access.",
    ),
    PartSpec(
        "PS-RV2272-SFS-ROOF-R",
        "rear/CBOX faceted 45-degree turtle shell roof; use with rear cap if clearance permits",
        "PETG/PLA", "RIGID", 1, "SFS-G2-P02-ROOF-R",
        "PS-RV2272-SFS-ROOF-R.stl", "PS-RV2272-SFS-ROOF-R.step",
        (188.0, 236.0, 66.0),
        "Rear side can be closed by REAR-CAP. Keep service access and drainage in mind.",
    ),
    PartSpec(
        "PS-RV2272-SFS-REAR-CAP",
        "optional faceted rear closure cap for CBOX side; includes lower drain notches",
        "PETG/PLA", "RIGID", 1, "SFS-G2-P03-CAPS",
        "PS-RV2272-SFS-REAR-CAP.stl", "PS-RV2272-SFS-REAR-CAP.step",
        (188.0, 12.0, 64.0),
        "Use on rear/CBOX end only. Do not fully seal if trapped mud/water cannot drain.",
    ),
    PartSpec(
        "PS-RV2272-SFS-FRONT-VISOR",
        "optional open PTO-side splash visor; sheds water but does not close the front",
        "PETG/PLA", "RIGID", 1, "SFS-G2-P03-CAPS",
        "PS-RV2272-SFS-FRONT-VISOR.stl", "PS-RV2272-SFS-FRONT-VISOR.step",
        (184.0, 38.0, 28.0),
        "Keep PTO side open. Use only if it does not interfere with unit attachment/removal.",
    ),
    PartSpec(
        "PS-RV2272-SFS-SIDE-FLOAT-L",
        "left detachable side sponson float; separate from roof and away from DRC/DRIVE",
        "PETG/PLA", "RIGID", 1, "SFS-G2-P04-FLOAT-L",
        "PS-RV2272-SFS-SIDE-FLOAT-L.stl", "PS-RV2272-SFS-SIDE-FLOAT-L.step",
        (56.0, 238.0, 42.0),
        "Not guaranteed watertight as raw FDM. Seal or fill with closed-cell foam before water tests.",
    ),
    PartSpec(
        "PS-RV2272-SFS-SIDE-FLOAT-R",
        "right detachable side sponson float; separate from roof and away from DRC/DRIVE",
        "PETG/PLA", "RIGID", 1, "SFS-G2-P05-FLOAT-R",
        "PS-RV2272-SFS-SIDE-FLOAT-R.stl", "PS-RV2272-SFS-SIDE-FLOAT-R.step",
        (56.0, 238.0, 42.0),
        "Print one first and dry-fit. Preserve tire and gearbox clearance before water tests.",
    ),
    PartSpec(
        "PS-RV2272-SFS-MCR-CLAMP-S",
        "loose retrofit U-clamp for MCR rail / shell dry fit",
        "PETG/PLA", "RIGID", 6, "SFS-G2-P06-MOUNTS",
        "PS-RV2272-SFS-MCR-CLAMP-S.stl", "PS-RV2272-SFS-MCR-CLAMP-S.step",
        (36.0, 44.0, 24.0),
        "Prototype clamp. Verify actual printed rail size and do not crush waterproof boxes.",
    ),
    PartSpec(
        "PS-RV2272-SFS-FLT-RCV-SADDLE-S",
        "adapter saddle for existing FLT-RCV receiver; side-float mounting reference",
        "PETG/PLA", "RIGID", 4, "SFS-G2-P06-MOUNTS",
        "PS-RV2272-SFS-FLT-RCV-SADDLE-S.stl", "PS-RV2272-SFS-FLT-RCV-SADDLE-S.step",
        (68.0, 34.0, 34.0),
        "Use as removable adapter. Do not make the float shell touch side gearboxes.",
    ),
    PartSpec(
        "PS-RV2272-SFS-CLEARANCE-GAUGE-S",
        "8/10/12 mm clearance gauge for DRC/DRIVE and tire sweep dry-fit checks",
        "PETG/PLA", "RIGID", 2, "SFS-G2-P06-MOUNTS",
        "PS-RV2272-SFS-CLEARANCE-GAUGE-S.stl", "PS-RV2272-SFS-CLEARANCE-GAUGE-S.step",
        (54.0, 18.0, 16.0),
        "Use before mounting floats. If this does not pass, the shell/float is too close.",
    ),
    PartSpec(
        "PS-RV2272-RCP-DOGHOUSE-G2",
        "high-mounted sloped E-stop doghouse; avoids simple top-hole waterproof weakness",
        "PETG/PLA", "RIGID", 1, "SFS-G2-P07-DOGHOUSE",
        "PS-RV2272-RCP-DOGHOUSE-G2.stl", "PS-RV2272-RCP-DOGHOUSE-G2.step",
        (112.0, 90.0, 78.0),
        "Use real waterproof 22mm-class E-stop. Protect rear terminals and add drip loop.",
    ),
]

DESIGN_CONTRACT = {
    "kit": KIT_NAME,
    "version": VERSION,
    "compatibility": {
        "base_rover": "Paddy Swarm Common Rover v2.27",
        "base_modification_required": False,
        "current_v227_print_can_continue": True,
        "retrofit_policy": "add-on clamps/adapters only; no BBOX/CBOX drilling in first test",
    },
    "geometry_policy": [
        "Use 45-degree faceted roof panels instead of smooth curves for lower-support printing.",
        "Keep PTO/front side open; optionally add FRONT-VISOR only.",
        "Close rear/CBOX side only with optional REAR-CAP and drain notches.",
        "Side floats are separate sponsons, not continuous walls around gearboxes.",
        "Do not make shell or floats touch DRC/DRIVE gearboxes or tire sweep.",
    ],
    "safety_policy": [
        "E-stop must be higher than likely splash/waterline and accessible with shell fitted.",
        "Do not rely on top-mounted button gasket alone; use DOGHOUSE, waterproof button, terminal cover, drip loop, and cable gland.",
        "Water-intrusion sensors and independent high-current cutoff should be added before powered water tests.",
        "Use dummy weights, not electronics, for first float/water tests.",
    ],
    "reference_dimensions_mm": REF,
    "roof_dimensions_mm": ROOF,
    "float_dimensions_mm": FLOAT,
    "doghouse_dimensions_mm": DOGHOUSE,
}


def load_cadquery():
    try:
        import cadquery as cq  # type: ignore
        from cadquery import exporters  # type: ignore
        return cq, exporters
    except Exception as exc:
        raise RuntimeError(
            "CadQuery is not installed in this environment. Use --metadata-only here, "
            "or run the script in your CadQuery environment. "
            f"Original error: {exc}"
        ) from exc


def box(cq, x: float, y: float, z: float, pos=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").box(x, y, z).translate(pos)


def cyl_z(cq, d: float, h: float, pos=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").circle(d / 2.0).extrude(h).translate((pos[0], pos[1], pos[2] - h / 2.0))


def cyl_y(cq, d: float, h: float, pos=(0.0, 0.0, 0.0)):
    return cq.Workplane("XZ").circle(d / 2.0).extrude(h).translate((pos[0], pos[1] - h / 2.0, pos[2]))


def add_label(obj, cq, text: str, x: float, y: float, z: float, size: float = 7.0):
    try:
        txt = cq.Workplane("XY").text(text, size, 0.7, halign="center", valign="center").translate((x, y, z))
        return obj.union(txt)
    except Exception:
        return obj


def make_roof_shell(cq, suffix: str):
    """Faceted 45-degree roof shell, open at both ends.

    End treatment is handled by optional REAR-CAP and FRONT-VISOR.  This keeps
    the main shell printable and prevents a forced closed-box shape.
    """
    L = ROOF["length"]
    top_w = ROOF["top_width"]
    run = ROOF["side_run"]
    rise = ROOF["side_rise"]
    skirt_h = ROOF["skirt_height"]
    t = ROOF["panel_t"]
    edge_t = ROOF["edge_t"]
    rib_t = ROOF["rib_t"]
    m3 = ROOF["m3_clearance"]
    base_half = top_w / 2.0 + run + edge_t
    slope_len = math.sqrt(run * run + rise * rise)

    # Top and two 45-degree roof facets.
    obj = box(cq, top_w, L, t, (0, 0, skirt_h + rise + t / 2.0))
    left = box(cq, slope_len, L, t).rotate((0, 0, 0), (0, 1, 0), -45)
    left = left.translate((-(top_w / 2.0 + run / 2.0), 0, skirt_h + rise / 2.0))
    right = box(cq, slope_len, L, t).rotate((0, 0, 0), (0, 1, 0), 45)
    right = right.translate(((top_w / 2.0 + run / 2.0), 0, skirt_h + rise / 2.0))
    obj = obj.union(left).union(right)

    # Short vertical drip skirts, not full side walls.
    obj = obj.union(box(cq, edge_t, L, skirt_h, (-base_half + edge_t / 2.0, 0, skirt_h / 2.0)))
    obj = obj.union(box(cq, edge_t, L, skirt_h, (base_half - edge_t / 2.0, 0, skirt_h / 2.0)))

    # End ribs make it read as a shell/dome while leaving the end open.
    for yy in (-(L / 2.0 - rib_t / 2.0), (L / 2.0 - rib_t / 2.0)):
        obj = obj.union(box(cq, top_w + 2.0, rib_t, t + 1.2, (0, yy, skirt_h + rise + t + 0.6)))
        obj = obj.union(box(cq, edge_t + 1.5, rib_t, skirt_h + 2.0, (-base_half + edge_t / 2.0, yy, skirt_h / 2.0)))
        obj = obj.union(box(cq, edge_t + 1.5, rib_t, skirt_h + 2.0, (base_half - edge_t / 2.0, yy, skirt_h / 2.0)))

    # Mount tabs under edge; holes vertical for loose straps/pins.
    tab_w, tab_l, tab_z = 22.0, 34.0, 5.0
    for x in (-(base_half - 16.0), (base_half - 16.0)):
        for y in (-(L / 2.0 - 38.0), (L / 2.0 - 38.0)):
            tab = box(cq, tab_w, tab_l, tab_z, (x, y, 4.0))
            tab = tab.cut(cyl_z(cq, m3, 18.0, (x, y, 4.0)))
            obj = obj.union(tab)

    # Center crown ridge sheds water and gives a visible top centerline.
    obj = obj.union(box(cq, 5.0, L - 18.0, 3.0, (0, 0, skirt_h + rise + t + 1.5)))
    obj = add_label(obj, cq, f"SFS-G2-{suffix}", 0, 0, skirt_h + rise + t + 5.0, 8.0)
    return obj


def make_rear_cap(cq):
    """Faceted rear cap plate with drain notches.

    It closes the CBOX/rear side without claiming full waterproof sealing.
    """
    top_w = ROOF["top_width"]
    run = ROOF["side_run"]
    rise = ROOF["side_rise"]
    skirt_h = ROOF["skirt_height"]
    edge_t = ROOF["edge_t"]
    cap_t = 4.0
    base_half = top_w / 2.0 + run + edge_t
    pts = [
        (-base_half, 0.0),
        (-base_half, skirt_h),
        (-top_w / 2.0, skirt_h + rise),
        (top_w / 2.0, skirt_h + rise),
        (base_half, skirt_h),
        (base_half, 0.0),
    ]
    obj = cq.Workplane("XZ").polyline(pts).close().extrude(cap_t).translate((0, -cap_t / 2.0, 0))
    # Drain/inspection notches along lower edge.
    for x in (-58.0, 0.0, 58.0):
        obj = obj.cut(box(cq, 18.0, 12.0, 8.0, (x, 0.0, 4.0)))
    # Simple screw slots in lower side regions.
    for x in (-72.0, 72.0):
        obj = obj.cut(cyl_y(cq, ROOF["m3_clearance"], 16.0, (x, 0.0, 20.0)))
    obj = add_label(obj, cq, "REAR", 0, -3.0, 54.0, 7.0)
    return obj


def make_front_visor(cq):
    """Open splash visor for PTO side, not a closure."""
    w = 184.0
    y = 34.0
    t = 3.2
    obj = box(cq, w, y, t, (0, 0, 20.0)).rotate((0, 0, 0), (1, 0, 0), -18.0)
    obj = obj.union(box(cq, w, 6.0, 8.0, (0, -y / 2.0 + 3.0, 8.0)))
    for x in (-70.0, 70.0):
        obj = obj.cut(cyl_z(cq, ROOF["m3_clearance"], 18.0, (x, 0.0, 7.0)))
    obj = add_label(obj, cq, "OPEN PTO", 0, 0, 25.0, 7.0)
    return obj


def make_side_float(cq, side: str):
    """Separate side sponson float, not a wall around the gearbox.

    The cross-section is a chamfered pontoon.  It must be sealed or foam-filled
    before any water test.  Mount tabs are on the inner side so the float can be
    spaced away from DRC/DRIVE using saddles/standoffs.
    """
    L = FLOAT["length"]
    W = FLOAT["width"]
    H = FLOAT["height"]
    C = FLOAT["chamfer"]
    pts = [
        (-W / 2.0, 0.0),
        (W / 2.0, 0.0),
        (W / 2.0, H - C),
        (W / 2.0 - C, H),
        (-W / 2.0 + C, H),
        (-W / 2.0, H - C),
    ]
    obj = cq.Workplane("XZ").polyline(pts).close().extrude(L).translate((0, -L / 2.0, 0))

    # Inner-side mounting tabs. L and R are mirrored by changing the tab side.
    sign = -1.0 if side == "L" else 1.0
    tab_x = sign * (W / 2.0 + 6.0)
    for y in (-78.0, 0.0, 78.0):
        tab = box(cq, 12.0, 28.0, 18.0, (tab_x, y, 18.0))
        tab = tab.cut(cyl_y(cq, FLOAT["m3_clearance"], 34.0, (tab_x, y, 18.0)))
        obj = obj.union(tab)

    # Waterline / orientation ridge on top; helps visually distinguish the float.
    obj = obj.union(box(cq, 6.0, L - 20.0, 2.0, (0, 0, H + 1.0)))
    obj = add_label(obj, cq, f"FLOAT-{side}", 0, 0, H + 4.0, 7.0)
    return obj


def make_mcr_clamp(cq):
    outer = box(cq, 36.0, 44.0, 24.0)
    slot = box(cq, 22.0, 48.0, 16.0, (0, 0, -4.0))
    obj = outer.cut(slot)
    obj = obj.cut(cyl_z(cq, 3.8, 32.0, (0, 0, 7.0)))
    obj = add_label(obj, cq, "MCR", 0, 0, 13.0, 6.0)
    return obj


def make_flt_rcv_saddle(cq):
    base = box(cq, 68.0, 34.0, 10.0, (0, 0, 5.0))
    vertical = box(cq, 14.0, 30.0, 28.0, (0, 0, 24.0))
    obj = base.union(vertical)
    obj = obj.cut(box(cq, 36.0, 14.0, 5.0, (0, 0, 2.0)))
    obj = obj.cut(cyl_y(cq, 4.0, 50.0, (0, 0, 24.0)))
    obj = add_label(obj, cq, "SADDLE", 0, 0, 39.0, 5.5)
    return obj


def make_clearance_gauge(cq):
    # Simple stepped gauge: 8, 10, 12 mm thicknesses.
    p8 = box(cq, 18.0, 18.0, 8.0, (-18.0, 0, 4.0))
    p10 = box(cq, 18.0, 18.0, 10.0, (0.0, 0, 5.0))
    p12 = box(cq, 18.0, 18.0, 12.0, (18.0, 0, 6.0))
    obj = p8.union(p10).union(p12)
    obj = add_label(obj, cq, "8 10 12", 0, 0, 14.0, 5.0)
    return obj


def make_rcp_doghouse(cq):
    pw = DOGHOUSE["panel_w"]
    ph = DOGHOUSE["panel_h"]
    pt = DOGHOUSE["panel_t"]
    d = DOGHOUSE["estop_hole_d"]
    angle = DOGHOUSE["angle_deg"]

    plate = cq.Workplane("XY").box(pw, ph, pt)
    plate = plate.faces(">Z").workplane().hole(d)
    plate = plate.rotate((0, 0, 0), (1, 0, 0), -angle).translate((0, -4.0, 46.0))

    base = box(cq, DOGHOUSE["base_w"], DOGHOUSE["base_l"], DOGHOUSE["base_t"], (0, 0, DOGHOUSE["base_t"] / 2.0))
    for hx in (-36.0, 36.0):
        for hy in (-20.0, 20.0):
            base = base.cut(cyl_z(cq, DOGHOUSE["m3_clearance"], 18.0, (hx, hy, DOGHOUSE["base_t"] / 2.0)))

    # Splash hood and rear terminal cup, still open enough to service.
    hood = box(cq, pw + 22.0, DOGHOUSE["hood_depth"], DOGHOUSE["hood_t"], (0, -42.0, 75.0))
    hood = hood.rotate((0, 0, 0), (1, 0, 0), -8.0)
    rear = box(cq, pw + 10.0, 4.0, 48.0, (0, 34.0, 38.0))
    left = box(cq, 4.0, 30.0, 48.0, (-(pw / 2.0 + 5.0), 20.0, 38.0))
    right = box(cq, 4.0, 30.0, 48.0, ((pw / 2.0 + 5.0), 20.0, 38.0))
    obj = base.union(plate).union(hood).union(rear).union(left).union(right)
    obj = add_label(obj, cq, "E-STOP", 0, -38.0, 80.0, 7.0)
    return obj


BUILDERS: Dict[str, Callable] = {
    "PS-RV2272-SFS-ROOF-F": lambda cq: make_roof_shell(cq, "F"),
    "PS-RV2272-SFS-ROOF-R": lambda cq: make_roof_shell(cq, "R"),
    "PS-RV2272-SFS-REAR-CAP": make_rear_cap,
    "PS-RV2272-SFS-FRONT-VISOR": make_front_visor,
    "PS-RV2272-SFS-SIDE-FLOAT-L": lambda cq: make_side_float(cq, "L"),
    "PS-RV2272-SFS-SIDE-FLOAT-R": lambda cq: make_side_float(cq, "R"),
    "PS-RV2272-SFS-MCR-CLAMP-S": make_mcr_clamp,
    "PS-RV2272-SFS-FLT-RCV-SADDLE-S": make_flt_rcv_saddle,
    "PS-RV2272-SFS-CLEARANCE-GAUGE-S": make_clearance_gauge,
    "PS-RV2272-RCP-DOGHOUSE-G2": make_rcp_doghouse,
}


def ensure_dirs(out: Path) -> Dict[str, Path]:
    paths = {"root": out, "stl": out / "stl", "step": out / "step", "docs": out / "docs"}
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def manifest_rows():
    rows = []
    for p in PARTS:
        bx, by, bz = p.bbox_mm
        stl_path = f"stl/{p.filename_stl}"
        step_path = f"step/{p.filename_step}"
        rows.append({
            "part_id": p.part_id,
            "part_no": p.part_id,
            "part_code": p.part_id,
            "label": p.part_id,
            "label_text": p.part_id,
            "description": p.description,
            "name": p.description,
            "part_name": p.description,
            "material": p.material,
            "material_hint": p.material,
            "material_group": "HARD",
            "group": p.group,
            "qty": p.qty,
            "quantity": p.qty,
            "count": p.qty,
            "is_tpu": "0",
            "split_group": "HARD",
            "plate": p.plate_group,
            "plate_group": p.plate_group,
            "plate_id": p.plate_group,
            "module": "v2272_summer_float_shell_g2",
            "title": p.description,
            "filename_stl": p.filename_stl,
            "filename_step": p.filename_step,
            "stl": stl_path,
            "stl_file": stl_path,
            "stl_path": stl_path,
            "file": stl_path,
            "filename": p.filename_stl,
            "path": stl_path,
            "file_path": stl_path,
            "source_file": stl_path,
            "source_path": stl_path,
            "output_stl": stl_path,
            "step": step_path,
            "step_file": step_path,
            "step_path": step_path,
            "bbox_x_mm": bx,
            "bbox_y_mm": by,
            "bbox_z_mm": bz,
            "bbox_x": bx,
            "bbox_y": by,
            "bbox_z": bz,
            "printable": "1",
            "marked": "1",
            "notes": p.notes,
        })
    return rows


def write_csv_rows(path: Path, rows):
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_manifests(out: Path):
    rows = manifest_rows()
    write_csv_rows(out / "print_manifest.csv", rows)
    write_csv_rows(out / "print_manifest_generic_marked.csv", rows)

    plates = {}
    for p in PARTS:
        plates.setdefault(p.plate_group, []).append(p)
    plate_rows = []
    for plate, items in sorted(plates.items()):
        plate_rows.append({
            "plate": plate,
            "plate_group": plate,
            "part_ids": ";".join(f"{p.part_id} x{p.qty}" for p in items),
            "material": "/".join(sorted({p.material for p in items})),
            "notes": "One large component per plate where possible. Use individual plate 3MF fallback if Bambu multi-plate project shows boundary warnings.",
        })
    write_csv_rows(out / "plate_manifest.csv", plate_rows)


def write_docs(out: Path):
    (out / "paddy_swarm_v2272_sfs_g2_design_contract.json").write_text(
        json.dumps(DESIGN_CONTRACT, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    readme = f"""
# {KIT_NAME} ({VERSION})

This is the G2 retrofit turtle-shell kit for the already printing Paddy Swarm
Common Rover v2.27.

## Main changes from G1

- The roof is treated as a faceted turtle-shell/dome, not just a flat open cover.
- PTO/front side remains open; use only the optional FRONT-VISOR if it clears the PTO/unit.
- Rear/CBOX side can be closed with the optional REAR-CAP, which includes drain notches.
- Side floats are separate left/right sponsons. They are not continuous walls around the gearboxes.
- The E-stop uses a high sloped doghouse instead of a simple top hole.
- `print_manifest_generic_marked.csv` is written directly for dense v5.7.

## First print order

1. Print `PS-RV2272-SFS-ROOF-F` or `PS-RV2272-SFS-ROOF-R` alone.
2. Place it on the v2.27 rover without fastening.
3. Confirm BBOX/CBOX lid, RCP/E-stop, DRC/DRIVE, tire sweep, and PTO clearance.
4. Print one side float only and use `CLEARANCE-GAUGE-S` before attaching it.
5. Add rear cap only if it does not trap mud/water and still allows cleaning.

## Important

- Raw FDM side floats are not guaranteed watertight. Seal, coat, or foam-fill before water testing.
- Do not run water tests with electronics installed.
- Use dummy weights first.
- Add water intrusion sensors and an independent high-current cutoff before powered water trials.

## Dense note

If Bambu Studio opens `*_bambu_multiplate_project.3mf` and shows objects outside the active plate, use the individual 3MF files under `3mf_dense_pack_rigid/` instead.  Those are the safer fallback for printing one plate at a time.
"""
    (out / "README_v2272_sfs_g2.md").write_text(textwrap.dedent(readme).strip() + "\n", encoding="utf-8")


def export_parts(out: Path):
    cq, exporters = load_cadquery()
    paths = ensure_dirs(out)
    for p in PARTS:
        obj = BUILDERS[p.part_id](cq)
        exporters.export(obj, str(paths["stl"] / p.filename_stl))
        exporters.export(obj, str(paths["step"] / p.filename_step))


def make_zip(out: Path) -> Path:
    zip_path = out.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(out.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(out.parent))
    return zip_path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_args(argv: Optional[Iterable[str]] = None):
    ap = argparse.ArgumentParser(description=KIT_NAME)
    ap.add_argument("--out", default="rover_v2272_sfs_g2_out")
    ap.add_argument("--metadata-only", action="store_true")
    ap.add_argument("--make-zip", action="store_true")
    return ap.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    out = Path(args.out).resolve()
    ensure_dirs(out)
    write_manifests(out)
    write_docs(out)
    if not args.metadata_only:
        export_parts(out)
    if args.make_zip:
        zp = make_zip(out)
        print(f"ZIP: {zp}")
        print(f"SHA256: {sha256_file(zp)}")
    print(f"WROTE: {out}")
    print("MODE:", "metadata-only" if args.metadata_only else "CAD exported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
