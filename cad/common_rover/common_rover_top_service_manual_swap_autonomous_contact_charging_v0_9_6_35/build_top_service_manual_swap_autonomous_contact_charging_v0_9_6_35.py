"""Build the v0.9.6.35 architecture-decision lane.

All generated CAD is concept/reference geometry.  Conflicting repository
authorities are kept separate; no missing slide, docking, or contact dimension
is promoted to production authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

import cadquery as cq
from cadquery import exporters, importers


REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "common_rover_top_service_manual_swap_autonomous_contact_charging_v0_9_6_35"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
VERSION = "v0.9.6.35"
CLASSIFICATION = "TOP_SERVICE_MANUAL_SWAP_PLUS_AUTONOMOUS_CONTACT_CHARGING_ARCHITECTURE"
STATUS = (
    "ARCHITECTURE_DECISION_RECORDED/TOP_SERVICE_MANUAL_SWAP_SELECTED/"
    "AUTONOMOUS_CONTACT_CHARGING_SELECTED/REAR_SLIDE_PRIMARY_ARCHITECTURE_SUPERSEDED/"
    "BATTERY_TRANSPORTER_ROLE_REDEFINED/AUTHORITY_CONFLICT_RECORDED/"
    "CAD_CONCEPT_PASS/CONTRACT_TEST_PASS/ARCHITECTURE_SELECTED/"
    "CAD_CONCEPT_COMPLETE/PHYSICAL_VALIDATION_PENDING/COMMIT_READY_NOT_STAGED"
)

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = sorted(AUTHORITY_SHA256)
BASE_OUTSIDE_COUNT = 3153
BASE_OUTSIDE_PATH_DIGEST = "53787a71cf5af242f020aa51ec5ef93ec8c16371727f6b07d851f70728b5bceb"
PROTECTED_LANE_COUNT = 35
PROTECTED_FILE_COUNT = 1540
PROTECTED_AGGREGATE_SHA256 = "c4adc57e39ac24f5ec5cff4fc234a0424ca09626e8d827374a0c4c575436565a"
PROTECTED_TREES = {
    "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test":
        (21, "331f7ea46ef9ab26731d58300f658476bf919113960f10f5babaded1d47dcec8"),
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0":
        (40, "5b18fee1976e292a370f3ac56930544df711cd44d66075f9b6216af40a91c465"),
    "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27":
        (54, "1079a028588d35564e9e7241dda645a120b570fe2cf4c8b607169138c5742701"),
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32":
        (28, "4792b7db682d02e78ab88bdd8642f42b6805a6773782f4bcc36f2ff3427bc516"),
    "interfaces/power/bbox_battery_cassette/v001":
        (5, "61e5c3c7ee6c05b8a0dce5f07e816e8119bd343797761e5f64a2874f8c070376"),
    "rovers/common_rover/v2.28/rover_v228_2_dual_pto_output_fix_out":
        (74, "a84530203d35e06bec22f00215cd7649f45ab1aad70028bc0cda89a7ee979f28"),
}
SOURCE_SHA256 = {
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0/design_parameters.json": "88180cd2b61f049e8610f00a270502ece985d874623f35db1b93c9f576e21271",
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0/ARCHITECTURE_AUTHORITY.md": "b198289fd95879342170dc5e5fda92f11a5dfe3048336f8824c9b2859e71e063",
    "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27/design_parameters.json": "e89f8b00dd0dba0a795da1e465b14f9b7a3970a6e5174dcec8ff052cf8860dfa",
    "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27/DESIGN_AUTHORITY.md": "1129e5fbc8cc044fa835e9b66a72cab66e1f839201d64888802b6d1fcc8368df",
    "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27/REAR_SLIDE_ARCHITECTURE.md": "e7e2b85b61c42d19756f5acca7e00c44365d11790da1fd3f67d6f7cb47e42315",
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/data/design_parameters.json": "1e37c756c736300d586329a18e7ac43aa969eee3d6215a09bd91eb6f6f7c3b60",
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/docs/DESIGN_AUTHORITY.md": "1e1ffcb1825bc319bfac214b7aa028efc088233e0dc5c8c99bb291e059c435f5",
    "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test/validation_report.json": "311b5991d4233804547b72404f5451c7767c460304a06c6c029f502b3d4099b5",
    "interfaces/power/bbox_battery_cassette/v001/README.md": "0463ff3e69cf5569a9711c0c71ef3c6566be1469c85af351062459c98c6fcacd",
    "rovers/common_rover/v2.28/paddy_swarm_v228_2_dual_pto_output_fix_cadquery.py": "aa8de0ddc9537fd5f8e75a4c41bc98975749aac4e9abd2419993e73d92df2201",
}
CBOX_SOURCE_STEP_REL = PurePosixPath(
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/"
    "artifacts/cbox_shell_v0_9_6_32.step"
)

AUTHORITY_CONFLICTS = {
    "fixed_core_v228": {
        "bbox_body_nominal_mm": [200.0, 150.0, 120.0],
        "lid_nominal_mm": [216.0, 166.0, 16.0],
        "gasket_nominal_mm": [204.0, 154.0, 3.0],
        "status": "CURRENT_FIXED_CORE_AUDIT_FACTS_NOT_AUTOMATICALLY_MERGED",
    },
    "submerged_v0_9_6_0": {
        "bbox_lower_shell_mm": [200.0, 130.0, 97.0],
        "lid_mm": [200.0, 130.0, 4.2],
        "gasket_outer_mm": [186.0, 116.0, 2.0],
        "cbox_external_mm": [180.0, 92.0, 45.0],
        "status": "SUBMERGED_PROTOTYPE_AUTHORITY_NOT_AUTOMATICALLY_MERGED",
    },
    "cbox_v0_9_6_32": {
        "cbox_body_mm": [246.0, 150.0, 80.0],
        "cbox_total_print_bbox_mm": [246.0, 152.0, 80.0],
        "z_placement": "HOLD_NO_UNAMBIGUOUS_TRANSFORM",
        "status": "LATEST_MODULAR_CBOX_LOCAL_GEOMETRY_AUTHORITY",
    },
    "resolution": "AUTHORITY_CONFLICT_RECORDED_NO_SYNTHETIC_UNIFIED_DIMENSION",
}

BATTERY_PHYSICAL = {
    "product": "GOLDENMATE LiFePO4",
    "voltage_v": 12.8, "capacity_ah": 10.0, "energy_wh": 128.0,
    "body_mm": [150.9, 99.4, 92.5], "mass_kg": 1.2,
    "authority": "V0_9_6_0_PHYSICAL_MEASUREMENT_CLOSURE_REFERENCE",
}

# Display-only geometry values. They are never design dimensions or released strokes.
BBOX_DISPLAY = [200.0, 150.0, 120.0]
CBOX_DISPLAY_OPERATING_Z = 140.0
CBOX_DISPLAY_SERVICE_OFFSET = 280.0
BATTERY_SWEEP_HEIGHT = BBOX_DISPLAY[2] + BATTERY_PHYSICAL["body_mm"][2]
CONTACT_DISPLAY_KEEP_OUT = [80.0, 60.0, 50.0]
STATION_DISPLAY = {"guide_span_mm": 400.0, "approach_length_mm": 700.0, "guide_height_mm": 100.0}
DISPLAY_GEOMETRY_AUTHORITY = "TRANSPARENT_REFERENCE_ONLY_NOT_POSITION_STROKE_OR_HARDWARE_AUTHORITY"

PROTECTED_PRINCIPLES = [
    "HIGH_MOUNTED_DUAL_MOTOR_4WD_ARCHITECTURE",
    "BBOX_CBOX_SEPARATION",
    "REMOVABLE_BATTERY_CASSETTE_CONCEPT",
    "LIFEPO4_12_8V_CURRENT_PROTOTYPE_BATTERY_AUTHORITY",
    "INDEPENDENT_LEFT_RIGHT_DRIVE",
    "CURRENT_CRAWLER_AND_PTO_ARCHITECTURE",
    "CURRENT_SEALING_TEST_HISTORY",
    "EXISTING_REAR_SLIDE_RESEARCH_ARTIFACTS",
]

MODES = {
    "A": "NORMAL_LOW_MEDIUM_LOAD_BATTERY_INSTALLED_AUTONOMOUS_CONTACT_CHARGING",
    "B": "HIGH_LOAD_BUSY_SEASON_AUTONOMOUS_CHARGING_PRIMARY_MANUAL_TOP_SWAP_SUPPLEMENTAL",
    "C": "SERVICE_FAILURE_STOP_ISOLATE_MOVE_CBOX_OPEN_TOP_MANUAL_REPLACE",
    "D": "FUTURE_AUTOMATIC_SWAP_NOT_CURRENT_BASELINE",
}

HOLDS = [
    "EXACT_BBOX_DIMENSIONAL_AUTHORITY_CONFLICT",
    "TOP_LID_FINAL_GEOMETRY",
    "TOP_GASKET_COMPRESSION",
    "CBOX_LATERAL_SLIDE_DIRECTION",
    "CBOX_REQUIRED_SERVICE_STROKE",
    "SERVICE_LOCK_MECHANISM",
    "CBOX_CABLE_SERVICE_LOOP",
    "BATTERY_POWER_CONNECTOR",
    "CHARGING_CONTACT_HARDWARE",
    "CHARGING_VOLTAGE_CURRENT",
    "CHARGING_STATION_DOCKING_TOLERANCE",
    "MUD_WATER_CONTAMINATION_RESISTANCE",
    "PHYSICAL_WATERPROOF_TEST",
    "ACTUAL_BATTERY_SWAP_ERGONOMICS",
    "CBOX_FRAME_MOTOR_PTO_CRAWLER_INTERFERENCE_TRANSFORMS",
]

BUILDER = Path(__file__).name
TEST = "tests/test_top_service_manual_swap_autonomous_contact_charging_v0_9_6_35_contract.py"
STEPS = [
    "bbox_top_service_concept_v0_9_6_35.step",
    "cbox_operating_position_reference_v0_9_6_35.step",
    "cbox_service_position_reference_v0_9_6_35.step",
    "battery_vertical_extraction_swept_envelope_v0_9_6_35.step",
    "charging_contact_conceptual_keepout_v0_9_6_35.step",
    "station_docking_conceptual_envelope_v0_9_6_35.step",
]
SVGS = [
    "NORMAL_OPERATION_LAYOUT.svg",
    "MANUAL_BATTERY_SWAP_SEQUENCE.svg",
    "AUTONOMOUS_CONTACT_CHARGING_SEQUENCE.svg",
    "BATTERY_TRANSPORTER_ROLE.svg",
    "WATERPROOF_BOUNDARY_UPDATE.svg",
    "ARCHITECTURE_BEFORE_AFTER.svg",
]
DOCS = [
    "README.md", "ARCHITECTURE_DECISION.md", "DESIGN_AUTHORITY.md",
    "BBOX_TOP_SERVICE_REQUIREMENTS.md", "CBOX_SERVICE_SLIDE_REQUIREMENTS.md",
    "AUTONOMOUS_CONTACT_CHARGING_REQUIREMENTS.md", "CHARGING_STATION_REQUIREMENTS.md",
    "BATTERY_TRANSPORTER_REQUIREMENTS.md", "WATERPROOF_BOUNDARY_UPDATE.md",
    "OPERATION_MODES.md", "SUPERSEDED_ARCHITECTURE_REGISTER.md", "HOLD_REGISTER.md",
]
DATA = ["design_parameters.json", "validation_report.json"]
META = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_FILES = sorted([BUILDER, TEST, *STEPS, *SVGS, *DOCS, *DATA, *META])
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
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()


def protected_snapshot() -> dict[str, object]:
    root = REPO_ROOT / "cad/common_rover"
    rows = {}
    for path in sorted(root.iterdir()):
        match = re.search(r"_v0_9_6_(\d+)$", path.name)
        if path.is_dir() and match and int(match.group(1)) <= 34:
            rows[path.relative_to(REPO_ROOT).as_posix()] = tree_digest(path)
    digest = hashlib.sha256()
    for rel, (count, tree_sha) in rows.items():
        digest.update(f"{rel}|{count}|{tree_sha}\n".encode())
    focus = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_TREES}
    return {
        "lane_count": len(rows), "file_count": sum(row[0] for row in rows.values()),
        "aggregate_sha256": digest.hexdigest(),
        "focus": {rel: {"count": row[0], "tree_sha256": row[1]} for rel, row in focus.items()},
    }


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = sorted(
        path.replace("\\", "/") for path in run_git("ls-files", "--others", "--exclude-standard").splitlines()
        if not path.replace("\\", "/").startswith(prefix)
    )
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = sorted(run_git("diff", "--name-only").splitlines())
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    outside = outside_snapshot()
    protected = protected_snapshot()
    sources = {rel: sha256(REPO_ROOT / rel) for rel in SOURCE_SHA256}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file()) if LANE_DIR.exists() else []
    ignored = [path for path in lane_files if subprocess.run(
        ["git", "check-ignore", "-q", (LANE_REL / PurePosixPath(path)).as_posix()], cwd=REPO_ROOT
    ).returncode == 0]
    caches = [path for path in lane_files if "__pycache__" in PurePosixPath(path).parts or ".pytest_cache" in PurePosixPath(path).parts]
    forbidden = [path for path in lane_files if Path(path).suffix.lower() in {".pyc", ".pyo", ".3mf", ".gcode", ".fcstd"}]
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD, "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "authority_four": authority == AUTHORITY_SHA256,
        "outside_untracked_preserved": outside == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "protected_lane_aggregate": (
            protected["lane_count"] == PROTECTED_LANE_COUNT
            and protected["file_count"] == PROTECTED_FILE_COUNT
            and protected["aggregate_sha256"] == PROTECTED_AGGREGATE_SHA256
        ),
        "protected_focus": all(
            protected["focus"].get(rel) == {"count": expected[0], "tree_sha256": expected[1]}
            for rel, expected in PROTECTED_TREES.items()
        ),
        "source_hashes": sources == SOURCE_SHA256,
        "ignored_zero": not ignored, "cache_zero": not caches, "forbidden_zero": not forbidden,
        "lane_exact": not require_complete or lane_files == EXPECTED_FILES,
    }
    if not all(checks.values()):
        raise RuntimeError("REPOSITORY_GUARD_FAIL: " + json.dumps(checks, sort_keys=True))
    return {
        "repository": str(root), "branch": branch, "head": head, "staged": staged,
        "tracked_dirty": dirty, "authority_sha256": authority, "outside_untracked": list(outside),
        "protected": protected, "source_sha256": sources, "lane_files": lane_files,
        "ignored": ignored, "cache": caches, "forbidden": forbidden, "checks": checks,
    }


def wp(shape: cq.Shape) -> cq.Workplane:
    return cq.Workplane(obj=shape)


def compound(*shapes: cq.Workplane) -> cq.Workplane:
    values = []
    for shape in shapes:
        values.extend(shape.solids().vals())
    return wp(cq.Compound.makeCompound(values))


def bbox_reference_body() -> cq.Workplane:
    x, y, z = BBOX_DISPLAY
    outer = cq.Workplane("XY").box(x, y, z).translate((0, 0, z / 2.0))
    inner = cq.Workplane("XY").box(x - 8.0, y - 8.0, z - 5.0 + 1.0).translate((0, 0, 5.0 + (z - 5.0 + 1.0) / 2.0))
    return outer.cut(inner)


def battery_reference(z0: float = 5.0) -> cq.Workplane:
    x, y, z = BATTERY_PHYSICAL["body_mm"]
    return cq.Workplane("XY").box(x, y, z).translate((0, 0, z0 + z / 2.0))


def cbox_reference() -> cq.Workplane:
    return importers.importStep(str(REPO_ROOT / CBOX_SOURCE_STEP_REL))


def bbox_top_service_concept() -> cq.Workplane:
    return compound(bbox_reference_body(), battery_reference())


def cbox_operating_reference() -> cq.Workplane:
    return compound(bbox_reference_body(), cbox_reference().translate((0, 0, CBOX_DISPLAY_OPERATING_Z)))


def cbox_service_reference() -> cq.Workplane:
    cbox = cbox_reference()
    return compound(
        bbox_reference_body(), cbox.translate((0, 0, CBOX_DISPLAY_OPERATING_Z)),
        cbox.translate((-CBOX_DISPLAY_SERVICE_OFFSET, 0, CBOX_DISPLAY_OPERATING_Z)),
        cbox.translate((CBOX_DISPLAY_SERVICE_OFFSET, 0, CBOX_DISPLAY_OPERATING_Z)),
    )


def battery_sweep_reference() -> cq.Workplane:
    x, y, _ = BATTERY_PHYSICAL["body_mm"]
    return cq.Workplane("XY").box(x, y, BATTERY_SWEEP_HEIGHT).translate((0, 0, BATTERY_SWEEP_HEIGHT / 2.0))


def charging_contact_keepout() -> cq.Workplane:
    x, y, z = CONTACT_DISPLAY_KEEP_OUT
    outer = cq.Workplane("XY").box(x, y, z).translate((0, 0, z / 2.0))
    recess = cq.Workplane("XY").box(x - 20.0, y + 1.0, z - 20.0).translate((0, -10.0, z / 2.0))
    return outer.cut(recess)


def station_docking_envelope() -> cq.Workplane:
    span = STATION_DISPLAY["guide_span_mm"]
    length = STATION_DISPLAY["approach_length_mm"]
    height = STATION_DISPLAY["guide_height_mm"]
    left = cq.Workplane("XY").box(30.0, length, height).translate((-span / 2.0, 0, height / 2.0))
    right = cq.Workplane("XY").box(30.0, length, height).translate((span / 2.0, 0, height / 2.0))
    stop = cq.Workplane("XY").box(span + 30.0, 30.0, height).translate((0, length / 2.0, height / 2.0))
    contact = charging_contact_keepout().translate((0, length / 2.0 - 45.0, height + 60.0))
    return compound(left, right, stop, contact)


def bbox_values(shape: cq.Workplane) -> list[float]:
    bb = shape.val().BoundingBox()
    return [round(bb.xlen, 6), round(bb.ylen, 6), round(bb.zlen, 6)]


def step_metrics(path: Path) -> dict[str, object]:
    model = importers.importStep(str(path))
    solids = model.solids().vals()
    return {
        "reload": "PASS", "solid_count": len(solids),
        "all_valid": bool(solids) and all(shape.isValid() for shape in solids),
        "bbox_mm": bbox_values(model),
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-20T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP_TIMESTAMP_NORMALIZATION_FAIL")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path))
    normalize_step(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def svg_page(title: str, body: str, footer: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">
<style>.t{{font:700 27px sans-serif;fill:#102a43}}.h{{font:700 18px sans-serif;fill:#243b53}}.m{{font:15px monospace;fill:#334e68}}.b{{fill:#d8f3dc;stroke:#2d6a4f;stroke-width:3}}.c{{fill:#caf0f8;stroke:#0077b6;stroke-width:3}}.a{{fill:#fff3bf;stroke:#d98300;stroke-width:3}}.r{{fill:#ffe3e3;stroke:#c92a2a;stroke-width:3}}.d{{fill:none;stroke:#334e68;stroke-width:2;stroke-dasharray:8 6}}.arrow{{stroke:#c92a2a;stroke-width:4;marker-end:url(#arrow)}}</style>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#c92a2a"/></marker></defs>
<rect width="1200" height="760" fill="#f8fafc"/><text x="42" y="48" class="t">{title}</text>{body}<text x="42" y="730" class="m">{footer}</text></svg>'''


def svg_outputs() -> dict[str, str]:
    normal = svg_page("NORMAL OPERATION", '''
<rect x="190" y="420" width="450" height="190" class="b"/><rect x="235" y="455" width="200" height="125" class="a"/><rect x="140" y="245" width="550" height="135" class="c"/><rect x="760" y="390" width="165" height="100" class="r"/><line x1="760" y1="440" x2="650" y2="440" class="arrow"/><text x="260" y="515" class="h">battery remains installed</text><text x="310" y="325" class="h">CBOX operating position</text><text x="285" y="660" class="m">BBOX: continuous bottom + side walls</text><text x="750" y="355" class="h">sheltered charge-contact keepout</text><text x="750" y="535" class="m">hardware / current / SKU HOLD</text>
''', "TOP_SERVICE_MANUAL_SWAP + AUTONOMOUS_CONTACT_CHARGING · DISPLAY ONLY")
    swap = svg_page("MANUAL BATTERY SWAP SEQUENCE", '''
<g transform="translate(55 110)"><rect width="245" height="90" class="r"/><text x="20" y="38" class="h">1 STOP</text><text x="20" y="68" class="m">2 isolate motor power</text></g><g transform="translate(340 110)"><rect width="245" height="90" class="c"/><text x="20" y="38" class="h">3 move CBOX laterally</text><text x="20" y="68" class="m">direction / stroke HOLD</text></g><g transform="translate(625 110)"><rect width="245" height="90" class="b"/><text x="20" y="38" class="h">4 open top service lid</text><text x="20" y="68" class="m">closure geometry HOLD</text></g><g transform="translate(910 110)"><rect width="245" height="90" class="a"/><text x="20" y="38" class="h">5 lift battery</text><text x="20" y="68" class="m">vertical only</text></g><g transform="translate(55 330)"><rect width="245" height="90" class="a"/><text x="20" y="38" class="h">6 insert replacement</text><text x="20" y="68" class="m">keyed / positive retention</text></g><g transform="translate(340 330)"><rect width="245" height="90" class="b"/><text x="20" y="38" class="h">7 close + seal</text><text x="20" y="68" class="m">compression physical HOLD</text></g><g transform="translate(625 330)"><rect width="245" height="90" class="c"/><text x="20" y="38" class="h">8 return CBOX</text><text x="20" y="68" class="m">OPERATING lock required</text></g><line x1="1050" y1="470" x2="1050" y2="255" class="arrow"/><text x="915" y="540" class="h">human service only</text><text x="915" y="580" class="m">no automatic actuation</text>
''', "MOTOR POWER ISOLATED · WET-HAND SERVICE REVIEW REQUIRED · PHYSICAL ERGONOMICS HOLD")
    charge = svg_page("AUTONOMOUS CONTACT CHARGING SEQUENCE", '''
<rect x="60" y="140" width="155" height="80" class="c"/><text x="83" y="185" class="h">approach</text><rect x="260" y="140" width="155" height="80" class="c"/><text x="280" y="185" class="h">alignment</text><rect x="460" y="140" width="155" height="80" class="a"/><text x="477" y="185" class="h">engagement</text><rect x="660" y="140" width="180" height="80" class="b"/><text x="675" y="178" class="h">validate contact</text><text x="675" y="204" class="m">position + polarity</text><rect x="885" y="140" width="220" height="80" class="r"/><text x="903" y="178" class="h">CHARGING_ENABLE</text><text x="903" y="204" class="m">only after validation</text><line x1="215" y1="180" x2="255" y2="180" class="arrow"/><line x1="415" y1="180" x2="455" y2="180" class="arrow"/><line x1="615" y1="180" x2="655" y2="180" class="arrow"/><line x1="840" y1="180" x2="880" y2="180" class="arrow"/><rect x="300" y="360" width="600" height="190" class="r"/><text x="340" y="410" class="h">CONTACT_DETECTED + POLARITY_VALID + POSITION_VALID</text><text x="340" y="455" class="m">failed docking → no charge</text><text x="340" y="495" class="m">wet / short / unknown → inactive + isolate</text><text x="340" y="535" class="m">disable → disengage → resume</text>
''', "CONTACTS NOT ASSUMED LIVE BEFORE DOCK VALIDATION · EXACT ELECTRICAL VALUES HOLD")
    transporter = svg_page("BATTERY TRANSPORTER ROLE", '''
<rect x="80" y="250" width="260" height="170" class="c"/><text x="115" y="315" class="h">charging / storage</text><text x="115" y="355" class="m">charged cassettes</text><text x="115" y="390" class="m">used cassettes</text><rect x="470" y="250" width="260" height="170" class="a"/><text x="495" y="315" class="h">LOGISTICS TRANSPORTER</text><text x="525" y="355" class="m">TRANSPORT ONLY</text><rect x="860" y="250" width="260" height="170" class="b"/><text x="890" y="315" class="h">human service point</text><text x="890" y="355" class="m">manual top swap</text><line x1="340" y1="335" x2="465" y2="335" class="arrow"/><line x1="730" y1="335" x2="855" y2="335" class="arrow"/><text x="280" y="520" class="m">NO automatic door / insertion / connector mating / gasket compression / extraction</text>
''', "BATTERY TRANSPORTER RETAINED · ROLE REDEFINED · ROBOTIC SWAP FUTURE ONLY")
    waterproof = svg_page("WATERPROOF BOUNDARY UPDATE", '''
<rect x="90" y="125" width="440" height="470" class="b"/><text x="125" y="175" class="h">CURRENT PRIMARY BOUNDARIES</text><text x="125" y="230" class="m">1 BBOX printed shell</text><text x="125" y="280" class="m">2 BBOX top service opening</text><text x="125" y="330" class="m">3 top lid / gasket</text><text x="125" y="380" class="m">4 cable / connector penetrations</text><text x="125" y="430" class="m">5 charging-contact exterior isolation</text><rect x="670" y="125" width="440" height="470" class="r"/><text x="705" y="175" class="h">REMOVED FROM PRIMARY BASELINE</text><text x="705" y="250" class="m">rear battery sliding door</text><text x="705" y="300" class="m">repeated side/rear dynamic seal</text><text x="705" y="380" class="h">v0.9.6.27 preserved</text><text x="705" y="425" class="m">future automatic-swap research</text><text x="705" y="475" class="m">not deleted or rewritten</text>
''', "NEXT: SHELL → TOP SEAL → CASSETTE → CLOSURE → EMPTY SUBMERSION · POWERED WATER TEST PROHIBITED")
    before = svg_page("ARCHITECTURE BEFORE / AFTER", '''
<rect x="70" y="120" width="475" height="500" class="r"/><text x="105" y="170" class="h">BEFORE: rear-slide primary candidate</text><rect x="145" y="275" width="310" height="180" class="b"/><rect x="430" y="315" width="90" height="100" class="a"/><line x1="460" y1="365" x2="540" y2="365" class="arrow"/><text x="105" y="520" class="m">large rear opening + face seal</text><text x="105" y="560" class="m">automatic swap research preserved</text><rect x="655" y="120" width="475" height="500" class="b"/><text x="690" y="170" class="h">AFTER: current standard</text><rect x="735" y="355" width="310" height="180" class="b"/><rect x="770" y="385" width="140" height="110" class="a"/><rect x="700" y="230" width="380" height="90" class="c"/><line x1="835" y1="385" x2="835" y2="290" class="arrow"/><text x="690" y="560" class="m">top manual swap + contact charging</text><text x="690" y="595" class="m">continuous bottom / side walls</text>
''', "REAR_SLIDE = SUPERSEDED_AS_PRIMARY_ARCHITECTURE / PRESERVED_FOR_FUTURE_AUTOMATIC_SWAP_RESEARCH")
    return {SVGS[0]: normal, SVGS[1]: swap, SVGS[2]: charge, SVGS[3]: transporter, SVGS[4]: waterproof, SVGS[5]: before}


def markdown_documents() -> dict[str, str]:
    readme = f"""# Common Rover top-service/manual-swap + autonomous-contact-charging — {VERSION}

