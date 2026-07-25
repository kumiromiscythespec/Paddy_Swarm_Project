from __future__ import annotations

import hashlib
import json
from pathlib import Path


BASE_MANIFEST_SCHEMA = "PS_PROGRESSIVE_FULL_SCALE_DUMMY_KIT_V0_1"
CONNECTIVITY_MANIFEST_SCHEMA = (
    "PS_PROGRESSIVE_FULL_SCALE_DUMMY_CONNECTIVITY_CORRECTION_V0_1"
)
BASE_GENERATOR_IDENTITY = "generate_dummy_kit.generate"
CONNECTIVITY_GENERATOR_IDENTITY = (
    "generate_connectivity_correction.generate"
)

BASE_CORE_OUTPUTS = (
    "a1_printability_audit.json",
    "anti_separation_lock_carrier.stl",
    "assembly_model.json",
    "battery_cassette_dummy.stl",
    "bbox_support_front.stl",
    "bbox_support_rear.stl",
    "cbox_saddle_left.stl",
    "cbox_saddle_right.stl",
    "core_alignment_key.stl",
    "current_bbox_dummy.stl",
    "current_cbox_dummy.stl",
    "dummy_kit_manifest.json",
    "exploded_full_dummy.svg",
    "float_slide_receiver_left.stl",
    "float_slide_receiver_right.stl",
    "float_width_audit.json",
    "fpb_front_crossmember_dummy.stl",
    "fpb_rail_left_dummy.stl",
    "fpb_rail_right_dummy.stl",
    "full_dummy_assembly_manual.md",
    "full_dummy_completeness_report.json",
    "full_dummy_disassembly_manual.md",
    "full_dummy_front.svg",
    "full_dummy_side.svg",
    "full_dummy_top.svg",
    "hardware_bom.csv",
    "lower_float_adapter_left.stl",
    "lower_float_adapter_right.stl",
    "part_number_location_map.svg",
    "pin_retainer_cover.stl",
    "print_quality_gate_checklist.csv",
    "print_to_assembly_dependency.svg",
    "printed_part_manifest.csv",
    "printed_part_number_audit.json",
    "profile_input_audit.json",
    "progressive_print_order.md",
    "rear_bbox_support_audit.json",
    "rear_cradle_dummy_part_1.stl",
    "rear_cradle_dummy_part_2.stl",
    "source_integrity_report.json",
    "stl_mesh_audit.json",
    "unresolved_full_scale_dimensions.md",
)

CONNECTIVITY_CORE_OUTPUTS = tuple(
    sorted(
        (
            *BASE_CORE_OUTPUTS,
            "ai10_clearance_reservation.md",
            "ai10_clearance_reservation.svg",
            "bbox_support_anchor_front.stl",
            "bbox_support_anchor_rear.stl",
            "bbox_support_attachment.svg",
            "cbox_saddle_attachment.svg",
            "cbox_saddle_base_clip_left.stl",
            "cbox_saddle_base_clip_right.stl",
            "connected_dry_assembly_report.json",
            "corrected_print_quality_gate_checklist.csv",
            "corrected_progressive_print_order.md",
            "float_adapter_profile3_attachment.svg",
            "front_fpb_to_rear_cradle_visual_locator.stl",
            "front_frame_corner_connector_left.stl",
            "front_frame_corner_connector_right.stl",
            "impossible_dependency_audit.json",
            "lower_adapter_visual_locator_left.stl",
            "lower_adapter_visual_locator_right.stl",
            "physical_connection_graph.json",
            "physical_connection_matrix.csv",
            "profile3_connection_exploded.svg",
            "profile3_dummy_connection_manual.md",
            "profile3_rail_outer_clamp_left.stl",
            "profile3_rail_outer_clamp_right.stl",
            "rear_cradle_center_joiner.stl",
            "rear_cradle_connection.svg",
            "rear_cradle_left_attachment.stl",
            "rear_cradle_right_attachment.stl",
            "static_stl_compatibility_report.json",
        )
    )
)

