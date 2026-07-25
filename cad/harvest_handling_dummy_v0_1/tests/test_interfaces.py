"""Common finite-value and interface validation tests."""

from __future__ import annotations

import math
import sys
import unittest
from dataclasses import replace
from pathlib import Path

CAD_ROOT = Path(__file__).resolve().parents[2]
if str(CAD_ROOT) not in sys.path:
    sys.path.insert(0, str(CAD_ROOT))

from harvest_handling_dummy_v0_1.interfaces import (
    require_finite,
    require_non_negative,
    require_positive,
    validate_all_interfaces,
    validate_base_socket_interface,
    validate_direction,
    validate_root_base,
    validate_stem_socket,
)
from harvest_handling_dummy_v0_1.parameters import (
    BASE_SOCKET,
    ROOT_BASE,
    BaseSocketInterface,
    StemSocketParams,
)


class InterfaceValidationTests(unittest.TestCase):
    """HHD interfaces must reject unsafe or non-finite values."""

    def test_standard_interfaces_validate(self) -> None:
        validate_all_interfaces()

    def test_negative_dimensions_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            require_positive(candidate=-1.0)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            require_non_negative(candidate=-0.1)

    def test_nan_and_infinity_are_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "finite"):
                    require_finite(candidate=value)
                with self.assertRaisesRegex(ValueError, "finite"):
                    validate_stem_socket(
                        replace(StemSocketParams(), outer_axis_length=value)
                    )

    def test_petg_wall_below_two_mm_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 2.0"):
            validate_root_base(replace(ROOT_BASE, petg_min_wall=1.99))
        with self.assertRaisesRegex(ValueError, "at least 2.0"):
            validate_stem_socket(
                replace(StemSocketParams(), petg_min_wall=1.99)
            )

    def test_receiver_not_larger_than_shank_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "larger than socket shank"):
            validate_base_socket_interface(
                replace(
                    BASE_SOCKET,
                    receiver_diameter=BASE_SOCKET.shank_diameter,
                )
            )

    def test_insufficient_insertion_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 12"):
            validate_base_socket_interface(
                replace(BASE_SOCKET, insertion_depth=11.9)
            )
        with self.assertRaisesRegex(ValueError, "insertion depth is insufficient"):
            validate_stem_socket(
                replace(StemSocketParams(), outer_axis_length=27.9)
            )

    def test_only_eight_index_directions_are_allowed(self) -> None:
        for direction in range(0, 360, 45):
            validate_direction(float(direction))
        for direction in (-45.0, 1.0, 22.5, 360.0):
            with self.subTest(direction=direction):
                with self.assertRaisesRegex(ValueError, "one of"):
                    validate_direction(direction)


if __name__ == "__main__":
    unittest.main()
