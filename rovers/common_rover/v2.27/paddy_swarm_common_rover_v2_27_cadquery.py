#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Paddy Swarm Common Rover v2.27 CadQuery generator

Fresh v2.27 baseline with top-open wire-drop notches and no cable guide beads for dual printed boxes.

Target commands:
  conda activate paddy-cad
  python paddy_swarm_common_rover_v2_25_cadquery.py --out rover_v227_out --manifests manifests --make-zip

Dense command:
  python paddy_swarm_a1_dense_project_tools_v5_7.py --manifest .\rover_v227_out\print_manifest_generic_marked.csv --out .\rover_v227_dense_v5_7_model --group-mode all --split-tpu --make-model-dense-sets --make-3mf --make-bambu-template-project-3mf --bambu-template-3mf .\blank_a1_plates.3mf --make-zip

Design goals:
- No legacy floating labels on open-top box bodies.
- Dual printed boxes: CBOX and BBOX, each 150 x 200 x 120 mm outer target.
- Each printed box body has exactly two top-open cable notches: one on each short/opposite side.
  Two boxes total = four ports.
- External protruding collars around the ports are not used.
- Slot cross-section slopes downward from inner high side to outer low side so water escapes outward.
- Slots are placed near the upper wall under the lid/raincoat area and are cable-bundle sized; connectors cross over the open lid edge before the lid closes.
- v2.27 removes separate cable guide ribs; the notch itself is the only body-side cable passage.
- Cable protection uses internal raised wipe/guide ribs only.
- Box labels are placed only on solid lids or solid floors, never over open-air body cavities.
- Commercial-box mode remains represented by a 300 x 200 x 120 mm reference envelope, excluded from print manifest.
- Print-focused cradle uses slide rails, wedges, latches, low hold-downs, and no required metal screws for printed joints.
- Gear case is represented as a functional serviceable assembly: cavities, cover, gear, idler, pins, axis rods references.

- v2.27 support-reduction policy:
  * Use 45-degree chamfer-like edges instead of rounded fillet-heavy rims where practical.
  * CBOX/BBOX bodies keep the open-top wire-drop U notch, but box rims are built from vertical support-safe bars.
  * Lids are flat support-safe panels; underside lips/grooves that create support-filled cavities are avoided.
  * Raincoat/hood parts are open-bottom 45-degree roof panels, not closed box roofs.
  * Dense orientation should keep open boxes upright and rain covers in their print-safe orientation.
  * 凸 labels disabled; recessed labels only on selected large flat hard parts, otherwise manifest-managed.
  * v2.27 adds sacrificial sprue bases to small multi-piece sets so every shell touches the bed.
  * v2.27 replaces horizontal printable rods/wheels with support-clean vertical/flat variants.
  * Rain/hood parts are generated in print-flat orientation as connected solids; usage angle is handled by mounting.
  * v2.27 is a clean rebuild from v2.18 with chassis/cradle tabs overlapped into parent bodies so no preview-floating tabs remain.
  * v2.27 fuses the motor-pod cable boss into the cap/body with deliberate overlap; no side boss floating island.
  * v2.27 keeps recessed labels on external flat/top faces only; no box-internal floor labels.
  * v2.27 fixes final print blockers: DRC mud-wash slots are true cut-only grooves, not loose blocks; GBOX shaft markers are recessed cuts, not raised discs.
  * v2.27 hardens the no-floating-island rule: lower frame uses one continuous undertray; gears/sprockets/wheels use fused spokes/discs.
  * v2.27 replaces printable rod surrogates with base-fused rectangular low-load rods to avoid raised rod islands.
  * v2.27 writes solid-count and optional STL mesh-component reports after export.
  * v2.27 fixes LOWER-FRAME floating islands by forcing every boss/pad to overlap the parent frame by at least 0.3 mm.
  * v2.27 adds an export-time CadQuery solid-count report to catch accidental multi-solid floating islands earlier.
  * v2.27 adds a clearly visible one-piece LOWER-FRAME undercarriage so the wheelbase is not mistaken for small rails.
  * v2.27 adds printable gearbox internal gear models, sprocket/pulley models, TPU belt loops, and float brackets for a fuller lower drivetrain mockup.
  * v2.27 adds printable wheelbase, axle carriers, visible drive path modules, floats, and a shallow boat/skid hull for a low-load moving model.
  * v2.27 keeps real field testing separate: printed rods/drive path are for assembly and low-load model motion only.
  * v2.27 adds PS-RV227-NP-PADDY-SWARM, a recessed-label test nameplate.
  * Horizontal cylinders/buttons on panels are avoided in favor of vertical, support-safe discs.

Notes:
- Printed box waterproofing still requires post-processing: PETG/ASA, epoxy sealing, urethane coating,
  gasket, compression latch/wedge, PS-WCH-G1, IP67 connectors, conformal coating, leak detection.
- Metal rods are reference/BOM only and are not included in the print manifest.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    import cadquery as cq
    from cadquery import exporters
except Exception as exc:  # pragma: no cover
    cq = None
    exporters = None
    CADQUERY_IMPORT_ERROR = exc
else:
    CADQUERY_IMPORT_ERROR = None

VERSION = "v2.27"
VERSION_TAG = "v227"

DESIGN = {
    "project": "Paddy Swarm Project",
    "part_family": "Common Rover Body",
    "version": VERSION,
    "units": "mm",
    "row_spacing_target": 300.0,
    "total_width_max_allowed": 300.0,
    "printed_box_outer_lwh": [150.0, 200.0, 120.0],
    "commercial_box_reference_lwh": [200.0, 300.0, 120.0],
    "box_wall": 4.0,
    "box_bottom": 4.0,
    "top_open_notch_count_per_box": 2,
    "top_open_notch_count_total_two_boxes": 4,
    "top_open_notch_w_depth": [14.0, 13.0],
    "top_open_notch_bottom_z": 104.0,
    "top_open_notch_slope_deg": 45.0,
    "slot_water_path": "top-open notch: connector passes over open lid edge; only bundled wires occupy the notch; bottom is rounded and lower/exterior side is treated as water escape; no upper bridge",
    "printed_joint_policy": "slide rails, wedges, latches, snap/retainer features before metal screws",
    "commercial_box_mode": "300x200x120mm class purchased IP65-IP67 box, reference only",
    "printed_box_mode": "150x200x120mm CBOX + 150x200x120mm BBOX, front/rear placement on rover",
    "transport_height_rule": "box height 120mm target; top protrusions <= +8mm standard, <= +12mm absolute upper limit",
    "water_depth_design_check": "15cm water depth plus mud sink-in requires flotation before real water operation; printed box height alone is not treated as safe freeboard",
    "flotation_mount_policy": "provide removable front/rear and inboard side float receivers; keep flotation within 300mm row-spacing envelope where possible; final float volume is determined by tank test",
}

FUSE_OVERLAP_MM = 0.30  # v2.27: minimum intentional overlap for attached features

@dataclass
class PartSpec:
    part_no: str
    name: str
    material: str
    material_group: str
    qty: int
    plate_id: str
    stl_name: str
    bbox_lwh_mm: Tuple[float, float, float]
    print_target: bool
    notes: str

