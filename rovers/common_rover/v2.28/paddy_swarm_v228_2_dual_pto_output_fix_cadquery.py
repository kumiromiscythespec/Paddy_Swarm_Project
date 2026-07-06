#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Paddy Swarm Common Rover v228.2 Dual PTO Output CADQuery Generator
=======================================================================

Purpose
-------
v228.1 dual-PTO-output revision: v227-compatible fixed two waterproof box core, high forward PTO with two left/right motor power output ports, clean shell/hull modules, and reference metal surrogate STL export.

This file fixes two practical issues found during Bambu Studio preview:

1. Long faceted shell/hull/sponson parts are split into A/B half-length parts.
2. The XZ-profile extrusion helper treats length_y as FINAL total length.
   In the earlier G0 generator, .extrude(length_y, both=True) made actual STLs
   twice as long as the manifest value.  G1 uses length_y / 2 with both=True.
   Wheel width extrusion is also corrected to width / 2 with both=True.
3. Fullset manifest includes two printed waterproof boxes: BBOX and CBOX body/lid/gasket.

Compatibility policy
--------------------
- Do not reprint or modify PS-RV227-BBOX-BDY / BBOX-LID / BBOX-GSK.
- Do not reprint or modify PS-RV227-CBOX-BDY / CBOX-LID / CBOX-GSK.
- Keep the v2.27 front/rear two-box layout.  Never place BBOX and CBOX side-by-side.
- Use MCR rails / LOWER-FRAME / FLT-RCV / existing bracket areas as mounting references.
- Do not drill into BBOX/CBOX during first retrofit testing.
- First water tests must use dummy weights only; no electronics.

Expected commands
-----------------
With CadQuery installed:
  python paddy_swarm_v228_1_dual_pto_output_cadquery.py --out rover_v228_1_dual_pto_output_out --make-zip

Metadata only:
  python paddy_swarm_v228_1_dual_pto_output_cadquery.py --metadata-only --out rover_v228_1_dual_pto_output_meta --make-zip
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

try:
    import cadquery as cq
    from cadquery import exporters
except Exception as exc:  # pragma: no cover
    cq = None
    exporters = None
    CADQUERY_IMPORT_ERROR = exc
else:
    CADQUERY_IMPORT_ERROR = None

VERSION = "v2.28.2-dual-pto-output-fix"
KIT_NAME = "Paddy Swarm v2.28.2 Dual PTO Output Clean Core Fix"

REF = {
    "base_rover": "Paddy Swarm Common Rover v2.27",
    "a1_nominal_plate_mm": [256, 256],
    "row_spacing_target_mm": 300.0,
    "v227_box_body_lwh_mm": [200.0, 150.0, 120.0],
    "v227_box_lid_lwh_mm": [216.0, 166.0, 16.0],
    "v227_box_gasket_lwh_mm": [204.0, 154.0, 3.0],
    "v2274_notch_reference": "Corrected layout: each printed box is 200mm wide x 150mm front/back; top-open wire-drop notches are on the 200mm wide front/rear faces, one inner-side and one outer-side.",
    "first_water_test": "dummy weights only; no electronics",
    "v2274_reason": "fix v2274 90-degree box-notch orientation: BBOX/CBOX become 200mm wide x 150mm front/back so notches sit on the 200mm wide faces",
}

DIM = {
    "box_body_lwh": [200.0, 150.0, 120.0],
    "box_lid_lwh": [216.0, 166.0, 16.0],
    "box_gasket_lwh": [204.0, 154.0, 3.0],
    "box_notch_width": 18.0,
    "box_notch_drop": 28.0,
    "box_notch_depth_y": 16.0,
    "box_notch_bottom_radius": 7.0,
    "box_gusset": 6.0,
    "box_drip_edge_lwh": [28.0, 3.0, 5.0],
    "box_rain_cap_lwh": [34.0, 24.0, 12.0],
    "hull_half_lwh": [220.0, 116.0, 34.0],       # X width, Y length, Z height
    "hull_crown_pad_lwh": [154.0, 88.0, 6.0],
    "hull_joiner_lwh": [78.0, 22.0, 8.0],
    "wheel_outer_d": 118.0,
    "wheel_inner_d": 54.0,
    "wheel_width": 48.0,
    "wheel_tread_h": 7.0,
    "wheel_tread_count": 16,
    "wheel_hub_outer_d": 104.0,
    "wheel_tpu_tread_outer_d": 118.0,
    "wheel_tpu_tread_inner_d": 106.0,
    "wheel_tpu_tread_width": 48.0,
    "wheel_tread_lug_h": 5.0,
    "shell_half_lwh": [196.0, 116.0, 74.0],
    "shell_crown_w": 66.0,
    "shell_skirt_h": 18.0,
    "shell_joiner_lwh": [76.0, 18.0, 8.0],
    "shell_panel_top_lwh": [132.0, 104.0, 2.6],
    "shell_panel_side_lwh": [92.0, 104.0, 2.6],
    "shell_panel_frame_lwh": [152.0, 108.0, 5.0],
    "restart_turtle_upper_half_lwh": [232.0, 168.0, 56.0],
    "restart_turtle_upper_quarter_lwh": [108.0, 156.0, 28.0],
    "restart_belly_hull_half_lwh": [238.0, 172.0, 46.0],
    "restart_belly_hull_quarter_lwh": [108.0, 156.0, 32.0],
    "restart_side_buoy_lwh": [38.0, 132.0, 34.0],
    "restart_motor_mount_lwh": [52.0, 72.0, 46.0],
    "restart_front_pto_high_lwh": [88.0, 56.0, 52.0],
    "restart_front_float_mount_lwh": [54.0, 34.0, 18.0],
    "side_sponson_half_lwh": [48.0, 116.0, 44.0],
    "sponson_joiner_lwh": [42.0, 18.0, 8.0],
    "front_visor_lwh": [188.0, 42.0, 32.0],
    "rear_cap_lwh": [190.0, 18.0, 68.0],
    "doghouse_lwh": [116.0, 92.0, 82.0],
    "mcr_clamp_lwh": [38.0, 46.0, 26.0],
    "flt_saddle_lwh": [70.0, 36.0, 34.0],
}

@dataclass(frozen=True)
class PartSpec:
    part_id: str
    description: str
    phase: str
    material: str
    material_group: str
    qty: int
    plate_group: str
    filename_stl: str
    filename_step: str
    bbox_mm: Tuple[float, float, float]
    compatibility: str
    notes: str

def p(part_id, desc, phase, mat, group, qty, plate, bbox, compat, notes):
    return PartSpec(
        part_id=part_id,
        description=desc,
        phase=phase,
        material=mat,
        material_group=group,
        qty=qty,
        plate_group=plate,
        filename_stl=f"{part_id}.stl",
        filename_step=f"{part_id}.step",
        bbox_mm=tuple(float(x) for x in bbox),
        compatibility=compat,
        notes=notes,
    )

