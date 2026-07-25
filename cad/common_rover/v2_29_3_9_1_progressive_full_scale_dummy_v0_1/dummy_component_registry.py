from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

from part_number_registry import PARTS, PrintedPart


@dataclass(frozen=True)
class ComponentGeometryRecord:
    key: str
    part: PrintedPart
    builder_module: str
    builder_function: str
    expected_envelope_source: str
    structural: bool
    primary_lock: str
    direct_rail_holes: bool
    host_slot: str | None = None
    assembly_role: str = "FULL_SCALE_DUMMY_FINAL_PART"


def _r(
    key: str,
    module: str,
    function: str,
    envelope: str,
    *,
    primary_lock: str = "NONE_DUMMY_POSITIONING_ONLY",
    host_slot: str | None = None,
) -> ComponentGeometryRecord:
    part = next(item for item in PARTS if item.key == key)
    return ComponentGeometryRecord(
        key,
        part,
        module,
        function,
        envelope,
        structural=False,
        primary_lock=primary_lock,
        direct_rail_holes=False,
        host_slot=host_slot,
    )


COMPONENTS: tuple[ComponentGeometryRecord, ...] = (
    _r(
        "current_cbox_dummy",
        "box_dummy_geometry",
        "build_current_cbox_dummy",
        "authority.fixed_body.current_dimensions.CBOX",
    ),
    _r(
        "current_bbox_dummy",
        "box_dummy_geometry",
        "build_current_bbox_dummy",
        "authority.fixed_body.current_dimensions.BBOX",
    ),
    _r(
        "battery_cassette_dummy",
        "battery_dummy_geometry",
        "build_battery_cassette_dummy",
        "authority.fixed_body.current_dimensions.BATTERY_CASSETTE",
    ),
    _r(
        "cbox_saddle_left",
        "box_saddle_geometry",
        "build_cbox_saddle_left",
        "AI-02 current CBOX positioning envelope",
        primary_lock="CANDIDATE_METAL_CLAMP_NOT_PRINTED_LATCH",
    ),
    _r(
        "cbox_saddle_right",
        "box_saddle_geometry",
        "build_cbox_saddle_right",
        "AI-02 current CBOX positioning envelope",
        primary_lock="CANDIDATE_METAL_CLAMP_NOT_PRINTED_LATCH",
    ),
    _r(
        "bbox_support_front",
        "rear_support_model",
        "build_bbox_support_front",
        "DUMMY_ONLY independent support representation",
        primary_lock="NONE_NOT_STRUCTURAL",
    ),
    _r(
        "bbox_support_rear",
        "rear_support_model",
        "build_bbox_support_rear",
        "DUMMY_ONLY independent support representation",
        primary_lock="NONE_NOT_STRUCTURAL",
    ),
    _r(
        "core_alignment_key",
        "box_saddle_geometry",
        "build_core_alignment_key",
        "AI-04 Y=0 alignment concept",
        primary_lock="CANDIDATE_METAL_PIN_SEPARATE",
    ),
    _r(
        "anti_separation_lock_carrier",
        "box_saddle_geometry",
        "build_anti_separation_lock_carrier",
        "AI-04 visible lock window",
        primary_lock="REMOVABLE_METAL_PIN",
    ),
    _r(
        "lower_float_adapter_left",
        "float_interface_geometry",
        "build_lower_float_adapter_left",
        "LOWER-ADAPTER-L authority zone",
        primary_lock="METAL_M5_T_NUT_CANDIDATE",
        host_slot="BOTTOM_SLOT",
    ),
    _r(
        "lower_float_adapter_right",
        "float_interface_geometry",
        "build_lower_float_adapter_right",
        "LOWER-ADAPTER-R authority zone",
        primary_lock="METAL_M5_T_NUT_CANDIDATE",
        host_slot="BOTTOM_SLOT",
    ),
    _r(
        "float_slide_receiver_left",
        "float_interface_geometry",
        "build_float_slide_receiver_left",
        "AI-06 legacy float hardpoint candidate",
        primary_lock="REMOVABLE_6MM_CLASS_METAL_PIN",
    ),
    _r(
        "float_slide_receiver_right",
        "float_interface_geometry",
        "build_float_slide_receiver_right",
        "AI-06 legacy float hardpoint candidate",
        primary_lock="REMOVABLE_6MM_CLASS_METAL_PIN",
    ),
    _r(
        "pin_retainer_cover",
        "float_interface_geometry",
        "build_pin_retainer_cover",
        "AI-08 secondary retainer envelope",
        primary_lock="SECONDARY_ONLY_NOT_PRIMARY",
    ),
    _r(
        "fpb_rail_left_dummy",
        "frame_profile_model",
        "build_fpb_rail_left_dummy",
        "authority.frame.rail_envelopes.LEFT",
    ),
    _r(
        "fpb_rail_right_dummy",
        "frame_profile_model",
        "build_fpb_rail_right_dummy",
        "authority.frame.rail_envelopes.RIGHT",
    ),
    _r(
        "fpb_front_crossmember_dummy",
        "frame_profile_model",
        "build_fpb_front_crossmember_dummy",
        "authority.front_crossmember.envelope_mm",
    ),
    _r(
        "rear_cradle_dummy_part_1",
        "rear_support_model",
        "build_rear_cradle_dummy_part_1",
        "DUMMY_ONLY unresolved rear cradle half",
    ),
    _r(
        "rear_cradle_dummy_part_2",
        "rear_support_model",
        "build_rear_cradle_dummy_part_2",
        "DUMMY_ONLY unresolved rear cradle half",
    ),
)

COMPONENT_BY_KEY = {component.key: component for component in COMPONENTS}


def load_builder(component: ComponentGeometryRecord) -> Callable:
    module = __import__(component.builder_module)
    return getattr(module, component.builder_function)


def registry_records() -> list[dict]:
    return [
        {
            **asdict(component),
            "part": asdict(component.part),
        }
        for component in COMPONENTS
    ]


def validate_component_registry(
    components: tuple[ComponentGeometryRecord, ...] = COMPONENTS,
) -> dict:
    keys = [component.key for component in components]
    part_keys = [part.key for part in PARTS]
    if len(keys) != len(set(keys)):
        raise ValueError("DUPLICATED_COMPONENT_KEY")
    if set(keys) != set(part_keys):
        raise ValueError("PART_COMPONENT_REGISTRY_MISMATCH")
    if any(component.direct_rail_holes for component in components):
        raise ValueError("DIRECT_RAIL_HOLE_FORBIDDEN")
    for component in components:
        if component.key.startswith("lower_float_adapter"):
            if component.host_slot != "BOTTOM_SLOT":
                raise ValueError("LOWER_ADAPTER_OFF_BOTTOM_SLOT")
    return {
        "status": "PASS",
        "component_count": len(components),
        "bbox_independent_support": all(
            key in keys
            for key in ("bbox_support_front", "bbox_support_rear")
        ),
        "direct_rail_holes": 0,
    }


validate_component_registry()
