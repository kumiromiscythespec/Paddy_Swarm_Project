from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Iterable

from jsonschema import Draft202012Validator


DEFAULT_MANIFEST = "software/rover_control/protocol/v0/test_vectors/manifest/test-vector-manifest.json"
EXPECTED_MARKER_SHA256 = "f6c3314d3355d3ab56736198af5a247487fac2ca9d1395f784a53ea60b50de16"
EXPECTED_SCHEMA_PATH = "software/rover_control/protocol/v0/test_vectors/schema/test-vector.schema.json"
EXPECTED_SCHEMA_SHA256 = "ea021f20390962246aad09a2334dfb898588442333c679cc2911fb9895dbc013"
VECTOR_DIRECTORY = "software/rover_control/protocol/v0/test_vectors/vectors"
ROOT_KEYS = (
    "manifest_version", "protocol_version", "vector_schema", "source_documents",
    "vector_directory", "vector_count", "source_scenario_count", "vectors",
)
ENTRY_KEYS = (
    "vector_id", "path", "sha256", "size_bytes", "source_scenario", "profile",
    "accepted_command_sequence_updated",
)
SOURCE_DOCUMENT_ROWS = (
    ("validation_order", "software/rover_control/protocol/v0/VALIDATION_ORDER.md", "ed600175566a55ad7eea921d2471107ad5d7ee9d86168054ecb7f647e0608e4a"),
    ("case_catalog", "software/rover_control/protocol/v0/test_vectors/CASE_CATALOG.md", "4021e082b9085f0785b5e3967389e1b0ee7535e682d832f6f4696997e369f22d"),
    ("field_model", "software/rover_control/protocol/v0/test_vectors/FIELD_MODEL.md", "792edc2a5885da182616d857f05f97e72465920db9205e3b3317009b9de0601e"),
    ("validation_limits", "software/rover_control/protocol/v0/test_vectors/VALIDATION_LIMITS.md", "bf15de9b7fc0b4f8c654ed327b183febe01c8591af0ef4d2c0a4f0c2ea69639f"),
)
SOURCE_KEYS = tuple(row[0] for row in SOURCE_DOCUMENT_ROWS)
EXPECTED_IDS = tuple(
    ["PV0-VAL-001A", "PV0-VAL-001B"]
    + [f"PV0-VAL-{number:03d}" for number in range(2, 14)]
    + ["PV0-VAL-014L", "PV0-VAL-014R"]
    + [f"PV0-VAL-{number:03d}" for number in range(15, 37)]
)
ACCEPTED_TRUE_IDS = frozenset({
    "PV0-VAL-001A", "PV0-VAL-001B", "PV0-VAL-002", "PV0-VAL-017",
    "PV0-VAL-018", "PV0-VAL-025", "PV0-VAL-032", "PV0-VAL-034",
})
SPLIT_PROFILE_IDS = frozenset({"PV0-VAL-001B", "PV0-VAL-018"})
STAGE_ORDER = MappingProxyType({
    "M0": 0, "M1": 1, "M2": 2,
    **{f"L0-{number:02d}": 2 + number for number in range(1, 15)},
    "L1": 17, "R0": 18, "INTERNAL": 19,
})
LAYER0_CODES = frozenset({
    "FILE_NOT_FOUND", "FILE_NOT_REGULAR", "SYMLINK_FORBIDDEN",
    "PATH_OUTSIDE_VECTOR_DIRECTORY", "INVALID_FILE_EXTENSION", "INVALID_VECTOR_FILENAME",
    "FILE_TOO_LARGE", "TOO_MANY_LINES", "LINE_TOO_LONG", "EMPTY_FILE",
    "WHITESPACE_ONLY_FILE", "INVALID_UTF8", "BOM_FORBIDDEN", "CR_FORBIDDEN",
    "TRAILING_NEWLINE_REQUIRED", "MULTIPLE_TRAILING_NEWLINES",
    "TRAILING_WHITESPACE_FORBIDDEN", "JSON_PARSE_ERROR", "ROOT_OBJECT_REQUIRED",
    "MULTIPLE_ROOT_VALUES", "DUPLICATE_KEY", "NESTING_DEPTH_EXCEEDED",
    "TOTAL_NODE_COUNT_EXCEEDED", "OBJECT_MEMBER_COUNT_EXCEEDED",
    "ARRAY_ELEMENT_COUNT_EXCEEDED", "KEY_LENGTH_EXCEEDED", "STRING_LENGTH_EXCEEDED",
    "FORBIDDEN_STRING_CHARACTER", "FORBIDDEN_NUMBER_FORMAT", "INTEGER_RANGE_EXCEEDED",
    "RESOURCE_LIMIT_EXCEEDED",
})
SCHEMA_CODES = frozenset({
    "SCHEMA_NOT_FOUND", "SCHEMA_HASH_MISMATCH", "SCHEMA_PARSE_ERROR",
    "SCHEMA_META_VALIDATION_FAILED", "SCHEMA_EXTERNAL_REF_FORBIDDEN",
    "SCHEMA_VALIDATION_FAILED",
})
BIDI_OR_ZERO_WIDTH = frozenset({
    0x061C, 0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x202A, 0x202B,
    0x202C, 0x202D, 0x202E, 0x2060, 0x2066, 0x2067, 0x2068, 0x2069,
    0xFEFF,
})


