"""Executable contract for the v0.9.6.33 industrial torque-core comparison."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_generic_keyed_industrial_torque_core_comparison_v0_9_6_33.py"
spec = importlib.util.spec_from_file_location("v09633", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load builder")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

checks: list[tuple[str, bool]] = []


def check(name: str, condition: object) -> None:
    value = bool(condition)
    checks.append((name, value))
    if not value:
        raise AssertionError(name)


guard = m.repository_guard(True)
validation = json.loads((LANE / "data/validation_report.json").read_text(encoding="utf-8"))
parameters = json.loads((LANE / "data/design_parameters.json").read_text(encoding="utf-8"))
metrics = json.loads((LANE / "data/candidate_metrics.json").read_text(encoding="utf-8"))

for name, value in guard["checks"].items():
    check(f"repository_{name}", value)
check("branch", guard["branch"] == m.EXPECTED_BRANCH)
check("head", guard["head"] == m.EXPECTED_HEAD)
check("staged_zero", guard["staged"] == [])
check("tracked_dirty_preserved", guard["tracked_dirty"] == m.TRACKED_DIRTY)
for rel, expected in m.AUTHORITY_SHA256.items():
    check(f"authority_{rel}", guard["authority_sha256"][rel] == expected)
for rel, expected in m.PROTECTED_LANES.items():
    row = guard["protected_lanes"][rel]
    check(f"protected_count_{rel}", row["count"] == expected[0])
    check(f"protected_sha_{rel}", row["tree_sha256"] == expected[1])
    check(f"protected_state_{rel}", row["status"] == "UNCHANGED")
for rel, expected in m.SOURCE_SHA256.items():
    check(f"source_{rel}", guard["source_sha256"][rel] == expected)

outer = validation["geometry"]["outer_p20653"]
check("p20653_source_sha", outer["source_step_sha256"] == m.SOURCE_SHA256[m.V31_STEP_REL.as_posix()])
check("p20653_count_14", outer["tooth_count"] == 14)
check("p20653_pitch", abs(outer["pitch_mm"] - 20.6533333333) < 1e-10)
check("p20653_pitch_diameter", abs(outer["pitch_diameter_mm"] - 92.8152374974) < 1e-8)
check("p20653_phase", abs(outer["phase_deg"] - 12.8571428571) < 1e-8)
check("p20653_spacing", abs(outer["spacing_deg"] - 25.7142857143) < 1e-8)
check("p20653_width", outer["tooth_axial_width_mm"] == 44.0)
check("p20653_regression_all", outer["regression"]["all_14_pass"])
check("p20653_added_zero", outer["regression"]["max_added_volume_mm3"] == 0)
check("p20653_removed_zero", outer["regression"]["max_removed_volume_mm3"] == 0)
for row in outer["regression"]["rows"]:
    check(f"tooth_{row['index']}_pass", row["status"] == "PASS")
    check(f"tooth_{row['index']}_added_zero", row["added_volume_mm3"] == 0)
    check(f"tooth_{row['index']}_removed_zero", row["removed_volume_mm3"] == 0)

check("shaft_10", parameters["shaft"]["diameter_mm"] == 10.0)
check("shaft_145", parameters["shaft"]["length_mm"] == 145.0)
check("key_3_class", parameters["shaft"]["key_class_mm"] == 3.0)
check("shaft_physical_not_yet", parameters["shaft"]["physical"] == "NOT_YET")
check("target_6p5", parameters["target_torque_nm"] == 6.5)
check("future_id_c1", parameters["future_coupon_notch_ids"]["C1"] == 1)
check("future_id_c2", parameters["future_coupon_notch_ids"]["C2"] == 2)
check("future_id_c3", parameters["future_coupon_notch_ids"]["C3"] == 3)
check("zero_fit_stl_authority", parameters["fit_stl_count"] == 0)

expected_source = {
    "A1": (5.0, 25, 39.79, 38.65, 45.0, 33.0),
    "A2": (5.0, 28, 44.56, 43.42, 50.0, 33.0),
    "B": (12.7, 12, 49.07, 55.0, 55.0, 22.0),
}
for key, values in expected_source.items():
    row = metrics[key]
    check(f"{key}_pitch", row["pitch_mm"] == values[0])
    check(f"{key}_teeth", row["teeth"] == values[1])
    check(f"{key}_pd", row["pitch_diameter_mm"] == values[2])
    check(f"{key}_tooth_od", row["toothed_body_od_mm"] == values[3])
    check(f"{key}_max_envelope", row["max_outer_envelope_mm"] == values[4])
    check(f"{key}_axial", row["overall_axial_envelope_mm"] == values[5])
    check(f"{key}_bore10", row["bore_mm"] == 10.0)
    check(f"{key}_key3", row["keyway_width_mm"] == 3.0)
    check(f"{key}_core_crawler_decoupled", row["core_crawler_pitch_decoupled"])
    check(f"{key}_positive_form", row["positive_engagement"].startswith("EXTERNAL_TEETH"))
    check(f"{key}_pocket_nonintersection", row["core_vs_envelope_pocket_intersection_mm3"] == 0)
    check(f"{key}_ligament_hard", row["minimum_continuous_ligament_mm"] >= 5.0)
    check(f"{key}_axial_fit44", row["overall_axial_envelope_mm"] <= 44.0)
    check(f"{key}_axial_status", row["axial_width_status"] == "PASS_REFERENCE")
    check(f"{key}_force_equation", abs(row["tangential_force_at_6p5nm_n"] - 6500.0 / row["expected_torque_contact_radius_mm"]) < 1e-4)
    check(f"{key}_one_feature", row["load_distribution_n_per_feature"]["one_feature"] == row["tangential_force_at_6p5nm_n"])
    check(f"{key}_two_features", abs(row["load_distribution_n_per_feature"]["two_features"] * 2 - row["tangential_force_at_6p5nm_n"]) < 2e-6)
    check(f"{key}_three_features", abs(row["load_distribution_n_per_feature"]["three_features"] * 3 - row["tangential_force_at_6p5nm_n"]) < 3e-6)
    check(f"{key}_source_hold", row["fit_coupon_readiness"] == "SOURCE_GEOMETRY_HOLD")
    check(f"{key}_fit_stl_false", row["fit_stl_generated"] is False)
    check(f"{key}_set_screw_phase_hold", row["set_screw_phase"] == "HOLD")
    check(f"{key}_reference_valid", len(row["reference_core_bounds_mm"]) == 6 and row["reference_core_volume_mm3"] > 0)

check("a1_ligament", abs(metrics["A1"]["minimum_continuous_ligament_mm"] - 11.05) < 1e-9)
check("a2_ligament", abs(metrics["A2"]["minimum_continuous_ligament_mm"] - 8.55) < 1e-9)
check("b_ligament", abs(metrics["B"]["minimum_continuous_ligament_mm"] - 6.05) < 1e-9)
check("a2_force_lower_a1", metrics["A2"]["tangential_force_at_6p5nm_n"] < metrics["A1"]["tangential_force_at_6p5nm_n"])
check("b_force_lowest", metrics["B"]["tangential_force_at_6p5nm_n"] < metrics["A2"]["tangential_force_at_6p5nm_n"])
check("a1_structural_highest", metrics["A1"]["minimum_continuous_ligament_mm"] > metrics["A2"]["minimum_continuous_ligament_mm"])
check("kana_corrosion", "CORROSION_MITIGATION_REQUIRED" in metrics["B"]["status"])
check("primary_a2", validation["geometry"]["recommendation"]["primary"] == "A2_P5M28")
check("secondary_a1", validation["geometry"]["recommendation"]["secondary"] == "A1_P5M25")
check("production_false", validation["geometry"]["recommendation"]["production_selected"] is False)

for rel in m.STEPS:
    info = m.step_info(LANE / rel)
    check(f"step_reload_{rel}", info["reload"] == "PASS")
    check(f"step_valid_{rel}", info["valid"])
    check(f"step_solids_{rel}", info["solid_count"] >= 1)
check("step_count6", len(list((LANE / "artifacts").glob("*.step"))) == 6)
check("stl_count0", len(list(LANE.rglob("*.stl"))) == 0)
check("stl_gate_honest", validation["checks"]["stl_manifold"] == "NOT_APPLICABLE_ZERO_STL_SOURCE_GEOMETRY_HOLD")
check("no_inaccurate_coupon", validation["checks"]["fit_coupon_print"] == "HOLD_NOT_GENERATED")

for rel in m.SVGS:
    text = (LANE / rel).read_text(encoding="utf-8")
    check(f"svg_exists_{rel}", text.startswith("<svg") and "SOURCE GEOMETRY HOLD" in text)
for rel in m.DOCS:
    text = (LANE / rel).read_text(encoding="utf-8")
    check(f"doc_nonempty_{rel}", len(text) > 150)
check("source_url_misumi", m.MISUMI_SOURCE_URL in (LANE / "docs/SOURCE_AUTHORITY.md").read_text(encoding="utf-8"))
check("source_url_kana", m.KANA_SOURCE_URL in (LANE / "docs/SOURCE_AUTHORITY.md").read_text(encoding="utf-8"))
check("full_drive_hold", "FULL_DRIVE_PRINT_HOLD" in validation["status"])
check("torque_not_yet", "STATIC_TORQUE_NOT_YET" in validation["status"])
check("production_not_selected", "PRODUCTION_NOT_SELECTED" in validation["status"])

actual = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
check("exact_path_count", len(actual) == m.EXPECTED_PATH_COUNT)
check("exact_paths", actual == m.EXPECTED_FILES)
manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
check("manifest_exact", manifest == m.EXPECTED_FILES)
commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
check("commit_count", len(commit_paths) == m.EXPECTED_PATH_COUNT)
check("commit_prefix", all(row.startswith(m.LANE_REL.as_posix() + "/") for row in commit_paths))
for row in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest, rel = row.split("  ", 1)
    check(f"sha_{rel}", m.sha256(LANE / rel) == digest)

result = {"total": len(checks), "passed": sum(value for _, value in checks), "failed": [name for name, value in checks if not value]}
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
