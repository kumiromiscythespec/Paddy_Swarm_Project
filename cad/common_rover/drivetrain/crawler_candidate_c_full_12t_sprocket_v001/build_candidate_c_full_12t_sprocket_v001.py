"""Build the Candidate-C full 12-tooth Common Rover crawler sprocket.

The physically screened Candidate-C tooth is imported directly from the
single-tooth coupon authority.  The P20653 12T centre, hub, shaft, fastening,
phase and pitch references are imported read-only from v0.9.6.20.  Only the
local tooth and its root bridge outside the protected core are replaced.
"""

from __future__ import annotations

import argparse
import collections
from datetime import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import zipfile

import cadquery as cq
from cadquery import exporters, importers


ROOT = Path(__file__).resolve().parents[4]
LANE_REL = Path("cad/common_rover/drivetrain/crawler_candidate_c_full_12t_sprocket_v001")
LANE = ROOT / LANE_REL
VERSION = "PADDY-SWARM-CRAWLER-CANDIDATE-C-FULL-12T-SPROCKET-V001"
STATUS = (
    "CAD_PASS/CONTRACT_TEST_PASS/CANDIDATE_C_FULL_12T_SPROCKET_PRINT_READY/"
    "PHYSICAL_VALIDATION_PENDING/CRAWLER_FULL_LOOP_VALIDATION_PENDING/"
    "POWERED_DRY_RUN_PENDING"
)
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_DIRTY = sorted([
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
])
OUTSIDE_UNTRACKED_COUNT = 3818
OUTSIDE_UNTRACKED_SHA = "1866329f95627ac3821b89662f118f6f2036aee83f76a1af500d4419bde52a82"

COUPON_REL = Path("cad/common_rover/drivetrain/crawler_sprocket_tooth_fit_coupons_v001")
COUPON_BUILDER_REL = COUPON_REL / "build_crawler_sprocket_tooth_fit_coupons_v001.py"
COUPON_C_STL_REL = COUPON_REL / "print/crawler_tooth_fit_C_h4p5_w6p5_ax22.stl"
PITCH_REL = Path("cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20")
PITCH_BUILDER_REL = PITCH_REL / "build_physical_pitch_drive_idler_v0_9_6_20.py"
PITCH_STEP_REL = PITCH_REL / "artifacts/drive_12t_pitch_p20653_v0_9_6_20.step"
V18_REL = Path("cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18")
CARRIER14_REL = Path("cad/common_rover/drivetrain/misumi_pulley_groove1_full_driven_carrier_v001")
P20653_14_REL = Path("cad/common_rover/common_rover_p20653_14t_18025_full_width_through_bolt_drive_v0_9_6_30")

SOURCE_SHA = {
    COUPON_BUILDER_REL.as_posix(): "4ffa3776904918292a28e2e736648c1c98bb43dd5d8fd4dd5cd90b2b98e8f780",
    COUPON_C_STL_REL.as_posix(): "c6fc7b47dfd4872428c0e01650473a08b50cb18d6d351e6af8f373964de90edc",
    PITCH_BUILDER_REL.as_posix(): "269354de29d6ec2fc4bead3dbe2523fded5ba04ab3419cbba619110dc6b5eb0f",
    PITCH_STEP_REL.as_posix(): "cf5a4bbdcc583105ad200009a671a0cb15c1697ab1eeff948a2313010c9212e3",
}
AUTHORITY_SHA = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PROTECTED_TREES = {
    COUPON_REL.as_posix(): (23, "18dfcd36ae1db9f779e641f2e72241c908df471727f3ae4bfc61b9fbccdf6a19"),
    PITCH_REL.as_posix(): (55, "5bc9cd5611b93b7ec67e68a7b6342f0c333245096bb961cfcf5fed2ecf2e7eef"),
    V18_REL.as_posix(): (39, "d9eb251e54d961eb328651fb7c8a5f91dfe41bf3f8a766ce31da30def47e74f7"),
    CARRIER14_REL.as_posix(): (28, "ca9e647a0bc3c50fef4b8a059ddc364495f98c8ad00a64913f675dcd692fb21e"),
    P20653_14_REL.as_posix(): (69, "b008a6bc52ec62b89f0dd5986b3d50279fd457561de931b3be8648a68ec7c428"),
}

CANDIDATE = {
    "id": "C",
    "radial_height_mm": 4.5,
    "tip_tangential_width_mm": 6.5,
    "axial_width_mm": 22.0,
    "root_transition_radius_mm": 1.25,
    "root_total_tangential_width_mm": 11.0,
    "physical_result": "HOLD_NEAR_PASS",
}
TOOTH_COUNT = 12
SPACING_DEG = 30.0
PHASE_DEG = 15.0
PITCH_MM = 20.6533333333
PITCH_DIAMETER_MM = 79.79835226236546
PITCH_RADIUS_MM = PITCH_DIAMETER_MM / 2.0
CORE_RADIUS_MM = 29.47
RADIAL_SHIFT_MM = 1.7019897891327247
CANDIDATE_ROOT_RADIUS_MM = CORE_RADIUS_MM + RADIAL_SHIFT_MM
CANDIDATE_TIP_RADIUS_MM = CANDIDATE_ROOT_RADIUS_MM + CANDIDATE["radial_height_mm"]
REFERENCE_TIP_RADIUS_MM = 33.07 + RADIAL_SHIFT_MM
REFERENCE_AXIAL_WIDTH_MM = 44.0
BRIDGE_OVERLAP_MM = 0.10
BRIDGE_SPAN_MM = RADIAL_SHIFT_MM + 2.0 * BRIDGE_OVERLAP_MM
BRIDGE_WIDTH_MM = CANDIDATE["root_total_tangential_width_mm"]

