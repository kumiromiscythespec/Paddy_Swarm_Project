from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from fastener_attachment_audit import (
    audit_attachment_groups,
    summarize_group_contradictions,
)
from fastener_requirement_authority import (
    classify_fastener_requirements,
    validate_requirement_authority,
)
from hole_containment_inspector import (
    inspect_all_hole_candidates,
    summarize_containment,
)
from hole_seat_inspector import inspect_all_hole_seats, summarize_hole_seats
from image_review_receipt import validate_review_receipt
from opening_router import route_loop001_openings, validate_routing
from pipeline_gates import evaluate_v229_3_5_final_gate, exit_code_for_context
from structural_joint_registry import load_structural_joint_registry

STAGES = (
    "PREFLIGHT",
    "REQUIREMENT_AUTHORITY_AUDIT",
    "GROUP_CONTRADICTION_AUDIT",
    "STATIC_HOLE_CONTAINMENT",
    "CADQUERY_IMPORT",
    "RAIL_SOLID_BUILD",
    "RAIL_SOLID_VALIDATION",
    "REQUIRED_HOLE_GENERATION",
    "HOLE_GEOMETRY_INSPECTION",
    "STEP_EXPORT",
    "STEP_REIMPORT_VERIFY",
    "VISUALIZATION_STL_EXPORT",
    "STL_VERIFY",
    "PNG_RENDER",
    "AUTOMATED_IMAGE_QA",
    "MINIMUM_ASSEMBLY_BUILD",
    "MINIMUM_ASSEMBLY_INSPECTION",
    "SERVICE_SWEEP_INSPECTION",
    "TECHNICAL_GATE",
    "IMAGE_REVIEW_PACK",
    "EXTERNAL_RECEIPT_VALIDATE_IF_PRESENT",
    "FINAL_LOOP_GATE",
    "PACKAGE",
    "FINAL_ZIP_SEAL",
)

EXIT_CODES = {
    "PASS": 0,
    "PREFLIGHT_AUTHORITY_FAILURE": 10,
    "CADQUERY_UNAVAILABLE": 20,
    "RAIL_SOLID_BUILD_FAILURE": 30,
    "REQUIRED_HOLE_FAILURE": 40,
    "STEP_STL_EXPORT_VERIFY_FAILURE": 50,
    "RENDER_IMAGE_QA_FAILURE": 60,
    "MINIMUM_ASSEMBLY_HARD_FAILURE": 70,
    "MINIMUM_ASSEMBLY_UNDEFINED_JOINT": 71,
    "EXTERNAL_RECEIPT_INVALID": 80,
    "FINAL_GATE_FAILURE": 90,
    "PACKAGE_FINAL_SEAL_FAILURE": 100,
}

STAGE_ALIASES = {
    "preflight": 4,
    "solid": 7,
    "holes": 9,
    "export": 13,
    "render": 15,
    "minimum-assembly": 18,
    "review-pack": 20,
    "finalize": 24,
    "all": 24,
}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stage(rows, name, status, **details):
    rows.append(
        {
            "sequence": STAGES.index(name) + 1,
            "stage": name,
            "status": status,
            **details,
        }
    )


def requested_stage_limit(stage):
    if stage not in STAGE_ALIASES:
        raise ValueError(f"unsupported stage: {stage}")
    return STAGE_ALIASES[stage]


def validate_stage_registry(stages):
    return {
        "status": "PASS" if tuple(stages) == STAGES else "FAIL",
        "stage_count": len(stages),
        "single_ordered_authority": tuple(stages) == STAGES,
    }


def validate_run_all_script(script_text):
    normalized = script_text.replace("`", " ").replace("\r", " ")
    invocation_count = normalized.count("run_loop001_full.py")
    return {
        "status": (
            "PASS"
            if invocation_count == 1 and "--stage all" in normalized
            else "FAIL"
        ),
        "full_runner_invocation_count": invocation_count,
        "stage_all_forwarded": "--stage all" in normalized,
        "review_receipt_forwarded": "--review-receipt" in normalized,
    }


def _partial_result(context, stage_rows, output, label):
    context.update(
        {
            "exit_code": 0,
            "loop_001_status": label,
            "stages": stage_rows,
        }
    )
    write_json(output / "full_loop_status.json", context)
    return context