PARTS: List[PartSpec] = [
    # Phase 0: common waterproof boxes included for GitHub fullset.
    # These are included in manifest/plates for a complete repository artifact.
    # If BBOX/CBOX are already printed, skip these plates during actual printing.
    p("PS-RV227-BBOX-BDY", "front printed waterproof battery/power box body, v2.27 common part", "0", "PETG/ASA", "HARD", 1, "FULLSET-BOX-BBOX-BDY", (200,150,120), "v2.27 common part; already-printable; do not side-by-side with CBOX in layout", "v2274: 200x150 body; two top-open rounded-bottom wire-drop notches per box on 200mm wide faces: one inner-side and one outer-side; not two notches on same side; drip-resistant only, not waterproof; seal with silicone/boot/gland/potting; dummy-weight first water test only"),
    p("PS-RV227-BBOX-LID", "front printed waterproof battery/power box lid, v2.27 common part", "0", "PETG/ASA", "HARD", 1, "FULLSET-BOX-BBOX-LID", (216,166,16), "v2.27 common part", "v2274 lid kept dimension-compatible; gasket compression not guaranteed by print alone; notch zones require separate sealing"),
    p("PS-RV227-BBOX-GSK", "front printed waterproof battery/power box TPU gasket, v2.27 common part", "0", "TPU", "TPU", 1, "FULLSET-BOX-BBOX-GSK", (204,154,3), "v2.27 common part", "TPU gasket candidate; notch zones require silicone/boot/gland/potting; not a waterproof guarantee"),
    p("PS-RV227-CBOX-BDY", "rear printed waterproof control/communication box body, v2.27 common part", "0", "PETG/ASA", "HARD", 1, "FULLSET-BOX-CBOX-BDY", (200,150,120), "v2.27 common part; already-printable; do not side-by-side with BBOX in layout", "v2274: 200x150 body; two top-open rounded-bottom wire-drop notches per box on 200mm wide faces: one inner-side and one outer-side; not two notches on same side; drip-resistant only, not waterproof; seal with silicone/boot/gland/potting; dummy-weight first water test only"),
    p("PS-RV227-CBOX-LID", "rear printed waterproof control/communication box lid, v2.27 common part", "0", "PETG/ASA", "HARD", 1, "FULLSET-BOX-CBOX-LID", (216,166,16), "v2.27 common part", "v2274 lid kept dimension-compatible; gasket compression not guaranteed by print alone; notch zones require separate sealing"),
    p("PS-RV227-CBOX-GSK", "rear printed waterproof control/communication box TPU gasket, v2.27 common part", "0", "TPU", "TPU", 1, "FULLSET-BOX-CBOX-GSK", (204,154,3), "v2.27 common part", "TPU gasket candidate; notch zones require silicone/boot/gland/potting; not a waterproof guarantee"),

    p("PS-RV2273v2274-BOX-NOTCH-RAIN-CAP-S", "optional drip-resistant rain cap set for inner/outer top-open wire-drop notches", "0", "PETG/ASA", "HARD", 4, "FULLSET-BOX-NOTCH-CAP", (34,24,12), "optional add-on; one cap candidate per BBOX/CBOX inner/outer notch", "drip-resistant helper only; not waterproof; use silicone boot/gland/potting for real cable sealing"),

    # Phase A: split lower hull/flotation assist
    p("PS-RV2273G1-HULL-KEEL-F-A", "front/BBOX shallow boat-hull lower assist, A half", "A", "PETG/ASA", "HARD", 1, "HQG1-A-HULL-F-A", (220,116,34), "retrofit; v2.27 boxes unchanged", "split half; use joiner straps; seal or foam-fill before water tests"),
    p("PS-RV2273G1-HULL-KEEL-F-B", "front/BBOX shallow boat-hull lower assist, B half", "A", "PETG/ASA", "HARD", 1, "HQG1-A-HULL-F-B", (220,116,34), "retrofit; v2.27 boxes unchanged", "split half; dry-fit under LOWER-FRAME/FLT area"),
    p("PS-RV2273G1-HULL-KEEL-R-A", "rear/CBOX shallow boat-hull lower assist, A half", "A", "PETG/ASA", "HARD", 1, "HQG1-A-HULL-R-A", (220,116,34), "retrofit; v2.27 boxes unchanged", "split half; use joiner straps; avoid mud trap"),
    p("PS-RV2273G1-HULL-KEEL-R-B", "rear/CBOX shallow boat-hull lower assist, B half", "A", "PETG/ASA", "HARD", 1, "HQG1-A-HULL-R-B", (220,116,34), "retrofit; v2.27 boxes unchanged", "split half; dry-fit first"),
    p("PS-RV2273G1-HULL-LONG-JOINER-S", "hull split-line joiner strap set", "A", "PETG/ASA", "HARD", 8, "HQG1-A-MOUNTS", (78,22,8), "optional add-on; no box drilling", "strap/alignment only; do not rely on printed strap for field load"),
    p("PS-RV2273G1-HULL-FLT-SADDLE-S", "hull-to-existing-FLT receiver saddle set", "A", "PETG/ASA", "HARD", 4, "HQG1-A-MOUNTS", (70,36,34), "uses FLT-RCV / FLT-BRACKET area", "check tire sweep clearance before water tests"),

    # Phase B: material-saver wheel system.
    # v2274.6 replaces full-TPU wheels with HARD wheel hubs + minimal TPU tread rings.
    p("PS-RV2274-WHL-HUB-S", "shared PETG/PLA hard wheel hub/core with axle bore and TPU tread groove", "B", "PETG/ASA", "HARD", 4, "MS-B-HARD-WHEEL-HUB", (108,50,108), "replacement for full TPU wheel core; one hub per wheel", "HARD hub/core/axle bore; TPU is limited to external replaceable tread contact surface"),
    p("PS-RV2274-WHL-TPU-TREAD-S", "minimal TPU external tread ring only, shared wheel contact surface", "B", "TPU", "TPU", 4, "MS-B-TPU-TREAD-RING", (124,50,124), "replaceable TPU tread/contact surface only; fits over hard hub", "TPU only on replaceable tread contact surface; low lugs; no full-TPU wheel"),
    p("PS-RV2274-WHL-TPU-TREAD-HALF-S", "optional TPU half tread segment for lower-risk flexible printing", "B", "TPU", "TPU", 0, "MS-B-TPU-TREAD-HALF-OPTIONAL", (124,25,124), "optional alternative to full TPU tread ring; print instead of TREAD-S if ring is difficult", "OPTIONAL: not required when PS-RV2274-WHL-TPU-TREAD-S is used; lower print risk but more assembly work"),
    p("PS-RV2273G1-WHL-CLEARANCE-GAUGE-S", "wheel / float / gearbox clearance gauge set", "B", "PETG/ASA", "HARD", 2, "HQG1-B-GAUGE", (76,22,18), "dry-fit inspection tool", "HARD part even though notes mention wheel/tire"),

    # Phase C: v228 restart turtle shell / belly hull / front high PTO architecture.
    p("PS-RV228-TURTLE-SHELL-UPPER-F-L", "front upper turtle shell left split quarter", "C", "PETG/ASA", "HARD", 1, "V228R-C-UPPER-SHELL-F-L", (108,156,28), "front-left removable turtle shell quarter; split to fit safe 232mm dense packing", "secondary splash/mud/sun cover only; not waterproof; fixed core preserved; left/right split avoids oversize exclusion"),
    p("PS-RV228-TURTLE-SHELL-UPPER-F-R", "front upper turtle shell right split quarter", "C", "PETG/ASA", "HARD", 1, "V228R-C-UPPER-SHELL-F-R", (108,156,28), "front-right removable turtle shell quarter; split to fit safe 232mm dense packing", "secondary splash/mud/sun cover only; not waterproof; fixed core preserved; left/right split avoids oversize exclusion"),
    p("PS-RV228-TURTLE-SHELL-UPPER-R-L", "rear upper turtle shell left split quarter", "C", "PETG/ASA", "HARD", 1, "V228R-C-UPPER-SHELL-R-L", (108,156,28), "rear-left removable turtle shell quarter; split to fit safe 232mm dense packing", "secondary splash/mud/sun cover only; not waterproof; fixed core preserved; left/right split avoids oversize exclusion"),
    p("PS-RV228-TURTLE-SHELL-UPPER-R-R", "rear upper turtle shell right split quarter", "C", "PETG/ASA", "HARD", 1, "V228R-C-UPPER-SHELL-R-R", (108,156,28), "rear-right removable turtle shell quarter; split to fit safe 232mm dense packing", "secondary splash/mud/sun cover only; not waterproof; fixed core preserved; left/right split avoids oversize exclusion"),
    p("PS-RV228-BELLY-HULL-CENTER-F-L", "front lower belly hull left split quarter", "C", "PETG/ASA", "HARD", 1, "V228R-C-BELLY-HULL-F-L", (108,156,32), "front-left lower hull under BBOX; split to fit safe 232mm dense packing", "printed buoyancy needs sealing/coating/foam; dummy-weight water test only; split avoids oversized exclusion"),
    p("PS-RV228-BELLY-HULL-CENTER-F-R", "front lower belly hull right split quarter", "C", "PETG/ASA", "HARD", 1, "V228R-C-BELLY-HULL-F-R", (108,156,32), "front-right lower hull under BBOX; split to fit safe 232mm dense packing", "printed buoyancy needs sealing/coating/foam; dummy-weight water test only; split avoids oversized exclusion"),
    p("PS-RV228-BELLY-HULL-CENTER-R-L", "rear lower belly hull left split quarter", "C", "PETG/ASA", "HARD", 1, "V228R-C-BELLY-HULL-R-L", (108,156,32), "rear-left lower hull under CBOX; split to fit safe 232mm dense packing", "printed buoyancy needs sealing/coating/foam; dummy-weight water test only; split avoids oversized exclusion"),
    p("PS-RV228-BELLY-HULL-CENTER-R-R", "rear lower belly hull right split quarter", "C", "PETG/ASA", "HARD", 1, "V228R-C-BELLY-HULL-R-R", (108,156,32), "rear-right lower hull under CBOX; split to fit safe 232mm dense packing", "printed buoyancy needs sealing/coating/foam; dummy-weight water test only; split avoids oversized exclusion"),
    p("PS-RV228-BUOYANCY-CHAMBER-SIDE-L", "left side removable buoyancy chamber / shoulder float", "C", "PETG/ASA", "HARD", 2, "V228R-C-SIDE-BUOY-L", (38,132,34), "left side buoyancy around core; keep wheel opening clear", "secondary buoyancy; not guaranteed waterproof without sealing/coating/foam"),
    p("PS-RV228-BUOYANCY-CHAMBER-SIDE-R", "right side removable buoyancy chamber / shoulder float", "C", "PETG/ASA", "HARD", 2, "V228R-C-SIDE-BUOY-R", (38,132,34), "right side buoyancy around core; keep wheel opening clear", "secondary buoyancy; not guaranteed waterproof without sealing/coating/foam"),
    p("PS-RV228-SIDE-MOTOR-POD-MOUNT-L", "left upper side-wall motor pod mount", "C", "PETG/ASA", "HARD", 1, "V228R-C-SIDE-MOTOR-MOUNT-L", (52,72,46), "left motor pod attaches to upper side wall of waterproof box core, not on top face", "fixed core: motor box on upper side wall; high motor/electrical contacts"),
    p("PS-RV228-SIDE-MOTOR-POD-MOUNT-R", "right upper side-wall motor pod mount", "C", "PETG/ASA", "HARD", 1, "V228R-C-SIDE-MOTOR-MOUNT-R", (52,72,46), "right motor pod attaches to upper side wall of waterproof box core, not on top face", "fixed core: motor box on upper side wall; high motor/electrical contacts"),
    p("PS-RV228-FRONT-PTO-HIGH-MOUNT-S", "front high dual PTO output mount and splash cowl base", "C", "PETG/ASA", "HARD", 1, "V228R-C-FRONT-PTO-DUAL", (88,56,52), "front high-mounted dual PTO output module above expected waterline; two output ports for left/right motor power takeoff", "PTO is front/high; dual left/right output holes; do not put PTO in low belly hull"),
    p("PS-RV228-FRONT-PTO-FLOAT-MOUNT-S", "optional front PTO unit float mount pair", "C", "PETG/ASA", "HARD", 2, "V228R-C-FRONT-PTO-FLOAT-MOUNT", (54,34,18), "optional mount for PTO attachment float to reduce nose-down trim", "front PTO work units may need their own float; optional but recommended for heavy units"),
    p("PS-RV2273G1-SHELL-DOME-JOINER-S", "shell split-line joiner strap set", "C", "PETG/ASA", "HARD", 8, "HQG1-C-MOUNTS", (76,18,8), "optional shell alignment strap", "strap only; seal seam separately if water exposure is expected"),
    p("PS-RV2273G1-SHELL-FRONT-VISOR", "open PTO-side splash visor", "C", "PETG/ASA", "HARD", 1, "HQG1-C-CAPS", (188,42,32), "optional; do not block PTO", "sheds splash only; not waterproof seal"),
    p("PS-RV2273G1-SHELL-REAR-CAP", "optional rear cap with drain notches", "C", "PETG/ASA", "HARD", 1, "HQG1-C-CAPS", (190,18,68), "rear/CBOX side only", "avoid trapping water/mud; keep drain path"),
    p("PS-RV2273G1-SHELL-SPONSON-L-A", "left detachable side sponson float, A half", "C", "PETG/ASA", "HARD", 1, "HQG1-C-SPON-L-A", (48,116,44), "side add-on; no box drilling", "seal or foam-fill; check tire sweep"),
    p("PS-RV2273G1-SHELL-SPONSON-L-B", "left detachable side sponson float, B half", "C", "PETG/ASA", "HARD", 1, "HQG1-C-SPON-L-B", (48,116,44), "side add-on; no box drilling", "split half; print one side first"),
    p("PS-RV2273G1-SHELL-SPONSON-R-A", "right detachable side sponson float, A half", "C", "PETG/ASA", "HARD", 1, "HQG1-C-SPON-R-A", (48,116,44), "side add-on; no box drilling", "seal or foam-fill; check tire sweep"),
    p("PS-RV2273G1-SHELL-SPONSON-R-B", "right detachable side sponson float, B half", "C", "PETG/ASA", "HARD", 1, "HQG1-C-SPON-R-B", (48,116,44), "side add-on; no box drilling", "split half; print one side first"),
    p("PS-RV2273G1-SPONSON-JOINER-S", "sponson split-line joiner strap set", "C", "PETG/ASA", "HARD", 4, "HQG1-C-MOUNTS", (42,18,8), "optional sponson alignment strap", "do not make a mud trap"),
    p("PS-RV2273G1-MCR-CLAMP-S", "MCR rail retrofit clamp set", "C", "PETG/ASA", "HARD", 6, "HQG1-C-MOUNTS", (38,46,26), "clamp to MCR rail; do not crush box", "measure actual printed MCR rail before tightening"),
    p("PS-RV2273G1-RCP-DOGHOUSE-G3", "high sloped waterproof E-stop doghouse candidate", "C", "PETG/ASA", "HARD", 1, "HQG1-C-DOGHOUSE", (116,92,82), "candidate high E-stop housing", "requires real waterproof E-stop, cable gland, potting, drip loop"),

    # Phase D: internal inserts
    p("PS-RV2273G1-INT-WATER-SENSOR-SADDLE-S", "bottom water-detection sensor saddle set", "D", "PETG/ASA", "HARD", 4, "HQG1-D-INTERNAL", (52,20,10), "internal loose insert / adhesive mount", "no powered water tests without cutoff plan"),
    p("PS-RV2273G1-INT-PCB-SHELF-S", "removable raised PCB shelf / standoff plate", "D", "PETG/ASA", "HARD", 2, "HQG1-D-INTERNAL", (138,92,16), "internal removable shelf", "keeps PCB above first ingress water; still not waterproof"),
    p("PS-RV2273G1-INT-BAT-BAG-RAIL-S", "battery waterproof-bag retaining rail set", "D", "PETG/ASA", "HARD", 2, "HQG1-D-INTERNAL", (142,20,14), "internal battery bag rail", "avoid puncturing waterproof bag"),
    p("PS-RV2273G1-INT-FUSE-RELAY-TRAY", "main fuse / relay / BMS tray candidate", "D", "PETG/ASA", "HARD", 1, "HQG1-D-INTERNAL", (130,76,14), "internal removable electrical tray", "layout study only"),
]

# v228.1 dual PTO output:
# Remove legacy G1 retrofit shell/hull/sponson print targets that do not belong
# to the fixed-core turtle-hull restart layout.  This prevents unrelated parts
# and known floating-island-prone legacy pieces from entering dense output.
RETIRED_PRINT_TARGET_IDS = {
    "PS-RV2273G1-HULL-KEEL-F-A",
    "PS-RV2273G1-HULL-KEEL-F-B",
    "PS-RV2273G1-HULL-KEEL-R-A",
    "PS-RV2273G1-HULL-KEEL-R-B",
    "PS-RV2273G1-HULL-LONG-JOINER-S",
    "PS-RV2273G1-HULL-FLT-SADDLE-S",
    "PS-RV2274-WHL-TPU-TREAD-HALF-S",
    "PS-RV2273G1-SHELL-DOME-JOINER-S",
    "PS-RV2273G1-SHELL-FRONT-VISOR",
    "PS-RV2273G1-SHELL-REAR-CAP",
    "PS-RV2273G1-SHELL-SPONSON-L-A",
    "PS-RV2273G1-SHELL-SPONSON-L-B",
    "PS-RV2273G1-SHELL-SPONSON-R-A",
    "PS-RV2273G1-SHELL-SPONSON-R-B",
    "PS-RV2273G1-SPONSON-JOINER-S",
}
PARTS = [part for part in PARTS if part.part_id not in RETIRED_PRINT_TARGET_IDS]


