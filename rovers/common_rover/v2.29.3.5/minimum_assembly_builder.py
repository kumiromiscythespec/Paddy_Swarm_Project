from __future__ import annotations
from cad_assembly import build_part

ACTIVE_PART = "V2292-FPB-RAIL-L"
REQUIRED_COMPONENTS = (
    ("V2292-FPB-RAIL-L", "ACTIVE_RAIL", "active validation solid"),
    ("V2292-FPB-FRONT-XMEMBER", "STRUCTURAL_JOINT", "rail/crossmember joint"),
    ("V2292-LOWER-ADAPTER", "STRUCTURAL_CONTACT", "lower load-path attachment"),
    ("V2292-MOTOR-BRACKET-L", "STRUCTURAL_BRACKET", "nearest rail bracket"),
)
OPTIONAL_COMPONENTS = (
    ("V2292-INPUT-CARTRIDGE-L", "OPTIONAL_COLLISION_REFERENCE"),
    ("V2292-OUTPUT-BRIDGE-L", "OPTIONAL_COLLISION_REFERENCE"),
    ("V2292-SERVO-BRIDGE", "OPTIONAL_COLLISION_REFERENCE"),
)

def create_minimum_assembly_manifest(registries, joints):
    components = {
        item["part_id"]: item for item in registries["components"]
    }
    required = []
    for part_id, role, reason in REQUIRED_COMPONENTS:
        required.append({
            "part_id": part_id, "required": True, "role": role,
            "classification_reason": reason,
            "registry_present": part_id in components,
            "missing_consequence": "HARD_FAILURE_NO_COLLISION_PASS",
        })
    optional = []
    for part_id, role in OPTIONAL_COMPONENTS:
        optional.append({
            "part_id": part_id, "required": False, "role": role,
            "classification_reason":
                "adjacent attachment retained as optional visual/collision reference",
            "registry_present": part_id in components,
            "missing_consequence": "WARNING_OR_CONDITIONAL_HOLD",
        })
    fastener_groups = sorted({
        group for joint in joints for group in joint["fastener_groups"]
    } | {"FG-002", "FG-004", "FG-006"})
    return {
        "loop_id": "LOOP-001", "active_part_id": ACTIVE_PART,
        "required_components": required, "optional_components": optional,
        "required_component_count": len(required),
        "optional_component_count": len(optional),
        "fastener_groups": fastener_groups,
        "required_service_sweeps": [
            "BOLT_INSERTION", "TOOL_ACCESS", "RAIL_REMOVAL",
        ],
        "execution_order": [
            "LOAD_MANIFEST", "BUILD_ALL_REQUIRED", "HARD_BUILD_ERROR_GATE",
            "APPLY_TRANSFORMS", "LOAD_JOINT_REGISTRY",
            "EVALUATE_JOINT", "FORBIDDEN_COLLISION",
            "FASTENER_AXIS", "BOLT_SWEEP", "TOOL_SWEEP",
            "ASSEMBLY_PATH", "REMOVAL_PATH", "AGGREGATE_GATE",
        ],
        "empty_assembly_collision_pass_forbidden": True,
    }

def validate_minimum_assembly_manifest(manifest):
    errors = []
    required = {
        item["part_id"]: item for item in manifest.get("required_components", [])
    }
    expected = {item[0] for item in REQUIRED_COMPONENTS}
    if set(required) != expected:
        errors.append("required component set mismatch")
    if any(item.get("required") is not True for item in required.values()):
        errors.append("required component marked optional")
    optional = manifest.get("optional_components", [])
    if any(item.get("required") is not False for item in optional):
        errors.append("optional component marked required")
    if manifest.get("required_component_count") != len(expected):
        errors.append("required component count mismatch")
    if not manifest.get("empty_assembly_collision_pass_forbidden"):
        errors.append("empty assembly collision pass not forbidden")
    return errors

def build_minimum_assembly(
    manifest, registries, params, active_solid=None,
):
    solids = {}
    build_rows = []
    for item in manifest["required_components"]:
        part_id = item["part_id"]
        try:
            if part_id == ACTIVE_PART and active_solid is not None:
                solid = active_solid
                method = "ACTIVE_VALIDATED_SOLID"
            else:
                solid = build_part(part_id, params, registries)
                method = "CAD_ASSEMBLY_BUILD_PART"
            solids[part_id] = solid
            build_rows.append({
                "part_id": part_id, "required": True,
                "status": "BUILT", "method": method, "error": "",
            })
        except Exception as exc:
            build_rows.append({
                "part_id": part_id, "required": True,
                "status": "BUILD_FAILED", "method": "CAD_ASSEMBLY_BUILD_PART",
                "error": str(exc),
            })
    required_failures = sum(
        row["required"] and row["status"] != "BUILT"
        for row in build_rows
    )
    return {
        "solids": solids, "build_rows": build_rows,
        "required_component_build_failure_count": required_failures,
        "complete": (
            not required_failures
            and len(solids) == manifest["required_component_count"]
        ),
        "collision_inspection_allowed": not required_failures,
    }