# One row per STL file. qty is intentionally 1 because dense tools expand STL rows.
PARTS: List[PartSpec] = [
    # Core split chassis / cradle
    PartSpec("PS-RV227-CHS-FL", "front-left split chassis with female slide slot", "PETG", "HARD", 1, "A1-HARD-01", "PS-RV227-CHS-FL.stl", (118, 178, 22), True, "printed chassis quadrant; v2.27 fused tabs; no metal screw dependency"),
    PartSpec("PS-RV227-CHS-FR", "front-right split chassis with female slide slot", "PETG", "HARD", 1, "A1-HARD-01", "PS-RV227-CHS-FR.stl", (118, 178, 22), True, "printed chassis quadrant; v2.27 fused tabs"),
    PartSpec("PS-RV227-CHS-RL", "rear-left split chassis with female slide slot", "PETG", "HARD", 1, "A1-HARD-01", "PS-RV227-CHS-RL.stl", (118, 178, 22), True, "printed chassis quadrant; v2.27 fused tabs"),
    PartSpec("PS-RV227-CHS-RR", "rear-right split chassis with female slide slot", "PETG", "HARD", 1, "A1-HARD-01", "PS-RV227-CHS-RR.stl", (118, 178, 22), True, "printed chassis quadrant; v2.27 fused tabs"),
    PartSpec("PS-WBX-MCR-L", "multi-cradle left rail for commercial or dual printed boxes", "PETG", "HARD", 1, "A1-HARD-02", "PS-WBX-MCR-L.stl", (18, 430, 18), True, "slide rail + fused low hold-down geometry"),
    PartSpec("PS-WBX-MCR-R", "multi-cradle right rail for commercial or dual printed boxes", "PETG", "HARD", 1, "A1-HARD-02", "PS-WBX-MCR-R.stl", (18, 430, 18), True, "slide rail + fused low hold-down geometry"),
    PartSpec("PS-WBX-MCR-LOC-S", "front/rear adjustable locator set", "PETG", "HARD", 1, "A1-HARD-02", "PS-WBX-MCR-LOC-S.stl", (120, 28, 22), True, "locator blocks for 300x200x120 or dual 150x200x120 boxes"),
    PartSpec("PS-WBX-MCR-WDG-S", "printed wedge key set for box cradle", "PETG", "HARD", 1, "A1-HARD-02", "PS-WBX-MCR-WDG-S.stl", (92, 52, 12), True, "no metal screw wedge locks"),
    PartSpec("PS-WBX-MCR-LAT-S", "printed latch key set for low hold-downs", "PETG", "HARD", 1, "A1-HARD-02", "PS-WBX-MCR-LAT-S.stl", (82, 48, 14), True, "low top protrusion latch keys"),
    PartSpec("PS-WBX-MCR-GAUGE", "transport rack height interference gauge", "PETG", "HARD", 1, "A1-HARD-02", "PS-WBX-MCR-GAUGE.stl", (170, 18, 16), True, "checks HCS-G1 roof rack clearance"),

    # Dual printed boxes
    PartSpec("PS-RV227-CBOX-BDY", "printed control/drive waterproof box body", "PETG", "HARD", 1, "A1-HARD-03", "PS-RV227-CBOX-BDY.stl", (150, 200, 120), True, "two top-open wire-drop notches with bottom-only rounded cable guide; no floating body label"),
    PartSpec("PS-RV227-CBOX-LID", "printed control/drive box lid with gasket groove", "PETG", "HARD", 1, "A1-HARD-03", "PS-RV227-CBOX-LID.stl", (166, 216, 16), True, "support-safe flat lid; solid lid label OK"),
    PartSpec("PS-RV227-BBOX-BDY", "printed power/battery waterproof box body", "PETG", "HARD", 1, "A1-HARD-03", "PS-RV227-BBOX-BDY.stl", (150, 200, 120), True, "two top-open wire-drop notches with bottom-only rounded cable guide; no floating body label"),
    PartSpec("PS-RV227-BBOX-LID", "printed power/battery box lid with gasket groove", "PETG", "HARD", 1, "A1-HARD-03", "PS-RV227-BBOX-LID.stl", (166, 216, 16), True, "support-safe flat lid; solid lid label OK"),
    PartSpec("PS-RV227-CBOX-GSK", "TPU gasket for control box lid", "TPU", "TPU", 1, "A1-TPU-01", "PS-RV227-CBOX-GSK.stl", (154, 204, 3), True, "TPU/EPDM gasket candidate"),
    PartSpec("PS-RV227-BBOX-GSK", "TPU gasket for battery box lid", "TPU", "TPU", 1, "A1-TPU-01", "PS-RV227-BBOX-GSK.stl", (154, 204, 3), True, "TPU/EPDM gasket candidate"),
    PartSpec("PS-RV227-DBX-RC", "low raincoat seam cover for dual box seam", "PETG", "HARD", 1, "A1-HARD-03", "PS-RV227-DBX-RC.stl", (160, 54, 18), True, "support-clean flat shingle raincoat cover; usage angle by mounting"),
    PartSpec("PS-RV227-DBX-PLG-S", "TPU sloped slot plug set", "TPU", "TPU", 1, "A1-TPU-01", "PS-RV227-DBX-PLG-S.stl", (96, 28, 6), True, "support-clean plug set on sacrificial sprue base"),

    # Control/drive details
    PartSpec("PS-RCP-G1", "rear high-mounted control panel", "PETG", "HARD", 1, "A1-HARD-04", "PS-RCP-G1.stl", (170, 28, 58), True, "real switch hole panel: 23mm E-stop, 17mm buttons, LED/buzzer holes, rear potting cups"),
    PartSpec("PS-RV227-RCP-BRKT", "raised top-access bracket for RCP-G1 control panel", "PETG", "HARD", 1, "A1-HARD-04", "PS-RV227-RCP-BRKT.stl", (98, 42, 56), True, "separates E-stop access from PTO face; mounts control panel above box edge with front/rear bolt slots"),
    PartSpec("PS-WCH-G1", "wa-shaped rain return cable hood", "PETG", "HARD", 1, "A1-HARD-04", "PS-WCH-G1.stl", (92, 70, 42), True, "support-clean flat shingle cable hood; usage angle by mounting"),
    PartSpec("PS-RV227-PTO", "front two-port PTO panel with bayonet lugs", "PETG", "HARD", 1, "A1-HARD-04", "PS-RV227-PTO.stl", (162, 24, 72), True, "support-clean face-up PTO representation; PTO stays on front lower face and is separated from emergency-stop controls"),
    PartSpec("PS-RV227-MPL", "left high motor pod", "PETG", "HARD", 1, "A1-HARD-04", "PS-RV227-MPL.stl", (54, 132, 58), True, "left high mounted motor pod; v2.27 fused cable boss; recessed external label"),
    PartSpec("PS-RV227-MPR", "right high motor pod", "PETG", "HARD", 1, "A1-HARD-04", "PS-RV227-MPR.stl", (54, 132, 58), True, "right high mounted motor pod; v2.27 fused cable boss; recessed external label"),

    # Drive case and internals
    PartSpec("PS-RV227-DRC-LF", "left front functional drive case half", "PETG", "HARD", 1, "A1-HARD-05", "PS-RV227-DRC-LF.stl", (32, 120, 38), True, "cavity, rod holes, service cover rail, drain"),
    PartSpec("PS-RV227-DRC-LR", "left rear functional drive case half", "PETG", "HARD", 1, "A1-HARD-05", "PS-RV227-DRC-LR.stl", (32, 120, 38), True, "cavity, rod holes, service cover rail, drain"),
    PartSpec("PS-RV227-DRC-RF", "right front functional drive case half", "PETG", "HARD", 1, "A1-HARD-05", "PS-RV227-DRC-RF.stl", (32, 120, 38), True, "cavity, rod holes, service cover rail, drain"),
    PartSpec("PS-RV227-DRC-RR", "right rear functional drive case half", "PETG", "HARD", 1, "A1-HARD-05", "PS-RV227-DRC-RR.stl", (32, 120, 38), True, "cavity, rod holes, service cover rail, drain"),
    PartSpec("PS-RV227-DRC-CVR-S", "slide service cover set for drive cases", "PETG", "HARD", 1, "A1-HARD-05", "PS-RV227-DRC-CVR-S.stl", (118, 82, 8), True, "four slide service covers"),
    PartSpec("PS-RV227-GEA-18T-S", "printed 18 tooth gear set", "PETG", "HARD", 1, "A1-HARD-05", "PS-RV227-GEA-18T-S.stl", (120, 60, 12), True, "assembly/test gears; metal rods still recommended for load"),
    PartSpec("PS-RV227-IDR-S", "printed idler roller set", "PETG", "HARD", 1, "A1-HARD-05", "PS-RV227-IDR-S.stl", (88, 42, 12), True, "idler rollers for belt/chain route mockup"),
    PartSpec("PS-RV227-PIN-S", "printed service pin and retainer set", "PETG", "HARD", 1, "A1-HARD-05", "PS-RV227-PIN-S.stl", (110, 42, 10), True, "printed service pins and retainers"),

    # v2.27 moving-model wheelbase, drivetrain path, float and hull parts
    PartSpec("PS-RV227-WBASE-L", "left printable wheelbase side rail with axle carriers", "PETG", "HARD", 1, "A1-HARD-06", "PS-RV227-WBASE-L.stl", (224, 32, 20), True, "moving model wheelbase; axle carrier rail; low-load printed model"),
    PartSpec("PS-RV227-WBASE-R", "right printable wheelbase side rail with axle carriers", "PETG", "HARD", 1, "A1-HARD-06", "PS-RV227-WBASE-R.stl", (224, 32, 20), True, "moving model wheelbase; axle carrier rail; low-load printed model"),
    PartSpec("PS-RV227-DRIVE-L", "left visible gearbox-to-wheel drive path module", "PETG", "HARD", 1, "A1-HARD-06", "PS-RV227-DRIVE-L.stl", (218, 46, 18), True, "visible belt/chain drive path from drive case output to front/rear wheel axles"),
    PartSpec("PS-RV227-DRIVE-R", "right visible gearbox-to-wheel drive path module", "PETG", "HARD", 1, "A1-HARD-06", "PS-RV227-DRIVE-R.stl", (218, 46, 18), True, "visible belt/chain drive path from drive case output to front/rear wheel axles"),
    PartSpec("PS-RV227-AXLE-HUB-S", "printable axle hub and wheel retainer set", "PETG", "HARD", 1, "A1-HARD-06", "PS-RV227-AXLE-HUB-S.stl", (126, 38, 14), True, "low-load model hubs/retainers for printed axles and TPU wheels"),
    PartSpec("PS-RV227-FLT-L", "left side float pontoon", "PETG", "HARD", 1, "A1-HARD-07", "PS-RV227-FLT-L.stl", (226, 34, 22), True, "support-clean side float / mud skid pontoon; model only until sealed"),
    PartSpec("PS-RV227-FLT-R", "right side float pontoon", "PETG", "HARD", 1, "A1-HARD-07", "PS-RV227-FLT-R.stl", (226, 34, 22), True, "support-clean side float / mud skid pontoon; model only until sealed"),
    PartSpec("PS-RV227-HULL-SKID", "central shallow boat skid hull", "PETG", "HARD", 1, "A1-HARD-07", "PS-RV227-HULL-SKID.stl", (178, 214, 18), True, "shallow underbody boat/skid tray for low-load moving model and float layout check"),
    PartSpec("PS-RV227-PAX-6X172-S", "printed 6mm class axle surrogate set", "PETG", "HARD", 1, "A1-HARD-08", "PS-RV227-PAX-6X172-S.stl", (190, 44, 8), True, "plastic surrogate for 6mm x 172mm wheel axles; low-load model only"),
    PartSpec("PS-RV227-PAX-4X54-S", "printed 4mm class gearbox rod surrogate set", "PETG", "HARD", 1, "A1-HARD-08", "PS-RV227-PAX-4X54-S.stl", (112, 46, 6), True, "plastic surrogate for 4mm x 54mm gearbox rods; low-load model only"),
    PartSpec("PS-RV227-PAX-6X52-S", "printed 6mm class PTO alignment surrogate set", "PETG", "HARD", 1, "A1-HARD-08", "PS-RV227-PAX-6X52-S.stl", (90, 28, 8), True, "plastic surrogate for 6mm x 52mm PTO/alignment rods; low-load model only"),

    # v2.27 clearer lower undercarriage and drivetrain completion parts
    PartSpec("PS-RV227-LOWER-FRAME", "one-piece visible lower undercarriage wheelbase frame", "PETG", "HARD", 1, "A1-HARD-09", "PS-RV227-LOWER-FRAME.stl", (232, 188, 22), True, "clear wheelbase frame with front/rear axle carriers and center gearbox mounts"),
    PartSpec("PS-RV227-GBOX-INTERNAL-L", "left gearbox internal gear mockup cartridge", "PETG", "HARD", 1, "A1-HARD-09", "PS-RV227-GBOX-INTERNAL-L.stl", (118, 46, 16), True, "printed gear train mockup replacing metal gears for low-load model"),
    PartSpec("PS-RV227-GBOX-INTERNAL-R", "right gearbox internal gear mockup cartridge", "PETG", "HARD", 1, "A1-HARD-09", "PS-RV227-GBOX-INTERNAL-R.stl", (118, 46, 16), True, "printed gear train mockup replacing metal gears for low-load model"),
    PartSpec("PS-RV227-AXLE-SPROCKET-S", "axle sprocket and spacer set for four wheels", "PETG", "HARD", 1, "A1-HARD-09", "PS-RV227-AXLE-SPROCKET-S.stl", (132, 52, 12), True, "four axle sprockets/pulleys plus spacers for printed wheel axles"),
    PartSpec("PS-RV227-FLT-BRACKET-S", "float and hull bracket set", "PETG", "HARD", 1, "A1-HARD-09", "PS-RV227-FLT-BRACKET-S.stl", (142, 46, 12), True, "brackets connecting side floats and central hull/skid to lower frame"),
    PartSpec("PS-RV227-FLT-RCV-L", "left inboard side float receiver rail", "PETG", "HARD", 1, "A1-HARD-10", "PS-RV227-FLT-RCV-L.stl", (226, 28, 18), True, "removable inboard side receiver for FLT-L or foam float; keeps float mount inside wheel envelope where possible"),
    PartSpec("PS-RV227-FLT-RCV-R", "right inboard side float receiver rail", "PETG", "HARD", 1, "A1-HARD-10", "PS-RV227-FLT-RCV-R.stl", (226, 28, 18), True, "removable inboard side receiver for FLT-R or foam float; keeps float mount inside wheel envelope where possible"),
    PartSpec("PS-RV227-FLT-RCV-FR-S", "front/rear cross float receiver saddle set", "PETG", "HARD", 1, "A1-HARD-10", "PS-RV227-FLT-RCV-FR-S.stl", (188, 58, 16), True, "front and rear cross saddles for float blocks; avoids side-width growth"),
    PartSpec("PS-RV227-FLT-STRAP-S", "float strap and locator key set", "TPU", "TPU", 1, "A1-TPU-03", "PS-RV227-FLT-STRAP-S.stl", (148, 48, 5), True, "TPU strap/locator mockup for detachable float modules; not a final load-rated strap"),
    PartSpec("PS-RV227-BELT-L", "left TPU loop belt mockup", "TPU", "TPU", 1, "A1-TPU-03", "PS-RV227-BELT-L.stl", (198, 42, 4), True, "TPU belt/chain loop mockup from gearbox output to front/rear axle sprockets"),
    PartSpec("PS-RV227-BELT-R", "right TPU loop belt mockup", "TPU", "TPU", 1, "A1-TPU-03", "PS-RV227-BELT-R.stl", (198, 42, 4), True, "TPU belt/chain loop mockup from gearbox output to front/rear axle sprockets"),

    # Wheel placeholders
    PartSpec("PS-RV227-WHL-FL", "front-left support-clean vertical TPU tire placeholder", "TPU", "TPU", 1, "A1-TPU-02", "PS-RV227-WHL-FL.stl", (112, 42, 112), True, "support-clean vertical TPU tire/contact placeholder"),
    PartSpec("PS-RV227-WHL-FR", "front-right support-clean vertical TPU tire placeholder", "TPU", "TPU", 1, "A1-TPU-02", "PS-RV227-WHL-FR.stl", (112, 42, 112), True, "support-clean vertical TPU tire/contact placeholder"),
    PartSpec("PS-RV227-WHL-RL", "rear-left support-clean vertical TPU tire placeholder", "TPU", "TPU", 1, "A1-TPU-02", "PS-RV227-WHL-RL.stl", (112, 42, 112), True, "support-clean vertical TPU tire/contact placeholder"),
    PartSpec("PS-RV227-WHL-RR", "rear-right support-clean vertical TPU tire placeholder", "TPU", "TPU", 1, "A1-TPU-02", "PS-RV227-WHL-RR.stl", (112, 42, 112), True, "support-clean vertical TPU tire/contact placeholder"),
]

