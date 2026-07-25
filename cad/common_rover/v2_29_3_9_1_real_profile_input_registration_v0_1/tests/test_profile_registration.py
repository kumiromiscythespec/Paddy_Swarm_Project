from __future__ import annotations

import unittest

from incoming_inspection_contract import (
    SAMPLE_IDS,
    build_inspection_contract,
    validate_inspection_contract,
)
from profile_input_contract import (
    CANONICAL_INVENTORY_ALGORITHM,
    CANONICAL_INVENTORY_SHA256,
)
from profile_role_candidate_matrix import (
    ROLE_CANDIDATES,
    build_role_matrix,
    validate_role_matrix,
)
from supplier_profile_registry import (
    build_registry,
    validate_registry,
)
from update_production_input_audit import build_production_audit_update


class ProfileRegistrationTests(unittest.TestCase):
    def test_registry_contains_two_distinct_ordered_profiles(self):
        registry = build_registry()
        validate_registry(registry)
        records = {
            record["profile_id"]: record
            for record in registry["profiles"]
        }
        self.assertEqual(
            records["PROFILE-01"]["ordered_part_number"],
            "NFS5-2020-400",
        )
        self.assertEqual(
            records["PROFILE-02"]["ordered_part_number"],
            "NFSB5-2040-400",
        )
        self.assertEqual(
            records["PROFILE-01"]["nominal_outer_section_mm"],
            [20, 20],
        )
        self.assertEqual(
            records["PROFILE-02"]["nominal_outer_section_mm"],
            [20, 40],
        )

    def test_purchase_evidence_never_becomes_geometry_authority(self):
        registry = build_registry()
        self.assertFalse(
            registry["purchase_evidence_is_geometry_authority"]
        )
        for record in registry["profiles"]:
            self.assertEqual(
                record["design_authority_status"],
                "NOT_ESTABLISHED",
            )
            self.assertEqual(record["arrival_status"], "PENDING")
            self.assertEqual(record["measurement_status"], "INCOMPLETE")
            self.assertEqual(record["production_geometry_gate"], "HOLD")

    def test_no_personal_order_data_is_registered(self):
        serialized = repr(build_registry()).lower()
        for forbidden in (
            "customer_name",
            "shipping_address",
            "payment_information",
            "personal_order_number",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_role_matrix_contains_only_candidate_roles(self):
        matrix = build_role_matrix()
        validate_role_matrix(matrix)
        self.assertEqual(
            len(matrix["rows"]),
            sum(len(roles) for roles in ROLE_CANDIDATES.values()),
        )
        self.assertTrue(
            all(row["role_status"] == "CANDIDATE_ONLY" for row in matrix["rows"])
        )

    def test_inspection_contract_has_two_samples_per_profile(self):
        contract = build_inspection_contract()
        validate_inspection_contract(contract)
        self.assertEqual(set(contract["sample_ids"]), set(SAMPLE_IDS))
        for profile_id in ("PROFILE-01", "PROFILE-02"):
            self.assertEqual(
                sum(sample.startswith(profile_id) for sample in SAMPLE_IDS),
                2,
            )

    def test_three_position_measurements_exist_for_each_sample(self):
        contract = build_inspection_contract()
        for sample_id in SAMPLE_IDS:
            for item in (
                "actual_overall_width",
                "actual_overall_height",
                "slot_opening_width",
            ):
                positions = {
                    row["measurement_position"]
                    for row in contract["rows"]
                    if row["sample_id"] == sample_id
                    and row["measurement_item"] == item
                }
                self.assertEqual(positions, {"END_A", "CENTER", "END_B"})

    def test_internal_geometry_is_not_direct_caliper_complete(self):
        contract = build_inspection_contract()
        methods = {
            row["measurement_item"]: row["required_method"]
            for row in contract["rows"]
        }
        self.assertEqual(
            methods["visible_internal_cavity_dimensions"],
            "SECTION_CUT_REQUIRED",
        )
        self.assertEqual(
            methods["slot_internal_maximum_width"],
            "SUPPLIER_DRAWING_REQUIRED",
        )

    def test_production_audit_update_preserves_all_holds(self):
        update = build_production_audit_update()
        self.assertEqual(update["PROFILE_REGISTRATION"], "PASS_WITH_HOLD")
        self.assertEqual(update["REAL_PROFILE_INPUT_STATUS"], "INCOMPLETE")
        self.assertEqual(update["PRODUCTION_STL_GENERATION"], "HOLD")
        self.assertEqual(update["PRINT_STAGE"], "NOT_REACHED")
        self.assertEqual(
            update["inherited_domain_gates"][
                "CBOX_STRUCTURAL_INPUT_STATUS"
            ],
            "INCOMPLETE",
        )

    def test_canonical_baseline_contract_is_pinned(self):
        self.assertEqual(
            CANONICAL_INVENTORY_ALGORITHM,
            "SHA256_OF_UTF8_BYTEWISE_SORTED_POSIX_PATH_RECORDS_V1",
        )
        self.assertEqual(
            CANONICAL_INVENTORY_SHA256,
            "741f6a2be192db200ba55e5388ca14d09020ff6f4f9de844f2353bd5ef382ad9",
        )


if __name__ == "__main__":
    unittest.main()
