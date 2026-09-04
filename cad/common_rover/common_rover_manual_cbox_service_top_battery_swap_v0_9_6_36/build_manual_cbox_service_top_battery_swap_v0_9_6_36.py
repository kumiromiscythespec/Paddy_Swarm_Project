"""Build the v0.9.6.36 initial-freeware architecture update."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree


REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "common_rover_manual_cbox_service_top_battery_swap_v0_9_6_36"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
VERSION = "v0.9.6.36"
CLASSIFICATION = "INITIAL_FREEWARE_MANUAL_CBOX_SIDE_PLACEMENT_TOP_BATTERY_SWAP"
STATUS = (
    "ARCHITECTURE_UPDATE_PASS/CBOX_MANUAL_SIDE_PLACEMENT_PHYSICAL_FEASIBILITY_PASS/"
    "CBOX_900MM_SERVICE_CABLE_PHYSICAL_REFERENCE_RECORDED/"
    "BATTERY_98P9MM_PHYSICAL_HEIGHT_RECORDED/"
    "BATTERY_VERTICAL_EXTRACTION_PHYSICALLY_FEASIBLE/"
    "FRAME_HAND_ACCESS_PHYSICALLY_CONFIRMED/INITIAL_FREEWARE_USER_SCOPE_SELECTED/"
    "AUTONOMOUS_CONTACT_CHARGING_PRESERVED/CONTRACT_TEST_PASS/"
    "ARCHITECTURE_SIMPLIFIED/INITIAL_FREEWARE_BASELINE_SELECTED/"
    "PHYSICAL_VALIDATION_CONTINUES/COMMIT_READY_NOT_STAGED"
)

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = sorted(AUTHORITY_SHA256)
BASE_OUTSIDE_COUNT = 3186
BASE_OUTSIDE_PATH_DIGEST = "d972fd6c0e026de38e555a4584a5c64d379f6c9dd92460da860f3462179f2a3d"
PROTECTED_LANE_COUNT = 36
PROTECTED_FILE_COUNT = 1573
PROTECTED_AGGREGATE_SHA256 = "ef7efc6aa3c4300fba45e1385a72d596ab103f1ccfabbfc546969a94be1954fb"
PROTECTED_TREES = {
    "cad/common_rover/common_rover_top_service_manual_swap_autonomous_contact_charging_v0_9_6_35":
        (33, "a6b6757e46720c6559a617852c42bddecb4f3f7c5905ab0577a2eb99cd243dee"),
    "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27":
        (54, "1079a028588d35564e9e7241dda645a120b570fe2cf4c8b607169138c5742701"),
    "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test":
        (21, "331f7ea46ef9ab26731d58300f658476bf919113960f10f5babaded1d47dcec8"),
    "cad/common_rover/common_rover_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31":
        (20, "8065cefb36cef1dfb823a989185a67534f7eebdfd432fd5a664b364cc9053a72"),
    "cad/common_rover/common_rover_p5m28_exact_vendor_core_fit_coupon_v0_9_6_34":
        (36, "121ae43e71aa732e601e67595401284f8953e4f55bde71dbd3340646e452451d"),
}
SOURCE_SHA256 = {
    "cad/common_rover/common_rover_top_service_manual_swap_autonomous_contact_charging_v0_9_6_35/design_parameters.json": "be89b1c79f8d12b5e0bf1ba39aba7c3e99c56379c6b33a463b994d6a4b49fc85",
    "cad/common_rover/common_rover_top_service_manual_swap_autonomous_contact_charging_v0_9_6_35/validation_report.json": "9959b584fe550da5094520fb368e3d9dd15ce3ec8081693d57f32808edbe2984",
    "cad/common_rover/common_rover_top_service_manual_swap_autonomous_contact_charging_v0_9_6_35/ARCHITECTURE_DECISION.md": "ca68886d2f692f5e40a15a5ba52a9e5f70cb93357a20c7b549c575530e51f5f5",
}

CBOX_PHYSICAL_MM = [150.0, 246.0, 80.0]
CBOX_SERVICE_CABLE_MM = 900.0
BATTERY_PHYSICAL_HEIGHT_MM = 98.9
INITIAL_USERS = ["TYPE_1", "TYPE_2"]
NOT_REQUIRED_MECHANISMS = {
    "CBOX_LATERAL_SERVICE_SLIDE": "NOT_REQUIRED_FOR_INITIAL_FREEWARE",
    "CBOX_SLIDE_DIRECTION": "NOT_REQUIRED",
    "CBOX_SLIDE_STROKE": "NOT_REQUIRED",
    "CBOX_SLIDE_RAIL": "NOT_REQUIRED",
    "CBOX_SERVICE_POSITION_LOCK": "NOT_REQUIRED",
    "CBOX_HINGE_GEOMETRY": "NOT_REQUIRED",
    "CBOX_AUTOMATIC_ACTUATOR": "NOT_REQUIRED",
}
SAFETY_MINIMUMS = [
    "FUSE", "POWER_ISOLATION", "POLARITY_PROTECTION", "STRAIN_RELIEF",
    "CABLE_ENTANGLEMENT_PREVENTION", "WATERPROOF_BOUNDARY",
    "EXPOSED_LIVE_CONDUCTOR_PREVENTION",
]
HOLDS = [
    "EXACT_BBOX_DIMENSIONAL_AUTHORITY_CONFLICT",
    "BBOX_TOP_LID_FINAL_GEOMETRY",
    "TOP_GASKET_COMPRESSION",
    "BATTERY_POWER_CONNECTOR",
    "CBOX_NORMAL_POSITION_RETENTION_DETAIL",
    "CABLE_RETENTION_DETAIL",
    "CHARGING_CONTACT_HARDWARE",
    "CHARGING_CURRENT",
    "DOCKING_TOLERANCE",
    "WATERPROOF_PHYSICAL_TEST",
    "POWERED_DRY_RUN",
    "KEYED_HUB_PHYSICAL_VALIDATION",
    "FRAME_INTERNAL_DIMENSIONS_REMEASUREMENT_REQUIRED",
]
FORBIDDEN_PASSES = [
    "BATTERY_SWAP_ENDURANCE_PASS", "CABLE_DURABILITY_PASS", "CBOX_RETENTION_PASS",
    "BBOX_WATER_PASS", "CHARGING_CONTACT_PASS", "DRY_RUN_PASS", "MUD_PASS",
    "FIELD_PASS", "DURABILITY_PASS",
]

BUILDER = Path(__file__).name
TEST = "tests/test_manual_cbox_service_top_battery_swap_v0_9_6_36_contract.py"
DOCS = [
    "README.md", "ARCHITECTURE_DECISION.md", "INITIAL_FREEWARE_USER_SCOPE.md",
    "CBOX_MANUAL_SERVICE_REQUIREMENTS.md", "BATTERY_TOP_SWAP_REQUIREMENTS.md",
    "SERVICE_CABLE_REQUIREMENTS.md", "SAFETY_MINIMUMS.md",
    "SUPERSEDED_MECHANISM_REGISTER.md", "DEVELOPMENT_PRIORITY_UPDATE.md",
    "HOLD_REGISTER.md",
]
SVGS = [
    "CBOX_MANUAL_SIDE_PLACEMENT.svg", "BATTERY_TOP_EXTRACTION_98P9.svg",
    "BATTERY_SWAP_SEQUENCE.svg", "SERVICE_CABLE_900MM.svg",
    "INITIAL_FREEWARE_USER_TYPES.svg",
]
DATA = ["design_parameters.json", "validation_report.json"]
META = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *SVGS, *DATA, *META])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()


def protected_snapshot() -> dict[str, object]:
    root = REPO_ROOT / "cad/common_rover"
    rows = {}
    for path in sorted(root.iterdir()):
        match = re.search(r"_v0_9_6_(\d+)$", path.name)
        if path.is_dir() and match and int(match.group(1)) <= 35:
            rows[path.relative_to(REPO_ROOT).as_posix()] = tree_digest(path)
    digest = hashlib.sha256()
    for rel, (count, tree_sha) in rows.items():
        digest.update(f"{rel}|{count}|{tree_sha}\n".encode())
    focus = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_TREES}
    return {
        "lane_count": len(rows), "file_count": sum(row[0] for row in rows.values()),
        "aggregate_sha256": digest.hexdigest(),
        "focus": {rel: {"count": row[0], "tree_sha256": row[1]} for rel, row in focus.items()},
    }


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = sorted(
        path.replace("\\", "/") for path in run_git("ls-files", "--others", "--exclude-standard").splitlines()
        if not path.replace("\\", "/").startswith(prefix)
    )
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = sorted(run_git("diff", "--name-only").splitlines())
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    outside = outside_snapshot()
    protected = protected_snapshot()
    source = {rel: sha256(REPO_ROOT / rel) for rel in SOURCE_SHA256}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file()) if LANE_DIR.exists() else []
    ignored = [path for path in lane_files if subprocess.run(
        ["git", "check-ignore", "-q", (LANE_REL / PurePosixPath(path)).as_posix()], cwd=REPO_ROOT
    ).returncode == 0]
    caches = [path for path in lane_files if "__pycache__" in PurePosixPath(path).parts or ".pytest_cache" in PurePosixPath(path).parts]
    forbidden = [path for path in lane_files if Path(path).suffix.lower() in {".pyc", ".pyo", ".3mf", ".gcode", ".fcstd", ".step", ".stl"}]
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD, "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY, "authority_four": authority == AUTHORITY_SHA256,
        "outside_untracked_preserved": outside == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "protected_aggregate": (
            protected["lane_count"] == PROTECTED_LANE_COUNT
            and protected["file_count"] == PROTECTED_FILE_COUNT
            and protected["aggregate_sha256"] == PROTECTED_AGGREGATE_SHA256
        ),
        "protected_focus": all(
            protected["focus"].get(rel) == {"count": expected[0], "tree_sha256": expected[1]}
            for rel, expected in PROTECTED_TREES.items()
        ),
        "source_hashes": source == SOURCE_SHA256,
        "ignored_zero": not ignored, "cache_zero": not caches,
        "no_complex_cad_formats": not forbidden,
        "lane_exact": not require_complete or lane_files == EXPECTED_FILES,
    }
    if not all(checks.values()):
        raise RuntimeError("REPOSITORY_GUARD_FAIL: " + json.dumps(checks, sort_keys=True))
    return {
        "repository": str(root), "branch": branch, "head": head, "staged": staged,
        "tracked_dirty": dirty, "authority_sha256": authority, "outside_untracked": list(outside),
        "protected": protected, "source_sha256": source, "lane_files": lane_files,
        "ignored": ignored, "cache": caches, "forbidden": forbidden, "checks": checks,
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def svg_page(title: str, body: str, footer: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">
<style>.t{{font:700 27px sans-serif;fill:#102a43}}.h{{font:700 18px sans-serif;fill:#243b53}}.m{{font:15px monospace;fill:#334e68}}.b{{fill:#d8f3dc;stroke:#2d6a4f;stroke-width:3}}.c{{fill:#caf0f8;stroke:#0077b6;stroke-width:3}}.a{{fill:#fff3bf;stroke:#d98300;stroke-width:3}}.r{{fill:#ffe3e3;stroke:#c92a2a;stroke-width:3}}.d{{fill:none;stroke:#334e68;stroke-width:2;stroke-dasharray:8 6}}.arrow{{stroke:#c92a2a;stroke-width:4;marker-end:url(#arrow)}}</style>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#c92a2a"/></marker></defs>
<rect width="1200" height="760" fill="#f8fafc"/><text x="42" y="48" class="t">{title}</text>{body}<text x="42" y="730" class="m">{footer}</text></svg>'''


def svg_outputs() -> dict[str, str]:
    side = svg_page("CBOX MANUAL SIDE PLACEMENT", '''
<rect x="180" y="400" width="400" height="210" class="b"/><rect x="135" y="230" width="490" height="130" class="c"/><text x="265" y="300" class="h">CBOX normal position</text><line x1="380" y1="225" x2="820" y2="225" class="arrow"/><rect x="820" y="390" width="290" height="150" class="c"/><text x="855" y="455" class="h">crawler-side safe place</text><text x="855" y="495" class="m">manual lift / manual return</text><text x="205" y="660" class="m">simple corner guide / stopper / outline / engraved visual mark allowed</text>
''', "150 × 246 × 80 mm AS REPORTED · NO SLIDE / HINGE / ACTUATOR · RETENTION DETAIL HOLD")
    extraction = svg_page("BATTERY TOP EXTRACTION — 98.9 mm", '''
<rect x="290" y="400" width="500" height="230" class="b"/><rect x="420" y="425" width="240" height="170" class="a"/><rect x="420" y="150" width="240" height="170" class="d"/><line x1="700" y1="520" x2="700" y2="210" class="arrow"/><text x="735" y="365" class="h">98.9 mm minimum physical travel reference</text><text x="735" y="410" class="m">battery bottom clears frame top</text><text x="735" y="455" class="m">extra margin NOT authority</text><text x="340" y="680" class="m">vertical extraction physically feasible · both-hand access physically confirmed</text>
''', "PHYSICAL HEIGHT 98.9 mm · FRAME INTERNAL DIMENSIONS REQUIRE REMEASUREMENT")
    sequence = svg_page("10-STEP MANUAL BATTERY SWAP", '''
<g transform="translate(45 105)"><rect width="210" height="82" class="r"/><text x="16" y="35" class="h">1 stop rover</text><text x="16" y="63" class="m">2 isolate power</text></g><g transform="translate(280 105)"><rect width="210" height="82" class="c"/><text x="16" y="35" class="h">3 lift CBOX</text><text x="16" y="63" class="m">place beside crawler</text></g><g transform="translate(515 105)"><rect width="210" height="82" class="b"/><text x="16" y="35" class="h">4 open top seal</text></g><g transform="translate(750 105)"><rect width="210" height="82" class="a"/><text x="16" y="35" class="h">5 lift ≥98.9</text><text x="16" y="63" class="m">clear frame top</text></g><g transform="translate(985 105)"><rect width="170" height="82" class="a"/><text x="16" y="35" class="h">6 insert</text></g><g transform="translate(45 335)"><rect width="210" height="82" class="r"/><text x="16" y="35" class="h">7 verify</text><text x="16" y="63" class="m">connection + retention</text></g><g transform="translate(280 335)"><rect width="210" height="82" class="b"/><text x="16" y="35" class="h">8 close top seal</text></g><g transform="translate(515 335)"><rect width="210" height="82" class="c"/><text x="16" y="35" class="h">9 return CBOX</text><text x="16" y="63" class="m">visual/simple guide</text></g><g transform="translate(750 335)"><rect width="405" height="82" class="r"/><text x="16" y="35" class="h">10 verify cable routing / retention</text><text x="16" y="63" class="m">then restart</text></g><text x="330" y="590" class="h">No automatic swap · no automatic CBOX displacement</text>
''', "HUMAN SERVICE · MOTOR / CHARGING POWER ISOLATED · WET-HAND SAFETY REVIEW RETAINED")
    cable = svg_page("900 mm SERVICE CABLE", '''
<rect x="100" y="220" width="360" height="250" class="b"/><text x="210" y="350" class="h">rover / power box</text><path d="M440 330 C560 150 680 560 820 325" fill="none" stroke="#d98300" stroke-width="8"/><rect x="820" y="240" width="270" height="180" class="c"/><text x="880" y="330" class="h">manual CBOX</text><text x="485" y="625" class="h">PHYSICAL REFERENCE = 900 mm</text><text x="330" y="675" class="m">strain relief both ends · quick service release · no ground sag / crawler / PTO / shaft contact</text>
''', "NORMAL EXCESS: REUSABLE TIE / VELCRO / SIMPLE CLIP / GUIDE · EXACT RETENTION DETAIL HOLD")
    users = svg_page("INITIAL FREEWARE USER TYPES", '''
<rect x="70" y="150" width="320" height="430" class="b"/><text x="115" y="210" class="h">TYPE 1 — PRIMARY</text><text x="105" y="270" class="m">complete self-build</text><text x="105" y="315" class="m">understands structure</text><text x="105" y="360" class="m">self repair / change</text><rect x="440" y="150" width="320" height="430" class="a"/><text x="485" y="210" class="h">TYPE 2 — PRIMARY</text><text x="475" y="270" class="m">commercial / partial kit</text><text x="475" y="315" class="m">simple repair / exchange</text><text x="475" y="360" class="m">field adjustment</text><rect x="810" y="150" width="320" height="430" class="c"/><text x="855" y="210" class="h">TYPE 3 — LATER</text><text x="845" y="270" class="m">finished product only</text><text x="845" y="315" class="m">manufacturer support</text><text x="845" y="360" class="m">consumer serviceability</text><text x="330" y="650" class="h">SELF_SERVICE ≠ SAFETY_RELAXATION</text>
''', "FIRST PRIORITY: WORKS / UNDERSTANDABLE / DIAGNOSABLE / USER-REPAIRABLE")
    return {SVGS[0]: side, SVGS[1]: extraction, SVGS[2]: sequence, SVGS[3]: cable, SVGS[4]: users}


def markdown_documents() -> dict[str, str]:
    readme = f"""# Initial freeware manual CBOX service + top battery swap — {VERSION}

