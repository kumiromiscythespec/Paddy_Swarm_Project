from __future__ import annotations

from dataclasses import asdict
from itertools import combinations
import json
import math
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

from authority_loader import (
    COMPONENT_IDS,
    INTERSECTION_VOLUME_TOLERANCE_MM3,
    LINEAR_TOLERANCE_MM,
    AuthorityError,
    AuthorityParameters,
    Envelope,
    load_authority,
)
from inspectors import (
    bounding_box,
    classify_envelope_relation,
    inspect_all_solids,
    inspect_mirror,
    inspect_pair,
    union_bounds,
)
from solid_builders import (
    SIMPLIFIED_TSLOT_AUTHORITY_ENVELOPE,
    build_minimum_assembly,
    require_cadquery,
)


IDS = {
    "left": "V22939-FPB-RAIL-L",
    "right": "V22939-FPB-RAIL-R",
    "cross": "V22939-FPB-FRONT-XMEMBER",
    "cbox": "V22939-CBOX",
    "bbox": "V22939-BBOX",
    "battery": "V22939-BATTERY-CASSETTE",
}
REQUIRED_SOLID_IDS = COMPONENT_IDS
TOTAL_POSSIBLE_PAIR_COUNT = 15


def _pair_key(first_id: str, second_id: str) -> frozenset[str]:
    return frozenset((first_id, second_id))


def build_pair_policy() -> list[dict]:
    semantic_policy = {
        _pair_key(IDS["left"], IDS["right"]): "EXPECTED_SEPARATION",
        _pair_key(IDS["left"], IDS["cross"]): "INTENDED_FACE_CONTACT",
        _pair_key(IDS["right"], IDS["cross"]): "INTENDED_FACE_CONTACT",
        _pair_key(IDS["cbox"], IDS["bbox"]): "INTENDED_FACE_CONTACT",
        _pair_key(IDS["bbox"], IDS["battery"]): "INTENDED_CONTAINMENT",
    }
    boolean_pairs = {
        _pair_key(IDS["left"], IDS["right"]),
        _pair_key(IDS["left"], IDS["cross"]),
        _pair_key(IDS["right"], IDS["cross"]),
        _pair_key(IDS["cbox"], IDS["bbox"]),
    }
    containment_pair = _pair_key(IDS["bbox"], IDS["battery"])
    rows: list[dict] = []
    for first_id, second_id in combinations(REQUIRED_SOLID_IDS, 2):
        key = _pair_key(first_id, second_id)
        relation_policy = semantic_policy.get(
            key, "NOT_AUTHORIZED_FOR_RELATION_ASSERTION"
        )
        if key in boolean_pairs:
            inspection_scope = "BOOLEAN_CHECKED"
        elif key == containment_pair:
            inspection_scope = "ENVELOPE_ONLY_CHECKED"
        else:
            inspection_scope = "NOT_AUTHORIZED_FOR_RELATION_ASSERTION"
        rows.append(
            {
                "first": first_id,
                "second": second_id,
                "relation_policy": relation_policy,
                "inspection_scope": inspection_scope,
                "boolean_checked": key in boolean_pairs,
                "envelope_checked": key in boolean_pairs
                or key == containment_pair,
            }
        )
    return rows


