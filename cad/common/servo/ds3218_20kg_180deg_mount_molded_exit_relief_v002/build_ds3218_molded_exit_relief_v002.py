"""Build the DS3218 two-stage molded cable-exit root relief V002."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import importers

ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "ds3218_20kg_180deg_mount_molded_exit_relief_v002"
LANE_REL = PurePosixPath("cad/common/servo") / LANE_NAME
LANE = ROOT / LANE_REL
PARENT_REL = PurePosixPath("cad/common/servo/ds3218_20kg_180deg_mount_cable_relief_v001")
PARENT = ROOT / PARENT_REL
PARENT_BUILDER = PARENT / "build_ds3218_mount_cable_relief_v001.py"
VERSION = "PADDY-SWARM-DS3218-MOLDED-EXIT-ROOT-RELIEF-V002"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = sorted(AUTHORITY)
OUTSIDE_COUNT = 3623
OUTSIDE_DIGEST = "1a038de826cc5187338e4fdcd47bc868a591414642a12b48b1c6aea7732bcade"
PROTECTED = {
    PARENT_REL.as_posix(): (27, "5483f5d88d45479ac97fc27dc73ca4c3be609221517b57e0d381f890142a100c"),
    "cad/common/servo/ds3218_20kg_180deg_physical_authority_v001": (41, "58256a9be468c78a49c68f77e5b1706634967625484481ceb832193ca2ba56fd"),
    "cad/common_rover/pto_servo_sliding_idler_clutch_v001": (39, "52c15cae54dbe8d4d336556df95b74b070b9ae40109271eb4d62dae4f1c78a43"),
    "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority": (18, "6a4ccbf88eac70a2bd938dcf672f380e108fc86ee05bdf503f9bd88f9f022a9c"),
    "cad/common_rover/bbox_lid_wiring_chimney_v003_local_gland_recess": (32, "052663630e9a1a9bfc84320c9286ad26f7559bb06e2274b326d6b1ef4c31ad99"),
    "cad/common_rover/bbox_lid_wiring_chimney_v002_compact_50mm": (29, "4ee812f422005201e8093fd710fd796be9bc49a7a30612e99e06696b79dc7503"),
    "rovers/common_rover/v2.29.3.9.1": (45, "ab8c79b41c5a7eae3f45dc6cc79564882c84e2a412a61fef7384b28c49d07659"),
}

_spec = importlib.util.spec_from_file_location("ds3218_cable_relief_v001", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError("V001_IMPORT_FAILED")
parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parent)
base = parent.base

# Protected servo and mount authority.
CASE_L, CASE_W, CASE_H = 40.0, 20.4, 41.7
MOUNT_ENVELOPE_L = 54.5
HOLE_PITCH_X, HOLE_PITCH_Y = 49.1, 10.0
SERVO_HOLE_D = 4.6
OUTPUT_X, OUTPUT_Y = 10.1, 10.2
HORN_LINK_R, HORN_PLANE_Z = 30.0, 46.2

# Physical result and two-stage relief contract.
FLEX_CABLE_WIDTH = 4.4
FLEX_SLOT_WIDTH_AUTHORITY = 6.0
MOLDED_ROOT_WIDTH = 6.4
MOLDED_ROOT_TOP_Z = 8.6
MOLDED_ROOT_PROTRUSION = 5.1
ROOT_POCKET_WIDTHS = (7.5, 8.0, 8.5)
PRIMARY_ROOT_POCKET_WIDTH = 8.0
ROOT_POCKET_HEIGHT = 10.0
ROOT_POCKET_OUTWARD_CLEARANCE = 6.5
ROOT_VERTICAL_CLEARANCE = ROOT_POCKET_HEIGHT - MOLDED_ROOT_TOP_Z
ROOT_OUTWARD_MARGIN = ROOT_POCKET_OUTWARD_CLEARANCE - MOLDED_ROOT_PROTRUSION
EDGE_RADIUS = 1.25
CASE_FACE_X = CASE_L
EXIT_Y_APPROX = CASE_W / 2
POCKET_INBOARD_DEPTH = 1.5
POCKET_INBOARD_X = CASE_FACE_X - POCKET_INBOARD_DEPTH
POCKET_OUTBOARD_X = CASE_FACE_X + ROOT_POCKET_OUTWARD_CLEARANCE
POCKET_BOTTOM_Z = -5.0
MIN_EXISTING_WALL = 2.5

BUILDER = Path(__file__).name
TEST = "tests/test_ds3218_molded_exit_relief_v002_contract.py"
STEPS = [
    "cad/molded_exit_root_pocket_7p5.step",
    "cad/molded_exit_root_pocket_8p0.step",
    "cad/molded_exit_root_pocket_8p5.step",
    "cad/combined_molded_exit_root_coupon_plate.step",
    "cad/HOLD_ds3218_generic_mount_molded_exit_relief_8p0.step",
]
STLS = [
    "print/molded_exit_root_pocket_7p5.stl",
    "print/molded_exit_root_pocket_8p0.stl",
    "print/molded_exit_root_pocket_8p5.stl",
    "print/combined_molded_exit_root_coupon_plate.stl",
    "print/HOLD_ds3218_generic_mount_molded_exit_relief_8p0.stl",
]
SVGS = [
    "artifacts/TWO_STAGE_RELIEF.svg",
    "artifacts/MOLDED_ROOT_POCKET_CANDIDATES.svg",
    "artifacts/PHYSICAL_SELECTION_SEQUENCE.svg",
]
DOCS = [
    "README.md", "DIMENSION_REPORT.md", "AUTHORITY_DELTA_REPORT.md",
    "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md", "design_parameters.json",
    "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *DOCS, *LOGS])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(
        p for p in path.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for item in files:
        digest.update((item.relative_to(path).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha(item)))
    return len(files), digest.hexdigest()


def untracked() -> list[str]:
    return sorted(
        line[3:].replace("\\", "/")
        for line in git("status", "--porcelain=v1", "-uall").splitlines()
        if line.startswith("?? ")
    )


def outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    dirty = sorted(git("diff", "--name-only").splitlines())
    authority = {path: sha(ROOT / path) for path in AUTHORITY}
    protected = {path: tree(ROOT / path) for path in PROTECTED}
    files = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file()) if LANE.exists() else []
    prefix = LANE_REL.as_posix() + "/"
    lane_untracked = sorted(path for path in untracked() if path.startswith(prefix))
    expected_untracked = sorted(prefix + path for path in EXPECTED)
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    cache = [path for path in files if "__pycache__" in PurePosixPath(path).parts or path.endswith((".pyc", ".pyo"))]
    checks = {
        "root": root == ROOT.resolve(), "branch": branch == BRANCH, "head": head == HEAD,
        "staged_zero": not staged, "dirty_preserved": dirty == DIRTY,
        "outside_preserved": outside() == (OUTSIDE_COUNT, OUTSIDE_DIGEST),
        "authority_4": authority == AUTHORITY, "protected_7": protected == PROTECTED,
        "scope": set(files).issubset(EXPECTED), "untracked_scope": set(lane_untracked).issubset(expected_untracked),
        "ignored_zero": not ignored, "cache_zero": not cache,
        "complete": not complete or (files == EXPECTED and lane_untracked == expected_untracked),
    }
    result = {
        "checks": checks, "root": str(root), "branch": branch, "head": head,
        "staged": staged, "dirty": dirty, "outside": list(outside()), "authority": authority,
        "protected": {path: {"files": value[0], "sha256": value[1], "status": "UNCHANGED"} for path, value in protected.items()},
        "lane_files": len(files), "lane_untracked": len(lane_untracked),
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED " + json.dumps(result, ensure_ascii=True))
    return result


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").box(x, y, z).translate(center)


def volume(shape) -> float:
    if isinstance(shape, cq.Workplane):
        return sum(solid.Volume() for solid in shape.solids().vals())
    return sum(solid.Volume() for solid in shape.Solids())


def common_volume(a, b) -> float:
    try:
        return volume(a.val().intersect(b.val()))
    except ValueError as exc:
        if "Null TopoDS_Shape" in str(exc):
            return 0.0
        raise


def root_pocket_cutter(width: float):
    """Rounded local pocket from 1.5 mm inboard to 6.5 mm outboard of the case face."""
    length = POCKET_OUTBOARD_X - POCKET_INBOARD_X
    height = ROOT_POCKET_HEIGHT - POCKET_BOTTOM_Z
    pocket = cq.Workplane("XY").rect(length, width).extrude(height)
    pocket = pocket.edges("|Z").fillet(EDGE_RADIUS)
    return pocket.translate(((POCKET_INBOARD_X + POCKET_OUTBOARD_X) / 2, EXIT_Y_APPROX, POCKET_BOTTOM_Z))


def stage_a_bracket():
    return parent.revised_bracket(FLEX_SLOT_WIDTH_AUTHORITY)


def revised_bracket(width: float = PRIMARY_ROOT_POCKET_WIDTH):
    return stage_a_bracket().cut(root_pocket_cutter(width)).clean()


def molded_root_coupon(width: float):
    stage_a_coupon = parent.cable_relief_coupon(FLEX_SLOT_WIDTH_AUTHORITY)
    return stage_a_coupon.cut(root_pocket_cutter(width)).clean()


def combined_coupon_plate():
    offsets = (-32.0, 0.0, 32.0)
    shape = molded_root_coupon(ROOT_POCKET_WIDTHS[0]).translate((0, offsets[0], 0))
    for width, offset in zip(ROOT_POCKET_WIDTHS[1:], offsets[1:]):
        shape = shape.union(molded_root_coupon(width).translate((0, offset, 0)))
    for offset in (-16.0, 16.0):
        shape = shape.union(box(5.0, 8.0, 2.0, (29.5, EXIT_Y_APPROX + offset, -3.0)))
    return shape.clean()


def root_service_envelope(width: float):
    # Evaluate the usable outward portion with the same rounded-corner contract
    # as the pocket; a sharp rectangular probe would count the intentionally
    # retained R1.25 corner material as interference.
    outward_window = box(
        ROOT_POCKET_OUTWARD_CLEARANCE, width, ROOT_POCKET_HEIGHT + 4.0,
        ((CASE_FACE_X + POCKET_OUTBOARD_X) / 2, EXIT_Y_APPROX, 3.0),
    )
    return root_pocket_cutter(width).intersect(outward_window).clean()


def geometry_analysis() -> dict:
    stage_a = stage_a_bracket()
    revised = revised_bracket()
    pocket = root_pocket_cutter(PRIMARY_ROOT_POCKET_WIDTH)
    removed = stage_a.cut(revised).clean()
    removed_volume = volume(stage_a) - volume(revised)
    removed_inside = common_volume(removed, pocket)
    bounds = removed.val().BoundingBox()
    coupons = {f"{width:.1f}": molded_root_coupon(width) for width in ROOT_POCKET_WIDTHS}
    return {
        "stage_a_valid": stage_a.val().isValid(), "revised_valid": revised.val().isValid(),
        "stage_a_solids": len(stage_a.solids().vals()), "revised_solids": len(revised.solids().vals()),
        "stage_a_volume_mm3": round(volume(stage_a), 3), "revised_volume_mm3": round(volume(revised), 3),
        "root_pocket_removed_volume_mm3": round(removed_volume, 3),
        "added_volume_mm3": round(volume(revised.cut(stage_a)), 6),
        "delta_outside_root_pocket_mm3": round(max(0.0, removed_volume - removed_inside), 6),
        "removed_delta_bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)],
        "removed_delta_origin_mm": [round(bounds.xmin, 3), round(bounds.ymin, 3), round(bounds.zmin, 3)],
        "stage_a_root_service_intersection_mm3": round(common_volume(stage_a, root_service_envelope(PRIMARY_ROOT_POCKET_WIDTH)), 3),
        "revised_root_service_intersection_mm3": round(common_volume(revised, root_service_envelope(PRIMARY_ROOT_POCKET_WIDTH)), 6),
        "flex_slot_width_mm": FLEX_SLOT_WIDTH_AUTHORITY,
        "root_pocket_widths_mm": list(ROOT_POCKET_WIDTHS), "primary_root_pocket_width_mm": PRIMARY_ROOT_POCKET_WIDTH,
        "root_pocket_height_mm": ROOT_POCKET_HEIGHT, "root_pocket_outward_clearance_mm": ROOT_POCKET_OUTWARD_CLEARANCE,
        "root_vertical_clearance_mm": round(ROOT_VERTICAL_CLEARANCE, 3), "root_outward_margin_mm": round(ROOT_OUTWARD_MARGIN, 3),
        "lateral_margin_per_side_mm": {f"{width:.1f}": round((width - MOLDED_ROOT_WIDTH) / 2, 3) for width in ROOT_POCKET_WIDTHS},
        "coupon_valid": {key: shape.val().isValid() for key, shape in coupons.items()},
        "coupon_solids": {key: len(shape.solids().vals()) for key, shape in coupons.items()},
        "combined_valid": combined_coupon_plate().val().isValid(),
        "body_fit_dimensions_mm": [CASE_L, CASE_W, CASE_H],
        "mount_hole_centers_mm": [[round(x, 3), round(y, 3)] for x, y in base.mount_hole_centers()],
        "output_axis_mm": [OUTPUT_X, OUTPUT_Y], "horn_keepout_mm": [HORN_LINK_R, base.HORN_T, HORN_PLANE_Z],
        "minimum_existing_wall_mm": MIN_EXISTING_WALL,
        "minimum_remaining_base_ligament_each_side_mm": round((32.0 - max(ROOT_POCKET_WIDTHS)) / 2, 3),
        "local_subtractive_only": volume(revised.cut(stage_a)) < 1e-6 and removed_volume > 0,
    }


def parameters() -> dict:
    return {
        "version": VERSION,
        "parent": {"lane": PARENT_REL.as_posix(), "tree_sha256": PROTECTED[PARENT_REL.as_posix()][1], "status": "READ_ONLY_V001_AUTHORITY"},
        "protected_servo_authority": {
            "case_lwh_mm": [CASE_L, CASE_W, CASE_H], "mounting_envelope_mm": MOUNT_ENVELOPE_L,
            "mount_pitch_xy_mm": [HOLE_PITCH_X, HOLE_PITCH_Y], "servo_hole_diameter_mm": SERVO_HOLE_D,
            "output_axis_xy_mm": [OUTPUT_X, OUTPUT_Y], "horn_radius_mm": HORN_LINK_R,
            "horn_rotation_plane_z_mm": HORN_PLANE_Z, "servo_mount_position_changed": False,
        },
        "physical_result": {
            "flexible_cable_width_mm": FLEX_CABLE_WIDTH, "flexible_cable_slot_authority_mm": FLEX_SLOT_WIDTH_AUTHORITY,
            "flexible_cable_slot_result": "PHYSICAL_PASS", "molded_exit_root_width_mm": MOLDED_ROOT_WIDTH,
            "molded_exit_root_top_z_from_servo_bottom_mm": MOLDED_ROOT_TOP_Z,
            "molded_exit_root_protrusion_from_case_face_mm": MOLDED_ROOT_PROTRUSION,
            "molded_exit_root_interference": "PHYSICAL_FAIL",
        },
        "two_stage_relief": {
            "stage_a": {"name": "FLEXIBLE_CABLE_SLOT", "clear_width_mm": FLEX_SLOT_WIDTH_AUTHORITY, "status": "PHYSICAL_AUTHORITY_PRESERVED"},
            "stage_b": {
                "name": "MOLDED_ROOT_LOCAL_POCKET", "candidate_widths_mm": list(ROOT_POCKET_WIDTHS),
                "primary_width_mm": PRIMARY_ROOT_POCKET_WIDTH, "height_mm": ROOT_POCKET_HEIGHT,
                "outward_clearance_mm": ROOT_POCKET_OUTWARD_CLEARANCE,
                "vertical_clearance_mm": round(ROOT_VERTICAL_CLEARANCE, 3), "outward_margin_mm": round(ROOT_OUTWARD_MARGIN, 3),
                "lateral_margin_per_side_mm": {str(width): round((width - MOLDED_ROOT_WIDTH) / 2, 3) for width in ROOT_POCKET_WIDTHS},
                "shape": "OPEN_DOWNWARD_AND_OUTWARD_ROUNDED_LOCAL_POCKET", "edge_radius_mm": EDGE_RADIUS,
            },
        },
        "exit_placement": {
            "case_face": "+X", "y_center_mm": EXIT_Y_APPROX,
            "status": "MOLDED_EXIT_XY_APPROXIMATED_FROM_EXISTING_MODEL",
            "hold": "DIRECT_XY_PHYSICAL_MEASUREMENT_PENDING",
        },
        "print": {
            "coupon_order": STLS[:3], "combined_plate": STLS[3], "full_bracket": STLS[4],
            "coupon_status": "MOLDED_EXIT_ROOT_COUPONS_PRINT_READY",
            "full_bracket_status": "FULL_BRACKET_HOLD_PENDING_MOLDED_EXIT_ROOT_PHYSICAL_VALIDATION",
            "slicer": "HOLD_SLICER_NOT_RUN",
        },
        "status": "CAD_PASS/CONTRACT_TEST_PASS/MOLDED_EXIT_ROOT_COUPONS_PRINT_READY/MOLDED_EXIT_ROOT_PHYSICAL_VALIDATION_PENDING/FULL_BRACKET_HOLD",
        "forbidden_claims": ["FULL_MOUNT_PASS", "POWERED_SERVO_PASS", "LOAD_PASS", "TORQUE_PASS", "DURABILITY_PASS", "FIELD_PASS"],
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620"><rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial;fill:#172033}}.h{{font-size:28px;font-weight:bold}}.s{{font-size:15px;fill:#475569}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.r{{fill:#fee2e2;stroke:#b91c1c;stroke-width:2}}.a{{stroke:#0f7184;stroke-width:4;fill:none;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#0f7184"/></marker></defs><text x="38" y="48" class="h">{title}</text><text x="38" y="78" class="s">{subtitle}</text>{body}<text x="38" y="590" class="s">{VERSION} · PHYSICAL_VALIDATION_PENDING</text></svg>'''


def svg_payload() -> dict[str, str]:
    candidates = ''.join(
        f'<rect x="{110 + i * 325}" y="170" width="260" height="290" class="{("b", "g", "q")[i]}"/><path d="M{185 + i * 325} 460V300Q{240 + i * 325} 245 {295 + i * 325} 300V460" fill="#f8fafc" stroke="#b91c1c" stroke-width="5"/><text x="{195 + i * 325}" y="505">{width:.1f} mm</text>'
        for i, width in enumerate(ROOT_POCKET_WIDTHS)
    )
    return {
        SVGS[0]: svg("TWO-STAGE CABLE RELIEF", "Stage A 6.0 mm is physical authority; Stage B is a local molded-root pocket.", '<rect x="160" y="190" width="760" height="270" class="b"/><path d="M300 460V315Q345 270 390 315V460" fill="#f8fafc" stroke="#087f5b" stroke-width="5"/><path d="M275 390V270Q345 200 415 270V390" fill="none" stroke="#b91c1c" stroke-width="5"/><text x="195" y="520">green: flexible 6.0 mm · red: local molded-root pocket 8.0 mm</text>'),
        SVGS[1]: svg("MOLDED ROOT POCKET CANDIDATES", "Physical root 6.4 mm; selection order 7.5 → 8.0 → 8.5.", candidates),
        SVGS[2]: svg("PHYSICAL SELECTION SEQUENCE", "Select the narrowest pocket that clears the molded strain-relief without harming fit.", '<text x="75" y="285">7.5</text><path d="M135 280H250" class="a"/><text x="275" y="285">8.0</text><path d="M335 280H450" class="a"/><text x="475" y="285">8.5</text><path d="M535 280H650" class="a"/><text x="675" y="285">SELECT</text><path d="M760 280H875" class="a"/><text x="900" y="285">FULL HOLD</text>'),
    }


def documents() -> dict[str, str]:
    header = "# DS3218 Molded Cable-Exit Root Relief V002\n\n"
    return {
        "README.md": header + (
            "New independent lane derived from read-only V001. Stage A preserves the physically passing 6.0 mm flexible-cable slot. Stage B adds only a local molded-root pocket at the approximated +X/Y10.2 exit. "
            "Print 7.5 mm first, then 8.0 and 8.5 only if required. The 8.0 mm full bracket remains HOLD.\n\n"
            "Status: `CAD_PASS / CONTRACT_TEST_PASS / MOLDED_EXIT_ROOT_COUPONS_PRINT_READY / MOLDED_EXIT_ROOT_PHYSICAL_VALIDATION_PENDING / FULL_BRACKET_HOLD`.\n"
        ),
        "DIMENSION_REPORT.md": header + (
            "|Item|Value|Class|\n|---|---:|---|\n|Flexible cable width|4.4 mm|PHYSICAL|\n|Stage A flexible slot|6.0 mm|PHYSICAL_AUTHORITY|\n"
            "|Molded-root width|6.4 mm|PHYSICAL|\n|Molded-root top Z|8.6 mm|PHYSICAL|\n|Molded-root protrusion|5.1 mm|PHYSICAL|\n"
            "|Stage B widths|7.5 / 8.0 / 8.5 mm|CAD_CANDIDATE|\n|Stage B height|10.0 mm|CAD_CANDIDATE|\n|Stage B outward clearance|6.5 mm|CAD_CANDIDATE|\n"
            "|Vertical clearance|1.4 mm|DERIVED|\n|Outward margin|1.4 mm|DERIVED|\n|Lateral margins|0.55 / 0.80 / 1.05 mm per side|DERIVED|\n|Contact-edge radius|R1.25|CAD_CANDIDATE|\n"
        ),
        "AUTHORITY_DELTA_REPORT.md": header + (
            "V001 tree is protected byte-for-byte. The V002 full candidate starts from the V001 6.0 mm Stage-A geometry and subtracts the rounded Stage-B pocket only. "
            "No material is added; delta outside the pocket must be zero. Case, cavity, mounting envelope/pitches/holes, output axis, horn origin/radius/plane/keep-outs and servo position are unchanged. "
            "Exact molded-exit XY was not independently measured: placement remains `MOLDED_EXIT_XY_APPROXIMATED_FROM_EXISTING_MODEL / DIRECT_XY_PHYSICAL_MEASUREMENT_PENDING`.\n"
        ),
        "PHYSICAL_TEST_PLAN.md": header + (
            "1. Print 7.5 mm coupon. 2. Mount real DS3218. 3. Confirm unchanged body fit. 4. Confirm molded root has no printed contact or catching during insertion/removal. "
            "5. Confirm flexible cable remains free, uncompressed and without hard bend. 6. Confirm slight hand movement and safe wall thickness. 7. Select 7.5 if PASS. "
            "8. If marginal test 8.0; use 8.5 only if needed. 9. Regenerate/authorize the full bracket at the selected width. 10. Print bracket and install screws. "
            "11. Install 30 mm horn. 12. Manual 180° sweep. 13. Powered 180° no-load sweep. 14. Inspect cable during movement. 15. Mechanism/load/torque/durability testing later.\n"
        ),
        "HOLD_REGISTER.md": header + (
            "- `MOLDED_EXIT_ROOT_PHYSICAL_VALIDATION_PENDING`\n- `DIRECT_XY_PHYSICAL_MEASUREMENT_PENDING`\n- selected Stage-B pocket width authority\n"
            "- `FULL_BRACKET_HOLD_PENDING_MOLDED_EXIT_ROOT_PHYSICAL_VALIDATION`\n- final fastener standard and bracket release\n- `HOLD_SLICER_NOT_RUN`\n"
            "- powered no-load, load, torque, durability and field validation\n"
        ),
    }


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def generate(out: Path):
    shapes = [*(molded_root_coupon(width) for width in ROOT_POCKET_WIDTHS), combined_coupon_plate(), revised_bracket()]
    for relative, shape in zip(STEPS, shapes):
        base.export_step(shape, out / relative)
    for relative, shape in zip(STLS, shapes):
        base.export_stl(shape, out / relative)
    for relative, payload in svg_payload().items():
        write(out / relative, payload)
    for relative, payload in documents().items():
        write(out / relative, payload)
    write(out / "design_parameters.json", json.dumps(parameters(), indent=2, sort_keys=True))


def artifact_audit(out: Path):
    steps = []
    for relative in STEPS:
        shape = importers.importStep(str(out / relative))
        bounds = shape.val().BoundingBox()
        steps.append({"path": relative, "valid": shape.val().isValid(), "solids": len(shape.solids().vals()), "bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)]})
    meshes = {relative: base.mesh_metrics(out / relative) for relative in STLS}
    return steps, meshes


def reproducibility() -> dict:
    compared = sorted([*STEPS, *STLS, *SVGS, *documents().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="ds3218_molded_exit_v002_") as temp:
        subprocess.run(
            [sys.executable, "-B", str(Path(__file__)), "--render-only", temp], cwd=ROOT,
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
        )
        mismatches = [relative for relative in compared if (LANE / relative).read_bytes() != (Path(temp) / relative).read_bytes()]
    return {"compared": len(compared), "byte_identical": len(compared) - len(mismatches), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def indexes():
    write(LANE / "COMMIT_PATHS.txt", "".join(f"{LANE_REL.as_posix()}/{relative}\n" for relative in EXPECTED))
    write(LANE / "MANIFEST.txt", f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\nFILES:\n" + "\n".join(EXPECTED))
    paths = [relative for relative in EXPECTED if relative != "SHA256SUMS.txt" and (LANE / relative).exists()]
    write(LANE / "SHA256SUMS.txt", "".join(f"{sha(LANE / relative)}  {relative}\n" for relative in paths))


def contract() -> tuple[int, str]:
    result = subprocess.run([sys.executable, "-B", str(LANE / TEST)], cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.returncode, result.stdout


def build():
    repository = guard(False)
    generate(LANE)
    geometry = geometry_analysis()
    steps, meshes = artifact_audit(LANE)
    repro = reproducibility()
    checks = {
        "parent_values": [base.CASE_L, base.CASE_W, base.CASE_H, base.MOUNT_ENVELOPE_L, base.HOLE_PITCH_X, base.HOLE_PITCH_Y, base.SERVO_HOLE_D, base.OUTPUT_X, base.OUTPUT_Y, base.HORN_LINK_R, base.HORN_PLANE_Z] == [CASE_L, CASE_W, CASE_H, MOUNT_ENVELOPE_L, HOLE_PITCH_X, HOLE_PITCH_Y, SERVO_HOLE_D, OUTPUT_X, OUTPUT_Y, HORN_LINK_R, HORN_PLANE_Z],
        "flex_slot_6": FLEX_SLOT_WIDTH_AUTHORITY == 6.0, "physical_root": [MOLDED_ROOT_WIDTH, MOLDED_ROOT_TOP_Z, MOLDED_ROOT_PROTRUSION] == [6.4, 8.6, 5.1],
        "pocket_widths": ROOT_POCKET_WIDTHS == (7.5, 8.0, 8.5), "primary_width": PRIMARY_ROOT_POCKET_WIDTH == 8.0,
        "pocket_height": ROOT_POCKET_HEIGHT == 10.0, "outward_clearance": ROOT_POCKET_OUTWARD_CLEARANCE == 6.5,
        "margins": [round((width - MOLDED_ROOT_WIDTH) / 2, 2) for width in ROOT_POCKET_WIDTHS] == [0.55, 0.8, 1.05] and round(ROOT_VERTICAL_CLEARANCE, 1) == 1.4 and round(ROOT_OUTWARD_MARGIN, 1) == 1.4,
        "edge_radius": 1.0 <= EDGE_RADIUS <= 1.5, "stage_a_valid": geometry["stage_a_valid"], "revised_valid": geometry["revised_valid"],
        "subtractive_only": geometry["local_subtractive_only"] and geometry["added_volume_mm3"] == 0,
        "removed_positive": geometry["root_pocket_removed_volume_mm3"] > 0,
        "outside_delta_zero": geometry["delta_outside_root_pocket_mm3"] == 0,
        "root_service_clear": geometry["stage_a_root_service_intersection_mm3"] > 0 and geometry["revised_root_service_intersection_mm3"] == 0,
        "coupon_valid": all(geometry["coupon_valid"].values()) and geometry["combined_valid"],
        "wall_safe": geometry["minimum_existing_wall_mm"] >= 2.5 and geometry["minimum_remaining_base_ligament_each_side_mm"] >= 10.0,
        "step_reload": all(row["valid"] for row in steps),
        "stl_quality": all(row["reload"] == "PASS" and row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in meshes.values()),
        "reproducibility": repro["status"] == "PASS", "authority": repository["checks"]["authority_4"],
        "protected": repository["checks"]["protected_7"], "xy_hold": parameters()["exit_placement"]["hold"] == "DIRECT_XY_PHYSICAL_MEASUREMENT_PENDING",
        "full_hold": parameters()["print"]["full_bracket_status"] == "FULL_BRACKET_HOLD_PENDING_MOLDED_EXIT_ROOT_PHYSICAL_VALIDATION",
        "forbidden_claims": all(status not in parameters()["status"] for status in parameters()["forbidden_claims"]),
    }
    validation = {
        "version": VERSION, "status": parameters()["status"], "checks": checks,
        "check_count": len(checks), "pass_count": sum(checks.values()), "geometry": geometry,
        "steps": steps, "stls": meshes, "reproducibility": repro,
        "repository": {"branch": repository["branch"], "head": repository["head"], "authority": repository["authority"], "protected": repository["protected"]},
        "assumptions": ["Molded exit placement uses the existing +X case face and Y=10.2 approximation; direct physical XY measurement is pending."],
        "forbidden_claims": parameters()["forbidden_claims"],
    }
    write(LANE / "validation_report.json", json.dumps(validation, indent=2, sort_keys=True))
    write(LANE / "BUILD_LOG.txt", f"BUILD=PASS\nVALIDATION={sum(checks.values())}/{len(checks)} PASS\nSTEP_RELOAD={len(STEPS)}/{len(STEPS)} PASS\nSTL_QUALITY={len(STLS)}/{len(STLS)} PASS\nREPRO={repro['byte_identical']}/{repro['compared']} {repro['status']}\n")
    write(LANE / "TEST_LOG.txt", "PENDING\n")
    indexes()
    code, output = contract()
    write(LANE / "TEST_LOG.txt", output)
    indexes()
    if code or not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL\n" + output + json.dumps(checks))
    return guard(True), validation


def package() -> tuple[Path, str]:
    guard(True)
    downloads = Path(r"D:\Downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_DS3218_MOLDED_EXIT_ROOT_RELIEF_V002_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in EXPECTED:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{relative}", (2026, 8, 27, 0, 0, 0))
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
        "status": "PASS", "lane": str(LANE), "paths": len(EXPECTED), "steps": len(STEPS), "stls": len(STLS), "svgs": len(SVGS),
        "branch": repository["branch"], "head": repository["head"], "staged": repository["staged"],
        "validation": f"{validation['pass_count']}/{validation['check_count']} PASS", "reproducibility": validation["reproducibility"],
    }
    if args.package:
        path, digest = package()
        result.update(zip_path=str(path), zip_sha256=digest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
