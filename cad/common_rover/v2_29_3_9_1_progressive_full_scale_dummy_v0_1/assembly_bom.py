from __future__ import annotations

from dataclasses import asdict

from dummy_component_registry import COMPONENTS
from part_number_registry import PARTS


HARDWARE_BOM: tuple[dict[str, object], ...] = (
    {
        "hardware_id": "HW-PFD-001",
        "candidate_specification": (
            "20x20 mm-class T-slot aluminum; exact supplier profile HOLD"
        ),
        "quantity": "2 x 232 mm rails; 1 x 138 mm crossmember",
        "used_interface": "AI-01, AI-02, AI-05",
        "classification": "STRUCTURAL CANDIDATE",
        "purchase_status": "NOT APPROVED",
        "unresolved_field": (
            "slot opening/depth, radius, bore, tolerance, alloy, finish, SKU"
        ),
    },
    {
        "hardware_id": "HW-PFD-002",
        "candidate_specification": "Metal 20x20 corner brackets",
        "quantity": 4,
        "used_interface": "AI-01",
        "classification": "STRUCTURAL CANDIDATE",
        "purchase_status": "NOT APPROVED",
        "unresolved_field": "SKU, thickness, alloy, load rating, corrosion",
    },
    {
        "hardware_id": "HW-PFD-003",
        "candidate_specification": "Compatible T-nuts for selected 20x20 profile",
        "quantity": 16,
        "used_interface": "AI-01, AI-05",
        "classification": "STRUCTURAL CANDIDATE",
        "purchase_status": "NOT APPROVED",
        "unresolved_field": "profile compatibility, thread engagement, SKU",
    },
    {
        "hardware_id": "HW-PFD-004",
        "candidate_specification": "M5 metal bolts",
        "quantity": 16,
        "used_interface": "AI-01, AI-02, AI-03, AI-05",
        "classification": "STRUCTURAL CANDIDATE",
        "purchase_status": "NOT APPROVED",
        "unresolved_field": "length, grade, torque, locking method, corrosion",
    },
    {
        "hardware_id": "HW-PFD-005",
        "candidate_specification": "M5 washers",
        "quantity": 16,
        "used_interface": "AI-01, AI-02, AI-03, AI-05",
        "classification": "STRUCTURAL CANDIDATE",
        "purchase_status": "NOT APPROVED",
        "unresolved_field": "OD, thickness, material, corrosion",
    },
    {
        "hardware_id": "HW-PFD-006",
        "candidate_specification": "Removable 6 mm-class metal pins",
        "quantity": 3,
        "used_interface": "AI-04, AI-06, AI-07",
        "classification": "PRIMARY RETENTION CANDIDATE",
        "purchase_status": "NOT APPROVED",
        "unresolved_field": "actual diameter, tolerance, grip length, material",
    },
    {
        "hardware_id": "HW-PFD-007",
        "candidate_specification": "R-pins compatible with removable pins",
        "quantity": 3,
        "used_interface": "AI-04, AI-06, AI-07",
        "classification": "SECONDARY RETENTION CANDIDATE",
        "purchase_status": "NOT APPROVED",
        "unresolved_field": "pin cross-hole and R-pin dimensions",
    },
    {
        "hardware_id": "HW-PFD-008",
        "candidate_specification": "Optional metal lower-frame/cradle members",
        "quantity": 2,
        "used_interface": "AI-02, AI-03",
        "classification": "STRUCTURAL CANDIDATE",
        "purchase_status": "NOT APPROVED",
        "unresolved_field": (
            "section, hardpoints, frame tie, stiffness, implement clearance"
        ),
    },
    {
        "hardware_id": "HW-PFD-009",
        "candidate_specification": (
            "Temporary dummy fasteners; nylon or low-strength metal"
        ),
        "quantity": 20,
        "used_interface": "ALL DUMMY-ONLY DRY ASSEMBLY",
        "classification": "DUMMY ONLY",
        "purchase_status": "NOT APPROVED",
        "unresolved_field": "match after real profile and pins are selected",
    },
)


