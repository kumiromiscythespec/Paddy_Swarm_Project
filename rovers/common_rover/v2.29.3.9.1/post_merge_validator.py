from __future__ import annotations

import hashlib
import json
from pathlib import Path
from branch_probe import declare, hit

declare(
    "manifest_exists", "manifest_missing", "manifest_relative", "manifest_bad_lookup",
    "manifest_paths_complete", "manifest_paths_missing", "forbidden_clear", "forbidden_present",
    "source_hash_match", "source_hash_mismatch", "root_pointer_ok", "root_pointer_bad",
    "secondary_pointer_ok", "secondary_pointer_bad", "release_ok", "release_bad",
    "post_apply_exit_ok", "post_apply_exit_bad",
)


def tree_hash(root, exclude=()):
    root = Path(root)
    exclude = set(exclude)
    lines = []
    paths = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in paths:
        rel = path.relative_to(root).as_posix()
        if (
            rel in exclude
            or "__pycache__" in path.parts
            or path.suffix.lower() in {".pyc", ".pyo", ".tmp", ".bak"}
            or path.name == ".DS_Store"
        ):
            continue
        file_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{file_sha}  {rel}\n")
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def manifest_exists(manifest_path):
    return Path(manifest_path).exists()


def forbidden_path_present(paths, prefixes):
    return any(path.startswith(prefix) for path in paths for prefix in prefixes)


def root_text_valid(text, expected_version):
    valid = (
        f"Current authority: **{expected_version}**" in text
        and "GITHUB_EXECUTABLE_CAD_RELEASE = HOLD" in text
        and "GITHUB_MANUFACTURING_RELEASE = HOLD" in text
    )
    return valid


def post_apply_exit_ok(exit_code):
    if exit_code == 0:
        hit("post_apply_exit_ok")
        return True
    hit("post_apply_exit_bad")
    return False


def validate_manifest(lane):
    lane = Path(lane)
    path = lane / "candidate_patch_manifest.json"
    blockers = []
    if not manifest_exists(path):
        hit("manifest_missing")
        return {"status": "FAIL", "blockers": ["CANDIDATE_PATCH_MANIFEST_MISSING"]}
    hit("manifest_exists")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("manifest_lookup") == "Path(__file__).resolve().parent/candidate_patch_manifest.json":
        hit("manifest_relative")
    else:
        hit("manifest_bad_lookup")
        blockers.append("MANIFEST_LOOKUP_NOT_LANE_RELATIVE")
    if manifest.get("validation_entry_point") != "rovers/common_rover/v2.29.3.9.1/run_validation.py":
        blockers.append("VALIDATION_ENTRY_POINT_MISMATCH")
    if manifest.get("expected_current_authority_pointer") != "v2.29.3.9.1":
        blockers.append("MANIFEST_CURRENT_POINTER_MISMATCH")
    required_lane = {
        "candidate_patch_manifest.json", "cross_registry_validator.py",
        "post_merge_validator.py", "run_validation.py", "tests/__init__.py",
        "fastener_boundary_authority.json", "slot_zone_authority.json",
        "slot_cross_registry_mapping.json",
    }
    listed = set(manifest.get("expected_version_lane_files", []))
    missing = required_lane - listed
    if missing:
        hit("manifest_paths_missing")
        blockers.append("MANIFEST_REQUIRED_FILE_MISSING")
    else:
        hit("manifest_paths_complete")
    required_prefixes = {
        "cad/dummy_panicle_v0_1/", "interfaces/", "result_bundle.zip",
        "package_receipt.json", "__pycache__/", "*.pyc", "*.step", "*.stl",
    }
    prefixes = set(manifest.get("forbidden_path_prefixes", []))
    if not required_prefixes <= prefixes:
        blockers.append("MANIFEST_FORBIDDEN_PREFIX_MISSING")
    all_paths = (
        manifest.get("expected_root_files", [])
        + manifest.get("expected_docs_files", [])
        + [f"rovers/common_rover/v2.29.3.9.1/{p}" for p in listed]
    )
    if forbidden_path_present(all_paths, ["cad/dummy_panicle_v0_1/", "interfaces/"]):
        hit("forbidden_present")
        blockers.append("UNRELATED_FILE_IN_PATCH")
    else:
        hit("forbidden_clear")
    text = path.read_text(encoding="utf-8")
    if "D:\\\\Paddy_Swarm_Project_work" in text or "D:/Paddy_Swarm_Project_work" in text:
        blockers.append("MANIFEST_ARTIFACT_ABSOLUTE_DEPENDENCY")
    expected_hash_contract = {
        "source_tree_hash_format_version": "PADDY_SOURCE_TREE_SHA256_V1",
        "source_tree_hash_root": "VERSION_LANE_ROOT",
        "source_tree_hash_algorithm": "SHA256_OF_SORTED_FILE_SHA256_AND_POSIX_PATH_LINES",
        "source_tree_hash_line_format": "<file_sha256>  <posix_relative_path>\\n",
    }
    if any(manifest.get(key) != value for key, value in expected_hash_contract.items()):
        blockers.append("MANIFEST_TREE_HASH_CONTRACT_MISMATCH")
    expected_exclusions = {
        "candidate_patch_manifest.json", "__pycache__/**", "**/*.pyc",
        "**/*.pyo", "**/*.tmp", "**/*.bak", "**/.DS_Store",
    }
    if set(manifest.get("source_tree_hash_exclusions", [])) != expected_exclusions:
        blockers.append("MANIFEST_TREE_HASH_EXCLUSION_MISMATCH")
    actual_hash = tree_hash(lane, exclude={"candidate_patch_manifest.json"})
    if actual_hash == manifest.get("source_tree_sha256"):
        hit("source_hash_match")
    else:
        hit("source_hash_mismatch")
        blockers.append("MANIFEST_SOURCE_TREE_HASH_MISMATCH")
    return {"status": "PASS" if not blockers else "FAIL", "manifest": manifest, "blockers": blockers}


