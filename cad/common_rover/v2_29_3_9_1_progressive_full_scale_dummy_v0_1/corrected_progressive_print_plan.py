from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from part_number_registry import ALL_PARTS, ALL_PART_BY_KEY
from physical_connection_model import (
    build_physical_connection_graph,
    validate_physical_connection_graph,
)


@dataclass(frozen=True)
class CorrectedPrintStep:
    print_number: int
    part_key: str
    print_prerequisites: tuple[str, ...]
    gates_available_at_step: tuple[str, ...]
    gates_deferred: tuple[str, ...]
    required_mating_parts: tuple[str, ...]
    assembly_growth_dependencies: tuple[str, ...]
    step_that_unlocks_deferred_gate: int | None
    unlocks_deferred_gates_for: tuple[str, ...]
    mirror_unlock_condition: str
    gate_scope: str
    inspection_points: str
    stop_conditions: str


def _s(
    number: int,
    key: str,
    prerequisites: Iterable[str],
    mates: Iterable[str],
    *,
    deferred_to: int | None = None,
    unlocks: Iterable[str] = (),
    mirror: str = "NOT_A_MIRROR_STEP",
    scope: str,
    inspection: str,
    stop: str = "ANY P0-P4 FAILURE STOPS DEPENDENT PRINTS",
) -> CorrectedPrintStep:
    available = ("P0", "P1", "P2") if deferred_to else (
        "P0",
        "P1",
        "P2",
        "P3",
        "P4",
    )
    deferred = ("P3", "P4") if deferred_to else ()
    mate_tuple = tuple(mates)
    return CorrectedPrintStep(
        number,
        key,
        tuple(prerequisites),
        available,
        deferred,
        mate_tuple,
        mate_tuple,
        deferred_to,
        tuple(unlocks),
        mirror,
        scope,
        inspection,
        stop,
    )


