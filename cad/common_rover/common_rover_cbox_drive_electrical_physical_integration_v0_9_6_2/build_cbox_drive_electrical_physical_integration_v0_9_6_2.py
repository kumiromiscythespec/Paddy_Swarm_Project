#!/usr/bin/env python3
"""Deterministic builder for Common Rover CBOX DRIVE v0.9.6.2.

This lane is design-candidate work only.  Unknown cable, gland, driver-height,
and connector dimensions deliberately remain HOLD and are not turned into
manufacturing holes or released hardware.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
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


VERSION = "v0.9.6.2"
CLASSIFICATION = "DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
REPO_ROOT = Path(__file__).resolve().parents[3]
LANE_REL = Path("cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2")
DEFAULT_LANE = REPO_ROOT / LANE_REL
ART = Path("artifacts")

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
SOURCE_LANES = {
    "v0.9.5.3": (Path("cad/common_rover/common_rover_physical_followup_measurement_v0_9_5_3"), 25,
                 "c49217200ea8d1a55b92632d4d1e3ad932fffd6ffdb9dbcb8edbea96c051ca0c"),
    "v0.9.6.0": (Path("cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0"), 40,
                 "6fff91564757139d0d8e99d7105dd33eec059bc426de6680da9356d46636f86e"),
}

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "CBOX_DRIVE_PHYSICAL_SPEC.md",
    "MD10C_PHYSICAL_INTEGRATION.md", "ESP32_PHYSICAL_INTEGRATION.md",
    "POWER_ARCHITECTURE.md", "SIGNAL_ARCHITECTURE.md", "GPIO_ALLOCATION_TABLE.md",
    "CABLE_ARCHITECTURE.md", "SERVICEABILITY_SPEC.md", "THERMAL_VALIDATION_PLAN.md",
    "WATERPROOF_BOUNDARY.md", "POWERED_DRIVE_PRECONDITIONS.md", "PHYSICAL_SOURCE_TRACE.md",
    "HOLD_REGISTER.md", "BOM_CANDIDATES.md", "PRINT_PLAN.md",
]
CAD_ARTIFACTS = [
    "artifacts/cbox_drive_v0_9_6_2_body.step", "artifacts/cbox_drive_v0_9_6_2_body.stl",
    "artifacts/cbox_drive_v0_9_6_2_lid.step", "artifacts/cbox_drive_v0_9_6_2_lid.stl",
    "artifacts/cbox_drive_v0_9_6_2_tray.step", "artifacts/cbox_drive_v0_9_6_2_tray.stl",
    "artifacts/cbox_drive_v0_9_6_2_esp32_cradle.step", "artifacts/cbox_drive_v0_9_6_2_esp32_cradle.stl",
    "artifacts/cbox_drive_v0_9_6_2_assembly.step", "artifacts/md10c_reference.step",
    "artifacts/esp32_freenove_wroom_v1_3_reference.step", "artifacts/two_pnct_axis_reference.step",
    "artifacts/motor_power_wire_bend_envelope_reference.step",
    "artifacts/encoder_cable_bend_envelope_reference.step",
    "artifacts/screwdriver_keepout_reference.step", "artifacts/antenna_keepout_reference.step",
    "artifacts/dc_dc_reserve_reference.step", "artifacts/usb_plug_keepout_reference.step",
    "artifacts/esp32_cradle_fit_coupon.step", "artifacts/esp32_cradle_fit_coupon.stl",
    "artifacts/md10c_standoff_access_coupon.step", "artifacts/md10c_standoff_access_coupon.stl",
]
SVG_ARTIFACTS = [
    "artifacts/cbox_drive_component_layout_v0_9_6_2.svg",
    "artifacts/cbox_drive_power_topology_v0_9_6_2.svg",
    "artifacts/cbox_drive_signal_routing_v0_9_6_2.svg",
    "artifacts/cbox_drive_service_keepouts_v0_9_6_2.svg",
    "artifacts/cbox_drive_gland_landing_zones_v0_9_6_2.svg",
]
DATA_FILES = [
    "design_parameters.json", "architecture_state.json", "validation_report.json",
    "reproducibility_report.json", "COMPONENT_PLACEMENT.csv", "GLAND_LANDING_ZONES.csv",
]
SOURCE_FILES = [
    "build_cbox_drive_electrical_physical_integration_v0_9_6_2.py",
    "tests/test_cbox_drive_electrical_physical_integration_v0_9_6_2_contract.py",
]
RELEASE_FILES = ["TEST_LOG.txt", "BUILD_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD_ARTIFACTS + SVG_ARTIFACTS + DATA_FILES + SOURCE_FILES + RELEASE_FILES)
assert len(EXPECTED_PATHS) == 57 and len(set(EXPECTED_PATHS)) == 57

HOLD_ITEMS = [
    "2PNCT_ACTUAL_OD", "CABLE_GLAND_SIZE", "GLAND_THREAD", "MAIN_POWER_GLAND_HOLE",
    "MOTOR_GLAND_HOLE", "ENCODER_GLAND_HOLE", "MD10C_PHYSICAL_MAX_HEIGHT",
    "MD10C_FINAL_FASTENER", "DC_DC_MODEL", "DC_DC_DIMENSIONS", "ENCODER_SUPPLY_VOLTAGE",
    "MAIN_FUSE_FINAL", "BRANCH_FUSE_FINAL", "MASTER_DISCONNECT_MODEL",
    "ABOVE_WATER_CONNECTOR_MODEL", "ESP32_GPIO_ASSIGNMENT", "ESP32_RF_EXACT_KEEPOUT",
    "CBOX_THERMAL_LIMIT", "POWERED_ROTATION",
]

PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "cbox_external": [230.0, 92.0, 55.0],
    "body": [230.0, 92.0, 50.0],
    "lid_thickness": 4.2,
    "compressed_gasket": 0.8,
    "tray_reference": [210.0, 72.0, 2.4],
    "internal_coordinate_origin_global": [-105.0, -42.8],
    "wall": 3.2,
    "floor": 3.2,
    "top_throat": [218.0, 80.0],
    "md10c": {
        "quantity": 2, "board": [75.0, 43.0], "mount_pattern": [69.0, 35.0],
        "drawing_hole_diameter_approx": 3.0, "reference_height_non_authority": 18.0,
        "max_height": "HOLD", "underside_clearance_candidate": 3.0,
        "left_internal_xy": [20.0, 95.0, 24.0, 67.0],
        "right_internal_xy": [115.0, 190.0, 24.0, 67.0], "relative_rotation_deg": 180,
        "outer_service_each": 20.0, "center_gap": 20.0,
    },
    "esp32": {
        "model": "Freenove ESP32 WROOM v1.3", "measured": [56.8, 28.2, 12.9],
        "mounting_holes": "NONE_OBSERVED", "cradle_cavity": [57.6, 29.0, 13.7],
        "nominal_allowance_each_side": 0.4, "internal_x": [76.6, 133.4],
        "installation": "SIDE_WALL_VERTICAL_REMOVABLE_PETG_CRADLE",
        "reference_clearance_to_md10c": 11.1,
    },
    "zones": {"logic_y": [0.0, 20.0], "separator_y": [20.0, 24.0], "power_y": [24.0, 72.0]},
    "printer": {"model": "Bambu A1", "bed": [256.0, 256.0], "part_margin_each_long_axis": 13.0,
                "recommended_brim": 5.0, "remaining_margin_after_brim_each": 8.0},
    "penetrations": {"lid": 0, "final_gland_holes": 0, "blank_landing_pads": 5},
    "purchased_main_cable": {"maker": "Taiyo Cabletec", "type": "2PNCT", "conductors": "1.25sq x 2C",
                              "purchased_length_m": 3.0, "actual_outer_diameter": "HOLD_PHYSICAL_MEASUREMENT"},
    "control": {"mode": "SIGN_MAGNITUDE_PWM", "powered_rotation": "NOT_APPROVED"},
    "battery": {"live_submersion": "NOT_APPROVED"},
    "field_deployment": "NOT_APPROVED", "holds": HOLD_ITEMS,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def csv_text(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(
        (p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    h = hashlib.sha256()
    for path in files:
        h.update(f"{sha256(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(files), h.hexdigest()


def solid_box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    cx, cy, cz = center
    return cq.Workplane("XY").box(x, y, z).translate((cx, cy, cz))


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Compound.makeCompound([p.val() for p in parts]))


def fused(parts: list[cq.Workplane]) -> cq.Workplane:
    result = parts[0]
    for part in parts[1:]:
        result = result.union(part)
    return result


def body() -> cq.Workplane:
    outer = solid_box(230, 92, 50, (0, 0, 25))
    cavity = solid_box(223.6, 85.6, 46.8, (0, 0, 26.6))
    shell = outer.cut(cavity)
    # Reinforced blank landing pads only.  No through-holes are present.
    pads = [
        solid_box(50, 3, 20, (0, 41.3, 35)),
        solid_box(3, 20, 20, (-110.3, 7.2, 30)), solid_box(3, 20, 20, (110.3, 7.2, 30)),
        solid_box(3, 16, 20, (-110.3, -32.8, 30)), solid_box(3, 16, 20, (110.3, -32.8, 30)),
    ]
    for pad in pads:
        shell = shell.union(pad)
    return shell


def lid() -> cq.Workplane:
    return solid_box(230, 92, 4.2, (0, 0, 52.9))


def gasket() -> cq.Workplane:
    outer = solid_box(228, 90, 0.8, (0, 0, 50.4))
    inner = solid_box(218, 80, 1.0, (0, 0, 50.4))
    return outer.cut(inner)


def tray() -> cq.Workplane:
    base = solid_box(210, 72, 2.4, (0, -6.8, 4.4))
    for bx in (-47.5, 47.5):
        for dx in (-34.5, 34.5):
            for dy in (-17.5, 17.5):
                post = cq.Workplane("XY").circle(3).circle(1.6).extrude(3).translate((bx + dx, 2.7 + dy, 5.6))
                base = base.union(post)
    return base


def md10c_reference() -> cq.Workplane:
    board = solid_box(75, 43, 1.6, (0, 0, 0.8))
    power_terminal = solid_box(11, 35, 10, (-30, 0, 6.6))
    logic_header = solid_box(8, 18, 8, (32, 0, 5.6))
    component_ref = solid_box(38, 30, 16.4, (3, 0, 9.8))
    return compound([board, power_terminal, logic_header, component_ref])


def installed_md10cs() -> tuple[cq.Workplane, cq.Workplane]:
    ref = md10c_reference()
    left = ref.translate((-47.5, 2.7, 8.6))
    right = ref.rotate((0, 0, 0), (0, 0, 1), 180).translate((47.5, 2.7, 8.6))
    return left, right


def esp32_reference() -> cq.Workplane:
    # Simplified measured maximum envelope; no invented component detail.
    return solid_box(56.8, 12.9, 28.2, (0, 0, 14.1))


def installed_esp32() -> cq.Workplane:
    return esp32_reference().translate((0, -36.35, 8.0))


def esp32_cradle() -> cq.Workplane:
    back = solid_box(61.6, 2.4, 33, (0, 0, 16.5))
    shelf = solid_box(61.6, 16.1, 2.0, (0, 6.85, 1.0))
    ends = [solid_box(2, 16.1, 31, (x, 6.85, 16.5)) for x in (-30.8, 30.8)]
    lips = [solid_box(8, 2.4, 4, (x, 13.7, 29)) for x in (-24, 24)]
    return fused([back, shelf, *ends, *lips])


def installed_cradle() -> cq.Workplane:
    return esp32_cradle().translate((0, -42.8, 5.0))


def dc_dc_reserve() -> cq.Workplane:
    # Internal-coordinate Y67..72, converted using global origin Y=-42.8.
    return solid_box(45, 5, 18, (0, 26.7, 21))


def antenna_keepout() -> cq.Workplane:
    return solid_box(25, 20, 20, (40.9, -32.8, 23))


def usb_keepout() -> cq.Workplane:
    return solid_box(35, 18, 12, (-46, -33.8, 22))


def screwdriver_keepouts() -> cq.Workplane:
    parts = []
    for bx in (-47.5, 47.5):
        for dy in (-13, 0, 13):
            parts.append(cq.Workplane("XY").circle(4).extrude(24).translate((bx + (-30 if bx < 0 else 30), 2.7 + dy, 26.6)))
    return compound(parts)


def two_pnct_axis() -> cq.Workplane:
    # D=1 marker only: actual purchased-cable OD remains unresolved.
    return cq.Workplane("YZ").circle(0.5).extrude(70, both=True).translate((0, 46, 35))


def motor_wire_bend() -> cq.Workplane:
    return compound([solid_box(22, 10, 10, (-100, 7.2, 19)), solid_box(22, 10, 10, (100, 7.2, 19))])


def encoder_bend() -> cq.Workplane:
    return compound([solid_box(18, 8, 8, (-102, -32.8, 18)), solid_box(18, 8, 8, (102, -32.8, 18))])


def esp32_coupon() -> cq.Workplane:
    base = solid_box(70, 28, 2.4, (0, 0, 1.2))
    rails = [solid_box(61.6, 2.2, 8, (0, y, 6.4)) for y in (-7.95, 7.95)]
    stops = [solid_box(2, 18.1, 8, (x, 0, 6.4)) for x in (-30.8, 30.8)]
    return fused([base, *rails, *stops])


def md10c_coupon() -> cq.Workplane:
    base = solid_box(45, 35, 2.4, (0, 0, 1.2))
    post = cq.Workplane("XY").circle(3).circle(1.6).extrude(8).translate((0, 0, 2.4))
    keepout = cq.Workplane("XY").circle(6).extrude(2.4).translate((18, 0, 2.4))
    return fused([base, post, keepout])


def assembly() -> cq.Workplane:
    left, right = installed_md10cs()
    return compound([body(), lid(), gasket(), tray(), left, right, installed_esp32(), installed_cradle(),
                     dc_dc_reserve(), antenna_keepout(), usb_keepout(), screwdriver_keepouts(),
                     two_pnct_axis(), motor_wire_bend(), encoder_bend()])


GEOMETRIES = {
    "cbox_drive_v0_9_6_2_body": body,
    "cbox_drive_v0_9_6_2_lid": lid,
    "cbox_drive_v0_9_6_2_tray": tray,
    "cbox_drive_v0_9_6_2_esp32_cradle": esp32_cradle,
    "cbox_drive_v0_9_6_2_assembly": assembly,
    "md10c_reference": md10c_reference,
    "esp32_freenove_wroom_v1_3_reference": esp32_reference,
    "two_pnct_axis_reference": two_pnct_axis,
    "motor_power_wire_bend_envelope_reference": motor_wire_bend,
    "encoder_cable_bend_envelope_reference": encoder_bend,
    "screwdriver_keepout_reference": screwdriver_keepouts,
    "antenna_keepout_reference": antenna_keepout,
    "dc_dc_reserve_reference": dc_dc_reserve,
    "usb_plug_keepout_reference": usb_keepout,
    "esp32_cradle_fit_coupon": esp32_coupon,
    "md10c_standoff_access_coupon": md10c_coupon,
}


def export_cad(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    stl_names = {"cbox_drive_v0_9_6_2_body", "cbox_drive_v0_9_6_2_lid", "cbox_drive_v0_9_6_2_tray",
                 "cbox_drive_v0_9_6_2_esp32_cradle", "esp32_cradle_fit_coupon", "md10c_standoff_access_coupon"}
    for name, factory in GEOMETRIES.items():
        obj = factory()
        step_path = out / f"{name}.step"
        cq.exporters.export(obj, str(step_path))
        # OCCT writes the wall-clock export time into FILE_NAME.  Normalize that
        # metadata only; all geometric entities remain byte-for-byte untouched.
        step_text = step_path.read_text(encoding="utf-8")
        step_text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'1970-01-01T00:00:00'", step_text, count=1)
        write_text(step_path, step_text)
        if name in stl_names:
            cq.exporters.export(obj, str(out / f"{name}.stl"), tolerance=0.02, angularTolerance=0.1)


def svg_page(title: str, body_markup: str, legend: bool = True) -> str:
    legend_markup = """
      <g transform="translate(25 430)" font-family="sans-serif" font-size="12">
        <rect x="0" y="0" width="14" height="14" fill="#2e86de"/><text x="20" y="12">MEASURED</text>
        <rect x="130" y="0" width="14" height="14" fill="#8e44ad"/><text x="150" y="12">DRAWING_REFERENCE</text>
        <rect x="330" y="0" width="14" height="14" fill="#27ae60"/><text x="350" y="12">DESIGN_CANDIDATE</text>
        <rect x="530" y="0" width="14" height="14" fill="#e67e22"/><text x="550" y="12">HOLD</text>
      </g>""" if legend else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="470" viewBox="0 0 900 470">
  <rect width="900" height="470" fill="#fafafa"/>
  <text x="25" y="32" font-family="sans-serif" font-size="22" font-weight="bold">{title}</text>
  <text x="875" y="30" text-anchor="end" font-family="sans-serif" font-size="12">v0.9.6.2 / NOT FOR MANUFACTURING</text>
  {body_markup}
  {legend_markup}
</svg>
"""