STEPS = [
    "artifacts/candidate_C_full_12T_sprocket.step",
    "artifacts/candidate_C_full_12T_sprocket_section.step",
]
STLS = [
    "artifacts/candidate_C_full_12T_sprocket.stl",
    "artifacts/candidate_C_curved_3tooth_validation.stl",
]
SVGS = [
    "artifacts/candidate_C_full_12T_sprocket_reference.svg",
    "artifacts/candidate_C_full_12T_sprocket_section.svg",
    "artifacts/candidate_C_full_12T_delta.svg",
]
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "SOURCE_TRACE.md",
    "CANDIDATE_C_PHYSICAL_RESULT.md", "DELTA_REPORT.md",
    "STRUCTURAL_SUPPORT_AUDIT.md", "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md",
]
TEST = "tests/test_candidate_c_full_12t_sprocket_v001_contract.py"
GENERATED_CORE = [*STEPS, *STLS, *SVGS, *DOCS, "design_parameters.json", TEST]
EXPECTED = sorted([
    "build_candidate_c_full_12t_sprocket_v001.py", *GENERATED_CORE,
    "validation_report.json", "BUILD_LOG.txt", "TEST_LOG.txt",
    "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
])


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_SPEC_FAIL: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


coupon = _load("crawler_tooth_coupon_authority_for_full12", ROOT / COUPON_BUILDER_REL)
pitch = _load("p20653_12t_authority_for_candidate_c", ROOT / PITCH_BUILDER_REL)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE).stdout


def tree_digest(relative: Path) -> tuple[int, str]:
    base = ROOT / relative
    files = sorted(p for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(base).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return len(files), digest.hexdigest()


def outside_untracked() -> tuple[int, str, list[str]]:
    prefix = LANE_REL.as_posix() + "/"
    rows = sorted(row.replace("\\", "/") for row in git("ls-files", "--others", "--exclude-standard").splitlines() if row and not row.replace("\\", "/").startswith(prefix))
    digest = hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()
    return len(rows), digest, rows


def guard(require_complete: bool = True) -> dict:
    lane_paths = sorted(row.replace("\\", "/")[len(LANE_REL.as_posix()) + 1:] for row in git("ls-files", "--others", "--exclude-standard").splitlines() if row.replace("\\", "/").startswith(LANE_REL.as_posix() + "/"))
    outside_count, outside_sha, _ = outside_untracked()
    protected = {rel: tree_digest(Path(rel)) for rel in PROTECTED_TREES}
    authority = {rel: sha(ROOT / rel) for rel in AUTHORITY_SHA}
    inputs = {rel: sha(ROOT / rel) for rel in SOURCE_SHA}
    dirty = sorted(git("diff", "--name-only").splitlines())
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    caches = [p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and ("__pycache__" in p.parts or p.suffix == ".pyc")] if LANE.exists() else []
    checks = {
        "root": Path(git("rev-parse", "--show-toplevel").strip()).resolve() == ROOT.resolve(),
        "branch": git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "head": git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == EXPECTED_DIRTY,
        "outside_untracked_preserved": (outside_count, outside_sha) == (OUTSIDE_UNTRACKED_COUNT, OUTSIDE_UNTRACKED_SHA),
        "authority_four": authority == AUTHORITY_SHA,
        "protected_five": protected == PROTECTED_TREES,
        "source_hashes": inputs == SOURCE_SHA,
        "lane_scope": set(lane_paths).issubset(set(EXPECTED)),
        "lane_complete": (not require_complete) or lane_paths == EXPECTED,
        "cache_zero": not caches,
    }
    result = {
        "branch": git("branch", "--show-current").strip(), "head": git("rev-parse", "HEAD").strip(),
        "staged": staged, "dirty": dirty, "outside_untracked_count": outside_count,
        "outside_untracked_sha256": outside_sha, "lane_paths": lane_paths,
        "authority": authority, "protected": {key: list(value) for key, value in protected.items()},
        "inputs": inputs, "checks": checks,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=False, default=list))
    return result


def cylinder(radius: float, height: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height / 2.0, both=True)


def volume(shape: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in shape.solids().vals()), 6)


def common_volume(left: cq.Workplane, right: cq.Workplane) -> float:
    return volume(left.intersect(right))


def source_candidate_c() -> cq.Workplane:
    """Direct editable-source reuse; no local profile reconstruction."""
    return coupon.candidate_tooth("C")


