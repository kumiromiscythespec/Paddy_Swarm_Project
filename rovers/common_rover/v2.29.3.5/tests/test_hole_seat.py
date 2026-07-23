import unittest

from _test_support import SEATS, STATIC, install_matrix_tests


class HoleSeatTests(unittest.TestCase):
    def test_required_hole_seats_have_no_static_failure(self):
        self.assertEqual(
            STATIC["seat_gate"]["required_hole_seat_failure_count"], 0
        )

    def test_half_seats_never_pass(self):
        self.assertTrue(
            all(
                row["seat_status"] == "HOLE_SEAT_FAILURE"
                for row in SEATS
                if row["unsupported_half_seat"]
            )
        )


install_matrix_tests(
    HoleSeatTests,
    "seat",
    30,
    lambda index: (
        SEATS[index % 24]["seat_outer_diameter_mm"] > 0
        and SEATS[index % 24]["actual_solid_validation"] == "NOT_RUN"
    ),
)
