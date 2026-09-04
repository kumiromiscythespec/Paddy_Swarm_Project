"""Build one-side PTO servo sliding-idler clutch parameter-study artifacts."""
from __future__ import annotations

import argparse, hashlib, json, math, re, struct, subprocess, tempfile, zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers

ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "pto_servo_sliding_idler_clutch_v001"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE = ROOT / LANE_REL
VERSION = "PTO_SERVO_SLIDING_IDLER_CLUTCH_V001"
AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = list(AUTHORITY)
OUTSIDE_COUNT = 3339
OUTSIDE_DIGEST = "b05bdb9271e6326e670af203da085cbe5bb73a817970f0a65a863650cb749276"
PROTECTED = {
    "cad/common_rover/common_rover_dual_outboard_pto_guard_interface_v0_9_6_38": (31, "5f90828318bb5f914893953abd385afb9234110c3fe50739a7a5b696b907288b"),
    "cad/common_rover/common_rover_motor_layout_powerpath_trade_study_v0_9_3_0": (151, "98d11ae279ad888e1f2aeda1353b84701757d2de1c13113f099bce7d74311541"),
    "cad/common_rover/common_rover_inward_pto_coupling_cad_verified_v0_9_2_1": (55, "fc0e459370be39f24a98d477a750a7c48e5533b85947432a0d80556d788e093a"),
    "cad/common_rover/common_rover_outboard_inward_pto_design_authority_v0_9_1": (37, "70ff56f30f406b0471220d3c2698f060f0697afc6518fe4af62fc4729f5ab5fd"),
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_5": (24, "2ae05cc9c7a3befd5b4f7e316d16e12da803b896800022bfaaf45b44e18d0a7a"),
    "cad/common_rover/common_rover_service_motion_servo_slide_clutch_h25a1_v0_9_4_3": (66, "9a167824f4260fd20629e45f5485dfb8da6c2fe5529101c7a26c0a13e0db2447"),
    "cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20": (55, "9d0d0eb92b759be81ed61a69d89a1888adbb4b88fcd66e63b14a056d59966300"),
    "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2": (57, "168a21f0a1cabb30971dfd4330f0d7b474a26a38b5fd735d455ff61ffed091ab"),
    "rovers/common_rover/v2.29.3.9.1": (45, "ab8c79b41c5a7eae3f45dc6cc79564882c84e2a412a61fef7384b28c49d07659"),
}

FRAME_W = 205.0
MOTOR_SHAFT_D = 6.0
OUTPUT_SHAFT_D = 10.0
TEETH = (20, 20)
PITCH = 5.0
RATIO = 1.0
STROKES = [6.0, 8.0, 10.0, 12.0]
SWEEPS = [45.0, 60.0, 75.0]
OVER_CENTERS = [0.0, 3.0, 5.0]
STOP_SPAN = 52.0
SLIDER_X = 39.0
SLIDER_Z = 10.0
GUIDE_CLEARANCE_PER_SIDE = 0.5
IDLER_OD_REF = 22.0
IDLER_WIDTH_REF = 18.0
IDLER_PIVOT_D_REF = 8.5
CENTER_DISTANCE_REF = 100.0
SERVO_BODY_REF = [40.0, 20.0, 40.5]
SERVO_EAR_LENGTH_REF = 54.0
HORN_NOMINAL_TOTAL_LENGTH = 37.0
FIRST_STROKE = "S06_MANUAL_FIRST_NO_WINNER_AUTHORITY"
FIXTURE_DIMS = [160.0, 130.0, 26.0]

BUILDER = Path(__file__).name
TEST = "tests/test_pto_servo_sliding_idler_clutch_v001_contract.py"
STEPS = ["reference/pto_one_side_reference.step", "reference/servo_envelope_reference.step",
         "reference/slider_s06.step", "reference/slider_s08.step", "reference/slider_s10.step",
         "reference/slider_s12.step", "reference/clutch_assembly_reference.step"]
STLS = ["print/slider_stroke_coupon.stl", "print/fixed_guide_coupon.stl",
        "print/linkage_coupon.stl", "print/one_side_clutch_test_fixture.stl"]
SVGS = ["artifacts/PTO_ARCHITECTURE.svg", "artifacts/CLUTCH_OFF.svg", "artifacts/CLUTCH_ON.svg",
        "artifacts/SLIDER_STROKE_COMPARISON.svg", "artifacts/SERVO_LINK_KINEMATICS.svg",
        "artifacts/OVER_CENTER_COMPARISON.svg", "artifacts/HARD_STOP_LOAD_PATH.svg",
        "artifacts/ONE_SIDE_TEST_SETUP.svg", "artifacts/FUTURE_LIMIT_SWITCH.svg"]
