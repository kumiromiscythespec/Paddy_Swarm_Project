import unittest

from _test_support import final_gate_context, install_matrix_tests
from pipeline_gates import evaluate_v229_3_5_final_gate


class PackageWiringTests(unittest.TestCase):
    def test_package_seal_is_final_gate_input(self):
        context = final_gate_context()
        context["package_seal_status"] = "FAIL"
        result = evaluate_v229_3_5_final_gate(context)
        self.assertIn("PACKAGE_SEAL_NOT_PASS", result["reasons"])

    def test_final_gate_does_not_unlock_loop_002(self):
        result = evaluate_v229_3_5_final_gate(final_gate_context())
        self.assertEqual(result["next_loop_eligibility"], "BLOCKED")


install_matrix_tests(
    PackageWiringTests,
    "package",
    30,
    lambda index: (
        "PACKAGE_SEAL_NOT_PASS"
        in evaluate_v229_3_5_final_gate(
            {**final_gate_context(), "package_seal_status": "FAIL"}
        )["reasons"]
        and index >= 0
    ),
)
