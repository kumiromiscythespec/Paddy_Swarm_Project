from __future__ import annotations

import copy
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from full_loop_runner import STAGES, run_static_authority
from registry_loader import load_registries

REGISTRIES = load_registries(SOURCE)
STATIC = run_static_authority(REGISTRIES, SOURCE)
AUTHORITY = STATIC["authority_rows"]
GROUPS = STATIC["group_rows"]
CONTAINMENT = STATIC["containment_rows"]
SEATS = STATIC["seat_rows"]
ROUTES = STATIC["routing_rows"]


def install_matrix_tests(test_case, prefix, count, predicate):
    for index in range(count):
        def test(self, case=index):
            self.assertTrue(predicate(case), f"{prefix}:{case}")

        setattr(test_case, f"test_{prefix}_{index:03d}", test)


def final_gate_context():
    return {
        "fastener_requirement_authority_status": "CONTRADICTION",
        "design_contradiction_count": 12,
        "required_hole_authority_undefined_count": 0,
        "required_hole_static_unreachable_count": 0,
        "required_hole_edge_breakout_count": 0,
        "required_hole_seat_failure_count": 0,
        "required_hole_material_continuity_failure_count": 0,
        "required_component_build_failure_count": 0,
        "forbidden_collision_count": 0,
        "required_contact_failure_count": 0,
        "bolt_insertion_obstruction_count": 0,
        "tool_access_obstruction_count": 0,
        "rail_removal_obstruction_count": 0,
        "rail_crossmember_joint_status": "MEASUREMENT_HOLD",
        "minimum_assembly_status": "BLOCKED_BY_UNDEFINED_STRUCTURAL_JOINT",
        "technical_gate_status": "CONDITIONAL_HOLD",
        "external_image_review_status": "PENDING_EXTERNAL_REVIEW",
        "blocking_issue_count": 0,
        "required_reinspection_count": 0,
        "critical_not_visible_count": 0,
        "package_seal_status": "PASS_FINAL_SEAL",
    }


def deep_static_copy():
    return copy.deepcopy(STATIC)
