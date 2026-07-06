#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paddy Swarm Common Rover v2.27.1 Retrofit Summer Float Shell Kit
================================================================

Purpose
-------
A retrofit, non-destructive "turtle shell" / summer float shell kit for the
existing Paddy Swarm Common Rover v2.27.

Design policy
-------------
- Do NOT modify the already-printing v2.27 BBOX/CBOX bodies or lids.
- Start with CENTRAL TOP PROTECTION only.
- Keep the shell away from DRC/DRIVE gearboxes and wheel/tire sweep.
- Use MCR rails / FLT-RCV rails / LOWER-FRAME side area as retrofit mounting
  references through add-on clamps/adapters.
- Do NOT clamp or drill directly into the waterproof BBOX/CBOX.
- E-stop must remain accessible when the shell is mounted.
- This is a prototype CAD generator. Verify clearances in the slicer and on the
  printed v2.27 body before water testing.

Coordinate convention for generated parts
-----------------------------------------
- X: rover width, left/right
- Y: rover length, front/rear
- Z: vertical

Expected command
----------------
python paddy_swarm_v2271_summer_float_shell_cadquery.py --out rover_v2271_sfs_out --make-zip

Metadata-only command when CadQuery is not installed
----------------------------------------------------
python paddy_swarm_v2271_summer_float_shell_cadquery.py --metadata-only --out rover_v2271_sfs_meta --make-zip

Notes
-----
This file intentionally avoids depending on the v2.27 source file. It is a
standalone retrofit kit generator so the current v2.27 printing can continue.
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

VERSION = "v2.27.1-sfs-g1"
KIT_NAME = "Paddy Swarm Retrofit Summer Float Shell G1"

# v2.27 reference dimensions, kept conservative.
# These are not imported from the v2.27 CAD file so that this retrofit kit remains standalone.
REF = {
    "printed_box_body_mm": [150.0, 200.0, 120.0],
    "printed_box_lid_mm": [166.0, 216.0, 16.0],
    "mcr_rail_nominal_mm": [18.0, 430.0, 18.0],
    "lower_frame_mm": [232.0, 188.0, 22.0],
    "float_receiver_nominal_mm": [226.0, 28.0, 18.0],
    "design_clearance_from_gearbox_mm": 8.0,
    "minimum_tire_clearance_mm": 12.0,
}

# Print/assembly dimensions for the retrofit parts.
# Main shell: each half fits on a 256 x 256 mm A1 plate.
SHELL = {
    "length": 232.0,          # covers a 216 mm lid with margin
    "base_width": 194.0,      # intentionally narrower than full wheel/gear region
    "top_width": 118.0,
    "side_run": 34.0,         # 45-degree slope run
    "side_rise": 34.0,        # 45-degree slope rise
    "side_skirt_height": 16.0,
    "thickness": 3.2,
    "edge_rail_thickness": 4.0,
    "flange_w": 22.0,
    "flange_l": 34.0,
    "m3_clearance": 3.6,
    "overlap": 0.35,
}

DOGHOUSE = {
    "panel_w": 86.0,
    "panel_h": 64.0,
    "panel_t": 4.0,
    "estop_hole_d": 23.5,     # 22 mm class waterproof panel-mount E-stop, verify actual part
    "angle_deg": 22.0,        # sloped face sheds water better than horizontal
    "hood_depth": 20.0,
    "hood_t": 4.0,
    "side_wall_t": 3.2,
    "base_w": 100.0,
    "base_l": 54.0,
    "base_t": 5.0,
    "m3_clearance": 3.6,
}


@dataclass(frozen=True)
class PartSpec:
    part_id: str
    description: str
    material: str
    group: str
    qty: int
    plate: str
    filename_stl: str
    filename_step: str
    bbox_mm: Tuple[float, float, float]
    notes: str


