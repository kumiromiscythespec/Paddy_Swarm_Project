"""Build and verify the 2026-09-01 Common Rover physical authority record.

Documentation only. This module never invokes a CAD kernel and never mutates Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[4]
LANE_REL = PurePosixPath(
    "cad/common_rover/physical_authority/"
    "common_rover_physical_dimensional_authority_2026_09_01_v001"
)
LANE = ROOT / Path(LANE_REL.as_posix())
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
SOURCE_DATE = "2026-09-01"

EXPECTED_DIRTY = [
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
]
AUTHORITY_FILES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md":
        "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md":
        "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md":
        "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md":
        "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PROTECTED = {
    "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority":
        (18, "cd3e28e773890edafc51fe25de3c8f6c3d85e2de3c529a9fea9a1d1497c3793e"),
    "cad/common_rover/frame/front_interface_dual_pto_20t_v002":
        (26, "e4924cf784ceb31a29deb15b71ec153b42789e11696ed33dbb56cb962984fd85"),
    "cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003":
        (29, "c531a9c94ae3229cf9fd4380d4a492ad740ce0bf894861ecc8d185737b4d7df5"),
    "cad/common_rover/drivetrain/misumi_pulley_groove1_full_driven_carrier_v001":
        (28, "ca9e647a0bc3c50fef4b8a059ddc364495f98c8ad00a64913f675dcd692fb21e"),
    "cad/common_rover/common_rover_generic_keyed_industrial_torque_core_comparison_v0_9_6_33":
        (30, "5241750bf94c4866000ec943d21697c9e5a0fbe98b3b7445d9f560750b415f7e"),
    "cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6":
        (66, "069885e4645f5f0433d07f5c316bb0863decbb25afaabc1cb318d603cd42945c"),
}
OUTSIDE_UNTRACKED_START = (
    4073,
    "8467946e2c2bf5e1b3f3616a78041c0dc0302c3fa4dcddf1f4c78daa026348f4",
)

BUILDER = "build_common_rover_physical_dimensional_authority_2026_09_01_v001.py"
TEST = "tests/test_common_rover_physical_dimensional_authority_2026_09_01_v001.py"
EXPECTED = sorted([
    "README.md",
    "COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01.md",
    "physical_dimensions_2026_09_01.json",
    "historical_dimension_precedence_audit.md",
    "misumi_shaft_key_procurement_update_2026_09_01.json",
    "MISUMI_SHAFT_KEY_PROCUREMENT_UPDATE_2026_09_01.md",
    "PROPOSED_BOM_UPDATE.md",
    "PROPOSED_CURRENT_AUTHORITY_UPDATE.md",
    "authority_sources.md",
    "validation_report.md",
    "manifest.json",
    "SHA256SUMS.txt",
    BUILDER,
    TEST,
    "COMMIT_PATHS.txt",
])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(
        item for item in path.rglob("*")
        if item.is_file()
        and "__pycache__" not in item.parts
        and item.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(item.read_bytes()).digest())
    return len(files), digest.hexdigest()


def untracked_outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    rows = sorted(
        row.replace("\\", "/")
        for row in git("ls-files", "--others", "--exclude-standard").splitlines()
        if row and not row.replace("\\", "/").startswith(prefix)
    )
    return len(rows), hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()


def repository_guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    dirty = sorted(git("diff", "--name-only").splitlines())
    authority = {name: sha(ROOT / name) for name in AUTHORITY_FILES}
    protected = {name: tree(ROOT / name) for name in PROTECTED}
    files = sorted(
        item.relative_to(LANE).as_posix()
        for item in LANE.rglob("*")
        if item.is_file()
    ) if LANE.exists() else []
    cache = [
        name for name in files
        if "__pycache__" in PurePosixPath(name).parts
        or name.lower().endswith((".pyc", ".pyo"))
    ]
    ignored = git(
        "ls-files", "--others", "--ignored", "--exclude-standard",
        "--", LANE_REL.as_posix(),
    ).splitlines()
    checks = {
        "repository_root": root == ROOT.resolve(),
        "required_branch": branch == BRANCH,
        "required_head": head == HEAD,
        "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == EXPECTED_DIRTY,
        "outside_untracked_preserved": untracked_outside() == OUTSIDE_UNTRACKED_START,
        "authority_files_preserved": authority == AUTHORITY_FILES,
        "protected_lanes_preserved": protected == PROTECTED,
        "lane_scope": set(files).issubset(EXPECTED),
        "lane_cache_zero": not cache,
        "lane_ignored_zero": not ignored,
        "lane_complete": not complete or files == EXPECTED,
    }
    report = {
        "checks": checks,
        "repository": str(root),
        "branch": branch,
        "head": head,
        "staged_count": len(staged),
        "tracked_dirty": dirty,
        "outside_untracked": {
            "count": untracked_outside()[0],
            "digest": untracked_outside()[1],
        },
        "authority_sha256": authority,
        "protected_lane_tree_hashes": {
            name: {"file_count": value[0], "sha256": value[1]}
            for name, value in protected.items()
        },
        "lane_files": files,
    }
    failed = [name for name, value in checks.items() if not value]
    if failed:
        raise RuntimeError("FAIL_CLOSED repository guard: " + ", ".join(failed))
    return report


def entry(value, unit: str, classification: str, note: str,
          source_type: str = "USER_PHYSICAL_MEASUREMENT",
          source_date: str = SOURCE_DATE) -> dict:
    return {
        "value": value,
        "unit": unit,
        "classification": classification,
        "source_date": source_date,
        "source_type": source_type,
        "note": note,
    }


def physical_data() -> dict:
    return {
        "schema": "COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_V001",
        "version": "2026-09-01_v001",
        "coordinate_basis": {
            "z_zero": entry(
                0.0, "mm", "PHYSICAL_DATUM",
                "CRAWLER_BOTTOM / FLOOR = Z0.",
            ),
            "absolute_upper_rail_axis_y": entry(
                None, "mm", "PHYSICAL_PENDING",
                "Span measurements establish relative geometry only; no absolute Y datum was measured.",
            ),
        },
        "frame_y": {
            "rail_outside_span_range": entry(
                [208.0, 210.0], "mm", "DIRECT_PHYSICAL_RANGE",
                "User-measured left-to-right upper-rail outside span.",
            ),
            "rail_inside_span_range": entry(
                [168.0, 170.0], "mm", "DIRECT_PHYSICAL_RANGE",
                "User-measured left-to-right upper-rail inside span.",
            ),
            "rail_width_each_from_210_170": entry(
                20.0, "mm", "PHYSICAL_DERIVED",
                "(210 - 170) / 2 = 20.",
            ),
            "rail_width_each_from_208_168": entry(
                20.0, "mm", "PHYSICAL_DERIVED",
                "(208 - 168) / 2 = 20.",
            ),
            "rail_center_span_range": entry(
                [188.0, 190.0], "mm", "PHYSICAL_DERIVED_RANGE",
                "(208 + 168) / 2 = 188 and (210 + 170) / 2 = 190.",
            ),
            "rail_center_span_midpoint": entry(
                189.0, "mm", "DERIVED_MIDPOINT",
                "Midpoint of 188..190; not a direct measurement and not authority for Y=±94.5.",
            ),
        },
        "frame_z": {
            "left_upper_rail_top": entry(
                255.0, "mm", "DIRECT_PHYSICAL", "Left upper rail top from Z0.",
            ),
            "right_upper_rail_top": entry(
                254.0, "mm", "DIRECT_PHYSICAL", "Right upper rail top from Z0.",
            ),
            "left_upper_rail_bottom": entry(
                235.0, "mm", "DIRECT_PHYSICAL", "Left upper rail bottom from Z0.",
            ),
            "right_upper_rail_bottom": entry(
                234.0, "mm", "DIRECT_PHYSICAL", "Right upper rail bottom from Z0.",
            ),
            "left_rail_height": entry(
                20.0, "mm", "PHYSICAL_DERIVED", "255 - 235 = 20.",
            ),
            "right_rail_height": entry(
                20.0, "mm", "PHYSICAL_DERIVED", "254 - 234 = 20.",
            ),
            "left_right_vertical_offset": entry(
                1.0, "mm", "PHYSICAL_DERIVED",
                "Observed as-built top and bottom offset, left above right.",
            ),
            "nominal_rail_top_midpoint": entry(
                254.5, "mm", "DERIVED_MIDPOINT",
                "Midpoint only; raw 255/254 values remain authoritative.",
            ),
        },
        "bbox": {
            "lid_highest_z": entry(
                254.0, "mm", "DIRECT_PHYSICAL",
                "Measured highest BBOX lid point from Z0.",
            ),
            "body_lowest_z": entry(
                148.0, "mm", "DIRECT_PHYSICAL",
                "Measured lowest BBOX body point from Z0.",
            ),
            "assembled_envelope_height": entry(
                106.0, "mm", "PHYSICAL_DERIVED", "254 - 148 = 106.",
            ),
            "lid_to_left_rail_top": entry(
                1.0, "mm", "PHYSICAL_DERIVED",
                "Left rail top is 1 mm above BBOX lid.",
            ),
            "lid_to_right_rail_top": entry(
                0.0, "mm", "PHYSICAL_DERIVED",
                "Right rail top and BBOX lid share measured Z254.",
            ),
            "fit_statement": entry(
                "APPROXIMATELY_FLUSH_WITHIN_1MM_AS_BUILT_VARIATION", "state",
                "PHYSICAL_DERIVED",
                "Not a rigid zero-offset mounting constraint.",
            ),
        },
        "crawler": {
            "left_highest_z": entry(
                181.0, "mm", "DIRECT_PHYSICAL",
                "Static as-built crawler highest point from Z0.",
            ),
            "right_highest_z": entry(
                180.0, "mm", "DIRECT_PHYSICAL",
                "Static as-built crawler highest point from Z0.",
            ),
            "left_rail_bottom_to_crawler_top": entry(
                54.0, "mm", "PHYSICAL_DERIVED_STATIC_CLEARANCE",
                "235 - 181 = 54; not powered or dynamic clearance.",
            ),
            "right_rail_bottom_to_crawler_top": entry(
                54.0, "mm", "PHYSICAL_DERIVED_STATIC_CLEARANCE",
                "234 - 180 = 54; not powered or dynamic clearance.",
            ),
        },
        "drive_axis_existing_record": {
            "left_center_z": entry(
                122.0, "mm", "DIRECT_PHYSICAL_REUSED",
                "Referenced from front_interface_dual_pto_20t_v001/V002.",
                "EXISTING_REPOSITORY_PHYSICAL_RECORD",
                "PRE_2026_09_01_RECORD_REUSED",
            ),
            "right_center_z": entry(
                123.0, "mm", "DIRECT_PHYSICAL_REUSED",
                "Referenced from front_interface_dual_pto_20t_v001/V002.",
                "EXISTING_REPOSITORY_PHYSICAL_RECORD",
                "PRE_2026_09_01_RECORD_REUSED",
            ),
            "nominal_midpoint_z": entry(
                122.5, "mm", "DERIVED_MIDPOINT_REUSED",
                "(122 + 123) / 2; current PTO design datum.",
                "EXISTING_REPOSITORY_PHYSICAL_RECORD",
                "PRE_2026_09_01_RECORD_REUSED",
            ),
        },
        "cbox_implication_only": {
            "candidate_floor_lower_bound": entry(
                191.0, "mm", "DESIGN_TARGET_ONLY",
                "181 + 10; not a released floor or Cross Base design.",
            ),
            "cross_saddle": entry(
                "NOT_DESIGNED_IN_THIS_TASK", "state", "HOLD",
                "No CBOX support geometry is created.",
            ),
            "one_piece_bbox_cbox_base": entry(
                "HOLD", "state", "HOLD",
                "Documentation task does not authorize a one-piece base.",
            ),
        },
        "release_limits": {
            "dynamic_crawler_clearance": entry(
                "PENDING", "state", "PHYSICAL_PENDING",
                "Static 54 mm result cannot be promoted to powered clearance.",
            ),
            "full_powered_field_validation": entry(
                "PENDING", "state", "PHYSICAL_PENDING",
                "No powered, water, mud or field validation is performed.",
            ),
            "cad_mutation": entry(
                "NONE", "state", "NO_CAD_MUTATION",
                "No STEP, STL, SVG, DXF or CAD source is generated or modified.",
            ),
        },
    }


def procurement_data() -> dict:
    return {
        "schema": "MISUMI_SHAFT_KEY_PROCUREMENT_UPDATE_2026_09_01",
        "status": entry(
            "PROCUREMENT_UPDATE_PARTIAL", "state", "PARTIAL",
            "Physical shortening is authoritative, but the prior purchased shaft SKU/order length "
            "and the purchased key nominal are not uniquely evidenced in repository records.",
        ),
        "shaft": {
            "quantity": entry(
                2, "pieces", "DIRECT_PHYSICAL", "Two independent shafts were physically updated.",
            ),
            "removed_each": entry(
                12.0, "mm", "DIRECT_PHYSICAL",
                "Each shaft was shortened by 12.0 mm.",
            ),
            "kp000_full_insertion": entry(
                "PASS", "state", "DIRECT_PHYSICAL_RESULT",
                "Both shortened shafts fit completely in KP000.",
            ),
            "axial_spare_approx": entry(
                1.0, "mm", "DIRECT_PHYSICAL_APPROXIMATE",
                "Approximately 1 mm axial spare was observed.",
            ),
            "frame_or_other_interference": entry(
                "NONE_OBSERVED", "state", "DIRECT_PHYSICAL_RESULT",
                "No frame or other interference was observed in the physical fit.",
            ),
            "prior_purchase_product": entry(
                None, "product_code", "PROCUREMENT_EVIDENCE_PENDING",
                "AHFGKR10-145-KA4-A20 appears only as PURCHASE_CANDIDATE / physical NOT_YET.",
                "REPOSITORY_SEARCH",
            ),
            "prior_ordered_length": entry(
                None, "mm", "PROCUREMENT_EVIDENCE_PENDING",
                "145 mm is not promoted because the source explicitly marks it as a purchase candidate.",
                "REPOSITORY_SEARCH",
            ),
            "future_order_rule": entry(
                "ACTUAL_PRIOR_PURCHASED_LENGTH_MINUS_12_PER_SHAFT", "rule",
                "PROCUREMENT_RULE_READY",
                "Apply only after the prior order record or direct remaining length is confirmed.",
            ),
            "future_exact_order_length": entry(
                None, "mm", "PROCUREMENT_HOLD",
                "Do not infer 133 mm from the unconfirmed 145 mm purchase candidate.",
            ),
            "final_shaft_absolute_length": entry(
                None, "mm", "PHYSICAL_PENDING",
                "Direct measurement or authoritative order evidence is still required.",
            ),
            "shaft_protrusion_final": entry(
                None, "mm", "PHYSICAL_PENDING",
                "Approximately 1 mm spare is not a final released protrusion.",
            ),
        },
        "key": {
            "original_physical_length": entry(
                19.7, "mm", "DIRECT_PHYSICAL_REUSED",
                "Existing keeperless drivetrain record.",
                "EXISTING_REPOSITORY_PHYSICAL_RECORD",
                "PRE_2026_09_01_RECORD_REUSED",
            ),
            "removed_length": entry(
                3.0, "mm", "DIRECT_PHYSICAL_REUSED",
                "Non-engaging overhang removed in existing record.",
                "EXISTING_REPOSITORY_PHYSICAL_RECORD",
                "PRE_2026_09_01_RECORD_REUSED",
            ),
            "effective_length": entry(
                16.7, "mm", "PHYSICAL_DERIVED_REUSED",
                "19.7 - 3.0 = 16.7.",
                "EXISTING_REPOSITORY_PHYSICAL_RECORD",
                "PRE_2026_09_01_RECORD_REUSED",
            ),
            "length_match": entry(
                "PASS", "state", "DIRECT_PHYSICAL_RESULT_REUSED",
                "Existing manual forward/reverse physical record retained.",
                "EXISTING_REPOSITORY_PHYSICAL_RECORD",
                "PRE_2026_09_01_RECORD_REUSED",
            ),
            "purchase_nominal_product": entry(
                None, "product_code", "PROCUREMENT_EVIDENCE_PENDING",
                "19.7 mm physical length does not independently prove a nominal 20 mm order.",
                "REPOSITORY_SEARCH",
            ),
        },
        "torque_path": entry(
            "SHAFT_TO_KEY_TO_MISUMI_METAL_PULLEY_TO_EXACT_GROOVE1_C1_"
            "TO_PRINTED_CARRIER_TO_CANDIDATE_C_12T",
            "architecture", "CURRENT_AUTHORITY_UNCHANGED",
            "This documentation update makes no drivetrain geometry change.",
        ),
    }


def contract_checks(p: dict, q: dict) -> dict[str, bool]:
    fy, fz, bbox, crawler = p["frame_y"], p["frame_z"], p["bbox"], p["crawler"]
    shaft, key = q["shaft"], q["key"]
    return {
        "raw_outside_span": fy["rail_outside_span_range"]["value"] == [208.0, 210.0],
        "raw_inside_span": fy["rail_inside_span_range"]["value"] == [168.0, 170.0],
        "rail_width_210_170": fy["rail_width_each_from_210_170"]["value"] == 20.0,
        "rail_width_208_168": fy["rail_width_each_from_208_168"]["value"] == 20.0,
        "center_span_range": fy["rail_center_span_range"]["value"] == [188.0, 190.0],
        "center_midpoint": fy["rail_center_span_midpoint"]["value"] == 189.0,
        "axis_y_pending": p["coordinate_basis"]["absolute_upper_rail_axis_y"]["classification"] == "PHYSICAL_PENDING",
        "raw_left_top": fz["left_upper_rail_top"]["value"] == 255.0,
        "raw_right_top": fz["right_upper_rail_top"]["value"] == 254.0,
        "raw_left_bottom": fz["left_upper_rail_bottom"]["value"] == 235.0,
        "raw_right_bottom": fz["right_upper_rail_bottom"]["value"] == 234.0,
        "left_rail_height": fz["left_rail_height"]["value"] == 20.0,
        "right_rail_height": fz["right_rail_height"]["value"] == 20.0,
        "vertical_offset": fz["left_right_vertical_offset"]["value"] == 1.0,
        "top_midpoint": fz["nominal_rail_top_midpoint"]["value"] == 254.5,
        "bbox_lid_raw": bbox["lid_highest_z"]["value"] == 254.0,
        "bbox_body_raw": bbox["body_lowest_z"]["value"] == 148.0,
        "bbox_height": bbox["assembled_envelope_height"]["value"] == 106.0,
        "bbox_flush_class": bbox["fit_statement"]["value"].startswith("APPROXIMATELY_FLUSH"),
        "crawler_left_raw": crawler["left_highest_z"]["value"] == 181.0,
        "crawler_right_raw": crawler["right_highest_z"]["value"] == 180.0,
        "crawler_left_clearance": crawler["left_rail_bottom_to_crawler_top"]["value"] == 54.0,
        "crawler_right_clearance": crawler["right_rail_bottom_to_crawler_top"]["value"] == 54.0,
        "crawler_clearance_static": all(
            "STATIC_CLEARANCE" in crawler[name]["classification"]
            for name in ("left_rail_bottom_to_crawler_top", "right_rail_bottom_to_crawler_top")
        ),
        "drive_raw_reused": (
            p["drive_axis_existing_record"]["left_center_z"]["value"],
            p["drive_axis_existing_record"]["right_center_z"]["value"],
            p["drive_axis_existing_record"]["nominal_midpoint_z"]["value"],
        ) == (122.0, 123.0, 122.5),
        "cbox_target_only": p["cbox_implication_only"]["candidate_floor_lower_bound"]["classification"] == "DESIGN_TARGET_ONLY",
        "cbox_floor_191": p["cbox_implication_only"]["candidate_floor_lower_bound"]["value"] == 191.0,
        "cbox_not_designed": p["cbox_implication_only"]["cross_saddle"]["value"] == "NOT_DESIGNED_IN_THIS_TASK",
        "shaft_quantity": shaft["quantity"]["value"] == 2,
        "shaft_cut_each": shaft["removed_each"]["value"] == 12.0,
        "shaft_fit": shaft["kp000_full_insertion"]["value"] == "PASS",
        "shaft_spare": shaft["axial_spare_approx"]["value"] == 1.0,
        "shaft_no_interference": shaft["frame_or_other_interference"]["value"] == "NONE_OBSERVED",
        "shaft_order_not_guessed": shaft["future_exact_order_length"]["value"] is None,
        "shaft_candidate_not_promoted": shaft["prior_ordered_length"]["value"] is None,
        "key_original": key["original_physical_length"]["value"] == 19.7,
        "key_removed": key["removed_length"]["value"] == 3.0,
        "key_effective": key["effective_length"]["value"] == 16.7,
        "key_math": round(key["original_physical_length"]["value"] - key["removed_length"]["value"], 10) == key["effective_length"]["value"],
        "key_nominal_not_guessed": key["purchase_nominal_product"]["value"] is None,
        "procurement_partial": q["status"]["value"] == "PROCUREMENT_UPDATE_PARTIAL",
        "torque_path_unchanged": "MISUMI_METAL_PULLEY_TO_EXACT_GROOVE1_C1" in q["torque_path"]["value"],
        "no_cad_mutation": p["release_limits"]["cad_mutation"]["value"] == "NONE",
        "dynamic_hold": p["release_limits"]["dynamic_crawler_clearance"]["value"] == "PENDING",
        "field_hold": p["release_limits"]["full_powered_field_validation"]["value"] == "PENDING",
    }


def measurement_metadata_ok(node) -> bool:
    if isinstance(node, dict):
        if "value" in node:
            return all(key in node for key in (
                "value", "unit", "classification", "source_date", "source_type", "note"
            ))
        return all(measurement_metadata_ok(value) for value in node.values())
    if isinstance(node, list):
        return all(measurement_metadata_ok(value) for value in node)
    return True


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def documents() -> dict[str, bytes]:
    p = physical_data()
    q = procurement_data()
    checks = contract_checks(p, q)
    assert all(checks.values())
    status = (
        "COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01_CAPTURED / "
        "MISUMI_SHAFT_KEY_PHYSICAL_UPDATE_CAPTURED / "
        "PROCUREMENT_UPDATE_PARTIAL / NO_CAD_MUTATION / NO_GIT_MUTATION"
    )
    authority = """# Common Rover physical dimensional authority — 2026-09-01

