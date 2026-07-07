#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Paddy Swarm Weed Unit V001 Passive Rake CADQuery Generator
==========================================================

Purpose
-------
Front-mounted first weeding unit for Paddy Swarm Common Rover v2.28.2.

This V001 unit is intentionally a passive rake / comb / hand-rake style unit.
The rover's forward motion performs the shallow mud disturbance.  PTO power is
not used for continuous weeding.  PTO is only used as an optional short-stroke
DROP assist to release/deploy the rake once, then PTO is stopped.

Design modes
------------
- MANUAL_DROP: hand lever / pull cord / pin release for safest first test.
- PTO_DROP: front high dual PTO can drive a small cam/link to release the latch.

Safety
------
This is not a field-ready paddy tool.  Use only bench, water tank, shallow mud,
and dummy-load tests first.  Keep PTO, motor boxes, box notches, and electronics
above water.  If the rake catches, the unit side should yield before the rover
core is damaged.

Expected commands
-----------------
Metadata only, safe without CadQuery:
  python paddy_swarm_weed_v001_2_passive_rake_cadquery.py --metadata-only --out weed_v001_2_passive_rake_meta --make-zip

With CadQuery installed:
  python paddy_swarm_weed_v001_2_passive_rake_cadquery.py --out weed_v001_2_passive_rake_out --make-zip

Dense packing example after STL export:
  python .\paddy_swarm_a1_dense_project_tools_v5_7_3_model_sets_paddy_fix.py --manifest .\weed_v001_2_passive_rake_out\print_manifest_generic_marked.csv --out .\weed_v001_2_passive_rake_model_dense_sets --group-mode all --ignore-manifest-plates --split-tpu --make-model-dense-sets --safe 240 --support-orient-fit-safe 244 --gap 4 --bambu-template-plate-inner-margin 12 --bambu-plate-inner-margin 12 --make-3mf --make-bambu-template-project-3mf --bambu-template-3mf .\blank_a1_plates_4.3mf --make-zip
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
import textwrap
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

try:
    import cadquery as cq
    from cadquery import exporters
except Exception as exc:  # pragma: no cover
    cq = None
    exporters = None
    CADQUERY_IMPORT_ERROR = exc
else:
    CADQUERY_IMPORT_ERROR = None

VERSION = "weed-v001.1-passive-rake-width-gauge-split"
KIT_NAME = "Paddy Swarm Weed Unit V001.2 Passive Rake Gauge Reference Fix Width Gauge Split"
MODULE = "weed_v001_1_passive_rake"

REF = {
    "compatible_rover": "Paddy Swarm Common Rover v2.28.2 Dual PTO Restart",
    "core_policy": "Do not redesign the v227-compatible two waterproof box fixed core.",
    "bbox_cbox_body_lwh_mm": [200.0, 150.0, 120.0],
    "wire_notch_policy": "Top-open notches on upper 200 mm wide wall faces only; no low side holes.",
    "front_pto_policy": "Front high dual PTO is used only for optional drop/release, not continuous weeding.",
    "row_spacing_target_mm": 300.0,
    "working_width_target_mm": [140.0, 180.0],
    "working_width_max_mm": 220.0,
    "rake_depth_targets_mm": [10.0, 20.0, 30.0],
    "a1_nominal_plate_mm": [256.0, 256.0],
    "recommended_dense_safe_mm": 240.0,
    "first_test": "bench / water tank / shallow mud only; dummy-load first; not field-ready",
}

@dataclass
class PartSpec:
    part_id: str
    name: str
    module: str
    material: str
    material_group: str
    qty: int
    plate_group: str
    filename_stl: str
    filename_step: str
    bbox_lwh: Tuple[float, float, float]
    usage: str
    notes: str
    print_target: bool = True


def ps(part_id: str, name: str, plate_group: str, material: str, material_group: str, qty: int,
       bbox_lwh: Tuple[float, float, float], usage: str, notes: str, print_target: bool = True) -> PartSpec:
    safe = part_id.replace("/", "_")
    return PartSpec(
        part_id=part_id,
        name=name,
        module=MODULE,
        material=material,
        material_group=material_group,
        qty=qty,
        plate_group=plate_group,
        filename_stl=f"{safe}.stl",
        filename_step=f"{safe}.step",
        bbox_lwh=tuple(float(x) for x in bbox_lwh),
        usage=usage,
        notes=notes,
        print_target=print_target,
    )