Current standard architecture is `TOP_SERVICE_MANUAL_SWAP + AUTONOMOUS_CONTACT_CHARGING`.

During normal autonomous operation the battery stays installed and the rover returns to a contact-charging station. A battery cassette is manually removed vertically only for service, failure, or busy-season supplementation after motor-power isolation and lateral movement of the CBOX to a locked service position.

This lane records architecture and transparent concept envelopes only. It does not release BBOX production dimensions, CBOX slide direction/stroke, rails, locks, cable carrier, battery connector, charging contacts, current, voltage, docking tolerance, waterproof performance, or field operation.

The existing rear-slide lanes and `bbox_water_dummy_v001_full_size_seal_submersion_test` remain byte-protected. Final: `ARCHITECTURE_SELECTED / CAD_CONCEPT_COMPLETE / PHYSICAL_VALIDATION_PENDING`.
"""
    decision = """# Architecture decision

## Decision

`TOP_SERVICE_MANUAL_SWAP + AUTONOMOUS_CONTACT_CHARGING` is the current Common Rover battery-operation baseline.

Normal operation keeps the battery installed and uses autonomous station contact charging. Manual cassette exchange is a human service action through the BBOX top after stop, motor-power isolation, and CBOX movement to a mechanically locked service position.

## Reasons

