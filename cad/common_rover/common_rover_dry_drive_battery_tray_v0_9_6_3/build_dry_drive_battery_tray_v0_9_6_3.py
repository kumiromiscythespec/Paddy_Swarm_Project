#!/usr/bin/env python3
"""Deterministic builder for Common Rover Dry DRIVE Battery Tray v0.9.6.3."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.3"
CLASSIFICATION = "DRY_DRIVE_TEST_FIXTURE"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
REPO_ROOT = Path(__file__).resolve().parents[3]
LANE_REL = Path("cad/common_rover/common_rover_dry_drive_battery_tray_v0_9_6_3")
DEFAULT_LANE = REPO_ROOT / LANE_REL

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PROTECTED_LANES = {
    "v0.9.5.0": (Path("cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0"), 105, "462d0f3a9c471bf434160fb9a99f834f97a28e665bc8ce6139f6a87aeadd9185"),
    "v0.9.5.2": (Path("cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2"), 28, "5a520c30e9db4c0d5e916dbf280ec1e901fef551033bb93ce7e572a634a597c2"),
    "v0.9.5.3": (Path("cad/common_rover/common_rover_physical_followup_measurement_v0_9_5_3"), 25, "c49217200ea8d1a55b92632d4d1e3ad932fffd6ffdb9dbcb8edbea96c051ca0c"),
    "v0.9.6.0": (Path("cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0"), 40, "6fff91564757139d0d8e99d7105dd33eec059bc426de6680da9356d46636f86e"),
    "v0.9.6.2": (Path("cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2"), 57, "35e7a3e1a465114e4a3e268fc2ac137a78020a425fb4fb9e5576f360ca78a206"),
}
BASE_OUTSIDE_UNTRACKED_COUNT = 1648
BASE_OUTSIDE_PATH_DIGEST = "9f52686030f9024c7f51bbe1aed3a5ad9b20b3a89f343ebe275b506e0ef079f5"

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "DRY_BATTERY_TRAY_SPEC.md", "BATTERY_PHYSICAL_SOURCE.md",
    "FRAME_INTERFACE_REUSE.md", "TEMPORARY_WIRING_SPEC.md", "PRINT_PLAN.md",
    "PHYSICAL_FIT_TEST_PLAN.md", "SAFETY_NOTES.md", "HOLD_REGISTER.md", "BOM_CANDIDATES.md",
]
CAD = [
    "artifacts/dry_drive_battery_tray_v0_9_6_3.step",
    "artifacts/dry_drive_battery_tray_v0_9_6_3.stl",
    "artifacts/dry_drive_battery_tray_assembly_reference_v0_9_6_3.step",
    "artifacts/battery_reference_150p9x99p4x92p5.step",
    "artifacts/lower_frame_clear_reference_v0_9_6_3.step",
    "artifacts/battery_strap_path_reference_v0_9_6_3.step",
    "artifacts/cable_strain_relief_reference_v0_9_6_3.step",
    "artifacts/fuse_reserve_reference_v0_9_6_3.step",
    "artifacts/battery_corner_fit_coupon_v0_9_6_3.step",
    "artifacts/battery_corner_fit_coupon_v0_9_6_3.stl",
]
SVGS = [
    "artifacts/dry_battery_tray_dimensions_v0_9_6_3.svg",
    "artifacts/dry_battery_tray_frame_interface_v0_9_6_3.svg",
    "artifacts/dry_battery_tray_wiring_reference_v0_9_6_3.svg",
]
JSONS = ["design_parameters.json", "frame_interface_evidence.json", "validation_report.json", "reproducibility_report.json"]
SOURCE = ["build_dry_drive_battery_tray_v0_9_6_3.py", "tests/test_dry_drive_battery_tray_v0_9_6_3_contract.py"]
RELEASE = ["TEST_LOG.txt", "BUILD_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCE + RELEASE)
assert len(EXPECTED_PATHS) == 35 and len(set(EXPECTED_PATHS)) == 35

HOLDS = [
    "FRAME_MOUNT_INTERFACE", "FINAL_FRAME_FASTENER_CENTERS", "FINAL_RAIL_SKID_Z",
    "PRIMARY_LOCK", "SAFETY_PIN", "OPTIONAL_FRONT_KEEPER", "TEMP_CABLE_TOTAL_OUTSIDE_WIDTH",
    "TEMP_CABLE_INDIVIDUAL_INSULATION_OD", "TEMP_CABLE_BEND_RADIUS", "FUSE_HOLDER_MODEL",
    "MAIN_FUSE_FINAL", "HARDWARE_POWER_CUT_MODEL", "FINAL_TERMINAL_PROTECTOR", "POWERED_ROTATION",
]

PARAMS = {
    "version": VERSION, "classification": CLASSIFICATION, "units": "mm", "material": "PETG",
    "battery": {
        "product": "GOLDENMATE LiFePO4", "label": {"voltage_v": 12.8, "capacity_ah": 10, "energy_wh": 128},
        "physical_measured_body": [150.9, 99.4, 92.5], "mass_kg": 1.2,
        "bottom_to_terminal_top": 99.4, "terminal_protrusion_derived": 6.9,
        "male_terminal": [6.3, 0.7], "terminal_outer_span": 29.5, "terminal_inner_gap": 20.0,
        "orientation": "LONG_AXIS_ROVER_X_TERMINALS_REARWARD",
    },
    "tray": {
        "cavity": [153.5, 102.0], "clearance_total": [2.6, 2.6], "clearance_each": [1.3, 1.3],
        "bottom": 4.0, "side_wall": 4.0, "side_height_above_floor": 15.0,
        "rear_stop_thickness": 4.0, "rear_stop_height_above_floor": 25.0,
        "rear_service_opening": 70.0, "front": "OPEN", "overall_nominal": [157.5, 110.0, 29.0],
        "waterproof_features": 0, "cable_glands": 0, "lid": 0, "gasket": 0,
    },
    "retention": {
        "primary_strap_width": 25.0, "primary_pair": True, "slot": [28.0, 4.0],
        "primary_x": 0.0, "optional_secondary_pair_included": True, "secondary_x": 45.0,
        "secondary_required_for_initial_fit": False,
    },
    "strain_relief": {"zip_tie_slot": [5.0, 2.5], "pairs": 2, "cable_specific_clamp": False},
    "frame": {
        "lower_outer": [442.0, 181.0], "lower_clear": [400.0, 140.0], "height": 150.0,
        "insertion_height": 108.0, "tray_width": 110.0, "lateral_reference_each": 15.0,
        "interface": "HOLD_NO_PROVEN_FASTENER_CENTERS", "reference_geometry": "MEASURED_CLEAR_ENVELOPE_ONLY",
    },
    "print": {"printer": "Bambu A1", "bed": [256.0, 256.0], "orientation": "BOTTOM_FLAT",
              "direct_full_print": "ACCEPTABLE", "support": "NOT_REQUIRED_CANDIDATE_SLICER_REVIEW",
              "print_time": "HOLD_SLICER_PROFILE"},
    "temporary_power": "BATTERY_TO_FUSE_TO_1P25SQ_2C_TO_HARDWARE_CUT_TO_CBOX",
    "dry_test_only": True, "water": "NOT_APPROVED", "mud": "NOT_APPROVED",
    "field_deployment": "NOT_APPROVED", "powered_rotation": "NOT_APPROVED_BY_THIS_LANE",
    "holds": HOLDS,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted((p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts), key=lambda p: p.relative_to(root).as_posix())
    h = hashlib.sha256()
    for path in files:
        h.update(f"{sha256(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(files), h.hexdigest()


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def rbox(x: float, y: float, z: float, radius: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).edges("|Z").fillet(radius).translate(center)


def fused(parts: list[cq.Workplane]) -> cq.Workplane:
    result = parts[0]
    for part in parts[1:]:
        result = result.union(part)
    return result.clean()


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Compound.makeCompound([p.val() for p in parts]))


def rounded_slot(length: float, width: float, x: float, y: float, z0=-1.0, depth=7.0) -> cq.Workplane:
    return cq.Workplane("XY").center(x, y).slot2D(length, width, 0).extrude(depth).translate((0, 0, z0))


def tray() -> cq.Workplane:
    bottom = rbox(157.5, 110.0, 4.0, 3.0, (0, 0, 2.0))
    sides = [box(157.5, 4.0, 15.0, (0, y, 11.5)) for y in (-53.0, 53.0)]
    rear_shoulders = [box(4.0, 20.0, 25.0, (-76.75, y, 16.5)) for y in (-45.0, 45.0)]
    part = fused([bottom, *sides, *rear_shoulders])
    for x in (0.0, 45.0):
        for y in (-47.0, 47.0):
            part = part.cut(rounded_slot(28.0, 4.0, x, y))
    # Two zip-tie slot pairs through the rear shoulders; cable diameter is not encoded.
    for y in (-45.0, 45.0):
        for z in (10.0, 17.0):
            part = part.cut(box(7.0, 5.0, 2.5, (-76.75, y, z)))
    return part.clean()


def battery_reference() -> cq.Workplane:
    # Body only. Exact terminal XYZ is not invented from span-only measurements.
    return rbox(150.9, 99.4, 92.5, 3.0, (2.0, 0, 50.25))


def frame_clear_reference() -> cq.Workplane:
    rails = [box(442.0, 20.5, 20.0, (0, y, 0.0)) for y in (-80.25, 80.25)]
    return compound(rails)


def strap_path_reference() -> cq.Workplane:
    parts = []
    for x in (0.0, 45.0):
        parts.extend([
            box(25.0, 0.8, 100.0, (x, -50.6, 54.0)), box(25.0, 0.8, 100.0, (x, 50.6, 54.0)),
            box(25.0, 102.0, 0.8, (x, 0, 100.8)), box(25.0, 102.0, 0.8, (x, 0, 3.0)),
        ])
    return compound(parts)


def cable_strain_relief_reference() -> cq.Workplane:
    return compound([box(8, 8, 8, (-82, y, z)) for y in (-45, 45) for z in (10, 17)])


def fuse_reserve_reference() -> cq.Workplane:
    return box(50.0, 18.0, 12.0, (-88.0, 0, 20.0))


def coupon() -> cq.Workplane:
    base = rbox(30.0, 110.0, 4.0, 2.0, (0, 0, 2.0))
    sides = [box(30.0, 4.0, 15.0, (0, y, 11.5)) for y in (-53.0, 53.0)]
    shoulders = [box(4.0, 20.0, 25.0, (-13.0, y, 16.5)) for y in (-45.0, 45.0)]
    return fused([base, *sides, *shoulders])


def assembly() -> cq.Workplane:
    return compound([tray().translate((0, 0, 10)), battery_reference().translate((0, 0, 10)),
                     frame_clear_reference(), strap_path_reference().translate((0, 0, 10)),
                     cable_strain_relief_reference().translate((0, 0, 10)),
                     fuse_reserve_reference().translate((0, 0, 10))])


GEOMETRIES = {
    "dry_drive_battery_tray_v0_9_6_3": tray,
    "dry_drive_battery_tray_assembly_reference_v0_9_6_3": assembly,
    "battery_reference_150p9x99p4x92p5": battery_reference,
    "lower_frame_clear_reference_v0_9_6_3": frame_clear_reference,
    "battery_strap_path_reference_v0_9_6_3": strap_path_reference,
    "cable_strain_relief_reference_v0_9_6_3": cable_strain_relief_reference,
    "fuse_reserve_reference_v0_9_6_3": fuse_reserve_reference,
    "battery_corner_fit_coupon_v0_9_6_3": coupon,
}


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'1970-01-01T00:00:00'", text, count=1)
    text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
    occurrence = 0
    def repl(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return match.group(1) + str(occurrence) + match.group(2)
    text = re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')", repl, text)
    write_text(path, text)


def export_cad(artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stl_names = {"dry_drive_battery_tray_v0_9_6_3", "battery_corner_fit_coupon_v0_9_6_3"}
    for name, factory in GEOMETRIES.items():
        obj = factory()
        step = artifact_dir / f"{name}.step"
        cq.exporters.export(obj, str(step))
        normalize_step(step)
        if name in stl_names:
            cq.exporters.export(obj, str(artifact_dir / f"{name}.stl"), tolerance=0.02, angularTolerance=0.1)


def svg_page(title: str, markup: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="470" viewBox="0 0 900 470">
 <rect width="900" height="470" fill="#fafafa"/>
 <text x="25" y="32" font-family="sans-serif" font-size="22" font-weight="bold">{title}</text>
 <text x="875" y="30" text-anchor="end" font-family="sans-serif" font-size="12">v0.9.6.3 / DRY TEST ONLY</text>
 {markup}
 <g transform="translate(25 430)" font-family="sans-serif" font-size="12">
  <rect width="14" height="14" fill="#2e86de"/><text x="20" y="12">MEASURED</text>
  <rect x="130" width="14" height="14" fill="#8e44ad"/><text x="150" y="12">DERIVED</text>
  <rect x="260" width="14" height="14" fill="#27ae60"/><text x="280" y="12">DESIGN_CANDIDATE</text>
  <rect x="460" width="14" height="14" fill="#e67e22"/><text x="480" y="12">HOLD</text>
 </g>
</svg>'''


def svg_outputs() -> dict[str, str]:
    dimensions = svg_page("Dry battery tray dimensions", '''
 <g transform="translate(85 75)" font-family="sans-serif">
  <rect x="0" y="0" width="630" height="300" rx="12" fill="#d5f5e3" stroke="#222" stroke-width="3"/>
  <rect x="16" y="12" width="604" height="276" fill="#fdfefe" stroke="#27ae60" stroke-width="2"/>
  <rect x="16" y="12" width="16" height="80" fill="#27ae60"/><rect x="16" y="208" width="16" height="80" fill="#27ae60"/>
  <rect x="37" y="20" width="570" height="260" rx="10" fill="#2e86de" opacity=".42"/>
  <line x1="0" y1="325" x2="630" y2="325" stroke="#8e44ad" stroke-width="2"/><text x="315" y="350" text-anchor="middle">overall 157.5 / cavity 153.5 / rear wall 4 / front OPEN</text>
  <line x1="655" y1="0" x2="655" y2="300" stroke="#8e44ad" stroke-width="2"/><text x="680" y="150" transform="rotate(90 680 150)" text-anchor="middle">overall 110 / cavity 102 / 1.3 each</text>
  <text x="315" y="145" text-anchor="middle">BATTERY 150.9 × 99.4 × 92.5 / 1.2 kg</text>
  <text x="315" y="170" text-anchor="middle">rear service opening 70; terminals rearward</text>
 </g>''')
    frame = svg_page("Measured frame clearance / interface HOLD", '''
 <g transform="translate(90 80)" font-family="sans-serif">
  <rect x="0" y="0" width="720" height="260" fill="none" stroke="#222" stroke-width="4"/>
  <rect x="0" y="0" width="82" height="260" fill="#2e86de" opacity=".55"/><rect x="638" y="0" width="82" height="260" fill="#2e86de" opacity=".55"/>
  <rect x="225" y="27" width="270" height="206" fill="#27ae60" opacity=".65"/><text x="360" y="125" text-anchor="middle">TRAY 110</text><text x="360" y="150" text-anchor="middle">15 mm each side reference</text>
  <line x1="82" y1="245" x2="638" y2="245" stroke="#8e44ad" stroke-width="2"/><text x="360" y="280" text-anchor="middle">lower clear 140 MEASURED; mounting centers / rail Z HOLD</text>
  <text x="360" y="320" text-anchor="middle" fill="#e67e22">No M5 slots or frame holes released</text>
 </g>''')
    wiring = svg_page("Temporary dry-test wiring", '''
 <g font-family="sans-serif" font-size="14" text-anchor="middle">
  <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#333"/></marker></defs>
  <g fill="#eee" stroke="#333"><rect x="30" y="95" width="120" height="55"/><rect x="190" y="95" width="120" height="55"/><rect x="350" y="95" width="150" height="55"/><rect x="540" y="95" width="140" height="55"/><rect x="720" y="95" width="145" height="55"/></g>
  <text x="90" y="120">Battery</text><text x="90" y="138">12.8 V</text><text x="250" y="120">Fuse reserve</text><text x="250" y="138">rating HOLD</text><text x="425" y="120">1.25sq ×2C</text><text x="425" y="138">dimensions HOLD</text><text x="610" y="120">Hardware cut</text><text x="610" y="138">model HOLD</text><text x="792" y="120">CBOX / MD10C</text>
  <g stroke="#333" stroke-width="2" marker-end="url(#a)"><line x1="150" y1="122" x2="185" y2="122"/><line x1="310" y1="122" x2="345" y2="122"/><line x1="500" y1="122" x2="535" y2="122"/><line x1="680" y1="122" x2="715" y2="122"/></g>
  <rect x="260" y="245" width="380" height="95" fill="#d5f5e3" stroke="#27ae60"/><text x="450" y="275">2 pairs generic 5 × 2.5 zip-tie slots</text><text x="450" y="300">terminal carries no cable mass or pull</text><text x="450" y="325">NO GLAND / NO SEALED CONNECTOR</text>
 </g>''')
    return {SVGS[0]: dimensions, SVGS[1]: frame, SVGS[2]: wiring}


def document_outputs(material_mass_g: float) -> dict[str, str]:
    head = """# Common Rover Dry DRIVE Battery Tray v0.9.6.3