PARTS: List[PartSpec] = [
    ps("PS-WEED-V001-FRONT-MOUNT", "front fixed mount bracket for v228.2 PTO area", "W001-A-MOUNT", "PETG/ASA", "HARD", 1, (184, 58, 46), "front mount / hinge support", "no new rover-core holes; bolts to existing/front PTO mount candidate; support-free flat/vertical bracket"),
    ps("PS-WEED-V001-HINGE-CROSSBAR", "hinge bearing crossbar for up/down rake motion", "W001-A-MOUNT", "PETG/ASA", "HARD", 1, (188, 28, 24), "hinge crossbar", "accepts approx 5-6mm metal shaft; printed pin is dry-fit only; actual load should use metal shaft"),
    ps("PS-WEED-V001-RAKE-ARM-L", "left support arm / yielding rake arm", "W001-B-RAKE", "PETG/ASA", "HARD", 1, (164, 18, 8), "left rake arm", "hinged arm; can lift upward if rake catches; use shear pin / latch for weak-link behavior"),
    ps("PS-WEED-V001-RAKE-ARM-R", "right support arm / yielding rake arm", "W001-B-RAKE", "PETG/ASA", "HARD", 1, (164, 18, 8), "right rake arm", "same geometry as left; mirror only in assembly"),
    ps("PS-WEED-V001-RAKE-COMB-BAR", "replaceable tine comb holding bar", "W001-B-RAKE", "PETG/ASA", "HARD", 1, (188, 24, 20), "comb bar / tine holder", "nine tine holes; use printed tines for dry-fit or metal/bent wire tines for muddy load tests"),
    ps("PS-WEED-V001-RAKE-TINE-S", "replaceable blunt rake tine", "W001-B-RAKE", "PETG/ASA", "HARD", 9, (74, 8, 6), "passive mud rake tine", "qty 9; blunt non-cutting tip; shallow mud disturbance only; should fail before rover core if overloaded"),
    ps("PS-WEED-V001-DEPTH-SKID-L", "left depth limiting skid", "W001-B-RAKE", "PETG/ASA", "HARD", 1, (124, 24, 20), "left skid / depth limiter", "keeps tines around 10/20/30mm mud depth; rounded sled shape; avoids mud-trap cavities"),
    ps("PS-WEED-V001-DEPTH-SKID-R", "right depth limiting skid", "W001-B-RAKE", "PETG/ASA", "HARD", 1, (124, 24, 20), "right skid / depth limiter", "same geometry as left; mirror only in assembly"),
    ps("PS-WEED-V001-SKID-HEIGHT-PLATE-S", "skid height adjustment plate", "W001-B-ADJUST", "PETG/ASA", "HARD", 2, (74, 34, 6), "depth height adjuster", "holes/marks for 10/20/30mm depth settings; print two"),
    ps("PS-WEED-V001-SHEAR-PIN-S", "printed weak shear pin", "W001-C-SAFETY", "PETG/ASA", "HARD", 4, (26, 5, 5), "weak pin / sacrificial dry-fit pin", "not for production load; intended to fail or release before the rover core/PTO is damaged"),
    ps("PS-WEED-V001-MANUAL-DROP-LEVER", "manual drop release lever", "W001-C-SAFETY", "PETG/ASA", "HARD", 1, (84, 18, 8), "manual drop lever", "used for MANUAL_DROP; pull/press to release latch without PTO"),
    ps("PS-WEED-V001-MANUAL-LIFT-CORD-ANCHOR", "manual lift cord / wire anchor", "W001-C-SAFETY", "PETG/ASA", "HARD", 1, (42, 30, 16), "lift cord anchor", "anchor for cord/wire so operator can lift/release in water tank tests"),
    ps("PS-WEED-V001-PTO-DROP-CAM", "PTO drop cam for short release motion", "W001-D-PTO-DROP", "PETG/ASA", "HARD", 1, (50, 44, 10), "PTO short-stroke release cam", "PTO_DROP only; does not drive continuous weeding; stop PTO after release"),
    ps("PS-WEED-V001-PTO-DROP-LINK", "PTO drop link", "W001-D-PTO-DROP", "PETG/ASA", "HARD", 1, (94, 14, 6), "link from cam to latch", "short visible link; do not bury in mud; use metal pins for load tests"),
    ps("PS-WEED-V001-DROP-LATCH", "drop latch / raised-state latch", "W001-D-PTO-DROP", "PETG/ASA", "HARD", 1, (64, 28, 10), "manual/PTO latch", "holds rake up; can be released manually or by PTO cam; geometry is first-fit candidate"),
    ps("PS-WEED-V001-DROP-LIMIT-STOP", "drop limit stop", "W001-D-PTO-DROP", "PETG/ASA", "HARD", 2, (30, 20, 18), "down travel limiter", "prevents over-drop that could damage PTO/front mount; print two"),
    ps("PS-WEED-V001-FRONT-MINI-FLOAT-L", "left detachable front mini float", "W001-E-FLOAT", "PETG/ASA", "HARD", 1, (96, 30, 26), "front trim float left", "optional trim float; not waterproof by printing alone; seal/coat/foam fill before water tests"),
    ps("PS-WEED-V001-FRONT-MINI-FLOAT-R", "right detachable front mini float", "W001-E-FLOAT", "PETG/ASA", "HARD", 1, (96, 30, 26), "front trim float right", "same as left; keeps front PTO from nosing down; optional and removable"),
    ps("PS-WEED-V001-DEPTH-GAUGE-S", "10/20/30mm rake depth gauge", "W001-F-GAUGE", "PETG/ASA", "HARD", 1, (86, 44, 6), "rake depth gauge", "dry-fit gauge for 10/20/30mm tine depth settings"),
    ps("PS-WEED-V001-WIDTH-GAUGE-300MM-S", "300mm row width gauge reference only", "W001-F-GAUGE-REF", "REFERENCE", "REFERENCE", 0, (300, 20, 5), "reference row spacing gauge only", "do not print as one piece on Bambu A1; use 150mm A/B split gauge parts instead", False),
    ps("PS-WEED-V001-WIDTH-GAUGE-150MM-A", "150mm row width gauge half A reference only", "W001-F-GAUGE-REF", "REFERENCE", "REFERENCE", 0, (150, 20, 5), "row spacing gauge half A reference", "reference-only; use a ruler/tape or create a separate simple gauge outside dense print workflow", False),
    ps("PS-WEED-V001-WIDTH-GAUGE-150MM-B", "150mm row width gauge half B reference only", "W001-F-GAUGE-REF", "REFERENCE", "REFERENCE", 0, (150, 20, 5), "row spacing gauge half B reference", "reference-only; use a ruler/tape or create a separate simple gauge outside dense print workflow", False),
    ps("PS-WEED-V001-LIMIT-BUMPER-TPU-S", "optional TPU soft limit bumper", "W001-G-TPU-OPTIONAL", "TPU", "TPU", 2, (24, 14, 6), "optional soft stop bumper", "optional TPU bumper for drop-limit impact; remove if TPU workflow should be skipped"),
]

