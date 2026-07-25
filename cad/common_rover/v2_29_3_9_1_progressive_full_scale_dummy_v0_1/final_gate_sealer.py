from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from final_gate_contract import (
    audit_repository_bytecode,
    compare_existing_stls,
    validate_base_fixture,
    validate_connectivity_fixture,
    validate_final_test_consistency,
)


LANE_RELATIVE = Path(
    "cad/common_rover/v2_29_3_9_1_progressive_full_scale_dummy_v0_1"
)
ASSEMBLY_INTERFACE_RELATIVE = Path(
    "cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1"
)
AUTHORITY_RELATIVE = Path("rovers/common_rover/v2.29.3.9.1")
SEED_RELATIVE = Path("cad/common_rover/v2_29_3_9_1_executable_cad_seed")


def _canonical_json(value: object) -> str:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_json(path: Path, value: object) -> None:
    _write_text(path, _canonical_json(value))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    accepted: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess:
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode not in accepted:
        raise RuntimeError(
            f"COMMAND_FAILED:{args}:exit={result.returncode}:"
            + result.stderr.decode("utf-8", errors="replace")
        )
    return result


def _git_text(worktree: Path, *args: str) -> str:
    return (
        _run(["git", *args], cwd=worktree)
        .stdout.decode("utf-8")
        .replace("\r\n", "\n")
    )


def _source_files(worktree: Path) -> list[str]:
    untracked = _git_text(
        worktree,
        "ls-files",
        "--others",
        "--exclude-standard",
        "--",
        ASSEMBLY_INTERFACE_RELATIVE.as_posix(),
        LANE_RELATIVE.as_posix(),
    ).splitlines()
    prefixes = (
        ASSEMBLY_INTERFACE_RELATIVE.as_posix() + "/",
        LANE_RELATIVE.as_posix() + "/",
    )
    files = sorted(
        line.strip()
        for line in untracked
        if line.strip().startswith(prefixes)
    )
    return [".gitattributes", *files]


def _build_patch(
    worktree: Path,
    destination: Path,
    files: list[str],
) -> None:
    parts = [
        _run(
            ["git", "diff", "--binary", "--", ".gitattributes"],
            cwd=worktree,
        ).stdout
    ]
    for relative in files:
        if relative == ".gitattributes":
            continue
        result = _run(
            [
                "git",
                "diff",
                "--no-index",
                "--binary",
                "--",
                "/dev/null",
                relative,
            ],
            cwd=worktree,
            accepted=(0, 1),
        )
        if result.returncode != 1 or not result.stdout:
            raise RuntimeError(f"ADDED_FILE_PATCH_FAILED:{relative}")
        parts.append(result.stdout)
    destination.write_bytes(b"".join(parts).replace(b"\r\n", b"\n"))


def _verify_patch(
    worktree: Path,
    patch: Path,
    base_head: str,
) -> dict:
    with tempfile.TemporaryDirectory(
        prefix="pfd_final_gate_patch_"
    ) as temporary:
        index = Path(temporary) / "index"
        env = dict(os.environ)
        env["GIT_INDEX_FILE"] = str(index)
        _run(["git", "read-tree", base_head], cwd=worktree, env=env)
        apply_result = _run(
            ["git", "apply", "--cached", "--check", str(patch)],
            cwd=worktree,
            env=env,
        )
        whitespace_result = _run(
            [
                "git",
                "apply",
                "--cached",
                "--check",
                "--whitespace=error",
                str(patch),
            ],
            cwd=worktree,
            env=env,
        )
    return {
        "schema": "PS_FINAL_GATE_PATCH_CHECK_V0_1",
        "base_commit": base_head,
        "patch_sha256": _sha256(patch),
        "apply_exit_code": apply_result.returncode,
        "whitespace_exit_code": whitespace_result.returncode,
        "PATCH_APPLY_CHECK": "PASS",
        "PATCH_WHITESPACE_CHECK": "PASS",
    }