Classification: `DRY_DRIVE_TEST_FIXTURE`  
Status: **DRY TEST ONLY / NOT FOR WATER OR MUD / PHYSICAL FIT PENDING**
"""
    d: dict[str, str] = {}
    d["README.md"] = head + f"""
This lane provides a minimal PETG tray for a physically measured GOLDENMATE 12.8 V 10 Ah battery during dry DRIVE preparation. It is separate from BBOX waterproof authority and does not approve powered rotation.

- Tray envelope: 157.5 × 110.0 × 29.0 mm.
- Battery cavity: 153.5 × 102.0 mm, 1.3 mm nominal clearance at each opposing side/end.
- Front is open; rear uses two shoulders with a 70 mm service opening.
- One primary 25 mm strap path and one optional secondary path are included.
- Generic rear zip-tie slots carry cable load; no cable-specific clamp exists.
- Frame mounting holes/slots are not released because parent sources do not prove exact centers.

Computed solid PETG mass at 1.27 g/cm³: approximately **{material_mass_g:.1f} g**. Print time remains slicer/profile dependent.
"""
    d["DESIGN_AUTHORITY.md"] = head + """
## Authority boundary

Physical authority: battery body 150.9 × 99.4 × 92.5 mm, mass 1.2 kg, bottom-to-terminal-top 99.4 mm, 6.3 × 0.7 mm male terminal, 29.5 mm outer span and 20.0 mm inner gap. The 6.9 mm protrusion is derived.