DESIGN_CONTRACT = {
    "kit": KIT_NAME,
    "version": VERSION,
    "reference": REF,
    "passive_rake_policy": [
        "V001 is a passive rake/comb unit, not a powered rotary weeder.",
        "The rover moves forward; the rake tines disturb shallow mud and weeds.",
        "Tines are blunt and replaceable; they are not cutting blades.",
    ],
    "manual_drop_policy": [
        "MANUAL_DROP is mandatory for first tests.",
        "The rake can be raised, latched, and then released by a hand lever or cord without PTO.",
        "Water-tank tests should begin with manual release only.",
    ],
    "pto_drop_policy": [
        "PTO_DROP is an optional release/deploy mechanism only.",
        "Front high dual PTO can rotate a small cam for latch release.",
        "PTO must be stopped after release; it is not used for continuous weeding.",
        "The cam/link/latch must remain visible and high, not buried in mud or low hull area.",
    ],
    "no_continuous_pto_weeding_policy": [
        "Do not connect V001 PTO parts to rotating blades, discs, or brushes.",
        "Continuous PTO weeding is deferred to later versions after water-propulsion stability is proven.",
    ],
    "depth_control_policy": [
        "Target tine engagement is shallow: about 10/20/30mm settings.",
        "Left/right skids limit depth and allow hard mud to lift the unit upward.",
        "The rover core should not be sunk to make the rake reach mud; the unit reaches down instead.",
    ],

    "width_gauge_split_policy": [
        "The 300mm row-width gauge is kept as a non-print reference part only.",
        "The 150mm A/B halves are also reference-only in v001.2 to keep dense output clean.",
        "Do not use --allow-excluded-print-targets for row-width gauges; use a ruler/tape or separate gauge print instead."
    ],
    "v2282_front_dual_pto_compatibility": [
        "Designed for Paddy Swarm Common Rover v2.28.2 front high dual PTO restart layout.",
        "Does not modify BBOX/CBOX fixed core or notch policy.",
        "Keep PTO/motor boxes/notches above water during tests.",
    ],
    "no_support_generation_policy": [
        "Parts are simple flat/box/rod geometries intended for support-free orientation.",
        "Avoid floating labels or detached overhang islands.",
        "45 degrees is not treated as safe; ramps are conservative and fused to parent solids.",
    ],
    "field_safety": [
        "This is not a field-ready tool.",
        "Rice fields are income-producing land; do not run unvalidated hardware in real paddies.",
        "Stage tests: bench -> dry fit -> water tank -> shallow mud -> low speed dummy-load only.",
        "If the rake catches, sacrifice pins/tines before rover core or PTO parts.",
    ],
}

