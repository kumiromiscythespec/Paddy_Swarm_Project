from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Iterable


DEFAULT_MANIFEST = "software/rover_control/protocol/v0/test_vectors/manifest/test-vector-manifest.json"
DEFAULT_CASE_RULE_TABLE = "software/rover_control/protocol/v0/test_vectors/case_rules/protocol-v0-case-rules.json"
EXPECTED_CASE_RULE_TABLE_SHA256 = "ff7c7369bf1fcf5293e231ba60384c24782f11694f007e08d1569a1b3ec4f11c"
EXPECTED_MARKER_SHA256 = "f6c3314d3355d3ab56736198af5a247487fac2ca9d1395f784a53ea60b50de16"

ROOT_KEYS = (
    "rule_table_version", "protocol_version", "source_documents", "vector_count",
    "source_scenario_count", "vector_id_order", "aggregate_expectations", "rules",
)
SOURCE_PATHS = {
    "safety_requirements": "software/rover_control/safety/SAFETY_REQUIREMENTS.md",
    "state_machine": "software/rover_control/safety/STATE_MACHINE.md",
    "protocol_readme": "software/rover_control/protocol/README.md",
    "protocol_v0_readme": "software/rover_control/protocol/v0/README.md",
    "validation_order": "software/rover_control/protocol/v0/VALIDATION_ORDER.md",
    "case_catalog": "software/rover_control/protocol/v0/test_vectors/CASE_CATALOG.md",
    "field_model": "software/rover_control/protocol/v0/test_vectors/FIELD_MODEL.md",
    "vector_schema": "software/rover_control/protocol/v0/test_vectors/schema/test-vector.schema.json",
    "manifest": DEFAULT_MANIFEST,
}
SOURCE_KEYS = tuple(SOURCE_PATHS)
SOURCE_ENTRY_KEYS = ("path", "sha256")
AGGREGATE_KEYS = (
    "split_profile_ids", "temporal_ids", "cache_replay_ids", "no_message_action_ids",
    "defensive_zero_ids", "accepted_sequence_update_true_ids", "real_motor_output_true_count",
)
RULE_KEYS = (
    "vector_id", "source_scenario", "profile", "initial_state", "trigger_kind",
    "logical_message_type", "command_type", "candidate_intent", "parseable",
    "terminal_step_number", "terminal_step_name", "formal_disposition",
    "defensive_action", "message_handling", "result_source", "rejection_reason",
    "state_event", "accepted_command_sequence_updated", "control_liveness_updated",
    "immediate_drive_output", "immediate_pto_output", "immediate_armed",
    "immediate_operation_id", "final_state", "communication_loss_latch",
    "fault_latch", "emergency_stop_latch", "temporal_required", "post_time_state",
    "relations",
)
RELATION_KEYS = (
    "sequence", "freshness", "boot_id", "session_id", "controller_ownership",
    "active_operation", "cached_identity", "watchdog", "first_failure",
)
EXPECTED_IDS = tuple(
    ["PV0-VAL-001A", "PV0-VAL-001B"]
    + [f"PV0-VAL-{number:03d}" for number in range(2, 14)]
    + ["PV0-VAL-014L", "PV0-VAL-014R"]
    + [f"PV0-VAL-{number:03d}" for number in range(15, 37)]
)
EXPECTED_AGGREGATE = {
    "split_profile_ids": ["PV0-VAL-001B", "PV0-VAL-018"],
    "temporal_ids": ["PV0-VAL-004", "PV0-VAL-023", "PV0-VAL-024", "PV0-VAL-030", "PV0-VAL-031"],
    "cache_replay_ids": ["PV0-VAL-009", "PV0-VAL-019", "PV0-VAL-026"],
    "no_message_action_ids": ["PV0-VAL-023", "PV0-VAL-024", "PV0-VAL-030", "PV0-VAL-031"],
    "defensive_zero_ids": ["PV0-VAL-020", "PV0-VAL-021", "PV0-VAL-022", "PV0-VAL-027", "PV0-VAL-028", "PV0-VAL-029"],
    "accepted_sequence_update_true_ids": [
        "PV0-VAL-001A", "PV0-VAL-001B", "PV0-VAL-002", "PV0-VAL-017",
        "PV0-VAL-018", "PV0-VAL-025", "PV0-VAL-032", "PV0-VAL-034",
    ],
    "real_motor_output_true_count": 0,
}
RELATION_ENUMS = {
    "sequence": {"NEW", "EXACT_DUPLICATE", "COLLISION", "STALE", "NOT_APPLICABLE"},
    "freshness": {"WITHIN_TTL", "EXPIRED", "NOT_APPLICABLE"},
    "boot_id": {"MATCH", "MISMATCH", "UNAVAILABLE", "NOT_APPLICABLE"},
    "session_id": {"MATCH", "MISMATCH", "UNAVAILABLE", "NOT_APPLICABLE"},
    "controller_ownership": {"OWNER", "NON_OWNER", "UNAVAILABLE", "NOT_APPLICABLE"},
    "active_operation": {"MATCH_CURRENT", "OLD_OR_INVALID", "PRESENT", "ABSENT", "NOT_APPLICABLE"},
    "cached_identity": {"MATCH", "SEQUENCE_MATCH_MESSAGE_ID_DIFFERS", "ABSENT", "NOT_APPLICABLE"},
    "watchdog": {"ADVANCE_COVERS_REMAINING", "NOT_APPLICABLE"},
    "first_failure": {"NONE", "CAPABILITY_BEFORE_STATE", "SESSION_BEFORE_OPERATION_AND_STATE"},
}
STRING_ENUMS = {
    "profile": {"one_side_test", "drive_pto_split_fixture"},
    "initial_state": {"BOOT_SAFE", "DISARMED", "ARMED_NEUTRAL", "DRIVE_READY", "DRIVE_ACTIVE", "PTO_READY", "PTO_ACTIVE", "COMM_LOSS_LATCHED", "FAULT_LATCHED", "EMERGENCY_STOP_LATCHED"},
    "trigger_kind": {"MESSAGE", "TIME_ADVANCE"},
    "logical_message_type": {"", "COMMAND", "CONTROL_UPDATE", "SESSION_END"},
    "formal_disposition": {"FORMAL_ACCEPT", "FORMAL_REJECT", "NONE"},
    "defensive_action": {"NONE", "DEFENSIVE_ZERO"},
    "message_handling": {"PROCESS", "CACHE_REPLAY", "NO_MESSAGE_ACTION", "NOT_APPLICABLE"},
    "result_source": {"NEW_RESULT", "CACHED_RESULT", "NONE"},
    "immediate_drive_output": {"zero", "forward", "same"},
    "immediate_pto_output": {"zero", "active", "same"},
    "immediate_operation_id": {"none", "new", "same", "invalid"},
    "final_state": {"BOOT_SAFE", "DISARMED", "ARMED_NEUTRAL", "DRIVE_READY", "DRIVE_ACTIVE", "PTO_READY", "PTO_ACTIVE", "COMM_LOSS_LATCHED", "FAULT_LATCHED", "EMERGENCY_STOP_LATCHED"},
}
BIDI_OR_ZERO_WIDTH = frozenset({
    0x061C, 0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x202A, 0x202B,
    0x202C, 0x202D, 0x202E, 0x2060, 0x2066, 0x2067, 0x2068, 0x2069,
    0xFEFF,
})