# Reference-only commercial box and metal rods are exported to separate folders but not print manifest.
REFERENCE_PARTS = [
    PartSpec("PS-RV227-COMBOX-REF", "commercial IP67 box reference 300x200x120", "REFERENCE", "REFERENCE", 1, "REFERENCE", "PS-RV227-COMBOX-REF.stl", (200, 300, 120), False, "purchased 300x200x120mm class IP65-IP67 box reference"),
]

METAL_BOM = [
    {"item": "wheel axle rod", "diameter_mm": 6, "length_mm": 172, "qty": 4, "notes": "real load path; stainless or plated steel candidate"},
    {"item": "gearbox internal rod", "diameter_mm": 4, "length_mm": 54, "qty": 8, "notes": "gear/idler support rods"},
    {"item": "PTO alignment rod", "diameter_mm": 6, "length_mm": 52, "qty": 2, "notes": "alignment/reference only"},
]

FONT_5X7: Dict[str, Tuple[str, ...]] = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10011", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def require_cadquery():
    if cq is None:
        raise RuntimeError(
            "CadQuery is not available. Run in the paddy-cad conda environment. "
            f"Import error: {CADQUERY_IMPORT_ERROR!r}"
        )


def box(x: float, y: float, z: float, fillet: float = 0.0):
    """Support-friendly rectangular solid.

    Historical generators used the parameter name `fillet`.
    In v2.27, positive values are interpreted as a small 45-degree-ish chamfer
    instead of a rounded fillet.  This reduces Bambu Studio support generation
    on box rims, lids, rails, and roof-like parts.
    """
    obj = cq.Workplane("XY").box(x, y, z)
    if fillet > 0:
        chamfer = min(float(fillet), x / 4.0, y / 4.0, z / 4.0)
        try:
            obj = obj.edges().chamfer(chamfer)
        except Exception:
            # Fallback to plain box.  Avoid rounded fillets here because they
            # triggered support-heavy slices on box/cap parts.
            pass
    return obj


def support_safe_top_rim(x: float, y: float, z_top: float, wall: float):
    """Four vertical rim bars with chamfered edges.

    This replaces a single overhanging rounded ring.  Each bar sits on the wall
    footprint and avoids horizontal underside overhangs.
    """
    rim_h = 7.0
    rim_t = max(4.2, wall)
    zc = z_top + rim_h / 2.0

    front = box(x - 2 * wall, rim_t, rim_h, fillet=0.8).translate((0, -y / 2 + wall / 2, zc))
    rear = box(x - 2 * wall, rim_t, rim_h, fillet=0.8).translate((0, y / 2 - wall / 2, zc))
    left = box(rim_t, y, rim_h, fillet=0.8).translate((-x / 2 + wall / 2, 0, zc))
    right = box(rim_t, y, rim_h, fillet=0.8).translate((x / 2 - wall / 2, 0, zc))
    return front.union(rear).union(left).union(right)



def sprue_base(x: float, y: float, z: float = 0.6):
    """Thin sacrificial base to keep multi-piece STL sets from floating.

    It can be cut away after printing.  The purpose is not strength; it prevents
    disconnected small shells from being raised by slicer orientation/placement.
    """
    return box(x, y, z, fillet=0.0).translate((0, 0, z / 2.0))


def cyl_x(radius: float, length: float):
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(-length / 2.0, 0, 0), cq.Vector(1, 0, 0))
    return cq.Workplane("XY").newObject([solid])


def cyl_y(radius: float, length: float):
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(0, -length / 2.0, 0), cq.Vector(0, 1, 0))
    return cq.Workplane("XY").newObject([solid])


def cyl_z(radius: float, length: float):
    return cq.Workplane("XY").circle(radius).extrude(length).translate((0, 0, -length / 2.0))


def block_label(text: str, cell: float = 1.05, gap: float = 0.16, height: float = 0.65):
    require_cadquery()
    text = text.upper()
    solids = []
    x_cursor = 0.0
    for ch in text:
        pattern = FONT_5X7.get(ch, FONT_5X7[" "])
        for row, line in enumerate(pattern):
            for col, bit in enumerate(line):
                if bit == "1":
                    x = x_cursor + col * (cell + gap)
                    y = (6 - row) * (cell + gap)
                    solids.append(box(cell, cell, height).translate((x, y, height / 2.0)))
        x_cursor += 6 * (cell + gap)
    if not solids:
        return cq.Workplane("XY")
    obj = solids[0]
    for s in solids[1:]:
        obj = obj.union(s)
    return obj.translate((-(x_cursor - (cell + gap)) / 2.0, -(7 * (cell + gap)) / 2.0, 0))


def add_top_label(obj, text: str, x: float, y: float, z: float, cell: float = 1.0, embed: float = 0.18):
    """Production-safe label policy.

    v2.27 disables geometry labels by default because raised block text can become
    floating fragments after automatic orientation/slicing.  Part identity is
    managed by print_manifest/plate_manifest instead.
    """
    return obj


def engrave_top_label(obj, text: str, x: float, y: float, z_top: float, cell: float = 1.35, depth: float = 0.55):
    """Conditional recessed ASCII block label for large flat hard parts.

    This cuts a short 5x7 block-label into a solid top face.  Do not use on
    TPU, gaskets, thin covers, gears, pins, wheels, or functional sealing/sliding
    surfaces.  Width/depth still need real Bambu Studio slice tests.
    """
    require_cadquery()
    if not text:
        return obj
    try:
        cutter = block_label(text, cell=cell, gap=0.18, height=depth + 0.08).translate((x, y, z_top - depth))
        return obj.cut(cutter)
    except Exception:
        return obj







def top_open_cable_notch_cut_y(face_y: float, side: str, width_x: float = 14.0):
    """Top-open wire-drop notch for CBOX/BBOX side walls.

    v2.27 policy:
      - The connector body does NOT pass through this notch.
      - With the lid open, the connector crosses over the open box edge.
      - Only the bundled wires drop into the notch before the lid is closed.
      - The notch must therefore stay open at the top; no upper bridge/cap is allowed.
      - The visible opening has a rounded bottom so the cable bundle is not pressed
        against a sharp rectangular corner.
      - Side openings are kept as small as practical; only the wire passage remains.
      - No exterior collar, spacer, tall side post, or floating U-shaped rib is created.
    """
    require_cadquery()
    depth_y = 13.0
    radius = width_x / 2.0
    z_top = 132.0
    z_bottom = 106.0

    if side == "front":
        y_ext = face_y - 2.4
        y_int = face_y + depth_y
    else:
        y_ext = face_y + 2.4
        y_int = face_y - depth_y

    y_ctr = (y_ext + y_int) / 2.0
    y_len = abs(y_int - y_ext) + 1.2

    # U-shaped, top-open cut when viewed from the box side:
    #   - rectangle cuts from the rounded bottom tangent up through the rim,
    #   - horizontal cylinder cuts the rounded bottom.
    # This avoids a support-demanding bridge and keeps only a wire-bundle-sized gap.
    rect_h = max(1.0, z_top - (z_bottom + radius))
    rect = box(width_x, y_len, rect_h, fillet=0).translate((0, y_ctr, (z_top + z_bottom + radius) / 2.0))
    rounded_bottom = cyl_y(radius, y_len).translate((0, y_ctr, z_bottom + radius))
    return rect.union(rounded_bottom)


def bottom_round_cable_guide_y(face_y: float, side: str, width_x: float = 14.0):
    """Deprecated in v2.27.

    The bottom cable guide bead was removed because it could appear as a small
    floating/unsupported fragment in Bambu Studio.  The cable passage is now only
    the top-open U notch; protection is handled by the lid/gasket, TPU plug, and
    raincoat cover.
    """
    require_cadquery()
    return cq.Workplane("XY").box(0.01, 0.01, 0.01).translate((9999, 9999, 9999))


def make_printed_box_body(kind: str):
    """Open-top support-safe box body with two top-open cable-only notches.

    v2.27 removes support-heavy rounded rims and any cable guide fragments.
    The body is intended to print upright: bottom on bed, open side upward.
    """
    require_cadquery()
    assert kind in ("CBOX", "BBOX")
    x, y, z = 150.0, 200.0, 120.0
    wall = DESIGN["box_wall"]
    bottom = DESIGN["box_bottom"]
    notch_w, notch_depth = DESIGN["top_open_notch_w_depth"]

    # Chamfered box body: avoids round fillet overhangs that generated support.
    outer = box(x, y, z, fillet=2.0).translate((0, 0, z / 2))
    inner = box(x - 2 * wall, y - 2 * wall, z + 4, fillet=0.0).translate((0, 0, bottom + (z + 4) / 2))
    obj = outer.cut(inner)

    # Support-safe vertical rim bars.  No overhanging rounded ring.
    obj = obj.union(support_safe_top_rim(x, y, z, wall))

    # Exactly two top-open cable-only notches per box: one on each short/opposite side.
    # Connector handling rule:
    #   lid open  -> connector crosses over the open top edge
    #   wire only -> wire bundle drops into this notch
    #   lid shut  -> only a cable-bundle-sized opening remains under the raincoat/seam cover
    # Water rule: top remains open for wire drop; the lower passage is minimal.
    for side, face_y in (("front", -y / 2), ("rear", y / 2)):
        obj = obj.cut(top_open_cable_notch_cut_y(face_y, side, width_x=notch_w))
        # v2.27: no cable guide bead/rib.  Notch only.

    # Internal equipment layout ribs on the bottom; no body-top labels.
    if kind == "CBOX":
        obj = obj.union(box(4, 150, 4, 0.8).translate((-44, -8, bottom + 2)))
        obj = obj.union(box(4, 150, 4, 0.8).translate((-22, -8, bottom + 2)))
        obj = obj.union(box(58, 4, 4, 0.8).translate((32, 48, bottom + 2)))
        obj = obj.union(box(58, 4, 4, 0.8).translate((32, -48, bottom + 2)))
        obj = add_top_label(obj, "C225", 42, 0, bottom + 4.2, cell=0.8)
    else:
        obj = obj.union(box(4, 162, 4, 0.8).translate((-28, 0, bottom + 2)))
        obj = obj.union(box(4, 162, 4, 0.8).translate((28, 0, bottom + 2)))
        obj = obj.union(box(42, 4, 4, 0.8).translate((48, 58, bottom + 2)))
        obj = obj.union(box(42, 4, 4, 0.8).translate((48, -58, bottom + 2)))
        obj = add_top_label(obj, "B225", 42, 0, bottom + 4.2, cell=0.8)

    return obj