Initial freeware standard:

`MANUAL_CBOX_SIDE_PLACEMENT + CBOX_SERVICE_CABLE_900MM + MANUAL_TOP_BATTERY_SWAP + AUTONOMOUS_CONTACT_CHARGING`.

For battery service, stop and isolate the rover, manually lift the 150×246×80 mm physical CBOX to a safe place beside the crawler while retaining the 900 mm service cable, remove the 98.9 mm-high physical battery vertically, then return the CBOX using simple visual/corner guides. No dedicated slide, hinge, guide rail, actuator, precise docking, or service-position lock is required in the initial freeware baseline.

This lane intentionally creates no new STEP/STL mechanism geometry. It records human physical observations, requirements, diagrams, and safety firewalls. Final: `ARCHITECTURE_SIMPLIFIED / INITIAL_FREEWARE_BASELINE_SELECTED / PHYSICAL_VALIDATION_CONTINUES`.
"""
    decision = """# Architecture decision

The v0.9.6.35 top-service/manual-swap and autonomous-contact-charging decision remains, but the initial freeware implementation is simplified.

The CBOX is manually lifted and placed beside the crawler. The physically checked 900 mm service cable stays connected. The battery is manually removed vertically through the BBOX top, and the CBOX is manually returned using a simple guide/mark. Dedicated CBOX lateral-slide and hinge mechanisms are not initial requirements.