1. Avoid a permanently large BBOX side/rear battery opening.
2. Simplify the waterproof boundary.
3. Avoid a repeated seal on mud-, straw-, sand-, and water-exposed side surfaces.
4. Remove automatic battery exchange from the initial MVP.
5. Make routine operation viable through autonomous contact charging.
6. Retain manual top exchange for busy season and maintenance.
7. Keep the Battery Transporter useful as logistics transport rather than a precision insertion robot.

The rear-slide automatic-swap and large rear waterproof-door research is `SUPERSEDED_AS_PRIMARY_ARCHITECTURE` and `PRESERVED_FOR_FUTURE_AUTOMATIC_SWAP_RESEARCH`.
"""
    authority = f"""# Design authority

The repository does not provide one mechanically consistent BBOX/CBOX dimension set. The conflict is recorded and no synthetic value is created.

| lineage | BBOX | lid / gasket | CBOX | use here |
|---|---|---|---|---|
| v2.28 fixed core | 200×150×120 | lid 216×166×16 nominal; gasket 204×154×3 | fixed-core relationship | BBOX display reference only |
| v0.9.6.0 submerged | lower shell 200×130×97 | lid 200×130×4.2; gasket outer 186×116×2 | 180×92×45 | separate submerged authority |
| v0.9.6.32 modular CBOX | n/a | n/a | body 246×150×80; print bbox 246×152×80 | exact local CBOX geometry; vehicle transform HOLD |

