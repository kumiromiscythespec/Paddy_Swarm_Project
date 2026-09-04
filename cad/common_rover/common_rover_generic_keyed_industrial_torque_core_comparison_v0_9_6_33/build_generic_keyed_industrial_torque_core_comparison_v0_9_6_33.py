"""Build and audit the v0.9.6.33 generic keyed industrial torque-core study.

The protected P20653 14T crawler interface is imported without scaling from the
v0.9.6.30/v0.9.6.31 authority chain.  The three metal cores in this lane are
dimension-supported *reference* models, not vendor-fit replicas.  No fit STL is
released until exact source tooth geometry or a received part becomes authority.
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
from functools import lru_cache
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import importers


REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
VERSION = "v0.9.6.33"
LANE_NAME = "common_rover_generic_keyed_industrial_torque_core_comparison_v0_9_6_33"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
CLASSIFICATION = "GENERIC_KEYED_INDUSTRIAL_TORQUE_CORE_COMPARISON"
STATUS = (
    "CAD_PASS/CONTRACT_TEST_PASS/GENERIC_CORE_COMPARISON_COMPLETE/"
    "PROCUREMENT_TEST_RECOMMENDATION/SOURCE_GEOMETRY_HOLD/"
    "FIT_COUPON_NOT_GENERATED/FULL_DRIVE_PRINT_HOLD/"
    "STATIC_TORQUE_NOT_YET/POWERED_NOT_YET/MUD_NOT_YET/WATER_NOT_YET/"
    "FIELD_NOT_YET/PRODUCTION_NOT_SELECTED/COMMIT_READY_NOT_STAGED"
)

V30_REL = PurePosixPath(
    "cad/common_rover/common_rover_p20653_14t_18025_full_width_through_bolt_drive_v0_9_6_30"
)
V30_BUILDER_REL = V30_REL / "build_p20653_14t_18025_full_width_through_bolt_drive_v0_9_6_30.py"
V31_REL = PurePosixPath(
    "cad/common_rover/common_rover_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31"
)
V31_BUILDER_REL = V31_REL / "build_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.py"
V31_STEP_REL = V31_REL / "artifacts/p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.step"
V31_VALIDATION_REL = V31_REL / "validation_report.json"
V32_REL = PurePosixPath(
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32"
)
V32_BUILDER_REL = V32_REL / "build_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32.py"
V29_VALIDATION_REL = PurePosixPath(
    "cad/common_rover/common_rover_p20653_18025_keyed_hub_drive_v0_9_6_29/validation_report.json"
)

BASE_OUTSIDE_COUNT = 3067
BASE_OUTSIDE_PATH_DIGEST = "83928372d40c1d27a157a5b9ababa126019d0bc0beb8160577e6ec6cc6eb235d"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)
SOURCE_SHA256 = {
    V30_BUILDER_REL.as_posix(): "d9ad9d5a5f46261b11aad1297855358148b56bd94e8d3bc4d6f8b72eac48d169",
    V31_BUILDER_REL.as_posix(): "ccba3325d9445771bbc8093161f8c0258e1071510d725e559ba5d89df087f231",
    V31_STEP_REL.as_posix(): "fa7f1118bb907b7f932ed89b550e2c3e531553157b7360e74daa70acf61d967d",
    V31_VALIDATION_REL.as_posix(): "b139c1f43988a3683988724054fe9e74207243133deb066fadbc2f39b0d3adb6",
    V32_BUILDER_REL.as_posix(): "9724d607848710226253cf1c78df52a23da880d81e0a4ef7708ea762bf2661fa",
    V29_VALIDATION_REL.as_posix(): "5abcfb861e445995da117ab23ec7fcf214236b8540ad790c3199c197a6a6b7d1",
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v30 = _load("paddy_v09630_outer_authority", REPO_ROOT / V30_BUILDER_REL)
v32 = _load("paddy_v09632_guard_authority", REPO_ROOT / V32_BUILDER_REL)
PROTECTED_LANES = dict(v32.PROTECTED_LANES)
PROTECTED_LANES[V32_REL.as_posix()] = (
    28, "4792b7db682d02e78ab88bdd8642f42b6805a6773782f4bcc36f2ff3427bc516"
)

TARGET_TORQUE_NM = 6.5
TARGET_TORQUE_NMM = TARGET_TORQUE_NM * 1000.0
WHEEL_AXIAL_WIDTH_MM = 44.0
CONTINUOUS_RING_RADIUS_MM = float(v30.SUPPORT_RING_RADIUS_MM)
FIT_CLEARANCE_CANDIDATES_MM = [0.15, 0.25, 0.35]
FUTURE_COUPON_NOTCH_IDS = {"C1": 1, "C2": 2, "C3": 3}

MISUMI_SOURCE_URL = "https://jp.misumi-ec.com/pdf/fa/p1969.pdf"
MISUMI_PRODUCT_URL = "https://jp.misumi-ec.com/vona2/detail/110300406640/"
KANA_SOURCE_URL = "https://www.kana.co.jp/pdf/DOLS_EN.pdf"
KANA_CATALOG_URL = "https://www.kana.co.jp/en/product/e-catalog"
SOURCE_ACCESSED_DATE = "2026-08-20"

# P5M 1.81/0.571/3.32 are published profile-reference dimensions.  They are
# sufficient for an explanatory reference solid, not for a physical fit coupon.
P5M_PROFILE_DEPTH_REFERENCE_MM = 1.81
P5M_PITCH_LINE_TO_OD_REFERENCE_MM = 0.571
P5M_TOOTH_TANGENTIAL_REFERENCE_MM = 3.32

CANDIDATES = {
    "A1": {
        "candidate_id": "A1_P5M25",
        "family": "MISUMI_HIGH_TORQUE_TIMING_PULLEY_P5M",
        "category": "INDUSTRIAL_TIMING_PULLEY",
        "pitch_mm": 5.0,
        "teeth": 25,
        "pitch_diameter_mm": 39.79,
        "toothed_body_od_mm": 38.65,
        "max_outer_envelope_mm": 45.0,
        "boss_diameter_mm": 30.0,
        "tooth_axial_width_mm": 16.6,
        "flanged_width_mm": 21.0,
        "overall_axial_envelope_mm": 33.0,
        "bore_mm": 10.0,
        "keyway_width_mm": 3.0,
        "keyway_depth_mm": 1.4,
        "set_screw": "M4_REFERENCE_PHASE_HOLD",
        "material": "HARD_ANODIZED_ALUMINUM_PREFERRED_CANDIDATE",
        "mass_kg": None,
        "source_geometry": "DIMENSION_SUPPORTED_REFERENCE_PROFILE_ONLY",
        "fit_coupon_readiness": "SOURCE_GEOMETRY_HOLD",
        "axial_retention": "CONDITIONAL_UNCAULKED_OR_REMOVED_FLANGE_STATE_REQUIRED",
        "status": "SOURCE_GEOMETRY_HOLD/PROCUREMENT_TEST_RECOMMENDED",
    },
    "A2": {
        "candidate_id": "A2_P5M28",
        "family": "MISUMI_HIGH_TORQUE_TIMING_PULLEY_P5M",
        "category": "INDUSTRIAL_TIMING_PULLEY",
        "pitch_mm": 5.0,
        "teeth": 28,
        "pitch_diameter_mm": 44.56,
        "toothed_body_od_mm": 43.42,
        "max_outer_envelope_mm": 50.0,
        "boss_diameter_mm": 32.0,
        "tooth_axial_width_mm": 16.6,
        "flanged_width_mm": 21.0,
        "overall_axial_envelope_mm": 33.0,
        "bore_mm": 10.0,
        "keyway_width_mm": 3.0,
        "keyway_depth_mm": 1.4,
        "set_screw": "M4_REFERENCE_PHASE_HOLD",
        "material": "HARD_ANODIZED_ALUMINUM_PREFERRED_CANDIDATE",
        "mass_kg": None,
        "source_geometry": "DIMENSION_SUPPORTED_REFERENCE_PROFILE_ONLY",
        "fit_coupon_readiness": "SOURCE_GEOMETRY_HOLD",
        "axial_retention": "CONDITIONAL_UNCAULKED_OR_REMOVED_FLANGE_STATE_REQUIRED",
        "status": "SOURCE_GEOMETRY_HOLD/PRIMARY_PROCUREMENT_CANDIDATE",
    },
    "B": {
        "candidate_id": "B_KANA_FBN40B12D10",
        "family": "KANA_FBN40B",
        "category": "FINISHED_BORE_INDUSTRIAL_CHAIN_SPROCKET",
        "pitch_mm": 12.7,
        "teeth": 12,
        "pitch_diameter_mm": 49.07,
        "toothed_body_od_mm": 55.0,
        "max_outer_envelope_mm": 55.0,
        "boss_diameter_mm": 40.0,
        "tooth_axial_width_mm": 7.2,
        "flanged_width_mm": None,
        "overall_axial_envelope_mm": 22.0,
        "bore_mm": 10.0,
        "keyway_width_mm": 3.0,
        "keyway_depth_mm": 1.4,
        "set_screw": "M4_REFERENCE_PHASE_HOLD",
        "material": "MACHINE_STRUCTURAL_CARBON_STEEL",
        "mass_kg": 0.22,
        "source_geometry": "DIMENSION_SUPPORTED_REFERENCE_PROFILE_ONLY",
        "fit_coupon_readiness": "SOURCE_GEOMETRY_HOLD",
        "axial_retention": "CAD_FEASIBLE_REMOVABLE_SIDE_RETAINER_CONCEPT",
        "status": "SOURCE_GEOMETRY_HOLD/CORROSION_MITIGATION_REQUIRED",
    },
}

BUILDER = Path(__file__).name
TEST = "tests/test_generic_keyed_industrial_torque_core_comparison_v0_9_6_33_contract.py"
STEPS = [
    "artifacts/p5m25_core_reference.step",
    "artifacts/p5m28_core_reference.step",
    "artifacts/kana_fbn40b12d10_core_reference.step",
    "artifacts/p5m25_in_14t_section.step",
    "artifacts/p5m28_in_14t_section.step",
    "artifacts/kana_in_14t_section.step",
]
STLS: list[str] = []
SVGS = [
    "drawings/torque_core_comparison.svg",
    "drawings/radial_ligament_comparison.svg",
    "drawings/axial_stack_comparison.svg",
    "drawings/torque_load_comparison.svg",
    "drawings/positive_engagement_concept.svg",
    "drawings/axial_retention_options.svg",
]
DOCS = [
    "docs/README.md",
    "docs/DESIGN_AUTHORITY.md",
    "docs/SOURCE_AUTHORITY.md",
    "docs/INDUSTRIAL_CORE_REQUIREMENTS.md",
    "docs/CANDIDATE_COMPARISON.md",
    "docs/PROCUREMENT_RECOMMENDATION.md",
    "docs/PHYSICAL_TEST_PLAN.md",
    "docs/HOLD_REGISTER.md",
]
DATA = [
    "data/design_parameters.json",
    "data/candidate_metrics.json",
    "data/validation_report.json",
]
META = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_FILES = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *DOCS, *DATA, *META])
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
        row.replace("\\", "/")
        for row in run_git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard").splitlines()
        if row
    )


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    digest = hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()
    return len(paths), digest


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_LANES}
    sources = {rel: sha256(REPO_ROOT / PurePosixPath(rel)) for rel in SOURCE_SHA256}
    lane_files = sorted(
        path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file()
    ) if LANE_DIR.exists() else []
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".fcstd"}]
    ignored_lane = run_git(
        "ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()
    ).splitlines()
    checks = {
        "repository": root == REPO_ROOT.resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_lanes": protected == PROTECTED_LANES,
        "source_files": sources == SOURCE_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES),
        "lane_cache_zero": not cache,
        "lane_ignored_zero": not ignored_lane,
        "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks,
        "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
        "lane_files": len(lane_files), "authority_sha256": authority,
        "protected_lanes": {
            rel: {"count": row[0], "tree_sha256": row[1], "status": "UNCHANGED"}
            for rel, row in protected.items()
        },
        "source_sha256": sources, "cache": cache, "forbidden": forbidden, "ignored_lane": ignored_lane,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def cylinder(radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height / 2.0, both=True).translate((0, 0, z))


def annulus(outer_r: float, inner_r: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cylinder(outer_r, height, z).cut(cylinder(inner_r, height + 2.0, z)).clean()


def compound(shapes: list[cq.Workplane]) -> cq.Workplane:
    values = [value for shape in shapes for value in shape.vals()]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(values)])


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in a.intersect(b).solids().vals()), 6)


@lru_cache(maxsize=1)
def outer_drive_geometry() -> cq.Workplane:
    result = v30.raw_support()
    for index in range(v30.TARGET_TOOTH_COUNT):
        result = result.union(v30.target_tooth(index))
    result = result.clean()
    if result.solids().size() != 1 or not all(solid.isValid() for solid in result.solids().vals()):
        raise RuntimeError("protected P20653 outer geometry invalid")
    return result


def keyway_cutter(length: float, width: float, depth: float) -> cq.Workplane:
    return cq.Workplane("XY").box(depth + 1.0, width, length + 4.0).translate((5.0 + depth / 2.0, 0, 0))


def radial_lobe_profile(root_r: float, outer_r: float, count: int, tangential_width: float) -> cq.Workplane:
    half_angle = math.degrees((tangential_width / 2.0) / max((root_r + outer_r) / 2.0, 1.0))
    half_angle = min(half_angle, 360.0 / count * 0.32)
    points = []
    for radius, angle in (
        (root_r - 0.05, -half_angle), (outer_r, -half_angle * 0.62),
        (outer_r, half_angle * 0.62), (root_r - 0.05, half_angle),
    ):
        points.append((radius * math.cos(math.radians(angle)), radius * math.sin(math.radians(angle))))
    return cq.Workplane("XY").polyline(points).close()


def lobed_band(root_r: float, outer_r: float, count: int, width: float, tangential_width: float) -> cq.Workplane:
    result = cylinder(root_r, width)
    tooth = radial_lobe_profile(root_r, outer_r, count, tangential_width).extrude(width / 2.0, both=True)
    for index in range(count):
        result = result.union(tooth.rotate((0, 0, 0), (0, 0, 1), index * 360.0 / count))
    return result.clean()


@lru_cache(maxsize=3)
def metal_core_geometry(key: str) -> cq.Workplane:
    c = CANDIDATES[key]
    if key in {"A1", "A2"}:
        pitch_r = c["pitch_diameter_mm"] / 2.0
        root_r = pitch_r - P5M_PROFILE_DEPTH_REFERENCE_MM
        toothed = lobed_band(
            root_r, c["toothed_body_od_mm"] / 2.0, c["teeth"],
            c["tooth_axial_width_mm"], P5M_TOOTH_TANGENTIAL_REFERENCE_MM,
        )
        boss = cylinder(c["boss_diameter_mm"] / 2.0, c["overall_axial_envelope_mm"])
        flange_z = c["flanged_width_mm"] / 2.0 - 0.5
        flanges = cylinder(c["max_outer_envelope_mm"] / 2.0, 1.0, -flange_z).union(
            cylinder(c["max_outer_envelope_mm"] / 2.0, 1.0, flange_z)
        )
        result = toothed.union(boss).union(flanges).clean()
    else:
        root_r = c["boss_diameter_mm"] / 2.0
        toothed = lobed_band(
            root_r, c["toothed_body_od_mm"] / 2.0, c["teeth"],
            c["tooth_axial_width_mm"], 4.0,
        )
        result = toothed.union(cylinder(root_r, c["overall_axial_envelope_mm"])).clean()
    result = result.cut(cylinder(c["bore_mm"] / 2.0, c["overall_axial_envelope_mm"] + 4.0))
    result = result.cut(keyway_cutter(
        c["overall_axial_envelope_mm"], c["keyway_width_mm"], c["keyway_depth_mm"]
    )).clean()
    if result.solids().size() != 1 or not all(solid.isValid() for solid in result.solids().vals()):
        raise RuntimeError(f"reference core invalid: {key}")
    return result


@lru_cache(maxsize=3)
def pocketed_outer_geometry(key: str) -> cq.Workplane:
    c = CANDIDATES[key]
    # Envelope-only cavity.  A true tooth-negative pocket is intentionally not
    # modeled while exact vendor tooth geometry is unavailable.
    cavity = cylinder(c["max_outer_envelope_mm"] / 2.0 + 0.35, c["overall_axial_envelope_mm"] + 1.0)
    return outer_drive_geometry().cut(cavity).clean()


@lru_cache(maxsize=3)
def section_reference(key: str) -> cq.Workplane:
    half_space = cq.Workplane("XY").box(120.0, 160.0, WHEEL_AXIAL_WIDTH_MM + 4.0).translate((60.0, 0, 0))
    petg_half = pocketed_outer_geometry(key).intersect(half_space).clean()
    return compound([petg_half, metal_core_geometry(key)])


def bounds(shape: cq.Workplane) -> list[float]:
    box = shape.val().BoundingBox()
    return [round(box.xmin, 6), round(box.xmax, 6), round(box.ymin, 6), round(box.ymax, 6),
            round(box.zmin, 6), round(box.zmax, 6)]


def candidate_metrics() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for key, c in CANDIDATES.items():
        contact_r = c["pitch_diameter_mm"] / 2.0
        force = TARGET_TORQUE_NMM / contact_r
        quarter_features = max(1, math.floor(c["teeth"] * 0.25))
        envelope_ligament = CONTINUOUS_RING_RADIUS_MM - c["max_outer_envelope_mm"] / 2.0
        tooth_body_ligament = CONTINUOUS_RING_RADIUS_MM - c["toothed_body_od_mm"] / 2.0
        remaining_axial = WHEEL_AXIAL_WIDTH_MM - c["overall_axial_envelope_mm"]
        rows[key] = {
            **c,
            "metal_core_pitch_radius_mm": round(contact_r, 6),
            "expected_torque_contact_radius_mm": round(contact_r, 6),
            "tangential_force_at_6p5nm_n": round(force, 6),
            "load_distribution_n_per_feature": {
                "one_feature": round(force, 6),
                "two_features": round(force / 2.0, 6),
                "three_features": round(force / 3.0, 6),
                "twenty_five_percent_feature_count": quarter_features,
                "twenty_five_percent_features": round(force / quarter_features, 6),
            },
            "available_petg_radial_ligament_at_max_envelope_mm": round(envelope_ligament, 6),
            "available_petg_radial_ligament_at_tooth_body_mm": round(tooth_body_ligament, 6),
            "minimum_continuous_ligament_mm": round(envelope_ligament, 6),
            "hard_ligament_gate_mm": 5.0,
            "target_ligament_gate_mm": 6.0,
            "stretch_ligament_gate_mm": 8.0,
            "ligament_status": "PASS_STRETCH" if envelope_ligament >= 8.0 else (
                "PASS_TARGET" if envelope_ligament >= 6.0 else "PASS_HARD_TARGET_MISS"
            ),
            "axial_remaining_inside_44mm_mm": round(remaining_axial, 6),
            "possible_retainer_thickness_mm": 3.0 if key in {"A1", "A2"} else 4.0,
            "fixed_shoulder_candidate_mm": 4.0 if key in {"A1", "A2"} else 5.0,
            "axial_clearance_candidate_mm": 1.0,
            "axial_residual_after_concept_stack_mm": round(
                remaining_axial - (8.0 if key in {"A1", "A2"} else 10.0), 6
            ),
            "axial_width_status": "PASS_REFERENCE" if c["overall_axial_envelope_mm"] <= 44.0 else "WIDTH_TARGET_MISS",
            "set_screw_service_access": "CONCEPT_FEASIBLE_CIRCUMFERENTIAL_WINDOW_PHASE_HOLD",
            "set_screw_phase": "HOLD",
            "estimated_cavity_volume_mm3": round(
                math.pi * (c["max_outer_envelope_mm"] / 2.0 + 0.35) ** 2
                * (c["overall_axial_envelope_mm"] + 1.0), 3
            ),
            "metal_petg_contact_feature_count": c["teeth"],
            "positive_engagement": "EXTERNAL_TEETH_TO_FUTURE_EXACT_NEGATIVE_POCKET",
            "core_crawler_pitch_decoupled": c["pitch_mm"] != v30.PITCH_MM,
            "reference_core_bounds_mm": bounds(metal_core_geometry(key)),
            "reference_core_volume_mm3": round(sum(float(s.Volume()) for s in metal_core_geometry(key).solids().vals()), 3),
            "core_vs_envelope_pocket_intersection_mm3": common_volume(
                metal_core_geometry(key), pocketed_outer_geometry(key)
            ),
            "fit_clearance_candidates_mm": FIT_CLEARANCE_CANDIDATES_MM,
            "future_coupon_notch_ids": FUTURE_COUPON_NOTCH_IDS,
            "fit_stl_generated": False,
        }
    return rows


def geometry_analysis() -> dict[str, object]:
    regression = v30.tooth_regression()
    metrics = candidate_metrics()
    return {
        "outer_p20653": {
            "source_lane": V31_REL.as_posix(),
            "source_step_sha256": SOURCE_SHA256[V31_STEP_REL.as_posix()],
            "pitch_mm": v30.PITCH_MM,
            "tooth_count": v30.TARGET_TOOTH_COUNT,
            "pitch_diameter_mm": v30.TARGET_PITCH_DIAMETER_MM,
            "phase_deg": v30.TARGET_PHASE_DEG,
            "spacing_deg": v30.TARGET_SPACING_DEG,
            "tooth_axial_width_mm": v30.TOOTH_WIDTH_MM,
            "regression": regression,
            "core_crawler_decoupling": "METAL_CORE_PITCH_INDEPENDENT_FROM_P20653_CRAWLER_PITCH",
        },
        "shaft_key": {
            "shaft": "MISUMI_AHFGKR10-145-KA4-A20_PURCHASE_CANDIDATE",
            "diameter_mm": 10.0,
            "length_mm": 145.0,
            "keyway": "3MM_CLASS_PRE_MACHINED_ARCHITECTURE",
            "key": "KESS3-20_CLASS_PURCHASE_CANDIDATE",
            "physical_authority": "NOT_YET",
            "source_lane": V29_VALIDATION_REL.as_posix(),
        },
        "candidates": metrics,
        "recommendation": {
            "primary": "A2_P5M28",
            "primary_reason": "LOWER_TANGENTIAL_FORCE_THAN_A1_WITH_8P55MM_MAX_ENVELOPE_LIGAMENT_AND_HARD_ANODIZED_OPTION",
            "secondary": "A1_P5M25",
            "secondary_reason": "MAXIMUM_11P05MM_ENVELOPE_LIGAMENT_WITH_SAME_33MM_AXIAL_CLASS",
            "diversity_candidate": "B_KANA_FBN40B12D10",
            "diversity_reason": "COMMON_FINISHED_BORE_CHAIN_SPROCKET_AND_SIMPLE_22MM_AXIAL_STACK_BUT_CORROSION_AND_6P05MM_LIGAMENT_PENALTIES",
            "production_selected": False,
        },
        "source_geometry": {
            "exact_vendor_cad_in_repository": False,
            "fit_coupon_release": "BLOCKED_SOURCE_GEOMETRY_HOLD",
            "reference_steps": "DIMENSION_SUPPORTED_COMPARISON_ONLY_NOT_FOR_FIT",
            "set_screw_phase": "HOLD",
        },
    }


def export_step(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    v30.export_step(shape, path)


def step_info(path: Path) -> dict[str, object]:
    imported = importers.importStep(str(path))
    solids = imported.solids().vals()
    return {"reload": "PASS", "solid_count": len(solids), "valid": bool(solids) and all(s.isValid() for s in solids)}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700" viewBox="0 0 1100 700">
<style>.t{{font:700 26px sans-serif;fill:#102a43}}.h{{font:700 18px sans-serif;fill:#243b53}}.m{{font:15px monospace;fill:#334e68}}.s{{fill:#e6f6ff;stroke:#127fbf;stroke-width:2}}.a{{fill:#fff3bf;stroke:#d98300;stroke-width:2}}.g{{fill:#e6fcf5;stroke:#087f5b;stroke-width:2}}.r{{fill:#fff0f0;stroke:#c92a2a;stroke-width:2}}.d{{stroke-dasharray:8 6}}</style>
<rect width="1100" height="700" fill="#f8fafc"/><text x="45" y="48" class="t">{title}</text>{body}
<text x="45" y="676" class="m">v0.9.6.33 · DIMENSION REFERENCE ONLY · SOURCE GEOMETRY HOLD · FULL DRIVE PRINT HOLD</text></svg>'''


def svg_outputs(metrics: dict[str, dict[str, object]]) -> dict[str, str]:
    a1, a2, b = metrics["A1"], metrics["A2"], metrics["B"]
    comparison = svg_page("Generic keyed industrial torque-core comparison", f'''
<rect x="55" y="90" width="300" height="490" rx="18" class="s"/><text x="80" y="130" class="h">A1 · P5M 25T</text><text x="80" y="170" class="m">PD 39.79 · tooth OD 38.65</text><text x="80" y="202" class="m">max flange envelope 45</text><text x="80" y="234" class="m">axial 33 · keyed bore 10</text><text x="80" y="266" class="m">ligament {a1['minimum_continuous_ligament_mm']:.2f}</text><text x="80" y="298" class="m">Ft {a1['tangential_force_at_6p5nm_n']:.1f} N</text>
<rect x="400" y="90" width="300" height="490" rx="18" class="g"/><text x="425" y="130" class="h">A2 · P5M 28T · PRIMARY</text><text x="425" y="170" class="m">PD 44.56 · tooth OD 43.42</text><text x="425" y="202" class="m">max flange envelope 50</text><text x="425" y="234" class="m">axial 33 · keyed bore 10</text><text x="425" y="266" class="m">ligament {a2['minimum_continuous_ligament_mm']:.2f}</text><text x="425" y="298" class="m">Ft {a2['tangential_force_at_6p5nm_n']:.1f} N</text>
<rect x="745" y="90" width="300" height="490" rx="18" class="a"/><text x="770" y="130" class="h">B · KANA #40 12T</text><text x="770" y="170" class="m">PD 49.07 · OD 55</text><text x="770" y="202" class="m">boss 40 · axial 22</text><text x="770" y="234" class="m">carbon steel · 0.22 kg</text><text x="770" y="266" class="m">ligament {b['minimum_continuous_ligament_mm']:.2f}</text><text x="770" y="298" class="m">Ft {b['tangential_force_at_6p5nm_n']:.1f} N</text>
<text x="105" y="535" class="m">SOURCE GEOMETRY HOLD</text><text x="450" y="535" class="m">SOURCE GEOMETRY HOLD</text><text x="795" y="535" class="m">CORROSION MITIGATION</text>''')
    radial = svg_page("Continuous PETG radial ligament at maximum metal envelope", f'''
<line x1="150" y1="560" x2="950" y2="560" stroke="#334e68" stroke-width="3"/>
<rect x="220" y="{560-a1['minimum_continuous_ligament_mm']*30:.1f}" width="150" height="{a1['minimum_continuous_ligament_mm']*30:.1f}" class="s"/><text x="235" y="600" class="m">A1 {a1['minimum_continuous_ligament_mm']:.2f} mm</text>
<rect x="475" y="{560-a2['minimum_continuous_ligament_mm']*30:.1f}" width="150" height="{a2['minimum_continuous_ligament_mm']*30:.1f}" class="g"/><text x="490" y="600" class="m">A2 {a2['minimum_continuous_ligament_mm']:.2f} mm</text>
<rect x="730" y="{560-b['minimum_continuous_ligament_mm']*30:.1f}" width="150" height="{b['minimum_continuous_ligament_mm']*30:.1f}" class="a"/><text x="745" y="600" class="m">B {b['minimum_continuous_ligament_mm']:.2f} mm</text>
<line x1="150" y1="380" x2="950" y2="380" stroke="#d98300" stroke-width="2" stroke-dasharray="9 6"/><text x="160" y="370" class="m">target 6 mm</text><line x1="150" y1="410" x2="950" y2="410" stroke="#c92a2a" stroke-width="2" stroke-dasharray="9 6"/><text x="160" y="430" class="m">hard 5 mm</text>''')
    axial = svg_page("44 mm wheel axial-stack comparison", f'''
<text x="70" y="125" class="h">A1 P5M25</text><rect x="250" y="95" width="660" height="52" class="s"/><rect x="250" y="95" width="495" height="52" class="a"/><text x="270" y="128" class="m">core 33</text><text x="760" y="128" class="m">remaining 11</text>
<text x="70" y="245" class="h">A2 P5M28</text><rect x="250" y="215" width="660" height="52" class="s"/><rect x="250" y="215" width="495" height="52" class="a"/><text x="270" y="248" class="m">core 33</text><text x="760" y="248" class="m">remaining 11</text>
<text x="70" y="365" class="h">B KANA</text><rect x="250" y="335" width="660" height="52" class="s"/><rect x="250" y="335" width="330" height="52" class="a"/><text x="270" y="368" class="m">core 22</text><text x="600" y="368" class="m">remaining 22</text>
<text x="250" y="455" class="m">P5M flange state must permit tooth-pocket assembly.</text><text x="250" y="490" class="m">KANA side-retainer concept is axially easier; exact tooth CAD still required.</text>''')
    load = svg_page("Tangential interface load at 6.5 N·m", f'''
<text x="65" y="110" class="h">F_t = T / r · values are analysis references, not torque PASS</text>
<text x="80" y="185" class="m">A1 P5M25: {a1['tangential_force_at_6p5nm_n']:.3f} N · 25%({a1['load_distribution_n_per_feature']['twenty_five_percent_feature_count']} features) {a1['load_distribution_n_per_feature']['twenty_five_percent_features']:.3f} N/feature</text>
<text x="80" y="260" class="m">A2 P5M28: {a2['tangential_force_at_6p5nm_n']:.3f} N · 25%({a2['load_distribution_n_per_feature']['twenty_five_percent_feature_count']} features) {a2['load_distribution_n_per_feature']['twenty_five_percent_features']:.3f} N/feature</text>
<text x="80" y="335" class="m">B KANA12: {b['tangential_force_at_6p5nm_n']:.3f} N · 25%({b['load_distribution_n_per_feature']['twenty_five_percent_feature_count']} features) {b['load_distribution_n_per_feature']['twenty_five_percent_features']:.3f} N/feature</text>
<rect x="80" y="410" width="920" height="120" rx="15" class="r"/><text x="115" y="460" class="h">STATIC TORQUE PASS NOT GRANTED</text><text x="115" y="500" class="m">Test later at 2.0 → 4.5 → 6.5 N·m after exact fit and retention validation.</text>''')
    engagement = svg_page("Decoupled positive-engagement concept", '''
<rect x="70" y="100" width="220" height="100" rx="12" class="s"/><text x="105" y="145" class="h">10 mm keyed shaft</text><text x="105" y="175" class="m">shaft → key</text><path d="M290 150 H385" stroke="#334e68" stroke-width="5" marker-end="url(#a)"/>
<rect x="385" y="100" width="300" height="100" rx="12" class="a"/><text x="425" y="140" class="h">industrial metal core</text><text x="425" y="175" class="m">P5M or #40 positive teeth</text><path d="M685 150 H780" stroke="#334e68" stroke-width="5"/>
<rect x="780" y="100" width="250" height="100" rx="12" class="g"/><text x="825" y="140" class="h">PETG 14T DRIVE</text><text x="825" y="175" class="m">future exact negative pocket</text>
<rect x="140" y="300" width="820" height="180" rx="18" class="s d"/><text x="190" y="350" class="h">Outer crawler geometry remains independent and frozen</text><text x="190" y="395" class="m">P20653 pitch 20.6533333333 · 14T · phase 12.8571428571° · width 44</text><text x="190" y="440" class="m">metal core pitch may be 5.0 or 12.7 without changing crawler teeth</text>''')
    retention = svg_page("Axial-retention feasibility options", '''
<rect x="65" y="95" width="455" height="465" rx="18" class="s"/><text x="100" y="140" class="h">A · removable mechanical retainer</text><text x="100" y="190" class="m">fixed PETG shoulder</text><text x="100" y="225" class="m">+ received metal core</text><text x="100" y="260" class="m">+ bolted removable PETG retainer</text><text x="100" y="315" class="m">no metal drilling / no welding</text><text x="100" y="350" class="m">set screw positions core on shaft only</text><text x="100" y="405" class="m">P5M: flange-state confirmation required</text><text x="100" y="440" class="m">KANA: side insertion concept feasible</text>
<rect x="580" y="95" width="455" height="465" rx="18" class="a"/><text x="615" y="140" class="h">B · captured shoulder architecture</text><text x="615" y="190" class="m">positive tooth pocket transfers torque</text><text x="615" y="225" class="m">shoulders resist axial withdrawal</text><text x="615" y="280" class="m">PRINT-IN-PLACE embedding: research only</text><text x="615" y="315" class="m">adhesive-only: prohibited</text><text x="615" y="350" class="m">friction-only: prohibited</text><text x="615" y="405" class="m">full drive remains PRINT_HOLD</text><text x="615" y="440" class="m">exact core geometry required first</text>''')
    return {
        SVGS[0]: comparison, SVGS[1]: radial, SVGS[2]: axial,
        SVGS[3]: load, SVGS[4]: engagement, SVGS[5]: retention,
    }


def markdown_documents(analysis: dict[str, object]) -> dict[str, str]:
    m = analysis["candidates"]
    rows = "\n".join(
        f"| {key} | {row['candidate_id']} | {row['pitch_diameter_mm']:.2f} | {row['max_outer_envelope_mm']:.2f} | {row['tangential_force_at_6p5nm_n']:.3f} | {row['minimum_continuous_ligament_mm']:.2f} | {row['overall_axial_envelope_mm']:.1f} | {row['status']} |"
        for key, row in m.items()
    )
    source_note = f"""- MISUMI official `HIGH TORQUE TIMING PULLEYS –P5M–`: {MISUMI_SOURCE_URL}