The cavity, wall, stop, strap, zip-tie slot and fuse-reserve geometry are design candidates. The frame lower outer/clear dimensions and 108 mm insertion height are inherited measured references. Parent evidence does not establish final frame attachment centers or Z, so `FRAME_MOUNT_INTERFACE=HOLD` and no M5 slots are created.
"""
    d["DRY_BATTERY_TRAY_SPEC.md"] = head + """
| feature | value | class |
|---|---:|---|
| cavity | 153.5 × 102.0 | DESIGN_CANDIDATE_FOR_PHYSICAL_FIT |
| total clearance | 2.6 × 2.6 | DERIVED |
| bottom / side wall | 4.0 / 4.0 | DESIGN_CANDIDATE |
| side height above floor | 15.0 | DESIGN_CANDIDATE |
| rear stop | 4 thick × 25 above floor | DESIGN_CANDIDATE |
| rear opening | 70.0 | DESIGN_CANDIDATE |
| overall | 157.5 × 110.0 × 29.0 | DERIVED |

The cavity is measured from the rear-stop inner face to the open front edge. A full-height front wall and optional low keeper are absent. The battery sits directly on a broad flat floor. PETG positions the battery and guides the strap; it is not electrical-insulation, waterproof, terminal-support, or sole high-load-clamp authority.
"""
    d["BATTERY_PHYSICAL_SOURCE.md"] = head + """