DESIGN_CONTRACT = {
    "kit": KIT_NAME,
    "version": VERSION,
    "reference": REF,
    "common_parts_to_keep": [
        "PS-RV227-BBOX-BDY", "PS-RV227-BBOX-LID", "PS-RV227-BBOX-GSK",
        "PS-RV227-CBOX-BDY", "PS-RV227-CBOX-LID", "PS-RV227-CBOX-GSK",
        "PS-RV227-DBX-RC", "PS-RV227-DBX-PLG-S",
        "PS-WBX-MCR-L", "PS-WBX-MCR-R", "PS-WBX-MCR-LOC-S", "PS-WBX-MCR-WDG-S", "PS-WBX-MCR-LAT-S",
        "PS-RV227-RCP-BRKT", "PS-RV227-PTO", "PS-WCH-G1",
    ],
    "g1_split_policy": [
        "Long hull/shell/sponson parts are split into half-length A/B parts.",
        "Largest split shell footprint is about 196 x 116 x 74 mm, not 196 x 238 x 74 mm.",
        "prism_xz(length_y) uses length_y/2 with both=True so manifest length matches STL length.",
    ],
    "v2274_orientation_fix": [
        "Corrected from the earlier 150x200 body orientation to 200x150.",
        "Two boxes in front/rear series make about 200mm width x 300mm length.",
        "Wire-drop notches are on the 200mm wide front/rear faces, matching the user's field layout diagram.",
        "BBOX outer notch is the front/negative-Y wide face; BBOX inner notch is the rear/positive-Y wide face.",
        "CBOX inner notch is the front/negative-Y wide face; CBOX outer notch is the rear/positive-Y wide face.",
    ],
    "v2274_box_notch_policy": [
        "Each BBOX/CBOX body is 200 x 150 x 120 mm and has exactly two top-open rounded-bottom wire-drop notches on the 200 mm wide faces.",
        "Each box has one inner-side notch and one outer-side notch.",
        "This is not a two-notches-on-one-side design.",
        "Physical side placement follows the corrected one-notch-per-wide-front/rear-face policy for the 20cm-wide by 30cm-long two-box layout.",
        "No low horizontal side hole near water/mud.",
        "Notches are drip-resistant helper geometry only, not waterproof.",
        "Seal cable exits with silicone, boot, cable gland where possible, potting, and leak detection.",
        "Notch zones use steep >46-degree local drip/rib wedges only; broad internal top-wall ramps were removed to prevent supports inside the waterproof box.",
    ],
    "no_floating_parts_policy": [
        "No CAD part may contain a detached shell, floating panel, floating roof, or floating decorative label.",
        "Every generated solid must touch the bed in print orientation or intentionally overlap/fuse with its parent body.",
        "Rotated panels are avoided unless they are deeply overlapped into base/body geometry.",
        "Optional caps and covers must be generated in print-safe bed-touching orientation, even if they are mounted differently in use.",
        "Bambu Studio preview must be checked for floating islands before printing.",
    ],
    "shell_panel_policy": [
        "Shell is a support-free lightweight panel structure.",
        "No hollow dome with trapped support is allowed.",
        "Panels are printed flat on the bed and repaired/reprinted individually.",
        "Shell is a splash/mud/sun cover only, not a waterproof enclosure.",
        "Panel tabs and beads are fused upward from the panel; no floating tabs.",
    ],
    "material_saver_shell_policy": [
        "Shell/dome parts are replaced by support-free lightweight flat/faceted panel structures.",
        "Shell is a splash cover only, not a waterproof enclosure.",
        "Avoid closed cavities that trap water, mud, or support material.",
        "Use flat bed-printed panels, fused beads, perimeter ribs, and simple panel frames instead of hollow dome cavities.",
        "If Bambu Studio shows shell support, remove or simplify the panel bead/tab rather than using slicer support.",
    ],
    "tpu_minimization_policy": [
        "TPU is limited to replaceable tread/contact surfaces.",
        "Wheel hub/core/axle bore/spokes/flanges are HARD material.",
        "Do not generate full-TPU wheels as the standard model.",
        "TPU tread lugs must avoid floating side overhangs and support-heavy shapes.",
        "Optional half tread is provided for print-risk testing, but do not print both full ring and half ring for the same model unless comparing.",
    ],
    "internal_box_support_policy": [
        "Waterproof box interiors must avoid slicer-generated support structures.",
        "Do not add broad internal top-wall ramps inside BBOX/CBOX.",
        "Use only small local notch ribs, and make their slopes steeper than 46 degrees; this policy also applies to shell ribs and TPU tread lugs.",
        "If Bambu Studio shows support inside a box, remove or shrink the internal feature rather than relying on slicer settings.",
    ],
    "support_generation_policy": [
        "Slicer support avoidance is a first-class CAD requirement.",
        "All lateral protrusions must include their own printable ramp steeper than 46 degrees where possible; exact 45 degrees is avoided because Bambu Studio may still generate support.",
        "No side protrusion may start with an unsupported outward lower point.",
        "Prefer chamfers, triangular ramps, wedges, and fused ribs over horizontal blocks.",
        "Bambu Studio support preview must be checked before printing each major revision.",
    ],
    "dual_pto_output_policy": [
        "Front high PTO output uses two side-by-side output holes for left/right power takeoff.",
        "The two PTO holes are kept high and forward to reduce water ingestion risk.",
        "The front PTO mount is a layout/fit-check part, not a sealed gearbox.",
        "Metal/bearing/shaft dimensions are reference-only and must be finalized before load testing.",
        "Heavy PTO work units may require their own float to prevent nose-down trim.",
    ],
    "v228_compatibility_policy": [
        "v228 keeps PS-RV227-BBOX-* and PS-RV227-CBOX-* part IDs for v227-compatible fixed core boxes.",
        "New external modules use PS-RV228-* part IDs.",
        "Do not reinterpret v228 as permission to redesign the fixed core.",
        "BBOX/CBOX remain 200 x 150 x 120 with notches on the upper area of the 200mm wide front/rear wall faces.",
    ],
    "clean_restart_policy": [
        "Obsolete G1 retrofit hull/shell/sponson print targets are removed from this restart manifest.",
        "Shell and belly hull modules are sized around the fixed 200 x 150 x 120 mm BBOX/CBOX core.",
        "No cut-based hollowing is used in clean shell/belly/side buoy parts to avoid floating-looking slicer islands.",
        "reference_metal_stl is generated for printed surrogate shafts/rods in rigid_plus_metal output.",
        "Plastic metal-surrogate parts are for visual/fit-check only and must be replaced with real metal for load tests.",
    ],
    "dense_safe_split_policy": [
        "Upper turtle shell and lower belly hull are split left/right to stay under safe=232mm.",
        "This split does not modify the BBOX/CBOX fixed core.",
        "Oversized single shell/hull halves are not included as print targets.",
        "External shell/hull split seams are service seams, not waterproof seams.",
    ],
    "fixed_core_policy": [
        "Do not redesign the core without explicit owner approval.",
        "Fixed core is BBOX + CBOX in front/rear series, not side-by-side.",
        "BBOX/CBOX body dimensions remain 200mm wide x 150mm front/back x 120mm high.",
        "Wire-drop notches are on the upper area of the 200mm wide front/rear wall faces.",
        "Each BBOX/CBOX has one notch on each 200mm wide face: front and rear; no notch on the 150mm side faces.",
        "The v227 notch position is treated as rotated 90 degrees to match the correct 20cm-wide wall-face layout.",
        "Motor boxes mount on upper side walls of the waterproof boxes, not on the box top.",
        "Tires exit from the hull sides.",
    ],
    "front_high_pto_policy": [
        "PTO is moved to a high forward position.",
        "PTO output/coupler must not be placed in the low belly hull or expected waterline.",
        "Front PTO work units may need their own float to prevent nose-down trim.",
    ],
    "turtle_shell_belly_hull_policy": [
        "BBOX/CBOX are the primary waterproof enclosures.",
        "Upper turtle shell is secondary splash/mud/sun protection, not a waterproof enclosure.",
        "Lower belly hull provides secondary buoyancy and bottom protection.",
        "Printed buoyancy chambers require sealing/coating or foam filling before water tests.",
    ],
        "field_safety": [
        "Rice fields are income-producing land, not disposable test fields.",
        "Stage tests: slicer preview -> dry bench -> dry ground -> soft soil -> shallow mud -> dummy-weight tub test -> powered test only after independent cutoff and recovery plan.",
        "Never put electronics into first water tests; use dummy weights.",
        "Keep clear of grass cutting, kuro-nuri, planter, combine, and kei-truck paths.",
    ],
}

# ---------- CAD helpers ----------

def require_cadquery() -> None:
    if cq is None or exporters is None:
        raise RuntimeError(f"CadQuery is not available: {CADQUERY_IMPORT_ERROR}")

def place_on_bed(obj):
    bb = obj.val().BoundingBox()
    return obj.translate((0, 0, -bb.zmin))

def prism_xz(points: List[Tuple[float, float]], length_y: float):
    """Create an X-Z cross-section prism extruded along Y.

    IMPORTANT:
      length_y is the final total part length.
      CadQuery .extrude(d, both=True) produces 2*d total length, so use d=length_y/2.
    """
    return cq.Workplane("XZ").polyline(points).close().extrude(length_y / 2.0, both=True)


def prism_yz(points: List[Tuple[float, float]], length_x: float):
    """Create a Y-Z cross-section prism extruded along X.

    length_x is the final total part length.
    Use this for front/rear wall drip wedges so any lateral protrusion has a
    45-degree self-supporting underside rather than a horizontal overhang.
    """
    return cq.Workplane("YZ").polyline(points).close().extrude(length_x / 2.0, both=True)

def add_recess_label(obj, text: str):
    try:
        return obj.faces(">Z").workplane(centerOption="CenterOfBoundBox").text(text, 6, -0.35, combine="cut")
    except Exception:
        return obj

def cyl_y(radius: float, length: float):
    """Y-axis cylinder helper for rounded notch bottoms.

    Centered at origin.  Translate after creation.
    """
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(0, -length / 2.0, 0), cq.Vector(0, 1, 0))
    return cq.Workplane("XY").newObject([solid])



def cyl_x(radius: float, length: float):
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(-length / 2.0, 0, 0), cq.Vector(1, 0, 0))
    return cq.Workplane("XY").newObject([solid])

def cyl_z(radius: float, length: float):
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(0, 0, -length / 2.0), cq.Vector(0, 0, 1))
    return cq.Workplane("XY").newObject([solid])

def make_45deg_box_gusset_y(length_y: float, size: float):
    """Simple 45-degree triangular prism along Y.

    Used as a self-supporting rib under the box top edge.  It intentionally
    consumes a small amount of internal top volume to avoid slicer-generated
    support around the rim/notch transition.
    """
    pts = [(0, 0), (size, 0), (0, size)]
    return prism_xz(pts, length_y)


