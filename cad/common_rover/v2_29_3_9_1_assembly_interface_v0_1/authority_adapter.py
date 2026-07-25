from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any


LANE_RELATIVE = Path(
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
        ).is_file() and (parent / SEED_RELATIVE / "authority_loader.py").is_file():
            return parent
    raise RuntimeError("REPOSITORY_ROOT_NOT_FOUND")


REPOSITORY_ROOT = find_repository_root()
for import_path in (
    REPOSITORY_ROOT / SEED_RELATIVE,
    REPOSITORY_ROOT / AUTHORITY_RELATIVE,
):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from authority_loader import COMPONENT_IDS, AuthorityParameters, load_authority
from post_merge_validator import tree_hash
from solid_builders import build_minimum_assembly
from validation import validate_seed


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(data: Any) -> str:
    return (
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )


@dataclass(frozen=True)
class AuthorityContext:
    repository_root: Path
    parameters: AuthorityParameters
    coordinate: dict
    frame: dict
    front_crossmember: dict
    fixed_body: dict
    width: dict
    slot_zones: dict
    holds: dict
    authority_tree_expected_sha256: str
    authority_tree_actual_sha256: str
    authority_tree_algorithm: str
    seed_report: dict

    @property
    def zone_by_id(self) -> dict[str, dict]:
        return {
            row["zone_id"]: row
            for row in self.slot_zones["zones"]
        }


def load_context(
    repository_root: Path | None = None,
    *,
    validate_seed_geometry: bool = True,
) -> AuthorityContext:
    root = (repository_root or REPOSITORY_ROOT).resolve()
    lane = root / AUTHORITY_RELATIVE
    parameters = load_authority(root)
    manifest = _load(lane / "candidate_patch_manifest.json")
    actual_tree = tree_hash(
        lane, exclude={"candidate_patch_manifest.json"}
    )
    if validate_seed_geometry:
        seed_report = validate_seed(
            parameters=parameters,
            include_step_roundtrip=False,
            solids_override=build_minimum_assembly(parameters),
        )
    else:
        seed_report = {
            "EXECUTABLE_CAD_SEED_STATUS": "NOT_RUN",
            "required_solid_ids": list(COMPONENT_IDS),
        }
    return AuthorityContext(
        repository_root=root,
        parameters=parameters,
        coordinate=_load(lane / "coordinate_authority.json"),
        frame=_load(lane / "body_frame_authority.json"),
        front_crossmember=_load(lane / "front_crossmember_authority.json"),
        fixed_body=_load(lane / "fixed_body_dimension_authority.json"),
        width=_load(lane / "operational_width_contract.json"),
        slot_zones=_load(lane / "slot_zone_authority.json"),
        holds=_load(lane / "known_hold_registry.json"),
        authority_tree_expected_sha256=manifest["source_tree_sha256"],
        authority_tree_actual_sha256=actual_tree,
        authority_tree_algorithm=manifest[
            "source_tree_hash_algorithm"
        ],
        seed_report=seed_report,
    )


def authority_sources(context: AuthorityContext) -> list[str]:
    return [
        record.relative_path
        for record in context.parameters.source_records
    ] + [
        (AUTHORITY_RELATIVE / "slot_zone_authority.json").as_posix(),
        (AUTHORITY_RELATIVE / "front_crossmember_authority.json").as_posix(),
    ]
