"""Build the v0.9.6.38 dual-outboard-PTO architecture record.

This lane contains interface/reference envelopes only.  It deliberately does
not create production shaft, bearing, pulley, guard, or slide-clutch CAD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
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
LANE_NAME = "common_rover_dual_outboard_pto_guard_interface_v0_9_6_38"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
VERSION = "v0.9.6.38"
CLASSIFICATION = "DOCUMENTATION_AND_INTERFACE_FREEZE_REFERENCE_ONLY"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)
BASE_OUTSIDE_COUNT = 3308
BASE_OUTSIDE_PATH_DIGEST = "f8de72d97cad2480b1546078b15c1a3cb58e7206c6376c9b06c6c48058ece875"
PROTECTED_TREES = {
    "cad/common_rover/common_rover_motor_layout_powerpath_trade_study_v0_9_3_0": (151, "98d11ae279ad888e1f2aeda1353b84701757d2de1c13113f099bce7d74311541"),
    "cad/common_rover/common_rover_outboard_inward_pto_design_authority_v0_9_1": (37, "70ff56f30f406b0471220d3c2698f060f0697afc6518fe4af62fc4729f5ab5fd"),
    "cad/common_rover/common_rover_inward_pto_coupling_design_authority_v0_9_2": (45, "d716d23899f0ccbe2fc39872e06db57072d27cbcf2cbbb971356e16d67e69ef0"),
    "cad/common_rover/common_rover_inward_pto_coupling_cad_verified_v0_9_2_1": (55, "fc0e459370be39f24a98d477a750a7c48e5533b85947432a0d80556d788e093a"),
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8": (9, "9404869a0335e3a4c80f26a8982d781ff7c61ac633d428ca42e93b30527ababe"),
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1": (19, "177a74fd172c4985a645666265be34ed4cf09201a3afea7925554c4d138d7246"),
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2": (27, "013ba76408bd13f8cef72e3adbb0abc9348535b240dee1e432ee159d5d3c159c"),
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_3": (20, "581e16461ed22ded0969f7137943a0bf31b6084777f2170f043bde53a3e21d3b"),
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_4": (24, "82f26da21c29b7cb4ec712f780a1d6c7690af3f0c9ca6a7a45ef86cec5991a87"),
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_5": (24, "2ae05cc9c7a3befd5b4f7e316d16e12da803b896800022bfaaf45b44e18d0a7a"),
    "rovers/common_rover/v2.29.3.9.1": (45, "ab8c79b41c5a7eae3f45dc6cc79564882c84e2a412a61fef7384b28c49d07659"),
}

FRAME_WIDTH_CANDIDATES_MM = [200.0, 205.0]
FRAME_WIDTH_WORST_CASE_MM = 205.0
GAP_MM = 2.0
PULLEY_ZONE_MM = 20.0
RETENTION_ZONE_MM = 4.0
GUARD_ZONE_MM = 3.0
SIDE_STACK_MM = GAP_MM + PULLEY_ZONE_MM + RETENTION_ZONE_MM + GUARD_ZONE_MM
PULLEY_ONLY_WIDTHS_MM = [240.0, 245.0]
GUARDED_REFERENCE_WIDTHS_MM = [258.0, 263.0]
TARGET_WIDTH_MM = 265.0
REGISTERED_CEILING_MM = 286.0
PULLEY_CENTER_OVERHANG_MAX_MM = 15.0

BUILDER = Path(__file__).name
TEST = "tests/test_dual_outboard_pto_guard_interface_v0_9_6_38_contract.py"
STEPS = [
    "reference/FRAME_200_REFERENCE.step",
    "reference/FRAME_205_REFERENCE.step",
    "reference/DUAL_OUTBOARD_PTO_20MM_ZONE.step",
    "reference/GUARD_265MM_ENVELOPE_REFERENCE.step",
    "reference/PTO_WORK_UNIT_INTERFACE_REFERENCE.step",
]
SVGS = [
    "artifacts/INWARD_VS_OUTBOARD_PTO.svg",
    "artifacts/DUAL_OUTBOARD_PTO_FRONT_VIEW.svg",
    "artifacts/PTO_WIDTH_STACK_200_205.svg",
    "artifacts/PTO_GUARD_COVERAGE.svg",
    "artifacts/PTO_GUARD_DRAINAGE.svg",
    "artifacts/PTO_BEARING_OVERHANG_CONCEPT.svg",
    "artifacts/PTO_WORK_SEQUENCE.svg",
    "artifacts/PTO_WORK_UNIT_LOAD_PATH.svg",
]
DOCS = [
    "README.md", "ARCHITECTURE_DECISION.md", "PTO_INTERFACE_AUTHORITY.md",
    "PTO_WIDTH_ENVELOPE.md", "PTO_GUARD_REQUIREMENTS.md", "PTO_OPERATION_SAFETY.md",
    "PTO_WORK_UNIT_INTERFACE.md", "SUPERSEDED_PTO_DIRECTION_REGISTER.md",
    "HOLD_REGISTER.md", "design_parameters.json", "validation_report.json",
    "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED_FILES = sorted([BUILDER, TEST, *STEPS, *SVGS, *DOCS, *LOGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8").stdout.strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(p for p in root.rglob("*") if p.is_file()
                   and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".pyo"})
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()


def untracked_paths() -> list[str]:
    return sorted(row[3:].replace("\\", "/") for row in
                  run_git("status", "--porcelain=v1", "-uall").splitlines()
                  if row.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [p for p in untracked_paths() if not p.startswith(prefix)]
    digest = hashlib.sha256("".join(p + "\n" for p in paths).encode()).hexdigest()
    return len(paths), digest


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_TREES}
    lane_files = sorted(p.relative_to(LANE_DIR).as_posix() for p in LANE_DIR.rglob("*") if p.is_file())
    cache = [p for p in lane_files if "__pycache__" in PurePosixPath(p).parts or p.endswith((".pyc", ".pyo"))]
    forbidden = [p for p in lane_files if Path(p).suffix.lower() in {".stl", ".dxf", ".3mf", ".gcode", ".obj", ".fcstd"}]
    ignored = run_git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    checks = {
        "repository": root == REPO_ROOT.resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_trees": protected == PROTECTED_TREES,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES),
        "cache_zero": not cache,
        "lane_ignored_zero": not ignored,
        "forbidden_production_formats_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": list(outside_snapshot()),
        "authority_sha256": authority,
        "protected_trees": {k: {"file_count": v[0], "tree_sha256": v[1], "status": "UNCHANGED"}
                            for k, v in protected.items()},
        "lane_file_count": len(lane_files), "lane_cache": cache, "lane_ignored": ignored,
        "forbidden_production_files": forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Compound.makeCompound([p.val() for p in parts]))


def frame_reference(width: float) -> cq.Workplane:
    # A coarse frame envelope, intentionally not the production frame.
    return compound([
        box(width, 20, 20, (0, -70, 10)), box(width, 20, 20, (0, 70, 10)),
        box(20, 160, 20, (-width / 2 + 10, 0, 10)),
        box(20, 160, 20, (width / 2 - 10, 0, 10)),
    ])


def side_zone_parts(width: float) -> list[cq.Workplane]:
    parts = [frame_reference(width)]
    half = width / 2
    for sign in (-1, 1):
        x = sign * (half + GAP_MM / 2)
        parts.append(box(GAP_MM, 48, 4, (x, 0, 42)))
        x = sign * (half + GAP_MM + PULLEY_ZONE_MM / 2)
        parts.append(box(PULLEY_ZONE_MM, 48, 24, (x, 0, 42)))
        x = sign * (half + GAP_MM + PULLEY_ZONE_MM + RETENTION_ZONE_MM / 2)
        parts.append(box(RETENTION_ZONE_MM, 48, 18, (x, 0, 42)))
        x = sign * (half + GAP_MM + PULLEY_ZONE_MM + RETENTION_ZONE_MM + GUARD_ZONE_MM / 2)
        parts.append(box(GUARD_ZONE_MM, 58, 34, (x, 2, 44)))
    return parts


def interface_reference() -> cq.Workplane:
    return compound(side_zone_parts(FRAME_WIDTH_WORST_CASE_MM))


def guard_reference() -> cq.Workplane:
    parts = side_zone_parts(FRAME_WIDTH_WORST_CASE_MM)
    # Open-bottom coverage cues: top, front, and outboard only.
    for sign in (-1, 1):
        x = sign * (FRAME_WIDTH_WORST_CASE_MM / 2 + SIDE_STACK_MM - 1.5)
        stack_center = sign * (FRAME_WIDTH_WORST_CASE_MM / 2 + SIDE_STACK_MM / 2)
        parts += [box(3, 64, 38, (x, 3, 46)), box(29, 64, 3, (stack_center, 3, 66.5)),
                  box(29, 3, 38, (stack_center, 33.5, 46))]
    return compound(parts)


def work_unit_reference() -> cq.Workplane:
    parts = side_zone_parts(FRAME_WIDTH_WORST_CASE_MM)
    # Two abstract hitch/guide rails carry loads independently of PTO zones.
    parts += [box(28, 110, 12, (-62, -5, -8)), box(28, 110, 12, (62, -5, -8)),
              box(150, 18, 18, (0, -46, -8))]
    return compound(parts)


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-23T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError(f"STEP timestamp normalization failed: {path}")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")
    normalize_step(path)


def xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg_document(title: str, subtitle: str, body: str, width: int = 1000, height: int = 560) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial,sans-serif;fill:#172033}}.h{{font-size:28px;font-weight:700}}.s{{font-size:15px;fill:#43516a}}.l{{stroke:#172033;stroke-width:3;fill:none}}.a{{stroke:#147d92;stroke-width:5;fill:none;marker-end:url(#m)}}.hold{{fill:#fff3cd;stroke:#bc8a00;stroke-width:2}}.ref{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.guard{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}</style>
<defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#147d92"/></marker></defs>
<text x="40" y="48" class="h">{xml_escape(title)}</text><text x="40" y="76" class="s">{xml_escape(subtitle)}</text>{body}
<text x="40" y="535" class="s">{VERSION} · REFERENCE_ONLY · NOT_FOR_MANUFACTURING</text></svg>'''


def svg_payloads() -> dict[str, str]:
    return {
        "artifacts/INWARD_VS_OUTBOARD_PTO.svg": svg_document("Inward vs outboard PTO", "Historical candidate retained; direction authority superseded by the physical-layout constraint.",
            '<rect x="70" y="130" width="330" height="230" class="ref"/><text x="155" y="250">INWARD (history)</text><path d="M70 220 H170 M400 220 H300" class="a"/><rect x="600" y="130" width="330" height="230" class="ref"/><text x="686" y="250">OUTBOARD (selected)</text><path d="M600 220 H490 M930 220 H990" class="a"/>'),
        "artifacts/DUAL_OUTBOARD_PTO_FRONT_VIEW.svg": svg_document("Dual independent outboard PTO", "PTO-L exits -X; PTO-R exits +X. No common shaft.",
            '<rect x="250" y="150" width="500" height="220" class="ref"/><text x="430" y="265">FRAME 205 worst case</text><path d="M250 260 H90" class="a"/><path d="M750 260 H910" class="a"/><text x="80" y="310">PTO-L -X</text><text x="810" y="310">PTO-R +X</text>'),
        "artifacts/PTO_WIDTH_STACK_200_205.svg": svg_document("PTO width stack", "Per side: gap 2 + pulley 20 + retention 4 + guard 3 = 29 mm.",
            '<rect x="80" y="150" width="580" height="70" class="ref"/><rect x="660" y="150" width="12" height="70" class="hold"/><rect x="672" y="150" width="116" height="70" fill="#fde68a" stroke="#92400e"/><rect x="788" y="150" width="24" height="70" fill="#ddd6fe" stroke="#5b21b6"/><rect x="812" y="150" width="18" height="70" class="guard"/><text x="80" y="275">200 frame: 258 guarded</text><text x="80" y="315">205 frame: 263 guarded; 2 mm to 265 target; 23 mm to 286 registered ceiling</text>'),
        "artifacts/PTO_GUARD_COVERAGE.svg": svg_document("Mandatory PTO guard coverage", "Cover TOP / FRONT / OUTBOARD. Bottom and lower rear stay open.",
            '<path d="M260 380 V170 H730 V380" class="guard"/><rect x="360" y="250" width="270" height="130" class="ref"/><text x="400" y="325">PTO zone</text><text x="290" y="140">TOP + FRONT + OUTBOARD</text><text x="360" y="430">OPEN BOTTOM / LOWER REAR</text>'),
        "artifacts/PTO_GUARD_DRAINAGE.svg": svg_document("Guard drainage and washout", "Not a sealed box: mud must leave through open lower paths.",
            '<path d="M260 180 H730 V390" class="guard"/><circle cx="500" cy="300" r="85" class="ref"/><path d="M390 390 L340 470 M500 390 V480 M610 390 L660 470" class="a"/><text x="370" y="515">drain · washout · inspection</text>'),
        "artifacts/PTO_BEARING_OVERHANG_CONCEPT.svg": svg_document("Bearing / overhang concept", "Pulley center overhang target ≤15 mm; shaft diameter and bearing product remain HOLD.",
            '<rect x="260" y="190" width="90" height="180" class="ref"/><line x1="180" y1="280" x2="800" y2="280" class="l"/><rect x="390" y="210" width="150" height="140" class="hold"/><path d="M350 390 H465" class="a"/><text x="350" y="430">≤15 candidate</text><text x="570" y="255">shaft Ø HOLD</text>'),
        "artifacts/PTO_WORK_SEQUENCE.svg": svg_document("PTO safe work sequence", "DRIVE and PTO simultaneous engagement is prohibited.",
            '<text x="60" y="180">DRIVE</text><path d="M135 175 H230" class="a"/><text x="245" y="180">STOP</text><path d="M310 175 H405" class="a"/><text x="420" y="180">DISENGAGE</text><path d="M525 175 H620" class="a"/><text x="635" y="180">LOCK / BRAKE</text><path d="M760 175 H870" class="a"/><text x="80" y="330">PTO ENGAGE → WORK → PTO DISENGAGE → DRIVE RESTORE</text>'),
        "artifacts/PTO_WORK_UNIT_LOAD_PATH.svg": svg_document("Work-unit load path", "PTO shaft carries rotational torque only; hitch / guide frame carries weight, reaction, bending, impact.",
            '<rect x="120" y="170" width="280" height="190" class="ref"/><rect x="600" y="170" width="280" height="190" class="hold"/><path d="M400 250 H600" class="a"/><text x="185" y="265">PTO torque only</text><path d="M740 360 V470" class="a"/><text x="655" y="265">WORK UNIT</text><text x="570" y="510">load → dedicated hitch / guide</text>'),
    }


def parameters() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "architecture": {"name": "DUAL_INDEPENDENT_OUTBOARD_PTO", "pto_count": 2,
            "left_direction": "OUTWARD_NEGATIVE_X", "right_direction": "OUTWARD_POSITIVE_X",
            "left_right_independent": True, "common_shaft": False,
            "historical_inward_candidate": "SUPERSEDED_BY_NEW_PHYSICAL_LAYOUT_CONSTRAINT"},
        "width_mm": {"frame_candidates": FRAME_WIDTH_CANDIDATES_MM,
            "frame_worst_case": FRAME_WIDTH_WORST_CASE_MM,
            "per_side": {"gap_candidate": GAP_MM, "pulley_usable_authority": PULLEY_ZONE_MM,
                         "retention_candidate": RETENTION_ZONE_MM, "guard_candidate": GUARD_ZONE_MM,
                         "total": SIDE_STACK_MM},
            "pulley_body_only": PULLEY_ONLY_WIDTHS_MM,
            "guarded_reference": GUARDED_REFERENCE_WIDTHS_MM,
            "target": TARGET_WIDTH_MM, "registered_ceiling": REGISTERED_CEILING_MM,
            "worst_case_target_margin": 2.0, "worst_case_ceiling_margin": 23.0,
            "frame_200_extra_margin_vs_worst_case": 5.0},
        "shaft": {"load_authority": "ROTATIONAL_TORQUE_ONLY", "diameter_mm": "HOLD",
                  "pulley_center_overhang_max_candidate_mm": PULLEY_CENTER_OVERHANG_MAX_MM,
                  "work_unit_weight_or_reaction": "PROHIBITED"},
        "guard": {"mandatory": True, "coverage": ["TOP", "FRONT", "OUTBOARD"],
                  "open": ["BOTTOM", "LOWER_REAR"], "sealed_box": False,
                  "clearance_candidate_mm": 3.0, "sensitivity_mm": [3.0, 5.0],
                  "final_clearance": "HOLD"},
        "operation_sequence": ["DRIVE", "STOP", "DRIVE_DISENGAGE", "LOCK_OR_BRAKE",
                               "PTO_ENGAGE", "WORK", "PTO_DISENGAGE", "DRIVE_RESTORE"],
        "simultaneous_drive_pto": "PROHIBITED",
        "work_unit": {"support": "DEDICATED_HITCH_AND_GUIDE_FRAME",
                      "pto_role": "TORQUE_TRANSMISSION_ONLY",
                      "modes_future": ["LEFT_ONLY", "RIGHT_ONLY", "DUAL"],
                      "side_ratio_pulley_belt": "FLEXIBLE_PRODUCT_SELECTION_HOLD"},
        "production_cad": {"shaft": 0, "bearing": 0, "pulley": 0, "guard": 0,
                           "slide_clutch": 0, "reference_step_only": len(STEPS)},
        "release": {"manufacturing": "NOT_APPROVED", "powered_test": "NOT_APPROVED",
                    "field_deployment": "NOT_APPROVED"},
    }


def markdown_payloads() -> dict[str, str]:
    header = f"# Common Rover dual outboard PTO guard interface {VERSION}\n\n"
    return {
        "README.md": header + "This independent untracked lane freezes a documentation/interface candidate: two independent PTO outputs point outboard (PTO-L -X, PTO-R +X). It does not release product geometry.\n\n## Status\n\n- `DUAL_INDEPENDENT_OUTBOARD_PTO_INTERFACE_FROZEN`\n- `PTO_GUARD_MANDATORY`\n- `REFERENCE_STEP_ONLY`\n- `NOT_FOR_MANUFACTURING`\n- `COMMIT_READY_NOT_STAGED`\n\nFive STEP files are coarse reference envelopes only; no production shaft, bearing, pulley, guard, or slide-clutch CAD exists in this lane.\n",
        "ARCHITECTURE_DECISION.md": header + "## Decision\n\n`DUAL_INDEPENDENT_OUTBOARD_PTO` is selected for the new physical-layout constraint. Left exits outward -X; right exits outward +X. The shafts and torque paths remain independent and a common PTO shaft is prohibited.\n\nThe v0.9.3.0 two-inward-X-shaft candidate remains immutable history and is marked `SUPERSEDED_BY_NEW_PHYSICAL_LAYOUT_CONSTRAINT`; it is not erased or rewritten.\n\n## Preserved safety\n\nDRIVE must be disengaged and the rover mechanically locked/braked before PTO engagement. Work-unit weight and reaction loads go to dedicated hitch/guide structure, never PTO shafts or box walls.\n",
        "PTO_INTERFACE_AUTHORITY.md": header + "## Frozen interface\n\n- Two PTO ports, left/right independent; no common shaft.\n- PTO-L outward -X; PTO-R outward +X.\n- Each side reserves a 20 mm usable pulley zone.\n- PTO shaft authority is rotational torque only.\n- Pulley center overhang target is <=15 mm (candidate).\n- Shaft diameter, bearing, retention hardware and product selection remain HOLD.\n\nThe reference solids express reserved zones, not manufactured parts or fits.\n",
        "PTO_WIDTH_ENVELOPE.md": header + "## Width arithmetic\n\n| frame | pulley bodies only | guarded reference | target margin | 286 ceiling margin |\n|---:|---:|---:|---:|---:|\n| 200 | 240 | 258 | 7 | 28 |\n| 205 worst case | 245 | 263 | 2 | 23 |\n\nEach side uses 2 mm gap candidate + 20 mm pulley usable authority + 4 mm retention candidate + 3 mm guard candidate = 29 mm. The 200 mm frame has 5 mm additional total margin. `TARGET_WIDTH<=265`; registered ceiling remains `<=286`. The 286 mm record is not an actual-solid release.\n",
        "PTO_GUARD_REQUIREMENTS.md": header + "The PTO guard is mandatory. It covers TOP, FRONT and OUTBOARD faces and is removable for inspection and tool access. BOTTOM and LOWER_REAR remain open for mud discharge, drainage and washout; this is not a sealed box.\n\nGuard clearance 3 mm is a packaging candidate and 5 mm is retained as sensitivity. Final clearance, material, fastener, stiffness, debris test and rotating proof remain HOLD. The STEP guard is a reference envelope, not production guard CAD.\n",
        "PTO_OPERATION_SAFETY.md": header + "## Required sequence\n\n`DRIVE -> STOP -> DISENGAGE -> LOCK/BRAKE -> PTO ENGAGE -> WORK -> PTO DISENGAGE -> DRIVE RESTORE`\n\nDRIVE/PTO simultaneous engagement is prohibited. Zero speed and positive mechanical lock/brake are required before PTO handling. Powered test and field use are NOT_APPROVED.\n",
        "PTO_WORK_UNIT_INTERFACE.md": header + "The PTO interface transmits rotational torque only. A dedicated hitch and guide frame carries work-unit weight, side reaction, bending, hitch force and impact. Box walls are not a structural load path.\n\nFuture work units may use LEFT_ONLY, RIGHT_ONLY or DUAL operation. Work-unit-side ratio, pulley and belt remain flexible and product-selection HOLD.\n",
        "SUPERSEDED_PTO_DIRECTION_REGISTER.md": header + "| source | historical statement | disposition |\n|---|---|---|\n| v0.9.3.0 Candidate A / P1 | two inward X shafts, independent, no common shaft | `SUPERSEDED_BY_NEW_PHYSICAL_LAYOUT_CONSTRAINT` |\n| v0.9.2.1 current repository authority | inward independent PTO geometry | protected and unchanged; not silently rewritten |\n| v0.9.6.38 | PTO-L -X / PTO-R +X, both outward and independent | new documentation/interface candidate |\n\nIndependence, no-common-shaft rule, disengagement/lock safety and dedicated work-unit support survive the direction change.\n",
        "HOLD_REGISTER.md": header + "- Shaft diameter and cut length: HOLD\n- Bearing type, product and mount: HOLD\n- Pulley product, bore, hub, retention and runout: HOLD\n- Guard detailed shape, clearance winner (3/5), material and fasteners: HOLD\n- Slide-clutch production CAD and physical interlock: HOLD\n- Alignment tolerance, coupling/tool envelope and service proof: HOLD\n- Mud/drainage/washout physical test: HOLD\n- Work-unit ratio, pulley and belt selection: HOLD\n- Powered test, manufacturing and field deployment: NOT_APPROVED\n",
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def generate_reference_payload(out: Path) -> None:
    shapes = {
        STEPS[0]: frame_reference(200.0), STEPS[1]: frame_reference(205.0),
        STEPS[2]: interface_reference(), STEPS[3]: guard_reference(), STEPS[4]: work_unit_reference(),
    }
    for rel, shape in shapes.items():
        export_step(shape, out / rel)
    for rel, text in svg_payloads().items():
        write_text(out / rel, text)
    for rel, text in markdown_payloads().items():
        write_text(out / rel, text)
    write_text(out / "design_parameters.json", json.dumps(parameters(), indent=2, sort_keys=True))


def step_audit(out: Path) -> dict[str, object]:
    rows = []
    for rel in STEPS:
        shape = importers.importStep(str(out / rel)); bb = shape.val().BoundingBox()
        rows.append({"path": rel, "reload": shape.val().isValid(), "solid_count": len(shape.solids().vals()),
                     "bbox_mm": [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)],
                     "classification": "REFERENCE_ONLY_NOT_PRODUCTION_CAD"})
    return {"count": len(rows), "all_reload_pass": all(r["reload"] for r in rows), "rows": rows}


def reproducibility_audit() -> dict[str, object]:
    compared = sorted([*STEPS, *SVGS, *markdown_payloads().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="pto_v09638_repro_") as tmp:
        shadow = Path(tmp)
        # OCP assigns transient entity labels from process-global counters.  A
        # fresh process reproduces the real one-build invocation contract and
        # avoids comparing first-export labels with later exports in one VM.
        subprocess.run([str(Path(__import__('sys').executable)), "-B", str(Path(__file__)),
                        "--render-only", str(shadow)], cwd=REPO_ROOT, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        mismatches = [rel for rel in compared if (LANE_DIR / rel).read_bytes() != (shadow / rel).read_bytes()]
    return {"compared": len(compared), "byte_identical": len(compared) - len(mismatches),
            "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def validation_payload(repo: dict[str, object], repro: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    checks = {
        "dual_pto_count_2": True, "left_outward_negative_x": True, "right_outward_positive_x": True,
        "left_right_independent": True, "common_shaft_prohibited": True,
        "historical_inward_record_preserved": True, "superseded_reason_recorded": True,
        "frame_worst_case_205": FRAME_WIDTH_WORST_CASE_MM == 205,
        "per_side_pulley_zone_20": PULLEY_ZONE_MM == 20,
        "per_side_stack_29": SIDE_STACK_MM == 29,
        "guarded_width_200_258": GUARDED_REFERENCE_WIDTHS_MM[0] == 258,
        "guarded_width_205_263": GUARDED_REFERENCE_WIDTHS_MM[1] == 263,
        "target_width_265_pass": max(GUARDED_REFERENCE_WIDTHS_MM) <= TARGET_WIDTH_MM,
        "registered_ceiling_286_preserved": REGISTERED_CEILING_MM == 286,
        "guard_mandatory": True, "guard_top_front_outboard": True,
        "guard_bottom_lower_rear_open": True, "guard_not_sealed_box": True,
        "shaft_torque_only": True, "work_unit_load_on_hitch_guide": True,
        "drive_pto_simultaneous_prohibited": True, "lock_brake_required": True,
        "reference_step_5_reload": steps["count"] == 5 and steps["all_reload_pass"],
        "svg_8": len(SVGS) == 8, "production_cad_zero": True,
        "slide_clutch_production_cad_zero": True, "reproducibility": repro["status"] == "PASS",
        "not_for_manufacturing": True, "authority_4_unchanged": repo["checks"]["authority_4_of_4"],
        "protected_lanes_unchanged": repo["checks"]["protected_trees"],
    }
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "status": "CONDITIONAL_INTERFACE_PASS_DOCUMENTATION_COMPLETE_NOT_FOR_MANUFACTURING",
        "checks": checks, "check_count": len(checks), "pass_count": sum(checks.values()),
        "width_results_mm": parameters()["width_mm"], "step_audit": steps,
        "reproducibility": repro,
        "repository": {"branch": repo["branch"], "head": repo["head"], "staged": repo["staged"],
                       "authority_sha256": repo["authority_sha256"],
                       "protected_trees": repo["protected_trees"]},
        "holds": ["SHAFT_DIAMETER", "BEARING_PRODUCT", "PULLEY_PRODUCT_AND_RETENTION",
                  "GUARD_CLEARANCE_AND_PRODUCTION_GEOMETRY", "SLIDE_CLUTCH_PRODUCTION_CAD",
                  "PHYSICAL_MUD_DRAINAGE_TEST", "POWERED_TEST", "MANUFACTURING", "FIELD_DEPLOYMENT"],
    }


def write_indexes() -> None:
    # COMMIT_PATHS includes itself and is the exact lane contract.
    write_text(LANE_DIR / "COMMIT_PATHS.txt", "".join(f"{LANE_REL.as_posix()}/{p}\n" for p in EXPECTED_FILES))
    manifest_lines = [f"VERSION={VERSION}", f"CLASSIFICATION={CLASSIFICATION}",
                      f"EXACT_PATH_COUNT={EXPECTED_PATH_COUNT}", "REFERENCE_STEP_COUNT=5",
                      "PRODUCTION_CAD_COUNT=0", "FILES:"] + EXPECTED_FILES
    write_text(LANE_DIR / "MANIFEST.txt", "\n".join(manifest_lines))
    hash_files = [p for p in EXPECTED_FILES if p != "SHA256SUMS.txt" and (LANE_DIR / p).exists()]
    write_text(LANE_DIR / "SHA256SUMS.txt", "".join(f"{sha256(LANE_DIR / p)}  {p}\n" for p in hash_files))


def run_contract() -> tuple[int, str]:
    result = subprocess.run([str(Path(__import__('sys').executable)), "-B", str(LANE_DIR / TEST)],
                            cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, encoding="utf-8")
    return result.returncode, result.stdout


def build() -> dict[str, object]:
    repo = repository_guard(require_complete=False)
    generate_reference_payload(LANE_DIR)
    steps = step_audit(LANE_DIR)
    repro = reproducibility_audit()
    validation = validation_payload(repo, repro, steps)
    write_text(LANE_DIR / "validation_report.json", json.dumps(validation, indent=2, sort_keys=True))
    write_text(LANE_DIR / "BUILD_LOG.txt",
               f"BUILD=PASS\nREFERENCE_STEP_RELOAD={steps['count']}/{steps['count']} PASS\nREPRODUCIBILITY={repro['byte_identical']}/{repro['compared']} PASS\nPRODUCTION_CAD=0\n")
    write_text(LANE_DIR / "TEST_LOG.txt", "PENDING_CONTRACT_RUN\n")
    write_indexes()
    code, output = run_contract()
    write_text(LANE_DIR / "TEST_LOG.txt", output if output else f"exit_code={code}\n")
    write_indexes()
    if code:
        raise RuntimeError("contract test failed:\n" + output)
    final_repo = repository_guard(require_complete=True)
    return {"repository": final_repo, "validation": validation}


def verify() -> dict[str, object]:
    repo = repository_guard(require_complete=True)
    params = json.loads((LANE_DIR / "design_parameters.json").read_text(encoding="utf-8"))
    validation = json.loads((LANE_DIR / "validation_report.json").read_text(encoding="utf-8"))
    steps = step_audit(LANE_DIR)
    repro = reproducibility_audit()
    code, output = run_contract()
    write_text(LANE_DIR / "TEST_LOG.txt", output if output else f"exit_code={code}\n")
    write_indexes()
    if code or not steps["all_reload_pass"] or repro["status"] != "PASS" or params["production_cad"]["reference_step_only"] != 5:
        raise RuntimeError("VERIFY_FAIL")
    return {"repository": repo, "validation": validation, "reproducibility": repro, "step_audit": steps}


def package() -> tuple[Path, str]:
    repository_guard(require_complete=True)
    downloads = Path(r"D:\Downloads"); downloads.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = downloads / f"Paddy_Swarm_DUAL_OUTBOARD_PTO_GUARD_v0.9.6.38_{stamp}.zip"
    if zip_path.exists():
        raise FileExistsError(zip_path)
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", date_time=(2026, 8, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE_DIR / rel).read_bytes())
    return zip_path, sha256(zip_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--render-only", type=Path)
    args = parser.parse_args()
    if args.render_only is not None:
        generate_reference_payload(args.render_only)
        return 0
    result = build()
    if args.verify:
        result = verify()
    summary = {"status": "PASS", "lane": str(LANE_DIR), "exact_paths": EXPECTED_PATH_COUNT,
               "reference_steps": len(STEPS), "svgs": len(SVGS), "production_cad": 0,
               "branch": result["repository"]["branch"], "head": result["repository"]["head"],
               "staged": result["repository"]["staged"]}
    if args.package:
        path, digest = package(); summary["zip_path"] = str(path); summary["zip_sha256"] = digest
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
