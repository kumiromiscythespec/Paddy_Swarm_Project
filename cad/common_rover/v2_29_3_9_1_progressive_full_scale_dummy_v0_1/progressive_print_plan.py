from __future__ import annotations

from dataclasses import dataclass

from part_number_registry import PART_BY_KEY


@dataclass(frozen=True)
class PrintStep:
    print_number: int
    part_key: str
    quantity: int
    estimated_risk: str
    inspection_points: str
    stop_conditions: str
    next_part_unlocked: str
    prerequisite: str


_ORDER = (
    ("cbox_saddle_left", "MEDIUM", "marking, warp, FRONT key, cage-corner fit", "P0-P4 failure", "cbox_saddle_right", "P0 source integrity"),
    ("cbox_saddle_right", "MEDIUM", "marking, mirror relation, seated indicator", "LEFT first article not PASS; P0-P4 failure", "current_cbox_dummy", "cbox_saddle_left PASS P0-P4"),
    ("current_cbox_dummy", "HIGH", "130x140x105 envelope, open cage, marking, warp", "saddle set not PASS; any dimension mismatch", "bbox_support_front", "CBOX saddle set PASS"),
    ("bbox_support_front", "MEDIUM", "independent feet, DUMMY/NO LOAD/NOT STRUCTURAL marks", "P0-P4 failure", "bbox_support_rear", "CBOX growth gate PASS"),
    ("bbox_support_rear", "MEDIUM", "independent support path, asymmetric rear key", "front support not PASS; P0-P4 failure", "core_alignment_key", "bbox_support_front PASS P0-P4"),
    ("core_alignment_key", "LOW", "asymmetric insertion, Y=0 alignment, full marking", "reversed insertion accepted; P0-P4 failure", "anti_separation_lock_carrier", "BBOX supports PASS"),
    ("anti_separation_lock_carrier", "MEDIUM", "6mm-class bore, lock window, glove access", "printed latch becomes primary; window obscured", "current_bbox_dummy", "alignment key PASS P0-P4"),
    ("current_bbox_dummy", "HIGH", "150x220x150 envelope, open cage, independent seat", "BBOX rests on CBOX; dimension mismatch", "battery_cassette_dummy", "BBOX interface set PASS"),
    ("battery_cassette_dummy", "HIGH", "125x180x120 envelope, open cage, no electrical claim", "dimension mismatch; cage omission", "lower_float_adapter_left", "body dummy growth gate PASS"),
    ("lower_float_adapter_left", "MEDIUM", "BOTTOM_SLOT marking, zone metadata, side key", "off BOTTOM_SLOT; direct rail hole; P0-P4 failure", "lower_float_adapter_right", "profile audit PROFILE-3 acknowledged"),
    ("lower_float_adapter_right", "MEDIUM", "mirror relation, BOTTOM_SLOT marking, side key", "LEFT first article not PASS; P0-P4 failure", "float_slide_receiver_left", "lower_float_adapter_left PASS P0-P4"),
    ("float_slide_receiver_left", "MEDIUM", "slide clearance, pin bore/window, positive stop", "reversed insertion accepted; pin misalignment", "float_slide_receiver_right", "adapter pair PASS"),
    ("float_slide_receiver_right", "MEDIUM", "mirror relation, pin window, positive stop", "LEFT first article not PASS; P0-P4 failure", "pin_retainer_cover", "float_slide_receiver_left PASS P0-P4"),
    ("pin_retainer_cover", "LOW", "SECONDARY ONLY mark, primary pin remains visible", "cover acts as primary; hides pin", "fpb_rail_left_dummy", "receiver pair PASS"),
    ("fpb_rail_left_dummy", "HIGH", "20x20x232 envelope, marking, brim, warp", "bed clearance/warp/marking failure", "fpb_rail_right_dummy", "float interface growth gate PASS"),
    ("fpb_rail_right_dummy", "HIGH", "mirror marking, 20x20x232, brim and warp", "LEFT first article not PASS; P0-P4 failure", "fpb_front_crossmember_dummy", "fpb_rail_left_dummy PASS P0-P4"),
    ("fpb_front_crossmember_dummy", "MEDIUM", "138x20x20, FRONT/TOP marks, no holes", "rail pair not PASS; envelope mismatch", "rear_cradle_dummy_part_1", "rail pair PASS"),
    ("rear_cradle_dummy_part_1", "MEDIUM", "LEFT mark, dummy-only independent path", "structural claim; P0-P4 failure", "rear_cradle_dummy_part_2", "frame front set PASS"),
    ("rear_cradle_dummy_part_2", "MEDIUM", "RIGHT mirror, join visibility, all HOLD marks", "part 1 not PASS; full assembly growth failure", "FULL DUMMY DRY ASSEMBLY", "rear_cradle_dummy_part_1 PASS P0-P4"),
)

PRINT_STEPS: tuple[PrintStep, ...] = tuple(
    PrintStep(index, row[0], 1, *row[1:])
    for index, row in enumerate(_ORDER, start=1)
)