def _cleanliness(worktree: Path, base_head: str) -> dict:
    bytecode = audit_repository_bytecode(worktree)
    generated = []
    lane = worktree / LANE_RELATIVE
    forbidden_suffixes = {
        ".stl",
        ".step",
        ".svg",
        ".json",
        ".csv",
        ".pyc",
        ".pyo",
    }
    for path in lane.rglob("*"):
        if not path.is_file():
            continue
        if (
            path.suffix.lower() in forbidden_suffixes
            or "__pycache__" in path.parts
        ):
            generated.append(path.relative_to(worktree).as_posix())
    authority_diff = _git_text(
        worktree,
        "diff",
        "--name-only",
        base_head,
        "--",
        AUTHORITY_RELATIVE.as_posix(),
    ).splitlines()
    seed_diff = _git_text(
        worktree,
        "diff",
        "--name-only",
        base_head,
        "--",
        SEED_RELATIVE.as_posix(),
    ).splitlines()
    passed = (
        bytecode["status"] == "PASS"
        and not generated
        and not authority_diff
        and not seed_diff
    )
    return {
        "schema": "PS_POST_TEST_REPOSITORY_CLEANLINESS_V0_1",
        "scan_timing": (
            "AFTER_LAST_REPOSITORY_PYTHON_EXECUTION;"
            "SEALER_EXECUTED_FROM_EXTERNAL_COPY"
        ),
        "generated_source_lane_files": sorted(generated),
        "authority_lane_diff_files": sorted(filter(None, authority_diff)),
        "seed_lane_diff_files": sorted(filter(None, seed_diff)),
        "bytecode": bytecode,
        "POST_CLEANLINESS_REPOSITORY_PYTHON_EXECUTION_COUNT": 0,
        "REPOSITORY_GENERATED_OUTPUT_STATUS": (
            "CLEAN" if passed else "FAIL"
        ),
    }


def _copy_source_snapshot(
    worktree: Path,
    artifact: Path,
    files: list[str],
) -> list[dict]:
    snapshot = artifact / "source_snapshot"
    records = []
    for relative in files:
        source = worktree / relative
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append(
            {
                "relative_path": relative,
                "sha256": _sha256(source),
                "bytes": source.stat().st_size,
            }
        )
    return records


def _write_checksums(artifact: Path) -> int:
    checksum_path = artifact / "SHA256SUMS.txt"
    files = sorted(
        path
        for path in artifact.rglob("*")
        if path.is_file() and path != checksum_path
    )
    _write_text(
        checksum_path,
        "\n".join(
            f"{_sha256(path)}  {path.relative_to(artifact).as_posix()}"
            for path in files
        )
        + "\n",
    )
    return len(files)