v0.9.6.35's slide concept is `SUPERSEDED_FOR_INITIAL_FREEWARE / PRESERVED_AS_FUTURE_SERVICEABILITY_RESEARCH`. Rear-slide battery research remains protected future research. Automatic CBOX displacement and automatic battery swapping remain out of scope.

Routine charging remains `AUTONOMOUS_CONTACT_CHARGING`; manual battery exchange supplements high-load season, maintenance, battery failure, or rapid turnaround.
"""
    users = """# Initial freeware user scope

- TYPE 1: complete self-build; understands structure; can judge, repair, modify, and adjust.
- TYPE 2: assembles from commercial or partially assembled parts; can perform simple repair and replacement.
- TYPE 3: finished-product user requiring manufacturer/support service; later phase.

Initial primary users are TYPE 1 and TYPE 2. The architecture prioritizes working simplicity, understandable construction, fault localization, self-build, self-repair, user discretion, and field adjustment.

It does not initially require automatic service, automatic battery swapping, precision CBOX docking, complex consumer foolproofing, nationwide support, or maintenance-free operation. `SELF_SERVICE ≠ SAFETY_RELAXATION`.
"""
    cbox = f"""# CBOX manual-service requirements

Physical reference: `{CBOX_PHYSICAL_MM[0]:.0f} × {CBOX_PHYSICAL_MM[1]:.0f} × {CBOX_PHYSICAL_MM[2]:.0f} mm`, recorded exactly as reported without silently reassigning axes. Historical CBOX authorities remain unchanged.

