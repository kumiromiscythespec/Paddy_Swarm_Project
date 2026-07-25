from __future__ import annotations

import unittest

from battery_dummy_geometry import build_battery_cassette_dummy
from box_dummy_geometry import (
    build_current_bbox_dummy,
    build_current_cbox_dummy,
)


class BoxDummyTests(unittest.TestCase):
    def _assert_geometry(self, geometry, expected):
        box = geometry.BoundingBox()
        actual = (box.xlen, box.ylen, box.zlen)
        for value, target in zip(actual, expected):
            self.assertAlmostEqual(value, target, places=5)
        self.assertTrue(geometry.shape.isValid())
        self.assertTrue(geometry.marking.marking_verified)
        self.assertEqual(geometry.marking.floating_text_solid_count, 0)
        self.assertFalse(geometry.design_metadata.get("structural_enclosure_claim", False))

    def test_current_cbox_authority_envelope(self):
        self._assert_geometry(build_current_cbox_dummy(), (130.0, 140.0, 105.0))

    def test_current_bbox_authority_envelope(self):
        self._assert_geometry(build_current_bbox_dummy(), (150.0, 220.0, 150.0))

    def test_battery_cassette_authority_envelope(self):
        geometry = build_battery_cassette_dummy()
        self._assert_geometry(geometry, (125.0, 180.0, 120.0))
        self.assertFalse(geometry.design_metadata["real_battery_use"])
        self.assertFalse(geometry.design_metadata["electrical_use"])


if __name__ == "__main__":
    unittest.main()
