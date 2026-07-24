import unittest

from _test_support import CONTAINMENT, STATIC, install_matrix_tests


class HoleEdgeDistanceTests(unittest.TestCase):
    def test_five_boundary_openings_are_stopped(self):
        self.assertEqual(
            set(STATIC["containment_gate"]["known_boundary_candidate_ids"]),
            {"OP-0057", "OP-0059", "OP-0069", "OP-0153", "OP-0157"},
        )

    def test_radius_is_included_in_ligament(self):
        self.assertTrue(
            all(
                abs(
                    row["measured_ligament_edge_distance_mm"]
                    - (
                        row["measured_center_to_edge_mm"]
                        - row["hole_radius_mm"]
                    )
                )
                < 1e-9
                for row in CONTAINMENT
            )
        )


install_matrix_tests(
    HoleEdgeDistanceTests,
    "edge_radius",
    30,
    lambda index: (
        CONTAINMENT[index % 24]["edge_distance_deficit_mm"] >= 0
        and CONTAINMENT[index % 24]["strength_approval"]
        == "NOT_GRANTED_STATIC_LAYOUT_PROXY_ONLY"
    ),
)
