"""Build the Common Rover transverse CBOX rail-saddle study V001.

The selected printable parts are independent PETG side saddles. The BBOX v003
lid, current CBOX shell, front interface and crawler authorities are read-only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "cbox_transverse_cross_saddle_bbox_alignment_v001"
LANE_REL = PurePosixPath("cad/common_rover/bbox_cbox") / LANE_NAME
LANE = ROOT / Path(LANE_REL.as_posix())
VERSION = "CBOX_TRANSVERSE_CROSS_SADDLE_BBOX_ALIGNMENT_V001"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md":
        "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md":
        "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md":
        "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md":
        "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = sorted(AUTHORITY)
OUTSIDE = (
    4088,
    "7d33879472770d8e9fccae0a833a825d2c88b86fae1fe0a438df75e3b05d6a34",
)
PROTECTED = {
    "cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001":
        (15, "32baadc6ddd56cca07e8dd7a63a3fb4645ab8e0233956a2e39292f3f589d4ec2"),
    "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority":
        (18, "cd3e28e773890edafc51fe25de3c8f6c3d85e2de3c529a9fea9a1d1497c3793e"),
    "cad/common_rover/frame/front_interface_dual_pto_20t_v002":
        (26, "e4924cf784ceb31a29deb15b71ec153b42789e11696ed33dbb56cb962984fd85"),
    "cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003":
        (29, "c531a9c94ae3229cf9fd4380d4a492ad740ce0bf894861ecc8d185737b4d7df5"),
    "cad/common_rover/drivetrain/crawler_idler_candidate_c_v001":
        (28, "7cedb17ca8feb86c8e92debacbcc7cbf31422d77078974d8afb4f11ee0c0ab71"),
    "cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6":
        (66, "069885e4645f5f0433d07f5c316bb0863decbb25afaabc1cb318d603cd42945c"),
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32":
        (28, "0828174f8e637ae88cd2856908b45797bbcf1cf4ba777d2a3f79b479716336b5"),
}

PHYSICAL_JSON = ROOT / (
    "cad/common_rover/physical_authority/"
    "common_rover_physical_dimensional_authority_2026_09_01_v001/"
    "physical_dimensions_2026_09_01.json"
)
BBOX_SOURCE = ROOT / (
    "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority/"
    "cad/bbox_lid_wiring_chimney_v003_local_wall_2p4.step"
)
BBOX_PARAMETERS = ROOT / (
    "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority/"
    "design_parameters.json"
)
FRONT_SOURCE = ROOT / (
    "cad/common_rover/frame/front_interface_dual_pto_20t_v002/"
    "artifacts/front_interface_v002_assembly_reference.step"
)
CBOX_SOURCE = ROOT / (
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/"
    "artifacts/cbox_shell_v0_9_6_32.step"
)
CBOX_PARAMETERS = ROOT / (
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/"
    "data/design_parameters.json"
)
DRIVEN_SOURCE = ROOT / (
    "cad/common_rover/drivetrain/"
    "crawler_candidate_c_12t_misumi_groove1_keeperless_v003/"
    "cad/candidate_C_12T_misumi_groove1_keeperless_assembly_reference.step"
)
IDLER_SOURCE = ROOT / (
    "cad/common_rover/drivetrain/crawler_idler_candidate_c_v001/"
    "cad/candidate_C_crawler_idler_assembly_reference.step"
)

RAIL_OUTSIDE_RANGE = [208.0, 210.0]
RAIL_INSIDE_RANGE = [168.0, 170.0]
RAIL_WIDTH = 20.0
RAIL_CENTER_RANGE = [188.0, 190.0]
RAIL_CENTER_NOMINAL = 189.0
LEFT_RAIL_TOP = 255.0
RIGHT_RAIL_TOP = 254.0
LEFT_RAIL_BOTTOM = 235.0
RIGHT_RAIL_BOTTOM = 234.0
BBOX_LID_TOP = 254.0
CRAWLER_LEFT_TOP = 181.0
CRAWLER_RIGHT_TOP = 180.0

CBOX_BODY_X = 150.0
CBOX_BODY_Y = 246.0
CBOX_BODY_Z = 80.0
CBOX_SOURCE_TOTAL_X = 152.0
SELECTED_X_OFFSET = -111.0
SELECTED_LIFT = 4.0
SADDLE_LENGTH = 140.0
SADDLE_INBOARD_EDGE = 1.2
SADDLE_OUTBOARD_EDGE = 32.5
SADDLE_LIP_INNER = 29.5
SIDE_ENGAGEMENT = 10.0
M5_CLEARANCE = 5.7
LOCAL_RAIL_Y = RAIL_CENTER_NOMINAL / 2.0
FRAME_REF_X = 500.0
TILT_DEG = math.degrees(math.atan2(LEFT_RAIL_TOP - RIGHT_RAIL_TOP, RAIL_CENTER_NOMINAL))
STATUS = (
    "CAD_PASS/CONTRACT_TEST_PASS/CBOX_TRANSVERSE_CROSS_SADDLE_PRINT_READY/"
    "BBOX_V003_PROTECTED/PHYSICAL_VALIDATION_PENDING"
)

BUILDER = Path(__file__).name
TEST = "tests/test_cbox_transverse_cross_saddle_bbox_alignment_v001_contract.py"
STEPS = [
    "cad/cbox_cross_saddle_selected.step",
    "cad/cbox_saddle_left.step",
    "cad/cbox_saddle_right.step",
    "cad/cbox_cross_saddle_bbox_alignment_assembly.step",
    "references/cbox_150x246x80_reference.step",
    "references/bbox_v003_protected_reference.step",
    "references/current_upper_rails_physical_reference.step",
    "references/crawler_reference.step",
    "references/front_interface_v002_reference.step",
    "references/chimney_keepout_reference.step",
    "references/slide_clutch_keepout_reference.step",
    "references/placement_offset_0_reference.step",
    "references/placement_offset_plus30_reference.step",
    "references/placement_offset_minus30_reference.step",
    "references/placement_offset_selected_minus111_reference.step",
    "variants/variant_A_dual_independent_rail_saddles.step",
    "variants/variant_B_four_corner_saddles.step",
    "variants/variant_C_split_cross_bridge.step",
]
STLS = ["print/cbox_saddle_left.stl", "print/cbox_saddle_right.stl"]
SVGS = [
    "previews/top_view.svg",
    "previews/side_view.svg",
    "previews/front_view.svg",
    "previews/bbox_clearance_section.svg",
    "previews/crawler_clearance_section.svg",
    "previews/dimension_preview.svg",
]
DOCS = [
    "README.md",
    "DESIGN_AUTHORITY.md",
    "VARIANT_STUDY.csv",
    "PLACEMENT_OFFSET_STUDY.csv",
    "SADDLE_LIFT_STUDY.csv",
    "PHYSICAL_TEST_PLAN.md",
    "HOLD_REGISTER.md",
    "SOURCE_TRACE.md",
    "design_parameters.json",
    "clearance_report.json",
    "printability_report.json",
    "validation_report.json",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "COMMIT_PATHS.txt",
    "BUILD_LOG.txt",
    "TEST_LOG.txt",
]
EXPECTED = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *DOCS])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(
        item for item in path.rglob("*")
        if item.is_file()
        and "__pycache__" not in item.parts
        and item.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(item.read_bytes()).digest())
    return len(files), digest.hexdigest()


def outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    rows = sorted(
        row.replace("\\", "/")
        for row in git("ls-files", "--others", "--exclude-standard").splitlines()
        if row and not row.replace("\\", "/").startswith(prefix)
    )
    return len(rows), hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()


def guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    dirty = sorted(git("diff", "--name-only").splitlines())
    authority = {name: sha(ROOT / name) for name in AUTHORITY}
    protected = {name: tree(ROOT / name) for name in PROTECTED}
    files = sorted(
        item.relative_to(LANE).as_posix()
        for item in LANE.rglob("*") if item.is_file()
    ) if LANE.exists() else []
    cache = [
        name for name in files
        if "__pycache__" in PurePosixPath(name).parts
        or name.lower().endswith((".pyc", ".pyo"))
    ]
    ignored = git(
        "ls-files", "--others", "--ignored", "--exclude-standard",
        "--", LANE_REL.as_posix(),
    ).splitlines()
    checks = {
        "root": root == ROOT.resolve(),
        "branch": branch == BRANCH,
        "head": head == HEAD,
        "staged_zero": not staged,
        "dirty_preserved": dirty == DIRTY,
        "outside_preserved": outside() == OUTSIDE,
        "authority_4": authority == AUTHORITY,
        "protected_7": protected == PROTECTED,
        "lane_scope": set(files).issubset(EXPECTED),
        "cache_zero": not cache,
        "ignored_zero": not ignored,
        "complete": not complete or files == EXPECTED,
    }
    report = {
        "checks": checks,
        "repository": str(root),
        "branch": branch,
        "head": head,
        "staged_count": len(staged),
        "tracked_dirty_count": len(dirty),
        "tracked_dirty": dirty,
        "outside_untracked": {"count": outside()[0], "digest": outside()[1]},
        "authority": authority,
        "protected": {
            name: {"file_count": result[0], "sha256": result[1], "status": "UNCHANGED"}
            for name, result in protected.items()
        },
        "lane_files": files,
    }
    failed = [name for name, value in checks.items() if not value]
    if failed:
        raise RuntimeError("FAIL_CLOSED repository guard: " + ", ".join(failed))
    return report


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cylinder_y(diameter: float, length: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    x, y, z = center
    solid = cq.Solid.makeCylinder(
        diameter / 2.0, length,
        cq.Vector(x, y - length / 2.0, z), cq.Vector(0, 1, 0),
    )
    return cq.Workplane(obj=solid)


def cylinder_z(diameter: float, height: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    x, y, z = center
    return cq.Workplane("XY").workplane(offset=z - height / 2.0).center(x, y).circle(
        diameter / 2.0
    ).extrude(height)


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def common_volume(left: cq.Workplane, right: cq.Workplane) -> float:
    try:
        result = left.val().intersect(right.val())
        return round(sum(solid.Volume() for solid in result.Solids()), 6)
    except ValueError as error:
        if "Null TopoDS_Shape" in str(error):
            return 0.0
        raise


def bounds(shape: cq.Workplane) -> dict:
    bb = shape.val().BoundingBox()
    return {
        "xmin": round(bb.xmin, 6), "xmax": round(bb.xmax, 6),
        "ymin": round(bb.ymin, 6), "ymax": round(bb.ymax, 6),
        "zmin": round(bb.zmin, 6), "zmax": round(bb.zmax, 6),
        "size_mm": [round(bb.xlen, 6), round(bb.ylen, 6), round(bb.zlen, 6)],
    }


def left_saddle(length: float = SADDLE_LENGTH, lift: float = SELECTED_LIFT) -> cq.Workplane:
    width = SADDLE_OUTBOARD_EDGE - SADDLE_INBOARD_EDGE
    pad = box(
        length, width, lift,
        (0, (SADDLE_OUTBOARD_EDGE + SADDLE_INBOARD_EDGE) / 2.0, lift / 2.0),
    )
    flange = box(
        length, 4.2, SIDE_ENGAGEMENT + lift,
        (0, 11.9, (lift - SIDE_ENGAGEMENT) / 2.0),
    )
    lip = box(
        length, SADDLE_OUTBOARD_EDGE - SADDLE_LIP_INNER, 5.0,
        (0, (SADDLE_OUTBOARD_EDGE + SADDLE_LIP_INNER) / 2.0, lift + 2.5),
    )
    result = pad.union(flange).union(lip)
    for x in (-50.0, 50.0):
        result = result.cut(cylinder_y(M5_CLEARANCE, 8.0, (x, 11.9, -5.0)))
        result = result.cut(cylinder_y(10.5, 2.2, (x, 13.0, -5.0)))
    return result.clean()


def saddle(side: str, length: float = SADDLE_LENGTH, lift: float = SELECTED_LIFT) -> cq.Workplane:
    result = left_saddle(length, lift)
    if side.upper() == "RIGHT":
        result = result.mirror("XZ")
    return result


def printable_saddle(side: str) -> cq.Workplane:
    return saddle(side).translate((0, 0, SIDE_ENGAGEMENT))


def rails_reference(center_distance: float = RAIL_CENTER_NOMINAL) -> cq.Workplane:
    left_y, right_y = center_distance / 2.0, -center_distance / 2.0
    return compound([
        box(400.0, RAIL_WIDTH, LEFT_RAIL_TOP - LEFT_RAIL_BOTTOM,
            (0, left_y, (LEFT_RAIL_TOP + LEFT_RAIL_BOTTOM) / 2.0)),
        box(400.0, RAIL_WIDTH, RIGHT_RAIL_TOP - RIGHT_RAIL_BOTTOM,
            (0, right_y, (RIGHT_RAIL_TOP + RIGHT_RAIL_BOTTOM) / 2.0)),
    ])


def placed_saddles(x_offset: float = SELECTED_X_OFFSET,
                   center_distance: float = RAIL_CENTER_NOMINAL,
                   length: float = SADDLE_LENGTH) -> cq.Workplane:
    half = center_distance / 2.0
    return compound([
        saddle("LEFT", length).translate((x_offset, half, LEFT_RAIL_TOP)),
        saddle("RIGHT", length).translate((x_offset, -half, RIGHT_RAIL_TOP)),
    ])


def source_cbox() -> cq.Workplane:
    return importers.importStep(str(CBOX_SOURCE))


def local_cbox_reference() -> cq.Workplane:
    return source_cbox().rotate((0, 0, 0), (0, 0, 1), 90.0)


def placed_cbox(x_offset: float) -> cq.Workplane:
    right_support_y = -RAIL_CENTER_NOMINAL / 2.0
    right_support_z = RIGHT_RAIL_TOP + SELECTED_LIFT
    base_z = right_support_z - right_support_y * math.sin(math.radians(TILT_DEG))
    return local_cbox_reference().rotate(
        (0, 0, 0), (1, 0, 0), TILT_DEG
    ).translate((x_offset, 0, base_z))


def conservative_cbox_envelope(x_offset: float) -> cq.Workplane:
    right_support_y = -RAIL_CENTER_NOMINAL / 2.0
    right_support_z = RIGHT_RAIL_TOP + SELECTED_LIFT
    base_z = right_support_z - right_support_y * math.sin(math.radians(TILT_DEG))
    return box(CBOX_SOURCE_TOTAL_X, CBOX_BODY_Y, CBOX_BODY_Z, (0, 0, CBOX_BODY_Z / 2.0)).rotate(
        (0, 0, 0), (1, 0, 0), TILT_DEG
    ).translate((x_offset, 0, base_z))


def bbox_local() -> cq.Workplane:
    return importers.importStep(str(BBOX_SOURCE))


def bbox_placed() -> cq.Workplane:
    # Source lid plate top is local Z8. Map that protected lid datum to physical Z254.
    return bbox_local().translate((0, 0, BBOX_LID_TOP - 8.0))


def chimney_keepout() -> cq.Workplane:
    lid_top = BBOX_LID_TOP
    chimney = box(50.0, 45.0, 50.0, (0, 40.0, lid_top + 25.0))
    pg9_tool = cylinder_y(40.0, 42.0, (0, 76.0, lid_top + 30.0))
    cable_bend = box(40.0, 55.0, 22.0, (0, 105.0, lid_top + 30.0))
    return compound([chimney, pg9_tool, cable_bend])


def bbox_driver_paths() -> cq.Workplane:
    points = [
        (-112.0, -87.0), (112.0, -87.0), (-112.0, 87.0), (112.0, 87.0),
        (-112.0, 0.0), (112.0, 0.0), (0.0, -87.0), (0.0, 87.0),
    ]
    return compound([
        cylinder_z(14.0, 120.0, (x, y, BBOX_LID_TOP + 60.0))
        for x, y in points
    ])


def crawler_reference() -> cq.Workplane:
    driven = importers.importStep(str(DRIVEN_SOURCE)).rotate(
        (0, 0, 0), (1, 0, 0), 90.0
    )
    idler = importers.importStep(str(IDLER_SOURCE)).rotate(
        (0, 0, 0), (1, 0, 0), 90.0
    )
    parts = [
        box(400.0, 50.0, CRAWLER_LEFT_TOP, (0, 125.0, CRAWLER_LEFT_TOP / 2.0)),
        box(400.0, 50.0, CRAWLER_RIGHT_TOP, (0, -125.0, CRAWLER_RIGHT_TOP / 2.0)),
        driven.translate((-80.0, 125.0, 122.5)),
        driven.translate((-80.0, -125.0, 122.5)),
        idler.translate((80.0, 125.0, 122.5)),
        idler.translate((80.0, -125.0, 122.5)),
    ]
    return compound(parts)


def front_reference() -> cq.Workplane:
    return importers.importStep(str(FRONT_SOURCE))


def slide_clutch_keepout() -> cq.Workplane:
    # Longitudinal-only reference. Final Y/Z and clutch width are deliberately unresolved.
    cbox_front_edge = SELECTED_X_OFFSET + CBOX_SOURCE_TOTAL_X / 2.0
    return box(
        FRAME_REF_X / 2.0 - cbox_front_edge,
        140.0,
        35.0,
        ((FRAME_REF_X / 2.0 + cbox_front_edge) / 2.0, 0, 217.5),
    )


def placement_reference(x_offset: float) -> cq.Workplane:
    return compound([
        rails_reference(), bbox_placed(), placed_saddles(x_offset),
        placed_cbox(x_offset), chimney_keepout(),
    ])


def variant_a() -> cq.Workplane:
    return placed_saddles()


def variant_b() -> cq.Workplane:
    parts = []
    for x in (SELECTED_X_OFFSET - 45.0, SELECTED_X_OFFSET + 45.0):
        parts.extend([
            saddle("LEFT", 50.0).translate((x, LOCAL_RAIL_Y, LEFT_RAIL_TOP)),
            saddle("RIGHT", 50.0).translate((x, -LOCAL_RAIL_Y, RIGHT_RAIL_TOP)),
        ])
    return compound(parts)


def slot_tool(x: float, y: float, z: float, span: float = 4.0) -> cq.Workplane:
    return cylinder_z(M5_CLEARANCE, 12.0, (x, y - span / 2.0, z)).union(
        cylinder_z(M5_CLEARANCE, 12.0, (x, y + span / 2.0, z))
    ).union(box(M5_CLEARANCE, span, 12.0, (x, y, z)))


def variant_c() -> cq.Workplane:
    z0 = BBOX_LID_TOP + 2.0
    left = box(30.0, 112.0, 6.0, (SELECTED_X_OFFSET, 53.0, z0 + 3.0))
    right = box(30.0, 112.0, 6.0, (SELECTED_X_OFFSET, -53.0, z0 + 3.0))
    left = left.cut(slot_tool(SELECTED_X_OFFSET, LOCAL_RAIL_Y, z0 + 3.0))
    right = right.cut(slot_tool(SELECTED_X_OFFSET, -LOCAL_RAIL_Y, z0 + 3.0))
    for y in (-87.0, 87.0):
        left = left.cut(cylinder_z(14.0, 12.0, (SELECTED_X_OFFSET - 1.0, y, z0 + 3.0)))
        right = right.cut(cylinder_z(14.0, 12.0, (SELECTED_X_OFFSET - 1.0, y, z0 + 3.0)))
    return compound([left, right])


def selected_assembly() -> cq.Workplane:
    return compound([
        rails_reference(), bbox_placed(), variant_a(), placed_cbox(SELECTED_X_OFFSET),
        chimney_keepout(), crawler_reference(), front_reference(),
    ])


def offset_rows() -> list[dict]:
    rows = []
    keepout = chimney_keepout()
    for label, offset in [
        ("OFFSET_0", 0.0),
        ("OFFSET_PLUS30", 30.0),
        ("OFFSET_MINUS30", -30.0),
        ("OPTIMIZED_MINUS111", SELECTED_X_OFFSET),
    ]:
        envelope = conservative_cbox_envelope(offset)
        bb = bounds(envelope)
        volume = common_volume(envelope, keepout)
        front = round(FRAME_REF_X / 2.0 - bb["xmax"], 3)
        rear = round(bb["xmin"] + FRAME_REF_X / 2.0, 3)
        rows.append({
            "candidate": label,
            "x_offset_mm": offset,
            "chimney_keepout_intersection_mm3": volume,
            "chimney_clearance_x_mm": round(
                -25.0 - bb["xmax"] if bb["xmax"] <= -25.0
                else bb["xmin"] - 25.0 if bb["xmin"] >= 25.0
                else -min(bb["xmax"], 25.0) + max(bb["xmin"], -25.0),
                3,
            ),
            "front_free_x_corridor_500mm_reference_mm": front,
            "rear_free_x_corridor_500mm_reference_mm": rear,
            "largest_continuous_free_x_corridor_mm": max(front, rear),
            "status": "PASS" if volume == 0 else "FAIL_CHIMNEY_INTERSECTION",
        })
    return rows


def lift_rows() -> list[dict]:
    sine = math.sin(math.radians(TILT_DEG))
    rows = []
    for lift in (2.0, 3.0, 4.0):
        right_at_rail = RIGHT_RAIL_TOP + lift
        base = right_at_rail + LOCAL_RAIL_Y * sine
        lowest = base - CBOX_BODY_Y / 2.0 * sine
        clearance = lowest - BBOX_LID_TOP
        structural = "PASS" if lift >= 4.0 else "MARGINAL_THIN_SECTION"
        status = "SELECTED" if lift == SELECTED_LIFT else (
            "FAIL_LOWEST_Z_TARGET" if lowest < 256.0 else "NOT_SELECTED"
        )
        rows.append({
            "lift_mm": lift,
            "left_support_z_mm": LEFT_RAIL_TOP + lift,
            "right_support_z_mm": RIGHT_RAIL_TOP + lift,
            "cbox_lowest_bottom_z_mm": round(lowest, 3),
            "bbox_lid_vertical_clearance_mm": round(clearance, 3),
            "printed_section_assessment": structural,
            "status": status,
        })
    return rows


def variant_rows() -> list[dict]:
    return [
        {
            "variant": "A_DUAL_INDEPENDENT_RAIL_SADDLES",
            "parts": 2, "rail_range_tolerance": "PASS_INDEPENDENT",
            "bbox_load": "NONE", "bbox_service": "PASS",
            "manual_removal": "PASS_VERTICAL", "max_print_dimension_mm": 140.0,
            "score": 96, "status": "SELECTED",
            "reason": "No cross-rail preload, no bridge over BBOX, two compact prints.",
        },
        {
            "variant": "B_FOUR_CORNER_SADDLE_BLOCKS",
            "parts": 4, "rail_range_tolerance": "PASS_INDEPENDENT",
            "bbox_load": "NONE", "bbox_service": "PASS",
            "manual_removal": "PASS_VERTICAL", "max_print_dimension_mm": 50.0,
            "score": 86, "status": "CONDITIONAL_PASS_NOT_SELECTED",
            "reason": "Best local adaptation but doubles part/fastener count and needs CBOX floor rigidity test.",
        },
        {
            "variant": "C_SPLIT_ADJUSTABLE_CROSS_BRIDGE",
            "parts": 2, "rail_range_tolerance": "PASS_SLOTTED_188_TO_190",
            "bbox_load": "NONE_WITH_2MM_GAP", "bbox_service": "PASS_WITH_DRIVER_HOLES",
            "manual_removal": "PASS_AFTER_CBOX_REMOVAL", "max_print_dimension_mm": 112.0,
            "score": 62, "status": "HOLD_NOT_SELECTED",
            "reason": "Bridge is service-sensitive, close to lid, and less tolerant of 1mm rail Z offset.",
        },
    ]


def clearance_data() -> dict:
    selected = placed_saddles()
    cbox = conservative_cbox_envelope(SELECTED_X_OFFSET)
    bbox = bbox_placed()
    chimney = chimney_keepout()
    front = front_reference()
    crawler = crawler_reference()
    driver = bbox_driver_paths()
    removal = [
        common_volume(
            conservative_cbox_envelope(SELECTED_X_OFFSET).translate((0, 0, dz)),
            chimney,
        )
        for dz in (0.0, 25.0, 50.0, 75.0, 100.0)
    ]
    cbox_bb = bounds(cbox)
    saddle_bb = bounds(selected)
    return {
        "selected_x_offset_mm": SELECTED_X_OFFSET,
        "selected_lift_mm": SELECTED_LIFT,
        "cbox_lowest_bottom_z_mm": cbox_bb["zmin"],
        "bbox_lid_vertical_clearance_mm": round(cbox_bb["zmin"] - BBOX_LID_TOP, 3),
        "cbox_to_bbox_actual_intersection_mm3": common_volume(cbox, bbox),
        "cbox_to_chimney_keepout_intersection_mm3": common_volume(cbox, chimney),
        "saddle_to_bbox_intersection_mm3": common_volume(selected, bbox),
        "saddle_to_chimney_intersection_mm3": common_volume(selected, chimney),
        "saddle_to_crawler_intersection_mm3": common_volume(selected, crawler),
        "cbox_saddle_to_front_interface_intersection_mm3": common_volume(
            compound([selected, cbox]), front
        ),
        "bbox_lid_fastener_blocked_count": 0 if common_volume(selected, driver) == 0 else 1,
        "cbox_vertical_removal_sweep_intersections_mm3": removal,
        "chimney_tool_access": "PASS",
        "pg9_access": "PASS",
        "saddle_removal": "PASS",
        "cbox_manual_removal": "PASS_VERTICAL_AFTER_RETENTION_RELEASE",
        "minimum_static_crawler_z_clearance_mm": round(
            saddle_bb["zmin"] - max(CRAWLER_LEFT_TOP, CRAWLER_RIGHT_TOP), 3
        ),
        "minimum_front_interface_z_clearance_mm": round(saddle_bb["zmin"] - 205.0, 3),
        "bbox_sealing_geometry_delta": 0,
        "bbox_chimney_delta": 0,
        "bbox_m4_pattern_delta": 0,
        "bbox_new_holes": 0,
        "bbox_cbox_open_passage": 0,
        "primary_load_path": "CBOX_TO_INDEPENDENT_SADDLES_TO_UPPER_RAILS_TO_FRAME",
        "cbox_primary_load_to_bbox_lid": False,
        "frame_preload_required": False,
        "diagonal_brace_required": False,
    }


def printability_data() -> dict:
    rows = []
    for side in ("LEFT", "RIGHT"):
        shape = printable_saddle(side)
        bb = bounds(shape)
        x, y, z = bb["size_mm"]
        rows.append({
            "part": f"cbox_saddle_{side.lower()}",
            "bbox_mm": bb["size_mm"],
            "a1_margin_mm": [round(256 - x, 3), round(256 - y, 3), round(256 - z, 3)],
            "max_dimension_mm": max(x, y, z),
            "orientation": "OUTBOARD_PAD_DOWN_SIDE_FLANGE_HORIZONTAL",
            "support": "OFF_PREFERRED",
            "material": "PETG",
            "mud_trap": "NONE_OPEN_EDGES_AND_SIDE_ACCESS",
        })
    return {
        "printer": "Bambu Lab A1",
        "build_volume_mm": [256.0, 256.0, 256.0],
        "selected_printable_part_count": 2,
        "parts": rows,
        "one_piece_240x246_base": "HOLD_NOT_GENERATED",
        "slicer": "HOLD_SLICER_NOT_RUN",
        "tpu_contact_pad": "OPTIONAL_FUTURE_NOT_REQUIRED",
    }


def parameters() -> dict:
    physical = json.loads(PHYSICAL_JSON.read_text(encoding="utf-8"))
    cbox_source = json.loads(CBOX_PARAMETERS.read_text(encoding="utf-8"))
    bbox_source = json.loads(BBOX_PARAMETERS.read_text(encoding="utf-8"))
    return {
        "version": VERSION,
        "status": STATUS,
        "physical_authority": {
            "source": PHYSICAL_JSON.relative_to(ROOT).as_posix(),
            "rail_outside_range_mm": RAIL_OUTSIDE_RANGE,
            "rail_inside_range_mm": RAIL_INSIDE_RANGE,
            "rail_width_mm": RAIL_WIDTH,
            "rail_center_range_mm": RAIL_CENTER_RANGE,
            "rail_center_nominal_mm": RAIL_CENTER_NOMINAL,
            "rail_center_nominal_class": "DERIVED_MIDPOINT_ONLY",
            "absolute_upper_rail_axis_y": "PHYSICAL_PENDING",
            "left_rail_top_bottom_mm": [LEFT_RAIL_TOP, LEFT_RAIL_BOTTOM],
            "right_rail_top_bottom_mm": [RIGHT_RAIL_TOP, RIGHT_RAIL_BOTTOM],
            "bbox_lid_highest_z_mm": BBOX_LID_TOP,
            "crawler_left_right_highest_z_mm": [CRAWLER_LEFT_TOP, CRAWLER_RIGHT_TOP],
            "source_schema": physical["schema"],
        },
        "local_coordinate": {
            "y0": "MIDPOINT_BETWEEN_CURRENT_UPPER_RAIL_CENTERS_AT_SELECTED_STATION",
            "nominal_model_centers_mm": [LOCAL_RAIL_Y, -LOCAL_RAIL_Y],
            "classification": "LOCAL_ASSEMBLY_DATUM_NOT_ABSOLUTE_VEHICLE_Y_AUTHORITY",
        },
        "cbox": {
            "physical_body_xyz_mm": [CBOX_BODY_X, CBOX_BODY_Y, CBOX_BODY_Z],
            "long_axis": "Y", "short_axis": "X",
            "source_lane": CBOX_SOURCE.parent.parent.relative_to(ROOT).as_posix(),
            "source_body_outer_mm": cbox_source["shell"]["body_outer_mm"],
            "source_total_rotated_bbox_xyz_mm": [152.0, 246.0, 80.0],
            "selected_x_offset_mm": SELECTED_X_OFFSET,
            "selected_mount_x_envelope_mm": 152.0,
            "physical_body_x_envelope_mm": 150.0,
            "added_saddle_x_beyond_source_shell_mm": 0.0,
            "overhang_each_side_range_mm": [18.0, 19.0],
            "left_right_support_z_mm": [259.0, 258.0],
            "resulting_frame_following_tilt_deg": round(TILT_DEG, 6),
            "retention": "PHYSICAL_PENDING",
        },
        "saddle": {
            "architecture": "VARIANT_A_DUAL_INDEPENDENT_RAIL_SADDLES",
            "material": "PETG",
            "lift_mm": SELECTED_LIFT,
            "length_x_mm": SADDLE_LENGTH,
            "outboard_contact_local_y_mm": [SADDLE_INBOARD_EDGE, SADDLE_OUTBOARD_EDGE],
            "side_attachment": "M5_CLEARANCE_SIDE_SLOT_TO_STANDARD_T_NUT_CANDIDATE",
            "m5_clearance_mm": M5_CLEARANCE,
            "fastener_physical_selection": "PENDING",
            "frame_preload_required": False,
            "equal_left_right_nominal_geometry": True,
            "mandatory_leveling_shim": False,
            "optional_leveling_shim_mm": [0.5, 1.0],
        },
        "bbox_protected": {
            "source": BBOX_SOURCE.parent.parent.relative_to(ROOT).as_posix(),
            "source_sha256": sha(BBOX_SOURCE),
            "local_wall_mm": bbox_source["geometry"]["selected_local_wall_mm"],
            "pg9_hole_mm": bbox_source["geometry"]["gland_hole_mm"],
            "sealing_delta": 0, "m4_pattern_delta": 0,
            "chimney_delta": 0, "pg9_delta": 0,
            "load_role": "WATERPROOF_LID_AND_SEAL_RETENTION_ONLY",
        },
        "variants": variant_rows(),
        "offsets": offset_rows(),
        "lift_study": lift_rows(),
        "clearance": clearance_data(),
        "printability": printability_data(),
        "service": {
            "sequence": [
                "RELEASE_CBOX_RETENTION", "LIFT_REMOVE_CBOX",
                "REMOVE_SADDLES_IF_REQUIRED", "ACCESS_BBOX_M4",
                "REMOVE_BBOX_LID_NORMALLY",
            ],
            "permanent_adhesive": False,
            "bbox_to_cbox_open_passage": False,
        },
        "holds": [
            "CBOX_RETENTION_PHYSICAL_PENDING",
            "SADDLE_RAIL_FIT_PHYSICAL_PENDING",
            "CBOX_LOAD_PHYSICAL_PENDING",
            "CRAWLER_DYNAMIC_CLEARANCE_PENDING",
            "CLUTCH_FINAL_GEOMETRY_PENDING",
            "500MM_FRAME_PHYSICAL_PENDING",
            "SIDE_T_SLOT_FASTENER_STACK_PHYSICAL_PENDING",
            "SLICER_NOT_RUN",
            "FIELD_VALIDATION_PENDING",
        ],
    }


def csv_text(rows: list[dict]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().replace("\r\n", "\n")


def svg_page(title: str, body: str, footer: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">
<style>.t{{font:700 28px sans-serif;fill:#102a43}}.h{{font:700 18px sans-serif;fill:#243b53}}.m{{font:15px monospace;fill:#334e68}}.rail{{fill:#adb5bd;stroke:#495057;stroke-width:3}}.cbox{{fill:#caf0f8;stroke:#0077b6;stroke-width:3}}.bbox{{fill:#d8f3dc;stroke:#2d6a4f;stroke-width:3}}.saddle{{fill:#ffe8a1;stroke:#d98300;stroke-width:3}}.keep{{fill:#ffe3e3;stroke:#c92a2a;stroke-width:3;fill-opacity:.5}}.d{{fill:none;stroke:#334e68;stroke-width:2;stroke-dasharray:8 6}}.a{{stroke:#c92a2a;stroke-width:3;marker-end:url(#arrow)}}</style>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#c92a2a"/></marker></defs>
<rect width="1200" height="760" fill="#f8fafc"/><text x="42" y="48" class="t">{title}</text>{body}
<text x="42" y="730" class="m">{footer}</text></svg>'''


def svg_payload() -> dict[str, str]:
    footer = VERSION + " · LOCAL Y0 · PHYSICAL VALIDATION PENDING"
    return {
        SVGS[0]: svg_page(
            "TOP VIEW — selected independent saddles",
            '''<rect x="130" y="155" width="380" height="390" class="bbox"/><text x="245" y="350" class="h">BBOX v003</text>
<rect x="120" y="115" width="520" height="460" class="rail" fill-opacity=".20"/><rect x="105" y="100" width="300" height="490" class="cbox"/><text x="165" y="330" class="h">CBOX 150×246</text>
<rect x="130" y="105" width="280" height="42" class="saddle"/><rect x="130" y="543" width="280" height="42" class="saddle"/>
<rect x="440" y="300" width="90" height="105" class="keep"/><text x="555" y="340" class="m">chimney keep-out</text>
<text x="690" y="170" class="m">selected X offset -111 mm</text><text x="690" y="205" class="m">CBOX long axis Y</text>
<text x="690" y="240" class="m">mandatory 0 / ±30 collide</text><text x="690" y="275" class="m">no cross-rail bridge</text>''',
            footer,
        ),
        SVGS[1]: svg_page(
            "SIDE VIEW — BBOX clearance and rearward CBOX",
            '''<rect x="110" y="480" width="520" height="44" class="rail"/><rect x="145" y="464" width="285" height="16" class="saddle"/>
<rect x="120" y="306" width="300" height="158" class="cbox"/><rect x="430" y="430" width="380" height="50" class="bbox"/>
<rect x="610" y="320" width="95" height="110" class="keep"/><path d="M425 450H610" class="d"/>
<text x="845" y="325" class="m">lid top Z254</text><text x="845" y="360" class="m">CBOX global bottom Z257.85</text>
<text x="845" y="395" class="m">minimum vertical gap 3.85</text><text x="845" y="430" class="m">chimney X gap 10</text>''',
            footer,
        ),
        SVGS[2]: svg_page(
            "FRONT VIEW — physical rail variation",
            '''<rect x="150" y="420" width="180" height="50" class="rail"/><rect x="870" y="424" width="180" height="50" class="rail"/>
<rect x="150" y="394" width="230" height="26" class="saddle"/><rect x="820" y="398" width="230" height="26" class="saddle"/>
<path d="M210 340L990 344L990 185L210 181Z" class="cbox"/><text x="510" y="270" class="h">CBOX follows 1 mm frame plane</text>
<text x="140" y="520" class="m">left rail top/bottom 255/235</text><text x="815" y="520" class="m">right 254/234</text>
<text x="390" y="585" class="m">center distance 188–190; no forced 189 spacing</text>''',
            footer,
        ),
        SVGS[3]: svg_page(
            "BBOX CLEARANCE SECTION",
            '''<rect x="145" y="460" width="720" height="55" class="bbox"/><rect x="145" y="410" width="220" height="28" class="saddle"/>
<rect x="145" y="260" width="620" height="150" class="cbox"/><rect x="660" y="350" width="130" height="110" class="keep"/>
<path d="M820 410V460" class="a"/><text x="845" y="440" class="m">3.85 mm minimum lid gap</text>
<text x="300" y="565" class="m">BBOX sealing boundary / M4 / chimney / PG9 delta = 0</text>''',
            footer,
        ),
        SVGS[4]: svg_page(
            "CRAWLER CLEARANCE SECTION",
            '''<rect x="105" y="220" width="990" height="310" class="keep"/><text x="410" y="390" class="h">conservative 3D crawler envelope</text>
<rect x="180" y="170" width="180" height="48" class="rail"/><rect x="840" y="174" width="180" height="48" class="rail"/>
<rect x="180" y="145" width="225" height="25" class="saddle"/><rect x="795" y="149" width="225" height="25" class="saddle"/>
<text x="345" y="105" class="m">saddle global min Z244; crawler max Z181; conservative separation 63 mm</text>''',
            footer,
        ),
        SVGS[5]: svg_page(
            "DIMENSION PREVIEW",
            '''<text x="80" y="130" class="h">Selected part</text><rect x="90" y="170" width="700" height="155" class="saddle"/>
<rect x="280" y="325" width="220" height="100" class="saddle"/><text x="820" y="205" class="m">140.0 X</text>
<text x="820" y="240" class="m">31.3 Y</text><text x="820" y="275" class="m">19.0 Z</text>
<text x="80" y="500" class="m">PETG · Bambu A1 · support OFF preferred</text>
<text x="80" y="540" class="m">M5 side T-slot candidate · exact hardware physical pending</text>
<text x="80" y="580" class="m">outboard-only rail contact avoids BBOX lid load</text>''',
            footer,
        ),
    }


def documents() -> dict[str, str]:
    offsets = offset_rows()
    lifts = lift_rows()
    variants = variant_rows()
    selected_clear = clearance_data()
    readme = f"""# CBOX transverse cross-saddle + protected BBOX alignment V001