PRINT_STEPS: tuple[CorrectedPrintStep, ...] = (
    _s(1, "front_frame_corner_connector_left", (), ("fpb_rail_left_dummy", "fpb_front_crossmember_dummy"), deferred_to=3, scope="AI-01 LEFT CORNER ASSEMBLY", inspection="part number, LEFT key, two open 20 mm-class channels, connector-only bolt bores"),
    _s(2, "fpb_rail_left_dummy", ("front_frame_corner_connector_left",), ("front_frame_corner_connector_left", "fpb_front_crossmember_dummy"), deferred_to=3, scope="AI-01 LEFT PROFILE ENVELOPE FIT", inspection="20x20x232 envelope, FRONT/TOP marking, warp"),
    _s(3, "fpb_front_crossmember_dummy", ("front_frame_corner_connector_left", "fpb_rail_left_dummy"), ("front_frame_corner_connector_left", "fpb_rail_left_dummy", "front_frame_corner_connector_right", "fpb_rail_right_dummy"), deferred_to=5, unlocks=("front_frame_corner_connector_left", "fpb_rail_left_dummy"), scope="AI-01 CROSSMEMBER FULL TWO-SIDE FIT", inspection="LEFT physical sleeve fit now; crossmember full P3/P4 deferred until RIGHT side exists"),
    _s(4, "front_frame_corner_connector_right", ("fpb_front_crossmember_dummy",), ("fpb_front_crossmember_dummy", "fpb_rail_right_dummy"), deferred_to=5, mirror="front_frame_corner_connector_left P3/P4 PASS AT STEP 3", scope="AI-01 RIGHT CORNER ASSEMBLY", inspection="RIGHT key rejects LEFT placement; markings visible"),
    _s(5, "fpb_rail_right_dummy", ("front_frame_corner_connector_right", "fpb_front_crossmember_dummy"), ("front_frame_corner_connector_right", "fpb_front_crossmember_dummy"), unlocks=("fpb_front_crossmember_dummy", "front_frame_corner_connector_right"), mirror="fpb_rail_left_dummy P3/P4 PASS AT STEP 3", scope="AI-01 COMPLETE FPB FRAME", inspection="both sleeves retained, FRONT datum visible, frame is one connected assembly"),
    _s(6, "rear_cradle_left_attachment", ("fpb_rail_left_dummy",), ("fpb_rail_left_dummy", "rear_cradle_dummy_part_1"), deferred_to=7, scope="AI-03 LEFT REAR ATTACHMENT", inspection="external rail channel, LEFT key, removable pin access"),
    _s(7, "rear_cradle_dummy_part_1", ("rear_cradle_left_attachment",), ("rear_cradle_left_attachment",), unlocks=("rear_cradle_left_attachment",), scope="AI-03 LEFT REAR FIRST-SIDE FIT", inspection="cradle remains connected to LEFT rail without hand support"),
    _s(8, "rear_cradle_center_joiner", ("rear_cradle_dummy_part_1",), ("rear_cradle_dummy_part_1", "rear_cradle_dummy_part_2"), deferred_to=11, scope="AI-03 CENTER JOINER TWO-HALF FIT", inspection="LEFT tab fit now; RIGHT channel remains gated"),
    _s(9, "front_fpb_to_rear_cradle_visual_locator", ("fpb_rail_left_dummy", "fpb_rail_right_dummy", "rear_cradle_center_joiner"), ("fpb_rail_left_dummy", "fpb_rail_right_dummy", "rear_cradle_center_joiner"), scope="AI-03 FPB-TO-REAR LOCATOR FIT", inspection="178 mm tie fixes lateral and center datum; both visible pins accessible"),
    _s(10, "rear_cradle_right_attachment", ("fpb_rail_right_dummy",), ("fpb_rail_right_dummy", "rear_cradle_dummy_part_2"), deferred_to=11, mirror="rear_cradle_left_attachment P3/P4 PASS AT STEP 7", scope="AI-03 RIGHT REAR ATTACHMENT", inspection="RIGHT key rejects LEFT placement; removable pin visible"),
    _s(11, "rear_cradle_dummy_part_2", ("rear_cradle_right_attachment", "rear_cradle_center_joiner"), ("rear_cradle_right_attachment", "rear_cradle_center_joiner"), unlocks=("rear_cradle_center_joiner", "rear_cradle_right_attachment"), mirror="rear_cradle_dummy_part_1 P3/P4 PASS AT STEP 7", scope="AI-03 COMPLETE REAR CRADLE CONNECTION", inspection="both halves, center joiner, attachments, and locator form one connected frame"),
    _s(12, "cbox_saddle_base_clip_left", ("fpb_rail_left_dummy",), ("fpb_rail_left_dummy", "cbox_saddle_left"), deferred_to=14, scope="AI-02 LEFT SADDLE ATTACHMENT", inspection="PROFILE-3 channel and existing 76 mm saddle-base channel"),
    _s(13, "cbox_saddle_left", ("cbox_saddle_base_clip_left",), ("cbox_saddle_base_clip_left", "current_cbox_dummy"), deferred_to=14, scope="AI-02 LEFT SADDLE AND BODY FIT", inspection="saddle base captured; body mate not yet printed"),
    _s(14, "current_cbox_dummy", ("cbox_saddle_left", "cbox_saddle_base_clip_left"), ("cbox_saddle_left",), unlocks=("cbox_saddle_base_clip_left", "cbox_saddle_left"), scope="AI-02 LEFT FIRST-SIDE CBOX FIT", inspection="CBOX lowers to positive stop; LEFT seated indicator and clip pin visible"),
    _s(15, "cbox_saddle_base_clip_right", ("fpb_rail_right_dummy", "current_cbox_dummy"), ("fpb_rail_right_dummy", "cbox_saddle_right"), deferred_to=16, mirror="cbox_saddle_base_clip_left P3/P4 PASS AT STEP 14", scope="AI-02 RIGHT SADDLE ATTACHMENT", inspection="RIGHT offset channel rejects LEFT clip"),
    _s(16, "cbox_saddle_right", ("cbox_saddle_base_clip_right", "current_cbox_dummy"), ("cbox_saddle_base_clip_right", "current_cbox_dummy"), unlocks=("cbox_saddle_base_clip_right",), mirror="cbox_saddle_left P3/P4 PASS AT STEP 14", scope="AI-02 COMPLETE CBOX FIT", inspection="both saddles fixed to rails; CBOX removable; no loose saddle"),
    _s(17, "bbox_support_anchor_front", ("rear_cradle_dummy_part_1",), ("rear_cradle_dummy_part_1", "bbox_support_front"), deferred_to=18, scope="AI-03 FRONT BBOX SUPPORT ANCHOR", inspection="FRONT key, cradle channel, support-base channel"),
    _s(18, "bbox_support_front", ("bbox_support_anchor_front",), ("bbox_support_anchor_front", "current_bbox_dummy"), deferred_to=21, unlocks=("bbox_support_anchor_front",), scope="AI-03 FRONT SUPPORT AND BBOX FIT", inspection="support remains on frame when released; BBOX mate deferred"),
    _s(19, "bbox_support_anchor_rear", ("rear_cradle_dummy_part_2",), ("rear_cradle_dummy_part_2", "bbox_support_rear"), deferred_to=20, scope="AI-03 REAR BBOX SUPPORT ANCHOR", inspection="REAR key differs from FRONT; lateral slide stop"),
    _s(20, "bbox_support_rear", ("bbox_support_anchor_rear",), ("bbox_support_anchor_rear", "current_bbox_dummy"), deferred_to=21, unlocks=("bbox_support_anchor_rear",), scope="AI-03 REAR SUPPORT AND BBOX FIT", inspection="support remains on frame; unique spacing visible; BBOX mate deferred"),
    _s(21, "current_bbox_dummy", ("bbox_support_front", "bbox_support_rear"), ("bbox_support_front", "bbox_support_rear"), unlocks=("bbox_support_front", "bbox_support_rear"), scope="AI-03 COMPLETE INDEPENDENT BBOX FIT", inspection="BBOX seats on both frame-retained supports and never on CBOX"),
    _s(22, "core_alignment_key", ("current_cbox_dummy", "current_bbox_dummy"), ("current_cbox_dummy", "current_bbox_dummy"), scope="AI-04 CORE ALIGNMENT FIT", inspection="asymmetric +Y insertion and Y=0 boundary alignment"),
    _s(23, "anti_separation_lock_carrier", ("core_alignment_key",), ("core_alignment_key",), scope="AI-04 VISIBLE PIN LOCK", inspection="metal-pin candidate visible; connector carries no BBOX vertical load"),
    _s(24, "battery_cassette_dummy", ("current_bbox_dummy",), ("current_bbox_dummy",), scope="BATTERY REMOVABLE ENVELOPE FIT", inspection="125x180x120 cage sits only inside authority BBOX envelope"),
    _s(25, "profile3_rail_outer_clamp_left", ("fpb_rail_left_dummy",), ("fpb_rail_left_dummy", "lower_adapter_visual_locator_left"), deferred_to=27, scope="AI-05 LEFT PROFILE-3 OUTER CLAMP", inspection="slotless envelope clamp, Y=-110 witness, visible dummy bolt"),
    _s(26, "lower_adapter_visual_locator_left", ("profile3_rail_outer_clamp_left",), ("profile3_rail_outer_clamp_left", "lower_float_adapter_left"), deferred_to=27, scope="AI-05 LEFT LOWER ADAPTER LOCATOR", inspection="existing 82 mm adapter edge channel and LEFT key"),
    _s(27, "lower_float_adapter_left", ("lower_adapter_visual_locator_left",), ("lower_adapter_visual_locator_left",), unlocks=("profile3_rail_outer_clamp_left", "lower_adapter_visual_locator_left"), scope="AI-05 LEFT PROFILE-3 FLOAT ADAPTER ATTACHMENT", inspection="adapter retained without T-slot, direct hole, glue, or tape"),
    _s(28, "profile3_rail_outer_clamp_right", ("fpb_rail_right_dummy",), ("fpb_rail_right_dummy", "lower_adapter_visual_locator_right"), deferred_to=30, mirror="profile3_rail_outer_clamp_left P3/P4 PASS AT STEP 27", scope="AI-05 RIGHT PROFILE-3 OUTER CLAMP", inspection="RIGHT key rejects LEFT locator; Y=-110 witness"),
    _s(29, "lower_adapter_visual_locator_right", ("profile3_rail_outer_clamp_right",), ("profile3_rail_outer_clamp_right", "lower_float_adapter_right"), deferred_to=30, mirror="lower_adapter_visual_locator_left P3/P4 PASS AT STEP 27", scope="AI-05 RIGHT LOWER ADAPTER LOCATOR", inspection="existing adapter unchanged; removable dummy pin visible"),
    _s(30, "lower_float_adapter_right", ("lower_adapter_visual_locator_right",), ("lower_adapter_visual_locator_right",), unlocks=("profile3_rail_outer_clamp_right", "lower_adapter_visual_locator_right"), mirror="lower_float_adapter_left P3/P4 PASS AT STEP 27", scope="AI-05 COMPLETE PROFILE-3 FLOAT ADAPTER ATTACHMENT", inspection="both adapter branches connected inside Y=-125..-95 authority zone"),
    _s(31, "float_slide_receiver_left", ("lower_float_adapter_left",), ("lower_float_adapter_left",), scope="AI-06 LEFT RECEIVER FIT", inspection="positive stop, pin window, reversed insertion rejection"),
    _s(32, "float_slide_receiver_right", ("lower_float_adapter_right",), ("lower_float_adapter_right",), mirror="float_slide_receiver_left P3/P4 PASS AT STEP 31", scope="AI-06 RIGHT RECEIVER FIT", inspection="mirror relation, pin window, positive stop"),
    _s(33, "pin_retainer_cover", ("float_slide_receiver_left",), ("float_slide_receiver_left",), scope="AI-08 SECONDARY RETAINER FIT", inspection="SECONDARY ONLY; primary pin remains visible"),
)