Status: {status}

## Authority rule

Direct user physical measurements dated 2026-09-01 take precedence for the current
as-built rover. Raw left/right and range values remain authoritative. Midpoints are
explicitly derived and do not become unmeasured absolute axes.

## Current as-built dimensions

| Group | Physical values | Derived result | Authority note |
|---|---:|---:|---|
| Upper rails Y span | outside 208–210; inside 168–170 mm | each rail 20.0 mm; centers 188–190 mm | absolute rail-axis Y remains PHYSICAL_PENDING |
| Upper rails Z | left top/bottom 255/235; right 254/234 mm | 20 mm height each; 1 mm side offset | 254.5 mm is midpoint only |
| BBOX | lid 254; body bottom 148 mm | 106 mm envelope | approximately flush with rail tops within 1 mm |
| Crawler | left 181; right 180 mm | 54 mm static clearance on both sides | not powered/dynamic clearance |
| DRIVE axis record | left 122; right 123 mm | nominal 122.5 mm | reused from existing physical record |

The old BBOX/frame Z257 assumption, rail Y ±100.5/±80.5 models and drive-axis
Z175/Z178 values are preserved in their source lanes but superseded for this
current as-built record.

## CBOX implication

The 150×246×80 CBOX remains an architectural envelope only. A provisional
floor lower bound of Z191 mm equals crawler-high Z181 + 10 mm and is
DESIGN_TARGET_ONLY. CBOX floor, Cross Base/saddle and a one-piece BBOX/CBOX
base remain HOLD and no geometry is created.

