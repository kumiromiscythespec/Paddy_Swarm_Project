from __future__ import annotations

from collections import Counter

from fastener_requirement_authority import GROUP_AUTHORITY

GROUP_DETAILS = {
    "FG-002": {
        "rail_connection_purpose": "lower-adapter structural load transfer",
        "joint_type": "DOWEL_AND_BOLT_WITH_UNRESOLVED_RAIL_SIDE_PATTERN",
        "force_direction": "radial / axial / torque",
        "fastening_method": "direct bolt, clamp, or bracket not resolved",
        "hole_pattern_authority": "MEASUREMENT_REQUIRED",
        "current_coordinate_validity": "0_OF_4_RAIL_INTERIOR",
        "required_design_correction": (
            "Select direct drilling, clamp, or bracket load path and issue "
            "authoritative coordinates; do not move existing axes automatically."
        ),
        "measurement_hold": True,
        "compatibility_impact": "LOWER_INTERFACE_AND_LOAD_PATH_UNRESOLVED",
        "interior_count": 0,
        "edge_breakout_count": 0,
        "exterior_count": 4,
    },
    "FG-004": {
        "rail_connection_purpose": "front crossmember structural load transfer",
        "joint_type": "UNDEFINED_MEASUREMENT_HOLD",
        "force_direction": "radial / axial / torque",
        "fastening_method": "butt/lap/tab/weld/bracket not resolved",
        "hole_pattern_authority": "BLOCKED_BY_UNDEFINED_STRUCTURAL_JOINT",
        "current_coordinate_validity": "0_OF_4_RAIL_INTERIOR",
        "required_design_correction": (
            "Define joint and fastener method under one authority before "
            "minimum-assembly approval."
        ),
        "measurement_hold": True,
        "compatibility_impact": "MINIMUM_ASSEMBLY_BLOCKED",
        "interior_count": 0,
        "edge_breakout_count": 0,
        "exterior_count": 4,
    },
    "FG-006": {
        "rail_connection_purpose": "motor bracket torque and radial load transfer",
        "joint_type": "BOLTED_ANGLE_BRACKET",
        "force_direction": "motor torque / radial / axial",
        "fastening_method": "four M4-class rail through holes",
        "hole_pattern_authority": "ATT-006_AND_FASTENER_REGISTRY",
        "current_coordinate_validity": "4_OF_4_FULL_CIRCLE_INTERIOR_PROXY",
        "required_design_correction": (
            "No coordinate change; execute Solid holes, seat, insertion, "
            "tool-access, and edge-strength validation."
        ),
        "measurement_hold": True,
        "compatibility_impact": "EDGE_STRENGTH_REQUIRES_ENGINEERING_APPROVAL",
        "interior_count": 4,
        "edge_breakout_count": 0,
        "exterior_count": 0,
    },
    "FG-008": {
        "rail_connection_purpose": "input cartridge belt and axial load transfer",
        "joint_type": "SLOT_AND_BOLT_UNDERDEFINED",
        "force_direction": "belt radial / shaft axial / tension reaction",
        "fastening_method": "slot-and-bolt claimed; slot geometry absent",
        "hole_pattern_authority": "DESIGN_CONTRADICTION",
        "current_coordinate_validity": "0_INTERIOR_2_EDGE_BREAKOUT_2_EXTERIOR",
        "required_design_correction": (
            "Issue slot/notch geometry and retention authority or correct host; "
            "do not reinterpret boundary circles as slots."
        ),
        "measurement_hold": True,
        "compatibility_impact": "INPUT_CARTRIDGE_ATTACHMENT_UNRESOLVED",
        "interior_count": 0,
        "edge_breakout_count": 2,
        "exterior_count": 2,
    },
    "FG-009": {
        "rail_connection_purpose": "output bridge belt and PTO load transfer",
        "joint_type": "BOLTED_FLANGE_PATTERN_CONFLICT",
        "force_direction": "belt radial / PTO reaction",
        "fastening_method": "four-fastener flange claimed",
        "hole_pattern_authority": "DESIGN_CONTRADICTION",
        "current_coordinate_validity": "0_INTERIOR_1_EDGE_BREAKOUT_3_EXTERIOR",
        "required_design_correction": (
            "Define a complete load path and valid rail/bracket pattern; "
            "single boundary-axis support is not approved."
        ),
        "measurement_hold": True,
        "compatibility_impact": "OUTPUT_BRIDGE_LOAD_PATH_UNRESOLVED",
        "interior_count": 0,
        "edge_breakout_count": 1,
        "exterior_count": 3,
    },
    "FG-020": {
        "rail_connection_purpose": "servo bridge torque and cam load transfer",
        "joint_type": "BOLTED_FLANGE_RAIL_RESPONSIBILITY_CONFLICT",
        "force_direction": "servo torque / cam radial",
        "fastening_method": "four-fastener flange claimed",
        "hole_pattern_authority": "DESIGN_CONTRADICTION",
        "current_coordinate_validity": "0_INTERIOR_2_EDGE_BREAKOUT_2_EXTERIOR",
        "required_design_correction": (
            "Define left/right rail responsibility and issue coordinates; "
            "do not move Z=24 axes or boundary holes automatically."
        ),
        "measurement_hold": True,
        "compatibility_impact": "SERVO_BRIDGE_RAIL_SPLIT_UNRESOLVED",
        "interior_count": 0,
        "edge_breakout_count": 2,
        "exterior_count": 2,
    },
}