def make_box_lid(kind: str):
    """Support-safe flat lid with optional recessed label.

    v2.27 uses recessed engraving only on this large flat hard part.  The
    engraving is intentionally short/deep enough for slice testing.
    """
    require_cadquery()
    assert kind in ("CBOX", "BBOX")
    x, y = 166.0, 216.0
    lid = box(x, y, 8, fillet=1.2).translate((0, 0, 4))

    # Top-side low gasket/locator rails only.  No underside cavity.
    rail_h = 1.8
    rail_t = 3.0
    zc = 8 + rail_h / 2.0
    front = box(142, rail_t, rail_h, fillet=0.4).translate((0, -94, zc))
    rear = box(142, rail_t, rail_h, fillet=0.4).translate((0, 94, zc))
    left = box(rail_t, 190, rail_h, fillet=0.4).translate((-70, 0, zc))
    right = box(rail_t, 190, rail_h, fillet=0.4).translate((70, 0, zc))
    obj = lid.union(front).union(rear).union(left).union(right)

    # Recessed label on clear solid top region only.
    txt = "CBOX" if kind == "CBOX" else "BBOX"
    obj = engrave_top_label(obj, txt, -28, 14, 8.05, cell=1.45, depth=0.60)
    return obj


def make_box_gasket():
    require_cadquery()
    outer = box(154, 204, 3, fillet=3)
    inner = box(136, 186, 4, fillet=2)
    return outer.cut(inner).translate((0, 0, 1.5))



def make_slot_plug_set():
    """Support-clean TPU plug set with sacrificial sprue base."""
    require_cadquery()
    base = sprue_base(122, 28, 0.6)
    obj = base
    # Four low cable-bundle notch plugs.  All touch the base.
    for x in [-42, -14, 14, 42]:
        body = box(18, 8, 8, 0.8).translate((x, 0, 4.6))
        cap = box(22, 12, 3, 0.5).translate((x, 0, 10.1))
        pull_tab = box(8, 4, 5, 0.4).translate((x, -7, 3.1))
        obj = obj.union(body).union(cap).union(pull_tab)
    return obj



def make_raincoat_cover():
    """Support-clean flat shingle raincoat cover for the dual-box seam.

    v2.27 explicitly restores this function.  The part prints as one connected
    flat body to avoid floating roof fragments and support-filled cavities.  It
    is mounted over the CBOX/BBOX seam during assembly to reduce direct rain or
    wash-water impact on the top-open cable notches.
    """
    require_cadquery()
    base = box(160, 54, 3.0, fillet=0.8).translate((0, 0, 1.5))
    center_ridge = box(142, 4, 3.0, fillet=0.4).translate((0, 0, 4.5))
    left_drip = box(150, 3, 2.2, fillet=0.3).translate((0, -22, 4.1))
    right_drip = box(150, 3, 2.2, fillet=0.3).translate((0, 22, 4.1))
    end_lip_l = box(5, 48, 2.2, fillet=0.3).translate((-72, 0, 4.1))
    end_lip_r = box(5, 48, 2.2, fillet=0.3).translate((72, 0, 4.1))

    # Low locator pads are fused to the main plate.  No floating islands.
    loc1 = box(18, 6, 2.0, fillet=0.3).translate((-42, -18, 0.8))
    loc2 = box(18, 6, 2.0, fillet=0.3).translate((42, 18, 0.8))

    return base.union(center_ridge).union(left_drip).union(right_drip).union(end_lip_l).union(end_lip_r).union(loc1).union(loc2)


def make_chassis_quadrant(name: str):
    """Support-clean chassis quadrant.

    v2.27 fix:
      - rail and pocket/tab features overlap the base by 0.2 mm.
      - no feature starts above the parent top face.
      - this removes Bambu Studio preview-floating rectangular tabs.
    """
    require_cadquery()
    base = box(118, 178, 12, fillet=1.2).translate((0, 0, 6))

    # Base top is z=12.  All raised features intentionally start at z=11.8.
    rail = box(18, 160, 8, 0.8).translate((-42, 0, 15.8))
    slot_marker = box(22, 132, 5, 0.5).translate((34, 0, 17.0))

    # Former floating pockets.  They now overlap the base top by 0.2 mm.
    pocket1 = box(22, 10, 8, 0.5).translate((0, -64, 15.8))
    pocket2 = box(22, 10, 8, 0.5).translate((0, 64, 15.8))

    obj = base.union(rail).cut(slot_marker).union(pocket1).union(pocket2)

    # Recessed ID only on the large flat base, away from slide/lock faces.
    return engrave_top_label(obj, name[-2:], 24, 0, 12.05, cell=1.15, depth=0.45)


def make_cradle_rail(side: str):
    """Support-clean cradle rail.

    v2.27 fix:
      - lip and hold-down blocks overlap the rail by 0.2 mm.
      - avoids preview-floating latch/hold blocks.
    """
    require_cadquery()
    sign = -1 if side == "L" else 1
    rail = box(18, 210, 12, fillet=1.0).translate((0, 0, 6))

    # Rail top is z=12.  Raised features start at z=11.8.
    top_lip = box(24, 190, 5, 0.6).translate((sign * 3, 0, 14.3))
    low_hold_a = box(10, 28, 8, 0.6).translate((sign * 12, -70, 15.8))
    low_hold_b = box(10, 28, 8, 0.6).translate((sign * 12, 70, 15.8))
    low_hold = low_hold_a.union(low_hold_b)

    # Notches for wedge keys.
    notch = box(8, 14, 8, 0.4).translate((sign * 8, 0, 15.8))
    obj = rail.union(top_lip).union(low_hold).cut(notch)

    return engrave_top_label(obj, f"MCR{side}", 0, 0, 12.05, cell=0.95, depth=0.40)


def make_locator_set():
    """Support-clean locator set with all features connected to a base."""
    require_cadquery()
    obj = sprue_base(132, 62, 0.6)
    a = box(120, 18, 16, 0.8).translate((0, -18, 8.6))
    b = box(120, 18, 16, 0.8).translate((0, 18, 8.6))
    # Low locator ridges, fully connected to the main blocks.
    a = a.union(box(32, 4, 4, 0.3).translate((0, -28, 16.6)))
    b = b.union(box(32, 4, 4, 0.3).translate((0, 28, 16.6)))
    return obj.union(a).union(b)


def make_wedge_set():
    """Support-clean wedge set with sacrificial sprue base.

    Slopes are shallow and every wedge touches the base.
    """
    require_cadquery()
    obj = sprue_base(110, 46, 0.6)
    for x in [-36, -12, 12, 36]:
        body = box(18, 38, 7, 0.5).translate((x, 0, 4.1))
        # Small stepped cap instead of rotated floating cap.
        cap1 = box(18, 26, 2.2, 0.3).translate((x, -1, 8.7))
        cap2 = box(18, 18, 2.0, 0.3).translate((x, 2, 10.6))
        obj = obj.union(body).union(cap1).union(cap2)
    return obj


def make_latch_set():
    """Support-clean latch set with sacrificial sprue base."""
    require_cadquery()
    obj = sprue_base(98, 42, 0.6)
    for x in [-30, -10, 10, 30]:
        body = box(15, 26, 8, 0.5).translate((x, 0, 4.6))
        # Hook as low stepped block that overlaps the body; no isolated upper tab.
        hook = box(15, 8, 5, 0.4).translate((x, 12, 8.1))
        toe = box(15, 5, 3, 0.3).translate((x, 17, 5.1))
        obj = obj.union(body).union(hook).union(toe)
    return obj


def make_height_gauge():
    """Support-clean height/interference gauge."""
    require_cadquery()
    obj = sprue_base(180, 28, 0.6)
    bar = box(170, 12, 10, 0.6).translate((0, 0, 5.6))
    feet = box(8, 18, 10, 0.5).translate((-78, 0, 5.6)).union(box(8, 18, 10, 0.5).translate((78, 0, 5.6)))
    return obj.union(bar).union(feet)


def make_control_panel():
    """RCP-G1 real switch mounting panel.

    v2.27 separates the emergency-stop/operation panel from the PTO attachment area.
    The panel itself stays as the switch face; a dedicated RCP bracket places it
    higher on the rover so the E-stop can be pressed even with a PTO-driven unit installed.

    v2.27 assumes commercial panel-mount waterproof switches:
      - E-stop: nominal 22 mm class, CAD hole 23.0 mm
      - Pause / Carry / Start: nominal 16 mm class, CAD hole 17.0 mm
      - Status LED: 8 mm class, CAD hole 8.6 mm
      - Buzzer/optional indicator: 12 mm class, CAD hole 12.8 mm

    The panel includes front-side shallow counterbores/flange seats and
    rear-side shallow waterproofing cups/potting trays.  Actual purchased parts
    can later override these diameters.
    """
    require_cadquery()

    panel = box(184, 72, 8, 1.0).translate((0, 0, 4))
    # Raised perimeter/frame to stiffen the button panel.
    frame_front = box(176, 4, 4, 0.4).translate((0, -32, 10))
    frame_rear = box(176, 4, 4, 0.4).translate((0, 32, 10))
    frame_l = box(4, 64, 4, 0.4).translate((-88, 0, 10))
    frame_r = box(4, 64, 4, 0.4).translate((88, 0, 10))
    obj = panel.union(frame_front).union(frame_rear).union(frame_l).union(frame_r)

    # Hole layout, face-up print orientation.
    # x, y, through-hole diameter, shallow front seat diameter, rear cup diameter
    holes = [
        (-62, 10, 23.0, 34.0, 38.0),  # E-stop
        (-18, 10, 17.0, 24.0, 28.0),  # pause/carry
        ( 24, 10, 17.0, 24.0, 28.0),  # position/start
        ( 64, 10, 17.0, 24.0, 28.0),  # spare/manual
        (-52,-20,  8.6, 13.0, 16.0),  # status LED
        (-28,-20,  8.6, 13.0, 16.0),  # status LED
        ( -4,-20,  8.6, 13.0, 16.0),  # status LED
        ( 40,-20, 12.8, 18.0, 22.0),  # buzzer/indicator
    ]

    for x, y, d, seat_d, cup_d in holes:
        # Through hole.
        obj = obj.cut(cyl_z(d / 2.0, 14).translate((x, y, 4)))
        # Front shallow seat/counterbore for flange.  Wide and shallow to avoid
        # the switch being pushed through the panel.
        obj = obj.cut(cyl_z(seat_d / 2.0, 1.8).translate((x, y, 8.9)))
        # Rear waterproofing/potting cup wall: low ring around terminals.
        cup_outer = cyl_z(cup_d / 2.0, 4.0).translate((x, y, -1.5))
        cup_inner = cyl_z((d + 3.0) / 2.0, 5.0).translate((x, y, -1.5))
        obj = obj.union(cup_outer.cut(cup_inner))

    # Rear-side drip-loop / cable tie rails, connected and low.
    obj = obj.union(box(150, 4, 4, 0.4).translate((0, -34, -1.5)))
    obj = obj.union(box(150, 4, 4, 0.4).translate((0, 34, -1.5)))
    for x in (-70, -35, 0, 35, 70):
        obj = obj.union(box(10, 4, 4, 0.3).translate((x, -28, -1.5)))
        obj = obj.union(box(10, 4, 4, 0.3).translate((x, 28, -1.5)))

    # Recessed short label on unused clear top area.
    obj = engrave_top_label(obj, "RCP", 58, -32, 8.05, cell=1.1, depth=0.45)
    return obj