def _active_rail(registries):
    return next(
        row
        for row in registries["components"]
        if row["part_id"] == "V2292-FPB-RAIL-L"
    )


def run_static_authority(registries, source_root):
    authority = classify_fastener_requirements(registries)
    authority_gate = validate_requirement_authority(authority)
    groups = audit_attachment_groups(authority)
    group_gate = summarize_group_contradictions(groups)
    containment = inspect_all_hole_candidates(
        authority, _active_rail(registries)
    )
    containment_gate = summarize_containment(containment)
    seats = inspect_all_hole_seats(
        authority,
        containment,
        _active_rail(registries),
        registries["fasteners"]["diameter_classes"],
    )
    seat_gate = summarize_hole_seats(seats)
    routes = route_loop001_openings(registries)
    routing_gate = validate_routing(routes)
    joints = load_structural_joint_registry(source_root)
    crossmember = next(
        row
        for row in joints
        if row["joint_id"] == "JOINT-LOOP001-RAIL-FRONT-XMEMBER"
    )
    return {
        "authority_rows": authority,
        "authority_gate": authority_gate,
        "group_rows": groups,
        "group_gate": group_gate,
        "containment_rows": containment,
        "containment_gate": containment_gate,
        "seat_rows": seats,
        "seat_gate": seat_gate,
        "routing_rows": routes,
        "routing_gate": routing_gate,
        "joints": joints,
        "rail_crossmember_joint_status": (
            "DEFINED"
            if crossmember["joint_type"] != "UNDEFINED_MEASUREMENT_HOLD"
            else "MEASUREMENT_HOLD"
        ),
    }


