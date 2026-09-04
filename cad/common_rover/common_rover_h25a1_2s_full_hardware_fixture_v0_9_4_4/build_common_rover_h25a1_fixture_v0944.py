#!/usr/bin/env python3
"""Build v0.9.4.4 H2.5-A1-2S measured full-hardware test fixtures."""
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

import cadquery as cq


VERSION = "0.9.4.4"
CLASSIFICATION = "PHYSICAL_HARDWARE_FIT_FIXTURE"
RELEASE = "HOLD"
FINAL_STATUS = "H25A1_V2_PHYSICAL_TEST_ARTIFACTS_COMPLETE / USER_PHYSICAL_TEST_PENDING"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_h25a1_2s_full_hardware_fixture_v0_9_4_4"
LANE = Path(__file__).resolve().parent
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
BASE_OUTSIDE_UNTRACKED = 1467
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_H25A1_Full_Hardware_Fixture_v0_9_4_4_"

P3_REL = "cad/common_rover/common_rover_service_motion_servo_slide_clutch_h25a1_v0_9_4_3"
P2_REL = "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2"
P3 = REPO_ROOT / P3_REL
P2 = REPO_ROOT / P2_REL
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
P3_HASHES = {
    "MANIFEST.txt": "af588b754f41ae049463312b123c33d5c22be91eb15864a6207ebe5600f16d15",
    "SHA256SUMS.txt": "55a46db50ceaf311ebe788f858a45752a2a8296c475b9bb140a9ab069df70fa0",
    "geometry_manifest.json": "fe8e5ef60a6d221a4479a3379e0baf27ee5b716c3d365c8d9ddb7a12781e2dee",
    "validation_report.json": "fcc789a77013a54f877bf4a734d4c77d4b4f4341419d8bc93cb0d4f10cae7e26",
    "build_common_rover_service_servo_clutch_v0943.py": "04b256b0e4e4dcc70c343226026579f11a7b738464fe08bdb42abf838d0fb8e2",
    "tests/test_common_rover_service_servo_clutch_v0943.py": "31c0a65d006807a295905bd3c23a97ec7d06bf5a476a768319a72231f3d63fef",
}
P2_HASHES = {
    "MANIFEST.txt": "a983a48c6f9394a9f90b112b3f1f7e2f89dbdc70a34044e4d4711bf6cf6adf4a",
    "SHA256SUMS.txt": "e0033d12141e805b11ec53dbe5c2de5e65fecb46a1a87a1b9f30b9113cce82b1",
    "geometry_manifest.json": "c9a9ce48fba8318ff0d41155c2cb47ec5a5b6beb3d688385ef0ba8f9cd90408c",
    "validation_report.json": "37d2da249ab66238b4ecc715550a45d7ef7a6a427fc533cb09c75248031d1da8",
    "build_common_rover_physical_fit_closure_v0942.py": "3356276d37bee8f7e84c82c9ada8b128c45206148952a0c3137d526590259172",
    "tests/test_common_rover_physical_fit_closure_v0942.py": "a6f5a0adce49bc71797175f337fe964a7dae3a13f87c4a815cbb0692db8609f3",
}

DOCS = [
    "README.md", "PARENT_AUDIT.md", "SOURCE_TRACE.md", "H25A1_FULL_HARDWARE_MEASUREMENTS.md",
    "H25A1_FULL_HARDWARE_ENVELOPE.md", "H25A1_V2_FIT_COUPON_SPEC.md",
    "H25A1_V2_STATIC_FIXTURE_SPEC.md", "H25A1_REACTION_KEY_SPEC.md",
    "H25A1_STATIC_TORQUE_TEST_PLAN.md", "H25A1_24H_CREEP_TEST.md",
    "H25A1_12T_HUB_FEASIBILITY.md", "H25A1_PROTECTED_GEOMETRY_AUDIT.md",
    "PRINT_PLAN.md", "PHYSICAL_RESULT_FORM.md", "MISSING_MEASUREMENTS.md", "DESIGN_GATE.md",
]
CAD = [
    "cad/collar_full_hardware_reference.step", "cad/full_hardware_envelope.step",
    "cad/washer_relief_coupon_90_92_94.step", "cad/washer_relief_coupon_90_92_94.stl",
    "cad/full_hardware_fit_coupon_v2.step", "cad/full_hardware_fit_coupon_v2.stl",
    "cad/reaction_key_41.step", "cad/reaction_key_42.step", "cad/reaction_key_43.step",
    "cad/reaction_key_41.stl", "cad/reaction_key_42.stl", "cad/reaction_key_43.stl",
    "cad/static_fixture_v2_body.step", "cad/static_fixture_v2_body.stl",
    "cad/static_fixture_v2_assembly.step", "cad/central_hub_feasibility_reference.step",
    "cad/PLATE_01_H25A1_FULL_HARDWARE_FIT.step", "cad/PLATE_01_H25A1_FULL_HARDWARE_FIT.stl",
    "cad/PLATE_02_H25A1_STATIC_FIXTURE_V2.step", "cad/PLATE_02_H25A1_STATIC_FIXTURE_V2.stl",
]
DRAWINGS = [
    "drawings/full_hardware_measurement_map.svg", "drawings/full_hardware_radial_section.svg",
    "drawings/full_hardware_axial_section.svg", "drawings/washer_relief_coupon_map.svg",
    "drawings/reaction_key_map.svg", "drawings/static_fixture_v2_section.svg",
    "drawings/static_fixture_v2_exploded.svg", "drawings/torque_load_path.svg",
    "drawings/protected_12t_margin.svg",
]
JSONS = ["dimensions.json", "interfaces.json", "hardware.json", "test_limits.json",
         "measurement_ledger.json", "geometry_manifest.json", "validation_report.json"]
SOURCE = ["build_common_rover_h25a1_fixture_v0944.py", "tests/test_common_rover_h25a1_fixture_v0944.py"]
RELEASE_FILES = ["MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt", "BUILD_LOG.txt", "TEST_LOG.txt"]
PACKAGE_PATHS = sorted(DOCS + CAD + DRAWINGS + JSONS + SOURCE + RELEASE_FILES)