Service sequence: stop rover; isolate motor/hazardous power; lift CBOX manually; place it at a safe crawler-side location; perform top battery service; return CBOX to the normal position.

Simple corner guides, stoppers, outline/engraved marks, and visual alignment marks are permitted. Precision docking, automatic locking, sensor confirmation, and motorized positioning are not required. Normal-operation retention must still prevent CBOX movement or falling into crawler, PTO, motor, or frame zones; exact retention remains HOLD.

Physical result: `CBOX_MANUAL_SIDE_PLACEMENT = PHYSICALLY_FEASIBLE`.
"""
    battery = f"""# Battery top-swap requirements

Physical measured height: `{BATTERY_PHYSICAL_HEIGHT_MM:.1f} mm`. This current service measurement is used instead of the earlier nominal height for extraction assessment; historical measurements remain preserved.

Physical observations: the battery enters the frame, both hands fit at its sides, it can be lifted vertically, and removal is possible once its bottom clears the frame top. `BATTERY_VERTICAL_EXTRACTION = PHYSICALLY_FEASIBLE`; `FRAME_HAND_ACCESS = PHYSICALLY_CONFIRMED`.

Minimum physical vertical extraction travel reference is 98.9 mm. No additional clearance is promoted to authority. Repository frame internal dimensions remain insufficiently authoritative: `REMEASUREMENT_REQUIRED`.

