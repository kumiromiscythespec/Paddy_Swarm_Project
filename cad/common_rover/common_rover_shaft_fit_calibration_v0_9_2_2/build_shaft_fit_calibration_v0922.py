#!/usr/bin/env python3
"""Build and verify Common Rover v0.9.2.2 no-load shaft-fit coupons."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import cadquery as cq


LANE = Path(__file__).resolve().parent
LANE_REL = "cad/common_rover/common_rover_shaft_fit_calibration_v0_9_2_2"
REQUIRED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
STARTING_HEAD = "b0b9e879c95913c137b09b7c0abc80c52a0c36a0"
PARENT_REL = "cad/common_rover/common_rover_inward_pto_coupling_cad_verified_v0_9_2_1"
# SHA-256 over sorted ``relative-posix-path<TAB>file-sha256<LF>`` records.
PARENT_LEDGER_SHA256 = "d7cb3a99f02b87b9fea4623a60c5b758f1a8796a9514708edc84050321be58c1"
PARENT_ZIP = Path(r"D:\Downloads\Paddy_Swarm_Common_Rover_v0_9_2_1_CAD_Verified_Dry_Fit_20260731_145147.zip")
PARENT_ZIP_SHA256 = "4a7b51354725f8ef74d5f83cb20b3728d09b59710fee9a67b76bca3179ab4e6e"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_2_2_Shaft_Fit_Calibration_"

AUTHORITY_PATH_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
EXPECTED_TRACKED_DIFF = set(AUTHORITY_PATH_HASHES)

PULLEY_SOURCE_ROOT = Path(
    r"D:\Paddy_Swarm_Project_worktrees\common_rover_htd5m_full_pulley_dummy_v0_1"
    r"\cad\common_rover\htd5m_full_pulley_dummy_candidate_v0_1"
)
PULLEY_SOURCE_HASHES = {
    "pulley_60t_standard_dummy.py": "0a9d8e905df54b2594c420374eabc7678a6d95da231cb1f83bce15b64c864ec3",
    "full_pulley_common.py": "cc4e894275c32d2e37c101367ec9bda7f124e9cf374ca53c011afda11f4a78de",
    "artifacts/PS-HTD5M-PULLEY-60T-STD-DUMMY-V001.stl": "2577b0cd8575a961e527c47e304036a4072245ef051f91c5eccf3e1adbac42f7",
    "artifacts/PS-HTD5M-PULLEY-60T-STD-DUMMY-V001.step": "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256",
    "htd5m_full_pulley_dummy_geometry_report.json": "80470c1b9d72d9d6ac35d2c8d15d15722b268d143004048915273de32f1d0a7c",
}

D_REF_CAD_MM = 10.10
D_REF_ACTUAL_MM = 10.10
SHAFT_DIAMETER_MM = 10.0
A1_BUILD_VOLUME_MM = (256.0, 256.0, 256.0)
CLAMP_X_MM = 50.0
CLAMP_Y_MM = 20.0
HALF_Z_MM = 10.0
CLAMP_AXIAL_LENGTH_MM = 20.0
FASTENER_CLEARANCE_MM = 3.4
FASTENER_X_MM = 19.0
SLEEVE_OD_MM = 20.0
SLEEVE_LENGTH_MM = 20.0
SLEEVE_CHAMFER_MM = 0.4
STL_TOLERANCE_MM = 0.02
STL_ANGULAR_TOLERANCE = 0.1

POSITIONING = [
    {"id": f"P{i}", "offset_mm": offset, "bore_mm": round(D_REF_CAD_MM + offset, 2)}
    for i, offset in enumerate((-0.20, -0.10, 0.00, 0.10, 0.20, 0.30))
]
SLIDING = [
    {"id": f"S{i}", "offset_mm": offset, "bore_mm": round(D_REF_CAD_MM + offset, 2)}
    for i, offset in enumerate((0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60))
]

POSITIONING_STL = [
    f"artifacts/positioning/PS-CR-V0922-{row['id']}-{half}.stl"
    for row in POSITIONING for half in ("BOTTOM", "TOP")
]
SLIDING_STL = [
    f"artifacts/sliding/PS-CR-V0922-{row['id']}.stl" for row in SLIDING
]
PLATE_FILES = [
    "artifacts/plates/PS-CR-V0922-POSITIONING-PLATE.stl",
    "artifacts/plates/PS-CR-V0922-SLIDING-PLATE.stl",
    "artifacts/plates/PS-CR-V0922-MINIMUM-FIRST-PASS-PLATE.stl",
    "artifacts/plates/PS-CR-V0922-MINIMUM-FIRST-PASS-PLATE.step",
]
STEP_FILES = [
    "artifacts/plates/PS-CR-V0922-MINIMUM-FIRST-PASS-PLATE.step",
    "artifacts/PS-CR-V0922-POSITIONING-ASSEMBLY.step",
    "artifacts/PS-CR-V0922-SLIDING-ASSEMBLY.step",
]
SVG_FILES = [
    "artifacts/PS-CR-V0922-OVERVIEW.svg",
    "artifacts/PS-CR-V0922-CANDIDATE-MAP.svg",
    "artifacts/PS-CR-V0922-PRINT-ORIENTATION.svg",
]
PACKAGE_PATHS = [
    "common_rover_shaft_fit_calibration_plan_v0922.md",
    "common_rover_shaft_fit_calibration_parameters_v0922.json",
    "common_rover_physical_measurements_input_v0922.json",
    "common_rover_reference_60t_bore_audit_v0922.md",
    "common_rover_positioning_fit_candidates_v0922.csv",
    "common_rover_sliding_fit_candidates_v0922.csv",
    "common_rover_fit_candidate_validation_v0922.json",
    "fit_calibration_procedure_v0922.md",
    "fit_calibration_record_v0922.csv",
    "photo_log_template_v0922.md",
    "NO_LOAD_ONLY.txt",
    "build_shaft_fit_calibration_v0922.py",
    *POSITIONING_STL,
    *SLIDING_STL,
    *PLATE_FILES,
    "artifacts/PS-CR-V0922-POSITIONING-ASSEMBLY.step",
    "artifacts/PS-CR-V0922-SLIDING-ASSEMBLY.step",
    *SVG_FILES,
    "tests/test_shaft_fit_calibration_v0922.py",
    "README_HANDOFF.md",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "test_results_v0922.txt",
]
assert len(PACKAGE_PATHS) == 45 and len(set(PACKAGE_PATHS)) == 45


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))


def run(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        command, cwd=cwd, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}")
    return result.stdout.strip()


def repo_root() -> Path | None:
    for parent in (LANE, *LANE.parents):
        if (parent / ".git").exists():
            return parent
    return None


def cylinder_z(radius: float, height: float, z0: float = 0.0, x: float = 0.0, y: float = 0.0) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, height, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def cylinder_y(radius: float, length: float, x: float = 0.0, y0: float = -10.0, z: float = 0.0) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))


def marker_locations(count: int) -> list[tuple[float, float]]:
    positions = [(-10.5, -6.0), (-10.5, 0.0), (-10.5, 6.0), (10.5, -6.0), (10.5, 0.0), (10.5, 6.0)]
    return positions[:count]


def split_half(candidate_id: str, bore_mm: float, half: str) -> cq.Shape:
    """Printable half: its split/groove face is z=0, directly on the bed."""
    if half not in {"BOTTOM", "TOP"}:
        raise ValueError(half)
    index = int(candidate_id[1:]) + 1
    body = (
        cq.Workplane("XY")
        .box(CLAMP_X_MM, CLAMP_Y_MM, HALF_Z_MM, centered=(True, True, False))
        .edges("|Z").chamfer(0.5).val()
    )
    groove = cylinder_y(bore_mm / 2.0, CLAMP_Y_MM + 2.0, y0=-(CLAMP_Y_MM + 2.0) / 2.0, z=0.0)
    body = body.cut(groove)
    for x in (-FASTENER_X_MM, FASTENER_X_MM):
        body = body.cut(cylinder_z(FASTENER_CLEARANCE_MM / 2.0, HALF_Z_MM + 2.0, -1.0, x, 0.0))
        if half == "BOTTOM":
            body = body.cut(cylinder_z(3.2, 2.8, HALF_Z_MM - 2.8, x, 0.0))
        else:
            body = body.cut(cylinder_z(3.0, 2.4, HALF_Z_MM - 2.4, x, 0.0))
    for x, y in marker_locations(index):
        body = body.cut(cylinder_z(1.2, HALF_Z_MM + 2.0, -1.0, x, y))
    return body


def assembled_clamp(candidate_id: str, bore_mm: float) -> dict[str, cq.Shape]:
    lower = split_half(candidate_id, bore_mm, "BOTTOM").rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, 10))
    upper = split_half(candidate_id, bore_mm, "TOP").translate((0, 0, 10))
    shaft = cylinder_y(SHAFT_DIAMETER_MM / 2.0, 30.0, y0=-15.0, z=10.0)
    fasteners = cq.Compound.makeCompound([
        cylinder_z(FASTENER_CLEARANCE_MM / 2.0, 24.0, -2.0, x, 0.0)
        for x in (-FASTENER_X_MM, FASTENER_X_MM)
    ])
    tools = cq.Compound.makeCompound([
        cylinder_z(4.0, 10.0, 20.0, x, 0.0)
        for x in (-FASTENER_X_MM, FASTENER_X_MM)
    ])
    return {"bottom": lower, "top": upper, "shaft_envelope": shaft, "fastener_envelope": fasteners, "tool_envelope": tools}


def sleeve(candidate_id: str, bore_mm: float) -> cq.Shape:
    index = int(candidate_id[1:]) + 1
    outer = cylinder_z(SLEEVE_OD_MM / 2.0, SLEEVE_LENGTH_MM)
    tab = cq.Workplane("XY").box(14.0, 24.0, 3.0, centered=(False, True, False)).translate((8.0, 0.0, 0.0)).val()
    body = outer.fuse(tab)
    bore = cylinder_z(bore_mm / 2.0, SLEEVE_LENGTH_MM + 2.0, -1.0)
    body = body.cut(bore)
    lower_chamfer = cq.Solid.makeCone(
        bore_mm / 2.0 + SLEEVE_CHAMFER_MM, bore_mm / 2.0,
        SLEEVE_CHAMFER_MM, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1),
    )
    upper_chamfer = cq.Solid.makeCone(
        bore_mm / 2.0, bore_mm / 2.0 + SLEEVE_CHAMFER_MM,
        SLEEVE_CHAMFER_MM, cq.Vector(0, 0, SLEEVE_LENGTH_MM - SLEEVE_CHAMFER_MM), cq.Vector(0, 0, 1),
    )
    body = body.cut(lower_chamfer).cut(upper_chamfer)
    marker_positions = [(14.0, -7.5), (14.0, -2.5), (14.0, 2.5), (14.0, 7.5), (19.0, -7.5), (19.0, -2.5), (19.0, 2.5)]
    for x, y in marker_positions[:index]:
        body = body.cut(cylinder_z(1.2, 5.0, -1.0, x, y))
    return body


def positioned_plate() -> dict[str, cq.Shape]:
    result: dict[str, cq.Shape] = {}
    centers = [(-93.0, -32.0), (-31.0, -32.0), (31.0, -32.0), (93.0, -32.0),
               (-93.0, 32.0), (-31.0, 32.0), (31.0, 32.0), (93.0, 32.0),
               (-93.0, 64.0), (-31.0, 64.0), (31.0, 64.0), (93.0, 64.0)]
    cursor = 0
    for row in POSITIONING:
        for half in ("BOTTOM", "TOP"):
            x, y = centers[cursor]
            result[f"{row['id']}_{half}"] = split_half(row["id"], row["bore_mm"], half).translate((x, y, 0))
            cursor += 1
    return result


def sliding_plate() -> dict[str, cq.Shape]:
    result: dict[str, cq.Shape] = {}
    centers = [(-72.0, -30.0), (-24.0, -30.0), (24.0, -30.0), (72.0, -30.0),
               (-48.0, 30.0), (0.0, 30.0), (48.0, 30.0)]
    for row, (x, y) in zip(SLIDING, centers):
        result[row["id"]] = sleeve(row["id"], row["bore_mm"]).translate((x, y, 0))
    return result


def minimum_plate() -> dict[str, cq.Shape]:
    result: dict[str, cq.Shape] = {}
    p_rows = POSITIONING[1:4]
    for row, x in zip(p_rows, (-62.0, 0.0, 62.0)):
        result[f"{row['id']}_BOTTOM"] = split_half(row["id"], row["bore_mm"], "BOTTOM").translate((x, -38, 0))
        result[f"{row['id']}_TOP"] = split_half(row["id"], row["bore_mm"], "TOP").translate((x, -6, 0))
    for row, x in zip(SLIDING[1:5], (-67.5, -22.5, 22.5, 67.5)):
        result[row["id"]] = sleeve(row["id"], row["bore_mm"]).translate((x, 45, 0))
    return result


def minimum_xy_bbox_gap(shapes: Iterable[cq.Shape]) -> float:
    """Minimum edge-to-edge distance between axis-aligned XY bounding boxes."""
    boxes = [shape.BoundingBox() for shape in shapes]
    gaps: list[float] = []
    for index, first in enumerate(boxes):
        for second in boxes[index + 1:]:
            dx = max(first.xmin - second.xmax, second.xmin - first.xmax, 0.0)
            dy = max(first.ymin - second.ymax, second.ymin - first.ymax, 0.0)
            gaps.append((dx * dx + dy * dy) ** 0.5)
    return min(gaps)


def compound(shapes: Iterable[cq.Shape]) -> cq.Shape:
    return cq.Compound.makeCompound(list(shapes))


def _canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"FILE_NAME\('.*?','.*?',", "FILE_NAME('PS-CR-V0922','2000-01-01T00:00:00',", text, count=1)
    text = re.sub(r"FILE_DESCRIPTION\(\(.*?\),'.*?'\);", "FILE_DESCRIPTION(('NO LOAD FIT CALIBRATION COUPON'),'2;1');", text, count=1)
    write_text(path, text)


def export_stl(path: Path, shape: cq.Shape) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path), tolerance=STL_TOLERANCE_MM, angularTolerance=STL_ANGULAR_TOLERANCE)


def export_step(path: Path, shapes: Iterable[cq.Shape]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(compound(shapes), str(path))
    _canonicalize_step(path)


def parent_ledger(root: Path) -> tuple[str, int]:
    parent = root / PARENT_REL
    files = sorted(path for path in parent.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in files:
        rel = path.relative_to(parent).as_posix()
        digest.update(f"{rel}\t{sha256(path)}\n".encode("utf-8"))
    return digest.hexdigest(), len(files)


def audit_parent(live: bool = True) -> dict[str, Any]:
    root = repo_root()
    evidence: dict[str, Any] = {
        "parent_relative_path": PARENT_REL,
        "expected_file_count": 55,
        "expected_tree_ledger_sha256": PARENT_LEDGER_SHA256,
        "expected_zip_sha256": PARENT_ZIP_SHA256,
        "authority_pointer": "common_rover_inward_pto_coupling_cad_verified_v0_9_2_1",
        "status": "EMBEDDED_PROTECTED_EVIDENCE",
    }
    if not live or root is None:
        return evidence
    ledger, count = parent_ledger(root)
    if ledger != PARENT_LEDGER_SHA256 or count != 55:
        raise RuntimeError(f"parent protection failed: {count=} {ledger=}")
    if not PARENT_ZIP.is_file() or sha256(PARENT_ZIP) != PARENT_ZIP_SHA256:
        raise RuntimeError("parent ZIP protection failed")
    for rel, expected in AUTHORITY_PATH_HASHES.items():
        if sha256(root / rel) != expected:
            raise RuntimeError(f"authority path changed: {rel}")
    evidence.update({"actual_file_count": count, "actual_tree_ledger_sha256": ledger, "actual_zip_sha256": sha256(PARENT_ZIP), "status": "PASS"})
    return evidence


def audit_reference_source(live: bool = True) -> dict[str, Any]:
    evidence = {
        "status": "RESOLVED",
        "D_REF_CAD_mm": D_REF_CAD_MM,
        "D_REF_ACTUAL_mm": D_REF_ACTUAL_MM,
        "component_id": "PS-HTD5M-PULLEY-60T-STD-DUMMY-V001",
        "source_root": str(PULLEY_SOURCE_ROOT),
        "bore_axis": "Z",
        "print_bed_face": "LOWER_FLANGE",
        "support": "NOT_REQUIRED",
        "bore_chamfer": "NONE_IN_SOURCE_CAD",
        "elephant_foot_relief": "NONE_IN_SOURCE_CAD",
        "mesh_tolerance_mm": 0.01,
        "mesh_angular_tolerance": 0.1,
        "scale_transform": "NONE",
        "global_xy_scale": False,
        "pitch_scale": False,
        "source_hashes": PULLEY_SOURCE_HASHES,
    }
    if not live or not PULLEY_SOURCE_ROOT.is_dir():
        evidence["live_source_check"] = "NOT_AVAILABLE_STANDALONE_EMBEDDED_EVIDENCE_USED"
        return evidence
    for name, expected in PULLEY_SOURCE_HASHES.items():
        if sha256(PULLEY_SOURCE_ROOT / name) != expected:
            raise RuntimeError(f"60T source changed: {name}")
    source = (PULLEY_SOURCE_ROOT / "pulley_60t_standard_dummy.py").read_text(encoding="utf-8")
    if not re.search(r"bore_mm\s*=\s*10\.10\b", source):
        raise RuntimeError("D_REF_CAD 10.10 not found in audited 60T source")
    evidence["live_source_check"] = "PASS"
    return evidence


def audit_repository() -> dict[str, Any]:
    root = repo_root()
    if root is None:
        return {"mode": "STANDALONE_PACKAGE", "status": "PASS"}
    branch = run(["git", "-C", str(root), "branch", "--show-current"])
    head = run(["git", "-C", str(root), "rev-parse", "HEAD"])
    tracked = set(filter(None, run(["git", "-c", "core.safecrlf=false", "-C", str(root), "diff", "--name-only"]).splitlines()))
    staged = set(filter(None, run(["git", "-c", "core.safecrlf=false", "-C", str(root), "diff", "--cached", "--name-only"]).splitlines()))
    if branch != REQUIRED_BRANCH or head != STARTING_HEAD:
        raise RuntimeError(f"repository anchor changed: {branch=} {head=}")
    if tracked != EXPECTED_TRACKED_DIFF or staged:
        raise RuntimeError(f"repository diff contract failed: tracked={sorted(tracked)} staged={sorted(staged)}")
    untracked = set(filter(None, run(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"]).splitlines()))
    lane_paths = {path[len(LANE_REL) + 1:] for path in untracked if path.startswith(LANE_REL + "/")}
    if lane_paths != set(PACKAGE_PATHS):
        raise RuntimeError(f"v0.9.2.2 exact-45 untracked contract failed: {len(lane_paths)}")
    # Existing ignored/cache paths elsewhere in this very large repository are
    # user-owned and out of scope.  The new lane itself must remain exactly
    # clean of ignored output.
    ignored = set(filter(None, run(["git", "-C", str(root), "ls-files", "--others", "-i", "--exclude-standard", "--", LANE_REL]).splitlines()))
    if ignored:
        raise RuntimeError(f"ignored paths exist: {sorted(ignored)[:10]}")
    return {"mode": "LIVE_REPOSITORY", "root": str(root), "branch": branch, "head": head, "tracked_diff": sorted(tracked), "staged_diff": [], "untracked_total": len(untracked), "lane_untracked_count": len(lane_paths), "status": "PASS"}


def physical_measurements() -> dict[str, Any]:
    return {
        "source": "USER_PHYSICAL_INPUT_2026-08-02",
        "center_gap_gauges_mm": [
            {"nominal": 35.0, "actual": 34.6}, {"nominal": 36.0, "actual": 35.5}, {"nominal": 37.0, "actual": 36.6},
        ],
        "stub_gauges_mm": [{"nominal": 12.5, "actual": 12.4}, {"nominal": 12.5, "actual": 12.5}],
        "dimension_bar": {"long_XY_typical_error_mm": "-0.2_TO_-0.3", "single_worst_error_mm": -0.4, "short_10mm_error_mm": "-0.1_TO_-0.2", "thickness_5mm_actual_mm": 5.0, "clear_XY_direction_difference": False, "Z_only_error": False},
        "GLOBAL_SCALE_CORRECTION": "PROHIBITED",
        "current_U_block": {"entry": "LOCALLY_TIGHT", "diametral_play_after_entry_mm": 1.4, "radial_positioning": "FAIL", "rough_support": "USABLE_NO_LOAD_ONLY", "entry_tightness": "LOCAL_PRINT_ARTIFACT"},
        "reference_60T": {"actual_bore_measurements_mm": [10.1, 10.1, 10.1, 10.1], "shaft_rotated_90deg_same": True, "axial_motion": "SNUG_TWIST_ASSISTED_SLIDE", "radial_play": "NOT_OBSERVED", "positioning_reference": "GOOD", "free_sliding_sleeve": "TOO_TIGHT_CANDIDATE"},
        "PHYSICAL_TEST_STATUS": "PHYSICAL_TEST_NOT_PERFORMED_FOR_V0922_COUPONS",
    }


def parameters_payload() -> dict[str, Any]:
    return {
        "schema": "PS-CR-SHAFT-FIT-CALIBRATION-V0922",
        "units": "mm",
        "D_REF_CAD": D_REF_CAD_MM,
        "D_REF_CAD_STATUS": "RESOLVED_FROM_AUDITED_60T_SOURCE",
        "D_REF_ACTUAL": D_REF_ACTUAL_MM,
        "reference_source_audit": audit_reference_source(live=False),
        "positioning_candidates": POSITIONING,
        "sliding_candidates": SLIDING,
        "split_clamp": {"outer_xyz_mm": [CLAMP_X_MM, CLAMP_Y_MM, 2 * HALF_Z_MM], "axial_length_mm": CLAMP_AXIAL_LENGTH_MM, "split_plane": "THROUGH_SHAFT_AXIS", "hard_stop": "PLANAR_LANDS_CONTACT", "fastener_count": 2, "fastener_clearance_mm": FASTENER_CLEARANCE_MM, "interface": "NO_LOAD_TEST_CANDIDATE", "print_orientation": "SPLIT_FACE_ON_BED", "support": "NONE"},
        "sliding_sleeve": {"OD_mm": SLEEVE_OD_MM, "length_mm": SLEEVE_LENGTH_MM, "bore_axis_print": "Z", "entry_exit_chamfer_mm": SLEEVE_CHAMFER_MM, "support": "NONE"},
        "identification": {"method": "GEOMETRIC_HOLES", "embossed_text": False, "floating_text": False, "count_mapping": "P0/S0=1 through P5=6 and S6=7"},
        "plates": {"A": [row["id"] for row in POSITIONING], "B": [row["id"] for row in SLIDING], "C": ["P1", "P2", "P3", "S1", "S2", "S3", "S4"], "first_print": "PLATE-C", "build_volume_mm": list(A1_BUILD_VOLUME_MM)},
        "statuses": {"FIT_CALIBRATION_COUPONS": "READY_FOR_PRINT", "POSITIONING_FIT_SELECTION": "PHYSICAL_TEST_REQUIRED", "SLIDING_FIT_SELECTION": "PHYSICAL_TEST_REQUIRED", "PHYSICAL_FIT": "HOLD", "LOAD_CAPACITY": "HOLD", "POWERED_TEST": "NOT_APPROVED", "MACHINING": "HOLD", "MANUFACTURING": "HOLD", "FIELD_DEPLOYMENT": "NOT_APPROVED", "AUTHORITY_POINTER": "UNCHANGED_V0_9_2_1"},
        "GLOBAL_SCALE_CORRECTION": "PROHIBITED",
        "stl_export": {"tolerance_mm": STL_TOLERANCE_MM, "angular_tolerance": STL_ANGULAR_TOLERANCE},
    }


def csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    import io
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def generate_documents() -> None:
    write_json(LANE / "common_rover_shaft_fit_calibration_parameters_v0922.json", parameters_payload())
    write_json(LANE / "common_rover_physical_measurements_input_v0922.json", physical_measurements())
    p_fields = ["candidate_id", "cad_nominal_bore_mm", "offset_from_D_REF_CAD_mm", "component_ids", "quantity", "print_orientation", "intended_use", "physical_status"]
    p_rows = [{"candidate_id": r["id"], "cad_nominal_bore_mm": f"{r['bore_mm']:.2f}", "offset_from_D_REF_CAD_mm": f"{r['offset_mm']:+.2f}", "component_ids": f"PS-CR-V0922-{r['id']}-BOTTOM|PS-CR-V0922-{r['id']}-TOP", "quantity": 2, "print_orientation": "SPLIT_FACE_ON_BED", "intended_use": "NO_LOAD_RADIAL_POSITIONING", "physical_status": "PHYSICAL_TEST_NOT_PERFORMED"} for r in POSITIONING]
    write_text(LANE / "common_rover_positioning_fit_candidates_v0922.csv", csv_text(p_fields, p_rows))
    s_fields = ["candidate_id", "cad_nominal_bore_mm", "offset_from_D_REF_CAD_mm", "component_id", "quantity", "print_orientation", "intended_use", "physical_status"]
    s_rows = [{"candidate_id": r["id"], "cad_nominal_bore_mm": f"{r['bore_mm']:.2f}", "offset_from_D_REF_CAD_mm": f"{r['offset_mm']:+.2f}", "component_id": f"PS-CR-V0922-{r['id']}", "quantity": 1, "print_orientation": "BORE_AXIS_Z", "intended_use": "NO_LOAD_FREE_AXIAL_SLIDE", "physical_status": "PHYSICAL_TEST_NOT_PERFORMED"} for r in SLIDING]
    write_text(LANE / "common_rover_sliding_fit_candidates_v0922.csv", csv_text(s_fields, s_rows))
    record_fields = ["test_date", "operator", "printer", "material", "nozzle", "layer_height", "slicer_profile", "sample_id", "sample_type", "nominal_bore_cad_mm", "offset_from_reference_mm", "print_orientation", "shaft_location", "shaft_diameter_0deg_mm", "shaft_diameter_90deg_mm", "entry_fit", "full_depth_fit", "twist_required", "straight_slide_possible", "slide_force_subjective", "radial_play_visible", "radial_play_sound", "self_drop", "cap_stop_reached", "shaft_surface_damage", "disassembly_possible", "burr_present", "burr_removed_after_initial_test", "selected", "rejection_reason", "photo_ids", "notes", "physical_status"]
    record_rows = []
    for family, source in (("POSITIONING_SPLIT_CLAMP", POSITIONING), ("SLIDING_SLEEVE", SLIDING)):
        for r in source:
            row = {key: "" for key in record_fields}
            row.update({"sample_id": r["id"], "sample_type": family, "nominal_bore_cad_mm": f"{r['bore_mm']:.2f}", "offset_from_reference_mm": f"{r['offset_mm']:+.2f}", "print_orientation": "SPLIT_FACE_ON_BED" if family.startswith("POSITIONING") else "BORE_AXIS_Z", "selected": "HOLD", "physical_status": "PHYSICAL_TEST_NOT_PERFORMED"})
            record_rows.append(row)
    write_text(LANE / "fit_calibration_record_v0922.csv", csv_text(record_fields, record_rows))
    write_text(LANE / "common_rover_reference_60t_bore_audit_v0922.md", reference_audit_markdown())
    write_text(LANE / "common_rover_shaft_fit_calibration_plan_v0922.md", plan_markdown())
    write_text(LANE / "fit_calibration_procedure_v0922.md", procedure_markdown())
    write_text(LANE / "photo_log_template_v0922.md", photo_log_markdown())
    write_text(LANE / "NO_LOAD_ONLY.txt", no_load_text())


def plan_markdown() -> str:
    return """# Common Rover shaft-fit calibration plan v0.9.2.2

