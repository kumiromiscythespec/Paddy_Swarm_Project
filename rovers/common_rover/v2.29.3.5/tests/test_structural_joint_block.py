import unittest

from _test_support import STATIC, install_matrix_tests


class StructuralJointBlockTests(unittest.TestCase):
    def test_crossmember_joint_remains_measurement_hold(self):
        self.assertEqual(
            STATIC["rail_crossmember_joint_status"], "MEASUREMENT_HOLD"
        )

    def test_static_candidate_is_not_overlap_authority(self):
        joint = STATIC["joints"][0]
        self.assertFalse(joint["allows_overlap"])
        self.assertEqual(joint["joint_type"], "UNDEFINED_MEASUREMENT_HOLD")


install_matrix_tests(
    StructuralJointBlockTests,
    "joint_block",
    30,
    lambda index: (
        STATIC["joints"][0]["expected_overlap"]["status"]
        == "MEASUREMENT_REQUIRED"
        and index >= 0
    ),
)
