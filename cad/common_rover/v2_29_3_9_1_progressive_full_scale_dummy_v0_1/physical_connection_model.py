from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from typing import Iterable

from part_number_registry import ALL_PARTS, ALL_PART_BY_KEY


def _edge(
    edge_id: str,
    a: str,
    b: str,
    interface_id: str,
    interface_type: str,
    insertion_direction: str,
    retention_method: str,
    removal_method: str,
    positive_stop: str,
    required_hardware: str,
    tolerance_candidate: str,
    visible_confirmation: str,
) -> dict:
    return {
        "edge_id": edge_id,
        "nodes": [a, b],
        "interface_id": interface_id,
        "interface_type": interface_type,
        "insertion_direction": insertion_direction,
        "retention_method": retention_method,
        "removal_method": removal_method,
        "positive_stop": positive_stop,
        "geometric_contact_exists": True,
        "retention_exists": True,
        "visible_confirmation_exists": True,
        "visible_confirmation": visible_confirmation,
        "structural_claim": False,
        "required_hardware": required_hardware,
        "mating_tolerance_candidate": tolerance_candidate,
        "dry_assembly_only": True,
    }


CONNECTION_EDGES: tuple[dict, ...] = (
    _edge("PC-001", "front_frame_corner_connector_left", "fpb_rail_left_dummy", "AI-01", "EXTERNAL SLEEVE / PROFILE ENVELOPE", "SLIDE RAIL END INTO OPEN CHANNEL", "VISIBLE CONNECTOR-ONLY DUMMY BOLT", "REMOVE BOLT; SLIDE RAIL OUT", "LEFT OUTER WALL", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "LEFT key and rail end remain visible"),
    _edge("PC-002", "front_frame_corner_connector_left", "fpb_front_crossmember_dummy", "AI-01", "ORTHOGONAL EXTERNAL SLEEVE", "SLIDE XMEMBER END INTO OPEN CHANNEL", "VISIBLE CONNECTOR-ONLY DUMMY BOLT", "REMOVE BOLT; SLIDE XMEMBER OUT", "FRONT BUTT FLOOR", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "FRONT butt seam remains visible"),
    _edge("PC-003", "front_frame_corner_connector_right", "fpb_front_crossmember_dummy", "AI-01", "ORTHOGONAL EXTERNAL SLEEVE", "SLIDE XMEMBER END INTO OPEN CHANNEL", "VISIBLE CONNECTOR-ONLY DUMMY BOLT", "REMOVE BOLT; SLIDE XMEMBER OUT", "FRONT BUTT FLOOR", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "FRONT butt seam remains visible"),
    _edge("PC-004", "front_frame_corner_connector_right", "fpb_rail_right_dummy", "AI-01", "EXTERNAL SLEEVE / PROFILE ENVELOPE", "SLIDE RAIL END INTO OPEN CHANNEL", "VISIBLE CONNECTOR-ONLY DUMMY BOLT", "REMOVE BOLT; SLIDE RAIL OUT", "RIGHT OUTER WALL", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "RIGHT key and rail end remain visible"),
    _edge("PC-005", "fpb_rail_left_dummy", "rear_cradle_left_attachment", "AI-03", "EXTERNAL PROFILE ENVELOPE CHANNEL", "SLIDE ATTACHMENT FROM OPEN REAR RAIL END", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE REARWARD", "REAR TRANSVERSE STOP", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "LEFT rear pin and stop visible"),
    _edge("PC-006", "rear_cradle_left_attachment", "rear_cradle_dummy_part_1", "AI-03", "EXTERNAL CRADLE EDGE CHANNEL", "SLIDE CRADLE LEFT TAB INTO CHANNEL", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE CRADLE OUT", "LEFT OFFSET STOP", "HW-PFD-009", "8.50 MM EDGE CHANNEL CANDIDATE", "LEFT cradle seat witness visible"),
    _edge("PC-007", "rear_cradle_dummy_part_1", "rear_cradle_center_joiner", "AI-03", "KEYED TAB RECEIVER LEFT", "SLIDE TOWARD X=0", "VISIBLE 6MM-CLASS DUMMY PIN", "PULL PIN; SLIDE OUTWARD", "CENTER DIVIDER LEFT FACE", "HW-PFD-006/HW-PFD-007", "0.30 MM PER FACE CANDIDATE", "LEFT tab end visible in receiver window"),
    _edge("PC-008", "rear_cradle_center_joiner", "rear_cradle_dummy_part_2", "AI-03", "KEYED TAB RECEIVER RIGHT", "SLIDE TOWARD X=0", "VISIBLE 6MM-CLASS DUMMY PIN", "PULL PIN; SLIDE OUTWARD", "CENTER DIVIDER RIGHT FACE", "HW-PFD-006/HW-PFD-007", "0.30 MM PER FACE CANDIDATE", "RIGHT tab end visible in receiver window"),
    _edge("PC-009", "rear_cradle_dummy_part_2", "rear_cradle_right_attachment", "AI-03", "EXTERNAL CRADLE EDGE CHANNEL", "SLIDE CRADLE RIGHT TAB INTO CHANNEL", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE CRADLE OUT", "RIGHT OFFSET STOP", "HW-PFD-009", "8.50 MM EDGE CHANNEL CANDIDATE", "RIGHT cradle seat witness visible"),
    _edge("PC-010", "rear_cradle_right_attachment", "fpb_rail_right_dummy", "AI-03", "EXTERNAL PROFILE ENVELOPE CHANNEL", "SLIDE ATTACHMENT FROM OPEN REAR RAIL END", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE REARWARD", "REAR TRANSVERSE STOP", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "RIGHT rear pin and stop visible"),
    _edge("PC-011", "front_fpb_to_rear_cradle_visual_locator", "fpb_rail_left_dummy", "AI-03", "REMOVABLE CROSS-TIE END STOP", "LOWER FROM +Z", "VISIBLE DUMMY PIN", "PULL PIN; LIFT +Z", "LEFT END STOP", "HW-PFD-009", "0.40 MM LOCATOR CLEARANCE", "LEFT end stop is visible"),
    _edge("PC-012", "front_fpb_to_rear_cradle_visual_locator", "fpb_rail_right_dummy", "AI-03", "REMOVABLE CROSS-TIE END STOP", "LOWER FROM +Z", "VISIBLE DUMMY PIN", "PULL PIN; LIFT +Z", "RIGHT END STOP", "HW-PFD-009", "0.40 MM LOCATOR CLEARANCE", "RIGHT end stop is visible"),
    _edge("PC-013", "front_fpb_to_rear_cradle_visual_locator", "rear_cradle_center_joiner", "AI-03", "CENTER KEY LOCATOR", "LOWER CENTER KEY FROM +Z", "VISIBLE CENTER DUMMY PIN", "PULL PIN; LIFT +Z", "CENTER KEY SHOULDER", "HW-PFD-009", "0.40 MM KEY CLEARANCE", "Center key and pin remain visible"),
    _edge("PC-014", "fpb_rail_left_dummy", "cbox_saddle_base_clip_left", "AI-02", "PROFILE OUTER CHANNEL", "SLIDE CLIP FROM REAR OPEN END", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE REARWARD", "LEFT OFFSET RAIL STOP", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "LEFT rail channel and pin visible"),
    _edge("PC-015", "cbox_saddle_base_clip_left", "cbox_saddle_left", "AI-02", "SADDLE BASE EDGE CHANNEL", "SLIDE CLIP ONTO REAR BASE EDGE", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE CLIP OFF", "FULL-WIDTH REAR STOP", "HW-PFD-009", "0.50 MM BASE CLEARANCE", "LEFT saddle seated indicator remains visible"),
    _edge("PC-016", "cbox_saddle_left", "current_cbox_dummy", "AI-02", "KEYED CORNER SEAT", "LOWER CBOX -Z", "TEMPORARY VISIBLE DUMMY STRAP", "REMOVE STRAP; LIFT +Z", "INTEGRAL FRONT WALL", "HW-PFD-009", "0.40 MM CAGE-CORNER CANDIDATE", "LEFT seated indicator visible"),
    _edge("PC-017", "fpb_rail_right_dummy", "cbox_saddle_base_clip_right", "AI-02", "PROFILE OUTER CHANNEL", "SLIDE CLIP FROM REAR OPEN END", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE REARWARD", "RIGHT OFFSET RAIL STOP", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "RIGHT rail channel and pin visible"),
    _edge("PC-018", "cbox_saddle_base_clip_right", "cbox_saddle_right", "AI-02", "SADDLE BASE EDGE CHANNEL", "SLIDE CLIP ONTO REAR BASE EDGE", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE CLIP OFF", "FULL-WIDTH REAR STOP", "HW-PFD-009", "0.50 MM BASE CLEARANCE", "RIGHT saddle seated indicator remains visible"),
    _edge("PC-019", "cbox_saddle_right", "current_cbox_dummy", "AI-02", "KEYED CORNER SEAT", "LOWER CBOX -Z", "TEMPORARY VISIBLE DUMMY STRAP", "REMOVE STRAP; LIFT +Z", "INTEGRAL FRONT WALL", "HW-PFD-009", "0.40 MM CAGE-CORNER CANDIDATE", "RIGHT seated indicator visible"),
    _edge("PC-020", "rear_cradle_dummy_part_1", "bbox_support_anchor_front", "AI-03", "CRADLE EDGE EXTERNAL ANCHOR", "SLIDE FRONT ANCHOR FROM OUTBOARD", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE OUTBOARD", "UNIQUE FRONT OFFSET STOP", "HW-PFD-009", "0.50 MM BASE CLEARANCE", "FRONT key remains visible"),
    _edge("PC-021", "bbox_support_anchor_front", "bbox_support_front", "AI-03", "SUPPORT BASE EXTERNAL CLIP", "SLIDE SUPPORT BASE INTO FRONT ANCHOR", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; LIFT SUPPORT OUT", "FRONT SUPPORT BASE STOP", "HW-PFD-009", "0.50 MM BASE CLEARANCE", "FRONT support seat and pin visible"),
    _edge("PC-022", "bbox_support_front", "current_bbox_dummy", "AI-03", "INDEPENDENT FRONT SEAT", "LOWER BBOX -Z", "TEMPORARY VISIBLE DUMMY STRAP", "REMOVE STRAP; LIFT +Z", "FRONT SEAT WITNESS", "HW-PFD-009", "VISUAL SEAT ONLY", "B1 seat remains visible"),
    _edge("PC-023", "rear_cradle_dummy_part_2", "bbox_support_anchor_rear", "AI-03", "CRADLE EDGE EXTERNAL ANCHOR", "SLIDE REAR ANCHOR FROM OUTBOARD", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE OUTBOARD", "UNIQUE REAR OFFSET STOP", "HW-PFD-009", "0.50 MM BASE CLEARANCE", "REAR key remains visible"),
    _edge("PC-024", "bbox_support_anchor_rear", "bbox_support_rear", "AI-03", "SUPPORT BASE EXTERNAL CLIP", "SLIDE SUPPORT BASE INTO REAR ANCHOR", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; LIFT SUPPORT OUT", "REAR SUPPORT BASE STOP", "HW-PFD-009", "0.50 MM BASE CLEARANCE", "REAR support seat and pin visible"),
    _edge("PC-025", "bbox_support_rear", "current_bbox_dummy", "AI-03", "INDEPENDENT REAR SEAT", "LOWER BBOX -Z", "TEMPORARY VISIBLE DUMMY STRAP", "REMOVE STRAP; LIFT +Z", "REAR SEAT WITNESS", "HW-PFD-009", "VISUAL SEAT ONLY", "B2 seat remains visible"),
    _edge("PC-026", "current_cbox_dummy", "core_alignment_key", "AI-04", "ASYMMETRIC CORE KEY", "INSERT +Y", "VISIBLE METAL-PIN CANDIDATE VIA CARRIER", "REMOVE PIN; WITHDRAW -Y", "CBOX SIDE SHOULDER", "HW-PFD-006/HW-PFD-007", "0.40 MM FIT CANDIDATE", "CBOX boundary window visible"),
    _edge("PC-027", "current_bbox_dummy", "core_alignment_key", "AI-04", "ASYMMETRIC CORE KEY", "INSERT +Y", "VISIBLE METAL-PIN CANDIDATE VIA CARRIER", "REMOVE PIN; WITHDRAW -Y", "BBOX SIDE SHOULDER", "HW-PFD-006/HW-PFD-007", "0.40 MM FIT CANDIDATE", "BBOX boundary window visible"),
    _edge("PC-028", "core_alignment_key", "anti_separation_lock_carrier", "AI-04", "VISIBLE LOCK CARRIER", "LOWER CARRIER FROM +Z", "REMOVABLE METAL-PIN CANDIDATE", "REMOVE R-PIN AND METAL PIN; LIFT", "CARRIER WINDOW SHOULDER", "HW-PFD-006/HW-PFD-007", "6.30 MM BORE CANDIDATE", "Primary pin state visible"),
    _edge("PC-029", "current_bbox_dummy", "battery_cassette_dummy", "BATTERY-CASSETTE", "REMOVABLE CONTAINED PLACEMENT MODULE", "LOWER -Z INTO AUTHORITY ENVELOPE", "TEMPORARY VISIBLE DUMMY STRAP", "REMOVE STRAP; LIFT +Z", "AUTHORITY CONTAINMENT ENVELOPE", "HW-PFD-009", "VISUAL ENVELOPE ONLY", "Battery dummy cage remains visible"),
    _edge("PC-030", "fpb_rail_left_dummy", "profile3_rail_outer_clamp_left", "AI-05", "PROFILE OUTER ENVELOPE CLAMP", "SLIDE FROM OPEN RAIL END", "VISIBLE CLAMP-EAR DUMMY BOLT", "REMOVE BOLT; SLIDE OFF", "Y=-110 WITNESS STOP", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "LEFT clamp and Y witness visible"),
    _edge("PC-031", "profile3_rail_outer_clamp_left", "lower_adapter_visual_locator_left", "AI-05", "KEYED CLAMP TONGUE RECEIVER", "SLIDE OUTBOARD TO INBOARD", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE OUTBOARD", "LEFT OFFSET TONGUE STOP", "HW-PFD-009", "0.40 MM SLIDE CANDIDATE", "LEFT tongue key and pin visible"),
    _edge("PC-032", "lower_adapter_visual_locator_left", "lower_float_adapter_left", "AI-05", "EXISTING ADAPTER EDGE LOCATOR", "SLIDE FROM OUTBOARD EDGE", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE OUTBOARD", "FULL-WIDTH ADAPTER EDGE STOP", "HW-PFD-009", "0.50 MM EDGE CLEARANCE", "Existing adapter marking remains visible"),
    _edge("PC-033", "lower_float_adapter_left", "float_slide_receiver_left", "AI-06", "KEYED SLIDE RECEIVER", "SLIDE +Y TO STOP", "REMOVABLE 6MM-CLASS METAL PIN", "REMOVE R-PIN/PIN; SLIDE -Y", "INTEGRAL REAR STOP", "HW-PFD-006/HW-PFD-007", "0.40 MM SLIDE CANDIDATE", "LEFT pin window visible"),
    _edge("PC-034", "float_slide_receiver_left", "pin_retainer_cover", "AI-08", "SECONDARY VISIBLE RETAINER COVER", "LOWER COVER FROM +Z", "SECONDARY PRINTED COVER ONLY", "LIFT COVER AFTER PRIMARY PIN REMOVAL", "COVER LIP", "NONE PRINTED SECONDARY", "0.40 MM CLIP CANDIDATE", "Primary pin remains visible through slot"),
    _edge("PC-035", "fpb_rail_right_dummy", "profile3_rail_outer_clamp_right", "AI-05", "PROFILE OUTER ENVELOPE CLAMP", "SLIDE FROM OPEN RAIL END", "VISIBLE CLAMP-EAR DUMMY BOLT", "REMOVE BOLT; SLIDE OFF", "Y=-110 WITNESS STOP", "HW-PFD-009", "20.60 MM CHANNEL CANDIDATE", "RIGHT clamp and Y witness visible"),
    _edge("PC-036", "profile3_rail_outer_clamp_right", "lower_adapter_visual_locator_right", "AI-05", "KEYED CLAMP TONGUE RECEIVER", "SLIDE OUTBOARD TO INBOARD", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE OUTBOARD", "RIGHT OFFSET TONGUE STOP", "HW-PFD-009", "0.40 MM SLIDE CANDIDATE", "RIGHT tongue key and pin visible"),
    _edge("PC-037", "lower_adapter_visual_locator_right", "lower_float_adapter_right", "AI-05", "EXISTING ADAPTER EDGE LOCATOR", "SLIDE FROM OUTBOARD EDGE", "VISIBLE CONNECTOR-ONLY DUMMY PIN", "PULL PIN; SLIDE OUTBOARD", "FULL-WIDTH ADAPTER EDGE STOP", "HW-PFD-009", "0.50 MM EDGE CLEARANCE", "Existing adapter marking remains visible"),
    _edge("PC-038", "lower_float_adapter_right", "float_slide_receiver_right", "AI-06", "KEYED SLIDE RECEIVER", "SLIDE +Y TO STOP", "REMOVABLE 6MM-CLASS METAL PIN", "REMOVE R-PIN/PIN; SLIDE -Y", "INTEGRAL REAR STOP", "HW-PFD-006/HW-PFD-007", "0.40 MM SLIDE CANDIDATE", "RIGHT pin window visible"),
)


REMOVABLE_MODULES = {
    "current_cbox_dummy",
    "current_bbox_dummy",
    "battery_cassette_dummy",
}


AI10_RESERVATION = {
    "interface_id": "AI-10",
    "name": "PTO-DRIVE SYNC LINK v0.1",
    "printed_geometry_in_this_dummy": False,
    "drive_candidate": "Drive 20T dual-row candidate",
    "pto_candidate": "PTO 20T dual-row candidate",
    "sync_candidate": "20T:20T 1:1 sync belt",
    "downstream_candidate": "PTO downstream 20T:60T candidate",
    "axial_shaft_length": "HOLD",
    "bearing_overhang": "HOLD",
    "belt_row_spacing": "HOLD",
    "guard_envelope": "HOLD",
    "width_300mm_interference": "HOLD",
    "independent_pto_neutral_interlock": "REQUIRED",
    "load_class": "LOW-LOAD SPREADER ONLY",
    "current_dummy_guarantees_axial_space": False,
    "AI10_CLEARANCE_STATUS": "NOT_YET_AUDITED",
}


def build_physical_connection_graph() -> dict:
    mates: dict[str, list[str]] = defaultdict(list)
    edge_ids: dict[str, list[str]] = defaultdict(list)
    for edge in CONNECTION_EDGES:
        a, b = edge["nodes"]
        mates[a].append(b)
        mates[b].append(a)
        edge_ids[a].append(edge["edge_id"])
        edge_ids[b].append(edge["edge_id"])

    nodes = []
    for part in ALL_PARTS:
        nodes.append(
            {
                "part_key": part.key,
                "part_number": part.part_number,
                "filename": part.filename,
                "orientation": part.orientation_marking,
                "interface_id": part.interface_id,
                "classification": part.classification_marking,
                "physical_mates": sorted(mates[part.key]),
                "connection_edge_ids": sorted(edge_ids[part.key]),
                "interface_type": "SEE CONNECTION EDGES",
                "insertion_direction": "SEE CONNECTION EDGES",
                "retention_method": "SEE CONNECTION EDGES",
                "removal_method": "SEE CONNECTION EDGES",
                "positive_stop": "SEE CONNECTION EDGES",
                "dry_assembly_role": (
                    "REMOVABLE MODULE"
                    if part.key in REMOVABLE_MODULES
                    else "CONNECTED POSITIONING PART"
                ),
                "structural_claim": False,
            }
        )
    return {
        "schema": "PS_PHYSICAL_CONNECTION_GRAPH_V0_1",
        "nodes": nodes,
        "edges": [deepcopy(edge) for edge in CONNECTION_EDGES],
        "ai10_reservation": deepcopy(AI10_RESERVATION),
        "float_body_boundary": {
            "legacy_hardpoint_measured": False,
            "float_body_generated": False,
            "FLOAT_BODY_SET_COMPLETE": "HOLD",
            "FLOAT_EQUIPPED_FULL_DUMMY_COMPLETE": "HOLD",
        },
    }


def _adjacency(graph: dict) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {
        node["part_key"]: set() for node in graph["nodes"]
    }
    for edge in graph["edges"]:
        a, b = edge["nodes"]
        if a in adjacency and b in adjacency:
            adjacency[a].add(b)
            adjacency[b].add(a)
    return adjacency


def connected_components(graph: dict) -> list[list[str]]:
    adjacency = _adjacency(graph)
    unseen = set(adjacency)
    result = []
    while unseen:
        start = min(unseen)
        queue = deque([start])
        component = []
        unseen.remove(start)
        while queue:
            node = queue.popleft()
            component.append(node)
            for neighbor in sorted(adjacency[node]):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        result.append(sorted(component))
    return result


def validate_physical_connection_graph(graph: dict | None = None) -> dict:
    data = graph or build_physical_connection_graph()
    blockers = []
    node_keys = [node["part_key"] for node in data.get("nodes", [])]
    expected = {part.key for part in ALL_PARTS}
    if len(node_keys) != len(set(node_keys)):
        blockers.append("DUPLICATED_PHYSICAL_NODE")
    if set(node_keys) != expected:
        blockers.append("PHYSICAL_NODE_SET_MISMATCH")
    edge_ids = [edge["edge_id"] for edge in data.get("edges", [])]
    if len(edge_ids) != len(set(edge_ids)):
        blockers.append("DUPLICATED_CONNECTION_EDGE")
    for edge in data.get("edges", []):
        if len(edge.get("nodes", [])) != 2:
            blockers.append("INVALID_CONNECTION_EDGE_ARITY")
            continue
        if any(node not in expected for node in edge["nodes"]):
            blockers.append("CONNECTION_EDGE_UNKNOWN_NODE")
        for required in (
            "geometric_contact_exists",
            "retention_exists",
            "visible_confirmation_exists",
        ):
            if edge.get(required) is not True:
                blockers.append(
                    f"LOOSE_PLACEMENT_ACCEPTED:{edge.get('edge_id')}:{required}"
                )
        if edge.get("structural_claim") is not False:
            blockers.append("DUMMY_CONNECTION_STRUCTURAL_CLAIM")
        retention = str(edge.get("retention_method", "")).upper()
        if "GLUE" in retention:
            blockers.append("GLUE_ONLY_CONNECTION")
        if "TAPE" in retention:
            blockers.append("TAPE_ONLY_CONNECTION")
        if "T-NUT" in retention or "T NUT" in retention:
            blockers.append("T_NUT_ON_SLOTLESS_PROFILE3")
        if not str(edge.get("positive_stop", "")).strip():
            blockers.append("POSITIVE_STOP_MISSING")
    components = connected_components(data) if node_keys else []
    if len(components) != 1:
        blockers.append("DISCONNECTED_FINAL_ASSEMBLY_GRAPH")
    adjacency = _adjacency(data) if node_keys else {}
    orphans = sorted(key for key, neighbors in adjacency.items() if not neighbors)
    if orphans:
        blockers.append("ORPHAN_PRINTED_PART")
    ai10 = data.get("ai10_reservation", {})
    if ai10.get("AI10_CLEARANCE_STATUS") != "NOT_YET_AUDITED":
        blockers.append("AI10_CLEARANCE_SILENTLY_APPROVED")
    if ai10.get("printed_geometry_in_this_dummy") is not False:
        blockers.append("AI10_DUAL_ROW_GEOMETRY_FORBIDDEN")
    boundary = data.get("float_body_boundary", {})
    if boundary.get("float_body_generated") is not False:
        blockers.append("UNKNOWN_FLOAT_HARDPOINT_BODY_GENERATED")
    if boundary.get("FLOAT_BODY_SET_COMPLETE") != "HOLD":
        blockers.append("FLOAT_BODY_HOLD_NOT_PRESERVED")
    return {
        "status": "PASS_WITH_HOLD" if not blockers else "FAIL",
        "blockers": sorted(set(blockers)),
        "node_count": len(node_keys),
        "edge_count": len(data.get("edges", [])),
        "connected_component_count": len(components),
        "connected_components": components,
        "orphan_parts": orphans,
        "DISCONNECTED_PRINTED_PART_COUNT": len(orphans),
        "PHYSICAL_ASSEMBLY_CONNECTIVITY": (
            "PASS_WITH_HOLD" if not blockers else "FAIL"
        ),
    }


def connection_matrix_rows(graph: dict | None = None) -> list[dict]:
    data = graph or build_physical_connection_graph()
    rows = []
    for edge in data["edges"]:
        rows.append(
            {
                "edge_id": edge["edge_id"],
                "part_a": edge["nodes"][0],
                "part_b": edge["nodes"][1],
                "interface_id": edge["interface_id"],
                "interface_type": edge["interface_type"],
                "geometric_contact_exists": edge[
                    "geometric_contact_exists"
                ],
                "retention_exists": edge["retention_exists"],
                "retention_method": edge["retention_method"],
                "visible_confirmation_exists": edge[
                    "visible_confirmation_exists"
                ],
                "visible_confirmation": edge["visible_confirmation"],
                "structural_claim": edge["structural_claim"],
                "required_hardware": edge["required_hardware"],
                "mating_tolerance_candidate": edge[
                    "mating_tolerance_candidate"
                ],
                "positive_stop": edge["positive_stop"],
                "removal_method": edge["removal_method"],
            }
        )
    return rows


validate_physical_connection_graph()