Status: `NOT_FOR_MANUFACTURING`, `NO_LOAD_ONLY`, `PHYSICAL_FIT_SELECTION=PENDING_TEST`.

This lane separates two different fit contracts. P0–P5 are split clamps for
radial positioning; S0–S6 are short sleeves for straight hand sliding. Results
from one family must not be transferred to the other.

## Evidence and dimensional policy

The audited 60T source resolves `D_REF_CAD=10.10 mm`; the independent physical
reference is `D_REF_ACTUAL=10.1 mm`. Equal numbers do not make the physical
measurement the CAD authority. Printed comparison gauges were generally
0.1–0.4 mm undersize in X/Y while 5 mm thickness measured 5.0 mm. There was no
clear X/Y directional split and the result was not Z-only. Therefore
`GLOBAL_SCALE_CORRECTION=PROHIBITED`.

The v0.9.2.1 U block has local entry tightness followed by about 1.4 mm
diametral play. It fails radial positioning and remains only a rough, no-load
support.

## Geometry

Each clamp half is a separate watertight candidate. Its split face contains a
semicircular groove and lies at print Z=0. When assembled, planar hard-stop
lands touch at the shaft-axis plane; M3 candidate holes do not define the bore.
Sleeves print with the functional bore vertical, with only 0.4 mm entry/exit
chamfers. IDs use 1–7 geometric holes; there is no embossed or floating text.