@dataclass(frozen=True)
class Diagnostic:
    family: str
    code: str
    stage: str
    repository_relative_path: str = ""
    vector_id: str = ""
    json_pointer: str = ""
    message: str = ""
    schema_json_pointer: str = ""
    validator_keyword: str = ""

    def sort_key(self) -> tuple[Any, ...]:
        return (
            STAGE_ORDER.get(self.stage, 999), self.vector_id,
            self.repository_relative_path, self.json_pointer, self.family,
            self.code, self.message,
        )


@dataclass(frozen=True)
class FileMeasurement:
    repository_relative_path: str
    size_bytes: int
    sha256: str


@dataclass
class VectorPhase1Result:
    vector_id: str
    repository_relative_path: str
    layer0_result: str = "NOT_RUN"
    schema_result: str = "NOT_RUN"
    data: dict[str, Any] | None = field(default=None, repr=False)

    def report_dict(self) -> dict[str, Any]:
        return {
            "vector_id": self.vector_id,
            "repository_relative_path": self.repository_relative_path,
            "layer0_result": self.layer0_result,
            "schema_result": self.schema_result,
        }


@dataclass
class Phase1Report:
    phase1_result: str
    toolchain: dict[str, Any]
    manifest: dict[str, Any]
    schema: dict[str, Any]
    vectors: list[VectorPhase1Result]
    diagnostics: list[Diagnostic]
    exit_code: int

    def report_dict(self) -> dict[str, Any]:
        layer0_pass = sum(vector.layer0_result == "PASS" for vector in self.vectors)
        layer0_fail = sum(vector.layer0_result == "FAIL" for vector in self.vectors)
        schema_pass = sum(vector.schema_result == "PASS" for vector in self.vectors)
        schema_fail = sum(vector.schema_result == "FAIL" for vector in self.vectors)
        return {
            "report_version": 1,
            "protocol_version": "v0",
            "phase": "manifest-layer0-schema",
            "phase1_result": self.phase1_result,
            "full_validator_result": "NOT_AVAILABLE",
            "toolchain": self.toolchain,
            "manifest": self.manifest,
            "schema": self.schema,
            "vectors": [vector.report_dict() for vector in self.vectors],
            "summary": {
                "vector_count": len(self.vectors),
                "layer0_pass_count": layer0_pass,
                "layer0_fail_count": layer0_fail,
                "schema_pass_count": schema_pass,
                "schema_fail_count": schema_fail,
                "semantic_result": "NOT_RUN",
                "semantic_reason": "LAYER2_NOT_IMPLEMENTED_IN_PHASE1",
                "diagnostic_count": len(self.diagnostics),
            },
            "diagnostics": [asdict(item) for item in sorted(self.diagnostics, key=Diagnostic.sort_key)],
            "exit_code": self.exit_code,
        }


class DuplicateKeyError(ValueError):
    pass


class ValidationFailure(Exception):
    def __init__(self, diagnostic: Diagnostic):
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_path_contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve(strict=True))
        return True
    except (OSError, ValueError):
        return False


def path_is_symlink(path: Path) -> bool:
    return path.is_symlink()


def json_pointer(parts: Iterable[Any]) -> str:
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "" if not escaped else "/" + "/".join(escaped)


def _pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_non_integer(token: str) -> int:
    raise ValueError(f"forbidden numeric token: {token}")


def strict_json_decode(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="strict")
    return json.loads(
        text, object_pairs_hook=_pairs_hook, parse_float=_reject_non_integer,
        parse_constant=_reject_non_integer,
    )


def strict_json_load(raw: bytes) -> dict[str, Any]:
    value = strict_json_decode(raw)
    if not isinstance(value, dict):
        raise TypeError("root value is not an object")
    return value


def _forbidden_character(text: str) -> bool:
    return any(
        ord(char) == 0 or ord(char) in BIDI_OR_ZERO_WIDTH
        or 0xD800 <= ord(char) <= 0xDFFF
        for char in text
    )


def _forbidden_raw_character(text: str) -> bool:
    return any(
        _forbidden_character(char)
        or (unicodedata.category(char) in {"Cc", "Cf", "Cs"} and char != "\n")
        for char in text
    )


def _scan_number_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            index += 1
            continue
        if char in "+-" or char.isdigit() or text.startswith("NaN", index) or text.startswith("Infinity", index):
            start = index
            index += 1
            while index < len(text) and (text[index].isascii() and (text[index].isalnum() or text[index] in ".+-")):
                index += 1
            tokens.append(text[start:index])
        else:
            index += 1
    return tokens