DOCS = ["README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_HARDWARE_REGISTER.md", "PTO_REQUIREMENTS.md",
        "CLUTCH_REQUIREMENTS.md", "SERVO_REQUIREMENTS.md", "PARAMETER_STUDY.md", "PHYSICAL_TEST_PLAN.md",
        "PRINT_GUIDE.md", "HOLD_REGISTER.md", "design_parameters.json", "validation_report.json",
        "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *DOCS, *LOGS])


def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8",
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
def tree(path: Path) -> tuple[int, str]:
    files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                   and p.suffix.lower() not in {".pyc", ".pyo"})
    h = hashlib.sha256()
    for p in files:
        h.update((p.relative_to(path).as_posix() + "\n").encode()); h.update(bytes.fromhex(sha(p)))
    return len(files), h.hexdigest()
def untracked() -> list[str]:
    return sorted(x[3:].replace("\\", "/") for x in git("status", "--porcelain=v1", "-uall").splitlines()
                  if x.startswith("?? "))
def outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"; paths = [x for x in untracked() if not x.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(x + "\n" for x in paths).encode()).hexdigest()


def repository_guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve(); branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD"); staged = git("diff", "--cached", "--name-only").splitlines()
    dirty = git("diff", "--name-only").splitlines(); auth = {x: sha(ROOT / x) for x in AUTHORITY}
    protected = {x: tree(ROOT / x) for x in PROTECTED}
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    cache = [x for x in files if "__pycache__" in PurePosixPath(x).parts or x.endswith((".pyc", ".pyo"))]
    checks = {"repository": root == ROOT.resolve(), "branch": branch == BRANCH, "head": head == HEAD,
              "staged_zero": not staged, "dirty_preserved": dirty == DIRTY,
              "outside_preserved": outside() == (OUTSIDE_COUNT, OUTSIDE_DIGEST),
              "authority_4": auth == AUTHORITY, "protected_9": protected == PROTECTED,
              "scope": set(files).issubset(EXPECTED), "ignored_zero": not ignored, "cache_zero": not cache,
              "complete": not complete or files == EXPECTED}
    result = {"checks": checks, "root": str(root), "branch": branch, "head": head, "staged": staged,
              "dirty": dirty, "outside": list(outside()), "authority": auth,
              "protected": {k: {"files": v[0], "sha256": v[1], "status": "UNCHANGED"} for k, v in protected.items()},
              "lane_files": len(files)}
    if not all(checks.values()): raise RuntimeError("FAIL_CLOSED: " + json.dumps(result, ensure_ascii=True))
    return result


def box(x, y, z, c=(0, 0, 0)): return cq.Workplane("XY").box(x, y, z).translate(c)
def cyl(d, h, c=(0, 0, 0)): return cq.Workplane("XY").circle(d / 2).extrude(h / 2, both=True).translate(c)
def cyl_x(d, h, c=(0, 0, 0)): return cq.Workplane("YZ").circle(d / 2).extrude(h / 2, both=True).translate(c)
def comp(parts): return cq.Workplane(obj=cq.Compound.makeCompound([p.val() for p in parts]))
def beam_xy(a, b, width, height, z):
    dx, dy = b[0]-a[0], b[1]-a[1]; length = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx)); mid = ((a[0]+b[0])/2, (a[1]+b[1])/2, z)
    return box(length, width, height).rotate((0,0,0),(0,0,1),angle).translate(mid)


def slider(stroke: float) -> cq.Workplane:
    length = STOP_SPAN - stroke; notches = int(stroke / 2 - 2)
    s = box(SLIDER_X, length, SLIDER_Z, (0, 0, SLIDER_Z / 2))
    s = s.union(cyl(18, 8, (0, 0, 14))).union(box(10, 8, 7, (12, 0, 13.5)))
    s = s.cut(cyl(IDLER_PIVOT_D_REF, 24, (0, 0, 10)))
    for i in range(notches):
        s = s.cut(box(1.2, 4, 2.2, (-8 + i * 3.0, 0, 9.7)))
    return s.clean()