README_TEMPLATE = r"""# Paddy Swarm Weed Unit V001 Passive Rake

`{kit}` / `{version}`

## Purpose

This is the first front-mounted weeding-unit study for Paddy Swarm Common Rover v2.28.2.
It is a passive comb / rake / hand-rake style unit.  It is intentionally not a
complex rotary weeder.

## Core design rule

- The rover body stays afloat and moves forward.
- The weeding unit reaches down to shallow mud.
- PTO is **not** used for continuous weeding.
- PTO is only used as an optional one-time DROP / latch-release assist.
- MANUAL_DROP must work without PTO for the first safety tests.

## Operation modes

### MANUAL_DROP

1. Raise the rake.
2. Hold it with the latch.
3. Pull the manual lever or cord.
4. Rake drops by gravity.
5. Depth skids limit tine engagement.
6. Rover propulsion performs passive weeding.

### PTO_DROP

1. Rake is latched in the raised state.
2. Run front PTO briefly.
3. PTO drop cam pushes the drop link.
4. Drop latch releases.
5. Rake drops by gravity.
6. Stop PTO.
7. Rover propulsion performs passive weeding.

PTO_DROP is a release/deploy mechanism only.  Do not use V001 PTO parts for
continuous rotary weeding.

## Row spacing / dimensions

- Target row spacing: 300mm.
- Initial work width target: 140-180mm.
- Maximum work width target: about 220mm.
- Unit body must stay under 300mm envelope.
- Tine depth targets: 10 / 20 / 30mm.

## Safety notes

- Not for real paddy field deployment.
- First tests: bench, tank, shallow mud, low speed only.
- Keep PTO, motor boxes, notches, and electronics above water.
- If the rake catches, unit-side shear pins/tines should yield before rover core damage.
- Mini floats are optional trim parts and are not waterproof without seal/coat/foam.

## Generated files

- `stl/*.stl`
- `step/*.step`
- `reference_metal_stl/*.stl` when full CadQuery export is run
- `print_manifest.csv`
- `print_manifest_generic_marked.csv`
- `plate_manifest.csv`
- `paddy_swarm_weed_v001_1_passive_rake_design_contract.json`
- `SHA256SUMS`

## Commands

Metadata-only:

```powershell
python .\paddy_swarm_weed_v001_2_passive_rake_cadquery.py --metadata-only --out .\weed_v001_2_passive_rake_meta --make-zip
```

Full CAD export:

```powershell
python .\paddy_swarm_weed_v001_2_passive_rake_cadquery.py --out .\weed_v001_2_passive_rake_out --make-zip
```

Dense model sets:

```powershell
python .\paddy_swarm_a1_dense_project_tools_v5_7_3_model_sets_paddy_fix.py --manifest .\weed_v001_2_passive_rake_out\print_manifest_generic_marked.csv --out .\weed_v001_2_passive_rake_model_dense_sets --group-mode all --ignore-manifest-plates --split-tpu --make-model-dense-sets --safe 240 --support-orient-fit-safe 244 --gap 4 --bambu-template-plate-inner-margin 12 --bambu-plate-inner-margin 12 --make-3mf --make-bambu-template-project-3mf --bambu-template-3mf .\blank_a1_plates_4.3mf --make-zip
```

## v001.2 width gauge dense fix

The 300mm row-width gauge and the 150mm A/B gauge halves are retained as metadata/reference parts only.  Dense printing excludes them because they are inspection aids, not rover/weed-unit hardware.  For row-width checking, use a ruler/tape measure or print a separate simple gauge outside the dense workflow.

## Known limits

- The PTO cam / latch is a first-fit mechanism.  Expect hand tuning after print.
- Printed shear pins are for safety/release testing, not final load-bearing pins.
- Real mud may require metal tines or softer replaceable tine variants.
- This generator cannot prove waterproofing or actual weeding performance.
"""


