"""Fixed-angle sockets, plugs, coupons, and gauges."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

CAD_ROOT = Path(__file__).resolve().parents[2]
if str(CAD_ROOT) not in sys.path:
    sys.path.insert(0, str(CAD_ROOT))

from harvest_handling_dummy_v0_1.angle_gauge import build as build_angle_gauge
from harvest_handling_dummy_v0_1.assemblies.handling_dummy_standard import minimum_socket_clearance
from harvest_handling_dummy_v0_1.cq_utils import validate_print_bounds
from harvest_handling_dummy_v0_1.parameters import BASE_SOCKET, STEM_PLUG_IF
from harvest_handling_dummy_v0_1.socket_lock_coupon import (
    build as build_socket_coupon,
    candidate_receiver_diameters,
)
from harvest_handling_dummy_v0_1.stem_end_plug import (
    build as build_plug,
    params_for_preset,
)
from harvest_handling_dummy_v0_1.stem_plug_fit_coupon import (
    HOLE_DIAMETERS,
    build as build_stem_coupon,
)
from harvest_handling_dummy_v0_1.stem_socket import (
    build as build_socket,
    measured_axis_angle_deg,
    params_for_angle,
)


class StemSocketTests(unittest.TestCase):
    """All fixed socket angles must be printable and numerically exact."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sockets = {
            angle: build_socket(params_for_angle(angle))
            for angle in (0.0, 10.0, 20.0, 30.0)
        }

    def test_four_angles_build_as_single_solids(self) -> None:
        for angle, shape in self.sockets.items():
            with self.subTest(angle=angle):
                metrics = validate_print_bounds(shape, f"socket-{angle}")
                self.assertEqual(metrics.solid_count, 1)
                self.assertGreater(metrics.volume_mm3, 0.0)
                self.assertAlmostEqual(
                    measured_axis_angle_deg(params_for_angle(angle)),
                    angle,
                    delta=0.3,
                )

    def test_eight_direction_index_and_stem_receiver_relations(self) -> None:
        self.assertLess(BASE_SOCKET.index_af, BASE_SOCKET.receiver_index_af)
        self.assertLess(BASE_SOCKET.shank_diameter, BASE_SOCKET.receiver_diameter)
        self.assertLess(STEM_PLUG_IF.shank_diameter, STEM_PLUG_IF.receiver_diameter)
        self.assertEqual(BASE_SOCKET.index_depth, 3.0)

    def test_standard_30_degree_layout_has_positive_socket_clearance(self) -> None:
        self.assertGreaterEqual(minimum_socket_clearance(), 0.0)


class StemPlugAndCouponTests(unittest.TestCase):
    """All five plugs and both calibration series must exist."""

    def test_five_plug_presets_build(self) -> None:
        for preset in (
            "rod_od_2p0",
            "rod_od_3p0",
            "rod_od_4p0",
            "rod_od_5p0",
            "blank_custom",
        ):
            with self.subTest(preset=preset):
                params = params_for_preset(preset)
                metrics = validate_print_bounds(build_plug(params), params.part_id)
                self.assertEqual(metrics.solid_count, 1)
                self.assertGreater(metrics.volume_mm3, 0.0)
                self.assertEqual(params.calibration_status, "CALIBRATION_PENDING")

    def test_three_snap_candidates_and_labels_exist(self) -> None:
        self.assertEqual(BASE_SOCKET.snap_candidate_values, (0.15, 0.25, 0.35))
        self.assertEqual(len(candidate_receiver_diameters()), 3)
        metrics = validate_print_bounds(build_socket_coupon(), "socket coupon")
        self.assertEqual(metrics.solid_count, 1)
        self.assertGreater(metrics.size_z, 18.0 - 1.0e-6)

    def test_five_common_plug_fit_candidates_and_labels_exist(self) -> None:
        self.assertEqual(HOLE_DIAMETERS, (6.10, 6.20, 6.25, 6.30, 6.40))
        metrics = validate_print_bounds(build_stem_coupon(), "plug coupon")
        self.assertEqual(metrics.solid_count, 1)
        self.assertGreater(metrics.size_z, 8.0)

    def test_angle_gauge_is_single_a1_safe_solid(self) -> None:
        metrics = validate_print_bounds(build_angle_gauge(), "angle gauge")
        self.assertEqual(metrics.solid_count, 1)
        self.assertGreater(metrics.size_z, 3.0)


if __name__ == "__main__":
    unittest.main()