def rounded_wire_drop_notch_cut_y(face_y: float, side: str, width_x: float = 18.0, depth_y: float = 16.0, drop_z: float = 28.0, body_z: float = 120.0):
    """v2274 top-open rounded-bottom cable-only notch.

    Based on the v2.27 policy:
      - top-open U notch;
      - connector does not pass through the notch;
      - only bundled wires drop into the notch;
      - no low side hole near water/mud;
      - no upper bridge that would require support;
      - rounded bottom to protect cable insulation.

    side:
      front -> notch on negative-Y short side
      rear  -> notch on positive-Y short side
    """
    require_cadquery()
    radius = float(DIM["box_notch_bottom_radius"])
    z_top = body_z + 10.0
    z_bottom = body_z - float(drop_z)

    if side == "front":
        y_ext = face_y - 2.8
        y_int = face_y + depth_y
    elif side == "rear":
        y_ext = face_y + 2.8
        y_int = face_y - depth_y
    else:
        raise ValueError(f"side must be front/rear, got {side}")

    y_ctr = (y_ext + y_int) / 2.0
    y_len = abs(y_int - y_ext) + 1.4

    # Rectangular part opens upward beyond the body top; cylinder makes the U bottom.
    rect_h = max(1.0, z_top - (z_bottom + radius))
    rect = cq.Workplane("XY").box(width_x, y_len, rect_h).translate(
        (0, y_ctr, (z_top + z_bottom + radius) / 2.0)
    )
    round_bottom = cyl_y(radius, y_len).translate((0, y_ctr, z_bottom + radius))
    return rect.union(round_bottom)


def make_notch_drip_edge_y(face_y: float, side: str, x_ctr: float = 0.0):
    """Steep self-supporting exterior drip wedge below a notch.

    v2274.6 policy:
      - Bambu Studio may still support exact 45-degree slopes.
      - Therefore this wedge is steeper than 46 degrees, using about
        4 mm outward run over 7 mm rise.
      - The lowest point remains on the wall; outward material appears only
        as Z increases, so no support should be needed.

    This is drip-resistant helper geometry only, not a waterproof seal.
    """
    dx, _, _ = DIM["box_drip_edge_lwh"]
    dx = float(dx)
    run_y = 4.0
    rise_z = 7.0
    z0 = 120.0 - float(DIM["box_notch_drop"]) - 5.0

    if side == "front":
        pts = [
            (face_y, z0),
            (face_y, z0 + rise_z),
            (face_y - run_y, z0 + rise_z),
        ]
    elif side == "rear":
        pts = [
            (face_y, z0),
            (face_y, z0 + rise_z),
            (face_y + run_y, z0 + rise_z),
        ]
    else:
        raise ValueError(f"side must be front/rear, got {side}")

    return prism_yz(pts, dx).translate((x_ctr, 0, 0))


def make_notch_self_support_gussets_y(face_y: float, side: str, notch_width: float = 18.0):
    """Small local steep ribs beside a notch, not broad internal supports.

    v2274.6:
      Earlier internal ribs could trigger support inside the waterproof box.
      These are reduced to small local ramps beside the notch only.
      Slope is intentionally steeper than 46 degrees: about 5 mm run over
      9 mm rise.  They are fused to the wall/rim and should not create
      a large internal support field.
    """
    rise_z = 9.0
    run_y = 5.0
    length_x = 5.0
    x_offsets = [-(notch_width / 2.0 + 5.0), (notch_width / 2.0 + 5.0)]
    z_low = 120.0 - rise_z - 2.0
    z_high = 120.0 - 2.0
    out = None

    for x in x_offsets:
        if side == "front":
            pts = [
                (face_y + 4.0, z_low),
                (face_y + 4.0, z_high),
                (face_y + 4.0 + run_y, z_high),
            ]
        elif side == "rear":
            pts = [
                (face_y - 4.0, z_low),
                (face_y - 4.0, z_high),
                (face_y - 4.0 - run_y, z_high),
            ]
        else:
            raise ValueError(f"side must be front/rear, got {side}")

        tri = prism_yz(pts, length_x).translate((x, 0, 0))
        out = tri if out is None else out.union(tri)
    return out if out is not None else cq.Workplane("XY")


def make_support_safe_top_wall_gussets(x: float, y: float, z: float, wall: float):
    """No broad internal top-wall ramp.

    v2274.6 removes the continuous internal top-wall ramps because Bambu Studio
    generated support structures inside the waterproof box.  A vertical open-top
    box wall does not need slicer support by itself.  Only small local notch
    ribs are kept elsewhere.

    Return a tiny off-model no-op body to preserve call structure.
    """
    return cq.Workplane("XY").box(0.01, 0.01, 0.01).translate((9999, 9999, 9999))


def resolve_box_notch_positions_from_v227_reference(part_id: str):
    """Resolve v2274 notch meaning while preserving v2.27 side placement.

    v2.27 used exactly two top-open notches per printed box, one on each
    short/opposite side.  v2274 keeps the same physical two-side placement but names
    their operational meaning explicitly:

      BBOX front box:
        outer-side notch = front/negative-Y side
        inner-side notch = rear/positive-Y side facing the CBOX/center

      CBOX rear box:
        inner-side notch = front/negative-Y side facing the BBOX/center
        outer-side notch = rear/positive-Y side

    Geometry remains one notch on each short/opposite side, not two notches on
    one side.
    """
    is_bbox = "BBOX" in part_id
    if is_bbox:
        return [
            {"side": "front", "semantic": "OUTER_SIDE_NOTCH"},
            {"side": "rear", "semantic": "INNER_SIDE_NOTCH"},
        ]
    return [
        {"side": "front", "semantic": "INNER_SIDE_NOTCH"},
        {"side": "rear", "semantic": "OUTER_SIDE_NOTCH"},
    ]


def apply_inner_outer_wire_drop_notches(obj, part_id: str, x: float, y: float, z: float):
    """Cut v2274 BBOX/CBOX inner/outer wire-drop notches and add support/drip details."""
    notch_w = float(DIM["box_notch_width"])
    notch_depth = float(DIM["box_notch_depth_y"])
    notch_drop = float(DIM["box_notch_drop"])

    for cfg in resolve_box_notch_positions_from_v227_reference(part_id):
        side = cfg["side"]
        face_y = -y / 2.0 if side == "front" else y / 2.0
        obj = obj.cut(
            rounded_wire_drop_notch_cut_y(
                face_y,
                side,
                width_x=notch_w,
                depth_y=notch_depth,
                drop_z=notch_drop,
                body_z=z,
            )
        )
        obj = obj.union(make_notch_drip_edge_y(face_y, side, x_ctr=0.0))
        obj = obj.union(make_notch_self_support_gussets_y(face_y, side, notch_width=notch_w))
    return obj


def make_box_body_v2274(part_id: str):
    """v2274 printed waterproof-box body candidate.

    Keeps the v2.27 150 x 200 x 120 mm printed box envelope, but improves the
    wire-drop notches:
      - exactly two top-open rounded-bottom notches per box;
      - one inner-side and one outer-side notch per box;
      - not two notches on the same side;
      - no low horizontal side hole;
      - 45-degree triangular drip wedge and 45-degree-ish self-support rib features.

    This is drip-resistant geometry only, not a waterproof guarantee.
    """
    x, y, z = DIM["box_body_lwh"]
    wall = 4.0
    bottom = 4.0

    outer = cq.Workplane("XY").box(x, y, z).translate((0, 0, z / 2.0))
    inner = cq.Workplane("XY").box(x - 2*wall, y - 2*wall, z - bottom + 0.8).translate((0, 0, bottom + (z - bottom + 0.8)/2.0))
    body = outer.cut(inner)

    # Support-safe top rim: vertical land plus internal fused ribs.  Keep the
    # top plane usable for lid/gasket reference; do not make an overhanging lip.
    rim_h = 5.0
    rim_t = 4.0
    zc = z - rim_h / 2.0
    front = cq.Workplane("XY").box(x, rim_t, rim_h).translate((0, -y/2 + rim_t/2, zc))
    rear = cq.Workplane("XY").box(x, rim_t, rim_h).translate((0, y/2 - rim_t/2, zc))
    left = cq.Workplane("XY").box(rim_t, y, rim_h).translate((-x/2 + rim_t/2, 0, zc))
    right = cq.Workplane("XY").box(rim_t, y, rim_h).translate((x/2 - rim_t/2, 0, zc))
    body = body.union(front).union(rear).union(left).union(right)
    # v2274.6: broad internal top-wall ramps removed to prevent Bambu internal supports.
    # Local notch ribs are still applied in apply_inner_outer_wire_drop_notches().

    # Cut and label operational semantics in docs/manifest, not by fragile text
    # geometry on the body.
    body = apply_inner_outer_wire_drop_notches(body, part_id, x, y, z)

    # Internal loose-layout ribs; keep simple and fused to the floor.
    if "CBOX" in part_id:
        body = body.union(cq.Workplane("XY").box(4, 150, 4).translate((-44, -8, bottom + 2)))
        body = body.union(cq.Workplane("XY").box(4, 150, 4).translate((-22, -8, bottom + 2)))
        body = body.union(cq.Workplane("XY").box(58, 4, 4).translate((32, 48, bottom + 2)))
        body = body.union(cq.Workplane("XY").box(58, 4, 4).translate((32, -48, bottom + 2)))
    else:
        body = body.union(cq.Workplane("XY").box(4, 162, 4).translate((-28, 0, bottom + 2)))
        body = body.union(cq.Workplane("XY").box(4, 162, 4).translate((28, 0, bottom + 2)))
        body = body.union(cq.Workplane("XY").box(42, 4, 4).translate((48, 58, bottom + 2)))
        body = body.union(cq.Workplane("XY").box(42, 4, 4).translate((48, -58, bottom + 2)))

    return place_on_bed(add_recess_label(body, "v2274BOX"))


def make_box_lid_v2274(part_id: str):
    """v2274 lid keeps v2.27 fullset footprint while avoiding support-heavy cavities."""
    x, y, z = DIM["box_lid_lwh"]
    lid = cq.Workplane("XY").box(x, y, z)
    # Keep a shallow top rib only; avoid support-filled underside cavity.
    rib1 = cq.Workplane("XY").box(x - 42, 8, 2.5).translate((0, 0, z/2 + 1.25))
    rib2 = cq.Workplane("XY").box(8, y - 42, 2.5).translate((0, 0, z/2 + 1.25))
    lid = lid.union(rib1).union(rib2)
    return place_on_bed(add_recess_label(lid, "v2274LID"))


def make_box_gasket_v2274(part_id: str):
    """TPU gasket candidate.  Notch zones need separate sealing."""
    x, y, z = DIM["box_gasket_lwh"]
    gasket = cq.Workplane("XY").box(x, y, z)
    inner = cq.Workplane("XY").box(x - 16, y - 16, z + 1)
    gasket = gasket.cut(inner)
    return place_on_bed(gasket)


def make_notch_rain_cap(part_id: str):
    """Optional no-floating rain-cap candidate for one notch.

    v2274.6: the cap is printed as a bed-touching wedge/block, not as an
    elevated roof.  In use it can be mounted over a notch, but in print
    orientation every part of it grows upward from the bed.
    """
    x, y, z = DIM["box_rain_cap_lwh"]
    x = float(x)
    y = float(y)
    z = float(z)

    # Bed-touching rectangular base.
    base = cq.Workplane("XY").box(x, y, 3.0).translate((0, 0, 1.5))

    # 45-degree-ish roof wedge growing from the base.  This creates no floating
    # underside in print orientation.
    pts = [
        (-x/2, 3.0),
        ( x/2, 3.0),
        ( x/2 - min(8.0, x/3.0), z),
        (-x/2 + min(8.0, x/3.0), z),
    ]
    roof = prism_xz(pts, y).translate((0, 0, 0))

    # Fused rear locator foot; touches base, not floating.
    foot = cq.Workplane("XY").box(x - 8, 5, 5).translate((0, -y/2 + 3, 5.5))

    return place_on_bed(base.union(roof).union(foot))


