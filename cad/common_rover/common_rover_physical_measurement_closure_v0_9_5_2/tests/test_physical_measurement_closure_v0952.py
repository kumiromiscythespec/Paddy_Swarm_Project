#!/usr/bin/env python3
"""Contract tests for the v0.9.5.2 physical measurement closure record."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_physical_measurement_closure_v0952.py"
spec = importlib.util.spec_from_file_location("measurement_v0952", BUILDER)
assert spec and spec.loader
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads((LANE / "measurement_ledger.json").read_text(encoding="utf-8"))
        cls.rows = {row["id"]: row for row in cls.ledger["records"]}
        cls.cbox = json.loads((LANE / "cbox_physical_record.json").read_text(encoding="utf-8"))
        cls.bbox = json.loads((LANE / "bbox_physical_record.json").read_text(encoding="utf-8"))
        cls.term = json.loads((LANE / "terminal_physical_record.json").read_text(encoding="utf-8"))
        cls.h25 = json.loads((LANE / "h25a1_physical_record.json").read_text(encoding="utf-8"))
        cls.drive = json.loads((LANE / "drive_belt_measurement_record.json").read_text(encoding="utf-8"))
        cls.valid = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))

    def test_001_repository_guard(self):
        self.assertEqual(b.repository_guard(True)["status"], "PASS")

    def test_002_authority_hashes(self):
        self.assertEqual(b.authority_audit()["hashes"], b.AUTHORITY_HASHES)

    def test_003_parent_trees(self):
        self.assertEqual(b.parent_audit()["status"], "PASS")

    def test_004_v0951_found(self):
        self.assertEqual(b.parent_audit()["v0.9.5.1_existence"], "FOUND_READ_ONLY_AUDIT_PASS")

    def test_005_unique_ids(self):
        ids = [row["id"] for row in self.ledger["records"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_006_units_explicit(self):
        self.assertTrue(all(row["unit"] for row in self.ledger["records"]))

    def test_007_classification_vocabulary(self):
        allowed = set(self.ledger["classification_vocabulary"])
        self.assertTrue(all(row["classification"] in allowed for row in self.ledger["records"]))

    def test_008_cbox_print(self):
        self.assertEqual(self.rows["CBOX-PRINT-BODY"]["value"], "COMPLETED")
        self.assertEqual(self.rows["CBOX-PRINT-LID"]["value"], "COMPLETED")
        self.assertEqual(self.rows["CBOX-PRINT-PLATE02"]["value"], "COMPLETED")

    def test_009_cbox_lid_gap(self):
        self.assertEqual(self.rows["CBOX-LID-GAP"]["value"], 0.4)
        self.assertEqual(self.rows["CBOX-SEAL-FLATNESS"]["classification"], "HOLD")

    def test_010_cbox_raw_heights(self):
        values = [self.rows[f"CBOX-HEIGHT-{x}"]["value"] for x in ("A1", "A2", "A3", "B1", "B2", "B3")]
        self.assertEqual(values, [39.8, 40.1, 40.0, 40.0, 40.3, 39.5])

    def test_011_cbox_statistics(self):
        self.assertEqual(self.rows["CBOX-HEIGHT-MEAN"]["value"], 39.95)
        self.assertEqual(self.rows["CBOX-HEIGHT-RANGE"]["value"], 0.8)
        self.assertEqual(self.rows["CBOX-HEIGHT-MEAN-ERROR"]["value"], -0.05)

    def test_012_cbox_waterproof_not_tested(self):
        self.assertEqual(self.rows["CBOX-WATERPROOF"]["value"], "NOT_TESTED")

    def test_013_bbox_ring_and_pad(self):
        self.assertEqual(self.rows["BBOX-RING-PARALLEL"]["value"], "YES")
        self.assertEqual(self.rows["BBOX-RING-M4"]["value"], "YES")
        self.assertEqual(self.rows["BBOX-PAD-M3"]["value"], "YES")
        self.assertEqual(self.rows["BBOX-BODY-PRINT"]["value"], "COMPLETED")

    def test_014_battery_authority(self):
        self.assertEqual([self.rows[f"BAT-DIM-{i}"]["value"] for i in (1, 2, 3)], [150.9, 99.4, 92.5])
        self.assertEqual(self.rows["BAT-MASS"]["value"], 1.2)

    def test_015_lateral_measurements(self):
        self.assertEqual((self.rows["BBOX-LATERAL-LEFT"]["value"], self.rows["BBOX-LATERAL-RIGHT"]["value"]), (20.0, 25.0))
        self.assertEqual(self.rows["BBOX-LATERAL-TOTAL"]["value"], 45.0)
        self.assertEqual(self.rows["BBOX-LATERAL-OFFSET"]["status"], "DERIVED_REFERENCE_ONLY")

    def test_016_terminal_orientation_history(self):
        self.assertEqual(self.rows["TERM-INITIAL-IDLER-CLEAR"]["value"], 4.0)
        self.assertEqual(self.rows["TERM-INITIAL-IDLER-CLEAR"]["status"], "SUPERSEDED")
        self.assertEqual(self.rows["TERM-REARDOWN-IDLER-CLEAR"]["value"], 10.0)

    def test_017_image_report_wording(self):
        for rid in ("TERM-REAR-WALL-CLEAR", "BBOX-BODY-H-PHYS", "BBOX-BOTTOM-TERM-EXTREME"):
            self.assertEqual(self.rows[rid]["classification"], "IMAGE_REPORTED_MEASUREMENT")
        forbidden = "CODEX_" + "MEASURED_FROM_IMAGE"
        self.assertTrue(all(row["source"] != forbidden for row in self.ledger["records"]))

    def test_018_bbox_body_physical_vs_cad(self):
        self.assertEqual((self.rows["BBOX-BODY-H-PHYS"]["value"], self.rows["BBOX-BODY-H-CAD"]["value"]), (97.0, 97.5))

    def test_019_terminal_dimensions(self):
        self.assertEqual((self.rows["BAT-TAB-WIDTH"]["value"], self.rows["BAT-TAB-THICK"]["value"]), (6.3, 0.7))
        self.assertEqual(self.rows["FEMALE-OUTER-W"]["value"], 10.6)

    def test_020_terminal_protrusion(self):
        self.assertEqual(self.rows["BAT-BOTTOM-TERM-TOP"]["value"], 99.4)
        self.assertTrue(math.isclose(self.rows["BAT-TERM-PROTRUSION"]["value"], 99.4 - 92.5, abs_tol=1e-12))

    def test_021_terminal_pair(self):
        self.assertEqual((self.rows["TERM-PAIR-OUTER"]["value"], self.rows["TERM-PAIR-INNER"]["value"]), (29.5, 20.0))

    def test_022_harness_holds(self):
        holds = [row for row in self.ledger["records"] if row["id"].startswith("HARNESS-HOLD-")]
        self.assertEqual(len(holds), 11)
        self.assertTrue(all(row["classification"] == "HOLD" for row in holds))

    def test_023_frame_values(self):
        self.assertEqual(self.rows["FRAME-HEIGHT"]["value"], 150.0)
        self.assertEqual(self.rows["FRAME-INSERT-DATUM"]["value"], 108.0)
        self.assertEqual(self.rows["FRAME-ALT-DATUM"]["value"], 90.7)

    def test_024_h25_coupon_not_selected(self):
        for code in ("W90", "W92", "W94", "R41", "R42", "R43"):
            self.assertEqual(self.rows[f"H25-CAND-{code}"]["status"], "NOT_SELECTED")
        self.assertEqual(self.rows["H25-FINAL-TOL"]["classification"], "HOLD")

    def test_025_h25_hand_rotation(self):
        self.assertEqual(self.rows["H25-HAND-ROT"]["value"], "NONE_REPORTED")

    def test_026_h25_torque_reference(self):
        expected = 1.2 * 9.80665 * 0.070
        self.assertTrue(math.isclose(self.rows["H25-TORQUE-CALC"]["value"], expected, abs_tol=1e-12))
        self.assertEqual(self.rows["H25-STATIC-INITIAL"]["value"], "NONE_REPORTED")
        self.assertEqual(self.rows["H25-CREEP"]["status"], "PENDING")

    def test_027_drive_raw_measurements(self):
        self.assertEqual(self.rows["DRIVE-CENTER"]["value"], 180.0)
        self.assertEqual(self.rows["DRIVE-STRING"]["value"], 583.0)

    def test_028_drive_candidates(self):
        self.assertEqual((self.rows["DRIVE-113-TEETH"]["value"], self.rows["DRIVE-113-LENGTH"]["value"]), (113, 565.0))
        self.assertEqual((self.rows["DRIVE-114-TEETH"]["value"], self.rows["DRIVE-114-LENGTH"]["value"]), (114, 570.0))
        self.assertEqual((self.rows["DRIVE-112-TEETH"]["value"], self.rows["DRIVE-112-LENGTH"]["value"]), (112, 560.0))

    def test_029_commercial_hold(self):
        self.assertEqual(self.rows["DRIVE-COMMERCIAL"]["value"], "HOLD")

    def test_030_powered_field_not_approved(self):
        self.assertEqual(self.rows["POWERED"]["value"], "NOT_APPROVED")
        self.assertEqual(self.rows["FIELD"]["value"], "NOT_APPROVED")

    def test_031_no_cad_pass(self):
        self.assertEqual(self.valid["cad_pass"], "NOT_EVALUATED_NO_DESIGN_CHANGE")
        self.assertEqual(self.valid["design_modification"], "NONE")

    def test_032_no_cad_artifacts(self):
        forbidden = {".step", ".stp", ".stl", ".dxf", ".3mf", ".gcode", ".pyc"}
        self.assertFalse([p for p in LANE.rglob("*") if p.is_file() and p.suffix.lower() in forbidden])

    def test_033_json_valid(self):
        self.assertEqual(len(b.JSONS), 7)
        for rel in b.JSONS:
            self.assertIsNotNone(json.loads((LANE / rel).read_text(encoding="utf-8")))

    def test_034_numeric_exclusions_present(self):
        self.assertGreaterEqual(len(self.ledger["prompt_numeric_exclusions"]), 10)

    def test_035_manifest_commit_paths_hashes(self):
        self.assertEqual(b.verify_files()["status"], "PASS")

    def test_036_authority_bytes_final(self):
        for rel, digest in b.AUTHORITY_HASHES.items():
            self.assertEqual(hashlib.sha256((b.REPO_ROOT / rel).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