MIRROR_GATE_PAIRS = (
    ("cbox_saddle_left", "cbox_saddle_right"),
    ("lower_float_adapter_left", "lower_float_adapter_right"),
    ("float_slide_receiver_left", "float_slide_receiver_right"),
    ("fpb_rail_left_dummy", "fpb_rail_right_dummy"),
    ("rear_cradle_dummy_part_1", "rear_cradle_dummy_part_2"),
)

GATES = (
    {
        "gate": "P0",
        "name": "Source integrity",
        "checks": (
            "authority PASS_WITH_HOLD; seed PASS_WITH_HOLD; Assembly Interface "
            "PASS_WITH_HOLD; unique part number; finite valid STL; scale 100%"
        ),
    },
    {
        "gate": "P1",
        "name": "First-layer and marking",
        "checks": (
            "correct bed contact; zero floating geometry; readable part number, "
            "R00, orientation, DUMMY/FIT TEST classification"
        ),
    },
    {
        "gate": "P2",
        "name": "Dimensional",
        "checks": (
            "bounding dimensions; critical fits; hole diameter; slide "
            "clearance; left/right mirror relation"
        ),
    },
    {
        "gate": "P3",
        "name": "Functional fit",
        "checks": (
            "saddle fit; positive stop; pin alignment; visible lock; reversed "
            "insertion rejection; glove access"
        ),
    },
    {
        "gate": "P4",
        "name": "Assembly growth",
        "checks": (
            "part remains usable in final dummy; no prior accepted part is "
            "discarded; failure stops all dependent prints"
        ),
    },
)


def validate_print_order(steps: tuple[PrintStep, ...] = PRINT_STEPS) -> dict:
    keys = [step.part_key for step in steps]
    if len(keys) != len(set(keys)):
        raise ValueError("DUPLICATED_PRINT_STEP")
    if set(keys) != set(PART_BY_KEY):
        raise ValueError("PRINT_PLAN_PART_SET_MISMATCH")
    positions = {key: index for index, key in enumerate(keys)}
    for first, mirror in MIRROR_GATE_PAIRS:
        if positions[mirror] <= positions[first]:
            raise ValueError("MIRROR_PRINTED_BEFORE_FIRST_SIDE_GATE")
        mirror_step = next(step for step in steps if step.part_key == mirror)
        if f"{first} PASS P0-P4" not in mirror_step.prerequisite:
            raise ValueError("MIRROR_GATE_PREREQUISITE_MISSING")
    if any(step.quantity != 1 for step in steps):
        raise ValueError("ALL_PARTS_ONE_PLATE_RECOMMENDATION_FORBIDDEN")
    return {
        "status": "PASS",
        "print_count": len(steps),
        "standalone_coupon_required": False,
        "all_parts_one_plate_recommended": False,
        "mirror_gate_pair_count": len(MIRROR_GATE_PAIRS),
    }


def progressive_print_markdown() -> str:
    validate_print_order()
    lines = [
        "# Progressive production-style print order",
        "",
        "Every print is a final-use dummy part. Print one step at a time at "
        "100% scale. A failed P0-P4 gate stops every dependent step; do not "
        "print a mirror until its first-side part passes.",
        "",
    ]
    for step in PRINT_STEPS:
        part = PART_BY_KEY[step.part_key]
        lines.extend(
            (
                f"## Print {step.print_number:02d} — {part.part_number}",
                "",
                f"- STL filename: `{part.filename}`",
                f"- Quantity at this step: {step.quantity}",
                f"- Material: {part.material}",
                f"- Orientation: {part.print_orientation}",
                f"- Support: {part.support}",
                f"- Brim: {part.brim}",
                f"- Estimated risk: {step.estimated_risk}",
                f"- Prerequisite: {step.prerequisite}",
                f"- Inspection points: {step.inspection_points}",
                f"- Stop conditions: {step.stop_conditions}",
                f"- Next part unlocked by PASS: {step.next_part_unlocked}",
                "",
            )
        )
    lines.extend(
        (
            "## Gate definitions",
            "",
        )
    )
    for gate in GATES:
        lines.append(
            f"- {gate['gate']} — {gate['name']}: {gate['checks']}"
        )
    lines.extend(
        (
            "",
            "Never place the complete kit on one print plate.",
            "",
        )
    )
    return "\n".join(lines)


def quality_gate_rows() -> list[dict[str, object]]:
    rows = []
    for step in PRINT_STEPS:
        part = PART_BY_KEY[step.part_key]
        for gate in GATES:
            rows.append(
                {
                    "print_number": step.print_number,
                    "part_number": part.part_number,
                    "stl_filename": part.filename,
                    "gate": gate["gate"],
                    "gate_name": gate["name"],
                    "required_check": gate["checks"],
                    "result": "NOT YET INSPECTED",
                    "inspector": "",
                    "evidence": "",
                    "stop_on_fail": "YES",
                }
            )
    return rows


validate_print_order()