def make_cable_hood():
    """Support-clean cable rain hood, generated in print-flat orientation.

    v2.27 replaces separated sloped roof leaves with one connected shingle plate.
    The printed part is mounted at a rain-shedding angle on the rover; the STL
    itself contains no floating angled panels.
    """
    require_cadquery()
    base = box(92, 70, 3.0, fillet=0.8).translate((0, 0, 1.5))
    center_ridge = box(78, 4, 3.0, fillet=0.4).translate((0, 0, 4.5))
    side_lip_l = box(4, 62, 2.4, fillet=0.3).translate((-40, 0, 4.2))
    side_lip_r = box(4, 62, 2.4, fillet=0.3).translate((40, 0, 4.2))
    rear_drip = box(84, 4, 2.4, fillet=0.3).translate((0, 31, 4.2))
    # Two low cable shadows/keepers on top; all connected to base.
    k1 = box(18, 6, 2.0, fillet=0.3).translate((-18, -22, 4.0))
    k2 = box(18, 6, 2.0, fillet=0.3).translate((18, -22, 4.0))
    return base.union(center_ridge).union(side_lip_l).union(side_lip_r).union(rear_drip).union(k1).union(k2)


def make_rcp_bracket():
    """Raised support-safe bracket for the RCP-G1 control panel.

    Purpose:
      - Moves the E-stop / operator buttons away from the PTO attachment face.
      - Keeps the emergency-stop reachable after a PTO tool is installed.
      - Prints as a single connected part with no floating islands.

    Intended mounting concept:
      - Base flange attaches to the rover/box structure.
      - Vertical plate holds the RCP-G1 panel above and behind the PTO area.
    """
    require_cadquery()

    base = box(98, 42, 6, 0.8).translate((0, 0, 3))
    # vertical panel plate, centered toward the rear edge of the base
    back_plate = box(98, 6, 52, 0.8).translate((0, -18, 26))
    # low front toe to resist peel and give a second mount line
    front_toe = box(82, 10, 6, 0.6).translate((0, 16, 3))

    # 45-degree style gussets as chunky wedges, intentionally overlapped
    gus_l = (
        cq.Workplane('XY')
        .polyline([(-43, -15), (-31, -15), (-31, 10), (-43, -2)])
        .close()
        .extrude(40)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((0, 0, 0))
    )
    gus_r = gus_l.mirror('YZ')

    obj = base.union(back_plate).union(front_toe).union(gus_l).union(gus_r)

    # Mounting slots in the base
    for x in (-30, 30):
        obj = obj.cut(box(8, 18, 8, 0.3).translate((x, 0, 3)))

    # Panel attachment slots in the back plate
    for x in (-60, -20, 20, 60):
        obj = obj.cut(box(6, 8, 16, 0.3).translate((x, -18, 30)))

    obj = engrave_top_label(obj, 'RCP-BRKT', 0, 12, 6.05, cell=0.95, depth=0.45)
    return obj


def make_pto_panel():
    """Support-clean front PTO panel.

    v2.27 intent: PTO remains on the front lower attachment face only.
    The emergency-stop function must not share this access plane.

    Face-up printing representation: PTO sockets are vertical Z rings, not
    horizontal Y cylinders.  Final assembly orientation is handled by the mount.
    """
    require_cadquery()
    panel = box(162, 70, 14, 1.0).translate((0, 0, 7))
    for x in (-55, 55):
        ring = cyl_z(18, 5).translate((x, 0, 16))
        hole = cyl_z(10, 7).translate((x, 0, 16))
        lug1 = box(12, 8, 4, 0.4).translate((x - 18, 15, 16))
        lug2 = box(12, 8, 4, 0.4).translate((x + 18, -15, 16))
        panel = panel.union(ring.cut(hole)).union(lug1).union(lug2)
    return panel


def make_motor_pod(side: str):
    """Support-clean high motor pod with fused cable boss.

    v2.27 fix:
      - The side cable boss is pulled inward and downward so it overlaps the cap.
      - The brace also overlaps the cap and boss.
      - All contacts are intentional volume overlaps, not coplanar face contact.
      - Recessed MP-L/MP-R label is cut only into the external top cap face.
    """
    require_cadquery()

    # Main pod body: z 0..56, y -66..66.
    body = box(54, 132, 56, 1.2).translate((0, 0, 28))

    # Top cap: z 55.8..72.2, overlapping the body top by 0.2 mm.
    cap = box(58, 72, 16.4, 0.9).translate((0, 0, 64.0))

    # Former floating rectangular boss.
    # It now overlaps the cap in Y by about 4 mm and in Z by about 2 mm.
    # cap y range is -36..36, boss y range is about -52..-32.
    boss = box(18, 20, 12, 0.5).translate((0, -42, 76.0))

    # Wide fused root/brace: overlaps cap, boss, and the upper body.
    root = box(24, 14, 10, 0.4).translate((0, -34, 70.5))
    lower_root = box(28, 10, 7, 0.3).translate((0, -36, 62.0))

    obj = body.union(cap).union(root).union(lower_root).union(boss)

    # External recessed label on the clear top cap area only.
    # Not placed inside the box/body or on hidden/functional mating faces.
    obj = engrave_top_label(obj, f"MP{side}", 0, 18, 72.25, cell=1.05, depth=0.45)
    return obj


def make_drive_case_half(label: str):
    """Functional drive case half, support-clean.

    v2.27 fix:
      - mud/wash slots are subtractive cuts only;
      - no small standalone rectangular cutter bodies are left behind;
      - slot cutters pass fully through the wall from the outside;
      - label is manifest-managed / no raised floating label.
    """
    require_cadquery()

    body = box(32, 120, 34, 1.2).translate((0, 0, 17))
    cavity = box(22, 96, 22, 0.6).translate((0, 0, 21))
    obj = body.cut(cavity)

    # Rod holes along X. These are real through-cuts.
    for y in (-36, 0, 36):
        obj = obj.cut(cyl_x(3.0, 42).translate((0, y, 18)))

    # Service cover rails.  Rails overlap case top wall volume.
    obj = obj.union(box(4, 104, 4, 0.4).translate((-15.6, 0, 32.2)))
    obj = obj.union(box(4, 104, 4, 0.4).translate((15.6, 0, 32.2)))

    # Low mud wash openings: cut-only, from outside, with full penetration.
    # Previous small box cutters could survive as independent STL components.
    # These larger cutters intentionally pass through the case wall and cannot
    # remain as printable islands.
    for y in (-42, 0, 42):
        cutter_front = box(40, 12, 4.8, 0.0).translate((0, y, 4.2))
        obj = obj.cut(cutter_front)

    # Shallow engraved ID on the solid upper rail area, not raised.
    return engrave_top_label(obj, label, 0, 0, 34.05, cell=0.65, depth=0.25)


def make_service_cover_set():
    """Support-clean service cover set with sacrificial sprue base."""
    require_cadquery()
    obj = sprue_base(52, 112, 0.6)
    for i, y in enumerate([-36, -12, 12, 36]):
        p = box(24, 22, 5, 0.5).translate((0, y, 3.1))
        p = p.union(box(4, 20, 3, 0.3).translate((-10, y, 6.9))).union(box(4, 20, 3, 0.3).translate((10, y, 6.9)))
        obj = obj.union(p)
    return obj


def make_gear_set():
    """Support-clean gear set with sacrificial sprue base."""
    require_cadquery()
    obj = sprue_base(132, 46, 0.6)
    for i, x in enumerate([-45, -15, 15, 45]):
        gear = cyl_z(15, 7).translate((x, 0, 4.1))
        hub = cyl_z(6, 9).translate((x, 0, 5.1))
        hole = cyl_z(2.2, 12).translate((x, 0, 5.1))
        g = gear.union(hub).cut(hole)
        # Low rectangular teeth, all overlap the gear disk.
        for t in range(18):
            tooth = box(3.5, 2.2, 6.0, 0.1).translate((x + 16.2, 0, 4.1)).rotate((x, 0, 0), (x, 0, 1), t * 20)
            g = g.union(tooth)
        obj = obj.union(g)
    return obj


def make_idler_set():
    """Support-clean idler set with sacrificial sprue base."""
    require_cadquery()
    obj = sprue_base(92, 28, 0.6)
    for x in [-30, -10, 10, 30]:
        p = cyl_z(8, 8).translate((x, 0, 4.6)).cut(cyl_z(2.2, 10).translate((x, 0, 4.6)))
        obj = obj.union(p)
    return obj


def make_pin_set():
    """Support-clean printable pin set.

    The old horizontal cylinders could float above the build plate.  v2.27 uses
    vertical print pins on a sacrificial base.  Metal rod references remain in
    metal_reference_bom_common_rover.
    """
    require_cadquery()
    obj = sprue_base(122, 30, 0.6)
    for i, x in enumerate([-45, -27, -9, 9, 27, 45]):
        pin = cyl_z(3.0, 20).translate((x, 0, 10.6))
        head = cyl_z(4.8, 2.4).translate((x, 0, 21.8))
        foot = cyl_z(4.0, 1.2).translate((x, 0, 1.2))
        obj = obj.union(foot).union(pin).union(head)
    return obj


def make_wheel():
    """Support-clean vertical wheel/tire print orientation.

    v2.27 adds spokes so the tire ring and hub are one mesh component.
    """
    require_cadquery()
    tire = cyl_z(56, 18).translate((0, 0, 9)).cut(cyl_z(32, 22).translate((0, 0, 9)))
    hub = cyl_z(22, 22).translate((0, 0, 11)).cut(cyl_z(6, 26).translate((0, 0, 11)))
    obj = tire.union(hub)

    # Six thick spokes connect hub to tire.  They overlap both hub and tire.
    for idx in range(6):
        spoke = box(42, 8, 12, 0.5).translate((31, 0, 11)).rotate((0, 0, 0), (0, 0, 1), idx * 60)
        obj = obj.union(spoke)

    # Support-safe tread blocks on top face, each overlaps tire.
    import math
    for idx in range(16):
        ang = math.radians(idx * 22.5)
        x = math.cos(ang) * 46
        y = math.sin(ang) * 46
        lug = box(12, 4, 4, 0.4).translate((x, y, 20)).rotate((0, 0, 0), (0, 0, 1), idx * 22.5)
        obj = obj.union(lug)
    return obj




def make_oct_rod_x(radius: float, length: float):
    """Support-friendlier printable rod surrogate.

    The shape is an 8-sided cylinder, intended for low-load model use.  Use real
    metal rods for field load tests.
    """
    require_cadquery()
    return cq.Workplane("XY").polygon(8, radius * 2.0).extrude(length).rotate((0, 0, 0), (0, 1, 0), 90).translate((-length / 2.0, 0, 0))


def make_wheelbase_side(side: str):
    """Printable wheelbase side rail with axle carriers.

    Purpose:
      - provide the missing wheelbase/footwork frame
      - show where front/rear 6 mm class axles pass
      - keep a simple low-load path for a moving model
    """
    require_cadquery()
    sign = -1 if side == "L" else 1
    base = box(224, 18, 10, 0.8).translate((0, 0, 5))

    # Front/rear axle carrier towers.  They overlap the base by 0.2 mm.
    carriers = []
    for x in (-84, 84):
        tower = box(28, 26, 18, 0.8).translate((x, 0, 18.8))
        # Axle hole along Y.  Hole is intentionally oversized for printed rods.
        tower = tower.cut(cyl_y(3.8, 34).translate((x, 0, 19)))
        saddle = box(38, 8, 6, 0.5).translate((x, sign * 13, 11.8))
        carriers.append(tower.union(saddle))

    obj = base
    for c in carriers:
        obj = obj.union(c)

    # Drive case locator pads, fully fused.
    for x in (-42, 42):
        obj = obj.union(box(32, 10, 5, 0.5).translate((x, sign * 10, 12.3)))

    # Float/hull connector slots as shallow rectangular marks.
    for x in (-96, 0, 96):
        obj = obj.cut(box(12, 6, 3, 0.2).translate((x, -sign * 7, 10.8)))

    return engrave_top_label(obj, f"WB{side}", 0, 0, 10.05, cell=0.95, depth=0.35)