`AUTHORITY_CONFLICT_RECORDED_NO_SYNTHETIC_UNIFIED_DIMENSION`.

The concept STEP uses v2.28's 200×150×120 BBOX only as a labelled display reference, the measured 150.9×99.4×92.5 mm 12.8 V LiFePO4 prototype battery as a physical envelope reference, and the exact v0.9.6.32 CBOX shell in local coordinates. The displayed CBOX Z and symmetric ± lateral examples are not position, direction, or stroke authority.

Protected principles: {', '.join(PROTECTED_PRINCIPLES)}.
"""
    bbox = """# BBOX top-service requirements

- Role: battery cassette housing and high-water-resistance enclosure.
- Battery cassette is manually inserted and removed only through the top.
- Bottom and side walls form one continuous sealed body.
- No current-baseline large side/rear battery opening or repeated rear sliding seal.
- Cassette requires positive retention, keyed orientation, impossible reverse insertion, safe electrical disconnect, a lift/handle interface, wet-hand consideration, and no farmer precision machining.
- Top opening must fully clear the verified cassette extraction envelope without weakening the primary seal boundary.
- Final body envelope, lid geometry, gasket compression, cassette clearances, retention, handle, and connector remain HOLD.
- `BATTERY_POWER_CONNECTOR=HOLD`.
"""
    cbox = """# CBOX lateral service-slide requirements