def audit_attachment_groups(authority_rows):
    by_group = {}
    for row in authority_rows:
        by_group.setdefault(row["group_id"], []).append(row)
    audits = []
    for group_id in sorted(GROUP_DETAILS):
        rows = by_group.get(group_id, [])
        detail = GROUP_DETAILS[group_id]
        policy = GROUP_AUTHORITY[group_id]
        audits.append(
            {
                "group_id": group_id,
                "instance_count": len(rows),
                "group_status": policy["group_status"],
                "rail_connection_purpose": detail["rail_connection_purpose"],
                "rail_hole_necessity": policy["requirement_status"],
                "mating_component": (
                    rows[0]["mating_component"] if rows else "MISSING"
                ),
                "joint_type": detail["joint_type"],
                "force_direction": detail["force_direction"],
                "fastening_method": detail["fastening_method"],
                "hole_pattern_authority": detail["hole_pattern_authority"],
                "current_coordinate_validity": detail[
                    "current_coordinate_validity"
                ],
                "required_design_correction": detail[
                    "required_design_correction"
                ],
                "measurement_hold": detail["measurement_hold"],
                "compatibility_impact": detail["compatibility_impact"],
                "fully_interior_candidate_count": detail["interior_count"],
                "edge_breakout_candidate_count": detail[
                    "edge_breakout_count"
                ],
                "rail_exterior_candidate_count": detail["exterior_count"],
            }
        )
    return audits


def summarize_group_contradictions(audits):
    statuses = Counter(row["group_status"] for row in audits)
    errors = []
    if len(audits) != 6:
        errors.append("EXPECTED_SIX_RAIL_ATTACHMENT_GROUPS")
    if sum(row["instance_count"] for row in audits) != 24:
        errors.append("GROUP_INSTANCE_ACCOUNTING_MISMATCH")
    if any(row["instance_count"] != 4 for row in audits):
        errors.append("GROUP_QUANTITY_MISMATCH")
    return {
        "status": "PASS_WITH_CONTRADICTION_HOLD" if not errors else "FAIL",
        "group_count": len(audits),
        "instance_count": sum(row["instance_count"] for row in audits),
        "group_status_counts": dict(statuses),
        "groups_requiring_design_or_measurement_resolution": sum(
            row["group_status"] != "RAIL_HOLE_PATTERN_VALID"
            for row in audits
        ),
        "errors": errors,
    }