def _authority_failure_report(
    blockers: Sequence[str],
    linear_tolerance_mm: float = LINEAR_TOLERANCE_MM,
    intersection_volume_tolerance_mm3: float = (
        INTERSECTION_VOLUME_TOLERANCE_MM3
    ),
) -> dict:
    return {
        "schema": "PS_COMMON_ROVER_V229391_EXECUTABLE_CAD_SEED_REPORT_V3",
        "source_version": "v2.29.3.9.1",
        "tolerances": {
            "linear_tolerance_mm": linear_tolerance_mm,
            "intersection_volume_tolerance_mm3":
                intersection_volume_tolerance_mm3,
        },
        "authority_record_uniqueness": {
            "required_component_ids": list(IDS.values()),
            "status": "FAIL",
        },
        "actual_solid_list": [],
        "required_solid_ids": list(REQUIRED_SOLID_IDS),
        "actual_solid_ids": [],
        "missing_solid_ids": list(REQUIRED_SOLID_IDS),
        "extra_solid_ids": [],
        "required_solid_count": len(REQUIRED_SOLID_IDS),
        "actual_solid_count": 0,
        "solid_id_set_status": "NOT_RUN_AUTHORITY_FAILURE",
        "solid_validation": [],
        "pair_validation": [],
        "battery_cassette": {
            "placement_status": "HOLD",
            "placement_source": None,
            "guessed_values_used": False,
        },
        "blockers": sorted(set(blockers)),
        "unresolved_holds": [
            "GITHUB_EXECUTABLE_CAD_RELEASE=HOLD",
            "GITHUB_MANUFACTURING_RELEASE=HOLD",
            "MANUFACTURING_STATUS=NOT_APPROVED",
            "PURCHASE_STATUS=NOT_APPROVED",
            "FIELD_DEPLOYMENT_STATUS=NOT_APPROVED",
            "WATERPROOF_STATUS=NOT_VALIDATED",
            "STRUCTURAL_STRENGTH_STATUS=NOT_VALIDATED",
        ],
        "DESIGN_ANALYSIS_PROCESS": "FAIL",
        "EXECUTABLE_CAD_SEED_STATUS": "FAIL",
        "SOURCE_REVIEW_CORRECTION_STATUS": "FAIL",
        "FINAL_CONTRACT_CORRECTION_STATUS": "FAIL",
        "COMMIT_READINESS": "HOLD",
        "GITHUB_EXECUTABLE_CAD_RELEASE": "HOLD",
        "GITHUB_MANUFACTURING_RELEASE": "HOLD",
        "MANUFACTURING_STATUS": "NOT_APPROVED",
        "PURCHASE_STATUS": "NOT_APPROVED",
        "FIELD_DEPLOYMENT_STATUS": "NOT_APPROVED",
        "WATERPROOF_STATUS": "NOT_VALIDATED",
        "STRUCTURAL_STRENGTH_STATUS": "NOT_VALIDATED",
    }


def _close(first: float, second: float, tolerance: float) -> bool:
    return math.isclose(first, second, abs_tol=tolerance, rel_tol=0.0)


def _same_envelope(
    first: Envelope, second: Envelope, tolerance: float
) -> bool:
    return all(
        _close(a, b, tolerance)
        for a, b in zip((*first.minimum, *first.maximum), (*second.minimum, *second.maximum))
    )


def validate_parameters(
    candidate: AuthorityParameters,
    reference: AuthorityParameters,
) -> list[str]:
    tolerance = reference.linear_tolerance_mm
    blockers: list[str] = []
    for envelope in candidate.components:
        values = (*envelope.minimum, *envelope.maximum)
        if not all(math.isfinite(value) for value in values):
            blockers.append(f"{envelope.component_id}:NONFINITE_PARAMETER")
            continue
        if any(value <= 0.0 for value in envelope.dimensions):
            blockers.append(f"{envelope.component_id}:NONPOSITIVE_DIMENSION")
    for key, component_id in IDS.items():
        candidate_envelope = candidate.component(component_id)
        reference_envelope = reference.component(component_id)
        if not _same_envelope(candidate_envelope, reference_envelope, tolerance):
            blockers.append(f"{key.upper()}_ENVELOPE_MISMATCH")
    left = candidate.component(IDS["left"])
    right = candidate.component(IDS["right"])
    cross = candidate.component(IDS["cross"])
    if not _close(left.center[0], 79.0, tolerance):
        blockers.append("LEFT_RAIL_CENTER_X_MISMATCH")
    if not _close(right.center[0], -79.0, tolerance):
        blockers.append("RIGHT_RAIL_CENTER_X_MISMATCH")
    if not _close(left.dimensions[0], 20.0, tolerance):
        blockers.append("LEFT_RAIL_WIDTH_MISMATCH")
    if not _close(right.dimensions[0], 20.0, tolerance):
        blockers.append("RIGHT_RAIL_WIDTH_MISMATCH")
    if not _close(
        left.minimum[1], candidate.front_datum_y_mm, tolerance
    ) or not _close(right.minimum[1], candidate.front_datum_y_mm, tolerance):
        blockers.append("FRONT_DATUM_MISMATCH")
    if not _close(cross.dimensions[0], 138.0, tolerance):
        blockers.append("CROSSMEMBER_LENGTH_MISMATCH")
    if not _close(candidate.core_length_mm, reference.core_length_mm, tolerance):
        blockers.append("CORE_LENGTH_MISMATCH")
    if not _close(
        candidate.bare_frame_width_mm,
        reference.bare_frame_width_mm,
        tolerance,
    ):
        blockers.append("BARE_FRAME_WIDTH_AUTHORITY_MISMATCH")
    if not _close(
        candidate.rail_center_separation_mm,
        reference.rail_center_separation_mm,
        tolerance,
    ):
        blockers.append("RAIL_CENTER_SEPARATION_AUTHORITY_MISMATCH")
    if not _close(
        candidate.registered_interface_width_mm,
        reference.registered_interface_width_mm,
        tolerance,
    ):
        blockers.append("REGISTERED_INTERFACE_WIDTH_AUTHORITY_MISMATCH")
    if not _close(
        candidate.operational_hard_limit_mm,
        reference.operational_hard_limit_mm,
        tolerance,
    ):
        blockers.append("OPERATIONAL_HARD_LIMIT_AUTHORITY_MISMATCH")
    if not (
        candidate.bare_frame_width_mm
        < candidate.registered_interface_width_mm
        < candidate.operational_hard_limit_mm
    ):
        blockers.append("WIDTH_CLASS_ORDER_MISMATCH")
    if candidate.linear_tolerance_mm != LINEAR_TOLERANCE_MM:
        blockers.append("LINEAR_TOLERANCE_CONTRACT_MISMATCH")
    if (
        candidate.intersection_volume_tolerance_mm3
        != INTERSECTION_VOLUME_TOLERANCE_MM3
    ):
        blockers.append("INTERSECTION_VOLUME_TOLERANCE_CONTRACT_MISMATCH")
    return sorted(set(blockers))


