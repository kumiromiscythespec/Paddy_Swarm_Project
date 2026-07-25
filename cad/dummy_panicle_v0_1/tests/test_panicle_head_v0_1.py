"""Geometry, interference, assembly, and export tests for DR-H01/02/03."""

from __future__ import annotations

import csv
import math
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

CAD_ROOT = Path(__file__).resolve().parents[2]
if str(CAD_ROOT) not in sys.path:
    sys.path.insert(0, str(CAD_ROOT))

from dummy_panicle_v0_1.assemblies.panicle_assembly_preview import build_preview
from dummy_panicle_v0_1.cq_config import PRINT
from dummy_panicle_v0_1.cq_utils import validate_printable_shape
from dummy_panicle_v0_1.generate_dummy_panicle_v0_1 import generate_all
from dummy_panicle_v0_1.interfaces import PANICLE_HEAD, PANICLE_TAB
from dummy_panicle_v0_1.panicle_branch import (
    PanicleBranchParams,
    branch_placements,
    build as build_branch,
    grain_placements,
    validate_params as validate_branch_params,
)
from dummy_panicle_v0_1.panicle_hub import (
    PanicleHubParams,
    build as build_hub,
    interference_clearances,
    params_for_preset,
    slot_angles_degrees,
    validate_params as validate_hub_params,
)
from dummy_panicle_v0_1.panicle_weight_cap import (
    PanicleWeightCapParams,
    build as build_cap,
    retention_interference,
    validate_params as validate_cap_params,
)


class StandardHeadGeometryTests(unittest.TestCase):
    """All default head parts must be single valid A1-safe solids."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.branch = build_branch()
        cls.upright = build_hub(params_for_preset("upright"))
        cls.droop20 = build_hub(params_for_preset("droop20"))
        cls.cap = build_cap()

    def test_standard_builds_are_single_positive_solids(self) -> None:
        for name, shape in (
            ("DR-H01", self.branch),
            ("DR-H02 upright", self.upright),
            ("DR-H02 droop20", self.droop20),
            ("DR-H03", self.cap),
        ):
            with self.subTest(name=name):
                metrics = validate_printable_shape(shape, name)
                self.assertEqual(metrics.solid_count, 1)
                self.assertGreater(metrics.volume, 0.0)
                self.assertLessEqual(metrics.size_x, PRINT.max_x + 1.0e-6)
                self.assertLessEqual(metrics.size_y, PRINT.max_y + 1.0e-6)
                self.assertLessEqual(metrics.size_z, PRINT.max_z + 1.0e-6)

    def test_branch_dimensions_counts_and_connectivity(self) -> None:
        params = PanicleBranchParams()
        metrics = validate_printable_shape(self.branch, "DR-H01")
        bounding_box = self.branch.val().BoundingBox()
        maximum_one_sided_width = max(
            abs(bounding_box.xmin),
            abs(bounding_box.xmax),
        )
        self.assertGreaterEqual(metrics.size_y, 175.0)
        self.assertLessEqual(metrics.size_y, 215.0)
        self.assertGreaterEqual(maximum_one_sided_width, 35.0)
        self.assertLessEqual(maximum_one_sided_width, 50.0)
        self.assertEqual(len(branch_placements(params)), 10)
        self.assertEqual(len(grain_placements(params)), 14)
        self.assertEqual(metrics.solid_count, 1)

    def test_hub_presets_and_four_slots(self) -> None:
        upright_params = params_for_preset("upright")
        droop_params = params_for_preset("droop20")
        self.assertEqual(upright_params.diameter, 30.0)
        self.assertLessEqual(upright_params.diameter, 30.0)
        self.assertEqual(slot_angles_degrees(upright_params), (0.0, 90.0, 180.0, 270.0))
        self.assertEqual(upright_params.droop_angle, 0.0)
        self.assertEqual(droop_params.droop_angle, 20.0)
        self.assertNotAlmostEqual(
            self.upright.val().Volume(),
            self.droop20.val().Volume(),
        )

    def test_cap_pocket_relation(self) -> None:
        params = PanicleWeightCapParams()
        self.assertLess(params.plug_diameter, params.pocket_diameter)
        self.assertGreater(params.retention_bead_diameter, params.pocket_diameter)
        self.assertAlmostEqual(retention_interference(params), 0.2)
        self.assertGreaterEqual(params.min_wall, 1.5)


class HeadParameterValidationTests(unittest.TestCase):
    """Invalid head inputs must fail before geometry is accepted."""

    def test_branch_rejects_under_minimums_and_wrong_tab(self) -> None:
        cases = (
            (replace(PanicleBranchParams(), thickness=0.79), "panel thickness"),
            (replace(PanicleBranchParams(), branch_tip_width=0.79), "branch tip"),
            (replace(PanicleBranchParams(), tab_width=8.1), "tab width"),
        )
        for params, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    validate_branch_params(params)

    def test_hub_rejects_interface_and_angle_errors(self) -> None:
        base = params_for_preset("droop20")
        cases = (
            (replace(base, slot_width=PANICLE_TAB.tab_width), "slot width"),
            (replace(base, slot_thickness=PANICLE_TAB.tab_thickness), "slot thickness"),
            (replace(base, slot_depth=PANICLE_TAB.tab_length + 0.1), "slot depth"),
            (replace(base, stem_hole_diameter=base.stem_od), "stem hole"),
            (replace(base, droop_angle=31.0), "0-30"),
            (replace(base, weight_pocket_diameter=-8.0), "finite and positive"),
        )
        for params, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    validate_hub_params(params)

    def test_panicle_validators_reject_nan_and_infinity(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "finite and positive"):
                    validate_branch_params(
                        replace(PanicleBranchParams(), total_length=value)
                    )

    def test_cap_rejects_negative_interference_and_thin_wall(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive candidate interference"):
            validate_cap_params(
                replace(PanicleWeightCapParams(), retention_bead_diameter=7.9)
            )
        with self.assertRaisesRegex(ValueError, "minimum wall"):
            validate_cap_params(replace(PanicleWeightCapParams(), min_wall=1.4))


class HubInterferenceTests(unittest.TestCase):
    """Analytic conservative clearances must meet the PETG wall target."""

    def test_all_required_clearances_are_at_least_two_mm(self) -> None:
        for preset in ("upright", "droop20"):
            clearances = interference_clearances(params_for_preset(preset))
            for name, value in clearances.items():
                with self.subTest(preset=preset, clearance=name):
                    self.assertGreaterEqual(value, 2.0 - 1.0e-9)

    def test_nominal_24_mm_body_is_rejected_with_numeric_reason(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires 30.0 mm OD"):
            validate_hub_params(replace(PanicleHubParams(), diameter=24.0))


class PreviewAssemblyTests(unittest.TestCase):
    """Panicle-only previews must seat four distinct panels."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.previews = {
            preset: build_preview(preset)
            for preset in ("upright", "droop20")
        }

    def test_upright_and_droop20_previews(self) -> None:
        for preset, preview in self.previews.items():
            with self.subTest(preset=preset):
                self.assertFalse(preview.printable)
                self.assertEqual(preview.branch_count, 4)
                self.assertEqual(
                    preview.branch_angles_degrees,
                    (0.0, 90.0, 180.0, 270.0),
                )
                self.assertEqual(preview.tab_insertion_depth, 12.0)
                self.assertEqual(preview.component_solid_count, 7)
                self.assertAlmostEqual(preview.max_panel_overlap_volume_mm3, 0.0)
                self.assertGreaterEqual(preview.metrics.size_z, 180.0)
                self.assertLessEqual(preview.metrics.size_z, 220.0)
                width = max(preview.metrics.size_x, preview.metrics.size_y)
                self.assertGreaterEqual(width, 80.0)
                self.assertLessEqual(width, 110.0)

    def test_fixed_droop_changes_whole_preview_envelope(self) -> None:
        upright = self.previews["upright"].metrics
        droop = self.previews["droop20"].metrics
        self.assertNotAlmostEqual(upright.size_z, droop.size_z)
        self.assertNotAlmostEqual(upright.size_x, droop.size_x)


