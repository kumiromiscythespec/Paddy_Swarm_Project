from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest

from incoming_inspection_contract import (
    build_inspection_contract,
    record_measurement,
    validate_inspection_contract,
)
from profile_input_contract import ensure_external_output
from profile_role_candidate_matrix import (
    build_role_matrix,
    promote_candidate_role,
    set_profile_02_orientation,
    validate_role_matrix,
)
from supplier_profile_registry import (
    build_registry,
    register_accessory,
    reject_generic_profile_fill,
    validate_registry,
)
from update_production_input_audit import (
    approve_production_stl,
    build_production_audit_update,
    validate_production_part_number,
)
from validate_profile_registration import (
    scan_profile_source_lane,
)

from repository_guard import (  # imported through validation audit-lane setup
    compare_baseline_to_files,
    scan_repository_bytecode,
    scan_untracked_cad,
)


def _cad_record(path: str, content: bytes) -> dict:
    return {
        "path": path,
        "extension": Path(path).suffix.lower(),
        "bytes": len(content),
        "git_blob_sha1": "synthetic",
        "sha256": hashlib.sha256(content).hexdigest(),
    }


class ProfileRegistrationNegativeTests(unittest.TestCase):
    def test_profiles_cannot_be_treated_as_same_section(self):
        registry = build_registry()
        registry["profiles"][1]["nominal_outer_section_mm"] = [20, 20]
        with self.assertRaisesRegex(
            ValueError,
            "PROFILES_MUST_NOT_BE_TREATED_AS_SAME_SECTION",
        ):
            validate_registry(registry)

    def test_20x40_cannot_be_treated_as_20x20(self):
        registry = build_registry()
        registry["profiles"][1]["nominal_outer_section_mm"] = [20, 30]
        with self.assertRaisesRegex(
            ValueError,
            "PROFILE_02_MUST_REMAIN_20X40",
        ):
            validate_registry(registry)

    def test_profile_02_orientation_cannot_be_auto_selected(self):
        with self.assertRaisesRegex(
            ValueError,
            "REQUIRES_MEASURED_CLEARANCE_EVIDENCE",
        ):
            set_profile_02_orientation(
                build_role_matrix(),
                "40_MM_VERTICAL",
            )

    def test_amazon_listing_cannot_be_geometry_authority(self):
        registry = build_registry()
        registry["profiles"][0][
            "design_authority_status"
        ] = "ESTABLISHED_FROM_AMAZON_LISTING"
        with self.assertRaisesRegex(
            ValueError,
            "LISTING_PROMOTED_TO_GEOMETRY_AUTHORITY",
        ):
            validate_registry(registry)

    def test_generic_5_series_values_cannot_fill_missing_inputs(self):
        with self.assertRaisesRegex(
            ValueError,
            "GENERIC_5_SERIES_VALUE_INFERENCE_FORBIDDEN",
        ):
            reject_generic_profile_fill(
                {},
                generic_defaults={"actual_slot_depth": 6.0},
            )

    def test_unmeasured_value_cannot_be_zero_filled(self):
        with self.assertRaisesRegex(
            ValueError,
            "UNMEASURED_VALUE_ZERO_FILLED",
        ):
            reject_generic_profile_fill(
                {"measured_outer_dimensions": 0}
            )

    def test_nominal_value_cannot_be_recorded_as_measurement(self):
        row = build_inspection_contract()["rows"][0]
        with self.assertRaisesRegex(
            ValueError,
            "NON_MEASUREMENT_VALUE_SUBSTITUTION_FORBIDDEN",
        ):
            record_measurement(
                row,
                value=20.0,
                instrument="caliper",
                instrument_resolution=0.01,
                repetition_count=1,
                arrival_status="RECEIVED",
                source_classification="NOMINAL_VALUE_SUBSTITUTION",
            )

    def test_t_nut_part_number_cannot_be_inferred(self):
        with self.assertRaisesRegex(
            ValueError,
            "ACCESSORY_INFERENCE_FORBIDDEN:T_NUT",
        ):
            register_accessory(
                "T_NUT",
                "GENERIC-5-SERIES",
                evidence_classification="INFERRED_FROM_ORDERED_PART_NUMBER",
            )

    def test_bracket_part_number_cannot_be_inferred(self):
        with self.assertRaisesRegex(
            ValueError,
            "ACCESSORY_INFERENCE_FORBIDDEN:CORNER_BRACKET",
        ):
            register_accessory(
                "CORNER_BRACKET",
                "GENERIC-2020",
                evidence_classification="INFERRED_FROM_PRODUCT_NAME",
            )

    def test_measurement_cannot_complete_before_arrival(self):
        registry = build_registry()
        registry["profiles"][0]["measurement_status"] = "COMPLETE"
        with self.assertRaisesRegex(
            ValueError,
            "MEASUREMENT_COMPLETE_BEFORE_ARRIVAL",
        ):
            validate_registry(registry)

    def test_inspection_contract_cannot_complete_before_arrival(self):
        contract = build_inspection_contract()
        contract["measurement_status"] = "COMPLETE"
        with self.assertRaisesRegex(
            ValueError,
            "MEASUREMENT_COMPLETE_BEFORE_ARRIVAL",
        ):
            validate_inspection_contract(contract)

    def test_candidate_role_cannot_be_promoted(self):
        with self.assertRaisesRegex(
            ValueError,
            "ROLE_PROMOTION_REQUIRES_SEPARATE_APPROVAL",
        ):
            promote_candidate_role(
                build_role_matrix(),
                profile_id="PROFILE-01",
                candidate_role="FPB left rail",
            )

    def test_mutated_final_role_is_rejected(self):
        matrix = build_role_matrix()
        matrix["rows"][0]["role_status"] = "FINAL"
        matrix["rows"][0]["final_role"] = "FPB left rail"
        with self.assertRaisesRegex(
            ValueError,
            "ROLE_CANDIDATE_IMPROPERLY_PROMOTED",
        ):
            validate_role_matrix(matrix)

    def test_registration_cannot_release_production_stl(self):
        with self.assertRaisesRegex(
            ValueError,
            "PROFILE_REGISTRATION_CANNOT_APPROVE_PRODUCTION_STL",
        ):
            approve_production_stl(build_production_audit_update())

    def test_dummy_part_number_cannot_be_reused(self):
        with self.assertRaisesRegex(
            ValueError,
            "DUMMY_PART_NUMBER_PRODUCTION_REUSE_FORBIDDEN",
        ):
            validate_production_part_number(
                "PS-PR-A0-MNT-001-R00",
                dummy_part_numbers={"PS-PR-A0-MNT-001-R00"},
            )

    def test_repository_cad_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(
                ValueError,
                "PRODUCTION_CAD_OUTPUT_FORBIDDEN",
            ):
                ensure_external_output(
                    root.parent / "profile.stl",
                    root,
                    allowed_names={"profile.stl"},
                )

    def test_modified_baseline_cad_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "baseline/profile.stl"
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(b"modified")
            report = compare_baseline_to_files(
                root,
                [_cad_record(relative, b"baseline")],
                {relative},
            )
            self.assertEqual(report["MODIFIED_TRACKED_CAD_OUTPUT_COUNT"], 1)

    def test_deleted_baseline_cad_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            report = compare_baseline_to_files(
                Path(directory),
                [_cad_record("baseline/profile.step", b"baseline")],
                set(),
            )
            self.assertEqual(report["DELETED_TRACKED_CAD_OUTPUT_COUNT"], 1)

    def test_untracked_cad_is_rejected_even_if_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".gitignore").write_text("*.step\n", encoding="utf-8")
            (root / "hidden.step").write_bytes(b"cad")
            report = scan_untracked_cad(root, set())
            self.assertEqual(report["UNTRACKED_CAD_OUTPUT_COUNT"], 1)

    def test_bytecode_and_pycache_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "profile.cpython-313.pyc").write_bytes(b"bytecode")
            report = scan_repository_bytecode(root)
            self.assertEqual(report["status"], "FAIL")

    def test_generated_result_in_source_lane_is_rejected(self):
        from profile_input_contract import LANE_RELATIVE

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lane = root / LANE_RELATIVE
            lane.mkdir(parents=True)
            (lane / "supplier_profile_registry.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            report = scan_profile_source_lane(root)
            self.assertEqual(report["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