def _can_build(parameters: AuthorityParameters) -> bool:
    return all(
        all(math.isfinite(value) for value in (*item.minimum, *item.maximum))
        and all(dimension > 0.0 for dimension in item.dimensions)
        for item in parameters.components
    )


def _solid_id_gate(solids: Mapping[str, object]) -> tuple[dict, list[str]]:
    required = set(REQUIRED_SOLID_IDS)
    actual = set(solids)
    missing = sorted(required - actual)
    extra = sorted(actual - required, key=str)
    non_null_ids = sorted(
        (component_id for component_id, shape in solids.items() if shape is not None),
        key=str,
    )
    actual_count = len(non_null_ids)
    blockers = [
        *(f"SOLID_ID_MISSING:{component_id}" for component_id in missing),
        *(f"SOLID_ID_EXTRA:{component_id}" for component_id in extra),
    ]
    if actual_count != len(REQUIRED_SOLID_IDS):
        blockers.append(f"ACTUAL_SOLID_COUNT_MISMATCH:{actual_count}")
    status = "PASS" if not blockers else "FAIL"
    return (
        {
            "required_solid_ids": list(REQUIRED_SOLID_IDS),
            "actual_solid_ids": sorted(actual, key=str),
            "missing_solid_ids": missing,
            "extra_solid_ids": extra,
            "required_solid_count": len(REQUIRED_SOLID_IDS),
            "actual_solid_count": actual_count,
            "non_null_solid_ids": non_null_ids,
            "solid_id_set_status": status,
        },
        blockers,
    )


def _validate_pair_policy(rows: Sequence[Mapping[str, object]]) -> tuple[dict, list[str]]:
    expected_keys = {
        _pair_key(first_id, second_id)
        for first_id, second_id in combinations(REQUIRED_SOLID_IDS, 2)
    }
    actual_keys = [
        _pair_key(str(row.get("first")), str(row.get("second"))) for row in rows
    ]
    blockers: list[str] = []
    if len(rows) != TOTAL_POSSIBLE_PAIR_COUNT:
        blockers.append(f"PAIR_POLICY_COUNT_MISMATCH:{len(rows)}")
    if set(actual_keys) != expected_keys or len(set(actual_keys)) != len(actual_keys):
        blockers.append("PAIR_POLICY_COVERAGE_MISMATCH")
    if [dict(row) for row in rows] != build_pair_policy():
        blockers.append("PAIR_POLICY_CONTRACT_MISMATCH")
    boolean_count = sum(bool(row.get("boolean_checked")) for row in rows)
    envelope_count = sum(bool(row.get("envelope_checked")) for row in rows)
    envelope_only_count = sum(
        row.get("inspection_scope") == "ENVELOPE_ONLY_CHECKED" for row in rows
    )
    containment_count = sum(
        row.get("relation_policy") == "INTENDED_CONTAINMENT" for row in rows
    )
    unchecked_count = sum(
        row.get("inspection_scope") == "NOT_AUTHORIZED_FOR_RELATION_ASSERTION"
        for row in rows
    )
    return (
        {
            "total_possible_pair_count": TOTAL_POSSIBLE_PAIR_COUNT,
            "pair_policy_count": len(rows),
            "boolean_checked_pair_count": boolean_count,
            "envelope_checked_pair_count": envelope_count,
            "envelope_only_checked_pair_count": envelope_only_count,
            "intended_containment_pair_count": containment_count,
            "unchecked_or_unauthorized_pair_count": unchecked_count,
            "policy_matrix": [dict(row) for row in rows],
            "status": "PASS" if not blockers else "FAIL",
        },
        blockers,
    )