def require_cadquery() -> None:
    if cq is None or exporters is None:
        raise RuntimeError(
            "CadQuery is required for STL/STEP export. Use --metadata-only without CadQuery. "
            f"Import error: {CADQUERY_IMPORT_ERROR!r}"
        )


def write_csv(rows: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def part_rows(parts: List[PartSpec]) -> List[dict]:
    rows = []
    for p in parts:
        x, y, z = p.bbox_lwh
        rows.append({
            "part_id": p.part_id,
            "name": p.name,
            "module": p.module,
            "material": p.material,
            "material_group": p.material_group,
            "is_tpu": "1" if p.material_group.upper() == "TPU" else "0",
            "qty": p.qty,
            "plate_group": p.plate_group,
            "filename": f"stl/{p.filename_stl}",
            "stl": f"stl/{p.filename_stl}",
            "filename_stl": p.filename_stl,
            "filename_step": p.filename_step,
            "bbox_x": x,
            "bbox_y": y,
            "bbox_z": z,
            "usage": p.usage,
            "notes": p.notes,
            "print_target": "1" if p.print_target else "0",
        })
    return rows


def plate_rows(parts: List[PartSpec]) -> List[dict]:
    groups: Dict[str, List[PartSpec]] = {}
    for p in parts:
        groups.setdefault(p.plate_group, []).append(p)
    rows = []
    for i, key in enumerate(sorted(groups), 1):
        ps = groups[key]
        rows.append({
            "plate_no": i,
            "plate_group": key,
            "material_groups": ",".join(sorted(set(p.material_group for p in ps))),
            "part_ids": ";".join(p.part_id for p in ps),
            "notes": "Logical group only; dense tool may repack by material and safe size.",
        })
    return rows


def write_metadata(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rows = part_rows(PARTS)
    write_csv(rows, out / "print_manifest.csv")
    write_csv(rows, out / "print_manifest_generic_marked.csv")
    write_csv(plate_rows(PARTS), out / "plate_manifest.csv")
    (out / "paddy_swarm_weed_v001_1_passive_rake_design_contract.json").write_text(
        json.dumps(DESIGN_CONTRACT, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "README_weed_v001_1_passive_rake.md").write_text(
        README_TEMPLATE.format(kit=KIT_NAME, version=VERSION), encoding="utf-8"
    )


def cyl_x(radius: float, length: float):
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(-length / 2.0, 0, 0), cq.Vector(1, 0, 0))
    return cq.Workplane("XY").newObject([solid])


def cyl_y(radius: float, length: float):
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(0, -length / 2.0, 0), cq.Vector(0, 1, 0))
    return cq.Workplane("XY").newObject([solid])


def cyl_z(radius: float, length: float):
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(0, 0, -length / 2.0), cq.Vector(0, 0, 1))
    return cq.Workplane("XY").newObject([solid])


def place_on_bed(obj):
    try:
        bb = obj.val().BoundingBox()
        return obj.translate((0, 0, -bb.zmin))
    except Exception:
        return obj


def box(l: float, w: float, h: float, zbase: bool = True):
    obj = cq.Workplane("XY").box(l, w, h)
    return obj.translate((0, 0, h / 2.0)) if zbase else obj


def make_front_mount(part_id: str):
    base = box(184, 58, 8)
    left = box(14, 44, 46).translate((-70, 0, 0))
    right = box(14, 44, 46).translate((70, 0, 0))
    bridge = box(152, 10, 20).translate((0, 24, 0))
    boss_l = box(24, 18, 18).translate((-38, -20, 0))
    boss_r = box(24, 18, 18).translate((38, -20, 0))
    obj = base.union(left).union(right).union(bridge).union(boss_l).union(boss_r)
    # hinge holes through the side cheeks, high and visible
    for x in (-70, 70):
        obj = obj.cut(cyl_x(3.2, 20).translate((x, 0, 30)))
        obj = obj.cut(cyl_z(2.0, 16).translate((x, -20, 0)))
    # bolt slots / front mount holes
    for x in (-55, 55):
        obj = obj.cut(cyl_z(2.2, 12).translate((x, 18, 0)))
        obj = obj.cut(cyl_z(2.2, 12).translate((x, -18, 0)))
    return place_on_bed(obj)