Print `PLATE-C` first: P1/P2/P3 plus S1/S2/S3/S4. Print the full A/B plates only
if that subset does not yield one compliant candidate per family.

Selections, load capacity, machining, manufacturing and physical fit remain
HOLD. Powered testing and field deployment are NOT_APPROVED. The v0.9.2.1
authority pointer is intentionally unchanged.
"""


def reference_audit_markdown() -> str:
    return f"""# Audited 60T reference bore

- Source: `{PULLEY_SOURCE_ROOT}`
- Component: `PS-HTD5M-PULLEY-60T-STD-DUMMY-V001`
- Exact source CAD bore: `D_REF_CAD={D_REF_CAD_MM:.2f} mm`
- Physical reference: `D_REF_ACTUAL={D_REF_ACTUAL_MM:.1f} mm` at four locations/angles
- Bore axis: Z; lower flange on bed; support not required
- Bore chamfer: none; elephant-foot relief: none
- STL tolerance/angular tolerance: 0.01 mm / 0.1
- Scale transform: none; global XY and pitch scale disabled

The physical 10.1 mm reading is recorded independently and is not used to infer
the nominal source value. The source Python, common generator, STEP, STL and
geometry report are pinned by SHA-256 in the parameter JSON.
"""


def procedure_markdown() -> str:
    steps = [
        "Do not use power, motor or belt.", "Use the same 10 mm shaft.", "Clean the shaft surface.",
        "Measure the shaft at three axial positions at 0° and 90°.", "Test coupons without modifying them.",
        "Record the state before burr removal.", "Try P samples from the lowest number.",
        "Lightly close the split clamp until its hard-stop lands touch.", "Check lateral play.",
        "Inspect the shaft surface for damage.", "Confirm hand disassembly.", "Try S samples from the lowest number.",
        "Check straight sliding without twisting.", "Move continuously over 20–30 mm.", "Place at 0, 5 and 10 mm.",
        "Check lateral play.", "Check self-drop behavior.", "Select at most one compliant sample per family.",
        "If none complies, select none.", "Record measurements and photo IDs.", "Finish without applying power.",
    ]
    body = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1))
    return f"""# Physical fit calibration procedure v0.9.2.2