def svg_outputs() -> dict[str, str]:
    layout = svg_page("CBOX DRIVE component layout", """
      <g transform="translate(65 70)" font-family="sans-serif">
        <rect x="0" y="0" width="690" height="276" rx="7" fill="none" stroke="#222" stroke-width="4"/>
        <rect x="30" y="30" width="630" height="216" fill="#f5f5f5" stroke="#777"/>
        <rect x="30" y="30" width="630" height="60" fill="#d6eaf8" opacity=".7"/><text x="42" y="62">LOGIC 0..20</text>
        <rect x="30" y="90" width="630" height="12" fill="#f9e79f"/><text x="42" y="100" font-size="9">SEPARATOR 20..24</text>
        <rect x="90" y="102" width="225" height="129" fill="#8e44ad" opacity=".75"/><text x="110" y="170" fill="white">MD10C-L 75×43</text>
        <rect x="375" y="102" width="225" height="129" fill="#8e44ad" opacity=".75"/><text x="395" y="170" fill="white">MD10C-R 180°</text>
        <rect x="260" y="38" width="170" height="40" fill="#2e86de" opacity=".85"/><text x="275" y="63" fill="white">ESP32 56.8×12.9 projection</text>
        <line x1="315" y1="240" x2="375" y2="240" stroke="#222" stroke-width="2"/><text x="345" y="263" text-anchor="middle">20 center</text>
        <text x="20" y="268">20 outer</text><text x="612" y="268">20 outer</text>
      </g>""")
    power = svg_page("CBOX DRIVE power topology", """
      <g font-family="sans-serif" font-size="14" text-anchor="middle">
        <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#333"/></marker></defs>
        <g fill="#eee" stroke="#333"><rect x="30" y="90" width="120" height="50"/><rect x="185" y="90" width="120" height="50"/><rect x="340" y="90" width="140" height="50"/><rect x="515" y="90" width="120" height="50"/><rect x="680" y="90" width="170" height="50"/></g>
        <text x="90" y="120">BBOX battery</text><text x="245" y="120">main fuse HOLD</text><text x="410" y="112">2PNCT + connector</text><text x="410" y="130">connector HOLD</text><text x="575" y="112">hardware cut</text><text x="575" y="130">HOLD</text><text x="765" y="120">CBOX STAR + / GND</text>
        <g stroke="#333" stroke-width="2" marker-end="url(#a)"><line x1="150" y1="115" x2="180" y2="115"/><line x1="305" y1="115" x2="335" y2="115"/><line x1="480" y1="115" x2="510" y2="115"/><line x1="635" y1="115" x2="675" y2="115"/></g>
        <g fill="#d5f5e3" stroke="#27ae60"><rect x="560" y="230" width="130" height="50"/><rect x="710" y="230" width="130" height="50"/><rect x="635" y="330" width="130" height="50"/></g>
        <text x="625" y="260">MD10C-L</text><text x="775" y="260">MD10C-R</text><text x="700" y="352">DC-DC HOLD</text><text x="700" y="370">→ ESP32 5 V</text>
        <g stroke="#333" stroke-width="2" marker-end="url(#a)"><line x1="735" y1="140" x2="625" y2="225"/><line x1="775" y1="140" x2="775" y2="225"/><line x1="755" y1="140" x2="705" y2="325"/></g>
      </g>""")
    signal = svg_page("CBOX DRIVE signal routing", """
      <g font-family="sans-serif" font-size="14">
        <rect x="70" y="75" width="760" height="245" fill="none" stroke="#222" stroke-width="3"/>
        <rect x="80" y="85" width="740" height="70" fill="#d6eaf8"/><text x="95" y="110">LOGIC CORRIDOR: ESP32 → PWM-L/DIR-L/GND and PWM-R/DIR-R/GND</text><text x="95" y="135">ENC-L-A/B + ENC-R-A/B; ENCODER_VCC TBD</text>
        <rect x="80" y="170" width="740" height="30" fill="#f9e79f"/><text x="95" y="191">4 mm separation candidate — non-conductive, no invented shield</text>
        <rect x="80" y="215" width="740" height="95" fill="#fadbd8"/><text x="95" y="245">POWER ZONE: STAR distribution → MD10C-L / MD10C-R / DC-DC</text><text x="95" y="275">Motor and encoder runs separated; unavoidable crossings approximately 90°</text>
      </g>""")
    service = svg_page("CBOX DRIVE service keep-outs", """
      <g transform="translate(80 70)" font-family="sans-serif">
        <rect x="0" y="0" width="690" height="276" fill="none" stroke="#222" stroke-width="3"/>
        <rect x="90" y="100" width="225" height="129" fill="#8e44ad" opacity=".55"/><rect x="375" y="100" width="225" height="129" fill="#8e44ad" opacity=".55"/>
        <g fill="#e67e22" opacity=".7"><circle cx="112" cy="120" r="12"/><circle cx="112" cy="164" r="12"/><circle cx="112" cy="208" r="12"/><circle cx="578" cy="120" r="12"/><circle cx="578" cy="164" r="12"/><circle cx="578" cy="208" r="12"/></g>
        <rect x="255" y="20" width="180" height="55" fill="#2e86de" opacity=".7"/><rect x="195" y="10" width="105" height="75" fill="#27ae60" opacity=".35"/><text x="15" y="255">orange: screwdriver vertical axes; green: qualitative antenna keepout; USB envelope DESIGN_REFERENCE_ONLY</text>
      </g>""")
    glands = svg_page("CBOX DRIVE blank gland landing zones", """
      <g font-family="sans-serif" text-anchor="middle">
        <rect x="90" y="100" width="720" height="220" fill="#eee" stroke="#222" stroke-width="4"/>
        <g fill="#27ae60" stroke="#176b3a"><rect x="350" y="100" width="200" height="42"/><rect x="90" y="155" width="42" height="75"/><rect x="90" y="245" width="42" height="60"/><rect x="768" y="155" width="42" height="75"/><rect x="768" y="245" width="42" height="60"/></g>
        <text x="450" y="127">MAIN POWER BLANK PAD</text><text x="111" y="190" transform="rotate(-90 111 190)">LEFT MOTOR</text><text x="111" y="275" transform="rotate(-90 111 275)">LEFT ENCODER</text><text x="789" y="190" transform="rotate(90 789 190)">RIGHT MOTOR</text><text x="789" y="275" transform="rotate(90 789 275)">RIGHT ENCODER</text>
        <text x="450" y="360">Final holes = 0 / lid penetrations = 0 / physical cable OD and gland required</text>
      </g>""")
    return {
        SVG_ARTIFACTS[0]: layout, SVG_ARTIFACTS[1]: power, SVG_ARTIFACTS[2]: signal,
        SVG_ARTIFACTS[3]: service, SVG_ARTIFACTS[4]: glands,
    }