PACKAGING_ONLY_NAMES = frozenset(
    {
        "SHA256SUMS.txt",
        "unit_test_results.json",
        "unit_test_results.txt",
        "commands_executed.txt",
        "repository_snapshot.txt",
        "repository_snapshot.json",
        "changed_files.txt",
        "source.patch",
        "patch_apply_checks.json",
        "repository_cleanliness_report.json",
        "repository_cleanliness_report.txt",
        "connectivity_validation.json",
        "deterministic_replay_report.json",
        "final_test_consistency_report.json",
        "fixture_schema_audit.json",
        "deterministic_core_scope.json",
        "repository_bytecode_audit.json",
        "post_test_repository_cleanliness_report.json",
        "existing_33_stl_byte_identity_report.json",
        "final_execution_order.txt",
    }
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _manifest(artifact: Path) -> dict:
    path = artifact / "dummy_kit_manifest.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_fixture(
    artifact_directory: Path,
    *,
    expected_schema: str,
    expected_generator_identity: str,
    expected_core_outputs: tuple[str, ...],
) -> dict:
    artifact = artifact_directory.resolve()
    manifest = _manifest(artifact)
    blockers = []
    actual_schema = manifest.get("schema")
    actual_generator = manifest.get("generator_identity")
    if actual_schema != expected_schema:
        if actual_schema == CONNECTIVITY_MANIFEST_SCHEMA:
            blockers.append("CONNECTIVITY_FIXTURE_USED_FOR_BASE")
        elif actual_schema == BASE_MANIFEST_SCHEMA:
            blockers.append("BASE_FIXTURE_USED_FOR_CONNECTIVITY")
        else:
            blockers.append("FIXTURE_SCHEMA_MISMATCH")
    if actual_generator != expected_generator_identity:
        blockers.append("FIXTURE_GENERATOR_IDENTITY_MISMATCH")
    contract = manifest.get("core_output_contract", {})
    if contract.get("count") != len(expected_core_outputs):
        blockers.append("FIXTURE_CORE_OUTPUT_COUNT_MISMATCH")
    if tuple(contract.get("files", ())) != expected_core_outputs:
        blockers.append("FIXTURE_CORE_OUTPUT_SET_MISMATCH")
    missing = [
        name for name in expected_core_outputs if not (artifact / name).is_file()
    ]
    if missing:
        blockers.append("FIXTURE_CORE_OUTPUT_MISSING")
    return {
        "status": "PASS" if not blockers else "FAIL",
        "blockers": sorted(set(blockers)),
        "artifact": str(artifact),
        "expected_schema": expected_schema,
        "actual_schema": actual_schema,
        "expected_generator_identity": expected_generator_identity,
        "actual_generator_identity": actual_generator,
        "expected_core_output_count": len(expected_core_outputs),
        "missing_core_outputs": missing,
    }


def validate_base_fixture(artifact_directory: Path) -> dict:
    return validate_fixture(
        artifact_directory,
        expected_schema=BASE_MANIFEST_SCHEMA,
        expected_generator_identity=BASE_GENERATOR_IDENTITY,
        expected_core_outputs=BASE_CORE_OUTPUTS,
    )


def validate_connectivity_fixture(artifact_directory: Path) -> dict:
    return validate_fixture(
        artifact_directory,
        expected_schema=CONNECTIVITY_MANIFEST_SCHEMA,
        expected_generator_identity=CONNECTIVITY_GENERATOR_IDENTITY,
        expected_core_outputs=CONNECTIVITY_CORE_OUTPUTS,
    )