## Release boundary

No CAD, STEP, STL, SVG or DXF is generated or changed. Static dimensions do not
authorize powered motion, dynamic crawler clearance, water/mud testing or field use.
""".format(status=status)

    historical = """# Historical dimension precedence audit

Precedence for the current as-built rover:

DIRECT_PHYSICAL_2026_09_01 > older physical/derived mounting assumptions > CAD-only/provisional.

| Value/source | Previous classification | Current disposition | Reason |
|---|---|---|---|
| BBOX lid/frame top Z257 in BBOX v002/v003/v004 | DERIVED_MOUNT_ASSUMPTION / CAD | SUPERSEDED_FOR_CURRENT_AS_BUILT_2026_09_01 | direct BBOX lid highest Z254 and rail tops Z255/254 |
| upper rail centers Y=±100.5 in narrow-frame v0.9.6.6 | CAD_ONLY / derived outboard move | SUPERSEDED_FOR_CURRENT_AS_BUILT_2026_09_01 | direct spans give center separation 188–190 but no absolute Y origin |
| upper rail centers Y=±80.5 in earlier frame lanes | CAD_ONLY / DERIVED_MOUNT_ASSUMPTION | SUPERSEDED_FOR_CURRENT_AS_BUILT_2026_09_01 | same reason; do not promote ±94.5 |
| drive shaft Z178 in v0.9.4.0 | PROVISIONAL | PROVISIONAL_OBSOLETE | direct physical 122/123 record already supersedes it |
| drive shaft Z175 in v0.9.6.6 | CAD_ONLY | CAD_ONLY_NOT_PHYSICAL_AUTHORITY | direct physical nominal 122.5 |
| drive shaft Z122/123, nominal122.5 in Front Interface v001/V002 | CURRENT_PHYSICAL | RETAINED_CURRENT_PHYSICAL | reused without duplication conflict |

