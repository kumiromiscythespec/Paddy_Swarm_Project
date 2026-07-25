from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


LANE_RELATIVE = Path(
    "cad/common_rover/v2_29_3_9_1_progressive_full_scale_dummy_v0_1"
)
ASSEMBLY_INTERFACE_RELATIVE = Path(
    "cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1"
)
SEED_RELATIVE = Path("cad/common_rover/v2_29_3_9_1_executable_cad_seed")
AUTHORITY_RELATIVE = Path("rovers/common_rover/v2.29.3.9.1")


def find_repository_root(start: Path | None = None) -> Path:
    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        if (
            parent / AUTHORITY_RELATIVE / "candidate_patch_manifest.json"
        ).is_file() and (
            parent / ASSEMBLY_INTERFACE_RELATIVE / "authority_adapter.py"
        ).is_file():
            return parent
    raise RuntimeError("REPOSITORY_ROOT_NOT_FOUND")


REPOSITORY_ROOT = find_repository_root()
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

# Reuse the existing corrected Assembly Interface v0.1 authority adapter.
from cad.common_rover.v2_29_3_9_1_assembly_interface_v0_1.authority_adapter import (  # noqa: E402
    AuthorityContext,
    canonical_json,
    load_context as load_assembly_interface_context,
)


def load_context(
    repository_root: Path | None = None,
    *,
    validate_seed_geometry: bool = True,
) -> AuthorityContext:
    return load_assembly_interface_context(
        repository_root or REPOSITORY_ROOT,
        validate_seed_geometry=validate_seed_geometry,
    )


def controlled_dimensions(context: AuthorityContext) -> dict[str, Any]:
    """Return authority-owned values without creating independent constants."""

    fixed = context.fixed_body
    frame = context.frame
    cross = context.front_crossmember
    width = context.width
    zones = context.zone_by_id
    return {
        "coordinate": {
            "X": context.coordinate["axes"]["X"],
            "Y": context.coordinate["axes"]["Y"],
            "Z": context.coordinate["axes"]["Z"],
        },
        "body_mm": fixed["current_dimensions"],
        "core_arrangement": fixed["core_arrangement"],
        "core_length_mm": fixed["core_length_mm"],
        "rail_centerlines_x_mm": frame["rail_centerlines_x_mm"],
        "rail_length_mm": frame["rail_length_mm"],
        "profile_section_mm": frame["section_mm"],
        "bare_frame_width_mm": frame["bare_frame_union"]["width_mm"],
        "front_crossmember_envelope_mm": {
            "X": cross["length_mm"],
            "Y": cross["section_mm"]["Y"],
            "Z": cross["section_mm"]["Z"],
        },
        "registered_width_mm": width["candidate_target_max_mm"],
        "hard_limit_width_mm": width["hard_limit_mm"],
        "preferred_width_mm": width["preferred_max_mm"],
        "lower_adapter_left": zones["LOWER-ADAPTER-L"],
        "lower_adapter_right": zones["LOWER-ADAPTER-R"],
        "upper_torque_mount": zones["UPPER-TORQUE-MOUNT"],
        "output_bridge_left": zones["OUTPUT-BRIDGE-L"],
        "output_bridge_right": zones["OUTPUT-BRIDGE-R"],
        "front_joint_reserved_interval_y_mm": context.slot_zones[
            "front_joint_reserved_interval_y_mm"
        ],
        "direct_rail_hole_policy": frame["direct_rail_hole_policy"],
    }


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_tree_hash(directory: Path) -> str:
    """Hash relative path, NUL, bytes, NUL for every source file."""

    digest = hashlib.sha256()
    for path in sorted(
        item for item in directory.rglob("*") if item.is_file()
    ):
        relative = path.relative_to(directory).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def source_integrity_report(
    context: AuthorityContext | None = None,
) -> dict[str, Any]:
    ctx = context or load_context(validate_seed_geometry=True)
    ai_lane = REPOSITORY_ROOT / ASSEMBLY_INTERFACE_RELATIVE
    seed_lane = REPOSITORY_ROOT / SEED_RELATIVE
    return {
        "schema": "PS_PROGRESSIVE_DUMMY_SOURCE_INTEGRITY_V0_1",
        "authority_tree_expected_sha256": (
            ctx.authority_tree_expected_sha256
        ),
        "authority_tree_actual_sha256": ctx.authority_tree_actual_sha256,
        "authority_tree_match": (
            ctx.authority_tree_expected_sha256
            == ctx.authority_tree_actual_sha256
        ),
        "seed_status": ctx.seed_report.get("EXECUTABLE_CAD_SEED_STATUS"),
        "assembly_interface_source_tree_sha256": source_tree_hash(ai_lane),
        "seed_source_tree_sha256": source_tree_hash(seed_lane),
        "assembly_interface_import_reused": True,
        "assembly_interface_adapter_path": (
            ASSEMBLY_INTERFACE_RELATIVE / "authority_adapter.py"
        ).as_posix(),
        "authority_manifest_sha256": _hash_file(
            REPOSITORY_ROOT
            / AUTHORITY_RELATIVE
            / "candidate_patch_manifest.json"
        ),
    }


