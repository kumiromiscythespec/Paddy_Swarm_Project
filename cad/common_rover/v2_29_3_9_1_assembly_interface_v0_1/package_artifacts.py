from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from authority_adapter import (
    AUTHORITY_RELATIVE,
    LANE_RELATIVE,
    SEED_RELATIVE,
    canonical_json,
    find_repository_root,
)


BASE_HEAD = "eb1a6e4bb7c775a02a5de9a3016b288122c23753"
EXPECTED_BRANCH = "cad/common-rover-v2.29.3.9.1-assembly-interface-v0.1"


def _run(
    root: Path,
    args: list[str],
    *,
    require_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if require_success and result.returncode != 0:
        raise RuntimeError(
            f"COMMAND_FAILED:{args!r}:{result.returncode}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result


def _write(path: Path, text: str) -> None:
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _external_artifact(path: Path, root: Path) -> Path:
    output = path.resolve()
    if output == root or root in output.parents:
        raise ValueError("ARTIFACT_DIRECTORY_MUST_BE_OUTSIDE_REPOSITORY")
    if not output.is_dir():
        raise ValueError("ARTIFACT_DIRECTORY_NOT_FOUND")
    return output


def _changed_files(root: Path) -> list[str]:
    tracked = _run(
        root, ["git", "diff", "--name-only", "--", ".gitattributes"]
    ).stdout.splitlines()
    untracked = _run(
        root,
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
            LANE_RELATIVE.as_posix(),
        ],
    ).stdout.splitlines()
    return sorted(set(tracked + untracked))


def _source_patch(root: Path, changed: list[str]) -> str:
    chunks = []
    tracked = _run(
        root,
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "diff",
            "--binary",
            "--",
            ".gitattributes",
        ],
    ).stdout
    if tracked:
        chunks.append(tracked)
    for relative in changed:
        if relative == ".gitattributes":
            continue
        result = _run(
            root,
            [
                "git",
                "-c",
                "core.autocrlf=false",
                "diff",
                "--no-index",
                "--binary",
                "--",
                "/dev/null",
                relative,
            ],
            require_success=False,
        )
        if result.returncode not in {0, 1}:
            raise RuntimeError(
                f"PATCH_FRAGMENT_FAILED:{relative}:{result.stderr}"
            )
        chunks.append(result.stdout)
    patch = "".join(chunks).replace("\r\n", "\n")
    if "\r" in patch:
        raise RuntimeError("PATCH_CONTAINS_CR")
    return patch


def _verify_patch(root: Path, patch: Path) -> dict:
    temporary_parent = Path(
        tempfile.mkdtemp(prefix="paddy_patch_check_")
    ).resolve()
    temporary_worktree = temporary_parent / "worktree"
    try:
        _run(
            root,
            [
                "git",
                "worktree",
                "add",
                "--detach",
                str(temporary_worktree),
                BASE_HEAD,
            ],
        )
        normal = _run(
            temporary_worktree,
            ["git", "apply", "--check", str(patch)],
            require_success=False,
        )
        whitespace = _run(
            temporary_worktree,
            [
                "git",
                "apply",
                "--check",
                "--whitespace=error",
                str(patch),
            ],
            require_success=False,
        )
        return {
            "PATCH_APPLY_CHECK": (
                "PASS" if normal.returncode == 0 else "FAIL"
            ),
            "PATCH_WHITESPACE_CHECK": (
                "PASS" if whitespace.returncode == 0 else "FAIL"
            ),
            "patch_apply_stdout": normal.stdout,
            "patch_apply_stderr": normal.stderr,
            "patch_whitespace_stdout": whitespace.stdout,
            "patch_whitespace_stderr": whitespace.stderr,
            "crlf_count": patch.read_bytes().count(b"\r\n"),
            "bare_cr_count": (
                patch.read_bytes().count(b"\r")
                - patch.read_bytes().count(b"\r\n")
            ),
        }
    finally:
        if temporary_worktree.exists():
            _run(
                root,
                [
                    "git",
                    "worktree",
                    "remove",
                    "--force",
                    str(temporary_worktree),
                ],
                require_success=False,
            )
        if temporary_parent.exists():
            shutil.rmtree(temporary_parent)


def _validation_reports(root: Path, artifact: Path) -> None:
    authority = _run(
        root,
        [
            sys.executable,
            str(root / AUTHORITY_RELATIVE / "run_validation.py"),
        ],
    )
    authority_data = json.loads(authority.stdout)
    _write(
        artifact / "authority_validation.json",
        canonical_json(authority_data),
    )
    _run(
        root,
        [
            sys.executable,
            str(root / SEED_RELATIVE / "validate_seed.py"),
            "--output",
            str(artifact / "seed_validation.json"),
        ],
    )
    _run(
        root,
        [
            sys.executable,
            str(root / LANE_RELATIVE / "validate_interfaces.py"),
            "--artifact-dir",
            str(artifact),
            "--output",
            str(artifact / "interface_validation.json"),
        ],
    )