def load_phase1_module() -> ModuleType:
    path = Path(__file__).with_name("phase1.py")
    spec = importlib.util.spec_from_file_location("paddy_protocol_v0_phase1", path)
    if spec is None or spec.loader is None:
        raise ImportError("Phase 1 module specification is unavailable")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


PHASE1 = load_phase1_module()
Diagnostic = PHASE1.Diagnostic
Phase1Report = PHASE1.Phase1Report
VectorPhase1Result = PHASE1.VectorPhase1Result
strict_json_decode = PHASE1.strict_json_decode
sha256_file = PHASE1.sha256_file
is_path_contained = PHASE1.is_path_contained
path_is_symlink = PHASE1.path_is_symlink
json_pointer = PHASE1.json_pointer


STAGE_ORDER = {
    "M0": 0, "M1": 1, "M2": 2,
    **{f"L0-{number:02d}": 2 + number for number in range(1, 15)},
    "L1": 17, "S0": 18, "L2": 19, "A0": 20, "R0": 21, "INTERNAL": 22,
}


@dataclass
class Phase2VectorResult:
    vector_id: str
    repository_relative_path: str
    layer0_result: str
    schema_result: str
    semantic_result: str = "NOT_RUN"

    def report_dict(self) -> dict[str, Any]:
        return {
            "vector_id": self.vector_id,
            "repository_relative_path": self.repository_relative_path,
            "layer0_result": self.layer0_result,
            "schema_result": self.schema_result,
            "semantic_result": self.semantic_result,
        }


@dataclass
class FullReport:
    phase1_result: str
    toolchain: dict[str, Any]
    manifest: dict[str, Any]
    schema: dict[str, Any]
    case_rule_table: dict[str, Any]
    vectors: list[Phase2VectorResult]
    diagnostics: list[Any]
    coverage_result: str
    exit_code: int

    def report_dict(self) -> dict[str, Any]:
        layer0_pass = sum(item.layer0_result == "PASS" for item in self.vectors)
        layer0_fail = sum(item.layer0_result == "FAIL" for item in self.vectors)
        schema_pass = sum(item.schema_result == "PASS" for item in self.vectors)
        schema_fail = sum(item.schema_result == "FAIL" for item in self.vectors)
        semantic_pass = sum(item.semantic_result == "PASS" for item in self.vectors)
        semantic_fail = sum(item.semantic_result == "FAIL" for item in self.vectors)
        semantic_not_run = sum(item.semantic_result == "NOT_RUN" for item in self.vectors)
        ordered = sorted(self.diagnostics, key=diagnostic_sort_key)
        return {
            "report_version": 1,
            "protocol_version": "v0",
            "phase": "manifest-layer0-schema-semantic-coverage",
            "phase1_result": self.phase1_result,
            "full_validator_result": "PASS" if self.exit_code == 0 else "FAIL",
            "toolchain": self.toolchain,
            "manifest": self.manifest,
            "schema": self.schema,
            "case_rule_table": self.case_rule_table,
            "vectors": [item.report_dict() for item in self.vectors],
            "summary": {
                "vector_count": len(self.vectors),
                "layer0_pass_count": layer0_pass,
                "layer0_fail_count": layer0_fail,
                "schema_pass_count": schema_pass,
                "schema_fail_count": schema_fail,
                "semantic_pass_count": semantic_pass,
                "semantic_fail_count": semantic_fail,
                "semantic_not_run_count": semantic_not_run,
                "coverage_result": self.coverage_result,
                "diagnostic_count": len(ordered),
            },
            "diagnostics": [asdict(item) for item in ordered],
            "exit_code": self.exit_code,
        }


def diagnostic_sort_key(item: Any) -> tuple[Any, ...]:
    return (
        STAGE_ORDER.get(item.stage, 999), item.vector_id,
        item.repository_relative_path, item.json_pointer, item.family,
        item.code, item.message,
    )


def _safe_relative_path(value: str) -> bool:
    pure = PurePosixPath(value)
    return (
        bool(value) and not pure.is_absolute() and "\\" not in value and ":" not in value
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def _s0(code: str, relative_path: str, message: str, pointer: str = "") -> Any:
    return Diagnostic("SEMANTIC", code, "S0", relative_path, json_pointer=pointer, message=message)


def _l2(code: str, vector: VectorPhase1Result, message: str, pointer: str = "") -> Any:
    return Diagnostic(
        "SEMANTIC", code, "L2", vector.repository_relative_path,
        vector.vector_id, pointer, message,
    )


def _a0(code: str, message: str) -> Any:
    return Diagnostic("COVERAGE", code, "A0", message=message)


def _forbidden_raw_character(text: str) -> bool:
    return any(
        ord(char) == 0 or ord(char) in BIDI_OR_ZERO_WIDTH
        or unicodedata.category(char) in {"Cc", "Cf", "Cs"} and char != "\n"
        for char in text
    )


def _maximum_depth(value: Any) -> int:
    maximum = 0
    stack = [(value, 1 if isinstance(value, (dict, list)) else 0)]
    while stack:
        item, depth = stack.pop()
        maximum = max(maximum, depth)
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values() if isinstance(child, (dict, list)))
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item if isinstance(child, (dict, list)))
    return maximum