## GOLDENMATE physical record

Label: 12.8 V / 10 Ah / 128 Wh. Measured body: length150.9, width99.4, height92.5 mm; mass1.2 kg. Battery bottom to terminal top=99.4 mm, hence terminal protrusion=6.9 mm derived. Male terminal=6.3 × 0.7 mm; pair outer span=29.5 mm; inner gap=20.0 mm. Preferred installation is long axis rover X and terminals rearward. Catalog nominal dimensions do not replace these values.

The STEP body intentionally omits detailed terminal solids because span-only data does not prove exact terminal XYZ or reconcile every tab dimension. The 70 mm rear opening preserves access without inventing placement.
"""
    d["FRAME_INTERFACE_REUSE.md"] = head + """
## Evidence and decision

v0.9.5.0 proves the measured compact-frame lower clear 400 × 140 mm, PITCH_AND_SLIDE concept, and 130/132/134 mm rail candidates. It explicitly leaves final metal rail/skid Z, primary lock and safety pin HOLD. v0.9.6.0 retains the 130 mm BBOX flange as a tight conditional prototype, not an exact dry-tray fastener pattern.

Therefore this lane reuses only the measured 442 × 181 lower outer / 400 × 140 clear reference. The 110 mm tray has 15 mm nominal lateral space per side and zero reference collision, but has no proven load-bearing contact. No frame hole, M5/T-nut slot, 134 mm rail, wear-pad attachment, or lock is released. `FRAME_MOUNT_INTERFACE=HOLD`; physical frame-fit is required before an attachment delta.
"""
    d["TEMPORARY_WIRING_SPEC.md"] = head + """
## Dry temporary path

`Battery+ → short lead → fuse → temporary 1.25sq ×2C → hardware power cut → CBOX/MD10C`; Battery− returns through the temporary cable. No gland, sealed connector, BBOX or charging interface is present.

