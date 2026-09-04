#!/usr/bin/env python3
"""Contract tests for Common Rover v0.9.2.2 shaft-fit calibration coupons."""

from __future__ import annotations

import csv
import json
import sys
import unittest
import zipfile
from pathlib import Path

import cadquery as cq


LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))

import build_shaft_fit_calibration_v0922 as build  # noqa: E402


def read_json(name: str):
    return json.loads((LANE / name).read_text(encoding="utf-8"))


def read_csv(name: str):
    with (LANE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class ShaftFitCalibrationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parameters = read_json("common_rover_shaft_fit_calibration_parameters_v0922.json")
        cls.measurements = read_json("common_rover_physical_measurements_input_v0922.json")
        cls.validation = read_json("common_rover_fit_candidate_validation_v0922.json")

    def test_001_exact_45_paths(self) -> None:
        actual = {p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file()}
        self.assertEqual(actual, set(build.PACKAGE_PATHS))
        self.assertEqual(len(actual), 45)

    def test_002_parent_paths_unchanged(self) -> None:
        self.assertEqual(build.audit_parent(live=build.repo_root() is not None)["status"], "PASS" if build.repo_root() else "EMBEDDED_PROTECTED_EVIDENCE")

    def test_003_parent_zip_sha(self) -> None:
        evidence = self.validation["parent_protection"]
        self.assertEqual(evidence["expected_zip_sha256"], build.PARENT_ZIP_SHA256)
        if build.repo_root():
            self.assertEqual(evidence["actual_zip_sha256"], build.PARENT_ZIP_SHA256)

    def test_004_authority_pointer_unchanged(self) -> None:
        self.assertEqual(self.parameters["statuses"]["AUTHORITY_POINTER"], "UNCHANGED_V0_9_2_1")
        self.assertEqual(self.validation["authority_pointer"], "UNCHANGED_V0_9_2_1")

    def test_005_reference_source_audit_exists(self) -> None:
        path = LANE / "common_rover_reference_60t_bore_audit_v0922.md"
        self.assertTrue(path.is_file())
        self.assertIn("PS-HTD5M-PULLEY-60T-STD-DUMMY-V001", path.read_text(encoding="utf-8"))

    def test_006_reference_resolved(self) -> None:
        self.assertTrue(self.validation["D_REF_CAD_resolved"])
        self.assertEqual(self.parameters["D_REF_CAD_STATUS"], "RESOLVED_FROM_AUDITED_60T_SOURCE")

    def test_007_d_ref_cad_exact(self) -> None:
        self.assertAlmostEqual(self.parameters["D_REF_CAD"], 10.10)
        self.assertAlmostEqual(build.audit_reference_source(live=build.repo_root() is not None)["D_REF_CAD_mm"], 10.10)

    def test_008_d_ref_actual_independent(self) -> None:
        self.assertAlmostEqual(self.parameters["D_REF_ACTUAL"], 10.1)
        self.assertEqual(self.measurements["reference_60T"]["actual_bore_measurements_mm"], [10.1] * 4)

    def test_009_physical_results_recorded(self) -> None:
        self.assertEqual(self.measurements["center_gap_gauges_mm"][0], {"actual": 34.6, "nominal": 35.0})
        self.assertEqual(self.measurements["stub_gauges_mm"][0], {"actual": 12.4, "nominal": 12.5})

    def test_010_global_scale_prohibited(self) -> None:
        self.assertEqual(self.measurements["GLOBAL_SCALE_CORRECTION"], "PROHIBITED")
        self.assertEqual(self.parameters["GLOBAL_SCALE_CORRECTION"], "PROHIBITED")

    def test_011_u_block_failure_recorded(self) -> None:
        block = self.measurements["current_U_block"]
        self.assertEqual(block["radial_positioning"], "FAIL")
        self.assertAlmostEqual(block["diametral_play_after_entry_mm"], 1.4)
        self.assertEqual(block["rough_support"], "USABLE_NO_LOAD_ONLY")

    def test_012_positioning_candidate_count(self) -> None:
        self.assertEqual(len(build.POSITIONING), 6)
        self.assertEqual(self.validation["positioning_candidate_count"], 6)

    def test_013_sliding_candidate_count(self) -> None:
        self.assertEqual(len(build.SLIDING), 7)
        self.assertEqual(self.validation["sliding_candidate_count"], 7)

    def test_014_positioning_offsets(self) -> None:
        self.assertEqual([r["offset_mm"] for r in build.POSITIONING], [-0.2, -0.1, 0.0, 0.1, 0.2, 0.3])
        self.assertEqual([r["bore_mm"] for r in build.POSITIONING], [9.9, 10.0, 10.1, 10.2, 10.3, 10.4])

    def test_015_sliding_offsets(self) -> None:
        self.assertEqual([r["offset_mm"] for r in build.SLIDING], [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        self.assertEqual([r["bore_mm"] for r in build.SLIDING], [10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7])

    def test_016_positioning_csv(self) -> None:
        rows = read_csv("common_rover_positioning_fit_candidates_v0922.csv")
        self.assertEqual([r["candidate_id"] for r in rows], [f"P{i}" for i in range(6)])
        self.assertTrue(all(r["physical_status"] == "PHYSICAL_TEST_NOT_PERFORMED" for r in rows))

    def test_017_sliding_csv(self) -> None:
        rows = read_csv("common_rover_sliding_fit_candidates_v0922.csv")
        self.assertEqual([r["candidate_id"] for r in rows], [f"S{i}" for i in range(7)])

    def test_018_split_clamp_top_bottom(self) -> None:
        for row in build.POSITIONING:
            self.assertTrue(build.split_half(row["id"], row["bore_mm"], "TOP").isValid())
            self.assertTrue(build.split_half(row["id"], row["bore_mm"], "BOTTOM").isValid())

    def test_019_split_plane_through_axis(self) -> None:
        self.assertTrue(self.validation["split_plane_passes_shaft_center"])
        for row in self.validation["actual_cad_interference"]["actual_shape_checks"]:
            self.assertEqual(row["split_plane_z_mm"], row["shaft_axis_z_mm"])

    def test_020_split_faces_print_flat(self) -> None:
        self.assertTrue(self.validation["split_faces_print_flat"])
        for row in build.POSITIONING:
            for half in ("BOTTOM", "TOP"):
                self.assertAlmostEqual(build.split_half(row["id"], row["bore_mm"], half).BoundingBox().zmin, 0.0)

    def test_021_hard_stops(self) -> None:
        self.assertTrue(self.validation["hard_stop_surfaces_exist"])
        self.assertTrue(all(row["hard_stop"] == "CONTACT_ZERO_VOLUME" for row in self.validation["actual_cad_interference"]["actual_shape_checks"]))

    def test_022_no_horizontal_bore_roof(self) -> None:
        self.assertFalse(self.validation["horizontal_bore_roof_overhang"])
        self.assertEqual(self.parameters["split_clamp"]["print_orientation"], "SPLIT_FACE_ON_BED")

    def test_023_two_fasteners(self) -> None:
        clamp = self.parameters["split_clamp"]
        self.assertEqual(clamp["fastener_count"], 2)
        self.assertAlmostEqual(clamp["fastener_clearance_mm"], 3.4)
        self.assertEqual(clamp["interface"], "NO_LOAD_TEST_CANDIDATE")

    def test_024_fastener_shaft_zero(self) -> None:
        self.assertTrue(self.validation["actual_cad_interference"]["all_fastener_shaft_zero"])

    def test_025_tool_shaft_zero(self) -> None:
        self.assertTrue(self.validation["actual_cad_interference"]["all_tool_shaft_zero"])

    def test_026_sleeve_bore_axis_vertical(self) -> None:
        self.assertTrue(self.validation["sleeve_bore_axis_vertical"])
        self.assertEqual(self.parameters["sliding_sleeve"]["bore_axis_print"], "Z")

    def test_027_sleeve_dimensions(self) -> None:
        self.assertEqual(self.parameters["sliding_sleeve"]["OD_mm"], 20.0)
        self.assertEqual(self.parameters["sliding_sleeve"]["length_mm"], 20.0)
        self.assertEqual(self.parameters["sliding_sleeve"]["entry_exit_chamfer_mm"], 0.4)
        checks = self.validation["actual_cad_interference"]["sliding_actual_shape_checks"]
        self.assertEqual(len(checks), 7)
        self.assertEqual([row["nominal_diametral_clearance_mm"] for row in checks], [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
        self.assertTrue(self.validation["actual_cad_interference"]["all_sleeve_shaft_zero"])
        self.assertTrue(all(row["functional_center_bore_unchanged"] for row in checks))
        self.assertTrue(all(row["identification_holes_outside_functional_bore"] for row in checks))

    def test_028_all_ids_unique(self) -> None:
        ids = [r["id"] for r in build.POSITIONING + build.SLIDING]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(self.validation["all_ids_unique"])

    def test_029_no_thin_long_embossed_text(self) -> None:
        identification = self.parameters["identification"]
        self.assertFalse(identification["embossed_text"])
        self.assertFalse(identification["floating_text"])
        self.assertEqual(identification["method"], "GEOMETRIC_HOLES")

    def test_030_plate_a_exists_and_count(self) -> None:
        self.assertTrue((LANE / build.PLATE_FILES[0]).is_file())
        self.assertEqual(len(build.positioned_plate()), 12)
        self.assertGreaterEqual(self.validation["plate_A_minimum_xy_bbox_gap_mm"], 10.0)

    def test_031_plate_b_exists_and_count(self) -> None:
        self.assertTrue((LANE / build.PLATE_FILES[1]).is_file())
        self.assertEqual(len(build.sliding_plate()), 7)
        self.assertGreaterEqual(self.validation["plate_B_minimum_xy_bbox_gap_mm"], 10.0)

    def test_032_plate_c_contract(self) -> None:
        self.assertTrue((LANE / build.PLATE_FILES[2]).is_file())
        self.assertEqual(self.validation["plate_C_candidate_ids"], ["P1", "P2", "P3", "S1", "S2", "S3", "S4"])
        self.assertEqual(len(build.minimum_plate()), 10)
        self.assertGreaterEqual(self.validation["plate_C_minimum_xy_bbox_gap_mm"], 10.0)

    def test_033_plate_c_is_first(self) -> None:
        self.assertEqual(self.parameters["plates"]["first_print"], "PLATE-C")

    def test_034_all_stl_reload(self) -> None:
        results = self.validation["exchange_artifact_checks"]["stl"]
        self.assertEqual(len(results), 22)
        self.assertTrue(all(row["watertight"] and row["winding_consistent"] for row in results))
        self.assertTrue(all(row["component_count"] == row["expected_component_count"] for row in results))

    def test_035_all_step_reload(self) -> None:
        results = self.validation["exchange_artifact_checks"]["step"]
        self.assertEqual(len(results), 3)
        self.assertTrue(all(row["status"] == "PASS" for row in results))
        for rel in build.STEP_FILES:
            self.assertGreater(len(cq.importers.importStep(str(LANE / rel)).solids().vals()), 0)

    def test_036_all_parts_fit_a1(self) -> None:
        self.assertTrue(all(row["fits_A1"] for row in self.validation["exchange_artifact_checks"]["stl"]))

    def test_037_print_bed_min_z_zero(self) -> None:
        self.assertTrue(all(abs(row["minimum_z_mm"]) <= 1e-5 for row in self.validation["exchange_artifact_checks"]["stl"]))

    def test_038_no_accidental_common_shaft(self) -> None:
        self.assertTrue(self.validation["no_accidental_common_shaft"])
        self.assertTrue(self.validation["no_common_PTO_geometry"])

    def test_039_bores_not_validated_from_bbox(self) -> None:
        self.assertIn("NOT_BOUNDING_BOX", self.validation["bore_validation_method"])

    def test_040_no_load_warnings(self) -> None:
        warning = (LANE / "NO_LOAD_ONLY.txt").read_text(encoding="utf-8")
        for phrase in ("NO_LOAD_ONLY", "NOT_FOR_TORQUE", "NOT_A_PRODUCTION_FASTENER_INTERFACE", "MANUFACTURING=HOLD"):
            self.assertIn(phrase, warning)

    def test_041_physical_test_not_performed(self) -> None:
        self.assertEqual(self.validation["physical_test_status"], "PHYSICAL_TEST_NOT_PERFORMED")
        rows = read_csv("fit_calibration_record_v0922.csv")
        self.assertEqual(len(rows), 13)
        self.assertTrue(all(r["physical_status"] == "PHYSICAL_TEST_NOT_PERFORMED" for r in rows))

    def test_042_fail_closed_statuses(self) -> None:
        statuses = self.parameters["statuses"]
        self.assertEqual(statuses["POSITIONING_FIT_SELECTION"], "PHYSICAL_TEST_REQUIRED")
        self.assertEqual(statuses["SLIDING_FIT_SELECTION"], "PHYSICAL_TEST_REQUIRED")
        self.assertEqual(statuses["PHYSICAL_FIT"], "HOLD")
        self.assertEqual(statuses["LOAD_CAPACITY"], "HOLD")

    def test_043_powered_and_field_not_approved(self) -> None:
        statuses = self.parameters["statuses"]
        self.assertEqual(statuses["POWERED_TEST"], "NOT_APPROVED")
        self.assertEqual(statuses["FIELD_DEPLOYMENT"], "NOT_APPROVED")

    def test_044_machining_and_manufacturing_hold(self) -> None:
        statuses = self.parameters["statuses"]
        self.assertEqual(statuses["MACHINING"], "HOLD")
        self.assertEqual(statuses["MANUFACTURING"], "HOLD")

    def test_045_manifest_complete(self) -> None:
        self.assertEqual((LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()[1:], build.PACKAGE_PATHS)

    def test_046_hashes_verify(self) -> None:
        self.assertEqual(build.verify_hashes()["status"], "PASS")

    def test_047_builder_verify(self) -> None:
        self.assertEqual(build.verify()["status"], "PASS")

    def test_048_zip_exists_in_downloads(self) -> None:
        matches = sorted(build.DOWNLOAD_DIR.glob(build.ZIP_PREFIX + "*.zip"))
        self.assertTrue(matches)

    def test_049_latest_zip_exact_scope(self) -> None:
        matches = sorted(build.DOWNLOAD_DIR.glob(build.ZIP_PREFIX + "*.zip"))
        self.assertTrue(matches)
        with zipfile.ZipFile(matches[-1]) as archive:
            self.assertEqual(archive.namelist(), build.PACKAGE_PATHS)

    def test_050_no_cache_or_forbidden_formats(self) -> None:
        self.assertFalse(any("__pycache__" in p.parts or p.suffix == ".pyc" for p in LANE.rglob("*")))
        allowed = {".md", ".json", ".csv", ".txt", ".py", ".stl", ".step", ".svg"}
        self.assertTrue(all(p.suffix.lower() in allowed for p in LANE.rglob("*") if p.is_file()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