def validate_rule_table_raw(
    repository_root: Path,
    relative_path: str = DEFAULT_CASE_RULE_TABLE,
    expected_sha256: str = EXPECTED_CASE_RULE_TABLE_SHA256,
) -> tuple[dict[str, Any] | None, dict[str, Any], list[Any]]:
    report = {"result": "FAIL", "repository_relative_path": relative_path}
    if not _safe_relative_path(relative_path):
        return None, report, [_s0("SEMANTIC_RULE_TABLE_PATH_OUTSIDE_REPOSITORY", relative_path, "case rule table path escapes repository")]
    path = repository_root / Path(relative_path)
    if not is_path_contained(repository_root, path):
        return None, report, [_s0("SEMANTIC_RULE_TABLE_PATH_OUTSIDE_REPOSITORY", relative_path, "case rule table path escapes repository")]
    if not path.exists():
        return None, report, [_s0("SEMANTIC_RULE_TABLE_NOT_FOUND", relative_path, "case rule table not found")]
    if not path.is_file():
        return None, report, [_s0("SEMANTIC_RULE_TABLE_NOT_REGULAR", relative_path, "case rule table is not a regular file")]
    if path_is_symlink(path):
        return None, report, [_s0("SEMANTIC_RULE_TABLE_SYMLINK_FORBIDDEN", relative_path, "case rule table symlink is forbidden")]
    digest = sha256_file(path)
    report["sha256"] = digest
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or digest != expected_sha256:
        return None, report, [_s0("SEMANTIC_RULE_TABLE_HASH_MISMATCH", relative_path, "case rule table SHA256 mismatch")]
    raw = path.read_bytes()
    if not raw or len(raw) > 65536:
        return None, report, [_s0("SEMANTIC_RULE_TABLE_FORMAT_ERROR", relative_path, "case rule table raw size is invalid")]
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        return None, report, [_s0("SEMANTIC_RULE_TABLE_FORMAT_ERROR", relative_path, "BOM or CR is forbidden")]
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        return None, report, [_s0("SEMANTIC_RULE_TABLE_FORMAT_ERROR", relative_path, "case rule table must end in exactly one LF")]
    lines = raw[:-1].split(b"\n")
    if len(lines) > 4096 or any(len(line) > 4096 for line in lines):
        return None, report, [_s0("SEMANTIC_RULE_TABLE_FORMAT_ERROR", relative_path, "case rule table line limit exceeded")]
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None, report, [_s0("SEMANTIC_RULE_TABLE_FORMAT_ERROR", relative_path, "case rule table is not valid UTF-8")]
    if _forbidden_raw_character(text):
        return None, report, [_s0("SEMANTIC_RULE_TABLE_FORMAT_ERROR", relative_path, "case rule table contains a forbidden character")]
    try:
        value = strict_json_decode(raw)
    except PHASE1.DuplicateKeyError as error:
        return None, report, [_s0("SEMANTIC_RULE_TABLE_DUPLICATE_KEY", relative_path, f"duplicate case rule table key: {error}")]
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as error:
        return None, report, [_s0("SEMANTIC_RULE_TABLE_PARSE_ERROR", relative_path, f"Strict JSON parse failed: {type(error).__name__}")]
    if not isinstance(value, dict):
        return None, report, [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, "case rule table root must be an object")]
    if _maximum_depth(value) > 8:
        return None, report, [_s0("SEMANTIC_RULE_TABLE_FORMAT_ERROR", relative_path, "case rule table nesting depth exceeds 8")]
    report["size_bytes"] = len(raw)
    return value, report, []