PARTS = [
    PartSpec(
        "PS-RV2271-SFS-CENTER-F",
        "front/BBOX retrofit 45-degree central turtle shell; top protection only",
        "PETG/PLA",
        "RIGID",
        1,
        "SFS-RIGID-01",
        "PS-RV2271-SFS-CENTER-F.stl",
        "PS-RV2271-SFS-CENTER-F.step",
        (194.0, 232.0, 56.0),
        "Do not attach to BBOX directly; use clamps/adapters. Keep clear of DRC/DRIVE.",
    ),
    PartSpec(
        "PS-RV2271-SFS-CENTER-R",
        "rear/CBOX retrofit 45-degree central turtle shell; top protection only",
        "PETG/PLA",
        "RIGID",
        1,
        "SFS-RIGID-01",
        "PS-RV2271-SFS-CENTER-R.stl",
        "PS-RV2271-SFS-CENTER-R.step",
        (194.0, 232.0, 56.0),
        "Do not attach to CBOX directly; use clamps/adapters. Leave E-stop visible/accesssible.",
    ),
    PartSpec(
        "PS-RV2271-SFS-JOINER-S",
        "front/rear shell joiner strap set; optional bridge between the two central shells",
        "PETG/PLA",
        "RIGID",
        2,
        "SFS-RIGID-02",
        "PS-RV2271-SFS-JOINER-S.stl",
        "PS-RV2271-SFS-JOINER-S.step",
        (148.0, 24.0, 6.0),
        "Use two straps left/right or top-side depending on actual assembly clearance.",
    ),
    PartSpec(
        "PS-RV2271-SFS-MCR-CLAMP-S",
        "retrofit clamp block for v2.27 MCR rail; keeps shell mounting away from waterproof boxes",
        "PETG/PLA",
        "RIGID",
        6,
        "SFS-RIGID-02",
        "PS-RV2271-SFS-MCR-CLAMP-S.stl",
        "PS-RV2271-SFS-MCR-CLAMP-S.step",
        (34.0, 42.0, 22.0),
        "Prototype U-clamp for nominal 18 mm MCR rail. Verify rail fit before tightening/locking.",
    ),
    PartSpec(
        "PS-RV2271-SFS-FLT-RCV-ADAPTER-S",
        "adapter foot for existing FLT-RCV side float receiver; keeps shell/float standoff separated from DRC",
        "PETG/PLA",
        "RIGID",
        4,
        "SFS-RIGID-02",
        "PS-RV2271-SFS-FLT-RCV-ADAPTER-S.stl",
        "PS-RV2271-SFS-FLT-RCV-ADAPTER-S.step",
        (64.0, 32.0, 34.0),
        "Use only if it clears DRC/DRIVE/tire sweep. Do not make the side shell touch gearboxes.",
    ),
    PartSpec(
        "PS-RV2271-SFS-SIDE-STANDOFF-S",
        "sacrificial side standoff/spacer; enforces clearance between shell/side float and gearboxes",
        "PETG/PLA",
        "RIGID",
        4,
        "SFS-RIGID-03",
        "PS-RV2271-SFS-SIDE-STANDOFF-S.stl",
        "PS-RV2271-SFS-SIDE-STANDOFF-S.step",
        (28.0, 24.0, 48.0),
        "Use as a clearance gauge/spacer first. Target DRC/DRIVE clearance: 8-10 mm or more.",
    ),
    PartSpec(
        "PS-RV2271-RCP-DOGHOUSE-G1",
        "high-mounted waterproof E-stop doghouse prototype with 22 mm class sloped button face",
        "PETG/PLA",
        "RIGID",
        1,
        "SFS-RIGID-03",
        "PS-RV2271-RCP-DOGHOUSE-G1.stl",
        "PS-RV2271-RCP-DOGHOUSE-G1.step",
        (110.0, 84.0, 74.0),
        "Prototype only. Use a real waterproof panel-mount E-stop; pot/protect rear terminals.",
    ),
]