def _mask_number_tokens(text: str) -> str:
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char in "+-" or char.isdigit() or text.startswith("NaN", index) or text.startswith("Infinity", index):
            index += 1
            while index < len(text) and (text[index].isascii() and (text[index].isalnum() or text[index] in ".+-")):
                index += 1
            output.append("0")
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _number_token_error(tokens: list[str]) -> tuple[str, str] | None:
    for token in tokens:
        if not re.fullmatch(r"0|[1-9][0-9]*", token):
            return "FORBIDDEN_NUMBER_FORMAT", f"forbidden integer token {token!r}"
        if len(token) > 16 or int(token) > 9007199254740991:
            return "INTEGER_RANGE_EXCEEDED", f"integer exceeds safe range: {token}"
    return None


def _container_metrics(value: Any) -> tuple[int, int, int, int]:
    maximum_depth = 0
    nodes = 0
    maximum_members = 0
    maximum_elements = 0
    stack = [(value, 1 if isinstance(value, (dict, list)) else 0)]
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if isinstance(item, dict):
            maximum_depth = max(maximum_depth, depth)
            maximum_members = max(maximum_members, len(item))
            stack.extend(
                (child, depth + 1 if isinstance(child, (dict, list)) else depth)
                for child in item.values()
            )
        elif isinstance(item, list):
            maximum_depth = max(maximum_depth, depth)
            maximum_elements = max(maximum_elements, len(item))
            stack.extend(
                (child, depth + 1 if isinstance(child, (dict, list)) else depth)
                for child in item
            )
    return maximum_depth, nodes, maximum_members, maximum_elements


def _contains_null(value: Any) -> bool:
    stack = [value]
    while stack:
        item = stack.pop()
        if item is None:
            return True
        if isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return False