def validate_rule_table_model(relative_path: str, table: dict[str, Any]) -> list[Any]:
    if tuple(table) != ROOT_KEYS:
        code = "SEMANTIC_RULE_TABLE_ORDER_MISMATCH" if set(table) == set(ROOT_KEYS) else "SEMANTIC_RULE_TABLE_MODEL_MISMATCH"
        return [_s0(code, relative_path, "case rule table root property model mismatch")]
    if table["rule_table_version"] != 1 or table["protocol_version"] != "v0" or table["vector_count"] != 38 or table["source_scenario_count"] != 36:
        return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, "case rule table fixed identity mismatch")]
    sources = table["source_documents"]
    if not isinstance(sources, dict) or tuple(sources) != SOURCE_KEYS:
        code = "SEMANTIC_RULE_TABLE_ORDER_MISMATCH" if isinstance(sources, dict) and set(sources) == set(SOURCE_KEYS) else "SEMANTIC_RULE_TABLE_MODEL_MISMATCH"
        return [_s0(code, relative_path, "source_documents property model mismatch", "/source_documents")]
    for key, expected_path in SOURCE_PATHS.items():
        source = sources.get(key)
        if not isinstance(source, dict) or tuple(source) != SOURCE_ENTRY_KEYS:
            return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, "source document entry model mismatch", f"/source_documents/{key}")]
        if source["path"] != expected_path or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, "source document identity mismatch", f"/source_documents/{key}")]
    ids = table["vector_id_order"]
    if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
        return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, "vector_id_order model mismatch", "/vector_id_order")]
    if len(ids) != len(set(ids)):
        return [_s0("SEMANTIC_RULE_TABLE_DUPLICATE_ID", relative_path, "duplicate vector ID in vector_id_order", "/vector_id_order")]
    if tuple(ids) != EXPECTED_IDS:
        return [_s0("SEMANTIC_RULE_TABLE_ORDER_MISMATCH", relative_path, "vector_id_order mismatch", "/vector_id_order")]
    aggregate = table["aggregate_expectations"]
    if not isinstance(aggregate, dict) or tuple(aggregate) != AGGREGATE_KEYS:
        code = "SEMANTIC_RULE_TABLE_ORDER_MISMATCH" if isinstance(aggregate, dict) and set(aggregate) == set(AGGREGATE_KEYS) else "SEMANTIC_RULE_TABLE_MODEL_MISMATCH"
        return [_s0(code, relative_path, "aggregate expectation model mismatch", "/aggregate_expectations")]
    if aggregate != EXPECTED_AGGREGATE:
        return [_s0("SEMANTIC_RULE_TABLE_COVERAGE_MISMATCH", relative_path, "aggregate expectation values mismatch", "/aggregate_expectations")]
    rules = table["rules"]
    if not isinstance(rules, list) or len(rules) != 38 or any(not isinstance(rule, dict) for rule in rules):
        return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, "rules array model mismatch", "/rules")]
    rule_ids: list[str] = []
    scenario_values: list[int] = []
    boolean_keys = {
        "parseable", "accepted_command_sequence_updated", "control_liveness_updated",
        "immediate_armed", "communication_loss_latch", "fault_latch",
        "emergency_stop_latch", "temporal_required",
    }
    integer_keys = {"source_scenario", "terminal_step_number"}
    for index, rule in enumerate(rules):
        if tuple(rule) != RULE_KEYS:
            code = "SEMANTIC_RULE_TABLE_ORDER_MISMATCH" if set(rule) == set(RULE_KEYS) else "SEMANTIC_RULE_TABLE_MODEL_MISMATCH"
            return [_s0(code, relative_path, "rule property model mismatch", f"/rules/{index}")]
        for key in RULE_KEYS[:-1]:
            value = rule[key]
            if key in boolean_keys and type(value) is not bool:
                return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, f"{key} must be boolean", f"/rules/{index}/{key}")]
            if key in integer_keys and (type(value) is not int or value < 0):
                return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, f"{key} must be a non-negative integer", f"/rules/{index}/{key}")]
            if key not in boolean_keys | integer_keys and not isinstance(value, str):
                return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, f"{key} must be a string", f"/rules/{index}/{key}")]
            if key in STRING_ENUMS and value not in STRING_ENUMS[key]:
                return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, f"{key} enum mismatch", f"/rules/{index}/{key}")]
        vector_id = rule["vector_id"]
        if not re.fullmatch(r"PV0-VAL-[0-9]{3}[A-Z]?", vector_id):
            return [_s0("SEMANTIC_RULE_TABLE_MODEL_MISMATCH", relative_path, "rule vector ID format mismatch", f"/rules/{index}/vector_id")]
        rule_ids.append(vector_id)
        scenario_values.append(rule["source_scenario"])
        relations = rule["relations"]
        if not isinstance(relations, dict) or tuple(relations) != RELATION_KEYS:
            return [_s0("SEMANTIC_RULE_TABLE_RELATION_MODEL_MISMATCH", relative_path, "relation property model mismatch", f"/rules/{index}/relations")]
        for key, allowed in RELATION_ENUMS.items():
            if relations.get(key) not in allowed:
                return [_s0("SEMANTIC_RULE_TABLE_RELATION_MODEL_MISMATCH", relative_path, "relation enum mismatch", f"/rules/{index}/relations/{key}")]
    if len(rule_ids) != len(set(rule_ids)):
        return [_s0("SEMANTIC_RULE_TABLE_DUPLICATE_ID", relative_path, "duplicate rule vector ID", "/rules")]
    if tuple(rule_ids) != EXPECTED_IDS:
        return [_s0("SEMANTIC_RULE_TABLE_ORDER_MISMATCH", relative_path, "rule order mismatch", "/rules")]
    scenario_counts = {value: scenario_values.count(value) for value in set(scenario_values)}
    if set(scenario_counts) != set(range(1, 37)) or scenario_counts.get(1) != 2 or scenario_counts.get(14) != 2 or any(count != 1 for key, count in scenario_counts.items() if key not in {1, 14}):
        return [_s0("SEMANTIC_RULE_TABLE_COVERAGE_MISMATCH", relative_path, "rule source scenario coverage mismatch", "/rules")]
    return []


def validate_rule_table_sources(
    repository_root: Path,
    relative_path: str,
    table: dict[str, Any],
) -> tuple[int, list[Any]]:
    matches = 0
    for key, source in table["source_documents"].items():
        source_path = source["path"]
        path = repository_root / Path(source_path)
        if not _safe_relative_path(source_path) or not is_path_contained(repository_root, path):
            return matches, [_s0("SEMANTIC_RULE_TABLE_SOURCE_HASH_MISMATCH", relative_path, "source document path escapes repository", f"/source_documents/{key}")]
        if not path.is_file() or path_is_symlink(path) or sha256_file(path) != source["sha256"]:
            return matches, [_s0("SEMANTIC_RULE_TABLE_SOURCE_HASH_MISMATCH", relative_path, "source document SHA256 mismatch", f"/source_documents/{key}")]
        matches += 1
    return matches, []


def derive_vector_core_expectation(data: dict[str, Any]) -> dict[str, Any]:
    message = data.get("stimulus", {}).get("message", {})
    validation = data.get("validation_expectation", {})
    immediate = data.get("immediate_expectation", {})
    latches = immediate.get("safety_latches", {})
    post_time = data.get("post_time_expectation", {})
    state_event = validation.get("state_machine_event", "") if validation.get("state_machine_event_generated", False) else ""
    return {
        "vector_id": data.get("identity", {}).get("vector_id", ""),
        "source_scenario": data.get("source", {}).get("source_scenario", 0),
        "profile": data.get("profile_and_capability", {}).get("profile", ""),
        "initial_state": data.get("initial_fixture", {}).get("official_state", ""),
        "trigger_kind": data.get("stimulus", {}).get("trigger_kind", ""),
        "logical_message_type": message.get("logical_message_type", ""),
        "command_type": message.get("command_type", ""),
        "candidate_intent": message.get("candidate_intent", ""),
        "parseable": bool(message.get("parseable", False)),
        "terminal_step_number": validation.get("terminal_step_number", 0),
        "terminal_step_name": validation.get("terminal_step_name", ""),
        "formal_disposition": validation.get("formal_disposition", ""),
        "defensive_action": validation.get("defensive_action", ""),
        "message_handling": validation.get("message_handling", ""),
        "result_source": validation.get("result_source", ""),
        "rejection_reason": validation.get("rejection_reason", ""),
        "state_event": state_event,
        "accepted_command_sequence_updated": bool(validation.get("accepted_command_sequence_updated", False)),
        "control_liveness_updated": bool(validation.get("control_liveness_updated", False)),
        "immediate_drive_output": immediate.get("drive_output", ""),
        "immediate_pto_output": immediate.get("pto_output", ""),
        "immediate_armed": bool(immediate.get("armed", False)),
        "immediate_operation_id": immediate.get("operation_id", ""),
        "final_state": immediate.get("official_state", ""),
        "communication_loss_latch": bool(latches.get("communication_loss", False)),
        "fault_latch": bool(latches.get("fault", False)),
        "emergency_stop_latch": bool(latches.get("emergency_stop", False)),
        "temporal_required": "time_advance" in data or "post_time_expectation" in data,
        "post_time_state": post_time.get("official_state", ""),
        "real_motor_output_enabled": bool(data.get("profile_and_capability", {}).get("real_motor_output_enabled", False)),
    }