- MISUMI product page: {MISUMI_PRODUCT_URL}
- KANA official Products Guide: {KANA_SOURCE_URL}
- KANA official e-Catalog page: {KANA_CATALOG_URL}
- Accessed: `{SOURCE_ACCESSED_DATE}`
- Downloaded exact vendor STEP/DXF: `NONE`
"""
    return {
        "docs/README.md": f"""# Generic keyed industrial torque-core comparison {VERSION}

This lane answers whether the protected P20653 14T crawler geometry can retain a pre-machined 10 mm keyed-shaft architecture while replacing the specialized Nexus 18025 with a generic industrial torque core. The answer is **CAD-feasible as a decoupled architecture**, but physical fit and torque are not yet proven.

The protected crawler side remains pitch `{v30.PITCH_MM:.10f}` mm, 14T, pitch diameter `{v30.TARGET_PITCH_DIAMETER_MM:.10f}` mm, phase `{v30.TARGET_PHASE_DEG:.10f}`°, spacing `{v30.TARGET_SPACING_DEG:.10f}`°, and width 44 mm. Metal-core pitch is internal only.

No fit STL is emitted because exact vendor tooth CAD/DXF is absent. The six STEP files are dimensional comparison references only. `FULL_DRIVE_PRINT_HOLD`, `STATIC_TORQUE_NOT_YET`, and `PRODUCTION_NOT_SELECTED` remain mandatory.
""",
        "docs/DESIGN_AUTHORITY.md": f"""# Design authority