def _safe_relative_posix_path(value: str) -> bool:
    if not value or "\x00" in value or "\\" in value or ":" in value or value.startswith("/"):
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def validate_toolchain(marker: Path | None, marker_sha256: str | None) -> tuple[dict[str, Any], list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    python_version = ".".join(map(str, sys.version_info[:3]))
    jsonschema_version = importlib.metadata.version("jsonschema")
    if python_version != "3.11.0":
        diagnostics.append(Diagnostic("TOOLCHAIN", "TOOLCHAIN_PYTHON_VERSION_MISMATCH", "M0", message=f"expected Python 3.11.0, got {python_version}"))
    if jsonschema_version != "4.26.0":
        diagnostics.append(Diagnostic("TOOLCHAIN", "TOOLCHAIN_JSONSCHEMA_VERSION_MISMATCH", "M0", message=f"expected jsonschema 4.26.0, got {jsonschema_version}"))
    if not callable(getattr(Draft202012Validator, "check_schema", None)):
        diagnostics.append(Diagnostic("TOOLCHAIN", "TOOLCHAIN_DRAFT202012_UNAVAILABLE", "M0", message="Draft202012Validator.check_schema is unavailable"))
    marker_result = "NOT_REQUESTED"
    if (marker is None) != (marker_sha256 is None):
        diagnostics.append(Diagnostic("TOOLCHAIN", "TOOLCHAIN_MARKER_ARGUMENT_MISMATCH", "M0", message="marker path and SHA256 must be specified together"))
        marker_result = "FAIL"
    elif marker is not None and marker_sha256 is not None:
        marker_result = "PASS"
        if not marker.is_file() or path_is_symlink(marker):
            diagnostics.append(Diagnostic("TOOLCHAIN", "TOOLCHAIN_MARKER_NOT_REGULAR", "M0", message="toolchain marker is not a regular file"))
            marker_result = "FAIL"
        elif not re.fullmatch(r"[0-9a-f]{64}", marker_sha256) or sha256_file(marker) != marker_sha256:
            diagnostics.append(Diagnostic("TOOLCHAIN", "TOOLCHAIN_MARKER_HASH_MISMATCH", "M0", message="toolchain marker SHA256 mismatch"))
            marker_result = "FAIL"
    return {
        "result": "FAIL" if diagnostics else "PASS",
        "python_version": python_version,
        "jsonschema_version": jsonschema_version,
        "draft202012validator_available": callable(getattr(Draft202012Validator, "check_schema", None)),
        "pip_check": "PREVALIDATED_EXTERNAL_GATE",
        "toolchain_marker_result": marker_result,
    }, diagnostics


def validate_manifest_raw(repository_root: Path, manifest_relative_path: str) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    pure = PurePosixPath(manifest_relative_path)
    def fail(code: str, message: str) -> tuple[None, list[Diagnostic]]:
        return None, [Diagnostic("MANIFEST", code, "M1", manifest_relative_path, message=message)]
    if pure.is_absolute() or not _safe_relative_posix_path(manifest_relative_path):
        return fail("MANIFEST_PATH_OUTSIDE_REPOSITORY", "manifest path escapes repository")
    path = repository_root / Path(manifest_relative_path)
    if not is_path_contained(repository_root, path):
        return fail("MANIFEST_PATH_OUTSIDE_REPOSITORY", "manifest path escapes repository")
    if path_is_symlink(path):
        return fail("MANIFEST_SYMLINK_FORBIDDEN", "manifest symlink is forbidden")
    if not path.exists():
        return fail("MANIFEST_NOT_FOUND", "manifest not found")
    if not path.is_file():
        return fail("MANIFEST_NOT_REGULAR", "manifest is not a regular file")
    raw = path.read_bytes()
    if not raw or len(raw) > 65536:
        return fail("MANIFEST_PARSE_ERROR", "manifest raw size is invalid")
    if raw.startswith(b"\xef\xbb\xbf"):
        return fail("MANIFEST_PARSE_ERROR", "manifest BOM is forbidden")
    if b"\r" in raw:
        return fail("MANIFEST_PARSE_ERROR", "manifest CR is forbidden")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        return fail("MANIFEST_PARSE_ERROR", "manifest must end in exactly one LF")
    lines = raw[:-1].split(b"\n")
    if len(lines) > 4096 or any(len(line) > 4096 for line in lines):
        return fail("MANIFEST_PARSE_ERROR", "manifest line limit exceeded")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return fail("MANIFEST_PARSE_ERROR", "manifest is not valid UTF-8")
    if _forbidden_raw_character(text):
        return fail("MANIFEST_PARSE_ERROR", "manifest contains a forbidden character")
    try:
        data = strict_json_load(raw)
    except DuplicateKeyError as error:
        return fail("MANIFEST_DUPLICATE_KEY", f"duplicate manifest key: {error}")
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as error:
        return fail("MANIFEST_PARSE_ERROR", f"manifest Strict JSON parse failed: {error}")
    depth, _, _, _ = _container_metrics(data)
    if depth > 8:
        return fail("MANIFEST_PARSE_ERROR", "manifest nesting depth exceeded")
    return data, diagnostics


def _m2(code: str, path: str, message: str, pointer: str = "") -> Diagnostic:
    return Diagnostic("MANIFEST", code, "M2", path, json_pointer=pointer, message=message)


def validate_manifest_model(repository_root: Path, manifest_path: str, data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    if tuple(data) != ROOT_KEYS:
        diagnostics.append(_m2("MANIFEST_UNKNOWN_PROPERTY", manifest_path, "root property set or order mismatch"))
        return [], diagnostics
    if data.get("manifest_version") != 1 or data.get("protocol_version") != "v0" or data.get("vector_directory") != VECTOR_DIRECTORY or data.get("vector_count") != 38 or data.get("source_scenario_count") != 36:
        diagnostics.append(_m2("MANIFEST_COVERAGE_MISMATCH", manifest_path, "manifest fixed identity mismatch"))
    schema_object = data.get("vector_schema")
    if not isinstance(schema_object, dict) or list(schema_object) != ["path", "sha256"] or schema_object.get("path") != EXPECTED_SCHEMA_PATH or schema_object.get("sha256") != EXPECTED_SCHEMA_SHA256:
        diagnostics.append(_m2("MANIFEST_SCHEMA_HASH_MISMATCH", manifest_path, "schema identity mismatch", "/vector_schema"))
    schema_path = repository_root / EXPECTED_SCHEMA_PATH
    if path_is_symlink(schema_path) or not schema_path.is_file() or sha256_file(schema_path) != EXPECTED_SCHEMA_SHA256:
        diagnostics.append(_m2("MANIFEST_SCHEMA_HASH_MISMATCH", EXPECTED_SCHEMA_PATH, "schema artifact SHA256 mismatch"))
    sources = data.get("source_documents")
    expected_sources = {
        name: {"path": path, "sha256": digest}
        for name, path, digest in SOURCE_DOCUMENT_ROWS
    }
    if not isinstance(sources, dict) or tuple(sources) != SOURCE_KEYS or sources != expected_sources:
        diagnostics.append(_m2("MANIFEST_SOURCE_HASH_MISMATCH", manifest_path, "source document model mismatch", "/source_documents"))
    for source in expected_sources.values():
        path = repository_root / source["path"]
        if not path.is_file() or path_is_symlink(path) or sha256_file(path) != source["sha256"]:
            diagnostics.append(_m2("MANIFEST_SOURCE_HASH_MISMATCH", source["path"], "source document SHA256 mismatch"))
    rows = data.get("vectors")
    if not isinstance(rows, list) or len(rows) != 38:
        diagnostics.append(_m2("MANIFEST_COVERAGE_MISMATCH", manifest_path, "vector entry count must be 38", "/vectors"))
        return [], diagnostics
    ids: list[str] = []
    paths: list[str] = []
    scenarios: list[int] = []
    profiles: dict[str, str] = {}
    accepted: set[str] = set()
    valid_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        pointer = f"/vectors/{index}"
        if not isinstance(row, dict) or tuple(row) != ENTRY_KEYS:
            diagnostics.append(_m2("MANIFEST_UNKNOWN_PROPERTY", manifest_path, "vector entry property set or order mismatch", pointer))
            continue
        vector_id = row.get("vector_id")
        rel = row.get("path")
        if not isinstance(vector_id, str) or not isinstance(rel, str):
            diagnostics.append(_m2("MANIFEST_VECTOR_ID_MISMATCH", manifest_path, "vector ID/path type mismatch", pointer))
            continue
        ids.append(vector_id); paths.append(rel)
        if vector_id != EXPECTED_IDS[index]:
            diagnostics.append(_m2("MANIFEST_ORDER_MISMATCH", manifest_path, "vector ID order mismatch", pointer + "/vector_id"))
        expected_rel = f"{VECTOR_DIRECTORY}/{vector_id}.json"
        path = repository_root / Path(rel)
        if not _safe_relative_posix_path(rel) or rel != expected_rel or not is_path_contained(repository_root / VECTOR_DIRECTORY, path):
            diagnostics.append(_m2("MANIFEST_VECTOR_PATH_MISMATCH", rel, "vector path mismatch or escape", pointer + "/path"))
            continue
        if not path.exists():
            diagnostics.append(_m2("MANIFEST_VECTOR_NOT_FOUND", rel, "vector file not found")); continue
        if path_is_symlink(path) or not path.is_file():
            diagnostics.append(_m2("MANIFEST_VECTOR_PATH_MISMATCH", rel, "vector must be a regular non-symlink file")); continue
        if path.stem != vector_id:
            diagnostics.append(_m2("MANIFEST_VECTOR_ID_MISMATCH", rel, "filename stem and vector ID differ"))
        if not isinstance(row.get("sha256"), str) or sha256_file(path) != row.get("sha256"):
            diagnostics.append(_m2("MANIFEST_VECTOR_HASH_MISMATCH", rel, "vector SHA256 mismatch"))
        if not isinstance(row.get("size_bytes"), int) or isinstance(row.get("size_bytes"), bool) or path.stat().st_size != row.get("size_bytes"):
            diagnostics.append(_m2("MANIFEST_VECTOR_SIZE_MISMATCH", rel, "vector raw size mismatch"))
        scenario = row.get("source_scenario")
        profile = row.get("profile")
        flag = row.get("accepted_command_sequence_updated")
        if not isinstance(scenario, int) or isinstance(scenario, bool) or not 1 <= scenario <= 36:
            diagnostics.append(_m2("MANIFEST_COVERAGE_MISMATCH", rel, "source scenario is invalid"))
        else:
            scenarios.append(scenario)
        if profile not in {"one_side_test", "drive_pto_split_fixture"}:
            diagnostics.append(_m2("MANIFEST_COVERAGE_MISMATCH", rel, "profile is invalid"))
        else:
            profiles[vector_id] = profile
        if not isinstance(flag, bool):
            diagnostics.append(_m2("MANIFEST_COVERAGE_MISMATCH", rel, "accepted sequence flag is not boolean"))
        elif flag:
            accepted.add(vector_id)
        valid_rows.append(row)
    if len(set(ids)) != len(ids):
        diagnostics.append(_m2("MANIFEST_DUPLICATE_VECTOR_ID", manifest_path, "duplicate vector ID"))
    if len(set(paths)) != len(paths):
        diagnostics.append(_m2("MANIFEST_DUPLICATE_VECTOR_PATH", manifest_path, "duplicate vector path"))
    scenario_counts = {scenario: scenarios.count(scenario) for scenario in set(scenarios)}
    if set(scenario_counts) != set(range(1, 37)) or scenario_counts.get(1) != 2 or scenario_counts.get(14) != 2 or any(count != 1 for scenario, count in scenario_counts.items() if scenario not in {1, 14}):
        diagnostics.append(_m2("MANIFEST_COVERAGE_MISMATCH", manifest_path, "source scenario coverage mismatch"))
    split = {vector_id for vector_id, profile in profiles.items() if profile == "drive_pto_split_fixture"}
    if split != SPLIT_PROFILE_IDS or sum(profile == "one_side_test" for profile in profiles.values()) != 36:
        diagnostics.append(_m2("MANIFEST_COVERAGE_MISMATCH", manifest_path, "profile coverage mismatch"))
    if accepted != ACCEPTED_TRUE_IDS:
        diagnostics.append(_m2("MANIFEST_COVERAGE_MISMATCH", manifest_path, "accepted sequence exact set mismatch"))
    return valid_rows, diagnostics


def validate_manifest_artifacts(repository_root: Path, manifest_path: str, data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[Diagnostic]]:
    return validate_manifest_model(repository_root, manifest_path, data)


def _l0(vector_id: str, rel: str, code: str, stage: int, message: str) -> Diagnostic:
    assert code in LAYER0_CODES
    return Diagnostic("LAYER0", code, f"L0-{stage:02d}", rel, vector_id, message=message)


def validate_vector_layer0(repository_root: Path, row: dict[str, Any]) -> tuple[VectorPhase1Result, list[Diagnostic]]:
    vector_id = str(row.get("vector_id", "")); rel = str(row.get("path", ""))
    result = VectorPhase1Result(vector_id, rel)
    path = repository_root / Path(rel)
    vector_root = repository_root / VECTOR_DIRECTORY
    if not _safe_relative_posix_path(rel) or not is_path_contained(vector_root, path):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "PATH_OUTSIDE_VECTOR_DIRECTORY", 1, "vector path escapes vector directory")]
    if path_is_symlink(path):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "SYMLINK_FORBIDDEN", 2, "vector symlink is forbidden")]
    if not path.exists():
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "FILE_NOT_FOUND", 2, "vector file not found")]
    if not path.is_file():
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "FILE_NOT_REGULAR", 2, "vector is not a regular file")]
    if path.suffix != ".json":
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "INVALID_FILE_EXTENSION", 3, "vector extension must be .json")]
    if path.name != f"{vector_id}.json" or not re.fullmatch(r"PV0-VAL-[0-9]{3}[A-Z]?\.json", path.name):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "INVALID_VECTOR_FILENAME", 3, "vector filename is invalid")]
    raw = path.read_bytes()
    if not raw:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "EMPTY_FILE", 4, "vector file is empty")]
    if len(raw) > 65536:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "FILE_TOO_LARGE", 4, "vector exceeds 65536 bytes")]
    if raw.startswith(b"\xef\xbb\xbf"):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "BOM_FORBIDDEN", 5, "UTF-8 BOM is forbidden")]
    if b"\r" in raw:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "CR_FORBIDDEN", 5, "CR byte is forbidden")]
    if not raw.endswith(b"\n"):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "TRAILING_NEWLINE_REQUIRED", 5, "exactly one trailing LF is required")]
    if raw.endswith(b"\n\n"):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "MULTIPLE_TRAILING_NEWLINES", 5, "multiple trailing LF bytes")]
    lines = raw[:-1].split(b"\n")
    if len(lines) > 2048:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "TOO_MANY_LINES", 5, "line count exceeds 2048")]
    if any(len(line) > 4096 for line in lines):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "LINE_TOO_LONG", 5, "line exceeds 4096 bytes")]
    if any(re.search(rb"[ \t]+$", line) for line in lines):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "TRAILING_WHITESPACE_FORBIDDEN", 5, "trailing whitespace is forbidden")]
    if not raw.strip():
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "WHITESPACE_ONLY_FILE", 5, "whitespace-only file")]
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "INVALID_UTF8", 6, "invalid UTF-8")]
    if _forbidden_raw_character(text):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "FORBIDDEN_STRING_CHARACTER", 7, "forbidden raw source character")]
    number_error = _number_token_error(_scan_number_tokens(text))
    try:
        parse_text = _mask_number_tokens(text) if number_error else text
        data = json.loads(
            parse_text, object_pairs_hook=_pairs_hook, parse_float=_reject_non_integer,
            parse_constant=_reject_non_integer,
        )
    except DuplicateKeyError as error:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "DUPLICATE_KEY", 9, f"duplicate key: {error}")]
    except json.JSONDecodeError as error:
        code = "MULTIPLE_ROOT_VALUES" if error.msg == "Extra data" else "JSON_PARSE_ERROR"
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, code, 8, f"Strict JSON parse failed: {error.msg}")]
    except (UnicodeDecodeError, ValueError) as error:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "JSON_PARSE_ERROR", 8, f"Strict JSON parse failed: {error}")]
    except (MemoryError, RecursionError):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "RESOURCE_LIMIT_EXCEEDED", 8, "JSON parser resource limit exceeded")]
    if _contains_null(data):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "JSON_PARSE_ERROR", 8, "null is forbidden")]
    depth, nodes, members, elements = _container_metrics(data)
    if depth > 16:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "NESTING_DEPTH_EXCEEDED", 10, "nesting depth exceeds 16")]
    if nodes > 512:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "TOTAL_NODE_COUNT_EXCEEDED", 10, "JSON node count exceeds 512")]
    if members > 32:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "OBJECT_MEMBER_COUNT_EXCEEDED", 10, "object member count exceeds 32")]
    if elements > 32:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "ARRAY_ELEMENT_COUNT_EXCEEDED", 10, "array element count exceeds 32")]
    if isinstance(data, dict) and len(data) > 11:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "OBJECT_MEMBER_COUNT_EXCEEDED", 10, "root object member count exceeds 11")]
    if isinstance(data, dict) and isinstance(data.get("notes"), dict) and isinstance(data["notes"].get("tags"), list) and len(data["notes"]["tags"]) > 16:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "ARRAY_ELEMENT_COUNT_EXCEEDED", 10, "notes.tags element count exceeds 16")]
    for item in _walk_strings(data):
        value, is_key = item
        if _forbidden_character(value) or any(unicodedata.category(char) in {"Cc", "Cf", "Cs"} for char in value):
            result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "FORBIDDEN_STRING_CHARACTER", 11, "forbidden decoded string character")]
        if is_key and (len(value) > 64 or len(value.encode("utf-8")) > 128):
            result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "KEY_LENGTH_EXCEEDED", 11, "key length exceeded")]
        if not is_key and (len(value) > 1024 or len(value.encode("utf-8")) > 4096):
            result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "STRING_LENGTH_EXCEEDED", 11, "string length exceeded")]
    if number_error:
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, number_error[0], 12, number_error[1])]
    if not isinstance(data, dict):
        result.layer0_result = "FAIL"; return result, [_l0(vector_id, rel, "ROOT_OBJECT_REQUIRED", 13, "root object required")]
    result.layer0_result = "PASS"; result.data = data
    return result, []