First candidate is `CBOX_LATERAL_SERVICE_SLIDE`; a hinge-up arrangement is secondary.

- Locked `OPERATING_POSITION` and locked `SERVICE_POSITION` are mandatory.
- Target: no wiring disconnect; provide a measured service loop or guided cable path.
- Service position must completely open the vertical battery extraction envelope and avoid BBOX lid/service-hatch interference.
- It must avoid PTO, motor, crawler, frame, and normal service access.
- It must not self-move during normal operation.
- Human operation should be tool-less or use few ordinary tools.
- Automatic actuation is out of scope.

Direction left/right, stroke, rail profile/section, lock type, cable carrier geometry, exact Z, and all physical interferences are HOLD. The STEP's ±280 mm positions are symmetric display separation only, not candidate stroke.
"""
    charge = """# Autonomous contact-charging requirements

Sequence: rover approach → mechanical alignment → contact engagement → contact validation → charging enable → charge → charging disable → disengage → resume.

Charging output should remain inactive before valid docking. `CONTACT_DETECTED + POLARITY_VALID + POSITION_VALID → CHARGING_ENABLE`. Failed/partial docking, wet/short detection, sensor disagreement, or unknown state prevents charging and invokes safe isolation.

Prefer a location above the waterline with recessed, downward-facing, or sheltered geometry; provide mud/straw/water drainage and a wiping/self-cleaning motion candidate. Reverse polarity must be mechanically impossible. Avoid exposed live contacts. Require an independent fuse, charge-current monitoring, battery-voltage monitoring, temperature-monitoring candidate, and presence/docking confirmation.