def make_hull(part_id: str):
    w, l, h = DIM["hull_half_lwh"]
    top_z = h
    keel_z = 0
    keel_w = 42.0
    shoulder_w = w * 0.44
    pts = [
        (-w / 2, top_z), (-shoulder_w, top_z), (-keel_w / 2, keel_z),
        (keel_w / 2, keel_z), (shoulder_w, top_z), (w / 2, top_z),
    ]
    body = prism_xz(pts, l)
    pad_w, pad_l, pad_h = DIM["hull_crown_pad_lwh"]
    pad = cq.Workplane("XY").box(pad_w, pad_l, pad_h).translate((0, 0, h + pad_h / 2 - 0.3))
    body = body.union(pad)
    rail_l = l - 12
    rail = cq.Workplane("XY").box(8, rail_l, 8)
    body = body.union(rail.translate((-w / 2 + 6, 0, h - 5)))
    body = body.union(rail.translate(( w / 2 - 6, 0, h - 5)))
    # split-line flat tabs
    tab = cq.Workplane("XY").box(72, 8, 6)
    body = body.union(tab.translate((-46, l/2 - 5, h + 2)))
    body = body.union(tab.translate(( 46, l/2 - 5, h + 2)))
    body = body.union(tab.translate((-46, -l/2 + 5, h + 2)))
    body = body.union(tab.translate(( 46, -l/2 + 5, h + 2)))
    return place_on_bed(add_recess_label(body, part_id[-3:]))

def make_hull_joiner(part_id: str):
    x, y, z = DIM["hull_joiner_lwh"]
    obj = cq.Workplane("XY").box(x, y, z)
    for sx in [-1, 1]:
        obj = obj.faces(">Z").workplane(centerOption="CenterOfBoundBox").pushPoints([(sx * x * 0.28, 0)]).hole(3.4)
    return place_on_bed(obj)

def make_saddle(part_id: str):
    x, y, z = DIM["flt_saddle_lwh"]
    obj = cq.Workplane("XY").box(x, y, z)
    obj = obj.faces(">Z").workplane(centerOption="CenterOfBoundBox").rect(x - 18, y - 14).cutBlind(-8)
    return place_on_bed(obj)

def make_clearance_gauge(part_id: str):
    obj = cq.Workplane("XY").box(76, 22, 6)
    obj = obj.union(cq.Workplane("XY").box(10, 18, 10).translate((-24, 0, 8)))
    obj = obj.union(cq.Workplane("XY").box(12, 18, 12).translate((0, 0, 9)))
    obj = obj.union(cq.Workplane("XY").box(14, 18, 14).translate((26, 0, 10)))
    return place_on_bed(obj)

def make_wheel_hub(part_id: str):
    """Hard PETG/PLA wheel hub/core for the material-saver wheel.

    The hub provides axle bore, disc/spokes, side flanges, and a shallow outer
    groove for the TPU tread.  It is explicitly HARD even though its notes may
    mention tire/tread.
    """
    outer_r = DIM["wheel_hub_outer_d"] / 2.0
    width = DIM["wheel_width"]
    bore_r = 6.0

    # Main hard wheel core.
    core = cq.Workplane("XZ").circle(outer_r).circle(bore_r).extrude(width / 2.0, both=True)

    # Side flanges that retain the TPU tread.  Avoid reverse dovetails.
    flange_r = outer_r + 2.2
    flange_t = 4.0
    left = cq.Workplane("XZ").circle(flange_r).circle(outer_r - 4.0).extrude(flange_t / 2.0, both=True).translate((0, -width/2 + flange_t/2, 0))
    right = cq.Workplane("XZ").circle(flange_r).circle(outer_r - 4.0).extrude(flange_t / 2.0, both=True).translate((0, width/2 - flange_t/2, 0))
    body = core.union(left).union(right)

    # Lightweight radial spokes as hard ribs.  These reduce solid infill while
    # preserving a printable one-piece core.
    for i in range(8):
        a = 360.0 * i / 8
        spoke = cq.Workplane("XY").box(outer_r * 0.86, 5.0, 7.0)
        spoke = spoke.translate((outer_r * 0.28, 0, 0)).rotate((0, 0, 0), (0, 1, 0), a)
        body = body.union(spoke)

    # Shallow anti-slip keys for TPU ring.  They are vertical/raised lands, not
    # reverse undercuts, so they should print without support.
    for i in range(12):
        a = 360.0 * i / 12
        key = cq.Workplane("XY").box(5.0, width - 10.0, 4.0)
        key = key.translate((outer_r - 1.5, 0, 0)).rotate((0, 0, 0), (0, 1, 0), a)
        body = body.union(key)

    return place_on_bed(add_recess_label(body, "HUB"))


def make_tpu_tread_ring(part_id: str):
    """Minimal TPU tread/contact ring only.

    TPU is limited to the replaceable contact surface.  The ring has low,
    support-safe lugs.  No full TPU wheel core is generated.
    """
    outer_r = DIM["wheel_tpu_tread_outer_d"] / 2.0
    inner_r = DIM["wheel_tpu_tread_inner_d"] / 2.0
    width = DIM["wheel_tpu_tread_width"]
    lug_h = DIM["wheel_tread_lug_h"]

    ring = cq.Workplane("XZ").circle(outer_r).circle(inner_r).extrude(width / 2.0, both=True)

    # Low lugs: radial blocks, no horizontal floating side paddles.
    for i in range(16):
        a = 360.0 * i / 16
        lug = cq.Workplane("XY").box(8.0, width - 6.0, lug_h)
        lug = lug.translate((outer_r + lug_h/2.0 - 0.5, 0, 0)).rotate((0, 0, 0), (0, 1, 0), a)
        ring = ring.union(lug)

    return place_on_bed(add_recess_label(ring, "TPU"))


def make_tpu_tread_half(part_id: str):
    """Optional TPU half tread segment.

    This is generated as a simpler bed-touching half-ring-like segment for users
    who have trouble printing a full TPU ring.  It is optional; do not print both
    TREAD-S and TREAD-HALF-S for the same model unless deliberately testing.
    """
    outer_r = DIM["wheel_tpu_tread_outer_d"] / 2.0
    inner_r = DIM["wheel_tpu_tread_inner_d"] / 2.0
    width = DIM["wheel_tpu_tread_width"]
    lug_h = DIM["wheel_tread_lug_h"]

    # Approximate half ring by subtracting a half-space from a full ring.
    full = cq.Workplane("XZ").circle(outer_r).circle(inner_r).extrude(width / 2.0, both=True)
    cutter = cq.Workplane("XY").box(outer_r * 3, width * 2, outer_r * 3).translate((-outer_r * 1.5, 0, 0))
    half = full.cut(cutter)

    for i in range(8):
        a = 180.0 * i / 8
        lug = cq.Workplane("XY").box(8.0, width - 6.0, lug_h)
        lug = lug.translate((outer_r + lug_h/2.0 - 0.5, 0, 0)).rotate((0, 0, 0), (0, 1, 0), a)
        half = half.union(lug)

    # Flat join ears, bed-safe.
    ear = cq.Workplane("XY").box(10, width - 8, 4)
    half = half.union(ear.translate((0, 0, outer_r - 2)))
    half = half.union(ear.translate((0, 0, -outer_r + 2)))

    return place_on_bed(add_recess_label(half, "H-TPU"))


def make_wheel(part_id: str):
    # Compatibility dispatcher for any legacy wheel id that might remain.
    if "TPU-TREAD-HALF" in part_id:
        return make_tpu_tread_half(part_id)
    if "TPU-TREAD" in part_id:
        return make_tpu_tread_ring(part_id)
    return make_wheel_hub(part_id)


def make_shell_panel_top(part_id: str):
    """Support-free lightweight top shell panel.

    This is a flat/faceted bed-printed panel, not a hollow dome.  It uses
    shallow raised beads and edge ribs for stiffness, all grown from the bed
    or parent panel so Bambu Studio should not need support.
    """
    x, y, z = DIM["shell_panel_top_lwh"]
    plate = cq.Workplane("XY").box(x, y, z).translate((0, 0, z/2))

    # Trim to a mild turtle/faceted octagonal panel.
    c = 14.0
    pts = [(-x/2+c, -y/2), (x/2-c, -y/2), (x/2, -y/2+c), (x/2, y/2-c),
           (x/2-c, y/2), (-x/2+c, y/2), (-x/2, y/2-c), (-x/2, -y/2+c)]
    panel = cq.Workplane("XY").polyline(pts).close().extrude(z)

    # Fused edge ribs. Vertical ribs print without support.
    rib_h = 3.0
    rib_w = 5.0
    panel = panel.union(cq.Workplane("XY").box(x-18, rib_w, rib_h).translate((0, -y/2 + 7, z + rib_h/2)))
    panel = panel.union(cq.Workplane("XY").box(x-18, rib_w, rib_h).translate((0,  y/2 - 7, z + rib_h/2)))
    panel = panel.union(cq.Workplane("XY").box(rib_w, y-18, rib_h).translate((-x/2 + 7, 0, z + rib_h/2)))
    panel = panel.union(cq.Workplane("XY").box(rib_w, y-18, rib_h).translate(( x/2 - 7, 0, z + rib_h/2)))

    # Low center bead / solar-pad candidate. No underside, no hollow pocket.
    panel = panel.union(cq.Workplane("XY").box(x-48, y-44, 1.0).translate((0, 0, z + 0.5)))
    panel = panel.union(cq.Workplane("XY").box(8, y-34, 2.0).translate((-22, 0, z + 1.0)))
    panel = panel.union(cq.Workplane("XY").box(8, y-34, 2.0).translate(( 22, 0, z + 1.0)))

    return place_on_bed(add_recess_label(panel, "TOP"))


def make_shell_panel_side(part_id: str):
    """Support-free lightweight side shell panel.

    Printed flat as a faceted plate with fused ribs.  The visual slope is
    represented by outline/facet beads, not by an overhanging 3D dome.
    """
    x, y, z = DIM["shell_panel_side_lwh"]
    c1 = 10.0
    c2 = 20.0
    # Trapezoid/hex side profile printed flat.
    pts = [(-x/2+c1, -y/2), (x/2-c2, -y/2), (x/2, -y/2+c2),
           (x/2-c1, y/2), (-x/2+c2, y/2), (-x/2, y/2-c2)]
    panel = cq.Workplane("XY").polyline(pts).close().extrude(z)

    rib_h = 2.8
    # Fused perimeter/diagonal beads; all raised upward from panel.
    panel = panel.union(cq.Workplane("XY").box(x-20, 4, rib_h).translate((0, -y/2 + 8, z + rib_h/2)))
    panel = panel.union(cq.Workplane("XY").box(x-26, 4, rib_h).translate((0,  y/2 - 8, z + rib_h/2)))
    diag = cq.Workplane("XY").box(5, y*0.72, rib_h).translate((0, 0, z + rib_h/2)).rotate((0,0,0), (0,0,1), 18)
    panel = panel.union(diag)
    diag2 = cq.Workplane("XY").box(5, y*0.52, rib_h).translate((18, 0, z + rib_h/2)).rotate((0,0,0), (0,0,1), -18)
    panel = panel.union(diag2)

    # Flat mounting tabs in-plane, not floating side tabs.
    tab = cq.Workplane("XY").box(22, 10, z).translate((-x/2 + 14, 0, z/2))
    panel = panel.union(tab)

    return place_on_bed(add_recess_label(panel, "SIDE"))


def make_shell_panel_frame(part_id: str):
    """Simple bed-flat rib/frame connector for panel shell.

    This is not a dome and not a closed frame pocket.  It is a flat locator
    that can be reprinted independently if broken.
    """
    x, y, z = DIM["shell_panel_frame_lwh"]
    base = cq.Workplane("XY").box(x, y, 3.0).translate((0, 0, 1.5))
    cut = cq.Workplane("XY").box(x-26, y-24, 5.0).translate((0, 0, 2.5))
    frame = base.cut(cut)

    # Cross ribs that touch the frame, no floating island.
    frame = frame.union(cq.Workplane("XY").box(8, y-18, z).translate((-24, 0, z/2)))
    frame = frame.union(cq.Workplane("XY").box(8, y-18, z).translate(( 24, 0, z/2)))
    frame = frame.union(cq.Workplane("XY").box(x-18, 8, z).translate((0, 0, z/2)))

    # Small round lightening holes in the crossbar; cuts only.
    for sx in [-1, 1]:
        try:
            hole = cq.Workplane("XY").cylinder(2.0, z+1).translate((sx*50, 0, z/2))
            frame = frame.cut(hole)
        except Exception:
            pass

    return place_on_bed(add_recess_label(frame, "FRM"))


