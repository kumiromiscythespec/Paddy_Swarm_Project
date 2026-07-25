from __future__ import annotations

import json
import unittest

from part_number_registry import PARTS
from tests._artifact import generated_artifact
from validate_dummy_kit import validate_artifact


class ExportedMeshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = generated_artifact()

    def test_all_required_stls_are_finite_and_valid(self):
        audit = json.loads(
            (self.artifact / "stl_mesh_audit.json").read_text(encoding="utf-8")
        )
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(len(audit["records"]), len(PARTS))
        for record in audit["records"]:
            self.assertTrue(record["finite_vertices"])
            self.assertGreater(record["triangle_count"], 0)
            self.assertEqual(record["zero_area_triangle_count"], 0)

    def test_all_exported_parts_are_marked_and_a1_printable(self):
        markings = json.loads(
            (self.artifact / "printed_part_number_audit.json").read_text(
                encoding="utf-8"
            )
        )
        a1 = json.loads(
            (self.artifact / "a1_printability_audit.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(markings["physically_marked_part_count"], len(PARTS))
        self.assertEqual(markings["floating_text_solid_count"], 0)
        self.assertTrue(markings["all_geometry_markings_verified"])
        self.assertEqual(a1["A1_PRINTABILITY"], "PASS")
        self.assertFalse(a1["all_parts_one_plate_recommended"])

    def test_generated_kit_validates_before_replay_report(self):
        report = validate_artifact(
            self.artifact,
            require_determinism=False,
        )
        self.assertEqual(report["status"], "PASS_WITH_HOLD", report["blockers"])
        self.assertEqual(report["FULL_DUMMY_PART_SET_COMPLETE"], "PASS")
        self.assertEqual(report["REPOSITORY_GENERATED_OUTPUT_STATUS"], "CLEAN")


if __name__ == "__main__":
    unittest.main()