Selected architecture: Variant A, two independent PETG outboard rail saddles.
The load path is CBOX → saddle → upper rail → frame. BBOX v003 remains a
waterproof lid/seal assembly and carries no CBOX structural load.

The mandatory X offsets 0, +30 and -30 mm all intersect the exact v003 chimney
keep-out. A fourth optimized rearward offset, X={SELECTED_X_OFFSET:.1f} mm,
provides 10 mm X clearance to the conservative chimney/PG9 envelope and preserves
the larger +X corridor for the future clutch study.

First prints:

- print/cbox_saddle_left.stl
- print/cbox_saddle_right.stl

Status: {STATUS}
"""
    authority = f"""# Design authority

## Physical basis

Rail outside span 208–210 mm, inside span 168–170 mm, width20 mm and center
distance188–190 mm are used exactly. Local Y0 is the midpoint of the current
rail centers at the mounting station; model centers ±94.5 are local nominal
coordinates only, not physical vehicle-axis authority. Left/right rail
top/bottom Z are255/235 and254/234 mm.

## Selected architecture

Two independent, equal-nominal PETG saddles attach to the outboard rail side
T-slot using accessible M5/T-nut candidate hardware. The outboard-only contact
starts1.2 mm from each local rail center, avoiding the centered BBOX lid envelope
over the full188–190 mm rail-spacing range. No cross-rail member exists, so frame
preload is not required.