MEASURED = {
    "collar_od_mm": 15.9, "collar_id_mm": 10.1, "collar_width_mm": 3.0,
    "set_screw_qty": 2, "set_screw_angle_deg": 90.0, "set_screw_nominal": "M4",
    "set_screw_major_od_measured_mm": 3.8, "set_screw_length_mm": 4.0,
    "set_screw_projection_mm": 1.0, "thread_pitch": None,
    "washer_max_od_mm": 8.8, "washer_stack_mm": 1.8,
    "screw_head_max_od_mm": 6.8, "screw_head_height_mm": 2.8,
    "full_radial_envelope_mm": 20.0, "full_axial_width_mm": 8.8,
}
PROTECTED = {
    "teeth": 12, "phase_deg": 15.0, "spacing_deg": 30.0, "tip_radius_mm": 33.07,
    "root_radius_mm": 29.47, "tip_width_mm": 7.5, "root_width_mm": 9.5,
    "axial_width_mm": 44.0, "pitch_diameter_mm": 76.3943726841,
    "buried_root_overlap_mm": 4.0, "external_geometry_delta_mm": 0.0,
    "radial_tooth_root_access_holes": 0,
}
DERIVED = {
    "hardware_to_root_theoretical_margin_mm": 9.47,
    "centered_axial_margin_each_side_mm": 17.6,
    "service_radial_candidates_mm": [20.2, 20.4, 20.6],
    "service_axial_candidates_mm": [9.0, 9.2, 9.4],
    "washer_relief_candidates_mm": [9.0, 9.2, 9.4],
    "reaction_shank_candidates_mm": [4.1, 4.2, 4.3],
    "shaft_clearance_candidates_mm": [10.2, 10.3, 10.4],
    "neutral_fixture": {"radial_mm": 20.4, "axial_mm": 9.2, "washer_mm": 9.2,
                        "reaction_mm": 4.2, "shaft_mm": 10.3, "final": False},
    "reaction_key_radial_allocation_mm": 3.5,
    "minimum_remaining_petg_wall_mm": 5.37,
    "link_width_reference_mm": 53.6, "centered_link_side_protrusion_mm": 4.8,
    "link_side_status": "BLOCKED_UNLESS_PHYSICAL_AXIAL_REGISTRATION_VALIDATED",
}
FAILURE_HISTORY = {
    "H0": "PHYSICAL_FAIL_SLIP_PETG_FRICTION_CLAMP_REJECTED",
    "H2.3": "FAIL_OD6P8_WASHER_EXCEEDS_6P001_ROOT_GAP_AND_LINK_INTERFERENCE",
    "H2.4": "FAIL_RADIAL_ACCESS_REMOVES_0P499080075_MM3_PROTECTED_ROOT_LINK",
    "absolute_rules": ["NO_PETG_FRICTION_ONLY_SHAFT_CLAMP", "NO_RADIAL_TOOTH_ROOT_SERVICE_HOLE",
                       "NO_PROTECTED_12T_EXTERNAL_CHANGE", "NO_FORCED_WASHER_PASSAGE_THROUGH_ROOT"],
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def box(x: float, y: float, z: float, cx=0.0, cy=0.0, cz=0.0) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate((cx, cy, cz))


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


def raised(text: str, x: float, y: float, z: float, size=3.2) -> cq.Workplane:
    return cq.Workplane("XY").text(text, size, 0.6, halign="center", valign="center").translate((x, y, z))


def export(shape: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path))
    if path.suffix.lower() in {".step", ".stp"}:
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"(FILE_NAME\('Open CASCADE Shape Model',')[^']+(')", r"\g<1>2000-01-01T00:00:00\2", text)
        text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
        occurrence = 0
        def normalize_occurrence(match: re.Match[str]) -> str:
            nonlocal occurrence
            occurrence += 1
            return match.group(1) + str(occurrence) + match.group(2)
        text = re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')", normalize_occurrence, text)
        path.write_text(text, encoding="utf-8", newline="\n")


def audit_dir(root: Path, expected_count: int, expected_hashes: dict[str, str]) -> dict[str, Any]:
    files = [p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    actual = {name: sha(root / name) for name in expected_hashes}
    return {"path": root.relative_to(REPO_ROOT).as_posix(), "file_count": len(files), "hashes": actual,
            "status": "CAD_PASS" if len(files) == expected_count and actual == expected_hashes else "FAIL"}


def parent_audit() -> dict[str, Any]:
    p3 = audit_dir(P3, 66, P3_HASHES)
    p2 = audit_dir(P2, 57, P2_HASHES)
    return {"v0943": p3, "v0942": p2,
            "runtime_reproduction": {"v0943": "19_ARTIFACT_BYTE_PASS_34_TEST_PASS",
                                     "v0942": "11_STANDALONE_PASS_24_TEST_PASS"},
            "status": "CAD_PASS" if p3["status"] == p2["status"] == "CAD_PASS" else "FAIL"}


def authority_audit() -> dict[str, Any]:
    actual = {name: sha(REPO_ROOT / name) for name in AUTHORITY_HASHES}
    return {"hashes": actual, "status": "CAD_PASS" if actual == AUTHORITY_HASHES else "FAIL"}


def repository_guard(complete: bool = False) -> dict[str, Any]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    tracked = sorted(git("diff", "--name-only").splitlines())
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    untracked = sorted(git("ls-files", "--others", "--exclude-standard").splitlines())
    lane = sorted(x[len(LANE_REL) + 1:] for x in untracked if x.startswith(LANE_REL + "/"))
    outside = [x for x in untracked if not x.startswith(LANE_REL + "/")]
    ignored_lane = git("ls-files", "--others", "-i", "--exclude-standard", "--", LANE_REL).splitlines()
    forbidden = [p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and
                 (p.suffix.lower() in {".pyc", ".dxf", ".3mf", ".gcode"} or "__pycache__" in p.parts)]
    checks = {
        "root": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "tracked_authority_set_preserved": set(tracked) == set(AUTHORITY_HASHES), "staged_zero": not staged,
        "outside_untracked_preserved": len(outside) == BASE_OUTSIDE_UNTRACKED,
        "lane_scope": set(lane).issubset(PACKAGE_PATHS),
        "lane_complete": set(lane) == set(PACKAGE_PATHS) if complete else True,
        "authority_hashes": authority_audit()["status"] == "CAD_PASS",
        "parent_hashes": parent_audit()["status"] == "CAD_PASS",
        "ignored_lane_zero": not ignored_lane, "forbidden_lane_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"checks": checks, "tracked": tracked, "staged": staged,
                            "outside": len(outside), "lane": lane, "ignored": ignored_lane, "forbidden": forbidden})
    return {"root": str(root), "branch": branch, "head": head, "tracked": tracked, "staged": staged,
            "untracked_total": len(untracked), "outside_untracked": len(outside), "lane_untracked": len(lane),
            "checks": checks, "status": "CAD_PASS"}