Historical source files are not deleted or edited. This lane records precedence only.
"""

    procurement_md = """# MISUMI shaft/key procurement update — 2026-09-01

## Physical result

- Two shafts were each shortened by 12.0 mm.
- Both shortened shafts fit fully in KP000.
- Approximately 1 mm axial spare remained.
- No frame or other interference was observed.
- Key physical record remains 19.7 mm original, 3.0 mm removed, 16.7 mm effective; length match PASS.

## Procurement decision

Status is PROCUREMENT_UPDATE_PARTIAL. Repository search found
AHFGKR10-145-KA4-A20 only as PURCHASE_CANDIDATE with physical=NOT_YET.
That is not an order receipt or purchase authority, so this task does not silently
publish a 133 mm reorder. The allowed rule is:

future shaft order length = confirmed prior purchased length - 12.0 mm per shaft.

Confirm the prior MISUMI order record or directly measure the finished shaft before
issuing an exact SKU/length. Likewise, 19.7 mm physical key length does not prove
a nominal 20 mm purchased key.

Torque path is unchanged:

SHAFT → KEY → MISUMI METAL PULLEY → EXACT GROOVE-1/C1 →
PRINTED CARRIER → CANDIDATE C 12T.
"""

    proposed_bom = """# Proposed BOM update