class FullExportTests(unittest.TestCase):
    """The integrated generator must honor naming, folders, and manifest rules."""

    def test_material_exports_preview_and_relative_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records, previews = generate_all(root)
            self.assertEqual(len(records), 11)
            self.assertEqual(len(previews), 2)

            for record in records:
                material = record.definition.material
                suffix = f"_{material}"
                self.assertTrue(record.step_path.stem.endswith(suffix))
                self.assertTrue(record.stl_path.stem.endswith(suffix))
                self.assertEqual(record.step_path.parent, root / "step" / material)
                self.assertEqual(record.stl_path.parent, root / "stl" / material)
                self.assertGreater(record.step_path.stat().st_size, 0)
                self.assertGreater(record.stl_path.stat().st_size, 0)

            for preview in previews:
                self.assertEqual(preview.step_path.parent, root / "preview")
                self.assertFalse((root / "preview" / f"{preview.step_path.stem}.stl").exists())

            manifest_path = root / "reports" / "export_manifest.csv"
            with manifest_path.open(newline="", encoding="utf-8-sig") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 24)
            required = {
                "part_id",
                "filename",
                "material",
                "quantity",
                "preset",
                "relative_path",
                "revision",
                "printable",
                "calibration_status",
            }
            self.assertTrue(required.issubset(rows[0]))
            for row in rows:
                path = Path(row["relative_path"])
                self.assertFalse(path.is_absolute())
                self.assertNotIn(str(root), row["relative_path"])
            preview_rows = [row for row in rows if row["material"] == "ASSEMBLY"]
            self.assertEqual(len(preview_rows), 2)
            self.assertTrue(all(row["printable"] == "false" for row in preview_rows))
            self.assertTrue(
                all(row["calibration_status"] == PANICLE_HEAD.calibration_status for row in rows)
            )

            for legacy in (
                "DR-S03_stem_end_plug_paper_tube",
                "DR-C01_cut_zone_marker",
            ):
                self.assertFalse(any(legacy in path.name for path in root.rglob("*")))
            self.assertFalse(any(path.suffix.lower() == ".3mf" for path in root.rglob("*")))


if __name__ == "__main__":
    unittest.main()