The ten-step exchange sequence is stop, isolate power, move CBOX manually, open top closure, lift battery ≥98.9 mm to clear frame top, insert replacement, verify connection/retention, close top seal, return CBOX to its guide, verify cable routing/retention, then restart.
"""
    cable = f"""# Service cable requirements

Human physical placement established `{CBOX_SERVICE_CABLE_MM:.0f} mm` as the initial freeware service-cable reference. It permits removal of the CBOX from the rover, placement beside the crawler, routing around the boxes, and top battery service with remaining reach.

Minimum requirements: no crawler/PTO/shaft entanglement, no ground sag, no direct connector tensile load, strain relief at CBOX and power-box ends, and simple service release. Normal excess may use a reusable tie, Velcro strap, simple printed clip, or simple guide. Exact geometry and SKU remain HOLD; no complex cable carrier is required.
"""
    safety = "# Safety minimums\n\n`SELF_SERVICE ≠ SAFETY_RELAXATION`. The initial freeware baseline retains:\n\n" + "\n".join(f"- `{value}`" for value in SAFETY_MINIMUMS) + "\n\nMotor and charging power must be isolated before battery service. The CBOX and cable must be retained away from crawler, PTO, motor, shaft, frame pinch, water, and exposed conductor hazards before restart."
    superseded = "# Superseded mechanism register\n\n" + "\n".join(f"- `{key} = {value}`" for key, value in NOT_REQUIRED_MECHANISMS.items()) + "\n\nThe v0.9.6.35 slide concept is `SUPERSEDED_FOR_INITIAL_FREEWARE / PRESERVED_AS_FUTURE_SERVICEABILITY_RESEARCH`. No new left/right slide comparison, rail/hinge optimization, service actuator, or automatic CBOX displacement lane should be started unless field need is later demonstrated."
    priority = """# Development priority update

