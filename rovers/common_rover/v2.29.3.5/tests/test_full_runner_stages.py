import unittest

from _test_support import STAGES, install_matrix_tests
from full_loop_runner import EXIT_CODES, requested_stage_limit


class FullRunnerStageTests(unittest.TestCase):
    def test_full_stage_registry_has_24_ordered_stages(self):
        self.assertEqual(len(STAGES), 24)
        self.assertEqual(STAGES[0], "PREFLIGHT")
        self.assertEqual(STAGES[-1], "FINAL_ZIP_SEAL")

    def test_cadquery_unavailable_is_not_success(self):
        self.assertEqual(EXIT_CODES["CADQUERY_UNAVAILABLE"], 20)
        self.assertNotEqual(EXIT_CODES["CADQUERY_UNAVAILABLE"], 0)


install_matrix_tests(
    FullRunnerStageTests,
    "stage",
    30,
    lambda index: (
        STAGES[index % 24]
        and requested_stage_limit("all") == 24
        and requested_stage_limit("finalize") == 24
    ),
)