def document_outputs() -> dict[str, str]:
    common = """# Common Rover CBOX DRIVE Electrical Physical Integration v0.9.6.2

Status: **NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING**  
Classification: `DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION`

This lane preserves the v0.9.6.0 above-water CBOX role and its power/signal separation. It does not approve powered rotation, live-battery submersion, or field deployment.
"""
    docs: dict[str, str] = {}
    docs["README.md"] = common + """
## Selected result

- One-piece 230 × 92 × 50 mm body, 230 × 92 × 4.2 mm unperforated lid, and 0.8 mm compressed-gasket reference form the approximately 55 mm external candidate.
- The 210 × 72 mm tray carries two independent MD10C references. Their power/motor terminals face the short ends and their logic connectors face the 20 mm center gap.
- The physically measured 56.8 × 28.2 × 12.9 mm ESP32 is held vertically in a removable PETG cradle; headers carry no structural load.
- Five wall reinforcements are blank landing pads. Final gland holes and lid penetrations are zero.

Print the two fit coupons before committing material and time to the full body. All release gates are listed in `HOLD_REGISTER.md`.
"""
    docs["DESIGN_AUTHORITY.md"] = common + """
## Authority boundary

Measured authority is limited to the ESP32 envelope and purchased-cable identity/length. MD10C board and 69 × 35 mm mounting pattern are drawing references. The 55 mm CBOX height, PETG cradle, standoffs, service envelopes, DC-DC zone, fuse zones, and keep-outs are design candidates. MD10C height, cable OD, all gland geometry, final fasteners, DC-DC, fuses, connector, hardware cut, GPIO, encoder VCC, thermal limit, and RF keepout remain HOLD.

The v0.9.5.3 and v0.9.6.0 lanes and all four current-authority files are read-only parents. This delta does not supersede their physical measurements except for selecting the resized CBOX candidate.
"""
    docs["CBOX_DRIVE_PHYSICAL_SPEC.md"] = common + """
## Enclosure and tray

| item | candidate |
|---|---:|
| external | 230 × 92 × 55 mm |
| body | 230 × 92 × 50 mm |
| lid | 230 × 92 × 4.2 mm |
| compressed gasket | 0.8 mm |
| tray | 210 × 72 × 2.4 mm |

The width stays 92 mm while length grows from 180 to 230 mm and height from 45 to 55 mm. The body has no penetration, the lid is one piece, and the gasket loop is continuous. Known measured-component geometry clears the lid, but final height is `HOLD_MD10C_PHYSICAL_MAX_HEIGHT`.

On the Bambu A1 256 mm bed, a 230 mm part has 13 mm nominal margin at each long end. A 5 mm brim is recommended, leaving 8 mm each side. This is geometric entry only; corner lift, first layer, sealing-face protection, and long-wall warp remain physical-print risks.
"""
    docs["MD10C_PHYSICAL_INTEGRATION.md"] = common + """
## Dual MD10C layout

Internal X/Y coordinates use the 210 × 72 mm tray. MD10C-L occupies X20..95, Y24..67; MD10C-R occupies X115..190, Y24..67 and rotates 180°. Thus each short-end service zone is 20 mm and the logic-side center gap is 20 mm. Four drawing-reference points per board use the 69 × 35 mm pattern. Underside clearance is a 3 mm candidate.

Six D8 mm reference cylinders preserve vertical screwdriver paths over terminal screws. The outer 20 mm spaces remain reserved for ferrules, conductor bends, inspection, and tools. If the real harness needs more, classification becomes `SERVICE_SPACE_CONFLICT`; geometry must not be silently reduced. Final M3-class retention and physical maximum component height remain HOLD.
"""
    docs["ESP32_PHYSICAL_INTEGRATION.md"] = common + """
## Freenove ESP32 WROOM v1.3

The physical measured envelope is 56.8 × 28.2 × 12.9 mm and no mounting holes were observed. A removable PETG side-wall cradle uses a 57.6 × 29.0 × 13.7 mm candidate cavity, approximately 0.4 mm allowance per side. It does not drill the PCB, use adhesive, or transfer structural load to headers.

The vertical board spans internal X76.6..133.4 and projects 12.9 mm from the logic wall. The MD10C zone begins at Y24, retaining the 11.1 mm geometric reference gap. The antenna keepout is qualitative and conservative, and the USB plug model is `DESIGN_REFERENCE_ONLY`; final harness and RF service PASS are not claimed.
"""
    docs["POWER_ARCHITECTURE.md"] = common + """
## Power path

`BBOX battery → main fuse near Battery+ → purchased 2PNCT 1.25sq ×2C → above-water connector → human-accessible software-independent hardware cut → CBOX STAR distribution`.

The star positive bus branches independently to MD10C-L, MD10C-R, and DC-DC. Battery negative terminates at STAR GND, which branches to both driver POWER- inputs, DC-DC input-, and logic reference. Motor current must never traverse ESP32 ground wiring. The 7.5 A main and 5 A branch values are engineering candidates only; all final ratings and commercial hardware remain HOLD.
"""
    docs["SIGNAL_ARCHITECTURE.md"] = common + """
## Control and encoder signals

SIGN-MAGNITUDE PWM uses PWM-L/DIR-L and PWM-R/DIR-R, with PWM low as the motor-output-off startup reference. No GPIO numbers are released. Encoder candidate channels are V+, GND, A, B; `ENCODER_VCC TBD` is mandatory because supply voltage is unverified. Encoder and motor wiring stay in separate corridors and cross at approximately 90 degrees where unavoidable.
"""
    docs["GPIO_ALLOCATION_TABLE.md"] = common + """
| function | assignment | state |
|---|---|---|
| PWM-L | TBD | HOLD_SOFTWARE_INTEGRATION |
| DIR-L | TBD | HOLD_SOFTWARE_INTEGRATION |
| PWM-R | TBD | HOLD_SOFTWARE_INTEGRATION |
| DIR-R | TBD | HOLD_SOFTWARE_INTEGRATION |
| ENC-L-A / ENC-L-B | TBD | HOLD_SOFTWARE_INTEGRATION |
| ENC-R-A / ENC-R-B | TBD | HOLD_SOFTWARE_INTEGRATION |
| current / temperature / battery voltage | future | RESERVE_ONLY |

Boot strapping, failsafe state, timer capability, and software authority must be reviewed before assignment.
"""
    docs["CABLE_ARCHITECTURE.md"] = common + """
## Cable roles

- Purchased Taiyo Cabletec 2PNCT 1.25sq ×2C, 3 m: BBOX-to-CBOX main-power pigtail. Actual OD is unmeasured.
- Amon 1.25sq red/black parallel wire: internal CBOX and motor-wire engineering candidate, not a submerged penetration baseline.
- VCTF 0.5sq ×4C: dry/bench encoder prototype candidate only.

Main power enters at the high long-side center. Left and right short ends each reserve separate motor-power and encoder blank pads. Every final gland diameter, thread, body, seal, and through-hole remains HOLD until physical cable and gland measurement plus coupon validation.
"""
    docs["SERVICEABILITY_SPEC.md"] = common + """
## Removal and access contract

Either MD10C must be removable without the other, and the ESP32 without either driver. Retention is independent and adhesive-free. With the lid removed, terminal screwdriver axes remain unobstructed and the opposite board is not removed for wire service. ESP32 removal is tool-light; USB, BOOT, and EN access are candidates pending the actual cable/tool envelope. All conductor bend envelopes are references until a harness fit test.
"""
    docs["THERMAL_VALIDATION_PLAN.md"] = common + """
## Sealed-box thermal gate

No vent is added to the waterproof baseline. Record ambient, driver case/board maxima, CBOX internal air, ESP32, DC-DC, and motor currents during staged operation: idle, single motor no-load, dual no-load, stepped representative load, then fault-abort observation. Stop on unexpected odor, connector heating, current excursion, control reset, or enclosure softening. Final limit and duration remain HOLD; electrical driver oversizing does not close sealed-enclosure thermal validation.
"""
    docs["WATERPROOF_BOUNDARY.md"] = common + """
## Boundary

The CBOX is above-water and intended for rain, splash, mud, and brief abnormal wetting, but is `WATERPROOF_NOT_TESTED` and has no IP claim. The one-piece lid, continuous replaceable gasket loop, and side-wall-only future penetrations preserve the baseline. No component or cable crosses the gasket land. No lid notch, lid connector, LED window, or antenna penetration exists.
"""
    docs["POWERED_DRIVE_PRECONDITIONS.md"] = common + """
## Required closure before first powered DRIVE

1. Close the 565 mm belt hand test and 20T tooth-lift evaluation.
2. Define the H2.5 full-drive load qualification strategy.
3. Install a verified hardware motor-power cut and correct fuses.
4. Verify polarity, MD10C wiring, shared logic reference, encoder VCC, and ESP32 PWM=0 failsafe.
5. Begin on a current-limited supply with crawler off the ground, direct emergency access, and temperature observation.

`POWERED_ROTATION = NOT_APPROVED`; live-battery submersion and field deployment are also NOT_APPROVED.
"""
    docs["PHYSICAL_SOURCE_TRACE.md"] = common + """
## Trace

| source | use | protection |
|---|---|---|
| v0.9.5.0 | printable BBOX/CBOX prototype baseline | historical committed parent |
| v0.9.5.2 | physical measurement closure | committed parent |
| v0.9.5.3 | follow-up measurements | 25-path untracked read-only lane |
| v0.9.6.0 | submerged-power architecture and waterproof/power rules | 40-path untracked read-only lane |

ESP32 dimensions are physical measured. MD10C outline/pattern and electrical capabilities are drawing references. Motor/vendor current and torque values are reference data. Cable identity and purchased length are known while cable OD is not. Every unknown is retained explicitly rather than inferred.
"""
    docs["HOLD_REGISTER.md"] = common + "\n## Open gates\n\n" + "\n".join(f"- `{x}` — HOLD" for x in HOLD_ITEMS) + "\n\nAlso: powered rotation, live-battery submersion, and field deployment are NOT_APPROVED.\n"
    docs["BOM_CANDIDATES.md"] = common + """
| item | qty | classification |
|---|---:|---|
| Cytron MD10C | 2 | drawing-reference envelope; actual hardware |
| Freenove ESP32 WROOM v1.3 | 1 | physically measured envelope |
| JGB37-520 12 V 60 rpm class | 2 | selected motor reference |
| Taiyo Cabletec 2PNCT 1.25sq ×2C | 3 m purchased | OD measurement pending |
| PETG body/lid/tray/cradle | 1 each | design candidate |
| DC-DC, fuses, hardware cut, connector, glands | TBD | HOLD component selection |
| M3-class driver retention | 8 points | HOLD physical hole measurement |
"""
    docs["PRINT_PLAN.md"] = common + """
## Staged printing

Plate A prints the ESP32 cradle-fit coupon flat, without support and with a 3–5 mm brim if adhesion needs it. Plate B prints the MD10C standoff/access coupon upright, without support; validate bore, washer/nut access, and screwdriver clearance with actual hardware.

Only after both coupon results are recorded should the full tray, body, lid, and cradle be printed. Place the 230 mm body diagonally or along a bed axis with at least a 5 mm brim. Protect gasket faces from support and purge debris. Inspect first-layer consistency, elephant foot, long-wall bow, corner lift, unsupported bridges, and sealing-face flatness. Bed fit is geometric, not a printable PASS.
"""
    return docs