def compare_connectivity_core_outputs(
    first_directory: Path,
    second_directory: Path,
) -> dict:
    first = first_directory.resolve()
    second = second_directory.resolve()
    first_manifest = _manifest(first)
    second_manifest = _manifest(second)
    blockers = []
    if (
        first_manifest.get("generator_identity")
        != second_manifest.get("generator_identity")
    ):
        blockers.append("DETERMINISM_GENERATOR_MISMATCH")
    for report in (
        validate_connectivity_fixture(first),
        validate_connectivity_fixture(second),
    ):
        blockers.extend(report["blockers"])
    first_files = sorted(
        path.relative_to(first).as_posix()
        for path in first.rglob("*")
        if path.is_file()
    )
    second_files = sorted(
        path.relative_to(second).as_posix()
        for path in second.rglob("*")
        if path.is_file()
    )
    packaging = sorted(
        name
        for name in set(first_files + second_files)
        if Path(name).name in PACKAGING_ONLY_NAMES
        or name.startswith("source_snapshot/")
    )
    if packaging:
        blockers.append("PACKAGING_FILE_IN_CORE_REPLAY")
    expected = list(CONNECTIVITY_CORE_OUTPUTS)
    if first_files != second_files or first_files != expected:
        blockers.append("DETERMINISM_FILE_SET_MISMATCH")
    common = sorted(set(first_files) & set(second_files))
    mismatches = [
        name for name in common
        if _sha256(first / name) != _sha256(second / name)
    ]
    if mismatches:
        blockers.append("DETERMINISM_CONTENT_MISMATCH")
    blockers = sorted(set(blockers))
    return {
        "schema": "PS_CONNECTIVITY_DETERMINISTIC_CORE_SCOPE_V0_1",
        "blockers": blockers,
        "first_file_set": first_files,
        "second_file_set": second_files,
        "expected_file_set": expected,
        "packaging_files_detected": packaging,
        "mismatches": mismatches,
        "CONNECTIVITY_CORE_OUTPUT_COUNT": len(expected),
        "FIRST_FILE_SET_EQUALS_SECOND_FILE_SET": first_files == second_files,
        "DETERMINISTIC_CORE_FILE_SET_MATCH": (
            "PASS"
            if first_files == second_files == expected and not packaging
            else "FAIL"
        ),
        "DETERMINISTIC_MISMATCH_COUNT": len(mismatches),
        "CONNECTIVITY_CORE_DETERMINISTIC_REPLAY": (
            "PASS" if not blockers else "FAIL"
        ),
    }


def audit_repository_bytecode(repository_root: Path) -> dict:
    root = repository_root.resolve()
    pyc = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.pyc")
        if path.is_file()
    )
    pyo = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.pyo")
        if path.is_file()
    )
    caches = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("__pycache__")
        if path.is_dir()
    )
    blockers = []
    if pyc:
        blockers.append("REPOSITORY_PYC_PRESENT")
    if pyo:
        blockers.append("REPOSITORY_PYO_PRESENT")
    if caches:
        blockers.append("REPOSITORY_PYCACHE_PRESENT")
    return {
        "schema": "PS_REPOSITORY_BYTECODE_AUDIT_V0_1",
        "blockers": blockers,
        "pyc_files": pyc,
        "pyo_files": pyo,
        "pycache_directories": caches,
        "REPOSITORY_PYC_COUNT": len(pyc),
        "REPOSITORY_PYO_COUNT": len(pyo),
        "REPOSITORY_PYCACHE_DIRECTORY_COUNT": len(caches),
        "status": "PASS" if not blockers else "FAIL",
    }


def validate_execution_order(events: list[str]) -> dict:
    blockers = []
    try:
        scan_index = events.index("FINAL_REPOSITORY_CLEANLINESS_SCAN")
    except ValueError:
        scan_index = -1
        blockers.append("FINAL_CLEANLINESS_SCAN_MISSING")
    if scan_index >= 0 and any(
        event == "REPOSITORY_PYTHON_EXECUTION"
        for event in events[scan_index + 1:]
    ):
        blockers.append("POST_CLEANLINESS_PYTHON_EXECUTION")
    return {
        "status": "PASS" if not blockers else "FAIL",
        "blockers": blockers,
        "events": events,
    }


