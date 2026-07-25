"""Integrated export, manifest, layout, and independence tests."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cadquery as cq

CAD_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(CAD_ROOT) not in sys.path:
    sys.path.insert(0, str(CAD_ROOT))

from harvest_handling_dummy_v0_1.generate_harvest_handling_dummy_v0_1 import (
    PARTS,
)
from harvest_handling_dummy_v0_1.presets.layout_standard_v001 import rows_as_dicts


class IntegratedExportTests(unittest.TestCase):
    """Generator outputs must be classified, relative, and isolated."""

    def test_all_exports_manifest_preview_and_independence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            isolated_cad = temporary_root / "cad"
            isolated_package = isolated_cad / PACKAGE_ROOT.name
            shutil.copytree(
                PACKAGE_ROOT,
                isolated_package,
                ignore=shutil.ignore_patterns("out", "__pycache__", "*.pyc"),
            )
            self.assertFalse((isolated_cad / "dummy_panicle_v0_1").exists())

            root = temporary_root / "generated"
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = str(isolated_cad)
            completed = subprocess.run(
                (
                    sys.executable,
                    str(
                        isolated_package
                        / "generate_harvest_handling_dummy_v0_1.py"
                    ),
                    "--out",
                    str(root),
                ),
                cwd=temporary_root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
            )

            step_files = sorted((root / "step" / "PETG").glob("*.step"))
            stl_files = sorted((root / "stl" / "PETG").glob("*.stl"))
            self.assertEqual(len(step_files), len(PARTS))
            self.assertEqual(len(step_files), 26)
            self.assertEqual(len(stl_files), 26)
            for path in (*step_files, *stl_files):
                self.assertTrue(path.stem.endswith("_PETG"))
                self.assertGreater(path.stat().st_size, 0)
            for path in step_files:
                self.assertEqual(len(cq.importers.importStep(str(path)).solids().vals()), 1)

            preview_path = (
                root / "preview" / "HU-H0-HHD_standard_fixed_root.step"
            )
            self.assertTrue(preview_path.is_file())
            self.assertFalse(preview_path.with_suffix(".stl").exists())
            self.assertEqual(
                len(cq.importers.importStep(str(preview_path)).solids().vals()),
                54,
            )

            with (root / "reports" / "export_manifest.csv").open(
                newline="",
                encoding="utf-8-sig",
            ) as stream:
                manifest = list(csv.DictReader(stream))
            self.assertEqual(len(manifest), 53)
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
                "module",
                "notes",
            }
            self.assertTrue(required.issubset(manifest[0]))
            for row in manifest:
                self.assertFalse(Path(row["relative_path"]).is_absolute())
                self.assertNotIn(str(root), row["relative_path"])
                self.assertNotIn("dummy_panicle", str(row).casefold())
                self.assertNotIn("protected_dummy", str(row).casefold())
            preview_rows = [row for row in manifest if row["material"] == "ASSEMBLY"]
            self.assertEqual(len(preview_rows), 1)
            self.assertEqual(preview_rows[0]["printable"], "false")
            self.assertFalse(
                (root / "reports" / "protected_dummy_panicle_hashes.json").exists()
            )
            self.assertFalse((root / "reports" / "audit").exists())

            self.assertFalse(any(root.rglob("*.3mf")))
            self.assertFalse(any(path.is_file() for path in (root / "step").glob("*.step")))
            self.assertFalse(any(path.is_file() for path in (root / "stl").glob("*.stl")))

            with (root / "reports" / "layout_standard_v001.csv").open(
                newline="",
                encoding="utf-8-sig",
            ) as stream:
                csv_rows = list(csv.DictReader(stream))
            json_rows = json.loads(
                (root / "reports" / "layout_standard_v001.json").read_text(
                    encoding="utf-8"
                )
            )["rows"]
            self.assertEqual(len(csv_rows), 24)
            self.assertEqual(json_rows, rows_as_dicts())
            for expected, actual in zip(rows_as_dicts(), csv_rows):
                self.assertEqual(actual["socket_id"], expected["socket_id"])
                self.assertAlmostEqual(float(actual["x_mm"]), expected["x_mm"])
                self.assertAlmostEqual(float(actual["y_mm"]), expected["y_mm"])


if __name__ == "__main__":
    unittest.main()
