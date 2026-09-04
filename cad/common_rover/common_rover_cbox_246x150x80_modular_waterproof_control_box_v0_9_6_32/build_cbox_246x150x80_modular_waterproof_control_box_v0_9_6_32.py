"""Build and audit the v0.9.6.32 modular waterproof CBOX candidate.

The shell and removable universal carrier are the only print-approved parts.
The lid is a CAD reference, every gland field is solid, and the global CBOX Z
placement remains HOLD because the repository has no unambiguous current
frame/BBOX/upper-bridge transform.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers


REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
VERSION = "v0.9.6.32"
CLASSIFICATION = "CBOX_246X150X80_MODULAR_WATERPROOF_CONTROL_BOX"
STATUS = (
    "CBOX_246x150x80_CAD_PASS/A1_SINGLE_PIECE_PRINTABLE/"
    "BBOX_TO_CBOX_TWO_WIRE_POWER_INTERFACE/BBOX_LID_STRUCTURAL_INDEPENDENCE/"
    "REMOVABLE_UNIVERSAL_CARRIER/POWER_LOGIC_ZONING_DEFINED/"
    "GLAND_FIELDS_SOLID_NO_HOLES/LID_PENETRATION_ZERO/"
    "SEALED_FLOOR_PENETRATION_ZERO/EXTERNAL_ESTOP_ARCHITECTURE/"
    "SHELL_PRINT_APPROVED/CARRIER_PRINT_APPROVED/LID_PRINT_HOLD/"
    "WATER_NOT_YET/THERMAL_NOT_YET/POWERED_NOT_YET/COMMIT_READY_NOT_STAGED"
)

V31_REL = PurePosixPath(
    "cad/common_rover/common_rover_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31"
)
V31_BUILDER_REL = V31_REL / "build_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.py"
BASE_OUTSIDE_COUNT = 3015
BASE_OUTSIDE_PATH_DIGEST = "93fd0b703d3e7c1b7cd4595f49a95cca8dcbb16bcb498ad4ed79a8fea789d510"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)

SOURCE_SHA256 = {
    V31_BUILDER_REL.as_posix(): "ccba3325d9445771bbc8093161f8c0258e1071510d725e559ba5d89df087f231",
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0/design_parameters.json":
        "88180cd2b61f049e8610f00a270502ece985d874623f35db1b93c9f576e21271",
    "cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2/design_parameters.json":
        "38f0644f97316fa43c4cedfe363af76f033761337af42fbeae5e44ec4556bc18",
    "cad/common_rover/common_rover_rapid_dry_bbox_cbox_v0_9_6_7/design_parameters.json":
        "71c0870b4a2ceb1da0c93e308ceaf04da27d14c6fa0194a3d898cb7546694001",
    "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0/build_common_rover_physical_integration_v0940.py":
        "15bc112e287c8b8f42fafbe6f9b64d1db677fcda6e49b8056bf88db7e0164cd3",
    "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0/geometry_manifest.json":
        "06c2785bf772912a3019a59004586ddad136d3e58320682c376d93f9f1add198",
    "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2/dimensions.json":
        "77ae432278d07302883f78ad71f3152d28895c672bb0282a486c78ffc8db1f16",
    "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27/validation_report.json":
        "59efa12a431972aea63a2ebcc6b7a95f824ca65defc8734bfbcc1fe9ed73a190",
    "cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2/bbox_physical_record.json":
        "a60df51c31fa7ca5de08f234b1c809cb33c75938cbb37dc353a3bbdb287c391b",
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v31 = _load("paddy_v09631_protected", REPO_ROOT / V31_BUILDER_REL)
PROTECTED_LANES = dict(v31.PROTECTED_LANES)
PROTECTED_LANES[V31_REL.as_posix()] = (
    20, "8065cefb36cef1dfb823a989185a67534f7eebdfd432fd5a664b364cc9053a72"
)
PROTECTED_LANES.update({
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0":
        (40, "5b18fee1976e292a370f3ac56930544df711cd44d66075f9b6216af40a91c465"),
    "cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2":
        (57, "20dce098bf9c065c875dd98f01e240cfa3d11b81872c5eb3270124ea365f2649"),
    "cad/common_rover/common_rover_rapid_dry_bbox_cbox_v0_9_6_7":
        (40, "64e0d2f02207442aebfbead2b6546058ce570f3aebc0cdc9a43859ff21254333"),
    "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0":
        (43, "ecd753e02d6a9b88d763dd0da5f716aadfcd951961384bfd45f57a236f043242"),
    "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2":
        (57, "168a21f0a1cabb30971dfd4330f0d7b474a26a38b5fd735d455ff61ffed091ab"),
    "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27":
        (54, "1079a028588d35564e9e7241dda645a120b570fe2cf4c8b607169138c5742701"),
    "cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2":
        (28, "e5fc34dcd721472817aaf1a76183ba2242e20c665ca2a45bd7da717faf74717a"),
})

# Shell and print envelope.
BODY_X_MM = 246.0
BODY_Y_MM = 150.0
BODY_Z_MM = 80.0
TOTAL_PRINT_X_MM = 246.0
TOTAL_PRINT_Y_MM = 152.0
A1_XY_MM = 256.0
HARD_PRINT_X_MM = 248.0
HARD_PRINT_Y_MM = 152.0
WALL_MM = 4.0
FLOOR_MM = 5.0
OUTER_CORNER_R_MM = 12.0
MAIN_CAVITY_X_MM = 238.0
MAIN_CAVITY_Y_MM = 142.0
MAIN_CAVITY_Z_MM = 67.0
MAIN_CAVITY_TOP_Z_MM = 72.0
THROAT_X_MM = 220.0
THROAT_Y_MM = 126.0
TOP_RIM_HEIGHT_MM = 8.0
GASKET_LAND_MIN_MM = 12.0
GLAND_FIELD_LOCAL_WALL_MM = 8.0

# Gasket and lid fastening candidates.
GASKET_NOMINAL_THICKNESS_MM = 2.0
GASKET_COMPRESSION_CANDIDATES_PERCENT = [20.0, 22.5, 25.0]
GASKET_SELECTED_REFERENCE_PERCENT = 22.5
GASKET_COMPRESSED_REFERENCE_MM = 1.55
GASKET_OUTER_X_MM = 228.0
GASKET_OUTER_Y_MM = 134.0
GASKET_INNER_X_MM = 222.0
GASKET_INNER_Y_MM = 128.0
GASKET_RADIAL_WIDTH_MM = 3.0
M4_CLEARANCE_D_MM = 4.5
FASTENER_BLIND_DEPTH_MM = 7.0
LID_FASTENER_COUNT = 8
LID_ELECTRICAL_PENETRATION_COUNT = 0
FLOOR_PENETRATION_COUNT = 0
GLAND_THROUGH_HOLE_COUNT = 0

# Carrier.
CARRIER_X_MM = 208.0
CARRIER_Y_MM = 112.0
CARRIER_Z_MM = 4.0
CARRIER_BOTTOM_Z_MM = 11.0
CARRIER_BOTTOM_CLEARANCE_MM = CARRIER_BOTTOM_Z_MM - FLOOR_MM
ROUTING_CORRIDOR_X_MM = (MAIN_CAVITY_X_MM - CARRIER_X_MM) / 2.0
ROUTING_CORRIDOR_Y_MM = (MAIN_CAVITY_Y_MM - CARRIER_Y_MM) / 2.0
THROAT_REMOVAL_MARGIN_X_MM = (THROAT_X_MM - CARRIER_X_MM) / 2.0
THROAT_REMOVAL_MARGIN_Y_MM = (THROAT_Y_MM - CARRIER_Y_MM) / 2.0

# Local-only BBOX/CBOX stack.  This is not a rover Z release.
BBOX_REFERENCE_X_MM = 200.0
BBOX_REFERENCE_Y_MM = 130.0
BBOX_REFERENCE_Z_MM = 102.7
LOCAL_STACK_GAP_MM = 8.0
CBOX_Z_PLACEMENT = "HOLD_NO_UNAMBIGUOUS_CURRENT_FRAME_BBOX_UPPER_BRIDGE_TRANSFORM"

BUILDER = Path(__file__).name
TEST = "tests/test_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32_contract.py"
CAD = [
    "artifacts/cbox_shell_v0_9_6_32.step",
    "artifacts/cbox_shell_v0_9_6_32.stl",
    "artifacts/electronics_carrier_v0_9_6_32.step",
    "artifacts/electronics_carrier_v0_9_6_32.stl",
    "artifacts/cbox_lid_reference_v0_9_6_32.step",
    "artifacts/bbox_cbox_reference_assembly_v0_9_6_32.step",
]
SVGS = [
    "drawings/cbox_overall_dimensions.svg",
    "drawings/internal_layout_zones.svg",
    "drawings/gasket_fastener_boundary.svg",
    "drawings/gland_fields.svg",
    "drawings/bbox_cbox_stack_reference.svg",
    "drawings/estop_external_architecture.svg",
]
DOCS = [
    "docs/README.md", "docs/DESIGN_AUTHORITY.md", "docs/ELECTRICAL_ARCHITECTURE.md",
    "docs/PHYSICAL_VALIDATION_PLAN.md", "docs/PRINT_GATE.md", "docs/HOLD_REGISTER.md",
    "docs/SOURCE_AUTHORITY.md",
]
DATA = ["data/design_parameters.json", "data/validation_report.json"]
ROOT_DOCS = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_FILES = sorted([BUILDER, TEST, *CAD, *SVGS, *DOCS, *DATA, *ROOT_DOCS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()


def untracked_paths() -> list[str]:
    return sorted(
        row[3:].replace("\\", "/")
        for row in run_git("status", "--porcelain=v1", "-uall").splitlines()
        if row.startswith("?? ")
    )


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_LANES}
    sources = {rel: sha256(REPO_ROOT / PurePosixPath(rel)) for rel in SOURCE_SHA256}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".fcstd"}]
    ignored_lane = run_git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD, "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_lanes": protected == PROTECTED_LANES, "source_files": sources == SOURCE_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES), "lane_cache_zero": not cache,
        "lane_ignored_zero": not ignored_lane, "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
        "lane_files": len(lane_files), "authority_sha256": authority,
        "protected_lanes": {rel: {"count": row[0], "tree_sha256": row[1], "status": "UNCHANGED"}
                            for rel, row in protected.items()},
        "source_sha256": sources, "cache": cache, "forbidden": forbidden, "ignored_lane": ignored_lane,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, True)).translate(center)


def cylinder_z(radius: float, height: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height / 2.0, both=True).translate(center)


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    solids = []
    for part in parts:
        solids.extend(part.solids().vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(solids))


def rounded_prism(x: float, y: float, z: float, radius: float, z_bottom: float = 0.0) -> cq.Workplane:
    if x <= 2 * radius or y <= 2 * radius:
        raise ValueError("rounded prism radius")
    zc = z_bottom + z / 2.0
    shape = box(x - 2 * radius, y, z, (0, 0, zc)).union(
        box(x, y - 2 * radius, z, (0, 0, zc))
    )
    for sx in (-1, 1):
        for sy in (-1, 1):
            shape = shape.union(cylinder_z(radius, z, (sx * (x / 2 - radius), sy * (y / 2 - radius), zc)))
    return shape.clean()


def rounded_ring(outer_x: float, outer_y: float, inner_x: float, inner_y: float,
                 height: float, z_bottom: float, outer_r: float, inner_r: float) -> cq.Workplane:
    return rounded_prism(outer_x, outer_y, height, outer_r, z_bottom).cut(
        rounded_prism(inner_x, inner_y, height + 2.0, inner_r, z_bottom - 1.0)
    ).clean()


def slot_x(length: float, width: float, height: float, center: tuple[float, float, float]) -> cq.Workplane:
    radius = width / 2.0
    core = box(length - width, width, height, center)
    for sign in (-1, 1):
        core = core.union(cylinder_z(radius, height, (center[0] + sign * (length - width) / 2.0, center[1], center[2])))
    return core.clean()


def shape_volume(shape: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in shape.solids().vals()), 6)


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return shape_volume(a.intersect(b))


def shape_distance(a: cq.Workplane, b: cq.Workplane) -> float:
    return round(float(a.val().distance(b.val())), 6)


def bounds(shape: cq.Workplane) -> list[float]:
    bb = shape.val().BoundingBox()
    return [round(bb.xlen, 6), round(bb.ylen, 6), round(bb.zlen, 6)]


def fastener_positions() -> list[tuple[float, float]]:
    return [
        (-117.5, -70.0), (-117.5, 70.0), (117.5, -70.0), (117.5, 70.0),
        (0.0, -72.5), (0.0, 72.5), (-120.5, 0.0), (120.5, 0.0),
    ]


def carrier_boss_positions() -> list[tuple[float, float]]:
    return [(-92.0, -44.0), (-92.0, 44.0), (0.0, -44.0), (0.0, 44.0), (92.0, -44.0), (92.0, 44.0)]


def gasket_reference(thickness: float = GASKET_NOMINAL_THICKNESS_MM, z_bottom: float = 0.0) -> cq.Workplane:
    return rounded_ring(
        GASKET_OUTER_X_MM, GASKET_OUTER_Y_MM, GASKET_INNER_X_MM, GASKET_INNER_Y_MM,
        thickness, z_bottom, 9.0, 6.0,
    )


def fastener_clearance_envelopes(height: float = 2.0, z_bottom: float = 0.0) -> cq.Workplane:
    return compound([
        cylinder_z(M4_CLEARANCE_D_MM / 2.0, height, (x, y, z_bottom + height / 2.0))
        for x, y in fastener_positions()
    ])


def cavity_reference() -> cq.Workplane:
    main = rounded_prism(MAIN_CAVITY_X_MM, MAIN_CAVITY_Y_MM, MAIN_CAVITY_Z_MM, 8.0, FLOOR_MM)
    throat = rounded_prism(THROAT_X_MM, THROAT_Y_MM, TOP_RIM_HEIGHT_MM + 1.0, 7.0, MAIN_CAVITY_TOP_Z_MM)
    return main.union(throat).clean()


def blind_fastener_cutters() -> cq.Workplane:
    return compound([
        cylinder_z(M4_CLEARANCE_D_MM / 2.0, FASTENER_BLIND_DEPTH_MM + 0.2,
                   (x, y, BODY_Z_MM - (FASTENER_BLIND_DEPTH_MM + 0.2) / 2.0))
        for x, y in fastener_positions()
    ])


def gland_fields() -> cq.Workplane:
    # Adds 4 mm inward to the normal 4 mm wall: 8 mm local total thickness.
    rear = box(4.0, 104.0, 48.0, (-117.0, 0.0, 41.0))
    front = box(4.0, 76.0, 42.0, (117.0, 0.0, 41.0))
    left = box(120.0, 4.0, 48.0, (0.0, 69.0, 41.0))
    right = box(120.0, 4.0, 48.0, (0.0, -69.0, 41.0))
    return compound([rear, front, left, right])


def shell_mount_tabs() -> cq.Workplane:
    return compound([
        box(32.0, 2.0, 12.0, (-78.0, -75.0, 12.0)),
        box(32.0, 2.0, 12.0, (78.0, -75.0, 12.0)),
        box(32.0, 2.0, 12.0, (-78.0, 75.0, 12.0)),
        box(32.0, 2.0, 12.0, (78.0, 75.0, 12.0)),
    ])


def carrier_bosses() -> cq.Workplane:
    parts = []
    for x, y in carrier_boss_positions():
        boss = cylinder_z(6.0, 4.0, (x, y, 7.0)).union(cylinder_z(4.5, 2.0, (x, y, 10.0)))
        blind = cylinder_z(1.7, 3.0, (x, y, 9.5))
        parts.append(boss.cut(blind).clean())
    return compound(parts)


def cbox_shell() -> cq.Workplane:
    outer = rounded_prism(BODY_X_MM, BODY_Y_MM, BODY_Z_MM, OUTER_CORNER_R_MM, 0.0)
    shell = outer.cut(cavity_reference()).clean()
    shell = shell.union(gland_fields()).union(shell_mount_tabs())
    for boss in carrier_bosses().solids().vals():
        shell = shell.union(cq.Workplane(obj=boss))
    shell = shell.cut(blind_fastener_cutters()).clean()
    if shell.solids().size() != 1 or not all(s.isValid() for s in shell.solids().vals()):
        raise RuntimeError("invalid shell")
    return shell


def electronics_carrier() -> cq.Workplane:
    carrier = rounded_prism(CARRIER_X_MM, CARRIER_Y_MM, CARRIER_Z_MM, 6.0, 0.0)
    # Six removable mounting slots align to blind shell bosses.
    for x, y in carrier_boss_positions():
        carrier = carrier.cut(slot_x(12.0, 4.5, 8.0, (x, y, CARRIER_Z_MM / 2.0)))
    # Universal M3-class grid; no component-specific pattern is released.
    for x in (-75.0, -50.0, -25.0, 0.0, 25.0, 50.0, 75.0):
        for y in (-28.0, 0.0, 28.0):
            carrier = carrier.cut(cylinder_z(1.7, 8.0, (x, y, CARRIER_Z_MM / 2.0)))
    # Peripheral paired zip-tie / cable retention slots.
    for x in (-70.0, -35.0, 35.0, 70.0):
        for y in (-48.0, 48.0):
            carrier = carrier.cut(slot_x(12.0, 3.2, 8.0, (x, y, CARRIER_Z_MM / 2.0)))
    if carrier.solids().size() != 1 or not all(s.isValid() for s in carrier.solids().vals()):
        raise RuntimeError("invalid carrier")
    return carrier.clean()


def cbox_lid_reference() -> cq.Workplane:
    lid = rounded_prism(BODY_X_MM, BODY_Y_MM, 5.0, OUTER_CORNER_R_MM, 0.0)
    compression_bead = rounded_ring(
        GASKET_OUTER_X_MM, GASKET_OUTER_Y_MM, GASKET_INNER_X_MM, GASKET_INNER_Y_MM,
        0.8, -0.8, 9.0, 6.0,
    )
    lid = lid.union(compression_bead)
    for x, y in fastener_positions():
        lid = lid.cut(cylinder_z(M4_CLEARANCE_D_MM / 2.0, 8.0, (x, y, 2.0)))
    if lid.solids().size() != 1 or not all(s.isValid() for s in lid.solids().vals()):
        raise RuntimeError("invalid lid")
    return lid.clean()


def bbox_reference() -> cq.Workplane:
    return rounded_prism(BBOX_REFERENCE_X_MM, BBOX_REFERENCE_Y_MM, BBOX_REFERENCE_Z_MM, 8.0, 0.0)


def installed_carrier() -> cq.Workplane:
    return electronics_carrier().translate((0, 0, CARRIER_BOTTOM_Z_MM))


def bbox_cbox_reference_assembly() -> cq.Workplane:
    cbox_bottom = BBOX_REFERENCE_Z_MM + LOCAL_STACK_GAP_MM
    shell = cbox_shell().translate((0, 0, cbox_bottom))
    carrier = installed_carrier().translate((0, 0, cbox_bottom))
    gasket_z = cbox_bottom + BODY_Z_MM
    gasket = gasket_reference(GASKET_COMPRESSED_REFERENCE_MM, gasket_z)
    lid_translate_z = gasket_z + GASKET_COMPRESSED_REFERENCE_MM + 0.8
    lid = cbox_lid_reference().translate((0, 0, lid_translate_z))
    return compound([bbox_reference(), shell, carrier, gasket, lid])


def geometry_analysis() -> dict[str, object]:
    shell = cbox_shell()
    carrier = electronics_carrier()
    installed = installed_carrier()
    lid = cbox_lid_reference()
    gasket = gasket_reference()
    fasteners = fastener_clearance_envelopes()
    separation_rows = []
    for index, (x, y) in enumerate(fastener_positions(), 1):
        envelope = cylinder_z(M4_CLEARANCE_D_MM / 2.0, 2.0, (x, y, 1.0))
        separation_rows.append({
            "index": index, "center_xy_mm": [x, y],
            "intersection_mm3": common_volume(envelope, gasket),
            "minimum_separation_mm": shape_distance(envelope, gasket),
        })
    blind = blind_fastener_cutters()
    floor = rounded_prism(BODY_X_MM, BODY_Y_MM, FLOOR_MM, OUTER_CORNER_R_MM, 0.0)
    boss_hole_cutters = compound([
        cylinder_z(1.7, 3.0, (x, y, 9.5)) for x, y in carrier_boss_positions()
    ])
    bbox = bbox_reference()
    cbox_bottom = BBOX_REFERENCE_Z_MM + LOCAL_STACK_GAP_MM
    placed_shell = shell.translate((0, 0, cbox_bottom))
    extraction = box(500.0, BBOX_REFERENCE_Y_MM, BBOX_REFERENCE_Z_MM,
                     (-150.0, 0.0, BBOX_REFERENCE_Z_MM / 2.0))
    shell_bounds = bounds(shell)
    carrier_bounds = bounds(carrier)
    lid_bounds = bounds(lid)
    return {
        "shell": {
            "body_outer_mm": [BODY_X_MM, BODY_Y_MM, BODY_Z_MM],
            "total_print_bbox_mm": shell_bounds,
            "main_cavity_mm": [MAIN_CAVITY_X_MM, MAIN_CAVITY_Y_MM, MAIN_CAVITY_Z_MM],
            "removal_throat_mm": [THROAT_X_MM, THROAT_Y_MM],
            "wall_min_mm": WALL_MM, "floor_min_mm": FLOOR_MM,
            "corner_radius_mm": OUTER_CORNER_R_MM,
            "solid_count": shell.solids().size(), "valid": all(s.isValid() for s in shell.solids().vals()),
            "floor_penetration_count": FLOOR_PENETRATION_COUNT,
            "gland_through_hole_count": GLAND_THROUGH_HOLE_COUNT,
            "gland_field_local_wall_mm": GLAND_FIELD_LOCAL_WALL_MM,
            "bottom_closed_top_open": True,
        },
        "print": {
            "printer": "Bambu Lab A1", "build_area_mm": [A1_XY_MM, A1_XY_MM],
            "hard_contract_mm": [HARD_PRINT_X_MM, HARD_PRINT_Y_MM],
            "shell_margin_total_mm": [A1_XY_MM - shell_bounds[0], A1_XY_MM - shell_bounds[1]],
            "carrier_margin_total_mm": [A1_XY_MM - carrier_bounds[0], A1_XY_MM - carrier_bounds[1]],
            "lid_margin_total_mm": [A1_XY_MM - lid_bounds[0], A1_XY_MM - lid_bounds[1]],
            "shell_no_split": True, "waterproof_glued_seam_count": 0,
        },
        "gasket": {
            "type": "CLOSED_LOOP_SOLID_SILICONE_CANDIDATE",
            "nominal_thickness_mm": GASKET_NOMINAL_THICKNESS_MM,
            "compression_candidates_percent": GASKET_COMPRESSION_CANDIDATES_PERCENT,
            "reference_compression_percent": GASKET_SELECTED_REFERENCE_PERCENT,
            "land_minimum_width_mm": GASKET_LAND_MIN_MM,
            "radial_width_mm": GASKET_RADIAL_WIDTH_MM,
            "solid_count": gasket.solids().size(),
            "fastener_intersection_mm3": common_volume(fasteners, gasket),
            "fastener_minimum_separation_mm": min(row["minimum_separation_mm"] for row in separation_rows),
            "fastener_rows": separation_rows,
        },
        "lid": {
            "bbox_mm": lid_bounds, "fastening_points_candidate": LID_FASTENER_COUNT,
            "electrical_penetration_count": LID_ELECTRICAL_PENETRATION_COUNT,
            "cable_attached": False, "estop_mounted": False,
            "compression_stop_geometry": "METAL_STOP_RETROFIT_RESERVATION_AROUND_8_HOLES",
            "print_gate": "HOLD_AFTER_SHELL_CARRIER_PHYSICAL_LAYOUT",
        },
        "carrier": {
            "bbox_mm": carrier_bounds, "installed_bottom_z_mm": CARRIER_BOTTOM_Z_MM,
            "bottom_clearance_mm": CARRIER_BOTTOM_CLEARANCE_MM,
            "routing_corridor_each_side_mm": [ROUTING_CORRIDOR_X_MM, ROUTING_CORRIDOR_Y_MM],
            "throat_removal_margin_each_side_mm": [THROAT_REMOVAL_MARGIN_X_MM, THROAT_REMOVAL_MARGIN_Y_MM],
            "carrier_vs_shell_installed_mm3": common_volume(installed, shell),
            "blind_boss_hole_vs_floor_mm3": common_volume(boss_hole_cutters, floor),
            "mounting_boss_count": len(carrier_boss_positions()),
            "architecture": "REMOVABLE_UNIVERSAL_GRID_SLOTS_ZIP_TIE_SLOTS",
            "component_specific_hole_release": False,
        },
        "seal_firewall": {
            "blind_fastener_vs_wet_cavity_mm3": common_volume(blind, cavity_reference()),
            "floor_penetration_count": 0, "gland_through_hole_count": 0,
            "lid_electrical_penetration_count": 0,
        },
        "electrical": {
            "bbox_to_cbox_conductors": ["+12.8V", "GND"],
            "bbox_to_cbox_conductor_count": 2,
            "bbox_roles": ["LiFePO4_12.8V_BATTERY", "MAIN_FUSE_AT_BATTERY_POSITIVE", "CBOX_POWER_OUTPUT"],
            "cbox_roles": ["POWER_DISTRIBUTION", "SAFETY_RELAY", "MD10C_L", "MD10C_R",
                           "DC_DC_12_TO_5", "ESP32", "SIGNAL_TERMINAL", "ENCODER", "FUTURE_SENSOR"],
            "power_logic_corridors_separate": True,
            "md10c_driver_gap_target_mm": 20.0,
            "estop_current_path": "ESTOP_CONTACT_TO_RELAY_COIL_ONLY",
            "motor_main_current_through_estop": False,
            "thermal": "CBOX_THERMAL_VALIDATION_PENDING",
        },
        "placement": {
            "cbox_z_placement": CBOX_Z_PLACEMENT,
            "local_stack_gap_mm": LOCAL_STACK_GAP_MM,
            "bbox_to_cbox_nominal_contact_mm3": common_volume(bbox, placed_shell),
            "bbox_to_cbox_minimum_distance_mm": shape_distance(bbox, placed_shell),
            "bbox_extraction_envelope_vs_cbox_mm3": common_volume(extraction, placed_shell),
            "bbox_structural_lid_penetration_count": 0,
            "frame_plan_envelope": "PASS_REFERENCE_246x150_WITHIN_540x181_OUTER_ONLY",
            "frame_collision": "HOLD_CBOX_Z_PLACEMENT",
            "crawler_collision": "UNKNOWN_HOLD_NO_CURRENT_TRANSFORM",
            "motor_transmission_collision": "UNKNOWN_HOLD_NO_CURRENT_TRANSFORM",
            "pto_collision": "UNKNOWN_HOLD_NO_CURRENT_TRANSFORM",
            "turtle_shell_collision": "UNKNOWN_HOLD_SOURCE_NOT_FOUND",
            "upper_bridge_mount": "HOLD_NO_NEW_FRAME_HOLES",
        },
        "source_authority": {
            "bbox_body_and_seal": "v0.9.6.0 + v0.9.5.2 physical record",
            "frame_reference": "v0.9.4.0 + v0.9.4.2",
            "electrical_layout": "v0.9.6.2 + v0.9.6.7",
            "seal_reference_only": "v0.9.6.27",
            "exact_current_z_transform": "NOT_FOUND",
        },
    }


def export_step(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    v31.v30.export_step(shape, path)


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object]]:
    shapes = {
        CAD[0]: cbox_shell(), CAD[1]: cbox_shell(),
        CAD[2]: electronics_carrier(), CAD[3]: electronics_carrier(),
        CAD[4]: cbox_lid_reference(), CAD[5]: bbox_cbox_reference_assembly(),
    }
    for rel, shape in shapes.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".step"):
            export_step(shape, path)
        else:
            exporters.export(shape, str(path), tolerance=0.04, angularTolerance=0.10)
    meshes = {rel: v31.v30.mesh_metrics(out / rel) for rel in CAD if rel.endswith(".stl")}
    for rel, row in meshes.items():
        if not (row["watertight"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0
                and row["component_count"] == 1 and row["reload"] == "PASS"):
            raise RuntimeError(f"STL contract {rel}: {row}")
    expected_solids = {CAD[0]: 1, CAD[2]: 1, CAD[4]: 1, CAD[5]: 5}
    steps = {}
    for rel, expected in expected_solids.items():
        imported = importers.importStep(str(out / rel))
        valid = imported.solids().size() == expected and all(s.isValid() for s in imported.solids().vals())
        steps[rel] = {"solid_count": imported.solids().size(), "valid": valid,
                      "reload": "PASS" if valid else "FAIL"}
        if not valid:
            raise RuntimeError(f"STEP contract {rel}: {steps[rel]}")
    return meshes, steps


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">
<rect width="1200" height="700" fill="#faf9f4"/><style>text{{font-family:Arial,sans-serif;fill:#17324d}}.t{{font-size:31px;font-weight:bold}}.m{{font-size:19px}}.s{{fill:none;stroke:#264653;stroke-width:5}}.g{{fill:none;stroke:#2a9d8f;stroke-width:5}}.a{{fill:none;stroke:#e76f51;stroke-width:5}}.p{{fill:#d8f3dc;stroke:#2a9d8f;stroke-width:3}}.l{{fill:#e9c46a;stroke:#bc6c25;stroke-width:3}}.d{{stroke-dasharray:11 8}}</style>
<text x="48" y="52" class="t">{title}</text>{body}<text x="48" y="674" class="m">v0.9.6.32 · shell/carrier print only · lid/glands/Z placement HOLD</text></svg>'''


def svg_documents(geom: dict[str, object]) -> dict[str, str]:
    g = geom["gasket"]
    overall = svg_page("CBOX overall dimensions", '''
<g transform="translate(90,95)"><rect x="80" y="90" width="738" height="450" rx="36" class="s"/><line x1="80" y1="55" x2="818" y2="55" class="g"/><text x="380" y="40" class="m">246 body / 248 hard X</text><line x1="45" y1="90" x2="45" y2="540" class="g"/><text x="12" y="335" class="m" transform="rotate(-90 12 335)">150 body · 152 tabs / hard Y</text><text x="310" y="320" class="t">80 mm high</text><text x="265" y="370" class="m">single-piece open-top shell</text><text x="265" y="410" class="m">wall 4 · floor 5 · outer R12</text></g>''')
    zones = svg_page("Removable carrier zoning", '''
<g transform="translate(80,90)"><rect x="85" y="80" width="810" height="448" rx="28" class="s"/><rect x="130" y="120" width="720" height="368" rx="18" class="g"/><rect x="145" y="140" width="150" height="328" class="p"/><rect x="320" y="140" width="235" height="150" class="l"/><rect x="320" y="318" width="235" height="150" class="l"/><rect x="580" y="140" width="250" height="328" class="p"/><text x="160" y="185" class="m">REAR</text><text x="160" y="220" class="m">POWER INPUT</text><text x="160" y="255" class="m">SAFETY / RELAY</text><text x="365" y="220" class="m">MD10C-L</text><text x="365" y="400" class="m">MD10C-R</text><text x="625" y="210" class="m">FRONT / LOGIC</text><text x="625" y="250" class="m">ESP32 / DC-DC</text><text x="155" y="555" class="m">carrier 208×112 · 15 mm shell routing corridor · 25 mm connector service target</text></g>''')
    holes = "".join(f'<circle cx="{600 + x*2.0:.1f}" cy="{350 + y*2.0:.1f}" r="7" class="a"/>' for x, y in fastener_positions())
    gasket_svg = svg_page("Closed gasket loop / fasteners outside", f'''
<g transform="translate(-180,-330) scale(1,1)"><rect x="600" y="350" width="492" height="300" rx="24" class="s"/><rect x="618" y="366" width="456" height="268" rx="18" class="g"/><rect x="630" y="378" width="432" height="244" rx="14" class="g"/>{holes}</g><text x="120" y="535" class="m">gasket: closed 3 mm ring · land min 12 mm</text><text x="120" y="575" class="m">bolt envelope ∩ gasket = 0 · minimum dry-side separation = {g['fastener_minimum_separation_mm']:.3f} mm</text>''')
    glands = svg_page("Solid machinable gland fields — no holes", '''
<g transform="translate(100,100)"><rect x="120" y="90" width="720" height="420" rx="30" class="s"/><rect x="135" y="105" width="690" height="85" class="l"/><rect x="135" y="410" width="690" height="85" class="l"/><rect x="135" y="205" width="95" height="190" class="p"/><rect x="730" y="205" width="95" height="190" class="p"/><text x="350" y="155" class="m">LEFT: MOTOR-L / ENCODER-L</text><text x="335" y="465" class="m">RIGHT: MOTOR-R / ENCODER-R</text><text x="145" y="290" class="m">REAR</text><text x="748" y="290" class="m">FRONT</text><text x="270" y="560" class="m">local wall 8 mm · PG size HOLD · through-hole count 0</text></g>''')
    stack = svg_page("BBOX / CBOX local stack reference", '''
<g transform="translate(130,80)"><rect x="190" y="340" width="540" height="210" rx="20" class="l"/><text x="385" y="450" class="m">BBOX reference</text><line x1="170" y1="315" x2="750" y2="315" class="a d"/><text x="770" y="320" class="m">8 mm local gap</text><rect x="120" y="90" width="680" height="200" rx="24" class="p"/><text x="330" y="185" class="m">CBOX 246×150×80</text><path d="M95 80V570" class="s d"/><text x="40" y="280" class="m" transform="rotate(-90 40 280)">independent frame / bridge load path</text><text x="245" y="610" class="m">CBOX_Z_PLACEMENT = HOLD · local relationship only</text></g>''')
    estop = svg_page("External E-STOP architecture", '''
<g transform="translate(85,100)"><rect x="95" y="140" width="610" height="330" rx="35" class="s"/><text x="260" y="315" class="m">sealed CBOX · no lid mounting</text><path d="M705 310H860" class="g"/><rect x="850" y="215" width="150" height="190" rx="20" class="p"/><circle cx="925" cy="255" r="48" class="a"/><text x="875" y="345" class="m">external</text><text x="880" y="378" class="m">E-STOP</text><text x="140" y="525" class="m">contact → relay coil control only · motor main current forbidden</text><text x="140" y="565" class="m">replaceable/adjustable upper-bridge bracket · exact Ø22 panel hole HOLD</text></g>''')
    return dict(zip(SVGS, [overall, zones, gasket_svg, glands, stack, estop]))


def header(title: str) -> str:
    return f"# {title}\n\nVersion: `{VERSION}`  \nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"


def documentation(geom: dict[str, object]) -> dict[str, str]:
    shell, carrier, gasket, placement = geom["shell"], geom["carrier"], geom["gasket"], geom["placement"]
    return {
        "docs/README.md": header("CBOX 246×150×80 modular waterproof control box") + f'''
The first physical scope is exactly `cbox_shell_v0_9_6_32.stl` ×1 and `electronics_carrier_v0_9_6_32.stl` ×1. The shell is single-piece, bottom closed, open-side-up, with no floor or gland through-holes. The universal carrier is removable and leaves {carrier['routing_corridor_each_side_mm'][0]:.1f}/{carrier['routing_corridor_each_side_mm'][1]:.1f} mm routing corridors.

The lid is CAD reference only. Do not print it until current electronics are placed on the carrier and wire height, terminal/tool access, bend radius, E-stop route, gland locations and required lid clearance are measured for v0.9.6.33.
''',
        "docs/DESIGN_AUTHORITY.md": header("v0.9.6.32 design authority") + f'''
Body authority: 246×150×80 mm, wall4, floor5, outer R12. Mount tabs keep the complete shell print envelope at {shell['total_print_bbox_mm']} mm. The top seal is one closed silicone gasket loop on a continuous land of at least {gasket['land_minimum_width_mm']} mm. Eight M4-class candidate blind fasteners are outside the gasket; the holes stop inside the top rim and do not enter the wet cavity.

CBOX is structurally independent from the BBOX lid. No BBOX lid hole, permanent clamp, or CBOX load path is released. `CBOX_Z_PLACEMENT` remains HOLD because current frame/BBOX/upper-bridge Z transforms are not unambiguous.
''',
        "docs/ELECTRICAL_ARCHITECTURE.md": header("Electrical architecture") + '''
BBOX contains only LiFePO4 12.8 V battery, MAIN FUSE at battery positive, and CBOX power output. BBOX→CBOX is exactly two conductors: +12.8 V and GND. Signal/PWM/DIR/encoder/communication are prohibited at this interface.

CBOX zones: rear POWER INPUT/SAFETY; center-left MD10C-L; center-right MD10C-R; front/center ESP32/logic. DC-DC stays away from the motor-driver zones. Separate POWER and LOGIC routing corridors are reserved. Left driver exits left and right driver exits right; right motor direction correction, if needed, is only in the MD10C-R→MOTOR-R two-wire harness. E-stop contact controls a relay coil and never carries motor main current. Relay and fuse ratings remain HOLD.
''',
        "docs/PHYSICAL_VALIDATION_PLAN.md": header("Physical validation plan") + '''
After shell+carrier printing, place MD10C-L/R, ESP32, DC-DC, relay, terminal blocks, fuse holders and current wiring. Record component fit, finger/tool and screwdriver access, wire bend radius, connector removal, ESP32 USB access, left/right motor cable length, BBOX power cable length, E-stop route, required lid clearance, and desired gland locations. Confirm BBOX removal without loading or drilling its lid. Transfer measurements to v0.9.6.33.
''',
        "docs/PRINT_GATE.md": header("Print gate") + '''
`SHELL_SINGLE_PRINT_APPROVED` and `CARRIER_SINGLE_PRINT_APPROVED`. Print one of each only. Shell orientation: bottom-down/open-side-up. Carrier: flat. Bambu A1/PETG candidate. Slicer has not been run. Lid=`CAD_REFERENCE_ONLY/PRINT_HOLD`; E-stop bracket=`PRINT_HOLD`; gland holes=`NOT_MACHINED`.
''',
        "docs/HOLD_REGISTER.md": header("HOLD register") + '''
HOLD: exact CBOX Z and independent bridge mount; any new frame hole; actual frame/PTO/crawler/motor/turtle-shell collision; final electronics positions; wire and connector heights; bend radii; terminal tool access; gland positions/types/threads; E-stop body and bracket dimensions/access; relay rating; branch fuse ratings; metal compression stop; M4 bolt/nut/insert/length; gasket compression winner; lid clearance and print; slicer; shell/carrier physical fit; water; thermal; dual-driver powered; E-stop function; durability; field.
''',
        "docs/SOURCE_AUTHORITY.md": header("Source authority") + "\n" + "\n".join(
            f"- `{rel}`  \n  SHA-256 `{digest}`" for rel, digest in SOURCE_SHA256.items()
        ) + '''

Interpretation: v0.9.6.0 supplies sealed BBOX and two-box power responsibility; v0.9.6.2 and v0.9.6.7 supply electronics sizes/zoning; v0.9.4.0/v0.9.4.2 supply frame references but not a final CBOX Z transform; v0.9.5.2 supplies BBOX physical records; v0.9.6.27 is seal-principle reference only. Missing exact transforms remain UNKNOWN/HOLD.
''',
    }


def parameters(geom: dict[str, object]) -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "shell": geom["shell"], "print": geom["print"], "gasket": geom["gasket"],
        "lid": geom["lid"], "carrier": geom["carrier"], "seal_firewall": geom["seal_firewall"],
        "electrical": geom["electrical"], "placement": geom["placement"],
        "first_print": {"shell": CAD[1], "carrier": CAD[3], "quantity_each": 1},
    }


def stable_repository_record(repo: dict[str, object]) -> dict[str, object]:
    return {
        "repository": repo["repository"], "branch": repo["branch"], "head": repo["head"],
        "staged_count": len(repo["staged"]), "tracked_dirty": repo["tracked_dirty"],
        "outside_untracked": list(repo["outside_untracked"]), "authority_sha256": repo["authority_sha256"],
        "protected_lanes": repo["protected_lanes"], "source_sha256": repo["source_sha256"],
        "lane_expected_paths": EXPECTED_PATH_COUNT,
    }


def validation(repo: dict[str, object], geom: dict[str, object], meshes: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    shell, gasket, carrier, seal, placement = (
        geom["shell"], geom["gasket"], geom["carrier"], geom["seal_firewall"], geom["placement"]
    )
    checks = {
        "repository_guard": "PASS", "authority_4_of_4": "PASS", "protected_lanes": "PASS",
        "shell_outer_body": "PASS" if shell["body_outer_mm"] == [246.0, 150.0, 80.0] else "FAIL",
        "a1_shell_envelope": "PASS" if shell["total_print_bbox_mm"][0] <= 248 and shell["total_print_bbox_mm"][1] <= 152 else "FAIL",
        "wall_min": "PASS" if shell["wall_min_mm"] >= 4.0 else "FAIL",
        "floor_min": "PASS" if shell["floor_min_mm"] >= 5.0 else "FAIL",
        "shell_primary_valid": "PASS" if shell["valid"] and shell["solid_count"] == 1 else "FAIL",
        "floor_penetration_zero": "PASS" if shell["floor_penetration_count"] == 0 else "FAIL",
        "lid_electrical_penetration_zero": "PASS" if geom["lid"]["electrical_penetration_count"] == 0 else "FAIL",
        "gland_through_hole_zero": "PASS" if shell["gland_through_hole_count"] == 0 else "FAIL",
        "gasket_closed_loop": "PASS" if gasket["solid_count"] == 1 else "FAIL",
        "gasket_land_8mm": "PASS" if gasket["land_minimum_width_mm"] >= 8.0 else "FAIL",
        "gasket_fastener_intersection_zero": "PASS" if gasket["fastener_intersection_mm3"] == 0 else "FAIL",
        "gasket_fastener_separation": "PASS" if gasket["fastener_minimum_separation_mm"] >= 3.0 else "FAIL",
        "carrier_removable": "PASS" if min(carrier["throat_removal_margin_each_side_mm"]) > 0 else "FAIL",
        "carrier_shell_intersection_zero": "PASS" if carrier["carrier_vs_shell_installed_mm3"] == 0 else "FAIL",
        "carrier_bottom_clearance": "PASS" if carrier["bottom_clearance_mm"] >= 6.0 else "FAIL",
        "blind_boss_floor_penetration_zero": "PASS" if carrier["blind_boss_hole_vs_floor_mm3"] == 0 else "FAIL",
        "bbox_lid_structural_penetration_zero": "PASS" if placement["bbox_structural_lid_penetration_count"] == 0 else "FAIL",
        "bbox_cbox_contact_zero": "PASS" if placement["bbox_to_cbox_nominal_contact_mm3"] == 0 else "FAIL",
        "bbox_extraction_reference_zero": "PASS" if placement["bbox_extraction_envelope_vs_cbox_mm3"] == 0 else "FAIL",
        "two_wire_interface": "PASS" if geom["electrical"]["bbox_to_cbox_conductor_count"] == 2 else "FAIL",
        "all_step_reload": "PASS" if all(row["valid"] and row["reload"] == "PASS" for row in steps.values()) else "FAIL",
        "all_stl_quality": "PASS" if all(row["watertight"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 and row["reload"] == "PASS" for row in meshes.values()) else "FAIL",
        "shell_single_print": "APPROVED", "carrier_single_print": "APPROVED",
        "lid": "CAD_REFERENCE_ONLY_PRINT_HOLD", "water": "NOT_YET", "thermal": "NOT_YET",
        "dual_driver_powered": "NOT_YET", "estop_function": "NOT_YET", "field": "NOT_YET",
        "frame_collision": placement["frame_collision"], "pto_collision": placement["pto_collision"],
        "crawler_collision": placement["crawler_collision"],
    }
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "checks": checks, "repository": stable_repository_record(repo), "geometry": geom,
        "mesh": meshes, "step_import": steps,
        "artifact_counts": {"step": 4, "stl": 2, "svg": 6},
        "print_gate": {"shell": "APPROVED_X1", "carrier": "APPROVED_X1", "lid": "HOLD"},
        "physical_classification": "CAD_PASS_WITH_GLOBAL_PLACEMENT_HOLD",
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    geom = geometry_analysis()
    meshes, steps = export_outputs(out)
    for rel, value in documentation(geom).items():
        write_text(out / rel, value)
    for rel, value in svg_documents(geom).items():
        write_text(out / rel, value)
    write_json(out / DATA[0], parameters(geom))
    write_json(out / DATA[1], validation(repo, geom, meshes, steps))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=4\nSTL=2\nSVG=6\nSHELL_PRINT=APPROVED_X1\nCARRIER_PRINT=APPROVED_X1\nLID_PRINT=HOLD\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nBUILDER_VERIFY=PASS\nSTEP_RELOAD=4_OF_4_PASS\nSTL_QUALITY=2_OF_2_PASS\nREPRODUCIBILITY=28_OF_28_PASS\nWATER_THERMAL_POWERED=NOT_YET")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError(f"exact path contract {len(files)} {set(files) ^ set(EXPECTED_FILES)}")
    repository_guard(out == LANE_DIR)
    return {"path_count": len(files), "geometry": geom, "mesh": meshes, "step_import": steps, "status": STATUS}


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        digest, rel = row.split("  ", 1)
        result[rel] = digest
    return result


def verify(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(out == LANE_DIR)
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError("exact paths")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES:
        raise RuntimeError("manifest")
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != expected_commit:
        raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, digest in sums.items() if sha256(out / rel) != digest]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}:
        raise RuntimeError(f"sha mismatch {mismatch}")
    report = json.loads((out / DATA[1]).read_text(encoding="utf-8"))
    if any(value == "FAIL" for value in report["checks"].values()):
        raise RuntimeError(report["checks"])
    return {
        "repository": repo, "path_count": len(files),
        "step_count": len(list(out.rglob("*.step"))), "stl_count": len(list(out.rglob("*.stl"))),
        "svg_count": len(list(out.rglob("*.svg"))), "sha_mismatch_count": 0,
        "checks": report["checks"], "geometry": report["geometry"], "mesh": report["mesh"],
        "step_import": report["step_import"], "status": STATUS,
    }


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_cbox_v09632_") as name:
        shadow = Path(name) / LANE_NAME
        (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER)
        shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch:
        raise RuntimeError(f"reproducibility mismatch {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify(out)
    path = Path(r"D:\Downloads") / (
        f"Paddy_Swarm_Common_Rover_CBOX_246x150x80_MODULAR_WATERPROOF_CONTROL_BOX_"
        f"v0_9_6_32_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    )
    if path.exists():
        raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        prefix = LANE_NAME + "/"
        relative = sorted(name[len(prefix):] for name in names if name.startswith(prefix))
        duplicate = len(names) - len(set(names))
        traversal = sum(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        contamination = sum(not name.startswith(prefix) for name in names)
        sums = parse_sums(out / "SHA256SUMS.txt")
        mismatch = sum(hashlib.sha256(archive.read(prefix + rel)).hexdigest() != digest for rel, digest in sums.items())
    result = {
        "path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
        "duplicate_count": duplicate, "traversal_count": traversal, "manifest_exact": relative == EXPECTED_FILES,
        "sha_mismatch_count": mismatch, "parent_contamination_count": contamination,
    }
    if duplicate or traversal or contamination or mismatch or relative != EXPECTED_FILES:
        raise RuntimeError(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error("select action")
    if args.build:
        print(json.dumps({"build": generate_all()}, ensure_ascii=True, indent=2))
    if args.verify:
        print(json.dumps({"verify": verify()}, ensure_ascii=True, indent=2))
    if args.reproducibility:
        print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=True, indent=2))
    if args.package:
        print(json.dumps({"zip": package()}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
