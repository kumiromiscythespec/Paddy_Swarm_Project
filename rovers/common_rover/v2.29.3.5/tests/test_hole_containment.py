import unittest

from _test_support import CONTAINMENT, STATIC, install_matrix_tests


class HoleContainmentTests(unittest.TestCase):
    def test_known_candidate_partition(self):
        summary = STATIC["containment_gate"]
        self.assertEqual(
            (
                summary["fully_interior_hole_candidate_count"],
                summary["edge_breakout_hole_candidate_count"],
                summary["rail_exterior_hole_candidate_count"],
            ),
            (4, 5, 15),
        )

    def test_full_circle_not_center_only(self):
        self.assertTrue(
            all(
                row["full_circle_contained"]
                == (row["measured_ligament_edge_distance_mm"] >= 0)
                for row in CONTAINMENT
                if not row["center_outside_material"]
            )
        )


install_matrix_tests(
    HoleContainmentTests,
    "full_circle",
    30,
    lambda index: (
        CONTAINMENT[index % 24]["hole_radius_mm"] > 0
        and CONTAINMENT[index % 24]["candidate_class"]
        in {
            "FULLY_INTERIOR",
            "EDGE_BREAKOUT",
            "RAIL_EXTERIOR_OR_CONTRADICTION",
        }
    ),
)
