from __future__ import annotations

from copy import deepcopy
import unittest
import xml.etree.ElementTree as ET

from authority_adapter import canonical_json, load_context
from svg_renderer import render_all
from validate_interfaces import build_complete_manifest


class DeterminismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_context(validate_seed_geometry=False)
        cls.manifest = build_complete_manifest(cls.context)

    def test_manifest_replay_is_byte_identical(self):
        self.assertEqual(
            canonical_json(self.manifest),
            canonical_json(deepcopy(self.manifest)),
        )

    def test_svg_replay_is_byte_identical_and_parseable(self):
        first = render_all(
            self.manifest,
            self.manifest["load_paths"],
            self.manifest["assembly_sequence"],
            self.context,
        )
        replay = render_all(
            self.manifest,
            self.manifest["load_paths"],
            self.manifest["assembly_sequence"],
            self.context,
        )
        self.assertEqual(first, replay)
        for payload in first.values():
            ET.fromstring(payload)
            self.assertNotIn(b"\r", payload)

    def test_every_svg_carries_orientation_and_hold_labels(self):
        rendered = render_all(
            self.manifest,
            self.manifest["load_paths"],
            self.manifest["assembly_sequence"],
            self.context,
        )
        for name, payload in rendered.items():
            text = payload.decode("utf-8")
            for label in (
                "FRONT",
                "REAR",
                "LEFT",
                "RIGHT",
                "TOP",
                "BOTTOM",
                "NOT MANUFACTURING APPROVED",
            ):
                self.assertIn(label, text, msg=f"{name}: {label}")