def _battery_bbox_containment(
    parameters: AuthorityParameters,
) -> tuple[dict, list[str]]:
    battery = parameters.component(IDS["battery"])
    bbox = parameters.component(IDS["bbox"])
    minimum_margins = tuple(
        battery.minimum[index] - bbox.minimum[index] for index in range(3)
    )
    maximum_margins = tuple(
        bbox.maximum[index] - battery.maximum[index] for index in range(3)
    )
    all_margins = (*minimum_margins, *maximum_margins)
    finite = all(math.isfinite(value) for value in all_margins)
    contained = finite and all(
        value >= -LINEAR_TOLERANCE_MM for value in all_margins
    )
    traceable = all(
        bool(envelope.source_path.strip() and envelope.source_revision.strip())
        for envelope in (battery, bbox)
    ) and any(
        record.relative_path.endswith("/hardware_envelope_registry.json")
        for record in parameters.source_records
    )
    placement_confirmed = (
        parameters.battery_placement_status
        == "PLACED_FROM_HARDWARE_ENVELOPE_REGISTRY"
    )
    blockers: list[str] = []
    if not finite:
        blockers.append("BATTERY_BBOX_CONTAINMENT_MARGIN_NONFINITE")
    if not contained:
        blockers.append("BATTERY_BBOX_CONTAINMENT_MISMATCH")
    if not traceable:
        blockers.append("BATTERY_BBOX_CONTAINMENT_SOURCE_INVALID")
    if not placement_confirmed:
        blockers.append("BATTERY_BBOX_CONTAINMENT_PLACEMENT_UNCONFIRMED")
    return (
        {
            "classification": "INTENDED_CONTAINMENT",
            "container_component_id": bbox.component_id,
            "contained_component_id": battery.component_id,
            "minimum_side_margins_mm": minimum_margins,
            "maximum_side_margins_mm": maximum_margins,
            "margins_finite": finite,
            "contained_within_linear_tolerance": contained,
            "container_record_source": bbox.source_path,
            "container_record_revision": bbox.source_revision,
            "contained_record_source": battery.source_path,
            "contained_record_revision": battery.source_revision,
            "placement_registry_source":
                "rovers/common_rover/v2.29.3.9.1/"
                "hardware_envelope_registry.json",
            "battery_placement_status": parameters.battery_placement_status,
            "authority_source_traceable": traceable,
            "guessed_values_used": False,
            "boolean_overlap_counted_as_unintended": False,
            "status": "PASS" if not blockers else "FAIL",
        },
        blockers,
    )