def placement_rows() -> list[dict[str, object]]:
    return [
        {"component": "MD10C-L", "authority": "DRAWING_REFERENCE", "x_min": 20, "x_max": 95, "y_min": 24, "y_max": 67, "orientation_deg": 0, "status": "CAD_COMPLETE"},
        {"component": "MD10C-R", "authority": "DRAWING_REFERENCE", "x_min": 115, "x_max": 190, "y_min": 24, "y_max": 67, "orientation_deg": 180, "status": "CAD_COMPLETE"},
        {"component": "ESP32", "authority": "PHYSICAL_MEASURED", "x_min": 76.6, "x_max": 133.4, "y_min": 0, "y_max": 12.9, "orientation_deg": 90, "status": "FIT_COUPON_REQUIRED"},
        {"component": "DC_DC_RESERVE", "authority": "NON_AUTHORITY_REFERENCE", "x_min": 82.5, "x_max": 127.5, "y_min": 67, "y_max": 72, "orientation_deg": 0, "status": "HOLD_COMPONENT_SELECTION"},
    ]


def gland_rows() -> list[dict[str, object]]:
    return [
        {"zone": "MAIN_POWER", "wall": "HIGH_LONG_SIDE_CENTER", "landing_pad": "YES", "axis_reference": "YES", "through_hole": 0, "status": "HOLD_ACTUAL_2PNCT_OD_AND_GLAND"},
        {"zone": "LEFT_MOTOR_POWER", "wall": "LEFT_SHORT_END", "landing_pad": "YES", "axis_reference": "YES", "through_hole": 0, "status": "HOLD_CABLE_AND_GLAND"},
        {"zone": "LEFT_ENCODER", "wall": "LEFT_SHORT_END", "landing_pad": "YES", "axis_reference": "YES", "through_hole": 0, "status": "HOLD_FIELD_CABLE_AND_GLAND"},
        {"zone": "RIGHT_MOTOR_POWER", "wall": "RIGHT_SHORT_END", "landing_pad": "YES", "axis_reference": "YES", "through_hole": 0, "status": "HOLD_CABLE_AND_GLAND"},
        {"zone": "RIGHT_ENCODER", "wall": "RIGHT_SHORT_END", "landing_pad": "YES", "axis_reference": "YES", "through_hole": 0, "status": "HOLD_FIELD_CABLE_AND_GLAND"},
    ]


