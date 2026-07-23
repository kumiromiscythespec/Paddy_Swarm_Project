import json
import unittest

from _test_support import SOURCE, REGISTRIES, deep_static_copy, install_matrix_tests
from full_loop_runner import run_static_authority


class ReplayTests(unittest.TestCase):
    def test_static_authority_is_deterministic(self):
        left = run_static_authority(REGISTRIES, SOURCE)
        right = run_static_authority(REGISTRIES, SOURCE)
        self.assertEqual(
            json.dumps(left, sort_keys=True),
            json.dumps(right, sort_keys=True),
        )

    def test_copy_does_not_mutate_authority(self):
        left = deep_static_copy()
        right = deep_static_copy()
        left["authority_rows"][0]["coordinate_relocated"] = True
        self.assertFalse(right["authority_rows"][0]["coordinate_relocated"])


install_matrix_tests(
    ReplayTests,
    "replay",
    30,
    lambda index: (
        run_static_authority(REGISTRIES, SOURCE)["routing_gate"]["status"]
        == "PASS"
        and index >= 0
    ),
)