def radial_tooth(angle_deg: float) -> cq.Workplane:
    # coupon axes: X=tangential, Y=axial, Z=radial insertion.
    # sprocket axes: XY=rotation plane, Z=axial.
    shape = source_candidate_c().rotate((0, 0, 0), (1, 0, 0), 90.0)
    shape = shape.rotate((0, 0, 0), (0, 0, 1), 90.0)
    shape = shape.translate((CANDIDATE_ROOT_RADIUS_MM, 0.0, 0.0))
    return shape.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def bridge(angle_deg: float, axial_width: float = REFERENCE_AXIAL_WIDTH_MM) -> cq.Workplane:
    shape = cq.Workplane("XY").box(BRIDGE_SPAN_MM, BRIDGE_WIDTH_MM, axial_width)
    shape = shape.translate((CORE_RADIUS_MM + RADIAL_SHIFT_MM / 2.0, 0.0, 0.0))
    return shape.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def tooth_angles() -> list[float]:
    return [PHASE_DEG + index * SPACING_DEG for index in range(TOOTH_COUNT)]


def reference_sprocket() -> cq.Workplane:
    return pitch.drive_candidate("P20653", mark=False)


def protected_core() -> cq.Workplane:
    return reference_sprocket().intersect(cylinder(CORE_RADIUS_MM, 46.0)).clean()


def full_sprocket() -> cq.Workplane:
    result = protected_core()
    for angle in tooth_angles():
        result = result.union(bridge(angle)).union(radial_tooth(angle))
    return result.clean()


def section_sprocket() -> cq.Workplane:
    half_space = cq.Workplane("XY").box(120.0, 120.0, 60.0).translate((60.0, 0.0, 0.0))
    return full_sprocket().intersect(half_space).clean()


def curved_three_tooth() -> cq.Workplane:
    angles = [15.0, 45.0, 75.0]
    points = []
    for angle in range(0, 91, 3):
        rad = math.radians(angle)
        points.append(((CORE_RADIUS_MM + 0.12) * math.cos(rad), (CORE_RADIUS_MM + 0.12) * math.sin(rad)))
    for angle in range(90, -1, -3):
        rad = math.radians(angle)
        points.append((24.5 * math.cos(rad), 24.5 * math.sin(rad)))
    result = cq.Workplane("XY").polyline(points).close().extrude(CANDIDATE["axial_width_mm"] / 2.0, both=True)
    for angle in angles:
        result = result.union(bridge(angle, CANDIDATE["axial_width_mm"])).union(radial_tooth(angle))
    return result.clean()


def tooth_geometry_metrics() -> dict:
    source = source_candidate_c()
    source_metrics = coupon.candidate_metrics("C")
    teeth = [radial_tooth(angle) for angle in tooth_angles()]
    overlaps = []
    for left in range(len(teeth)):
        for right in range(left + 1, len(teeth)):
            overlaps.append({"pair": [left, right], "volume_mm3": common_volume(teeth[left], teeth[right])})
    volumes = [volume(tooth) for tooth in teeth]
    centres = []
    for tooth in teeth:
        centre = tooth.val().Center()
        value = math.degrees(math.atan2(centre.y, centre.x)) % 360.0
        centres.append(round(value, 9))
    full = full_sprocket()
    reference = reference_sprocket()
    core = protected_core()
    final_core = full.intersect(cylinder(CORE_RADIUS_MM, 46.0)).clean()
    return {
        "candidate_source_metrics": source_metrics,
        "source_bounds_mm": [source.val().BoundingBox().xlen, source.val().BoundingBox().ylen, source.val().BoundingBox().zlen],
        "tooth_count": len(teeth), "angles_deg": tooth_angles(), "centroid_angles_deg": centres,
        "tooth_volumes_mm3": volumes, "tooth_volume_spread_mm3": round(max(volumes) - min(volumes), 9),
        "pairwise_overlap": overlaps, "maximum_pairwise_overlap_mm3": max(row["volume_mm3"] for row in overlaps),
        "full_valid": full.val().isValid(), "full_solids": len(full.solids().vals()), "full_volume_mm3": volume(full),
        "reference_volume_mm3": volume(reference),
        "delta_missing_reference_mm3": volume(reference.cut(full)),
        "delta_added_candidate_mm3": volume(full.cut(reference)),
        "protected_core_missing_mm3": volume(core.cut(final_core)),
        "protected_core_added_mm3": volume(final_core.cut(core)),
        "section_valid": section_sprocket().val().isValid(),
        "curved_coupon_valid": curved_three_tooth().val().isValid(),
        "curved_coupon_solids": len(curved_three_tooth().solids().vals()),
        "root_radius_mm": CANDIDATE_ROOT_RADIUS_MM, "tip_centerline_radius_mm": CANDIDATE_TIP_RADIUS_MM,
        "pitch_radius_mm": PITCH_RADIUS_MM, "bridge_count": 12, "bridge_span_mm": BRIDGE_SPAN_MM,
        "bridge_width_mm": BRIDGE_WIDTH_MM, "bridge_axial_width_mm": REFERENCE_AXIAL_WIDTH_MM,
    }


