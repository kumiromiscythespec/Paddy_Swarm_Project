from __future__ import annotations

import csv
import json
import os
import sys
import unittest
from pathlib import Path

import cadquery as cq
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


LANE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE_DIR))

import build_candidate_a_physical_mockup_v0931 as builder  # noqa: E402


class CandidateAPhysicalMockupV0931Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.params = json.loads(
            (LANE_DIR / "candidate_a_physical_mockup_parameters_v0931.json").read_text(
                encoding="utf-8"
            )
        )
        with (LANE_DIR / "candidate_a_mockup_part_list_v0931.csv").open(
            "r", encoding="utf-8", newline=""
        ) as stream:
            cls.parts = list(csv.DictReader(stream))
        with (LANE_DIR / "candidate_a_mockup_measurement_record_v0931.csv").open(
            "r", encoding="utf-8", newline=""
        ) as stream:
            cls.measurements = list(csv.DictReader(stream))

    def test_001_document_identity_and_scope(self) -> None:
        self.assertEqual(self.params["document_id"], builder.DOCUMENT_ID)
        self.assertEqual(self.params["version"], "0.9.3.1")
        self.assertEqual(self.params["physical_mockup_class"], "NO_LOAD_LAYOUT_ONLY")
        self.assertEqual(self.params["physical_mockup"], "NOT_YET_PERFORMED")

    def test_002_parent_lane_and_zip_are_protected(self) -> None:
        audit = builder.parent_audit()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["parent_path_count"], 151)
        self.assertEqual(audit["parent_ledger_sha256"], builder.PARENT_LEDGER_SHA256)
        self.assertEqual(audit["parent_zip_sha256"], builder.PARENT_ZIP_SHA256)

    def test_003_authority_pointer_remains_unchanged(self) -> None:
        self.assertEqual(self.params["authority_pointer"], "UNCHANGED")
        self.assertEqual(self.params["manufacturing"], "HOLD")

    def test_004_candidate_a_datums_are_exact(self) -> None:
        self.assertEqual(
            self.params["motor_front_plate_datums_mm"],
            {"LEFT": [68.0, -185.0, 105.0], "RIGHT": [-68.0, -185.0, 105.0]},
        )
        self.assertEqual(self.params["coordinate_system"], {"X": "left", "Y": "rear", "Z": "up"})

    def test_005_motor_measurements_are_exact(self) -> None:
        motor = self.params["motor_measurements_mm"]
        expected = {
            "cylinder_diameter": 36.9,
            "front_to_rear_fixed": 70.1,
            "front_to_shaft_tip": 16.9,
            "total_axial_fixed": 87.0,
            "shaft_diameter": 5.9,
            "boss": [12.0, 2.7],
            "bracket": [40.1, 45.5, 42.8],
            "bracket_thickness": 3.1,
            "fastener_hole": 3.4,
            "hole_centers": [30.0, 23.8],
            "vertical_slot_representative": 27.7,
        }
        for key, value in expected.items():
            self.assertEqual(motor[key], value, key)
        self.assertEqual(motor["vertical_slot_exact_geometry"], "MEASUREMENT_HOLD")

    def test_006_jig_b_is_recommended_and_jig_a_is_comparison_only(self) -> None:
        trade = self.params["jig_trade"]
        self.assertEqual(trade["recommended"], "JIG-B_EXTERNAL_CRADLE")
        self.assertIn("COMPARISON_ONLY", trade["JIG-A"])
        self.assertIn("NO_CLAMP_LOAD", trade["JIG-B"])

    def test_007_cad_width_contract(self) -> None:
        width = self.params["width_contract"]
        self.assertEqual(width["boundary_x_mm"], [-145.0, 145.0])
        self.assertEqual(width["motor_fixed_width_mm"], 276.2)
        self.assertEqual(width["motor_g1_guard_width_mm"], 286.2)
        self.assertEqual(width["track_proxy_width_mm"], 290.0)
        self.assertEqual(width["complete_fixed_width_mm"], 290.0)
        self.assertEqual(width["complete_guarded_width_mm"], 290.0)
        self.assertEqual(width["s2_temporary_service_width_mm"], 316.2)
        self.assertEqual(width["status"], "CONDITIONAL_PASS")

    def test_008_actual_cad_intersections_are_zero(self) -> None:
        width = builder.cad_reconfirmation()
        self.assertEqual(width["status"], "CONDITIONAL_PASS")
        self.assertTrue(all(row["pass"] for row in width["collisions"]))
        self.assertTrue(all(row["intersection_volume_mm3"] == 0.0 for row in width["collisions"]))

    def test_009_service_sweep_is_not_a_fixed_width_failure(self) -> None:
        width = self.params["width_contract"]
        self.assertGreater(width["s2_temporary_service_width_mm"], 300.0)
        self.assertLess(width["motor_g1_guard_width_mm"], 290.0)
        row = next(item for item in self.measurements if item["measurement_id"] == "motor_removal_temporary_width")
        self.assertEqual(row["acceptance_condition"], "SERVICE_ONLY_NOT_FIXED_FAIL")
        part_ids = {item["part_id"] for item in self.parts}
        self.assertIn("LEFT_S2_SERVICE_SWEEP_GAUGE", part_ids)
        self.assertIn("RIGHT_S2_SERVICE_SWEEP_GAUGE", part_ids)

    def test_010_frame_authority_is_2020_class_and_2040_is_hold(self) -> None:
        frame = self.params["frame"]
        self.assertEqual(frame["authority"], "20X20MM_T_SLOT_CLASS")
        self.assertIn("HOLD", frame["2040"])
        self.assertEqual(frame["direct_holes"], "PROHIBITED")

    def test_011_pulley_references_are_pinned_not_duplicated(self) -> None:
        self.assertEqual(set(self.params["pulley_reuse"]), {"20T_STEP", "20T_STL", "60T_STEP", "60T_STL"})
        for record in self.params["pulley_reuse"].values():
            self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
        duplicated = [path for path in builder.PACKAGE_PATHS if "PULLEY" in path and path.lower().endswith((".step", ".stl"))]
        self.assertEqual(duplicated, [])

    def test_012_ten_millimetre_shaft_is_reference_only(self) -> None:
        shaft = self.params["ten_mm_shaft_reference"]
        self.assertEqual(shaft["physical_reference"], "USER_EXISTING_10MM_SHAFT")
        self.assertIn("NO_LOAD", shaft["S2_10P30"])

    def test_013_all_fourteen_print_parts_reload_and_fit_a1(self) -> None:
        self.assertEqual(len(builder.PRINT_FILES), 14)
        report = builder.verify_stls()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["pass_count"], 14)
        printed = [row for row in self.parts if row["method"] == "3D_PRINT"]
        self.assertEqual(len(printed), 14)
        self.assertTrue(all(row["a1_256_fit"] == "PASS" for row in printed))

    def test_014_print_orientation_and_no_load_authority_are_recorded(self) -> None:
        printed = [row for row in self.parts if row["method"] == "3D_PRINT"]
        self.assertTrue(all(row["print_orientation"] == "AS_EXPORTED_FLAT_BASE_Z0" for row in printed))
        self.assertTrue(all(row["load_authority"] == "NO_LOAD_POSITIONING_ONLY" for row in printed))

    def test_015_left_right_printable_bounds_are_symmetric(self) -> None:
        for left, right in zip(builder.PRINT_FILES[0::2], builder.PRINT_FILES[1::2]):
            left_native, right_native = TopoDS_Shape(), TopoDS_Shape()
            self.assertTrue(StlAPI_Reader().Read(left_native, str(LANE_DIR / left)))
            self.assertTrue(StlAPI_Reader().Read(right_native, str(LANE_DIR / right)))
            lb = cq.Shape(left_native).BoundingBox()
            rb = cq.Shape(right_native).BoundingBox()
            self.assertAlmostEqual(lb.xlen, rb.xlen, places=3)
            self.assertAlmostEqual(lb.ylen, rb.ylen, places=3)
            self.assertAlmostEqual(lb.zlen, rb.zlen, places=3)

    def test_016_all_seven_step_assemblies_reload(self) -> None:
        self.assertEqual(len(builder.ASSEMBLY_FILES), 7)
        report = builder.verify_steps()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["pass_count"], 7)

    def test_017_all_nine_one_to_one_templates_exist(self) -> None:
        self.assertEqual(len(builder.TEMPLATE_FILES), 9)
        for rel in builder.TEMPLATE_FILES:
            text = (LANE_DIR / rel).read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertIn("NO LOAD / NO POWER / NOT FOR MANUFACTURING", text)

    def test_018_selector_states_are_0_5_10_and_mutually_exclusive(self) -> None:
        clutch = self.params["clutch"]
        self.assertEqual(clutch["positions_mm"], {"DRIVE": 0, "NEUTRAL": 5, "PTO": 10})
        self.assertEqual(clutch["simultaneous_drive_pto"], "GEOMETRICALLY_NOT_SHOWN_AND_PROHIBITED")
        self.assertEqual(clutch["torque_transmission"], "PROHIBITED")

    def test_019_left_right_pto_are_independent_and_inward(self) -> None:
        plan = (LANE_DIR / "candidate_a_physical_mockup_plan_v0931.md").read_text(encoding="utf-8")
        self.assertIn("PTO witnesses: X=±14", plan)
        self.assertIn("inward and mechanically independent", plan)
        self.assertIn("left/right common shaft is prohibited", plan)

    def test_020_unit_mass_is_not_supported_by_pto_shafts(self) -> None:
        plan = (LANE_DIR / "candidate_a_physical_mockup_plan_v0931.md").read_text(encoding="utf-8")
        self.assertIn("Unit weight is supported by a separate hitch/guide-frame region", plan)
        self.assertIn("never by PTO shafts", plan)

    def test_021_procedure_has_thirty_steps_and_ends_unpowered(self) -> None:
        text = (LANE_DIR / "physical_mockup_procedure_v0931.md").read_text(encoding="utf-8")
        numbered = [line for line in text.splitlines() if line.split(".", 1)[0].isdigit()]
        self.assertEqual(len(numbered), 30)
        self.assertIn("30. End without energizing or rotating the motors.", text)

    def test_022_measurement_record_is_blank_for_physical_results(self) -> None:
        self.assertEqual(len(self.measurements), 25)
        self.assertTrue(all(row["physical_measured_value"] == "" for row in self.measurements))
        self.assertTrue(all(row["physical_result"] == "NOT_MEASURED" for row in self.measurements))

    def test_023_no_power_no_load_contract_is_explicit(self) -> None:
        text = (LANE_DIR / "NO_POWER_NO_LOAD_ONLY.txt").read_text(encoding="utf-8")
        for token in (
            "MOTOR_POWER=PROHIBITED",
            "MOTOR_ROTATION=PROHIBITED",
            "BELT_TENSION=PROHIBITED",
            "TORQUE_TRANSMISSION=PROHIBITED",
            "SHAFT_CUTTING=PROHIBITED",
            "FRAME_DRILLING=PROHIBITED",
            "METAL_MACHINING_APPROVAL=NOT_APPROVED",
            "PURCHASE_APPROVAL=NOT_APPROVED",
            "MANUFACTURING=HOLD",
            "LOAD_TEST=NOT_PERFORMED",
            "POWERED_TEST=NOT_APPROVED",
            "FIELD_DEPLOYMENT=NOT_APPROVED",
            "AUTHORITY_POINTER=UNCHANGED",
        ):
            self.assertIn(token, text)

    def test_024_exact_package_path_contract(self) -> None:
        self.assertEqual(len(builder.PACKAGE_PATHS), 46)
        self.assertEqual(len(set(builder.PACKAGE_PATHS)), 46)
        self.assertEqual(builder.lane_files(), sorted(builder.PACKAGE_PATHS))

    def test_025_commit_paths_are_exactly_scoped(self) -> None:
        paths = (LANE_DIR / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        prefix = "cad/common_rover/common_rover_candidate_a_physical_mockup_v0_9_3_1/"
        self.assertEqual(paths, [prefix + rel for rel in builder.PACKAGE_PATHS])
        self.assertTrue(all(path.startswith(prefix) for path in paths))

    def test_026_manifest_exact_order_and_roles(self) -> None:
        report = builder.verify_manifest()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["entry_count"], 46)
        manifest = (LANE_DIR / "MANIFEST.txt").read_text(encoding="utf-8")
        self.assertIn("scope=V0931_ONLY", manifest)
        self.assertIn("physical_mockup=NOT_YET_PERFORMED", manifest)

    def test_027_sha256_ledger_is_complete(self) -> None:
        report = builder.verify_hashes()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["verified"], 45)

    def test_028_repository_lifecycle_guard(self) -> None:
        audit = builder.repository_audit()
        self.assertEqual(audit["status"], "PASS")
        if audit["mode"] == "LIVE_REPOSITORY":
            self.assertEqual(audit["branch"], builder.EXPECTED_BRANCH)
            self.assertEqual(audit["head"], builder.EXPECTED_HEAD)
            self.assertEqual(audit["lane_untracked_count"], 46)

    def test_029_evidence_contract(self) -> None:
        self.assertEqual(builder.verify_evidence()["status"], "PASS")

    def test_030_zip_scope_hashes_and_bytes(self) -> None:
        value = os.environ.get("V0931_TEST_ZIP", "")
        path = Path(value) if value else builder.latest_handoff_zip()
        if path is None:
            self.skipTest("ZIP is tested during --package")
        report = builder.verify_zip(path, standalone=False)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["entry_count"], 46)
        self.assertEqual(report["internal_hash_verification"], "PASS")
        self.assertEqual(report["lane_byte_match"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