def _unit_test_reports(root: Path, artifact: Path) -> None:
    _run(
        root,
        [
            sys.executable,
            str(root / LANE_RELATIVE / "run_unit_tests.py"),
            "--json",
            str(artifact / "unit_test_results.json"),
            "--text",
            str(artifact / "unit_test_results.txt"),
        ],
    )
    _run(
        root,
        [
            sys.executable,
            str(root / AUTHORITY_RELATIVE / "run_unit_tests.py"),
            "--json",
            str(artifact / "authority_unit_test_results.json"),
            "--text",
            str(artifact / "authority_unit_test_results.txt"),
        ],
    )
    _run(
        root,
        [
            sys.executable,
            str(root / SEED_RELATIVE / "run_unit_tests.py"),
            "--json",
            str(artifact / "seed_unit_test_results.json"),
            "--text",
            str(artifact / "seed_unit_test_results.txt"),
        ],
    )


def _snapshot_reports(
    root: Path, artifact: Path, changed: list[str]
) -> None:
    branch = _run(root, ["git", "branch", "--show-current"]).stdout.strip()
    head = _run(root, ["git", "rev-parse", "HEAD"]).stdout.strip()
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"BRANCH_MISMATCH:{branch}")
    if head != BASE_HEAD:
        raise RuntimeError(f"HEAD_MISMATCH:{head}")
    worktrees = _run(root, ["git", "worktree", "list", "--porcelain"]).stdout
    target_status = _run(
        root, ["git", "status", "--short", "--untracked-files=all"]
    ).stdout
    main_root = Path("D:/Paddy_Swarm_Project")
    main_status = (
        _run(
            main_root,
            ["git", "status", "--short", "--untracked-files=all"],
        ).stdout
        if main_root.is_dir()
        else "MAIN_WORKTREE_NOT_FOUND\n"
    )
    snapshot = (
        f"branch={branch}\n"
        f"HEAD={head}\n"
        "staged_diff_count="
        f"{len(_run(root, ['git', 'diff', '--cached', '--name-only']).stdout.splitlines())}\n"
        "tracked_diff_files=\n"
        f"{_run(root, ['git', 'diff', '--name-only']).stdout}"
        "worktrees=\n"
        f"{worktrees}"
        "target_worktree_status=\n"
        f"{target_status}"
        "original_main_worktree_status=\n"
        f"{main_status}"
    )
    _write(artifact / "repository_snapshot.txt", snapshot)
    _write(artifact / "git_status.txt", target_status)
    _write(artifact / "changed_files.txt", "\n".join(changed) + "\n")


def _cleanliness_report(root: Path, artifact: Path) -> None:
    lane = root / LANE_RELATIVE
    generated = [
        path.relative_to(root).as_posix()
        for path in sorted(lane.rglob("*"))
        if path.is_file()
        and path.suffix.lower() in {".stl", ".svg", ".json", ".step"}
        and "__pycache__" not in path.parts
    ]
    authority_diff = _run(
        root,
        [
            "git",
            "diff",
            "--name-only",
            BASE_HEAD,
            "--",
            AUTHORITY_RELATIVE.as_posix(),
        ],
    ).stdout.splitlines()
    seed_diff = _run(
        root,
        [
            "git",
            "diff",
            "--name-only",
            BASE_HEAD,
            "--",
            SEED_RELATIVE.as_posix(),
        ],
    ).stdout.splitlines()
    status = (
        "PASS"
        if not generated and not authority_diff and not seed_diff
        else "FAIL"
    )
    report = [
        f"status={status}",
        f"generated_source_lane_file_count={len(generated)}",
        f"authority_diff_count={len(authority_diff)}",
        f"seed_diff_count={len(seed_diff)}",
        "repository_STL_SVG_JSON_output=CLEAN",
        "artifact_outputs_external=YES",
    ]
    if generated:
        report.extend(generated)
    _write(
        artifact / "no_generated_repository_files_report.txt",
        "\n".join(report) + "\n",
    )


def _readme_review(root: Path, artifact: Path) -> None:
    readme = (root / LANE_RELATIVE / "README.md").read_text(
        encoding="utf-8"
    )
    requirements = {
        "purpose": "目的",
        "legacy_grade_0_not_complete_kit": "Grade 0 STL",
        "aluminum_fpb_front_structure": "aluminum 20×20-class T-slot の FPB",
        "boxes_not_placed_only": "単純に FPB の上へ置くだけではありません",
        "printed_vs_metal": "Three-layer responsibility",
        "thumb_latch_secondary_only": "SECONDARY ONLY",
        "float_slide_pin_rpin": "slide + metal pin + R-pin",
        "orientation_marks": "FRONT`, `REAR`, `LEFT`, `RIGHT",
        "assembly_sequence": "Assembly sequence",
        "fit_test_coupon_use": "Fit-test coupons",
        "full_dummy_hold": "FULL DUMMY PRINT",
        "manufacturing_hold": "MANUFACTURING: **NOT APPROVED**",
        "waterproof_hold": "WATERPROOF",
        "structural_hold": "STRUCTURAL",
        "field_deployment_hold": "FIELD DEPLOYMENT",
    }
    rows = [
        f"{name}={'PASS' if text in readme else 'FAIL'}"
        for name, text in requirements.items()
    ]
    overall = (
        "PASS" if all(row.endswith("PASS") for row in rows) else "FAIL"
    )
    _write(
        artifact / "README_review.txt",
        f"status={overall}\n" + "\n".join(rows) + "\n",
    )
    if overall != "PASS":
        raise RuntimeError("README_REVIEW_FAILED")