STEP_BY_KEY = {step.part_key: step for step in PRINT_STEPS}


def achieved_gate_step(part_key: str) -> int:
    step = STEP_BY_KEY[part_key]
    return step.step_that_unlocks_deferred_gate or step.print_number


def dependency_edges(
    steps: tuple[CorrectedPrintStep, ...] = PRINT_STEPS,
) -> list[tuple[str, str]]:
    return [
        (prerequisite, step.part_key)
        for step in steps
        for prerequisite in step.print_prerequisites
    ]


def _acyclic(
    steps: tuple[CorrectedPrintStep, ...],
) -> tuple[bool, list[str]]:
    keys = {step.part_key for step in steps}
    indegree = {key: 0 for key in keys}
    outgoing = {key: set() for key in keys}
    for before, after in dependency_edges(steps):
        if before in keys and after in keys and after not in outgoing[before]:
            outgoing[before].add(after)
            indegree[after] += 1
    ready = sorted(key for key, degree in indegree.items() if degree == 0)
    visited = []
    while ready:
        current = ready.pop(0)
        visited.append(current)
        for neighbor in sorted(outgoing[current]):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                ready.append(neighbor)
                ready.sort()
    return len(visited) == len(keys), visited


def validate_corrected_dependencies(
    steps: tuple[CorrectedPrintStep, ...] = PRINT_STEPS,
    *,
    physical_graph: dict | None = None,
) -> dict:
    blockers = []
    keys = [step.part_key for step in steps]
    expected = {part.key for part in ALL_PARTS}
    if len(keys) != len(set(keys)):
        blockers.append("DUPLICATED_PRINT_STEP")
    if set(keys) != expected:
        blockers.append("PRINT_STEP_PART_SET_MISMATCH")
    positions = {key: index + 1 for index, key in enumerate(keys)}

    acyclic, topological = _acyclic(steps)
    if not acyclic:
        blockers.append("DEPENDENCY_CYCLE")
    for step in steps:
        if step.print_number != positions.get(step.part_key):
            blockers.append("PRINT_NUMBER_ORDER_MISMATCH")
        for prerequisite in step.print_prerequisites:
            if prerequisite not in positions:
                blockers.append("UNKNOWN_PRINT_PREREQUISITE")
            elif positions[prerequisite] >= step.print_number:
                blockers.append("STEP_REQUIRES_FUTURE_PART")
        mates_printed_now = {
            key for key, position in positions.items()
            if position <= step.print_number
        }
        if "P3" in step.gates_available_at_step and not set(
            step.required_mating_parts
        ).issubset(mates_printed_now):
            blockers.append("P3_REQUIRED_BEFORE_MATING_PART_EXISTS")
        if "P4" in step.gates_available_at_step and not set(
            step.assembly_growth_dependencies
        ).issubset(mates_printed_now):
            blockers.append("P4_REQUIRED_BEFORE_ASSEMBLY_DEPENDENCY_EXISTS")
        if step.gates_deferred:
            unlock = step.step_that_unlocks_deferred_gate
            if unlock is None or unlock <= step.print_number or unlock > len(steps):
                blockers.append("IMPOSSIBLE_DEFERRED_GATE_UNLOCK")
            else:
                printed_at_unlock = {
                    key for key, position in positions.items()
                    if position <= unlock
                }
                if not set(step.required_mating_parts).issubset(
                    printed_at_unlock
                ):
                    blockers.append("DEFERRED_P3_MATES_NOT_AVAILABLE")
                if not set(step.assembly_growth_dependencies).issubset(
                    printed_at_unlock
                ):
                    blockers.append("DEFERRED_P4_DEPENDENCIES_NOT_AVAILABLE")
                unlock_step = steps[unlock - 1]
                if step.part_key not in unlock_step.unlocks_deferred_gates_for:
                    blockers.append("DEFERRED_GATE_UNLOCK_NOT_DECLARED")
        elif step.step_that_unlocks_deferred_gate is not None:
            blockers.append("UNEXPECTED_DEFERRED_UNLOCK")

        part = ALL_PART_BY_KEY[step.part_key]
        if part.mirror_of:
            first_achieved = achieved_gate_step(part.mirror_of)
            if step.print_number <= first_achieved:
                blockers.append("MIRROR_UNLOCK_BEFORE_FIRST_SIDE_P3_P4")
            expected_token = f"{part.mirror_of} P3/P4 PASS AT STEP {first_achieved}"
            if step.mirror_unlock_condition != expected_token:
                blockers.append("MIRROR_UNLOCK_CONDITION_NOT_PHYSICAL")

    graph = physical_graph or build_physical_connection_graph()
    graph_report = validate_physical_connection_graph(graph)
    if graph_report["connected_component_count"] != 1:
        blockers.append("DISCONNECTED_FINAL_ASSEMBLY_GRAPH")
    if graph_report["orphan_parts"]:
        blockers.append("ORPHAN_PRINTED_PART")

    impossible = sorted(set(blockers))
    return {
        "schema": "PS_IMPOSSIBLE_DEPENDENCY_AUDIT_V0_1",
        "status": "PASS" if not impossible else "FAIL",
        "blockers": impossible,
        "dependency_graph_acyclic": acyclic,
        "topological_node_count": len(topological),
        "print_step_count": len(steps),
        "deferred_gate_count": sum(bool(step.gates_deferred) for step in steps),
        "mirror_step_count": sum(
            ALL_PART_BY_KEY[step.part_key].mirror_of is not None
            for step in steps
        ),
        "final_graph_connected": (
            graph_report["connected_component_count"] == 1
        ),
        "orphan_part_count": len(graph_report["orphan_parts"]),
        "IMPOSSIBLE_DEPENDENCY_COUNT": (
            0 if not impossible else len(impossible)
        ),
        "PROGRESSIVE_DEPENDENCY_GRAPH": (
            "PASS" if not impossible else "FAIL"
        ),
    }


