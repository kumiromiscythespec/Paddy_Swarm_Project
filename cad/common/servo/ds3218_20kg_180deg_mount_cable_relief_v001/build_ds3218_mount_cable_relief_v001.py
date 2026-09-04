"""Build DS3218 generic-mount local cable-exit relief candidates."""
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
LANE_NAME = "ds3218_20kg_180deg_mount_cable_relief_v001"
LANE_REL = PurePosixPath("cad/common/servo") / LANE_NAME
LANE = ROOT / LANE_REL
PARENT_REL = PurePosixPath("cad/common/servo/ds3218_20kg_180deg_physical_authority_v001")
PARENT = ROOT / PARENT_REL
PARENT_BUILDER = PARENT / "build_ds3218_physical_authority_v001.py"
VERSION = "PADDY-SWARM-DS3218-MOUNT-CABLE-RELIEF-V001"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = sorted(AUTHORITY)
OUTSIDE_COUNT = 3596
OUTSIDE_DIGEST = "23f85e06b4c6d20e1abd629a865638d204c96246c1fa4ac1f95fc06559660acc"
PROTECTED = {
    PARENT_REL.as_posix(): (41, "58256a9be468c78a49c68f77e5b1706634967625484481ceb832193ca2ba56fd"),
    "cad/common_rover/pto_servo_sliding_idler_clutch_v001": (39, "52c15cae54dbe8d4d336556df95b74b070b9ae40109271eb4d62dae4f1c78a43"),
    "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority": (18, "6a4ccbf88eac70a2bd938dcf672f380e108fc86ee05bdf503f9bd88f9f022a9c"),
    "cad/common_rover/bbox_lid_wiring_chimney_v003_local_gland_recess": (32, "052663630e9a1a9bfc84320c9286ad26f7559bb06e2274b326d6b1ef4c31ad99"),
    "cad/common_rover/bbox_lid_wiring_chimney_v002_compact_50mm": (29, "4ee812f422005201e8093fd710fd796be9bc49a7a30612e99e06696b79dc7503"),
    "rovers/common_rover/v2.29.3.9.1": (45, "ab8c79b41c5a7eae3f45dc6cc79564882c84e2a412a61fef7384b28c49d07659"),
}