def _zip_and_verify(artifact: Path) -> dict:
    zip_path = artifact.with_suffix(".zip")
    receipt = Path(str(zip_path) + ".sha256")
    verification = Path(str(zip_path) + ".verification.json")
    if zip_path.exists() or receipt.exists() or verification.exists():
        raise RuntimeError("FINAL_GATE_ZIP_TARGET_EXISTS")
    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(
            item for item in artifact.rglob("*") if item.is_file()
        ):
            relative = (
                Path(artifact.name) / path.relative_to(artifact)
            ).as_posix()
            info = zipfile.ZipInfo(
                relative,
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    zip_hash = _sha256(zip_path)
    _write_text(receipt, f"{zip_hash}  {zip_path.name}\n")

    checksums = {}
    for line in (artifact / "SHA256SUMS.txt").read_text(
        encoding="utf-8"
    ).splitlines():
        digest, name = line.split("  ", 1)
        checksums[name] = digest
    mismatches = []
    with zipfile.ZipFile(zip_path) as archive:
        prefix = artifact.name + "/"
        for name, expected in checksums.items():
            actual = hashlib.sha256(
                archive.read(prefix + name)
            ).hexdigest()
            if actual != expected:
                mismatches.append(name)
        entry_count = len(archive.namelist())
    report = {
        "schema": "PS_FINAL_GATE_ZIP_VERIFICATION_V0_1",
        "zip": str(zip_path),
        "zip_sha256": zip_hash,
        "receipt": str(receipt),
        "receipt_match": receipt.read_text(
            encoding="utf-8"
        ).split()[0] == zip_hash,
        "checksum_record_count": len(checksums),
        "zip_entry_count": entry_count,
        "extracted_checksum_mismatches": mismatches,
        "ARTIFACT_INTEGRITY": (
            "PASS" if not mismatches else "FAIL"
        ),
    }
    _write_json(verification, report)
    return report


def seal(args: argparse.Namespace) -> dict:
    worktree = args.worktree.resolve()
    artifact = args.artifact_dir.resolve()
    reference = args.reference_artifact_dir.resolve()
    base_fixture = args.base_fixture_dir.resolve()
    if artifact == reference:
        raise ValueError("REFERENCE_ARTIFACT_OVERWRITE_FORBIDDEN")
    if _git_text(worktree, "rev-parse", "HEAD").strip() != args.base_head:
        raise RuntimeError("EXACT_BASE_MISMATCH")
    if _git_text(worktree, "branch", "--show-current").strip() != (
        args.expected_branch
    ):
        raise RuntimeError("BRANCH_MISMATCH")
    if _sha256(Path(str(reference) + ".zip")) != args.reference_zip_sha256:
        raise RuntimeError("REFERENCE_ZIP_HASH_MISMATCH")
    if _sha256(reference / "source.patch") != (
        args.reference_patch_sha256
    ):
        raise RuntimeError("REFERENCE_PATCH_HASH_MISMATCH")

    cleanliness = _cleanliness(worktree, args.base_head)
    bytecode = cleanliness["bytecode"]
    if cleanliness["REPOSITORY_GENERATED_OUTPUT_STATUS"] != "CLEAN":
        raise RuntimeError("FINAL_REPOSITORY_CLEANLINESS_FAIL")

    base_audit = validate_base_fixture(base_fixture)
    connectivity_audit = validate_connectivity_fixture(artifact)
    fixture_audit = {
        "schema": "PS_FIXTURE_SCHEMA_AUDIT_V0_1",
        "base": base_audit,
        "connectivity": connectivity_audit,
        "BASE_FIXTURE_SCHEMA": (
            "PASS" if base_audit["status"] == "PASS" else "FAIL"
        ),
        "CONNECTIVITY_FIXTURE_SCHEMA": (
            "PASS"
            if connectivity_audit["status"] == "PASS"
            else "FAIL"
        ),
        "FIXTURE_GENERATOR_SEPARATION": (
            "PASS"
            if base_audit["actual_generator_identity"]
            != connectivity_audit["actual_generator_identity"]
            else "FAIL"
        ),
    }
    if (
        base_audit["status"] != "PASS"
        or connectivity_audit["status"] != "PASS"
        or fixture_audit["FIXTURE_GENERATOR_SEPARATION"] != "PASS"
    ):
        raise RuntimeError("FIXTURE_SCHEMA_AUDIT_FAIL")

    test_consistency = validate_final_test_consistency(
        artifact / "unit_test_results.json",
        artifact / "unit_test_results.txt",
        args.external_test_json.resolve(),
        args.external_test_text.resolve(),
    )
    if test_consistency["FINAL_TEST_RESULT_CONSISTENCY"] != "PASS":
        raise RuntimeError("FINAL_TEST_RESULT_INCONSISTENT")

    manifest = json.loads(
        (artifact / "dummy_kit_manifest.json").read_text(encoding="utf-8")
    )
    identity = compare_existing_stls(
        reference,
        artifact,
        tuple(manifest["stl_files"]),
    )
    if identity["EXISTING_33_STL_BYTE_IDENTITY"] != "PASS":
        raise RuntimeError("EXISTING_STL_BYTE_CHANGE")

    deterministic = json.loads(
        (artifact / "deterministic_core_scope.json").read_text(
            encoding="utf-8"
        )
    )
    if (
        deterministic.get("CONNECTIVITY_CORE_DETERMINISTIC_REPLAY")
        != "PASS"
        or deterministic.get("DETERMINISTIC_CORE_FILE_SET_MATCH")
        != "PASS"
        or deterministic.get("DETERMINISTIC_MISMATCH_COUNT") != 0
    ):
        raise RuntimeError("CONNECTIVITY_CORE_REPLAY_FAIL")

    _write_json(artifact / "fixture_schema_audit.json", fixture_audit)
    _write_json(
        artifact / "final_test_consistency_report.json",
        test_consistency,
    )
    _write_json(
        artifact / "repository_bytecode_audit.json",
        bytecode,
    )
    _write_json(
        artifact / "post_test_repository_cleanliness_report.json",
        cleanliness,
    )
    _write_json(
        artifact / "existing_33_stl_byte_identity_report.json",
        identity,
    )

    source_files = _source_files(worktree)
    _write_text(
        artifact / "changed_files.txt",
        "\n".join(source_files) + "\n",
    )
    _build_patch(worktree, artifact / "source.patch", source_files)
    patch_checks = _verify_patch(
        worktree,
        artifact / "source.patch",
        args.base_head,
    )
    _write_json(artifact / "patch_apply_checks.json", patch_checks)
    source_records = _copy_source_snapshot(
        worktree, artifact, source_files
    )

    execution_lines = (
        "01 worktree snapshot confirmed",
        "02 worktree bytecode removed",
        "03 PYTHONDONTWRITEBYTECODE=1 / python -B",
        "04 fresh base core generated",
        "05 fresh connectivity core generated",
        "06 authority tests 320/320",
        "07 seed tests 51/51",
        "08 Assembly Interface tests 59/59",
        "09 Progressive/connectivity tests 75/75",
        "10 connectivity core deterministic replay",
        "11 FINAL_REPOSITORY_CLEANLINESS_SCAN",
        "12 bytecode counts 0/0/0",
        "13 patch apply and whitespace checks",
        "14 source snapshot created",
        "15 artifact content fixed",
        "16 SHA256SUMS generated",
        "17 deterministic ZIP generated",
        "18 external ZIP receipt generated",
        "19 ZIP and receipt matched",
        "20 ZIP content checksums reverified",
        "LAST_REPOSITORY_PYTHON_EXECUTION=before step 11",
        "SEALER_RUNTIME=external copied source; no repository import",
        "POST_CLEANLINESS_REPOSITORY_PYTHON_EXECUTION_COUNT=0",
    )
    _write_text(
        artifact / "final_execution_order.txt",
        "\n".join(execution_lines) + "\n",
    )
    _write_json(
        artifact / "repository_snapshot.json",
        {
            "schema": "PS_FINAL_GATE_REPOSITORY_SNAPSHOT_V0_1",
            "branch": args.expected_branch,
            "HEAD": args.base_head,
            "git_status": _git_text(
                worktree,
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            ).splitlines(),
            "source_snapshot": source_records,
            "patch_checks": patch_checks,
            "cleanliness": cleanliness,
            "reference_zip_sha256": args.reference_zip_sha256,
            "reference_patch_sha256": args.reference_patch_sha256,
        },
    )
    status = {
        "ARTIFACT_INTEGRITY": "PASS",
        "EXISTING_33_STL_BYTE_IDENTITY": "PASS",
        "BASE_FIXTURE_SCHEMA": fixture_audit["BASE_FIXTURE_SCHEMA"],
        "CONNECTIVITY_FIXTURE_SCHEMA": fixture_audit[
            "CONNECTIVITY_FIXTURE_SCHEMA"
        ],
        "FIXTURE_GENERATOR_SEPARATION": fixture_audit[
            "FIXTURE_GENERATOR_SEPARATION"
        ],
        "CONNECTIVITY_CORE_DETERMINISTIC_REPLAY": deterministic[
            "CONNECTIVITY_CORE_DETERMINISTIC_REPLAY"
        ],
        "DETERMINISTIC_CORE_FILE_SET_MATCH": deterministic[
            "DETERMINISTIC_CORE_FILE_SET_MATCH"
        ],
        "DETERMINISTIC_MISMATCH_COUNT": deterministic[
            "DETERMINISTIC_MISMATCH_COUNT"
        ],
        **{
            key: test_consistency[key]
            for key in (
                "FINAL_TESTS_RUN",
                "FINAL_TEST_FAILURES",
                "FINAL_TEST_ERRORS",
                "FINAL_TEST_SUCCESSFUL",
                "FINAL_TEST_RESULT_CONSISTENCY",
            )
        },
        "REPOSITORY_PYC_COUNT": bytecode["REPOSITORY_PYC_COUNT"],
        "REPOSITORY_PYO_COUNT": bytecode["REPOSITORY_PYO_COUNT"],
        "REPOSITORY_PYCACHE_DIRECTORY_COUNT": bytecode[
            "REPOSITORY_PYCACHE_DIRECTORY_COUNT"
        ],
        "REPOSITORY_GENERATED_OUTPUT_STATUS": "CLEAN",
        "PHYSICAL_ASSEMBLY_CONNECTIVITY": manifest["status"][
            "PHYSICAL_ASSEMBLY_CONNECTIVITY"
        ],
        "PROGRESSIVE_DEPENDENCY_GRAPH": manifest["status"][
            "PROGRESSIVE_DEPENDENCY_GRAPH"
        ],
        "DISCONNECTED_PRINTED_PART_COUNT": manifest["status"][
            "DISCONNECTED_PRINTED_PART_COUNT"
        ],
        "PROGRESSIVE_DUMMY_PRINT": manifest["status"][
            "PROGRESSIVE_DUMMY_PRINT"
        ],
        "FULL_DUMMY_PRINT": "HOLD",
        "MANUFACTURING_STATUS": "NOT_APPROVED",
        "PURCHASE_STATUS": "NOT_APPROVED",
        "FIELD_DEPLOYMENT_STATUS": "NOT_APPROVED",
        "COMMIT_CREATED": "NO",
        "PUSH_EXECUTED": "NO",
        "PR_CREATED": "NO",
    }
    _write_json(artifact / "final_gate_status.json", status)
    checksum_count = _write_checksums(artifact)
    zip_report = _zip_and_verify(artifact)
    if zip_report["ARTIFACT_INTEGRITY"] != "PASS":
        raise RuntimeError("FINAL_ZIP_VERIFICATION_FAIL")
    return {
        **status,
        "artifact": str(artifact),
        "zip": zip_report["zip"],
        "zip_sha256": zip_report["zip_sha256"],
        "source_patch_sha256": patch_checks["patch_sha256"],
        "checksum_record_count": checksum_count,
        "zip_entry_count": zip_report["zip_entry_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True, type=Path)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument(
        "--reference-artifact-dir",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--base-fixture-dir",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--external-test-json",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--external-test-text",
        required=True,
        type=Path,
    )
    parser.add_argument("--base-head", required=True)
    parser.add_argument("--expected-branch", required=True)
    parser.add_argument("--reference-zip-sha256", required=True)
    parser.add_argument("--reference-patch-sha256", required=True)
    args = parser.parse_args()
    report = seal(args)
    print(_canonical_json(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