def make_shell(part_id: str):
    """Material-saver open-bottom turtle shell.

    v2274.6 replaces the old near-solid dome with a thin open-bottom shell.
    It is a splash/sun/mud cover only, not a waterproof enclosure.

    Printability policy:
      - open bottom, no closed trapped cavity;
      - exterior faceted shape kept;
      - interior is cut out from below;
      - only rim rails and small vertical ribs remain;
      - no broad internal ceiling supports;
      - no floating panels/labels.
    """
    w, l, h = DIM["shell_half_lwh"]
    crown_w = DIM["shell_crown_w"]
    skirt = DIM["shell_skirt_h"]
    shell_t = 3.0
    rim_t = 5.0

    pts = [
        (-w/2, 0), (-w/2, skirt), (-w*0.36, h*0.68), (-crown_w/2, h),
        (crown_w/2, h), (w*0.36, h*0.68), (w/2, skirt), (w/2, 0),
    ]
    body = prism_xz(pts, l)

    # Large bottom-up interior cut.  This is intentionally simple and open, not
    # a closed shell() operation, so support cannot be trapped inside.
    inner_pts = [
        (-w/2 + shell_t, 1.5),
        (-w/2 + shell_t, skirt - shell_t),
        (-w*0.36 + shell_t, h*0.68 - shell_t),
        (-crown_w/2 + shell_t, h - shell_t),
        (crown_w/2 - shell_t, h - shell_t),
        (w*0.36 - shell_t, h*0.68 - shell_t),
        (w/2 - shell_t, skirt - shell_t),
        (w/2 - shell_t, 1.5),
    ]
    inner = prism_xz(inner_pts, l - 2 * rim_t).translate((0, 0, 0.2))
    body = body.cut(inner)

    # Perimeter rails / mounting lands. These are fused and bed-oriented.
    rail = cq.Workplane("XY").box(10, l - 12, 8)
    body = body.union(rail.translate((-w/2 + 8, 0, 5)))
    body = body.union(rail.translate(( w/2 - 8, 0, 5)))

    # Narrow split seam tabs. Keep them small to avoid material waste.
    tab = cq.Workplane("XY").box(58, 8, 5)
    body = body.union(tab.translate((-38, l/2 - 5, 7)))
    body = body.union(tab.translate(( 38, l/2 - 5, 7)))
    body = body.union(tab.translate((-38, -l/2 + 5, 7)))
    body = body.union(tab.translate(( 38, -l/2 + 5, 7)))

    # Small top pad only, not a thick filled roof.
    solar_pad = cq.Workplane("XY").box(crown_w - 14, l - 34, 1.2).translate((0, 0, h + 0.6))
    body = body.union(solar_pad)

    # Two small vertical internal ribs that are printable as walls, not ceilings.
    rib = cq.Workplane("XY").box(3.0, l - 34, max(8.0, h * 0.36))
    body = body.union(rib.translate((-crown_w * 0.22, 0, 3 + max(8.0, h * 0.36)/2)))
    body = body.union(rib.translate(( crown_w * 0.22, 0, 3 + max(8.0, h * 0.36)/2)))

    return place_on_bed(add_recess_label(body, "MSH"))


def make_shell_joiner(part_id: str):
    x, y, z = DIM["shell_joiner_lwh"]
    obj = cq.Workplane("XY").box(x, y, z)
    for sx in [-1, 1]:
        obj = obj.faces(">Z").workplane(centerOption="CenterOfBoundBox").pushPoints([(sx * x * 0.25, 0)]).hole(3.4)
    return place_on_bed(obj)

def make_visor(part_id: str):
    x, y, z = DIM["front_visor_lwh"]
    pts = [(-x/2, 0), (-x/2, z*0.45), (-x*0.32, z), (x*0.32, z), (x/2, z*0.45), (x/2, 0)]
    return place_on_bed(prism_xz(pts, y))

def make_rear_cap(part_id: str):
    x, y, z = DIM["rear_cap_lwh"]
    obj = cq.Workplane("XY").box(x, y, z)
    for sx in [-1, 1]:
        notch = cq.Workplane("XY").box(34, y + 2, 12).translate((sx * 48, 0, -z/2 + 5))
        obj = obj.cut(notch)
    return place_on_bed(obj)

def make_sponson(part_id: str):
    x, y, z = DIM["side_sponson_half_lwh"]
    c = 12.0
    pts = [(-x/2 + c, 0), (x/2 - c, 0), (x/2, c), (x/2, z - c), (x/2 - c, z), (-x/2 + c, z), (-x/2, z - c), (-x/2, c)]
    body = prism_xz(pts, y)
    tab = cq.Workplane("XY").box(14, 32, 10)
    for sy in [-0.28, 0.28]:
        body = body.union(tab.translate((0, sy * y, z * 0.55)))
    return place_on_bed(add_recess_label(body, "SPN"))

def make_sponson_joiner(part_id: str):
    x, y, z = DIM["sponson_joiner_lwh"]
    obj = cq.Workplane("XY").box(x, y, z)
    obj = obj.faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(3.4)
    return place_on_bed(obj)

def make_mcr_clamp(part_id: str):
    x, y, z = DIM["mcr_clamp_lwh"]
    obj = cq.Workplane("XY").box(x, y, z)
    relief = cq.Workplane("XY").box(20, y + 2, 15).translate((0, 0, -z/2 + 6))
    return place_on_bed(obj.cut(relief))

def make_doghouse(part_id: str):
    """No-floating, support-safe E-stop doghouse candidate.

    v2274.6 replaces the earlier rotated sloped panel/hood construction because
    Bambu Studio could show a detached slanted shell.  This version is built from
    base-fused solids only:
      - broad base touches the bed;
      - rear wall grows from the base;
      - side buttresses grow from the base;
      - top rain visor is supported by 45-degree buttresses and overlaps the wall.

    It is a layout/cover candidate, not a waterproof switch assembly.
    """
    x, y, z = DIM["doghouse_lwh"]

    base = cq.Workplane("XY").box(x, y, 8).translate((0, 0, 4))

    # Rear vertical wall fused deeply into the base.
    wall_h = z * 0.62
    rear_wall = cq.Workplane("XY").box(x, 10, wall_h).translate((0, y/2 - 5, 8 + wall_h/2 - 0.4))

    # Front lower sill, fused to base; avoids a floating face/panel.
    sill = cq.Workplane("XY").box(x - 18, 10, 18).translate((0, -y/2 + 10, 8 + 9 - 0.4))

    # Two 45-degree side buttresses from base toward rear wall.
    buttress_len = y - 26
    buttress_h = 34
    pts = [
        (-buttress_len/2, 0),
        ( buttress_len/2, 0),
        ( buttress_len/2, buttress_h),
    ]
    left_b = prism_xz(pts, 8).rotate((0,0,0),(0,0,1),90).translate((-x/2 + 14, 0, 8))
    right_b = prism_xz(pts, 8).rotate((0,0,0),(0,0,1),90).translate(( x/2 - 14, 0, 8))

    # Top visor: rectangular cap overlapped into rear wall and buttresses.
    # It is not a free-floating roof; it is supported from below by buttresses.
    visor = cq.Workplane("XY").box(x - 8, 28, 7).translate((0, y/2 - 18, 8 + wall_h - 2))

    # Central low boss placeholder for a real waterproof E-stop gland/cable boot.
    boss = cq.Workplane("XY").box(42, 10, 18).translate((0, -y/2 + 15, 8 + 9))

    obj = base.union(rear_wall).union(sill).union(left_b).union(right_b).union(visor).union(boss)

    # Small recessed switch center marker; cut only, no raised island.
    try:
        marker = cq.Workplane("XY").cylinder(1.4, 16).rotate((0,0,0),(1,0,0),90).translate((0, -y/2 + 9, 28))
        obj = obj.cut(marker)
    except Exception:
        pass

    return place_on_bed(obj)


def make_internal(part_id: str):
    if "WATER-SENSOR" in part_id:
        base = cq.Workplane("XY").box(52, 20, 4)
        clip = cq.Workplane("XY").box(38, 8, 6).translate((0, 0, 5))
        return place_on_bed(base.union(clip))
    if "PCB-SHELF" in part_id:
        obj = cq.Workplane("XY").box(138, 92, 3)
        for sx in [-1, 1]:
            for sy in [-1, 1]:
                obj = obj.union(cq.Workplane("XY").box(10, 10, 13).translate((sx*56, sy*34, 8)))
        return place_on_bed(obj)
    if "BAT-BAG" in part_id:
        rail = cq.Workplane("XY").box(142, 20, 6)
        lip = cq.Workplane("XY").box(142, 4, 10).translate((0, 8, 5))
        return place_on_bed(rail.union(lip))
    if "FUSE-RELAY" in part_id:
        obj = cq.Workplane("XY").box(130, 76, 4)
        obj = obj.union(cq.Workplane("XY").box(118, 6, 10).translate((0, -31, 6)))
        obj = obj.union(cq.Workplane("XY").box(118, 6, 10).translate((0, 31, 6)))
        return place_on_bed(obj)
    return place_on_bed(cq.Workplane("XY").box(20, 20, 5))



def make_restart_turtle_shell_split(part_id: str):
    """Clean split upper turtle shell quarter.

    This is a simple support-safe faceted cap.  Earlier versions used a
    bottom-up boolean cut to hollow the shell; in slicer preview that could
    leave a floating-looking internal island.  This clean version avoids
    cut-based hollowing and uses only fused solids.

    It is a secondary splash/mud/sun cover, not a waterproof enclosure.
    """
    x, y, z = DIM["restart_turtle_upper_quarter_lwh"]
    crown_w = x * 0.66
    skirt = 5.0

    pts = [
        (-x/2, 0), (-x/2, skirt),
        (-x*0.40, z*0.58), (-crown_w/2, z),
        ( crown_w/2, z), ( x*0.40, z*0.58),
        ( x/2, skirt), ( x/2, 0),
    ]
    shell = prism_xz(pts, y)

    # Seam flange on the inner split side; overlaps the shell body.
    seam_x = x/2 - 5 if part_id.endswith("-L") else -x/2 + 5
    shell = shell.union(cq.Workplane("XY").box(7, y-18, 6).translate((seam_x, 0, 4)))

    # Front/rear service rails, overlapped.
    shell = shell.union(cq.Workplane("XY").box(x-16, 5, 5).translate((0, -y/2+7, 3)))
    shell = shell.union(cq.Workplane("XY").box(x-16, 5, 5).translate((0,  y/2-7, 3)))

    # Shallow top bead / turtle panel line, overlapping the cap top.
    shell = shell.union(cq.Workplane("XY").box(max(12, crown_w-14), y-34, 1.4).translate((0, 0, z-0.2)))
    return place_on_bed(add_recess_label(shell, "V228C"))


def make_restart_belly_hull_split(part_id: str):
    """Clean split lower belly hull quarter.

    This is a support-safe lower skid / belly-float candidate.  It avoids large
    cavity cuts in the CAD because those caused confusing floating-looking
    slicer artifacts.  Real buoyancy must be confirmed by coating, sealing, or
    foam filling; first water tests use dummy weights only.
    """
    x, y, z = DIM["restart_belly_hull_quarter_lwh"]

    pts = [
        (-x/2, z*0.66), (-x*0.42, z), (x*0.42, z), (x/2, z*0.66),
        (x*0.28, 0), (-x*0.28, 0),
    ]
    hull = prism_xz(pts, y)

    # Seam flange and keel/ribs, all overlapped into the hull.
    seam_x = x/2 - 5 if part_id.endswith("-L") else -x/2 + 5
    hull = hull.union(cq.Workplane("XY").box(7, y-18, 6).translate((seam_x, 0, 4)))
    hull = hull.union(cq.Workplane("XY").box(12, y-22, 7).translate((0, 0, 3.5)))
    for yy in [-y*0.28, 0, y*0.28]:
        hull = hull.union(cq.Workplane("XY").box(x-26, 6, 7).translate((0, yy, 3.5)))
    return place_on_bed(add_recess_label(hull, "V228H"))


