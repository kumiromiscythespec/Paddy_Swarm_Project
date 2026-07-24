from __future__ import annotations

from copy import deepcopy

from params_v229_3_4 import PARAMS as _PRIOR_PARAMS

PARAMS = deepcopy(_PRIOR_PARAMS)
PARAMS.update(
    {
        "version": "v2.29.3.5",
        "active_loop": "LOOP-001",
        "active_part": "V2292-FPB-RAIL-L",
        "part_process_class": "METAL_PART_CAD_VALIDATION",
        "print_target": False,
        "requirement_authority_order": (
            "ATTACHMENT_JOINT_RESPONSIBILITY_BEFORE_REACHABILITY"
        ),
        "full_runner_stage_count": 24,
        "production_print_stl_status": "NOT_APPLICABLE_METAL_CANDIDATE",
    }
)
