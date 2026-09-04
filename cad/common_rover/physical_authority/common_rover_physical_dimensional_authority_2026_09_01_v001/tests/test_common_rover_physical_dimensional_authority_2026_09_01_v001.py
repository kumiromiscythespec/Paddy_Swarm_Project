"""Contract tests for the 2026-09-01 documentation-only physical authority."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_common_rover_physical_dimensional_authority_2026_09_01_v001.py"
spec = importlib.util.spec_from_file_location("physical_authority_v001", BUILDER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def main() -> int:
    report = module.verify()
    repro = module.reproducibility()
    p = json.loads((LANE / "physical_dimensions_2026_09_01.json").read_text(encoding="utf-8"))
    q = json.loads((LANE / "misumi_shaft_key_procurement_update_2026_09_01.json").read_text(encoding="utf-8"))
    extras = {
        "verify_all": report["check_count"] == report["pass_count"],
        "repro_15": repro["file_count"] == repro["byte_identical_count"] == 15,
        "outside_preserved": report["repository"]["outside_untracked"]["count"] == 4073,
        "staged_zero": report["repository"]["staged_count"] == 0,
        "tracked_dirty_exact": report["repository"]["tracked_dirty"] == module.EXPECTED_DIRTY,
        "rail_midpoint_not_axis": p["frame_y"]["rail_center_span_midpoint"]["classification"] == "DERIVED_MIDPOINT",
        "bbox_257_not_current": p["bbox"]["lid_highest_z"]["value"] == 254.0,
        "clearance_not_dynamic": p["release_limits"]["dynamic_crawler_clearance"]["classification"] == "PHYSICAL_PENDING",
        "shaft_order_partial": q["shaft"]["future_exact_order_length"]["classification"] == "PROCUREMENT_HOLD",
        "key_nominal_pending": q["key"]["purchase_nominal_product"]["classification"] == "PROCUREMENT_EVIDENCE_PENDING",
        "torque_path": q["torque_path"]["classification"] == "CURRENT_AUTHORITY_UNCHANGED",
        "path_count": len(report["repository"]["lane_files"]) == 15,
        "no_cad_suffixes": not any(
            Path(name).suffix.lower() in {".step", ".stp", ".stl", ".svg", ".dxf"}
            for name in report["repository"]["lane_files"]
        ),
    }
    failed = [name for name, value in extras.items() if not value]
    if failed:
        raise AssertionError("FAIL: " + ", ".join(failed))
    total = report["check_count"] + len(extras)
    for index, name in enumerate(sorted(extras), 1):
        print(f"extra_{index:03d}_{name}: PASS")
    print(f"TOTAL: {total}/{total} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
