import unittest

from _test_support import GROUPS, STATIC, install_matrix_tests


class AttachmentGroupAuditTests(unittest.TestCase):
    def test_six_groups_have_four_instances_each(self):
        self.assertEqual(len(GROUPS), 6)
        self.assertTrue(all(row["instance_count"] == 4 for row in GROUPS))

    def test_no_group_is_silently_dropped(self):
        self.assertEqual(STATIC["group_gate"]["instance_count"], 24)


install_matrix_tests(
    AttachmentGroupAuditTests,
    "group_authority",
    30,
    lambda index: (
        GROUPS[index % 6]["required_design_correction"]
        and GROUPS[index % 6]["hole_pattern_authority"]
    ),
)