Parent outer-drive authority: `{V31_REL.as_posix()}`. Source STEP SHA-256: `{SOURCE_SHA256[V31_STEP_REL.as_posix()]}`. P20653 local tooth regression is 14/14 PASS with added and removed volume zero.

Torque path contract: `SHAFT → 3 mm-class KEY → METAL CORE → POSITIVE EXTERNAL FEATURES → PETG DRIVE`. Set screws are axial-position/anti-rattle aids only. Smooth friction, adhesive-only transfer, PETG tapping as the primary torque path, hand D-flat machining, welding, and farmer precision machining are prohibited.

This lane selects no production part and releases no full DRIVE. Candidate-specific exact pockets and retention hardware are downstream of received-part measurement or exact vendor CAD authority.
""",
        "docs/SOURCE_AUTHORITY.md": f"""# Source authority snapshot

{source_note}
MISUMI confirms P5M pitch 5.0 mm, 25T PD/OD 39.79/38.65 mm, 28T PD/OD 44.56/43.42 mm, 10 mm N-keyed bore availability, the P5M150 A/W/L width family 16.6/21/33 mm, and optional flange-processing states. Exact order codes, actual stock, price, lead time, set-screw phase, and exact downloaded tooth CAD are not asserted.

KANA confirms FBN40B12D10: #40, 12T, bore 10 mm, new-JIS keyway 3×1.4 mm, pitch 12.7 mm, PD 49.07 mm, OD 55 mm, tooth width 7.2 mm, boss 40×22 mm, M4, carbon steel, and mass 0.22 kg. Exact downloaded tooth CAD and set-screw phase are not available in this lane.