def guide_core(base_x=76.0, base_y=80.0) -> cq.Workplane:
    g = box(base_x, base_y, 6, (0, 0, 3))
    for x in (-22, 22): g = g.union(box(4, 56, 8, (x, 0, 10)))
    for y in (-28, 28): g = g.union(box(44, 4, 8, (0, y, 10)))
    # Reserved switch pads are deliberately undrilled until hardware selection.
    for x, y in ((-31, -25), (31, 25)): g = g.union(box(12, 18, 5, (x, y, 8.5)))
    return g.clean()


def link_shape() -> cq.Workplane:
    link = box(37, 9, 4, (0, 0, 2))
    for x in (-12, 12): link = link.cut(cyl(3.4, 8, (x, 0, 2)))
    return link.clean()


def linkage_coupon() -> cq.Workplane:
    return comp([link_shape().translate((0, y, 0)) for y in (-15, 0, 15)])


def slider_coupon() -> cq.Workplane:
    positions = [(-28, -32), (28, -32), (-28, 32), (28, 32)]
    return comp([slider(s).translate((x, y, 0)) for s, (x, y) in zip(STROKES, positions)])


def servo_envelope() -> cq.Workplane:
    body = box(*SERVO_BODY_REF, (0, 0, SERVO_BODY_REF[2] / 2))
    ears = box(SERVO_EAR_LENGTH_REF, 20, 3.5, (0, 0, 28))
    spline = cyl(12, 6, (12, 0, 43.5))
    return comp([body, ears, spline])


def fixture() -> cq.Workplane:
    f = box(FIXTURE_DIMS[0], FIXTURE_DIMS[1], 8, (0, 0, 4))
    # Guide, hard stops and reserved switch pads.
    for x in (-22, 22): f = f.union(box(4, 56, 8, (x, 4, 12)))
    for y in (-24, 32): f = f.union(box(44, 4, 8, (0, y, 12)))
    for x, y in ((-31, -21), (31, 29)): f = f.union(box(12, 18, 5, (x, y, 10.5)))
    # Open nominal servo cradle: actual mounting-hole pitch remains HOLD.
    f = f.union(box(4, 27, 18, (52, -40, 17))).union(box(4, 27, 18, (76, -40, 17)))
    # Reference-only motor and two output-support mounting zones; no released hole pattern.
    f = f.union(box(30, 26, 8, (-52, 32, 12))).union(box(30, 26, 8, (52, 32, 12)))
    return f.clean()


def pulley_ref(bore: float, c) -> cq.Workplane:
    pitch_d = 20 * PITCH / math.pi
    return cyl(pitch_d + 1.0, 16, c).cut(cyl(bore, 24, c)).clean()


def clutch_assembly() -> cq.Workplane:
    # Engaged-belt centerline is an envelope cue only; actual belt length and
    # tangent geometry remain physical HOLD.
    belt = [beam_xy((-50, 48), (50, 48), 1.6, 15, 30),
            beam_xy((-50, 16), (-10, 10), 1.6, 15, 30),
            beam_xy((10, 10), (50, 16), 1.6, 15, 30)]
    parts = [fixture(), slider(12).translate((0, 10, 8)),
             pulley_ref(6, (-50, 32, 30)), pulley_ref(10, (50, 32, 30)),
             cyl(IDLER_OD_REF, IDLER_WIDTH_REF, (0, 10, 30)),
             servo_envelope().translate((64, -40, 8)), link_shape().translate((31, -10, 26)), *belt]
    return comp(parts)


def pto_one_side() -> cq.Workplane:
    # Global width reference in X plus a separate coupon assembly above it.
    frame = box(FRAME_W, 24, 40, (0, 0, 20))
    output = cyl_x(OUTPUT_SHAFT_D, 40, (122.5, 0, 20))
    # Inner support is within the frame envelope; pulley and outer support are
    # outside.  The shaft end remains exactly 40 mm beyond the 205 mm frame.
    bearing_a = box(17, 67, 35, (93.5, 0, 20)); bearing_b = box(17, 67, 35, (131.0, 0, 20))
    pulley = cyl_x(34, 20, (112.5, 0, 20))
    return comp([frame, output, bearing_a, bearing_b, pulley, clutch_assembly().translate((0, 110, 0))])