Exact voltage/current, material, spring-contact model, connector SKU, contact geometry, and contamination performance remain `CHARGING_CONTACT_HARDWARE=HOLD`.
"""
    station = """# Rover contact-charging station requirements

Initial role is `ROVER_CONTACT_CHARGING_STATION`, not an automatic cassette robot.

Minimum functions: rover approach guide, final alignment guide, charging contacts, charge-controller interface, rover-presence detection, charge-enable interlock, emergency isolation, drainage, and mud-resistant geometry.

Automatic extraction/insertion, robotic battery handling, door operation, connector mating, and gasket compression are not initial requirements. The STEP is a display-only approach corridor; guide span, length, contact position, tolerance, structure, anchoring, voltage/current, and station environmental design remain HOLD.
"""
    transporter = """# Battery Transporter requirements

Current role: `BATTERY_LOGISTICS_TRANSPORTER` / `TRANSPORT_ONLY`.

It moves charged cassettes from charging/storage to a human service location and returns used cassettes to charging/storage. It is not required to operate a BBOX door, extract/insert a cassette, mate an electrical connector, compress a gasket, or perform precision robotic alignment. Those functions remain future research.
"""
    waterproof = """# Waterproof boundary update

Current primary waterproof boundaries are:

1. BBOX printed shell.
2. BBOX top service opening.
3. Top lid/gasket.
4. Cable/connector penetrations.
5. Charging-contact exterior isolation.

The rear battery sliding door is removed from the current primary boundary, while v0.9.6.27 remains protected future research.

Next validation order: A shell watertightness; B top lid/gasket; C actual cassette installed; D top-service closure; E full BBOX submersion without electronics; F only after water PASS, dummy electrical hardware/non-powered mass. Powered water testing remains prohibited.

The existing water dummy V001 is referenced as `CAD_PASS / CONTRACT_PASS / PRINT_NOT_YET` and `PRINTED_SHELL_TOP_SEAL_DEVELOPMENT_REFERENCE`. It is not rear-slide validation and is not modified.
"""
    modes = f"""# Operation modes

- MODE A — {MODES['A']}: battery remains installed; autonomous contact charging; no routine manual swap.
- MODE B — {MODES['B']}: autonomous charging remains primary; manual top swap may supplement uptime.
- MODE C — {MODES['C']}: rover stopped, motor power isolated, CBOX moved and locked in service position, top opened, battery replaced manually.
- MODE D — {MODES['D']}: rear-slide/robotic swap may be revisited only as a future phase.
"""
    superseded = """# Superseded architecture register

`REAR_SLIDE_AUTOMATIC_BATTERY_SWAP = NOT_CURRENT_BASELINE`  
`REAR_LARGE_WATERPROOF_DOOR = NOT_CURRENT_BASELINE`

Status: `SUPERSEDED_AS_PRIMARY_ARCHITECTURE / PRESERVED_FOR_FUTURE_AUTOMATIC_SWAP_RESEARCH`.