This is a proposal only; no tracked BOM is modified.

| Item | Qty | Proposed record | State |
|---|---:|---|---|
| MISUMI keyed shaft | 2 | confirmed prior purchased length minus 12.0 mm each | EXACT SKU/LENGTH HOLD |
| Current physical shortened shafts | 2 | full KP000 insertion PASS; approx. 1 mm spare | PHYSICAL FIT GOOD |
| Parallel key | 2 | effective physical length 16.7 mm after 3.0 mm removal | PHYSICAL LENGTH PASS |

Do not order AHFGKR10-133-KA4-A20 from this document: the only 145 mm repository
record is explicitly a purchase candidate, not verified procurement evidence.
"""

    proposed_current = """# Proposed current-authority update

This is proposed text only. Existing tracked authority files remain untouched.

- Current as-built upper-rail outside span: 208–210 mm.
- Current as-built upper-rail inside span: 168–170 mm.
- Derived rail center separation: 188–190 mm; absolute Y axes PHYSICAL_PENDING.
- Rail Z: left top/bottom 255/235 mm; right 254/234 mm.
- BBOX: highest lid Z254, lowest body Z148, total 106 mm.
- Static crawler high Z: left181/right180; rail-bottom clearances54/54 mm.
- Drive shaft center record retained: left122/right123; nominal122.5 mm.
- BBOX/frame Z257 and rail Y ±100.5/±80.5 are superseded for the current as-built rover.
- CBOX floor/Cross Base remain not designed; Z191 is DESIGN_TARGET_ONLY.
- Two MISUMI shafts shortened12.0 mm each fit KP000; exact reorder length remains procurement HOLD.
"""

    sources = """# Authority sources