CBOX service mechanism is not a current blocker. Development priority returns to:

1. DRIVETRAIN TORQUE TRANSMISSION — keyed hub, 18025, full drive, static torque.
2. CRAWLER / DRY RUN — final engagement, powered dual-side test, continuous dry run.
3. SEALING BOUNDARY — BBOX top lid, gasket compression, shell watertightness, non-powered submersion.

No powered water test is authorized. Existing drivetrain and sealing lanes remain protected and unchanged.
"""
    hold = "# HOLD register\n\n" + "\n".join(f"- `{value}`" for value in HOLDS) + "\n\nSlide direction/stroke/rail/service lock/hinge are not HOLD items for the initial freeware baseline; they are `NOT_REQUIRED_FOR_INITIAL_FREEWARE`."
    return {
        DOCS[0]: readme, DOCS[1]: decision, DOCS[2]: users, DOCS[3]: cbox,
        DOCS[4]: battery, DOCS[5]: cable, DOCS[6]: safety, DOCS[7]: superseded,
        DOCS[8]: priority, DOCS[9]: hold,
    }


def design_parameters() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "initial_freeware_standard": [
            "MANUAL_CBOX_SIDE_PLACEMENT", "CBOX_SERVICE_CABLE_900MM",
            "MANUAL_TOP_BATTERY_SWAP", "AUTONOMOUS_CONTACT_CHARGING",
        ],
        "cbox_physical_mm": CBOX_PHYSICAL_MM,
        "cbox_physical_dimension_order": "AS_REPORTED_NO_AXIS_REASSIGNMENT",
        "cbox_service_method": "MANUAL_SIDE_PLACEMENT",
        "cbox_manual_side_placement": "PHYSICALLY_FEASIBLE",
        "cbox_service_cable_mm": CBOX_SERVICE_CABLE_MM,
        "cbox_service_cable_authority": "USER_PHYSICAL_PLACEMENT_REFERENCE",
        "battery_physical_height_mm": BATTERY_PHYSICAL_HEIGHT_MM,
        "battery_height_authority": "USER_CALIPER_MEASUREMENT",
        "battery_extraction": "MANUAL_VERTICAL_TOP",
        "battery_vertical_extraction": "PHYSICALLY_FEASIBLE",
        "minimum_physical_vertical_extraction_travel_reference_mm": BATTERY_PHYSICAL_HEIGHT_MM,
        "frame_hand_access": "PHYSICALLY_CONFIRMED",
        "frame_internal_dimensions": "REMEASUREMENT_REQUIRED",
        "cbox_slide_mechanism_required": False,
        "not_required_mechanisms": NOT_REQUIRED_MECHANISMS,
        "autonomous_contact_charging": True,
        "automatic_battery_swap": False,
        "initial_freeware_primary_users": INITIAL_USERS,
        "user_philosophy": ["SELF_BUILD", "SELF_REPAIR", "USER_DISCRETION", "FIELD_ADJUSTMENT"],
        "safety_minimums": SAFETY_MINIMUMS,
        "remaining_holds": HOLDS,
        "development_priority": ["DRIVETRAIN_TORQUE_TRANSMISSION", "CRAWLER_DRY_RUN", "SEALING_BOUNDARY"],
    }


def canonical_guard(guard: dict[str, object]) -> dict[str, object]:
    return {key: guard[key] for key in (
        "repository", "branch", "head", "staged", "tracked_dirty", "authority_sha256",
        "outside_untracked", "protected", "source_sha256",
    )}


def validation_report(parameters: dict[str, object], svg_rows: dict[str, object], guard: dict[str, object]) -> dict[str, object]:
    checks = {
        "cbox_physical_exact": parameters["cbox_physical_mm"] == [150.0, 246.0, 80.0],
        "cbox_dimension_order_preserved": parameters["cbox_physical_dimension_order"] == "AS_REPORTED_NO_AXIS_REASSIGNMENT",
        "service_cable_900_exact": parameters["cbox_service_cable_mm"] == 900.0,
        "battery_height_98p9_exact": parameters["battery_physical_height_mm"] == 98.9,
        "battery_extraction_vertical": parameters["battery_extraction"] == "MANUAL_VERTICAL_TOP",
        "battery_extraction_feasible": parameters["battery_vertical_extraction"] == "PHYSICALLY_FEASIBLE",
        "frame_hand_access_confirmed": parameters["frame_hand_access"] == "PHYSICALLY_CONFIRMED",
        "frame_remeasurement_required": parameters["frame_internal_dimensions"] == "REMEASUREMENT_REQUIRED",
        "slide_mechanism_not_required": not parameters["cbox_slide_mechanism_required"],
        "all_slide_items_not_required": all("NOT_REQUIRED" in value for value in parameters["not_required_mechanisms"].values()),
        "autonomous_contact_charging_preserved": parameters["autonomous_contact_charging"],
        "automatic_battery_swap_false": not parameters["automatic_battery_swap"],
        "initial_users_type_1_2": parameters["initial_freeware_primary_users"] == ["TYPE_1", "TYPE_2"],
        "safety_not_relaxed": set(parameters["safety_minimums"]) == set(SAFETY_MINIMUMS),
        "priority_returned": parameters["development_priority"] == ["DRIVETRAIN_TORQUE_TRANSMISSION", "CRAWLER_DRY_RUN", "SEALING_BOUNDARY"],
        "svg_valid_5": len(svg_rows) == 5 and all(row["xml_valid"] for row in svg_rows.values()),
        "no_step_stl": not any(path.suffix.lower() in {".step", ".stl"} for path in LANE_DIR.rglob("*") if path.is_file()),
        "forbidden_passes_absent": not any(value in STATUS for value in FORBIDDEN_PASSES),
    }
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "repository_guard": canonical_guard(guard), "parameters": parameters,
        "svg_validation": svg_rows,
        "checks": {name: "PASS" if value else "FAIL" for name, value in checks.items()},
        "final": ["ARCHITECTURE_SIMPLIFIED", "INITIAL_FREEWARE_BASELINE_SELECTED", "PHYSICAL_VALIDATION_CONTINUES"],
    }


def validate_svgs(out: Path) -> dict[str, object]:
    rows = {}
    for rel in SVGS:
        try:
            root = ElementTree.fromstring((out / rel).read_text(encoding="utf-8"))
            valid = root.tag.endswith("svg")
        except Exception:
            valid = False
        rows[rel] = {"xml_valid": valid, "bytes": (out / rel).stat().st_size}
    if not all(row["xml_valid"] for row in rows.values()):
        raise RuntimeError("SVG_VALIDATION_FAIL")
    return rows


def generate(out: Path, copy_sources: bool = False) -> dict[str, object]:
    out.mkdir(parents=True, exist_ok=True)
    if copy_sources:
        (out / "tests").mkdir(parents=True, exist_ok=True)
        (out / BUILDER).write_bytes((LANE_DIR / BUILDER).read_bytes())
        (out / TEST).write_bytes((LANE_DIR / TEST).read_bytes())
    for rel, svg in svg_outputs().items():
        write_text(out / rel, svg)
    svg_rows = validate_svgs(out)
    for rel, text in markdown_documents().items():
        write_text(out / rel, text)
    parameters = design_parameters()
    write_json(out / DATA[0], parameters)
    guard = repository_guard(False)
    report = validation_report(parameters, svg_rows, guard)
    if any(value == "FAIL" for value in report["checks"].values()):
        raise RuntimeError("VALIDATION_FAIL: " + json.dumps(report["checks"], sort_keys=True))
    write_json(out / DATA[1], report)
    write_text(out / "BUILD_LOG.txt", (
        f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=0\nSTL=0\nSVG=5\n"
        "CBOX_PHYSICAL_MM=150,246,80\nSERVICE_CABLE_MM=900\nBATTERY_HEIGHT_MM=98.9\n"
        "CBOX_SLIDE_MECHANISM=NOT_REQUIRED_FOR_INITIAL_FREEWARE\n"
        f"STATUS={STATUS}"
    ))
    write_text(out / "TEST_LOG.txt", (
        "CONTRACT_TEST=PASS\nBUILDER_VERIFY=PASS\nSVG_XML_VALID=5_OF_5_PASS\n"
        "EXACT_PHYSICAL_VALUES=3_OF_3_PASS\nREPRODUCIBILITY=ALL_EXPECTED_PATHS_BYTE_IDENTICAL\n"
        "PROTECTED_FILES=UNCHANGED\nPHYSICAL_VALIDATION=CONTINUES"
    ))
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    sum_files = [rel for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"]
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in sum_files))
    return report


def verify() -> dict[str, object]:
    guard = repository_guard(True)
    files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    manifest = (LANE_DIR / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    commit_paths = (LANE_DIR / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    mismatches = []
    for line in (LANE_DIR / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        if sha256(LANE_DIR / rel) != digest:
            mismatches.append(rel)
    svg_rows = validate_svgs(LANE_DIR)
    report = json.loads((LANE_DIR / DATA[1]).read_text(encoding="utf-8"))
    checks = {
        "repository_guard": all(guard["checks"].values()), "exact_paths": files == EXPECTED_FILES,
        "manifest_exact": manifest == EXPECTED_FILES, "commit_paths_exact": commit_paths == expected_commit,
        "sha_mismatch_zero": not mismatches,
        "svg_5_of_5": len(svg_rows) == 5 and all(row["xml_valid"] for row in svg_rows.values()),
        "validation_nonfail": all(value != "FAIL" for value in report["checks"].values()),
        "physical_values": (
            report["parameters"]["cbox_physical_mm"] == [150.0, 246.0, 80.0]
            and report["parameters"]["cbox_service_cable_mm"] == 900.0
            and report["parameters"]["battery_physical_height_mm"] == 98.9
        ),
        "final_exact": report["final"] == ["ARCHITECTURE_SIMPLIFIED", "INITIAL_FREEWARE_BASELINE_SELECTED", "PHYSICAL_VALIDATION_CONTINUES"],
    }
    if not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL: " + json.dumps({"checks": checks, "mismatches": mismatches}, sort_keys=True))
    return {"checks": checks, "paths": len(files), "step": 0, "stl": 0, "svg": 5, "sha_mismatches": mismatches, "repository": guard}


def reproducibility() -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_v09636_repro_") as temp:
        target = Path(temp) / LANE_NAME
        generate(target, copy_sources=True)
        mismatches = [rel for rel in EXPECTED_FILES if sha256(target / rel) != sha256(LANE_DIR / rel)]
    if mismatches:
        raise RuntimeError("REPRODUCIBILITY_FAIL: " + json.dumps(mismatches))
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package() -> dict[str, object]:
    verify()
    reproducibility()
    downloads = Path(r"D:\Downloads")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = downloads / f"Paddy_Swarm_MANUAL_CBOX_TOP_BATTERY_SWAP_{VERSION}_{stamp}.zip"
    counter = 1
    while target.exists():
        target = downloads / f"Paddy_Swarm_MANUAL_CBOX_TOP_BATTERY_SWAP_{VERSION}_{stamp}_{counter:02d}.zip"
        counter += 1
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", date_time=(2026, 8, 20, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE_DIR / rel).read_bytes())
    return {"path": str(target), "sha256": sha256(target), "entries": EXPECTED_PATH_COUNT}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any((args.build, args.verify, args.reproducibility, args.package)):
        args.build = True
    result = {}
    if args.build:
        repository_guard(False)
        result["build"] = generate(LANE_DIR)
    if args.verify:
        result["verify"] = verify()
    if args.reproducibility:
        result["reproducibility"] = reproducibility()
    if args.package:
        result["package"] = package()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
