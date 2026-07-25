from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from coupon_geometry import (
    COMMON_MARKING_HANDLER,
    COUPON_BUILDERS,
    PART_NUMBERS,
    PIN_BORE_CANDIDATES_MM,
    SADDLE_CLEARANCE_CANDIDATES_MM,
    SLIDE_CLEARANCE_CANDIDATES_MM,
    THUMB_LATCH_GAP_CANDIDATES_MM,
    THUMB_LATCH_THICKNESS_CANDIDATES_MM,
    coupon_manifest_rows,
    export_coupons,
    replay_coupon_exports,
)


class CouponGeometryTests(unittest.TestCase):
    def test_exactly_five_fit_test_only_coupon_records(self):
        rows = coupon_manifest_rows()
        self.assertEqual(5, len(rows))
        self.assertEqual(5, len(COUPON_BUILDERS))
        for row in rows:
            self.assertIn("FIT TEST ONLY", row["classification"])
            self.assertIn("100% scale", row["printer"])
            self.assertEqual(row["coupon_id"], row["part_number"])
            self.assertEqual("ENGRAVED", row["physical_marking"])
            self.assertEqual("true", row["marking_verified"])

    def test_multiple_clearance_and_latch_candidates(self):
        self.assertEqual(
            (0.20, 0.30, 0.40, 0.50),
            SADDLE_CLEARANCE_CANDIDATES_MM,
        )
        self.assertEqual(
            (0.20, 0.30, 0.40, 0.50),
            SLIDE_CLEARANCE_CANDIDATES_MM,
        )
        self.assertEqual(
            (6.10, 6.20, 6.30, 6.40),
            PIN_BORE_CANDIDATES_MM,
        )
        self.assertEqual(4, len(THUMB_LATCH_THICKNESS_CANDIDATES_MM))
        self.assertEqual(4, len(THUMB_LATCH_GAP_CANDIDATES_MM))

    def test_coupon_geometry_fits_bambu_a1_xy_envelope(self):
        for coupon_id, _filename, builder in COUPON_BUILDERS:
            geometry = builder()
            box = geometry.BoundingBox()
            self.assertLessEqual(box.xlen, 256.0, msg=coupon_id)
            self.assertLessEqual(box.ylen, 256.0, msg=coupon_id)
            self.assertGreater(box.zlen, 0.0, msg=coupon_id)
            self.assertLessEqual(box.zlen, 25.0, msg=coupon_id)
            self.assertEqual(coupon_id, geometry.marking.part_number)
            self.assertEqual(
                coupon_id, geometry.marking.geometry_part_number
            )
            self.assertEqual(
                COMMON_MARKING_HANDLER,
                geometry.marking.common_marking_handler,
            )
            self.assertTrue(
                geometry.marking.common_marking_handler_invoked
            )
            self.assertTrue(geometry.marking.marking_verified)
            self.assertEqual(
                geometry.marking.glyph_solid_count,
                geometry.marking.intersecting_glyph_solid_count,
            )
            self.assertEqual(
                0, geometry.marking.floating_part_number_solid_count
            )
            self.assertGreater(geometry.marking.engraved_volume_mm3, 0.0)

    def test_five_unique_source_authoritative_part_numbers(self):
        self.assertEqual(5, len(PART_NUMBERS))
        self.assertEqual(5, len(set(PART_NUMBERS)))
        self.assertTrue(all(number.strip() for number in PART_NUMBERS))

    def test_coupon_export_replay_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "first"
            export_coupons(output)
            replay = replay_coupon_exports(output)
        self.assertEqual("PASS", replay["status"])
        self.assertTrue(all(row["match"] for row in replay["files"]))