## Direct source

- User physical measurement task: 2026-09-01, attachment
  C:/Users/yu_ki/.codex/attachments/34965dab-05df-4c7c-9cb1-2702e7314258/pasted-text.txt

## Read-only repository evidence

- cad/common_rover/frame/front_interface_dual_pto_20t_v001:
  physical drive centers122/123 and nominal122.5; Z178 provisional obsolete; Z175 CAD-only.
- cad/common_rover/frame/front_interface_dual_pto_20t_v002:
  current front-interface reuse of drive/PTO Z122.5.
- cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority:
  BBOX lid Z257 classified DERIVED_MOUNT_ASSUMPTION, now superseded for current as-built.
- cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6:
  CAD rail centers ±100.5 from ±80.5 and CAD drive Z175, now superseded.
- cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003:
  key 19.7/3.0/16.7 and current torque path.
- cad/common_rover/drivetrain/misumi_pulley_groove1_full_driven_carrier_v001:
  Groove-1 center/torque authority, read-only.
- cad/common_rover/common_rover_generic_keyed_industrial_torque_core_comparison_v0_9_6_33:
  AHFGKR10-145-KA4-A20 marked PURCHASE_CANDIDATE and physical NOT_YET; not purchase proof.

All protected lanes are hashed before and after generation. No source is modified.
"""

    validation = """# Validation report