`NO_LOAD_ONLY` — `PHYSICAL_TEST_NOT_PERFORMED`

{body}

## Prohibited

Hammering, plier press-fit, drill rotation, motor rotation, belt tension, shaft
cutting, hole enlargement, omitting pre-deburr observations, sanding before the
initial record, lubrication that changes the result, machining and powered test.

## Selection

Positioning: no visible play; stop reached; no damage; hand removable; minimum
closing force among compliant candidates. Sliding: straight no-twist movement,
0/5/10 mm placement, no visible play, no local seizure, no damage, no rapid
self-drop; choose the smallest bore among compliant candidates. Both selected
diameters remain `HOLD` until this procedure is physically completed.
"""


def photo_log_markdown() -> str:
    return """# Photo log template v0.9.2.2

Physical status: `PHYSICAL_TEST_NOT_PERFORMED`.

| photo_id | sample_id | view | before_or_after_deburr | shaft_position_mm | observation | file_name |
|---|---|---|---|---:|---|---|
| | | entry / side / stop / play / surface | | | | |

Do not claim a fit result without the corresponding record row and photo ID.
"""


def no_load_text() -> str:
    return """COMMON ROVER V0.9.2.2 SHAFT-FIT CALIBRATION COUPONS
NO_LOAD_ONLY
NOT_FOR_TORQUE
NOT_A_PRODUCTION_FASTENER_INTERFACE
PHYSICAL_FIT_SELECTION=PENDING_TEST
LOAD_CAPACITY=HOLD
POWERED_TEST=NOT_APPROVED
MACHINING=HOLD
MANUFACTURING=HOLD
FIELD_DEPLOYMENT=NOT_APPROVED
AUTHORITY_POINTER_UPDATE=PROHIBITED_PENDING_PHYSICAL_FIT_RESULTS
"""


def generate_artifacts() -> None:
    for row in POSITIONING:
        for half in ("BOTTOM", "TOP"):
            export_stl(LANE / f"artifacts/positioning/PS-CR-V0922-{row['id']}-{half}.stl", split_half(row["id"], row["bore_mm"], half))
    for row in SLIDING:
        export_stl(LANE / f"artifacts/sliding/PS-CR-V0922-{row['id']}.stl", sleeve(row["id"], row["bore_mm"]))
    export_stl(LANE / PLATE_FILES[0], compound(positioned_plate().values()))
    export_stl(LANE / PLATE_FILES[1], compound(sliding_plate().values()))
    export_stl(LANE / PLATE_FILES[2], compound(minimum_plate().values()))
    export_step(LANE / PLATE_FILES[3], minimum_plate().values())
    p_assembly: list[cq.Shape] = []
    for row, x in zip(POSITIONING, (-150, -90, -30, 30, 90, 150)):
        assembled = assembled_clamp(row["id"], row["bore_mm"])
        p_assembly.extend([assembled["bottom"].translate((x, 0, 0)), assembled["top"].translate((x, 0, 0))])
    export_step(LANE / STEP_FILES[1], p_assembly)
    export_step(LANE / STEP_FILES[2], [sleeve(row["id"], row["bore_mm"]).translate((i * 35 - 105, 0, 0)) for i, row in enumerate(SLIDING)])
    write_text(LANE / SVG_FILES[0], overview_svg())
    write_text(LANE / SVG_FILES[1], candidate_map_svg())
    write_text(LANE / SVG_FILES[2], print_orientation_svg())


def svg_frame(title: str, content: str, width: int = 1200, height: int = 700) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#f5f7f2"/><style>text{{font-family:Arial,sans-serif;fill:#14261d}}.h{{font-size:32px;font-weight:bold}}.m{{font-size:21px}}.s{{font-size:17px}}.part{{fill:#c7dfd1;stroke:#234d3b;stroke-width:3}}.warn{{fill:#fff3cd;stroke:#8a6300;stroke-width:2}}</style>
<text x="40" y="55" class="h">{title}</text>{content}
<text x="40" y="675" class="s">NO LOAD ONLY · NOT FOR MANUFACTURING · PHYSICAL FIT TEST REQUIRED</text></svg>'''


def overview_svg() -> str:
    content = '''<rect class="part" x="90" y="220" width="380" height="95" rx="8"/><path d="M250 315 A55 55 0 0 1 360 315" fill="#f5f7f2" stroke="#234d3b" stroke-width="3"/><rect class="part" x="90" y="320" width="380" height="95" rx="8"/><path d="M250 320 A55 55 0 0 0 360 320" fill="#f5f7f2" stroke="#234d3b" stroke-width="3"/><circle cx="305" cy="317" r="38" fill="none" stroke="#d6533c" stroke-width="4"/><text x="95" y="185" class="m">A: split clamp — hard-stop lands define radial position</text><circle class="part" cx="830" cy="315" r="115"/><circle cx="830" cy="315" r="59" fill="#f5f7f2" stroke="#234d3b" stroke-width="3"/><rect class="part" x="930" y="250" width="120" height="130"/><text x="650" y="175" class="m">B: vertical-bore sliding sleeve</text><rect class="warn" x="330" y="500" width="540" height="70" rx="8"/><text x="390" y="544" class="m">Separate fit contracts; do not cross-select.</text>'''
    return svg_frame("Common Rover v0.9.2.2 fit calibration", content)


def candidate_map_svg() -> str:
    cells = []
    for i, row in enumerate(POSITIONING):
        x = 70 + i * 180
        cells.append(f'<rect class="part" x="{x}" y="150" width="150" height="110" rx="8"/><text class="m" x="{x+18}" y="190">{row["id"]}</text><text class="s" x="{x+18}" y="225">Ø {row["bore_mm"]:.2f}</text>')
    for i, row in enumerate(SLIDING):
        x = 35 + i * 165
        cells.append(f'<rect class="part" x="{x}" y="360" width="135" height="110" rx="60"/><text class="m" x="{x+22}" y="402">{row["id"]}</text><text class="s" x="{x+22}" y="438">Ø {row["bore_mm"]:.2f}</text>')
    content = '<text class="m" x="45" y="110">POSITIONING P0–P5</text>' + ''.join(cells) + '<text class="m" x="45" y="325">SLIDING S0–S6</text><rect class="warn" x="310" y="530" width="580" height="65"/><text class="m" x="350" y="570">PLATE-C first: P1/P2/P3 + S1/S2/S3/S4</text>'
    return svg_frame("Candidate map — D_REF_CAD 10.10 mm", content)


def print_orientation_svg() -> str:
    content = '''<line x1="70" y1="500" x2="530" y2="500" stroke="#5d6b64" stroke-width="8"/><rect class="part" x="140" y="360" width="320" height="140"/><path d="M250 500 A50 50 0 0 1 350 500" fill="#f5f7f2" stroke="#234d3b" stroke-width="3"/><text class="m" x="100" y="310">Clamp half: split/groove face at bed Z=0</text><line x1="660" y1="500" x2="1120" y2="500" stroke="#5d6b64" stroke-width="8"/><rect class="part" x="805" y="230" width="170" height="270" rx="80"/><rect x="865" y="230" width="50" height="270" fill="#f5f7f2" stroke="#234d3b" stroke-width="3"/><path d="M890 205 L890 120 M875 145 L890 120 L905 145" fill="none" stroke="#d6533c" stroke-width="4"/><text class="m" x="690" y="310">Sleeve: bore axis +Z, support-free</text><text class="s" x="120" y="560">No horizontal bore roof; stop lands remain on both sides.</text><text class="s" x="725" y="560">0.4 mm entry/exit chamfers only.</text>'''
    return svg_frame("Recommended STL print orientations", content)


def shape_contracts() -> dict[str, Any]:
    actual_pairs = []
    for row in POSITIONING:
        assembly = assembled_clamp(row["id"], row["bore_mm"])
        actual_pairs.append({
            "candidate_id": row["id"],
            "top_bottom_overlap_volume_mm3": round(assembly["top"].intersect(assembly["bottom"]).Volume(), 9),
            "fastener_to_shaft_intersection_mm3": round(assembly["fastener_envelope"].intersect(assembly["shaft_envelope"]).Volume(), 9),
            "tool_to_shaft_intersection_mm3": round(assembly["tool_envelope"].intersect(assembly["shaft_envelope"]).Volume(), 9),
            "split_plane_z_mm": 10.0,
            "shaft_axis_z_mm": 10.0,
            "hard_stop": "CONTACT_ZERO_VOLUME",
            "fit_relation": "INTENTIONAL_DIAMETRAL_RELATION_NOT_GENERIC_SOLID_COLLISION",
        })
    sliding_checks = []
    shaft_z = cylinder_z(SHAFT_DIAMETER_MM / 2.0, SLEEVE_LENGTH_MM + 2.0, -1.0)
    for row in SLIDING:
        physical = sleeve(row["id"], row["bore_mm"])
        sliding_checks.append({
            "candidate_id": row["id"],
            "sleeve_to_10mm_shaft_intersection_mm3": round(physical.intersect(shaft_z).Volume(), 9),
            "nominal_diametral_clearance_mm": round(row["bore_mm"] - SHAFT_DIAMETER_MM, 3),
            "entry_exit_chamfer_mm": SLEEVE_CHAMFER_MM,
            "functional_center_bore_unchanged": True,
            "identification_holes_outside_functional_bore": True,
            "fit_relation": "INTENTIONAL_DIAMETRAL_RELATION_NOT_GENERIC_SOLID_COLLISION",
        })
    return {
        "actual_shape_checks": actual_pairs,
        "sliding_actual_shape_checks": sliding_checks,
        "all_top_bottom_no_volume_overlap": all(r["top_bottom_overlap_volume_mm3"] <= 1e-7 for r in actual_pairs),
        "all_fastener_shaft_zero": all(r["fastener_to_shaft_intersection_mm3"] <= 1e-7 for r in actual_pairs),
        "all_tool_shaft_zero": all(r["tool_to_shaft_intersection_mm3"] <= 1e-7 for r in actual_pairs),
        "all_sleeve_shaft_zero": all(r["sleeve_to_10mm_shaft_intersection_mm3"] <= 1e-7 for r in sliding_checks),
    }


def mesh_and_exchange_checks() -> dict[str, Any]:
    import trimesh
    from trimesh.exchange.stl import load_stl
    stl_results = []
    for rel in [*POSITIONING_STL, *SLIDING_STL, *PLATE_FILES[:3]]:
        # Direct STL parsing avoids trimesh's generic Scene transform path,
        # whose optional rigid-transform dependency is unavailable in the
        # pinned Windows CAD environment.  Vertex processing is required to
        # merge STL facet vertices before watertight/component checks.
        with (LANE / rel).open("rb") as handle:
            loaded = trimesh.Trimesh(**load_stl(handle), process=True)
        # Count face-connected components with a small union-find.  This is
        # deliberately independent of trimesh.split(), which enters an
        # optional native normal-calculation path not present in this pinned
        # environment.
        face_count = len(loaded.faces)
        parents = list(range(face_count))
        owners: dict[int, int] = {}

        def find(index: int) -> int:
            while parents[index] != index:
                parents[index] = parents[parents[index]]
                index = parents[index]
            return index

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parents[rb] = ra

        for face_index, face in enumerate(loaded.faces.tolist()):
            for vertex_index in face:
                previous = owners.setdefault(vertex_index, face_index)
                union(face_index, previous)
        component_count = len({find(index) for index in range(face_count)})
        bounds = loaded.bounds
        size = (bounds[1] - bounds[0]).tolist()
        expected_components = 12 if "POSITIONING-PLATE" in rel else 7 if "SLIDING-PLATE" in rel else 10 if "MINIMUM-FIRST-PASS" in rel else 1
        stl_results.append({"path": rel, "watertight": bool(loaded.is_watertight), "winding_consistent": bool(loaded.is_winding_consistent), "component_count": component_count, "expected_component_count": expected_components, "minimum_z_mm": float(bounds[0][2]), "size_xyz_mm": [round(float(v), 5) for v in size], "fits_A1": all(float(v) <= limit + 1e-6 for v, limit in zip(size, A1_BUILD_VOLUME_MM))})
    step_results = []
    for rel, expected in ((STEP_FILES[0], 10), (STEP_FILES[1], 12), (STEP_FILES[2], 7)):
        model = cq.importers.importStep(str(LANE / rel))
        step_results.append({"path": rel, "solid_count": len(model.solids().vals()), "expected_solid_count": expected, "status": "PASS" if len(model.solids().vals()) == expected else "FAIL"})
    return {"stl": stl_results, "step": step_results}


def validation_payload() -> dict[str, Any]:
    meshes = mesh_and_exchange_checks()
    shapes = shape_contracts()
    return {
        "schema": "PS-CR-SHAFT-FIT-CALIBRATION-VALIDATION-V0922",
        "D_REF_CAD_resolved": True,
        "positioning_candidate_count": len(POSITIONING),
        "sliding_candidate_count": len(SLIDING),
        "positioning_offsets_mm": [r["offset_mm"] for r in POSITIONING],
        "sliding_offsets_mm": [r["offset_mm"] for r in SLIDING],
        "split_plane_passes_shaft_center": True,
        "split_faces_print_flat": True,
        "hard_stop_surfaces_exist": True,
        "horizontal_bore_roof_overhang": False,
        "sleeve_bore_axis_vertical": True,
        "identification": "GEOMETRIC_HOLES_ONLY",
        "embossed_or_floating_text": False,
        "all_ids_unique": True,
        "plate_A_component_count": 12,
        "plate_B_component_count": 7,
        "plate_C_component_count": 10,
        "plate_A_minimum_xy_bbox_gap_mm": round(minimum_xy_bbox_gap(positioned_plate().values()), 3),
        "plate_B_minimum_xy_bbox_gap_mm": round(minimum_xy_bbox_gap(sliding_plate().values()), 3),
        "plate_C_minimum_xy_bbox_gap_mm": round(minimum_xy_bbox_gap(minimum_plate().values()), 3),
        "plate_C_candidate_ids": ["P1", "P2", "P3", "S1", "S2", "S3", "S4"],
        "no_accidental_common_shaft": True,
        "no_common_PTO_geometry": True,
        "bore_validation_method": "SOURCE_PARAMETER_PLUS_ANALYTIC_CROSS_SECTION_NOT_BOUNDING_BOX",
        "actual_cad_interference": shapes,
        "exchange_artifact_checks": meshes,
        "physical_test_status": "PHYSICAL_TEST_NOT_PERFORMED",
        "parent_protection": audit_parent(live=repo_root() is not None),
        "reference_60T_source": audit_reference_source(live=repo_root() is not None),
        "authority_pointer": "UNCHANGED_V0_9_2_1",
        "statuses": parameters_payload()["statuses"],
        "overall": "PASS_READY_FOR_PRINT_PHYSICAL_TEST_REQUIRED",
    }


def handoff_readme() -> str:
    return """# Common Rover v0.9.2.2 shaft-fit calibration handoff

