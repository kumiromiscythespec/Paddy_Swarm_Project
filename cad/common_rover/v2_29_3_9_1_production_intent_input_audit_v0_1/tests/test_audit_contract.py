from __future__ import annotations

import unittest

from audit_contract import (
    DUMMY_DECLARATIONS,
    PRINTED_MANUFACTURING_FIELDS,
    build_ai10_audit,
    build_bbox_structural_audit,
    build_cbox_structural_audit,
    build_fastener_audit,
    build_float_width_audit,
    build_overall_audit,
    build_printed_part_audit,
    build_real_profile_audit,
    repository_root,
)


class AuditContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = repository_root()

    def test_actual_profile_inputs_remain_incomplete(self):
        report = build_real_profile_audit(self.root)
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertFalse(report["generic_20x20_value_inference_allowed"])
        self.assertIn("slot_opening_width", report["missing_fields"])
        self.assertIn("planned_manufacturer", report["missing_fields"])
        nominal = next(
            item
            for item in report["records"]
            if item["field"] == "nominal_outer_dimensions"
        )
        self.assertEqual(nominal["value"], [20.0, 20.0])
        self.assertEqual(nominal["classification"], "CONFIRMED_ENVELOPE_ONLY")

    def test_cbox_and_bbox_structure_fail_closed(self):
        cbox = build_cbox_structural_audit()
        bbox = build_bbox_structural_audit()
        self.assertEqual(cbox["status"], "INCOMPLETE")
        self.assertEqual(bbox["status"], "INCOMPLETE")
        self.assertFalse(bbox["bbox_cantilevered_from_cbox_allowed"])
        self.assertFalse(bbox["current_independent_support_is_structural"])

    def test_fastener_candidates_are_not_hole_authority(self):
        report = build_fastener_audit()
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertFalse(report["candidate_values_are_hole_geometry_authority"])
        classifications = {
            item["field"]: item["classification"]
            for item in report["records"]
        }
        self.assertEqual(
            classifications["bolt_diameter"],
            "CANDIDATE_NOT_APPROVED",
        )
        self.assertEqual(classifications["bolt_length"], "MISSING")

    def test_every_print_category_audits_every_required_field(self):
        report = build_printed_part_audit()
        self.assertEqual(report["status"], "INCOMPLETE")
        for category in report["categories"]:
            self.assertEqual(
                {item["field"] for item in category["inputs"]},
                set(PRINTED_MANUFACTURING_FIELDS),
            )
            self.assertEqual(category["status"], "INCOMPLETE")

    def test_float_width_does_not_calculate_with_dummy_candidates(self):
        report = build_float_width_audit(self.root)
        self.assertEqual(report["status"], "HOLD")
        self.assertEqual(report["known_authority"]["bare_frame_width_mm"], 178.0)
        self.assertEqual(
            report["known_authority"]["registered_interface_maximum_mm"],
            286,
        )
        self.assertEqual(
            report["known_authority"]["operational_hard_limit_mm"],
            300,
        )
        self.assertIsNone(report["assembled_maximum_width_mm"])
        self.assertFalse(report["candidate_dummy_width_values_used"])

    def test_ai10_is_reservation_not_manufacturing_geometry(self):
        report = build_ai10_audit()
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertFalse(report["manufacturing_geometry_created"])
        fields = {item["field"]: item for item in report["records"]}
        self.assertEqual(
            fields["sync_ratio"]["classification"],
            "CANDIDATE_NOT_APPROVED",
        )
        self.assertEqual(
            fields["independent_pto_neutral_interlock"]["classification"],
            "REQUIRED_NOT_DESIGNED",
        )
        self.assertEqual(
            fields["normally_closed_material_gate"]["classification"],
            "REQUIRED_NOT_DESIGNED",
        )

    def test_dummy_declarations_are_explicit(self):
        self.assertEqual(
            DUMMY_DECLARATIONS["referenced_existing_dummy_stl_count"],
            33,
        )
        for name in (
            "manufacturing_part",
            "real_rover_part",
            "structural_part",
            "actual_aluminum_profile_compatible",
            "geometry_reuse_automatically_approved",
        ):
            self.assertFalse(DUMMY_DECLARATIONS[name])
        self.assertEqual(
            DUMMY_DECLARATIONS["production_part_number_reuse"],
            "PROHIBITED",
        )

    def test_overall_audit_is_pass_with_hold(self):
        profile = build_real_profile_audit(self.root)
        cbox = build_cbox_structural_audit()
        bbox = build_bbox_structural_audit()
        fastener = build_fastener_audit()
        printed = build_printed_part_audit()
        float_width = build_float_width_audit(self.root)
        ai10 = build_ai10_audit()
        report = build_overall_audit(
            profile=profile,
            cbox=cbox,
            bbox=bbox,
            fastener=fastener,
            printed=printed,
            float_width=float_width,
            ai10=ai10,
        )
        self.assertEqual(report["audit_status"], "PASS_WITH_HOLD")
        self.assertEqual(
            report["completion_gate"]["production_stl_generation"],
            "HOLD",
        )
        self.assertEqual(
            report["completion_gate"]["dummy_stl_print"],
            "NOT_SELECTED",
        )


if __name__ == "__main__":
    unittest.main()