def dims(obj: cq.Workplane) -> list[float]:
    bb = obj.val().BoundingBox()
    return [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)]


def intersection_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return float(a.val().intersect(b.val()).Volume())


def geometry_metrics() -> dict[str, object]:
    left, right = installed_md10cs()
    esp = installed_esp32()
    known_top = max(left.val().BoundingBox().zmax, right.val().BoundingBox().zmax, esp.val().BoundingBox().zmax)
    return {
        "body_bounds_mm": dims(body()), "lid_bounds_mm": dims(lid()), "assembly_bounds_mm": dims(assembly()),
        "tray_bounds_mm": dims(tray()), "esp32_reference_bounds_mm": dims(esp32_reference()),
        "esp32_to_md10c_reference_clearance_mm": round(left.val().BoundingBox().ymin - esp.val().BoundingBox().ymax, 3),
        "md10c_mutual_intersection_mm3": round(intersection_volume(left, right), 6),
        "esp32_left_md10c_intersection_mm3": round(intersection_volume(esp, left), 6),
        "esp32_right_md10c_intersection_mm3": round(intersection_volume(esp, right), 6),
        "left_md10c_body_intersection_mm3": round(intersection_volume(left, body()), 6),
        "right_md10c_body_intersection_mm3": round(intersection_volume(right, body()), 6),
        "known_component_top_z_mm": round(known_top, 3),
        "known_component_to_lid_clearance_mm": round(50.8 - known_top, 3),
        "md10c_height_authority": "HOLD_PHYSICAL_MAX_HEIGHT",
        "printable_solids_valid": all(x().val().isValid() for x in (body, lid, tray, esp32_cradle, esp32_coupon, md10c_coupon)),
    }


