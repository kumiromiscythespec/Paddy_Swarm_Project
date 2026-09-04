"""Contract test for CBOX transverse cross-saddle V001."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_cbox_transverse_cross_saddle_bbox_alignment_v001.py"
spec = importlib.util.spec_from_file_location("cbox_cross_saddle_v001", BUILDER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def main() -> int:
    validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
    parameters = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
    checks = dict(validation["checks"])
    extras = {
        "all_builder_checks": validation["check_count"] == validation["pass_count"],
        "exact_paths": sorted(
            item.relative_to(LANE).as_posix()
            for item in LANE.rglob("*") if item.is_file()
        ) == module.EXPECTED,
        "physical_lane": parameters["physical_authority"]["rail_center_range_mm"] == [188.0, 190.0],
        "no_absolute_y_promotion": parameters["local_coordinate"]["classification"].endswith("NOT_ABSOLUTE_VEHICLE_Y_AUTHORITY"),
        "cbox_long_y": parameters["cbox"]["long_axis"] == "Y",
        "variant_a": parameters["saddle"]["architecture"] == "VARIANT_A_DUAL_INDEPENDENT_RAIL_SADDLES",
        "no_bbox_load": not parameters["clearance"]["cbox_primary_load_to_bbox_lid"],
        "bbox_copy_exact": module.sha(LANE / module.STEPS[5]) == module.sha(module.BBOX_SOURCE),
        "front_copy_exact": module.sha(LANE / module.STEPS[8]) == module.sha(module.FRONT_SOURCE),
        "printable_pair": len(module.STLS) == 2,
        "step_count": len(module.STEPS) == 18,
        "svg_count": len(module.SVGS) == 6,
        "holds_retained": "CLUTCH_FINAL_GEOMETRY_PENDING" in parameters["holds"],
        "no_one_piece_base": parameters["printability"]["one_piece_240x246_base"] == "HOLD_NOT_GENERATED",
        "staged_zero": module.guard(True)["staged_count"] == 0,
    }
    failed = [name for name, value in {**checks, **extras}.items() if not value]
    if failed:
        raise AssertionError("FAIL: " + ", ".join(failed))
    total = len(checks) + len(extras)
    for index, name in enumerate(sorted(extras), 1):
        print(f"extra_{index:03d}_{name}: PASS")
    print(f"TOTAL: {total}/{total} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
