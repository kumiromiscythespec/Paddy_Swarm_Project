"""Standard 24-root non-printable assembly tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

CAD_ROOT = Path(__file__).resolve().parents[2]
if str(CAD_ROOT) not in sys.path:
    sys.path.insert(0, str(CAD_ROOT))

from harvest_handling_dummy_v0_1.assemblies.handling_dummy_standard import (
    build_six_stem_preview,
    build_standard_preview,
)


class StandardAssemblyTests(unittest.TestCase):
    """Preview must retain all 24 independent sockets and stems."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.six = build_six_stem_preview()
        cls.standard = build_standard_preview()

    def test_phase_three_six_stem_preview(self) -> None:
        self.assertEqual(self.six.socket_count, 6)
        self.assertEqual(self.six.virtual_stem_count, 6)
        self.assertEqual(self.six.component_solid_count, 13)
        self.assertGreaterEqual(self.six.minimum_socket_clearance_mm, 0.0)

    def test_standard_has_24_independent_sockets_and_stems(self) -> None:
        preview = self.standard
        self.assertFalse(preview.printable)
        self.assertEqual(preview.socket_count, 24)
        self.assertEqual(preview.virtual_stem_count, 24)
        self.assertEqual(len(set(preview.socket_ids)), 24)
        self.assertEqual(preview.component_solid_count, 54)
        self.assertEqual(preview.metrics.solid_count, 54)

    def test_standard_distributions_and_nonplanar_tops(self) -> None:
        preview = self.standard
        self.assertEqual(preview.height_counts, {"HIGH": 6, "LOW": 8, "STANDARD": 10})
        self.assertEqual(preview.tilt_counts, {20.0: 6, 0.0: 8, 10.0: 8, 30.0: 2})
        self.assertEqual(
            preview.direction_counts,
            {
                0.0: 3,
                45.0: 3,
                90.0: 3,
                135.0: 3,
                180.0: 3,
                225.0: 3,
                270.0: 3,
                315.0: 3,
            },
        )
        self.assertGreaterEqual(len({round(value, 6) for value in preview.top_z_values}), 3)

    def test_crossings_clearance_and_full_preview_size(self) -> None:
        preview = self.standard
        self.assertGreater(preview.projected_stem_crossing_count, 0)
        self.assertGreaterEqual(preview.minimum_socket_clearance_mm, 0.0)
        self.assertGreater(preview.metrics.size_z, 850.0)
        self.assertGreater(preview.metrics.size_x, 210.0)
        self.assertGreater(preview.metrics.size_y, 210.0)


if __name__ == "__main__":
    unittest.main()
