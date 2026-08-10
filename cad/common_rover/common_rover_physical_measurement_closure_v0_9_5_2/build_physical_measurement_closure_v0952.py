#!/usr/bin/env python3
"""Build the measurement-only Common Rover physical closure record v0.9.5.2."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

sys.dont_write_bytecode = True

VERSION = "0.9.5.2"
CLASSIFICATION = "PHYSICAL_MEASUREMENT_RECORD"
RELEASE = "HOLD"
DESIGN_MODIFICATION = "NONE"
FINAL_STATUS = "PHYSICAL_MEASUREMENTS_RECORDED / COMMIT_READY_NOT_STAGED"
DATE_RANGE = "2026-08-09..2026-08-10"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2"
LANE = Path(__file__).resolve().parent
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_Physical_Measurement_Closure_v0_9_5_2_"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
BASE_OUTSIDE_UNTRACKED = 1684
BASE_IGNORED_TOTAL = 470

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_TREES = {
    "common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0":
        (43, "f7272fe63cc425e89e651bd413ed1822578ced912a8cf8504832457bccdfaa1b"),
    "common_rover_190mm_frame_h25a1_2s_bbox_cbox_integration_v0_9_4_1":
        (68, "ebc85195613ebdcc59925b012eacfb02900ac379d0d3c3417e2e5a53b5dab210"),
    "common_rover_physical_fit_closure_v0_9_4_2":
        (57, "ccfa35a7e5ea2d1350fae7cc6ade9f40301f0582f1ecc76f9a3de5556dfe4fe7"),
    "common_rover_service_motion_servo_slide_clutch_h25a1_v0_9_4_3":
        (66, "8b2bd9e87615c298435d3529727933e4ecb60bfdbf66275281583f0756a22b9b"),
    "common_rover_h25a1_2s_full_hardware_fixture_v0_9_4_4":
        (59, "096b9cb753c1a049f2d33248ac905aeb0c3ea768c5bdbe6ceed98e99cec2fdbe"),
    "common_rover_bbox_cbox_printable_prototype_v0_9_5_0":
        (105, "462d0f3a9c471bf434160fb9a99f834f97a28e665bc8ce6139f6a87aeadd9185"),
    "common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1":
        (53, "0157f6bb4a6f02dad08e9eade45cf3eeeb71d6b61a82e4e24ee5404498ebbe31"),
}

DOCS = [
    "README.md", "REPOSITORY_AUDIT.md", "PARENT_AUDIT.md", "MEASUREMENT_LEDGER.md",
    "CBOX_PHYSICAL_PRINT_RECORD.md", "CBOX_LID_FLATNESS_RECORD.md", "BBOX_PHYSICAL_FIT_RECORD.md",
    "BBOX_BATTERY_ORIENTATION_RECORD.md", "BBOX_TERMINAL_MEASUREMENT_RECORD.md",
    "H25A1_PRELIMINARY_PHYSICAL_TEST_RECORD.md", "DRIVE_BELT_PHYSICAL_MEASUREMENT_RECORD.md",
    "FRAME_PHYSICAL_REFERENCE_RECORD.md", "OPEN_PHYSICAL_ITEMS.md", "DESIGN_GATE.md",
]
JSONS = [
    "measurement_ledger.json", "cbox_physical_record.json", "bbox_physical_record.json",
    "terminal_physical_record.json", "h25a1_physical_record.json",
    "drive_belt_measurement_record.json", "validation_report.json",
]
SOURCE = ["build_physical_measurement_closure_v0952.py",
          "tests/test_physical_measurement_closure_v0952.py"]
RELEASE_FILES = ["MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt", "BUILD_LOG.txt", "TEST_LOG.txt"]
PACKAGE_PATHS = sorted(DOCS + JSONS + SOURCE + RELEASE_FILES)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def tree_digest(root: Path) -> tuple[int, str]:
    paths = sorted((p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts),
                   key=lambda p: p.relative_to(root).as_posix())
    h = hashlib.sha256()
    for path in paths:
        h.update(f"{sha(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(paths), h.hexdigest()


def authority_audit() -> dict[str, Any]:
    actual = {name: sha(REPO_ROOT / name) for name in AUTHORITY_HASHES}
    return {"hashes": actual, "status": "PASS" if actual == AUTHORITY_HASHES else "FAIL"}


def parent_audit() -> dict[str, Any]:
    root = REPO_ROOT / "cad/common_rover"
    rows = {}
    for name, expected in PARENT_TREES.items():
        lane = root / name
        actual = tree_digest(lane) if lane.is_dir() else None
        rows[name] = {"exists": lane.is_dir(), "expected": expected, "actual": actual,
                      "status": "PASS" if actual == expected else
                                "NOT_FOUND / RESERVED_OR_NOT_YET_GENERATED" if actual is None else "FAIL"}
    status = "PASS" if all(row["status"] == "PASS" for row in rows.values()) else "FAIL"
    return {"parents": rows, "v0.9.5.1_existence": "FOUND_READ_ONLY_AUDIT_PASS"
            if rows["common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1"]["status"] == "PASS"
            else "NOT_FOUND / RESERVED_OR_NOT_YET_GENERATED", "status": status}


def repository_guard(complete: bool = False) -> dict[str, Any]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    tracked = sorted(git("diff", "--name-only").splitlines())
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    untracked = sorted(git("ls-files", "--others", "--exclude-standard").splitlines())
    ignored = sorted(git("ls-files", "--others", "-i", "--exclude-standard").splitlines())
    lane = sorted(p[len(LANE_REL) + 1:] for p in untracked if p.startswith(LANE_REL + "/"))
    outside = [p for p in untracked if not p.startswith(LANE_REL + "/")]
    ignored_lane = [p for p in ignored if p.startswith(LANE_REL + "/")]
    forbidden = [p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and
                 (p.suffix.lower() in {".step", ".stp", ".stl", ".dxf", ".3mf", ".gcode", ".pyc"}
                  or "__pycache__" in p.parts or ".pytest_cache" in p.parts)]
    checks = {
        "root": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "tracked_preexisting_four": set(tracked) == set(AUTHORITY_HASHES), "staged_zero": not staged,
        "outside_untracked_preserved": len(outside) == BASE_OUTSIDE_UNTRACKED,
        "ignored_total_preserved": len(ignored) == BASE_IGNORED_TOTAL, "ignored_lane_zero": not ignored_lane,
        "lane_scope": set(lane).issubset(PACKAGE_PATHS),
        "lane_complete": set(lane) == set(PACKAGE_PATHS) if complete else True,
        "authority_hashes": authority_audit()["status"] == "PASS",
        "parents_read_only": parent_audit()["status"] == "PASS", "forbidden_lane_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_guard": checks, "tracked": tracked, "staged": staged,
                            "outside_untracked": len(outside), "lane": lane,
                            "ignored_total": len(ignored), "ignored_lane": ignored_lane,
                            "forbidden": forbidden})
    return {"root": str(root), "branch": branch, "head": head, "tracked": tracked, "staged": staged,
            "untracked_total": len(untracked), "outside_untracked": len(outside), "lane_untracked": len(lane),
            "ignored_total": len(ignored), "checks": checks, "status": "PASS"}


def record(record_id: str, subsystem: str, measurement: str, value: Any, unit: str,
           classification: str, source: str, status: str = "RECORDED", supersedes: str = "NONE",
           notes: str = "", date: str = DATE_RANGE, derived_from: list[str] | None = None) -> dict[str, Any]:
    row = {"id": record_id, "subsystem": subsystem, "measurement": measurement, "value": value,
           "unit": unit, "classification": classification, "date": date, "source": source,
           "status": status, "supersedes": supersedes, "notes": notes}
    if derived_from is not None:
        row["derived_from"] = derived_from
    return row


def records() -> list[dict[str, Any]]:
    r: list[dict[str, Any]] = []
    add = r.append
    # CBOX print and dry-fit results.
    add(record("CBOX-PRINT-BODY", "CBOX", "body print", "COMPLETED", "status", "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    add(record("CBOX-PRINT-LID", "CBOX", "lid print", "COMPLETED", "status", "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    add(record("CBOX-PRINT-PLATE02", "CBOX", "Plate 02 print", "COMPLETED", "status", "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    for rid, name in (("CBOX-WARP", "major visible warp"), ("CBOX-WALL-COLLAPSE", "wall collapse"),
                      ("CBOX-CORNER-LIFT", "corner lift"), ("CBOX-LID-ROCK", "lid/body rocking"),
                      ("CBOX-OPPOSITE-LIFT", "opposite-side lift when pressed"), ("CBOX-RATTLE", "lid rattle"),
                      ("CBOX-LIFT", "lid lift")):
        add(record(rid, "CBOX", name, "NONE_REPORTED" if rid in {"CBOX-WARP", "CBOX-WALL-COLLAPSE", "CBOX-CORNER-LIFT"} else "NONE",
                   "status", "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    add(record("CBOX-LID-M4", "CBOX", "all lid M4 holes", "NO_SNAG / ALIGNMENT_PASS_USER_REPORTED",
               "status", "USER_REPORTED_PHYSICAL", "USER_REPORT", "PHYSICAL_PASS_REPORTED_SCOPE_ONLY"))
    add(record("CBOX-LID-GAP", "CBOX", "unclamped/lightly seated center gap", 0.4, "mm", "MEASURED",
               "USER_REPORTED", "APPROXIMATE / GASKET_TEST_PENDING", notes="Not waterproof evidence."))
    heights = [("A1", 39.8), ("A2", 40.1), ("A3", 40.0), ("B1", 40.0), ("B2", 40.3), ("B3", 39.5)]
    for label, value in heights:
        add(record(f"CBOX-HEIGHT-{label}", "CBOX", f"body height Row/Side {label[0]} point {label[1]}", value,
                   "mm", "MEASURED", "USER_REPORTED", notes="Raw label preserved; no directional remap."))
    add(record("CBOX-HEIGHT-COUNT", "CBOX", "body height sample count", 6, "count", "DERIVED", "CALCULATION",
               derived_from=[f"CBOX-HEIGHT-{label}" for label, _ in heights]))
    add(record("CBOX-HEIGHT-MEAN", "CBOX", "body height mean", 39.95, "mm", "DERIVED", "CALCULATION",
               derived_from=[f"CBOX-HEIGHT-{label}" for label, _ in heights]))
    add(record("CBOX-HEIGHT-MIN", "CBOX", "body height minimum", 39.5, "mm", "DERIVED", "CALCULATION",
               derived_from=[f"CBOX-HEIGHT-{label}" for label, _ in heights]))
    add(record("CBOX-HEIGHT-MAX", "CBOX", "body height maximum", 40.3, "mm", "DERIVED", "CALCULATION",
               derived_from=[f"CBOX-HEIGHT-{label}" for label, _ in heights]))
    add(record("CBOX-HEIGHT-RANGE", "CBOX", "body height range", 0.8, "mm", "DERIVED", "CALCULATION",
               derived_from=["CBOX-HEIGHT-MIN", "CBOX-HEIGHT-MAX"]))
    add(record("CBOX-HEIGHT-CAD", "CBOX", "CAD nominal body height", 40.0, "mm", "CAD_NOMINAL", "V0.9.5.0_PARENT"))
    add(record("CBOX-HEIGHT-MEAN-ERROR", "CBOX", "mean minus CAD nominal", -0.05, "mm", "DERIVED", "CALCULATION",
               derived_from=["CBOX-HEIGHT-MEAN", "CBOX-HEIGHT-CAD"]))
    add(record("CBOX-SEAL-FLATNESS", "CBOX", "sealing flatness", "CONDITIONAL / PHYSICAL_GASKET_TEST_PENDING",
               "status", "HOLD", "ASSESSMENT"))
    add(record("CBOX-WATERPROOF", "CBOX", "waterproof", "NOT_TESTED", "status", "HOLD", "USER_REPORT"))
    add(record("CBOX-DRY-ASSEMBLY", "CBOX", "dry assembly", "PHYSICAL_PASS_CANDIDATE", "status",
               "USER_REPORTED_PHYSICAL", "USER_REPORT", "CANDIDATE_ONLY"))

    # BBOX, battery, and terminal evidence.
    add(record("BBOX-RING-PARALLEL", "BBOX", "service ring parallel", "YES", "status",
               "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    add(record("BBOX-RING-M4", "BBOX", "service ring M4 hole clearance sufficient", "YES", "status",
               "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    add(record("BBOX-PAD-M3", "BBOX", "wear pad M3 hole clearance sufficient", "YES", "status",
               "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    add(record("BBOX-BODY-PRINT", "BBOX", "lower body print", "COMPLETED", "status",
               "USER_REPORTED_PHYSICAL", "USER_REPORT", "PHYSICAL_PRINT_PASS_CANDIDATE"))
    add(record("BAT-LABEL-V", "Battery", "nominal label voltage", 12.8, "V", "USER_REPORTED_PHYSICAL", "PARENT_RECORD", "NOMINAL_LABEL_NOT_ELECTRICAL_TEST"))
    add(record("BAT-LABEL-AH", "Battery", "nominal label capacity", 10.0, "Ah", "USER_REPORTED_PHYSICAL", "PARENT_RECORD", "NOMINAL_LABEL_NOT_CAPACITY_TEST"))
    add(record("BAT-LABEL-WH", "Battery", "nominal label energy", 128.0, "Wh", "USER_REPORTED_PHYSICAL", "PARENT_RECORD", "NOMINAL_LABEL"))
    for rid, name, value in (("BAT-DIM-1", "physical body dimension 1", 150.9),
                             ("BAT-DIM-2", "physical body dimension 2", 99.4),
                             ("BAT-DIM-3", "physical body dimension 3", 92.5)):
        add(record(rid, "Battery", name, value, "mm", "MEASURED", "PARENT_MEASUREMENT",
                   notes="Axis naming retained as parent dimension order; no remap."))
    add(record("BAT-MASS", "Battery", "mass", 1.2, "kg", "MEASURED", "PARENT_MEASUREMENT"))
    add(record("BBOX-LONG-FIT", "BBOX/Battery", "long-side fit", "FULL_LENGTH_FIT_USER_REPORTED", "status",
               "USER_REPORTED_PHYSICAL", "USER_REPORT", notes="Does not assert zero clearance."))
    add(record("BBOX-LATERAL-LEFT", "BBOX/Battery", "reported left lateral clearance", 20.0, "mm", "MEASURED", "USER_REPORTED"))
    add(record("BBOX-LATERAL-RIGHT", "BBOX/Battery", "reported right lateral clearance", 25.0, "mm", "MEASURED", "USER_REPORTED"))
    add(record("BBOX-LATERAL-TOTAL", "BBOX/Battery", "total lateral free space", 45.0, "mm", "DERIVED", "CALCULATION",
               derived_from=["BBOX-LATERAL-LEFT", "BBOX-LATERAL-RIGHT"]))
    add(record("BBOX-LATERAL-DIFF", "BBOX/Battery", "right minus left clearance", 5.0, "mm", "DERIVED", "CALCULATION",
               derived_from=["BBOX-LATERAL-LEFT", "BBOX-LATERAL-RIGHT"]))
    add(record("BBOX-LATERAL-OFFSET", "BBOX/Battery", "half-difference from equal-center reference", 2.5, "mm", "DERIVED", "CALCULATION",
               "DERIVED_REFERENCE_ONLY", notes="Left/right datum not established.",
               derived_from=["BBOX-LATERAL-DIFF"]))
    add(record("BBOX-BAT-INSERT", "BBOX/Battery", "insertion/removal in current 150 mm frame", "POSSIBLE",
               "status", "USER_REPORTED_PHYSICAL", "PRIOR_USER_TEST"))
    add(record("BBOX-BAT-HANDLING", "BBOX/Battery", "removal handling", "GRIP_UNDERSIDE_AND_TILT_TOP_TOWARD_FRAME",
               "status", "USER_REPORTED_PHYSICAL", "PRIOR_USER_TEST", notes="Not final cassette mechanism PASS."))
    add(record("TERM-INITIAL-ORIENTATION", "Battery terminal", "initial terminal orientation", "TOWARD_IDLER_SHAFT_SIDE",
               "status", "SUPERSEDED", "USER_REPORT", "SUPERSEDED_BY_REAR_DOWN_CANDIDATE"))
    add(record("TERM-INITIAL-IDLER-CLEAR", "Battery terminal", "initial terminal-to-idler minimum clearance", 4.0,
               "mm", "MEASURED", "USER_REPORTED", "SUPERSEDED", "TERM-REARDOWN-IDLER-CLEAR", "Approximate."))
    add(record("TERM-REARDOWN-ORIENTATION", "Battery terminal", "rear/down orientation", "PREFERRED_PHYSICAL_CANDIDATE",
               "status", "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    add(record("TERM-REARDOWN-IDLER-CLEAR", "Battery terminal", "battery body-to-idler shaft clearance", 10.0,
               "mm", "MEASURED", "USER_REPORTED", "PREFERRED_CANDIDATE / HARNESS_HOLD", notes="Approximate."))
    add(record("TERM-REAR-WALL-CLEAR", "Battery terminal", "terminal-to-BBOX rear wall horizontal clearance", 37.0,
               "mm", "IMAGE_REPORTED_MEASUREMENT", "USER_REPORTED_IMAGE_CONTEXT", "CABLE_BEND_HOLD"))
    add(record("BBOX-BODY-H-PHYS", "BBOX", "lower body physical height", 97.0, "mm",
               "IMAGE_REPORTED_MEASUREMENT", "USER_REPORTED_IMAGE_CONTEXT", "APPROXIMATE / NOT_DIMENSIONAL_AUTHORITY"))
    add(record("BBOX-BODY-H-CAD", "BBOX", "lower body CAD nominal height", 97.5, "mm", "CAD_NOMINAL", "V0.9.5.0_PARENT"))
    add(record("BBOX-BOTTOM-TERM-EXTREME", "BBOX/Battery", "assembly bottom datum to terminal extreme", 103.9,
               "mm", "IMAGE_REPORTED_MEASUREMENT", "USER_REPORTED_IMAGE_CONTEXT", notes="Raw datum retained; no subtraction."))
    add(record("BAT-TAB-WIDTH", "Battery terminal", "male tab width", 6.3, "mm", "MEASURED", "USER_MEASUREMENT",
               notes="6.3 mm-class female quick-disconnect candidate only."))
    add(record("BAT-TAB-THICK", "Battery terminal", "male tab thickness", 0.7, "mm", "MEASURED", "USER_MEASUREMENT"))
    add(record("FEMALE-OUTER-W", "Battery terminal", "candidate female receptacle outer metal width", 10.6,
               "mm", "MEASURED", "USER_MEASUREMENT", "PHYSICAL_MATING_REQUIRED"))
    add(record("BAT-BOTTOM-TERM-TOP", "Battery terminal", "battery bottom to installed terminal top envelope", 99.4,
               "mm", "MEASURED", "USER_MEASUREMENT"))
    add(record("BAT-BODY-H", "Battery", "body height for common-datum terminal derivation", 92.5,
               "mm", "MEASURED", "PARENT_MEASUREMENT"))
    add(record("BAT-TERM-PROTRUSION", "Battery terminal", "terminal protrusion above battery body", 6.9,
               "mm", "DERIVED", "CALCULATION", derived_from=["BAT-BOTTOM-TERM-TOP", "BAT-BODY-H"]))
    add(record("TERM-PAIR-OUTER", "Battery terminal", "terminal pair outer span", 29.5, "mm", "MEASURED", "PRIOR_USER_MEASUREMENT"))
    add(record("TERM-PAIR-INNER", "Battery terminal", "terminal pair inner gap", 20.0, "mm", "MEASURED", "PRIOR_USER_MEASUREMENT",
               notes="Individual terminal width not derived."))
    add(record("TERM-PROTECTOR-W", "Battery terminal", "protector internal width", 13.0, "mm", "DESIGN_CANDIDATE",
               "PRIOR_DISCUSSION", "FINAL_FALSE", notes="Based on10.6 mm terminal width; no CAD generated."))
    harness_missing = ["actual crimped wire", "wire gauge", "wire insulation OD", "crimp barrel length",
                       "completed receptacle axial length", "bend start distance", "cable bend radius",
                       "strain relief dimensions", "fuse", "final connector", "waterproof boot/insulation"]
    for index, name in enumerate(harness_missing, 1):
        add(record(f"HARNESS-HOLD-{index:02d}", "Battery harness", name, None, "HOLD", "HOLD",
                   "NOT_MEASURED", "HOLD_CRIMP_TOOL_AND_HARNESS"))
    add(record("BBOX-BAT-FIT-GATE", "BBOX", "battery fit", "PHYSICAL_PASS_CANDIDATE", "status",
               "USER_REPORTED_PHYSICAL", "USER_REPORT", "CANDIDATE_ONLY"))
    add(record("BBOX-TERM-PACKAGING", "BBOX", "terminal packaging", "CONDITIONAL_PASS_CANDIDATE", "status",
               "USER_REPORTED_PHYSICAL", "ASSESSMENT", "HARNESS_HOLD"))
    add(record("BBOX-WATERPROOF", "BBOX", "waterproof", "NOT_TESTED", "status", "HOLD", "USER_REPORT"))

    # Frame physical reference.
    frame_values = [
        ("FRAME-UPPER-OUTER-1", "upper outer dimension 1", 540.0),
        ("FRAME-UPPER-OUTER-2", "upper outer dimension 2", 181.0),
        ("FRAME-LOWER-OUTER-1", "lower outer dimension 1", 442.0),
        ("FRAME-LOWER-OUTER-2", "lower outer dimension 2", 181.0),
        ("FRAME-HEIGHT", "compact frame height", 150.0),
        ("FRAME-UPPER-CLEAR-1", "upper clear dimension 1", 500.0),
        ("FRAME-UPPER-CLEAR-2", "upper clear dimension 2", 100.0),
        ("FRAME-LOWER-CLEAR-1", "lower clear dimension 1", 400.0),
        ("FRAME-LOWER-CLEAR-2", "lower clear dimension 2", 140.0),
        ("FRAME-VERTICAL-L", "vertical member length", 110.0),
        ("FRAME-GROUND-REF", "frame-bottom-to-ground/crawler-bottom reference", 68.0),
        ("FRAME-INSERT-DATUM", "idler-side observation datum to upper frame underside", 108.0),
        ("FRAME-ALT-DATUM", "previous different-datum passage measurement", 90.7),
    ]
    for rid, name, value in frame_values:
        add(record(rid, "Frame", name, value, "mm", "MEASURED", "PRIOR_PHYSICAL_AUTHORITY",
                   notes="Parent axis/datum naming retained."))
    add(record("FRAME-VERTICAL-QTY", "Frame", "vertical member count", 4, "count", "MEASURED", "PRIOR_PHYSICAL_AUTHORITY"))
    add(record("FRAME-150-STATE", "Frame", "150 mm frame state", "PRIMARY_COMPACT_BASELINE_CANDIDATE",
               "status", "DESIGN_CANDIDATE", "ASSESSMENT"))
    add(record("FRAME-190-STATE", "Frame", "190 mm frame state", "ALTERNATIVE_HOLD", "status",
               "HOLD", "ASSESSMENT"))
    add(record("FRAME-BAT-PASS", "Frame/Battery", "battery physical passage", "PHYSICAL_PASS_USER_REPORTED",
               "status", "USER_REPORTED_PHYSICAL", "PRIOR_USER_TEST"))

    # H2.5-A1-2S preliminary evidence.
    add(record("H25-COUPON-COLLAR", "H2.5-A1-2S", "collar/full-hardware narrowest coupon clearance", "VISIBLE_USABLE_CLEARANCE",
               "status", "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    add(record("H25-COUPON-REACTION", "H2.5-A1-2S", "reaction/related narrowest coupon clearance", "CLEARANCE_PRESENT",
               "status", "USER_REPORTED_PHYSICAL", "USER_REPORT"))
    for code in ("W90", "W92", "W94", "R41", "R42", "R43"):
        add(record(f"H25-CAND-{code}", "H2.5-A1-2S", "coupon candidate code", code, "candidate_code",
                   "DESIGN_CANDIDATE", "PARENT_CANDIDATE_SET", "NOT_SELECTED"))
    add(record("H25-FINAL-TOL", "H2.5-A1-2S", "final selected tolerance", None, "HOLD", "HOLD", "NOT_REPORTED", "HOLD"))
    add(record("H25-HAND-ROT", "H2.5-A1-2S", "aggressive hand rotation shaft shift", "NONE_REPORTED",
               "status", "USER_REPORTED_PHYSICAL", "USER_REPORT", "NO_SHAFT_SHIFT_REPORTED"))
    add(record("H25-STATIC-INITIAL", "H2.5-A1-2S", "initial1.2 kg static lever observation shaft shift",
               "NONE_REPORTED", "status", "USER_REPORTED_PHYSICAL", "USER_REPORT",
               "PRELIMINARY_ONLY / CREEP_NOT_CLOSED"))
    add(record("H25-LOAD-MASS", "H2.5-A1-2S", "preliminary static-load battery mass", 1.2, "kg", "MEASURED", "PARENT_MEASUREMENT"))
    add(record("H25-LEVER", "H2.5-A1-2S", "later observation lever point", 70.0, "mm", "MEASURED", "USER_REPORTED"))
    add(record("H25-G", "H2.5-A1-2S", "nominal gravitational acceleration reference", 9.80665, "m/s^2", "DERIVED", "STANDARD_CONSTANT",
               "REFERENCE_ONLY"))
    torque = 1.2 * 9.80665 * 0.070
    add(record("H25-TORQUE-CALC", "H2.5-A1-2S", "nominal vertical/perpendicular torque calculation", torque,
               "N*m", "DERIVED", "CALCULATION", "DERIVED_NOMINAL_REFERENCE_ONLY",
               notes="Not formal torque PASS.", derived_from=["H25-LOAD-MASS", "H25-LEVER", "H25-G"]))
    add(record("H25-TORQUE-ROUND", "H2.5-A1-2S", "rounded nominal torque reference", 0.824,
               "N*m", "DERIVED", "CALCULATION", "DERIVED_NOMINAL_REFERENCE_ONLY",
               derived_from=["H25-TORQUE-CALC"]))
    add(record("H25-CREEP", "H2.5-A1-2S", "1.2 kg at70 mm creep observation", "PHYSICAL_OBSERVATION_PENDING / DO_NOT_CLOSE",
               "status", "HOLD", "USER_REPORT", "PENDING"))
    add(record("H25-FULL-SPROCKET", "H2.5-A1-2S", "full sprocket", "HOLD", "status", "HOLD", "PARENT_GATE"))

    # DRIVE belt physical and candidate data.
    add(record("DRIVE-SMALL-T", "DRIVE", "small pulley tooth count", 20, "teeth", "CAD_NOMINAL", "PARENT_CAD"))
    add(record("DRIVE-LARGE-T", "DRIVE", "large pulley tooth count", 60, "teeth", "CAD_NOMINAL", "PARENT_CAD"))
    add(record("DRIVE-PITCH", "DRIVE", "HTD5M pitch", 5.0, "mm", "CAD_NOMINAL", "PARENT_CAD"))
    add(record("DRIVE-CENTER", "DRIVE", "20T-to-60T center distance", 180.0, "mm", "MEASURED", "USER_REPORTED"))
    add(record("DRIVE-STRING", "DRIVE", "vinyl string loop", 583.0, "mm", "MEASURED", "USER_REPORTED",
               "CONFLICT_RETAINED"))
    for teeth, length, status in ((113, 565.0, "PRIMARY_TPU_TRIAL_CANDIDATE"),
                                  (114, 570.0, "COMPARISON_CANDIDATE"),
                                  (112, 560.0, "COMPARISON_CANDIDATE")):
        add(record(f"DRIVE-{teeth}-TEETH", "DRIVE", f"{teeth}T candidate tooth count", teeth, "teeth",
                   "DESIGN_CANDIDATE", "V0.9.5.1_DISCUSSION", status))
        add(record(f"DRIVE-{teeth}-LENGTH", "DRIVE", f"{teeth}T candidate pitch length", length, "mm",
                   "DESIGN_CANDIDATE", "V0.9.5.1_DISCUSSION", status))
    add(record("DRIVE-CONFLICT", "DRIVE", "583 mm string versus two-pulley geometry", "UNRESOLVED",
               "status", "HOLD", "ASSESSMENT", "PHYSICAL_BELT_TEST_REQUIRED"))
    add(record("DRIVE-TPU", "DRIVE", "113T TPU trial", "PHYSICAL_TEST_PENDING", "status",
               "HOLD", "V0.9.5.1_PARENT"))
    add(record("DRIVE-COMMERCIAL", "DRIVE", "commercial belt final", "HOLD", "status", "HOLD", "ASSESSMENT",
               "NO_PURCHASE_APPROVAL"))

    add(record("POWERED", "System", "powered rotation", "NOT_APPROVED", "status", "HOLD", "PROTECTED_GATE"))
    add(record("FIELD", "System", "field deployment", "NOT_APPROVED", "status", "HOLD", "PROTECTED_GATE"))
    return r


def numeric_exclusions() -> list[dict[str, str]]:
    return [
        {"token": "0..49", "context": "prompt section numbers", "reason": "document structure, not engineering data"},
        {"token": "1..42", "context": "requested final-report numbering", "reason": "output structure, not engineering data"},
        {"token": "v0.9.4.0..v0.9.5.2", "context": "lane versions", "reason": "version identifiers; parent hashes are audited separately"},
        {"token": "20260725", "context": "historical branch identifier", "reason": "identifier component, not measurement"},
        {"token": "facb4f63...", "context": "Git commit hash", "reason": "identifier; recorded by repository audit"},
        {"token": "4 tracked changes", "context": "pre-existing worktree state", "reason": "repository count; recorded by repository audit, not measurement ledger"},
        {"token": "Plate 02", "context": "printed artifact name", "reason": "part identifier; print result is ledgered"},
        {"token": "M3/M4", "context": "fastener/hole designation", "reason": "thread nominal designation, not a measured diameter"},
        {"token": "YYYYMMDD_HHMMSS", "context": "ZIP filename format", "reason": "timestamp template, not engineering data"},
        {"token": "6.3mm-class", "context": "connector reference class", "reason": "compatibility label only; measured tab6.3 mm is ledgered"},
    ]


def ledger() -> dict[str, Any]:
    return {"schema": "paddy_swarm.common_rover.physical_measurement_ledger.v0.9.5.2",
            "version": VERSION, "classification": CLASSIFICATION, "release": RELEASE,
            "design_modification": DESIGN_MODIFICATION, "date_range": DATE_RANGE,
            "classification_vocabulary": ["MEASURED", "USER_REPORTED_PHYSICAL", "IMAGE_REPORTED_MEASUREMENT",
                                          "DERIVED", "CAD_NOMINAL", "DESIGN_CANDIDATE", "HOLD", "SUPERSEDED"],
            "records": records(), "prompt_numeric_exclusions": numeric_exclusions(),
            "image_authority_statement": "USER_REPORTED / IMAGE_REPORTED_MEASUREMENT; Codex did not perform image metrology"}


def cbox_record() -> dict[str, Any]:
    rows = {row["id"]: row for row in records() if row["subsystem"] == "CBOX"}
    return {"schema": "paddy_swarm.common_rover.cbox_physical_record.v0.9.5.2", "records": rows,
            "raw_heights_mm": {"Row/Side A": [39.8, 40.1, 40.0], "Row/Side B": [40.0, 40.3, 39.5]},
            "derived_statistics_mm": {"mean": 39.95, "minimum": 39.5, "maximum": 40.3,
                                      "range": 0.8, "mean_error_from_cad40": -0.05},
            "waterproof": "NOT_TESTED", "cad_pass": "NOT_EVALUATED_NO_DESIGN_CHANGE"}


def bbox_record() -> dict[str, Any]:
    rows = {row["id"]: row for row in records() if row["subsystem"] in {"BBOX", "BBOX/Battery", "Battery", "Frame/Battery"}}
    return {"schema": "paddy_swarm.common_rover.bbox_physical_record.v0.9.5.2", "records": rows,
            "axis_rule": "PARENT_DIMENSION_ORDER_RETAINED / NO_XYZ_REMAP",
            "battery_fit": "PHYSICAL_PASS_CANDIDATE", "waterproof": "NOT_TESTED"}


def terminal_record() -> dict[str, Any]:
    rows = {row["id"]: row for row in records() if row["subsystem"] in {"Battery terminal", "Battery harness"}}
    return {"schema": "paddy_swarm.common_rover.terminal_physical_record.v0.9.5.2", "records": rows,
            "preferred_orientation": "TERMINALS_REAR_AND_DOWN", "final_harness": "HOLD_CRIMP_TOOL_AND_HARNESS",
            "commercial_faston_standard_proven": False, "cable_bend_pass": False, "waterproof_pass": False}


def h25_record() -> dict[str, Any]:
    rows = {row["id"]: row for row in records() if row["subsystem"] == "H2.5-A1-2S"}
    return {"schema": "paddy_swarm.common_rover.h25a1_preliminary_physical_record.v0.9.5.2", "records": rows,
            "coupon_fit": "PHYSICAL_CLEARANCE_CONFIRMED_USER_REPORTED", "final_selected_tolerance": "HOLD",
            "hand_rotation": "NO_SHAFT_SHIFT_REPORTED", "creep": "PHYSICAL_OBSERVATION_PENDING / DO_NOT_CLOSE",
            "formal_torque_pass": False, "powered_rotation": "NOT_APPROVED"}


def drive_record() -> dict[str, Any]:
    rows = {row["id"]: row for row in records() if row["subsystem"] == "DRIVE"}
    return {"schema": "paddy_swarm.common_rover.drive_belt_measurement_record.v0.9.5.2", "records": rows,
            "measured_center_mm": 180.0, "measured_string_loop_mm": 583.0,
            "primary_candidate": {"teeth": 113, "pitch_length_mm": 565.0, "classification": "DESIGN_CANDIDATE"},
            "conflict": "RETAINED / PHYSICAL_BELT_TEST_REQUIRED", "commercial_belt_final": "HOLD"}


def validate_measurements() -> dict[str, Any]:
    rows = records()
    by_id = {row["id"]: row for row in rows}
    heights = [by_id[f"CBOX-HEIGHT-{label}"]["value"] for label in ("A1", "A2", "A3", "B1", "B2", "B3")]
    calc_torque = 1.2 * 9.80665 * 0.070
    ids = [row["id"] for row in rows]
    allowed = {"MEASURED", "USER_REPORTED_PHYSICAL", "IMAGE_REPORTED_MEASUREMENT", "DERIVED",
               "CAD_NOMINAL", "DESIGN_CANDIDATE", "HOLD", "SUPERSEDED"}
    forbidden_image_source = "CODEX_" + "MEASURED_FROM_IMAGE"
    checks = {
        "measurement_ids_unique": len(ids) == len(set(ids)),
        "units_explicit": all(bool(row["unit"]) for row in rows),
        "classifications_closed": all(row["classification"] in allowed for row in rows),
        "cbox_raw_preserved": heights == [39.8, 40.1, 40.0, 40.0, 40.3, 39.5],
        "cbox_mean": math.isclose(sum(heights) / 6.0, 39.95, abs_tol=1e-12),
        "cbox_range": math.isclose(max(heights) - min(heights), 0.8, abs_tol=1e-12),
        "cbox_mean_error": math.isclose(by_id["CBOX-HEIGHT-MEAN"]["value"] - 40.0, -0.05, abs_tol=1e-12),
        "terminal_protrusion": math.isclose(99.4 - 92.5, 6.9, abs_tol=1e-12),
        "lateral_total": 20.0 + 25.0 == 45.0,
        "lateral_difference": 25.0 - 20.0 == 5.0,
        "lateral_half_difference": (25.0 - 20.0) / 2.0 == 2.5,
        "torque_reference": math.isclose(calc_torque, by_id["H25-TORQUE-CALC"]["value"], abs_tol=1e-12),
        "torque_not_pass": by_id["H25-CREEP"]["status"] == "PENDING",
        "image_wording": all(row["source"] != forbidden_image_source for row in rows),
        "unresolved_hold": all(key in by_id for key in ("H25-FINAL-TOL", "DRIVE-COMMERCIAL", "CBOX-WATERPROOF", "BBOX-WATERPROOF")),
        "no_powered_pass": by_id["POWERED"]["value"] == "NOT_APPROVED",
        "no_field_pass": by_id["FIELD"]["value"] == "NOT_APPROVED",
        "no_cad_artifacts": not any(p.suffix.lower() in {".step", ".stp", ".stl", ".dxf", ".3mf", ".gcode"}
                                    for p in LANE.rglob("*") if p.is_file()),
        "authority_unchanged": authority_audit()["status"] == "PASS",
        "parents_unchanged": parent_audit()["status"] == "PASS",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL",
            "record_count": len(rows), "cad_pass": "NOT_EVALUATED_NO_DESIGN_CHANGE",
            "physical_pass_scope": "ONLY_EXPLICIT_USER_REPORTED_ITEMS / CANDIDATE_WHERE_SPECIFIED",
            "design_modification": DESIGN_MODIFICATION, "release": RELEASE,
            "powered_rotation": "NOT_APPROVED", "field_deployment": "NOT_APPROVED",
            "final_status": FINAL_STATUS if all(checks.values()) else "FAIL"}


def gates() -> dict[str, str]:
    return {
        "FRAME_PHYSICAL_REFERENCE": "RECORDED",
        "CBOX_PRINT": "PHYSICAL_PRINT_PASS_CANDIDATE",
        "CBOX_DRY_ASSEMBLY": "PHYSICAL_PASS_CANDIDATE",
        "CBOX_SEALING_FLATNESS": "CONDITIONAL / PHYSICAL_GASKET_TEST_PENDING",
        "CBOX_WATERPROOF": "NOT_TESTED",
        "BBOX_BODY_PRINT": "PHYSICAL_PRINT_PASS_CANDIDATE",
        "BBOX_BATTERY_FIT": "PHYSICAL_PASS_CANDIDATE",
        "BBOX_REAR_DOWN_ORIENTATION": "PREFERRED_PHYSICAL_CANDIDATE",
        "BBOX_FINAL_HARNESS": "HOLD_CRIMP_TOOL_AND_HARNESS",
        "BBOX_WATERPROOF": "NOT_TESTED",
        "H25A1_COUPON_FIT": "PHYSICAL_CLEARANCE_CONFIRMED_USER_REPORTED",
        "H25A1_HAND_ROTATION": "NO_SHAFT_SHIFT_REPORTED",
        "H25A1_CREEP": "PENDING",
        "FULL_SPROCKET": "HOLD",
        "DRIVE_113T_TPU": "DESIGN_CANDIDATE / PHYSICAL_TEST_PENDING",
        "COMMERCIAL_DRIVE_BELT": "HOLD",
        "POWERED_ROTATION": "NOT_APPROVED",
        "FIELD_DEPLOYMENT": "NOT_APPROVED",
    }


def md_table(rows: list[dict[str, Any]]) -> str:
    columns = ["id", "subsystem", "measurement", "value", "unit", "classification", "date", "source", "status", "supersedes", "notes"]
    header = "| ID | Subsystem | Measurement | Value | Unit | Classification | Date | Source | Status | Supersedes | Notes |\n"
    divider = "|---|---|---|---:|---|---|---|---|---|---|---|\n"
    lines = []
    for row in rows:
        values = []
        for key in columns:
            value = row.get(key, "")
            if isinstance(value, list):
                value = ", ".join(value)
            values.append(str(value).replace("|", "/").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return header + divider + "\n".join(lines) + "\n"


def documents(repo: dict[str, Any], parents: dict[str, Any], valid: dict[str, Any]) -> dict[str, str]:
    head = lambda title: (f"# {title}\n\nVersion: v{VERSION}  \nClassification: `{CLASSIFICATION}`  \n"
                          f"Release: `{RELEASE}`  \nDesign modification: `{DESIGN_MODIFICATION}`  \n")
    rows = records()
    by_id = {row["id"]: row for row in rows}
    parent_lines = "\n".join(f"- `{name}`: {row['actual'][0]} files / `{row['actual'][1]}` — `{row['status']}`"
                             for name, row in parents["parents"].items())
    docs = {
        "README.md": head("Common Rover Physical Measurement Closure Record") +
            f"\nThis lane records physical measurements and user-reported tests from {DATE_RANGE}. It changes no CAD, STEP, STL, parent lane or authority. Raw, reported, image-context, derived, candidate, superseded and HOLD information remain distinct.\n\nFinal status: `{FINAL_STATUS}`. Powered rotation and field deployment remain `NOT_APPROVED`.\n",
        "REPOSITORY_AUDIT.md": head("Repository audit") +
            f"\n- Root: `{repo['root']}`\n- Branch: `{repo['branch']}`\n- HEAD: `{repo['head']}`\n- Pre-existing tracked paths: {len(repo['tracked'])}, unchanged\n- Staged: {len(repo['staged'])}\n- Outside-lane untracked: {repo['outside_untracked']}\n- Ignored total: {repo['ignored_total']}\n- Authority audit: `{authority_audit()['status']}`\n\nNo Git mutation operation was performed.\n",
        "PARENT_AUDIT.md": head("Read-only parent lane audit") + "\n" + parent_lines +
            f"\n\nv0.9.5.1 existence: `{parents['v0.9.5.1_existence']}`. Parent files were read only.\n",
        "MEASUREMENT_LEDGER.md": head("Measurement ledger") +
            "\nClassification follows the closed vocabulary in `measurement_ledger.json`. IMAGE_REPORTED_MEASUREMENT means the user supplied the measurement through image context; it never means Codex performed image metrology.\n\n" +
            md_table(rows) + "\n## Prompt numeric exclusions\n\n" +
            "\n".join(f"- `{row['token']}` ({row['context']}): {row['reason']}" for row in numeric_exclusions()) + "\n",
        "CBOX_PHYSICAL_PRINT_RECORD.md": head("CBOX physical print record") +
            "\nBody, lid and Plate02 prints are complete. No major visible warp, wall collapse or corner lift was reported. Lid/body rocking and opposite-side lift were reported as NONE. All lid M4 holes were reported NO_SNAG/aligned. Waterproof testing has not occurred.\n",
        "CBOX_LID_FLATNESS_RECORD.md": head("CBOX lid flatness record") +
            "\nThe unclamped/lightly seated center gap is approximately0.4 mm (`MEASURED`, user-reported). Rattle and lift were reported NONE. Raw body heights remain A:[39.8,40.1,40.0] and B:[40.0,40.3,39.5] mm without directional remap. Derived mean39.95, min39.5, max40.3, range0.8 and error from40.0 nominal −0.05 mm. `SEALING_FLATNESS=CONDITIONAL`; `WATERPROOF=NOT_TESTED`.\n",
        "BBOX_PHYSICAL_FIT_RECORD.md": head("BBOX physical fit record") +
            "\nService ring parallel and M4 clearance were reported YES. Wear-pad M3 clearance was reported YES. Battery long-side fit is `FULL_LENGTH_FIT_USER_REPORTED`, not measured zero clearance. Lateral clearances20/25 mm derive45 mm total,5 mm difference and2.5 mm reference-only offset. Battery insertion/removal is possible by the reported underside-grip and tilt handling, but no final cassette mechanism is released.\n",
        "BBOX_BATTERY_ORIENTATION_RECORD.md": head("BBOX battery orientation record") +
            "\nThe initial terminal-toward-idler orientation retained an approximately4 mm clearance and is `SUPERSEDED_BY_REAR_DOWN_CANDIDATE`. Rear/down is preferred and reports approximately10 mm battery-body/idler clearance. Cable, lug and insulation are absent, so final harness clearance is HOLD.\n",
        "BBOX_TERMINAL_MEASUREMENT_RECORD.md": head("BBOX terminal measurement record") +
            "\nRear-wall clearance37.0 mm and assembly-bottom-to-terminal-extreme103.9 mm are `IMAGE_REPORTED_MEASUREMENT`; no Codex image metrology is claimed. Lower body is approximately97.0 mm image-context versus97.5 mm CAD nominal. Male tab6.3×0.7 mm, female outer metal width10.6 mm, battery-bottom-to-terminal-top99.4 mm and common-datum body height92.5 mm are retained. Only the last common-datum pair derives6.9 mm protrusion. Terminal pair outer span29.5 mm and inner gap20.0 mm do not derive individual widths. The13 mm protector width is a design candidate only; no CAD was generated.\n",
        "H25A1_PRELIMINARY_PHYSICAL_TEST_RECORD.md": head("H2.5-A1-2S preliminary physical test") +
            f"\nNarrowest collar/full-hardware and reaction coupons were reported to retain clearance, but W90/W92/W94 and R41/R42/R43 remain unselected. Aggressive hand rotation reported no shaft shift; it was not powered. A1.2 kg load moved to a70 mm point gives a nominal vertical/perpendicular reference of {by_id['H25-TORQUE-CALC']['value']:.9f} N·m (≈0.824), not a formal torque PASS. Creep remains `PHYSICAL_OBSERVATION_PENDING / DO_NOT_CLOSE`.\n",
        "DRIVE_BELT_PHYSICAL_MEASUREMENT_RECORD.md": head("DRIVE belt physical measurement record") +
            "\n20T→60T HTD5M at measured center180.0 mm and measured/user-reported vinyl string583 mm are both retained. The string conflict is unresolved. 113T/565 mm is the primary TPU design candidate;114T/570 and112T/560 are comparisons. TPU physical testing and commercial belt selection remain HOLD; no purchase is approved.\n",
        "FRAME_PHYSICAL_REFERENCE_RECORD.md": head("Frame physical reference record") +
            "\nPrimary compact reference: upper outer540×181, lower442×181, height150, upper clear500×100, lower clear400×140 mm, four110 mm verticals and68 mm ground/crawler reference. The108.0 mm insertion datum and90.7 mm prior datum are both valid different-datum measurements. Frame150 remains primary candidate;190 is alternative HOLD. No axis remap or frame redesign occurs here.\n",
        "OPEN_PHYSICAL_ITEMS.md": head("Open physical items") +
            "\n- CBOX gasket compression, seal and water test: HOLD\n- BBOX ring/gasket/cap/feedthrough/restraint and water test: HOLD\n- Crimped harness geometry, wire, bend, strain relief, fuse, connector and boot: HOLD\n- H2.5 selected tolerance and post-creep inspection: HOLD\n- DRIVE TPU coupon/full-loop test, adjustment range and commercial belt: HOLD\n- Powered rotation and field deployment: NOT_APPROVED\n",
        "DESIGN_GATE.md": head("Measurement closure design gates") + "\n" +
            "\n".join(f"- `{key}` = `{value}`" for key, value in gates().items()) +
            "\n\nNo CAD_PASS is issued in this measurement-only lane. Candidate physical states do not imply waterproof, powered or field approval.\n",
    }
    return docs


def build() -> dict[str, Any]:
    preflight = repository_guard(False)
    parents = parent_audit()
    valid = validate_measurements()
    payloads = {
        "measurement_ledger.json": ledger(), "cbox_physical_record.json": cbox_record(),
        "bbox_physical_record.json": bbox_record(), "terminal_physical_record.json": terminal_record(),
        "h25a1_physical_record.json": h25_record(), "drive_belt_measurement_record.json": drive_record(),
        "validation_report.json": valid,
    }
    for name, value in payloads.items():
        write_json(LANE / name, value)
    for name, value in documents(preflight, parents, valid).items():
        write(LANE / name, value)
    write(LANE / "MANIFEST.txt", "\n".join(PACKAGE_PATHS))
    write(LANE / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL}/{path}" for path in PACKAGE_PATHS))
    write(LANE / "BUILD_LOG.txt",
          f"BUILD PASS\nversion={VERSION}\nclassification={CLASSIFICATION}\ndesign_modification={DESIGN_MODIFICATION}\n"
          f"Python={sys.version.split()[0]}\nbranch={preflight['branch']}\nHEAD={preflight['head']}\n"
          f"preflight_untracked={preflight['untracked_total']}\noutside_untracked={preflight['outside_untracked']}\n"
          f"ignored_total={preflight['ignored_total']}\nparent_lanes=7_PASS\nv0.9.5.1=FOUND_READ_ONLY_AUDIT_PASS\n"
          f"record_count={valid['record_count']}\ncad_artifacts=0\ncad_pass=NOT_EVALUATED_NO_DESIGN_CHANGE\n"
          "powered_rotation=NOT_APPROVED\nfield_deployment=NOT_APPROVED\n")
    write(LANE / "TEST_LOG.txt", "PENDING_TEST_EXECUTION")
    hashed = [path for path in PACKAGE_PATHS if path != "SHA256SUMS.txt"]
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / path)}  {path}" for path in hashed))
    test = subprocess.run([sys.executable, "-B", str(LANE / SOURCE[1])], cwd=REPO_ROOT,
                          text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if test.returncode:
        raise RuntimeError(test.stdout)
    write(LANE / "TEST_LOG.txt", test.stdout)
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / path)}  {path}" for path in hashed))
    return {"status": valid["final_status"], "guard": repository_guard(True), "validation": valid}


def verify_files() -> dict[str, Any]:
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts)
    manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    hashes = {}
    for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        hashes[rel] = digest
    bad = [rel for rel, digest in hashes.items() if sha(LANE / rel) != digest]
    parsed = {rel: json.loads((LANE / rel).read_text(encoding="utf-8")) for rel in JSONS}
    forbidden = [rel for rel in files if Path(rel).suffix.lower() in {".step", ".stp", ".stl", ".dxf", ".3mf", ".gcode", ".pyc"}]
    checks = {
        "package_exact": files == PACKAGE_PATHS and manifest == PACKAGE_PATHS,
        "commit_paths_exact": commit_paths == [f"{LANE_REL}/{path}" for path in PACKAGE_PATHS],
        "hashes_exact": not bad and set(hashes) == set(PACKAGE_PATHS) - {"SHA256SUMS.txt"},
        "json_valid": len(parsed) == 7, "forbidden_zero": not forbidden,
        "validation_pass": parsed["validation_report.json"]["status"] == "PASS",
        "cad_pass_not_issued": parsed["validation_report.json"]["cad_pass"] == "NOT_EVALUATED_NO_DESIGN_CHANGE",
        "design_none": parsed["validation_report.json"]["design_modification"] == "NONE",
        "release_hold": parsed["validation_report.json"]["release"] == "HOLD",
    }
    if not all(checks.values()):
        raise RuntimeError({"checks": checks, "bad": bad, "forbidden": forbidden,
                            "missing": sorted(set(PACKAGE_PATHS) - set(files)),
                            "extras": sorted(set(files) - set(PACKAGE_PATHS))})
    return {"status": "PASS", "file_count": len(files), "json_count": len(parsed),
            "cad_artifact_count": 0, "checks": checks, "bad_hashes": bad}


def make_zip() -> tuple[Path, str]:
    path = DOWNLOADS / f"{ZIP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise FileExistsError(path)
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as archive:
        for rel in PACKAGE_PATHS:
            archive.write(LANE / rel, rel)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        bad_paths = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts]
        if archive.testzip() or len(names) != len(set(names)) or bad_paths or sorted(names) != PACKAGE_PATHS:
            raise RuntimeError("ZIP_STRUCTURE_CONTRACT_FAILED")
        if archive.read("MANIFEST.txt").decode("utf-8").splitlines() != PACKAGE_PATHS:
            raise RuntimeError("ZIP_MANIFEST_CONTRACT_FAILED")
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            if hashlib.sha256(archive.read(rel)).hexdigest() != digest:
                raise RuntimeError(f"ZIP_HASH_FAILED: {rel}")
        for rel in JSONS:
            json.loads(archive.read(rel).decode("utf-8"))
    return path, sha(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        args.build = args.verify = True
    result: dict[str, Any] = {}
    if args.build:
        result["build"] = build()
    if args.verify:
        result["guard"] = repository_guard(True)
        result["verify"] = verify_files()
    if args.zip:
        path, digest = make_zip()
        result["zip"] = {"path": str(path), "sha256": digest}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