DESIGN_CONTRACT = {
    "kit": KIT_NAME,
    "version": VERSION,
    "compatibility": {
        "base_rover": "Paddy Swarm Common Rover v2.27",
        "requires_base_modification": False,
        "do_not_reprint_current_bbox_cbox": True,
        "intended_use": "retrofit top shell / summer water-weeding season protection prototype",
    },
    "safety_policy": [
        "This shell is not a waterproof guarantee.",
        "Do not hide or block the emergency stop button.",
        "Do not place the shell or side adapters against DRC/DRIVE gearboxes.",
        "Do not drill into the waterproof BBOX/CBOX during first retrofit testing.",
        "Do not run water tests with electronics installed; use dummy weights first.",
        "Use water intrusion sensors and independent high-current cutoff in later electrical builds.",
    ],
    "mechanical_policy": [
        "Central top shell protects BBOX/CBOX lid, cable-notch area, and direct splash path.",
        "MCR/FLT-RCV/LOWER-FRAME area is used as mounting reference instead of the waterproof boxes.",
        "Side float shells must remain separate from central shell and must preserve gearbox service access.",
        "Minimum target clearance around DRC/DRIVE is 8 mm, preferably 10 mm or more.",
        "Minimum target clearance around tire sweep is 12 mm or more in clean dry test, more in mud.",
        "All dimensions are prototype values and must be checked on the actual printed v2.27 body.",
    ],
    "print_policy": [
        "Main shell halves fit within a 256 x 256 mm class plate as separate front/rear parts.",
        "For lowest support, orient central shells with the broad top/roof face toward the build plate if needed.",
        "Do not enable heavy supports before checking orientation manually in the slicer.",
        "PETG is preferred for outdoor testing; PLA is acceptable for dry fit/mockup.",
    ],
    "reference_dimensions_mm": REF,
    "shell_dimensions_mm": SHELL,
    "doghouse_dimensions_mm": DOGHOUSE,
}


def load_cadquery():
    try:
        import cadquery as cq  # type: ignore
        from cadquery import exporters  # type: ignore
        return cq, exporters
    except Exception as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "CadQuery is not installed in this Python environment. "
            "Use --metadata-only here, or run this script in a CadQuery-enabled environment. "
            f"Original error: {exc}"
        ) from exc