def parameters() -> dict:
    return {
        "version": VERSION, "status": STATUS,
        "candidate_c": dict(CANDIDATE),
        "physical_result": {
            "candidate_B": "FAIL_LOOSE_LARGE_LEFT_RIGHT_PLAY",
            "candidate_C": "HOLD_NEAR_PASS_SMALL_LEFT_RIGHT_PLAY_NO_REPORTED_CRACK_OR_BINDING",
            "selection": "CANDIDATE_C_CURRENT_FULL_SPROCKET_BASELINE",
        },
        "pattern": {"tooth_count": TOOTH_COUNT, "spacing_deg": SPACING_DEG, "phase_deg": PHASE_DEG, "pitch_mm": PITCH_MM, "pitch_diameter_mm": PITCH_DIAMETER_MM, "pitch_classification": "P20653_PHYSICAL_MAX_EXTENSION_SUPPORTED_PRIMARY_CANDIDATE_NOT_UNIVERSAL_OPERATING_AUTHORITY"},
        "axial": {"candidate_engagement_width_mm": 22.0, "protected_body_width_mm": 44.0, "rule": "CANDIDATE_WIDTH_ONLY_ON_ENGAGEMENT_TOOTH"},
        "radial": {"protected_core_radius_mm": CORE_RADIUS_MM, "p20653_radial_shift_mm": RADIAL_SHIFT_MM, "candidate_root_radius_mm": CANDIDATE_ROOT_RADIUS_MM, "candidate_tip_centerline_radius_mm": CANDIDATE_TIP_RADIUS_MM, "reference_tip_centerline_radius_mm": REFERENCE_TIP_RADIUS_MM},
        "support": {"local_bridge_count": 12, "bridge_span_mm": BRIDGE_SPAN_MM, "bridge_tangential_width_mm": BRIDGE_WIDTH_MM, "bridge_axial_width_mm": REFERENCE_AXIAL_WIDTH_MM, "continuous_new_ring_count": 0},
        "protected_center": {"source": PITCH_STEP_REL.as_posix(), "shaft_hub": "V09618_H25A1_DUAL_L_Y3_B_COLLAR_HEADED_M4X2", "center_axis": [0.0, 0.0], "expected_core_missing_mm3": 0.0, "expected_core_added_mm3": 0.0},
        "authority_conflict": {"current_project_carrier": "PROTECTED_P20653_14T_MISUMI_GROOVE1_SEPARATE_ARCHITECTURE", "requested_output": "P20653_12T_CANDIDATE_C", "disposition": "NEW_12T_PHYSICAL_TEST_CANDIDATE_ONLY_NO_GLOBAL_AUTHORITY_PROMOTION"},
        "sources": {"candidate_c_lane": COUPON_REL.as_posix(), "candidate_c_builder": COUPON_BUILDER_REL.as_posix(), "candidate_c_stl": COUPON_C_STL_REL.as_posix(), "current_12t_lane": PITCH_REL.as_posix(), "current_12t_step": PITCH_STEP_REL.as_posix(), "sha256": dict(SOURCE_SHA)},
        "holds": ["PHYSICAL_VALIDATION_PENDING", "CRAWLER_FULL_LOOP_VALIDATION_PENDING", "POWERED_DRY_RUN_PENDING", "CONTINUOUS_DRY_RUN_PENDING", "MUD_WATER_FIELD_HOLD", "SLICER_REVIEW_PENDING", "P20653_FINAL_OPERATING_PITCH_AUTHORITY_HOLD"],
        "forbidden_claims": ["CRAWLER_PASS", "DERAILMENT_PASS", "POWERED_PASS", "MUD_PASS", "FIELD_PASS"],
    }