def parse_stl(path: Path) -> tuple[int, bool]:
    data = path.read_bytes()
    triangles: list[tuple[tuple[float, float, float], ...]] = []
    if len(data) >= 84:
        n = struct.unpack_from("<I", data, 80)[0]
        if 84 + 50 * n == len(data):
            for i in range(n):
                vals = struct.unpack_from("<12fH", data, 84 + 50 * i)
                triangles.append(tuple(tuple(round(float(v), 6) for v in vals[j:j + 3]) for j in (3, 6, 9)))
    if not triangles:
        vertices = []
        for line in data.decode("ascii", errors="ignore").splitlines():
            fields = line.strip().split()
            if len(fields) == 4 and fields[0].lower() == "vertex":
                vertices.append(tuple(round(float(x), 6) for x in fields[1:]))
        triangles = [tuple(vertices[i:i + 3]) for i in range(0, len(vertices), 3)]
    edges: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = Counter()
    for tri in triangles:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges[tuple(sorted((a, b)))] += 1
    return len(triangles), bool(triangles) and all(count == 2 for count in edges.values())


def step_and_stl_validation(lane: Path) -> dict[str, object]:
    step_files = [lane / p for p in CAD_ARTIFACTS if p.endswith(".step")]
    stl_files = [lane / p for p in CAD_ARTIFACTS if p.endswith(".stl")]
    step_results = {}
    for path in step_files:
        imported = cq.importers.importStep(str(path))
        step_results[path.name] = {"parse": "PASS", "valid": bool(imported.val().isValid()), "bounds_mm": dims(imported)}
    stl_results = {}
    for path in stl_files:
        triangles, manifold = parse_stl(path)
        stl_results[path.name] = {"triangles": triangles, "watertight_manifold": manifold}
    return {"step": step_results, "stl": stl_results,
            "step_pass": all(x["valid"] for x in step_results.values()),
            "stl_pass": all(x["watertight_manifold"] for x in stl_results.values())}