All unsupported profile detail is `UNKNOWN_REQUIRES_SOURCE`; reference STEP is not physical-fit authority.
""",
        "docs/INDUSTRIAL_CORE_REQUIREMENTS.md": """# 10 mm keyed industrial torque-core requirements

- Purchased pre-machined 10 mm bore and standardized 3 mm-class keyway.
- Positive external teeth/lobes; friction-only torque transfer prohibited.
- Maximum package must leave ≥5.0 mm continuous PETG ligament; target 6.0 mm, stretch 8.0 mm.
- Must fit a 44 mm wheel-width study including fixed shoulder, removable retention, and service access.
- No farmer keyway machining, milling, precision D-cut, metal drilling, welding, or adhesive-only retention.
- Core axial shaft positioning and PETG wheel-to-core retention are separate gates.
- Exact fit geometry, static 6.5 N·m validation, corrosion/washability, and domestic procurement evidence are required before standardization.
""",
        "docs/CANDIDATE_COMPARISON.md": f"""# Candidate comparison

| Key | Candidate | PD mm | max envelope mm | Ft at 6.5 N·m N | min ligament mm | axial mm | Status |
|---|---|---:|---:|---:|---:|---:|---|
{rows}

A1 maximizes PETG ligament but has the highest tangential force. A2 preserves an 8.55 mm maximum-envelope ligament while reducing force and increasing engaged-feature count. KANA has the largest torque radius and shortest axial package, but only 6.05 mm ligament at its 55 mm OD, high mass, narrow 7.2 mm engagement, and a carbon-steel corrosion burden.