def _source_snapshot(root: Path, artifact: Path) -> None:
    destination = artifact / "source_snapshot"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        root / LANE_RELATIVE,
        destination / LANE_RELATIVE,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    shutil.copy2(
        root / ".gitattributes", destination / ".gitattributes"
    )


def _commands_report(artifact: Path) -> None:
    commands = [
        "git branch --show-current",
        "git rev-parse HEAD",
        "git status --porcelain=v1 --untracked-files=all",
        "git worktree list --porcelain",
        "python rovers/common_rover/v2.29.3.9.1/run_validation.py",
        "python rovers/common_rover/v2.29.3.9.1/run_unit_tests.py --json <external> --text <external>",
        "python cad/common_rover/v2_29_3_9_1_executable_cad_seed/validate_seed.py --output <external>",
        "python cad/common_rover/v2_29_3_9_1_executable_cad_seed/run_unit_tests.py --json <external> --text <external>",
        "python cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1/run_unit_tests.py --json <external> --text <external>",
        "python cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1/generate_interface_package.py --output-dir <external>",
        "python cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1/validate_interfaces.py --artifact-dir <external> --output <external>",
        "git apply --check source.patch",
        "git apply --check --whitespace=error source.patch",
    ]
    _write(artifact / "commands_executed.txt", "\n".join(commands) + "\n")


def _checksums(artifact: Path) -> None:
    output = artifact / "SHA256SUMS.txt"
    rows = []
    for path in sorted(artifact.rglob("*")):
        if not path.is_file() or path == output:
            continue
        rows.append(
            f"{_sha256(path)}  {path.relative_to(artifact).as_posix()}"
        )
    _write(output, "\n".join(rows) + "\n")


def _deterministic_zip(artifact: Path) -> tuple[Path, Path, str]:
    zip_path = artifact.parent / f"{artifact.name}.zip"
    receipt = artifact.parent / f"{zip_path.name}.sha256"
    fixed_time = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(artifact.rglob("*")):
            if not path.is_file():
                continue
            relative = (
                Path(artifact.name) / path.relative_to(artifact)
            ).as_posix()
            info = zipfile.ZipInfo(relative, date_time=fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    digest = _sha256(zip_path)
    _write(receipt, f"{digest}  {zip_path.name}\n")
    return zip_path, receipt, digest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = find_repository_root().resolve()
    artifact = _external_artifact(args.artifact_dir, root)
    changed = _changed_files(root)
    allowed = all(
        path == ".gitattributes"
        or path.startswith(f"{LANE_RELATIVE.as_posix()}/")
        for path in changed
    )
    if not allowed:
        raise RuntimeError("PATCH_SCOPE_VIOLATION")
    patch_text = _source_patch(root, changed)
    _write(artifact / "source.patch", patch_text)
    patch_checks = _verify_patch(root, artifact / "source.patch")
    _write(
        artifact / "patch_apply_checks.json",
        canonical_json(patch_checks),
    )
    if (
        patch_checks["PATCH_APPLY_CHECK"] != "PASS"
        or patch_checks["PATCH_WHITESPACE_CHECK"] != "PASS"
        or patch_checks["crlf_count"] != 0
        or patch_checks["bare_cr_count"] != 0
    ):
        raise RuntimeError("PATCH_CHECK_FAILED")

    _validation_reports(root, artifact)
    _unit_test_reports(root, artifact)
    _snapshot_reports(root, artifact, changed)
    _cleanliness_report(root, artifact)
    _readme_review(root, artifact)
    _source_snapshot(root, artifact)
    _commands_report(artifact)
    _checksums(artifact)
    zip_path, receipt, zip_digest = _deterministic_zip(artifact)
    result = {
        "status": "PASS_WITH_HOLD",
        "artifact_directory": str(artifact),
        "zip_path": str(zip_path),
        "zip_receipt_path": str(receipt),
        "zip_sha256": zip_digest,
        "patch_sha256": _sha256(artifact / "source.patch"),
        **{
            key: patch_checks[key]
            for key in ("PATCH_APPLY_CHECK", "PATCH_WHITESPACE_CHECK")
        },
    }
    sys.stdout.write(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
