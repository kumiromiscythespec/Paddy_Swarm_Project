#!/usr/bin/env python3
"""Build Common Rover BBOX/CBOX printable physical prototypes v0.9.5.0."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

import cadquery as cq


VERSION = "0.9.5.0"
CLASSIFICATION = "BBOX_CBOX_PRINTABLE_PHYSICAL_PROTOTYPE"
RELEASE = "HOLD"
FINAL_STATUS = "BBOX_CBOX_PRINTABLE_PROTOTYPES_COMPLETE / PHYSICAL_FIT_AND_SEAL_TEST_PENDING"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0"
LANE = Path(__file__).resolve().parent
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_BBOX_CBOX_Printable_Prototype_v0_9_5_0_"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
BASE_OUTSIDE_UNTRACKED = 1526

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_TREES = {
    "common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0": (43, "f7272fe63cc425e89e651bd413ed1822578ced912a8cf8504832457bccdfaa1b"),
    "common_rover_190mm_frame_h25a1_2s_bbox_cbox_integration_v0_9_4_1": (68, "ebc85195613ebdcc59925b012eacfb02900ac379d0d3c3417e2e5a53b5dab210"),
    "common_rover_physical_fit_closure_v0_9_4_2": (57, "ccfa35a7e5ea2d1350fae7cc6ade9f40301f0582f1ecc76f9a3de5556dfe4fe7"),
    "common_rover_service_motion_servo_slide_clutch_h25a1_v0_9_4_3": (66, "8b2bd9e87615c298435d3529727933e4ecb60bfdbf66275281583f0756a22b9b"),
    "common_rover_h25a1_2s_full_hardware_fixture_v0_9_4_4": (59, "096b9cb753c1a049f2d33248ac905aeb0c3ea768c5bdbe6ceed98e99cec2fdbe"),
}

DOCS = [
    "README.md", "PARENT_AUDIT.md", "SOURCE_TRACE.md", "FRAME_REFERENCE.md", "BATTERY_REFERENCE.md",
    "BATTERY_TERMINAL_REFERENCE.md", "BBOX_ARCHITECTURE.md", "BBOX_DIMENSION_AUTHORITY.md",
    "BBOX_BATTERY_CAVITY.md", "BBOX_TERMINAL_OPENING.md", "BBOX_SERVICE_RING.md", "BBOX_WEAR_PAD.md",
    "BBOX_BOTTOM_GRIP.md", "BBOX_RAIL_INTERFACE.md", "BBOX_CONNECTOR_PANEL.md", "BBOX_SERVICE_MOTION.md",
    "BBOX_PHYSICAL_TEST_PLAN.md", "BBOX_PHYSICAL_RESULT_FORM.md", "CBOX_ARCHITECTURE.md",
    "CBOX_WIDTH_COMPARISON.md", "CBOX_LID_AND_GASKET.md", "CBOX_UNIVERSAL_TRAY.md",
    "CBOX_CONNECTOR_PANEL.md", "CBOX_FRAME_SUPPORT.md", "CBOX_THERMAL_RESERVATION.md",
    "CBOX_PHYSICAL_TEST_PLAN.md", "CBOX_PHYSICAL_RESULT_FORM.md", "BBOX_CBOX_INTEGRATION.md",
    "INTERFERENCE_REPORT.md", "PRINT_RISK_REPORT.md", "PRINT_PLAN.md", "MISSING_MEASUREMENTS.md",
    "DESIGN_GATE.md",
]
CAD = [
    "cad/bbox_lower_body.step", "cad/bbox_lower_body.stl",
    "cad/bbox_top_service_ring.step", "cad/bbox_top_service_ring.stl",
    "cad/bbox_top_wear_pad_left.step", "cad/bbox_top_wear_pad_left.stl",
    "cad/bbox_top_wear_pad_right.step", "cad/bbox_top_wear_pad_right.stl",
    "cad/bbox_connector_blank_panel.step", "cad/bbox_connector_blank_panel.stl",
    "cad/bbox_battery_restraint_pad.step", "cad/bbox_battery_restraint_pad.stl",
    "cad/bbox_assembly_reference.step", "cad/bbox_pitch_slide_sweep.step",
    "cad/bbox_terminal_cap_reference.step", "cad/bbox_terminal_keepout_reference.step",
    "cad/bbox_bottom_grip_reference.step", "cad/bbox_rail_width_comparison.step",
    "cad/PLATE_01_BBOX_SERVICE_PARTS.step", "cad/PLATE_01_BBOX_SERVICE_PARTS.stl",
    "cad/cbox_body.step", "cad/cbox_body.stl", "cad/cbox_lid.step", "cad/cbox_lid.stl",
    "cad/cbox_gasket_land_reference.step", "cad/cbox_universal_tray.step", "cad/cbox_universal_tray.stl",
    "cad/cbox_connector_blank_panel.step", "cad/cbox_connector_blank_panel.stl",
    "cad/cbox_frame_mount_interface.step", "cad/cbox_frame_mount_interface.stl",
    "cad/cbox_assembly_reference.step", "cad/cbox_width_comparison.step",
    "cad/cbox_gasket_compression_coupon_20_25_30.step", "cad/cbox_gasket_compression_coupon_20_25_30.stl",
    "cad/PLATE_02_CBOX_SERVICE_PARTS.step", "cad/PLATE_02_CBOX_SERVICE_PARTS.stl",
    "cad/bbox_cbox_frame_reference.step", "cad/bbox_service_corridor_reference.step",
    "cad/cbox_lid_service_sweep.step",
]
DRAWINGS = [
    "drawings/bbox_top.svg", "drawings/bbox_side.svg", "drawings/bbox_front.svg", "drawings/bbox_section.svg",
    "drawings/bbox_battery_fit.svg", "drawings/bbox_terminal_keepout.svg", "drawings/bbox_pitch_slide.svg",
    "drawings/bbox_bottom_grip.svg", "drawings/cbox_top.svg", "drawings/cbox_side.svg",
    "drawings/cbox_front.svg", "drawings/cbox_section.svg", "drawings/cbox_tray.svg", "drawings/cbox_mount.svg",
    "drawings/bbox_cbox_x_serial.svg", "drawings/bbox_service_sweep.svg", "drawings/sealing_land.svg",
]
JSONS = ["dimensions.json", "interfaces.json", "hardware.json", "service_motions.json",
         "measurement_ledger.json", "test_limits.json", "geometry_manifest.json", "validation_report.json"]
SOURCE = ["build_common_rover_bbox_cbox_prototype_v0950.py", "tests/test_common_rover_bbox_cbox_prototype_v0950.py"]
RELEASE_FILES = ["MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt", "BUILD_LOG.txt", "TEST_LOG.txt"]
PACKAGE_PATHS = sorted(DOCS + CAD + DRAWINGS + JSONS + SOURCE + RELEASE_FILES)

FRAME = {
    "upper_outer_mm": [540.0, 181.0], "lower_outer_mm": [442.0, 181.0],
    "structural_height_mm": 150.0, "upper_clear_mm": [500.0, 100.0],
    "lower_clear_mm": [400.0, 140.0], "vertical_2020_mm": 110.0,
    "physical_tolerance_mm": 1.0, "status": "REOPENED_PRIMARY_COMPACT_BASELINE",
    "alternative_190mm": "HOLD",
}
BATTERY = {
    "product": "GOLDENMATE LiFePO4 12.8V 10Ah 128Wh", "x_mm": 150.9, "y_mm": 99.4,
    "z_mm": 92.5, "mass_kg": 1.2, "insertion_clear_height_mm": 108.0,
    "terminal_equipped_frame_pass": "PHYSICAL_PASS_USER_REPORTED",
}
TERMINAL = {
    "pair_outer_span_mm": 29.5, "inner_gap_mm": 20.0, "individual_width_mm": None,
    "opening_candidates_mm": [33.5, 34.5, 35.5], "preferred_candidate_mm": 34.5,
    "exact_x_mm": None, "exact_y_mm": None, "protrusion_z_mm": None,
}
BBOX = {
    "designation": "BBOX_REAR_REMOVABLE_BATTERY_CASSETTE", "outer_x_mm": 180.0,
    "outer_y_mm": 114.0, "service_envelope_z_mm": 103.0, "lower_body_height_mm": 97.5,
    "service_ring_height_mm": 3.0, "wear_pad_thickness_mm": 2.5, "wall_mm": 3.2,
    "bottom_mm": 3.2, "inner_x_nominal_mm": 173.6, "inner_y_nominal_mm": 107.6,
    "battery_y_clear_total_mm": 8.2, "battery_y_clear_each_mm": 4.1,
    "battery_x_free_nominal_mm": 22.7, "removal_direction": "-X",
    "service_motion": "PITCH_AND_SLIDE", "idler_support": False,
    "rail_width_candidates_mm": [130.0, 132.0, 134.0], "wear_pad_replaceable": True,
    "final_terminal_cap_manufacturing": False, "final_waterproof": False,
}
CBOX = {
    "designation": "CBOX_FRONT_HIGH_FIXED_UNIVERSAL_ELECTRONICS", "outer_x_mm": 180.0,
    "width_candidates_mm": [90.0, 92.0, 94.0], "selected_y_mm": 92.0,
    "total_z_mm": 45.0, "body_height_mm": 40.0, "lid_thickness_mm": 4.2,
    "compressed_gasket_reference_mm": 0.8, "wall_mm": 3.2, "bottom_mm": 3.2,
    "on_bbox": False, "independent_support": True, "tray_removable": True,
    "connector_panel_replaceable": True, "bolt_count": 16, "max_unsupported_gasket_span_mm": 36.0,
    "final_electronics": "HOLD", "waterproof": "PHYSICAL_TEST_REQUIRED",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def box(x: float, y: float, z: float, cx=0.0, cy=0.0, cz=0.0) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate((cx, cy, cz))


def rbox(x: float, y: float, z: float, radius: float, cx=0.0, cy=0.0, cz=0.0) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).edges("|Z").fillet(radius).translate((cx, cy, cz))


def cyl(radius: float, length: float, origin=(0.0, 0.0, 0.0), direction=(0.0, 0.0, 1.0)) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(*origin), cq.Vector(*direction)))


def compound(parts: list[Any]) -> cq.Compound:
    values: list[Any] = []
    for part in parts:
        if isinstance(part, cq.Workplane):
            values.extend(part.vals())
        elif isinstance(part, cq.Compound):
            values.extend(part.Solids())
        else:
            values.append(part)
    return cq.Compound.makeCompound(values)


def raised(label: str, x: float, y: float, z: float, size=3.0) -> cq.Workplane:
    return cq.Workplane("XY").text(label, size, 0.5, halign="center", valign="center").translate((x, y, z))


def export(shape: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path))
    if path.suffix.lower() in {".step", ".stp"}:
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"(FILE_NAME\('Open CASCADE Shape Model',')[^']+(')", r"\g<1>2000-01-01T00:00:00\2", text)
        text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
        occurrence = 0
        def normalize(match: re.Match[str]) -> str:
            nonlocal occurrence
            occurrence += 1
            return match.group(1) + str(occurrence) + match.group(2)
        text = re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')", normalize, text)
        path.write_text(text, encoding="utf-8", newline="\n")


def tree_digest(root: Path) -> tuple[int, str]:
    paths = sorted((p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts),
                   key=lambda p: p.relative_to(root).as_posix())
    h = hashlib.sha256()
    for path in paths:
        h.update(f"{sha(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(paths), h.hexdigest()


def parent_audit() -> dict[str, Any]:
    rows = {}
    root = REPO_ROOT / "cad" / "common_rover"
    for name, expected in PARENT_TREES.items():
        actual = tree_digest(root / name)
        manifest = (root / name / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
        sums = (root / name / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        rows[name] = {"file_count": actual[0], "tree_sha256": actual[1], "manifest_count": len(manifest),
                      "sha_entry_count": len(sums), "status": "CAD_PASS" if actual == expected else "FAIL"}
    return {"parents": rows, "status": "CAD_PASS" if all(r["status"] == "CAD_PASS" for r in rows.values()) else "FAIL"}


def authority_audit() -> dict[str, Any]:
    actual = {name: sha(REPO_ROOT / name) for name in AUTHORITY_HASHES}
    return {"hashes": actual, "status": "CAD_PASS" if actual == AUTHORITY_HASHES else "FAIL"}


def repository_guard(complete: bool = False) -> dict[str, Any]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    tracked = sorted(git("diff", "--name-only").splitlines())
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    untracked = sorted(git("ls-files", "--others", "--exclude-standard").splitlines())
    lane = sorted(p[len(LANE_REL) + 1:] for p in untracked if p.startswith(LANE_REL + "/"))
    outside = [p for p in untracked if not p.startswith(LANE_REL + "/")]
    ignored_lane = git("ls-files", "--others", "-i", "--exclude-standard", "--", LANE_REL).splitlines()
    forbidden = [p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and
                 (p.suffix.lower() in {".pyc", ".dxf", ".3mf", ".gcode"} or "__pycache__" in p.parts)]
    checks = {
        "root": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "tracked_existing_four": set(tracked) == set(AUTHORITY_HASHES), "staged_zero": not staged,
        "outside_untracked_preserved": len(outside) == BASE_OUTSIDE_UNTRACKED,
        "lane_scope": set(lane).issubset(PACKAGE_PATHS),
        "lane_complete": set(lane) == set(PACKAGE_PATHS) if complete else True,
        "authority_hashes": authority_audit()["status"] == "CAD_PASS",
        "parents": parent_audit()["status"] == "CAD_PASS", "ignored_lane_zero": not ignored_lane,
        "forbidden_lane_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_guard": checks, "tracked": tracked, "staged": staged,
                            "outside": len(outside), "lane": lane, "ignored": ignored_lane, "forbidden": forbidden})
    return {"root": str(root), "branch": branch, "head": head, "tracked": tracked, "staged": staged,
            "untracked_total": len(untracked), "outside_untracked": len(outside), "lane_untracked": len(lane),
            "checks": checks, "status": "CAD_PASS"}


def bbox_body() -> cq.Workplane:
    outer = rbox(180, 114, 97.5, 5, cz=48.75)
    cavity = rbox(173.6, 107.6, 98, 2.5, cz=52.2)
    part = outer.cut(cavity)
    # Rear grip block and upper connector backer preserve a sealed inner wall.
    part = part.union(box(22, 70, 24, -79, 0, 12))
    part = part.union(box(10, 64, 40, -85, 0, 62))
    grip = cyl(9.5, 52, (-82, -26, 13), (0, 1, 0))
    panel_recess = box(4.2, 52, 32, -88.9, 0, 62)
    part = part.cut(grip).cut(panel_recess)
    # Broad low floor ribs; top Z4.0 is the battery support datum.
    for y in (-34, 0, 34):
        part = part.union(box(148, 8, 0.8, 8.5, y, 3.6))
    # Two rear bosses use the X service reserve; two smaller side-wall bosses
    # remain outside the battery Y envelope.  This avoids a false front-corner
    # collision while retaining four M4 candidate ring fasteners.
    for x, y, radius in ((-80, -52, 4.0), (-80, 52, 4.0), (65, -53.5, 3.5), (65, 53.5, 3.5)):
        part = part.union(cyl(radius, 94.3, (x, y, 3.2))).cut(cyl(2.15, 96, (x, y, 2.5)))
    return part.clean()


def bbox_ring() -> cq.Workplane:
    ring = rbox(180, 114, 3, 5, cz=1.5).cut(rbox(166, 100, 4, 2.5, cz=2))
    for x, y in ((-80, -52), (-80, 52), (65, -53.5), (65, 53.5)):
        ring = ring.cut(cyl(2.15, 5, (x, y, -1)))
    return ring.clean()


def wear_pad(left: bool) -> cq.Workplane:
    pad = rbox(72, 8, 2.5, 1.2, cz=1.25)
    # Rounded/chamfered lead-in; the two files remain mirror-authoritative.
    direction = -1 if left else 1
    lead = box(6, 10, 3, 33 * direction, 0, 1.5).rotate((0, 0, 0), (0, 1, 0), 20 * direction)
    return pad.cut(lead).clean()


def bbox_connector_panel() -> cq.Workplane:
    panel = rbox(30, 50, 3.2, 2, cz=1.6)
    for x in (-10.5, 10.5):
        for y in (-20, 20):
            panel = panel.cut(cyl(1.7, 5, (x, y, -1)))
    return panel.clean()


def bbox_restraint_print_kit() -> cq.Compound:
    front = rbox(95, 2, 12, 0.8, 0, 22, 6)
    side_a = rbox(118, 2, 12, 0.8, 0, -8, 6)
    side_b = rbox(118, 2, 12, 0.8, 0, 8, 6)
    return compound([front, side_a, side_b])


def bbox_restraint_installed() -> cq.Compound:
    front = rbox(2, 95, 12, 0.8, 85.05, 0, 10)
    side_l = rbox(118, 2, 12, 0.8, 0, 50.95, 10)
    side_r = rbox(118, 2, 12, 0.8, 0, -50.95, 10)
    return compound([front, side_l, side_r])


def battery_reference() -> cq.Workplane:
    return rbox(150.9, 99.4, 92.5, 3, 8.35, 0, 50.25)


def terminal_keepout(width=34.5) -> cq.Workplane:
    # XY is a parameter origin only; actual terminal location remains HOLD.
    return rbox(20, width, 5.5, 2, 0, 0, 2.75)


def terminal_keepout_comparison() -> cq.Compound:
    parts = []
    for x, width, label in zip((-42, 0, 42), (33.5, 34.5, 35.5), ("W335", "W345", "W355")):
        frame = rbox(30, width + 8, 2.5, 2, x, 0, 1.25).cut(rbox(20, width, 4, 1, x, 0, 2))
        parts.append(frame.union(raised(label, x, -(width + 8) / 2 + 3.2, 2.4, 2.4)))
    return compound(parts)


def bbox_terminal_cap_reference() -> cq.Workplane:
    cap = rbox(50, 48, 4, 3, cz=2).cut(rbox(20, 34.5, 6, 1.5, cz=3))
    for x in (-20, 20):
        for y in (-19, 19):
            cap = cap.cut(cyl(1.7, 6, (x, y, -1)))
    return cap.clean()


def bbox_grip_reference() -> cq.Compound:
    block = box(22, 70, 24, -79, 0, 12)
    grip = cyl(9.5, 52, (-82, -26, 13), (0, 1, 0))
    return compound([block.cut(grip), grip])


def bbox_rail_comparison() -> cq.Compound:
    parts = []
    for z, width in enumerate((130.0, 132.0, 134.0)):
        parts.append(rbox(180, width, 1.2, 3, 0, 0, z * 2.2 + 0.6).cut(rbox(174, width - 6, 2, 1, 0, 0, z * 2.2 + 1)))
    return compound(parts)


def bbox_assembly() -> cq.Compound:
    panel = bbox_connector_panel().rotate((0, 0, 0), (0, 1, 0), 90).translate((-90, 0, 62))
    parts = [bbox_body(), bbox_ring().translate((0, 0, 97.5)),
             wear_pad(True).translate((0, 53, 100.5)), wear_pad(False).translate((0, -53, 100.5)),
             battery_reference(), bbox_restraint_installed(), panel,
             terminal_keepout().translate((0, 0, 97.5))]
    return compound(parts)


def bbox_sweep_solids() -> list[cq.Workplane]:
    parts = []
    for angle, shift in zip((0, 2, 4, 6), (0, 125, 195, 220)):
        shape = rbox(180, 114, 103, 5, -100 - shift, 0, 51.5)
        pivot_x = -10 - shift
        parts.append(shape.rotate((pivot_x, 0, 0), (pivot_x, 1, 0), angle))
    return parts


def bbox_sweep() -> cq.Compound:
    return compound(bbox_sweep_solids())


def cbox_bolt_positions() -> list[tuple[float, float]]:
    return [(x, y) for y in (-37, 37) for x in (-75, -45, -15, 15, 45, 75)] + \
           [(x, y) for x in (-82, 82) for y in (-18, 18)]


def cbox_body() -> cq.Workplane:
    outer = rbox(180, 92, 40, 5, cz=20)
    void = (cq.Workplane("XY").workplane(offset=3.2).rect(173.6, 85.6)
            .workplane(offset=28.8).rect(173.6, 85.6)
            .workplane(offset=8.5).rect(157.6, 69.6).loft(combine=True))
    part = outer.cut(void)
    # Bottom-anchored tray posts; holes remain blind above the waterproof floor.
    for x in (-65, 65):
        for y in (-27, 27):
            part = part.union(cyl(4.5, 5, (x, y, 3.2))).cut(cyl(1.65, 4.5, (x, y, 4.2)))
    # Front removable-panel backer is thick and remains sealed behind the blank.
    part = part.union(box(10, 52, 28, 85, 0, 20)).cut(box(4, 46, 26, 89, 0, 20))
    for x, y in cbox_bolt_positions():
        part = part.cut(cyl(2.15, 11, (x, y, 30)))
    return part.clean()


def cbox_lid() -> cq.Workplane:
    lid = rbox(180, 92, 4.2, 5, cz=2.1)
    for x, y in cbox_bolt_positions():
        lid = lid.cut(cyl(2.15, 7, (x, y, -1)))
    return lid.clean()


def cbox_gasket_land() -> cq.Workplane:
    return rbox(176, 88, 0.8, 4, cz=0.4).cut(rbox(170, 82, 2, 2.5, cz=1))


def cbox_tray() -> cq.Workplane:
    tray = rbox(160, 72, 2.4, 3, cz=1.2)
    for x in (-60, -40, -20, 0, 20, 40, 60):
        for y in (-24, 0, 24):
            tray = tray.cut(box(10, 3.4, 4, x, y, 2))
    for x in (-65, 65):
        for y in (-27, 27):
            tray = tray.cut(cyl(1.65, 5, (x, y, -1)))
    return tray.clean()


def cbox_connector_panel() -> cq.Workplane:
    panel = rbox(24, 44, 3, 2, cz=1.5)
    for x in (-8.5, 8.5):
        for y in (-18, 18):
            panel = panel.cut(cyl(1.65, 5, (x, y, -1)))
    return panel.clean()


def cbox_mount_interface() -> cq.Compound:
    rails = []
    for y in (-32, 32):
        rail = rbox(160, 12, 4, 2, 0, y, 2)
        for x in (-65, -25, 25, 65):
            rail = rail.cut(box(12, 4.6, 6, x, y, 3))
        rails.append(rail)
    return compound(rails)


def cbox_gasket_coupon() -> cq.Compound:
    parts = []
    for x, depth, label in zip((-36, 0, 36), (2.0, 2.5, 3.0), ("G20", "G25", "G30")):
        coupon = rbox(30, 24, 5, 2, x, 0, 2.5).cut(box(18, 12, depth, x, 0, 5 - depth / 2))
        parts.append(coupon.union(raised(label, x, -8, 4.9, 2.5)))
    return compound(parts)


def cbox_width_comparison() -> cq.Compound:
    return compound([rbox(180, width, 2, 4, (index - 1) * 195, 0, 1)
                     for index, width in enumerate((90.0, 92.0, 94.0))])


def cbox_assembly() -> cq.Compound:
    panel = cbox_connector_panel().rotate((0, 0, 0), (0, 1, 0), 90).translate((87, 0, 20))
    return compound([cbox_body(), cbox_tray().translate((0, 0, 8.2)), cbox_gasket_land().translate((0, 0, 40)),
                     cbox_lid().translate((0, 0, 40.8)), panel])


def bbox_plate_components() -> list[Any]:
    # All service parts nest inside the ring aperture without touching it or
    # one another; this keeps the complete plate within 180×114 mm.
    return [bbox_ring(), bbox_restraint_print_kit().translate((0, -22, 0)),
            bbox_connector_panel().rotate((0, 0, 0), (0, 0, 1), 90).translate((0, 25, 0)),
            wear_pad(True).translate((-42, 45, 0)), wear_pad(False).translate((42, 45, 0))]


def bbox_plate() -> cq.Compound:
    return compound(bbox_plate_components())


def cbox_plate_components() -> list[Any]:
    return [cbox_tray().translate((0, 45, 0)),
            cbox_connector_panel().rotate((0, 0, 0), (0, 0, 1), 90).translate((0, -18, 0)),
            cbox_gasket_coupon().translate((0, -50, 0))]


def cbox_plate() -> cq.Compound:
    return compound(cbox_plate_components())


def frame_reference() -> cq.Compound:
    upper = [box(540, 40.5, 20, 0, y, 118) for y in (-70.25, 70.25)]
    lower = [box(442, 20.5, 20, 0, y, -10) for y in (-80.25, 80.25)]
    posts = [box(20, 20, 110, x, y, 55) for x in (-201, 201) for y in (-80.25, 80.25)]
    return compound(upper + lower + posts)


def cbox_support_reference() -> cq.Compound:
    return compound([box(190, 8, 6, 100, y, 127) for y in (-40, 40)])


def integration_reference() -> cq.Compound:
    return compound([frame_reference(), bbox_assembly().translate((-100, 0, 0)),
                     cbox_assembly().translate((100, 0, 130)), cbox_support_reference()])


def service_corridor_reference() -> cq.Compound:
    crawler = [box(500, 30, 80, -40, y, 45) for y in (-120, 120)]
    idlers = [cyl(25, 12, (-230, y, 45), (0, 1 if y < 0 else -1, 0)) for y in (-90, 90)]
    kp = [box(67, 17, 35, 80, y, 120) for y in (-78, 78)]
    servo = box(75, 70, 50, 175, 0, 180)
    clutch = box(90, 65, 45, 205, 0, 105)
    fasteners = [cyl(4, 12, (x, y, 108), (0, 0, -1)) for x in (-180, 180) for y in (-62, 62)]
    return compound([frame_reference(), bbox_sweep(), cbox_assembly().translate((100, 0, 130)),
                     cbox_support_reference(), *crawler, *idlers, *kp, servo, clutch, *fasteners])


def cbox_lid_sweep() -> cq.Compound:
    return compound([cbox_lid().translate((100, 0, z)) for z in (170.8, 200, 230)])


def artifact_jobs() -> list[tuple[Any, str]]:
    return [
        (bbox_body(), CAD[0]), (bbox_body(), CAD[1]), (bbox_ring(), CAD[2]), (bbox_ring(), CAD[3]),
        (wear_pad(True), CAD[4]), (wear_pad(True), CAD[5]), (wear_pad(False), CAD[6]), (wear_pad(False), CAD[7]),
        (bbox_connector_panel(), CAD[8]), (bbox_connector_panel(), CAD[9]),
        (bbox_restraint_print_kit(), CAD[10]), (bbox_restraint_print_kit(), CAD[11]),
        (bbox_assembly(), CAD[12]), (bbox_sweep(), CAD[13]), (bbox_terminal_cap_reference(), CAD[14]),
        (terminal_keepout_comparison(), CAD[15]), (bbox_grip_reference(), CAD[16]), (bbox_rail_comparison(), CAD[17]),
        (bbox_plate(), CAD[18]), (bbox_plate(), CAD[19]),
        (cbox_body(), CAD[20]), (cbox_body(), CAD[21]), (cbox_lid(), CAD[22]), (cbox_lid(), CAD[23]),
        (cbox_gasket_land(), CAD[24]), (cbox_tray(), CAD[25]), (cbox_tray(), CAD[26]),
        (cbox_connector_panel(), CAD[27]), (cbox_connector_panel(), CAD[28]),
        (cbox_mount_interface(), CAD[29]), (cbox_mount_interface(), CAD[30]),
        (cbox_assembly(), CAD[31]), (cbox_width_comparison(), CAD[32]),
        (cbox_gasket_coupon(), CAD[33]), (cbox_gasket_coupon(), CAD[34]),
        (cbox_plate(), CAD[35]), (cbox_plate(), CAD[36]),
        (integration_reference(), CAD[37]), (service_corridor_reference(), CAD[38]), (cbox_lid_sweep(), CAD[39]),
    ]


def common_volume(a: Any, b: Any) -> float:
    sa = a.val() if isinstance(a, cq.Workplane) else a
    sb = b.val() if isinstance(b, cq.Workplane) else b
    return float(sa.intersect(sb).Volume())


def maximum_pairwise_volume(parts: list[Any]) -> float:
    return max((common_volume(parts[i], parts[j]) for i in range(len(parts)) for j in range(i + 1, len(parts))),
               default=0.0)


def interference_report() -> dict[str, Any]:
    frame = frame_reference()
    bbox_installed = rbox(180, 114, 103, 5, -100, 0, 51.5)
    sweeps = bbox_sweep()
    cbox = rbox(180, 92, 45, 5, 100, 0, 152.5)
    support = cbox_support_reference()
    battery = battery_reference()
    body = bbox_body()
    pads = bbox_restraint_installed()
    ring = bbox_ring().translate((0, 0, 97.5))
    terminal = terminal_keepout().translate((0, 0, 97.5))
    grip = cyl(9.5, 52, (-182, -26, 13), (0, 1, 0))
    bbox_panel = bbox_connector_panel().rotate((0, 0, 0), (0, 1, 0), 90).translate((-190, 0, 62))
    cbox_panel = cbox_connector_panel().rotate((0, 0, 0), (0, 1, 0), 90).translate((187, 0, 150))
    lid_service = cbox_lid_sweep()
    bbox_installed_body = bbox_body().translate((-100, 0, 0))
    bbox_installed_pads = bbox_restraint_installed().translate((-100, 0, 0))
    cbox_installed_body = cbox_body().translate((100, 0, 130))
    cbox_installed_tray = cbox_tray().translate((100, 0, 138.2))
    cbox_installed_gasket = cbox_gasket_land().translate((100, 0, 170))
    cbox_installed_lid = cbox_lid().translate((100, 0, 170.8))
    refs = {
        "crawler": compound([box(500, 30, 80, -40, y, 45) for y in (-120, 120)]),
        "idler": compound([cyl(25, 12, (-230, y, 45), (0, 1 if y < 0 else -1, 0)) for y in (-90, 90)]),
        "kp000": compound([box(67, 17, 35, 80, y, 120) for y in (-78, 78)]),
        "servo": box(75, 70, 50, 175, 0, 180), "clutch": box(90, 65, 45, 205, 0, 105),
        "fasteners": compound([cyl(4, 12, (x, y, 108), (0, 0, -1)) for x in (-180, 180) for y in (-62, 62)]),
    }
    raw = [
        ("BATTERY_VS_BBOX_SHELL", common_volume(battery, body), "CAD_PASS_REFERENCE"),
        ("BATTERY_VS_RESTRAINT_PADS", common_volume(battery, pads), "CONTROLLED_0P25_CLEARANCE_PHYSICAL_PENDING"),
        ("TERMINAL_W345_VS_SERVICE_RING", common_volume(terminal, ring), "CAD_PASS_PARAMETRIC_ORIGIN_XY_HOLD"),
        ("BBOX_INSTALLED_VS_FRAME", common_volume(bbox_installed, frame), "CAD_PASS_REFERENCE_5MM_Z_13MM_Y_EACH"),
        ("BBOX_PITCH_SWEEP_VS_CBOX", common_volume(sweeps, cbox), "CAD_PASS_REFERENCE"),
        ("BBOX_PITCH_SWEEP_VS_CBOX_SUPPORT", common_volume(sweeps, support), "CAD_PASS_REFERENCE"),
        ("BBOX_GRIP_VS_FRAME", common_volume(grip, frame), "CAD_PASS_REFERENCE"),
        ("CBOX_VS_FRAME", common_volume(cbox, frame), "CAD_PASS_REFERENCE_4MM_Y_EACH"),
        ("CBOX_LID_SERVICE_VS_FRAME", common_volume(lid_service, frame), "CAD_PASS_REFERENCE"),
        ("BBOX_CONNECTOR_PANEL_VS_FRAME", common_volume(bbox_panel, frame), "CAD_PASS_REFERENCE"),
        ("CBOX_CONNECTOR_PANEL_VS_FRAME", common_volume(cbox_panel, frame), "CAD_PASS_REFERENCE"),
        ("BBOX_RESTRAINT_PADS_VS_SHELL", common_volume(bbox_installed_pads, bbox_installed_body), "CAD_PASS_REFERENCE"),
        ("BBOX_CONNECTOR_PANEL_VS_SHELL", common_volume(bbox_panel, bbox_installed_body), "CAD_PASS_REFERENCE"),
        ("CBOX_TRAY_VS_SHELL", common_volume(cbox_installed_tray, cbox_installed_body), "CAD_PASS_REFERENCE"),
        ("CBOX_GASKET_VS_BODY", common_volume(cbox_installed_gasket, cbox_installed_body), "CAD_PASS_FACE_CONTACT_ONLY"),
        ("CBOX_GASKET_VS_LID", common_volume(cbox_installed_gasket, cbox_installed_lid), "CAD_PASS_FACE_CONTACT_ONLY"),
        ("CBOX_CONNECTOR_PANEL_VS_SHELL", common_volume(cbox_panel, cbox_installed_body), "CAD_PASS_REFERENCE"),
        ("BBOX_SWEEP_VS_CRAWLER_REFERENCE", common_volume(sweeps, refs["crawler"]), "HOLD_ACTUAL_TRANSFORMS_REFERENCE_ZERO"),
        ("BBOX_SWEEP_VS_IDLER_REFERENCE", common_volume(sweeps, refs["idler"]), "HOLD_ACTUAL_TRANSFORMS_REFERENCE_ZERO"),
        ("BBOX_SWEEP_VS_KP000_REFERENCE", common_volume(sweeps, refs["kp000"]), "HOLD_ACTUAL_TRANSFORMS_REFERENCE_ZERO"),
        ("BBOX_SWEEP_VS_SERVO_BRIDGE_REFERENCE", common_volume(sweeps, refs["servo"]), "HOLD_ACTUAL_TRANSFORMS_REFERENCE_ZERO"),
        ("BBOX_SWEEP_VS_SLIDE_CLUTCH_REFERENCE", common_volume(sweeps, refs["clutch"]), "HOLD_ACTUAL_TRANSFORMS_REFERENCE_ZERO"),
        ("BBOX_SWEEP_VS_SCREW_HEAD_BOLT_TIP_REFERENCE", common_volume(sweeps, refs["fasteners"]), "HOLD_ACTUAL_TRANSFORMS_REFERENCE_ZERO"),
    ]
    rows = [{"check": name, "common_volume_mm3": round(value, 9), "status": status if value <= 1e-7 else "FAIL"}
            for name, value, status in raw]
    return {"method": "CADQUERY_ACTUAL_COMMON_VOLUME_REFERENCE_SOLIDS", "rows": rows,
            "all_zero_reference": all(row["common_volume_mm3"] == 0.0 for row in rows),
            "physical_fit": "USER_TEST_PENDING", "actual_transform_rows_remain_hold": 6}


def width_comparison() -> list[dict[str, Any]]:
    return [{"candidate": f"Y{int(y)}", "outer_y_mm": y, "nominal_clearance_each_mm": (100 - y) / 2,
             "clearance_each_at_minus_1mm_frame_mm": (99 - y) / 2,
             "internal_usable_y_mm": y - 6.4, "selected": y == 92,
             "implication": "MAX_SERVICE_MARGIN" if y == 90 else ("BALANCED_SELECTED" if y == 92 else "HISTORY_MAX_VOLUME_LOW_MARGIN")}
            for y in (90.0, 92.0, 94.0)]


def stl_semantic(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise RuntimeError(f"bad STL {path}")
    mins, maxs = [float("inf")] * 3, [float("-inf")] * 3
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + 50 * index)
        for offset in (3, 6, 9):
            for axis in range(3):
                value = values[offset + axis]
                mins[axis], maxs[axis] = min(mins[axis], value), max(maxs[axis], value)
    return {"triangles": count, "bounds_mm": [round(maxs[i] - mins[i], 3) for i in range(3)]}


def printability() -> dict[str, Any]:
    shapes = {
        "BBOX_LOWER_BODY": bbox_body(), "BBOX_SERVICE_RING": bbox_ring(), "BBOX_WEAR_PAD": wear_pad(True),
        "BBOX_CONNECTOR_PANEL": bbox_connector_panel(), "BBOX_RESTRAINT_KIT": bbox_restraint_print_kit(),
        "BBOX_PLATE_01": bbox_plate(), "CBOX_BODY": cbox_body(), "CBOX_LID": cbox_lid(),
        "CBOX_TRAY": cbox_tray(), "CBOX_CONNECTOR_PANEL": cbox_connector_panel(),
        "CBOX_FRAME_INTERFACE": cbox_mount_interface(), "CBOX_GASKET_COUPON": cbox_gasket_coupon(),
        "CBOX_PLATE_02": cbox_plate(),
    }
    rows = {}
    for name, shape in shapes.items():
        bb = shape.val().BoundingBox() if isinstance(shape, cq.Workplane) else shape.BoundingBox()
        rows[name] = {"bounds_mm": [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)],
                      "fits_bambu_a1_xy": bb.xlen <= 256 and bb.ylen <= 256,
                      "orientation": "BOTTOM_OR_FLAT_ON_PLATE_OPEN_UP",
                      "support": "SUPPORT_FREE_CANDIDATE_SLICER_CONFIRMATION_REQUIRED"}
    plate_overlaps = {"BBOX_PLATE_01": round(maximum_pairwise_volume(bbox_plate_components()), 9),
                      "CBOX_PLATE_02": round(maximum_pairwise_volume(cbox_plate_components()), 9)}
    return {"printer": "Bambu A1", "material": "PETG", "bed_mm": [256, 256], "rows": rows,
            "all_fit": all(row["fits_bambu_a1_xy"] for row in rows.values()),
            "plate_component_common_volume_mm3": plate_overlaps,
            "plate_components_clear": all(value == 0 for value in plate_overlaps.values()),
            "sealing_face_support_contact": False, "slicer_confirmation": "USER_REQUIRED",
            "large_shell_warping": "HIGH_RISK_BRIM_AND_TUNING_CANDIDATE"}


def dimensions() -> dict[str, Any]:
    return {"version": VERSION, "unit": "mm", "coordinate_system": {"+X": "front", "+Y": "left", "+Z": "up"},
            "frame": FRAME, "battery": BATTERY, "terminal": TERMINAL, "bbox": BBOX, "cbox": CBOX,
            "cbox_width_comparison": width_comparison(),
            "layout": {"bbox_x_interval_mm": [-190, -10], "gap_mm": 20, "cbox_x_interval_mm": [10, 190]}}


def interfaces() -> dict[str, Any]:
    return {"bbox": {"load_path": "BATTERY_BROAD_FLOOR_RIBS_SHELL_SKID_METAL_FRAME",
                     "removal": "PITCH_AND_SLIDE_MINUS_X", "friction_only_lock": "REJECT",
                     "idler_support": False, "terminal_module": "REPLACEABLE_CAP_AND_BLANK_PANEL",
                     "wear_surface": "REPLACEABLE_PAD_NOT_SEALING_FACE"},
            "cbox": {"load_path": "SHELL_REINFORCED_INTERFACE_METAL_BRACKET_2020_FRAME",
                     "independent_of_bbox": True, "petg_cantilever_primary_support": "REJECT",
                     "tray": "REMOVABLE_NO_SHELL_THROUGH_HOLES", "connector": "REPLACEABLE_BLANK"},
            "separation": {"shared_lid": False, "cbox_load_through_bbox": False,
                           "bbox_removal_without_opening_cbox": True},
            "approvals": {"powered_rotation": False, "field_deployment": False}}


def hardware() -> dict[str, Any]:
    return {"bbox": {"service_ring_fastener": "M4_CANDIDATE_BROAD_BOSS", "primary_lock": "RESERVED_HOLD",
                     "safety_pin": "RESERVED_HOLD", "connector_type": "HOLD", "wear_pad_material": "PETG_PROTOTYPE",
                     "future_wear_materials": ["POM", "UHMW-PE"]},
            "cbox": {"lid_fastener": "M4_CANDIDATE", "lid_fastener_count": 16,
                     "max_unsupported_gasket_span_mm": 36, "gasket_material": "TPU95A_FUTURE_CANDIDATE",
                     "mount_primary": "METAL_BRACKET_REQUIRED", "electronics_pattern": "UNIVERSAL_M3_SLOT_GRID"}}


def service_motions() -> dict[str, Any]:
    return {"bbox": {"direction": "-X", "method": "PITCH_AND_SLIDE", "angles_deg": [0, 2, 4, 6],
                     "reference_translation_minus_x_mm": [0, 125, 195, 220],
                     "actual_pitch": "PHYSICAL_TEST_REQUIRED", "straight_only_required": False,
                     "full_removal_cycles_required": 10},
            "cbox": {"fixed_during_bbox_service": True, "lid_service_translation_plus_z_mm": [0, 29.2, 59.2],
                     "bbox_removal_required_for_lid": False}}


def measurement_ledger() -> dict[str, Any]:
    rows = [
        {"id": "FR-01", "name": "UPPER_OUTER", "value": [540, 181], "class": "MEASURED"},
        {"id": "FR-02", "name": "LOWER_OUTER", "value": [442, 181], "class": "MEASURED"},
        {"id": "FR-03", "name": "STRUCTURAL_HEIGHT", "value": 150, "class": "MEASURED"},
        {"id": "FR-04", "name": "UPPER_CLEAR", "value": [500, 100], "class": "MEASURED"},
        {"id": "FR-05", "name": "LOWER_CLEAR", "value": [400, 140], "class": "MEASURED"},
        {"id": "BAT-01", "name": "BATTERY_BODY", "value": [150.9, 99.4, 92.5], "class": "MEASURED_USER_REPORTED"},
        {"id": "BAT-02", "name": "BATTERY_MASS", "value": 1.2, "class": "MEASURED_USER_REPORTED"},
        {"id": "BAT-03", "name": "INSERTION_PASSAGE", "value": 108.0, "class": "MEASURED_DIFFERENT_DATUM"},
        {"id": "TER-01", "name": "PAIR_OUTER_SPAN", "value": 29.5, "class": "MEASURED_USER_REPORTED"},
        {"id": "TER-02", "name": "INNER_GAP", "value": 20.0, "class": "MEASURED_USER_REPORTED"},
        {"id": "TER-03", "name": "INDIVIDUAL_WIDTH", "value": None, "class": "NOT_DERIVED"},
        {"id": "DER-01", "name": "BBOX_INNER_Y", "value": 107.6, "class": "DERIVED_CANDIDATE"},
        {"id": "DER-02", "name": "BBOX_Y_CLEAR_EACH", "value": 4.1, "class": "DERIVED_CANDIDATE"},
        {"id": "DER-03", "name": "BBOX_PASSAGE_Z_CLEAR", "value": 5.0, "class": "DERIVED_CANDIDATE"},
    ]
    return {"schema": "paddy_swarm.common_rover.bbox_cbox.measurement.v0.9.5.0", "rows": rows}


def test_limits() -> dict[str, Any]:
    return {"bbox": {"passage_mm": 108, "service_envelope_max_mm": 103, "cycles": 10,
                     "fit": ["INSERT", "REMOVE", "SIDE_PLAY", "TERMINAL_CLEARANCE", "PAD_CONTACT", "GRIP"],
                     "water_stages": ["VISUAL", "EMPTY_SPLASH", "EMPTY_STANDING_WATER", "TEMPORARY_IMMERSION", "PAPER_INSPECTION"]},
            "cbox": {"width_candidates_mm": [90, 92, 94], "frame_tolerance_adverse_mm": -1,
                     "gasket_coupon_mm": [2.0, 2.5, 3.0], "waterproof": "PHYSICAL_TEST_REQUIRED"},
            "printer": {"name": "Bambu A1", "bed_mm": [256, 256], "material": "PETG",
                        "support_auto_detection_trusted": False}}


def geometry_manifest() -> dict[str, Any]:
    return {"schema": "paddy_swarm.common_rover.bbox_cbox.geometry.v0.9.5.0", "version": VERSION,
            "classification": CLASSIFICATION, "release": RELEASE, "cad_count": len(CAD),
            "step_count": len([p for p in CAD if p.endswith(".step")]),
            "stl_count": len([p for p in CAD if p.endswith(".stl")]),
            "interference": interference_report(), "printability": printability(),
            "cbox_width_comparison": width_comparison(), "parents": parent_audit(),
            "waterproof_pass": False, "powered_rotation": False, "field_deployment": False}


def validation() -> dict[str, Any]:
    gates = {
        "BBOX_LOWER_BODY": "PRINT_READY_CANDIDATE", "BBOX_SERVICE_RING": "PRINT_READY_CANDIDATE",
        "BBOX_WEAR_PADS": "PRINT_READY_CANDIDATE", "BBOX_BOTTOM_GRIP": "PRINT_READY_CANDIDATE",
        "BBOX_CONNECTOR_BLANK": "PRINT_READY_CANDIDATE", "BBOX_TERMINAL_CAP": "HOLD",
        "BBOX_PHYSICAL_FIT": "USER_TEST_PENDING", "BBOX_FINAL_WATERPROOF": "HOLD_PHYSICAL_TEST_REQUIRED",
        "CBOX_BODY": "PRINT_READY_CANDIDATE", "CBOX_LID": "PRINT_READY_CANDIDATE",
        "CBOX_TRAY": "PRINT_READY_CANDIDATE", "CBOX_CONNECTOR_BLANK": "PRINT_READY_CANDIDATE",
        "CBOX_FINAL_ELECTRONICS": "HOLD", "CBOX_WATERPROOF": "PHYSICAL_TEST_REQUIRED",
        "POWERED_ROTATION": "NOT_APPROVED", "FIELD_DEPLOYMENT": "NOT_APPROVED",
    }
    missing = ["TERMINAL_EXACT_X", "TERMINAL_EXACT_Y", "TERMINAL_PROTRUSION_Z", "CABLE_LUG_ENVELOPE",
               "CABLE_BEND_RADIUS", "FINAL_BBOX_CONNECTOR", "FINAL_SUPPORT_RAIL_Z", "FINAL_GASKET_COMPRESSION",
               "FINAL_BBOX_MASS", "CBOX_PCB_DIMENSIONS", "CBOX_HEAT_GENERATION", "ABSOLUTE_GROUND_FRAME_Z"]
    return {"version": VERSION, "classification": CLASSIFICATION, "release": RELEASE, "gates": gates,
            "missing_nonblocking": missing, "cad_complete": True, "physical_fit_complete": False,
            "waterproof_pass": False, "battery_operational_approved": False, "electronics_operational_approved": False,
            "powered_rotation_approved": False, "field_approved": False, "final_status": FINAL_STATUS}


def header(title: str) -> str:
    return f"# {title}\n\nVersion: `{VERSION}`  \nClassification: `{CLASSIFICATION}`  \nRelease: `{RELEASE}`  \nStatus: `{FINAL_STATUS}`\n"


def source_trace() -> list[dict[str, str]]:
    rels = [
        "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0/PHYSICAL_FRAME_REFERENCE.md",
        "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0/BBOX_CBOX_ARCHITECTURE.md",
        "cad/common_rover/common_rover_190mm_frame_h25a1_2s_bbox_cbox_integration_v0_9_4_1/BBOX_CBOX_X_SERIAL_LAYOUT.md",
        "cad/common_rover/common_rover_190mm_frame_h25a1_2s_bbox_cbox_integration_v0_9_4_1/CBOX_ARCHITECTURE.md",
        "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2/PHYSICAL_FRAME_150_RECORD.md",
        "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2/BATTERY_INSERTION_CLEARANCE.md",
        "cad/common_rover/common_rover_service_motion_servo_slide_clutch_h25a1_v0_9_4_3/BBOX_PITCH_AND_SLIDE_SERVICE.md",
        "cad/common_rover/common_rover_service_motion_servo_slide_clutch_h25a1_v0_9_4_3/BBOX_TOP_GUIDE_ARCHITECTURE.md",
        "cad/common_rover/common_rover_h25a1_2s_full_hardware_fixture_v0_9_4_4/MANIFEST.txt",
    ]
    return [{"path": rel, "sha256": sha(REPO_ROOT / rel)} for rel in rels]


def documents(valid: dict[str, Any], geom: dict[str, Any]) -> dict[str, str]:
    h = header
    widths = width_comparison()
    rows = geom["interference"]["rows"]
    d: dict[str, str] = {}
    d["README.md"] = h("Common Rover BBOX + CBOX printable prototype") + "\nPrintable PETG BBOX/CBOX physical-fit artifacts for the 150 mm compact frame. CAD_PASS is neither WATERPROOF_PASS nor operational approval.\n"
    d["PARENT_AUDIT.md"] = h("Parent audit") + "\n" + "\n".join(f"- `{k}`: {v[0]} files, tree `{v[1]}`, PASS" for k, v in PARENT_TREES.items()) + "\n"
    d["SOURCE_TRACE.md"] = h("Source trace") + "\n" + "\n".join(f"- `{r['path']}` — `{r['sha256']}`" for r in source_trace()) + "\n"
    d["FRAME_REFERENCE.md"] = h("150 mm physical frame") + "\nUpper outer 540×181, lower outer 442×181, structural height150, upper clear500×100, lower clear400×140 and four110 mm verticals are MEASURED. Tolerance≈±1 mm. Frame-relative dimensions govern; 190 mm frame remains ALTERNATIVE_HOLD.\n"
    d["BATTERY_REFERENCE.md"] = h("Battery authority") + "\nGOLDENMATE LiFePO4 12.8 V 10 Ah 128 Wh: 150.9×99.4×92.5 mm, 1.2 kg MEASURED/USER_REPORTED. Terminal-equipped battery passage is PHYSICAL_PASS_USER_REPORTED; no operational approval is inferred.\n"
    d["BATTERY_TERMINAL_REFERENCE.md"] = h("Terminal authority") + "\nPair outer span29.5 mm and inner gap20.0 mm are measured. Individual width is `NOT_DERIVED`. Exact X/Y/Z, lug, boot and cable bend remain HOLD.\n"
    d["BBOX_ARCHITECTURE.md"] = h("BBOX architecture") + "\nRear/low removable cassette, extraction −X by PITCH_AND_SLIDE. Modular lower body, removable ring, two replaceable pads, replaceable restraint kit, recessed grip and blank panel prevent terminal changes from forcing a complete shell reprint. Idler support and friction-only retention are rejected.\n"
    d["BBOX_DIMENSION_AUTHORITY.md"] = h("BBOX dimensions") + "\nPrototype target180×114×103 mm. Split: lower97.5 + ring3.0 + wear pad2.5 =103.0. PETG wall/floor3.2 mm. Values are physical-fit candidates, not waterproof release.\n"
    d["BBOX_BATTERY_CAVITY.md"] = h("BBOX battery cavity") + "\nNominal cavity173.6×107.6 mm; Y free8.2 total/4.1 each. Rear grip/backer consumes selected X service volume. Battery rests at Z4.0 on three broad0.8 mm ribs; replaceable pads retain 0.25 mm nominal clearances and do not hard press-fit.\n"
    d["BBOX_TERMINAL_OPENING.md"] = h("BBOX terminal opening") + "\nW335/W345/W355 compare33.5/34.5/35.5 mm. W345 is the starting CAD candidate. Its XY origin is explicitly parametric; final cap and manufacturing STL remain HOLD until terminal XYZ, lug and cable envelope are measured.\n"
    d["BBOX_SERVICE_RING.md"] = h("BBOX service ring") + "\nA removable3.0 mm structural perimeter ring uses four M4 candidate wall-adjacent bosses. It supports pads and future small cap/panel interfaces. Seal compression remains unselected; no weak terminal neck is released.\n"
    d["BBOX_WEAR_PAD.md"] = h("BBOX wear pads") + "\nLeft/right72×8×2.5 mm PETG prototype pads are separate and lead-in rounded. Load hierarchy: frame underside→pad→structural ring/shoulder. Waterproof faces never serve as wear faces. POM/UHMW-PE remain future candidates.\n"
    d["BBOX_BOTTOM_GRIP.md"] = h("BBOX bottom grip") + "\nA recessed R9.5 circular-arch grip pocket gives an18 mm-class recess in a22×70×24 mm rear block. At least3.5 mm floor and4.5 mm inner barrier remain; the block carries load broadly into floor/rear structure without a large external handle.\n"
    d["BBOX_RAIL_INTERFACE.md"] = h("BBOX rail interface") + "\n130/132/134 mm are retained. For140 mm lower clear they provide5/4/3 mm nominal per side. 130/132 are candidates;134 is reference-only. Final metal rail/skid Z and primary lock/safety pin remain HOLD.\n"
    d["BBOX_CONNECTOR_PANEL.md"] = h("BBOX connector panel") + "\nA removable30×50×3.2 mm blank panel sits flush in a thick sealed backer. The main shell has no final connector penetration. M3 candidate holes are outside any released gasket claim; connector type remains HOLD.\n"
    d["BBOX_SERVICE_MOTION.md"] = h("BBOX PITCH_AND_SLIDE") + "\nReference stages are0°/0,2°/−125,4°/−195,6°/−220 mm. Translation precedes pitch so the finite upper rail edge remains clear in the simplified CAD. Actual pitch, hand path, crawler/idler/KP000 transforms and10-cycle performance require physical test.\n"
    d["BBOX_PHYSICAL_TEST_PLAN.md"] = h("BBOX physical tests") + "\nInstall actual battery, verify insert/remove, side play, terminal clearance, pad/frame contact and grip. Execute10 PITCH_AND_SLIDE cycles; stop on hard contact, crack, whitening, trapped battery or excessive play. Empty-shell water stages: visual, splash, standing water, temporary immersion, then internal paper inspection.\n"
    d["BBOX_PHYSICAL_RESULT_FORM.md"] = h("BBOX result form") + "\n[BATTERY FIT]\ninsert YES/NO: ____  remove YES/NO: ____  side play NONE/SLIGHT/EXCESSIVE: ____  terminal GOOD/MARGINAL/BAD: ____\n\n[BBOX FRAME]\nstraight removal YES/NO: ____  pitch-and-slide YES/NO: ____  top contact NONE/LIGHT/HARD: ____  wear-pad contact NONE/LIGHT/HARD: ____  bottom grip GOOD/MARGINAL/BAD: ____  10 cycles PASS/FAIL: ____  damage NONE/DETAIL: ____\n"
    d["CBOX_ARCHITECTURE.md"] = h("CBOX architecture") + "\nFront/high/fixed180×92×45 mm universal enclosure. Body, flat lid, continuous land, removable tray, blank connector panel and independent frame interface are modular. BBOX lid carries no CBOX load.\n"
    d["CBOX_WIDTH_COMPARISON.md"] = h("CBOX width comparison") + "\n|ID|Outer Y|Nominal/side|At clear99/side|Internal Y|Decision|\n|---|---:|---:|---:|---:|---|\n" + "\n".join(f"|{r['candidate']}|{r['outer_y_mm']:.0f}|{r['nominal_clearance_each_mm']:.1f}|{r['clearance_each_at_minus_1mm_frame_mm']:.1f}|{r['internal_usable_y_mm']:.1f}|{r['implication']}|" for r in widths) + "\n\nY92 balances3.5 mm/side adverse clearance with85.6 mm internal width; Y94 history remains recorded.\n"
    d["CBOX_LID_AND_GASKET.md"] = h("CBOX lid and gasket") + "\nBody40.0 + compressed gasket reference0.8 + lid4.2 =45.0 mm. A continuous outer perimeter land has no screw interruption. Sixteen M4 candidate holes lie inside the seal loop; maximum reference unsupported span is36 mm. G20/G25/G30 coupons precede any gasket selection or waterproof claim.\n"
    d["CBOX_UNIVERSAL_TRAY.md"] = h("CBOX universal tray") + "\nA removable160×72×2.4 mm tray provides M3 slots, four shell-blind mounting references, PCB stand-off zones and routing space. No electronics-specific shell hole is released.\n"
    d["CBOX_CONNECTOR_PANEL.md"] = h("CBOX connector panel") + "\nA removable24×44×3.0 mm blank panel is flush-mounted against a thick sealed front backer. Final connector cutting is confined to the replaceable part after selection.\n"
    d["CBOX_FRAME_SUPPORT.md"] = h("CBOX frame support") + "\nLoad path is shell reinforced interface→metal washer/bracket→2020 bridge/frame. Printed rails are adjustment/interface prototypes only; a PETG cantilever as sole primary support is REJECTED.\n"
    d["CBOX_THERMAL_RESERVATION.md"] = h("CBOX thermal reservation") + "\nThe lid retains an unpierced approximately100×60 mm central flat reservation for a future external heat spreader/radiative treatment. PCB layout and heat generation remain HOLD.\n"
    d["CBOX_PHYSICAL_TEST_PLAN.md"] = h("CBOX physical tests") + "\nCheck body, lid, tray, blank panel, frame fit, lid service with BBOX installed and seal flatness. Only an empty shell proceeds through visual, splash, standing-water, temporary-immersion and paper-inspection stages.\n"
    d["CBOX_PHYSICAL_RESULT_FORM.md"] = h("CBOX result form") + "\nbody PASS/FAIL: ____  lid PASS/FAIL: ____  tray PASS/FAIL: ____  connector panel PASS/FAIL: ____  frame fit PASS/FAIL: ____  lid service with BBOX YES/NO: ____  seal flatness PASS/FAIL: ____  water test NOT_TESTED/PASS/FAIL: ____\n"
    d["BBOX_CBOX_INTEGRATION.md"] = h("BBOX/CBOX X-serial integration") + "\nLayout A remains BBOX X[−190,−10],20 mm gap,CBOX X[10,190]. CBOX is at frame-relative high Z and independent. BBOX removal never requires opening CBOX; there is no shared lid or vertical load path.\n"
    d["INTERFERENCE_REPORT.md"] = h("Reference interference report") + "\n" + "\n".join(f"- `{r['check']}`: {r['common_volume_mm3']:.9f} mm³ — `{r['status']}`" for r in rows) + "\n\nAll simplified reference common volumes are zero. Rows marked HOLD do not become physical PASS until actual transforms and fasteners are measured.\n"
    d["PRINT_RISK_REPORT.md"] = h("PETG print risks") + "\nLarge180 mm shells have HIGH warping/tall-wall risk: dry PETG, tuned flow, brim candidate and conservative acceleration. BBOX grip uses a circular self-supporting arch; CBOX top flange uses a45° internal transition. No sealing face is intentionally support-contacted. Automatic support detection is not trusted; inspect sliced layers.\n"
    p = geom["printability"]
    d["PRINT_PLAN.md"] = h("Bambu A1 print plan") + "\nBody parts print bottom-down/open-up; ring, pads, panels, tray and lid print flat. Lid exterior faces the bed so the gasket face remains support-free. All generated print parts fit256×256 mm.\n\n" + "\n".join(f"- `{k}`: {v['bounds_mm']} mm" for k, v in p["rows"].items()) + "\n"
    d["MISSING_MEASUREMENTS.md"] = h("Missing non-blocking measurements") + "\n" + "\n".join(f"- `{x}`: HOLD" for x in valid["missing_nonblocking"]) + "\n"
    d["DESIGN_GATE.md"] = h("Design gates") + "\n" + "\n".join(f"- `{k}`: `{v}`" for k, v in valid["gates"].items()) + "\n\nCAD_PASS is not WATERPROOF_PASS, powered approval or field approval.\n"
    return d


def svg(title: str, body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560"><style>text{{font-family:Arial;fill:#17212b}}.b{{fill:#d9eafd;stroke:#245b8a;stroke-width:2}}.c{{fill:#e5f4df;stroke:#477d38;stroke-width:2}}.h{{fill:#fde2e2;stroke:#a33;stroke-width:2}}.u{{fill:#fff2b2;stroke:#a26f00;stroke-dasharray:8 5}}.f{{fill:none;stroke:#334e68;stroke-width:2}}.a{{stroke:#168aad;stroke-width:4;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#168aad"/></marker></defs><rect width="100%" height="100%" fill="#fbfcfe"/><text x="24" y="34" font-size="22">{title}</text>{body}<text x="24" y="538" font-size="13">v0.9.5.0 · PHYSICAL PROTOTYPE · HOLD · NOT WATERPROOF/POWERED/FIELD APPROVED</text></svg>'


def drawings() -> None:
    values = {
        "bbox_top.svg": '<rect class="b" x="140" y="140" width="720" height="228" rx="20"/><rect class="f" x="166" y="153" width="668" height="202"/><text x="420" y="405">180 × 114</text>',
        "bbox_side.svg": '<rect class="b" x="120" y="170" width="720" height="310"/><rect class="c" x="120" y="160" width="720" height="10"/><rect class="u" x="230" y="470" width="210" height="-60"/><text x="380" y="135">97.5 + 3.0 + 2.5 = 103</text>',
        "bbox_front.svg": '<rect class="b" x="230" y="120" width="540" height="360"/><rect class="h" x="390" y="340" width="220" height="90" rx="42"/><text x="400" y="95">Y114 / Z103</text>',
        "bbox_section.svg": '<rect class="b" x="150" y="110" width="700" height="380"/><rect class="f" x="180" y="135" width="640" height="330"/><rect class="h" x="225" y="155" width="550" height="295"/><text x="620" y="190">wall/floor 3.2</text><text x="620" y="230">battery 92.5</text>',
        "bbox_battery_fit.svg": '<rect class="b" x="120" y="120" width="760" height="350"/><rect class="h" x="215" y="145" width="640" height="305"/><text x="370" y="505">Y clearance 4.1 / side</text>',
        "bbox_terminal_keepout.svg": '<rect class="u" x="110" y="180" width="200" height="160"/><rect class="u" x="400" y="175" width="210" height="170"/><rect class="u" x="700" y="170" width="220" height="180"/><text x="170" y="380">W335</text><text x="465" y="380">W345 selected candidate</text><text x="770" y="380">W355</text>',
        "bbox_pitch_slide.svg": '<rect class="b" x="500" y="270" width="320" height="180"/><path class="a" d="M500 360H120"/><path class="f" d="M400 260L90 220"/><text x="150" y="480">0/2/4/6° after −X translation</text>',
        "bbox_bottom_grip.svg": '<rect class="b" x="150" y="120" width="700" height="360"/><circle class="h" cx="250" cy="365" r="78"/><text x="390" y="360">R9.5 recessed arch</text><text x="390" y="400">broad rear block load path</text>',
        "cbox_top.svg": '<rect class="c" x="140" y="150" width="720" height="184" rx="20"/><rect class="f" x="160" y="164" width="680" height="156"/><text x="390" y="390">180 × 92 · 16 M4 candidates</text>',
        "cbox_side.svg": '<rect class="c" x="130" y="250" width="720" height="160"/><rect class="u" x="130" y="230" width="720" height="20"/><text x="390" y="455">40 + 0.8 + 4.2 = 45</text>',
        "cbox_front.svg": '<rect class="c" x="260" y="170" width="480" height="230"/><rect class="h" x="560" y="240" width="150" height="110"/><text x="360" y="450">Y92 / Z45</text>',
        "cbox_section.svg": '<path class="c" d="M150 150V440H850V150H800V375H200V150Z"/><path class="u" d="M150 135H850V150H150Z"/><text x="300" y="105">continuous outer sealing land</text>',
        "cbox_tray.svg": '<rect class="c" x="140" y="150" width="720" height="300"/><path class="f" d="M210 210H790M210 270H790M210 330H790M210 390H790"/><text x="370" y="495">160×72 removable M3 slot grid</text>',
        "cbox_mount.svg": '<rect class="c" x="220" y="150" width="560" height="160"/><path class="f" d="M240 360H760M240 400H760"/><text x="250" y="455">metal bracket / 2020 bridge required</text>',
        "bbox_cbox_x_serial.svg": '<rect class="b" x="90" y="210" width="380" height="180"/><rect class="c" x="530" y="210" width="380" height="180"/><text x="180" y="430">BBOX [−190,−10]</text><text x="610" y="430">CBOX [10,190]</text><text x="475" y="300">20</text>',
        "bbox_service_sweep.svg": '<rect class="c" x="620" y="130" width="300" height="140"/><path class="a" d="M570 350H100"/><path class="b" d="M450 290L150 250L130 390L430 430Z"/><text x="630" y="320">CBOX fixed</text>',
        "sealing_land.svg": '<rect class="c" x="120" y="120" width="760" height="320" rx="25"/><rect class="f" x="150" y="150" width="700" height="260" rx="18"/><rect class="u" x="170" y="170" width="660" height="220" rx="12"/><text x="300" y="490">continuous land · holes inside seal loop</text>',
    }
    for name, body in values.items():
        write(LANE / "drawings" / name, svg(name.replace("_", " "), body))


def build() -> dict[str, Any]:
    before = repository_guard(False)
    for shape, rel in artifact_jobs():
        export(shape, LANE / rel)
    drawings()
    geom, valid = geometry_manifest(), validation()
    payloads = {"dimensions.json": dimensions(), "interfaces.json": interfaces(), "hardware.json": hardware(),
                "service_motions.json": service_motions(), "measurement_ledger.json": measurement_ledger(),
                "test_limits.json": test_limits(), "geometry_manifest.json": geom, "validation_report.json": valid}
    for name, value in payloads.items():
        write_json(LANE / name, value)
    for name, value in documents(valid, geom).items():
        write(LANE / name, value)
    write(LANE / "MANIFEST.txt", "\n".join(PACKAGE_PATHS))
    write(LANE / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL}/{p}" for p in PACKAGE_PATHS))
    write(LANE / "BUILD_LOG.txt", f"BUILD PASS\nversion={VERSION}\nPython={sys.version.split()[0]}\nCadQuery={cq.__version__}\npreflight_untracked={before['untracked_total']}\noutside_untracked={before['outside_untracked']}\nparent_lanes=5_PASS\nwaterproof=HOLD\npowered=NOT_APPROVED\nfield=NOT_APPROVED")
    write(LANE / "TEST_LOG.txt", "PENDING_TEST_EXECUTION")
    hashed = [p for p in PACKAGE_PATHS if p != "SHA256SUMS.txt"]
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / p)}  {p}" for p in hashed))
    test = subprocess.run([sys.executable, "-B", str(LANE / SOURCE[1])], cwd=REPO_ROOT,
                          text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if test.returncode:
        raise RuntimeError(test.stdout)
    write(LANE / "TEST_LOG.txt", test.stdout)
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / p)}  {p}" for p in hashed))
    return {"status": "CAD_PASS", "guard": repository_guard(True), "validation": valid}


def verify_files() -> dict[str, Any]:
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    missing, extras = sorted(set(PACKAGE_PATHS) - set(files)), sorted(set(files) - set(PACKAGE_PATHS))
    manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    hashes = {}
    for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        hashes[rel] = digest
    bad = [rel for rel, digest in hashes.items() if sha(LANE / rel) != digest]
    steps = {rel: cq.importers.importStep(str(LANE / rel)).val() for rel in CAD if rel.endswith(".step")}
    stls = {rel: stl_semantic(LANE / rel) for rel in CAD if rel.endswith(".stl")}
    for rel in DRAWINGS:
        ET.parse(LANE / rel)
    dim = json.loads((LANE / "dimensions.json").read_text(encoding="utf-8"))
    geom = json.loads((LANE / "geometry_manifest.json").read_text(encoding="utf-8"))
    valid = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
    checks = {
        "package": not missing and not extras and manifest == PACKAGE_PATHS,
        "hashes": not bad and set(hashes) == set(PACKAGE_PATHS) - {"SHA256SUMS.txt"},
        "cad_counts": len(steps) == 26 and len(stls) == 14,
        "step_reload": all(shape.isValid() and shape.Volume() > 0 for shape in steps.values()),
        "stl_semantic": all(row["triangles"] > 0 and all(v > 0 for v in row["bounds_mm"]) for row in stls.values()),
        "svg_parse": len(DRAWINGS) == 17, "frame": dim["frame"] == FRAME,
        "battery": dim["battery"] == BATTERY, "terminal": dim["terminal"] == TERMINAL,
        "bbox": dim["bbox"] == BBOX, "cbox": dim["cbox"] == CBOX,
        "interference": geom["interference"]["all_zero_reference"],
        "printability": geom["printability"]["all_fit"] and geom["printability"]["plate_components_clear"],
        "release": not valid["waterproof_pass"] and not valid["powered_rotation_approved"] and not valid["field_approved"],
    }
    if not all(checks.values()):
        raise RuntimeError({"checks": checks, "missing": missing, "extras": extras, "bad": bad})
    return {"status": "CAD_PASS", "file_count": len(files), "step_count": len(steps), "stl_count": len(stls),
            "svg_count": len(DRAWINGS), "checks": checks, "bad_hashes": bad}


def standalone_rebuild() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ps_cr_v0950_a_") as a, tempfile.TemporaryDirectory(prefix="ps_cr_v0950_b_") as b:
        aa, bb = Path(a), Path(b)
        for shape, rel in artifact_jobs():
            export(shape, aa / rel)
        for shape, rel in artifact_jobs():
            export(shape, bb / rel)
        equal = {rel: sha(aa / rel) == sha(bb / rel) for rel in CAD}
        steps = {rel: cq.importers.importStep(str(aa / rel)).val().isValid() for rel in CAD if rel.endswith(".step")}
        stls = {rel: stl_semantic(aa / rel) for rel in CAD if rel.endswith(".stl")}
        checks = {"outputs": len(equal) == len(CAD), "byte_reproducible": all(equal.values()),
                  "step_reload": all(steps.values()), "stl_semantic": len(stls) == 14}
        if not all(checks.values()):
            raise RuntimeError({"checks": checks, "equal": equal})
        return {"status": "CAD_PASS", "artifact_count": len(equal), "step_count": len(steps),
                "stl_count": len(stls), "checks": checks}


def make_zip() -> tuple[Path, str]:
    path = DOWNLOADS / f"{ZIP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise FileExistsError(path)
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as archive:
        for rel in PACKAGE_PATHS:
            archive.write(LANE / rel, rel)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        bad = [n for n in names if PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts]
        if archive.testzip() or len(names) != len(set(names)) or bad or sorted(names) != PACKAGE_PATHS:
            raise RuntimeError("ZIP contract")
        if archive.read("MANIFEST.txt").decode("utf-8").splitlines() != PACKAGE_PATHS:
            raise RuntimeError("ZIP manifest")
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            if hashlib.sha256(archive.read(rel)).hexdigest() != digest:
                raise RuntimeError(f"ZIP hash: {rel}")
    return path, sha(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--standalone-rebuild", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        args.build = args.verify = True
    result: dict[str, Any] = {}
    if args.build:
        result["build"] = build()
    if args.verify:
        result["guard"] = repository_guard(True)
        result["verify"] = verify_files()
    if args.standalone_rebuild:
        result["standalone_rebuild"] = standalone_rebuild()
    if args.zip:
        path, digest = make_zip()
        result["zip"] = {"path": str(path), "sha256": digest}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