def profile_input_audit(context: AuthorityContext | None = None) -> dict:
    ctx = context or load_context(validate_seed_geometry=False)
    profile_source = ctx.repository_root / AUTHORITY_RELATIVE / (
        "tslot_profile_authority.json"
    )
    data = json.loads(profile_source.read_text(encoding="utf-8"))
    required = (
        "slot_opening_mm",
        "slot_depth_mm",
        "corner_radius_mm",
        "center_bore_mm",
        "compatible_t_nut",
        "outer_dimension_tolerance_mm",
    )
    missing = [field for field in required if field not in data]
    return {
        "schema": "PS_PROFILE_INPUT_AUDIT_V0_1",
        "source": profile_source.relative_to(ctx.repository_root).as_posix(),
        "profile_class": data["profile_class"],
        "required_supplier_fields": list(required),
        "missing_supplier_fields": missing,
        "profile_1_supplier_neutral_split_clamp": (
            "POSSIBLE_AFTER_OUTER_TOLERANCE_MEASUREMENT"
        ),
        "profile_2_slot_mount": "HOLD_UNTIL_PROFILE_SELECTED",
        "profile_3_envelope_dummy": "SELECTED_DUMMY_ONLY",
        "selected_option": "PROFILE-3",
        "status": "DUMMY_ENVELOPE_ONLY",
        "prohibitions": [
            "NO_INFERRED_SLOT_GEOMETRY",
            "NO_STRUCTURAL_TEST",
            "NO_DIRECT_RAIL_HOLES",
        ],
    }


def rear_support_input_audit() -> dict:
    unresolved = [
        "rear_bridge_hardpoints",
        "cradle_section",
        "frame_tie",
        "clamp_geometry",
        "stiffness",
        "implement_clearance",
    ]
    return {
        "schema": "PS_REAR_BBOX_SUPPORT_AUDIT_V0_1",
        "unresolved_fields": unresolved,
        "selected_representation": (
            "INDEPENDENT_FRONT_REAR_VISUAL_SUPPORTS"
        ),
        "geometry_classification": "DUMMY_ONLY_NO_LOAD_NOT_STRUCTURAL",
        "structural_claim": False,
        "bbox_supported_only_by_cbox": False,
        "status": "PASS_WITH_HOLD",
    }


def validate_rear_support_audit(audit: dict) -> None:
    if not audit.get("unresolved_fields"):
        raise ValueError("UNRESOLVED_STRUCTURAL_DIMENSION_SILENTLY_FIXED")
    if audit.get("structural_claim") is not False:
        raise ValueError("UNRESOLVED_REAR_SUPPORT_STRUCTURAL_CLAIM")
    classification = str(audit.get("geometry_classification", ""))
    for required in ("DUMMY_ONLY", "NO_LOAD", "NOT_STRUCTURAL"):
        if required not in classification:
            raise ValueError(f"REAR_SUPPORT_MARKING_MISSING:{required}")