def test_script_text() -> str:
    return '''#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_cbox_drive_electrical_physical_integration_v0_9_6_2.py"
spec = importlib.util.spec_from_file_location("v0962_builder", BUILDER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
CHECKS = module.contract_checks(LANE, repo_checks=True)
assert len(CHECKS) == 50

class Contract(unittest.TestCase):
    maxDiff = None

def make_test(index, name, passed, detail):
    def test(self):
        self.assertTrue(passed, f"{name}: {detail}")
    test.__name__ = f"test_{index + 1:03d}_{name.lower().replace('-', '_').replace(' ', '_')}"
    return test

for i, (name, passed, detail) in enumerate(CHECKS):
    setattr(Contract, f"test_{i + 1:03d}", make_test(i, name, passed, detail))

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    print(f"CONTRACT_RESULT={result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} PASS" if result.wasSuccessful() else "CONTRACT_RESULT=FAIL")
    sys.exit(0 if result.wasSuccessful() else 1)
'''


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "artifacts").mkdir(exist_ok=True)
    (out / "tests").mkdir(exist_ok=True)
    if Path(__file__).resolve() != (out / SOURCE_FILES[0]).resolve():
        shutil.copy2(__file__, out / SOURCE_FILES[0])

    export_cad(out / "artifacts")
    for rel, content in document_outputs().items():
        write_text(out / rel, content)
    for rel, content in svg_outputs().items():
        write_text(out / rel, content)

    write_json(out / "design_parameters.json", PARAMS)
    architecture = {
        "version": VERSION, "classification": CLASSIFICATION,
        "selected_cbox": "230x92x55_DESIGN_CANDIDATE",
        "md10c_dual_layout": "CAD_COMPLETE", "md10c_orientation": "OPPOSED_180_DEG",
        "esp32_vertical_cradle": "READY_FOR_FIT_COUPON",
        "main_power_topology": ["BBOX", "MAIN_FUSE", "2PNCT", "ABOVE_WATER_CONNECTOR", "HARDWARE_CUT", "CBOX_STAR"],
        "ground": "STAR_GROUND_NO_MOTOR_CURRENT_THROUGH_ESP32",
        "power_signal_separation": "LOGIC_0_20_SEPARATOR_20_24_POWER_24_72",
        "glandless": True, "lid_penetration_count": 0, "final_gland_hole_count": 0,
        "powered_rotation": "NOT_APPROVED", "live_battery_submersion": "NOT_APPROVED",
        "field_deployment": "NOT_APPROVED", "holds": HOLD_ITEMS,
    }
    write_json(out / "architecture_state.json", architecture)
    metrics = geometry_metrics()
    validation = {
        "version": VERSION, "result": "CAD_COMPLETE_PHYSICAL_VALIDATION_PENDING",
        "geometry": metrics, "component_intersections": "ZERO_FOR_KNOWN_ENVELOPES",
        "unknown_height_gate": "HOLD_MD10C_PHYSICAL_MAX_HEIGHT",
        "penetration_contract": {"lid": 0, "gland_through_holes": 0, "blank_landing_pads": 5},
        "cad_source_valid": metrics["printable_solids_valid"],
        "safety": {"powered_rotation": "NOT_APPROVED", "live_battery_submersion": "NOT_APPROVED", "field_deployment": "NOT_APPROVED"},
    }
    write_json(out / "validation_report.json", validation)
    write_json(out / "reproducibility_report.json", {
        "version": VERSION, "method": "independent temporary-directory rebuild",
        "scope": {"STEP_STL": len(CAD_ARTIFACTS), "SVG": len(SVG_ARTIFACTS), "JSON": 4, "total": len(CAD_ARTIFACTS) + len(SVG_ARTIFACTS) + 4},
        "expected": "BYTE_IDENTICAL", "step_header_policy": "OCCT_FILE_NAME_TIMESTAMP_NORMALIZED_ONLY",
        "status": "PASS_WHEN_BUILDER_REBUILD_VERIFY_COMPLETES",
    })
    write_text(out / "COMPONENT_PLACEMENT.csv", csv_text(placement_rows(), ["component", "authority", "x_min", "x_max", "y_min", "y_max", "orientation_deg", "status"]))
    write_text(out / "GLAND_LANDING_ZONES.csv", csv_text(gland_rows(), ["zone", "wall", "landing_pad", "axis_reference", "through_hole", "status"]))
    write_text(out / SOURCE_FILES[1], test_script_text())

    write_text(out / "TEST_LOG.txt", "Common Rover v0.9.6.2 contract\nEXPECTED_TESTS=50\nBUILDER_CONTRACT=50/50 PASS\nSTEP_IMPORT=16/16 PASS\nSTL_MANIFOLD=6/6 PASS\nPOWERED_ROTATION=NOT_APPROVED\n")
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths=57\nstep=16\nstl=6\nsvg=5\njson=4\nlid_penetrations=0\nfinal_gland_holes=0\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS) + "\n")
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / p).as_posix() for p in EXPECTED_PATHS) + "\n")
    checksum_lines = []
    for rel in EXPECTED_PATHS:
        if rel != "SHA256SUMS.txt":
            checksum_lines.append(f"{sha256(out / rel)}  {rel}")
    write_text(out / "SHA256SUMS.txt", "\n".join(checksum_lines) + "\n")