ASSEMBLY_SEQUENCE: tuple[dict[str, str], ...] = (
    {
        "step": "1",
        "part_keys": (
            "fpb_rail_left_dummy,fpb_rail_right_dummy,"
            "fpb_front_crossmember_dummy"
        ),
        "quantity": "1 each",
        "orientation": "FRONT marks toward -Y; TOP marks upward",
        "interface_id": "AI-01",
        "insertion_direction": (
            "Butt crossmember ends between rail front inner faces"
        ),
        "fastener": "HW-PFD-002/003/004/005 candidates; dummy dry-fit only",
        "visible_verification": (
            "Both butt seams, FRONT marks, and reserved corner zones visible"
        ),
    },
    {
        "step": "2",
        "part_keys": "rear_cradle_dummy_part_1,rear_cradle_dummy_part_2",
        "quantity": "1 each",
        "orientation": "LEFT/RIGHT and REAR/TOP marks readable",
        "interface_id": "AI-03",
        "insertion_direction": "Bring halves toward X=0 center plane",
        "fastener": "HW-PFD-009 temporary dummy fasteners only",
        "visible_verification": (
            "Independent rear support route remains separate from CBOX"
        ),
    },
    {
        "step": "3",
        "part_keys": "cbox_saddle_left,cbox_saddle_right",
        "quantity": "1 each",
        "orientation": "LEFT/RIGHT; FRONT stops toward -Y",
        "interface_id": "AI-02",
        "insertion_direction": "Seat onto visual cradle datums from +Z",
        "fastener": "HW-PFD-009 only; metal clamp design remains HOLD",
        "visible_verification": "Both seated-indicator posts remain visible",
    },
    {
        "step": "4",
        "part_keys": "current_cbox_dummy",
        "quantity": "1",
        "orientation": "FRONT toward -Y; TOP upward",
        "interface_id": "AI-02",
        "insertion_direction": "Lower -Z into both keyed CBOX saddles",
        "fastener": "No structural fastener; dry placement only",
        "visible_verification": "Cage corners contact stops; both indicators visible",
    },
    {
        "step": "5",
        "part_keys": "bbox_support_front,bbox_support_rear",
        "quantity": "1 each",
        "orientation": "FRONT support at B1; REAR support at B2",
        "interface_id": "AI-03",
        "insertion_direction": "Place from +Z on independent rear dummy path",
        "fastener": "HW-PFD-009; structural hardpoints remain HOLD",
        "visible_verification": (
            "DUMMY ONLY / NO LOAD marks and both support feet visible"
        ),
    },
    {
        "step": "6",
        "part_keys": "current_bbox_dummy",
        "quantity": "1",
        "orientation": "REAR toward +Y; TOP upward",
        "interface_id": "AI-03",
        "insertion_direction": "Lower -Z onto both independent BBOX supports",
        "fastener": "No structural fastener; dry placement only",
        "visible_verification": "No BBOX vertical load path touches the CBOX cage",
    },
    {
        "step": "7",
        "part_keys": "core_alignment_key,anti_separation_lock_carrier",
        "quantity": "1 each",
        "orientation": "Key FRONT first; carrier lock window upward",
        "interface_id": "AI-04",
        "insertion_direction": "Insert key +Y, then carrier and metal pin candidate",
        "fastener": "HW-PFD-006/007 candidates; no printed primary latch",
        "visible_verification": "Pin state visible through carrier window",
    },
    {
        "step": "8",
        "part_keys": "battery_cassette_dummy",
        "quantity": "1",
        "orientation": "FRONT toward -Y; TOP upward",
        "interface_id": "BATTERY-CASSETTE",
        "insertion_direction": "Place only at documented authority envelope",
        "fastener": "None; real battery restraint not represented",
        "visible_verification": "All cage edges and DUMMY ONLY marking visible",
    },
    {
        "step": "9",
        "part_keys": "lower_float_adapter_left,lower_float_adapter_right",
        "quantity": "1 each",
        "orientation": "LEFT/RIGHT; BOTTOM to rail BOTTOM_SLOT",
        "interface_id": "AI-05",
        "insertion_direction": "Offer upward +Z inside Y=-125..-95 zones",
        "fastener": "HW-PFD-003/004/005 candidate only",
        "visible_verification": "BOTTOM SLOT marking and all access faces visible",
    },
    {
        "step": "10",
        "part_keys": (
            "float_slide_receiver_left,float_slide_receiver_right"
        ),
        "quantity": "1 each",
        "orientation": "LEFT/RIGHT; slide rearward +Y to stop",
        "interface_id": "AI-06",
        "insertion_direction": "Slide +Y; opposite-side key must reject",
        "fastener": "HW-PFD-006/007 candidate pins",
        "visible_verification": "Pin bores align and windows show retained pin",
    },
    {
        "step": "11",
        "part_keys": "pin_retainer_cover",
        "quantity": "1",
        "orientation": "TOP mark upward; FRONT toward -Y",
        "interface_id": "AI-08",
        "insertion_direction": "Clip only after primary pin and R-pin are visible",
        "fastener": "SECONDARY ONLY printed cover",
        "visible_verification": "Primary pin remains visible through cover slot",
    },
)


def printed_bom_records() -> list[dict]:
    component_by_key = {item.key: item for item in COMPONENTS}
    return [
        {
            **asdict(part),
            "quantity": 1,
            "structural": False,
            "direct_rail_holes": component_by_key[part.key].direct_rail_holes,
            "primary_lock": component_by_key[part.key].primary_lock,
            "host_slot": component_by_key[part.key].host_slot or "",
            "scale_percent": 100,
        }
        for part in PARTS
    ]


def hardware_bom_records() -> list[dict[str, object]]:
    return [dict(row) for row in HARDWARE_BOM]


def assembly_sequence_records() -> list[dict[str, str]]:
    return [dict(row) for row in ASSEMBLY_SEQUENCE]
