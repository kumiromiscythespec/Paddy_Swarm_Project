from __future__ import annotations

from copy import deepcopy
from typing import Any


ROLE_CANDIDATES = {
    "PROFILE-01": (
        "FPB left rail",
        "FPB right rail",
        "front crossmember",
        "light secondary crossmember",
        "dimensional fit reference",
    ),
    "PROFILE-02": (
        "independent BBOX longitudinal support",
        "lower-frame longitudinal member",
        "high-stiffness crossmember",
        "battery support candidate",
        "front-to-rear structural tie candidate",
    ),
}

UNRESOLVED_ROLE_INPUTS = (
    "final placement",
    "20x40 section 40 mm direction",
    "20x40 vertical or horizontal orientation",
    "left/right symmetric placement",
    "required cut length",
    "frame connection method",
    "rover overall width",
    "BBOX support height",
    "PTO interference",
    "motor-pod interference",
    "float interference",
)


def build_role_matrix() -> dict[str, Any]:
    rows = []
    for profile_id, roles in ROLE_CANDIDATES.items():
        for role in roles:
            rows.append(
                {
                    "profile_id": profile_id,
                    "candidate_role": role,
                    "role_status": "CANDIDATE_ONLY",
                    "final_role": "",
                    "orientation_status": "HOLD_UNRESOLVED",
                    "cut_length_status": "HOLD_UNRESOLVED",
                    "interference_status": "HOLD_UNRESOLVED",
                    "production_geometry_gate": "HOLD",
                }
            )
    return {
        "schema": "PS_PROFILE_ROLE_CANDIDATE_MATRIX_V0_1",
        "rows": rows,
        "unresolved_role_inputs": list(UNRESOLVED_ROLE_INPUTS),
        "profile_02_orientation_automatically_selected": False,
        "status": "HOLD",
    }


def validate_role_matrix(matrix: dict[str, Any]) -> None:
    expected = {
        (profile_id, role)
        for profile_id, roles in ROLE_CANDIDATES.items()
        for role in roles
    }
    actual = {
        (row.get("profile_id"), row.get("candidate_role"))
        for row in matrix.get("rows", [])
    }
    if actual != expected:
        raise ValueError("ROLE_CANDIDATE_MATRIX_MISMATCH")
    for row in matrix["rows"]:
        if row["role_status"] != "CANDIDATE_ONLY" or row["final_role"]:
            raise ValueError("ROLE_CANDIDATE_IMPROPERLY_PROMOTED")
        if row["orientation_status"] != "HOLD_UNRESOLVED":
            raise ValueError("PROFILE_ORIENTATION_AUTOMATICALLY_SELECTED")
        if row["production_geometry_gate"] != "HOLD":
            raise ValueError("ROLE_MATRIX_RELEASED_PRODUCTION_GEOMETRY")
    if matrix.get("profile_02_orientation_automatically_selected") is not False:
        raise ValueError("PROFILE_02_ORIENTATION_AUTO_SELECTION_FORBIDDEN")


def promote_candidate_role(
    matrix: dict[str, Any],
    *,
    profile_id: str,
    candidate_role: str,
    approval_evidence: str | None = None,
) -> dict[str, Any]:
    del matrix, profile_id, candidate_role
    if not approval_evidence:
        raise ValueError("ROLE_PROMOTION_REQUIRES_SEPARATE_APPROVAL")
    raise ValueError("ROLE_PROMOTION_OUTSIDE_REGISTRATION_SCOPE")


def set_profile_02_orientation(
    matrix: dict[str, Any],
    orientation: str,
    *,
    measured_clearance_evidence: str | None = None,
) -> dict[str, Any]:
    del matrix, orientation
    if not measured_clearance_evidence:
        raise ValueError(
            "PROFILE_02_ORIENTATION_REQUIRES_MEASURED_CLEARANCE_EVIDENCE"
        )
    raise ValueError("ORIENTATION_SELECTION_OUTSIDE_REGISTRATION_SCOPE")


def copy_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(matrix)