def full_hardware_parts() -> dict[str, cq.Workplane]:
    collar = cq.Workplane("XY").circle(15.9 / 2).circle(10.1 / 2).extrude(3).translate((0, 0, -1.5))
    screw_x = cyl(1.9, 4.0, (5.05, 0, 0), (1, 0, 0))
    screw_y = cyl(1.9, 4.0, (0, 5.05, 0), (0, 1, 0))
    washer_x = cyl(4.4, 1.8, (8.95, 0, 0), (1, 0, 0)).cut(cyl(2.05, 2.0, (8.85, 0, 0), (1, 0, 0)))
    washer_y = cyl(4.4, 1.8, (0, 8.95, 0), (0, 1, 0)).cut(cyl(2.05, 2.0, (0, 8.85, 0), (0, 1, 0)))
    head_x = cyl(3.4, 2.8, (10.75, 0, 0), (1, 0, 0))
    head_y = cyl(3.4, 2.8, (0, 10.75, 0), (0, 1, 0))
    return {"collar": collar, "screw_x": screw_x, "screw_y": screw_y,
            "washer_x": washer_x, "washer_y": washer_y, "head_x": head_x, "head_y": head_y}


def full_hardware() -> cq.Compound:
    return compound(list(full_hardware_parts().values()))


def hardware_envelope() -> cq.Compound:
    shell = cq.Workplane("XY").circle(20.0).circle(19.4).extrude(8.8).translate((0, 0, -4.4))
    end_rings = [cq.Workplane("XY").circle(20).circle(18.8).extrude(0.5).translate((0, 0, z)) for z in (-4.4, 3.9)]
    return compound([full_hardware(), shell, *end_rings])


def washer_coupon() -> cq.Workplane:
    part = box(120, 34, 6, 0, 0, 3)
    for x, width, label in zip((-40, 0, 40), DERIVED["washer_relief_candidates_mm"], ("W90", "W92", "W94")):
        part = part.cut(box(width, 20, 8, x, 14, 4)).union(raised(label, x, -10, 5.8))
    return part.clean()


def fit_coupon() -> cq.Workplane:
    part = box(150, 58, 12, 0, 0, 6)
    rows = zip((-50, 0, 50), DERIVED["service_radial_candidates_mm"], DERIVED["service_axial_candidates_mm"],
               ("R202 A90", "R204 A92", "R206 A94"))
    for x, radius, depth, label in rows:
        part = part.cut(cyl(radius, depth, (x, 4, 12), (0, 0, -1)))
        part = part.cut(cyl(5.5, 14, (x, 4, -1)))
        part = part.union(raised(label, x, -23, 11.8, 2.8))
    return part.clean()


def reaction_key(slot: float, label: str) -> cq.Workplane:
    # Open-edge, three-stage service profile.  The 9.2 mm washer relief is
    # clearance-only; the 6.9 mm head land is the first intended metal
    # reaction surface, followed by the parameterized shank throat.  The
    # 17.8 mm body width keeps the installed orthogonal keys mutually clear.
    part = box(28, 17.8, 4, 0, 0, 2)
    part = part.cut(box(1.8, 9.2, 6, -13.1, 0, 3))
    part = part.cut(box(2.8, 6.9, 6, -10.8, 0, 3))
    part = part.cut(box(19.4, slot, 6, 0.3, 0, 3))
    part = part.union(raised(label, 12, 0, 3.8, 2.6))
    return part.clean()


def static_body() -> cq.Workplane:
    part = box(84, 84, 16, 0, 0, 8)
    part = part.cut(cyl(20.6, 9.4, (0, 0, 16), (0, 0, -1)))
    part = part.cut(cyl(10.3 / 2, 18, (0, 0, -1)))
    # Full-width channels open at +X/+Y.  Each orthogonal key therefore slides
    # in from outside; no washer removal, blind pocket or hidden roof is used.
    part = part.cut(box(26, 18.2, 10, 31, 0, 12)).cut(box(18.2, 26, 10, 0, 31, 12))
    for x, y in ((-30, -30), (-30, 30), (30, -30), (30, 30)):
        part = part.cut(cyl(2.6, 18, (x, y, -1)))
    return part.clean()


def static_assembly() -> cq.Compound:
    zc = 11.0
    hardware = full_hardware().translate((0, 0, zc))
    shaft = cyl(5.0, 56, (0, 0, -20))
    # 22.95 locates the staged open edge at washer x/y=8.95 mm.  The 9.2 mm
    # washer relief and 6.9 mm head land retain 0.2/0.1 mm diametral candidates.
    key_x = reaction_key(4.2, "R42").translate((22.95, 0, 8))
    key_y = reaction_key(4.2, "R42").rotate((0, 0, 0), (0, 0, 1), 90).translate((0, 22.95, 8))
    return compound([static_body(), hardware, shaft, key_x, key_y])


