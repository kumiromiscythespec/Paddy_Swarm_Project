from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from authority_adapter import (
    ASSEMBLY_INTERFACE_RELATIVE,
    AUTHORITY_RELATIVE,
    LANE_RELATIVE,
    REPOSITORY_ROOT,
    SEED_RELATIVE,
)


BASE_HEAD = "eb1a6e4bb7c775a02a5de9a3016b288122c23753"
EXPECTED_BRANCH = "cad/common-rover-v2.29.3.9.1-assembly-interface-v0.1"
EXPECTED_CORRECTED_ZIP_SHA256 = (
    "db8cae619147eef7a832a01bc342978ec91974c7bb935b756a5ecf81f2b00e06"
)
EXPECTED_CORRECTED_PATCH_SHA256 = (
    "be23eab918dfb08518e4c59fe99d08233fadb4732679bf6e97388f99cb97c7be"
)


def _run(
    args: list[str],
    *,
    cwd: Path = REPOSITORY_ROOT,
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
            f"COMMAND_FAILED:{args!r}:exit={result.returncode}:"
            f"{result.stderr.decode('utf-8', errors='replace')}"
        )
    return result


def _git_text(*args: str) -> str:
    return _run(["git", *args]).stdout.decode("utf-8").replace("\r\n", "\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_json(path: Path, value: object) -> None:
    _write_text(
        path,
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
    )


def _source_files() -> list[str]:
    prefixes = (
        ASSEMBLY_INTERFACE_RELATIVE.as_posix() + "/",
        LANE_RELATIVE.as_posix() + "/",
    )
    untracked = _git_text(
        "ls-files",
        "--others",
        "--exclude-standard",
        "--",
        ASSEMBLY_INTERFACE_RELATIVE.as_posix(),
        LANE_RELATIVE.as_posix(),
    ).splitlines()
    files = [
        line.strip()
        for line in untracked
        if line.strip().startswith(prefixes)
    ]
    return [".gitattributes", *sorted(files)]


def _build_patch(destination: Path, files: list[str]) -> None:
    parts = [
        _run(
            ["git", "diff", "--binary", "--", ".gitattributes"]
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
            accepted=(0, 1),
        )
        if result.returncode != 1 or not result.stdout:
            raise RuntimeError(f"ADDED_FILE_PATCH_FAILED:{relative}")
        parts.append(result.stdout)
    payload = b"".join(parts).replace(b"\r\n", b"\n")
    destination.write_bytes(payload)


def _verify_patch(patch: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="pfd_patch_index_") as temporary:
        index = Path(temporary) / "index"
        env = dict(__import__("os").environ)
        env["GIT_INDEX_FILE"] = str(index)
        _run(["git", "read-tree", BASE_HEAD], env=env)
        apply_result = _run(
            ["git", "apply", "--cached", "--check", str(patch)],
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
            env=env,
        )
    return {
        "schema": "PS_PROGRESSIVE_DUMMY_PATCH_CHECK_V0_1",
        "base_commit": BASE_HEAD,
        "patch_sha256": _sha256(patch),
        "apply_exit_code": apply_result.returncode,
        "whitespace_exit_code": whitespace_result.returncode,
        "PATCH_APPLY_CHECK": "PASS",
        "PATCH_WHITESPACE_CHECK": "PASS",
    }


def _copy_source_snapshot(
    artifact: Path,
    files: list[str],
) -> list[dict]:
    snapshot = artifact / "source_snapshot"
    records = []
    for relative in files:
        source = REPOSITORY_ROOT / relative
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


def _corrected_source_comparison(corrected_artifact: Path) -> dict:
    corrected_snapshot = corrected_artifact / "source_snapshot"
    mismatches = []
    files = []
    for source in sorted(
        path
        for path in corrected_snapshot.rglob("*")
        if path.is_file()
    ):
        relative = source.relative_to(corrected_snapshot).as_posix()
        current = REPOSITORY_ROOT / relative
        if relative == ".gitattributes" and current.is_file():
            expected_append = (
                b"cad/common_rover/"
                b"v2_29_3_9_1_progressive_full_scale_dummy_v0_1/** "
                b"text eol=lf\n"
            )
            source_bytes = source.read_bytes().replace(b"\r\n", b"\n")
            current_bytes = current.read_bytes().replace(b"\r\n", b"\n")
            match = current_bytes == source_bytes + expected_append
            comparison = "AUTHORIZED_EXACT_LF_RULE_APPEND"
        else:
            match = current.is_file() and _sha256(source) == _sha256(current)
            comparison = "EXACT_BYTE_MATCH"
        files.append(
            {
                "relative_path": relative,
                "match": match,
                "comparison": comparison,
            }
        )
        if not match:
            mismatches.append(relative)
    return {
        "file_count": len(files),
        "mismatches": mismatches,
        "all_match": not mismatches,
        "files": files,
    }


def _repository_cleanliness() -> dict:
    generated = []
    lane = REPOSITORY_ROOT / LANE_RELATIVE
    forbidden_suffixes = {
        ".stl",
        ".step",
        ".svg",
        ".json",
        ".csv",
        ".pyc",
    }
    for path in lane.rglob("*"):
        if not path.is_file():
            continue
        if (
            path.suffix.lower() in forbidden_suffixes
            or "__pycache__" in path.parts
        ):
            generated.append(path.relative_to(REPOSITORY_ROOT).as_posix())
    authority_diff = _git_text(
        "diff", "--name-only", BASE_HEAD, "--", AUTHORITY_RELATIVE.as_posix()
    ).splitlines()
    seed_diff = _git_text(
        "diff", "--name-only", BASE_HEAD, "--", SEED_RELATIVE.as_posix()
    ).splitlines()
    return {
        "schema": "PS_PROGRESSIVE_DUMMY_REPOSITORY_CLEANLINESS_V0_1",
        "new_lane_generated_outputs": sorted(generated),
        "authority_lane_diff_files": sorted(filter(None, authority_diff)),
        "seed_lane_diff_files": sorted(filter(None, seed_diff)),
        "repository_generated_output_count": len(generated),
        "REPOSITORY_GENERATED_OUTPUT_STATUS": (
            "CLEAN"
            if not generated and not authority_diff and not seed_diff
            else "FAIL"
        ),
    }


def _commands_executed() -> str:
    commands = (
        "git branch --show-current",
        "git rev-parse HEAD",
        "git status --porcelain=v1 --untracked-files=all",
        "verify corrected ZIP SHA-256",
        "verify corrected source.patch SHA-256",
        "compare corrected source_snapshot to existing worktree",
        "repository profile specification audit with rg",
        "paddy-cad python run_unit_tests.py",
        "paddy-cad python generate_dummy_kit.py --output-dir <external>",
        "paddy-cad python run_unit_tests.py --json <external> --text <external>",
        "authority run_validation.py",
        "seed validate_seed.py --output <external> --no-step-roundtrip",
        "Assembly Interface validate_interfaces.py --output <external>",
        "validate_dummy_kit.py --artifact-dir <external> --output <external>",
        "git apply --cached --check source.patch against base index",
        "git apply --cached --check --whitespace=error source.patch",
        "deterministic sorted ZIP creation and external SHA-256 receipt",
    )
    return "\n".join(commands) + "\n"


def _write_checksums(artifact: Path) -> None:
    checksum_path = artifact / "SHA256SUMS.txt"
    files = sorted(
        path
        for path in artifact.rglob("*")
        if path.is_file() and path != checksum_path
    )
    lines = [
        f"{_sha256(path)}  {path.relative_to(artifact).as_posix()}"
        for path in files
    ]
    _write_text(checksum_path, "\n".join(lines) + "\n")


def _deterministic_zip(artifact: Path) -> tuple[Path, str]:
    zip_path = artifact.with_suffix(".zip")
    receipt = Path(str(zip_path) + ".sha256")
    if zip_path.exists() or receipt.exists():
        raise RuntimeError("ZIP_OR_RECEIPT_ALREADY_EXISTS")
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
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    digest = _sha256(zip_path)
    _write_text(receipt, f"{digest}  {zip_path.name}\n")
    return zip_path, digest


def package(artifact: Path, corrected_artifact: Path) -> dict:
    artifact = artifact.resolve()
    corrected_artifact = corrected_artifact.resolve()
    if _git_text("rev-parse", "HEAD").strip() != BASE_HEAD:
        raise RuntimeError("EXACT_BASE_MISMATCH")
    if _git_text("branch", "--show-current").strip() != EXPECTED_BRANCH:
        raise RuntimeError("BRANCH_MISMATCH")
    corrected_zip = Path(str(corrected_artifact) + ".zip")
    if _sha256(corrected_zip) != EXPECTED_CORRECTED_ZIP_SHA256:
        raise RuntimeError("CORRECTED_ZIP_HASH_MISMATCH")
    if _sha256(corrected_artifact / "source.patch") != (
        EXPECTED_CORRECTED_PATCH_SHA256
    ):
        raise RuntimeError("CORRECTED_PATCH_HASH_MISMATCH")
    comparison = _corrected_source_comparison(corrected_artifact)
    if not comparison["all_match"]:
        raise RuntimeError("CORRECTED_SOURCE_SNAPSHOT_MISMATCH")

    files = _source_files()
    _write_text(artifact / "changed_files.txt", "\n".join(files) + "\n")
    _build_patch(artifact / "source.patch", files)
    patch_checks = _verify_patch(artifact / "source.patch")
    _write_json(artifact / "patch_apply_checks.json", patch_checks)
    source_records = _copy_source_snapshot(artifact, files)

    cleanliness = _repository_cleanliness()
    if cleanliness["REPOSITORY_GENERATED_OUTPUT_STATUS"] != "CLEAN":
        raise RuntimeError("REPOSITORY_GENERATED_OUTPUT_STATUS_FAIL")
    _write_json(
        artifact / "repository_cleanliness_report.json",
        cleanliness,
    )
    _write_text(
        artifact / "repository_cleanliness_report.txt",
        "REPOSITORY_GENERATED_OUTPUT_STATUS=CLEAN\n"
        "authority_lane_diff_count=0\n"
        "seed_lane_diff_count=0\n"
        "new_lane_generated_output_count=0\n",
    )
    _write_text(
        artifact / "commands_executed.txt",
        _commands_executed(),
    )

    snapshot = {
        "schema": "PS_PROGRESSIVE_DUMMY_REPOSITORY_SNAPSHOT_V0_1",
        "branch": EXPECTED_BRANCH,
        "HEAD": BASE_HEAD,
        "git_status": _git_text(
            "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines(),
        "worktrees": _git_text("worktree", "list", "--porcelain").splitlines(),
        "corrected_zip_sha256": _sha256(corrected_zip),
        "corrected_patch_sha256": _sha256(
            corrected_artifact / "source.patch"
        ),
        "corrected_source_comparison": comparison,
        "source_snapshot": source_records,
        "patch_checks": patch_checks,
        "repository_cleanliness": cleanliness,
    }
    _write_json(artifact / "repository_snapshot.json", snapshot)
    snapshot_lines = [
        f"branch={snapshot['branch']}",
        f"HEAD={snapshot['HEAD']}",
        f"corrected_zip_sha256={snapshot['corrected_zip_sha256']}",
        f"corrected_patch_sha256={snapshot['corrected_patch_sha256']}",
        f"corrected_source_match={comparison['all_match']}",
        f"source_snapshot_file_count={len(source_records)}",
        "PATCH_APPLY_CHECK=PASS",
        "PATCH_WHITESPACE_CHECK=PASS",
        "REPOSITORY_GENERATED_OUTPUT_STATUS=CLEAN",
        "git_status=",
        *snapshot["git_status"],
        "worktrees=",
        *snapshot["worktrees"],
    ]
    _write_text(
        artifact / "repository_snapshot.txt",
        "\n".join(snapshot_lines) + "\n",
    )

    _write_checksums(artifact)
    zip_path, zip_sha256 = _deterministic_zip(artifact)
    return {
        "artifact": str(artifact),
        "zip": str(zip_path),
        "zip_sha256": zip_sha256,
        "patch_sha256": _sha256(artifact / "source.patch"),
        "source_file_count": len(files),
        **patch_checks,
        **cleanliness,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--corrected-artifact-dir", required=True, type=Path)
    args = parser.parse_args()
    report = package(args.artifact_dir, args.corrected_artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
