import unittest

from _test_support import AUTHORITY, STATIC, install_matrix_tests


class FastenerRequirementAuthorityTests(unittest.TestCase):
    def test_authority_accounts_for_all_24(self):
        self.assertEqual(len(AUTHORITY), 24)
        self.assertEqual(
            STATIC["authority_gate"]["authority_accounting_result"],
            "PASS_24_OF_24",
        )

    def test_requirement_precedes_reachability(self):
        self.assertTrue(
            all(not row["reachability_used_for_requirement"] for row in AUTHORITY)
        )


install_matrix_tests(
    FastenerRequirementAuthorityTests,
    "authority_row",
    30,
    lambda index: (
        AUTHORITY[index % 24]["classification_order"]
        == "AUTHORITY_BEFORE_REACHABILITY_AND_GEOMETRY"
        and not AUTHORITY[index % 24]["coordinate_relocated"]
    ),
)