def derive_relations(data: dict[str, Any]) -> dict[str, str]:
    initial = data.get("initial_fixture", {})
    message = data.get("stimulus", {}).get("message", {})
    logical_type = message.get("logical_message_type", "")
    sequence = message.get("sequence")
    cached = initial.get("cached_command_result") if initial.get("cached_command_result_present", False) else None
    if sequence is None:
        sequence_relation = "NOT_APPLICABLE"
    elif cached is not None and sequence == cached.get("sequence") and message.get("message_id") == cached.get("message_id"):
        sequence_relation = "EXACT_DUPLICATE"
    elif cached is not None and sequence == cached.get("sequence"):
        sequence_relation = "COLLISION"
    elif sequence < initial.get("last_seen_sequence", sequence) or sequence < initial.get("last_accepted_command_sequence", sequence):
        sequence_relation = "STALE"
    else:
        sequence_relation = "NEW"
    age = message.get("freshness_age_ms")
    ttl = message.get("ttl_ms")
    freshness = "NOT_APPLICABLE" if age is None or ttl is None else "EXPIRED" if age > ttl else "WITHIN_TTL"

    def identity_relation(key: str) -> str:
        if key not in message:
            return "UNAVAILABLE"
        return "MATCH" if message[key] == initial.get(key) else "MISMATCH"

    ownership = message.get("controller_ownership")
    ownership_relation = "UNAVAILABLE" if ownership is None else "OWNER" if ownership else "NON_OWNER"
    active_present = bool(initial.get("active_operation_present", False))
    if logical_type == "CONTROL_UPDATE":
        active_relation = "MATCH_CURRENT" if active_present and message.get("operation_id") == initial.get("active_operation_id") else "OLD_OR_INVALID"
    else:
        active_relation = "PRESENT" if active_present else "ABSENT"
    message_id = message.get("message_id")
    if message_id is None or sequence is None:
        cached_identity = "NOT_APPLICABLE"
    elif cached is None:
        cached_identity = "ABSENT"
    elif message_id == cached.get("message_id") and sequence == cached.get("sequence"):
        cached_identity = "MATCH"
    elif sequence == cached.get("sequence"):
        cached_identity = "SEQUENCE_MATCH_MESSAGE_ID_DIFFERS"
    else:
        cached_identity = "ABSENT"
    advance = data.get("time_advance", {})
    watchdog = (
        "ADVANCE_COVERS_REMAINING"
        if advance and advance.get("advance_ms", -1) >= initial.get("watchdog_remaining_ms", sys.maxsize)
        and advance.get("watchdog_expiry_expected") is True
        else "NOT_APPLICABLE"
    )
    vector_id = data.get("identity", {}).get("vector_id", "")
    first_failure = {
        "PV0-VAL-015": "CAPABILITY_BEFORE_STATE",
        "PV0-VAL-035": "SESSION_BEFORE_OPERATION_AND_STATE",
    }.get(vector_id, "NONE")
    return {
        "sequence": sequence_relation,
        "freshness": freshness,
        "boot_id": identity_relation("rover_boot_id"),
        "session_id": identity_relation("session_id"),
        "controller_ownership": ownership_relation,
        "active_operation": active_relation,
        "cached_identity": cached_identity,
        "watchdog": watchdog,
        "first_failure": first_failure,
    }


