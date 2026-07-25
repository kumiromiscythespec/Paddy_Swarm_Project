from __future__ import annotations

from copy import deepcopy
import unittest

from authority_adapter import load_context
from validate_interfaces import (
    build_complete_manifest,
    validate_contract_data,
)


class InterfaceNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        context = load_context(validate_seed_geometry=False)
        cls.baseline = build_complete_manifest(context)

    def mutated(self):
        return deepcopy(self.baseline)

    def blockers(self, data):
        return validate_contract_data(data)

    def interface(self, data, interface_id):
        return next(
            row
            for row in data["interfaces"]
            if row["interface_id"] == interface_id
        )

    def printed_part(self, data, coupon_id):
        return next(
            row
            for row in data["printed_parts"]
            if row["coupon_id"] == coupon_id
        )

    def test_negative_01_float_fixed_by_thumb_latch_only(self):
        data = self.mutated()
        ai07 = self.interface(data, "AI-07")
        ai07["primary_secondary"] = "SECONDARY"
        ai07["fastener_candidate"] = "printed thumb latch"
        ai07["visible_confirmation_point"] = "thumb latch"
        ai07["human_intervention_method"] = "press thumb latch"
        self.assertIn("FLOAT_THUMB_LATCH_ONLY", self.blockers(data))

    def test_negative_02_cbox_fixed_by_snap_hook_only(self):
        data = self.mutated()
        ai02 = self.interface(data, "AI-02")
        ai02["primary_secondary"] = "SECONDARY"
        ai02["fastener_candidate"] = "printed snap hook only"
        self.assertIn("CBOX_SNAP_HOOK_ONLY", self.blockers(data))

    def test_negative_03_bbox_cantilevered_from_cbox_only(self):
        data = self.mutated()
        bbox = next(
            row for row in data["load_paths"] if row["component"] == "BBOX"
        )
        bbox["nodes"] = [
            node
            for node in bbox["nodes"]
            if node["name"] != "INDEPENDENT REAR SUPPORT BRIDGE"
        ]
        self.assertIn("BBOX_CANTILEVERED_FROM_CBOX", self.blockers(data))

    def test_negative_04_connector_used_as_structural_support(self):
        data = self.mutated()
        data["electrical_policy"]["connector_structural_load"] = True
        self.assertIn(
            "CONNECTOR_USED_AS_STRUCTURAL_SUPPORT", self.blockers(data)
        )

    def test_negative_05_direct_hole_added_to_fpb(self):
        data = self.mutated()
        data["slot_zone_audit"]["direct_rail_holes_added"] = True
        self.assertIn("UNVALIDATED_DIRECT_RAIL_HOLE", self.blockers(data))

    def test_negative_06_lower_adapter_moved_from_bottom_slot(self):
        data = self.mutated()
        data["slot_zone_audit"]["lower_adapter_slot_face"] = "TOP_SLOT"
        self.assertIn("LOWER_ADAPTER_NOT_BOTTOM_SLOT", self.blockers(data))

    def test_negative_07_lower_adapter_overlaps_occupied_zone(self):
        data = self.mutated()
        data["slot_zone_audit"]["lower_adapter_conflict_count"] = 1
        self.assertIn(
            "LOWER_ADAPTER_SLOT_ZONE_CONFLICT", self.blockers(data)
        )

    def test_negative_08_front_corner_bracket_conflict(self):
        data = self.mutated()
        data["slot_zone_audit"]["front_corner_conflict_count"] = 1
        self.assertIn("FRONT_CORNER_BRACKET_CONFLICT", self.blockers(data))

    def test_negative_09_left_right_key_symmetry(self):
        data = self.mutated()
        data["assembly_markings"]["left_right_keys_asymmetric"] = False
        self.assertIn(
            "LEFT_RIGHT_KEY_REVERSAL_ALLOWED", self.blockers(data)
        )

    def test_negative_10_no_positive_stop(self):
        data = self.mutated()
        self.interface(data, "AI-06")["positive_stop"] = "NONE"
        self.assertIn("POSITIVE_STOP_MISSING:AI-06", self.blockers(data))

    def test_negative_11_no_pin_retention(self):
        data = self.mutated()
        ai07 = self.interface(data, "AI-07")
        ai07["fastener_candidate"] = "6 mm metal pin"
        ai07["visible_confirmation_point"] = "pin head visible"
        ai07["human_intervention_method"] = "withdraw pin"
        self.assertIn("PIN_RETENTION_MISSING", self.blockers(data))

    def test_negative_12_hidden_lock_state(self):
        data = self.mutated()
        self.interface(data, "AI-07")[
            "visible_confirmation_point"
        ] = "HIDDEN under cover"
        self.assertIn(
            "VISIBLE_LOCK_STATE_MISSING:AI-07", self.blockers(data)
        )

    def test_negative_13_pin_aligned_before_final_position(self):
        data = self.mutated()
        data["assembly_markings"][
            "pin_alignment_only_at_positive_stop"
        ] = False
        self.assertIn(
            "PIN_ALIGNS_BEFORE_POSITIVE_STOP", self.blockers(data)
        )

    def test_negative_14_286_treated_as_bare_frame_width(self):
        data = self.mutated()
        data["width_classification"]["bare_frame_width_mm"] = 286.0
        self.assertIn("BARE_FRAME_WIDTH_MISCLASSIFIED", self.blockers(data))

    def test_negative_15_300_treated_as_registered_width(self):
        data = self.mutated()
        data["width_classification"]["registered_width_mm"] = 300.0
        self.assertIn("REGISTERED_WIDTH_MISCLASSIFIED", self.blockers(data))

    def test_negative_16_missing_front_marking(self):
        data = self.mutated()
        data["assembly_markings"]["orientation"].remove("FRONT")
        self.assertIn("MISSING_ORIENTATION_MARKING", self.blockers(data))

    def test_negative_17_duplicated_interface_id(self):
        data = self.mutated()
        data["interfaces"][-1]["interface_id"] = "AI-08"
        self.assertIn("DUPLICATE_INTERFACE_ID", self.blockers(data))

    def test_negative_18_missing_load_path(self):
        data = self.mutated()
        data["load_paths"] = [
            row
            for row in data["load_paths"]
            if row["component"] != "CBOX"
        ]
        self.assertIn("LOAD_PATH_COUNT:CBOX:0", self.blockers(data))

    def test_negative_19_unknown_fastener_silently_accepted(self):
        data = self.mutated()
        ai04 = self.interface(data, "AI-04")
        ai04["fastener_candidate"] = "UNKNOWN"
        ai04["unresolved_values"] = []
        self.assertIn(
            "UNKNOWN_FASTENER_SILENTLY_ACCEPTED:AI-04",
            self.blockers(data),
        )

    def test_negative_20_unresolved_value_becomes_manufacturing_dimension(self):
        data = self.mutated()
        data["unresolved_dimension_policy"][
            "manufacturing_dimensions_created"
        ] = [{"name": "rear_bridge_length_mm", "value": 220.0}]
        self.assertIn(
            "UNRESOLVED_CONVERTED_TO_MANUFACTURING_DIMENSION",
            self.blockers(data),
        )

    def test_negative_21_full_size_structural_stl_exported(self):
        data = self.mutated()
        data["output_audit"]["exported_stl_files"].append(
            "full_rover_structural_part.stl"
        )
        self.assertIn(
            "FULL_SIZE_STRUCTURAL_STL_EXPORTED", self.blockers(data)
        )

    def test_negative_22_repository_output_pollution(self):
        data = self.mutated()
        data["output_audit"]["repository_generated_output_present"] = True
        self.assertIn("REPOSITORY_OUTPUT_POLLUTION", self.blockers(data))

    def test_negative_23_release_hold_removed(self):
        data = self.mutated()
        data["release_holds"]["GITHUB_MANUFACTURING_RELEASE"] = "APPROVED"
        self.assertIn(
            "RELEASE_HOLD_REMOVED:GITHUB_MANUFACTURING_RELEASE",
            self.blockers(data),
        )

    def test_negative_24_coupon_01_part_number_missing(self):
        data = self.mutated()
        self.printed_part(data, "COUPON-01")["part_number"] = ""
        self.assertIn("PRINTED_PART_NUMBER_MISSING", self.blockers(data))

    def test_negative_25_duplicate_coupon_part_number(self):
        data = self.mutated()
        self.printed_part(data, "COUPON-02")[
            "part_number"
        ] = "COUPON-01"
        self.assertIn("PRINTED_PART_NUMBER_DUPLICATE", self.blockers(data))

    def test_negative_26_metadata_part_number_without_geometry_marking(self):
        data = self.mutated()
        row = self.printed_part(data, "COUPON-01")
        row["geometry_part_number"] = ""
        row["marking_verified"] = False
        self.assertIn(
            "PRINTED_PART_NUMBER_METADATA_ONLY", self.blockers(data)
        )

    def test_negative_27_geometry_and_manifest_part_number_mismatch(self):
        data = self.mutated()
        self.printed_part(data, "COUPON-01")[
            "geometry_part_number"
        ] = "COUPON-05"
        self.assertIn(
            "PRINTED_PART_NUMBER_GEOMETRY_MISMATCH",
            self.blockers(data),
        )

    def test_negative_28_filename_and_part_number_mismatch(self):
        data = self.mutated()
        self.printed_part(data, "COUPON-01")[
            "filename"
        ] = "coupon_05_wrong.stl"
        self.assertIn(
            "PRINTED_PART_NUMBER_FILENAME_MISMATCH",
            self.blockers(data),
        )

    def test_negative_29_whitespace_part_number(self):
        data = self.mutated()
        self.printed_part(data, "COUPON-01")["part_number"] = "   "
        self.assertIn("PRINTED_PART_NUMBER_MISSING", self.blockers(data))

    def test_negative_30_floating_part_number_text(self):
        data = self.mutated()
        self.printed_part(data, "COUPON-01")[
            "floating_part_number_solid_count"
        ] = 1
        self.assertIn("PRINTED_PART_NUMBER_FLOATING", self.blockers(data))

    def test_negative_31_part_number_on_sliding_surface(self):
        data = self.mutated()
        self.printed_part(data, "COUPON-02")[
            "marking_surface_class"
        ] = "SLIDING_SURFACE"
        self.assertIn(
            "PRINTED_PART_NUMBER_MARKING_SURFACE_INVALID",
            self.blockers(data),
        )

    def test_negative_32_builder_bypasses_common_marking_handler(self):
        data = self.mutated()
        row = self.printed_part(data, "COUPON-03")
        row["common_marking_handler_invoked"] = False
        row["common_marking_handler"] = "DIRECT_TEXT"
        blockers = self.blockers(data)
        self.assertIn("PRINTED_PART_NUMBER_BUILDER_BYPASS", blockers)
        self.assertIn("PRINTED_PART_NUMBER_METADATA_ONLY", blockers)

    def test_negative_33_fit_test_only_without_part_number(self):
        data = self.mutated()
        row = self.printed_part(data, "COUPON-05")
        row["part_number"] = ""
        row["contains_fit_test_only"] = True
        self.assertIn("PRINTED_PART_NUMBER_MISSING", self.blockers(data))