def temporary_step_roundtrip(
    shape,
    expected_bbox: dict,
    linear_tolerance_mm: float,
    volume_tolerance_mm3: float,
) -> dict:
    result = {
        "verification_only": True,
        "repository_export": False,
        "step_operation_status": "FAIL",
        "step_error_type": None,
        "source_valid": None,
        "source_volume_mm3": None,
        "temporary_step_created": False,
        "temporary_step_size_bytes": None,
        "roundtrip_valid": None,
        "roundtrip_volume_mm3": None,
        "roundtrip_bounding_box_mm": None,
        "bounding_box_mismatch_fields": [],
        "volume_difference_mm3": None,
        "volume_tolerance_mm3": volume_tolerance_mm3,
        "temporary_step_deleted": False,
        "status": "FAIL",
    }
    path: Path | None = None
    try:
        cq = require_cadquery()
        source_valid = bool(shape.isValid())
        source_volume = float(shape.Volume())
        result["source_valid"] = source_valid
        result["source_volume_mm3"] = (
            source_volume if math.isfinite(source_volume) else None
        )
        if not source_valid:
            result["step_error_type"] = "INVALID_SOURCE_SHAPE"
        elif not math.isfinite(source_volume):
            result["step_error_type"] = "NONFINITE_SOURCE_VOLUME"
        elif source_volume <= 0.0:
            result["step_error_type"] = "NONPOSITIVE_SOURCE_VOLUME"
        else:
            with tempfile.TemporaryDirectory(
                prefix="paddy_v229391_step_"
            ) as temp_dir:
                path = Path(temp_dir) / "verification_only_roundtrip.step"
                cq.exporters.export(shape, str(path))
                result["temporary_step_created"] = path.exists()
                result["temporary_step_size_bytes"] = path.stat().st_size
                imported = cq.importers.importStep(str(path)).val()
                imported_valid = bool(imported.isValid())
                imported_volume = float(imported.Volume())
                measured = bounding_box(imported)
                finite_bbox = all(math.isfinite(value) for value in measured.values())
                mismatch = (
                    [
                        key
                        for key in expected_bbox
                        if not _close(
                            measured[key],
                            expected_bbox[key],
                            linear_tolerance_mm,
                        )
                    ]
                    if finite_bbox
                    else sorted(expected_bbox)
                )
                result["roundtrip_valid"] = imported_valid
                result["roundtrip_volume_mm3"] = (
                    imported_volume if math.isfinite(imported_volume) else None
                )
                result["roundtrip_bounding_box_mm"] = (
                    measured if finite_bbox else None
                )
                result["bounding_box_mismatch_fields"] = mismatch
                if math.isfinite(imported_volume):
                    result["volume_difference_mm3"] = abs(
                        imported_volume - source_volume
                    )
                if not imported_valid:
                    result["step_error_type"] = "INVALID_IMPORTED_SHAPE"
                elif not math.isfinite(imported_volume):
                    result["step_error_type"] = "NONFINITE_IMPORTED_VOLUME"
                elif imported_volume <= 0.0:
                    result["step_error_type"] = "NONPOSITIVE_IMPORTED_VOLUME"
                elif not finite_bbox:
                    result["step_error_type"] = "NONFINITE_IMPORTED_BOUNDING_BOX"
                elif mismatch:
                    result["step_error_type"] = "ROUNDTRIP_BOUNDING_BOX_MISMATCH"
                elif (
                    result["volume_difference_mm3"] > volume_tolerance_mm3
                ):
                    result["step_error_type"] = "ROUNDTRIP_VOLUME_MISMATCH"
                else:
                    result["step_operation_status"] = "PASS"
    except Exception as exc:
        result["step_error_type"] = type(exc).__name__
    result["temporary_step_deleted"] = path is not None and not path.exists()
    result["status"] = (
        "PASS"
        if result["step_operation_status"] == "PASS"
        and result["temporary_step_deleted"]
        else "FAIL"
    )
    return result


def _inspect_or_skip_pair(
    first: Envelope,
    second: Envelope,
    solids: Mapping[str, object],
    solid_status: Mapping[str, str],
    linear_tolerance_mm: float,
    intersection_volume_tolerance_mm3: float,
    expected_relation: str,
) -> dict:
    if (
        solid_status.get(first.component_id) == "PASS"
        and solid_status.get(second.component_id) == "PASS"
    ):
        return inspect_pair(
            first,
            second,
            solids[first.component_id],
            solids[second.component_id],
            linear_tolerance_mm,
            intersection_volume_tolerance_mm3,
            expected_relation,
        )
    relation = classify_envelope_relation(
        first, second, linear_tolerance_mm
    )
    relation.update(
        {
            "expected_relation": expected_relation,
            "intersection_operation_status": "NOT_RUN",
            "intersection_error_type": "INVALID_SOLID_INPUT",
            "actual_intersection_volume_mm3": None,
            "unintended_volumetric_intersection": None,
            "blockers": [
                f"PAIR_VALIDATION_NOT_RUN:{first.component_id}:{second.component_id}"
            ],
            "status": "FAIL",
        }
    )
    return relation


def _body_relations(
    parameters: AuthorityParameters,
    solids: dict[str, object],
    solid_status: Mapping[str, str],
) -> tuple[list[dict], list[str]]:
    tolerance = LINEAR_TOLERANCE_MM
    cbox = parameters.component(IDS["cbox"])
    bbox = parameters.component(IDS["bbox"])
    blockers: list[str] = []
    pair = _inspect_or_skip_pair(
        cbox,
        bbox,
        solids,
        solid_status,
        tolerance,
        INTERSECTION_VOLUME_TOLERANCE_MM3,
        "FACE_CONTACT",
    )
    blockers.extend(pair["blockers"])
    if pair["status"] != "PASS":
        blockers.append("CBOX_BBOX_SHARED_BOUNDARY_MISMATCH")
    if not (
        cbox.minimum[1] < bbox.minimum[1]
        and _close(cbox.maximum[1], bbox.minimum[1], tolerance)
    ):
        blockers.append("CBOX_BBOX_ORDER_MISMATCH")
    y_overlap = min(cbox.maximum[1], bbox.maximum[1]) - max(
        cbox.minimum[1], bbox.minimum[1]
    )
    x_overlap = min(cbox.maximum[0], bbox.maximum[0]) - max(
        cbox.minimum[0], bbox.minimum[0]
    )
    if y_overlap > tolerance and x_overlap <= tolerance:
        blockers.append("CBOX_BBOX_SIDE_BY_SIDE_FORBIDDEN")
    extent = bbox.maximum[1] - cbox.minimum[1]
    if not _close(extent, parameters.core_length_mm, tolerance):
        blockers.append("CORE_LONGITUDINAL_EXTENT_MISMATCH")
    return [pair], blockers