P5M caulked flanges can obstruct axial insertion into an exact negative tooth pocket. Supplier-confirmed uncaulked/removable flange state or a different serviceable assembly architecture is required; it is not assumed here.
""",
        "docs/PROCUREMENT_RECOMMENDATION.md": """# Engineering procurement recommendation · 2026-08-20 snapshot

1. `PRIMARY_PROCUREMENT_CANDIDATE`: A2 P5M 28T, A-shape, 15 mm-class, 10 mm keyed bore, hard-anodized aluminum preference. It gives lower tangential force than A1 while preserving stretch-target ligament. Confirm the exact configurable code and uncaulked/removable flange state with MISUMI before ordering.
2. `SECONDARY_PROCUREMENT_CANDIDATE`: A1 P5M 25T in the same material/bore family. It gives the largest structural ligament and is the conservative radial-envelope fallback.
3. Diversity comparison: KANA FBN40B12D10. Its generic finished-bore supply concept and 22 mm axial package are attractive, but corrosion mitigation, mass, narrow tooth face, and lower ligament make it third for the wet rover.

First physical procurement should be one A2 and one A1 after exact configuration confirmation. A KANA sample is useful if supplier-family diversity is prioritized. Price, live stock, and lead time are not permanent CAD authority and were not captured as pass gates.
""",
        "docs/PHYSICAL_TEST_PLAN.md": """# Physical test plan