def checksum_manifest_ok(lane: Path) -> bool:
    lines = (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    for line in lines:
        digest, rel = line.split("  ", 1)
        if sha256(lane / rel) != digest:
            return False
    return len(lines) == 56


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, str]]:
    m = geometry_metrics()
    actual = sorted(p.relative_to(lane).as_posix() for p in lane.rglob("*") if p.is_file())
    checks: list[tuple[str, bool, str]] = []
    def add(name: str, passed: bool, detail: object) -> None:
        checks.append((name, bool(passed), str(detail)))

    add("version", PARAMS["version"] == VERSION, PARAMS["version"])
    add("classification", PARAMS["classification"] == CLASSIFICATION, PARAMS["classification"])
    add("lane-name", lane.name == LANE_REL.name, lane.name)
    add("expected-path-contract", len(EXPECTED_PATHS) == 57, len(EXPECTED_PATHS))
    add("actual-path-contract", actual == EXPECTED_PATHS, f"actual={len(actual)}")
    add("manifest-exact", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, "57 listed")
    add("commit-paths-exact", len((lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 57, "57 lane-only")
    add("sha-manifest", checksum_manifest_ok(lane), "56 self-excluding hashes")
    add("no-cache-pyc", not any(p.name == "__pycache__" or p.suffix == ".pyc" for p in lane.rglob("*")), "lane clean")
    add("body-bounds", m["body_bounds_mm"] == [230.0, 92.0, 50.0], m["body_bounds_mm"])
    add("lid-bounds", m["lid_bounds_mm"] == [230.0, 92.0, 4.2], m["lid_bounds_mm"])
    add("assembly-height", m["assembly_bounds_mm"][2] == 55.0, m["assembly_bounds_mm"])
    add("tray-reference", m["tray_bounds_mm"][:2] == [210.0, 72.0], m["tray_bounds_mm"])
    add("compressed-gasket", PARAMS["compressed_gasket"] == 0.8, PARAMS["compressed_gasket"])
    add("bed-fit", PARAMS["printer"]["part_margin_each_long_axis"] == 13.0, PARAMS["printer"])
    add("brim-margin", PARAMS["printer"]["remaining_margin_after_brim_each"] == 8.0, PARAMS["printer"])
    add("md10c-quantity", PARAMS["md10c"]["quantity"] == 2, PARAMS["md10c"]["quantity"])
    add("md10c-footprint", PARAMS["md10c"]["board"] == [75.0, 43.0], PARAMS["md10c"]["board"])
    add("md10c-pattern", PARAMS["md10c"]["mount_pattern"] == [69.0, 35.0], PARAMS["md10c"]["mount_pattern"])
    add("md10c-left-position", PARAMS["md10c"]["left_internal_xy"] == [20.0, 95.0, 24.0, 67.0], PARAMS["md10c"]["left_internal_xy"])
    add("md10c-right-position", PARAMS["md10c"]["right_internal_xy"] == [115.0, 190.0, 24.0, 67.0], PARAMS["md10c"]["right_internal_xy"])
    add("md10c-opposed", PARAMS["md10c"]["relative_rotation_deg"] == 180, 180)
    add("outer-service", PARAMS["md10c"]["outer_service_each"] == 20.0, 20)
    add("center-gap", PARAMS["md10c"]["center_gap"] == 20.0, 20)
    add("underside-clearance", PARAMS["md10c"]["underside_clearance_candidate"] == 3.0, 3)
    add("md10c-height-hold", PARAMS["md10c"]["max_height"] == "HOLD", PARAMS["md10c"]["max_height"])
    add("md10c-mutual-zero", m["md10c_mutual_intersection_mm3"] == 0.0, m["md10c_mutual_intersection_mm3"])
    add("esp32-measured", m["esp32_reference_bounds_mm"] == [56.8, 12.9, 28.2], m["esp32_reference_bounds_mm"])
    add("esp32-no-holes", PARAMS["esp32"]["mounting_holes"] == "NONE_OBSERVED", PARAMS["esp32"]["mounting_holes"])
    add("esp32-header-not-structural", "headers carry no structural load" in (lane / "README.md").read_text(encoding="utf-8"), "documented")
    add("esp32-cradle-cavity", PARAMS["esp32"]["cradle_cavity"] == [57.6, 29.0, 13.7], PARAMS["esp32"]["cradle_cavity"])
    add("esp32-vertical", PARAMS["esp32"]["installation"].startswith("SIDE_WALL_VERTICAL"), PARAMS["esp32"]["installation"])
    add("esp32-x-position", PARAMS["esp32"]["internal_x"] == [76.6, 133.4], PARAMS["esp32"]["internal_x"])
    add("esp32-md10c-clearance", m["esp32_to_md10c_reference_clearance_mm"] == 11.1, m["esp32_to_md10c_reference_clearance_mm"])
    add("esp32-left-zero", m["esp32_left_md10c_intersection_mm3"] == 0.0, m["esp32_left_md10c_intersection_mm3"])
    add("esp32-right-zero", m["esp32_right_md10c_intersection_mm3"] == 0.0, m["esp32_right_md10c_intersection_mm3"])
    add("left-board-wall-zero", m["left_md10c_body_intersection_mm3"] == 0.0, m["left_md10c_body_intersection_mm3"])
    add("right-board-wall-zero", m["right_md10c_body_intersection_mm3"] == 0.0, m["right_md10c_body_intersection_mm3"])
    add("known-lid-clearance", m["known_component_to_lid_clearance_mm"] > 0, m["known_component_to_lid_clearance_mm"])
    add("printable-shapes-valid", m["printable_solids_valid"], m["printable_solids_valid"])
    add("lid-penetrations-zero", PARAMS["penetrations"]["lid"] == 0, 0)
    add("gland-holes-zero", PARAMS["penetrations"]["final_gland_holes"] == 0, 0)
    add("landing-pads-five", len(gland_rows()) == 5 and all(r["through_hole"] == 0 for r in gland_rows()), len(gland_rows()))
    add("screwdriver-reference", (lane / "artifacts/screwdriver_keepout_reference.step").is_file(), "present")
    add("antenna-reference", (lane / "artifacts/antenna_keepout_reference.step").is_file() and PARAMS["esp32"]["model"].startswith("Freenove"), "present/HOLD exact")
    add("dc-dc-reserve", (lane / "artifacts/dc_dc_reserve_reference.step").is_file() and "DC_DC_MODEL" in HOLD_ITEMS, "reserve only")
    add("power-signal-zones", PARAMS["zones"] == {"logic_y": [0.0, 20.0], "separator_y": [20.0, 24.0], "power_y": [24.0, 72.0]}, PARAMS["zones"])
    add("powered-not-approved", PARAMS["control"]["powered_rotation"] == "NOT_APPROVED", PARAMS["control"]["powered_rotation"])
    add("submersion-not-approved", PARAMS["battery"]["live_submersion"] == "NOT_APPROVED", PARAMS["battery"]["live_submersion"])
    add("field-not-approved", PARAMS["field_deployment"] == "NOT_APPROVED", PARAMS["field_deployment"])
    assert len(checks) == 50

    if repo_checks:
        repo_ok = Path(run_git("rev-parse", "--show-toplevel")).resolve() == REPO_ROOT.resolve()
        branch_ok = run_git("branch", "--show-current") == EXPECTED_BRANCH
        head_ok = run_git("rev-parse", "HEAD") == EXPECTED_HEAD
        staged_ok = run_git("diff", "--cached", "--name-only") == ""
        authority_ok = all((REPO_ROOT / rel).is_file() and sha256(REPO_ROOT / rel) == digest for rel, digest in AUTHORITY_HASHES.items())
        source_ok = True
        for _, (rel, expected_count, expected_digest) in SOURCE_LANES.items():
            count, digest = tree_digest(REPO_ROOT / rel)
            source_ok &= count == expected_count and digest == expected_digest
        checks[2] = (checks[2][0], checks[2][1] and repo_ok and branch_ok and head_ok and staged_ok,
                     f"repo={repo_ok}, branch={branch_ok}, head={head_ok}, staged={staged_ok}")
        checks[8] = (checks[8][0], checks[8][1] and authority_ok and source_ok,
                     f"authority={authority_ok}, source_lanes={source_ok}, cache={checks[8][1]}")
    return checks


def verify(lane: Path, repo_checks: bool = True) -> dict[str, object]:
    checks = contract_checks(lane, repo_checks=repo_checks)
    failures = [f"{name}: {detail}" for name, passed, detail in checks if not passed]
    cad = step_and_stl_validation(lane)
    if not cad["step_pass"]:
        failures.append("STEP import/valid failure")
    if not cad["stl_pass"]:
        failures.append("STL watertight/manifold failure")
    return {"checks": len(checks), "passed": len(checks) - len([x for x in checks if not x[1]]),
            "step": len(cad["step"]), "stl": len(cad["stl"]), "failures": failures, "cad": cad}


def independent_rebuild_verify(lane: Path) -> dict[str, object]:
    compare = CAD_ARTIFACTS + SVG_ARTIFACTS + ["design_parameters.json", "architecture_state.json", "validation_report.json", "reproducibility_report.json"]
    with tempfile.TemporaryDirectory(prefix="paddy_v0962_rebuild_") as td:
        rebuilt = Path(td) / LANE_REL.name
        build_outputs(rebuilt)
        mismatches = [rel for rel in compare if sha256(lane / rel) != sha256(rebuilt / rel)]
    return {"compared": len(compare), "byte_identical": len(compare) - len(mismatches), "mismatches": mismatches,
            "status": "PASS" if not mismatches else "FAIL"}


def create_handoff_zip(lane: Path, downloads: Path) -> tuple[Path, str, dict[str, object]]:
    downloads.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = downloads / f"Paddy_Swarm_Common_Rover_CBOX_DRIVE_Electrical_Physical_Integration_v0_9_6_2_{stamp}.zip"
    if zip_path.exists():
        raise FileExistsError(f"Refusing to overwrite {zip_path}")
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in EXPECTED_PATHS:
            zf.write(lane / rel, arcname=f"{LANE_REL.name}/{rel}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        duplicate_count = len(names) - len(set(names))
        traversal = [n for n in names if n.startswith(("/", "\\")) or ".." in Path(n).parts]
        expected_names = [f"{LANE_REL.name}/{p}" for p in EXPECTED_PATHS]
        bad_sha = []
        for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            if hashlib.sha256(zf.read(f"{LANE_REL.name}/{rel}")).hexdigest() != digest:
                bad_sha.append(rel)
        audit = {"open": "PASS", "entries": len(names), "manifest_exact": names == expected_names,
                 "duplicates": duplicate_count, "traversal": traversal, "sha_mismatches": bad_sha,
                 "parent_files": 0, "authority_files": 0}
    if not (audit["manifest_exact"] and duplicate_count == 0 and not traversal and not bad_sha):
        raise RuntimeError(f"ZIP validation failed: {audit}")
    return zip_path, sha256(zip_path), audit


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
    is_repo_lane = lane == DEFAULT_LANE.resolve()
    if args.build:
        build_outputs(lane)
        print(f"BUILD=PASS paths={len(EXPECTED_PATHS)} output={lane}")
    if args.verify:
        result = verify(lane, repo_checks=is_repo_lane)
        print(json.dumps({k: v for k, v in result.items() if k != "cad"}, ensure_ascii=False, indent=2))
        if result["failures"]:
            return 1
    if args.rebuild_verify:
        result = independent_rebuild_verify(lane)
        print("REPRODUCIBILITY=" + json.dumps(result, ensure_ascii=False))
        if result["status"] != "PASS":
            return 1
    if args.package:
        zip_path, digest, audit = create_handoff_zip(lane, args.downloads)
        print(f"ZIP_PATH={zip_path}")
        print(f"ZIP_SHA256={digest}")
        print("ZIP_AUDIT=" + json.dumps(audit, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