def make_hinge_crossbar(part_id: str):
    obj = box(188, 28, 24)
    # metal shaft channel along X
    obj = obj.cut(cyl_x(3.3, 198).translate((0, 0, 14)))
    # lightening access, not a closed mud trap
    for x in (-60, 0, 60):
        obj = obj.cut(cyl_z(3.0, 30).translate((x, 0, 0)))
    return place_on_bed(obj)


def make_rake_arm(part_id: str):
    obj = box(164, 18, 8)
    # vertical pin holes at both ends; print flat
    for x in (-70, 70):
        obj = obj.cut(cyl_z(3.0, 12).translate((x, 0, 0)))
    # sacrificial shear-pin holes
    for x in (-25, 25):
        obj = obj.cut(cyl_z(2.2, 12).translate((x, 0, 0)))
    return place_on_bed(obj)


def make_comb_bar(part_id: str):
    obj = box(188, 24, 20)
    # crossbar metal shaft channel
    obj = obj.cut(cyl_x(3.3, 198).translate((0, 0, 13)))
    # nine tine sockets, vertical; tines can be printed or replaced by metal wire
    pitch = 18.0
    for i in range(9):
        x = (i - 4) * pitch
        obj = obj.cut(cyl_z(2.4, 24).translate((x, -6, 0)))
        obj = obj.cut(cyl_y(1.6, 32).translate((x, -6, 10)))
    return place_on_bed(obj)


def make_tine(part_id: str):
    # Flat printable blunt tine; in assembly, long direction points down/back.
    body = box(74, 8, 6)
    # blunt wedge nose, fused; no sharp blade
    nose = cq.Workplane("XY").polyline([(0, -4), (8, 0), (0, 4), (0, -4)]).close().extrude(6).translate((37, 0, 0))
    root = box(12, 12, 6).translate((-35, 0, 0))
    obj = body.union(nose).union(root)
    obj = obj.cut(cyl_z(1.8, 10).translate((-34, 0, 0)))
    return place_on_bed(obj)


def make_depth_skid(part_id: str):
    base = box(100, 24, 10)
    front_ramp = cq.Workplane("YZ").polyline([(-12, 0), (12, 0), (12, 10), (-12, 0)]).close().extrude(22).translate((50, 0, 0))
    rear = box(18, 24, 14).translate((-50, 0, 0))
    tab = box(34, 8, 18).translate((-35, 0, 0))
    obj = base.union(front_ramp).union(rear).union(tab)
    for x in (-30, 20):
        obj = obj.cut(cyl_z(2.2, 24).translate((x, 0, 0)))
    return place_on_bed(obj)


def make_height_plate(part_id: str):
    obj = box(74, 34, 6)
    # 10 / 20 / 30mm notional adjustment positions
    for x in (-24, 0, 24):
        obj = obj.cut(cyl_z(2.2, 10).translate((x, 0, 0)))
    return place_on_bed(obj)


def make_shear_pin(part_id: str):
    return place_on_bed(cyl_x(2.25, 26))


def make_manual_drop_lever(part_id: str):
    obj = box(84, 18, 8)
    handle = box(18, 26, 8).translate((35, 0, 0))
    obj = obj.union(handle)
    for x in (-34, 20):
        obj = obj.cut(cyl_z(2.3, 12).translate((x, 0, 0)))
    return place_on_bed(obj)


def make_cord_anchor(part_id: str):
    obj = box(42, 30, 16)
    bridge = box(22, 10, 12).translate((0, 0, 10))
    obj = obj.union(bridge)
    obj = obj.cut(cyl_y(3.2, 36).translate((0, 0, 12)))
    for x in (-12, 12):
        obj = obj.cut(cyl_z(2.0, 20).translate((x, 0, 0)))
    return place_on_bed(obj)