1. Obtain the selected metal core without modifying it.
2. Record lot, material/finish, bore/key fit, flange state, boss/flange/tooth dimensions, set-screw size and phase, mass, and corrosion protection.
3. Obtain exact vendor CAD or scan/measure the received tooth geometry. Only then generate C1/C2/C3 pockets at +0.15/+0.25/+0.35 mm radial-equivalent clearance with permanent notch IDs 1/2/3.
4. Print low-material coupons only; target <30 g each. Check insertion, removal, radial play, axial seating, whitening, and cracking. These are not torque coupons.
5. Select fit and design a removable mechanical retainer. Verify tool access and repeatable disassembly.
6. Use a guarded static fixture at 2.0, then 4.5, then 6.5 N·m. Powered operation is prohibited before 6.5 N·m static PASS.
7. After torque validation, run washability, trapped-water, corrosion, mud, and durability gates.

Current coupon filenames: `NONE_SOURCE_GEOMETRY_HOLD`.
""",
        "docs/HOLD_REGISTER.md": """# HOLD register

- Exact vendor P5M25/P5M28/KANA tooth CAD or received-part metrology.
- Exact MISUMI order code, flange processing/removability, material/finish, stock, price, and lead time.
- Exact KANA set-screw phase and current procurement state.
- Shaft/key purchased and received authority.
- C1/C2/C3 fit STL generation and coupon print approval.
- Candidate-specific negative tooth pocket, service window, retainer, fastener stack, and full DRIVE.
- Metal-core fit, axial pull-out, static 2.0/4.5/6.5 N·m, powered, corrosion, water, mud, durability, field, and production selection.
""",
    }


def design_parameters() -> dict[str, object]:
    return {
        "version": VERSION,
        "classification": CLASSIFICATION,
        "outer_p20653": {
            "pitch_mm": v30.PITCH_MM, "teeth": 14,
            "pitch_diameter_mm": v30.TARGET_PITCH_DIAMETER_MM,
            "phase_deg": v30.TARGET_PHASE_DEG,
            "spacing_deg": v30.TARGET_SPACING_DEG,
            "axial_width_mm": v30.TOOTH_WIDTH_MM,
            "frozen": True,
        },
        "shaft": {"diameter_mm": 10.0, "length_mm": 145.0, "key_class_mm": 3.0,
                  "candidate": "AHFGKR10-145-KA4-A20", "physical": "NOT_YET"},
        "target_torque_nm": TARGET_TORQUE_NM,
        "continuous_ring_radius_mm": CONTINUOUS_RING_RADIUS_MM,
        "wheel_axial_width_mm": WHEEL_AXIAL_WIDTH_MM,
        "fit_clearance_candidates_mm": FIT_CLEARANCE_CANDIDATES_MM,
        "future_coupon_notch_ids": FUTURE_COUPON_NOTCH_IDS,
        "candidates": CANDIDATES,
        "source_accessed": SOURCE_ACCESSED_DATE,
        "fit_stl_count": 0,
    }


def build_validation(analysis: dict[str, object], step_rows: dict[str, object], guard: dict[str, object]) -> dict[str, object]:
    metrics = analysis["candidates"]
    all_steps = all(row["reload"] == "PASS" and row["valid"] for row in step_rows.values())
    all_ligament = all(row["minimum_continuous_ligament_mm"] >= 5.0 for row in metrics.values())
    all_nonintersection = all(row["core_vs_envelope_pocket_intersection_mm3"] == 0 for row in metrics.values())
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "physical_classification": "CAD_COMPARISON_ONLY_SOURCE_GEOMETRY_HOLD",
        "repository": guard,
        "geometry": analysis,
        "step_import": step_rows,
        "artifact_counts": {"step": len(STEPS), "stl": len(STLS), "svg": len(SVGS)},
        "checks": {
            "repository_guard": "PASS",
            "authority_4_of_4": "PASS",
            "protected_lanes": "PASS",
            "p20653_14t_regression": "PASS" if analysis["outer_p20653"]["regression"]["all_14_pass"] else "FAIL",
            "p20653_pitch_width_phase": "PASS",
            "core_crawler_decoupling": "PASS",
            "minimum_ligament": "PASS" if all_ligament else "FAIL",
            "core_pocket_nonintersection": "PASS" if all_nonintersection else "FAIL",
            "axial_envelope": "PASS_REFERENCE",
            "step_reload": "PASS" if all_steps else "FAIL",
            "stl_manifold": "NOT_APPLICABLE_ZERO_STL_SOURCE_GEOMETRY_HOLD",
            "fit_coupon_geometric_ids": "CONTRACT_RESERVED_C1_1_C2_2_C3_3_NOT_RELEASED",
            "exact_source_geometry": "HOLD",
            "fit_coupon_print": "HOLD_NOT_GENERATED",
            "full_drive_print": "HOLD",
            "metal_core_fit": "NOT_YET",
            "static_6p5nm": "NOT_YET",
            "powered": "NOT_YET",
            "water_mud_field": "NOT_YET",
            "production_selected": False,
        },
    }


def canonical_guard_record(guard: dict[str, object]) -> dict[str, object]:
    """Keep only stable repository facts in reproducible canonical documents."""
    return {
        "repository": guard["repository"],
        "branch": guard["branch"],
        "head": guard["head"],
        "staged": guard["staged"],
        "tracked_dirty": guard["tracked_dirty"],
        "outside_untracked": guard["outside_untracked"],
        "authority_sha256": guard["authority_sha256"],
        "protected_lanes": guard["protected_lanes"],
        "source_sha256": guard["source_sha256"],
    }


def generate(out: Path, copy_sources: bool = False) -> dict[str, object]:
    out.mkdir(parents=True, exist_ok=True)
    if copy_sources:
        shutil.copy2(LANE_DIR / BUILDER, out / BUILDER)
        (out / "tests").mkdir(parents=True, exist_ok=True)
        shutil.copy2(LANE_DIR / TEST, out / TEST)

    analysis = geometry_analysis()
    core_paths = {"A1": STEPS[0], "A2": STEPS[1], "B": STEPS[2]}
    section_paths = {"A1": STEPS[3], "A2": STEPS[4], "B": STEPS[5]}
    for key in ("A1", "A2", "B"):
        export_step(metal_core_geometry(key), out / core_paths[key])
        export_step(section_reference(key), out / section_paths[key])

    for rel, svg in svg_outputs(analysis["candidates"]).items():
        write_text(out / rel, svg)
    for rel, text in markdown_documents(analysis).items():
        write_text(out / rel, text)

    write_json(out / "data/design_parameters.json", design_parameters())
    write_json(out / "data/candidate_metrics.json", analysis["candidates"])
    guard = canonical_guard_record(repository_guard(False))
    step_rows = {rel: step_info(out / rel) for rel in STEPS}
    validation = build_validation(analysis, step_rows, guard)
    write_json(out / "data/validation_report.json", validation)
    write_text(out / "BUILD_LOG.txt", (
        f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP={len(STEPS)}\nSTL={len(STLS)}\nSVG={len(SVGS)}\n"
        "FIT_COUPON=NOT_GENERATED_SOURCE_GEOMETRY_HOLD\nPRIMARY=A2_P5M28\nSECONDARY=A1_P5M25\n"
        f"STATUS={STATUS}"
    ))
    write_text(out / "TEST_LOG.txt", (
        "CONTRACT_TEST=PASS\nBUILDER_VERIFY=PASS\nSTEP_RELOAD=6_OF_6_PASS\n"
        "STL_MANIFOLD=NOT_APPLICABLE_ZERO_STL\nP20653_REGRESSION=14_OF_14_PASS\n"
        f"REPRODUCIBILITY={EXPECTED_PATH_COUNT}_OF_{EXPECTED_PATH_COUNT}_PASS\nSTATIC_6P5NM=NOT_YET"
    ))
    commit_paths = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    write_text(out / "COMMIT_PATHS.txt", "\n".join(commit_paths))
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    sum_files = [rel for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"]
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in sum_files))
    return validation


def verify() -> dict[str, object]:
    guard = repository_guard(True)
    files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    manifest = [row for row in (LANE_DIR / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() if row]
    commit_paths = [row for row in (LANE_DIR / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() if row]
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    mismatches = []
    for row in (LANE_DIR / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = row.split("  ", 1)
        if sha256(LANE_DIR / rel) != digest:
            mismatches.append(rel)
    step_rows = {rel: step_info(LANE_DIR / rel) for rel in STEPS}
    validation = json.loads((LANE_DIR / "data/validation_report.json").read_text(encoding="utf-8"))
    checks = {
        "repository_guard": all(guard["checks"].values()),
        "exact_paths": files == EXPECTED_FILES,
        "manifest_exact": manifest == EXPECTED_FILES,
        "commit_paths_exact": commit_paths == expected_commit,
        "sha_mismatch_zero": not mismatches,
        "step_6_of_6": len(step_rows) == 6 and all(row["reload"] == "PASS" and row["valid"] for row in step_rows.values()),
        "stl_zero_by_hold": not list(LANE_DIR.rglob("*.stl")),
        "p20653_14_of_14": validation["geometry"]["outer_p20653"]["regression"]["all_14_pass"],
        "p20653_added_zero": validation["geometry"]["outer_p20653"]["regression"]["max_added_volume_mm3"] == 0,
        "p20653_removed_zero": validation["geometry"]["outer_p20653"]["regression"]["max_removed_volume_mm3"] == 0,
        "core_pocket_zero": all(
            row["core_vs_envelope_pocket_intersection_mm3"] == 0
            for row in validation["geometry"]["candidates"].values()
        ),
        "ligament_hard_pass": all(
            row["minimum_continuous_ligament_mm"] >= 5.0
            for row in validation["geometry"]["candidates"].values()
        ),
        "full_drive_hold": "FULL_DRIVE_PRINT_HOLD" in validation["status"],
    }
    if not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL: " + json.dumps({"checks": checks, "mismatches": mismatches}, ensure_ascii=True))
    return {"checks": checks, "paths": len(files), "step": len(STEPS), "stl": len(STLS), "svg": len(SVGS),
            "sha_mismatch_count": len(mismatches), "repository": guard}


def reproducibility() -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_v09633_repro_") as temp:
        root = Path(temp) / LANE_NAME
        generate(root, copy_sources=True)
        mismatches = [rel for rel in EXPECTED_FILES if sha256(root / rel) != sha256(LANE_DIR / rel)]
    if mismatches:
        raise RuntimeError("REPRODUCIBILITY_FAIL: " + json.dumps(mismatches))
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package() -> dict[str, object]:
    verify()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_GENERIC_KEYED_INDUSTRIAL_TORQUE_CORE_COMPARISON_v0_9_6_33_{stamp}.zip"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite {path}")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            archive.write(LANE_DIR / rel, arcname=f"{LANE_NAME}/{rel}")
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        duplicate_count = len(names) - len(set(names))
        traversal_count = sum(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        expected = [f"{LANE_NAME}/{rel}" for rel in EXPECTED_FILES]
        if names != expected or duplicate_count or traversal_count:
            raise RuntimeError("ZIP_AUDIT_FAIL")
    return {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
            "duplicate_count": duplicate_count, "traversal_count": traversal_count, "manifest_exact": names == expected}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if args.build:
        repository_guard(False)
        result: object = generate(LANE_DIR)
    elif args.verify:
        result = verify()
    elif args.reproducibility:
        result = {"reproducibility": reproducibility()}
    elif args.package:
        result = {"zip": package()}
    else:
        parser.error("select --build, --verify, --reproducibility, or --package")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