def _walk_strings(value: Any) -> Iterable[tuple[str, bool]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, True
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)
    elif isinstance(value, str):
        yield value, False


def validate_schema_artifact(repository_root: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any], list[Diagnostic]]:
    schema_info = manifest["vector_schema"]
    rel = schema_info["path"]; path = repository_root / rel
    def fail(code: str, message: str) -> tuple[None, dict[str, Any], list[Diagnostic]]:
        assert code in SCHEMA_CODES
        return None, {"result": "FAIL", "repository_relative_path": rel}, [Diagnostic("SCHEMA", code, "L1", rel, message=message)]
    if not path.exists(): return fail("SCHEMA_NOT_FOUND", "schema not found")
    if not path.is_file() or path_is_symlink(path): return fail("SCHEMA_NOT_FOUND", "schema is not a regular file")
    if sha256_file(path) != schema_info["sha256"]: return fail("SCHEMA_HASH_MISMATCH", "schema SHA256 mismatch")
    try:
        schema = strict_json_load(path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, ValueError, TypeError) as error:
        return fail("SCHEMA_PARSE_ERROR", f"schema Strict JSON parse failed: {error}")
    for ref in _find_refs(schema):
        if not ref.startswith("#/$defs/"):
            return fail("SCHEMA_EXTERNAL_REF_FORBIDDEN", f"external or non-$defs ref forbidden: {ref}")
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        return fail("SCHEMA_META_VALIDATION_FAILED", f"schema meta-validation failed: {error}")
    return schema, {"result": "PASS", "repository_relative_path": rel}, []