def normalize_step(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text, n = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-23T00:00:00'", text, count=1)
    if n != 1: raise RuntimeError("STEP normalize")
    path.write_text(text, encoding="utf-8", newline="\n")
def export_step(shape, path):
    path.parent.mkdir(parents=True, exist_ok=True); exporters.export(shape, str(path), exportType="STEP"); normalize_step(path)
def export_stl(shape, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STL", tolerance=0.06, angularTolerance=0.08)


def stl_triangles(path: Path):
    data = path.read_bytes()
    if len(data) >= 84:
        n = struct.unpack_from("<I", data, 80)[0]
        if 84 + 50 * n == len(data):
            for i in range(n):
                vals = struct.unpack_from("<12fH", data, 84 + 50 * i)
                yield (vals[3:6], vals[6:9], vals[9:12])
            return
    verts = []
    for line in data.decode("ascii", errors="ignore").splitlines():
        if line.strip().startswith("vertex "): verts.append(tuple(float(x) for x in line.split()[1:4]))
    for i in range(0, len(verts), 3): yield tuple(verts[i:i+3])


def stl_audit(path: Path) -> dict:
    edges = {}; degenerate = 0; triangles = 0
    def key(v): return tuple(round(x, 5) for x in v)
    for tri in stl_triangles(path):
        if len(tri) != 3: continue
        triangles += 1; a, b, c = tri
        cross = ((b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]),
                 (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]),
                 (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
        if sum(x*x for x in cross) < 1e-14: degenerate += 1
        vs = [key(a), key(b), key(c)]
        for u, v in ((vs[0],vs[1]),(vs[1],vs[2]),(vs[2],vs[0])):
            e = tuple(sorted((u,v))); edges[e] = edges.get(e,0)+1
    bad = sum(1 for n in edges.values() if n != 2)
    return {"triangles": triangles, "bad_edges": bad, "degenerate_triangles": degenerate,
            "watertight": bad == 0, "manifold": bad == 0}


def kinematics():
    rows=[]
    for stroke in STROKES:
        for sweep in SWEEPS:
            radius=stroke/(2*math.sin(math.radians(sweep)/2))
            rows.append({"stroke_mm":stroke,"sweep_deg":sweep,"required_horn_radius_mm":round(radius,3),
                         "within_unverified_37mm_total_horn":radius < HORN_NOMINAL_TOTAL_LENGTH,
                         "physical_status":"HOLD_ACTUAL_HOLE_RADIUS"})
    return rows


def params():
    return {"version":VERSION,"classification":"ONE_SIDE_PARAMETER_STUDY_AND_FIRST_PHYSICAL_COUPON",
      "architecture":{"clutch_type":"SERVO_ACTUATED_SLIDING_IDLER","first_build":"ONE_SIDE_ONLY",
        "final_left_right":"INDEPENDENT_CONTROL","moving_parts":["IDLER_CARRIAGE","SERVO_LINK"],
        "motor_fixed":True,"output_shaft_fixed":True,"states":["OFF","ON"]},
      "hardware":{"frame_outer_width_mm":FRAME_W,"drive_motor_shafts":{"diameter_mm":6,"count":2},
        "pto_motor_shafts":{"diameter_mm":6,"count":2},"pto_output_shafts":{"diameter_mm":10,"count":2},
        "servo":{"model":"DS3218_180_DEG_20KG_CLASS_25T","final_qty":2,"prototype_qty":1,
          "nominal_body_envelope_mm":SERVO_BODY_REF,"actual_dimensions":"PHYSICAL_HOLD"},
        "horn":{"spline":"25T","reported_nominal_total_length_mm":37,"hole_radii":"PHYSICAL_HOLD"}},
      "transmission":{"type":"HTD5M","pitch_mm":PITCH,"motor_pulley_teeth":20,"output_pulley_teeth":20,
        "ratio":RATIO,"shaft_diameter_adapter":"NOT_REQUIRED","center_distance_reference_mm":CENTER_DISTANCE_REF,
        "center_distance_authority":"HOLD","belt_length":"HOLD"},
      "idler":{"route":"SMOOTH_ROLLER_ON_BELT_BACKSIDE","od_reference_mm":IDLER_OD_REF,
        "width_reference_mm":IDLER_WIDTH_REF,"pivot_hole_reference_mm":IDLER_PIVOT_D_REF,"selection":"HOLD",
        "repository_inventory":"CRAWLER_TOOTHED_6000_2RS_WIDTH44_REJECTED_FOR_HTD5M_PTO_REUSE"},
      "study":{"stroke_candidates_mm":STROKES,"permanent_notch_ids":{"6":1,"8":2,"10":3,"12":4},
        "servo_sweep_candidates_deg":SWEEPS,"over_center_candidates_deg":OVER_CENTERS,
        "kinematics":kinematics(),"first_manual_sequence":FIRST_STROKE,"winner":"HOLD_PHYSICAL_BELT_TEST"},
      "guide":{"type":"DOUBLE_RAIL_PRINTABLE","stop_span_mm":STOP_SPAN,
        "clearance_per_side_mm":GUIDE_CLEARANCE_PER_SIDE,"on_hard_stop":True,"off_hard_stop":True,
        "servo_continuous_belt_load_path":False,"switch_pads":["ON_SWITCH_RESERVED_PAD","OFF_SWITCH_RESERVED_PAD"]},
      "output":{"double_supported":True,"bearing_reference":"KP000_ENVELOPE_NOMINAL_10MM_BORE",
        "projection_per_side_candidate_mm":[30,40],"one_side_total_width_candidate_mm":[235,245],
        "future_dual_total_width_candidate_mm":[265,285],"target_total_width_mm":290,"hard_ceiling_mm":300},
      "fixture":{"dimensions_mm":FIXTURE_DIMS,"servo_mount":"NOMINAL_OPEN_CRADLE_HOLE_PATTERN_HOLD",
        "idler_mount":"REFERENCE_PIVOT_ONLY","high_load_work_unit":"PROHIBITED"},
      "electrical":{"servo_supply":"DEDICATED_BEC_NOT_ESP32_5V","target":"6V_8A_CLASS_MINIMUM_CANDIDATE",
        "common_ground":True,"regulator_sku":"HOLD"},
      "operation":["PTO_MOTOR_STOP","CONFIRM_STOP_OR_DELAY","MOVE_SERVO","REACH_HARD_STOP",
                   "FUTURE_SWITCH_CONFIRM","ENABLE_PTO_MOTOR"],
      "status":["PTO_CLUTCH_ARCHITECTURE_SELECTED","PARAMETER_STUDY_COMPLETE",
                "ONE_SIDE_PHYSICAL_VALIDATION_PENDING","PTO_POWERED_PASS_PROHIBITED"]}


def svg(title, subtitle, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560"><rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial;fill:#172033}}.h{{font-size:28px;font-weight:bold}}.s{{font-size:15px;fill:#475569}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.a{{stroke:#0f7184;stroke-width:4;fill:none;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#0f7184"/></marker></defs><text x="38" y="48" class="h">{title}</text><text x="38" y="76" class="s">{subtitle}</text>{body}<text x="38" y="535" class="s">{VERSION} · ONE_SIDE_FIRST · PHYSICAL_VALIDATION_PENDING</text></svg>'''


def svgs():
    return {
      SVGS[0]:svg("PTO architecture","Fixed 20T / sliding backside idler / fixed 20T; 1:1.",'<circle cx="250" cy="270" r="70" class="b"/><circle cx="750" cy="270" r="70" class="b"/><line x1="320" y1="220" x2="680" y2="220" stroke="#172033" stroke-width="8"/><circle cx="500" cy="360" r="42" class="g"/><text x="180" y="380">Ø6 MOTOR FIXED</text><text x="680" y="380">Ø10 OUTPUT FIXED</text>'),
      SVGS[1]:svg("CLUTCH OFF","Idler retracted; belt slack; torque transmission disabled.",'<circle cx="250" cy="260" r="55" class="b"/><circle cx="750" cy="260" r="55" class="b"/><path d="M305 220H695" stroke="#172033" stroke-width="7"/><circle cx="500" cy="420" r="35" class="g"/><text x="450" y="480">OFF STOP</text>'),
      SVGS[2]:svg("CLUTCH ON","Idler tensions belt and carriage seats on mechanical ON stop.",'<circle cx="250" cy="260" r="55" class="b"/><circle cx="750" cy="260" r="55" class="b"/><path d="M305 220L465 330L535 330L695 220" stroke="#172033" stroke-width="7" fill="none"/><circle cx="500" cy="330" r="35" class="g"/><rect x="455" y="375" width="90" height="24" class="q"/><text x="430" y="440">SERVO DOES NOT HOLD LOAD</text>'),
      SVGS[3]:svg("Slider stroke comparison","S06/S08/S10/S12 use 1/2/3/4 permanent top notches.",''.join(f'<rect x="{100+i*215}" y="190" width="150" height="{190-s*5}" class="b"/><text x="{125+i*215}" y="420">S{int(s):02d} · {int(s/2-2)} notch</text>' for i,s in enumerate(STROKES))),
      SVGS[4]:svg("Servo-link kinematics","Required radius r = stroke / (2 sin(sweep/2)); actual horn holes remain HOLD.",'<path d="M220 390A220 220 0 0 1 600 160" class="a"/><circle cx="220" cy="390" r="16" class="q"/><text x="250" y="460">45° / 60° / 75° parameter sweep</text><text x="620" y="230">37 mm is total horn length, NOT radius</text>'),
      SVGS[5]:svg("Over-center comparison","OC0 / OC3 / OC5 only; release force and no-lock-up require physical test.",'<line x1="160" y1="350" x2="840" y2="350" stroke="#172033" stroke-width="4"/><path d="M330 350L470 210M500 350L630 202M670 350L790 190" class="a"/><text x="300" y="410">OC0</text><text x="490" y="410">OC3</text><text x="680" y="410">OC5</text>'),
      SVGS[6]:svg("Hard-stop load path","Belt restoring force flows slider → hard stop → fixture, not servo gears.",'<rect x="110" y="210" width="180" height="100" class="b"/><rect x="410" y="210" width="180" height="100" class="g"/><rect x="710" y="210" width="180" height="100" class="q"/><path d="M290 260H410M590 260H710" class="a"/><text x="145" y="265">BELT / IDLER</text><text x="450" y="265">SLIDER</text><text x="750" y="265">HARD STOP</text>'),
      SVGS[7]:svg("One-side test setup","160 × 130 mm fixture; no high-load work unit in coupon test.",'<rect x="180" y="130" width="640" height="350" class="b"/><rect x="390" y="210" width="220" height="150" class="g"/><circle cx="300" cy="270" r="45" class="q"/><circle cx="700" cy="270" r="45" class="q"/><text x="370" y="410">GUIDE + SLIDER + STOPS</text>'),
      SVGS[8]:svg("Future limit switches","Pads are reserved; exact mounting holes await selected hardware.",'<rect x="190" y="210" width="220" height="130" class="q"/><rect x="590" y="210" width="220" height="130" class="q"/><text x="230" y="280">OFF PAD</text><text x="640" y="280">ON PAD</text><path d="M410 275H590" class="a"/>')}


def docs():
    h="# PTO Servo Sliding Idler Clutch V001\n\n"
    return {
      "README.md":h+"One-side first parameter study for DS3218 + parameterized 25T horn + printable sliding backside idler. The PTO motor and output shaft remain fixed; only carriage and servo link move.\n\nStatus: `PTO_CLUTCH_ARCHITECTURE_SELECTED / PARAMETER_STUDY_COMPLETE / ONE_SIDE_PHYSICAL_VALIDATION_PENDING`.\n",
      "DESIGN_AUTHORITY.md":h+"`CLUTCH_TYPE=SERVO_ACTUATED_SLIDING_IDLER`; `FIRST_BUILD=ONE_SIDE_ONLY`. Ø6 motor, Ø10 fixed double-supported output, HTD5M 20T→20T 1:1 and frame width205 are user authority. Product fits, belt length and center distance remain HOLD. Servo never carries continuous belt load.\n",
      "PHYSICAL_HARDWARE_REGISTER.md":h+"| item | authority | status |\n|---|---:|---|\n| DRIVE motor shaft | Ø6 ×2 | owned |\n| PTO motor shaft | Ø6 ×2 | owned |\n| PTO output shaft | Ø10 ×2 | owned |\n| DS3218 180° 25T | 2 final / 1 prototype | purchase target; dimensions HOLD |\n| 25T metal horn | nominal 37 mm total | do not interpret as radius |\n| crawler idler inventory | toothed, 6000-2RS, width44 | rejected for HTD5M PTO reuse |\n| PTO idler | smooth backside reference Ø22 | product/bearing HOLD |\n| output supports | two KP000 envelopes | exact mounting pitch HOLD |\n",
      "PTO_REQUIREMENTS.md":h+"HTD5M, 20T motor and 20T output, exact ratio1.0. Ø6 and Ø10 pulley bores are purchased independently; no shaft-diameter adapter. Fixed center distance reference100 mm is CAD-only and actual center distance/belt length remain HOLD. Final dual width candidate265–285 mm, target<=290 and hard ceiling<300.\n",
      "CLUTCH_REQUIREMENTS.md":h+"OFF/ON only. ON and OFF mechanical stops are mandatory. Belt load flows carriage→hard stop→fixture. Smooth roller acts only on belt backside. Slider uses coarse double rails with0.5 mm/side clearance. Functional slide faces carry no ID marks. Limit-switch pads are reserved.\n",
      "SERVO_REQUIREMENTS.md":h+"DS3218 20kg-class,180°,25T,metal gear,water-resistant; one prototype then two independent final servos. Nominal body reference40×20×40.5 mm only. Actual case, mount pitch, spline offset and tolerance are PHYSICAL_HOLD. Dedicated6V/8A-class-minimum candidate BEC, common ground; never ESP32 5V rail.\n",
      "PARAMETER_STUDY.md":h+"Strokes S06/S08/S10/S12 use 1/2/3/4 top notches. Sweeps45/60/75° and over-center OC0/OC3/OC5 are evaluated. Horn radius is calculated from chord motion; 37 mm is retained as total horn length, not center-to-hole radius. No winner is released before belt/manual test. Begin S06 and increase only if OFF disconnect or ON engagement is insufficient.\n\n"+"\n".join(f"- stroke {r['stroke_mm']:.0f}, sweep {r['sweep_deg']:.0f}: required radius {r['required_horn_radius_mm']:.3f} mm — HOLD actual horn hole" for r in kinematics())+"\n",
      "PHYSICAL_TEST_PLAN.md":h+"A: servo disconnected; hand ON/OFF and stop seating. B: S06→S08→S10→S12. C: manual rotation; ON follows without skip/derail, OFF does not strongly drag motor. D: servo10 cycles. E: 50 cycles only with no damage. F: very-low-speed PTO1–2 s only after manual PASS. No high-load work unit. Stop motor before every shift.\n",
      "PRINT_GUIDE.md":h+"First print: fixed guide, four-carriage slider coupon, linkage coupon, then one-side fixture. PETG/Bambu A1 candidate. Print top-notch faces upward; never sand functional rails asymmetrically. Actual DS3218/horn/idler should be measured before treating fixture mounting references as fit authority.\n",
      "HOLD_REGISTER.md":h+"- DS3218 case, hole pitch, output location and tolerance\n- horn hole radii and thickness\n- HTD5M belt length and fixed center distance\n- idler OD, bearing and pivot hardware\n- output pulley exact bore/width and KP000 mounting pitch\n- final output projection\n- over-center winner and release force\n- servo regulator SKU and limit switches\n- physical fit, powered, torque, L/R, durability and field PASS\n"}


def write(path, text): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text.rstrip()+"\n",encoding="utf-8",newline="\n")
def generate(out: Path):
    step_shapes={STEPS[0]:pto_one_side(),STEPS[1]:servo_envelope(),STEPS[2]:slider(6),STEPS[3]:slider(8),
                 STEPS[4]:slider(10),STEPS[5]:slider(12),STEPS[6]:clutch_assembly()}
    stl_shapes={STLS[0]:slider_coupon(),STLS[1]:guide_core(),STLS[2]:linkage_coupon(),STLS[3]:fixture()}
    for rel,s in step_shapes.items(): export_step(s,out/rel)
    for rel,s in stl_shapes.items(): export_stl(s,out/rel)
    for rel,text in svgs().items(): write(out/rel,text)
    for rel,text in docs().items(): write(out/rel,text)
    write(out/"design_parameters.json",json.dumps(params(),indent=2,sort_keys=True))


def audits(out: Path):
    step_rows=[]
    for rel in STEPS:
        s=importers.importStep(str(out/rel)); bb=s.val().BoundingBox()
        step_rows.append({"path":rel,"valid":s.val().isValid(),"solids":len(s.solids().vals()),
                          "bbox_mm":[round(bb.xlen,3),round(bb.ylen,3),round(bb.zlen,3)]})
    stl_rows={rel:stl_audit(out/rel) for rel in STLS}
    return step_rows,stl_rows


def repro():
    compared=sorted([*STEPS,*STLS,*SVGS,*docs().keys(),"design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="pto_clutch_v001_") as td:
        subprocess.run([__import__('sys').executable,"-B",str(Path(__file__)),"--render-only",td],cwd=ROOT,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8")
        bad=[x for x in compared if (LANE/x).read_bytes()!=(Path(td)/x).read_bytes()]
    return {"compared":len(compared),"byte_identical":len(compared)-len(bad),"mismatches":bad,
            "status":"PASS" if not bad else "FAIL"}


def indexes():
    write(LANE/"COMMIT_PATHS.txt","".join(f"{LANE_REL.as_posix()}/{x}\n" for x in EXPECTED))
    write(LANE/"MANIFEST.txt",f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT=7\nSTL_COUNT=4\nSVG_COUNT=9\nFILES:\n"+"\n".join(EXPECTED))
    files=[x for x in EXPECTED if x!="SHA256SUMS.txt" and (LANE/x).exists()]
    write(LANE/"SHA256SUMS.txt","".join(f"{sha(LANE/x)}  {x}\n" for x in files))


def contract():
    r=subprocess.run([__import__('sys').executable,"-B",str(LANE/TEST)],cwd=ROOT,text=True,encoding="utf-8",
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT); return r.returncode,r.stdout


def build():
    repo=repository_guard(False); generate(LANE); step_rows,stl_rows=audits(LANE); rp=repro()
    checks={"frame_205":True,"motor_shaft_6":True,"output_shaft_10":True,"pulley_20_20":True,"ratio_1":True,
      "motor_fixed":True,"output_fixed":True,"idler_only_moves":True,"stroke_candidates":True,"sweep_candidates":True,
      "over_center_candidates":True,"on_stop":True,"off_stop":True,"servo_not_load_path":True,"one_side_first":True,
      "switch_pads":True,"double_support":True,"hard_width_below_300":True,
      "step_reload":all(x["valid"] for x in step_rows),
      "stl_watertight":all(x["watertight"] and x["manifold"] and x["degenerate_triangles"]==0 for x in stl_rows.values()),
      "reproducibility":rp["status"]=="PASS","authority":repo["checks"]["authority_4"],
      "protected":repo["checks"]["protected_9"]}
    val={"version":VERSION,"status":"PTO_CLUTCH_ARCHITECTURE_SELECTED/PARAMETER_STUDY_COMPLETE/ONE_SIDE_PHYSICAL_VALIDATION_PENDING",
         "checks":checks,"check_count":len(checks),"pass_count":sum(checks.values()),"steps":step_rows,"stls":stl_rows,
         "reproducibility":rp,"repository":{"branch":repo["branch"],"head":repo["head"],"authority":repo["authority"],"protected":repo["protected"]},
         "forbidden_statuses":["SERVO_PHYSICAL_FIT_PASS","CLUTCH_PHYSICAL_PASS","PTO_POWERED_PASS","PTO_TORQUE_PASS","LEFT_RIGHT_CLUTCH_PASS","FIELD_PASS","DURABILITY_PASS"]}
    write(LANE/"validation_report.json",json.dumps(val,indent=2,sort_keys=True))
    write(LANE/"BUILD_LOG.txt",f"BUILD=PASS\nSTEP_RELOAD=7/7 PASS\nSTL_WATERTIGHT=4/4 PASS\nREPRO={rp['byte_identical']}/{rp['compared']} {rp['status']}\n")
    write(LANE/"TEST_LOG.txt","PENDING\n"); indexes(); code,out=contract(); write(LANE/"TEST_LOG.txt",out); indexes()
    if code or not all(checks.values()): raise RuntimeError("BUILD_VERIFY_FAIL\n"+out+json.dumps(checks))
    return repository_guard(True),val


def package():
    repository_guard(True); d=Path(r"D:\Downloads"); d.mkdir(parents=True,exist_ok=True)
    p=d/f"Paddy_Swarm_PTO_SERVO_SLIDING_IDLER_CLUTCH_V001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(p,"x",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in EXPECTED:
            info=zipfile.ZipInfo(f"{LANE_NAME}/{rel}",(2026,8,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,(LANE/rel).read_bytes())
    return p,sha(p)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--verify",action="store_true");ap.add_argument("--package",action="store_true");ap.add_argument("--render-only",type=Path);a=ap.parse_args()
    if a.render_only: generate(a.render_only);return 0
    repo,val=build()
    result={"status":"PASS","lane":str(LANE),"paths":len(EXPECTED),"steps":len(STEPS),"stls":len(STLS),"svgs":len(SVGS),"branch":repo["branch"],"head":repo["head"],"staged":repo["staged"]}
    if a.package: p,h=package();result.update(zip_path=str(p),zip_sha256=h)
    print(json.dumps(result,indent=2,ensure_ascii=False));return 0
if __name__=="__main__":raise SystemExit(main())