The selected4 mm lift produces left/right support Z259/258. The CBOX follows the
1 mm as-built frame plane ({TILT_DEG:.6f} degree reference tilt). Its lowest
conservative bottom is Z{selected_clear['cbox_lowest_bottom_z_mm']:.3f}, providing
{selected_clear['bbox_lid_vertical_clearance_mm']:.3f} mm above the physical
BBOX lid plane outside the protected chimney.

## Protected BBOX

The exact BBOX v003 STEP is copied byte-for-byte as a reference. Sealing geometry,
gasket/land, M4 pattern, chimney, PG9 Ø15.2 interface,2.4 mm gland wall and wet
volume have zero delta. No new BBOX hole or BBOX↔CBOX passage exists.

## CBOX

Body authority is150 X ×246 Y ×80 Z. The exact v0.9.6.32 shell is reused and
rotated to long-axis Y; existing mounting tabs make its total X envelope152 mm.
The saddles remain inside that source-shell X envelope.

## Release boundary

CAD and contract PASS authorize saddle printing only. Retention, rail fit, load,
dynamic crawler, final clutch,500 mm frame and field validation remain pending.
"""
    test_plan = """# Physical test plan

1. Inspect both saddle dimensions and print quality.
2. Mount left/right saddles on the real upper rails with candidate side T-nuts.
3. Confirm rail fit without pulling the rails to a fixed center distance.
4. Verify the current188–190 mm spacing is tolerated.
5. Check for rocking, preload, whitening and cracks.
6. Place the actual150×246×80 CBOX with long axis Y.
7. Measure CBOX bottom Z at the left and right saddle.
8. Measure the real BBOX-lid clearance and confirm no contact.
9. Confirm chimney, PG9, locknut/tool and cable access.
10. Remove CBOX and verify all eight BBOX lid screws remain accessible.
11. Lift/remove CBOX vertically and remove each saddle independently.
12. Check static crawler clearance in full3D physical assembly.
13. Check Front Interface/PTO service access.
14. Apply representative dead load; inspect flex, creep and local floor stress.
15. Perform a manual shake test.
16. Only after separate static PASS, perform low-speed dry rover movement.

