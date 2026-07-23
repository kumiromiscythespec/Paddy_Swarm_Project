import unittest

from _test_support import final_gate_context, install_matrix_tests
from pipeline_gates import evaluate_v229_3_5_final_gate, exit_code_for_context


class MinimumAssemblyGateWiringTests(unittest.TestCase):
    def test_undefined_joint_blocks_final_gate(self):
        result = evaluate_v229_3_5_final_gate(final_gate_context())
        self.assertEqual(result["status"], "BLOCKED")

    def test_undefined_joint_exit_is_nonzero(self):
        context = final_gate_context()
        context["minimum_assembly_status"] = (
            "BLOCKED_BY_UNDEFINED_STRUCTURAL_JOINT"
        )
        self.assertEqual(exit_code_for_context(context), 71)


install_matrix_tests(
    MinimumAssemblyGateWiringTests,
    "assembly_gate",
    30,
    lambda index: (
        evaluate_v229_3_5_final_gate(final_gate_context())[
            "next_loop_eligibility"
        ]
        == "BLOCKED"
        and index >= 0
    ),
)