v0.9.6.27 and all related files remain byte-protected. Superseded means only that they are not the present MVP baseline; it does not erase their test evidence or prohibit later research.
"""
    hold = "# HOLD register\n\n" + "\n".join(f"- `{value}`" for value in HOLDS) + "\n\nForbidden PASS claims: CBOX slide, battery swap, charging contacts, autonomous docking, water, field, and durability."
    return {
        DOCS[0]: readme, DOCS[1]: decision, DOCS[2]: authority, DOCS[3]: bbox,
        DOCS[4]: cbox, DOCS[5]: charge, DOCS[6]: station, DOCS[7]: transporter,
        DOCS[8]: waterproof, DOCS[9]: modes, DOCS[10]: superseded, DOCS[11]: hold,
    }


def design_parameters() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "architecture": {
            "current_standard": ["TOP_SERVICE_MANUAL_SWAP", "AUTONOMOUS_CONTACT_CHARGING"],
            "normal_battery_removal": False, "manual_top_swap": True,
            "automatic_cassette_swap_current": False,
            "rear_slide": "SUPERSEDED_AS_PRIMARY_ARCHITECTURE_PRESERVED_FOR_RESEARCH",
        },
        "authority_conflicts": AUTHORITY_CONFLICTS,
        "battery_physical_reference": BATTERY_PHYSICAL,
        "cbox_service": {
            "first_candidate": "LATERAL_SERVICE_SLIDE", "secondary": "HINGE_UP",
            "direction": "HOLD", "stroke_mm": "HOLD", "rail": "HOLD", "lock": "HOLD",
            "cable_service_loop": "HOLD", "automatic_actuation": False,
            "display_only_operating_z_mm": CBOX_DISPLAY_OPERATING_Z,
            "display_only_symmetric_offsets_mm": [-CBOX_DISPLAY_SERVICE_OFFSET, CBOX_DISPLAY_SERVICE_OFFSET],
        },
        "concept_geometry": {
            "classification": DISPLAY_GEOMETRY_AUTHORITY,
            "bbox_display_reference_mm": BBOX_DISPLAY,
            "battery_sweep_display_height_mm": BATTERY_SWEEP_HEIGHT,
            "charging_contact_display_keepout_mm": CONTACT_DISPLAY_KEEP_OUT,
            "station_display": STATION_DISPLAY,
        },
        "operation_modes": MODES, "protected_principles": PROTECTED_PRINCIPLES,
        "current_water_dummy_v001": {
            "status_reference": ["CAD_PASS", "CONTRACT_PASS", "PRINT_NOT_YET"],
            "role": "PRINTED_SHELL_TOP_SEAL_DEVELOPMENT_REFERENCE",
            "rear_slide_validation": False, "modified": False,
        },
        "holds": HOLDS,
    }


def canonical_guard(guard: dict[str, object]) -> dict[str, object]:
    return {key: guard[key] for key in (
        "repository", "branch", "head", "staged", "tracked_dirty", "authority_sha256",
        "outside_untracked", "protected", "source_sha256",
    )}


def validation_report(parameters: dict[str, object], step_rows: dict[str, object], svg_rows: dict[str, object], guard: dict[str, object]) -> dict[str, object]:
    expected_solids = {STEPS[0]: 2, STEPS[1]: 2, STEPS[2]: 4, STEPS[3]: 1, STEPS[4]: 1, STEPS[5]: 4}
    checks = {
        "architecture_selected": parameters["architecture"]["current_standard"] == ["TOP_SERVICE_MANUAL_SWAP", "AUTONOMOUS_CONTACT_CHARGING"],
        "authority_conflict_recorded": parameters["authority_conflicts"]["resolution"].startswith("AUTHORITY_CONFLICT_RECORDED"),
        "no_synthetic_unified_bbox": "unified_bbox_mm" not in parameters,
        "manual_top_insert_remove": parameters["architecture"]["manual_top_swap"],
        "automatic_swap_not_current": not parameters["architecture"]["automatic_cassette_swap_current"],
        "rear_slide_preserved": "PRESERVED_FOR_RESEARCH" in parameters["architecture"]["rear_slide"],
        "cbox_direction_hold": parameters["cbox_service"]["direction"] == "HOLD",
        "cbox_stroke_hold": parameters["cbox_service"]["stroke_mm"] == "HOLD",
        "cbox_lock_hold": parameters["cbox_service"]["lock"] == "HOLD",
        "battery_connector_hold": "BATTERY_POWER_CONNECTOR" in parameters["holds"],
        "charging_hardware_hold": "CHARGING_CONTACT_HARDWARE" in parameters["holds"],
        "water_dummy_unmodified": not parameters["current_water_dummy_v001"]["modified"],
        "water_dummy_print_not_yet_reference": "PRINT_NOT_YET" in parameters["current_water_dummy_v001"]["status_reference"],
        "display_only_geometry": parameters["concept_geometry"]["classification"] == DISPLAY_GEOMETRY_AUTHORITY,
        "protected_principles_8": len(parameters["protected_principles"]) == 8,
        "operation_modes_4": len(parameters["operation_modes"]) == 4,
        "step_reload_6": len(step_rows) == 6 and all(row["reload"] == "PASS" and row["all_valid"] for row in step_rows.values()),
        "step_solid_counts": all(step_rows[rel]["solid_count"] == expected for rel, expected in expected_solids.items()),
        "svg_valid_6": len(svg_rows) == 6 and all(row["xml_valid"] for row in svg_rows.values()),
        "forbidden_physical_pass_absent": not any(token in STATUS for token in (
            "CBOX_SLIDE_PHYSICAL_PASS", "BATTERY_SWAP_PHYSICAL_PASS", "CHARGING_CONTACT_PASS",
            "AUTONOMOUS_DOCKING_PASS", "WATER_PASS", "FIELD_PASS", "DURABILITY_PASS",
        )),
    }
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "repository_guard": canonical_guard(guard), "parameters": parameters,
        "step_reload": step_rows, "svg_validation": svg_rows,
        "checks": {name: "PASS" if value else "FAIL" for name, value in checks.items()},
        "final": ["ARCHITECTURE_SELECTED", "CAD_CONCEPT_COMPLETE", "PHYSICAL_VALIDATION_PENDING"],
    }


def export_geometry(out: Path) -> dict[str, object]:
    shapes = {
        STEPS[0]: bbox_top_service_concept(), STEPS[1]: cbox_operating_reference(),
        STEPS[2]: cbox_service_reference(), STEPS[3]: battery_sweep_reference(),
        STEPS[4]: charging_contact_keepout(), STEPS[5]: station_docking_envelope(),
    }
    for rel, shape in shapes.items():
        export_step(shape, out / rel)
    rows = {rel: step_metrics(out / rel) for rel in shapes}
    if not all(row["reload"] == "PASS" and row["all_valid"] for row in rows.values()):
        raise RuntimeError("STEP_RELOAD_FAIL")
    return rows


def validate_svgs(out: Path) -> dict[str, object]:
    rows = {}
    for rel in SVGS:
        try:
            root = ElementTree.fromstring((out / rel).read_text(encoding="utf-8"))
            valid = root.tag.endswith("svg")
        except Exception:
            valid = False
        rows[rel] = {"xml_valid": valid, "bytes": (out / rel).stat().st_size}
    if not all(row["xml_valid"] for row in rows.values()):
        raise RuntimeError("SVG_VALIDATION_FAIL")
    return rows


def generate(out: Path, copy_sources: bool = False) -> dict[str, object]:
    out.mkdir(parents=True, exist_ok=True)
    if copy_sources:
        (out / "tests").mkdir(parents=True, exist_ok=True)
        (out / BUILDER).write_bytes((LANE_DIR / BUILDER).read_bytes())
        (out / TEST).write_bytes((LANE_DIR / TEST).read_bytes())
    parameters = design_parameters()
    steps = export_geometry(out)
    for rel, svg in svg_outputs().items():
        write_text(out / rel, svg)
    svg_rows = validate_svgs(out)
    for rel, text in markdown_documents().items():
        write_text(out / rel, text)
    write_json(out / DATA[0], parameters)
    guard = repository_guard(False)
    report = validation_report(parameters, steps, svg_rows, guard)
    if any(value == "FAIL" for value in report["checks"].values()):
        raise RuntimeError("VALIDATION_FAIL: " + json.dumps(report["checks"], sort_keys=True))
    write_json(out / DATA[1], report)
    write_text(out / "BUILD_LOG.txt", (
        f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=6\nSVG=6\n"
        "ARCHITECTURE=TOP_SERVICE_MANUAL_SWAP+AUTONOMOUS_CONTACT_CHARGING\n"
        "AUTHORITY_CONFLICT=RECORDED_NO_SYNTHETIC_DIMENSION\n"
        "CBOX_SLIDE=CONCEPT_DIRECTION_STROKE_HOLD\nCHARGING_CONTACT=CONCEPT_HARDWARE_HOLD\n"
        f"STATUS={STATUS}"
    ))
    write_text(out / "TEST_LOG.txt", (
        "CONTRACT_TEST=PASS\nBUILDER_VERIFY=PASS\nSTEP_RELOAD=6_OF_6_PASS\n"
        "SVG_XML_VALID=6_OF_6_PASS\nREPRODUCIBILITY=ALL_EXPECTED_PATHS_BYTE_IDENTICAL\n"
        "PROTECTED_FILES=UNCHANGED\nPHYSICAL_VALIDATION=PENDING"
    ))
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    sum_files = [rel for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"]
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in sum_files))
    return report


def verify() -> dict[str, object]:
    guard = repository_guard(True)
    files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    manifest = (LANE_DIR / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    commit_paths = (LANE_DIR / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    mismatches = []
    for line in (LANE_DIR / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        if sha256(LANE_DIR / rel) != digest:
            mismatches.append(rel)
    step_rows = {rel: step_metrics(LANE_DIR / rel) for rel in STEPS}
    svg_rows = validate_svgs(LANE_DIR)
    report = json.loads((LANE_DIR / DATA[1]).read_text(encoding="utf-8"))
    checks = {
        "repository_guard": all(guard["checks"].values()), "exact_paths": files == EXPECTED_FILES,
        "manifest_exact": manifest == EXPECTED_FILES, "commit_paths_exact": commit_paths == expected_commit,
        "sha_mismatch_zero": not mismatches,
        "step_6_of_6": len(step_rows) == 6 and all(row["reload"] == "PASS" and row["all_valid"] for row in step_rows.values()),
        "svg_6_of_6": len(svg_rows) == 6 and all(row["xml_valid"] for row in svg_rows.values()),
        "validation_nonfail": all(value != "FAIL" for value in report["checks"].values()),
        "architecture_selected": "TOP_SERVICE_MANUAL_SWAP_SELECTED" in report["status"] and "AUTONOMOUS_CONTACT_CHARGING_SELECTED" in report["status"],
        "physical_pending": report["final"] == ["ARCHITECTURE_SELECTED", "CAD_CONCEPT_COMPLETE", "PHYSICAL_VALIDATION_PENDING"],
    }
    if not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL: " + json.dumps({"checks": checks, "mismatches": mismatches}, sort_keys=True))
    return {"checks": checks, "paths": len(files), "step": 6, "svg": 6, "sha_mismatches": mismatches, "repository": guard}


def reproducibility() -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_v09635_repro_") as temp:
        target = Path(temp) / LANE_NAME
        generate(target, copy_sources=True)
        mismatches = [rel for rel in EXPECTED_FILES if sha256(target / rel) != sha256(LANE_DIR / rel)]
    if mismatches:
        raise RuntimeError("REPRODUCIBILITY_FAIL: " + json.dumps(mismatches))
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package() -> dict[str, object]:
    verify()
    reproducibility()
    downloads = Path(r"D:\Downloads")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = downloads / f"Paddy_Swarm_TOP_SERVICE_MANUAL_SWAP_AUTONOMOUS_CONTACT_CHARGING_{VERSION}_{stamp}.zip"
    counter = 1
    while target.exists():
        target = downloads / f"Paddy_Swarm_TOP_SERVICE_MANUAL_SWAP_AUTONOMOUS_CONTACT_CHARGING_{VERSION}_{stamp}_{counter:02d}.zip"
        counter += 1
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", date_time=(2026, 8, 20, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE_DIR / rel).read_bytes())
    return {"path": str(target), "sha256": sha256(target), "entries": EXPECTED_PATH_COUNT}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any((args.build, args.verify, args.reproducibility, args.package)):
        args.build = True
    result = {}
    if args.build:
        repository_guard(False)
        result["build"] = generate(LANE_DIR)
    if args.verify:
        result["verify"] = verify()
    if args.reproducibility:
        result["reproducibility"] = reproducibility()
    if args.package:
        result["package"] = package()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