def validate_state_invariant(vector: VectorPhase1Result, data: dict[str, Any]) -> list[Any]:
    initial = data.get("initial_fixture", {})
    immediate = data.get("immediate_expectation", {})
    state = immediate.get("official_state", "")
    drive_raw = immediate.get("drive_output", "")
    pto_raw = immediate.get("pto_output", "")
    drive = initial.get("drive_output", "") if drive_raw == "same" else drive_raw
    pto = initial.get("pto_output", "") if pto_raw == "same" else pto_raw
    armed = immediate.get("armed")
    latches = immediate.get("safety_latches", {})
    communication = latches.get("communication_loss")
    fault = latches.get("fault")
    emergency = latches.get("emergency_stop")
    diagnostics: list[Any] = []

    safe_states = {"BOOT_SAFE", "DISARMED", "ARMED_NEUTRAL", "DRIVE_READY", "PTO_READY"}
    expected_armed = {"BOOT_SAFE": False, "DISARMED": False, "ARMED_NEUTRAL": True, "DRIVE_READY": True, "PTO_READY": True}
    if state in safe_states:
        if drive != "zero" or pto != "zero":
            diagnostics.append(_l2("SEMANTIC_OUTPUT_MISMATCH", vector, "safe state output invariant failed", "/immediate_expectation"))
        if armed is not expected_armed[state]:
            diagnostics.append(_l2("SEMANTIC_ARMED_MISMATCH", vector, "safe state armed invariant failed", "/immediate_expectation/armed"))
        if any(value is not False for value in (communication, fault, emergency)):
            diagnostics.append(_l2("SEMANTIC_LATCH_MISMATCH", vector, "safe state latch invariant failed", "/immediate_expectation/safety_latches"))
    elif state == "DRIVE_ACTIVE":
        if drive not in {"forward", "same"} or pto != "zero" or armed is not True or any(value is not False for value in (communication, fault, emergency)):
            diagnostics.append(_l2("SEMANTIC_STATE_MISMATCH", vector, "DRIVE_ACTIVE invariant failed", "/immediate_expectation"))
    elif state == "PTO_ACTIVE":
        if drive != "zero" or pto not in {"active", "same"} or armed is not True or any(value is not False for value in (communication, fault, emergency)):
            diagnostics.append(_l2("SEMANTIC_STATE_MISMATCH", vector, "PTO_ACTIVE invariant failed", "/immediate_expectation"))
    elif state == "COMM_LOSS_LATCHED":
        if drive != "zero" or pto != "zero" or armed is not False or communication is not True:
            diagnostics.append(_l2("SEMANTIC_STATE_MISMATCH", vector, "COMM_LOSS_LATCHED invariant failed", "/immediate_expectation"))
    elif state == "FAULT_LATCHED":
        if drive != "zero" or pto != "zero" or armed is not False or fault is not True:
            diagnostics.append(_l2("SEMANTIC_STATE_MISMATCH", vector, "FAULT_LATCHED invariant failed", "/immediate_expectation"))
    elif state == "EMERGENCY_STOP_LATCHED":
        if drive != "zero" or pto != "zero" or armed is not False or emergency is not True:
            diagnostics.append(_l2("SEMANTIC_STATE_MISMATCH", vector, "EMERGENCY_STOP_LATCHED invariant failed", "/immediate_expectation"))
    if drive not in {"zero", "same"} and pto not in {"zero", "same"}:
        diagnostics.append(_l2("SEMANTIC_OUTPUT_MISMATCH", vector, "drive and PTO cannot be active together", "/immediate_expectation"))
    message = data.get("stimulus", {}).get("message", {})
    validation = data.get("validation_expectation", {})
    if message.get("command_type") == "EMERGENCY_STOP" and validation.get("formal_disposition") == "FORMAL_REJECT" and emergency is True:
        diagnostics.append(_l2("SEMANTIC_LATCH_MISMATCH", vector, "invalid emergency stop cannot establish its latch", "/immediate_expectation/safety_latches/emergency_stop"))
    if message.get("command_type") == "emergency_stop_reset" and validation.get("formal_disposition") == "FORMAL_ACCEPT" and armed is not False:
        diagnostics.append(_l2("SEMANTIC_ARMED_MISMATCH", vector, "successful reset must remain disarmed", "/immediate_expectation/armed"))
    if data.get("profile_and_capability", {}).get("real_motor_output_enabled") is not False:
        diagnostics.append(_l2("SEMANTIC_OUTPUT_MISMATCH", vector, "real motor output is forbidden", "/profile_and_capability/real_motor_output_enabled"))
    if message.get("logical_message_type") == "SESSION_END" and (armed is not False or immediate.get("operation_id") != "invalid"):
        diagnostics.append(_l2("SEMANTIC_OPERATION_MISMATCH", vector, "SESSION_END cannot restore ARM or operation", "/immediate_expectation"))
    return diagnostics


def validate_vector_semantics(
    repository_root: Path,
    vector: VectorPhase1Result,
    manifest_row: dict[str, Any],
    rule: dict[str, Any],
) -> tuple[dict[str, Any], list[Any]]:
    assert vector.data is not None
    data = vector.data
    actual = derive_vector_core_expectation(data)
    relations = derive_relations(data)
    diagnostics: list[Any] = []
    path = repository_root / Path(vector.repository_relative_path)
    if (
        manifest_row.get("vector_id") != vector.vector_id
        or manifest_row.get("path") != vector.repository_relative_path
        or manifest_row.get("size_bytes") != path.stat().st_size
        or manifest_row.get("sha256") != sha256_file(path)
    ):
        diagnostics.append(_l2("SEMANTIC_MANIFEST_IDENTITY_MISMATCH", vector, "manifest identity or integrity mismatch"))
    if Path(vector.repository_relative_path).stem != actual["vector_id"]:
        diagnostics.append(_l2("SEMANTIC_FILENAME_ID_MISMATCH", vector, "vector filename and identity mismatch", "/identity/vector_id"))
    if rule.get("vector_id") != vector.vector_id:
        diagnostics.append(_l2("SEMANTIC_CASE_RULE_MISMATCH", vector, "case rule vector ID mismatch", "/identity/vector_id"))

    comparisons = (
        ("SEMANTIC_SOURCE_MISMATCH", ("source_scenario",), "/source/source_scenario"),
        ("SEMANTIC_PROFILE_MISMATCH", ("profile",), "/profile_and_capability/profile"),
        ("SEMANTIC_STATE_MISMATCH", ("initial_state",), "/initial_fixture/official_state"),
        ("SEMANTIC_TRIGGER_MISMATCH", ("trigger_kind", "logical_message_type", "command_type", "candidate_intent", "parseable"), "/stimulus"),
        ("SEMANTIC_TERMINAL_STEP_MISMATCH", ("terminal_step_number", "terminal_step_name"), "/validation_expectation"),
        ("SEMANTIC_DISPOSITION_MISMATCH", ("formal_disposition",), "/validation_expectation/formal_disposition"),
        ("SEMANTIC_DEFENSIVE_ACTION_MISMATCH", ("defensive_action",), "/validation_expectation/defensive_action"),
        ("SEMANTIC_MESSAGE_HANDLING_MISMATCH", ("message_handling",), "/validation_expectation/message_handling"),
        ("SEMANTIC_RESULT_SOURCE_MISMATCH", ("result_source",), "/validation_expectation/result_source"),
        ("SEMANTIC_REJECTION_REASON_MISMATCH", ("rejection_reason",), "/validation_expectation/rejection_reason"),
        ("SEMANTIC_STATE_EVENT_MISMATCH", ("state_event",), "/validation_expectation/state_machine_event"),
        ("SEMANTIC_SEQUENCE_POLICY_MISMATCH", ("accepted_command_sequence_updated",), "/validation_expectation/accepted_command_sequence_updated"),
        ("SEMANTIC_LIVENESS_MISMATCH", ("control_liveness_updated",), "/validation_expectation/control_liveness_updated"),
        ("SEMANTIC_OUTPUT_MISMATCH", ("immediate_drive_output", "immediate_pto_output"), "/immediate_expectation"),
        ("SEMANTIC_ARMED_MISMATCH", ("immediate_armed",), "/immediate_expectation/armed"),
        ("SEMANTIC_OPERATION_MISMATCH", ("immediate_operation_id",), "/immediate_expectation/operation_id"),
        ("SEMANTIC_STATE_MISMATCH", ("final_state",), "/immediate_expectation/official_state"),
        ("SEMANTIC_LATCH_MISMATCH", ("communication_loss_latch", "fault_latch", "emergency_stop_latch"), "/immediate_expectation/safety_latches"),
        ("SEMANTIC_TEMPORAL_MISMATCH", ("temporal_required", "post_time_state"), "/post_time_expectation"),
    )
    for code, keys, pointer in comparisons:
        if any(actual[key] != rule.get(key) for key in keys):
            diagnostics.append(_l2(code, vector, f"case rule comparison mismatch: {','.join(keys)}", pointer))
    if relations != rule.get("relations"):
        diagnostics.append(_l2("SEMANTIC_RELATION_MISMATCH", vector, "derived relation mismatch", "/relations"))
    diagnostics.extend(validate_state_invariant(vector, data))
    actual["relations"] = relations
    actual["filename_match"] = Path(vector.repository_relative_path).stem == actual["vector_id"]
    return actual, diagnostics


