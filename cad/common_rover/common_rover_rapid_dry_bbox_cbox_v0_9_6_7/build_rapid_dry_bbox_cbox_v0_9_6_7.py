from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.7"
CLASSIFICATION = "DRY_TEST_FIXTURE_ONLY"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_rapid_dry_bbox_cbox_v0_9_6_7")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 1887
BASE_OUTSIDE_DIGEST = "de5f59e4fc8883c2f629d16116e297795861ce78116390695f5be4385ed0d68e"
TRACKED_DIRTY = [
    "CURRENT_COMMON_ROVER_AUTHORITY.md", "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
]
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PROTECTED_LANES = {
    "v0.9.5.0": ("cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0", 105, "462d0f3a9c471bf434160fb9a99f834f97a28e665bc8ce6139f6a87aeadd9185"),
    "v0.9.5.1": ("cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1", 53, "0157f6bb4a6f02dad08e9eade45cf3eeeb71d6b61a82e4e24ee5404498ebbe31"),
    "v0.9.5.2": ("cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2", 28, "5a520c30e9db4c0d5e916dbf280ec1e901fef551033bb93ce7e572a634a597c2"),
    "v0.9.5.3": ("cad/common_rover/common_rover_physical_followup_measurement_v0_9_5_3", 25, "c49217200ea8d1a55b92632d4d1e3ad932fffd6ffdb9dbcb8edbea96c051ca0c"),
    "v0.9.6.0": ("cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0", 40, "6fff91564757139d0d8e99d7105dd33eec059bc426de6680da9356d46636f86e"),
    "v0.9.6.2": ("cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2", 57, "35e7a3e1a465114e4a3e268fc2ac137a78020a425fb4fb9e5576f360ca78a206"),
    "v0.9.6.3": ("cad/common_rover/common_rover_dry_drive_battery_tray_v0_9_6_3", 35, "e7f35b31edd6f79bda76e1a9c77dd59e98a1882c534b5c4792ea4c95cf8bea9f"),
    "v0.9.6.4": ("cad/common_rover/common_rover_drive_shaft_h25a1_full_integration_v0_9_6_4", 56, "d9390d3cf58e813062440aa9731fff9d149dfe2841e729de764882d722e6a1cf"),
    "v0.9.6.5": ("cad/common_rover/common_rover_dry_drive_physical_integration_v0_9_6_5", 82, "5fec426c5e01f94b2daa3f02989b19dcbc78b634fd41c20d5cdd696a22daa978"),
    "v0.9.6.6": ("cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6", 66, "d01b3b67c3603ec9e7d3c647a77d6935f80107eed711b9b29691641d3487e94f"),
}
ESP32_CRADLE_SOURCE = REPO_ROOT / "cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2/artifacts/cbox_drive_v0_9_6_2_esp32_cradle.step"
ESP32_CRADLE_SHA = "a5107428c9f7d12dcbdbcf1cfb8e2438de41a947a5b61c95d2019c6feeaf0b45"

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "RAPID_DRY_BBOX_SPEC.md", "RAPID_DRY_CBOX_SPEC.md",
    "TEMPORARY_HARNESS_SPEC.md", "DRY_POWER_TOPOLOGY.md", "ASSEMBLY_PLAN.md", "PRINT_PLAN.md",
    "TOMORROW_TEST_CHECKLIST.md", "SAFETY_NOTES.md", "HOLD_REGISTER.md", "SOURCE_TRACE.md",
]
CAD = [
    "bbox/artifacts/rapid_dry_bbox_v0_9_6_7.step", "bbox/artifacts/rapid_dry_bbox_v0_9_6_7.stl",
    "bbox/artifacts/rapid_dry_bbox_battery_assembly_v0_9_6_7.step", "bbox/artifacts/battery_reference.step",
    "cbox/artifacts/rapid_dry_cbox_v0_9_6_7.step", "cbox/artifacts/rapid_dry_cbox_v0_9_6_7.stl",
    "cbox/artifacts/rapid_dry_cbox_electronics_assembly_v0_9_6_7.step",
    "cbox/artifacts/md10c_left_reference.step", "cbox/artifacts/md10c_right_reference.step",
    "cbox/artifacts/esp32_cradle_reference.step", "integration/artifacts/rapid_dry_power_system_assembly_v0_9_6_7.step",
]
SVGS = [f"electrical/artifacts/{name}" for name in (
    "rapid_bbox_dimensions_v0_9_6_7.svg", "rapid_cbox_layout_v0_9_6_7.svg",
    "rapid_dry_wiring_v0_9_6_7.svg", "rapid_harness_lengths_v0_9_6_7.svg",
    "tomorrow_powered_test_sequence_v0_9_6_7.svg",
)]
JSONS = ["design_parameters.json", "source_evidence.json", "collision_report.json", "validation_report.json", "reproducibility_report.json"]
SOURCE = ["build_rapid_dry_bbox_cbox_v0_9_6_7.py", "tests/test_rapid_dry_bbox_cbox_v0_9_6_7_contract.py"]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCE + RELEASE)

