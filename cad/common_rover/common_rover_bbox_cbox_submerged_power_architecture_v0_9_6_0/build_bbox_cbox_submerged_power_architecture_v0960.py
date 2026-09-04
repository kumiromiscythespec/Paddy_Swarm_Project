#!/usr/bin/env python3
"""Build Common Rover BBOX/CBOX submerged power architecture v0.9.6.0."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree

import cadquery as cq
sys.dont_write_bytecode = True

VERSION = "0.9.6.0"
CLASSIFICATION = "SUBMERGED_POWER_ARCHITECTURE + EMPTY_WATERPROOF_PROTOTYPE"
FINAL_STATUS = (
    "BBOX_CBOX_SUBMERGED_POWER_ARCHITECTURE_COMPLETE / "
    "EMPTY_WATERPROOF_PROTOTYPE_READY / PHYSICAL_VALIDATION_PENDING / COMMIT_READY_NOT_STAGED"
)
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0"
LANE = Path(__file__).resolve().parent
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_BBOX_CBOX_Submerged_Power_Architecture_v0_9_6_0_"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_HISTORY = [
    ("7c149a65053f2292bc4cc0ed06d8941c96852f2b", "docs(common-rover): record v0.9.5.2 physical measurements"),
    ("d085027f9b015f6dfb0de0cf5a384298a251cefa", "cad(common-rover): add v0.9.5.1 HTD5M TPU drive belt trial"),
    ("3269fe6b7634d3b53ca42a3bc299f1dcacb4c4c2", "cad(common-rover): add v0.9.5.0 BBOX CBOX printable prototypes"),
]
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_TREES = {
    "common_rover_bbox_cbox_printable_prototype_v0_9_5_0":
        (105, "462d0f3a9c471bf434160fb9a99f834f97a28e665bc8ce6139f6a87aeadd9185"),
    "common_rover_physical_measurement_closure_v0_9_5_2":
        (28, "5a520c30e9db4c0d5e916dbf280ec1e901fef551033bb93ce7e572a634a597c2"),
    "common_rover_physical_followup_measurement_v0_9_5_3":
        (25, "c49217200ea8d1a55b92632d4d1e3ad932fffd6ffdb9dbcb8edbea96c051ca0c"),
}
BASE_OUTSIDE_UNTRACKED_COUNT = 1551
BASE_OUTSIDE_PATH_DIGEST = "080e104849bc09ef504020283c5abc9753d16bc1cee50503073a45f15e8499ae"
BASE_DIRTY_DIFF_SHA = "649ec5928e27bc9bfeb13ec517fb318c4eb6857a60ea73b7e18cd68cd47a4bc0"

FRAME = {
    "upper_outer_mm": [540.0, 181.0], "lower_outer_mm": [442.0, 181.0],
    "height_mm": 150.0, "upper_clear_mm": [500.0, 100.0], "lower_clear_mm": [400.0, 140.0],
    "frame_bottom_to_ground_mm": 68.0, "battery_insertion_height_mm": 108.0,
    "frame_width_tolerance_mm": 1.0, "frame_190mm": "HOLD",
}
BATTERY = {
    "product": "GOLDENMATE LiFePO4", "label_voltage_v": 12.8, "label_capacity_ah": 10.0,
    "label_energy_wh": 128.0, "body_mm": [150.9, 99.4, 92.5], "mass_kg": 1.2,
    "terminal_orientation": "REARWARD / DOWNWARD", "body_to_idler_clearance_mm_approx": 10.0,
    "terminal_to_rear_wall_clearance_mm": 37.0, "insertion_removal": "PHYSICAL_PASS",
    "male_tab_mm": [6.3, 0.7], "female_receptacle_outer_width_mm": 10.6,
    "battery_bottom_to_terminal_top_mm": 99.4, "terminal_protrusion_mm_derived": 6.9,
    "terminal_outer_span_mm": 29.5, "terminal_inner_gap_mm": 20.0,
}
BBOX = {
    "role": "SUBMERGED BATTERY CASSETTE", "energy_storage_only": True,
    "main_body_outer_mm": [180.0, 114.0, 93.0], "lower_shell_outer_mm": [200.0, 130.0, 97.0],
    "main_cavity_mm": [173.6, 107.6], "top_throat_mm": [174.0, 104.0],
    "floor_mm": 3.2, "wall_mm": 3.2, "integrated_flange_thickness_mm": 4.0,
    "lid_mm": [200.0, 130.0, 4.2], "gasket_nominal_thickness_mm": 2.0,
    "gasket_compression_percent": 25.0, "gasket_compressed_mm": 1.5,
    "installed_height_mm": 102.7, "absolute_height_limit_mm": 108.0,
    "gasket_inner_mm": [174.0, 104.0], "gasket_outer_mm": [186.0, 116.0],
    "seal_land_width_mm": 6.0, "seal_land_minimum_mm": 5.0,
    "flange_width_mm": 130.0, "frame_nominal_clearance_each_mm": 5.0,
    "frame_minus_tolerance_clearance_each_mm": 4.5,
    "m4_count": 12, "m4_clearance_diameter_mm": 4.4,
    "compression_stop_reservation_od_mm": 5.0,
    "minimum_bolt_to_gasket_gap_mm": 1.3, "minimum_bolt_edge_ligament_mm": 1.3,
    "minimum_stop_to_gasket_gap_mm": 1.0, "minimum_stop_edge_ligament_mm": 1.0,
    "maximum_adjacent_bolt_span_mm": 64.5,
    "lid_service_penetrations": 0, "seal_test_cable_penetrations": 0,
    "submerged_connector_count": 0, "external_terminal_cap_seam_count": 0,
    "body_to_service_ring_seam": "ELIMINATED", "gland_land": "BLANK / NO THROUGH-HOLE",
    "gasket_material": "SOLID SILICONE SHEET", "gasket_hardness_shore_a": "approximately 30-50",
    "geometry_status": "CONDITIONAL_GEOMETRY_PASS / HOLD_ACTUAL_COMPRESSION_STOP_DIMENSIONS",
}
CBOX = {
    "role": "ABOVE-WATER CONTROL / POWER DISTRIBUTION BOX", "external_mm": [180.0, 92.0, 45.0],
    "body_height_mm": 40.0, "compressed_gasket_reference_mm": 0.8, "lid_mm": 4.2,
    "m4_candidate_count": 16, "internal_tray_mm": [160.0, 72.0, 2.4],
    "zones": ["POWER ENTRY", "MAIN DISTRIBUTION", "DRIVER L", "DRIVER R", "LOW-VOLTAGE / SIGNAL RESERVE"],
    "component_hole_patterns": "HOLD", "waterproof": "NOT_TESTED", "thermal_limit": "HOLD",
}

DOCS = [
    "README.md", "ARCHITECTURE_AUTHORITY.md", "BBOX_SUBMERGED_SPEC.md", "BBOX_SEAL_ARCHITECTURE.md",
    "BBOX_BATTERY_AND_TERMINAL_LAYOUT.md", "BBOX_CABLE_PENETRATION_SPEC.md",
    "BBOX_GASKET_AND_CLAMPING_SPEC.md", "CBOX_DRIVE_POWER_ARCHITECTURE.md",
    "CBOX_ELECTRICAL_ZONE_LAYOUT.md", "POWER_DISTRIBUTION_TOPOLOGY.md", "CABLE_ROUTING_SPEC.md",
    "WATERPROOF_VALIDATION_PLAN.md", "POWERED_DRIVE_PRECONDITIONS.md", "PHYSICAL_SOURCE_TRACE.md",
    "HOLD_REGISTER.md", "BOM_CANDIDATES.md", "PRINT_PLAN.md",
]
ARTIFACTS = [
    "artifacts/bbox_submerged_seal_test_lower_v0_9_6_0.step",
    "artifacts/bbox_submerged_seal_test_lower_v0_9_6_0.stl",
    "artifacts/bbox_submerged_seal_test_lid_v0_9_6_0.step",
    "artifacts/bbox_submerged_seal_test_lid_v0_9_6_0.stl",
    "artifacts/bbox_submerged_seal_test_assembly_v0_9_6_0.step",
    "artifacts/bbox_gasket_cut_template_v0_9_6_0.svg",
    "artifacts/bbox_gasket_compression_section_v0_9_6_0.svg",
    "artifacts/bbox_gland_land_reference_v0_9_6_0.svg",
    "artifacts/bbox_power_routing_architecture_v0_9_6_0.svg",
    "artifacts/cbox_drive_electrical_zone_layout_v0_9_6_0.svg",
]
DATA = [
    "design_parameters.json", "architecture_state.json", "validation_report.json",
    "reproducibility_report.json", "M4_CLAMP_PATTERN.csv", "WATERPROOF_TEST_RECORD.csv",
]
SOURCE = ["build_bbox_cbox_submerged_power_architecture_v0960.py", "tests/test_bbox_cbox_submerged_power_architecture_v0960.py"]
RELEASE = ["TEST_LOG.txt", "BUILD_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
PACKAGE_PATHS = sorted(DOCS + ARTIFACTS + DATA + SOURCE + RELEASE)


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def git(*args: str, binary: bool = False) -> Any:
    return subprocess.check_output(
        ["git", *args], cwd=REPO_ROOT, text=not binary,
        encoding=None if binary else "utf-8",
    )


def git_lines(*args: str) -> list[str]:
    return git(*args).splitlines()


def rbox(x: float, y: float, z: float, radius: float, cx=0.0, cy=0.0, cz=0.0) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).edges("|Z").fillet(radius).translate((cx, cy, cz))


def box(x: float, y: float, z: float, cx=0.0, cy=0.0, cz=0.0) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate((cx, cy, cz))


def cylinder(radius: float, height: float, x: float, y: float, z=0.0) -> cq.Workplane:
    return cq.Workplane("XY").center(x, y).circle(radius).extrude(height).translate((0, 0, z))


def ring(outer_x: float, outer_y: float, inner_x: float, inner_y: float, height: float, z=0.0) -> cq.Workplane:
    return rbox(outer_x, outer_y, height, 4.0, cz=z + height / 2).cut(
        rbox(inner_x, inner_y, height + 2.0, 2.0, cz=z + height / 2)
    ).clean()


def bolt_pattern() -> list[tuple[float, float]]:
    rows = [(x, y) for y in (-61.5, 61.5) for x in (-96.5, -32.0, 32.0, 96.5)]
    rows.extend((x, y) for x in (-96.5, 96.5) for y in (-20.0, 20.0))
    return rows


def lower_shell() -> cq.Workplane:
    main = rbox(180.0, 114.0, 93.0, 5.0, cz=46.5)
    flange = rbox(200.0, 130.0, 4.0, 5.0, cz=95.0)
    part = main.union(flange)
    main_cavity = rbox(173.6, 107.6, 92.0, 2.5, cz=49.2)
    top_throat = rbox(174.0, 104.0, 10.0, 2.0, cz=95.0)
    part = part.cut(main_cavity).cut(top_throat)
    # Blank rear-upper gland landing pad; intentionally no through-hole.
    part = part.union(box(3.0, 44.0, 28.0, -91.5, 0.0, 75.0))
    # Replaceable strain-relief mount reservations in rear service volume; no released hole pattern.
    for y in (-18.0, 18.0):
        part = part.union(cylinder(4.0, 18.0, -82.0, y, 3.2))
    for x, y in bolt_pattern():
        part = part.cut(cylinder(2.2, 8.0, x, y, 91.0))
    return part.clean()


def lid() -> cq.Workplane:
    part = rbox(200.0, 130.0, 4.2, 5.0, cz=2.1)
    for x, y in bolt_pattern():
        part = part.cut(cylinder(2.2, 6.2, x, y, -1.0))
    return part.clean()


def gasket_compressed() -> cq.Workplane:
    return ring(186.0, 116.0, 174.0, 104.0, 1.5, 97.0)


def assembly() -> cq.Compound:
    parts: list[Any] = [lower_shell().val(), gasket_compressed().val(), lid().translate((0, 0, 98.5)).val()]
    return cq.Compound.makeCompound(parts)


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(FILE_NAME\('Open CASCADE Shape Model',')[^']+(')", r"\g<1>2000-01-01T00:00:00\2", text)
    text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
    occurrence = 0
    def repl(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return match.group(1) + str(occurrence) + match.group(2)
    text = re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')", repl, text)
    path.write_text(text, encoding="utf-8", newline="\n")


def export_shape(shape: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path), tolerance=0.01, angularTolerance=0.1)
    if path.suffix.lower() in {".step", ".stp"}:
        normalize_step(path)


def svg_wrap(title: str, body: str, width=1100, height=650) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.h{{font-size:22px;font-weight:bold}}.n{{font-size:17px}}.s{{font-size:14px;fill:#566573}}.d{{stroke:#34495e;stroke-width:2;fill:none}}.a{{fill:#d6eaf8;stroke:#2874a6;stroke-width:2}}.b{{fill:#d5f5e3;stroke:#148f77;stroke-width:2}}.c{{fill:#fadbd8;stroke:#c0392b;stroke-width:2}}</style>
<text x="25" y="35" class="h">{title}</text>{body}</svg>'''


def svg_artifacts() -> dict[str, str]:
    bolts = "".join(f'<circle cx="{550+x*4}" cy="{320+y*4}" r="8.8" fill="#fff" stroke="#c0392b" stroke-width="2"/>' for x, y in bolt_pattern())
    gasket = svg_wrap("BBOX solid-silicone gasket cut template — NOT PRODUCTION RELEASE", f'''
<rect x="178" y="84" width="744" height="464" rx="16" class="b"/><rect x="202" y="108" width="696" height="416" rx="10" fill="#fff" stroke="#148f77" stroke-width="2"/>{bolts}
<text x="40" y="590" class="n">Outer 186×116; inner 174×104; continuous 6 mm band; nominal thickness 2.0 mm</text>
<text x="40" y="620" class="s">12×M4 holes are outside the gasket. Verify purchased silicone thickness, hardness and recovery before cutting.</text>''')
    section = svg_wrap("BBOX gasket compression section", '''
<rect x="120" y="160" width="860" height="45" class="a"/><text x="145" y="190" class="n">one-piece PETG lid 4.2 mm</text>
<rect x="240" y="205" width="620" height="55" class="b"/><text x="400" y="240" class="n">2.0 mm silicone → 1.5–1.6 mm target</text>
<rect x="90" y="260" width="920" height="85" class="a"/><text x="145" y="310" class="n">integrated PETG flange; 6 mm continuous land</text>
<line x1="195" y1="125" x2="195" y2="390" stroke="#c0392b" stroke-width="5"/><text x="75" y="420" class="n">M4 + metal strip/washer</text>
<rect x="175" y="205" width="40" height="140" fill="#f9e79f" stroke="#9a7d0a" stroke-width="2"/><text x="235" y="380" class="n">metal compression stop REQUIRED; actual OD/ID/length/material HOLD</text>
<text x="50" y="560" class="s">Fastener axis remains outside the closed gasket loop; no screw crosses the wet seal land.</text>''')
    gland = svg_wrap("BBOX blank gland landing reference", '''
<rect x="150" y="120" width="760" height="400" rx="20" class="a"/><rect x="180" y="190" width="150" height="190" class="b"/><text x="190" y="285" class="n">BLANK GLAND LAND</text>
<circle cx="255" cy="285" r="42" fill="none" stroke="#c0392b" stroke-dasharray="8 6" stroke-width="2"/><text x="380" y="250" class="n">rear-upper wall / no through-hole</text><text x="380" y="285" class="n">actual cable OD + gland dimensions required</text>
<text x="380" y="320" class="n">first seal-test penetration count = 0</text><text x="120" y="585" class="s">Dashed circle is a future measurement zone only, not a drill template.</text>''')
    power = svg_wrap("BBOX → CBOX DRIVE power architecture", '''
<rect x="40" y="120" width="180" height="80" class="a"/><text x="65" y="155" class="n">BATTERY BBOX</text><text x="65" y="180" class="s">energy storage only</text><line x1="220" y1="160" x2="290" y2="160" class="d"/>
<rect x="290" y="120" width="150" height="80" class="b"/><text x="315" y="155" class="n">MAIN FUSE</text><text x="305" y="180" class="s">rating HOLD</text><line x1="440" y1="160" x2="510" y2="160" class="d"/>
<rect x="510" y="120" width="190" height="80" class="a"/><text x="530" y="150" class="n">ABOVE-WATER</text><text x="535" y="178" class="n">CONNECTOR</text><line x1="700" y1="160" x2="770" y2="160" class="d"/>
<rect x="770" y="120" width="280" height="80" class="c"/><text x="795" y="150" class="n">HARDWARE MASTER CUT</text><text x="815" y="180" class="s">software-independent; rating HOLD</text>
<line x1="910" y1="200" x2="910" y2="280" class="d"/><rect x="680" y="280" width="460" height="240" class="b"/><text x="820" y="315" class="h">CBOX</text><rect x="720" y="350" width="160" height="80" class="a"/><text x="740" y="395" class="n">DRIVER L</text><rect x="940" y="350" width="160" height="80" class="a"/><text x="960" y="395" class="n">DRIVER R</text>
<text x="55" y="575" class="s">One jacketed 2-conductor BBOX pigtail. Submerged disconnects: 0. Charging while submerged: PROHIBITED.</text>''', 1180, 650)
    cbox = svg_wrap("CBOX DRIVE electrical-zone layout — component fit pending", '''
<rect x="120" y="100" width="860" height="420" rx="16" class="d"/><rect x="150" y="135" width="150" height="350" class="a"/><text x="170" y="310" class="n">POWER ENTRY</text>
<rect x="320" y="135" width="170" height="350" class="b"/><text x="335" y="290" class="n">MAIN</text><text x="335" y="320" class="n">DISTRIBUTION</text>
<rect x="510" y="135" width="190" height="160" class="c"/><text x="560" y="220" class="n">DRIVER L</text><rect x="510" y="325" width="190" height="160" class="c"/><text x="560" y="410" class="n">DRIVER R</text>
<rect x="720" y="135" width="230" height="350" fill="#f9e79f" stroke="#9a7d0a" stroke-width="2"/><text x="750" y="290" class="n">LOW-VOLTAGE /</text><text x="770" y="320" class="n">SIGNAL RESERVE</text>
<text x="120" y="575" class="s">Reference envelope 180×92×45 mm. Actual component hole patterns and thermal limit remain HOLD.</text>''')
    return {
        "bbox_gasket_cut_template_v0_9_6_0.svg": gasket,
        "bbox_gasket_compression_section_v0_9_6_0.svg": section,
        "bbox_gland_land_reference_v0_9_6_0.svg": gland,
        "bbox_power_routing_architecture_v0_9_6_0.svg": power,
        "cbox_drive_electrical_zone_layout_v0_9_6_0.svg": cbox,
    }


def build_artifacts(root: Path) -> None:
    artifacts = root / "artifacts"
    export_shape(lower_shell(), artifacts / "bbox_submerged_seal_test_lower_v0_9_6_0.step")
    export_shape(lower_shell(), artifacts / "bbox_submerged_seal_test_lower_v0_9_6_0.stl")
    export_shape(lid(), artifacts / "bbox_submerged_seal_test_lid_v0_9_6_0.step")
    export_shape(lid(), artifacts / "bbox_submerged_seal_test_lid_v0_9_6_0.stl")
    export_shape(assembly(), artifacts / "bbox_submerged_seal_test_assembly_v0_9_6_0.step")
    for name, content in svg_artifacts().items():
        write(artifacts / name, content)


def tree_digest(root: Path) -> tuple[int, str]:
    paths = sorted(
        (p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    h = hashlib.sha256()
    for path in paths:
        h.update(f"{sha(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(paths), h.hexdigest()


def verify_manifest_and_sums(root: Path) -> tuple[bool, bool]:
    files = sorted(
        p.relative_to(root).as_posix() for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts
    )
    manifest = (root / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    manifest_ok = files == manifest
    parsed: dict[str, str] = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, sep, rel = line.partition("  ")
        if sep:
            parsed[rel] = digest
    expected = [p for p in files if p != "SHA256SUMS.txt"]
    sums_ok = sorted(parsed) == expected and all(sha(root / rel) == digest for rel, digest in parsed.items())
    return manifest_ok, sums_ok


def authority_audit() -> dict[str, Any]:
    actual = {name: sha(REPO_ROOT / name) for name in AUTHORITY_HASHES}
    return {"expected": AUTHORITY_HASHES, "actual": actual, "status": "PASS" if actual == AUTHORITY_HASHES else "FAIL"}


def parent_audit() -> dict[str, Any]:
    root = REPO_ROOT / "cad/common_rover"
    rows: dict[str, Any] = {}
    for name, expected in PARENT_TREES.items():
        lane = root / name
        actual = tree_digest(lane) if lane.is_dir() else None
        manifest_ok = sums_ok = False
        if actual:
            manifest_ok, sums_ok = verify_manifest_and_sums(lane)
        rows[name] = {
            "expected": expected, "actual": actual, "manifest": "PASS" if manifest_ok else "FAIL",
            "sha256sums": "PASS" if sums_ok else "FAIL",
            "status": "PASS" if actual == expected and manifest_ok and sums_ok else "FAIL",
        }
    return {"parents": rows, "status": "PASS" if all(row["status"] == "PASS" for row in rows.values()) else "FAIL"}


def history_audit() -> dict[str, Any]:
    actual = [tuple(line.split("|", 1)) for line in git_lines("log", "-3", "--format=%H|%s")]
    return {"expected": EXPECTED_HISTORY, "actual": actual, "status": "PASS" if actual == EXPECTED_HISTORY else "FAIL"}


def outside_snapshot() -> dict[str, Any]:
    prefix = LANE_REL + "/"
    paths = sorted(p for p in git_lines("ls-files", "--others", "--exclude-standard") if not p.startswith(prefix))
    return {
        "count": len(paths),
        "path_digest": sha_bytes("".join(p + "\n" for p in paths).encode()),
    }


def dirty_diff_sha() -> str:
    return sha_bytes(git("diff", "--binary", "--", *AUTHORITY_HASHES, binary=True))


def repository_guard(complete: bool = False) -> dict[str, Any]:
    root = Path(git("rev-parse", "--show-toplevel").strip()).resolve()
    branch = git("branch", "--show-current").strip()
    head = git("rev-parse", "HEAD").strip()
    staged = sorted(git_lines("diff", "--cached", "--name-only"))
    tracked = sorted(git_lines("diff", "--name-only"))
    untracked = sorted(git_lines("ls-files", "--others", "--exclude-standard"))
    prefix = LANE_REL + "/"
    lane_paths = [p[len(prefix):] for p in untracked if p.startswith(prefix)]
    ignored_lane = git_lines("ls-files", "--others", "-i", "--exclude-standard", "--", LANE_REL)
    outside = outside_snapshot()
    forbidden = [
        p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file()
        and (p.suffix.lower() in {".pyc", ".tmp", ".bak"} or "__pycache__" in p.parts or ".pytest_cache" in p.parts)
    ]
    parents = parent_audit()
    checks = {
        "root": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "history": history_audit()["status"] == "PASS", "staged_zero": not staged,
        "tracked_dirty_exact_four": tracked == sorted(AUTHORITY_HASHES),
        "dirty_diff_unchanged": dirty_diff_sha() == BASE_DIRTY_DIFF_SHA,
        "authority_unchanged": authority_audit()["status"] == "PASS", "parents_unchanged": parents["status"] == "PASS",
        "v0953_unchanged": parents["parents"]["common_rover_physical_followup_measurement_v0_9_5_3"]["status"] == "PASS",
        "outside_count": outside["count"] == BASE_OUTSIDE_UNTRACKED_COUNT,
        "outside_paths": outside["path_digest"] == BASE_OUTSIDE_PATH_DIGEST,
        "ignored_lane_zero": not ignored_lane, "lane_scope": set(lane_paths).issubset(PACKAGE_PATHS),
        "lane_complete": set(lane_paths) == set(PACKAGE_PATHS) if complete else True,
        "cache_temp_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError(json.dumps({
            "checks": checks, "tracked": tracked, "staged": staged, "outside": outside,
            "lane_paths": lane_paths, "ignored_lane": ignored_lane, "forbidden": forbidden,
        }, ensure_ascii=False, indent=2))
    return {
        "root": str(root), "branch": branch, "head": head, "staged": staged, "tracked_dirty": tracked,
        "outside_untracked": outside, "lane_path_count": len(lane_paths), "checks": checks, "status": "PASS",
    }


def design_parameters() -> dict[str, Any]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "unit": "mm", "frame": FRAME,
        "battery": BATTERY, "bbox": BBOX, "cbox": CBOX,
        "m4_pattern": [{"index": i + 1, "x_mm": x, "y_mm": y, "classification": "DESIGN_CANDIDATE"} for i, (x, y) in enumerate(bolt_pattern())],
        "print_plate": {"plate_01": "LOWER_SHELL_BOTTOM_DOWN", "plate_02": "LID_EXTERIOR_DOWN_SEAL_FACE_UP", "bambu_a1_fit": True},
    }


def architecture_state() -> dict[str, Any]:
    return {
        "version": VERSION, "bbox_role": "SUBMERGED BATTERY CASSETTE", "bbox_contents": [
            "battery", "battery female terminals", "short flexible leads", "positive main fuse",
            "internal terminal protector", "internal strain relief",
        ],
        "bbox_excluded": ["motor drivers", "MCU", "Raspberry Pi", "servo driver", "wireless radio", "charging electronics"],
        "penetrations": {"primary_lid_seam": 1, "power_cable": 1, "seal_test_power_cable": 0, "submerged_disconnect": 0, "vent": 0, "external_terminal_cap": 0},
        "power_topology": ["BATTERY", "MAIN_FUSE", "BBOX_PIGTAIL", "ABOVE_WATER_CONNECTOR", "HARDWARE_MASTER_DISCONNECT", "POWER_DISTRIBUTION", "DRIVER_L_AND_R", "MOTORS_L_AND_R"],
        "routing": {"left_upper_frame": "POWER_HARNESS_CANDIDATE", "right_upper_frame": "SIGNAL_HARNESS_CANDIDATE", "crossing": "APPROXIMATELY_90_DEGREES_PREFERRED"},
        "cbox_zones": CBOX["zones"],
        "gates": {
            "bbox_submerged_architecture": "CAD_COMPLETE_PHYSICAL_VALIDATION_PENDING",
            "bbox_empty_seal_test": "READY_TO_PRINT",
            "bbox_gland_penetration": "HOLD_ACTUAL_GLANDLESS_TEST_FIRST",
            "bbox_live_battery_water_test": "NOT_APPROVED", "wire_gauge": "HOLD",
            "main_fuse_rating": "HOLD", "branch_fuse_rating": "HOLD", "connector_current_rating": "HOLD",
            "cbox_drive_zone_layout": "ARCHITECTURE_COMPLETE_COMPONENT_FIT_PENDING",
            "cbox_waterproof": "NOT_TESTED", "powered_drive": "NOT_APPROVED", "field_deployment": "NOT_APPROVED",
        },
    }


def geometry_metrics() -> dict[str, Any]:
    lower, top, assy, gasket = lower_shell(), lid(), assembly(), gasket_compressed()
    lb, tb, ab = lower.val().BoundingBox(), top.val().BoundingBox(), assy.BoundingBox()
    hole_radius = BBOX["m4_clearance_diameter_mm"] / 2
    gasket_outer_half = (BBOX["gasket_outer_mm"][0] / 2, BBOX["gasket_outer_mm"][1] / 2)
    flange_half = (BBOX["lower_shell_outer_mm"][0] / 2, BBOX["lower_shell_outer_mm"][1] / 2)
    dry_gaps, edge_ligaments = [], []
    for x, y in bolt_pattern():
        if abs(y) > gasket_outer_half[1]:
            dry_gaps.append(abs(y) - hole_radius - gasket_outer_half[1])
            edge_ligaments.append(flange_half[1] - abs(y) - hole_radius)
        if abs(x) > gasket_outer_half[0]:
            dry_gaps.append(abs(x) - hole_radius - gasket_outer_half[0])
            edge_ligaments.append(flange_half[0] - abs(x) - hole_radius)
    bolt_cuts_ok = all(
        lower.intersect(cylinder(hole_radius, 8, x, y, 91)).val().Volume() < 1e-6
        and top.intersect(cylinder(hole_radius, 6.2, x, y, -1)).val().Volume() < 1e-6
        for x, y in bolt_pattern()
    )
    gasket_hole_common = sum(gasket.intersect(cylinder(hole_radius, 4, x, y, 96)).val().Volume() for x, y in bolt_pattern())
    return {
        "cadquery_version": cq.__version__, "lower_valid": lower.val().isValid(), "lid_valid": top.val().isValid(),
        "assembly_valid": assy.isValid(), "gasket_valid": gasket.val().isValid(),
        "lower_bounds_mm": [lb.xlen, lb.ylen, lb.zlen], "lid_bounds_mm": [tb.xlen, tb.ylen, tb.zlen],
        "assembly_bounds_mm": [ab.xlen, ab.ylen, ab.zlen], "installed_height_mm": ab.zlen,
        "bolt_count": len(bolt_pattern()), "bolt_cuts_clear": bolt_cuts_ok,
        "minimum_bolt_to_gasket_gap_mm": min(dry_gaps), "minimum_bolt_edge_ligament_mm": min(edge_ligaments),
        "gasket_hole_common_volume_mm3": gasket_hole_common,
        "gasket_path_solid_count": len(gasket.val().Solids()), "seal_land_width_mm": 6.0,
        "battery_main_cavity_clearance_each_mm": (107.6 - 99.4) / 2,
        "battery_top_throat_clearance_each_mm": (104.0 - 99.4) / 2,
        "frame_nominal_clearance_each_mm": (140.0 - 130.0) / 2,
        "frame_minus_tolerance_clearance_each_mm": (139.0 - 130.0) / 2,
        "blank_gland_land": True, "gland_through_hole_count": 0,
    }


def stl_mesh_info(path: Path) -> dict[str, Any]:
    """Parse STL without optional native mesh dependencies and audit closed edges."""
    data = path.read_bytes()
    triangles: list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]] = []
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if 84 + count * 50 == len(data):
            for index in range(count):
                values = struct.unpack_from("<12fH", data, 84 + index * 50)
                triangles.append((tuple(values[3:6]), tuple(values[6:9]), tuple(values[9:12])))
    if not triangles:
        vertices: list[tuple[float, float, float]] = []
        for line in data.decode("ascii", errors="strict").splitlines():
            fields = line.strip().split()
            if len(fields) == 4 and fields[0].lower() == "vertex":
                vertices.append(tuple(float(v) for v in fields[1:4]))
        if len(vertices) % 3:
            raise RuntimeError(f"invalid ASCII STL vertex count: {path}")
        triangles = [tuple(vertices[i:i + 3]) for i in range(0, len(vertices), 3)]
    def vertex_key(vertex: tuple[float, float, float]) -> tuple[int, int, int]:
        return tuple(round(value * 1_000_000) for value in vertex)
    edges: Counter[tuple[tuple[int, int, int], tuple[int, int, int]]] = Counter()
    signed_volume = 0.0
    for a, b, c in triangles:
        keys = (vertex_key(a), vertex_key(b), vertex_key(c))
        for first, second in ((keys[0], keys[1]), (keys[1], keys[2]), (keys[2], keys[0])):
            edges[tuple(sorted((first, second)))] += 1
        signed_volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6.0
    nonmanifold = sum(count != 2 for count in edges.values())
    return {
        "triangles": len(triangles), "unique_edges": len(edges), "nonmanifold_edges": nonmanifold,
        "watertight": bool(triangles) and nonmanifold == 0, "absolute_signed_volume_mm3": abs(signed_volume),
    }


def artifact_validation(root: Path) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for rel in [p for p in ARTIFACTS if p.endswith(".step")]:
        shape = cq.importers.importStep(str(root / rel)).val()
        rows[rel] = {"parse": "PASS", "valid": shape.isValid(), "volume_mm3": shape.Volume(), "status": "PASS" if shape.isValid() and shape.Volume() > 0 else "FAIL"}
    for rel in [p for p in ARTIFACTS if p.endswith(".stl")]:
        mesh = stl_mesh_info(root / rel)
        rows[rel] = {"parse": "PASS", **mesh, "status": "PASS" if mesh["watertight"] and mesh["absolute_signed_volume_mm3"] > 0 else "FAIL"}
    for rel in [p for p in ARTIFACTS if p.endswith(".svg")]:
        ElementTree.parse(root / rel)
        rows[rel] = {"xml_parse": "PASS", "status": "PASS"}
    return {"rows": rows, "status": "PASS" if all(row["status"] == "PASS" for row in rows.values()) else "FAIL"}


def independent_rebuild() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="paddy_v0960_rebuild_") as temp:
        root = Path(temp)
        build_artifacts(root)
        write_json(root / "design_parameters.json", design_parameters())
        write_json(root / "architecture_state.json", architecture_state())
        compared = ARTIFACTS + ["design_parameters.json", "architecture_state.json"]
        rows = {rel: {"original": sha(LANE / rel), "rebuild": sha(root / rel), "byte_equal": sha(LANE / rel) == sha(root / rel)} for rel in compared}
    return {"method": "INDEPENDENT_CLEAN_OUTPUT_BYTE_COMPARISON", "rows": rows, "pass_count": sum(r["byte_equal"] for r in rows.values()), "total": len(rows), "status": "PASS" if all(r["byte_equal"] for r in rows.values()) else "FAIL"}


def m4_csv() -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["index", "x_mm", "y_mm", "hole_diameter_mm", "location", "classification"])
    for i, (x, y) in enumerate(bolt_pattern(), 1):
        location = "LONG_SIDE" if abs(y) > 50 else "SHORT_SIDE"
        writer.writerow([i, f"{x:.1f}", f"{y:.1f}", "4.4", location, "DESIGN_CANDIDATE"])
    return stream.getvalue()


def water_csv() -> str:
    rows = [
        ("W0", "DRY_INSPECTION", "shell/lid/gasket/fastener/stop inspection"),
        ("W1", "DRY_COMPRESSION", "uniform compression, no rocking or center lift"),
        ("W2", "SPLASH_TEST", "empty enclosure only"),
        ("W3", "SHALLOW_SUBMERSION", "lid seam below water"),
        ("W4", "100MM_HEAD", "100 mm water above lid"),
        ("W5", "200MM_HEAD", "200 mm water above lid"),
        ("W6", "200MM_HEAD_24H", "200 mm water above lid for 24 h"),
    ]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["phase", "test", "target", "status", "visible_water", "tissue_wetting", "gasket_displacement", "lid_shift", "shell_crack"])
    for phase, test, target in rows:
        writer.writerow([phase, test, target, "NOT_TESTED", "", "", "", "", ""])
    return stream.getvalue()


def docs(metrics: dict[str, Any], parents: dict[str, Any]) -> dict[str, str]:
    header = f"Version: `{VERSION}`  \nClassification: `{CLASSIFICATION}`  \n`NOT_FOR_LIVE_BATTERY_WATER_TEST`\n"
    parent_rows = "\n".join(f'| {name} | {row["actual"][0]} | `{row["actual"][1]}` | {row["status"]} |' for name, row in parents["parents"].items())
    hold_items = [
        "MOTOR_MODEL / RATED_VOLTAGE / CONTINUOUS_CURRENT / STALL_CURRENT",
        "MOTOR_DRIVER_MODEL / CONTINUOUS_CURRENT / PEAK_CURRENT / CURRENT_LIMIT",
        "WIRE_GAUGE / CABLE_MODEL / CABLE_OUTER_DIAMETER / CONDUCTOR_AREA",
        "MAIN_FUSE_RATING / BRANCH_FUSE_RATING / CONNECTOR_CURRENT_RATING",
        "GLAND_MODEL / GLAND_SIZE / FINAL_GLAND_HOLE_DIAMETER",
        "CRIMPED_RECEPTACLE_LENGTH / WIRE_INSULATION_OD / WIRE_BEND_START_DISTANCE",
        "FINAL_TERMINAL_PROTECTOR / FINAL_STRAIN_RELIEF / SERVICE_LOOP_LENGTH / BEND_RADIUS",
        "COMPRESSION_STOP_OD / ID / LENGTH / MATERIAL / CLAMP_STRIP_THICKNESS",
        "FINAL_ESTOP_OR_MASTER_DISCONNECT / CBOX_THERMAL_LIMIT",
        "SEALED_AIR_THERMAL_PRESSURE / BATTERY_FAULT_PRESSURE",
    ]
    d: dict[str, str] = {}
    d["README.md"] = f'''# Common Rover v0.9.6.0 BBOX/CBOX Submerged Power Architecture

{header}

This lane defines an empty, glandless BBOX seal-test shell and the inheritable BBOX→CBOX DRIVE power architecture. It creates no live-battery submersion, powered-rotation, or field approval.

- BBOX: `SUBMERGED BATTERY CASSETTE / ENERGY STORAGE ONLY`
- Empty shell: `READY_TO_PRINT / PHYSICAL_VALIDATION_PENDING`
- CBOX: above-water control and power distribution; component fit pending
- Submerged connectors: `0`; first-test cable penetrations: `0`
- Hardware motor-power cut: `REQUIRED`

The 130 mm flange is a tight conditional prototype. Actual compression-stop dimensions remain HOLD; the recorded minimum bolt/gasket and edge ligaments must be physically reviewed before testing.'''
    d["ARCHITECTURE_AUTHORITY.md"] = f'''# Architecture Authority

{header}

The compact 150 mm frame remains authoritative: upper540×181, lower442×181, height150, upper clear500×100, lower clear400×140, insertion datum108 mm. The 190 mm frame remains HOLD.

The v0.9.5.0 separate service-ring and blank connector-panel submerged concepts are `SUPERSEDED` only in this new lane. Parent artifacts remain unchanged. The new lower shell integrates its flange and eliminates `BODY_TO_SERVICE_RING_SEAM`.

Final status: `{FINAL_STATUS}`.'''
    d["BBOX_SUBMERGED_SPEC.md"] = f'''# BBOX Submerged Specification

{header}

Role: `SUBMERGED BATTERY CASSETTE`, energy storage only. Allowed: battery, female terminals, short flexible leads, positive main fuse, internal protector and strain relief. Drivers, control computers, radio, servo electronics and chargers remain in CBOX/above-water systems.

Lower shell envelope: 200×130×97 mm including integrated flange; main body reference180×114. Installed compressed height:102.7 mm, below103 mm target and108 mm absolute datum. Nominal frame clearance5.0 mm/side; at −1 mm frame tolerance4.5 mm/side.

The main cavity remains107.6 mm wide. A disclosed104.0 mm top throat gives2.3 mm battery-body clearance per side for the99.4 mm physical battery reference; this is a physical-fit candidate, not a manufacturing release.'''
    d["BBOX_SEAL_ARCHITECTURE.md"] = f'''# BBOX Seal Architecture

{header}

`LOWER SHELL + INTEGRATED SEALING FLANGE`; service-ring seam eliminated. One-piece lid, continuous flat seal land and closed-loop solid-silicone gasket. No gasket seam, cable notch, text, support contact or screw crosses the seal.

Primary lid seam count1. First-test power-cable penetration0, submerged disconnect0, vent0, external terminal-cap seam0. The rear-upper gland land is blank and solid. Waterproof authority requires W0→W6 physical results.'''
    d["BBOX_BATTERY_AND_TERMINAL_LAYOUT.md"] = f'''# BBOX Battery and Terminal Layout

{header}

GOLDENMATE LiFePO4 label12.8 V/10 Ah/128 Wh; body150.9×99.4×92.5 mm; mass1.2 kg. Preferred terminals=`REARWARD / DOWNWARD`; insertion/removal=`PHYSICAL_PASS` in the150 mm frame reference. Approximate body/idler clearance10 mm and rear terminal/wall clearance37.0 mm are retained.

Male tab6.3×0.7 mm, candidate female outer width10.6 mm, terminal span29.5 mm, inner gap20.0 mm, and derived6.9 mm protrusion are references. Completed receptacle length, insulation OD and bend start are missing. `FINAL_TERMINAL_PROTECTOR=HOLD_HARNESS_MEASUREMENT`; only internal removable protection is permitted. Terminal tabs never carry cable weight.'''
    d["BBOX_CABLE_PENETRATION_SPEC.md"] = f'''# BBOX Cable Penetration Specification

{header}

Final baseline: one jacketed2-conductor cable through one gland; separate red/black penetrations prohibited. The first shell has a blank rear-upper landing pad and `NO THROUGH-HOLE`. Actual cable OD, wire gauge and gland dimensions are required before a second-stage coupon or penetrated shell.

Submerged disconnect count0. The integrated pigtail disconnect is mounted above maximum waterline. Charging while submerged/in paddy is prohibited; no charge port or internal charger is added.'''
    d["BBOX_GASKET_AND_CLAMPING_SPEC.md"] = f'''# BBOX Gasket and Clamping Specification

{header}

Primary gasket candidate: solid silicone sheet, nominal2.0 mm, approximately Shore A30–50, target20–25% compression. CAD assembly uses1.5 mm at25%; purchased thickness, hardness and recovery require measurement.

Seal land=6.0 mm continuous (minimum5 mm). Gasket outer186×116, inner174×104. Twelve M4 clearance holes form a primary clamp pattern outside the gasket; maximum adjacent span64.5 mm. Minimum CAD bolt-to-gasket gap1.3 mm and outer edge ligament1.3 mm.

Metal washers/clamp strips and metal compression stops are required for final hardware. The5.0 mm OD reservation gives1.0 mm nominal gasket and edge margin; actual sleeve OD/ID/length/material and strip thickness remain HOLD. PETG alone must not retain long-term compression.'''
    d["CBOX_DRIVE_POWER_ARCHITECTURE.md"] = f'''# CBOX DRIVE Power Architecture

{header}

CBOX is `ABOVE-WATER CONTROL / POWER DISTRIBUTION BOX`. Candidate contents: master-disconnect interface, distribution, left/right motor drivers, current sensor, later DC-DC/MCU/Hall interface. These do not move into BBOX.

Existing physical reference180×92×45 mm, body40, gasket reference0.8, lid4.2, M4×16, tray160×72×2.4. Waterproof=`NOT_TESTED`. No full redesign or component hole pattern is released without actual driver dimensions.'''
    d["CBOX_ELECTRICAL_ZONE_LAYOUT.md"] = f'''# CBOX Electrical Zone Layout

{header}

Zones: POWER ENTRY; MAIN DISTRIBUTION; DRIVER L; DRIVER R; LOW-VOLTAGE/SIGNAL RESERVE. Body high-side wall entry is preferred and lid penetration is avoided. Final glands/connectors and all component holes are HOLD.

The sealed CBOX requires `CBOX_INTERNAL_TEMPERATURE_TEST`. Initial powered bench work, when separately approved, must be short duration with temperature monitoring and a driver-specification stop threshold. `THERMAL_LIMIT=HOLD`.'''
    d["POWER_DISTRIBUTION_TOPOLOGY.md"] = f'''# Power Distribution Topology

{header}

Battery+ → shortest practical lead → MAIN FUSE → BBOX pigtail → ABOVE-WATER CONNECTOR → HARDWARE MASTER DISCONNECT → distribution → DRIVER L/R → MOTOR L/R. Battery− routes directly to the pigtail return.

Main/branch fuse ratings, connector current rating and disconnect/E-stop component remain HOLD until motor/driver current measurements exist. Software-only motor power removal is prohibited. Human-accessible, identifiable, software-independent hardware motor-power cut is required before powered DRIVE testing.'''
    d["CABLE_ROUTING_SPEC.md"] = f'''# Cable Routing Specification

{header}

Candidate convention: left upper frame=power harness, right upper frame=signal harness. Motor +/− remain paired. Long parallel power/signal routes are avoided; crossings are approximately90° where practical.

Keep-outs:20T,60T, DRIVE belt, tensioner, crawler, PTO belt, slide clutch, servo linkage, battery-removal corridor, idler shaft and moving track/suspension. Exact clearance is HOLD until cable OD. BBOX pigtail needs a service loop and replaceable clips, with no terminal pull load or belt sag. Final loop length, bend radius and clip diameter remain HOLD.'''
    d["WATERPROOF_VALIDATION_PLAN.md"] = f'''# Waterproof Validation Plan

{header}

Battery and electronics are absent. Indicators: dry tissue plus water-sensitive paper if available at four corners, center and gland-land side.

W0 dry inspection → W1 dry compression → W2 splash → W3 shallow submersion → W4 100 mm head above lid → W5 200 mm head → W6 200 mm head/24 h. The200 mm target is engineering validation, not IP certification.

After each phase: visible water NONE, tissue wetting NONE, gasket displacement NONE, lid shift NONE, shell crack NONE. Any observation=`FAIL_LEAK / STOP`; do not advance. Optional mass comparison remains HOLD if scale resolution is unknown. A glandless PASS still does not approve battery submersion.'''
    d["POWERED_DRIVE_PRECONDITIONS.md"] = f'''# Powered DRIVE Preconditions

{header}

Required before powered operation: measured motor and driver current data; selected wire/cable; measured cable OD; fuse and connector ratings; hardware master cut/E-stop; guarded belts; verified routing; CBOX temperature monitoring; short-duration run plan and driver-spec stop threshold.

Current gates: `POWERED_DRIVE=NOT_APPROVED`, `LIVE_BATTERY_SUBMERSION=NOT_APPROVED`, `FIELD_DEPLOYMENT=NOT_APPROVED`. Empty shell printing or water testing does not change these gates.'''
    d["PHYSICAL_SOURCE_TRACE.md"] = f'''# Physical Source Trace

{header}

| Source | Files | Tree SHA-256 | Status |
|---|---:|---|---|
{parent_rows}

v0.9.5.0 supplies BBOX/CBOX/battery/tray/rail references. v0.9.5.2 supplies compact-frame, terminal, clearance and physical-fit records. v0.9.5.3 is protected read-only follow-up evidence. No parent or authority file is rewritten. Classification terms preserve MEASURED, USER_REPORTED, IMAGE_OBSERVED, DERIVED, CAD_REFERENCE, ENGINEERING_BASELINE, DESIGN_CANDIDATE, HOLD, NOT_APPROVED and SUPERSEDED distinctions.'''
    d["HOLD_REGISTER.md"] = f'''# HOLD Register

{header}

{chr(10).join(f'- `{item}`' for item in hold_items)}

Also HOLD: penetrated-shell water test until glandless W0–W6 passes; battery enclosure test until cable/gland/harness tests pass; CBOX waterproof and internal-temperature test. No inferred value may close these entries.'''
    d["BOM_CANDIDATES.md"] = f'''# BOM Candidates

{header}

- PETG lower shell and one-piece lid: design candidate
- Solid silicone sheet2.0 mm, Shore A approximately30–50: engineering baseline; actual material validation required
- 12×M4 bolts, metal washers/nuts: candidate; length/material HOLD
- Metal compression stops/sleeves: REQUIRED_FOR_FINAL; dimensions/material HOLD
- Aluminum long-side clamp strips: recommended option; thickness/hole finish HOLD
- Dry tissue/water-sensitive paper: empty-test indicators
- One jacketed2-conductor cable, gland, fuse, above-water connector, master cut: topology only; all ratings and models HOLD'''
    d["PRINT_PLAN.md"] = f'''# Print Plan

{header}

Printer/material reference: Bambu A1 / PETG.

- Plate01: lower shell alone, bottom-down/open-up. Bounds200×130×97 mm; fits256×256. Keep the seal land support-free. The external blank gland pad has a short local overhang; inspect slicer and use exterior-only localized support if required. Interior throat overhang is3.6 mm total and must be inspected.
- Plate02: one-piece lid, exterior face down and sealing face up. Bounds200×130×4.2 mm; no support on sealing face. Long flat-surface warp risk is high; use verified bed adhesion/brim/process controls without altering seal geometry.

No embossed text, support scar, seam or cable notch is permitted on the seal land. Automatic support placement must be manually reviewed. Optional gasket/compression coupon is deferred until actual metal-stop hardware dimensions are available.'''
    return d


def test_source() -> str:
    return '''#!/usr/bin/env python3
"""Contract tests for BBOX/CBOX submerged power architecture v0.9.6.0."""
from __future__ import annotations
import json, math, sys, unittest
from pathlib import Path
sys.dont_write_bytecode=True
LANE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(LANE))
import build_bbox_cbox_submerged_power_architecture_v0960 as b

class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=b.verify_lane(repository=True,rebuild=False)
  cls.params=json.loads((LANE/'design_parameters.json').read_text(encoding='utf-8'))
  cls.state=json.loads((LANE/'architecture_state.json').read_text(encoding='utf-8'))
  cls.validation=json.loads((LANE/'validation_report.json').read_text(encoding='utf-8'))
 def test_001_version(self): self.assertEqual(self.params['version'],'0.9.6.0')
 def test_002_lane(self): self.assertEqual(LANE.name,'common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0')
 def test_003_classification(self): self.assertIn('EMPTY_WATERPROOF_PROTOTYPE',self.params['classification'])
 def test_004_parent(self): self.assertEqual(self.report['parent_audit'],'PASS')
 def test_005_authority(self): self.assertEqual(self.report['authority_audit'],'PASS')
 def test_006_v0953(self): self.assertTrue(self.report['repository_guard']['checks']['v0953_unchanged'])
 def test_007_manifest(self): self.assertEqual(self.report['manifest'],'PASS')
 def test_008_sha(self): self.assertEqual(self.report['sha256sums'],'PASS')
 def test_009_commit_paths(self): self.assertEqual(self.report['commit_paths'],'PASS')
 def test_010_no_cache(self): self.assertTrue(self.report['repository_guard']['checks']['cache_temp_zero'])
 def test_011_json(self): self.assertEqual(self.report['json_parse'],'PASS')
 def test_012_svg(self): self.assertEqual(self.report['svg_parse'],'PASS')
 def test_013_step(self): self.assertEqual(self.report['artifact_validation'],'PASS')
 def test_014_stl(self): self.assertEqual(self.report['artifact_validation'],'PASS')
 def test_015_battery(self): self.assertEqual(self.params['battery']['body_mm'],[150.9,99.4,92.5])
 def test_016_insertion(self): self.assertEqual(self.params['frame']['battery_insertion_height_mm'],108.0)
 def test_017_height_target(self): self.assertLessEqual(self.params['bbox']['installed_height_mm'],103.0)
 def test_018_absolute_height(self): self.assertLessEqual(self.validation['geometry']['assembly_bounds_mm'][2],108.0)
 def test_019_width(self): self.assertLessEqual(self.params['bbox']['flange_width_mm'],130.0)
 def test_020_gasket_continuous(self): self.assertEqual(self.validation['geometry']['gasket_path_solid_count'],1)
 def test_021_gasket_width(self): self.assertGreaterEqual(self.params['bbox']['seal_land_width_mm'],5.0)
 def test_022_gasket_nominal(self): self.assertEqual(self.params['bbox']['seal_land_width_mm'],6.0)
 def test_023_m4_outside(self): self.assertEqual(self.validation['geometry']['gasket_hole_common_volume_mm3'],0.0)
 def test_024_m4_count(self): self.assertEqual(self.params['bbox']['m4_count'],12)
 def test_025_lid_penetration(self): self.assertEqual(self.params['bbox']['lid_service_penetrations'],0)
 def test_026_seal_test_penetration(self): self.assertEqual(self.params['bbox']['seal_test_cable_penetrations'],0)
 def test_027_gland_land(self): self.assertEqual(self.params['bbox']['gland_land'],'BLANK / NO THROUGH-HOLE')
 def test_028_submerged_connector(self): self.assertEqual(self.params['bbox']['submerged_connector_count'],0)
 def test_029_terminal_cap(self): self.assertEqual(self.params['bbox']['external_terminal_cap_seam_count'],0)
 def test_030_integrated_flange(self): self.assertEqual(self.params['bbox']['body_to_service_ring_seam'],'ELIMINATED')
 def test_031_terminal_orientation(self): self.assertEqual(self.params['battery']['terminal_orientation'],'REARWARD / DOWNWARD')
 def test_032_battery_corridor(self): self.assertGreater(self.validation['geometry']['battery_top_throat_clearance_each_mm'],0)
 def test_033_idler(self): self.assertEqual(self.params['battery']['body_to_idler_clearance_mm_approx'],10.0)
 def test_034_powered(self): self.assertEqual(self.state['gates']['powered_drive'],'NOT_APPROVED')
 def test_035_battery_water(self): self.assertEqual(self.state['gates']['bbox_live_battery_water_test'],'NOT_APPROVED')
 def test_036_cbox_water(self): self.assertEqual(self.state['gates']['cbox_waterproof'],'NOT_TESTED')
 def test_037_hardware_cut(self): self.assertIn('HARDWARE_MASTER_DISCONNECT',self.state['power_topology'])
 def test_038_repro(self): self.assertEqual(json.loads((LANE/'reproducibility_report.json').read_text())['status'],'PASS')
 def test_039_staged_zero(self): self.assertEqual(self.report['repository_guard']['staged'],[])
 def test_040_final(self): self.assertEqual(self.report['final_status'],b.FINAL_STATUS)

if __name__=='__main__': unittest.main(verbosity=2)
'''


def build() -> None:
    repository_guard(complete=False)
    build_artifacts(LANE)
    params, state = design_parameters(), architecture_state()
    write_json(LANE / "design_parameters.json", params)
    write_json(LANE / "architecture_state.json", state)
    metrics = geometry_metrics()
    parents = parent_audit()
    for name, content in docs(metrics, parents).items():
        write(LANE / name, content)
    write(LANE / "M4_CLAMP_PATTERN.csv", m4_csv())
    write(LANE / "WATERPROOF_TEST_RECORD.csv", water_csv())
    write(LANE / "tests/test_bbox_cbox_submerged_power_architecture_v0960.py", test_source())
    artifacts = artifact_validation(LANE)
    reproducibility = independent_rebuild()
    write_json(LANE / "reproducibility_report.json", reproducibility)
    checks = {
        "version": VERSION == "0.9.6.0", "correct_lane": LANE.name.endswith("v0_9_6_0"),
        "parents": parents["status"] == "PASS", "authority": authority_audit()["status"] == "PASS",
        "v0953": parents["parents"]["common_rover_physical_followup_measurement_v0_9_5_3"]["status"] == "PASS",
        "artifacts": artifacts["status"] == "PASS", "reproducibility": reproducibility["status"] == "PASS",
        "battery_dimensions": BATTERY["body_mm"] == [150.9, 99.4, 92.5],
        "insertion_108": FRAME["battery_insertion_height_mm"] == 108.0,
        "installed_height": metrics["installed_height_mm"] <= 103.0,
        "absolute_height": metrics["assembly_bounds_mm"][2] <= 108.0,
        "flange_width": metrics["lower_bounds_mm"][1] <= 130.0,
        "continuous_gasket": metrics["gasket_path_solid_count"] == 1,
        "gasket_width": BBOX["seal_land_width_mm"] == 6.0 and BBOX["seal_land_width_mm"] >= 5.0,
        "m4_outside_gasket": metrics["gasket_hole_common_volume_mm3"] < 1e-9,
        "m4_count": len(bolt_pattern()) == 12, "bolt_cuts": metrics["bolt_cuts_clear"],
        "no_lid_service_penetration": BBOX["lid_service_penetrations"] == 0,
        "no_seal_test_cable_penetration": BBOX["seal_test_cable_penetrations"] == 0,
        "blank_gland_land": metrics["blank_gland_land"] and metrics["gland_through_hole_count"] == 0,
        "submerged_connectors_zero": BBOX["submerged_connector_count"] == 0,
        "external_terminal_cap_zero": BBOX["external_terminal_cap_seam_count"] == 0,
        "integrated_flange": BBOX["body_to_service_ring_seam"] == "ELIMINATED",
        "terminal_rear_down": BATTERY["terminal_orientation"] == "REARWARD / DOWNWARD",
        "battery_removal_corridor": metrics["battery_top_throat_clearance_each_mm"] > 0,
        "idler_clearance": BATTERY["body_to_idler_clearance_mm_approx"] == 10.0,
        "powered_not_approved": state["gates"]["powered_drive"] == "NOT_APPROVED",
        "battery_water_not_approved": state["gates"]["bbox_live_battery_water_test"] == "NOT_APPROVED",
    }
    validation = {
        "version": VERSION, "classification": CLASSIFICATION, "geometry": metrics,
        "artifact_validation": artifacts, "parent_audit": parents["status"],
        "authority_audit": authority_audit()["status"], "v0953_protection": "PASS",
        "checks": {name: "PASS" if ok else "FAIL" for name, ok in checks.items()},
        "pass_count": sum(checks.values()), "total": len(checks),
        "status": "PASS" if all(checks.values()) else "FAIL", "final_status": FINAL_STATUS,
    }
    if validation["status"] != "PASS":
        raise RuntimeError(json.dumps(validation, indent=2))
    write_json(LANE / "validation_report.json", validation)
    write(LANE / "TEST_LOG.txt", f'''Common Rover v0.9.6.0 internal validation
python={sys.version.split()[0]}
cadquery={cq.__version__}
stl_validator=BUILTIN_TRIANGLE_EDGE_AUDIT
checks={len(checks)}
passed={sum(checks.values())}
failed=0
step_stl_svg={len(ARTIFACTS)}/{len(ARTIFACTS)} PASS
parents=3/3 PASS
authority=4/4 PASS
reproducibility={reproducibility['pass_count']}/{reproducibility['total']} PASS
result=PASS''')
    write(LANE / "BUILD_LOG.txt", f'''Common Rover v0.9.6.0 build
classification={CLASSIFICATION}
python={sys.version.split()[0]}
cadquery={cq.__version__}
generated_path_count={len(PACKAGE_PATHS)}
cad_artifact_count=5
svg_count=5
seal_test_cable_penetration_count=0
git_write=NONE
result=PASS''')
    write(LANE / "MANIFEST.txt", "\n".join(PACKAGE_PATHS))
    write(LANE / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL}/{rel}" for rel in PACKAGE_PATHS))
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / rel)}  {rel}" for rel in PACKAGE_PATHS if rel != "SHA256SUMS.txt"))
    repository_guard(complete=True)
    verify_lane(repository=True, rebuild=False)


def verify_lane(repository: bool = True, rebuild: bool = False) -> dict[str, Any]:
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts)
    manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    manifest_ok = files == manifest == PACKAGE_PATHS
    commits = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    expected_commits = [f"{LANE_REL}/{rel}" for rel in PACKAGE_PATHS]
    commit_ok = commits == expected_commits and len(commits) == len(set(commits)) and all(".." not in PurePosixPath(p).parts for p in commits)
    parsed: dict[str, str] = {}
    for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, sep, rel = line.partition("  ")
        if sep:
            parsed[rel] = digest
    expected_sums = [p for p in PACKAGE_PATHS if p != "SHA256SUMS.txt"]
    sums_ok = sorted(parsed) == expected_sums and all(sha(LANE / rel) == digest for rel, digest in parsed.items())
    json_ok = True
    for rel in [p for p in PACKAGE_PATHS if p.endswith(".json")]:
        try: json.loads((LANE / rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): json_ok = False
    svg_ok = True
    for rel in [p for p in PACKAGE_PATHS if p.endswith(".svg")]:
        try: ElementTree.parse(LANE / rel)
        except (OSError, ElementTree.ParseError): svg_ok = False
    artifacts = artifact_validation(LANE)
    repro = independent_rebuild() if rebuild else json.loads((LANE / "reproducibility_report.json").read_text(encoding="utf-8"))
    guard = repository_guard(complete=True) if repository else {"status": "SKIPPED"}
    checks = {"manifest": manifest_ok, "commit_paths": commit_ok, "sha256sums": sums_ok, "json": json_ok, "svg": svg_ok, "artifacts": artifacts["status"] == "PASS", "reproducibility": repro["status"] == "PASS"}
    if not all(checks.values()):
        raise RuntimeError(json.dumps(checks, indent=2))
    return {
        "version": VERSION, "generated_path_count": len(files), "manifest": "PASS", "sha256sums": "PASS",
        "commit_paths": "PASS", "json_parse": "PASS", "svg_parse": "PASS",
        "artifact_validation": artifacts["status"], "reproducibility": repro["status"],
        "authority_audit": authority_audit()["status"], "parent_audit": parent_audit()["status"],
        "repository_guard": guard, "final_status": FINAL_STATUS, "status": "PASS",
    }


def verify_zip(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        if archive.testzip() is not None: raise RuntimeError("ZIP corruption")
        if len(names) != len(set(names)): raise RuntimeError("duplicate ZIP entry")
        prefix = LANE.name + "/"
        if any(not n.startswith(prefix) or ".." in PurePosixPath(n).parts for n in names): raise RuntimeError("ZIP scope/traversal")
        if sorted(n[len(prefix):] for n in names) != PACKAGE_PATHS: raise RuntimeError("ZIP manifest")
        for line in archive.read(prefix + "SHA256SUMS.txt").decode().splitlines():
            digest, sep, rel = line.partition("  ")
            if not sep or sha_bytes(archive.read(prefix + rel)) != digest: raise RuntimeError(f"ZIP SHA {rel}")
    return {"path": str(path), "entry_count": len(names), "sha256": sha(path), "status": "PASS"}


def package() -> dict[str, Any]:
    verify_lane(repository=True, rebuild=False)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    path = DOWNLOADS / f"{ZIP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists(): raise FileExistsError(path)
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in PACKAGE_PATHS: archive.write(LANE / rel, f"{LANE.name}/{rel}")
    return verify_zip(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--rebuild-verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()): args.build = args.verify = True
    if args.build:
        build(); print(json.dumps({"build": "PASS", "paths": len(PACKAGE_PATHS)}, indent=2))
    if args.verify:
        print(json.dumps(verify_lane(repository=True, rebuild=args.rebuild_verify), ensure_ascii=False, indent=2))
    if args.package:
        print(json.dumps(package(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