def make_restart_turtle_shell(part_id: str):
    """Upper turtle shell half.

    Removable secondary splash cover. It is not the primary waterproof enclosure.
    The fixed BBOX/CBOX core remains unchanged below it.
    """
    x, y, z = DIM["restart_turtle_upper_half_lwh"]
    crown_w = x * 0.62
    skirt = 8.0
    pts = [
        (-x/2, 0), (-x/2, skirt),
        (-x*0.40, z*0.58), (-crown_w/2, z),
        ( crown_w/2, z), ( x*0.40, z*0.58),
        ( x/2, skirt), ( x/2, 0),
    ]
    shell = prism_xz(pts, y)
    # open underside cut to avoid trapped support; keep ribs/edges.
    inner = prism_xz([
        (-x/2+4, 2), (-x/2+4, skirt-2),
        (-x*0.40+4, z*0.58-4), (-crown_w/2+4, z-4),
        ( crown_w/2-4, z-4), ( x*0.40-4, z*0.58-4),
        ( x/2-4, skirt-2), ( x/2-4, 2),
    ], max(4.0, y-10))
    shell = shell.cut(inner)

    # Perimeter service rails, fused and support-safe.
    shell = shell.union(cq.Workplane("XY").box(x-20, 5, 5).translate((0, -y/2+7, 4)))
    shell = shell.union(cq.Workplane("XY").box(x-20, 5, 5).translate((0,  y/2-7, 4)))
    shell = shell.union(cq.Workplane("XY").box(5, y-20, 5).translate((-x/2+8, 0, 4)))
    shell = shell.union(cq.Workplane("XY").box(5, y-20, 5).translate(( x/2-8, 0, 4)))
    # Shallow top bead / solar-pad candidate.
    shell = shell.union(cq.Workplane("XY").box(crown_w-24, y-36, 1.2).translate((0, 0, z+0.6)))
    return place_on_bed(add_recess_label(shell, "V228S"))


def make_restart_belly_hull(part_id: str):
    """Lower belly hull half.

    Open-top printed hull / buoyancy candidate.  Not a guaranteed waterproof
    float unless sealed/coated/foam-filled.  It sits below the fixed core.
    """
    x, y, z = DIM["restart_belly_hull_half_lwh"]
    pts = [
        (-x/2, z*0.62), (-x*0.44, z), (x*0.44, z), (x/2, z*0.62),
        (x*0.34, 0), (-x*0.34, 0),
    ]
    hull = prism_xz(pts, y)

    # Open top service cavity; do not make one huge sealed tub in the CAD.
    cavity = cq.Workplane("XY").box(x-34, y-24, z+3).translate((0, 0, z*0.55))
    hull = hull.cut(cavity)

    # Longitudinal keel and cross ribs, all fused.
    hull = hull.union(cq.Workplane("XY").box(20, y-22, 7).translate((0, 0, 3.5)))
    for yy in [-y*0.28, 0, y*0.28]:
        hull = hull.union(cq.Workplane("XY").box(x-40, 6, 7).translate((0, yy, 3.5)))
    return place_on_bed(add_recess_label(hull, "HULL"))


def make_restart_side_buoy(part_id: str):
    """Clean side shoulder buoyancy chamber candidate.

    Simple fused solids only.  Printed chamber is not guaranteed waterproof
    without sealing/coating/foam filling.
    """
    x, y, z = DIM["restart_side_buoy_lwh"]
    body = cq.Workplane("XY").box(x, y, z).translate((0, 0, z/2))

    # Support-safe top ridge and end pads, overlapped into the main body.
    body = body.union(cq.Workplane("XY").box(8, y-20, 6).translate((0, 0, z-2)))
    body = body.union(cq.Workplane("XY").box(x-8, 12, 6).translate((0, -y/2+10, z-2)))
    body = body.union(cq.Workplane("XY").box(x-8, 12, 6).translate((0,  y/2-10, z-2)))
    return place_on_bed(add_recess_label(body, "BUOY"))


def make_restart_side_motor_mount(part_id: str):
    """Upper side-wall motor pod mount.

    v228.2 fix:
    - remove the floating slanted side pieces seen in slicer preview;
    - every rib must overlap both the bed-touching base and the rear wall;
    - keep the bracket as a high side-wall mount, not a top mount.
    """
    x, y, z = DIM["restart_motor_mount_lwh"]
    base = cq.Workplane("XY").box(x, y, 8).translate((0, 0, 4))
    wall = cq.Workplane("XY").box(x, 10, z).translate((0, y/2-5, z/2))

    # Two side buttresses built as YZ-profile ramps and extruded along X.
    # The profile intentionally overlaps the base at z=8 and the wall around
    # y ~= y/2-5 so no disconnected/floating island remains.
    buttress_profile = [(0, 0), (14, 22), (14, 0)]
    b1 = prism_yz(buttress_profile, 8).translate((-x/2 + 10, y/2 - 22, 8))
    b2 = prism_yz(buttress_profile, 8).translate(( x/2 - 10, y/2 - 22, 8))

    # Rear boss overlaps the wall and grows upward from supported geometry.
    boss = cq.Workplane("XY").box(30, 14, 18).translate((0, y/2-14, 18))
    obj = base.union(wall).union(b1).union(b2).union(boss)
    return place_on_bed(add_recess_label(obj, "MTR-S"))


def make_restart_front_pto_high_mount(part_id: str):
    """Front high dual PTO output mount / splash cowl.

    v228.1 restores the PTO output concept to two high forward ports:
    - left output port
    - right output port

    These are layout / fit-check holes for left/right motor power takeoff.
    This is not a sealed gearbox and not a final bearing design.
    """
    x, y, z = DIM["restart_front_pto_high_lwh"]
    base = cq.Workplane("XY").box(x, y, 8).translate((0, 0, 4))
    upright = cq.Workplane("XY").box(x*0.70, 14, z).translate((0, y/2-7, z/2))
    nose = cq.Workplane("XY").box(x*0.62, 24, 24).translate((0, -y/2+14, 21))

    # Two high output ports, side-by-side across X.
    # Axis is along Y, so these appear as two front-facing holes.
    port_r = 5.2
    port_spacing = 26.0
    try:
        left_port = cyl_y(port_r, y+6).translate((-port_spacing/2.0, -2, 23))
        right_port = cyl_y(port_r, y+6).translate(( port_spacing/2.0, -2, 23))
        nose = nose.cut(left_port).cut(right_port)
    except Exception:
        pass

    # Two raised bosses around the ports, fused into the nose.
    boss_l = cq.Workplane("XY").box(20, 8, 20).translate((-port_spacing/2.0, -y/2+3, 23))
    boss_r = cq.Workplane("XY").box(20, 8, 20).translate(( port_spacing/2.0, -y/2+3, 23))

    # Support-safe splash cowl roof: grows upward/back.
    cowl = prism_yz([( -y/2+4, 20), (-y/2+4, 40), (-y/2+24, 40)], x*0.76)

    # Center divider/strength rib between two PTO ports.
    divider = cq.Workplane("XY").box(5, 22, 22).translate((0, -y/2+12, 22))

    obj = base.union(upright).union(nose).union(boss_l).union(boss_r).union(divider).union(cowl)
    return place_on_bed(add_recess_label(obj, "2PTO"))


def make_restart_front_pto_float_mount(part_id: str):
    """Optional front PTO unit float mount."""
    x, y, z = DIM["restart_front_float_mount_lwh"]
    obj = cq.Workplane("XY").box(x, y, z).translate((0, 0, z/2))
    obj = obj.union(cq.Workplane("XY").box(x-10, 6, 5).translate((0, 0, z+2.5)))
    return place_on_bed(add_recess_label(obj, "PTO-F"))


def builder_for(part_id: str):
    if part_id in {
        "PS-RV228-TURTLE-SHELL-UPPER-F-L", "PS-RV228-TURTLE-SHELL-UPPER-F-R",
        "PS-RV228-TURTLE-SHELL-UPPER-R-L", "PS-RV228-TURTLE-SHELL-UPPER-R-R",
    }:
        return make_restart_turtle_shell_split
    if part_id in {
        "PS-RV228-BELLY-HULL-CENTER-F-L", "PS-RV228-BELLY-HULL-CENTER-F-R",
        "PS-RV228-BELLY-HULL-CENTER-R-L", "PS-RV228-BELLY-HULL-CENTER-R-R",
    }:
        return make_restart_belly_hull_split
    if part_id in {"PS-RV228-BUOYANCY-CHAMBER-SIDE-L", "PS-RV228-BUOYANCY-CHAMBER-SIDE-R"}:
        return make_restart_side_buoy
    if part_id in {"PS-RV228-SIDE-MOTOR-POD-MOUNT-L", "PS-RV228-SIDE-MOTOR-POD-MOUNT-R"}:
        return make_restart_side_motor_mount
    if part_id == "PS-RV228-FRONT-PTO-HIGH-MOUNT-S":
        return make_restart_front_pto_high_mount
    if part_id == "PS-RV228-FRONT-PTO-FLOAT-MOUNT-S":
        return make_restart_front_pto_float_mount
    if part_id in {"PS-RV227-BBOX-BDY", "PS-RV227-CBOX-BDY"}:
        return make_box_body_v2274
    if part_id in {"PS-RV227-BBOX-LID", "PS-RV227-CBOX-LID"}:
        return make_box_lid_v2274
    if part_id in {"PS-RV227-BBOX-GSK", "PS-RV227-CBOX-GSK"}:
        return make_box_gasket_v2274
    if part_id == "PS-RV2273v2274-BOX-NOTCH-RAIN-CAP-S":
        return make_notch_rain_cap
    if "HULL-KEEL" in part_id:
        return make_hull
    if "HULL-LONG-JOINER" in part_id:
        return make_hull_joiner
    if "HULL-FLT-SADDLE" in part_id:
        return make_saddle
    if part_id == "PS-RV2274-WHL-HUB-S":
        return make_wheel_hub
    if part_id == "PS-RV2274-WHL-TPU-TREAD-S":
        return make_tpu_tread_ring
    if part_id == "PS-RV2274-WHL-TPU-TREAD-HALF-S":
        return make_tpu_tread_half
    if "WHL-PADDLE" in part_id:
        return make_wheel
    if "WHL-CLEARANCE" in part_id:
        return make_clearance_gauge
    if part_id == "PS-RV2274-SHELL-PANEL-TOP-S":
        return make_shell_panel_top
    if part_id in {"PS-RV2274-SHELL-PANEL-SIDE-L-S", "PS-RV2274-SHELL-PANEL-SIDE-R-S"}:
        return make_shell_panel_side
    if part_id == "PS-RV2274-SHELL-PANEL-FRAME-S":
        return make_shell_panel_frame
    if "SHELL-DOME-" in part_id:
        return make_shell
    if "SHELL-DOME-JOINER" in part_id:
        return make_shell_joiner
    if "SHELL-FRONT-VISOR" in part_id:
        return make_visor
    if "SHELL-REAR-CAP" in part_id:
        return make_rear_cap
    if "SHELL-SPONSON" in part_id:
        return make_sponson
    if "SPONSON-JOINER" in part_id:
        return make_sponson_joiner
    if "MCR-CLAMP" in part_id:
        return make_mcr_clamp
    if "RCP-DOGHOUSE" in part_id:
        return make_doghouse
    if "-INT-" in part_id:
        return make_internal
    raise KeyError(f"No builder for {part_id}")

# ---------- manifest / docs ----------