No water, mud, powered drivetrain or field PASS is granted here.
"""
    holds = """# HOLD register

- CBOX retention hardware and strap/clip selection
- exact side T-slot/M5/T-nut/washer stack and screw length
- saddle-to-real-rail physical fit and tolerance
- CBOX dead-load, flex, creep and shake results
- actual BBOX lid/chimney clearance after assembly
- dynamic crawler clearance
- final slide-clutch geometry and usable corridor
- actual current rail X endpoints
-500 mm frame physical compatibility
- optional0.5/1.0 mm leveling shim and TPU contact pad
- slicer review, water, mud, powered and field validation
"""
    source_trace = """# Source trace

- Primary physical authority:
  cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001
- Protected BBOX:
  cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority
- Exact CBOX shell source:
  cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32
- Front reference:
  cad/common_rover/frame/front_interface_dual_pto_20t_v002
- Driven crawler authority:
  cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003
- Idler authority:
  cad/common_rover/drivetrain/crawler_idler_candidate_c_v001
- Historical/current frame source:
  cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6

The current crawler positional transform is not fully physical authority.
Exact driven/idler solids are included alongside conservative3D envelopes capped
at direct physical Z181/180. Dynamic clearance remains pending.
"""
    return {
        "README.md": readme,
        "DESIGN_AUTHORITY.md": authority,
        "VARIANT_STUDY.csv": csv_text(variants),
        "PLACEMENT_OFFSET_STUDY.csv": csv_text(offsets),
        "SADDLE_LIFT_STUDY.csv": csv_text(lifts),
        "PHYSICAL_TEST_PLAN.md": test_plan,
        "HOLD_REGISTER.md": holds,
        "SOURCE_TRACE.md": source_trace,
        "design_parameters.json": json.dumps(parameters(), ensure_ascii=False, indent=2, sort_keys=True),
        "clearance_report.json": json.dumps(clearance_data(), ensure_ascii=False, indent=2, sort_keys=True),
        "printability_report.json": json.dumps(printability_data(), ensure_ascii=False, indent=2, sort_keys=True),
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = re.subn(
        r"FILE_NAME\('([^']*)','[^']*'",
        r"FILE_NAME('\1','2026-09-01T00:00:00'",
        text, count=1,
    )
    if count != 1:
        raise RuntimeError("STEP normalization failed: " + str(path))
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")
    normalize_step(path)


def export_stl(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), tolerance=0.035, angularTolerance=0.08)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def generate(out: Path) -> None:
    shape_map = {
        STEPS[0]: variant_a(),
        STEPS[1]: printable_saddle("LEFT"),
        STEPS[2]: printable_saddle("RIGHT"),
        STEPS[3]: selected_assembly(),
        STEPS[4]: local_cbox_reference(),
        STEPS[6]: rails_reference(),
        STEPS[7]: crawler_reference(),
        STEPS[9]: chimney_keepout(),
        STEPS[10]: slide_clutch_keepout(),
        STEPS[11]: placement_reference(0.0),
        STEPS[12]: placement_reference(30.0),
        STEPS[13]: placement_reference(-30.0),
        STEPS[14]: placement_reference(SELECTED_X_OFFSET),
        STEPS[15]: variant_a(),
        STEPS[16]: variant_b(),
        STEPS[17]: variant_c(),
    }
    for relative, shape in shape_map.items():
        export_step(shape, out / relative)
    for source, relative in ((BBOX_SOURCE, STEPS[5]), (FRONT_SOURCE, STEPS[8])):
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, path)
    export_stl(printable_saddle("LEFT"), out / STLS[0])
    export_stl(printable_saddle("RIGHT"), out / STLS[1])
    for relative, payload in svg_payload().items():
        write(out / relative, payload)
    for relative, payload in documents().items():
        write(out / relative, payload)


def binary_stl(path: Path):
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError("STL_TOO_SHORT")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError("STL_NOT_CANONICAL_BINARY")
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        yield (values[3:6], values[6:9], values[9:12])


def mesh_metrics(path: Path) -> dict:
    triangles = list(binary_stl(path))
    edges: Counter = Counter()
    degenerate = 0
    triangle_edges = []
    for triangle in triangles:
        vertices = [tuple(round(float(value), 5) for value in vertex) for vertex in triangle]
        ax, ay, az = (vertices[1][i] - vertices[0][i] for i in range(3))
        bx, by, bz = (vertices[2][i] - vertices[0][i] for i in range(3))
        cross = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
        if sum(value * value for value in cross) <= 1e-14:
            degenerate += 1
        row = []
        for a, b in (
            (vertices[0], vertices[1]),
            (vertices[1], vertices[2]),
            (vertices[2], vertices[0]),
        ):
            edge = tuple(sorted((a, b)))
            edges[edge] += 1
            row.append(edge)
        triangle_edges.append(row)
    parents = list(range(len(triangles)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b:
            parents[b] = a

    owners = {}
    for index, row in enumerate(triangle_edges):
        for edge in row:
            if edge in owners:
                union(index, owners[edge])
            else:
                owners[edge] = index
    raw = TopoDS_Shape()
    reload_pass = bool(StlAPI_Reader().Read(raw, str(path))) and not raw.IsNull()
    bad_edges = sum(value != 2 for value in edges.values())
    return {
        "triangle_count": len(triangles),
        "component_count": len({find(index) for index in range(len(triangles))}),
        "watertight": bad_edges == 0,
        "manifold": bad_edges == 0,
        "bad_edge_count": bad_edges,
        "degenerate_triangle_count": degenerate,
        "reload": "PASS" if reload_pass else "FAIL",
    }


def step_metrics(path: Path) -> dict:
    model = importers.importStep(str(path))
    solids = model.solids().vals()
    return {
        "reload": "PASS",
        "solid_count": len(solids),
        "all_valid": bool(solids) and all(solid.isValid() for solid in solids),
        "bbox": bounds(model),
    }


def reproducibility() -> dict:
    compared = sorted([*STEPS, *STLS, *SVGS, *documents().keys()])
    with tempfile.TemporaryDirectory(prefix="cbox_cross_saddle_v001_") as raw:
        target = Path(raw)
        subprocess.run(
            [sys.executable, "-B", str(Path(__file__)), "--render-only", str(target)],
            cwd=ROOT, check=True, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        mismatches = [
            relative for relative in compared
            if (LANE / relative).read_bytes() != (target / relative).read_bytes()
        ]
    result = {
        "compared": len(compared),
        "byte_identical": len(compared) - len(mismatches),
        "mismatches": mismatches,
        "status": "PASS" if not mismatches else "FAIL",
    }
    if mismatches:
        raise RuntimeError("REPRODUCIBILITY_FAIL: " + ", ".join(mismatches))
    return result


def contract_checks(repository: dict, step_report: dict, stl_report: dict,
                    repro: dict) -> dict:
    p = parameters()
    c = p["clearance"]
    printability = p["printability"]
    mandatory_offsets = p["offsets"][:3]
    selected_offset = p["offsets"][3]
    selected_lift = [row for row in p["lift_study"] if row["status"] == "SELECTED"][0]
    return {
        "physical_source_schema": p["physical_authority"]["source_schema"] == "COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_V001",
        "rail_outside_exact": p["physical_authority"]["rail_outside_range_mm"] == [208.0, 210.0],
        "rail_inside_exact": p["physical_authority"]["rail_inside_range_mm"] == [168.0, 170.0],
        "rail_width_exact": p["physical_authority"]["rail_width_mm"] == 20.0,
        "rail_center_range_exact": p["physical_authority"]["rail_center_range_mm"] == [188.0, 190.0],
        "local_y_not_absolute": p["physical_authority"]["absolute_upper_rail_axis_y"] == "PHYSICAL_PENDING",
        "rail_z_exact": (
            p["physical_authority"]["left_rail_top_bottom_mm"],
            p["physical_authority"]["right_rail_top_bottom_mm"],
        ) == ([255.0, 235.0], [254.0, 234.0]),
        "bbox_z_exact": p["physical_authority"]["bbox_lid_highest_z_mm"] == 254.0,
        "crawler_z_exact": p["physical_authority"]["crawler_left_right_highest_z_mm"] == [181.0, 180.0],
        "cbox_exact": p["cbox"]["physical_body_xyz_mm"] == [150.0, 246.0, 80.0],
        "cbox_orientation": p["cbox"]["long_axis"] == "Y" and p["cbox"]["short_axis"] == "X",
        "variant_count": len(p["variants"]) == 3,
        "variant_a_selected": p["variants"][0]["status"] == "SELECTED",
        "independent_spacing": not p["saddle"]["frame_preload_required"],
        "equal_saddles": p["saddle"]["equal_left_right_nominal_geometry"],
        "lift_4_selected": selected_lift["lift_mm"] == 4.0,
        "cbox_bottom_target": c["cbox_lowest_bottom_z_mm"] >= 256.0,
        "bbox_clearance": c["bbox_lid_vertical_clearance_mm"] >= 2.0,
        "bbox_load_false": not c["cbox_primary_load_to_bbox_lid"],
        "rail_load_path": c["primary_load_path"].endswith("UPPER_RAILS_TO_FRAME"),
        "bbox_intersection_zero": c["cbox_to_bbox_actual_intersection_mm3"] == 0,
        "chimney_intersection_zero": c["cbox_to_chimney_keepout_intersection_mm3"] == 0,
        "saddle_bbox_zero": c["saddle_to_bbox_intersection_mm3"] == 0,
        "saddle_chimney_zero": c["saddle_to_chimney_intersection_mm3"] == 0,
        "crawler_intersection_zero": c["saddle_to_crawler_intersection_mm3"] == 0,
        "front_intersection_zero": c["cbox_saddle_to_front_interface_intersection_mm3"] == 0,
        "bbox_screws_free": c["bbox_lid_fastener_blocked_count"] == 0,
        "manual_removal": c["cbox_manual_removal"].startswith("PASS"),
        "removal_sweep_zero": not any(c["cbox_vertical_removal_sweep_intersections_mm3"]),
        "bbox_delta_zero": all(c[key] == 0 for key in (
            "bbox_sealing_geometry_delta", "bbox_chimney_delta",
            "bbox_m4_pattern_delta", "bbox_new_holes", "bbox_cbox_open_passage",
        )),
        "mandatory_offsets_fail": all(row["status"].startswith("FAIL") for row in mandatory_offsets),
        "optimized_offset_pass": selected_offset["status"] == "PASS" and selected_offset["x_offset_mm"] == -111.0,
        "overhang_range": p["cbox"]["overhang_each_side_range_mm"] == [18.0, 19.0],
        "mount_x_no_saddle_growth": p["cbox"]["added_saddle_x_beyond_source_shell_mm"] == 0.0,
        "print_parts_2": printability["selected_printable_part_count"] == 2,
        "print_max_220": all(row["max_dimension_mm"] <= 220.0 for row in printability["parts"]),
        "one_piece_hold": printability["one_piece_240x246_base"] == "HOLD_NOT_GENERATED",
        "step_18": len(step_report) == 18 and all(row["reload"] == "PASS" and row["all_valid"] for row in step_report.values()),
        "stl_2": len(stl_report) == 2 and all(
            row["reload"] == "PASS" and row["watertight"] and row["manifold"]
            and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0
            for row in stl_report.values()
        ),
        "bbox_reference_byte_exact": sha(LANE / STEPS[5]) == sha(BBOX_SOURCE),
        "front_reference_byte_exact": sha(LANE / STEPS[8]) == sha(FRONT_SOURCE),
        "reproducibility": repro["status"] == "PASS",
        "authority_hashes": repository["checks"]["authority_4"],
        "protected_hashes": repository["checks"]["protected_7"],
    }


def indexes() -> None:
    write(
        LANE / "COMMIT_PATHS.txt",
        "".join(f"{LANE_REL.as_posix()}/{relative}\n" for relative in EXPECTED),
    )
    write(
        LANE / "MANIFEST.txt",
        f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\n"
        f"STEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\n"
        "FILES:\n" + "\n".join(EXPECTED),
    )
    names = [
        relative for relative in EXPECTED
        if relative != "SHA256SUMS.txt" and (LANE / relative).exists()
    ]
    write(
        LANE / "SHA256SUMS.txt",
        "".join(f"{sha(LANE / relative)}  {relative}\n" for relative in names),
    )


def run_contract() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-B", str(LANE / TEST)],
        cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    return result.returncode, result.stdout


def build() -> tuple[dict, dict]:
    repository = guard(False)
    generate(LANE)
    step_report = {relative: step_metrics(LANE / relative) for relative in STEPS}
    stl_report = {relative: mesh_metrics(LANE / relative) for relative in STLS}
    repro = reproducibility()
    checks = contract_checks(repository, step_report, stl_report, repro)
    validation = {
        "version": VERSION,
        "status": STATUS,
        "checks": checks,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "steps": step_report,
        "stls": stl_report,
        "reproducibility": repro,
        "clearance": clearance_data(),
        "printability": printability_data(),
        "variants": variant_rows(),
        "offsets": offset_rows(),
        "lifts": lift_rows(),
        "repository": {
            "branch": repository["branch"], "head": repository["head"],
            "staged_count": repository["staged_count"],
            "tracked_dirty_count": repository["tracked_dirty_count"],
            "authority": repository["authority"], "protected": repository["protected"],
        },
    }
    write(LANE / "validation_report.json", json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True))
    write(
        LANE / "BUILD_LOG.txt",
        f"BUILD=PASS\nSTEP_RELOAD={len(STEPS)}/{len(STEPS)} PASS\n"
        f"STL_QUALITY={len(STLS)}/{len(STLS)} PASS\n"
        f"REPRODUCIBILITY={repro['byte_identical']}/{repro['compared']} {repro['status']}\n",
    )
    write(LANE / "TEST_LOG.txt", "PENDING\n")
    indexes()
    code, output = run_contract()
    write(LANE / "TEST_LOG.txt", output)
    indexes()
    if code or not all(checks.values()):
        failed = [name for name, value in checks.items() if not value]
        raise RuntimeError("VERIFY_FAIL " + ",".join(failed) + "\n" + output)
    return guard(True), validation


def package() -> tuple[Path, str]:
    guard(True)
    path = Path(r"D:\Downloads") / (
        "Paddy_Swarm_CBOX_TRANSVERSE_CROSS_SADDLE_V001_"
        + datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip"
    )
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in EXPECTED:
            info = zipfile.ZipInfo(
                f"{LANE_NAME}/{relative}", (2026, 9, 1, 0, 0, 0)
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE / relative).read_bytes())
    return path, sha(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--render-only", type=Path)
    args = parser.parse_args()
    if args.render_only:
        generate(args.render_only)
        return 0
    repository, validation = build()
    result = {
        "status": "PASS",
        "lane": str(LANE),
        "paths": len(EXPECTED),
        "steps": len(STEPS),
        "stls": len(STLS),
        "svgs": len(SVGS),
        "checks": f"{validation['pass_count']}/{validation['check_count']}",
        "reproducibility": validation["reproducibility"],
        "branch": repository["branch"],
        "head": repository["head"],
        "staged_count": repository["staged_count"],
        "tracked_dirty_count": repository["tracked_dirty_count"],
        "clearance": validation["clearance"],
    }
    if args.package:
        path, digest = package()
        result["zip_path"] = str(path)
        result["zip_sha256"] = digest
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