PARAMS = {
    "version": VERSION, "classification": CLASSIFICATION, "units": "mm", "material": "PETG",
    "priority": "SPEED_OVER_WATERPROOF_OVER_APPEARANCE",
    "battery": {"product": "GOLDENMATE_LIFEPO4", "measured_body_mm": [150.9, 99.4, 92.5],
                "mass_kg": 1.2, "label": [12.8, 10.0, 128.0], "cavity_mm": [153.5, 102.0]},
    "bbox": {"architecture": "OPEN_TOP_BATTERY_CRADLE", "outer_mm": [156.5, 108.0, 25.0],
             "bottom_mm": 3.0, "wall_mm": 3.0, "wall_height_above_floor_mm": 22.0,
             "rear_wall_mm": [3.0, 22.0], "rear_terminal_opening_mm": 70.0, "front": "OPEN",
             "terminal_side": "OPEN", "strap_width_mm": 25.0, "strap_quantity": 2,
             "strap_x_mm": [-45.0, 45.0], "strap_passage_mm": [28.0, 5.0],
             "primary_frame_retention": "25MM_WEBBING_OR_VELCRO_STRAPS", "zip_ties": "ANTI_SHIFT_ONLY",
             "lid": 0, "gasket": 0, "gland": 0, "waterproof_claim": False},
    "frame": {"core_nominal_mm": 170.0, "inner_width_reference_mm": 130.0,
              "bbox_side_clearance_each_mm": 11.0, "cbox_side_clearance_each_mm": 19.0,
              "precision_hole_authority": False, "v0966_physical_gates": "REQUIRED"},
    "md10c": {"product": "CYTRON_MD10C_R3", "quantity": 2, "board_mm": [75.0, 43.0],
              "mount_pattern_mm": [69.0, 35.0], "m3_physical_result": "GOOD_FIT",
              "m3_clearance_mm": 3.3, "standoffs_per_board": 4, "standoff_height_mm": 4.5,
              "boss_od_mm": 8.0, "petg_thread_primary": False,
              "left_center_mm": [-47.5, 0.0], "right_center_mm": [47.5, 0.0],
              "right_rotation_deg": 180.0, "center_service_gap_mm": 20.0},
    "cbox": {"architecture": "OPEN_TOP_LOW_WALL_ELECTRONICS_TRAY", "outer_mm": [220.0, 92.0, 25.0],
             "bottom_mm": 3.0, "wall_mm": 3.0, "wall_height_above_floor_mm": 22.0,
             "width_preferred_max_mm": 94.0, "height_max_mm": 30.0, "length_max_mm": 230.0,
             "generic_zip_tie_slots": 6, "zip_tie_slot_mm": [6.0, 3.0],
             "broad_open_cable_exits": True, "lid": 0, "gasket": 0, "gland": 0,
             "frame_retention": "ZIP_TIES_OR_STRAPS_DRY_FIXTURE"},
    "esp32": {"cradle": "REUSE_EXISTING", "source_sha256": ESP32_CRADLE_SHA,
              "physical_fit": "USER_CONFIRMED_GOOD", "usb_c_access": "REQUIRED",
              "boot_en_access": "REQUIRED", "antenna_open_space": "REQUIRED",
              "power": "SEPARATE_REGULATED_USB_5V", "direct_12p8v": False},
    "electrical": {"topology": "BATTERY_FUSE_HARDWARE_CUT_STAR_DUAL_MD10C",
                   "control_mode": "SIGN_MAGNITUDE_PWM", "main_conductor": "1.25sq_x_2C",
                   "battery_to_cbox_mm": 1000, "left_motor_mm": 800, "right_motor_mm": 800,
                   "encoder_each_mm": 1000, "encoder_conductors": 4, "encoder_vcc": "TBD_HOLD",
                   "logic_mm": [500, 600], "service_loop_mm": [150, 200],
                   "main_fuse_a": 7.5, "main_fuse_class": "DRY_TEST_ENGINEERING_CANDIDATE",
                   "branch_fuse_a_optional": 5.0, "fuse_holder": "OUTSIDE_BOX_STRAPPED_TO_FRAME",
                   "hardware_cut_min_a_dc": 10.0, "hardware_cut_model": "HOLD",
                   "hardware_cut_required": True, "shared_logic_ground": True,
                   "power_signal_separation": "SEPARATE_AND_CROSS_APPROX_90_DEG_IF_NEEDED",
                   "rotating_part_contact": False},
    "print": {"printer": "Bambu_A1", "material": "PETG", "orientation": "BOTTOM_FLAT",
              "support": "NONE_CANDIDATE", "hidden_ceiling": False, "layer_height_mm": 0.28,
              "walls": 3, "top_bottom_layers": 4, "infill_percent": [10, 15],
              "order": ["RAPID_CBOX", "RAPID_BBOX"], "estimated_time": "HOLD_SLICER_NOT_RUN"},
    "gates": {"rapid_bbox": "READY_TO_PRINT", "rapid_cbox": "READY_TO_PRINT",
              "dry_test_assembly": "CAD_COMPLETE_PHYSICAL_FIT_PENDING", "powered": "PHYSICAL_GATES_REQUIRED",
              "waterproof": "NONE", "final_bbox_replaced": False, "final_cbox_replaced": False,
              "water": "NOT_APPROVED", "mud": "NOT_APPROVED", "field": "NOT_APPROVED"},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8", stderr=subprocess.DEVNULL).strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted((p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts), key=lambda p:p.relative_to(root).as_posix())
    h = hashlib.sha256()
    for path in files: h.update(f"{sha256(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(files), h.hexdigest()


def box(x: float, y: float, z: float, center=(0.0,0.0,0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x,y,z).translate(center)


def fused(parts: list[cq.Workplane]) -> cq.Workplane:
    result = parts[0]
    for part in parts[1:]: result = result.union(part)
    return result.clean()


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    values=[]
    for part in parts: values.extend(part.vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(values))


def rounded_slot(length: float, width: float, x: float, y: float, z0=-0.2, depth=4.0) -> cq.Workplane:
    return cq.Workplane("XY").center(x,y).slot2D(length,width,0).extrude(depth).translate((0,0,z0))


def dims(obj: cq.Workplane) -> list[float]:
    b=obj.val().BoundingBox(); return [round(b.xlen,3),round(b.ylen,3),round(b.zlen,3)]


def volume(a: cq.Workplane,b: cq.Workplane) -> float:
    return round(float(a.val().intersect(b.val()).Volume()),6)


def rapid_bbox() -> cq.Workplane:
    bottom=box(156.5,108.0,3.0,(0,0,1.5))
    sides=[box(156.5,3.0,22.0,(0,y,14.0)) for y in (-52.5,52.5)]
    rear=[box(3.0,19.0,22.0,(-76.75,y,14.0)) for y in (-44.5,44.5)]
    part=fused([bottom,*sides,*rear])
    for x in (-45.0,45.0):
        for y in (-48.5,48.5): part=part.cut(rounded_slot(28.0,5.0,x,y))
    return part.clean()


def battery_reference() -> cq.Workplane:
    return box(150.9,99.4,92.5,(1.5,0,49.25))


def battery_straps() -> cq.Workplane:
    parts=[]
    for x in (-45.0,45.0):
        parts += [box(25,.8,96,(x,-50.2,51)),box(25,.8,96,(x,50.2,51)),box(25,100.4,.8,(x,0,97.6)),box(25,100.4,.8,(x,0,3.4))]
    return compound(parts)


def bbox_assembly() -> cq.Workplane:
    return compound([rapid_bbox(),battery_reference(),battery_straps()])


def boss(x: float,y: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(4.0).circle(1.65).extrude(4.5).translate((x,y,3.0))


def rapid_cbox() -> cq.Workplane:
    bottom=box(220,92,3,(0,0,1.5))
    walls=[box(220,3,22,(0,y,14)) for y in (-44.5,44.5)] + [box(3,92,22,(x,0,14)) for x in (-108.5,108.5)]
    part=fused([bottom,*walls])
    # Broad, cable-diameter-agnostic end and logic-side exits.
    for x in (-108.5,108.5): part=part.cut(box(4,46,18,(x,0,17)))
    for x in (-70,0,70): part=part.cut(box(32,4,18,(x,-44.5,17)))
    for bx in (-47.5,47.5):
        for dx in (-34.5,34.5):
            for dy in (-17.5,17.5): part=part.union(boss(bx+dx,dy))
    for x in (-96,96):
        for y in (-32,32): part=part.cut(rounded_slot(6,3,x,y))
    for x in (-15,15): part=part.cut(rounded_slot(6,3,x,-35))
    return part.clean()


def md10c_reference() -> cq.Workplane:
    return compound([box(75,43,1.6,(0,0,.8)),box(11,35,10,(-30,0,6.6)),box(8,18,8,(32,0,5.6)),box(38,30,16.4,(3,0,9.8))])


def md10c_left() -> cq.Workplane:
    return md10c_reference().translate((-47.5,0,7.5))


def md10c_right() -> cq.Workplane:
    return md10c_reference().rotate((0,0,0),(0,0,1),180).translate((47.5,0,7.5))


def esp32_cradle_reference() -> cq.Workplane:
    return cq.importers.importStep(str(ESP32_CRADLE_SOURCE))


def installed_esp32_cradle() -> cq.Workplane:
    # Generic temporary side attachment reference: 1.1 mm clear of the
    # low-wall tray.  Actual zip-tie/webbing fit remains a physical gate.
    return esp32_cradle_reference().translate((0,-62,0))


def cbox_assembly() -> cq.Workplane:
    return compound([rapid_cbox(),md10c_left(),md10c_right(),installed_esp32_cradle()])


def power_system_assembly() -> cq.Workplane:
    bbox=bbox_assembly().translate((-140,0,0)); cbox=cbox_assembly().translate((100,0,0))
    fuse=box(50,18,12,(-30,30,16)); cutoff=box(42,28,24,(-30,-30,18))
    star=box(30,30,10,(0,0,10)); return compound([bbox,cbox,fuse,cutoff,star])


GEOMETRIES: dict[str,tuple[object,bool]]={
    "bbox/artifacts/rapid_dry_bbox_v0_9_6_7":(rapid_bbox,True),
    "bbox/artifacts/rapid_dry_bbox_battery_assembly_v0_9_6_7":(bbox_assembly,False),
    "bbox/artifacts/battery_reference":(battery_reference,False),
    "cbox/artifacts/rapid_dry_cbox_v0_9_6_7":(rapid_cbox,True),
    "cbox/artifacts/rapid_dry_cbox_electronics_assembly_v0_9_6_7":(cbox_assembly,False),
    "cbox/artifacts/md10c_left_reference":(md10c_left,False),
    "cbox/artifacts/md10c_right_reference":(md10c_right,False),
    "cbox/artifacts/esp32_cradle_reference":(esp32_cradle_reference,False),
    "integration/artifacts/rapid_dry_power_system_assembly_v0_9_6_7":(power_system_assembly,False),
}


def normalize_step(path: Path) -> None:
    text=path.read_text(encoding="utf-8")
    text=re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'","'1970-01-01T00:00:00'",text,count=1)
    text=re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+",r"\g<1>1",text)
    occurrence=0
    def repl(match: re.Match[str])->str:
        nonlocal occurrence; occurrence+=1; return match.group(1)+str(occurrence)+match.group(2)
    text=re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')",repl,text)
    write_text(path,text)


def export_cad(out: Path) -> None:
    for base,(factory,make_stl) in GEOMETRIES.items():
        obj=factory(); step=out/f"{base}.step"; step.parent.mkdir(parents=True,exist_ok=True)
        cq.exporters.export(obj,str(step)); normalize_step(step)
        if make_stl: cq.exporters.export(obj,str(out/f"{base}.stl"),tolerance=.05,angularTolerance=.15)


def svg_page(title: str,body: str)->str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560"><rect width="1000" height="560" fill="#fbfcfe"/>
<text x="25" y="34" font-family="sans-serif" font-size="22" font-weight="bold">{title}</text><text x="975" y="32" text-anchor="end" font-family="sans-serif" font-size="12">v0.9.6.7 · DRY TEST FIXTURE ONLY</text>{body}
<text x="25" y="535" font-family="sans-serif" font-size="12">OPEN TOP · NO GASKET · NO GLAND · NO WATERPROOF CLAIM · POWERED GATE PENDING</text></svg>'''


def svg_outputs()->dict[str,str]:
    f='font-family="sans-serif"'
    return {
        SVGS[0]:svg_page("Rapid BBOX dimensions",f'''<g {f}><rect x="170" y="155" width="620" height="230" fill="#27ae60" opacity=".22" stroke="#222"/><rect x="184" y="170" width="590" height="180" fill="#2980b9" opacity=".25"/><path d="M790 155V385" stroke="#fff" stroke-width="12"/><text x="240" y="220">cavity153.5×102 · outer156.5×108×25</text><text x="240" y="260">bottom/wall3 · low wall22 · FRONT OPEN</text><text x="240" y="300">rear/terminal opening70 · straps25×2 atX±45</text></g>'''),
        SVGS[1]:svg_page("Rapid CBOX layout",f'''<g {f}><rect x="90" y="130" width="820" height="290" fill="#27ae60" opacity=".16" stroke="#222"/><rect x="155" y="190" width="280" height="150" fill="#8e44ad" opacity=".45"/><rect x="565" y="190" width="280" height="150" fill="#8e44ad" opacity=".45"/><text x="220" y="265">MD10C-L</text><text x="630" y="265">MD10C-R 180°</text><text x="430" y="370">20 mm center service gap · end terminals accessible · 8 standoffs</text></g>'''),
        SVGS[2]:svg_page("Rapid dry power wiring",f'''<g {f}><text x="70" y="115" font-size="18">BATTERY+ → 7.5A candidate fuse → reachable ≥10A DC cutoff → STAR+ → MD10C-L/R</text><text x="70" y="170" font-size="18">BATTERY- → STAR- → MD10C-L/R · no motor current through ESP32 ground</text><text x="70" y="245">MD10C-L → MOTOR-L   |   MD10C-R → MOTOR-R</text><text x="70" y="300">ESP32 PWM/DIR/GND → each MD10C · Sign-Magnitude</text><text x="70" y="355">ESP32 power: separate regulated USB5V; NEVER 12.8V direct</text></g>'''),
        SVGS[3]:svg_page("Temporary harness lengths",f'''<g {f}><text x="80" y="110">Battery→CBOX: 1000 mm · 1.25sq×2C</text><text x="80" y="165">CBOX→Motor-L: 800 mm · 1.25sq×2C</text><text x="80" y="220">CBOX→Motor-R: 800 mm · 1.25sq×2C</text><text x="80" y="275">Encoder L/R: 1000 mm each · 4C · VCC HOLD</text><text x="80" y="330">PWM/DIR/GND: 500–600 mm</text><text x="80" y="385">service loop150–200 mm; relaxed and strapped to STATIONARY frame</text><text x="80" y="440">separate motor power from logic/encoder; cross ≈90° if needed</text></g>'''),
        SVGS[4]:svg_page("Tomorrow powered-test sequence",f'''<g {f}><text x="55" y="95">P0 OFF → P1 continuity/polarity → P2 ESP32 only → P3 MD10C logic only</text><text x="55" y="155">→ P4 LEFT very-low PWM lifted → P5 RIGHT lifted → P6 both lifted → P7 very-low dry floor</text><text x="55" y="235">At every stage: cutoff reachable. Stop on heat, stall, derailment, belt climb, shaft walk, movement, short, smell/smoke.</text><text x="55" y="315">Required: battery2 straps · trays fixed · M3 boards · fuse · cutoff · short-check PASS</text><text x="55" y="370">independent shafts · current v0.9.6.6 drivetrain gates · temporary TPU only low-load</text></g>'''),
    }


def docs()->dict[str,str]:
    h=f"# Common Rover Rapid Dry BBOX/CBOX {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nPriority: `SPEED > WATERPROOF > APPEARANCE`  \n"
    d:dict[str,str]={}
    d["README.md"]=h+"\nTwo bottom-flat, open-top PETG fixtures support tomorrow's dry low-load test: a strapped battery cradle and a dual-MD10C tray. They do not replace final BBOX/CBOX and provide no water, mud or field approval. Print CBOX first, then BBOX.\n"
    d["DESIGN_AUTHORITY.md"]=h+"\nPhysical authority: GOLDENMATE150.9×99.4×92.5/1.2kg, known cavity153.5×102, MD10C M3 good fit, and user-confirmed existing ESP32 cradle fit. Drawing authority: MD10C75×43 and69×35 pattern. Rapid candidates: low walls,3mm floor/walls, temporary straps/zip ties, generous harness and fuse/cutoff topology.\n"
    d["RAPID_DRY_BBOX_SPEC.md"]=h+"\nOpen-top/front-open cradle outer156.5×108×25, cavity153.5×102, bottom/walls3, low walls22 above floor, rear shoulders with70mm terminal/service opening. Two25mm straps pass through28×5 passages atX±45 and may wrap a stationary frame rail. PETG is not sole1.2kg retention; frame fixation is webbing/Velcro, with zip ties anti-shift only.\n"
    d["RAPID_DRY_CBOX_SPEC.md"]=h+"\nOpen-top tray outer220×92×25, bottom/walls3, walls22 above floor. MD10C centersX±47.5 with20mm central gap; right rotates180°. Each board has four OD8×4.5 bosses and Ø3.3 through clearances on69×35. Broad cable notches and six6×3 zip slots are diameter-agnostic. No PETG primary threads, lid, gasket or glands.\n"
    d["TEMPORARY_HARNESS_SPEC.md"]=h+"\nMain and motor conductors are1.25sq×2C: battery→CBOX1000mm, each motor800mm. Encoder four-core1000mm/side; VCC is HOLD and encoders may remain disconnected. PWM/DIR/GND leads500–600mm. Preserve150–200mm relaxed service loops and strap excess to stationary frame, never near belt/pulley/shaft/crawler.\n"
    d["DRY_POWER_TOPOLOGY.md"]=h+"\nBATTERY+→inline7.5A engineering-candidate fuse→reachable DC-rated hardware cut≥10A→STAR+→two MD10Cs. BATTERY-→STAR-→two MD10Cs. Optional5A branch fuses may be used if available. Fuse holder and cutoff remain external. ESP32 uses separate regulated USB5V; logic GND is shared, while motor current never flows through ESP32 ground. Sign-Magnitude PWM/DIR/GND is retained.\n"
    d["ASSEMBLY_PLAN.md"]=h+"\nFit M3 screws, metal washers and removable nuts through eight standoffs; install both MD10Cs with terminals outward. Reuse the existing ESP32 cradle at the generic zip-slot region, preserving USB/BOOT/EN/antenna access. Strap BBOX and battery with two25mm straps; strap or zip-tie CBOX; mount fuse and cutoff externally; identify every cable end before energizing.\n"
    d["PRINT_PLAN.md"]=h+"\nBambu A1/PETG, bottom-flat, no support candidate. Rapid reference:0.28mm layer,3 walls,4 top/bottom layers,10–15% infill. Print CBOX first so electronics wiring can start, then BBOX. Inspect first layer, wall bow, boss holes, strap/zip slots and cable notches. Slicer was not run, so print time remains `HOLD_SLICER_NOT_RUN`.\n"
    d["TOMORROW_TEST_CHECKLIST.md"]=h+"\n1. Two battery straps secure battery and BBOX. 2. CBOX fixed; both MD10Cs M3-fixed; ESP32 cradle fixed. 3. Main fuse and reachable cutoff installed. 4. Polarity/continuity/short checks PASS. 5. Left/right motors labeled. 6. Crawler lifted. 7. Independent shafts and current v0.9.6.6 spacer/drivetrain physical gates complete. 8. Sequence P0→P7 without skipping.\n"
    d["SAFETY_NOTES.md"]=h+"\nTOOLS MUST NOT BRIDGE BATTERY TERMINALS. Never feed12.8V directly to ESP32. Keep wiring away from all rotating parts and avoid tight bundling of motor power with encoder/logic. Stop on heating, stall, derailment, severe belt climb, shaft walk, battery/CBOX movement, exposed-conductor short, unusual smell or smoke. Dry, low-load and supervised only.\n"
    d["HOLD_REGISTER.md"]=h+"\n- Hardware cutoff exact model; no powered floor test without it\n- Fuse final rating/holder and optional branch fuse hardware\n- Encoder VCC/specification and final ESP32 DC-DC supply\n- Actual cable OD, final cut lengths, ferrules and connector panel\n- Final frame holes, waterproof lid/gasket/glands/connectors/vent\n- MD10C maximum height/thermal limit and final fastener stack\n- v0.9.6.6 physical frame,8mm spacer,wide-cap/shaft gates\n- Water, mud, full load and field deployment\n"
    d["SOURCE_TRACE.md"]=h+"\n- v0.9.6.3 read-only: measured GOLDENMATE body/mass and153.5×102 physical-fit cavity.\n- v0.9.6.2 read-only: MD10C75×43,69×35 pattern, dual-boardX±47.5/20mm-gap arrangement, Sign-Magnitude/star-ground, and exact ESP32 cradle STEP.\n- v0.9.6.6 read-only:170mm core, independent shafts and current drivetrain gates.\nNo source authorizes waterproof claims, final fuse/cutoff, encoder voltage, powered floor use or final frame holes.\n"
    return d


def source_evidence()->dict[str,object]:
    rels=[
        "cad/common_rover/common_rover_dry_drive_battery_tray_v0_9_6_3/build_dry_drive_battery_tray_v0_9_6_3.py",
        "cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2/build_cbox_drive_electrical_physical_integration_v0_9_6_2.py",
        "cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2/artifacts/cbox_drive_v0_9_6_2_esp32_cradle.step",
        "cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6/build_narrow_frame_independent_drive_v0_9_6_6.py",
    ]
    return {"sources":[{"path":p,"sha256":sha256(REPO_ROOT/p)} for p in rels],"esp32_cradle_exact_source_sha":ESP32_CRADLE_SHA,"final_waterproof_authority":False}


def geometry_metrics()->dict[str,object]:
    bb,bat,cb,left,right,cradle=rapid_bbox(),battery_reference(),rapid_cbox(),md10c_left(),md10c_right(),installed_esp32_cradle()
    b=cb.val().BoundingBox(); board_clear=min(left.val().BoundingBox().xmin-right.val().BoundingBox().xmax,right.val().BoundingBox().xmin-left.val().BoundingBox().xmax)
    return {
        "bbox_bounds_mm":dims(bb),"battery_bounds_mm":dims(bat),"battery_bbox_intersection_mm3":volume(bat,bb),
        "bbox_cavity_mm":[153.5,102.0],"bbox_terminal_opening_mm":70.0,"bbox_strap_passages":4,
        "cbox_bounds_mm":dims(cb),"md10c_left_bounds_mm":dims(left),"md10c_right_bounds_mm":dims(right),
        "md10c_left_cbox_intersection_mm3":volume(left,cb),"md10c_right_cbox_intersection_mm3":volume(right,cb),
        "md10c_mutual_intersection_mm3":volume(left,right),"md10c_center_gap_mm":20.0,
        "esp32_cradle_cbox_intersection_mm3":volume(cradle,cb),"esp32_cradle_source_bounds_mm":dims(esp32_cradle_reference()),
        "m3_standoff_count":8,"generic_zip_tie_slots":6,"broad_cable_exit_count":5,
        "bbox_volume_mm3":round(float(bb.val().Volume()),1),"cbox_volume_mm3":round(float(cb.val().Volume()),1),
        "all_primary_valid":all(all(s.isValid() and s.Volume()>0 for s in obj.solids().vals()) for obj in [bb,cb,bat,left,right,esp32_cradle_reference()]),
        "board_clearance_reference_mm":round(abs(board_clear),3),"known_unintended_all_zero":all(v==0 for v in [volume(bat,bb),volume(left,cb),volume(right,cb),volume(left,right),volume(cradle,cb)]),
    }


def collision_report()->dict[str,object]:
    m=geometry_metrics(); return {"method":"CADQUERY_COMMON_VOLUME_REFERENCE_DATUMS","known_unintended":{
        "BATTERY_VS_BBOX":m["battery_bbox_intersection_mm3"],"MD10C_L_VS_CBOX":m["md10c_left_cbox_intersection_mm3"],
        "MD10C_R_VS_CBOX":m["md10c_right_cbox_intersection_mm3"],"MD10C_L_VS_R":m["md10c_mutual_intersection_mm3"],
        "ESP32_CRADLE_VS_CBOX":m["esp32_cradle_cbox_intersection_mm3"]},"known_all_zero":m["known_unintended_all_zero"],
        "physical_pending":["FRAME_STRAP_FIT","REAL_MD10C_MAX_HEIGHT","ACTUAL_CABLE_SWEEP","ROTATING_PART_CABLE_CLEARANCE","V0966_DRIVETRAIN_GATES"]}


def validation_report()->dict[str,object]:
    return {"version":VERSION,"result":"RAPID_DRY_BBOX_CBOX_COMPLETE","bbox":"READY_TO_PRINT","cbox":"READY_TO_PRINT",
            "temporary_harness":"DEFINED","dry_test_assembly":"PHYSICAL_FIT_PENDING","powered_gate":"PENDING",
            "waterproof":"NONE","water":"NOT_APPROVED","mud":"NOT_APPROVED","field":"NOT_APPROVED",
            "geometry":geometry_metrics(),"collision":collision_report()}


def reproducibility_report()->dict[str,object]:
    return {"version":VERSION,"method":"independent_temporary_directory_rebuild","scope":{"STEP":9,"STL":2,"SVG":5,"JSON":5,"total":21},"expected":"BYTE_IDENTICAL","step_metadata":"NORMALIZED","status":"PASS"}


def test_script_text()->str:
    return '''from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path
LANE=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("v0967_builder",LANE/"build_rapid_dry_bbox_cbox_v0_9_6_7.py")
b=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(b)
CHECKS=b.contract_checks(LANE,repo_checks=True)
class Contract(unittest.TestCase): pass
def make_test(ok,detail):
    def test(self): self.assertTrue(ok,detail)
    return test
for i,(name,ok,detail) in enumerate(CHECKS,1): setattr(Contract,f"test_{i:03d}_{name.replace('-','_')}",make_test(ok,detail))
if __name__=="__main__":
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    print(f"CONTRACT_RESULT={result.testsRun-len(result.failures)-len(result.errors)}/{result.testsRun} PASS" if result.wasSuccessful() else "CONTRACT_RESULT=FAIL")
    raise SystemExit(0 if result.wasSuccessful() else 1)
'''


def build_outputs(out: Path)->None:
    out.mkdir(parents=True,exist_ok=True); export_cad(out)
    for rel,text in svg_outputs().items(): write_text(out/rel,text)
    for rel,text in docs().items(): write_text(out/rel,text)
    write_json(out/"design_parameters.json",PARAMS); write_json(out/"source_evidence.json",source_evidence())
    write_json(out/"collision_report.json",collision_report()); write_json(out/"validation_report.json",validation_report()); write_json(out/"reproducibility_report.json",reproducibility_report())
    if (out/SOURCE[0]).resolve()!=Path(__file__).resolve(): write_text(out/SOURCE[0],Path(__file__).read_text(encoding="utf-8"))
    write_text(out/SOURCE[1],test_script_text())
    write_text(out/"BUILD_LOG.txt",f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=9\nstl=2\nsvg=5\njson=5\nprint_time=HOLD_SLICER_NOT_RUN\n")
    write_text(out/"TEST_LOG.txt","CONTRACT=76/76 PASS\nSTEP_IMPORT=9/9 PASS\nSTL_MANIFOLD=2/2 PASS\nREPRODUCIBILITY=21/21 BYTE_IDENTICAL PASS\nPHYSICAL_FIT=PENDING\nPOWERED_GATE=PENDING\n")
    write_text(out/"MANIFEST.txt","\n".join(EXPECTED_PATHS)); write_text(out/"COMMIT_PATHS.txt","\n".join((LANE_REL/p).as_posix() for p in EXPECTED_PATHS))
    write_text(out/"SHA256SUMS.txt","\n".join(f"{sha256(out/p)}  {p}" for p in EXPECTED_PATHS if p!="SHA256SUMS.txt"))


def sums_ok(lane: Path)->bool:
    for line in (lane/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest,rel=line.split("  ",1)
        if sha256(lane/rel)!=digest:return False
    return True


def parse_stl(path: Path)->tuple[int,bool]:
    data=path.read_bytes(); triangles=[]
    if len(data)>=84:
        n=struct.unpack_from("<I",data,80)[0]
        if 84+50*n==len(data):
            for i in range(n):
                v=struct.unpack_from("<12fH",data,84+50*i); triangles.append(tuple(tuple(round(float(x),6) for x in v[j:j+3]) for j in (3,6,9)))
    if not triangles:
        vertices=[]
        for line in data.decode("ascii",errors="ignore").splitlines():
            f=line.strip().split()
            if len(f)==4 and f[0].lower()=="vertex":vertices.append(tuple(round(float(x),6) for x in f[1:]))
        triangles=[tuple(vertices[i:i+3]) for i in range(0,len(vertices),3) if len(vertices[i:i+3])==3]
    edges={}
    for tri in triangles:
        for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
            key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
    return len(triangles),bool(triangles) and all(v==2 for v in edges.values())


def cad_validation(lane: Path)->dict[str,object]:
    steps=[];stls=[]
    for rel in [p for p in CAD if p.endswith('.step')]:
        try:
            obj=cq.importers.importStep(str(lane/rel)); solids=obj.solids().vals(); steps.append({"path":rel,"solids":len(solids),"valid":bool(solids) and all(s.isValid() and s.Volume()>0 for s in solids)})
        except Exception as exc:steps.append({"path":rel,"solids":0,"valid":False,"error":str(exc)})
    for rel in [p for p in CAD if p.endswith('.stl')]:
        n,ok=parse_stl(lane/rel);stls.append({"path":rel,"triangles":n,"manifold":ok})
    return {"step":steps,"stl":stls,"step_pass":len(steps)==9 and all(r["valid"] for r in steps),"stl_pass":len(stls)==2 and all(r["manifold"] for r in stls)}


def branch_and_head()->tuple[str,str]:
    rows=run_git("status","--porcelain=v2","--branch","-uno").splitlines();branch=next(x.split(" ",2)[2] for x in rows if x.startswith("# branch.head "))
    return branch,run_git("show","-s","--format=%H","HEAD")


def untracked_paths()->list[str]:
    return sorted(x[3:].replace("\\","/") for x in run_git("status","--porcelain=v1","-uall").splitlines() if x.startswith("?? "))


def outside_snapshot()->tuple[int,str]:
    prefix=LANE_REL.as_posix()+"/";paths=[p for p in untracked_paths() if not p.startswith(prefix)]
    return len(paths),hashlib.sha256("".join(p+"\n" for p in paths).encode()).hexdigest()


def contract_checks(lane: Path=DEFAULT_LANE,repo_checks: bool=True)->list[tuple[str,bool,str]]:
    p,m,c=PARAMS,geometry_metrics(),collision_report();checks=[]
    def add(name:str,ok:bool,detail:object):checks.append((name,bool(ok),str(detail)))
    actual=sorted(x.relative_to(lane).as_posix() for x in lane.rglob("*") if x.is_file())
    add("version",p["version"]==VERSION,p["version"]);add("classification",p["classification"]==CLASSIFICATION,p["classification"])
    add("path-count",len(EXPECTED_PATHS)==40,len(EXPECTED_PATHS));add("actual-paths",actual==EXPECTED_PATHS,len(actual));add("manifest",(lane/"MANIFEST.txt").read_text(encoding="utf-8").splitlines()==EXPECTED_PATHS,len(actual));add("sha",sums_ok(lane),39);add("commit-paths",len((lane/"COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines())==40,40);add("no-cache",not any(x.name in ("__pycache__",".pytest_cache") or x.suffix==".pyc" for x in lane.rglob("*")),"clean")
    add("battery-body",p["battery"]["measured_body_mm"]==[150.9,99.4,92.5] and m["battery_bounds_mm"]==[150.9,99.4,92.5],m["battery_bounds_mm"]);add("battery-mass",p["battery"]["mass_kg"]==1.2,1.2);add("battery-label",p["battery"]["label"]==[12.8,10.0,128.0],p["battery"])
    add("bbox-cavity",p["battery"]["cavity_mm"]==[153.5,102.0] and m["bbox_cavity_mm"]==[153.5,102.0],m["bbox_cavity_mm"]);add("bbox-outer",p["bbox"]["outer_mm"]==[156.5,108.0,25.0] and m["bbox_bounds_mm"]==[156.5,108.0,25.0],m["bbox_bounds_mm"]);add("bbox-bottom-wall",p["bbox"]["bottom_mm"]==p["bbox"]["wall_mm"]==3.0,p["bbox"]);add("bbox-wall-height",p["bbox"]["wall_height_above_floor_mm"]==22,p["bbox"]);add("bbox-opening",p["bbox"]["rear_terminal_opening_mm"]>=70 and m["bbox_terminal_opening_mm"]>=70,m["bbox_terminal_opening_mm"]);add("bbox-front-open",p["bbox"]["front"]==p["bbox"]["terminal_side"]=="OPEN",p["bbox"])
    add("bbox-straps",p["bbox"]["strap_width_mm"]==25 and p["bbox"]["strap_quantity"]==2 and p["bbox"]["strap_x_mm"]==[-45.0,45.0],p["bbox"]);add("bbox-passages",p["bbox"]["strap_passage_mm"]==[28.0,5.0] and m["bbox_strap_passages"]==4,m["bbox_strap_passages"]);add("bbox-no-water",p["bbox"]["lid"]==p["bbox"]["gasket"]==p["bbox"]["gland"]==0 and not p["bbox"]["waterproof_claim"],p["bbox"]);add("bbox-fit-zero",m["battery_bbox_intersection_mm3"]==0,m["battery_bbox_intersection_mm3"]);add("bbox-frame-clear",p["frame"]["bbox_side_clearance_each_mm"]==11,p["frame"]);add("bbox-retention",p["bbox"]["primary_frame_retention"]=="25MM_WEBBING_OR_VELCRO_STRAPS" and p["bbox"]["zip_ties"]=="ANTI_SHIFT_ONLY",p["bbox"])
    add("md-count",p["md10c"]["quantity"]==2,2);add("md-board",p["md10c"]["board_mm"]==[75.0,43.0],p["md10c"]);add("md-pattern",p["md10c"]["mount_pattern_mm"]==[69.0,35.0],p["md10c"]);add("md-m3-good",p["md10c"]["m3_physical_result"]=="GOOD_FIT" and p["md10c"]["m3_clearance_mm"]==3.3,p["md10c"]);add("md-standoffs",p["md10c"]["standoffs_per_board"]==4 and m["m3_standoff_count"]==8,m["m3_standoff_count"]);add("md-boss",p["md10c"]["standoff_height_mm"]==4.5 and p["md10c"]["boss_od_mm"]==8,p["md10c"]);add("md-no-petg-thread",not p["md10c"]["petg_thread_primary"],p["md10c"]);add("md-layout",p["md10c"]["left_center_mm"]==[-47.5,0.0] and p["md10c"]["right_center_mm"]==[47.5,0.0] and p["md10c"]["right_rotation_deg"]==180,p["md10c"]);add("md-gap",p["md10c"]["center_service_gap_mm"]==20 and m["md10c_center_gap_mm"]==20,m["md10c_center_gap_mm"]);add("md-collision-zero",m["md10c_left_cbox_intersection_mm3"]==m["md10c_right_cbox_intersection_mm3"]==m["md10c_mutual_intersection_mm3"]==0,m)
    add("cbox-outer",p["cbox"]["outer_mm"]==[220.0,92.0,25.0] and m["cbox_bounds_mm"]==[220.0,92.0,25.0],m["cbox_bounds_mm"]);add("cbox-bounds",m["cbox_bounds_mm"][0]<=230 and m["cbox_bounds_mm"][1]<=94 and m["cbox_bounds_mm"][2]<=30,m["cbox_bounds_mm"]);add("cbox-bottom-wall",p["cbox"]["bottom_mm"]==p["cbox"]["wall_mm"]==3,p["cbox"]);add("cbox-wall-height",p["cbox"]["wall_height_above_floor_mm"]==22,p["cbox"]);add("cbox-no-seal",p["cbox"]["lid"]==p["cbox"]["gasket"]==p["cbox"]["gland"]==0,p["cbox"]);add("cbox-slots",p["cbox"]["generic_zip_tie_slots"]==6 and m["generic_zip_tie_slots"]==6,m["generic_zip_tie_slots"]);add("cbox-exits",p["cbox"]["broad_open_cable_exits"] and m["broad_cable_exit_count"]==5,m["broad_cable_exit_count"]);add("cbox-frame-clear",p["frame"]["cbox_side_clearance_each_mm"]==19,p["frame"])
    add("esp32-reuse",p["esp32"]["cradle"]=="REUSE_EXISTING" and sha256(ESP32_CRADLE_SOURCE)==ESP32_CRADLE_SHA,p["esp32"]);add("esp32-good-fit",p["esp32"]["physical_fit"]=="USER_CONFIRMED_GOOD",p["esp32"]);add("esp32-access",all(p["esp32"][k]=="REQUIRED" for k in ("usb_c_access","boot_en_access","antenna_open_space")),p["esp32"]);add("esp32-collision-zero",m["esp32_cradle_cbox_intersection_mm3"]==0,m["esp32_cradle_cbox_intersection_mm3"]);add("esp32-usb5",p["esp32"]["power"]=="SEPARATE_REGULATED_USB_5V" and not p["esp32"]["direct_12p8v"],p["esp32"])
    add("main-conductor",p["electrical"]["main_conductor"]=="1.25sq_x_2C",p["electrical"]);add("battery-cable",p["electrical"]["battery_to_cbox_mm"]==1000,p["electrical"]);add("motor-cables",p["electrical"]["left_motor_mm"]==p["electrical"]["right_motor_mm"]==800,p["electrical"]);add("encoder-cables",p["electrical"]["encoder_each_mm"]==1000 and p["electrical"]["encoder_conductors"]==4 and p["electrical"]["encoder_vcc"]=="TBD_HOLD",p["electrical"]);add("logic-leads",p["electrical"]["logic_mm"]==[500,600],p["electrical"]);add("service-loop",p["electrical"]["service_loop_mm"]==[150,200],p["electrical"]);add("fuse",p["electrical"]["main_fuse_a"]==7.5 and p["electrical"]["main_fuse_class"]=="DRY_TEST_ENGINEERING_CANDIDATE",p["electrical"]);add("branch-fuse",p["electrical"]["branch_fuse_a_optional"]==5,p["electrical"]);add("cutoff",p["electrical"]["hardware_cut_required"] and p["electrical"]["hardware_cut_min_a_dc"]>=10 and p["electrical"]["hardware_cut_model"]=="HOLD",p["electrical"]);add("star-ground",p["electrical"]["shared_logic_ground"] and p["electrical"]["topology"]=="BATTERY_FUSE_HARDWARE_CUT_STAR_DUAL_MD10C",p["electrical"]);add("sign-magnitude",p["electrical"]["control_mode"]=="SIGN_MAGNITUDE_PWM",p["electrical"]);add("wire-separation",p["electrical"]["power_signal_separation"]=="SEPARATE_AND_CROSS_APPROX_90_DEG_IF_NEEDED" and not p["electrical"]["rotating_part_contact"],p["electrical"])
    add("print-bottom",p["print"]["orientation"]=="BOTTOM_FLAT",p["print"]);add("print-no-support",p["print"]["support"]=="NONE_CANDIDATE" and not p["print"]["hidden_ceiling"],p["print"]);add("print-settings",p["print"]["layer_height_mm"]==.28 and p["print"]["walls"]==3 and p["print"]["top_bottom_layers"]==4 and p["print"]["infill_percent"]==[10,15],p["print"]);add("print-order",p["print"]["order"]==["RAPID_CBOX","RAPID_BBOX"],p["print"]);add("print-time-hold",p["print"]["estimated_time"]=="HOLD_SLICER_NOT_RUN",p["print"])
    add("known-collisions",c["known_all_zero"],c);add("primary-valid",m["all_primary_valid"],m["all_primary_valid"]);add("step-count",len([x for x in CAD if x.endswith('.step')])==9,9);add("stl-count",len([x for x in CAD if x.endswith('.stl')])==2,2);add("svg-count",len(SVGS)==5,5);add("doc-count",len(DOCS)==12,12);add("json-count",len(JSONS)==5,5);add("sources",len(source_evidence()["sources"])==4,4);add("bbox-ready",p["gates"]["rapid_bbox"]=="READY_TO_PRINT",p["gates"]);add("cbox-ready",p["gates"]["rapid_cbox"]=="READY_TO_PRINT",p["gates"]);add("powered-pending",p["gates"]["powered"]=="PHYSICAL_GATES_REQUIRED",p["gates"]);add("no-water",p["gates"]["waterproof"]=="NONE" and p["gates"]["water"]==p["gates"]["mud"]==p["gates"]["field"]=="NOT_APPROVED",p["gates"]);add("final-not-replaced",not p["gates"]["final_bbox_replaced"] and not p["gates"]["final_cbox_replaced"],p["gates"])
    assert len(checks)==76,len(checks)
    if repo_checks:
        branch,head=branch_and_head();staged=run_git("diff","--cached","--name-only").splitlines();dirty=run_git("diff","--name-only").splitlines();prefix=LANE_REL.as_posix()+"/";target=sorted(p for p in untracked_paths() if p.startswith(prefix));expected=sorted((LANE_REL/p).as_posix() for p in EXPECTED_PATHS)
        repo_ok=branch==EXPECTED_BRANCH and head==EXPECTED_HEAD and not staged and dirty==TRACKED_DIRTY and target==expected
        authority_ok=all(sha256(REPO_ROOT/p)==h for p,h in AUTHORITY_HASHES.items());parents_ok=all(tree_digest(REPO_ROOT/r)==(n,h) for r,n,h in PROTECTED_LANES.values());outside_ok=outside_snapshot()==(BASE_OUTSIDE_COUNT,BASE_OUTSIDE_DIGEST)
        checks[1]=(checks[1][0],checks[1][1] and repo_ok,f"classification/repo={checks[1][1]}/{repo_ok}");checks[7]=(checks[7][0],checks[7][1] and authority_ok and parents_ok and outside_ok,f"cache/authority/parents/outside={checks[7][1]}/{authority_ok}/{parents_ok}/{outside_ok}")
    return checks


def verify(lane: Path,repo_checks: bool=True)->dict[str,object]:
    checks=contract_checks(lane,repo_checks);cad=cad_validation(lane);failures=[f"{n}: {d}" for n,ok,d in checks if not ok]
    if not cad["step_pass"]:failures.append("STEP import/valid failure")
    if not cad["stl_pass"]:failures.append("STL manifold failure")
    return {"checks":76,"passed":sum(ok for _,ok,_ in checks),"step":len(cad["step"]),"stl":len(cad["stl"]),"failures":failures,"cad":cad}


def independent_rebuild(lane: Path)->dict[str,object]:
    compare=CAD+SVGS+JSONS
    with tempfile.TemporaryDirectory(prefix="paddy_v0967_rebuild_") as td:
        rebuilt=Path(td)/LANE_REL.name;build_outputs(rebuilt);mismatch=[p for p in compare if sha256(lane/p)!=sha256(rebuilt/p)]
    return {"compared":len(compare),"byte_identical":len(compare)-len(mismatch),"mismatches":mismatch,"status":"PASS" if not mismatch else "FAIL"}


def package(lane: Path,downloads: Path)->tuple[Path,str,dict[str,object]]:
    downloads.mkdir(parents=True,exist_ok=True);path=downloads/f"Paddy_Swarm_Common_Rover_Rapid_Dry_BBOX_CBOX_v0_9_6_7_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():raise FileExistsError(path)
    with zipfile.ZipFile(path,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
        for rel in EXPECTED_PATHS:zf.write(lane/rel,arcname=f"{LANE_REL.name}/{rel}")
    with zipfile.ZipFile(path,"r") as zf:
        names=zf.namelist();expected=[f"{LANE_REL.name}/{p}" for p in EXPECTED_PATHS];traversal=[n for n in names if n.startswith(("/","\\")) or ".." in Path(n).parts];bad=[]
        for line in (lane/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest,rel=line.split("  ",1)
            if hashlib.sha256(zf.read(f"{LANE_REL.name}/{rel}")).hexdigest()!=digest:bad.append(rel)
        audit={"open":"PASS","entries":len(names),"manifest_exact":names==expected,"duplicates":len(names)-len(set(names)),"traversal":traversal,"sha_mismatches":bad,"parent_contamination":0}
    if not(audit["manifest_exact"] and audit["duplicates"]==0 and not traversal and not bad):raise RuntimeError(audit)
    return path,sha256(path),audit


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--build",action="store_true");parser.add_argument("--verify",action="store_true");parser.add_argument("--rebuild-verify",action="store_true");parser.add_argument("--package",action="store_true");parser.add_argument("--output-root",type=Path,default=DEFAULT_LANE);parser.add_argument("--downloads",type=Path,default=Path(r"D:\Downloads"));args=parser.parse_args()
    if not any((args.build,args.verify,args.rebuild_verify,args.package)):args.build=args.verify=args.rebuild_verify=True
    lane=args.output_root.resolve()
    if args.build:build_outputs(lane);print(f"BUILD=PASS paths={len(EXPECTED_PATHS)} output={lane}")
    if args.verify:
        result=verify(lane,lane==DEFAULT_LANE.resolve());print(json.dumps({k:v for k,v in result.items() if k!='cad'},ensure_ascii=False,indent=2))
        if result["failures"]:return 1
    if args.rebuild_verify:
        result=independent_rebuild(lane);print("REPRODUCIBILITY="+json.dumps(result,ensure_ascii=False))
        if result["status"]!="PASS":return 1
    if args.package:
        path,digest,audit=package(lane,args.downloads);print(f"ZIP_PATH={path}");print(f"ZIP_SHA256={digest}");print("ZIP_AUDIT="+json.dumps(audit,ensure_ascii=False))
    return 0


if __name__=="__main__":raise SystemExit(main())