def make_drive_path_module(side: str):
    """Visible gearbox-to-wheel drive path module for the printed model.

    This is a protective/visual belt-chain path from center drive output to the
    front and rear axle stations.  It is not yet a high-load sealed transmission.
    """
    require_cadquery()
    sign = -1 if side == "L" else 1
    base = box(218, 42, 4, 0.7).translate((0, 0, 2))

    # Three pulleys: front axle, gearbox/motor output, rear axle.
    obj = base
    pulley_specs = [(-84, 0, 14), (0, sign * 8, 12), (84, 0, 14)]
    for x, y, r in pulley_specs:
        pulley = cyl_z(r, 5).translate((x, y, 6.5)).cut(cyl_z(3.4, 7).translate((x, y, 6.5)))
        obj = obj.union(pulley)

    # Belt/chain visible path approximated by two narrow straight covers.
    belt1 = box(88, 6, 5, 0.4).rotate((0, 0, 0), (0, 0, 1), 8 * sign).translate((-42, sign * 4, 6.5))
    belt2 = box(88, 6, 5, 0.4).rotate((0, 0, 0), (0, 0, 1), -8 * sign).translate((42, sign * 4, 6.5))
    lower_run = box(172, 4, 4, 0.3).translate((0, -sign * 13, 5.8))
    obj = obj.union(belt1).union(belt2).union(lower_run)

    # Low clip tabs to attach to wheelbase rail.
    for x in (-84, 0, 84):
        obj = obj.union(box(14, 8, 4, 0.3).translate((x, sign * 17, 5.8)))

    return engrave_top_label(obj, f"DRV{side}", 0, -sign * 15, 4.05, cell=0.9, depth=0.30)


def make_axle_hub_set():
    """Hub and wheel retainer set for printed moving model."""
    require_cadquery()
    obj = sprue_base(126, 38, 0.6)
    for i, x in enumerate([-48, -16, 16, 48]):
        hub = cyl_z(12, 8).translate((x, 0, 4.6)).cut(cyl_z(3.6, 10).translate((x, 0, 4.6)))
        flange = cyl_z(16, 2.4).translate((x, 0, 9.8)).cut(cyl_z(3.6, 4).translate((x, 0, 9.8)))
        key = box(8, 3, 3, 0.2).translate((x, 10, 10.2))
        obj = obj.union(hub).union(flange).union(key)
    return obj


def make_float_pontoon(side: str):
    """Support-clean side pontoon / mud skid float.

    This prints as a solid model pontoon.  For real water tests, seal/coating or
    foam-fill strategy is still required.
    """
    require_cadquery()
    sign = -1 if side == "L" else 1
    body = box(206, 30, 18, 1.0).translate((0, 0, 9))
    nose_f = box(22, 26, 14, 0.8).rotate((0, 0, 0), (0, 0, 1), 12).translate((108, 0, 9))
    nose_r = box(22, 26, 14, 0.8).rotate((0, 0, 0), (0, 0, 1), -12).translate((-108, 0, 9))
    keel = box(190, 5, 4, 0.4).translate((0, -sign * 12, 3.2))
    obj = body.union(nose_f).union(nose_r).union(keel)

    # Top mounting pads overlap body.
    for x in (-80, 0, 80):
        obj = obj.union(box(24, 18, 4, 0.4).translate((x, sign * 3, 19.8)))

    return engrave_top_label(obj, f"FLT{side}", 0, 0, 18.05, cell=0.9, depth=0.35)


def make_hull_skid():
    """Central shallow boat/skid undertray.

    This is the 'boat' candidate: a low underbody tray that helps mock up float
    and mud-skid geometry.  It is not a sealed hull until post-processed.
    """
    require_cadquery()
    base = box(178, 214, 6, 1.0).translate((0, 0, 3))
    # Shallow central raised keel/rib layout, all above the plate.
    keel = box(22, 196, 10, 0.8).translate((0, 0, 8.8))
    side_l = box(12, 184, 8, 0.6).translate((-70, 0, 7.8))
    side_r = box(12, 184, 8, 0.6).translate((70, 0, 7.8))
    bow = box(156, 16, 8, 0.6).translate((0, 98, 7.8))
    stern = box(156, 16, 8, 0.6).translate((0, -98, 7.8))
    obj = base.union(keel).union(side_l).union(side_r).union(bow).union(stern)

    # Drain/inspection shallow grooves on upper side; not through-holes.
    for x in (-40, 40):
        obj = obj.cut(box(18, 120, 2.0, 0.2).translate((x, 0, 12.8)))

    return engrave_top_label(obj, "HULL", 0, 0, 6.05, cell=1.0, depth=0.35)


def make_printed_axle_6x172_set():
    """Four printed 6 mm class wheel-axle surrogate rods, low-load model only.

    v2.27 uses rectangular/square rods fused to the sprue base to avoid floating
    cylinder islands.  These are not load-bearing field-test rods.
    """
    require_cadquery()
    obj = sprue_base(190, 44, 0.8)
    for y in [-15, -5, 5, 15]:
        rod = box(172, 5.4, 5.4, 0.3).translate((0, y, 0.7 + 2.7))
        collar_l = box(6, 8, 5.8, 0.2).translate((-78, y, 0.7 + 2.9))
        collar_r = box(6, 8, 5.8, 0.2).translate((78, y, 0.7 + 2.9))
        obj = obj.union(rod).union(collar_l).union(collar_r)
    return obj


def make_printed_gear_rod_4x54_set():
    """Eight printed 4 mm class gearbox rod surrogates, low-load model only."""
    require_cadquery()
    obj = sprue_base(112, 46, 0.8)
    for y in [-10, 10]:
        for x in [-36, -12, 12, 36]:
            rod = box(54, 3.8, 3.8, 0.2).translate((x, y, 0.7 + 1.9))
            obj = obj.union(rod)
    return obj


def make_printed_pto_rod_6x52_set():
    """Two printed 6 mm class PTO/alignment rod surrogates."""
    require_cadquery()
    obj = sprue_base(90, 28, 0.8)
    for y in [-7, 7]:
        rod = box(52, 5.4, 5.4, 0.3).translate((0, y, 0.7 + 2.7))
        obj = obj.union(rod)
    return obj


def make_lower_frame():
    """One-piece lower undercarriage frame.

    v2.27 uses a continuous undertray instead of a mostly open frame so every
    boss/pad/tower is physically supported.  This is slightly heavier but much
    safer for the first moving-model print.
    """
    require_cadquery()
    overlap = FUSE_OVERLAP_MM

    # Continuous low undertray: all later features sit on it.
    tray = box(232, 188, 6, 0.8).translate((0, 0, 3))
    rail_l = box(222, 18, 8, 0.6).translate((0, -74, 6 - overlap + 4))
    rail_r = box(222, 18, 8, 0.6).translate((0, 74, 6 - overlap + 4))
    cross_f = box(18, 166, 8, 0.6).translate((96, 0, 6 - overlap + 4))
    cross_r = box(18, 166, 8, 0.6).translate((-96, 0, 6 - overlap + 4))
    center = box(58, 144, 8, 0.5).translate((0, 0, 6 - overlap + 4))
    obj = tray.union(rail_l).union(rail_r).union(cross_f).union(cross_r).union(center)

    # Four axle carrier towers, all overlapping tray/rails.
    for x in (-84, 84):
        for y in (-74, 74):
            tower_h = 22
            tower_bottom = 6.0 - overlap
            tower = box(30, 28, tower_h, 0.7).translate((x, y, tower_bottom + tower_h / 2.0))
            tower = tower.cut(cyl_y(3.9, 36).translate((x, y, tower_bottom + tower_h / 2.0)))
            foot = box(44, 34, 5, 0.5).translate((x, y, 6.0 - overlap + 2.5))
            obj = obj.union(foot).union(tower)

    # Gearbox mounting bosses converted to fused rectangular pads with center holes.
    for x in (-36, 0, 36):
        pad = box(20, 18, 5, 0.4).translate((x, 0, 6.0 - overlap + 2.5))
        pad = pad.cut(cyl_z(2.3, 7).translate((x, 0, 6.0 - overlap + 2.5)))
        obj = obj.union(pad)

    # Float/hull mount pads all inside the tray envelope.
    # v2.27: make these intentionally obvious as float receiver hardpoints.
    for x in (-72, 0, 72):
        for y in (-86, 86):
            pad = box(34, 20, 6, 0.4).translate((x, y, 6.0 - overlap + 3.0))
            obj = obj.union(pad)
            obj = obj.cut(box(20, 5, 2.2, 0.2).translate((x, y, 11.4)))

    # Long inboard float receiver guide rails.  These are still inside the tray
    # footprint and mark where PS-RV227-FLT-RCV-L/R can be attached.
    for y in (-58, 58):
        rail = box(188, 10, 5, 0.4).translate((0, y, 6.0 - overlap + 2.5))
        obj = obj.union(rail)
        for x in (-70, 0, 70):
            obj = obj.cut(box(18, 3, 1.5, 0.2).translate((x, y, 10.8)))

    # Front/rear cross-float receiver marks.
    for x in (-96, 96):
        rail = box(12, 150, 5, 0.4).translate((x, 0, 6.0 - overlap + 2.5))
        obj = obj.union(rail)

    # Shallow grooves show frame/float/hull alignment without cutting through.
    for y in (-58, 58):
        obj = obj.cut(box(190, 3, 1.4, 0.1).translate((0, y, 12.6)))
    for x in (-58, 58):
        obj = obj.cut(box(3, 150, 1.4, 0.1).translate((x, 0, 12.6)))

    return engrave_top_label(obj, "LOWER FRAME", 0, 0, 6.05, cell=0.85, depth=0.35)


def make_spur_gear_xy(x: float, y: float, z: float, r: float, teeth: int, hole_r: float = 2.4):
    """Simple fused gear-disc mockup.

    v2.27 removes separate tooth blocks.  Teeth are represented by shallow
    radial groove cuts on a single disc so the STL does not create tooth islands.
    """
    gear = cyl_z(r, 5).translate((x, y, z)).cut(cyl_z(hole_r, 7).translate((x, y, z)))
    hub = cyl_z(max(4.5, hole_r + 2.0), 7).translate((x, y, z + 0.8)).cut(cyl_z(hole_r, 9).translate((x, y, z + 0.8)))
    obj = gear.union(hub)
    # Shallow top grooves only.
    import math
    for t in range(max(8, min(teeth, 24))):
        groove = box(r * 0.35, 0.7, 1.0, 0.05).translate((x + r * 0.72, y, z + 2.5)).rotate((x, y, z), (x, y, z + 1), t * (360 / max(8, min(teeth, 24))))
        obj = obj.cut(groove)
    return obj


