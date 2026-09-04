from __future__ import annotations

import importlib
from pathlib import Path

from common.cq_helpers import export_part

PARTS = {
    "PVSP-WT-001_tank_body": "water_trap.tank_body",
    "PVSP-WT-002_tank_lid": "water_trap.tank_lid",
    "PVSP-WT-003_baffle": "water_trap.baffle",
    "PVSP-WT-004_tank_stand": "water_trap.tank_stand",
    "PVSP-WT-005_sight_tube_guard": "water_trap.sight_tube_guard",
    "PVSP-WT-006_dip_tube": "water_trap.dip_tube",
    "PVSP-BL-001_bellows_tpu": "bellows.bellows_tpu",
    "PVSP-BL-002_fixed_base": "bellows.fixed_base",
    "PVSP-BL-003_foot_plate": "bellows.foot_plate",
    "PVSP-BL-004_clamp_ring": "bellows.clamp_ring",
    "PVSP-BL-006_guide_bushing": "bellows.guide_bushing",
    "PVSP-BL-007_spring_anchor": "bellows.spring_anchor",
    "PVSP-BL-008_stroke_stop": "bellows.stroke_stop",
    "PVSP-BL-009_foot_pad_tpu": "bellows.foot_pad_tpu",
    "PVSP-AD-001_hose_support": "adapters.hose_support",
    "PVSP-AD-002_check_valve_bracket": "adapters.check_valve_bracket",
    "PVSP-CAL-001_bulkhead_hole_coupon": "calibration.bulkhead_hole_coupon",
    "PVSP-CAL-002_gasket_compression_coupon": "calibration.gasket_compression_coupon",
    "PVSP-CAL-003_bellows_wall_coupon": "calibration.bellows_wall_coupon",
}


def main() -> None:
    root = Path(__file__).resolve().parent
    stl_dir = root / "exports" / "stl"
    step_dir = root / "exports" / "step"
    failures = []

    for stem, module_name in PARTS.items():
        try:
            module = importlib.import_module(module_name)
            part = module.build()
            export_part(part, step_dir, stem)
            # export_part writes both formats into one directory, so move the STL.
            generated_stl = step_dir / f"{stem}.stl"
            stl_dir.mkdir(parents=True, exist_ok=True)
            generated_stl.replace(stl_dir / generated_stl.name)
            print(f"OK  {stem}")
        except Exception as exc:  # noqa: BLE001 - build report needs all failures
            failures.append((stem, repr(exc)))
            print(f"FAIL {stem}: {exc!r}")

    if failures:
        details = "\n".join(f"- {stem}: {error}" for stem, error in failures)
        raise RuntimeError(f"CAD generation failed for {len(failures)} part(s):\n{details}")


if __name__ == "__main__":
    main()