def corrected_progressive_print_order_markdown() -> str:
    audit = validate_corrected_dependencies()
    if audit["status"] != "PASS":
        raise ValueError(f"INVALID_DEPENDENCY_PLAN:{audit['blockers']}")
    lines = [
        "# Corrected progressive print order — physical dry assembly",
        "",
        "Every step prints one final-use part. P0/P1/P2 may run before a mate "
        "exists. P3/P4 are available only when every mate and assembly-growth "
        "dependency named for that gate scope has physically been printed.",
        "",
    ]
    for step in PRINT_STEPS:
        part = ALL_PART_BY_KEY[step.part_key]
        lines.extend(
            (
                f"## Print {step.print_number:02d} — {part.part_number}",
                "",
                f"- STL filename: `{part.filename}`",
                "- Quantity at this step: 1",
                f"- Material: {part.material}",
                f"- Orientation: {part.print_orientation}",
                f"- Support: {part.support}",
                f"- Brim: {part.brim}",
                f"- Print prerequisites: {', '.join(step.print_prerequisites) or 'NONE'}",
                f"- Gate scope: {step.gate_scope}",
                f"- gates_available_at_step: {', '.join(step.gates_available_at_step)}",
                f"- gates_deferred: {', '.join(step.gates_deferred) or 'NONE'}",
                f"- required_mating_parts: {', '.join(step.required_mating_parts) or 'NONE'}",
                f"- assembly_growth_dependencies: {', '.join(step.assembly_growth_dependencies) or 'NONE'}",
                f"- step_that_unlocks_deferred_gate: {step.step_that_unlocks_deferred_gate or 'NONE'}",
                f"- unlocks_deferred_gates_for: {', '.join(step.unlocks_deferred_gates_for) or 'NONE'}",
                f"- mirror_unlock_condition: {step.mirror_unlock_condition}",
                f"- Inspection points: {step.inspection_points}",
                f"- Stop conditions: {step.stop_conditions}",
                "",
            )
        )
    lines.extend(
        (
            "## Graph audit",
            "",
            "- Directed dependency graph: ACYCLIC",
            "- Impossible dependency count: 0",
            "- Orphan printed part count: 0",
            "- Final physical dry-assembly graph: CONNECTED",
            "- Complete-kit single-plate placement: PROHIBITED",
            "",
        )
    )
    return "\n".join(lines)


def corrected_quality_gate_rows() -> list[dict]:
    rows = []
    for step in PRINT_STEPS:
        part = ALL_PART_BY_KEY[step.part_key]
        for gate in ("P0", "P1", "P2", "P3", "P4"):
            available = gate in step.gates_available_at_step
            rows.append(
                {
                    "print_number": step.print_number,
                    "part_number": part.part_number,
                    "stl_filename": part.filename,
                    "gate": gate,
                    "gate_scope": step.gate_scope,
                    "availability_at_print_step": (
                        "AVAILABLE" if available else "DEFERRED"
                    ),
                    "required_mating_parts": "|".join(
                        step.required_mating_parts
                    ),
                    "assembly_growth_dependencies": "|".join(
                        step.assembly_growth_dependencies
                    ),
                    "unlock_step": (
                        ""
                        if available
                        else step.step_that_unlocks_deferred_gate
                    ),
                    "mirror_unlock_condition": (
                        step.mirror_unlock_condition
                    ),
                    "result": "NOT YET INSPECTED",
                    "stop_on_fail": "YES",
                }
            )
    return rows


validate_corrected_dependencies()