def _find_refs(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str): yield child
            yield from _find_refs(child)
    elif isinstance(value, list):
        for child in value: yield from _find_refs(child)


def validate_vector_schema(schema: dict[str, Any], vectors: list[VectorPhase1Result]) -> list[Diagnostic]:
    validator = Draft202012Validator(schema)
    diagnostics: list[Diagnostic] = []
    for vector in vectors:
        if vector.layer0_result != "PASS" or vector.data is None:
            continue
        errors = sorted(validator.iter_errors(vector.data), key=lambda item: (json_pointer(item.absolute_path), json_pointer(item.absolute_schema_path), item.message))
        if not errors:
            vector.schema_result = "PASS"; continue
        vector.schema_result = "FAIL"
        for error in errors:
            diagnostics.append(Diagnostic(
                "SCHEMA", "SCHEMA_VALIDATION_FAILED", "L1",
                vector.repository_relative_path, vector.vector_id,
                json_pointer(error.absolute_path), error.message,
                json_pointer(error.absolute_schema_path), str(error.validator or ""),
            ))
    return diagnostics


def build_report(toolchain: dict[str, Any], manifest: dict[str, Any], schema: dict[str, Any], vectors: list[VectorPhase1Result], diagnostics: list[Diagnostic], exit_code: int) -> Phase1Report:
    return Phase1Report("PASS" if exit_code == 0 else "FAIL", toolchain, manifest, schema, vectors, sorted(diagnostics, key=Diagnostic.sort_key), exit_code)