def validate_aggregate_coverage(actuals: list[dict[str, Any]]) -> tuple[str, list[Any]]:
    diagnostics: list[Any] = []
    ids = [item["vector_id"] for item in actuals]
    if len(actuals) != 38:
        diagnostics.append(_a0("COVERAGE_VECTOR_COUNT_MISMATCH", "vector count mismatch"))
    if len(ids) != len(set(ids)) or set(ids) != set(EXPECTED_IDS) or any(not item.get("filename_match", False) for item in actuals):
        diagnostics.append(_a0("COVERAGE_VECTOR_ID_MISMATCH", "vector ID, uniqueness, or filename coverage mismatch"))
    scenarios = [item["source_scenario"] for item in actuals]
    scenario_counts = {value: scenarios.count(value) for value in set(scenarios)}
    if set(scenario_counts) != set(range(1, 37)) or scenario_counts.get(1) != 2 or scenario_counts.get(14) != 2 or any(count != 1 for key, count in scenario_counts.items() if key not in {1, 14}):
        diagnostics.append(_a0("COVERAGE_SCENARIO_MISMATCH", "source scenario coverage mismatch"))

    def selected(key: str, value: Any) -> list[str]:
        return [item["vector_id"] for item in actuals if item[key] == value]

    checks = (
        ("COVERAGE_PROFILE_SET_MISMATCH", selected("profile", "drive_pto_split_fixture"), EXPECTED_AGGREGATE["split_profile_ids"]),
        ("COVERAGE_TEMPORAL_SET_MISMATCH", selected("temporal_required", True), EXPECTED_AGGREGATE["temporal_ids"]),
        ("COVERAGE_CACHE_REPLAY_SET_MISMATCH", selected("message_handling", "CACHE_REPLAY"), EXPECTED_AGGREGATE["cache_replay_ids"]),
        ("COVERAGE_NO_MESSAGE_ACTION_SET_MISMATCH", selected("message_handling", "NO_MESSAGE_ACTION"), EXPECTED_AGGREGATE["no_message_action_ids"]),
        ("COVERAGE_DEFENSIVE_ZERO_SET_MISMATCH", selected("defensive_action", "DEFENSIVE_ZERO"), EXPECTED_AGGREGATE["defensive_zero_ids"]),
        ("COVERAGE_ACCEPTED_SEQUENCE_SET_MISMATCH", selected("accepted_command_sequence_updated", True), EXPECTED_AGGREGATE["accepted_sequence_update_true_ids"]),
    )
    for code, actual, expected in checks:
        if actual != expected:
            diagnostics.append(_a0(code, f"aggregate ID set mismatch: {code}"))
    if sum(item["real_motor_output_enabled"] for item in actuals) != 0:
        diagnostics.append(_a0("COVERAGE_REAL_MOTOR_OUTPUT_VIOLATION", "real motor output true count must be zero"))
    return ("FAIL" if diagnostics else "PASS"), diagnostics


def build_full_report(
    phase1: Phase1Report,
    case_rule_table: dict[str, Any],
    vectors: list[Phase2VectorResult],
    diagnostics: Iterable[Any],
    coverage_result: str,
    exit_code: int,
) -> FullReport:
    return FullReport(
        phase1.phase1_result, phase1.toolchain, phase1.manifest, phase1.schema,
        case_rule_table, vectors, sorted(diagnostics, key=diagnostic_sort_key),
        coverage_result, exit_code,
    )


