from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import sys
import unittest
import zipfile
from pathlib import Path, PurePosixPath


LANE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v0933_builder", LANE / "build_motor_bracket_8hole_flat_plate_v0933.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import v0.9.3.3 builder")
B = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = B
SPEC.loader.exec_module(B)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class V0933Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.params = json.loads((LANE / "motor_bracket_8hole_flat_plate_parameters_v0933.json").read_text(encoding="utf-8"))
        cls.measurements = json.loads((LANE / "motor_bracket_8hole_measurements_v0933.json").read_text(encoding="utf-8"))
        cls.geometry = cls.params["geometry_report"]

    def test_001_document_identity(self) -> None:
        self.assertEqual(B.DOCUMENT_ID, "PS-CR-V0933-MOTOR-BRACKET-8HOLE-FLAT-PLATE")
        self.assertEqual(B.VERSION, "0.9.3.3")

    def test_002_anchor_exists_and_is_ancestor(self) -> None:
        if not B.live_repository():
            self.skipTest("standalone embedded anchor evidence")
        B.git("cat-file", "-e", f"{B.ANCHOR}^{{commit}}")
        self.assertEqual(B.run(["git", "merge-base", "--is-ancestor", B.ANCHOR, "HEAD"]).returncode, 0)

    def test_003_repository_guard(self) -> None:
        self.assertEqual(B.repository_audit(require_complete=True)["status"], "PASS")

    def test_004_parent_lanes_protected(self) -> None:
        report = B.parent_audit()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(set(report["parents"]), {"v0.9.3.1", "v0.9.3.2"})

    def test_005_authority_pointer_unchanged(self) -> None:
        self.assertEqual(self.params["approval"]["authority_pointer"], "UNCHANGED")
        if B.live_repository():
            self.assertEqual({rel: B.sha256(B.REPO_ROOT / rel) for rel in B.AUTHORITY_POINTER_HASHES}, B.AUTHORITY_POINTER_HASHES)

    def test_006_flat_plate_size_and_radius(self) -> None:
        self.assertEqual(self.params["plate"]["size_mm"], [42.0, 80.0])
        self.assertEqual(self.params["plate"]["corner_radius_mm"], 3.0)
        self.assertEqual(self.geometry["plate_bounds_mm"]["xlen"], 42.0)
        self.assertEqual(self.geometry["plate_bounds_mm"]["ylen"], 80.0)

    def test_007_petg_and_metal_thicknesses(self) -> None:
        self.assertEqual(self.params["plate"]["petg_thickness_mm"], 6.0)
        self.assertEqual(self.params["plate"]["metal_reference_thickness_mm"], 3.0)
        self.assertEqual(self.geometry["plate_bounds_mm"]["zlen"], 6.0)
        self.assertEqual(self.geometry["metal_bounds_mm"]["zlen"], 3.0)

    def test_008_m3_contract(self) -> None:
        m3 = self.params["holes"]["M3"]
        self.assertEqual(m3["diameter_mm"], 3.4)
        self.assertEqual(m3["count"], 4)
        self.assertEqual(m3["coordinates_mm"], [[-12.0, -15.0], [12.0, -15.0], [-12.0, 15.0], [12.0, 15.0]])
        self.assertEqual(m3["pitch_mm"], [24.0, 30.0])

    def test_009_m5_contract(self) -> None:
        m5 = self.params["holes"]["M5"]
        self.assertEqual(m5["diameter_mm"], 5.7)
        self.assertEqual(m5["count"], 4)
        self.assertEqual(m5["coordinates_mm"], [[-10.0, -30.0], [10.0, -30.0], [-10.0, 30.0], [10.0, 30.0]])
        self.assertEqual(m5["pitch_mm"], [20.0, 60.0])

    def test_010_exactly_eight_holes_and_no_m4(self) -> None:
        self.assertEqual(self.params["holes"]["total"], 8)
        self.assertEqual(self.params["physical_fit"]["M4_holes_in_plate"], 0)
        self.assertEqual(len(B.hole_rows()), 8)

    def test_011_physical_fit_records(self) -> None:
        self.assertEqual(self.params["physical_fit"]["M3_3P4"], "PASS / JUST_FIT")
        self.assertEqual(self.params["physical_fit"]["M4_4P2"], "PASS / JUST_FIT_REFERENCE_ONLY")

    def test_012_all_features_are_straight_through(self) -> None:
        self.assertEqual(self.params["holes"]["all"], "STRAIGHT_THROUGH_CLEARANCE")
        self.assertTrue(all(row["feature"] == "STRAIGHT_THROUGH_CLEARANCE" for row in B.hole_rows()))

    def test_013_no_unsupported_features(self) -> None:
        self.assertFalse(any(self.params["features_not_used"].values()))
        source = (LANE / "build_motor_bracket_8hole_flat_plate_v0933.py").read_text(encoding="utf-8")
        self.assertNotIn(".cskHole(", source)
        self.assertNotIn(".cboreHole(", source)
        self.assertNotIn(".threadedHole(", source)

    def test_014_single_solid(self) -> None:
        self.assertEqual(self.geometry["solid_count"], 1)
        self.assertEqual(len(B.flat_plate(B.PETG_Z).Solids()), 1)

    def test_015_planar_top_bottom_and_flat_z0(self) -> None:
        self.assertTrue(self.geometry["top_bottom_planar"])
        self.assertIn(0.0, self.geometry["planar_face_z_mm"])
        self.assertIn(6.0, self.geometry["planar_face_z_mm"])
        self.assertEqual(B.bounds(B.flat_plate(B.PETG_Z))["zmin"], 0.0)

    def test_016_all_eight_holes_fully_through(self) -> None:
        self.assertLess(self.geometry["plate_to_hole_void_residual_max_volume_mm3"], 1e-8)

    def test_017_blank_minus_only_eight_holes_volume(self) -> None:
        self.assertLess(self.geometry["volume_delta_mm3"], 1e-5)
        self.assertAlmostEqual(self.geometry["actual_volume_mm3"], self.geometry["expected_volume_mm3"], places=5)

    def test_018_pairwise_hole_intersections_zero(self) -> None:
        self.assertLess(self.geometry["pairwise_hole_intersection_max_volume_mm3"], 1e-9)

    def test_019_edge_ligaments(self) -> None:
        self.assertEqual(self.geometry["ligaments"], {"m3_x_mm": 7.3, "m3_y_mm": 23.3, "m5_x_mm": 8.15, "m5_y_mm": 7.15})
        self.assertGreaterEqual(self.geometry["minimum_edge_ligament_mm"], 5.0)

    def test_020_pair_distances(self) -> None:
        self.assertAlmostEqual(self.geometry["pairwise_minimum_center_distance_mm"], math.hypot(2.0, 15.0), places=6)
        self.assertAlmostEqual(self.geometry["pairwise_minimum_edge_gap_mm"], math.hypot(2.0, 15.0) - 4.55, places=6)

    def test_021_petg_metal_xy_identical_thickness_only(self) -> None:
        self.assertTrue(self.geometry["petg_metal_xy_identical"])
        self.assertEqual(self.geometry["plate_bounds_mm"]["xlen"], self.geometry["metal_bounds_mm"]["xlen"])
        self.assertEqual(self.geometry["plate_bounds_mm"]["ylen"], self.geometry["metal_bounds_mm"]["ylen"])

    def test_022_left_right_identical_single_stl(self) -> None:
        self.assertEqual(self.params["left_part"], "IDENTICAL")
        self.assertEqual(self.params["right_part"], "IDENTICAL")
        self.assertEqual(self.params["quantity_required"], 2)
        self.assertEqual(len(B.PRINT_FILES), 1)
        self.assertNotIn("LEFT", B.PRINT_FILES[0])
        self.assertNotIn("RIGHT", B.PRINT_FILES[0])

    def test_023_frame_proxy_contract(self) -> None:
        self.assertEqual(self.params["proxies"]["frame_mm"], [40.0, 120.0, 20.0])
        self.assertEqual(self.params["proxies"]["frame_slot_center_x_mm"], [-10.0, 10.0])
        self.assertEqual(self.params["proxies"]["t_slot_exact_profile"], "MEASUREMENT_HOLD")

    def test_024_bracket_proxy_contract(self) -> None:
        self.assertEqual(self.params["proxies"]["bracket_mm"], [40.2, 40.0, 3.1])
        shape = B.bracket_proxy()
        self.assertEqual(len(shape.Solids()), 1)

    def test_025_spacer_sweep_is_hold(self) -> None:
        self.assertEqual(self.params["spacer"]["comparison_heights_mm"], [6.0, 8.0, 10.0])
        self.assertEqual(self.params["spacer"]["status"], "PHYSICAL_MEASUREMENT_HOLD")
        self.assertEqual(self.params["spacer"]["M3_nut_exact_envelope"], "MEASUREMENT_HOLD")
        self.assertEqual(self.params["spacer"]["M5_nut_exact_envelope"], "MEASUREMENT_HOLD")

    def test_026_height_impact(self) -> None:
        height = self.params["height"]
        self.assertEqual([height["spacer_H6_total_z_increase_mm"], height["spacer_H8_total_z_increase_mm"], height["spacer_H10_total_z_increase_mm"]], [12.0, 14.0, 16.0])
        self.assertEqual(height["candidate_motor_and_20T_z_mm"], [117.0, 119.0, 121.0])
        self.assertEqual(height["status"], "REVALIDATION_REQUIRED")

    def test_027_print_contract(self) -> None:
        p = self.params["print"]
        self.assertEqual((p["material"], p["nozzle_mm"], p["layer_height_mm"]), ("PETG", 0.4, 0.2))
        self.assertGreaterEqual(p["wall_loops_min"], 5)
        self.assertGreaterEqual(p["top_bottom_layers_min"], 6)
        self.assertEqual(p["support"], "NONE")
        self.assertTrue(p["bambu_a1_fit"])

    def test_028_stl_reload_flat_and_a1_fit(self) -> None:
        report = B.verify_stls()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (1, 1))
        self.assertTrue(report["rows"][0]["flat_base"])
        self.assertTrue(report["rows"][0]["a1_fit"])

    def test_029_exact_eight_step_files_reload(self) -> None:
        self.assertEqual(len(B.ASSEMBLY_FILES), 8)
        report = B.verify_steps()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (8, 8))

    def test_030_two_identical_plates_step(self) -> None:
        shape = B.cq.importers.importStep(str(LANE / B.ASSEMBLY_FILES[-1])).val()
        solids = shape.Solids()
        self.assertEqual(len(solids), 2)
        self.assertAlmostEqual(solids[0].Volume(), solids[1].Volume(), places=5)

    def test_031_svg_contract(self) -> None:
        report = B.verify_templates()
        self.assertEqual(len(report["svg"]), 7)
        self.assertTrue(all(row["pass"] for row in report["svg"]))

    def test_032_dxf_contract(self) -> None:
        report = B.verify_templates()
        self.assertTrue(all(report["dxf"].values()))
        dxf = (LANE / B.TEMPLATE_FILES[6]).read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"(?m)^CIRCLE$", dxf)), 8)

    def test_033_physical_procedure_exact_twenty_no_power(self) -> None:
        text = (LANE / "physical_fit_procedure_v0933.md").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"(?m)^\d+\. ", text)), 20)
        self.assertIn("Finish without applying power", text)
        self.assertIn("FASTENER_TORQUE = MEASUREMENT_HOLD", text)

    def test_034_no_power_or_load_approval(self) -> None:
        approval = self.params["approval"]
        self.assertEqual(approval["belt_tension"], "NOT_APPROVED")
        self.assertEqual(approval["powered_rotation"], "NOT_APPROVED")
        self.assertEqual(approval["torque_load"], "NOT_APPROVED")
        self.assertEqual(approval["field_deployment"], "NOT_APPROVED")

    def test_035_v0932_supersession_record(self) -> None:
        self.assertEqual(self.params["supersession"], "V0932_M4_DIRECT_THREAD_VARIANTS=SUPERSEDED_BY_V0933_M3_M5_THROUGH_HOLE_FLAT_PLATE")
        self.assertIn("v0.9.3.2 lane is preserved byte-for-byte", (LANE / "v0932_supersession_notice_v0933.md").read_text(encoding="utf-8"))

    def test_036_exact_38_paths(self) -> None:
        self.assertEqual(len(B.PACKAGE_PATHS), 38)
        self.assertEqual(B.lane_files(), sorted(B.PACKAGE_PATHS))

    def test_037_commit_paths_v0933_only(self) -> None:
        values = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        prefix = "cad/common_rover/common_rover_candidate_a_motor_bracket_8hole_flat_plate_v0_9_3_3/"
        self.assertEqual(len(values), 38)
        self.assertTrue(all(value.startswith(prefix) for value in values))
        self.assertEqual([value[len(prefix):] for value in values], list(B.PACKAGE_PATHS))

    def test_038_manifest_exact(self) -> None:
        report = B.verify_manifest()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["entry_count"], 38)

    def test_039_sha256_ledger(self) -> None:
        report = B.verify_hashes()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["verified"], 37)

    def test_040_machine_evidence(self) -> None:
        self.assertEqual(B.verify_evidence()["status"], "PASS")
        self.assertEqual(len(self.measurements["rows"]), 10)

    def test_041_builder_verify(self) -> None:
        report = B.verify()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["exact_package_paths"], 38)

    def test_042_zip_standalone_contract_when_requested(self) -> None:
        value = os.environ.get("V0933_TEST_ZIP")
        if not value:
            self.skipTest("V0933_TEST_ZIP not set")
        path = Path(value)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            self.assertEqual(names, list(B.PACKAGE_PATHS))
            self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name for name in names))
            hashes = {}
            for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
                if line.strip():
                    expected, rel = line.split("  ", 1)
                    hashes[rel] = expected
            self.assertEqual(set(hashes), set(B.PACKAGE_PATHS) - {"SHA256SUMS.txt"})
            self.assertTrue(all(hashlib.sha256(archive.read(rel)).hexdigest() == expected for rel, expected in hashes.items()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