def make_gearbox_internal(side: str):
    """Gearbox internal gear mockup cartridge.

    v2.27 fix:
      - shaft location markers are recessed holes/circles cut into the base;
      - no small raised discs are added;
      - gears overlap the base and use groove-only tooth representation.
    """
    require_cadquery()
    sign = -1 if side == "L" else 1

    # Base top is z=5.  Gears at z=5.8 overlap the base by their lower layers.
    base = box(118, 46, 5, 0.5).translate((0, 0, 2.5))
    obj = base

    positions = [
        (-42, sign * 5, 12, 16),
        (-15, -sign * 5, 16, 22),
        (18, sign * 5, 14, 20),
        (45, -sign * 5, 12, 16),
    ]

    for x, y, r, teeth in positions:
        obj = obj.union(make_spur_gear_xy(x, y, 5.8, r, teeth, hole_r=2.3))

    # Recessed shaft markers: cuts only, not raised cylinders.
    # These are shallow pockets around each shaft position.
    for x, y, r, teeth in positions:
        obj = obj.cut(cyl_z(3.4, 1.2).translate((x, y, 5.35)))

    # Route line as a recessed groove, not a raised bar.
    obj = obj.cut(box(92, 2.2, 1.0, 0.1).translate((0, 0, 5.45)))

    return engrave_top_label(obj, f"GBOX{side}", 0, -18, 5.05, cell=0.75, depth=0.25)


def make_axle_sprocket_set():
    """Four sprockets/pulleys and spacers for the moving model wheel axles.

    v2.27: sprocket teeth are shallow grooves on fused discs.
    """
    require_cadquery()
    obj = sprue_base(132, 52, 0.8)
    for x in (-48, -16, 16, 48):
        sprocket = cyl_z(14, 5).translate((x, 8, 3.1)).cut(cyl_z(3.4, 7).translate((x, 8, 3.1)))
        for t in range(12):
            groove = box(5.5, 0.7, 1.0, 0.05).translate((x + 10, 8, 5.4)).rotate((x, 8, 3.1), (x, 8, 4.1), t * 30)
            sprocket = sprocket.cut(groove)
        spacer = cyl_z(7, 6).translate((x, -12, 3.6)).cut(cyl_z(3.4, 8).translate((x, -12, 3.6)))
        # Tiny bridge to the sprue base, so each disk is intentionally connected.
        bridge1 = box(6, 4, 1.0, 0.1).translate((x, 8, 0.9))
        bridge2 = box(6, 4, 1.0, 0.1).translate((x, -12, 0.9))
        obj = obj.union(bridge1).union(sprocket).union(bridge2).union(spacer)
    return obj


def make_float_bracket_set():
    """Brackets to attach floats and central hull/skid to lower frame."""
    require_cadquery()
    obj = sprue_base(142, 46, 0.6)
    for x in (-54, -18, 18, 54):
        bracket = box(24, 18, 8, 0.5).translate((x, 0, 4.6))
        slot = box(14, 5, 4, 0.2).translate((x, 0, 7.5))
        latch = box(18, 4, 4, 0.2).translate((x, 11, 6.0))
        obj = obj.union(bracket.cut(slot)).union(latch)
    return obj



def make_float_receiver_side(side: str):
    """Removable inboard side float receiver rail.

    v2.27 purpose:
      - Adds an obvious mounting location for mandatory flotation.
      - Keeps float mounting inside/near the existing wheel envelope where possible.
      - Provides shallow strap slots and keyed pads for FLT-L / FLT-R / foam blocks.
    """
    require_cadquery()
    sign = -1 if side == "L" else 1
    base = box(226, 24, 8, 0.8).translate((0, 0, 4))
    upper = box(214, 14, 8, 0.5).translate((0, sign * 2, 11.7))
    obj = base.union(upper)

    # Three fused locator pads.  They are intentionally raised but connected.
    for x in (-78, 0, 78):
        pad = box(28, 20, 6, 0.4).translate((x, 0, 15.0))
        obj = obj.union(pad)
        # strap grooves: shallow cuts only, not loose parts
        obj = obj.cut(box(18, 4, 2.0, 0.2).translate((x, sign * 7, 18.1)))

    # Keyed underside marks for lower-frame pads.
    for x in (-96, -32, 32, 96):
        obj = obj.cut(box(14, 5, 2.0, 0.2).translate((x, -sign * 7, 1.0)))

    return engrave_top_label(obj, f"FLT-RCV-{side}", 0, -sign * 8, 8.05, cell=0.65, depth=0.28)


def make_float_receiver_front_rear_set():
    """Front/rear float receiver saddle set.

    This gives an alternative to widening the rover with side floats.  The front
    and rear saddles can carry test foam/PET-bottle/printed float blocks across
    the rover while keeping the 30 cm row-spacing width target under control.
    """
    require_cadquery()
    obj = sprue_base(188, 58, 0.8)
    for y, label_y in [(-15, "F"), (15, "R")]:
        rail = box(174, 18, 8, 0.6).translate((0, y, 4.8))
        lip_a = box(174, 4, 5, 0.4).translate((0, y - 9, 10.5))
        lip_b = box(174, 4, 5, 0.4).translate((0, y + 9, 10.5))
        obj = obj.union(rail).union(lip_a).union(lip_b)
        for x in (-58, 0, 58):
            obj = obj.cut(box(20, 4, 2.0, 0.2).translate((x, y, 13.0)))
    return obj


def make_float_strap_set():
    """TPU float strap / locator mockup set.

    These are low-load assembly aids, not final field-retention straps.
    Real water testing should use mechanical retention plus inspection.
    """
    require_cadquery()
    obj = sprue_base(148, 48, 0.6)
    for y in (-12, 12):
        strap = box(132, 8, 3.2, 0.7).translate((0, y, 2.2))
        for x in (-48, 0, 48):
            strap = strap.cut(box(18, 3, 1.4, 0.2).translate((x, y, 3.4)))
        obj = obj.union(strap)
    # Four soft locator pads
    for x in (-54, -18, 18, 54):
        obj = obj.union(box(14, 10, 4, 0.4).translate((x, 0, 2.6)))
    return obj

def make_tpu_belt_loop(side: str):
    """TPU belt/chain loop mockup.

    It prints flat.  The loop is a simplified elongated belt that represents
    front axle sprocket -> gearbox output -> rear axle sprocket.
    """
    require_cadquery()
    sign = -1 if side == "L" else 1
    # outer rounded rectangle style loop
    outer = box(176, 24, 3.2, 0.8).translate((0, 0, 1.6))
    left_round = cyl_z(14, 3.2).translate((-88, 0, 1.6))
    right_round = cyl_z(14, 3.2).translate((88, 0, 1.6))
    outer = outer.union(left_round).union(right_round)

    inner = box(160, 12, 4.0, 0.4).translate((0, 0, 1.6))
    inner_l = cyl_z(6, 4.0).translate((-80, 0, 1.6))
    inner_r = cyl_z(6, 4.0).translate((80, 0, 1.6))
    belt = outer.cut(inner.union(inner_l).union(inner_r))

    # Center output sprocket witness bulge.
    bulge = cyl_z(10, 3.2).translate((0, sign * 10, 1.6)).cut(cyl_z(4, 4).translate((0, sign * 10, 1.6)))
    return belt.union(bulge)


def make_paddy_swarm_nameplate():
    """Recessed label visibility test plate.

    The lettering is intentionally engraved, not raised.  It is a separate test
    object so the main rover parts do not depend on untested label dimensions.
    """
    require_cadquery()
    plate = box(126, 34, 4, fillet=0.8).translate((0, 0, 2))

    # Low border is fused to the plate and does not create floating islands.
    border_front = box(118, 2.0, 1.0, fillet=0.2).translate((0, -14, 4.5))
    border_rear = box(118, 2.0, 1.0, fillet=0.2).translate((0, 14, 4.5))
    border_l = box(2.0, 28, 1.0, fillet=0.2).translate((-60, 0, 4.5))
    border_r = box(2.0, 28, 1.0, fillet=0.2).translate((60, 0, 4.5))
    obj = plate.union(border_front).union(border_rear).union(border_l).union(border_r)

    # Recessed block label.  The generated text is uppercase due to the simple
    # 5x7 font, but the part name remains "Paddy Swarm".
    obj = engrave_top_label(obj, "PADDY SWARM", 0, -1.5, 4.05, cell=1.25, depth=0.65)
    return obj


def make_commercial_box_reference():
    require_cadquery()
    x, y, z = 200, 300, 120
    outer = box(x, y, z, fillet=6).translate((0, 0, z / 2))
    inner = box(x - 8, y - 8, z - 8, fillet=3).translate((0, 0, z / 2 + 4))
    obj = outer.cut(inner)
    lid_outline = box(x + 8, y + 8, 5, fillet=3).translate((0, 0, z + 2.5))
    obj = obj.union(lid_outline)
    return add_top_label(obj, "COMBOX-REF", 0, 0, z + 5.2, cell=0.8)


def make_metal_rod_reference(diameter: float, length: float, axis: str = "x"):
    require_cadquery()
    if axis == "x":
        return cyl_x(diameter / 2, length)
    if axis == "y":
        return cyl_y(diameter / 2, length)
    return cyl_z(diameter / 2, length)


def make_parts() -> Dict[str, object]:
    require_cadquery()
    parts = {
        "PS-RV227-CHS-FL": make_chassis_quadrant("FL"),
        "PS-RV227-CHS-FR": make_chassis_quadrant("FR"),
        "PS-RV227-CHS-RL": make_chassis_quadrant("RL"),
        "PS-RV227-CHS-RR": make_chassis_quadrant("RR"),
        "PS-WBX-MCR-L": make_cradle_rail("L"),
        "PS-WBX-MCR-R": make_cradle_rail("R"),
        "PS-WBX-MCR-LOC-S": make_locator_set(),
        "PS-WBX-MCR-WDG-S": make_wedge_set(),
        "PS-WBX-MCR-LAT-S": make_latch_set(),
        "PS-WBX-MCR-GAUGE": make_height_gauge(),
        "PS-RV227-CBOX-BDY": make_printed_box_body("CBOX"),
        "PS-RV227-CBOX-LID": make_box_lid("CBOX"),
        "PS-RV227-BBOX-BDY": make_printed_box_body("BBOX"),
        "PS-RV227-BBOX-LID": make_box_lid("BBOX"),
        "PS-RV227-CBOX-GSK": make_box_gasket(),
        "PS-RV227-BBOX-GSK": make_box_gasket(),
        "PS-RV227-DBX-RC": make_raincoat_cover(),
        "PS-RV227-DBX-PLG-S": make_slot_plug_set(),
        "PS-RV227-NP-PADDY-SWARM": make_paddy_swarm_nameplate(),
        "PS-RCP-G1": make_control_panel(),
        "PS-RV227-RCP-BRKT": make_rcp_bracket(),
        "PS-WCH-G1": make_cable_hood(),
        "PS-RV227-PTO": make_pto_panel(),
        "PS-RV227-MPL": make_motor_pod("L"),
        "PS-RV227-MPR": make_motor_pod("R"),
        "PS-RV227-DRC-LF": make_drive_case_half("LF"),
        "PS-RV227-DRC-LR": make_drive_case_half("LR"),
        "PS-RV227-DRC-RF": make_drive_case_half("RF"),
        "PS-RV227-DRC-RR": make_drive_case_half("RR"),
        "PS-RV227-DRC-CVR-S": make_service_cover_set(),
        "PS-RV227-GEA-18T-S": make_gear_set(),
        "PS-RV227-IDR-S": make_idler_set(),
        "PS-RV227-PIN-S": make_pin_set(),
        "PS-RV227-WBASE-L": make_wheelbase_side("L"),
        "PS-RV227-WBASE-R": make_wheelbase_side("R"),
        "PS-RV227-DRIVE-L": make_drive_path_module("L"),
        "PS-RV227-DRIVE-R": make_drive_path_module("R"),
        "PS-RV227-AXLE-HUB-S": make_axle_hub_set(),
        "PS-RV227-FLT-L": make_float_pontoon("L"),
        "PS-RV227-FLT-R": make_float_pontoon("R"),
        "PS-RV227-HULL-SKID": make_hull_skid(),
        "PS-RV227-PAX-6X172-S": make_printed_axle_6x172_set(),
        "PS-RV227-PAX-4X54-S": make_printed_gear_rod_4x54_set(),
        "PS-RV227-PAX-6X52-S": make_printed_pto_rod_6x52_set(),
        "PS-RV227-LOWER-FRAME": make_lower_frame(),
        "PS-RV227-GBOX-INTERNAL-L": make_gearbox_internal("L"),
        "PS-RV227-GBOX-INTERNAL-R": make_gearbox_internal("R"),
        "PS-RV227-AXLE-SPROCKET-S": make_axle_sprocket_set(),
        "PS-RV227-FLT-BRACKET-S": make_float_bracket_set(),
        "PS-RV227-FLT-RCV-L": make_float_receiver_side("L"),
        "PS-RV227-FLT-RCV-R": make_float_receiver_side("R"),
        "PS-RV227-FLT-RCV-FR-S": make_float_receiver_front_rear_set(),
        "PS-RV227-FLT-STRAP-S": make_float_strap_set(),
        "PS-RV227-BELT-L": make_tpu_belt_loop("L"),
        "PS-RV227-BELT-R": make_tpu_belt_loop("R"),
        "PS-RV227-WHL-FL": make_wheel(),
        "PS-RV227-WHL-FR": make_wheel(),
        "PS-RV227-WHL-RL": make_wheel(),
        "PS-RV227-WHL-RR": make_wheel(),
    }
    return parts


