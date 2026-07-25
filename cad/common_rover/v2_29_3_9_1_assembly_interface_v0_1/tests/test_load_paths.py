from __future__ import annotations

import unittest

from load_path_model import (
    HEAVY_COMPONENTS,
    build_load_paths,
    validate_load_paths,
)


class LoadPathTests(unittest.TestCase):
    def test_every_heavy_component_has_primary_metal_path(self):
        paths = build_load_paths()
        self.assertEqual(set(HEAVY_COMPONENTS), {row["component"] for row in paths})
        self.assertEqual([], validate_load_paths(paths))

    def test_bbox_has_independent_rear_support(self):
        bbox = next(
            row for row in build_load_paths() if row["component"] == "BBOX"
        )
        names = [node["name"] for node in bbox["nodes"]]
        self.assertIn("INDEPENDENT REAR SUPPORT BRIDGE", names)
        self.assertIn("CBOX VERTICAL SUPPORT", bbox["independent_of"])

    def test_connector_is_never_structural(self):
        for path in build_load_paths():
            self.assertFalse(path["connector_structural"])

    def test_load_path_sources_are_traceable(self):
        for path in build_load_paths():
            for node in path["nodes"]:
                self.assertTrue(node["authority_source"])
