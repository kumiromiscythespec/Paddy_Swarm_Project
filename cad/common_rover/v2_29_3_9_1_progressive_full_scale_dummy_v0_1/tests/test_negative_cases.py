from __future__ import annotations

from dataclasses import replace
import unittest

from authority_adapter import (
    rear_support_input_audit,
    validate_rear_support_audit,
)
from dummy_component_registry import COMPONENTS, validate_component_registry
from float_width_audit import reject_unqualified_width
from part_number_registry import (
    PARTS,
    reject_filename_or_metadata_only,
    validate_registry,
)
from progressive_print_plan import PRINT_STEPS, validate_print_order
from stl_exporter import MarkingEvidence, validate_marking_evidence
from validate_dummy_kit import (
    validate_assembly_safety_contract,
    validate_body_dimension_records,
    validate_full_set_declaration,
)


class NegativeCaseTests(unittest.TestCase):
    def test_missing_part_number_rejected(self):
        bad = (replace(PARTS[0], part_number=""), *PARTS[1:])
        with self.assertRaises(ValueError):
            validate_registry(bad)

    def test_duplicated_part_number_rejected(self):
        bad = (
            PARTS[0],
            replace(PARTS[1], part_number=PARTS[0].part_number),
            *PARTS[2:],
        )
        with self.assertRaises(ValueError):
            validate_registry(bad)

    def test_filename_only_marking_rejected(self):
        with self.assertRaisesRegex(ValueError, "ONLY_IN_FILENAME"):
            reject_filename_or_metadata_only(
                physical_marking=False,
                filename_marking=True,
                metadata_marking=False,
            )

    def test_metadata_only_marking_rejected(self):
        with self.assertRaisesRegex(ValueError, "ONLY_IN_METADATA"):
            reject_filename_or_metadata_only(
                physical_marking=False,
                filename_marking=False,
                metadata_marking=True,
            )

    def test_part_number_on_slide_surface_rejected(self):
        bad = (
            replace(PARTS[0], marking_surface="SLIDING SURFACE"),
            *PARTS[1:],
        )
        with self.assertRaises(ValueError):
            validate_registry(bad)

    def test_floating_marking_rejected(self):
        evidence = MarkingEvidence(
            part_number=PARTS[0].part_number,
            geometry_part_number=PARTS[0].part_number,
            required_lines=PARTS[0].required_marking_lines,
            marking_surface=PARTS[0].marking_surface,
            physical_marking="ENGRAVED",
            marking_verified=False,
            glyph_solid_count=4,
            intersecting_glyph_solid_count=3,
            floating_text_solid_count=1,
            engraved_volume_mm3=1.0,
        )
        with self.assertRaisesRegex(ValueError, "FLOATING"):
            validate_marking_evidence(evidence)

    def test_old_cbox_dimensions_rejected(self):
        actual = {
            "current_cbox_dummy": (150.0, 200.0, 120.0),
            "current_bbox_dummy": (150.0, 220.0, 150.0),
            "battery_cassette_dummy": (125.0, 180.0, 120.0),
        }
        authority = {
            "CBOX": {"X": 130.0, "Y": 140.0, "Z": 105.0},
            "BBOX": {"X": 150.0, "Y": 220.0, "Z": 150.0},
            "BATTERY_CASSETTE": {"X": 125.0, "Y": 180.0, "Z": 120.0},
        }
        with self.assertRaisesRegex(ValueError, "OLD_OR_INCORRECT"):
            validate_body_dimension_records(actual, authority)

    def test_old_bbox_dimensions_rejected(self):
        actual = {
            "current_cbox_dummy": (130.0, 140.0, 105.0),
            "current_bbox_dummy": (150.0, 200.0, 120.0),
            "battery_cassette_dummy": (125.0, 180.0, 120.0),
        }
        authority = {
            "CBOX": {"X": 130.0, "Y": 140.0, "Z": 105.0},
            "BBOX": {"X": 150.0, "Y": 220.0, "Z": 150.0},
            "BATTERY_CASSETTE": {"X": 125.0, "Y": 180.0, "Z": 120.0},
        }
        with self.assertRaisesRegex(ValueError, "OLD_OR_INCORRECT"):
            validate_body_dimension_records(actual, authority)

    def test_battery_omission_rejected(self):
        actual = {
            "current_cbox_dummy": (130.0, 140.0, 105.0),
            "current_bbox_dummy": (150.0, 220.0, 150.0),
        }
        authority = {
            "CBOX": {"X": 130.0, "Y": 140.0, "Z": 105.0},
            "BBOX": {"X": 150.0, "Y": 220.0, "Z": 150.0},
            "BATTERY_CASSETTE": {"X": 125.0, "Y": 180.0, "Z": 120.0},
        }
        with self.assertRaisesRegex(ValueError, "BODY_DUMMY_OMITTED"):
            validate_body_dimension_records(actual, authority)

    def test_bbox_supported_only_by_cbox_rejected(self):
        assembly = {
            "dummy_interfaces": {
                "BBOX": {
                    "supported_by_cbox": True,
                    "independent_support_path_visible": False,
                    "supports": ["current_cbox_dummy"],
                },
                "CBOX_BBOX_ALIGNMENT": {
                    "connector_structural_load": False,
                    "primary_lock": "REMOVABLE_METAL_PIN_CANDIDATE",
                },
                "FLOAT": {
                    "lower_adapter_host": "BOTTOM_SLOT",
                    "printed_cover_primary": False,
                },
            }
        }
        with self.assertRaisesRegex(ValueError, "BBOX_SUPPORTED_ONLY"):
            validate_assembly_safety_contract(assembly)

    def test_float_above_300_rejected(self):
        with self.assertRaisesRegex(ValueError, "EXCEEDS_HARD_LIMIT"):
            reject_unqualified_width(
                nominal_mm=301.0,
                bracket_audited=True,
            )

    def test_290_without_bracket_audit_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNAUDITED_290"):
            reject_unqualified_width(
                nominal_mm=290.0,
                bracket_audited=False,
            )

    def test_width_category_conflation_rejected(self):
        with self.assertRaisesRegex(ValueError, "REGISTERED_WIDTH"):
            reject_unqualified_width(
                nominal_mm=280.0,
                bracket_audited=True,
                registered_treated_as_hard=True,
            )
        with self.assertRaisesRegex(ValueError, "HARD_LIMIT"):
            reject_unqualified_width(
                nominal_mm=280.0,
                bracket_audited=True,
                hard_treated_as_registered=True,
            )

    def test_lower_adapter_off_bottom_slot_rejected(self):
        changed = tuple(
            replace(component, host_slot="TOP_SLOT")
            if component.key == "lower_float_adapter_left"
            else component
            for component in COMPONENTS
        )
        with self.assertRaisesRegex(ValueError, "OFF_BOTTOM_SLOT"):
            validate_component_registry(changed)

    def test_direct_rail_hole_rejected(self):
        changed = (
            replace(COMPONENTS[0], direct_rail_holes=True),
            *COMPONENTS[1:],
        )
        with self.assertRaisesRegex(ValueError, "DIRECT_RAIL_HOLE"):
            validate_component_registry(changed)

    def test_thumb_latch_as_primary_rejected(self):
        assembly = {
            "dummy_interfaces": {
                "BBOX": {
                    "supported_by_cbox": False,
                    "independent_support_path_visible": True,
                    "supports": ["bbox_support_front", "bbox_support_rear"],
                },
                "CBOX_BBOX_ALIGNMENT": {
                    "connector_structural_load": False,
                    "primary_lock": "PRINTED_THUMB_LATCH",
                },
                "FLOAT": {
                    "lower_adapter_host": "BOTTOM_SLOT",
                    "printed_cover_primary": False,
                },
            }
        }
        with self.assertRaisesRegex(ValueError, "LATCH_AS_PRIMARY"):
            validate_assembly_safety_contract(assembly)

    def test_complete_with_coupon_only_rejected(self):
        with self.assertRaises(ValueError):
            validate_full_set_declaration(
                part_keys={"coupon_01"},
                document_names={"full_dummy_assembly_manual.md"},
                declared_complete="PASS",
            )

    def test_complete_without_manual_rejected(self):
        with self.assertRaisesRegex(ValueError, "WITHOUT_ASSEMBLY_MANUAL"):
            validate_full_set_declaration(
                part_keys={part.key for part in PARTS},
                document_names=set(),
                declared_complete="PASS",
            )

    def test_mirror_before_first_side_gate_rejected(self):
        steps = list(PRINT_STEPS)
        steps[0], steps[1] = steps[1], steps[0]
        with self.assertRaisesRegex(ValueError, "MIRROR_PRINTED_BEFORE"):
            validate_print_order(tuple(steps))

    def test_all_parts_one_plate_rejected(self):
        steps = (
            replace(PRINT_STEPS[0], quantity=19),
            *PRINT_STEPS[1:],
        )
        with self.assertRaisesRegex(ValueError, "ONE_PLATE"):
            validate_print_order(steps)

    def test_unresolved_structure_silently_fixed_rejected(self):
        audit = rear_support_input_audit()
        audit["unresolved_fields"] = []
        with self.assertRaisesRegex(ValueError, "SILENTLY_FIXED"):
            validate_rear_support_audit(audit)

    def test_dummy_only_missing_no_load_rejected(self):
        bad = (
            replace(PARTS[0], classification_marking="DUMMY ONLY"),
            *PARTS[1:],
        )
        with self.assertRaisesRegex(ValueError, "missing_no_load"):
            validate_registry(bad)


if __name__ == "__main__":
    unittest.main()