def write_csv(path: Path, rows: Iterable[dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)

def manifest_rows() -> List[dict]:
    rows = []
    for part in PARTS:
        rows.append({
            "part_no": part.part_id,
            "part_id": part.part_id,
            "part_code": part.part_id,
            "label": part.part_id,
            "label_text": part.part_id,
            "name": part.description,
            "part_name": part.description,
            "qty": part.qty,
            "quantity": part.qty,
            "count": part.qty,
            "material": part.material,
            "material_hint": part.material_group,
            "material_group": part.material_group,
            "group": part.material_group,
            "is_tpu": "1" if part.material_group == "TPU" else "0",
            "split_group": part.material_group,
            "plate_id": part.plate_group,
            "plate": part.plate_group,
            "plate_group": part.plate_group,
            "module": "common_rover_v228_1_dual_pto_output",
            "phase": part.phase,
            "title": part.description,
            "stl": f"stl/{part.filename_stl}",
            "stl_file": f"stl/{part.filename_stl}",
            "stl_path": f"stl/{part.filename_stl}",
            "file": f"stl/{part.filename_stl}",
            "filename": part.filename_stl,
            "path": f"stl/{part.filename_stl}",
            "file_path": f"stl/{part.filename_stl}",
            "source_file": f"stl/{part.filename_stl}",
            "source_path": f"stl/{part.filename_stl}",
            "output_stl": f"stl/{part.filename_stl}",
            "step": f"step/{part.filename_step}",
            "step_file": f"step/{part.filename_step}",
            "step_path": f"step/{part.filename_step}",
            "bbox_x": f"{part.bbox_mm[0]:.3f}",
            "bbox_y": f"{part.bbox_mm[1]:.3f}",
            "bbox_z": f"{part.bbox_mm[2]:.3f}",
            "printable": "1",
            "marked": "1",
            "compatibility": part.compatibility,
            "notes": part.notes,
            "optional": "1" if (part.qty == 0 or "OPTIONAL" in part.notes.upper() or "OPTIONAL" in part.part_id.upper()) else "0",
        })
    return rows

def plate_rows() -> List[dict]:
    groups: Dict[str, List[str]] = {}
    material: Dict[str, str] = {}
    phase: Dict[str, str] = {}
    for part in PARTS:
        groups.setdefault(part.plate_group, []).append(part.part_id)
        material[part.plate_group] = part.material_group
        phase[part.plate_group] = part.phase
    return [
        {
            "plate_id": pg,
            "material_group": material[pg],
            "phase": phase[pg],
            "items": "; ".join(ids),
            "notes": "G1 split; dense tool may pack further; verify in Bambu Studio",
        }
        for pg, ids in groups.items()
    ]

def write_docs(out: Path) -> None:
    (out / "paddy_swarm_v228_1_dual_pto_output_design_contract.json").write_text(
        json.dumps(DESIGN_CONTRACT, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    readme = rf"""# {KIT_NAME}

Version: `{VERSION}`

v2.27.4 is a box-notch orientation fix of the G1/v2274 fullset.  It keeps the G1 split hull,
split turtle shell, split sponsons, TPU tire candidates, and internal insert
parts, while improving BBOX/CBOX body cable passages.

## GitHub v2.27 reference used

The v2.27 reference design states that each printed box body has exactly two
top-open cable notches, one on each short/opposite side.  Two boxes total means
four ports.  The connector crosses over the open lid edge; only bundled wires
drop into the notch.  v2.27.4 corrects the physical orientation so each box is 200 mm wide and 150 mm front/back; the notches are on the 200 mm wide front/rear faces.

## v2.27.4 BBOX/CBOX notch rule

Each 200 x 150 x 120 mm box has exactly two top-open rounded-bottom wire-drop notches on the 200 mm wide faces:

- `INNER_SIDE_NOTCH`: the side facing the other box / rover center.
- `OUTER_SIDE_NOTCH`: the side facing the outside/end of the rover.

This is **not** a two-notches-on-one-side design.

Operational mapping:

- BBOX/front box, 200 mm wide face:
  - front / negative-Y side = `OUTER_SIDE_NOTCH`
  - rear / positive-Y side = `INNER_SIDE_NOTCH`
- CBOX/rear box, 200 mm wide face:
  - front / negative-Y side = `INNER_SIDE_NOTCH`
  - rear / positive-Y side = `OUTER_SIDE_NOTCH`

## Notch shape

- top-open U-style wire drop notch
- rounded/U bottom, no sharp bottom corner
- cable-bundle sized; connector does not pass through the notch
- no low horizontal hole near water/mud
- 45-degree triangular drip wedge
- local 45-degree triangular self-support/gusset geometry near notch and top wall

This is **drip-resistant helper geometry only**, not a waterproof guarantee.

The notch zones still require practical sealing such as:

- silicone
- cable boot
- cable gland where possible
- potting
- drip loop
- leak detection

## Shell panel policy

The shell is now a support-free lightweight panel structure.  It is not a
hollow dome and it is not a waterproof enclosure.  Panels are intended to print
flat on the bed with no trapped support, and broken panels can be reprinted
individually.

## Material saver shell policy

The shell/dome parts are open-bottom hollow shells.  They are material saver
splash covers only, not waterproof enclosures.  The design avoids trapped
support, trapped water, and closed mud pockets.

## TPU minimization policy

TPU is limited to the replaceable tread/contact surface.

- wheel hub/core/axle bore: HARD material
- external tread ring/contact lugs: TPU material

Do not print the old full-TPU wheel unless deliberately comparing prototypes.

## Clean restart notes

This clean version removes obsolete G1 retrofit shell/hull/sponson print targets
from the v228 restart manifest.  The old parts were not fitted to the new fixed
core turtle-hull layout and could appear as unrelated loose blocks on dense
plates.

The upper turtle shell and lower belly hull are intentionally smaller and
simpler than the previous concept parts.  They are external modules around the
200 x 150 x 120 mm BBOX/CBOX fixed core, not replacements for the boxes.

When CadQuery export is run, `reference_metal_stl/` is also generated with
plastic surrogate shaft/rod models for `rigid_plus_metal` dense output.  These
are fit-check placeholders only, not load-bearing metal.

## Dense-safe split shell / hull policy

The upper turtle shell and lower belly hull are split left/right because the
single half parts were at or above the safe 232mm dense packing limit.  This
does not change the fixed core.  It only splits the external shell/hull modules
to avoid oversized print-target exclusion.

## v228.1 dual PTO output policy

The high front PTO returns to a two-output layout.  The front PTO mount has two
high forward output holes intended as left/right power takeoff ports.  This is a
layout and fit-check design, not a final sealed gearbox or final bearing design.

- left PTO output hole
- right PTO output hole
- both stay high, away from the expected waterline
- the PTO unit must not be placed in the low belly hull
- heavy front PTO work units may need their own float

## v228 compatibility note

v228 is a restart/release version for the external turtle-hull/front-PTO layout.
The BBOX/CBOX core remains v227-compatible and keeps the `PS-RV227-BBOX-*` and
`PS-RV227-CBOX-*` part IDs to protect already printed and already planned core
parts.  New external shell, belly hull, side motor mount, buoyancy, and front PTO
parts use `PS-RV228-*` IDs.

## v228 restart fixed core policy

This generator returns to the v227 fixed-core rule:

- BBOX + CBOX are arranged front/rear in series, not side-by-side.
- The correct box body orientation is 200 mm wide x 150 mm front/back x 120 mm high.
- Wire-drop notches are on the upper area of the 200 mm wide front/rear wall faces.
- Each BBOX/CBOX has one notch on each 200 mm wide face: front and rear.
- Do not put notches on the 150 mm side faces.
- The old v227 notch orientation must be treated as rotated 90 degrees.
- Motor boxes mount high on the waterproof box side walls, not on box top.
- PTO is front/high.
- Tires exit from the hull sides.

## Turtle shell / belly hull policy

BBOX/CBOX are the primary waterproof enclosures.  The upper turtle shell and
lower belly hull are secondary splash protection, bottom protection, and
buoyancy aids.  Printed buoyancy chambers are not guaranteed waterproof without
sealing/coating/foam filling.

## Dense maxpack command

```powershell
python .\paddy_swarm_a1_dense_project_tools_v5_7_3_model_sets_paddy_fix.py --manifest .\rover_v228_1_dual_pto_output_out\print_manifest_generic_marked.csv --out .\rover_v228_1_dual_pto_output_model_dense_sets --group-mode all --ignore-manifest-plates --split-tpu --safe 240 --support-orient-fit-safe 244 --gap 4 --bambu-template-plate-inner-margin 12 --bambu-plate-inner-margin 12 --make-3mf --make-bambu-template-project-3mf --bambu-template-3mf .\blank_a1_plates_4.3mf --make-zip
```

## Safety

- Do not use real electronics in first water tests.
- Use dummy weights.
- Keep E-stop visible and reachable.
- Do not block PTO.
- Do not drill into BBOX/CBOX for first retrofit testing.
- Rice fields are income-producing land; test in stages before any field use.
"""
    (out / "README_v228_1_dual_pto_output.md").write_text(readme, encoding="utf-8")

def write_manifests(out: Path, rows: List[dict]) -> None:
    fields = [
        "part_no", "part_id", "part_code", "label", "label_text", "name", "part_name",
        "qty", "quantity", "count", "material", "material_hint", "material_group", "group",
        "is_tpu", "split_group", "plate_id", "plate", "plate_group", "module", "phase", "title",
        "stl", "stl_file", "stl_path", "file", "filename", "path", "file_path", "source_file", "source_path", "output_stl",
        "step", "step_file", "step_path", "bbox_x", "bbox_y", "bbox_z", "printable", "marked", "compatibility", "notes", "optional",
    ]
    write_csv(out / "print_manifest.csv", rows, fields)
    write_csv(out / "print_manifest_generic_marked.csv", rows, fields)
    write_csv(out / "plate_manifest.csv", plate_rows(), ["plate_id", "material_group", "phase", "items", "notes"])

def export_parts(out: Path, metadata_only: bool = False) -> List[dict]:
    rows = manifest_rows()
    if metadata_only:
        return rows
    require_cadquery()
    stl_dir = out / "stl"
    step_dir = out / "step"
    stl_dir.mkdir(parents=True, exist_ok=True)
    step_dir.mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        obj = builder_for(part.part_id)(part.part_id)
        exporters.export(obj, str(stl_dir / part.filename_stl))
        exporters.export(obj, str(step_dir / part.filename_step))
    export_reference_metal_stl(out)
    return rows


def export_reference_metal_stl(out: Path) -> None:
    """Export printable rigid surrogate models for metal shafts/rods.

    These are not real metal parts.  They exist so dense_rigid_plus_metal can
    include visible shaft/rod placeholders in a complete fit-check model.
    Replace with real shafts/bearings/fasteners for load or water tests.
    """
    require_cadquery()
    metal_dir = out / "reference_metal_stl"
    metal_dir.mkdir(parents=True, exist_ok=True)

    refs = {
        "REF-METAL-LEFT-DRIVE-SHAFT.stl": cyl_y(3.0, 185.0),
        "REF-METAL-RIGHT-DRIVE-SHAFT.stl": cyl_y(3.0, 185.0),
        "REF-METAL-FRONT-AXLE-ROD.stl": cyl_x(3.0, 210.0),
        "REF-METAL-REAR-AXLE-ROD.stl": cyl_x(3.0, 210.0),
        "REF-METAL-FRONT-PTO-LEFT-SHAFT.stl": cyl_y(3.0, 74.0).translate((-13.0, 0, 0)),
        "REF-METAL-FRONT-PTO-RIGHT-SHAFT.stl": cyl_y(3.0, 74.0).translate((13.0, 0, 0)),
        "REF-METAL-COUPLER-PIN-SET.stl": cyl_z(2.5, 32.0),
    }
    for name, obj in refs.items():
        exporters.export(place_on_bed(obj), str(metal_dir / name))

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def make_zip(out: Path) -> Path:
    zip_path = out.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(out.rglob("*")):
            if path.is_file():
                z.write(path, path.relative_to(out.parent))
    (out / "SHA256SUMS.txt").write_text(f"{sha256_file(zip_path)}  {zip_path.name}\n", encoding="utf-8")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(out.rglob("*")):
            if path.is_file():
                z.write(path, path.relative_to(out.parent))
    return zip_path

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="rover_v228_2_dual_pto_output_fix_out")
    ap.add_argument("--metadata-only", action="store_true")
    ap.add_argument("--make-zip", action="store_true")
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = export_parts(out, metadata_only=args.metadata_only)
    write_manifests(out, rows)
    write_docs(out)
    try:
        src = Path(__file__)
        (out / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass
    if args.make_zip:
        zip_path = make_zip(out)
        print(f"Wrote {zip_path}")
    print(f"Wrote {out}")
    if args.metadata_only and CADQUERY_IMPORT_ERROR is not None:
        print(f"metadata-only mode; CadQuery not used: {CADQUERY_IMPORT_ERROR}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