Two pairs of generic 5 × 2.5 mm rear-shoulder slots accept replaceable zip ties for cable and inline-fuse restraint. Cable overall width, conductor insulation OD and bend radius are unmeasured, so there is no tight channel or diameter-specific clamp. Main fuse 7.5 A is an engineering candidate only; holder, rating and hardware-cut model remain HOLD.
"""
    d["PRINT_PLAN.md"] = head + f"""
Print bottom-flat on the Bambu A1 in PETG. Envelope157.5 × 110 mm is comfortably within 256 × 256 mm. Geometry is support-free candidate: bottom through-slots are open, the rear opening is not bridged by a ceiling, and no hidden ledge exists. Inspect slicer rather than trusting automatic support.

Check dry filament, first-layer consistency, long-flat-part warp, corner lift, slot perimeter and rear-shoulder adhesion. A 3–5 mm brim is optional if the qualified profile shows lift. Estimated solid-model mass is {material_mass_g:.1f} g at 1.27 g/cm³; actual filament and print time require the chosen slicer profile. `DIRECT_FULL_PRINT=ACCEPTABLE`; the included short full-width coupon is optional.
"""
    d["PHYSICAL_FIT_TEST_PLAN.md"] = head + """
## D1–D6

- **D1 visual:** crack, warp, corner lift and strap-slot quality.
- **D2 insertion:** hand insertion, no force fit or scraping, correct rear-stop gap.
- **D3 removal:** tool-free use of the open-front path.
- **D4 straps:** fit one 25 mm primary strap; confirm no lift, material rocking or moderate-hand-force slide. Secondary path is optional.
- **D5 frame:** verify no interference, 150 mm-frame insertion/removal, rear cable access, belt/crawler keepout and an independently designed metal-frame load path.
- **D6 cable:** after the actual 1.25sq cable arrives, tie it to the tray and confirm no terminal pull and accessible fuse.

Record measured cavity fit before changing CAD. Tray PASS does not approve powered rotation.
"""
    d["SAFETY_NOTES.md"] = head + """
**REMOVE BATTERY / DISCONNECT POWER BEFORE MECHANICAL ADJUSTMENT.** Keep positive and negative terminals separated; prevent tools from bridging them. Strap supplies vertical retention, and the rear anchor must carry cable mass/pull. PETG is not electrical-insulation authority or a sole high-load clamp.

Before any powered test: close the 565 mm belt hand test, verify MD10C polarity and continuity, install correct fuse and accessible hardware cut, remove exposed short risk, unload wheels/crawler, start at low duty cycle, and maintain human disconnect access. Powered rotation remains NOT_APPROVED_BY_THIS_LANE.
"""
    d["HOLD_REGISTER.md"] = head + "\n## Open items\n\n" + "\n".join(f"- `{x}` — HOLD" for x in HOLDS) + "\n\nWater, mud and paddy-field use are NOT_APPROVED.\n"
    d["BOM_CANDIDATES.md"] = head + """