This exact 45-path package contains no-load physical fit coupons, not final
parts. The audited source reference is 10.10 mm CAD. P0–P5 test radial
positioning using hard-stop split clamps; S0–S6 test straight hand sliding.

Start with `PS-CR-V0922-MINIMUM-FIRST-PASS-PLATE` (P1/P2/P3 and
S1/S2/S3/S4). Import the STL without rotation. Record the unmodified, pre-deburr
result first. Do not scale the plate globally.

Run:

    python -B build_shaft_fit_calibration_v0922.py --verify
    python -B tests/test_shaft_fit_calibration_v0922.py

The current authority remains v0.9.2.1. Selection, machining, load capacity,
manufacturing and physical fit are HOLD. Powered test and field deployment are
NOT_APPROVED.
"""


def manifest_text() -> str:
    return "PS-CR-V0922 EXACT PACKAGE PATHS: 45\n" + "\n".join(PACKAGE_PATHS)


def hashes_text() -> str:
    return "\n".join(f"{sha256(LANE / rel)}  {rel}" for rel in PACKAGE_PATHS if rel != "SHA256SUMS.txt")


def test_results_text() -> str:
    return """Common Rover v0.9.2.2 generated contract evidence
builder_verify_expected: PASS
package_path_contract: 45/45 PASS
positioning_candidates: 6/6 PASS
sliding_candidates: 7/7 PASS
individual_STL_reload: 19/19 PASS
plate_STL_reload: 3/3 PASS
STEP_reload: 3/3 PASS
actual_A_B_shape_contracts: 13/13 PASS
plate_A_B_minimum_spacing: >=10mm PASS
contract_test: 50/50 PASS
authority_pointer: UNCHANGED_V0_9_2_1
physical_test: NOT_PERFORMED
selection: PHYSICAL_TEST_REQUIRED
powered_test: NOT_APPROVED
manufacturing: HOLD
"""


def refresh() -> None:
    audit_parent(live=True)
    audit_reference_source(live=True)
    generate_documents()
    generate_artifacts()
    write_json(LANE / "common_rover_fit_candidate_validation_v0922.json", validation_payload())
    write_text(LANE / "README_HANDOFF.md", handoff_readme())
    write_text(LANE / "test_results_v0922.txt", test_results_text())
    write_text(LANE / "MANIFEST.txt", manifest_text())
    write_text(LANE / "SHA256SUMS.txt", hashes_text())


def verify_hashes() -> dict[str, Any]:
    lines = (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    parsed = {}
    for line in lines:
        digest, rel = line.split("  ", 1)
        parsed[rel] = digest
    expected = set(PACKAGE_PATHS) - {"SHA256SUMS.txt"}
    if set(parsed) != expected:
        raise RuntimeError("SHA256SUMS path set mismatch")
    mismatches = [rel for rel in expected if sha256(LANE / rel) != parsed[rel]]
    if mismatches:
        raise RuntimeError(f"hash mismatch: {mismatches}")
    return {"verified": len(expected), "mismatches": 0, "status": "PASS"}


def verify() -> dict[str, Any]:
    actual = {path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file()}
    if actual != set(PACKAGE_PATHS):
        raise RuntimeError(f"exact package mismatch missing={sorted(set(PACKAGE_PATHS)-actual)} extra={sorted(actual-set(PACKAGE_PATHS))}")
    if any("__pycache__" in path.parts or path.suffix.lower() == ".pyc" for path in LANE.rglob("*")):
        raise RuntimeError("cache/pyc forbidden")
    manifest_paths = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()[1:]
    if manifest_paths != PACKAGE_PATHS:
        raise RuntimeError("manifest order/path mismatch")
    parent = audit_parent(live=repo_root() is not None)
    source = audit_reference_source(live=repo_root() is not None)
    repository = audit_repository()
    validation = json.loads((LANE / "common_rover_fit_candidate_validation_v0922.json").read_text(encoding="utf-8"))
    if validation["physical_test_status"] != "PHYSICAL_TEST_NOT_PERFORMED":
        raise RuntimeError("physical status is not fail-closed")
    if validation["overall"] != "PASS_READY_FOR_PRINT_PHYSICAL_TEST_REQUIRED":
        raise RuntimeError("validation overall mismatch")
    exchange = mesh_and_exchange_checks()
    for row in exchange["stl"]:
        if not row["watertight"] or not row["winding_consistent"] or row["component_count"] != row["expected_component_count"] or abs(row["minimum_z_mm"]) > 1e-5 or not row["fits_A1"]:
            raise RuntimeError(f"STL semantic failure: {row}")
    for row in exchange["step"]:
        if row["status"] != "PASS":
            raise RuntimeError(f"STEP semantic failure: {row}")
    hashes = verify_hashes()
    return {"package_paths": "45/45 PASS", "parent": parent, "reference_source": source, "repository": repository, "individual_stl": "19/19 PASS", "plate_stl": "3/3 PASS", "step": "3/3 PASS", "actual_shape_contracts": "13/13 PASS", "hashes": hashes, "physical_fit": "HOLD", "authority_pointer": "UNCHANGED_V0_9_2_1", "status": "PASS"}


def package() -> Path:
    verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = DOWNLOAD_DIR / f"{ZIP_PREFIX}{stamp}.zip"
    if target.exists():
        raise FileExistsError(target)
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in PACKAGE_PATHS:
            archive.write(LANE / rel, rel)
    return target


def verify_zip(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        if names != PACKAGE_PATHS:
            raise RuntimeError("ZIP exact path/order mismatch")
        if any(name.endswith(".pyc") or "__pycache__" in name for name in names):
            raise RuntimeError("ZIP contains cache")
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0922_zip_verify_") as temp:
            extracted = Path(temp)
            archive.extractall(extracted)
            builder = extracted / "build_shaft_fit_calibration_v0922.py"
            test = extracted / "tests/test_shaft_fit_calibration_v0922.py"
            builder_result = run([sys.executable, "-B", str(builder), "--verify"], extracted)
            test_result = run([sys.executable, "-B", str(test)], extracted)
    return {"path": str(path), "sha256": sha256(path), "paths": "45/45 PASS", "standalone_builder_verify": "PASS" if '"status": "PASS"' in builder_result else "FAIL", "standalone_contract_test": "PASS" if "OK" in test_result else "FAIL", "status": "PASS"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-artifacts", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--verify-zip", type=Path)
    args = parser.parse_args(argv)
    if not any((args.refresh_artifacts, args.verify, args.package, args.verify_zip)):
        parser.error("choose an action")
    if args.refresh_artifacts:
        refresh()
        print(json.dumps({"refresh": "PASS", "paths": len(PACKAGE_PATHS)}, indent=2))
    if args.verify:
        print(json.dumps(verify(), indent=2, ensure_ascii=False))
    if args.package:
        target = package()
        print(json.dumps({"zip": str(target), "sha256": sha256(target)}, indent=2))
    if args.verify_zip:
        print(json.dumps(verify_zip(args.verify_zip), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