def make_pto_drop_cam(part_id: str):
    disk = cyl_z(18, 8)
    lobe = cyl_z(11, 8).translate((16, 0, 0))
    hub = cyl_z(8, 12).translate((0, 0, 2))
    obj = disk.union(lobe).union(hub)
    obj = obj.cut(cyl_z(3.1, 18))
    # small M3 set-screw style side hole, printed as inspection/fit candidate
    obj = obj.cut(cyl_x(1.6, 44).translate((0, 0, 6)))
    return place_on_bed(obj)


def make_pto_drop_link(part_id: str):
    obj = box(94, 14, 6)
    for x in (-40, 40):
        obj = obj.cut(cyl_z(2.2, 10).translate((x, 0, 0)))
    return place_on_bed(obj)


def make_drop_latch(part_id: str):
    base = box(64, 18, 8)
    hook = box(22, 28, 8).translate((22, 0, 0))
    ramp = cq.Workplane("XY").polyline([(0, -10), (20, 0), (0, 10), (0, -10)]).close().extrude(8).translate((22, 0, 0))
    obj = base.union(hook).union(ramp)
    obj = obj.cut(cyl_z(2.4, 12).translate((-24, 0, 0)))
    obj = obj.cut(cyl_z(2.0, 12).translate((18, 0, 0)))
    return place_on_bed(obj)


def make_drop_limit_stop(part_id: str):
    base = box(30, 20, 10)
    ramp = cq.Workplane("YZ").polyline([(-10, 0), (10, 0), (10, 10), (-10, 0)]).close().extrude(30).translate((0, 0, 8))
    obj = base.union(ramp)
    obj = obj.cut(cyl_z(2.2, 18).translate((0, 0, 0)))
    return place_on_bed(obj)


def make_mini_float(part_id: str):
    # Simple detachable trim float; no sealed-waterproof guarantee.
    body = box(96, 30, 22)
    top = box(78, 18, 8).translate((0, 0, 18))
    pad1 = box(18, 20, 8).translate((-30, 0, 22))
    pad2 = box(18, 20, 8).translate((30, 0, 22))
    obj = body.union(top).union(pad1).union(pad2)
    for x in (-30, 30):
        obj = obj.cut(cyl_z(2.2, 38).translate((x, 0, 0)))
    return place_on_bed(obj)


def make_depth_gauge(part_id: str):
    plate = box(86, 44, 4)
    # three raised steps/marks; still flat-printable because they grow upward from bed
    step10 = box(18, 8, 10).translate((-28, 12, 0))
    step20 = box(18, 8, 20).translate((0, 12, 0))
    step30 = box(18, 8, 30).translate((28, 12, 0))
    obj = plate.union(step10).union(step20).union(step30)
    return place_on_bed(obj)


def make_width_gauge(part_id: str):
    # v001.2: width gauges are reference-only and excluded from dense print output.
    if part_id == "PS-WEED-V001-WIDTH-GAUGE-300MM-S":
        return place_on_bed(box(300, 20, 5))

    obj = box(150, 20, 5)
    # End stop / butt alignment mark, kept inside the 150mm envelope.
    obj = obj.union(box(4, 20, 7).translate((-73, 0, 0)))
    obj = obj.union(box(4, 20, 7).translate((73, 0, 0)))
    # Center tick marks grow upward from the bed; no floating labels.
    obj = obj.union(box(2, 20, 7).translate((0, 0, 0)))
    # Two small M3 clearance holes for optional temporary joining strip.
    for x in (-55, 55):
        obj = obj.cut(cyl_z(2.1, 12).translate((x, 0, 0)))
    return place_on_bed(obj)


def make_limit_bumper_tpu(part_id: str):
    obj = box(24, 14, 6)
    obj = obj.cut(cyl_z(1.8, 10).translate((0, 0, 0)))
    return place_on_bed(obj)