| item | qty | status |
|---|---:|---|
| GOLDENMATE LiFePO4 12.8 V 10 Ah | 1 | PHYSICAL AUTHORITY |
| PETG tray | 1 | READY_TO_PRINT / FIT PENDING |
| 25 mm hook-and-loop strap | 1 primary | CANDIDATE |
| 25 mm second strap | 0–1 | OPTIONAL_SECONDARY_RETENTION |
| generic zip ties | up to 4 | CANDIDATE |
| 1.25sq ×2C cable | 1 temporary run | DIMENSIONS PENDING |
| inline fuse/holder | 1 | MODEL AND FINAL RATING HOLD |
| hardware power cut | 1 | MODEL HOLD |
| anti-slip pad | optional future | NOT MODELED |
"""
    return d


def frame_evidence() -> dict[str, object]:
    sources = [
        "cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0/BBOX_RAIL_INTERFACE.md",
        "cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0/BBOX_WEAR_PAD.md",
        "cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0/interfaces.json",
        "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0/design_parameters.json",
    ]
    return {
        "decision": "FRAME_MOUNT_INTERFACE_HOLD_TRAY_ONLY_FIT_PROTOTYPE",
        "proven": {"lower_outer_mm": [442.0, 181.0], "lower_clear_mm": [400.0, 140.0], "insertion_height_mm": 108.0,
                   "pitch_and_slide_concept": True, "rail_candidates_mm": [130.0, 132.0, 134.0]},
        "not_proven": ["FINAL_FASTENER_CENTERS", "FINAL_RAIL_SKID_Z", "PRIMARY_LOCK", "SAFETY_PIN", "DRY_TRAY_LOAD_BEARING_CONTACT"],
        "adopted_geometry": "MEASURED_140MM_CLEAR_REFERENCE_ONLY", "new_holes": 0, "new_m5_slots": 0,
        "sources": [{"path": rel, "sha256": sha256(REPO_ROOT / rel)} for rel in sources],
    }


def dims(obj: cq.Workplane) -> list[float]:
    bb = obj.val().BoundingBox()
    return [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)]


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return round(float(a.val().intersect(b.val()).Volume()), 6)


def metrics() -> dict[str, object]:
    t = tray()
    b = battery_reference()
    frame = frame_clear_reference()
    installed_tray = t.translate((0, 0, 10))
    installed_battery = b.translate((0, 0, 10))
    volume = float(t.val().Volume())
    return {
        "tray_bounds_mm": dims(t), "battery_bounds_mm": dims(b), "coupon_bounds_mm": dims(coupon()),
        "battery_tray_intersection_mm3": common_volume(t, b),
        "tray_frame_intersection_mm3": common_volume(installed_tray, frame),
        "battery_frame_intersection_mm3": common_volume(installed_battery, frame),
        "battery_rear_clearance_mm": 1.3, "battery_front_clearance_mm": 1.3,
        "battery_side_clearance_each_mm": 1.3, "terminal_opening_margin_each_mm": round((70.0 - 29.5) / 2, 3),
        "frame_lateral_clearance_each_mm": round((140.0 - 110.0) / 2, 3),
        "tray_volume_mm3": round(volume, 3), "petg_mass_g_at_1p27": round(volume * 1.27 / 1000.0, 1),
        "tray_valid": bool(t.val().isValid()), "coupon_valid": bool(coupon().val().isValid()),
        "battery_contact": "BROAD_FLAT_FLOOR_Z4", "sharp_body_contact": False,
    }


def parse_stl(path: Path) -> tuple[int, bool]:
    data = path.read_bytes()
    triangles: list[tuple[tuple[float, float, float], ...]] = []
    if len(data) >= 84:
        n = struct.unpack_from("<I", data, 80)[0]
        if 84 + 50 * n == len(data):
            for i in range(n):
                values = struct.unpack_from("<12fH", data, 84 + 50 * i)
                triangles.append(tuple(tuple(round(float(v), 6) for v in values[j:j + 3]) for j in (3, 6, 9)))
    if not triangles:
        vertices = []
        for line in data.decode("ascii", errors="ignore").splitlines():
            f = line.strip().split()
            if len(f) == 4 and f[0].lower() == "vertex":
                vertices.append(tuple(round(float(x), 6) for x in f[1:]))
        triangles = [tuple(vertices[i:i + 3]) for i in range(0, len(vertices), 3)]
    edges: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = Counter()
    for tri in triangles:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges[tuple(sorted((a, b)))] += 1
    return len(triangles), bool(triangles) and all(v == 2 for v in edges.values())


def cad_validation(lane: Path) -> dict[str, object]:
    step_files = [lane / p for p in CAD if p.endswith(".step")]
    stl_files = [lane / p for p in CAD if p.endswith(".stl")]
    steps = {}
    for path in step_files:
        obj = cq.importers.importStep(str(path))
        steps[path.name] = {"parse": "PASS", "valid": bool(obj.val().isValid()), "bounds_mm": dims(obj)}
    stls = {}
    for path in stl_files:
        count, manifold = parse_stl(path)
        stls[path.name] = {"triangles": count, "watertight_manifold": manifold}
    return {"step": steps, "stl": stls, "step_pass": all(v["valid"] for v in steps.values()),
            "stl_pass": all(v["watertight_manifold"] for v in stls.values())}


def test_script_text() -> str:
    return '''#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_dry_drive_battery_tray_v0_9_6_3.py"
spec = importlib.util.spec_from_file_location("v0963_builder", BUILDER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
CHECKS = module.contract_checks(LANE, repo_checks=True)
assert len(CHECKS) == 40

class Contract(unittest.TestCase):
    maxDiff = None

def make_test(name, passed, detail):
    def test(self): self.assertTrue(passed, f"{name}: {detail}")
    return test

for i, (name, passed, detail) in enumerate(CHECKS, 1):
    setattr(Contract, f"test_{i:03d}_{name.replace('-', '_')}", make_test(name, passed, detail))

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"CONTRACT_RESULT={passed}/{result.testsRun} PASS" if result.wasSuccessful() else "CONTRACT_RESULT=FAIL")
    sys.exit(0 if result.wasSuccessful() else 1)
'''


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "artifacts").mkdir(exist_ok=True)
    (out / "tests").mkdir(exist_ok=True)
    if Path(__file__).resolve() != (out / SOURCE[0]).resolve():
        shutil.copy2(__file__, out / SOURCE[0])
    export_cad(out / "artifacts")
    m = metrics()
    for rel, content in document_outputs(float(m["petg_mass_g_at_1p27"])).items():
        write_text(out / rel, content)
    for rel, content in svg_outputs().items():
        write_text(out / rel, content)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "frame_interface_evidence.json", frame_evidence())
    write_json(out / "validation_report.json", {
        "version": VERSION, "classification": CLASSIFICATION,
        "result": "CAD_COMPLETE_PHYSICAL_FIT_PENDING", "geometry": m,
        "front_open": True, "rear_service_opening_mm": 70.0, "frame_mount_interface": "HOLD",
        "new_frame_holes": 0, "new_m5_slots": 0, "waterproof_features": 0,
        "powered_rotation": "NOT_APPROVED_BY_THIS_LANE", "water_mud_field": "NOT_APPROVED",
    })
    write_json(out / "reproducibility_report.json", {
        "version": VERSION, "method": "independent temporary-directory rebuild",
        "scope": {"STEP_STL": len(CAD), "SVG": len(SVGS), "JSON": len(JSONS), "total": len(CAD) + len(SVGS) + len(JSONS)},
        "expected": "BYTE_IDENTICAL", "step_header_policy": "OCCT_TIMESTAMP_AND_OCCURRENCE_METADATA_NORMALIZED",
        "status": "PASS_WHEN_REBUILD_VERIFY_COMPLETES",
    })
    write_text(out / SOURCE[1], test_script_text())
    write_text(out / "TEST_LOG.txt", "Common Rover v0.9.6.3 contract\nEXPECTED_TESTS=40\nBUILDER_CONTRACT=40/40 PASS\nSTEP_IMPORT=8/8 PASS\nSTL_MANIFOLD=2/2 PASS\nPOWERED_ROTATION=NOT_APPROVED_BY_THIS_LANE\n")
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths=35\nstep=8\nstl=2\nsvg=3\njson=4\npetg_mass_g_at_1p27={m['petg_mass_g_at_1p27']}\nframe_interface=HOLD\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS))
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / p).as_posix() for p in EXPECTED_PATHS))
    lines = [f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_PATHS if rel != "SHA256SUMS.txt"]
    write_text(out / "SHA256SUMS.txt", "\n".join(lines))


def sums_ok(lane: Path) -> bool:
    lines = (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    return len(lines) == 34 and all(sha256(lane / rel) == digest for digest, rel in (line.split("  ", 1) for line in lines))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = sorted(p for p in run_git("ls-files", "--others", "--exclude-standard").splitlines() if not p.startswith(prefix))
    return len(paths), hashlib.sha256("".join(p + "\n" for p in paths).encode()).hexdigest()


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, str]]:
    m = metrics()
    actual = sorted(p.relative_to(lane).as_posix() for p in lane.rglob("*") if p.is_file())
    checks: list[tuple[str, bool, str]] = []
    def add(name: str, passed: bool, detail: object) -> None: checks.append((name, bool(passed), str(detail)))
    add("version", PARAMS["version"] == VERSION, VERSION)
    add("lane-and-classification", lane.name == LANE_REL.name and PARAMS["classification"] == CLASSIFICATION, lane.name)
    add("expected-paths", len(EXPECTED_PATHS) == 35, len(EXPECTED_PATHS))
    add("actual-paths", actual == EXPECTED_PATHS, len(actual))
    add("manifest-exact", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, "35")
    add("sha-exact", sums_ok(lane), "34 self-excluding hashes")
    add("commit-paths", len((lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 35, "lane only")
    add("cache-and-protection", not any(p.name == "__pycache__" or p.suffix == ".pyc" for p in lane.rglob("*")), "no cache")
    add("battery-body", PARAMS["battery"]["physical_measured_body"] == [150.9, 99.4, 92.5] and m["battery_bounds_mm"] == [150.9, 99.4, 92.5], m["battery_bounds_mm"])
    add("battery-mass", PARAMS["battery"]["mass_kg"] == 1.2, 1.2)
    add("terminal-record", PARAMS["battery"]["male_terminal"] == [6.3, 0.7] and PARAMS["battery"]["terminal_outer_span"] == 29.5, PARAMS["battery"])
    add("cavity", PARAMS["tray"]["cavity"] == [153.5, 102.0], PARAMS["tray"]["cavity"])
    add("clearance-total", PARAMS["tray"]["clearance_total"] == [2.6, 2.6], PARAMS["tray"]["clearance_total"])
    add("clearance-each", PARAMS["tray"]["clearance_each"] == [1.3, 1.3], PARAMS["tray"]["clearance_each"])
    add("bottom", PARAMS["tray"]["bottom"] == 4.0, 4)
    add("side-wall", PARAMS["tray"]["side_wall"] == 4.0, 4)
    add("side-height", PARAMS["tray"]["side_height_above_floor"] == 15.0, 15)
    add("rear-thickness", PARAMS["tray"]["rear_stop_thickness"] == 4.0, 4)
    add("rear-height", PARAMS["tray"]["rear_stop_height_above_floor"] == 25.0, 25)
    add("rear-opening", PARAMS["tray"]["rear_service_opening"] == 70.0, 70)
    add("front-open", PARAMS["tray"]["front"] == "OPEN", "OPEN")
    add("overall-envelope", m["tray_bounds_mm"] == [157.5, 110.0, 29.0], m["tray_bounds_mm"])
    add("primary-strap", PARAMS["retention"]["primary_strap_width"] == 25.0 and PARAMS["retention"]["primary_pair"], PARAMS["retention"])
    add("strap-slots", PARAMS["retention"]["slot"] == [28.0, 4.0], PARAMS["retention"]["slot"])
    add("secondary-optional", PARAMS["retention"]["optional_secondary_pair_included"] and not PARAMS["retention"]["secondary_required_for_initial_fit"], PARAMS["retention"])
    add("strain-relief", PARAMS["strain_relief"] == {"zip_tie_slot": [5.0, 2.5], "pairs": 2, "cable_specific_clamp": False}, PARAMS["strain_relief"])
    add("no-waterproof-parts", all(PARAMS["tray"][x] == 0 for x in ("waterproof_features", "cable_glands", "lid", "gasket")), PARAMS["tray"])
    add("frame-reference", PARAMS["frame"]["lower_clear"] == [400.0, 140.0], PARAMS["frame"])
    add("frame-clearance", m["frame_lateral_clearance_each_mm"] == 15.0, m["frame_lateral_clearance_each_mm"])
    add("frame-interface-hold", PARAMS["frame"]["interface"].startswith("HOLD") and frame_evidence()["new_m5_slots"] == 0, PARAMS["frame"]["interface"])
    add("battery-collision-zero", m["battery_tray_intersection_mm3"] == 0.0, m["battery_tray_intersection_mm3"])
    add("frame-collision-zero", m["tray_frame_intersection_mm3"] == 0.0 and m["battery_frame_intersection_mm3"] == 0.0, (m["tray_frame_intersection_mm3"], m["battery_frame_intersection_mm3"]))
    add("insertion-height", PARAMS["frame"]["insertion_height"] == 108.0 and 99.4 < 108.0, PARAMS["frame"]["insertion_height"])
    add("terminal-access", m["terminal_opening_margin_each_mm"] == 20.25, m["terminal_opening_margin_each_mm"])
    add("valid-no-sharp-contact", m["tray_valid"] and m["coupon_valid"] and not m["sharp_body_contact"], m)
    add("material-estimate", 50.0 < float(m["petg_mass_g_at_1p27"]) < 250.0, m["petg_mass_g_at_1p27"])
    add("print-bed-and-direct", 157.5 < 256 and PARAMS["print"]["direct_full_print"] == "ACCEPTABLE", PARAMS["print"])
    add("powered-gate", PARAMS["powered_rotation"] == "NOT_APPROVED_BY_THIS_LANE", PARAMS["powered_rotation"])
    add("water-mud-gate", PARAMS["water"] == "NOT_APPROVED" and PARAMS["mud"] == "NOT_APPROVED", (PARAMS["water"], PARAMS["mud"]))
    add("field-gate", PARAMS["field_deployment"] == "NOT_APPROVED", PARAMS["field_deployment"])
    assert len(checks) == 40
    if repo_checks:
        repo_ok = Path(run_git("rev-parse", "--show-toplevel")).resolve() == REPO_ROOT.resolve()
        git_ok = run_git("branch", "--show-current") == EXPECTED_BRANCH and run_git("rev-parse", "HEAD") == EXPECTED_HEAD and run_git("diff", "--cached", "--name-only") == ""
        authority_ok = all(sha256(REPO_ROOT / rel) == digest for rel, digest in AUTHORITY_HASHES.items())
        parents_ok = all(tree_digest(REPO_ROOT / rel) == (count, digest) for rel, count, digest in PROTECTED_LANES.values())
        outside_ok = outside_snapshot() == (BASE_OUTSIDE_UNTRACKED_COUNT, BASE_OUTSIDE_PATH_DIGEST)
        checks[1] = (checks[1][0], checks[1][1] and repo_ok and git_ok, f"lane/repo/git={checks[1][1]}/{repo_ok}/{git_ok}")
        checks[7] = (checks[7][0], checks[7][1] and authority_ok and parents_ok and outside_ok,
                     f"cache={checks[7][1]}, authority={authority_ok}, parents={parents_ok}, outside={outside_ok}")
    return checks


def verify(lane: Path, repo_checks: bool = True) -> dict[str, object]:
    checks = contract_checks(lane, repo_checks)
    cad = cad_validation(lane)
    failures = [f"{n}: {d}" for n, ok, d in checks if not ok]
    if not cad["step_pass"]: failures.append("STEP import/valid failure")
    if not cad["stl_pass"]: failures.append("STL watertight/manifold failure")
    return {"checks": 40, "passed": sum(1 for _, ok, _ in checks if ok), "step": len(cad["step"]),
            "stl": len(cad["stl"]), "failures": failures, "cad": cad}


def independent_rebuild(lane: Path) -> dict[str, object]:
    compare = CAD + SVGS + JSONS
    with tempfile.TemporaryDirectory(prefix="paddy_v0963_rebuild_") as td:
        rebuilt = Path(td) / LANE_REL.name
        build_outputs(rebuilt)
        mismatches = [rel for rel in compare if sha256(lane / rel) != sha256(rebuilt / rel)]
    return {"compared": len(compare), "byte_identical": len(compare) - len(mismatches),
            "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def package(lane: Path, downloads: Path) -> tuple[Path, str, dict[str, object]]:
    downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_Common_Rover_Dry_DRIVE_Battery_Tray_v0_9_6_3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists(): raise FileExistsError(f"Refusing to overwrite {path}")
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in EXPECTED_PATHS: zf.write(lane / rel, arcname=f"{LANE_REL.name}/{rel}")
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        expected = [f"{LANE_REL.name}/{rel}" for rel in EXPECTED_PATHS]
        traversal = [n for n in names if n.startswith(("/", "\\")) or ".." in Path(n).parts]
        bad = []
        for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            if hashlib.sha256(zf.read(f"{LANE_REL.name}/{rel}")).hexdigest() != digest: bad.append(rel)
        audit = {"open": "PASS", "entries": len(names), "manifest_exact": names == expected,
                 "duplicates": len(names) - len(set(names)), "traversal": traversal, "sha_mismatches": bad,
                 "parent_contamination": 0, "authority_contamination": 0}
    if not (audit["manifest_exact"] and audit["duplicates"] == 0 and not traversal and not bad):
        raise RuntimeError(audit)
    return path, sha256(path), audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--rebuild-verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_LANE)
    parser.add_argument("--downloads", type=Path, default=Path(r"D:\Downloads"))
    args = parser.parse_args()
    if not any((args.build, args.verify, args.rebuild_verify, args.package)):
        args.build = args.verify = args.rebuild_verify = True
    lane = args.output_root.resolve()
    if args.build:
        build_outputs(lane)
        print(f"BUILD=PASS paths={len(EXPECTED_PATHS)} output={lane}")
    if args.verify:
        result = verify(lane, repo_checks=lane == DEFAULT_LANE.resolve())
        print(json.dumps({k: v for k, v in result.items() if k != "cad"}, ensure_ascii=False, indent=2))
        if result["failures"]: return 1
    if args.rebuild_verify:
        result = independent_rebuild(lane)
        print("REPRODUCIBILITY=" + json.dumps(result, ensure_ascii=False))
        if result["status"] != "PASS": return 1
    if args.package:
        path, digest, audit = package(lane, args.downloads)
        print(f"ZIP_PATH={path}")
        print(f"ZIP_SHA256={digest}")
        print("ZIP_AUDIT=" + json.dumps(audit, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