def manifest_rows():
    rows = []
    for p in PARTS:
        rel_stl = f"stl/{p.stl_name}"
        rel_step = f"step/{Path(p.stl_name).with_suffix('.step').name}"
        x, y, z = p.bbox_lwh_mm
        is_tpu = "1" if p.material_group.upper() == "TPU" else "0"
        rows.append({
            "part_no": p.part_no,
            "part_id": p.part_no,
            "part_code": p.part_no,
            "label": p.part_no,
            "label_text": p.part_no,
            "name": p.name,
            "part_name": p.name,
            "qty": str(p.qty),
            "quantity": str(p.qty),
            "count": str(p.qty),
            "material": p.material,
            "material_hint": p.material,
            "material_group": p.material_group,
            "group": p.material_group,
            "is_tpu": is_tpu,
            "split_group": p.material_group,
            "plate_id": p.plate_id,
            "plate": p.plate_id,
            "plate_group": p.plate_id,
            "module": "common_rover_v227",
            "title": p.name,
            "stl": rel_stl,
            "stl_file": rel_stl,
            "stl_path": rel_stl,
            "file": rel_stl,
            "filename": rel_stl,
            "path": rel_stl,
            "file_path": rel_stl,
            "source_file": rel_stl,
            "source_path": rel_stl,
            "output_stl": rel_stl,
            "step": rel_step,
            "step_file": rel_step,
            "step_path": rel_step,
            "bbox_x": f"{x:.3f}",
            "bbox_y": f"{y:.3f}",
            "bbox_z": f"{z:.3f}",
            "printable": "1" if p.print_target else "0",
            "marked": "1",
            "notes": p.notes,
        })
    return rows


def write_csv(path: Path, rows: List[Dict[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = []
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifests(out_dir: Path, manifest_dir: Path):
    rows = manifest_rows()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    for name in ["print_manifest_generic_marked.csv", "print_manifest.csv", "print_manifest_common_rover_v2_25.csv"]:
        write_csv(out_dir / name, rows)
    for name in ["print_manifest_generic_marked.csv", "print_manifest_common_rover_v2_25.csv"]:
        write_csv(manifest_dir / name, rows)

    by_plate: Dict[str, List[str]] = {}
    for p in PARTS:
        by_plate.setdefault(p.plate_id, []).append(p.part_no)
    plate_rows = []
    for plate_id in sorted(by_plate):
        group = "TPU" if "TPU" in plate_id else "HARD"
        plate_rows.append({
            "plate_id": plate_id,
            "material_group": group,
            "items": "; ".join(by_plate[plate_id]),
            "notes": "auto-generated v223 lower-drivetrain moving-model plate group; dense v5.5 may split further if needed",
        })
    write_csv(out_dir / "plate_manifest.csv", plate_rows)
    write_csv(out_dir / "plate_manifest_common_rover_v2_25.csv", plate_rows)
    write_csv(manifest_dir / "plate_manifest_common_rover_v2_25.csv", plate_rows)

    write_csv(out_dir / "metal_reference_bom_common_rover_v2_25.csv", METAL_BOM)
    write_csv(manifest_dir / "metal_reference_bom_common_rover_v2_25.csv", METAL_BOM)


def write_design_contract(out_dir: Path):
    data = {
        "design": DESIGN,
        "parts": [asdict(p) for p in PARTS],
        "reference_parts": [asdict(p) for p in REFERENCE_PARTS],
        "metal_reference_bom": METAL_BOM,
        "v2_25_rebuild_rules": [
            "No floating labels on open-top CBOX/BBOX body cavities.",
            "CBOX/BBOX body each has exactly two narrowed small top-open cable-bundle notches; total four slots for two boxes.",
            "No external protruding collar or floating U-rib around top-open cable notches; bottom-only rounded guide bead only.",
            "Notch water management uses an open-top sloped cut: inner floor high, exterior floor low.",
            "Cable protection uses a bottom-only low rounded interior guide bead; no side posts and no exterior notch collar.",
            "Commercial 300x200x120 box is reference-only; printed dual 150x200x120 boxes are print targets.",
        ],
    }
    (out_dir / "paddy_swarm_common_rover_v2_25_design_contract.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")




def prepare_for_export(obj):
    """Best-effort fuse/clean before counting/exporting.

    This does not invent new geometry.  It asks CadQuery/OpenCascade to combine
    overlapping solids that CAD construction already intended to be one part.
    """
    try:
        obj = obj.combine(clean=True)
    except Exception:
        try:
            obj = obj.combine()
        except Exception:
            pass
    try:
        obj = obj.clean()
    except Exception:
        pass
    return obj


def count_cadquery_solids(obj) -> int:
    """Best-effort CadQuery solid count for floating-island QA.

    This does not modify geometry.  It reports suspicious multi-solid parts so
    we can fix CAD intentionally instead of blindly moving or joining unrelated
    pieces.  Multi-part sets should be connected by a sacrificial sprue base.
    """
    try:
        return len(obj.solids().vals())
    except Exception:
        try:
            val = obj.val()
            if hasattr(val, "Solids"):
                return len(list(val.Solids()))
        except Exception:
            pass
    return -1



def write_mesh_component_report(out_dir: Path, parts: List[PartSpec]):
    """Optional STL mesh component report.

    Uses trimesh only if available in the user's paddy-cad environment.  If not,
    writes a skipped report rather than failing CAD export.
    """
    report = []
    try:
        import trimesh  # optional
    except Exception as exc:
        report.append({
            "part_no": "TRIMESH_NOT_AVAILABLE",
            "stl_name": "",
            "mesh_components": "",
            "status": "SKIPPED",
            "notes": f"Install trimesh for STL-level component checks. Import error: {exc!r}",
        })
        write_csv(out_dir / "mesh_component_report_common_rover_v2_25.csv", report)
        return

    stl_dir = out_dir / "stl"
    for p in parts:
        stl_path = stl_dir / p.stl_name
        try:
            mesh = trimesh.load_mesh(stl_path, force="mesh")
            comps = mesh.split(only_watertight=False)
            count = len(comps)
            report.append({
                "part_no": p.part_no,
                "stl_name": p.stl_name,
                "mesh_components": str(count),
                "status": "CHECK_MULTI_COMPONENT" if count > 1 else "OK",
                "notes": "Multiple STL mesh components may indicate floating islands unless it is an intentionally sprued set.",
            })
        except Exception as exc:
            report.append({
                "part_no": p.part_no,
                "stl_name": p.stl_name,
                "mesh_components": "",
                "status": "ERROR",
                "notes": repr(exc),
            })
    write_csv(out_dir / "mesh_component_report_common_rover_v2_25.csv", report)


def export_models(out_dir: Path):
    require_cadquery()
    stl_dir = out_dir / "stl"
    step_dir = out_dir / "step"
    ref_stl = out_dir / "reference_stl"
    ref_step = out_dir / "reference_step"
    metal_stl = out_dir / "reference_metal_stl"
    metal_step = out_dir / "reference_metal_step"
    for d in [stl_dir, step_dir, ref_stl, ref_step, metal_stl, metal_step]:
        d.mkdir(parents=True, exist_ok=True)

    raw_parts = make_parts()
    parts = {}
    solid_report_rows = []
    for p in PARTS:
        obj = prepare_for_export(raw_parts[p.part_no])
        parts[p.part_no] = obj
        solid_count = count_cadquery_solids(obj)
        solid_report_rows.append({
            "part_no": p.part_no,
            "stl_name": p.stl_name,
            "solid_count": str(solid_count),
            "status": "CHECK_MULTI_SOLID" if solid_count not in (-1, 1) else "OK",
            "notes": "multi-solid may indicate a floating island unless this is an intentionally sprued set",
        })
        exporters.export(obj, str(stl_dir / p.stl_name))
        exporters.export(obj, str(step_dir / Path(p.stl_name).with_suffix(".step").name))

    write_csv(out_dir / "solid_component_report_common_rover_v2_25.csv", solid_report_rows)
    write_mesh_component_report(out_dir, PARTS)

    # Reference commercial box.
    com_ref = make_commercial_box_reference()
    exporters.export(com_ref, str(ref_stl / "PS-RV227-COMBOX-REF.stl"))
    exporters.export(com_ref, str(ref_step / "PS-RV227-COMBOX-REF.step"))

    # Reference metal rods.
    for idx, row in enumerate(METAL_BOM, 1):
        dia = float(row["diameter_mm"])
        length = float(row["length_mm"])
        name = f"REF-METAL-{idx:02d}-{int(dia)}mm-x-{int(length)}mm"
        rod = make_metal_rod_reference(dia, length, axis="x")
        exporters.export(rod, str(metal_stl / f"{name}.stl"))
        exporters.export(rod, str(metal_step / f"{name}.step"))


def make_zip(out_dir: Path) -> Path:
    zip_path = out_dir.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(out_dir.rglob("*")):
            if p.is_file() and p.resolve() != zip_path.resolve():
                zf.write(p, p.relative_to(out_dir.parent))
    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="rover_v227_out")
    parser.add_argument("--manifests", default="manifests")
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--make-zip", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out)
    manifest_dir = Path(args.manifests)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    write_design_contract(out_dir)
    write_manifests(out_dir, manifest_dir)

    if args.metadata_only:
        if args.make_zip:
            z = make_zip(out_dir)
            print(f"metadata-only complete: {out_dir}; zip={z}")
        else:
            print(f"metadata-only complete: {out_dir}")
        return 0

    export_models(out_dir)
    if args.make_zip:
        z = make_zip(out_dir)
        print(f"CadQuery exports complete: {out_dir}; zip={z}")
    else:
        print(f"CadQuery exports complete: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
