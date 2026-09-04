"""Build the MISUMI Groove-1 authority full driven-wheel carrier V001."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
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
LANE_NAME = "misumi_pulley_groove1_full_driven_carrier_v001"
LANE_REL = PurePosixPath("cad/common_rover/drivetrain") / LANE_NAME
LANE = ROOT / LANE_REL
AUTH_REL = PurePosixPath("cad/common_rover/common_rover_p5m28_exact_vendor_core_fit_coupon_v0_9_6_34")
AUTH_LANE = ROOT / AUTH_REL
AUTH_BUILDER = AUTH_LANE / "build_p5m28_exact_vendor_core_fit_coupon_v0_9_6_34.py"
VERSION = "PADDY-SWARM-MISUMI-GROOVE1-FULL-DRIVEN-CARRIER-V001"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = sorted(AUTHORITY)
OUTSIDE_COUNT = 3682
OUTSIDE_DIGEST = "ec726ca2bd89829485687b95b78500579992397be790ac5f907f0e256c66a907"
PROTECTED = {
    AUTH_REL.as_posix(): (36, "121ae43e71aa732e601e67595401284f8953e4f55bde71dbd3340646e452451d"),
    "cad/common_rover/common_rover_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31": (20, "8065cefb36cef1dfb823a989185a67534f7eebdfd432fd5a664b364cc9053a72"),
    "cad/common_rover/common_rover_p20653_14t_18025_full_width_through_bolt_drive_v0_9_6_30": (69, "8ac79a2b4dadeb6a8584e8949e190e62fd74cdb4299dee0276be0c14e7513cd2"),
    "cad/common_rover/common_rover_drive_entry_top_hold_down_roller_v0_9_6_19": (39, "e632689b54678455adec6758b2420bcf0ed4a2bd8ade8d229d80087275a4630e"),
    "cad/common/servo/ds3218_20kg_180deg_mount_molded_exit_relief_v002": (27, "5b41936960958df146933f6e2da8d443891ccf4ca37c85c60d0feb7893f78c88"),
}

_spec = importlib.util.spec_from_file_location("p5m28_groove_authority", AUTH_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError("GROOVE_AUTHORITY_IMPORT_FAILED")
authority = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(authority)
# Use the protected repository copy, not a mutable external download location.
authority.SOURCE_ZIP = AUTH_LANE / "source/vendor/PTPK28P5M150-A-N10-NFC_STEP.zip"
for cached in (
    authority.source_step_bytes, authority.vendor_assembly, authority.main_solid,
    authority.exact_outer_wire, authority.exact_profile_solid_z,
):
    cached.cache_clear()

# Exact imported authority.
GROOVE_CODE = "C1"
GROOVE_CLEARANCE = authority.CLEARANCES[GROOVE_CODE]
P5M_PITCH = authority.P5M28_PITCH_MM
P5M_TOOTH_COUNT = authority.P5M28_TOOTH_COUNT
METAL_TIP_OD = 43.42
METAL_ROOT_OD = 39.80
METAL_BODY_WIDTH = authority.MAIN_AXIAL_WIDTH_MM
METAL_TOOTH_WIDTH = authority.TOOTH_ZONE_WIDTH_MM
COUPON_ENGAGEMENT = authority.COUPON_ENGAGEMENT_MM
SOURCE_STEP_SHA256 = authority.SOURCE_STEP_SHA256
SOURCE_ZIP_SHA256 = authority.SOURCE_ZIP_SHA256

# P20653 outer driven-wheel carrier and serviceable axial package.
OUTER_TOOTH_COUNT = authority.P20653["tooth_count"]
OUTER_PITCH = authority.P20653["pitch_mm"]
OUTER_WIDTH = authority.P20653["tooth_axial_width_mm"]
OUTER_ROOT_RADIUS = 33.55
CARRIER_FRONT_Z = OUTER_WIDTH / 2.0
CARRIER_REAR_Z = -OUTER_WIDTH / 2.0
KEEPER_GAP = 0.5
METAL_FRONT_Z = CARRIER_FRONT_Z - KEEPER_GAP
METAL_REAR_Z = METAL_FRONT_Z - METAL_BODY_WIDTH
METAL_CENTER_Z = (METAL_FRONT_Z + METAL_REAR_Z) / 2.0
METAL_TOOTH_Z_MIN = METAL_CENTER_Z - METAL_TOOTH_WIDTH / 2.0
METAL_TOOTH_Z_MAX = METAL_CENTER_Z + METAL_TOOTH_WIDTH / 2.0
INSERTION_CHANNEL_TOP_Z = CARRIER_FRONT_Z + 1.0
SHAFT_CLEARANCE_D = 12.0

KEEPER_OD = 66.0
KEEPER_ID = 36.0
KEEPER_T = 3.5
KEEPER_Z = CARRIER_FRONT_Z
KEEPER_SCREW_COUNT = 4
KEEPER_SCREW_PCD = 56.0
KEEPER_CLEARANCE_HOLE_D = 5.5
KEEPER_HARDWARE = "M5_THROUGH_BOLT_LOCKNUT_CANDIDATE"
KEEPER_HARDWARE_STATUS = "PHYSICAL_FASTENER_SELECTION_PENDING"
PRETEST_POST_D = 10.0
PRETEST_KEEPER_Z = authority.COUPON_STOP_MM + METAL_BODY_WIDTH + KEEPER_GAP

BUILDER = Path(__file__).name
TEST = "tests/test_misumi_groove1_full_driven_carrier_v001_contract.py"
STEPS = [
    "cad/full_driven_wheel_carrier_groove1.step",
    "cad/removable_axial_keeper.step",
    "cad/full_carrier_assembly_reference.step",
    "cad/groove1_C1_exact_interface_envelope.step",
    "cad/pretest_carrier_keeper_coupon.step",
    "cad/pretest_coupon_assembly_reference.step",
]
STLS = [
    "print/full_driven_wheel_carrier_groove1.stl",
    "print/removable_axial_keeper.stl",
    "print/pretest_carrier_keeper_coupon.stl",
]
SVGS = [
    "drawings/TORQUE_AND_RETENTION_ARCHITECTURE.svg",
    "drawings/AXIAL_SERVICE_SECTION.svg",
    "drawings/SERVICE_REMOVAL_SEQUENCE.svg",
    "drawings/PHYSICAL_AND_POWERED_GATES.svg",
]
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "GROOVE1_SOURCE_TRACE.md", "KEEPER_ARCHITECTURE.md",
    "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md", "design_parameters.json", "validation_report.json",
    "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
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
    authority_hashes = {path: sha(ROOT / path) for path in AUTHORITY}
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
        "authority_4": authority_hashes == AUTHORITY, "protected_5": protected == PROTECTED,
        "source_zip": sha(authority.SOURCE_ZIP) == SOURCE_ZIP_SHA256,
        "source_step": authority.read_source_authority()["step_sha256"] == SOURCE_STEP_SHA256,
        "scope": set(files).issubset(EXPECTED), "untracked_scope": set(lane_untracked).issubset(expected_untracked),
        "ignored_zero": not ignored, "cache_zero": not cache,
        "complete": not complete or (files == EXPECTED and lane_untracked == expected_untracked),
    }
    result = {
        "checks": checks, "root": str(root), "branch": branch, "head": head,
        "staged": staged, "dirty": dirty, "outside": list(outside()), "authority": authority_hashes,
        "protected": {path: {"files": value[0], "sha256": value[1], "status": "UNCHANGED"} for path, value in protected.items()},
        "lane_files": len(files), "lane_untracked": len(lane_untracked),
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED " + json.dumps(result, ensure_ascii=True))
    return result


def cyl(radius: float, height: float, z: float = 0.0):
    return authority.cylinder(radius, height, z)


def shape_volume(shape) -> float:
    return sum(solid.Volume() for solid in shape.solids().vals())


def common_volume(a, b) -> float:
    try:
        return shape_volume(a.intersect(b))
    except ValueError as exc:
        if "Null TopoDS_Shape" in str(exc):
            return 0.0
        raise


def screw_holes(height: float, z: float = 0.0):
    holes = []
    for index in range(KEEPER_SCREW_COUNT):
        holes.append(
            cyl(KEEPER_CLEARANCE_HOLE_D / 2.0, height, z)
            .translate((KEEPER_SCREW_PCD / 2.0, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), index * 360.0 / KEEPER_SCREW_COUNT)
        )
    return holes


def metal_pulley_envelope(z_center: float = METAL_CENTER_Z):
    return authority.exact_main_clearance_envelope(0.0).translate((0, 0, z_center))


def groove1_interface_envelope(axial_width: float = COUPON_ENGAGEMENT):
    return authority.exact_profile_solid_z(GROOVE_CLEARANCE, axial_width)


def insertion_cavity():
    tooth_height = INSERTION_CHANNEL_TOP_Z - METAL_TOOTH_Z_MIN
    tooth_channel = authority.exact_profile_solid_z(GROOVE_CLEARANCE, tooth_height).translate(
        (0, 0, (INSERTION_CHANNEL_TOP_Z + METAL_TOOTH_Z_MIN) / 2.0)
    )
    boss_channel = cyl(
        METAL_ROOT_OD / 2.0 - 0.9 + GROOVE_CLEARANCE,
        INSERTION_CHANNEL_TOP_Z - METAL_REAR_Z,
        (INSERTION_CHANNEL_TOP_Z + METAL_REAR_Z) / 2.0,
    )
    return tooth_channel.union(boss_channel).clean()


def full_carrier():
    carrier = authority.protected_outer_drive().cut(insertion_cavity())
    carrier = carrier.cut(cyl(SHAFT_CLEARANCE_D / 2.0, OUTER_WIDTH + 2.0, 0.0))
    for hole in screw_holes(OUTER_WIDTH + 2.0, 0.0):
        carrier = carrier.cut(hole)
    carrier = carrier.clean()
    if carrier.solids().size() != 1 or not carrier.val().isValid():
        raise RuntimeError("FULL_CARRIER_GEOMETRY_FAIL")
    return carrier


def keeper():
    ring = cyl(KEEPER_OD / 2.0, KEEPER_T, KEEPER_T / 2.0).cut(cyl(KEEPER_ID / 2.0, KEEPER_T + 2.0, KEEPER_T / 2.0))
    for hole in screw_holes(KEEPER_T + 2.0, KEEPER_T / 2.0):
        ring = ring.cut(hole)
    ring = ring.clean()
    if ring.solids().size() != 1 or not ring.val().isValid():
        raise RuntimeError("KEEPER_GEOMETRY_FAIL")
    return ring


def installed_keeper(z: float = KEEPER_Z):
    return keeper().translate((0, 0, z))


def pretest_coupon():
    coupon = authority.coupon(GROOVE_CODE)
    for index in range(KEEPER_SCREW_COUNT):
        post = cyl(PRETEST_POST_D / 2.0, PRETEST_KEEPER_Z, PRETEST_KEEPER_Z / 2.0)
        post = post.translate((KEEPER_SCREW_PCD / 2.0, 0, 0)).rotate((0, 0, 0), (0, 0, 1), index * 90.0)
        coupon = coupon.union(post)
    for hole in screw_holes(PRETEST_KEEPER_Z + 2.0, PRETEST_KEEPER_Z / 2.0):
        coupon = coupon.cut(hole)
    coupon = coupon.clean()
    if coupon.solids().size() != 1 or not coupon.val().isValid():
        raise RuntimeError("PRETEST_COUPON_GEOMETRY_FAIL")
    return coupon


def compound(parts):
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def full_assembly_reference():
    shaft = cyl(5.0, OUTER_WIDTH + KEEPER_T + 8.0, 1.75)
    return compound([full_carrier(), installed_keeper(), metal_pulley_envelope(), shaft])


def pretest_assembly_reference():
    metal_center = authority.COUPON_STOP_MM + METAL_BODY_WIDTH / 2.0
    return compound([pretest_coupon(), installed_keeper(PRETEST_KEEPER_Z), metal_pulley_envelope(metal_center)])


def geometry_analysis() -> dict:
    source = authority.source_geometry_metrics()["main_body"]
    outer = authority.protected_outer_drive()
    carrier, plate, metal = full_carrier(), installed_keeper(), metal_pulley_envelope()
    tooth_annulus = cyl(50.0, OUTER_WIDTH + 2.0, 0.0).cut(cyl(OUTER_ROOT_RADIUS, OUTER_WIDTH + 4.0, 0.0))
    pretest = pretest_coupon()
    pretest_metal = metal_pulley_envelope(authority.COUPON_STOP_MM + METAL_BODY_WIDTH / 2.0)
    exact = groove1_interface_envelope()
    exact_box = exact.val().BoundingBox()
    parent_tooth_volume = common_volume(outer, tooth_annulus)
    carrier_tooth_volume = common_volume(carrier, tooth_annulus)
    return {
        "source_step_sha256": SOURCE_STEP_SHA256, "source_zip_sha256": SOURCE_ZIP_SHA256,
        "source_tooth_count": source["tooth_count_detected"], "source_pitch_mm": P5M_PITCH,
        "source_tip_od_mm": round(source["exact_tooth_tip_od_mm"], 6), "source_root_od_mm": round(source["exact_root_envelope_diameter_mm"], 6),
        "source_wire_edges": source["section_wire_edge_count"], "source_geometry_method": source["tooth_geometry_source"],
        "groove_code": GROOVE_CODE, "groove_clearance_radial_equivalent_mm": GROOVE_CLEARANCE,
        "groove_profile_bbox_mm": [round(exact_box.xlen, 6), round(exact_box.ylen, 6), round(exact_box.zlen, 6)],
        "groove_profile_volume_mm3": round(shape_volume(exact), 6), "groove_engagement_mm": METAL_TOOTH_WIDTH,
        "outer_tooth_count": OUTER_TOOTH_COUNT, "outer_pitch_mm": OUTER_PITCH, "outer_width_mm": OUTER_WIDTH,
        "carrier_valid": carrier.val().isValid(), "carrier_solids": carrier.solids().size(),
        "keeper_valid": plate.val().isValid(), "keeper_solids": plate.solids().size(),
        "pretest_valid": pretest.val().isValid(), "pretest_solids": pretest.solids().size(),
        "carrier_metal_intersection_mm3": round(common_volume(carrier, metal), 6),
        "keeper_metal_intersection_mm3": round(common_volume(plate, metal), 6),
        "keeper_carrier_intersection_mm3": round(common_volume(plate, carrier), 6),
        "pretest_metal_intersection_mm3": round(common_volume(pretest, pretest_metal), 6),
        "outer_tooth_parent_volume_mm3": round(parent_tooth_volume, 6),
        "outer_tooth_carrier_volume_mm3": round(carrier_tooth_volume, 6),
        "outer_tooth_removed_mm3": round(max(0.0, parent_tooth_volume - carrier_tooth_volume), 6),
        "outer_tooth_added_mm3": round(max(0.0, carrier_tooth_volume - parent_tooth_volume), 6),
        "keeper_to_outer_tooth_mm3": round(common_volume(plate, tooth_annulus), 6),
        "keeper_outer_to_root_clearance_mm": round(OUTER_ROOT_RADIUS - KEEPER_OD / 2.0, 3),
        "screw_outer_to_root_clearance_mm": round(OUTER_ROOT_RADIUS - (KEEPER_SCREW_PCD + KEEPER_CLEARANCE_HOLE_D) / 2.0, 3),
        "radial_backing_at_groove_tip_mm": round(OUTER_ROOT_RADIUS - (METAL_TIP_OD / 2.0 + GROOVE_CLEARANCE), 3),
        "rear_shoulder_backing_mm": round(METAL_REAR_Z - CARRIER_REAR_Z, 3),
        "axial_keeper_gap_mm": KEEPER_GAP, "shaft_clearance_diameter_mm": SHAFT_CLEARANCE_D,
        "assembly_axial_width_mm": round((KEEPER_Z + KEEPER_T) - CARRIER_REAR_Z, 3),
        "service_withdrawal_direction": "+Z_AFTER_KEEPER_REMOVAL",
        "torque_path": "KEYED_METAL_PULLEY_TO_EXACT_GROOVE1_TO_PRINTED_P20653_14T",
        "retention_path": "REMOVABLE_KEEPER_ONLY_NOT_PRIMARY_TORQUE",
    }


def parameters() -> dict:
    return {
        "version": VERSION,
        "authority": {
            "lane": AUTH_REL.as_posix(), "tree_sha256": PROTECTED[AUTH_REL.as_posix()][1],
            "vendor_part": "PTPK28P5M150-A-N10-NFC", "source_step_sha256": SOURCE_STEP_SHA256,
            "reuse_method": "DIRECT_IMPORT_OF_EXACT_OUTER_WIRE_AND_OCCT_C1_0P15_NORMAL_OFFSET_NO_RECONSTRUCTION_NO_SCALING",
        },
        "physical_result": {
            "pulley_groove_1_physical_fit": "PASS", "hand_removable": True, "repeated_insertion_removal": "PASS",
            "cracking": "NONE", "whitening": "NONE", "tooth_ride_over": "NONE", "permanent_deformation": "NONE",
            "initial_rotational_backlash": "SLIGHT_APPROX_0P1MM_VISUAL", "backlash_growth_after_staged_manual_static_torque": "NONE",
            "tooth_damage": "NONE", "pulley_groove_1_static_torque_transfer": "PASS",
            "interface_authority": "FULL_CARRIER_INTERFACE_AUTHORITY", "tightening_to_remove_initial_play": "PROHIBITED",
        },
        "groove1": {
            "code": GROOVE_CODE, "clearance_radial_equivalent_mm": GROOVE_CLEARANCE,
            "source": "AP203_EXACT_SECTION_NO_APPROXIMATION", "pitch_mm": P5M_PITCH, "tooth_count": P5M_TOOTH_COUNT,
            "tip_od_mm": METAL_TIP_OD, "root_od_mm": METAL_ROOT_OD, "metal_tooth_width_mm": METAL_TOOTH_WIDTH,
            "torque_function": "PRIMARY_ROTATIONAL_TORQUE_PATH",
        },
        "carrier": {
            "outer_geometry": "PROTECTED_P20653_14T", "outer_tooth_count": OUTER_TOOTH_COUNT,
            "outer_pitch_mm": OUTER_PITCH, "outer_width_mm": OUTER_WIDTH,
            "metal_center_z_mm": METAL_CENTER_Z, "rear_seat_z_mm": METAL_REAR_Z,
            "shaft_clearance_diameter_mm": SHAFT_CLEARANCE_D, "material": "PETG_CANDIDATE",
            "status": "FULL_DRIVEN_WHEEL_CARRIER_PRINT_READY_PHYSICAL_VALIDATION_PENDING",
        },
        "keeper": {
            "architecture": "REMOVABLE_FRONT_ANNULAR_PLATE", "od_mm": KEEPER_OD, "id_mm": KEEPER_ID,
            "thickness_mm": KEEPER_T, "axial_gap_mm": KEEPER_GAP,
            "screw_count": KEEPER_SCREW_COUNT, "screw_pcd_mm": KEEPER_SCREW_PCD,
            "printed_clearance_hole_mm": KEEPER_CLEARANCE_HOLE_D, "hardware_candidate": KEEPER_HARDWARE,
            "hardware_status": KEEPER_HARDWARE_STATUS, "primary_torque_path": False,
            "glue": False, "permanent_press_fit": False, "destructive_removal": False,
        },
        "service": {
            "sequence": ["REMOVE_KEEPER_FASTENERS", "REMOVE_KEEPER", "WITHDRAW_METAL_PULLEY_PLUS_Z", "INSPECT_OR_REPLACE_PRINTED_CARRIER", "REINSTALL_PULLEY", "REINSTALL_KEEPER"],
            "pulley_trapped": False, "metal_damage_required_for_removal": False,
        },
        "pretest": {
            "carrier_coupon": STLS[2], "keeper": STLS[1], "cycles": 5,
            "checks": ["AXIAL_PLAY", "HAND_REMOVAL", "CRACK", "WHITENING", "TOOTH_DAMAGE", "KEEPER_ACCESS"],
        },
        "gates": {
            "cad": "CAD_PASS", "contract": "CONTRACT_TEST_PASS", "print": "GROOVE1_FULL_CARRIER_PRINT_READY",
            "powered_torque": "POWERED_TORQUE_VALIDATION_PENDING", "crawler_dry_run": "CRAWLER_DRY_RUN_PENDING",
            "continuous_run": "CONTINUOUS_RUN_PENDING", "mud": "MUD_RESISTANCE_PENDING", "field": "FIELD_PENDING",
        },
        "status": "CAD_PASS/CONTRACT_TEST_PASS/GROOVE1_FULL_CARRIER_PRINT_READY/POWERED_TORQUE_VALIDATION_PENDING/CRAWLER_DRY_RUN_PENDING/CONTINUOUS_RUN_PENDING/MUD_RESISTANCE_PENDING/FIELD_PENDING",
        "forbidden_claims": ["POWERED_DRIVETRAIN_PASS", "CRAWLER_DRY_RUN_PASS", "CONTINUOUS_RUN_PASS", "MUD_RESISTANCE_PASS", "FIELD_PASS"],
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="650" viewBox="0 0 1100 650"><rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial;fill:#172033}}.h{{font-size:27px;font-weight:bold}}.s{{font-size:15px;fill:#475569}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.r{{fill:#fee2e2;stroke:#b91c1c;stroke-width:2}}.a{{stroke:#0f7184;stroke-width:4;fill:none;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#0f7184"/></marker></defs><text x="38" y="48" class="h">{title}</text><text x="38" y="78" class="s">{subtitle}</text>{body}<text x="38" y="620" class="s">{VERSION} · POWERED_TORQUE_VALIDATION_PENDING</text></svg>'''


def svg_payload() -> dict[str, str]:
    return {
        SVGS[0]: svg("SEPARATED TORQUE / AXIAL RETENTION", "Groove-1 carries torque; the removable keeper carries axial retention only.", '<circle cx="300" cy="325" r="180" class="b"/><circle cx="300" cy="325" r="95" class="q"/><path d="M390 325H590" class="a"/><rect x="610" y="235" width="340" height="180" class="g"/><text x="170" y="545">exact C1 tooth engagement</text><text x="675" y="330">keeper · 4×M5 candidate</text><text x="650" y="375">NOT primary torque path</text>'),
        SVGS[1]: svg("AXIAL SERVICE SECTION", "+Z insertion; rear shoulder seats the core; front keeper leaves 0.5 mm candidate gap.", '<rect x="120" y="180" width="760" height="260" class="b"/><rect x="510" y="205" width="355" height="210" class="q"/><rect x="890" y="175" width="55" height="270" class="g"/><path d="M700 135V70" class="a"/><text x="145" y="500">carrier Z −22…+22</text><text x="515" y="500">metal Z +0.5…+21.5</text><text x="850" y="545">keeper Z +22…+25.5</text>'),
        SVGS[2]: svg("SERVICE REMOVAL SEQUENCE", "No glue, permanent press fit or destructive removal.", '<text x="65" y="290">UNBOLT</text><path d="M150 285H265" class="a"/><text x="285" y="290">KEEPER OFF</text><path d="M395 285H510" class="a"/><text x="535" y="290">PULL +Z</text><path d="M620 285H735" class="a"/><text x="755" y="290">INSPECT</text><path d="M835 285H950" class="a"/><text x="960" y="290">REBUILD</text>'),
        SVGS[3]: svg("PHYSICAL AND POWERED GATES", "Static fit/keeper cycles precede shaft mounting and any powered test.", '<rect x="90" y="170" width="270" height="290" class="g"/><rect x="415" y="170" width="270" height="290" class="q"/><rect x="740" y="170" width="270" height="290" class="r"/><text x="145" y="260">5× SERVICE</text><text x="455" y="260">MANUAL 20+20</text><text x="785" y="260">POWERED HOLD</text><text x="125" y="350">print / insert / keeper</text><text x="450" y="350">forward / reverse</text><text x="775" y="350">no-load then low-load</text>'),
    }


def documents() -> dict[str, str]:
    h = "# MISUMI Groove-1 Full Driven-Wheel Carrier V001\n\n"
    return {
        "README.md": h + (
            "The physically passing Groove-1/C1 interface is reused directly from the protected MISUMI AP203 authority. A protected P20653 14T printed carrier receives the metal keyed core from +Z. "
            "Groove-1 carries rotational torque; a separate four-fastener annular keeper provides removable axial retention. Print the low-material carrier coupon and keeper first, perform five service cycles, then print the full carrier.\n\n"
            "Status: `CAD_PASS / CONTRACT_TEST_PASS / GROOVE1_FULL_CARRIER_PRINT_READY / POWERED_TORQUE_VALIDATION_PENDING`.\n"
        ),
        "DESIGN_AUTHORITY.md": h + (
            "Physical authority: Groove-1/C1 passed hand insertion/removal, repeated cycles and staged manual/static torque with no backlash growth, crack, whitening, permanent deformation, ride-over or tooth damage. Initial approximately 0.1 mm visual rotational play is accepted and must not be removed by tightening the geometry. "
            "Primary torque path is keyed metal pulley → exact C1 tooth engagement → protected P20653 14T printed carrier. Keeper is axial only.\n"
        ),
        "GROOVE1_SOURCE_TRACE.md": h + (
            f"Authority lane: `{AUTH_REL.as_posix()}`. Vendor `PTPK28P5M150-A-N10-NFC`; STEP SHA-256 `{SOURCE_STEP_SHA256}`. "
            "The builder imports `exact_outer_wire()` and `exact_profile_solid_z(0.15, …)` directly. This is the C1 AP203 wire plus OCCT arc-join normal offset; pitch/phase reconstruction, approximation and XYZ scaling are absent. "
            "Authority metrics: 28 teeth, pitch5.0 mm, tip OD43.420 mm, root envelope39.800 mm, tooth width16.600 mm.\n"
        ),
        "KEEPER_ARCHITECTURE.md": h + (
            "Removable front annular keeper: OD66, ID36, thickness3.5 mm, four Ø5.5 printed clearance holes on PCD56. The candidate follows the repository M5 through-bolt/locknut architecture, but exact bolt length, washer, nut and tool envelope remain `PHYSICAL_FASTENER_SELECTION_PENDING`. "
            "Keeper bottom is Z+22.0; metal front is Z+21.5, giving0.5 mm candidate axial gap. Keeper radius33.0 remains0.55 mm inside the protected outer root radius33.55 and does not enter the crawler tooth annulus.\n"
        ),
        "PHYSICAL_TEST_PLAN.md": h + (
            "Pre-test: print the carrier/keeper coupon and keeper; insert the pulley; install keeper; measure axial and rotational play; remove keeper and pulley; repeat5 cycles; reject crack, whitening, catching, tooth damage or permanent deformation. "
            "Full sequence:1 print carrier;2 insert pulley;3 install keeper;4 check play;5 manually rotate20+ forward;6 manually rotate20+ reverse;7 inspect;8 mount actual shaft;9 low-power no-load;10 forward/reverse;11 inspect backlash growth;12 low-load crawler;13 dry-run crawler only after prior PASS. Water/mud and field remain HOLD.\n"
        ),
        "HOLD_REGISTER.md": h + (
            "- exact M5 bolt length, washer, locknut and installed tool access\n- physical keeper axial-play result and five-cycle service result\n- shaft/key assembly and carrier position on the actual rover\n"
            "- low-power no-load, powered torque, crawler dry run, continuous run, mud resistance and field validation\n- production material/process and fatigue life\n"
        ),
    }


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def generate(out: Path):
    shapes = {
        STEPS[0]: full_carrier(), STEPS[1]: keeper(), STEPS[2]: full_assembly_reference(),
        STEPS[3]: groove1_interface_envelope(), STEPS[4]: pretest_coupon(), STEPS[5]: pretest_assembly_reference(),
    }
    for relative, shape in shapes.items():
        authority.export_step(shape, out / relative)
    for relative, shape in zip(STLS, (full_carrier(), keeper(), pretest_coupon())):
        authority.export_stl(shape, out / relative)
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
    meshes = {relative: authority.mesh_metrics(out / relative) for relative in STLS}
    return steps, meshes


def reproducibility() -> dict:
    compared = sorted([*STEPS, *STLS, *SVGS, *documents().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="misumi_groove1_carrier_v001_") as temp:
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
        "groove_c1": GROOVE_CODE == "C1" and GROOVE_CLEARANCE == 0.15,
        "source_exact": geometry["source_tooth_count"] == 28 and geometry["source_pitch_mm"] == 5.0 and geometry["source_geometry_method"] == "AP203_EXACT_SECTION_NO_APPROXIMATION",
        "source_dimensions": geometry["source_tip_od_mm"] == 43.42 and geometry["source_root_od_mm"] == 39.8,
        "physical_pass": parameters()["physical_result"]["pulley_groove_1_static_torque_transfer"] == "PASS",
        "initial_play_retained": parameters()["physical_result"]["tightening_to_remove_initial_play"] == "PROHIBITED",
        "carrier_valid": geometry["carrier_valid"] and geometry["carrier_solids"] == 1,
        "keeper_valid": geometry["keeper_valid"] and geometry["keeper_solids"] == 1,
        "pretest_valid": geometry["pretest_valid"] and geometry["pretest_solids"] == 1,
        "metal_clear": geometry["carrier_metal_intersection_mm3"] == 0 and geometry["keeper_metal_intersection_mm3"] == 0,
        "keeper_separate": geometry["keeper_carrier_intersection_mm3"] == 0,
        "pretest_clear": geometry["pretest_metal_intersection_mm3"] == 0,
        "outer_teeth_frozen": geometry["outer_tooth_removed_mm3"] == 0 and geometry["outer_tooth_added_mm3"] == 0,
        "keeper_tooth_clear": geometry["keeper_to_outer_tooth_mm3"] == 0 and geometry["keeper_outer_to_root_clearance_mm"] > 0,
        "screw_tooth_clear": geometry["screw_outer_to_root_clearance_mm"] >= 2.5,
        "backing": geometry["radial_backing_at_groove_tip_mm"] >= 10.0 and geometry["rear_shoulder_backing_mm"] >= 20.0,
        "shaft_clearance": geometry["shaft_clearance_diameter_mm"] == 12.0,
        "service": geometry["service_withdrawal_direction"] == "+Z_AFTER_KEEPER_REMOVAL",
        "separated_functions": not parameters()["keeper"]["primary_torque_path"],
        "step_reload": all(row["valid"] for row in steps),
        "stl_quality": all(row["reload"] == "PASS" and row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in meshes.values()),
        "reproducibility": repro["status"] == "PASS", "authority": repository["checks"]["authority_4"],
        "protected": repository["checks"]["protected_5"], "hardware_hold": KEEPER_HARDWARE_STATUS == "PHYSICAL_FASTENER_SELECTION_PENDING",
        "forbidden_claims": all(claim not in parameters()["status"] for claim in parameters()["forbidden_claims"]),
    }
    validation = {
        "version": VERSION, "status": parameters()["status"], "checks": checks,
        "check_count": len(checks), "pass_count": sum(checks.values()), "geometry": geometry,
        "steps": steps, "stls": meshes, "reproducibility": repro,
        "repository": {"branch": repository["branch"], "head": repository["head"], "authority": repository["authority"], "protected": repository["protected"]},
        "holds": ["PHYSICAL_FASTENER_SELECTION_PENDING", "KEEPER_5_CYCLE_PHYSICAL_VALIDATION_PENDING", "POWERED_TORQUE_VALIDATION_PENDING", "CRAWLER_DRY_RUN_PENDING", "CONTINUOUS_RUN_PENDING", "MUD_RESISTANCE_PENDING", "FIELD_PENDING"],
        "assumptions": ["M5 through-bolt/locknut is an architecture candidate inherited from Common Rover practice; exact hardware length, washer, nut and installed tool envelope are not released."],
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
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_MISUMI_GROOVE1_FULL_DRIVEN_CARRIER_V001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
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