Result: PASS

- repository/branch/HEAD guard: PASS
- staged changes: 0
- existing tracked dirty paths: preserved exactly
- existing untracked paths outside this lane: preserved by count and digest
- four authority-file SHA-256 values: unchanged
- six protected lane tree hashes: unchanged
- raw dimensional values: exact
- derived arithmetic without silent rounding: PASS
- measurement metadata fields: complete
- historical precedence classification: PASS
- exact shaft order length not guessed: PASS
- torque path unchanged: PASS
- CAD/STEP/STL/SVG/DXF outputs: 0
- contract checks: {count}/{count} PASS
- expected lane paths: 15
- reproducibility target: 15/15 byte-identical
""".format(count=len(checks))

    readme = """# Common Rover 2026-09-01 physical dimensional authority V001

Documentation-only, untracked authority-capture lane.

Captured:

- current physical rail spans and Z levels;
- BBOX and crawler static Z measurements;
- historical value precedence;
- two-shaft 12.0 mm shortening result;
- key 19.7 → 16.7 mm physical record;
- partial procurement update without guessing an exact order length.

No CAD artifacts are present. Run:

python -B build_common_rover_physical_dimensional_authority_2026_09_01_v001.py --verify

Status:

COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01_CAPTURED /
MISUMI_SHAFT_KEY_PHYSICAL_UPDATE_CAPTURED /
PROCUREMENT_UPDATE_PARTIAL /
NO_CAD_MUTATION /
NO_GIT_MUTATION
"""

    manifest = {
        "schema": "COMMON_ROVER_PHYSICAL_AUTHORITY_MANIFEST_V001",
        "lane": LANE_REL.as_posix(),
        "version": "2026-09-01_v001",
        "classification": "DOCUMENTATION_ONLY",
        "expected_path_count": len(EXPECTED),
        "files": EXPECTED,
        "cad_artifact_count": 0,
        "status": status,
    }
    commit_paths = "".join(f"{LANE_REL.as_posix()}/{name}\n" for name in EXPECTED)
    rendered = {
        "README.md": readme,
        "COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01.md": authority,
        "physical_dimensions_2026_09_01.json": json_text(p),
        "historical_dimension_precedence_audit.md": historical,
        "misumi_shaft_key_procurement_update_2026_09_01.json": json_text(q),
        "MISUMI_SHAFT_KEY_PROCUREMENT_UPDATE_2026_09_01.md": procurement_md,
        "PROPOSED_BOM_UPDATE.md": proposed_bom,
        "PROPOSED_CURRENT_AUTHORITY_UPDATE.md": proposed_current,
        "authority_sources.md": sources,
        "validation_report.md": validation,
        "manifest.json": json_text(manifest),
        "COMMIT_PATHS.txt": commit_paths,
    }
    return {
        name: (value if value.endswith("\n") else value + "\n").encode("utf-8")
        for name, value in rendered.items()
    }


def expected_bytes() -> dict[str, bytes]:
    rendered = documents()
    for fixed in (BUILDER, TEST):
        rendered[fixed] = (LANE / fixed).read_bytes()
    sums = "".join(
        f"{hashlib.sha256(rendered[name]).hexdigest()}  {name}\n"
        for name in sorted(rendered)
    )
    rendered["SHA256SUMS.txt"] = sums.encode("utf-8")
    return rendered


def build() -> dict:
    start = repository_guard(False)
    rendered = expected_bytes()
    for name, payload in rendered.items():
        path = LANE / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    end = repository_guard(True)
    return {"start": start, "end": end}


def verify() -> dict:
    repository = repository_guard(True)
    p = json.loads((LANE / "physical_dimensions_2026_09_01.json").read_text(encoding="utf-8"))
    q = json.loads((LANE / "misumi_shaft_key_procurement_update_2026_09_01.json").read_text(encoding="utf-8"))
    contract = contract_checks(p, q)
    sums = {}
    for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    checksum_ok = (
        set(sums) == set(EXPECTED) - {"SHA256SUMS.txt"}
        and all(sha(LANE / name) == digest for name, digest in sums.items())
    )
    manifest = json.loads((LANE / "manifest.json").read_text(encoding="utf-8"))
    no_cad = not any(
        (LANE / name).suffix.lower() in {".step", ".stp", ".stl", ".svg", ".dxf"}
        for name in EXPECTED
    )
    checks = {
        **contract,
        "physical_metadata": measurement_metadata_ok(p),
        "procurement_metadata": measurement_metadata_ok(q),
        "sha256sums": checksum_ok,
        "manifest_exact": manifest["files"] == EXPECTED and manifest["expected_path_count"] == len(EXPECTED),
        "no_cad_files": no_cad and manifest["cad_artifact_count"] == 0,
        "authority_hashes": repository["authority_sha256"] == AUTHORITY_FILES,
        "protected_hashes": all(
            (
                value["file_count"],
                value["sha256"],
            ) == PROTECTED[name]
            for name, value in repository["protected_lane_tree_hashes"].items()
        ),
    }
    failed = [name for name, value in checks.items() if not value]
    if failed:
        raise RuntimeError("contract FAIL: " + ", ".join(failed))
    return {
        "status": "PASS",
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "checks": checks,
        "repository": repository,
    }


def reproducibility() -> dict:
    reference = expected_bytes()
    with tempfile.TemporaryDirectory(prefix="ps_physical_authority_v001_") as raw:
        target = Path(raw)
        for name, payload in reference.items():
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        mismatches = [
            name for name in EXPECTED
            if (target / name).read_bytes() != (LANE / name).read_bytes()
        ]
    result = {
        "status": "PASS" if not mismatches else "FAIL",
        "file_count": len(EXPECTED),
        "byte_identical_count": len(EXPECTED) - len(mismatches),
        "mismatches": mismatches,
    }
    if mismatches:
        raise RuntimeError("reproducibility FAIL: " + ", ".join(mismatches))
    return result


def create_zip() -> dict:
    repository_guard(True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path("D:/Downloads") / (
        f"Paddy_Swarm_COMMON_ROVER_PHYSICAL_AUTHORITY_20260901_V001_{stamp}.zip"
    )
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in EXPECTED:
            info = zipfile.ZipInfo(
                f"{LANE.name}/{name}",
                (2026, 9, 1, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE / name).read_bytes())
    return {"path": str(path), "sha256": sha(path), "entry_count": len(EXPECTED)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        args.build = args.verify = args.reproducibility = True
    result = {}
    if args.build:
        result["build"] = build()
    if args.verify:
        result["verify"] = verify()
    if args.reproducibility:
        result["reproducibility"] = reproducibility()
    if args.zip:
        result["zip"] = create_zip()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