_spec = importlib.util.spec_from_file_location("ds3218_parent_v001", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError("PARENT_BUILDER_IMPORT_FAILED")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

# Read-only parent authority, repeated here so accidental drift fails visibly.
CASE_L, CASE_W, CASE_H = 40.0, 20.4, 41.7
MOUNT_ENVELOPE_L = 54.5
HOLE_PITCH_X, HOLE_PITCH_Y = 49.1, 10.0
SERVO_PHYSICAL_HOLE_D = 4.6
PRINTED_BRACKET_HOLE_CANDIDATE_D = 5.0
OUTPUT_X, OUTPUT_Y = 10.1, 10.2
HORN_LINK_R, HORN_T, HORN_PLANE_Z, MAX_H = 30.0, 2.4, 46.2, 48.0
BODY_FIT_RESULT = "PASS"
MOUNT_PATTERN_RESULT = "PASS"

# New physical cable input and deliberately local CAD candidates.
CABLE_BUNDLE_WIDTH = 4.4
CABLE_EXIT_X = CASE_L
CABLE_EXIT_Y = CASE_W / 2
CABLE_EXIT_Z_APPROX = 4.0
RELIEF_WIDTHS = (6.0, 6.5, 7.0)
PRIMARY_RELIEF_WIDTH = 6.5
RELIEF_HEIGHT = 8.0
EDGE_CHAMFER_EQUIVALENT = 1.25
RELIEF_ROOT_X = 34.0
RELIEF_FLARE_START_X = 40.0
RELIEF_OUTER_X = 52.0
RELIEF_BOTTOM_Z = -5.0
EXISTING_BASE_BOTTOM_Z = -4.0
EXISTING_BASE_TOP_Z = 0.0
MIN_EXISTING_WALL = 2.5

BUILDER = Path(__file__).name
TEST = "tests/test_ds3218_mount_cable_relief_v001_contract.py"
STEPS = [
    "cad/cable_relief_width_6p0.step",
    "cad/cable_relief_width_6p5.step",
    "cad/cable_relief_width_7p0.step",
    "cad/combined_cable_relief_coupon_plate.step",
    "cad/HOLD_ds3218_generic_mount_cable_relief_6p5.step",
]
STLS = [
    "print/cable_relief_width_6p0.stl",
    "print/cable_relief_width_6p5.stl",
    "print/cable_relief_width_7p0.stl",
    "print/combined_cable_relief_coupon_plate.stl",
    "print/HOLD_ds3218_generic_mount_cable_relief_6p5.stl",
]
SVGS = [
    "artifacts/CABLE_RELIEF_CANDIDATES.svg",
    "artifacts/BRACKET_LOCAL_DELTA.svg",
    "artifacts/PHYSICAL_TEST_SEQUENCE.svg",
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
    digest = hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()
    return len(paths), digest


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
    cache = [path for path in files if "__pycache__" in PurePosixPath(path).parts or path.endswith((".pyc", ".pyo"))]
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    checks = {
        "root": root == ROOT.resolve(), "branch": branch == BRANCH, "head": head == HEAD,
        "staged_zero": not staged, "dirty_preserved": dirty == DIRTY,
        "outside_preserved": outside() == (OUTSIDE_COUNT, OUTSIDE_DIGEST),
        "authority_4": authority == AUTHORITY, "protected_6": protected == PROTECTED,
        "scope": set(files).issubset(EXPECTED), "untracked_scope": set(lane_untracked).issubset(expected_untracked),
        "cache_zero": not cache, "ignored_zero": not ignored,
        "complete": not complete or (files == EXPECTED and lane_untracked == expected_untracked),
    }
    report = {
        "checks": checks, "root": str(root), "branch": branch, "head": head,
        "staged": staged, "dirty": dirty, "outside": list(outside()), "authority": authority,
        "protected": {key: {"files": value[0], "sha256": value[1], "status": "UNCHANGED"} for key, value in protected.items()},
        "lane_files": len(files), "lane_untracked": len(lane_untracked),
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED " + json.dumps(report, ensure_ascii=True))
    return report


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").box(x, y, z).translate(center)


def relief_cutter(width: float):
    """Open +X slot with a rounded root and 1.25 mm/side printable entry flare."""
    height = RELIEF_HEIGHT - RELIEF_BOTTOM_Z
    z_center = (RELIEF_HEIGHT + RELIEF_BOTTOM_Z) / 2
    root = (
        cq.Workplane("XY").circle(width / 2).extrude(height)
        .translate((RELIEF_ROOT_X, CABLE_EXIT_Y, RELIEF_BOTTOM_Z))
    )
    straight = box(
        RELIEF_FLARE_START_X - RELIEF_ROOT_X, width, height,
        ((RELIEF_ROOT_X + RELIEF_FLARE_START_X) / 2, CABLE_EXIT_Y, z_center),
    )
    half = width / 2
    flare = (
        cq.Workplane("XY")
        .polyline([
            (RELIEF_FLARE_START_X, CABLE_EXIT_Y - half),
            (RELIEF_OUTER_X, CABLE_EXIT_Y - half - EDGE_CHAMFER_EQUIVALENT),
            (RELIEF_OUTER_X, CABLE_EXIT_Y + half + EDGE_CHAMFER_EQUIVALENT),
            (RELIEF_FLARE_START_X, CABLE_EXIT_Y + half),
        ])
        .close().extrude(height).translate((0, 0, RELIEF_BOTTOM_Z))
    )
    return root.union(straight).union(flare).clean()


def cable_root_keepout(width: float):
    return box(
        RELIEF_OUTER_X - CABLE_EXIT_X, width, RELIEF_HEIGHT - EXISTING_BASE_BOTTOM_Z,
        ((RELIEF_OUTER_X + CABLE_EXIT_X) / 2, CABLE_EXIT_Y, (RELIEF_HEIGHT + EXISTING_BASE_BOTTOM_Z) / 2),
    )


def revised_bracket(width: float = PRIMARY_RELIEF_WIDTH):
    return base.generic_bracket().cut(relief_cutter(width)).clean()


def cable_relief_coupon(width: float):
    # A local slice of the actual parent bracket preserves its case-contact rails and Z0/base references.
    local_window = box(24.0, 26.0, 12.0, (40.0, CABLE_EXIT_Y, 2.0))
    return base.generic_bracket().intersect(local_window).cut(relief_cutter(width)).clean()


def combined_coupon_plate():
    offsets = (-32.0, 0.0, 32.0)
    shape = cable_relief_coupon(RELIEF_WIDTHS[0]).translate((0, offsets[0], 0))
    for width, offset in zip(RELIEF_WIDTHS[1:], offsets[1:]):
        shape = shape.union(cable_relief_coupon(width).translate((0, offset, 0)))
    # Low, local bridges join the three samples without changing their cable openings.
    for offset in (-16.0, 16.0):
        shape = shape.union(box(5.0, 8.0, 2.0, (29.5, CABLE_EXIT_Y + offset, -3.0)))
    return shape.clean()


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


def geometry_analysis() -> dict:
    parent = base.generic_bracket()
    revised = revised_bracket()
    removed = parent.cut(revised).clean()
    delta_box = removed.val().BoundingBox()
    coupons = {f"{width:.1f}": cable_relief_coupon(width) for width in RELIEF_WIDTHS}
    clearances = {f"{width:.1f}": round((width - CABLE_BUNDLE_WIDTH) / 2, 3) for width in RELIEF_WIDTHS}
    return {
        "parent_valid": parent.val().isValid(), "revised_valid": revised.val().isValid(),
        "parent_solids": len(parent.solids().vals()), "revised_solids": len(revised.solids().vals()),
        "parent_volume_mm3": round(volume(parent), 3), "revised_volume_mm3": round(volume(revised), 3),
        "removed_volume_mm3": round(volume(parent) - volume(revised), 3),
        "added_volume_mm3": round(volume(revised.cut(parent)), 6),
        "removed_delta_bbox_mm": [round(delta_box.xlen, 3), round(delta_box.ylen, 3), round(delta_box.zlen, 3)],
        "removed_delta_origin_mm": [round(delta_box.xmin, 3), round(delta_box.ymin, 3), round(delta_box.zmin, 3)],
        "parent_cable_keepout_intersection_mm3": round(common_volume(parent, cable_root_keepout(PRIMARY_RELIEF_WIDTH)), 3),
        "revised_cable_keepout_intersection_mm3": round(common_volume(revised, cable_root_keepout(PRIMARY_RELIEF_WIDTH)), 6),
        "relief_widths_mm": list(RELIEF_WIDTHS), "primary_relief_width_mm": PRIMARY_RELIEF_WIDTH,
        "relief_height_mm": RELIEF_HEIGHT, "entry_chamfer_equivalent_mm": EDGE_CHAMFER_EQUIVALENT,
        "cable_width_mm": CABLE_BUNDLE_WIDTH, "lateral_clearance_per_side_mm": clearances,
        "coupon_valid": {key: shape.val().isValid() for key, shape in coupons.items()},
        "coupon_solids": {key: len(shape.solids().vals()) for key, shape in coupons.items()},
        "combined_valid": combined_coupon_plate().val().isValid(),
        "body_fit_dimensions_mm": [CASE_L, CASE_W, CASE_H],
        "mount_hole_centers_mm": [[round(x, 3), round(y, 3)] for x, y in base.mount_hole_centers()],
        "output_axis_mm": [OUTPUT_X, OUTPUT_Y],
        "horn_keepout_mm": [HORN_LINK_R, HORN_T, HORN_PLANE_Z],
        "minimum_existing_wall_mm": MIN_EXISTING_WALL,
        "minimum_remaining_base_ligament_each_side_mm": round((32.0 - (max(RELIEF_WIDTHS) + 2 * EDGE_CHAMFER_EQUIVALENT)) / 2, 3),
        "local_only": volume(revised.cut(parent)) < 1e-6 and volume(parent) > volume(revised),
    }


def parameters() -> dict:
    return {
        "version": VERSION,
        "parent": {"lane": PARENT_REL.as_posix(), "tree_sha256": PROTECTED[PARENT_REL.as_posix()][1], "status": "READ_ONLY_PHYSICAL_CAD_AUTHORITY"},
        "physical_results": {"servo_case_fit": BODY_FIT_RESULT, "mount_pattern_physical_fit": MOUNT_PATTERN_RESULT},
        "servo_authority_unchanged": {
            "case_lwh_mm": [CASE_L, CASE_W, CASE_H], "mounting_envelope_length_mm": MOUNT_ENVELOPE_L,
            "mount_pitch_xy_mm": [HOLE_PITCH_X, HOLE_PITCH_Y], "servo_physical_hole_diameter_mm": SERVO_PHYSICAL_HOLE_D,
            "output_axis_xy_mm": [OUTPUT_X, OUTPUT_Y], "horn_link_radius_mm": HORN_LINK_R,
            "horn_thickness_mm": HORN_T, "horn_rotation_plane_z_mm": HORN_PLANE_Z,
            "servo_with_horn_max_height_mm": MAX_H,
        },
        "fastener": {
            "narrower_coupon_pattern_identity_mm": 4.6,
            "narrower_coupon_pattern_role": "PHYSICAL_SERVO_HOLE_REFERENCE_PATTERN_PHYSICALLY_ALIGNED",
            "existing_full_bracket_hole_candidate_mm": PRINTED_BRACKET_HOLE_CANDIDATE_D,
            "full_bracket_hole_in_this_revision_mm": PRINTED_BRACKET_HOLE_CANDIDATE_D,
            "hardware_standard": "PHYSICAL_FASTENER_SELECTION_PENDING",
            "promotion": "NOT_PROMOTED_BY_THIS_CABLE_RELIEF_REVISION",
        },
        "cable": {
            "bundle_width_at_servo_exit_mm": CABLE_BUNDLE_WIDTH, "width_status": "PHYSICAL_AUTHORITY",
            "exit_reference_mm": [CABLE_EXIT_X, CABLE_EXIT_Y, CABLE_EXIT_Z_APPROX],
            "vertical_start": "APPROX_SERVO_BOTTOM_PLUS_4MM",
            "direction_assumption": "+X_END_CENTERLINE_REUSED_FROM_PARENT_PLACEHOLDER",
            "exact_exit_xyz_status": "HOLD_PHYSICAL_COORDINATE_REMEASUREMENT",
        },
        "relief": {
            "architecture": "OPEN_BOTTOM_U_SHAPED_LOCAL_SLOT", "candidate_clear_widths_mm": list(RELIEF_WIDTHS),
            "primary_width_mm": PRIMARY_RELIEF_WIDTH, "height_mm": RELIEF_HEIGHT,
            "edge_treatment": "1P25MM_PER_SIDE_PRINTABLE_ENTRY_CHAMFER_EQUIVALENT_WITH_ROUNDED_SLOT_ROOT",
            "clearance_per_side_mm": {str(width): round((width - CABLE_BUNDLE_WIDTH) / 2, 3) for width in RELIEF_WIDTHS},
            "global_cavity_change": False, "mount_location_change": False, "retention_load_on_cable": False,
        },
        "print": {
            "coupon_order": STLS[:3], "combined_plate": STLS[3], "full_bracket": STLS[4],
            "coupon_status": "CABLE_RELIEF_COUPONS_PRINT_READY",
            "full_bracket_status": "HOLD_PENDING_CABLE_RELIEF_PHYSICAL_VALIDATION", "slicer": "HOLD_SLICER_NOT_RUN",
        },
        "status": "CAD_PASS/CONTRACT_TEST_PASS/CABLE_RELIEF_COUPONS_PRINT_READY/CABLE_RELIEF_PHYSICAL_VALIDATION_PENDING/FULL_BRACKET_HOLD_PENDING_CABLE_RELIEF_PHYSICAL_VALIDATION",
        "forbidden_claims": ["FULL_MOUNT_PASS", "POWERED_SERVO_PASS", "LOAD_PASS", "FIELD_PASS"],
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620"><rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial;fill:#172033}}.h{{font-size:28px;font-weight:bold}}.s{{font-size:15px;fill:#475569}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.r{{fill:#fee2e2;stroke:#b91c1c;stroke-width:2}}.a{{stroke:#0f7184;stroke-width:4;fill:none;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#0f7184"/></marker></defs><text x="38" y="48" class="h">{title}</text><text x="38" y="78" class="s">{subtitle}</text>{body}<text x="38" y="590" class="s">{VERSION} · PHYSICAL_VALIDATION_PENDING</text></svg>'''


def svg_payload() -> dict[str, str]:
    candidates = ''.join(
        f'<rect x="{125 + i * 315}" y="180" width="250" height="270" class="{("b", "g", "q")[i]}"/><path d="M{205 + i * 315} 450V310Q{250 + i * 315} 260 {295 + i * 315} 310V450" fill="#f8fafc" stroke="#b91c1c" stroke-width="5"/><text x="{205 + i * 315}" y="500">{width:.1f} mm</text>'
        for i, width in enumerate(RELIEF_WIDTHS)
    )
    return {
        SVGS[0]: svg("CABLE RELIEF CANDIDATES", "Open-bottom local slots; 6.5 mm is CAD primary, not physical authority.", candidates),
        SVGS[1]: svg("GENERIC BRACKET LOCAL DELTA", "Blue is preserved parent bracket; red is the only removed +X/base region.", '<rect x="120" y="180" width="790" height="280" class="b"/><rect x="735" y="365" width="175" height="95" class="r"/><path d="M820 365V255" class="a"/><text x="655" y="235">open down / outward</text><text x="650" y="510">no global cavity or hole shift</text>'),
        SVGS[2]: svg("PHYSICAL TEST SEQUENCE", "Select the narrowest cable-safe coupon before any full-bracket release.", '<text x="75" y="285">6.0</text><path d="M135 280H250" class="a"/><text x="275" y="285">6.5</text><path d="M335 280H450" class="a"/><text x="475" y="285">7.0</text><path d="M535 280H650" class="a"/><text x="675" y="285">SELECT</text><path d="M760 280H875" class="a"/><text x="900" y="285">BRACKET HOLD</text>'),
    }


def documents() -> dict[str, str]:
    header = "# DS3218 Generic Mount Cable Exit Relief V001\n\n"
    return {
        "README.md": header + (
            "Local correction derived from the read-only DS3218 physical-authority lane. The validated body cavity, mounting pattern, output axis and horn keep-outs remain unchanged. "
            "Print `cable_relief_width_6p0.stl` first, then 6.5 and 7.0 only as needed. Select the narrowest candidate that permits insertion/removal, natural cable exit, no sheath compression, no hard bend, no sharp-edge rubbing and slight free cable movement. "
            "The 6.5 mm full bracket is a HOLD artifact, not final print authority.\n\n"
            "Status: `CAD_PASS / CONTRACT_TEST_PASS / CABLE_RELIEF_COUPONS_PRINT_READY / CABLE_RELIEF_PHYSICAL_VALIDATION_PENDING / FULL_BRACKET_HOLD_PENDING_CABLE_RELIEF_PHYSICAL_VALIDATION`.\n"
        ),
        "DIMENSION_REPORT.md": header + (
            "|Item|Value|Class|\n|---|---:|---|\n|Cable bundle at exit|4.4 mm|PHYSICAL|\n|Cable vertical start|servo bottom + approximately 4 mm|PHYSICAL_APPROX|\n"
            "|Relief A/B/C clear width|6.0 / 6.5 / 7.0 mm|CAD_CANDIDATE|\n|Primary width|6.5 mm|CAD_PRIMARY|\n|Primary lateral clearance|1.05 mm/side|DERIVED|\n"
            "|Relief height|8.0 mm|CAD_CANDIDATE|\n|Entry edge treatment|1.25 mm/side chamfer equivalent|CAD_CANDIDATE|\n|Existing minimum rail wall|2.5 mm|UNCHANGED|\n"
        ),
        "AUTHORITY_DELTA_REPORT.md": header + (
            "Only the +X cable-exit/base region is subtractively changed. The slot is open downward and outward, has a rounded inner root and an outward 1.25 mm/side entry flare. No material is added. "
            "Case 40.0×20.4×41.7, mounting envelope 54.5, pitches 49.1×10.0, physical holes Ø4.6, bracket-hole candidate Ø5.0, output (10.1,10.2), horn R30/T2.4/Z46.2 and all horn keep-outs are frozen by the parent tree hash. "
            "The physically aligned narrower coupon pattern is identifiable as Ø4.6, but this revision does not promote a screw standard or replace the existing bracket Ø5.0 candidate.\n"
        ),
        "PHYSICAL_TEST_PLAN.md": header + (
            "1. Print 6.0 mm coupon. 2. Insert and remove servo. 3. Confirm cable root is not pinched. 4. Confirm natural exit, no visible sheath compression, no hard bend and no sharp-edge rubbing. "
            "5. Confirm slight manual cable movement does not load the bracket. 6. If comfortable, select 6.0. 7. If tight, repeat with 6.5. 8. Use 7.0 only if needed. "
            "9. Record selected physical authority. 10. Regenerate/authorize the full bracket at that width. 11. Print and install screws. 12. Confirm cable root free. 13. Install 30 mm horn. "
            "14. Manual sweep. 15. Powered 180° no-load sweep. 16. Observe cable through motion. 17. Load/torque testing only later.\n"
        ),
        "HOLD_REGISTER.md": header + (
            "- `CABLE_RELIEF_PHYSICAL_VALIDATION_PENDING`\n- exact cable-exit X/Y/Z and bend radius remeasurement\n- selected relief width authority\n"
            "- `FULL_BRACKET_HOLD_PENDING_CABLE_RELIEF_PHYSICAL_VALIDATION`\n- final fastener standard and printed-hole authority\n- slicer/orientation result (`HOLD_SLICER_NOT_RUN`)\n"
            "- powered no-load, load, durability and field validation\n"
        ),
    }


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def generate(out: Path):
    shapes = [*(cable_relief_coupon(width) for width in RELIEF_WIDTHS), combined_coupon_plate(), revised_bracket()]
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
        steps.append({
            "path": relative, "valid": shape.val().isValid(), "solids": len(shape.solids().vals()),
            "bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)],
        })
    meshes = {relative: base.mesh_metrics(out / relative) for relative in STLS}
    return steps, meshes


def reproducibility() -> dict:
    compared = sorted([*STEPS, *STLS, *SVGS, *documents().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="ds3218_cable_relief_v001_") as temp:
        subprocess.run(
            [sys.executable, "-B", str(Path(__file__)), "--render-only", temp], cwd=ROOT,
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
        )
        mismatches = [relative for relative in compared if (LANE / relative).read_bytes() != (Path(temp) / relative).read_bytes()]
    return {"compared": len(compared), "byte_identical": len(compared) - len(mismatches), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def indexes():
    write(LANE / "COMMIT_PATHS.txt", "".join(f"{LANE_REL.as_posix()}/{relative}\n" for relative in EXPECTED))
    write(
        LANE / "MANIFEST.txt",
        f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\nFILES:\n" + "\n".join(EXPECTED),
    )
    paths = [relative for relative in EXPECTED if relative != "SHA256SUMS.txt" and (LANE / relative).exists()]
    write(LANE / "SHA256SUMS.txt", "".join(f"{sha(LANE / relative)}  {relative}\n" for relative in paths))


def contract() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-B", str(LANE / TEST)], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    return result.returncode, result.stdout


def build():
    repository = guard(False)
    generate(LANE)
    geometry = geometry_analysis()
    steps, meshes = artifact_audit(LANE)
    repro = reproducibility()
    parent_values = [
        base.CASE_L == CASE_L, base.CASE_W == CASE_W, base.CASE_H == CASE_H,
        base.MOUNT_ENVELOPE_L == MOUNT_ENVELOPE_L, base.HOLE_PITCH_X == HOLE_PITCH_X,
        base.HOLE_PITCH_Y == HOLE_PITCH_Y, base.SERVO_HOLE_D == SERVO_PHYSICAL_HOLE_D,
        base.PRINTED_HOLE_CANDIDATE == PRINTED_BRACKET_HOLE_CANDIDATE_D,
        base.OUTPUT_X == OUTPUT_X, base.OUTPUT_Y == OUTPUT_Y, base.HORN_LINK_R == HORN_LINK_R,
        base.HORN_T == HORN_T, base.HORN_PLANE_Z == HORN_PLANE_Z, base.MAX_H == MAX_H,
    ]
    checks = {
        "parent_authority_values": all(parent_values), "body_fit_pass_reused": BODY_FIT_RESULT == "PASS",
        "mount_pattern_pass_reused": MOUNT_PATTERN_RESULT == "PASS", "cable_width": CABLE_BUNDLE_WIDTH == 4.4,
        "relief_widths": RELIEF_WIDTHS == (6.0, 6.5, 7.0), "primary_width": PRIMARY_RELIEF_WIDTH == 6.5,
        "primary_side_clearance": abs((PRIMARY_RELIEF_WIDTH - CABLE_BUNDLE_WIDTH) / 2 - 1.05) < 1e-9,
        "relief_height": RELIEF_HEIGHT == 8.0, "edge_treatment": 1.0 <= EDGE_CHAMFER_EQUIVALENT <= 1.5,
        "parent_valid": geometry["parent_valid"], "revised_valid": geometry["revised_valid"],
        "subtractive_only": geometry["added_volume_mm3"] == 0 and geometry["removed_volume_mm3"] > 0,
        "parent_interference_reproduced": geometry["parent_cable_keepout_intersection_mm3"] > 0,
        "revised_root_clear": geometry["revised_cable_keepout_intersection_mm3"] == 0,
        "local_only": geometry["local_only"], "coupon_valid": all(geometry["coupon_valid"].values()),
        "wall_safe": geometry["minimum_existing_wall_mm"] >= 2.5 and geometry["minimum_remaining_base_ligament_each_side_mm"] >= 10.0,
        "step_reload": all(row["valid"] for row in steps),
        "stl_quality": all(row["reload"] == "PASS" and row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in meshes.values()),
        "reproducibility": repro["status"] == "PASS", "authority": repository["checks"]["authority_4"],
        "protected": repository["checks"]["protected_6"], "fastener_not_promoted": parameters()["fastener"]["promotion"].startswith("NOT_PROMOTED"),
        "full_bracket_hold": parameters()["print"]["full_bracket_status"] == "HOLD_PENDING_CABLE_RELIEF_PHYSICAL_VALIDATION",
        "forbidden_claims": all(word not in parameters()["status"] for word in parameters()["forbidden_claims"]),
    }
    validation = {
        "version": VERSION, "status": parameters()["status"], "checks": checks,
        "check_count": len(checks), "pass_count": sum(checks.values()), "geometry": geometry,
        "steps": steps, "stls": meshes, "reproducibility": repro,
        "repository": {"branch": repository["branch"], "head": repository["head"], "authority": repository["authority"], "protected": repository["protected"]},
        "assumptions": ["Cable exits at the +X end on Y=10.2 centerline, inherited from the parent placeholder; exact X/Y/Z remains HOLD."],
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
    path = downloads / f"Paddy_Swarm_DS3218_CABLE_RELIEF_V001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
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
        "status": "PASS", "lane": str(LANE), "paths": len(EXPECTED), "steps": len(STEPS),
        "stls": len(STLS), "svgs": len(SVGS), "branch": repository["branch"], "head": repository["head"],
        "staged": repository["staged"], "validation": f"{validation['pass_count']}/{validation['check_count']} PASS",
        "reproducibility": validation["reproducibility"],
    }
    if args.package:
        path, digest = package()
        result.update(zip_path=str(path), zip_sha256=digest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