BUILDERS: Dict[str, Callable[[str], object]] = {
    "PS-WEED-V001-FRONT-MOUNT": make_front_mount,
    "PS-WEED-V001-HINGE-CROSSBAR": make_hinge_crossbar,
    "PS-WEED-V001-RAKE-ARM-L": make_rake_arm,
    "PS-WEED-V001-RAKE-ARM-R": make_rake_arm,
    "PS-WEED-V001-RAKE-COMB-BAR": make_comb_bar,
    "PS-WEED-V001-RAKE-TINE-S": make_tine,
    "PS-WEED-V001-DEPTH-SKID-L": make_depth_skid,
    "PS-WEED-V001-DEPTH-SKID-R": make_depth_skid,
    "PS-WEED-V001-SKID-HEIGHT-PLATE-S": make_height_plate,
    "PS-WEED-V001-SHEAR-PIN-S": make_shear_pin,
    "PS-WEED-V001-MANUAL-DROP-LEVER": make_manual_drop_lever,
    "PS-WEED-V001-MANUAL-LIFT-CORD-ANCHOR": make_cord_anchor,
    "PS-WEED-V001-PTO-DROP-CAM": make_pto_drop_cam,
    "PS-WEED-V001-PTO-DROP-LINK": make_pto_drop_link,
    "PS-WEED-V001-DROP-LATCH": make_drop_latch,
    "PS-WEED-V001-DROP-LIMIT-STOP": make_drop_limit_stop,
    "PS-WEED-V001-FRONT-MINI-FLOAT-L": make_mini_float,
    "PS-WEED-V001-FRONT-MINI-FLOAT-R": make_mini_float,
    "PS-WEED-V001-DEPTH-GAUGE-S": make_depth_gauge,
    "PS-WEED-V001-WIDTH-GAUGE-300MM-S": make_width_gauge,
    "PS-WEED-V001-WIDTH-GAUGE-150MM-A": make_width_gauge,
    "PS-WEED-V001-WIDTH-GAUGE-150MM-B": make_width_gauge,
    "PS-WEED-V001-LIMIT-BUMPER-TPU-S": make_limit_bumper_tpu,
}


def export_reference_metal_stl(out: Path) -> None:
    require_cadquery()
    metal_dir = out / "reference_metal_stl"
    metal_dir.mkdir(parents=True, exist_ok=True)
    refs = {
        "REF-WEED-HINGE-SHAFT-6MM-190.stl": cyl_x(3.0, 190.0),
        "REF-WEED-COMB-SHAFT-6MM-185.stl": cyl_x(3.0, 185.0),
        "REF-WEED-PTO-CAM-SHAFT-5MM-80.stl": cyl_x(2.5, 80.0),
        "REF-WEED-LINK-PIN-4MM-28.stl": cyl_x(2.0, 28.0),
        "REF-WEED-TINE-WIRE-3MM-90.stl": cyl_x(1.5, 90.0),
        "REF-WEED-R-PIN-SURROGATE.stl": cyl_x(1.2, 24.0).union(cyl_z(3.0, 2.4).translate((10, 0, 0))),
    }
    for name, obj in refs.items():
        exporters.export(place_on_bed(obj), str(metal_dir / name))


def export_cad(out: Path) -> None:
    require_cadquery()
    stl_dir = out / "stl"
    step_dir = out / "step"
    stl_dir.mkdir(parents=True, exist_ok=True)
    step_dir.mkdir(parents=True, exist_ok=True)
    for p in PARTS:
        obj = BUILDERS[p.part_id](p.part_id)
        exporters.export(obj, str(stl_dir / p.filename_stl))
        exporters.export(obj, str(step_dir / p.filename_step))
    export_reference_metal_stl(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sha256s(out: Path) -> None:
    rows = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            rows.append(f"{sha256_file(p)}  {p.relative_to(out).as_posix()}")
    (out / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")


def make_zip(out: Path) -> Path:
    zip_path = out.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(out.parent))
    print(f"[ZIP] {zip_path}")
    return zip_path


def maybe_copy_generator(out: Path) -> None:
    try:
        src = Path(__file__).resolve()
        dst = out / src.name
        if src.exists() and src != dst:
            shutil.copy2(src, dst)
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="weed_v001_2_passive_rake_out")
    ap.add_argument("--metadata-only", action="store_true")
    ap.add_argument("--make-zip", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    write_metadata(out)
    maybe_copy_generator(out)
    if not args.metadata_only:
        export_cad(out)
    write_sha256s(out)
    if args.make_zip:
        make_zip(out)
    print(f"[OK] {KIT_NAME} {VERSION} -> {out}")
    if args.metadata_only:
        print("[INFO] metadata-only: STL/STEP export skipped")
    elif CADQUERY_IMPORT_ERROR:
        print(f"[WARN] CadQuery import issue: {CADQUERY_IMPORT_ERROR!r}")


if __name__ == "__main__":
    main()