def validate_seed(
    parameters: AuthorityParameters | None = None,
    reference: AuthorityParameters | None = None,
    include_step_roundtrip: bool = False,
    solids_override: Mapping[str, object] | None = None,
    authority_hardware_records: Sequence[Mapping[str, object]] | None = None,
    pair_policy_override: Sequence[Mapping[str, object]] | None = None,
) -> dict:
    if reference is None:
        try:
            reference = load_authority(
                hardware_records=authority_hardware_records
            )
        except AuthorityError as exc:
            return _authority_failure_report(exc.blockers)
    parameters = parameters or reference
    blockers = validate_parameters(parameters, reference)
    policy_rows = (
        list(pair_policy_override)
        if pair_policy_override is not None
        else build_pair_policy()
    )
    pair_policy_report, pair_policy_blockers = _validate_pair_policy(policy_rows)
    blockers.extend(pair_policy_blockers)
    containment_report, containment_blockers = _battery_bbox_containment(
        parameters
    )
    blockers.extend(containment_blockers)
    solids: dict[str, object] = {}
    solid_rows: list[dict] = []
    pair_rows: list[dict] = []
    mirror = {"status": "NOT_RUN"}
    step_roundtrip = {"status": "NOT_RUN"}
    assembly_bounds: dict[str, float] = {}
    solid_id_report = {
        "required_solid_ids": list(REQUIRED_SOLID_IDS),
        "actual_solid_ids": [],
        "missing_solid_ids": list(REQUIRED_SOLID_IDS),
        "extra_solid_ids": [],
        "required_solid_count": len(REQUIRED_SOLID_IDS),
        "actual_solid_count": 0,
        "non_null_solid_ids": [],
        "solid_id_set_status": "NOT_RUN",
    }

    if _can_build(parameters):
        solids = (
            dict(solids_override)
            if solids_override is not None
            else dict(build_minimum_assembly(parameters))
        )
        solid_id_report, solid_id_blockers = _solid_id_gate(solids)
        blockers.extend(solid_id_blockers)
        solid_rows = inspect_all_solids(
            solids, parameters.components, LINEAR_TOLERANCE_MM
        )
        for row in solid_rows:
            blockers.extend(row["blockers"])
        solid_status = {
            row["component_id"]: row["status"] for row in solid_rows
        }
        left = parameters.component(IDS["left"])
        right = parameters.component(IDS["right"])
        cross = parameters.component(IDS["cross"])
        pair_specs = (
            (left, cross, "FACE_CONTACT", "LEFT_CROSSMEMBER_CONTACT_MISMATCH"),
            (right, cross, "FACE_CONTACT", "RIGHT_CROSSMEMBER_CONTACT_MISMATCH"),
            (left, right, "SEPARATED", "LEFT_RIGHT_RAIL_SEPARATION_MISMATCH"),
        )
        for first, second, expected, blocker in pair_specs:
            row = _inspect_or_skip_pair(
                first,
                second,
                solids,
                solid_status,
                LINEAR_TOLERANCE_MM,
                INTERSECTION_VOLUME_TOLERANCE_MM3,
                expected,
            )
            pair_rows.append(row)
            blockers.extend(row["blockers"])
            if row["status"] != "PASS":
                blockers.append(blocker)
            if row["unintended_volumetric_intersection"] is True:
                blockers.append("UNINTENDED_VOLUMETRIC_INTERSECTION")
        mirror = inspect_mirror(left, right, LINEAR_TOLERANCE_MM)
        if mirror["status"] != "PASS":
            blockers.append("RAIL_MIRROR_SYMMETRY_MISMATCH")
        body_pairs, body_blockers = _body_relations(
            parameters, solids, solid_status
        )
        pair_rows.extend(body_pairs)
        blockers.extend(body_blockers)
        assembly_bounds = union_bounds(parameters.components)
        if not _close(
            assembly_bounds["xlen"],
            parameters.bare_frame_width_mm,
            LINEAR_TOLERANCE_MM,
        ):
            blockers.append("ACTUAL_MINIMUM_ASSEMBLY_WIDTH_MISMATCH")
        if include_step_roundtrip:
            left_row = next(
                row for row in solid_rows if row["component_id"] == IDS["left"]
            )
            if left_row["status"] == "PASS":
                step_roundtrip = temporary_step_roundtrip(
                    solids[IDS["left"]],
                    left_row["bounding_box_mm"],
                    LINEAR_TOLERANCE_MM,
                    INTERSECTION_VOLUME_TOLERANCE_MM3,
                )
            else:
                step_roundtrip = {
                    "step_operation_status": "NOT_RUN",
                    "step_error_type": "INVALID_SOURCE_SHAPE",
                    "status": "FAIL",
                }
            if step_roundtrip["status"] != "PASS":
                blockers.append("TEMPORARY_STEP_ROUNDTRIP_FAILED")

    blockers = sorted(set(blockers))
    intended_contacts = sum(
        row["relation"] == "FACE_CONTACT"
        and row["status"] == "PASS"
        and row["first"] in {IDS["left"], IDS["right"]}
        and row["second"] == IDS["cross"]
        for row in pair_rows
    )
    unintended_intersections = sum(
        row["unintended_volumetric_intersection"] is True for row in pair_rows
    )
    status = "PASS_WITH_HOLD" if not blockers else "FAIL"
    hardware_registry_source = next(
        record.relative_path
        for record in parameters.source_records
        if record.relative_path.endswith("/hardware_envelope_registry.json")
    )
    release_hold_map = dict(parameters.release_holds)
    return {
        "schema": "PS_COMMON_ROVER_V229391_EXECUTABLE_CAD_SEED_REPORT_V3",
        "source_version": parameters.version,
        "tolerances": {
            "linear_tolerance_mm": parameters.linear_tolerance_mm,
            "intersection_volume_tolerance_mm3":
                parameters.intersection_volume_tolerance_mm3,
            "basis": (
                "Linear coordinate comparisons and volumetric Boolean noise "
                "are dimensionally separate absolute tolerances."
            ),
        },
        "authority_record_uniqueness": {
            "required_component_ids": list(IDS.values()),
            "record_count_per_required_id": 1,
            "battery_placement_confirmed_only_after_uniqueness": True,
            "status": "PASS",
        },
        "coordinate_system": {
            "X": "lateral; +X rover left",
            "Y": "longitudinal; -Y rover front",
            "Z": "upward; +Z up",
            "front_datum_y_mm": parameters.front_datum_y_mm,
            "units": parameters.units,
        },
        "geometry_classification": SIMPLIFIED_TSLOT_AUTHORITY_ENVELOPE,
        "manufacturing_profile": False,
        "required_solid_ids": solid_id_report["required_solid_ids"],
        "actual_solid_ids": solid_id_report["actual_solid_ids"],
        "missing_solid_ids": solid_id_report["missing_solid_ids"],
        "extra_solid_ids": solid_id_report["extra_solid_ids"],
        "required_solid_count": solid_id_report["required_solid_count"],
        "actual_solid_list": solid_id_report["non_null_solid_ids"],
        "actual_solid_count": solid_id_report["actual_solid_count"],
        "solid_id_set_status": solid_id_report["solid_id_set_status"],
        "solid_validation": solid_rows,
        "pair_validation": pair_rows,
        "pair_policy": pair_policy_report["policy_matrix"],
        "total_possible_pair_count":
            pair_policy_report["total_possible_pair_count"],
        "pair_policy_count": pair_policy_report["pair_policy_count"],
        "boolean_checked_pair_count":
            pair_policy_report["boolean_checked_pair_count"],
        "envelope_checked_pair_count":
            pair_policy_report["envelope_checked_pair_count"],
        "envelope_only_checked_pair_count":
            pair_policy_report["envelope_only_checked_pair_count"],
        "intended_containment_pair_count":
            pair_policy_report["intended_containment_pair_count"],
        "unchecked_or_unauthorized_pair_count":
            pair_policy_report["unchecked_or_unauthorized_pair_count"],
        "pair_policy_status": pair_policy_report["status"],
        "intended_face_contact_count": intended_contacts,
        "unintended_volumetric_intersection_count": unintended_intersections,
        "unintended_volumetric_intersection_scope":
            "FOUR_BOOLEAN_CHECKED_PAIRS_ONLY; "
            "BATTERY_BBOX_INTENDED_CONTAINMENT_EXCLUDED",
        "unintended_intersection_count_in_checked_pairs":
            unintended_intersections,
        "mirror_validation": mirror,
        "fpb_authority_validation": {
            "left_rail_center_x_mm": parameters.component(IDS["left"]).center[0],
            "right_rail_center_x_mm": parameters.component(IDS["right"]).center[0],
            "rail_center_separation_mm": parameters.rail_center_separation_mm,
            "front_datum_y_mm": parameters.front_datum_y_mm,
            "crossmember_length_mm": parameters.component(IDS["cross"]).dimensions[0],
            "crossmember_section_mm": parameters.component(IDS["cross"]).dimensions[1:],
            "bare_frame_width_mm": parameters.bare_frame_width_mm,
            "intended_face_contacts": intended_contacts,
            "unintended_volumetric_intersections": unintended_intersections,
            "status": "PASS" if not blockers else "FAIL",
        },
        "body_authority_validation": {
            "cbox_dimensions_mm": parameters.component(IDS["cbox"]).dimensions,
            "cbox_y_range_mm": (
                parameters.component(IDS["cbox"]).minimum[1],
                parameters.component(IDS["cbox"]).maximum[1],
            ),
            "bbox_dimensions_mm": parameters.component(IDS["bbox"]).dimensions,
            "bbox_y_range_mm": (
                parameters.component(IDS["bbox"]).minimum[1],
                parameters.component(IDS["bbox"]).maximum[1],
            ),
            "shared_boundary_y_mm": parameters.component(IDS["bbox"]).minimum[1],
            "core_longitudinal_extent_mm": (
                parameters.component(IDS["cbox"]).minimum[1],
                parameters.component(IDS["bbox"]).maximum[1],
            ),
            "core_length_mm": parameters.core_length_mm,
        },
        "battery_bbox_containment": containment_report,
        "minimum_assembly_bounding_box_mm": assembly_bounds,
        "width_authority": {
            "actual_minimum_assembly_width_mm": assembly_bounds.get("xlen"),
            "bare_fpb_width_mm": parameters.bare_frame_width_mm,
            "registered_maximum_interface_width_mm":
                parameters.registered_interface_width_mm,
            "operational_hard_limit_mm": parameters.operational_hard_limit_mm,
            "registered_interface_geometry_synthesized": False,
        },
        "battery_cassette": {
            "placement_status": parameters.battery_placement_status,
            "placement_source": hardware_registry_source,
            "registry_record_source": parameters.component(IDS["battery"]).source_path,
            "registry_record_revision":
                parameters.component(IDS["battery"]).source_revision,
            "minimum_xyz_mm": parameters.component(IDS["battery"]).minimum,
            "maximum_xyz_mm": parameters.component(IDS["battery"]).maximum,
            "guessed_values_used": False,
        },
        "authority_sources": [asdict(record) for record in parameters.source_records],
        "temporary_step_roundtrip": step_roundtrip,
        "blockers": blockers,
        "unresolved_holds": [
            f"{key}={value}" for key, value in sorted(release_hold_map.items())
        ] + ["SIMPLIFIED_TSLOT_IS_NOT_A_MANUFACTURING_PROFILE"],
        "DESIGN_ANALYSIS_PROCESS": status,
        "EXECUTABLE_CAD_SEED_STATUS": status,
        "SOURCE_REVIEW_CORRECTION_STATUS": status,
        "FINAL_CONTRACT_CORRECTION_STATUS": status,
        "COMMIT_READINESS": "PASS_WITH_HOLD" if not blockers else "HOLD",
        "GITHUB_EXECUTABLE_CAD_RELEASE": "HOLD",
        "GITHUB_MANUFACTURING_RELEASE": "HOLD",
        "MANUFACTURING_STATUS": "NOT_APPROVED",
        "PURCHASE_STATUS": "NOT_APPROVED",
        "FIELD_DEPLOYMENT_STATUS": "NOT_APPROVED",
        "WATERPROOF_STATUS": "NOT_VALIDATED",
        "STRUCTURAL_STRENGTH_STATUS": "NOT_VALIDATED",
        "ELECTRICAL_SAFETY_STATUS": release_hold_map["ELECTRICAL_SAFETY_STATUS"],
        "THERMAL_STATUS": release_hold_map["THERMAL_STATUS"],
    }


def canonical_report_json(report: dict) -> str:
    return json.dumps(
        report, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