def protected_root_annulus(width: float = 44.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(33.07).circle(29.47).extrude(width).translate((0, 0, -width / 2))


def hub_feasibility() -> cq.Compound:
    hardware = cq.Workplane("XY").circle(20).extrude(8.8).translate((0, 0, -4.4))
    service = cq.Workplane("XY").circle(20.6).circle(20.0).extrude(9.4).translate((0, 0, -4.7))
    key_zone = cq.Workplane("XY").circle(24.1).circle(20.6).extrude(12).translate((0, 0, -6))
    wall = cq.Workplane("XY").circle(29.47).circle(24.1).extrude(16).translate((0, 0, -8))
    cover = cq.Workplane("XY").circle(24.1).extrude(3).translate((0, 0, 7))
    axial_refs = [box(2, 72, 2, 0, 0, z) for z in (-22, 22)]
    return compound([protected_root_annulus(), hardware, service, key_zone, wall, cover, *axial_refs])


def plate1() -> cq.Compound:
    parts: list[Any] = [fit_coupon().translate((0, 35, 0)), washer_coupon().translate((-15, -35, 0))]
    for x, slot, label in zip((52, 84, 116), (4.1, 4.2, 4.3), ("R41", "R42", "R43")):
        parts.append(reaction_key(slot, label).translate((x, -35, 0)))
    return compound(parts)


def plate2() -> cq.Compound:
    parts: list[Any] = [static_body().translate((-50, 0, 0))]
    for x in (20, 50, 80, 110):
        parts.append(reaction_key(4.2, "R42").translate((x, 0, 0)))
    return compound(parts)


def artifact_jobs() -> list[tuple[Any, str]]:
    k41, k42, k43 = reaction_key(4.1, "R41"), reaction_key(4.2, "R42"), reaction_key(4.3, "R43")
    return [
        (full_hardware(), CAD[0]), (hardware_envelope(), CAD[1]),
        (washer_coupon(), CAD[2]), (washer_coupon(), CAD[3]),
        (fit_coupon(), CAD[4]), (fit_coupon(), CAD[5]),
        (k41, CAD[6]), (k42, CAD[7]), (k43, CAD[8]),
        (k41, CAD[9]), (k42, CAD[10]), (k43, CAD[11]),
        (static_body(), CAD[12]), (static_body(), CAD[13]),
        (static_assembly(), CAD[14]), (hub_feasibility(), CAD[15]),
        (plate1(), CAD[16]), (plate1(), CAD[17]), (plate2(), CAD[18]), (plate2(), CAD[19]),
    ]


def common_volume(a: Any, b: Any) -> float:
    sa = a.val() if isinstance(a, cq.Workplane) else a
    sb = b.val() if isinstance(b, cq.Workplane) else b
    return float(sa.intersect(sb).Volume())


def interference_report() -> dict[str, Any]:
    hardware = full_hardware()
    root = protected_root_annulus()
    key_zone = cq.Workplane("XY").circle(24.1).circle(20.6).extrude(12).translate((0, 0, -6))
    parts = full_hardware_parts()
    # Place hardware at the neutral fixture cavity elevation.
    zc = 11.0
    body = static_body()
    placed = {name: shape.translate((0, 0, zc)) for name, shape in parts.items()}
    placed_all = compound(list(placed.values()))
    key_x = reaction_key(4.2, "R42").translate((22.95, 0, 8))
    key_y = reaction_key(4.2, "R42").rotate((0, 0, 0), (0, 0, 1), 90).translate((0, 22.95, 8))
    installed_keys = compound([key_x, key_y])
    checks = [
        ("HARDWARE_VS_PROTECTED_ROOT", common_volume(hardware, root)),
        ("HARDWARE_VS_REACTION_KEY_ZONE", common_volume(hardware, key_zone)),
        ("WASHERS_VS_FIXTURE_BODY", common_volume(compound([placed["washer_x"], placed["washer_y"]]), body)),
        ("HEADS_VS_FIXTURE_BODY", common_volume(compound([placed["head_x"], placed["head_y"]]), body)),
        ("FULL_HARDWARE_VS_FIXTURE_BODY", common_volume(placed_all, body)),
        ("FULL_HARDWARE_VS_INSTALLED_REACTION_KEYS", common_volume(placed_all, installed_keys)),
        ("INSTALLED_REACTION_KEYS_MUTUAL", common_volume(key_x, key_y)),
        ("INSTALLED_REACTION_KEYS_VS_FIXTURE_BODY", common_volume(installed_keys, body)),
        ("REACTION_KEY_ZONE_VS_PROTECTED_ROOT", common_volume(key_zone, root)),
    ]
    rows = [{"check": name, "common_volume_mm3": round(volume, 9),
             "status": "CAD_PASS" if volume <= 1e-7 else "FAIL"} for name, volume in checks]
    wall_by_candidate = [{"service_radius_mm": r, "reaction_allocation_mm": 3.5,
                          "remaining_petg_wall_mm": round(29.47 - r - 3.5, 2),
                          "target_ge_3": 29.47 - r - 3.5 >= 3.0}
                         for r in DERIVED["service_radial_candidates_mm"]]
    return {"method": "CADQUERY_ACTUAL_COMMON_VOLUME_FOR_REFERENCE_SOLIDS",
            "rows": rows, "all_zero": all(r["status"] == "CAD_PASS" for r in rows),
            "wall_by_candidate": wall_by_candidate,
            "axial": {"hardware_width_mm": 8.8, "hub_width_mm": 44.0, "margin_each_side_mm": 17.6,
                      "link_width_mm": 53.6, "centered_side_protrusion_mm": 4.8,
                      "link_status": DERIVED["link_side_status"]},
            "physical_fit_status": "USER_TEST_PENDING"}


def stl_semantic(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise RuntimeError(f"bad binary STL: {path}")
    mins, maxs, positive = [math.inf] * 3, [-math.inf] * 3, 0
    for i in range(count):
        vals = struct.unpack_from("<12f", data, 84 + 50 * i)
        pts = [vals[3:6], vals[6:9], vals[9:12]]
        a = [pts[1][j] - pts[0][j] for j in range(3)]
        b = [pts[2][j] - pts[0][j] for j in range(3)]
        cross = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
        positive += sum(x * x for x in cross) > 1e-12
        for p in pts:
            for j in range(3):
                mins[j], maxs[j] = min(mins[j], p[j]), max(maxs[j], p[j])
    if positive != count:
        raise RuntimeError(f"degenerate STL: {path}")
    return {"triangles": count, "bounds_mm": [round(maxs[j] - mins[j], 4) for j in range(3)]}


def source_trace() -> list[dict[str, str]]:
    paths = [
        f"{P3_REL}/H25A1_FULL_HARDWARE_MEASUREMENT_SHEET.md",
        f"{P3_REL}/H25A1_FULL_HARDWARE_FIT_ARCHITECTURE.md",
        f"{P2_REL}/H25A1_COLLAR_COUPON_SPEC.md", f"{P2_REL}/H25A1_REACTION_COUPON_SPEC.md",
        "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0/H0_H23_H24_FAILURE_HISTORY.md",
        "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0/H25A1_DESIGN_SPEC.md",
        "cad/common_rover/common_rover_four_point_set_screw_drive_sprocket_v0_9_3_7_1/PHYSICAL_FAILURE_INPUT.md",
        "cad/common_rover/common_rover_staggered_alternating_deep_nut_drive_sprocket_v0_9_3_7_2/DESIGN_REVIEW.md",
        "cad/common_rover/common_rover_staggered_deep_nut_set_screw_drive_sprocket_v0_9_3_7_3/EXTERNAL_GEOMETRY_COMPARISON.md",
    ]
    return [{"path": p, "sha256": sha(REPO_ROOT / p)} for p in paths]


def dimensions() -> dict[str, Any]:
    return {"version": VERSION, "classification": CLASSIFICATION, **MEASURED,
            "target_shaft_mm": 10.0, "measurement_classification": "MEASURED_USER_REPORTED",
            "protected_12t": PROTECTED, "derived": DERIVED}


def interfaces() -> dict[str, Any]:
    return {
        "designation": "H25A1_2S_DUAL_SET_SCREW_REACTION_KEY",
        "load_path": "PHI10_SHAFT_M4X2_METAL_COLLAR_TWO_METAL_REACTION_FEATURES_REPLACEABLE_KEY_PETG_HUB_12T",
        "full_hardware_insertion": "OPEN_TOP_AXIAL_WITH_OPEN_BACK_PUSH_THROUGH",
        "washer_primary_torque_path": False, "cover_bolts_primary_torque_path": False,
        "fixture": {"shaft_hole_candidates_mm": [10.2, 10.3, 10.4], "neutral_mm": 10.3,
                    "bearing_fit": False, "external_reaction": "FIXTURE_BODY_TO_BENCH_HAND_TOOL"},
        "full_sprocket": {"manufacturing": "HOLD", "powered": False, "field": False},
    }


def hardware() -> dict[str, Any]:
    return {"actual": MEASURED, "full_assembly_required": ["COLLAR", "M4_X", "M4_Y", "CAPTIVE_WASHER_X",
                                                             "CAPTIVE_WASHER_Y", "HEAD_X", "HEAD_Y"],
            "reference_geometry": "MEASURED_MAXIMA_WITH_SYMMETRIC_PARAMETRIC_PLACEMENT",
            "remaining_asymmetry_hold": True, "reaction_key": {"variants_mm": [4.1, 4.2, 4.3],
            "neutral_mm": 4.2, "neutral_final": False, "washer_relief_mm": 9.2,
            "head_reaction_land_relief_mm": 6.9, "body_width_mm": 17.8,
            "installed_center_offset_mm": 22.95, "replaceable": True, "spare_ratio": 1.0},
            "failure_history": FAILURE_HISTORY}


def test_limits() -> dict[str, Any]:
    return {"static_torque_nm": [0.25, 0.50, 0.75], "creep_hours": 24,
            "stop_on_first_failure": True,
            "failure": ["SHAFT_COLLAR_SLIP", "COLLAR_ROTATION", "M4_BACKOUT", "WASHER_PETG_DIG",
                        "KEY_CRACK", "KEY_PERMANENT_CRUSH", "PETG_WHITENING", "PETG_CRACK",
                        "PERMANENT_EXCESSIVE_PLAY", "FIXTURE_SPLIT", "CANNOT_REMOVE_HARDWARE"],
            "minimum_petg_wall_target_mm": 3.0, "bambu_a1_bed_mm": [256, 256],
            "powered_rotation": False, "crawler_test": False, "field": False}


def measurement_ledger() -> dict[str, Any]:
    rows = []
    for index, (name, value) in enumerate(MEASURED.items(), 1):
        classification = "HOLD" if value is None else "MEASURED_USER_REPORTED"
        rows.append({"id": f"H25-{index:02d}", "name": name.upper(), "value": value, "classification": classification})
    rows += [
        {"id": "DER-01", "name": "ROOT_MINUS_HARDWARE", "value": 9.47, "classification": "DERIVED"},
        {"id": "DER-02", "name": "CENTERED_AXIAL_MARGIN_EACH_SIDE", "value": 17.6, "classification": "DERIVED"},
        {"id": "DER-03", "name": "MIN_REMAINING_PETG_WALL_R206", "value": 5.37, "classification": "DERIVED_CANDIDATE"},
        {"id": "DER-04", "name": "LINK_CENTERED_SIDE_PROTRUSION", "value": 4.8, "classification": "DERIVED_BLOCKED"},
    ]
    return {"schema": "paddy_swarm.common_rover.h25a1.full_hardware_fixture.measurements.v0.9.4.4", "rows": rows}


def printability() -> dict[str, Any]:
    rows = {}
    for name, shape in (("PLATE_01", plate1()), ("PLATE_02", plate2()), ("FIT_COUPON", fit_coupon()),
                        ("STATIC_BODY", static_body()), ("REACTION_KEY", reaction_key(4.2, "R42"))):
        b = shape.val().BoundingBox() if isinstance(shape, cq.Workplane) else shape.BoundingBox()
        rows[name] = {"bounds_mm": [round(b.xlen, 3), round(b.ylen, 3), round(b.zlen, 3)],
                      "fits_bambu_a1_xy": b.xlen <= 256 and b.ylen <= 256,
                      "support": "SUPPORT_FREE_CANDIDATE_SLICER_CONFIRMATION_REQUIRED"}
    return {"printer": "Bambu A1", "bed_mm": [256, 256], "rows": rows,
            "all_fit": all(r["fits_bambu_a1_xy"] for r in rows.values()),
            "slicer_support_generation": "USER_CONFIRM_REQUIRED"}


def geometry_manifest() -> dict[str, Any]:
    return {"schema": "paddy_swarm.common_rover.h25a1.full_hardware_fixture.geometry.v0.9.4.4",
            "classification": CLASSIFICATION, "release": RELEASE, "cad_count": len(CAD),
            "step_count": len([p for p in CAD if p.endswith(".step")]),
            "stl_count": len([p for p in CAD if p.endswith(".stl")]),
            "interference": interference_report(), "printability": printability(),
            "protected_12t": PROTECTED, "external_geometry_delta_mm": 0.0,
            "full_12t_sprocket_stl_generated": False, "parents": parent_audit()}


def validation() -> dict[str, Any]:
    gates = {
        "FULL_HARDWARE_MEASUREMENTS": "COMPLETE", "V2_FIT_COUPON": "PRINT_READY_CANDIDATE",
        "V2_STATIC_FIXTURE": "PRINT_READY_CANDIDATE", "COLLAR_FINAL_POCKET": "USER_TEST_PENDING",
        "WASHER_FINAL_CLEARANCE": "USER_TEST_PENDING", "REACTION_FINAL_SLOT": "USER_TEST_PENDING",
        "STATIC_TORQUE_025": "PHYSICAL_PENDING", "STATIC_TORQUE_050": "PHYSICAL_PENDING",
        "STATIC_TORQUE_075": "PHYSICAL_PENDING", "24H_CREEP": "PHYSICAL_PENDING",
        "CENTRAL_HUB_LINK_WIDTH": DERIVED["link_side_status"], "FULL_SPROCKET": "HOLD",
        "POWERED_ROTATION": "NOT_APPROVED", "FIELD": "NOT_APPROVED",
    }
    missing = ["M4_THREAD_PITCH", "EXACT_3D_WASHER_STACK_ASYMMETRY", "ACTUAL_TORQUE_COEFFICIENT",
               "TRACK_LATERAL_DYNAMIC_MOVEMENT", "FULL_SPROCKET_COVER_FINAL_STACK"]
    return {"version": VERSION, "classification": CLASSIFICATION, "release": RELEASE, "gates": gates,
            "missing_nonblocking_measurements": missing, "fixture_inputs_complete": True,
            "physical_tests_complete": False, "full_sprocket_manufacturing": "HOLD",
            "powered_rotation_approved": False, "field_approved": False, "final_status": FINAL_STATUS}


def header(title: str) -> str:
    return f"# {title}\n\nVersion: `{VERSION}`  \nClassification: `{CLASSIFICATION}`  \nRelease: `{RELEASE}`  \nStatus: `{FINAL_STATUS}`\n"


def documents(valid: dict[str, Any]) -> dict[str, str]:
    h = header
    d: dict[str, str] = {}
    d["README.md"] = h("Common Rover H2.5-A1-2S Full-Hardware Fixture") + "\nMeasured collar, two 90° M4 screws, captive washers and heads are now represented in printable V2 fit and static fixtures. This lane does not generate or release a full 12T sprocket. CAD_PASS is not PHYSICAL_PASS.\n"
    d["PARENT_AUDIT.md"] = h("Parent audit") + "\n- v0.9.4.3: 66 files and protected hashes PASS; 19 artifacts byte reproducible; 34/34 tests PASS.\n- v0.9.4.2: 57 files and protected hashes PASS; standalone 11/11; 24/24 tests PASS.\n- Parent lanes and authority files are read-only.\n"
    d["SOURCE_TRACE.md"] = h("Source trace") + "\n" + "\n".join(f"- `{r['path']}` — `{r['sha256']}`" for r in source_trace()) + "\n"
    d["H25A1_FULL_HARDWARE_MEASUREMENTS.md"] = h("H2.5-A1 measured full hardware") + "\n|Item|Value|Class|\n|---|---:|---|\n|Collar OD/ID/W|15.9 / 10.1 / 3.0 mm|MEASURED USER_REPORTED|\n|M4 count/angle|2 / 90°|MEASURED USER_REPORTED|\n|Major OD/length/projection|3.8 / 4.0 / 1.0 mm|MEASURED USER_REPORTED|\n|Washer OD/stack|8.8 / 1.8 mm|MEASURED USER_REPORTED|\n|Head OD/height|6.8 / 2.8 mm|MEASURED USER_REPORTED|\n|Full radial/axial envelope|R20.0 / 8.8 mm|MEASURED USER_REPORTED|\n|Thread pitch|—|HOLD, non-blocking|\n"
    d["H25A1_FULL_HARDWARE_ENVELOPE.md"] = h("Full-hardware envelope") + "\nThe STEP uses the measured collar, shanks, washer discs and heads together plus the R20.0 × 8.8 envelope. The washer/head arrangement is a symmetric parametric representation of measured maxima; exact 3D asymmetry remains HOLD. R20.0 is clearance, never a torque-reaction gap.\n"
    d["H25A1_V2_FIT_COUPON_SPEC.md"] = h("V2 full-hardware fit coupons") + "\nWasher edge gauges W90/W92/W94 provide +0.2/+0.4/+0.6 mm diametral relief. The full assembly coupon compares R202/A90, R204/A92 and R206/A94. All pockets are top-open with a back push-through, so captive hardware need not be dismantled and cannot be trapped in a blind pocket. Final values require physical insertion/removal results.\n"
    d["H25A1_V2_STATIC_FIXTURE_SPEC.md"] = h("Static reaction fixture V2") + "\nOne 84×84×16 mm body uses an open R20.6×9.4 cavity, through 10.3 mm neutral shaft clearance, two full-width +X/+Y service channels, four hold-down holes and replaceable keys. Each key slides inward from the open outer side; actual hardware remains one assembly and no blind roof traps it. Neutral CAD checks include hardware↔body, hardware↔installed keys, key↔key and installed keys↔body. The displayed 10.3/20.6/9.4 values are fixture candidates, not full-sprocket release dimensions.\n"
    d["H25A1_REACTION_KEY_SPEC.md"] = h("Replaceable reaction key") + "\nR41/R42/R43 use a staged open edge: 9.2 mm washer clearance, 6.9 mm head reaction land, then 4.1/4.2/4.3 shank throat. The washer is not the primary torque path; the head land is the first intended local metal reaction surface. The 17.8 mm key width and 22.95 mm neutral center offset keep the installed orthogonal keys mutually clear. R42 is the neutral fixture candidate, `FINAL=false`. Keys are sacrificial, separately side-removable, require no washer removal, shaft machining or tooth/root access. The fixture plate provides four R42 pieces: operating pair plus 100% spare pair.\n"
    d["H25A1_STATIC_TORQUE_TEST_PLAN.md"] = h("Static torque test") + "\nMotor and crawler remain OFF. Assemble actual full hardware; mark shaft↔collar, collar↔key and key↔fixture witnesses. Apply 0.25 N·m, inspect; then 0.50, inspect; then 0.75, inspect. Stop immediately on slip, rotation, M4 back-out, washer digging, key crush/crack, whitening, body split, permanent play or failed removal.\n"
    d["H25A1_24H_CREEP_TEST.md"] = h("24-hour creep test") + "\nOnly after all three static levels PASS, retain the assembled/preloaded state for 24 h. Recheck witness marks, play, PETG deformation, screw looseness and service removal. Classification remains `PHYSICAL_CREEP_REQUIRED`; no long-term strength claim is made.\n"
    d["H25A1_12T_HUB_FEASIBILITY.md"] = h("12T central-hub feasibility") + "\nR20.0 to root R29.47 gives 9.47 mm theoretical radial residual. With conservative R20.6 and a separate 3.5 mm reaction allocation, the minimum PETG wall candidate is 5.37 mm (>3 mm target). Hardware-only centered axial margin is 17.6 mm/side. However link reference width 53.6 versus sprocket 44 gives 4.8 mm centered protrusion/side: BLOCKED until physical axial registration is validated. Full sprocket manufacturing remains HOLD.\n"
    d["H25A1_PROTECTED_GEOMETRY_AUDIT.md"] = h("Protected 12T geometry audit") + "\nProtected values remain 12T, phase15°, spacing30°, tip/root R33.07/R29.47, widths7.5/9.5, axial44, pitch diameter76.3943726841 and buried overlap4.0. External delta=0; radial tooth/root holes=0. H0 friction slip, H2.3 washer/root-link interference, and H2.4 0.499080075 mm³ access-bore removal remain inherited failures.\n"
    p = printability()
    d["PRINT_PLAN.md"] = h("Bambu A1 print plan") + "\nPlate 01 contains full-fit, W90/W92/W94 and R41/R42/R43 references. Plate 02 contains one fixture body and four identical R42 keys (pair + spare pair). All generated XY bounds are within 256×256 mm and modeled as support-free candidates. Confirm support generation in the slicer; print at 100% scale and do not auto-orient without checking labels/open pockets.\n\n" + "\n".join(f"- `{k}`: {v['bounds_mm']} mm" for k, v in p["rows"].items()) + "\n"
    d["PHYSICAL_RESULT_FORM.md"] = h("Physical result form") + "\n[COLLAR BODY] 16.0: ____  16.1: ____  16.2: ____\n\n[SHANK] 4.1: ____  4.2: ____  4.3: ____\n\n[WASHER RELIEF] 9.0: ____  9.2: ____  9.4: ____\n\n[V2 FULL HARDWARE]\ninsert YES/NO: ____  remove YES/NO: ____  washer rub NONE/LIGHT/HARD: ____  head rub NONE/LIGHT/HARD: ____  play NONE/SLIGHT/EXCESSIVE: ____\n\n[STATIC TORQUE]\n0.25 N·m PASS/FAIL: ____  0.50 N·m PASS/FAIL: ____  0.75 N·m PASS/FAIL: ____  24 h PASS/FAIL/HOLD: ____\n"
    d["MISSING_MEASUREMENTS.md"] = h("Remaining non-blocking measurements") + "\nV2 fixture generation inputs are COMPLETE. Remaining: M4 pitch, exact washer-stack 3D asymmetry, actual torque coefficient, track lateral dynamic movement, and final full-sprocket cover stack. These do not block printing V2 coupons/fixture but do block final product release where applicable.\n"
    d["DESIGN_GATE.md"] = h("Design gates") + "\n" + "\n".join(f"- `{k}`: `{v}`" for k, v in valid["gates"].items()) + "\n\nFull sprocket requires known collar/washer/reaction fits, V2 insert/remove PASS, 0.25/0.50/0.75 N·m PASS, acceptable 24 h creep, and unchanged protected geometry.\n"
    return d


def svg(title: str, body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 520"><style>text{{font-family:Arial;fill:#17212b}}.f{{fill:none;stroke:#334e68;stroke-width:2}}.g{{fill:#d9eafd;stroke:#245b8a}}.h{{fill:#fde2e2;stroke:#a33}}.u{{fill:#fff2b2;stroke:#a26f00;stroke-dasharray:8 5}}.a{{fill:none;stroke:#168aad;stroke-width:4;marker-end:url(#m)}}.d{{stroke:#667;stroke-dasharray:7 5}}</style><defs><marker id="m" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#168aad"/></marker></defs><rect width="100%" height="100%" fill="#fbfcfe"/><text x="24" y="32" font-size="22">{title}</text>{body}<text x="24" y="500" font-size="13">v0.9.4.4 · PHYSICAL TEST FIXTURE · HOLD · NO POWERED ROTATION</text></svg>'


def drawings() -> None:
    values = {
        "full_hardware_measurement_map.svg": '<circle class="g" cx="330" cy="270" r="80"/><path class="h" d="M410 245H610V295H410M305 190V70H355V190"/><circle class="u" cx="610" cy="270" r="55"/><text x="680" y="170">collar 15.9 / 10.1 / 3.0</text><text x="680" y="215">washer 8.8 × 1.8</text><text x="680" y="260">head 6.8 × 2.8</text><text x="680" y="305">R20.0 / axial 8.8</text>',
        "full_hardware_radial_section.svg": '<circle class="u" cx="350" cy="270" r="200"/><circle class="g" cx="350" cy="270" r="95"/><circle class="f" cx="350" cy="270" r="147"/><path class="d" d="M350 270H650"/><text x="665" y="235">hardware R20.0</text><text x="665" y="275">root R29.47</text><text x="665" y="315">theoretical 9.47</text>',
        "full_hardware_axial_section.svg": '<rect class="f" x="170" y="145" width="660" height="230"/><rect class="h" x="434" y="170" width="132" height="180"/><path class="d" d="M170 400H830"/><text x="210" y="430">44.0 total</text><text x="430" y="140">8.8 hardware</text><text x="215" y="115">17.6 theoretical each side</text>',
        "washer_relief_coupon_map.svg": '<rect class="g" x="120" y="160" width="760" height="200"/><path class="h" d="M250 160V280M500 160V280M750 160V280"/><text x="205" y="330">W90 (+0.2)</text><text x="455" y="330">W92 (+0.4)</text><text x="705" y="330">W94 (+0.6)</text>',
        "reaction_key_map.svg": '<path class="g" d="M120 150H350V350H120Z M120 225H260V275H120Z"/><path class="g" d="M390 150H620V350H390Z M390 225H530V275H390Z"/><path class="g" d="M660 150H890V350H660Z M660 225H800V275H660Z"/><text x="195" y="390">R41</text><text x="465" y="390">R42 neutral</text><text x="735" y="390">R43</text>',
        "static_fixture_v2_section.svg": '<rect class="g" x="190" y="120" width="620" height="300"/><path class="u" d="M350 120V320H650V120"/><circle class="h" cx="500" cy="270" r="70"/><path class="f" d="M470 120V420M530 120V420"/><text x="660" y="180">R20.6 × 9.4 open top</text><text x="660" y="230">shaft Ø10.3 through</text><text x="660" y="280">body 84×84×16</text>',
        "static_fixture_v2_exploded.svg": '<rect class="g" x="110" y="320" width="240" height="100"/><circle class="h" cx="500" cy="250" r="65"/><rect class="u" x="670" y="160" width="170" height="70"/><path class="a" d="M350 350L450 275M565 250L670 210"/><text x="100" y="455">fixture body</text><text x="440" y="335">full hardware</text><text x="690" y="145">R42 keys ×2</text>',
        "torque_load_path.svg": '<text x="80" y="120">φ10 shaft → M4×2 → metal collar → metal reaction features → replaceable key → PETG fixture → external reaction</text><path class="a" d="M80 170H900"/><text x="120" y="260">washer = clearance only</text><text x="120" y="310">cover bolts = not primary torque</text><text x="120" y="360">0.25 → 0.50 → 0.75 N·m; STOP ON FAIL</text>',
        "protected_12t_margin.svg": '<circle class="f" cx="340" cy="270" r="220"/><circle class="u" cx="340" cy="270" r="153"/><circle class="h" cx="340" cy="270" r="104"/><text x="620" y="180">root R29.47</text><text x="620" y="230">max service R20.6</text><text x="620" y="280">key allocation 3.5</text><text x="620" y="330">PETG wall 5.37 ≥ 3</text><text x="620" y="380">external delta 0 / holes 0</text>',
    }
    for name, body in values.items():
        write(LANE / "drawings" / name, svg(name.replace("_", " "), body))


def build() -> dict[str, Any]:
    before = repository_guard(False)
    for shape, rel in artifact_jobs():
        export(shape, LANE / rel)
    drawings()
    valid = validation()
    payloads = {"dimensions.json": dimensions(), "interfaces.json": interfaces(), "hardware.json": hardware(),
                "test_limits.json": test_limits(), "measurement_ledger.json": measurement_ledger(),
                "geometry_manifest.json": geometry_manifest(), "validation_report.json": valid}
    for name, value in payloads.items():
        write_json(LANE / name, value)
    for name, value in documents(valid).items():
        write(LANE / name, value)
    write(LANE / "MANIFEST.txt", "\n".join(PACKAGE_PATHS))
    write(LANE / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL}/{p}" for p in PACKAGE_PATHS))
    write(LANE / "BUILD_LOG.txt", f"BUILD PASS\nversion={VERSION}\nPython={sys.version.split()[0]}\nCadQuery={cq.__version__}\npreflight_untracked={before['untracked_total']}\noutside_untracked={before['outside_untracked']}\nmeasured_full_hardware=COMPLETE\nparent_v0943=CAD_PASS\nfull_sprocket=HOLD")
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
    missing = [p for p in PACKAGE_PATHS if not (LANE / p).is_file()]
    extras = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and
                    "__pycache__" not in p.parts and p.relative_to(LANE).as_posix() not in PACKAGE_PATHS)
    manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    hashes: dict[str, str] = {}
    for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        hashes[rel] = digest
    bad = [rel for rel, digest in hashes.items() if sha(LANE / rel) != digest]
    steps = {}
    for rel in [p for p in CAD if p.endswith(".step")]:
        shape = cq.importers.importStep(str(LANE / rel)).val()
        steps[rel] = {"valid": shape.isValid(), "volume_mm3": shape.Volume()}
    stls = {rel: stl_semantic(LANE / rel) for rel in CAD if rel.endswith(".stl")}
    dim, geom, valid = (json.loads((LANE / p).read_text(encoding="utf-8")) for p in
                        ("dimensions.json", "geometry_manifest.json", "validation_report.json"))
    checks = {
        "package": not missing and not extras and manifest == PACKAGE_PATHS,
        "hashes": not bad and set(hashes) == set(PACKAGE_PATHS) - {"SHA256SUMS.txt"},
        "cad_counts": len(steps) == 12 and len(stls) == 8,
        "step_reload": all(r["valid"] and r["volume_mm3"] > 0 for r in steps.values()),
        "measured": all(dim[k] == v for k, v in MEASURED.items()),
        "derived": dim["derived"]["hardware_to_root_theoretical_margin_mm"] == 9.47 and dim["derived"]["centered_axial_margin_each_side_mm"] == 17.6,
        "wall": dim["derived"]["minimum_remaining_petg_wall_mm"] == 5.37,
        "protected": dim["protected_12t"] == PROTECTED,
        "interference": geom["interference"]["all_zero"],
        "printability": geom["printability"]["all_fit"],
        "no_full_sprocket_stl": not geom["full_12t_sprocket_stl_generated"],
        "release": valid["full_sprocket_manufacturing"] == "HOLD" and not valid["powered_rotation_approved"] and not valid["field_approved"],
    }
    if not all(checks.values()):
        raise RuntimeError({"checks": checks, "missing": missing, "extras": extras, "bad": bad})
    return {"status": "CAD_PASS", "file_count": len(PACKAGE_PATHS), "step_count": len(steps),
            "stl_count": len(stls), "checks": checks, "bad_hashes": bad}


def standalone_rebuild() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ps_cr_v0944_a_") as a, tempfile.TemporaryDirectory(prefix="ps_cr_v0944_b_") as b:
        aa, bb = Path(a), Path(b)
        for shape, rel in artifact_jobs():
            export(shape, aa / rel)
        for shape, rel in artifact_jobs():
            export(shape, bb / rel)
        equal = {rel: sha(aa / rel) == sha(bb / rel) for rel in CAD}
        step_valid = {rel: cq.importers.importStep(str(aa / rel)).val().isValid() for rel in CAD if rel.endswith(".step")}
        stls = {rel: stl_semantic(aa / rel) for rel in CAD if rel.endswith(".stl")}
        checks = {"outputs": len(equal) == len(CAD), "byte_reproducible": all(equal.values()),
                  "step_reload": all(step_valid.values()), "stl_semantic": len(stls) == 8}
        if not all(checks.values()):
            raise RuntimeError({"checks": checks, "equal": equal})
        return {"status": "CAD_PASS", "artifact_count": len(equal), "step_count": len(step_valid),
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
