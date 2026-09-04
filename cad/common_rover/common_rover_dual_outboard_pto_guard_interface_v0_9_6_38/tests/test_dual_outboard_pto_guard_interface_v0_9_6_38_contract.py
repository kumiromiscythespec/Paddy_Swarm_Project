"""Contract for the v0.9.6.38 documentation/interface-freeze lane."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import cadquery as cq
from cadquery import importers

LANE = Path(__file__).resolve().parents[1]
BUILDER_PATH = LANE / "build_dual_outboard_pto_guard_interface_v0_9_6_38.py"
spec = importlib.util.spec_from_file_location("pto_v09638", BUILDER_PATH)
assert spec and spec.loader
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

tests = 0


def check(condition: bool, label: str) -> None:
    global tests
    tests += 1
    if not condition:
        raise AssertionError(label)


repo = b.repository_guard(require_complete=True)
p = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
v = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))

check(repo["checks"]["repository"], "repository")
check(repo["checks"]["branch"], "branch")
check(repo["checks"]["head"], "head")
check(repo["checks"]["staged_zero"], "staged")
check(repo["checks"]["tracked_dirty_preserved"], "tracked dirty")
check(repo["checks"]["outside_untracked_preserved"], "outside untracked")
check(repo["checks"]["authority_4_of_4"], "authority")
check(repo["checks"]["protected_trees"], "protected trees")
check(repo["checks"]["forbidden_production_formats_zero"], "production formats")
check(repo["checks"]["complete"], "exact files")
check(p["architecture"]["pto_count"] == 2, "two PTO")
check(p["architecture"]["left_direction"] == "OUTWARD_NEGATIVE_X", "left -X")
check(p["architecture"]["right_direction"] == "OUTWARD_POSITIVE_X", "right +X")
check(p["architecture"]["left_right_independent"], "independent")
check(p["architecture"]["common_shaft"] is False, "no common shaft")
check(p["architecture"]["historical_inward_candidate"] == "SUPERSEDED_BY_NEW_PHYSICAL_LAYOUT_CONSTRAINT", "superseded register")
check(p["width_mm"]["frame_worst_case"] == 205, "worst case")
check(p["width_mm"]["per_side"]["pulley_usable_authority"] == 20, "20 zone")
check(p["width_mm"]["per_side"]["total"] == 29, "side stack")
check(p["width_mm"]["pulley_body_only"] == [240.0, 245.0], "pulley widths")
check(p["width_mm"]["guarded_reference"] == [258.0, 263.0], "guarded widths")
check(max(p["width_mm"]["guarded_reference"]) <= 265, "target")
check(p["width_mm"]["registered_ceiling"] == 286, "registered ceiling")
check(p["width_mm"]["worst_case_target_margin"] == 2, "target margin")
check(p["width_mm"]["worst_case_ceiling_margin"] == 23, "ceiling margin")
check(p["guard"]["mandatory"], "guard mandatory")
check(set(p["guard"]["coverage"]) == {"TOP", "FRONT", "OUTBOARD"}, "coverage")
check(set(p["guard"]["open"]) == {"BOTTOM", "LOWER_REAR"}, "open")
check(p["guard"]["sealed_box"] is False, "not sealed")
check(p["guard"]["sensitivity_mm"] == [3.0, 5.0], "guard sensitivity")
check(p["shaft"]["load_authority"] == "ROTATIONAL_TORQUE_ONLY", "torque only")
check(p["shaft"]["diameter_mm"] == "HOLD", "shaft hold")
check(p["shaft"]["pulley_center_overhang_max_candidate_mm"] <= 15, "overhang")
check(p["shaft"]["work_unit_weight_or_reaction"] == "PROHIBITED", "no work loads")
check(p["work_unit"]["support"] == "DEDICATED_HITCH_AND_GUIDE_FRAME", "support path")
check(p["simultaneous_drive_pto"] == "PROHIBITED", "simultaneous")
check(p["operation_sequence"] == ["DRIVE", "STOP", "DRIVE_DISENGAGE", "LOCK_OR_BRAKE", "PTO_ENGAGE", "WORK", "PTO_DISENGAGE", "DRIVE_RESTORE"], "sequence")
check(all(value == 0 for key, value in p["production_cad"].items() if key != "reference_step_only"), "no production CAD")
check(p["production_cad"]["reference_step_only"] == 5, "five refs")
check(len(b.STEPS) == 5, "STEP count")
check(len(b.SVGS) == 8, "SVG count")
check(len(b.DOCS) == 14, "doc count")
check(b.EXPECTED_PATH_COUNT == 31, "path count")
check(len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 31, "commit paths")
check("SUPERSEDED_BY_NEW_PHYSICAL_LAYOUT_CONSTRAINT" in (LANE / "SUPERSEDED_PTO_DIRECTION_REGISTER.md").read_text(encoding="utf-8"), "historic record")
check("not a sealed box" in (LANE / "PTO_GUARD_REQUIREMENTS.md").read_text(encoding="utf-8"), "drainage")
check("never PTO shafts or box walls" in (LANE / "ARCHITECTURE_DECISION.md").read_text(encoding="utf-8"), "load path")
check("NOT_FOR_MANUFACTURING" in (LANE / "README.md").read_text(encoding="utf-8"), "release label")
for rel in b.STEPS:
    shape = importers.importStep(str(LANE / rel))
    check(shape.val().isValid(), rel + " valid")
    check(len(shape.solids().vals()) >= 1, rel + " solids")
for rel in b.SVGS:
    text = (LANE / rel).read_text(encoding="utf-8")
    check(text.startswith("<svg"), rel + " SVG")
    check("REFERENCE_ONLY" in text, rel + " reference")
check(round(importers.importStep(str(LANE / b.STEPS[0])).val().BoundingBox().xlen, 3) == 200, "frame 200 bbox")
check(round(importers.importStep(str(LANE / b.STEPS[1])).val().BoundingBox().xlen, 3) == 205, "frame 205 bbox")
check(round(importers.importStep(str(LANE / b.STEPS[2])).val().BoundingBox().xlen, 3) == 263, "interface 263 bbox")
check(round(importers.importStep(str(LANE / b.STEPS[3])).val().BoundingBox().xlen, 3) == 263, "guard reference 263 bbox")
check(v["pass_count"] == v["check_count"], "validation")
check(v["reproducibility"]["status"] == "PASS", "repro report")
check(v["step_audit"]["all_reload_pass"], "step report")
check(v["status"] == "CONDITIONAL_INTERFACE_PASS_DOCUMENTATION_COMPLETE_NOT_FOR_MANUFACTURING", "status")

print(f"AUTOMATED_TESTS={tests}/{tests} PASS")
print("REFERENCE_STEP_RELOAD=5/5 PASS")
print("PRODUCTION_CAD=0 PASS")
print("PROTECTED_LANES=11/11 UNCHANGED")
print("FINAL=PASS")
