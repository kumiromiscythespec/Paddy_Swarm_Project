"""Automated geometry and interface tests for dummy panicle head v0.1."""

from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

CAD_ROOT = Path(__file__).resolve().parents[2]
if str(CAD_ROOT) not in sys.path:
    sys.path.insert(0, str(CAD_ROOT))

from dummy_panicle_v0_1.cq_config import PRINT
from dummy_panicle_v0_1.cq_utils import (
    ShapeMetrics,
    export_step,
    export_stl,
    require_positive,
    validate_printable_shape,
    validate_step_round_trip,
)
from dummy_panicle_v0_1.cutting_cartridge_holder import (
    CuttingCartridgeHolderParams,
    build as build_holder,
    build_tube_marking_gauge,
)
from dummy_panicle_v0_1.generate_dummy_panicle_v0_1 import (
    PARTS,
    GeneratedPart,
    PartDefinition,
    _write_manifest_csv,
)
from dummy_panicle_v0_1.interfaces import (
    CARTRIDGE,
    M4_CLEARANCE_DIAMETER,
    PANICLE_TAB,
    STEM,
)
from dummy_panicle_v0_1.panicle_slot_coupon import (
    PanicleSlotCouponParams,
    validate_params as validate_slot_params,
)
from dummy_panicle_v0_1.root_socket import (
    RootSocketParams,
    build as build_root_socket,
    clamp_screw_center,
    mount_hole_centers,
    validate_params as validate_root_params,
)
from dummy_panicle_v0_1.stem_clearance_coupon import (
    StemClearanceCouponParams,
    build as build_stem_coupon,
    validate_params as validate_stem_coupon_params,
)
from dummy_panicle_v0_1.stem_end_plug import (
    build as build_stem_end_plug,
    params_for_preset,
)


class DefaultBuildTests(unittest.TestCase):
    """Default parts must be printable valid solids."""

    def test_every_generated_part_builds_as_one_positive_solid(self) -> None:
        for part in PARTS:
            with self.subTest(part=part.filename_stem):
                metrics = validate_printable_shape(part.builder(), part.filename_stem)
                self.assertEqual(metrics.solid_count, 1)
                self.assertGreater(metrics.volume, 0.0)

    def test_required_primary_build_functions(self) -> None:
        shapes = (
            build_stem_coupon(),
            build_root_socket(),
            build_stem_end_plug(),
            build_holder(),
            build_tube_marking_gauge(),
        )
        self.assertEqual(len(shapes), 5)


class ParameterValidationTests(unittest.TestCase):
    """Required invalid parameter cases must fail clearly."""

    def test_negative_stem_diameter_fails(self) -> None:
        params = replace(RootSocketParams(), stem_nominal_diameter=-4.0)
        with self.assertRaisesRegex(ValueError, "positive"):
            validate_root_params(params)

    def test_receiver_not_larger_than_stem_fails(self) -> None:
        params = replace(
            RootSocketParams(),
            stem_hole_diameter=STEM.nominal_diameter,
        )
        with self.assertRaisesRegex(ValueError, "opening > insert"):
            validate_root_params(params)

    def test_petg_wall_under_two_mm_fails(self) -> None:
        params = replace(RootSocketParams(), socket_outer_diameter=8.0)
        with self.assertRaisesRegex(ValueError, "radial wall"):
            validate_root_params(params)

    def test_short_stem_insertion_fails(self) -> None:
        params = replace(RootSocketParams(), stem_insertion_depth=19.0)
        with self.assertRaisesRegex(ValueError, "insertion depth"):
            validate_root_params(params)

    def test_invalid_stem_coupon_clearance_fails(self) -> None:
        params = replace(
            StemClearanceCouponParams(),
            hole_diameters=(4.0, 4.2, 4.3, 4.4, 4.5),
        )
        with self.assertRaisesRegex(ValueError, "opening > insert"):
            validate_stem_coupon_params(params)

    def test_invalid_tab_slot_clearance_fails(self) -> None:
        params = replace(
            PanicleSlotCouponParams(),
            slot_sizes=((8.0, 2.4), (8.4, 2.4), (8.6, 2.4)),
        )
        with self.assertRaisesRegex(ValueError, "opening > insert"):
            validate_slot_params(params)

    def test_nan_dimension_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            require_positive(candidate=float("nan"))

    def test_infinite_dimension_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            require_positive(candidate=float("inf"))

    def test_unverified_tube_preset_has_calibration_name(self) -> None:
        params = params_for_preset("tube_id_3p6_calibration")
        self.assertEqual(params.material_core_diameter, 3.6)
        with self.assertRaisesRegex(ValueError, "unknown"):
            params_for_preset("paper_tube")


class BuildEnvelopeTests(unittest.TestCase):
    """Every artifact must stay inside the conservative A1 envelope."""

    def test_all_bounding_boxes_fit_a1(self) -> None:
        for part in PARTS:
            with self.subTest(part=part.filename_stem):
                metrics = validate_printable_shape(part.builder(), part.filename_stem)
                self.assertLessEqual(metrics.size_x, PRINT.max_x + 1.0e-6)
                self.assertLessEqual(metrics.size_y, PRINT.max_y + 1.0e-6)
                self.assertLessEqual(metrics.size_z, PRINT.max_z + 1.0e-6)