def _run_phase1(repository_root: Path, manifest_path: str, marker: Path | None, marker_sha256: str | None) -> Phase1Report:
    toolchain, diagnostics = validate_toolchain(marker, marker_sha256)
    if diagnostics:
        return build_report(toolchain, {"result": "NOT_RUN", "repository_relative_path": manifest_path}, {"result": "NOT_RUN", "repository_relative_path": ""}, [], diagnostics, 2)
    manifest_data, manifest_diagnostics = validate_manifest_raw(repository_root, manifest_path)
    if manifest_diagnostics or manifest_data is None:
        return build_report(toolchain, {"result": "FAIL", "repository_relative_path": manifest_path}, {"result": "NOT_RUN", "repository_relative_path": ""}, [], manifest_diagnostics, 2)
    rows, m2_diagnostics = validate_manifest_artifacts(repository_root, manifest_path, manifest_data)
    if m2_diagnostics:
        return build_report(toolchain, {"result": "FAIL", "repository_relative_path": manifest_path, "vector_entry_count": len(manifest_data.get("vectors", []))}, {"result": "NOT_RUN", "repository_relative_path": ""}, [], m2_diagnostics, 2)
    manifest_report = {"result": "PASS", "repository_relative_path": manifest_path, "vector_entry_count": len(rows)}
    vectors: list[VectorPhase1Result] = []
    layer0_diagnostics: list[Diagnostic] = []
    for row in rows:
        vector, found = validate_vector_layer0(repository_root, row)
        vectors.append(vector); layer0_diagnostics.extend(found)
    schema_data, schema_report, schema_diagnostics = validate_schema_artifact(repository_root, manifest_data)
    vector_schema_diagnostics = validate_vector_schema(schema_data, vectors) if schema_data is not None else []
    diagnostics = [*layer0_diagnostics, *schema_diagnostics, *vector_schema_diagnostics]
    if layer0_diagnostics:
        exit_code = 3
    elif schema_diagnostics or vector_schema_diagnostics:
        exit_code = 4
    else:
        exit_code = 0
    return build_report(toolchain, manifest_report, schema_report, vectors, diagnostics, exit_code)


