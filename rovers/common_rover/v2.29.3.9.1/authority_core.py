from __future__ import annotations

import hashlib
import json
from pathlib import Path
from branch_probe import declare, hit
from cross_registry_validator import validate_cross_registry
from post_merge_validator import validate_manifest, validate_pointers_and_holds

declare(
    "scope_file_match", "scope_file_mismatch", "scope_value_match", "scope_value_mismatch",
    "scope_internal_match", "scope_internal_mismatch", "gate_no_blockers", "gate_blockers",
    "gate_ready", "gate_hold",
)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return canonical_hash(load(path))


def canonical_hash(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def nested_values(lane):
    fixed = load(lane / "fixed_body_dimension_authority.json")
    frame = load(lane / "body_frame_authority.json")
    cross = load(lane / "front_crossmember_authority.json")
    width = load(lane / "operational_width_contract.json")
    slots = load(lane / "slot_zone_authority.json")
    zone = {z["zone_id"]: z for z in slots["zones"]}
    return {
        "CBOX": fixed["current_dimensions"]["CBOX"],
        "BBOX": fixed["current_dimensions"]["BBOX"],
        "BATTERY_CASSETTE": fixed["current_dimensions"]["BATTERY_CASSETTE"],
        "CORE_LENGTH_MM": fixed["core_length_mm"],
        "RAIL_CENTERS_X_MM": frame["rail_centerlines_x_mm"],
        "FRONT_CROSSMEMBER_ENVELOPE": cross["envelope"],
        "FRONT_CROSSMEMBER_LENGTH_MM": cross["length_mm"],
        "BARE_FRAME_WIDTH_MM": frame["bare_frame_union"]["width_mm"],
        "REGISTERED_WIDTH_MM": 286.0,
        "HARD_WIDTH_LIMIT_MM": width["hard_limit_mm"],
        "OUTPUT_ZONE_Y_MM": zone["OUTPUT-BRIDGE-L"]["zone_interval"],
        "MOTOR_ZONE_Y_MM": zone["MOTOR-ADAPTER-L"]["zone_interval"],
        "INPUT_ZONE_Y_MM": zone["INPUT-CARTRIDGE-L"]["zone_interval"],
        "SERVO_ZONE_Y_MM": zone["SERVO-BRIDGE-L"]["zone_interval"],
    }


def validate_scope(lane):
    lane = Path(lane)
    contract = load(lane / "correction_scope_contract.json")
    blockers = []
    violations = []
    for name, expected in contract["immutable_file_sha256"].items():
        actual = sha(lane / name)
        if actual != expected:
            hit("scope_file_mismatch")
            violations.append(f"FILE:{name}")
        else:
            hit("scope_file_match")
    actual_values = nested_values(lane)
    for key, expected in contract["immutable_values"].items():
        actual = actual_values.get(key)
        if actual != expected:
            hit("scope_value_mismatch")
            violations.append(f"VALUE:{key}")
        else:
            hit("scope_value_match")
    fastener = load(lane / "fastener_boundary_authority.json")
    if (
        canonical_hash(fastener["adapter_internal_records"]) != contract["internal_fastener_digest"]
        or canonical_hash(fastener["classification_records"]) != contract["classification_digest"]
    ):
        hit("scope_internal_mismatch")
        violations.append("FASTENER_CLASSIFICATION_OR_INTERNAL")
    else:
        hit("scope_internal_match")
    if violations:
        blockers.append("CORRECTION_SCOPE_VIOLATION")
    return {
        "status": "PASS" if not blockers else "FAIL",
        "CORRECTION_SCOPE_VIOLATION_COUNT": len(violations),
        "violations": violations,
        "blockers": blockers,
    }


def main_gate(results):
    blockers = []
    for section in results.values():
        blockers.extend(section.get("blockers", []))
    blocker_count = len(set(blockers))
    if blocker_count:
        hit("gate_blockers")
        hit("gate_hold")
    else:
        hit("gate_no_blockers")
        hit("gate_ready")
    return {
        "MAIN_MERGE_BLOCKER_COUNT": blocker_count,
        "MAIN_MERGE_BLOCKERS": sorted(set(blockers)),
        "MAIN_MERGE_READINESS": "READY" if blocker_count == 0 else "HOLD",
        "GITHUB_DESIGN_AUTHORITY_MAIN_MERGE": "APPROVED" if blocker_count == 0 else "HOLD",
    }


def validate_all(lane=None):
    lane = Path(lane or Path(__file__).resolve().parent).resolve()
    required = [
        "fastener_boundary_authority.json", "slot_zone_authority.json",
        "slot_cross_registry_mapping.json", "tslot_profile_authority.json",
        "current_authority_expectations.json", "known_hold_registry.json",
        "correction_scope_contract.json",
    ]
    missing = [name for name in required if not (lane / name).exists()]
    if missing:
        return {
            "status": "FAIL", "DESIGN_ANALYSIS_PROCESS": "FAIL",
            "blockers": ["REQUIRED_SOURCE_FILE_MISSING"],
            "missing_files": missing,
        }
    fastener = load(lane / "fastener_boundary_authority.json")
    slots = load(lane / "slot_zone_authority.json")
    mapping = load(lane / "slot_cross_registry_mapping.json")
    hosts = load(lane / "tslot_profile_authority.json")
    expectations = load(lane / "current_authority_expectations.json")
    holds = load(lane / "known_hold_registry.json")
    results = {
        "cross_registry": validate_cross_registry(fastener, slots, mapping, hosts, expectations),
        "correction_scope": validate_scope(lane),
        "manifest": validate_manifest(lane),
        "pointers_release": validate_pointers_and_holds(lane, holds),
    }
    gate = main_gate(results)
    return {
        "status": "PASS_WITH_HOLD" if gate["MAIN_MERGE_READINESS"] == "READY" else "FAIL",
        "DESIGN_ANALYSIS_PROCESS": "PASS_WITH_HOLD" if gate["MAIN_MERGE_READINESS"] == "READY" else "FAIL",
        "CURRENT_AUTHORITY_VERSION": "V2.29.3.9.1",
        "results": results,
        **gate,
        "blockers": gate["MAIN_MERGE_BLOCKERS"],
    }