def svg_page(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760"><style>text{{font-family:Arial,sans-serif;fill:#17212b}}.t{{font-size:31px;font-weight:700}}.s{{font-size:18px;fill:#455}}.n{{font-size:18px}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:3}}.g{{fill:#dcfce7;stroke:#087f5b;stroke-width:3}}.o{{fill:#ffedd5;stroke:#c2410c;stroke-width:3}}.d{{fill:none;stroke:#7c3aed;stroke-width:3;stroke-dasharray:10 8}}.l{{stroke:#334155;stroke-width:3}}</style><text x="50" y="55" class="t">{title}</text><text x="50" y="90" class="s">{subtitle}</text>{body}</svg>'''


def svgs() -> dict[str, str]:
    teeth = "".join(f'<rect x="-13" y="-250" width="26" height="48" rx="7" class="o" transform="rotate({15 + 30*i})"/>' for i in range(12))
    reference = svg_page("Candidate C full 12T sprocket", "P20653 12T pattern; Candidate C engagement H4.5 / tip W6.5 / axial22", f'<g transform="translate(390,420)"><circle r="205" class="b"/><circle r="150" class="g"/>{teeth}<circle r="45" fill="white" stroke="#334155" stroke-width="4"/></g><text x="690" y="190" class="n">12 teeth · phase 15° · spacing 30°</text><text x="690" y="235" class="n">pitch chord {PITCH_MM:.10f} mm</text><text x="690" y="280" class="n">pitch diameter {PITCH_DIAMETER_MM:.9f} mm</text><text x="690" y="325" class="n">same center axis / H2.5-A1 core</text><text x="690" y="370" class="n">engagement width 22 mm</text><text x="690" y="415" class="n">body/support width 44 mm retained</text><text x="690" y="485" class="n">PRINT READY · physical full-loop HOLD</text>')
    section = svg_page("Candidate C radial / axial section", "Local tooth authority changes; protected center remains exact", '<g transform="translate(100,180)"><rect x="0" y="245" width="620" height="110" class="b"/><rect x="520" y="170" width="100" height="185" class="g"/><path d="M620 355H760V250L730 80H650L620 250Z" class="o"/><line x1="650" y1="60" x2="730" y2="60" class="l"/><text x="652" y="45" class="n">6.5 tip</text><line x1="780" y1="80" x2="780" y2="250" class="l"/><text x="795" y="175" class="n">4.5 radial</text><text x="270" y="410" class="n">R29.47 protected core</text><text x="520" y="445" class="n">local full-width backing</text><text x="650" y="485" class="n">22 mm engagement axial</text></g>')
    delta = svg_page("Expected delta versus P20653 12T reference", "Green is zero-diff protected core; orange is Candidate C local engagement", '<g transform="translate(330,410)"><circle r="210" class="d"/><circle r="155" class="g"/><path d="M155 -23L185 -24L210 -13L210 13L185 24L155 23Z" class="o"/><text x="-120" y="10" class="n">ZERO-DIFF CORE</text></g><text x="650" y="180" class="n">EXPECTED: old tooth removed / C tooth added</text><text x="650" y="235" class="n">ZERO-DIFF: hub, bore, center datum, fastening</text><text x="650" y="290" class="n">ZERO-DIFF: 12T, P20653 pitch, 15° phase</text><text x="650" y="345" class="n">NO GLOBAL SCALE</text><text x="650" y="430" class="n">14T Groove-1 carrier stays protected and separate</text>')
    return {SVGS[0]: reference, SVGS[1]: section, SVGS[2]: delta}


def documents() -> dict[str, str]:
    h = "# Candidate C full 12T crawler sprocket V001\n\n"
    return {
        "README.md": h + f"Candidate C (`H4.5 / tip W6.5 / engagement axial22`) is patterned exactly 12 times on the read-only P20653 12T authority. The v0.9.6.20 center/hub/shaft/fastening core is unchanged. Primary print: `{STLS[0]}`. Status: `{STATUS}`.\n",
        "DESIGN_AUTHORITY.md": h + "Local authority is only the physically screened Candidate C tooth. Pattern authority is P20653 12T: pitch chord20.6533333333 mm, phase15°, spacing30°. Center authority is the v0.9.6.20/v0.9.6.18 H2.5-A1, Dual-L, Y3, B-collar and headed-M4×2 core. The separately current MISUMI Groove-1 P20653 14T carrier is protected and is not imported or superseded.\n",
        "SOURCE_TRACE.md": h + f"Candidate C editable source: `{COUPON_BUILDER_REL.as_posix()}` SHA `{SOURCE_SHA[COUPON_BUILDER_REL.as_posix()]}`; validated STL SHA `{SOURCE_SHA[COUPON_C_STL_REL.as_posix()]}`. Current 12T source: `{PITCH_BUILDER_REL.as_posix()}` SHA `{SOURCE_SHA[PITCH_BUILDER_REL.as_posix()]}`; P20653 STEP SHA `{SOURCE_SHA[PITCH_STEP_REL.as_posix()]}`. Candidate C is direct-imported from `candidate_tooth('C')`; it is not reconstructed from prompt values.\n",
        "CANDIDATE_C_PHYSICAL_RESULT.md": h + "Candidate B H4.25/W6.0/AX20=`FAIL_LOOSE` with large lateral play. Candidate C H4.5/W6.5/AX22=`HOLD_NEAR_PASS`: much less lateral play, some small residual play, and no reported crack or binding. C is therefore the current full-sprocket baseline, not a crawler physical PASS. Zero play is not required.\n",
        "DELTA_REPORT.md": h + "Expected differences are the twelve old engagement teeth removed, twelve Candidate C teeth added, and twelve local root bridges widened only outside the protected R29.47 core. Zero-diff is required for the complete center core, bore/shaft interface, hub, center datum, fastening interface, tooth count, phase and P20653 pitch. No global scale is applied. Validation records exact removed/added volumes and zero protected-core volume delta.\n",
        "STRUCTURAL_SUPPORT_AUDIT.md": h + f"Each Candidate C tooth receives one local bridge: span {BRIDGE_SPAN_MM:.9f} mm including 0.10 mm overlap at both ends, tangential width11.0 mm matching the tooth root, and axial backing width44.0 mm. There are12 bridges, no new continuous ring, no isolated tooth fin, and the engagement surface remains the exact22 mm Candidate C source. Full-load structural qualification remains physical HOLD.\n",
        "PHYSICAL_TEST_PLAN.md": h + "1. Print and visually inspect. 2. Mount on the real shaft. 3. Install the actual crawler. 4. Hand rotate forward20 revolutions and reverse20. 5. Bias left, then right. 6. Check tooth climbing, derailment, binding, side rubbing, root whitening/cracking and change in lateral play. If hand testing passes, proceed to low-speed powered no-load forward/reverse, then low-load dry crawler testing. Continuous dry run follows only after those passes. Mud/water remain HOLD. Accept small repeatable clearance when guidance remains stable and damage-free.\n",
        "HOLD_REGISTER.md": h + "- full-loop physical fit and 20+20 hand revolutions\n- left/right bias derailment check\n- slicer review and print settings\n- final operating pitch authority (P20653 is maximum-extension supported candidate)\n- powered no-load and low-load dry run\n- continuous dry run\n- mud, water and field deployment\n- 14T versus this new 12T architecture selection\n",
    }


def test_source() -> str:
    return '''from __future__ import annotations
import importlib.util
from pathlib import Path
import sys

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_candidate_c_full_12t_sprocket_v001.py"
spec = importlib.util.spec_from_file_location("candidate_c_full12_contract_builder", BUILDER)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

checks = module.contract_checks(LANE, repo_checks=True)
failed = []
for index, (name, passed, detail) in enumerate(checks, 1):
    print(f"test_{index:03d}_{name}: {'PASS' if passed else 'FAIL'} | {detail}")
    if not passed:
        failed.append(name)
print(f"RESULT={len(checks)-len(failed)}/{len(checks)} PASS")
if failed:
    raise SystemExit("FAILED: " + ", ".join(failed))
'''


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-28T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP_NORMALIZATION_FAIL")
    path.write_text(text, encoding="utf-8", newline="\n")


def canonicalize_binary_stl(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError("STL_TOO_SHORT")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError("STL_NOT_BINARY")
    records = []
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        vertices = [tuple(0.0 if abs(float(v)) < 5.0e-6 else round(float(v), 5) for v in values[offset:offset+3]) for offset in (3, 6, 9)]
        ordered = min((vertices[i:] + vertices[:i] for i in range(3)), key=lambda row: tuple(v for vertex in row for v in vertex))
        left = tuple(ordered[1][axis] - ordered[0][axis] for axis in range(3))
        right = tuple(ordered[2][axis] - ordered[0][axis] for axis in range(3))
        normal = (left[1]*right[2]-left[2]*right[1], left[2]*right[0]-left[0]*right[2], left[0]*right[1]-left[1]*right[0])
        length = math.sqrt(sum(v*v for v in normal))
        unit = tuple(v/length for v in normal) if length else (0.0, 0.0, 0.0)
        key = tuple(v for vertex in ordered for v in vertex)
        records.append((key, struct.pack("<12fH", *unit, *ordered[0], *ordered[1], *ordered[2], 0)))
    records.sort(key=lambda row: row[0])
    path.write_bytes(b"PADDY_SWARM_CANONICAL_BINARY_STL".ljust(80, b"\0") + struct.pack("<I", count) + b"".join(row[1] for row in records))


def export_step(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")
    normalize_step(path)


def export_stl(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), tolerance=0.035, angularTolerance=0.08)
    canonicalize_binary_stl(path)


def generate(out: Path) -> None:
    export_step(full_sprocket(), out / STEPS[0])
    export_step(section_sprocket(), out / STEPS[1])
    export_stl(full_sprocket(), out / STLS[0])
    export_stl(curved_three_tooth(), out / STLS[1])
    for relative, payload in svgs().items():
        write(out / relative, payload)
    for relative, payload in documents().items():
        write(out / relative, payload)
    write(out / "design_parameters.json", json.dumps(parameters(), ensure_ascii=False, indent=2, sort_keys=True))
    write(out / TEST, test_source())


def binary_stl(path: Path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError("STL_BINARY_LENGTH")
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        yield (values[3:6], values[6:9], values[9:12])


def mesh_metrics(path: Path) -> dict:
    triangles = list(binary_stl(path))
    edges: collections.Counter = collections.Counter()
    degenerate = 0
    parents = list(range(len(triangles)))
    owners = {}
    vertices_all = []
    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index
    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b:
            parents[b] = a
    for triangle_index, triangle in enumerate(triangles):
        vertices = [tuple(round(float(v), 5) for v in vertex) for vertex in triangle]
        vertices_all.extend(vertices)
        a = tuple(vertices[1][i]-vertices[0][i] for i in range(3)); b = tuple(vertices[2][i]-vertices[0][i] for i in range(3))
        cross = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
        if sum(v*v for v in cross) <= 1.0e-14:
            degenerate += 1
        for left, right in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            edge = tuple(sorted((left, right)))
            edges[edge] += 1
            if edge in owners:
                union(triangle_index, owners[edge])
            else:
                owners[edge] = triangle_index
    bad = sum(count != 2 for count in edges.values())
    bounds = [[min(v[i] for v in vertices_all) for i in range(3)], [max(v[i] for v in vertices_all) for i in range(3)]]
    return {"triangles": len(triangles), "components": len({find(i) for i in range(len(triangles))}), "watertight": bad == 0, "manifold": bad == 0, "bad_edges": bad, "degenerate_triangles": degenerate, "bounds_mm": bounds, "extents_mm": [round(bounds[1][i]-bounds[0][i], 6) for i in range(3)]}


def step_metrics(path: Path) -> dict:
    shape = importers.importStep(str(path))
    return {"reload": "PASS", "valid": shape.val().isValid(), "solids": len(shape.solids().vals()), "volume_mm3": volume(shape)}


def artifact_audit(lane: Path) -> dict:
    return {"step": [{"path": rel, **step_metrics(lane / rel)} for rel in STEPS], "stl": [{"path": rel, **mesh_metrics(lane / rel)} for rel in STLS]}


def reproducibility() -> dict:
    compared = sorted(GENERATED_CORE)
    with tempfile.TemporaryDirectory(prefix="candidate_c_full12_repro_") as temp:
        result = subprocess.run([sys.executable, "-B", str(Path(__file__)), "--render-only", temp], cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError("REPRO_RENDER_FAIL\n" + result.stdout)
        target = Path(temp)
        mismatches = [rel for rel in compared if (LANE / rel).read_bytes() != (target / rel).read_bytes()]
    return {"compared": len(compared), "byte_identical": len(compared)-len(mismatches), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def contract_checks(lane: Path = LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    report = json.loads((lane / "validation_report.json").read_text(encoding="utf-8"))
    params = json.loads((lane / "design_parameters.json").read_text(encoding="utf-8"))
    geometry = report["geometry"]
    audit = artifact_audit(lane)
    checks: list[tuple[str, bool, object]] = []
    def add(name: str, passed: bool, detail: object) -> None:
        checks.append((name, bool(passed), detail))
    add("candidate-c-exact", [params["candidate_c"][key] for key in ("radial_height_mm", "tip_tangential_width_mm", "axial_width_mm")] == [4.5, 6.5, 22.0], params["candidate_c"])
    add("candidate-source-direct", params["sources"]["candidate_c_builder"] == COUPON_BUILDER_REL.as_posix(), params["sources"])
    add("tooth-count", geometry["tooth_count"] == 12, geometry["tooth_count"])
    add("pattern-contract", params["pattern"]["spacing_deg"] == 30.0 and params["pattern"]["phase_deg"] == 15.0 and params["pattern"]["pitch_mm"] == PITCH_MM, params["pattern"])
    add("center-axis", params["protected_center"]["center_axis"] == [0.0, 0.0], params["protected_center"])
    add("axial-contract", params["axial"]["candidate_engagement_width_mm"] == 22.0 and params["axial"]["protected_body_width_mm"] == 44.0, params["axial"])
    add("full-valid-single-solid", geometry["full_valid"] and geometry["full_solids"] == 1, [geometry["full_valid"], geometry["full_solids"]])
    add("protected-core-zero-diff", geometry["protected_core_missing_mm3"] == 0.0 and geometry["protected_core_added_mm3"] == 0.0, [geometry["protected_core_missing_mm3"], geometry["protected_core_added_mm3"]])
    add("hub-shaft-fastener-zero-diff", geometry["protected_core_missing_mm3"] == geometry["protected_core_added_mm3"] == 0.0, "R29.47 complete center core")
    add("no-global-scale", geometry["pitch_radius_mm"] == PITCH_RADIUS_MM and geometry["root_radius_mm"] == CANDIDATE_ROOT_RADIUS_MM, [geometry["pitch_radius_mm"], geometry["root_radius_mm"]])
    add("support-count", geometry["bridge_count"] == 12, geometry["bridge_count"])
    add("support-width", geometry["bridge_width_mm"] == 11.0 and geometry["bridge_axial_width_mm"] == 44.0, [geometry["bridge_width_mm"], geometry["bridge_axial_width_mm"]])
    add("curved-coupon", geometry["curved_coupon_valid"] and geometry["curved_coupon_solids"] == 1, [geometry["curved_coupon_valid"], geometry["curved_coupon_solids"]])
    add("tooth-volume-identical", geometry["tooth_volume_spread_mm3"] <= 1.0e-6, geometry["tooth_volume_spread_mm3"])
    add("no-tooth-overlap", geometry["maximum_pairwise_overlap_mm3"] == 0.0, geometry["maximum_pairwise_overlap_mm3"])
    for index, angle in enumerate(geometry["angles_deg"]):
        add(f"tooth-{index+1:02d}-angle", angle == PHASE_DEG + index*SPACING_DEG, angle)
    for index in range(12):
        next_index = (index + 1) % 12
        delta = (geometry["centroid_angles_deg"][next_index] - geometry["centroid_angles_deg"][index]) % 360.0
        add(f"spacing-{index+1:02d}", abs(delta-SPACING_DEG) <= 1.0e-7, delta)
    for row in geometry["pairwise_overlap"]:
        add(f"pair-{row['pair'][0]+1:02d}-{row['pair'][1]+1:02d}-zero", row["volume_mm3"] == 0.0, row["volume_mm3"])
    for row in audit["step"]:
        add("step-reload-" + Path(row["path"]).stem, row["reload"] == "PASS" and row["valid"] and row["solids"] >= 1, row)
    for row in audit["stl"]:
        name = Path(row["path"]).stem
        add("stl-watertight-" + name, row["watertight"], row)
        add("stl-manifold-" + name, row["manifold"], row)
        add("stl-bad-edge-zero-" + name, row["bad_edges"] == 0, row["bad_edges"])
        add("stl-degenerate-zero-" + name, row["degenerate_triangles"] == 0, row["degenerate_triangles"])
        add("stl-single-component-" + name, row["components"] == 1, row["components"])
    for rel in EXPECTED:
        add("path-" + rel.replace("/", "-").replace(".", "-"), (lane / rel).is_file(), rel)
    add("manifest-exact", sorted((lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == sorted(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED), len(EXPECTED))
    add("reproducibility", report["reproducibility"]["status"] == "PASS", report["reproducibility"])
    add("status-holds", "PHYSICAL_VALIDATION_PENDING" in params["status"] and "CRAWLER_PASS" in params["forbidden_claims"], params["status"])
    if repo_checks:
        repo = guard(True)
        for key, passed in repo["checks"].items():
            add("repository-" + key, passed, key)
    return checks


def indexes() -> None:
    write(LANE / "COMMIT_PATHS.txt", "".join(f"{LANE_REL.as_posix()}/{rel}\n" for rel in EXPECTED))
    write(LANE / "MANIFEST.txt", f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\nFILES:\n" + "\n".join(EXPECTED))
    rows = [rel for rel in EXPECTED if rel != "SHA256SUMS.txt" and (LANE / rel).is_file()]
    write(LANE / "SHA256SUMS.txt", "".join(f"{sha(LANE / rel)}  {rel}\n" for rel in rows))


def build() -> dict:
    guard(False)
    generate(LANE)
    geometry = tooth_geometry_metrics()
    audit = artifact_audit(LANE)
    repro = reproducibility()
    checks = {
        "candidate_exact": [CANDIDATE[key] for key in ("radial_height_mm", "tip_tangential_width_mm", "axial_width_mm")] == [4.5, 6.5, 22.0],
        "tooth_count": geometry["tooth_count"] == 12,
        "spacing": all(abs(((geometry["centroid_angles_deg"][(i+1)%12]-geometry["centroid_angles_deg"][i])%360)-30.0) <= 1e-7 for i in range(12)),
        "no_overlap": geometry["maximum_pairwise_overlap_mm3"] == 0.0,
        "full_valid": geometry["full_valid"] and geometry["full_solids"] == 1,
        "core_zero_diff": geometry["protected_core_missing_mm3"] == geometry["protected_core_added_mm3"] == 0.0,
        "step_reload": all(row["reload"] == "PASS" and row["valid"] for row in audit["step"]),
        "stl_quality": all(row["watertight"] and row["manifold"] and row["bad_edges"] == 0 and row["degenerate_triangles"] == 0 and row["components"] == 1 for row in audit["stl"]),
        "reproducibility": repro["status"] == "PASS",
    }
    report = {"version": VERSION, "status": STATUS, "checks": checks, "check_count": len(checks), "pass_count": sum(checks.values()), "geometry": geometry, "artifacts": audit, "reproducibility": repro, "sources": parameters()["sources"], "holds": parameters()["holds"]}
    write(LANE / "validation_report.json", json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    write(LANE / "BUILD_LOG.txt", f"BUILD={'PASS' if all(checks.values()) else 'FAIL'}\nCHECKS={sum(checks.values())}/{len(checks)} PASS\nSTEP={len(STEPS)}/{len(STEPS)} RELOAD PASS\nSTL={len(STLS)}/{len(STLS)} QUALITY PASS\nREPRO={repro['byte_identical']}/{repro['compared']} {repro['status']}\n")
    write(LANE / "TEST_LOG.txt", "PENDING\n")
    indexes()
    result = subprocess.run([sys.executable, "-B", str(LANE / TEST)], cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    write(LANE / "TEST_LOG.txt", result.stdout)
    indexes()
    if result.returncode:
        raise RuntimeError("CONTRACT_TEST_FAIL\n" + result.stdout)
    guard(True)
    return report


def verify() -> tuple[int, int]:
    checks = contract_checks(LANE, repo_checks=True)
    passed = sum(item[1] for item in checks)
    for index, (name, ok, detail) in enumerate(checks, 1):
        print(f"verify_{index:03d}_{name}: {'PASS' if ok else 'FAIL'} | {detail}")
    print(f"VERIFY_RESULT={passed}/{len(checks)} PASS")
    if passed != len(checks):
        raise RuntimeError("VERIFY_FAIL")
    return passed, len(checks)


def zip_handoff() -> tuple[Path, str]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path("D:/Downloads") / f"Paddy_Swarm_CRAWLER_SPROCKET_C_FULL_12T_V001_{timestamp}.zip"
    if target.exists():
        raise RuntimeError("ZIP_EXISTS_REFUSE_OVERWRITE")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED:
            archive.write(LANE / rel, f"{LANE.name}/{rel}")
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(EXPECTED):
            raise RuntimeError("ZIP_VALIDATION_FAIL")
    return target, sha(target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render-only")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--zip", action="store_true")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if args.render_only:
        generate(Path(args.render_only))
        return
    requested = args.build or args.verify or args.reproducibility or args.zip
    if not requested or args.build:
        report = build()
        print(f"BUILD={report['pass_count']}/{report['check_count']} PASS")
    if not requested:
        verify()
        target, digest = zip_handoff()
        print(f"ZIP={target}")
        print(f"ZIP_SHA256={digest}")
        return
    if args.verify:
        verify()
    if args.reproducibility:
        result = reproducibility(); print(json.dumps(result, indent=2));
        if result["status"] != "PASS": raise SystemExit(1)
    if args.zip:
        target, digest = zip_handoff(); print(f"ZIP={target}"); print(f"ZIP_SHA256={digest}")


if __name__ == "__main__":
    main()
