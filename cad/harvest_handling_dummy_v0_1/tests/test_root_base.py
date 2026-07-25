"""Base-module and workbench-mount geometry tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import cadquery as cq

CAD_ROOT = Path(__file__).resolve().parents[2]
if str(CAD_ROOT) not in sys.path:
    sys.path.insert(0, str(CAD_ROOT))

from harvest_handling_dummy_v0_1.cq_utils import measure_shape, shape_solids, validate_print_bounds
from harvest_handling_dummy_v0_1.parameters import ROOT_BASE, ROOT_MOUNT
from harvest_handling_dummy_v0_1.presets.layout_standard_v001 import entries_for_module
from harvest_handling_dummy_v0_1.root_base import (
    build as build_base,
    minimum_m4_socket_wall,
    socket_edge_margin,
)
from harvest_handling_dummy_v0_1.root_base_mount import (
    build as build_mount,
    m6_hole_centers,
    minimum_m6_m4_wall,
)


class RootBaseTests(unittest.TestCase):
    """Each quadrant module must carry six isolated receivers safely."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bases = {module: build_base(module) for module in "ABCD"}

    def test_four_modules_build_as_single_a1_safe_solids(self) -> None:
        for module, shape in self.bases.items():
            with self.subTest(module=module):
                metrics = validate_print_bounds(shape, f"BASE-{module}")
                self.assertEqual(metrics.solid_count, 1)
                self.assertGreater(metrics.volume_mm3, 0.0)
                self.assertAlmostEqual(metrics.size_x, 105.0)
                self.assertAlmostEqual(metrics.size_y, 105.0)
                self.assertAlmostEqual(metrics.size_z, 18.0)

    def test_six_receivers_per_module_and_twenty_four_total(self) -> None:
        counts = [len(entries_for_module(module)) for module in "ABCD"]
        self.assertEqual(counts, [6, 6, 6, 6])
        self.assertEqual(sum(counts), 24)

    def test_receiver_edges_and_m4_walls(self) -> None:
        for module in "ABCD":
            with self.subTest(module=module):
                self.assertGreaterEqual(
                    min(socket_edge_margin(entry) for entry in entries_for_module(module)),
                    ROOT_BASE.min_socket_edge_margin,
                )
                self.assertGreaterEqual(
                    minimum_m4_socket_wall(module),
                    ROOT_BASE.petg_min_wall,
                )


class RootMountTests(unittest.TestCase):
    """Two mount halves must retain four M6 and sixteen M4 positions."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.left = build_mount("L")
        cls.right = build_mount("R")

    def test_mount_halves_are_single_a1_safe_solids(self) -> None:
        for side, shape in (("L", self.left), ("R", self.right)):
            with self.subTest(side=side):
                metrics = validate_print_bounds(shape, f"MOUNT-{side}")
                self.assertEqual(metrics.solid_count, 1)
                self.assertGreater(metrics.volume_mm3, 0.0)
                self.assertLessEqual(metrics.size_x, 110.0)
                self.assertAlmostEqual(metrics.size_y, 210.0)
                self.assertLessEqual(metrics.size_z, 9.0)

    def test_four_m6_holes_and_safe_m4_separation(self) -> None:
        self.assertEqual(len(m6_hole_centers("L")) + len(m6_hole_centers("R")), 4)
        self.assertGreaterEqual(minimum_m6_m4_wall("L"), ROOT_MOUNT.petg_min_wall)
        self.assertGreaterEqual(minimum_m6_m4_wall("R"), ROOT_MOUNT.petg_min_wall)

    def test_joined_mount_is_approximately_210_square(self) -> None:
        compound = cq.Workplane("XY").newObject(
            [
                cq.Compound.makeCompound(
                    [*shape_solids(self.left), *shape_solids(self.right)]
                )
            ]
        )
        metrics = measure_shape(compound)
        self.assertAlmostEqual(metrics.size_x, 210.0)
        self.assertAlmostEqual(metrics.size_y, 210.0)
        self.assertEqual(metrics.solid_count, 2)


if __name__ == "__main__":
    unittest.main()