def validate_pointers_and_holds(lane, holds):
    lane = Path(lane)
    repo_root = lane.parents[2]
    root_path = repo_root / "CURRENT_COMMON_ROVER_AUTHORITY.md"
    secondary_path = repo_root / "rovers" / "common_rover" / "CURRENT_COMMON_ROVER_AUTHORITY.md"
    blockers = []
    root_text = root_path.read_text(encoding="utf-8") if root_path.exists() else ""
    secondary_text = secondary_path.read_text(encoding="utf-8") if secondary_path.exists() else ""
    if root_text_valid(root_text, "v2.29.3.9.1") and "v2.29.3.9.1 > v2.29.3.9 > v2.29.3.8" in root_text:
        hit("root_pointer_ok")
    else:
        hit("root_pointer_bad")
        blockers.append("ROOT_POINTER_MISMATCH")
    if root_text_valid(secondary_text, "v2.29.3.9.1") and "v2.29.3.9.1 > v2.29.3.9 > v2.29.3.8" in secondary_text:
        hit("secondary_pointer_ok")
    else:
        hit("secondary_pointer_bad")
        blockers.append("SECONDARY_POINTER_MISMATCH")
    expected = {
        "GITHUB_EXECUTABLE_CAD_RELEASE": "HOLD",
        "GITHUB_MANUFACTURING_RELEASE": "HOLD",
        "MANUFACTURING_STATUS": "NOT_APPROVED",
        "PURCHASE_STATUS": "NOT_APPROVED",
        "FIELD_DEPLOYMENT_STATUS": "NOT_APPROVED",
        "WATERPROOF_STATUS": "NOT_VALIDATED",
        "ELECTRICAL_SAFETY_STATUS": "NOT_VALIDATED",
        "THERMAL_STATUS": "NOT_VALIDATED",
        "STRUCTURAL_STRENGTH_STATUS": "NOT_VALIDATED",
    }
    mismatch = [k for k, v in expected.items() if holds.get(k) != v]
    if mismatch:
        hit("release_bad")
        blockers.append("RELEASE_HOLD_MISMATCH")
    else:
        hit("release_ok")
    return {"status": "PASS" if not blockers else "FAIL", "blockers": blockers}