class InterfaceTests(unittest.TestCase):
    """Cross-part mechanical interface dimensions must remain consistent."""

    def test_stem_shaft_receiver_relation(self) -> None:
        self.assertEqual(STEM.nominal_diameter, 4.0)
        self.assertEqual(STEM.receiver_diameter, 4.3)
        self.assertAlmostEqual(STEM.diametral_clearance, 0.30)

    def test_tab_slot_relation(self) -> None:
        self.assertGreater(PANICLE_TAB.slot_width, PANICLE_TAB.tab_width)
        self.assertGreater(PANICLE_TAB.slot_thickness, PANICLE_TAB.tab_thickness)
        self.assertLessEqual(PANICLE_TAB.insertion_depth, PANICLE_TAB.tab_length)

    def test_cartridge_holder_relation_and_safe_zone(self) -> None:
        params = CuttingCartridgeHolderParams()
        self.assertGreater(params.cartridge_bore_diameter, CARTRIDGE.tube_outer_diameter)
        self.assertEqual(params.cartridge_insertion_depth, 15.0)
        self.assertEqual(CARTRIDGE.holder_face_safety_distance, 30.0)
        self.assertEqual(CARTRIDGE.derived_cuttable_length, 80.0)

    def test_corrected_cartridge_length_equation(self) -> None:
        expected_length = (
            2.0 * CARTRIDGE.holder_insertion_depth
            + 2.0 * CARTRIDGE.holder_face_safety_distance
            + CARTRIDGE.cuttable_length
        )
        self.assertEqual(expected_length, 170.0)
        self.assertEqual(CARTRIDGE.cartridge_length, expected_length)
        self.assertEqual(CARTRIDGE.required_cartridge_length, expected_length)

    def test_m3_clearance_has_lug_wall(self) -> None:
        params = RootSocketParams()
        center_x, center_z = clamp_screw_center(params)
        radius = 0.5 * params.clamp_screw_diameter
        self.assertGreaterEqual(
            center_x - radius - params.clamp_lug_x_start,
            PRINT.petg_min_wall,
        )
        self.assertGreaterEqual(
            params.clamp_lug_x_end - center_x - radius,
            PRINT.petg_min_wall,
        )
        self.assertGreater(
            center_z,
            params.base_height,
        )

    def test_m4_holes_have_base_edge_wall(self) -> None:
        params = RootSocketParams()
        radius = 0.5 * M4_CLEARANCE_DIAMETER
        for center_x, center_y in mount_hole_centers(params):
            x_wall = 0.5 * params.base_width - abs(center_x) - radius
            y_wall = 0.5 * params.base_length - abs(center_y) - radius
            self.assertGreaterEqual(x_wall, PRINT.petg_min_wall)
            self.assertGreaterEqual(y_wall, PRINT.petg_min_wall)


class ExportTests(unittest.TestCase):
    """Representative STEP/STL export must create and round-trip real files."""

    def test_export_creates_missing_directories_and_nonempty_files(self) -> None:
        shape = build_stem_end_plug(params_for_preset("tube_id_3p6_calibration"))
        with tempfile.TemporaryDirectory() as temporary:
            nested = Path(temporary) / "new" / "nested"
            step_path = export_step(shape, nested / "DR-S03.step")
            stl_path = export_stl(shape, nested / "DR-S03.stl")
            self.assertTrue(step_path.is_file())
            self.assertTrue(stl_path.is_file())
            self.assertGreater(step_path.stat().st_size, 0)
            self.assertGreater(stl_path.stat().st_size, 0)
            round_trip = validate_step_round_trip(step_path)
            self.assertEqual(round_trip.solid_count, 1)
            self.assertGreater(round_trip.volume, 0.0)

    def test_manifest_uses_output_root_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            step_path = root / "step" / "sample.step"
            stl_path = root / "stl" / "sample.stl"
            step_path.parent.mkdir(parents=True)
            stl_path.parent.mkdir(parents=True)
            step_path.write_bytes(b"step")
            stl_path.write_bytes(b"stl")
            definition = PartDefinition(
                part_id="SAMPLE",
                filename_stem="sample_PETG",
                description="sample",
                material="PETG",
                quantity=1,
                preset="sample",
                printable=True,
                calibration_status="CALIBRATION_PENDING",
                builder=build_stem_end_plug,
            )
            record = GeneratedPart(
                definition,
                ShapeMetrics(1.0, 1.0, 1.0, 1, 1.0),
                0.00127,
                step_path,
                stl_path,
            )
            manifest_path = root / "reports" / "export_manifest.csv"
            _write_manifest_csv([record], [], manifest_path, root)
            manifest = manifest_path.read_text(encoding="utf-8-sig")
            self.assertIn("step/sample.step", manifest)
            self.assertIn("stl/sample.stl", manifest)
            self.assertNotIn(root.as_posix(), manifest)


if __name__ == "__main__":
    unittest.main()