def validate_receipt_argument(path, expected, image_rows):
    if path is None:
        return {
            "status": "PENDING_EXTERNAL_REVIEW",
            "overall_decision": "PENDING",
            "blocking_issue_count": 0,
            "required_reinspection_count": 0,
            "critical_not_visible_count": 0,
            "receipt_argument_consumed": False,
        }
    receipt_path = Path(path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    result = validate_review_receipt(receipt, expected, image_rows)
    result["receipt_argument_consumed"] = True
    return result


def _hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _context_from_static(static):
    return {
        "preflight_status": "PASS",
        "fastener_requirement_authority_status": static[
            "authority_gate"
        ]["status"],
        "design_contradiction_count": static[
            "authority_gate"
        ]["design_contradiction_count"],
        "required_hole_authority_undefined_count": static[
            "authority_gate"
        ]["required_hole_authority_undefined_count"],
        "required_hole_static_unreachable_count": static[
            "containment_gate"
        ]["required_hole_static_unreachable_count"],
        "required_hole_edge_breakout_count": static[
            "containment_gate"
        ]["required_hole_edge_breakout_count"],
        "required_hole_material_continuity_failure_count": static[
            "containment_gate"
        ]["required_hole_material_continuity_failure_count"],
        "required_hole_seat_failure_count": static[
            "seat_gate"
        ]["required_hole_seat_failure_count"],
        "rail_crossmember_joint_status": static[
            "rail_crossmember_joint_status"
        ],
        "minimum_assembly_status": "NOT_RUN",
        "technical_gate_status": "NOT_RUN",
        "external_image_review_status": "PENDING_EXTERNAL_REVIEW",
        "blocking_issue_count": 0,
        "required_reinspection_count": 0,
        "critical_not_visible_count": 0,
        "package_seal_status": "NOT_RUN",
    }


def _cadquery_unavailable_result(context, stage_rows, limit, output):
    for name in STAGES[5:limit]:
        _stage(
            stage_rows,
            name,
            "NOT_RUN_ENVIRONMENT_UNAVAILABLE",
            blocked_by="CADQUERY_IMPORT",
        )
    context.update(
        {
            "cad_execution_status": "NOT_RUN_ENVIRONMENT_UNAVAILABLE",
            "rail_solid_status": "NOT_RUN",
            "required_hole_gate_status": "NOT_RUN",
            "export_gate_status": "NOT_RUN",
            "render_gate_status": "NOT_RUN",
            "minimum_assembly_status": (
                "NOT_RUN_ENVIRONMENT_UNAVAILABLE_AND_"
                "BLOCKED_BY_UNDEFINED_STRUCTURAL_JOINT"
            ),
            "technical_gate_status": "NOT_RUN_ENVIRONMENT_UNAVAILABLE",
            "final_loop_gate_status": "BLOCKED",
            "next_loop_eligibility": "BLOCKED",
            "loop_001_status": (
                "SOURCE_AUTHORITY_AND_RUNNER_REPAIRED_AWAITING_CADQUERY"
            ),
            "exit_code": EXIT_CODES["CADQUERY_UNAVAILABLE"],
            "stages": stage_rows,
        }
    )
    write_json(output / "full_loop_status.json", context)
    return context


def run_full_loop(
    registries,
    source_root,
    output_root,
    stage="all",
    review_receipt=None,
):
    """Run one ordered closed loop; no reachability-created requirement."""
    limit = requested_stage_limit(stage)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    stage_rows = []
    static = run_static_authority(registries, source_root)
    static_ok = (
        not static["authority_gate"]["errors"]
        and static["routing_gate"]["status"] == "PASS"
        and not static["group_gate"]["errors"]
    )
    _stage(stage_rows, "PREFLIGHT", "PASS" if static_ok else "FAIL")
    _stage(
        stage_rows,
        "REQUIREMENT_AUTHORITY_AUDIT",
        static["authority_gate"]["status"],
    )
    _stage(
        stage_rows,
        "GROUP_CONTRADICTION_AUDIT",
        static["group_gate"]["status"],
    )
    _stage(
        stage_rows,
        "STATIC_HOLE_CONTAINMENT",
        static["containment_gate"]["status"],
    )
    context = _context_from_static(static)
    if not static_ok:
        context.update(
            {
                "preflight_status": "FAIL",
                "exit_code": EXIT_CODES["PREFLIGHT_AUTHORITY_FAILURE"],
                "loop_001_status": "FAIL",
                "stages": stage_rows,
            }
        )
        write_json(output / "full_loop_status.json", context)
        return context
    if limit <= 4:
        return _partial_result(
            context, stage_rows, output, "STATIC_PREFLIGHT_COMPLETE"
        )

    cadquery_available = importlib.util.find_spec("cadquery") is not None
    _stage(
        stage_rows,
        "CADQUERY_IMPORT",
        "PASS" if cadquery_available else "UNAVAILABLE",
    )
    context["cadquery_import_status"] = (
        "PASS" if cadquery_available else "UNAVAILABLE"
    )
    if not cadquery_available:
        return _cadquery_unavailable_result(
            context, stage_rows, limit, output
        )

    # CAD imports remain behind the import gate.
    import cadquery as cq
    from cad_assembly import build_part
    from cad_fasteners import (
        aggregate_required_hole_gate,
        apply_required_rail_holes,
    )
    from cad_primitives import is_valid_solid
    from minimum_assembly_builder import (
        build_minimum_assembly,
        create_minimum_assembly_manifest,
    )
    from minimum_assembly_inspector import inspect_minimum_assembly
    from params_v229_3_5 import PARAMS
    from render_views import render_actual_solid_views
    from software_renderer import validate_png

    try:
        rail = build_part("V2292-FPB-RAIL-L", PARAMS, registries)
    except Exception as exc:
        _stage(stage_rows, "RAIL_SOLID_BUILD", "FAIL", error=str(exc))
        context.update(
            {
                "rail_solid_status": "FAIL",
                "loop_001_status": "FAIL",
                "exit_code": EXIT_CODES["RAIL_SOLID_BUILD_FAILURE"],
                "stages": stage_rows,
            }
        )
        write_json(output / "full_loop_status.json", context)
        return context
    _stage(stage_rows, "RAIL_SOLID_BUILD", "PASS")
    valid = is_valid_solid(rail)
    _stage(stage_rows, "RAIL_SOLID_VALIDATION", "PASS" if valid else "FAIL")
    context["rail_solid_status"] = "PASS" if valid else "FAIL"
    if not valid:
        context.update(
            {
                "loop_001_status": "FAIL",
                "exit_code": EXIT_CODES["RAIL_SOLID_BUILD_FAILURE"],
                "stages": stage_rows,
            }
        )
        return context
    if limit <= 7:
        return _partial_result(
            context, stage_rows, output, "RAIL_SOLID_STAGE_COMPLETE"
        )

    rail, hole_rows = apply_required_rail_holes(
        rail,
        static["routing_rows"],
        registries["fasteners"]["instances"],
        PARAMS["boolean_volume_tolerance_mm3"],
    )
    hole_gate = aggregate_required_hole_gate(hole_rows, is_valid_solid(rail))
    _stage(
        stage_rows,
        "REQUIRED_HOLE_GENERATION",
        hole_gate["status"],
        executed=hole_gate["required_rail_hole_execution_count"],
    )
    _stage(stage_rows, "HOLE_GEOMETRY_INSPECTION", hole_gate["status"])
    context["required_hole_gate_status"] = hole_gate["status"]
    if hole_gate["status"] != "PASS":
        context.update(
            {
                "loop_001_status": "FAIL",
                "exit_code": EXIT_CODES["REQUIRED_HOLE_FAILURE"],
                "stages": stage_rows,
            }
        )
        return context
    if limit <= 9:
        return _partial_result(
            context, stage_rows, output, "REQUIRED_HOLE_STAGE_COMPLETE"
        )

    step_path = output / "step" / "V2292-FPB-RAIL-L.step"
    stl_path = output / "stl_visualization" / "V2292-FPB-RAIL-L.stl"
    step_path.parent.mkdir(parents=True, exist_ok=True)
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cq.exporters.export(rail, str(step_path))
        _stage(stage_rows, "STEP_EXPORT", "PASS", sha256=_hash_file(step_path))
        reimported = cq.importers.importStep(str(step_path))
        step_ok = is_valid_solid(reimported)
        _stage(
            stage_rows,
            "STEP_REIMPORT_VERIFY",
            "PASS" if step_ok else "FAIL",
        )
        cq.exporters.export(rail, str(stl_path))
        _stage(
            stage_rows,
            "VISUALIZATION_STL_EXPORT",
            "PASS",
            sha256=_hash_file(stl_path),
        )
        stl_ok = stl_path.stat().st_size > 84
        _stage(stage_rows, "STL_VERIFY", "PASS" if stl_ok else "FAIL")
        if not (step_ok and stl_ok):
            raise RuntimeError("STEP_OR_STL_VERIFY_FAILURE")
    except Exception as exc:
        context.update(
            {
                "export_gate_status": "FAIL",
                "loop_001_status": "FAIL",
                "exit_code": EXIT_CODES["STEP_STL_EXPORT_VERIFY_FAILURE"],
                "stages": stage_rows,
                "export_error": str(exc),
            }
        )
        return context
    context["export_gate_status"] = "PASS"
    if limit <= 13:
        return _partial_result(
            context, stage_rows, output, "EXPORT_STAGE_COMPLETE"
        )

    try:
        image_rows, _ = render_actual_solid_views(
            rail,
            "V2292-FPB-RAIL-L",
            "revA",
            output / "images",
            PARAMS,
            {"annotation_text": "ACTUAL LOOP-001 RAIL SOLID"},
        )
        _stage(stage_rows, "PNG_RENDER", "PASS", image_count=len(image_rows))
        image_ok = all(
            validate_png(row["filename"])["status"] == "PASS"
            for row in image_rows
        )
        _stage(
            stage_rows,
            "AUTOMATED_IMAGE_QA",
            "PASS" if image_ok else "FAIL",
        )
        if not image_ok:
            raise RuntimeError("AUTOMATED_IMAGE_QA_FAILURE")
    except Exception as exc:
        context.update(
            {
                "render_gate_status": "FAIL",
                "loop_001_status": "FAIL",
                "exit_code": EXIT_CODES["RENDER_IMAGE_QA_FAILURE"],
                "stages": stage_rows,
                "render_error": str(exc),
            }
        )
        return context
    context["render_gate_status"] = "PASS"
    if limit <= 15:
        return _partial_result(
            context, stage_rows, output, "RENDER_STAGE_COMPLETE"
        )

    manifest = create_minimum_assembly_manifest(
        registries, static["joints"]
    )
    assembly = build_minimum_assembly(
        manifest, registries, PARAMS, active_solid=rail
    )
    _stage(
        stage_rows,
        "MINIMUM_ASSEMBLY_BUILD",
        assembly.get("status", "FAIL"),
    )
    minimum = inspect_minimum_assembly(
        assembly,
        manifest,
        static["joints"],
        PARAMS["contact_tolerance_mm"],
        PARAMS["boolean_volume_tolerance_mm3"],
    )
    if static["rail_crossmember_joint_status"] != "DEFINED":
        minimum["status"] = "BLOCKED_BY_UNDEFINED_STRUCTURAL_JOINT"
    _stage(
        stage_rows,
        "MINIMUM_ASSEMBLY_INSPECTION",
        minimum["status"],
    )
    _stage(
        stage_rows,
        "SERVICE_SWEEP_INSPECTION",
        "BLOCKED" if minimum["status"] != "PASS" else "PASS",
    )
    context["minimum_assembly_status"] = minimum["status"]
    context["technical_gate_status"] = (
        "PASS" if minimum["status"] == "PASS" else "CONDITIONAL_HOLD"
    )
    if limit <= 18:
        return _partial_result(
            context, stage_rows, output, "MINIMUM_ASSEMBLY_STAGE_COMPLETE"
        )
    _stage(stage_rows, "TECHNICAL_GATE", context["technical_gate_status"])

    image_manifest = output / "image_review_pack" / "image_manifest.json"
    write_json(image_manifest, image_rows)
    _stage(stage_rows, "IMAGE_REVIEW_PACK", "PASS")
    if limit <= 20:
        return _partial_result(
            context, stage_rows, output, "IMAGE_REVIEW_PACK_COMPLETE"
        )
    expected = {
        "loop_id": "LOOP-001",
        "part_id": "V2292-FPB-RAIL-L",
        "revision": "revA",
        "image_manifest_sha256": _hash_file(image_manifest),
        "source_geometry_fingerprint": {"hash": _hash_file(step_path)},
    }
    receipt = validate_receipt_argument(
        review_receipt, expected, image_rows
    )
    _stage(
        stage_rows,
        "EXTERNAL_RECEIPT_VALIDATE_IF_PRESENT",
        receipt["status"],
        receipt_consumed=receipt["receipt_argument_consumed"],
    )
    context.update(
        {
            "external_image_review_status": (
                "PASS" if receipt["status"] == "PASS" else receipt["status"]
            ),
            "receipt_status": (
                "INVALID" if receipt["status"] == "FAIL" else receipt["status"]
            ),
            "blocking_issue_count": receipt.get("blocking_issue_count", 0),
            "required_reinspection_count": receipt.get(
                "required_reinspection_count", 0
            ),
            "critical_not_visible_count": receipt.get(
                "critical_not_visible_count", 0
            ),
        }
    )
    final = evaluate_v229_3_5_final_gate(context)
    _stage(stage_rows, "FINAL_LOOP_GATE", final["status"])

    from package_seal import build_and_seal_package

    package_path = output / "loop001_run_bundle.zip"
    seal = build_and_seal_package(output, package_path)
    _stage(stage_rows, "PACKAGE", "PASS")
    _stage(stage_rows, "FINAL_ZIP_SEAL", seal["final_status"])
    context["package_seal_status"] = seal["final_status"]
    final = evaluate_v229_3_5_final_gate(context)
    context["final_loop_gate_status"] = final["status"]
    context["next_loop_eligibility"] = final["next_loop_eligibility"]
    context["loop_001_status"] = (
        "PASS"
        if final["status"] == "PASS"
        else "BLOCKED_BY_UNDEFINED_DIMENSION"
        if static["rail_crossmember_joint_status"] != "DEFINED"
        else "CONDITIONAL_PASS"
    )
    context["exit_code"] = exit_code_for_context(context)
    context["stages"] = stage_rows
    write_json(output / "full_loop_status.json", context)
    return context


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage", choices=tuple(STAGE_ALIASES), default="all"
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--review-receipt")
    return parser