def box(cq, x: float, y: float, z: float, pos=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").box(x, y, z).translate(pos)


def cyl_z(cq, d: float, h: float, pos=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").circle(d / 2.0).extrude(h).translate((pos[0], pos[1], pos[2] - h / 2.0))


def add_label(obj, cq, text: str, x: float, y: float, z: float, size: float = 8.0):
    """Add a tiny raised label when text support exists; otherwise return object unchanged."""
    try:
        txt = cq.Workplane("XY").text(text, size, 0.8, halign="center", valign="center").translate((x, y, z))
        return obj.union(txt)
    except Exception:
        return obj


def make_center_shell(cq, suffix: str):
    """Make one 45-degree central retrofit shell half.

    The shell deliberately covers only the BBOX/CBOX top region. It does not drop
    down over DRC/DRIVE gearboxes.
    """
    L = SHELL["length"]
    top_w = SHELL["top_width"]
    side_run = SHELL["side_run"]
    side_rise = SHELL["side_rise"]
    skirt_h = SHELL["side_skirt_height"]
    t = SHELL["thickness"]
    rail_t = SHELL["edge_rail_thickness"]
    overlap = SHELL["overlap"]
    m3 = SHELL["m3_clearance"]

    slope_len = math.sqrt(side_run ** 2 + side_rise ** 2)
    base_half = top_w / 2.0 + side_run + rail_t

    # Broad top plate. In final assembly this is high; in printing it can be rotated top-face-down.
    obj = box(cq, top_w + 2 * overlap, L, t, (0, 0, skirt_h + side_rise + t / 2.0))

    # 45-degree side roof panels. They overlap the top and side rails to avoid floating seams.
    left_slope = box(cq, slope_len + 2 * overlap, L, t, (0, 0, 0)).rotate((0, 0, 0), (0, 1, 0), -45)
    left_slope = left_slope.translate((-(top_w / 2.0 + side_run / 2.0), 0, skirt_h + side_rise / 2.0))
    right_slope = box(cq, slope_len + 2 * overlap, L, t, (0, 0, 0)).rotate((0, 0, 0), (0, 1, 0), 45)
    right_slope = right_slope.translate(((top_w / 2.0 + side_run / 2.0), 0, skirt_h + side_rise / 2.0))
    obj = obj.union(left_slope).union(right_slope)

    # Drip/edge skirts. These are short, intentionally not a full side wall.
    obj = obj.union(box(cq, rail_t, L, skirt_h + overlap, (-base_half + rail_t / 2.0, 0, skirt_h / 2.0)))
    obj = obj.union(box(cq, rail_t, L, skirt_h + overlap, (base_half - rail_t / 2.0, 0, skirt_h / 2.0)))

    # Four small lower flanges for clamp/joiner attachment. They hang under the roof edge, not on waterproof boxes.
    flange_w = SHELL["flange_w"]
    flange_l = SHELL["flange_l"]
    flange_z = 4.0
    flange_y_positions = [-(L / 2.0 - 34.0), (L / 2.0 - 34.0)]
    flange_x_positions = [-(base_half - flange_w / 2.0 - 2.0), (base_half - flange_w / 2.0 - 2.0)]
    for fx in flange_x_positions:
        for fy in flange_y_positions:
            pad = box(cq, flange_w, flange_l, flange_z, (fx, fy, 3.0))
            # Vertical clearance hole for M3/M3.5 printed pin or screw.
            pad = pad.cut(cyl_z(cq, m3, 20.0, (fx, fy, 3.0)))
            obj = obj.union(pad)

    # Rear/front rain split notch indicator: small external ridge, not a real drainage channel.
    # Actual drainage should be checked after assembly.
    obj = obj.union(box(cq, 6.0, L - 18.0, 2.0, (0, 0, skirt_h + side_rise + t + 1.0)))

    label = "SFS-F" if suffix == "F" else "SFS-R"
    obj = add_label(obj, cq, label, 0, 0, skirt_h + side_rise + t + 2.5, size=10.0)
    return obj


def make_joiner_strap(cq):
    x, y, z = 148.0, 24.0, 6.0
    obj = box(cq, x, y, z)
    for hx in (-54.0, 54.0):
        obj = obj.cut(cyl_z(cq, SHELL["m3_clearance"], 18.0, (hx, 0.0, 0.0)))
    obj = add_label(obj, cq, "JOIN", 0, 0, z / 2 + 0.8, size=8.0)
    return obj


def make_mcr_clamp(cq):
    """Nominal U-clamp for 18 mm MCR rail, intentionally loose for first retrofit test."""
    outer = box(cq, 34.0, 42.0, 22.0)
    # Bottom/side opening for nominal 18 mm rail. Oversized to avoid forcing printed v2.27 rails.
    slot = box(cq, 21.0, 46.0, 15.0, (0, 0, -4.0))
    obj = outer.cut(slot)
    # Top pin/screw hole.
    obj = obj.cut(cyl_z(cq, 3.8, 30.0, (0, 0, 6.0)))
    # Small witness notch on one side for orientation.
    obj = obj.cut(box(cq, 6.0, 8.0, 6.0, (17.0, 0, 5.0)))
    obj = add_label(obj, cq, "MCR", 0, 0, 12.0, size=6.0)
    return obj


def make_flt_rcv_adapter(cq):
    """Adapter foot for the existing v2.27 float receiver area.

    The vertical tab gives a shell/side-float standoff location without pressing
    against DRC/DRIVE gearboxes.
    """
    base = box(cq, 64.0, 32.0, 10.0, (0, 0, 5.0))
    tab = box(cq, 12.0, 30.0, 28.0, (0, 0, 24.0))
    obj = base.union(tab)
    # Rail clearance grooves on underside; intentionally shallow/loose.
    obj = obj.cut(box(cq, 34.0, 12.0, 5.0, (0, 0, 2.0)))
    # Horizontal-ish attachment hole through the tab along Y.
    hole = cq.Workplane("XZ").circle(2.0).extrude(50.0).translate((0, -25.0, 24.0))
    obj = obj.cut(hole)
    obj = add_label(obj, cq, "FLT", 0, 0, 39.0, size=6.0)
    return obj


def make_side_standoff(cq):
    obj = box(cq, 28.0, 24.0, 48.0, (0, 0, 24.0))
    obj = obj.cut(cyl_z(cq, 4.0, 60.0, (0, 0, 24.0)))
    # Clearance gauge marks: stepped notches, so the printed part is also useful as a dry-fit spacer.
    obj = obj.cut(box(cq, 8.0, 26.0, 8.0, (10.0, 0.0, 12.0)))
    obj = obj.cut(box(cq, 8.0, 26.0, 8.0, (10.0, 0.0, 28.0)))
    obj = add_label(obj, cq, "8-10", 0, 0, 49.0, size=5.0)
    return obj


def make_rcp_doghouse(cq):
    """E-stop doghouse prototype.

    Sloped panel has a 23.5 mm through-hole for a 22 mm class waterproof E-stop.
    Verify actual button datasheet before committing to a water test.
    """
    pw = DOGHOUSE["panel_w"]
    ph = DOGHOUSE["panel_h"]
    pt = DOGHOUSE["panel_t"]
    angle = DOGHOUSE["angle_deg"]
    d = DOGHOUSE["estop_hole_d"]

    # Start as local vertical plate in XY with thickness along Z, cut the button hole, then rotate.
    plate = cq.Workplane("XY").box(pw, ph, pt)
    plate = plate.faces(">Z").workplane().hole(d)
    plate = plate.rotate((0, 0, 0), (1, 0, 0), -angle).translate((0, 0, 42.0))

    # Mounting base. This mounts to shell/MCR adapter, not directly to BBOX/CBOX.
    base = box(cq, DOGHOUSE["base_w"], DOGHOUSE["base_l"], DOGHOUSE["base_t"], (0, 0, DOGHOUSE["base_t"] / 2.0))
    for hx in (-34.0, 34.0):
        for hy in (-17.0, 17.0):
            base = base.cut(cyl_z(cq, DOGHOUSE["m3_clearance"], 20.0, (hx, hy, DOGHOUSE["base_t"] / 2.0)))

    # Rear terminal splash cup, open downward/backward. This is not a waterproof seal; it is a protective hood.
    cup_back = box(cq, pw + 8.0, 4.0, 48.0, (0, 32.0, 34.0))
    cup_l = box(cq, 4.0, 28.0, 48.0, (-(pw / 2.0 + 4.0), 18.0, 34.0))
    cup_r = box(cq, 4.0, 28.0, 48.0, ((pw / 2.0 + 4.0), 18.0, 34.0))

    # Upper hood / small eave above button face.
    hood = box(cq, pw + 20.0, DOGHOUSE["hood_depth"], DOGHOUSE["hood_t"], (0, -34.0, 70.0))
    hood = hood.rotate((0, 0, 0), (1, 0, 0), -8.0)

    obj = base.union(plate).union(cup_back).union(cup_l).union(cup_r).union(hood)
    obj = add_label(obj, cq, "E-STOP", 0, -30, 74.0, size=7.0)
    return obj


BUILDERS: Dict[str, Callable] = {
    "PS-RV2271-SFS-CENTER-F": lambda cq: make_center_shell(cq, "F"),
    "PS-RV2271-SFS-CENTER-R": lambda cq: make_center_shell(cq, "R"),
    "PS-RV2271-SFS-JOINER-S": make_joiner_strap,
    "PS-RV2271-SFS-MCR-CLAMP-S": make_mcr_clamp,
    "PS-RV2271-SFS-FLT-RCV-ADAPTER-S": make_flt_rcv_adapter,
    "PS-RV2271-SFS-SIDE-STANDOFF-S": make_side_standoff,
    "PS-RV2271-RCP-DOGHOUSE-G1": make_rcp_doghouse,
}


def ensure_dirs(out: Path) -> Dict[str, Path]:
    paths = {
        "root": out,
        "stl": out / "stl",
        "step": out / "step",
        "docs": out / "docs",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def write_manifest(out: Path) -> None:
    fields = [
        "part_id",
        "description",
        "material",
        "group",
        "qty",
        "plate",
        "filename_stl",
        "filename_step",
        "bbox_x_mm",
        "bbox_y_mm",
        "bbox_z_mm",
        "notes",
    ]
    with (out / "print_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for p in PARTS:
            row = asdict(p)
            bx, by, bz = p.bbox_mm
            row.pop("bbox_mm")
            row.update({"bbox_x_mm": bx, "bbox_y_mm": by, "bbox_z_mm": bz})
            w.writerow(row)

    with (out / "plate_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        fields2 = ["plate", "part_ids", "material", "notes"]
        w = csv.DictWriter(f, fieldnames=fields2)
        w.writeheader()
        plates: Dict[str, list] = {}
        for p in PARTS:
            plates.setdefault(p.plate, []).append(p)
        for plate, items in sorted(plates.items()):
            w.writerow({
                "plate": plate,
                "part_ids": ";".join(f"{p.part_id} x{p.qty}" for p in items),
                "material": "/".join(sorted({p.material for p in items})),
                "notes": "A1 256x256-class plate; verify orientation and support manually",
            })


def write_design_contract(out: Path) -> None:
    (out / "paddy_swarm_v2271_sfs_design_contract.json").write_text(
        json.dumps(DESIGN_CONTRACT, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_readme(out: Path) -> None:
    readme = f"""
# {KIT_NAME} ({VERSION})

This is a **retrofit add-on shell kit** for the already printable Paddy Swarm
Common Rover v2.27. It is intended to let the current v2.27 print continue while
adding a removable water-season top shell later.

## What this kit tries to do

- Add a central 45-degree turtle-shell style top protector over BBOX/CBOX.
- Keep mounting loads away from the waterproof BBOX/CBOX bodies.
- Use MCR rails / FLT-RCV side receiver area / lower-frame region as retrofit mounting references.
- Keep DRC/DRIVE gearboxes open enough for inspection, cleaning, and mud removal.
- Provide a first E-stop doghouse prototype so the emergency stop can be moved high and remain accessible.

## What this kit does NOT do

- It does not make the rover waterproof by itself.
- It does not replace real waterproof buttons, cable glands, gaskets, sealing, or water-intrusion sensors.
- It does not validate side-float clearance around tires/gearboxes.
- It does not authorize real paddy-field operation.

## First dry-fit order

1. Print one `PS-RV2271-SFS-CENTER-F` or `PS-RV2271-SFS-CENTER-R` only.
2. Place it over the printed v2.27 BBOX/CBOX lid area without fastening.
3. Confirm that it does not touch DRC/DRIVE gearboxes, tire sweep, or RCP/E-stop area.
4. Try `PS-RV2271-SFS-MCR-CLAMP-S` and `PS-RV2271-SFS-FLT-RCV-ADAPTER-S` as loose mockups.
5. Only after dry fit, print the second shell half and joiner straps.
6. Keep emergency stop visible and pushable at all times.

## Recommended material

- PETG for outdoor/water-season dry fit.
- PLA is acceptable for a shape check only.
- Do not rely on untreated FDM shells as watertight floats.

## Critical Paddy Swarm safety notes

- Do not drill into BBOX/CBOX during first retrofit testing.
- Do not mount the shell directly against the side gearboxes.
- Do not test in water with electronics installed.
- Use dummy weights for float/water trials.
- Add BBOX/CBOX water sensors and independent high-current cutoff before powered water trials.

"""
    (out / "README_v2271_sfs_g1.md").write_text(textwrap.dedent(readme).strip() + "\n", encoding="utf-8")


def export_parts(out: Path) -> None:
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
    ap.add_argument("--out", default="rover_v2271_sfs_out", help="output directory")
    ap.add_argument("--metadata-only", action="store_true", help="write manifests/docs only; do not require CadQuery")
    ap.add_argument("--make-zip", action="store_true", help="create ZIP after generation")
    return ap.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    out = Path(args.out).resolve()
    ensure_dirs(out)
    write_manifest(out)
    write_design_contract(out)
    write_readme(out)

    if not args.metadata_only:
        export_parts(out)

    if args.make_zip:
        zp = make_zip(out)
        print(f"ZIP: {zp}")
        print(f"SHA256: {sha256_file(zp)}")

    print(f"WROTE: {out}")
    if args.metadata_only:
        print("MODE: metadata-only; no STL/STEP generated")
    else:
        print("MODE: CAD exported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
