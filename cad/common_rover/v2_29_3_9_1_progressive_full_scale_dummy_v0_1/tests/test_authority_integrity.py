from __future__ import annotations

import unittest

from authority_adapter import (
    controlled_dimensions,
    load_context,
    profile_input_audit,
    source_integrity_report,
)


class AuthorityIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_context(validate_seed_geometry=True)
        cls.dimensions = controlled_dimensions(cls.context)

    def test_authority_and_seed_pass_with_holds(self):
        report = source_integrity_report(self.context)
        self.assertTrue(report["authority_tree_match"])
        self.assertEqual(report["seed_status"], "PASS_WITH_HOLD")
        self.assertTrue(report["assembly_interface_import_reused"])

    def test_controlled_dimensions_are_imported_exactly(self):
        self.assertEqual(
            self.dimensions["body_mm"]["CBOX"],
            {"X": 130.0, "Y": 140.0, "Z": 105.0},
        )
        self.assertEqual(
            self.dimensions["body_mm"]["BBOX"],
            {"X": 150.0, "Y": 220.0, "Z": 150.0},
        )
        self.assertEqual(
            self.dimensions["body_mm"]["BATTERY_CASSETTE"],
            {"X": 125.0, "Y": 180.0, "Z": 120.0},
        )
        self.assertEqual(self.dimensions["core_length_mm"], 360.0)
        self.assertEqual(
            self.dimensions["rail_centerlines_x_mm"],
            {"LEFT": 79.0, "RIGHT": -79.0},
        )
        self.assertEqual(self.dimensions["rail_length_mm"], 232.0)
        self.assertEqual(self.dimensions["bare_frame_width_mm"], 178.0)
        self.assertEqual(
            self.dimensions["front_crossmember_envelope_mm"],
            {"X": 138.0, "Y": 20.0, "Z": 20.0},
        )

    def test_reserved_authority_regions_are_preserved(self):
        self.assertEqual(
            self.dimensions["lower_adapter_left"]["zone_interval"],
            [-125, -95],
        )
        self.assertEqual(
            self.dimensions["lower_adapter_left"]["normalized_slot_face"],
            "BOTTOM_SLOT",
        )
        self.assertEqual(
            self.dimensions["upper_torque_mount"]["zone_id"],
            "UPPER-TORQUE-MOUNT",
        )
        self.assertEqual(
            self.dimensions["output_bridge_left"]["zone_interval"],
            [-222, -212],
        )
        self.assertEqual(
            self.dimensions["front_joint_reserved_interval_y_mm"],
            [-232, -224],
        )
        self.assertEqual(
            self.dimensions["direct_rail_hole_policy"],
            "NO_UNVALIDATED_DIRECT_HOLES",
        )

    def test_profile_audit_selects_only_envelope_dummy(self):
        report = profile_input_audit(self.context)
        self.assertEqual(report["selected_option"], "PROFILE-3")
        self.assertEqual(report["status"], "DUMMY_ENVELOPE_ONLY")
        self.assertEqual(len(report["missing_supplier_fields"]), 6)
        self.assertIn("NO_INFERRED_SLOT_GEOMETRY", report["prohibitions"])


if __name__ == "__main__":
    unittest.main()
