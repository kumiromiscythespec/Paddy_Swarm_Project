from __future__ import annotations

import unittest

from authority_adapter import load_context
from interface_model import (
    REQUIRED_COUPONS,
    REQUIRED_DIAGRAMS,
    REQUIRED_INTERFACE_IDS,
)
from validate_interfaces import (
    build_complete_manifest,
    validate_contract_data,
)


class InterfacePositiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_context(validate_seed_geometry=False)
        cls.manifest = build_complete_manifest(cls.context)

    def test_contract_has_no_logical_blockers(self):
        self.assertEqual([], validate_contract_data(self.manifest))

    def test_exact_interface_ids_and_required_fields(self):
        self.assertEqual(
            list(REQUIRED_INTERFACE_IDS),
            [
                row["interface_id"]
                for row in self.manifest["interfaces"]
            ],
        )
        required = {
            "connected_components",
            "primary_secondary",
            "function_classification",
            "assembly_direction",
            "removal_direction",
            "fastener_candidate",
            "visible_confirmation_point",
            "positive_stop",
            "anti_rotation_feature",
            "dirt_water_escape",
            "failure_mode",
            "human_intervention_method",
            "authority_source",
            "unresolved_values",
        }
        for row in self.manifest["interfaces"]:
            self.assertTrue(required.issubset(row))
            self.assertTrue(row["authority_source"])

    def test_three_architectures_and_fourteen_dimensions(self):
        comparison = self.manifest["architecture_comparison"]
        self.assertEqual(3, len(comparison))
        for row in comparison:
            self.assertEqual(14, len(row["ratings"]))
        self.assertEqual(
            "OPTION B",
            self.manifest["recommended_architecture"]["option_id"],
        )
        self.assertEqual(
            "HOLD",
            self.manifest["recommended_architecture"][
                "manufacturing_status"
            ],
        )

    def test_width_classes_are_distinct(self):
        widths = self.manifest["width_classification"]
        self.assertEqual(178.0, widths["bare_frame_width_mm"])
        self.assertEqual(286.0, widths["registered_width_mm"])
        self.assertEqual(300.0, widths["hard_limit_mm"])

    def test_slot_zone_audit_preserves_authority(self):
        audit = self.manifest["slot_zone_audit"]
        self.assertEqual("BOTTOM_SLOT", audit["lower_adapter_slot_face"])
        self.assertEqual(0, audit["lower_adapter_conflict_count"])
        self.assertEqual(0, audit["front_corner_conflict_count"])
        self.assertEqual(0, audit["new_anchor_count"])
        self.assertFalse(audit["direct_rail_holes_added"])
        self.assertEqual([-222, -212], audit["output_bridge_zone_y_mm"])

    def test_required_diagrams_and_coupons(self):
        self.assertEqual(
            list(REQUIRED_DIAGRAMS), self.manifest["required_diagrams"]
        )
        self.assertEqual(
            list(REQUIRED_COUPONS), self.manifest["required_coupons"]
        )
        self.assertEqual(5, len(self.manifest["required_coupons"]))

    def test_all_printed_parts_have_unique_physical_part_numbers(self):
        records = self.manifest["printed_parts"]
        self.assertEqual(5, len(records))
        self.assertEqual(
            5, len({record["part_number"] for record in records})
        )
        for record in records:
            self.assertEqual(record["coupon_id"], record["part_number"])
            self.assertEqual(
                record["part_number"], record["geometry_part_number"]
            )
            self.assertEqual("ENGRAVED", record["physical_marking"])
            self.assertTrue(record["marking_verified"])
            self.assertTrue(record["common_marking_handler_invoked"])
            self.assertEqual(
                "NON_FUNCTIONAL_PRINTABLE_EXTERIOR",
                record["marking_surface_class"],
            )
            self.assertFalse(record["support_removal_exposure"])
            self.assertEqual(
                0, record["floating_part_number_solid_count"]
            )

    def test_printed_part_identification_policy_is_fail_closed(self):
        self.assertEqual(
            {
                "required": True,
                "filename_only_identification_allowed": False,
                "physical_marking_required": True,
                "missing_part_number_result": "FAIL",
                "duplicate_part_number_result": "FAIL",
                "part_number_geometry_mismatch_result": "FAIL",
            },
            self.manifest["printed_part_identification_policy"],
        )

    def test_thumb_latch_is_secondary_only(self):
        self.assertEqual(
            "SECONDARY_ONLY",
            self.manifest["thumb_latch_policy"]["classification"],
        )
        ai08 = self.manifest["interfaces"][7]
        self.assertEqual("AI-08", ai08["interface_id"])
        self.assertEqual("SECONDARY", ai08["primary_secondary"])

    def test_unresolved_dimensions_remain_hold(self):
        policy = self.manifest["unresolved_dimension_policy"]
        self.assertEqual("HOLD", policy["status"])
        self.assertEqual([], policy["manufacturing_dimensions_created"])
        self.assertTrue(
            all(
                row["unresolved_values"]
                for row in self.manifest["interfaces"]
            )
        )