def _run_phase2(
    repository_root: Path,
    manifest_path: str,
    case_rule_table_path: str,
    marker: Path | None,
    marker_sha256: str | None,
    case_rule_table_sha256: str,
) -> FullReport:
    root = repository_root.resolve(strict=True)
    phase1 = PHASE1._run_phase1(root, manifest_path, marker, marker_sha256)
    vectors = [
        Phase2VectorResult(item.vector_id, item.repository_relative_path, item.layer0_result, item.schema_result)
        for item in phase1.vectors
    ]
    if phase1.exit_code in {2, 7}:
        case_report = {"result": "NOT_RUN", "repository_relative_path": case_rule_table_path}
        return build_full_report(phase1, case_report, vectors, phase1.diagnostics, "NOT_RUN", phase1.exit_code)
    table, case_report, diagnostics = validate_rule_table_raw(root, case_rule_table_path, case_rule_table_sha256)
    if table is not None:
        diagnostics.extend(validate_rule_table_model(case_rule_table_path, table))
    source_matches = 0
    if table is not None and not diagnostics:
        source_matches, source_diagnostics = validate_rule_table_sources(root, case_rule_table_path, table)
        diagnostics.extend(source_diagnostics)
    if diagnostics or table is None:
        case_report.update({"result": "FAIL", "source_hash_match_count": source_matches})
        return build_full_report(phase1, case_report, vectors, [*phase1.diagnostics, *diagnostics], "NOT_RUN", phase1.exit_code if phase1.exit_code in {3, 4} else 5)
    case_report.update({"result": "PASS", "rule_count": len(table["rules"]), "source_hash_match_count": source_matches})
    manifest = strict_json_decode((root / Path(manifest_path)).read_bytes())
    manifest_rows = {row["vector_id"]: row for row in manifest["vectors"]}
    rules = {rule["vector_id"]: rule for rule in table["rules"]}
    actuals: list[dict[str, Any]] = []
    semantic_diagnostics: list[Any] = []
    for phase1_vector, phase2_vector in zip(phase1.vectors, vectors):
        if phase1_vector.schema_result != "PASS" or phase1_vector.data is None:
            continue
        actual, found = validate_vector_semantics(root, phase1_vector, manifest_rows[phase1_vector.vector_id], rules[phase1_vector.vector_id])
        actuals.append(actual)
        semantic_diagnostics.extend(found)
        phase2_vector.semantic_result = "FAIL" if found else "PASS"
    if any(item.semantic_result == "NOT_RUN" for item in vectors):
        coverage_result, coverage_diagnostics = "NOT_RUN", []
    else:
        coverage_result, coverage_diagnostics = validate_aggregate_coverage(actuals)
    all_diagnostics = [*phase1.diagnostics, *semantic_diagnostics, *coverage_diagnostics]
    if phase1.exit_code == 3:
        exit_code = 3
    elif phase1.exit_code == 4:
        exit_code = 4
    elif semantic_diagnostics:
        exit_code = 5
    elif coverage_diagnostics:
        exit_code = 6
    else:
        exit_code = 0
    return build_full_report(phase1, case_report, vectors, all_diagnostics, coverage_result, exit_code)


def run_phase2(
    repository_root: Path,
    manifest_path: str = DEFAULT_MANIFEST,
    case_rule_table_path: str = DEFAULT_CASE_RULE_TABLE,
    marker: Path | None = None,
    marker_sha256: str | None = None,
    case_rule_table_sha256: str = EXPECTED_CASE_RULE_TABLE_SHA256,
) -> FullReport:
    try:
        return _run_phase2(
            repository_root, manifest_path, case_rule_table_path,
            marker, marker_sha256, case_rule_table_sha256,
        )
    except Exception as error:
        diagnostic = Diagnostic(
            "INTERNAL", "INTERNAL_UNEXPECTED_ERROR", "INTERNAL",
            message=f"unexpected internal error: {type(error).__name__}",
        )
        return FullReport(
            "FAIL",
            {"result": "NOT_AVAILABLE", "pip_check": "PREVALIDATED_EXTERNAL_GATE", "toolchain_marker_result": "NOT_AVAILABLE"},
            {"result": "NOT_AVAILABLE", "repository_relative_path": manifest_path},
            {"result": "NOT_AVAILABLE", "repository_relative_path": ""},
            {"result": "NOT_AVAILABLE", "repository_relative_path": case_rule_table_path},
            [], [diagnostic], "NOT_RUN", 7,
        )


def render_json_report(report: FullReport) -> str:
    return json.dumps(report.report_dict(), ensure_ascii=False, indent=2) + "\n"


def render_text_report(report: FullReport) -> str:
    data = report.report_dict()
    summary = data["summary"]
    fields = (
        ("phase1_result", data["phase1_result"]),
        ("full_validator_result", data["full_validator_result"]),
        ("manifest_result", data["manifest"].get("result", "NOT_AVAILABLE")),
        ("schema_artifact_result", data["schema"].get("result", "NOT_AVAILABLE")),
        ("case_rule_table_result", data["case_rule_table"].get("result", "NOT_AVAILABLE")),
        ("vector_count", summary["vector_count"]),
        ("layer0_pass_count", summary["layer0_pass_count"]),
        ("layer0_fail_count", summary["layer0_fail_count"]),
        ("schema_pass_count", summary["schema_pass_count"]),
        ("schema_fail_count", summary["schema_fail_count"]),
        ("semantic_pass_count", summary["semantic_pass_count"]),
        ("semantic_fail_count", summary["semantic_fail_count"]),
        ("semantic_not_run_count", summary["semantic_not_run_count"]),
        ("coverage_result", summary["coverage_result"]),
        ("diagnostic_count", summary["diagnostic_count"]),
        ("exit_code", data["exit_code"]),
    )
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def _output_path_is_valid(repository_root: Path, output: Path) -> bool:
    return not is_path_contained(repository_root, output)


def _with_report_write_error(report: FullReport) -> FullReport:
    diagnostic = Diagnostic("INTERNAL", "INTERNAL_REPORT_WRITE_ERROR", "R0", message="report output rejected: ValueError")
    return FullReport(
        report.phase1_result, report.toolchain, report.manifest, report.schema,
        report.case_rule_table, report.vectors, [*report.diagnostics, diagnostic],
        report.coverage_result, 7,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Protocol v0 offline validator Phase 2")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--manifest-path", default=DEFAULT_MANIFEST)
    parser.add_argument("--case-rule-table", default=DEFAULT_CASE_RULE_TABLE)
    parser.add_argument("--toolchain-marker", type=Path)
    parser.add_argument("--toolchain-marker-sha256")
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--text-report", type=Path)
    args = parser.parse_args(argv)
    report = run_phase2(
        args.repository_root, args.manifest_path, args.case_rule_table,
        args.toolchain_marker, args.toolchain_marker_sha256,
    )
    outputs = [path for path in (args.json_report, args.text_report) if path is not None]
    try:
        root = args.repository_root.resolve(strict=True)
        if any(not _output_path_is_valid(root, path) for path in outputs):
            raise ValueError("report path inside repository is forbidden")
        if args.json_report is not None:
            args.json_report.parent.mkdir(parents=True, exist_ok=True)
            args.json_report.write_text(render_json_report(report), encoding="utf-8", newline="\n")
        if args.text_report is not None:
            args.text_report.parent.mkdir(parents=True, exist_ok=True)
            args.text_report.write_text(render_text_report(report), encoding="utf-8", newline="\n")
    except (OSError, ValueError):
        report = _with_report_write_error(report)
    sys.stdout.write(render_text_report(report))
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