def validate_final_test_consistency(
    artifact_json: Path,
    artifact_text: Path,
    external_json: Path,
    external_text: Path,
) -> dict:
    paths = (
        artifact_json,
        artifact_text,
        external_json,
        external_text,
    )
    blockers = []
    if any(not path.is_file() for path in paths):
        blockers.append("FINAL_TEST_RESULT_INCONSISTENT")
        payloads = [{}, {}]
    else:
        payloads = [
            json.loads(artifact_json.read_text(encoding="utf-8")),
            json.loads(external_json.read_text(encoding="utf-8")),
        ]
        if _sha256(artifact_json) != _sha256(external_json):
            blockers.append("FINAL_TEST_RESULT_INCONSISTENT")
        if _sha256(artifact_text) != _sha256(external_text):
            blockers.append("FINAL_TEST_RESULT_INCONSISTENT")
    expected = {
        "tests_run": 75,
        "failures": 0,
        "errors": 0,
        "successful": True,
    }
    for payload in payloads:
        if any(payload.get(key) != value for key, value in expected.items()):
            blockers.append("FINAL_TEST_RESULT_INCONSISTENT")
    run_ids = {payload.get("run_id") for payload in payloads}
    if None in run_ids or len(run_ids) != 1:
        blockers.append("FINAL_TEST_RESULT_INCONSISTENT")
    blockers = sorted(set(blockers))
    return {
        "schema": "PS_FINAL_TEST_CONSISTENCY_REPORT_V0_1",
        "blockers": blockers,
        "artifact_json_sha256": (
            _sha256(artifact_json) if artifact_json.is_file() else None
        ),
        "artifact_text_sha256": (
            _sha256(artifact_text) if artifact_text.is_file() else None
        ),
        "external_json_sha256": (
            _sha256(external_json) if external_json.is_file() else None
        ),
        "external_text_sha256": (
            _sha256(external_text) if external_text.is_file() else None
        ),
        "run_id": next(iter(run_ids)) if len(run_ids) == 1 else None,
        "FINAL_TESTS_RUN": payloads[0].get("tests_run"),
        "FINAL_TEST_FAILURES": payloads[0].get("failures"),
        "FINAL_TEST_ERRORS": payloads[0].get("errors"),
        "FINAL_TEST_SUCCESSFUL": payloads[0].get("successful"),
        "FINAL_TEST_RESULT_CONSISTENCY": (
            "PASS" if not blockers else "FAIL"
        ),
    }


def compare_existing_stls(
    reference_directory: Path,
    candidate_directory: Path,
    filenames: tuple[str, ...],
) -> dict:
    reference = reference_directory.resolve()
    candidate = candidate_directory.resolve()
    records = []
    for name in filenames:
        old = reference / name
        new = candidate / name
        old_hash = _sha256(old) if old.is_file() else None
        new_hash = _sha256(new) if new.is_file() else None
        records.append(
            {
                "filename": name,
                "reference_sha256": old_hash,
                "candidate_sha256": new_hash,
                "raw_byte_identical": old_hash is not None
                and old_hash == new_hash,
            }
        )
    changed = [
        row["filename"] for row in records if not row["raw_byte_identical"]
    ]
    return {
        "schema": "PS_EXISTING_33_STL_BYTE_IDENTITY_REPORT_V0_1",
        "blockers": (
            ["EXISTING_STL_BYTE_CHANGE"] if changed else []
        ),
        "EXPECTED_EXISTING_STL_COUNT": len(filenames),
        "MODIFIED_EXISTING_STL_COUNT": len(changed),
        "changed_files": changed,
        "records": records,
        "EXISTING_33_STL_BYTE_IDENTITY": (
            "PASS" if not changed else "FAIL"
        ),
    }