def run_phase1(repository_root: Path, manifest_path: str = DEFAULT_MANIFEST, marker: Path | None = None, marker_sha256: str | None = None) -> Phase1Report:
    try:
        return _run_phase1(repository_root.resolve(strict=True), manifest_path, marker, marker_sha256)
    except Exception as error:
        diagnostic = Diagnostic("INTERNAL", "INTERNAL_UNEXPECTED_ERROR", "INTERNAL", message=f"unexpected internal error: {type(error).__name__}")
        toolchain = {"result": "NOT_AVAILABLE", "pip_check": "PREVALIDATED_EXTERNAL_GATE", "toolchain_marker_result": "NOT_AVAILABLE"}
        return build_report(toolchain, {"result": "NOT_AVAILABLE", "repository_relative_path": manifest_path}, {"result": "NOT_AVAILABLE", "repository_relative_path": ""}, [], [diagnostic], 7)


def render_json_report(report: Phase1Report) -> str:
    return json.dumps(report.report_dict(), ensure_ascii=False, indent=2) + "\n"


def render_text_report(report: Phase1Report) -> str:
    data = report.report_dict(); summary = data["summary"]
    fields = [
        ("phase1_result", data["phase1_result"]),
        ("full_validator_result", data["full_validator_result"]),
        ("manifest_result", data["manifest"].get("result", "NOT_AVAILABLE")),
        ("schema_artifact_result", data["schema"].get("result", "NOT_AVAILABLE")),
        ("vector_count", summary["vector_count"]),
        ("layer0_pass_count", summary["layer0_pass_count"]),
        ("layer0_fail_count", summary["layer0_fail_count"]),
        ("schema_pass_count", summary["schema_pass_count"]),
        ("schema_fail_count", summary["schema_fail_count"]),
        ("semantic_result", summary["semantic_result"]),
        ("semantic_reason", summary["semantic_reason"]),
        ("diagnostic_count", summary["diagnostic_count"]),
        ("exit_code", data["exit_code"]),
    ]
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def _write_external_report(repository_root: Path, output: Path, content: str) -> None:
    if is_path_contained(repository_root, output):
        raise ValueError("report path inside repository is forbidden")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Protocol v0 offline validator Phase 1")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--manifest-path", default=DEFAULT_MANIFEST)
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--text-report", type=Path)
    parser.add_argument("--toolchain-marker", type=Path)
    parser.add_argument("--toolchain-marker-sha256")
    args = parser.parse_args(argv)
    report = run_phase1(args.repository_root, args.manifest_path, args.toolchain_marker, args.toolchain_marker_sha256)
    text = render_text_report(report)
    try:
        if args.json_report is not None:
            _write_external_report(args.repository_root, args.json_report, render_json_report(report))
        if args.text_report is not None:
            _write_external_report(args.repository_root, args.text_report, text)
    except (OSError, ValueError) as error:
        diagnostic = Diagnostic("INTERNAL", "INTERNAL_REPORT_WRITE_ERROR", "R0", message=f"report output rejected: {type(error).__name__}")
        report = build_report(report.toolchain, report.manifest, report.schema, report.vectors, [*report.diagnostics, diagnostic], 7)
        text = render_text_report(report)
    sys.stdout.write(text)
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
