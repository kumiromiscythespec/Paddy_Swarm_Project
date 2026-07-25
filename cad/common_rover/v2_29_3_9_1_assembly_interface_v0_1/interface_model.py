from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from authority_adapter import (
    AUTHORITY_RELATIVE,
    LANE_RELATIVE,
    AuthorityContext,
    authority_sources,
)
from coupon_geometry import printed_part_manifest_records


REQUIRED_INTERFACE_IDS = tuple(f"AI-{index:02d}" for index in range(1, 10))
REQUIRED_MARKINGS = (
    "FRONT",
    "REAR",
    "LEFT",
    "RIGHT",
    "TOP",
    "BOTTOM",
)
REQUIRED_CONNECTION_MARKINGS = (
    "A1",
    "A2",
    "B1",
    "B2",
    "F1",
    "F2",
    "L1",
    "L2",
)
REQUIRED_OPERATION_MARKINGS = (
    "1 INSERT",
    "2 SLIDE",
    "3 LOCK",
    "4 VERIFY",
)
REQUIRED_DIAGRAMS = (
    "exploded_assembly_isometric.svg",
    "assembly_sequence.svg",
    "connection_map_top.svg",
    "connection_map_side.svg",
    "load_path_diagram.svg",
    "cbox_saddle_interface.svg",
    "bbox_support_interface.svg",
    "float_slide_pin_interface.svg",
    "thumb_latch_secondary_only.svg",
)
REQUIRED_COUPONS = (
    "coupon_01_tslot_saddle_fit.stl",
    "coupon_02_slide_fit.stl",
    "coupon_03_pin_alignment.stl",
    "coupon_04_thumb_latch_secondary.stl",
    "coupon_05_marking_readability.stl",
)


@dataclass(frozen=True)
class InterfaceRecord:
    interface_id: str
    connected_components: tuple[str, ...]
    primary_secondary: str
    function_classification: str
    assembly_direction: str
    removal_direction: str
    fastener_candidate: str
    visible_confirmation_point: str
    positive_stop: str
    anti_rotation_feature: str
    dirt_water_escape: str
    failure_mode: str
    human_intervention_method: str
    authority_source: tuple[str, ...]
    unresolved_values: tuple[str, ...]
    manufacturing_geometry_status: str = "CONCEPT_ONLY"


def _src(name: str) -> str:
    return (AUTHORITY_RELATIVE / name).as_posix()


def build_interfaces(context: AuthorityContext) -> tuple[InterfaceRecord, ...]:
    zones = context.zone_by_id
    lower_left = zones["LOWER-ADAPTER-L"]
    lower_right = zones["LOWER-ADAPTER-R"]
    return (
        InterfaceRecord(
            interface_id="AI-01",
            connected_components=(
                "V22939-FPB-RAIL-L",
                "V22939-FPB-RAIL-R",
                "V22939-FPB-FRONT-XMEMBER",
            ),
            primary_secondary="PRIMARY",
            function_classification="STRUCTURAL",
            assembly_direction=(
                "BUTT front crossmember end faces to rail inner faces"
            ),
            removal_direction="Separate after metal bracket bolts are removed",
            fastener_candidate=(
                "Existing metal T-slot corner brackets, T-nuts, and metal bolts"
            ),
            visible_confirmation_point=(
                "Both corner brackets, bolt heads, and butt-face seams remain visible"
            ),
            positive_stop="Rail end / crossmember butt-face datum",
            anti_rotation_feature="Paired metal corner brackets",
            dirt_water_escape="Open T-slot ends and exposed bracket faces",
            failure_mode="Bolt loosening or bracket deformation opens a visible seam",
            human_intervention_method="One hex-key size; inspect both brackets",
            authority_source=(
                _src("front_crossmember_authority.json"),
                _src("slot_zone_authority.json"),
            ),
            unresolved_values=(
                "Bolt grade, torque, bracket SKU, and corrosion system remain HOLD",
            ),
            manufacturing_geometry_status="AUTHORITY_RECONFIRMED_NO_REDESIGN",
        ),
        InterfaceRecord(
            interface_id="AI-02",
            connected_components=(
                "V22939-CBOX",
                "PRINTED-CBOX-SADDLE",
                "METAL-LOWER-FRAME-CRADLE",
            ),
            primary_secondary="PRIMARY",
            function_classification="STRUCTURAL + POSITIONING",
            assembly_direction="Drop CBOX downward (-Z) into keyed saddle",
            removal_direction="Lift CBOX upward (+Z) after primary clamp removal",
            fastener_candidate=(
                "Metal clamp to validated cradle member; M5-class candidate"
            ),
            visible_confirmation_point=(
                "A1/A2 saddle witness lines and both metal clamp heads visible"
            ),
            positive_stop="Printed saddle floor and asymmetric FRONT shoulder",
            anti_rotation_feature="LEFT/RIGHT asymmetric saddle keys",
            dirt_water_escape="Open-bottom saddle channels and lateral mud reliefs",
            failure_mode=(
                "Saddle wear allows motion; metal clamp retains primary load path"
            ),
            human_intervention_method=(
                "Release two visible clamps with one hex key and lift with gloves"
            ),
            authority_source=(
                _src("fixed_body_dimension_authority.json"),
                _src("body_frame_authority.json"),
                _src("slot_zone_authority.json"),
            ),
            unresolved_values=(
                "CBOX saddle wall clearance remains a fit-test value",
                "Cradle member section and registered attachment are unresolved HOLD",
                "Clamp geometry, bolt grade, and torque are unresolved HOLD",
            ),
        ),
        InterfaceRecord(
            interface_id="AI-03",
            connected_components=(
                "V22939-BBOX",
                "PRINTED-BBOX-SADDLE",
                "INDEPENDENT-METAL-REAR-SUPPORT-BRIDGE",
            ),
            primary_secondary="PRIMARY",
            function_classification="STRUCTURAL + POSITIONING",
            assembly_direction="Drop BBOX downward (-Z) onto independent rear bridge",
            removal_direction="Lift BBOX upward (+Z) after bridge clamps are removed",
            fastener_candidate=(
                "Metal clamp to independent rear support; candidate only"
            ),
            visible_confirmation_point=(
                "B1/B2 seat witness marks and both primary clamp heads visible"
            ),
            positive_stop="Independent bridge seat; not the CBOX wall",
            anti_rotation_feature="Front/rear asymmetric bridge saddle keys",
            dirt_water_escape="Open bridge, drain gaps, and shovel-access mud relief",
            failure_mode=(
                "Bridge attachment failure releases BBOX; CBOX is not a cantilever"
            ),
            human_intervention_method=(
                "Visible clamp removal with one hex key; bridge remains glove-accessible"
            ),
            authority_source=(
                _src("fixed_body_dimension_authority.json"),
                _src("hardware_envelope_registry.json"),
            ),
            unresolved_values=(
                "Rear structural support authority is not established: HOLD",
                "Bridge section, attachment anchors, stiffness, and clamp geometry: HOLD",
                "No BBOX support manufacturing shape is authorized in v0.1",
            ),
            manufacturing_geometry_status="HOLD_NO_MANUFACTURING_SHAPE",
        ),
        InterfaceRecord(
            interface_id="AI-04",
            connected_components=(
                "V22939-CBOX",
                "V22939-BBOX",
                "METAL-ANTI-SEPARATION-LINK",
            ),
            primary_secondary="PRIMARY",
            function_classification="POSITIONING + ANTI-SEPARATION",
            assembly_direction="Install link after both boxes are independently seated",
            removal_direction="Remove link before either box is lifted",
            fastener_candidate="Visible removable metal pin or metal clamp candidate",
            visible_confirmation_point="A2/B1 alignment window and retained metal pin",
            positive_stop="Y=0 box boundary alignment shoulders",
            anti_rotation_feature="Front/rear asymmetric link tongue",
            dirt_water_escape="Through-window and downward drain slot",
            failure_mode=(
                "Link loss permits separation but must not carry BBOX vertical weight"
            ),
            human_intervention_method="Pull visible R-pin, then withdraw metal link pin",
            authority_source=(
                _src("fixed_body_dimension_authority.json"),
                _src("coordinate_authority.json"),
            ),
            unresolved_values=(
                "Link pin diameter, edge distances, and box hardpoints remain HOLD",
            ),
        ),
        InterfaceRecord(
            interface_id="AI-05",
            connected_components=(
                "V22939-FPB-RAIL-L",
                "V22939-FPB-RAIL-R",
                "PRINTED-LOWER-FLOAT-ADAPTERS",
            ),
            primary_secondary="PRIMARY",
            function_classification="STRUCTURAL + POSITIONING",
            assembly_direction="Offer adapter upward (+Z) to each BOTTOM_SLOT",
            removal_direction="Lower adapter (-Z) after T-slot bolts are released",
            fastener_candidate="Metal M5 T-slot fasteners and T-nuts candidate",
            visible_confirmation_point=(
                "L1/L2 witness marks and all lower bolt heads visible from below"
            ),
            positive_stop=str(lower_left["positive_stop_relation"]),
            anti_rotation_feature="LEFT/RIGHT asymmetric keyed lower-frame shoulder",
            dirt_water_escape="Open-bottom slot access and downward drain relief",
            failure_mode="T-nut slip or printed wear becomes visible at witness marks",
            human_intervention_method="One hex key from below; no hidden fastener",
            authority_source=(
                _src("slot_zone_authority.json"),
                _src("slot_cross_registry_mapping.json"),
                _src("body_frame_authority.json"),
            ),
            unresolved_values=(
                f"LEFT placement remains within authority zone {lower_left['zone_interval']}",
                f"RIGHT placement remains within authority zone {lower_right['zone_interval']}",
                "Exact symbolic end clearance E and adapter geometry remain HOLD",
            ),
        ),
        InterfaceRecord(
            interface_id="AI-06",
            connected_components=(
                "PRINTED-LOWER-FLOAT-ADAPTER",
                "PRINTED-FLOAT-SLIDE-RECEIVER",
                "FLOAT-MODULE",
            ),
            primary_secondary="PRIMARY",
            function_classification="STRUCTURAL + POSITIONING",
            assembly_direction="1 INSERT, then 2 SLIDE rearward (+Y) to hard stop",
            removal_direction="Withdraw forward (-Y) after AI-07 pin removal",
            fastener_candidate=(
                "Keyed slide transfers bearing; AI-07 metal pin prevents separation"
            ),
            visible_confirmation_point="F1/F2 stop witness marks and pin window align",
            positive_stop="Front/rear asymmetric closed-end slide shoulder",
            anti_rotation_feature="Different LEFT/RIGHT key widths and noncentral rib",
            dirt_water_escape="Open-ended mud channel with downward drain slots",
            failure_mode="Printed guide wear increases play; metal pin remains primary lock",
            human_intervention_method=(
                "Brush channel, pull with gloves, and use visible extraction face"
            ),
            authority_source=(
                _src("slot_zone_authority.json"),
                _src("coordinate_authority.json"),
            ),
            unresolved_values=(
                "Slide tongue width and bearing length remain coupon-derived HOLD values",
                "Float module hardpoint geometry is unresolved HOLD",
            ),
        ),
        InterfaceRecord(
            interface_id="AI-07",
            connected_components=(
                "PRINTED-FLOAT-SLIDE-RECEIVER",
                "PRINTED-LOWER-FLOAT-ADAPTER",
                "REMOVABLE-METAL-PIN",
                "METAL-R-PIN",
            ),
            primary_secondary="PRIMARY",
            function_classification="STRUCTURAL LOCK",
            assembly_direction="3 LOCK: insert pin laterally (±X) only at slide stop",
            removal_direction="Remove R-pin, then withdraw main pin laterally",
            fastener_candidate="6 mm-class removable metal pin plus metal R-pin",
            visible_confirmation_point=(
                "Pin head, R-pin, and green VERIFY window remain visible after assembly"
            ),
            positive_stop="Pin bores align only at AI-06 positive stop",
            anti_rotation_feature="Keyed D-head or retained pin-head flat candidate",
            dirt_water_escape="Oversize drain notch below pin bore; both ends accessible",
            failure_mode=(
                "Missing R-pin permits pin migration; visible state changes to NOT LOCKED"
            ),
            human_intervention_method="Gloved manual R-pin pull; drift access from far side",
            authority_source=(
                _src("slot_zone_authority.json"),
                _src("fastener_boundary_authority.json"),
            ),
            unresolved_values=(
                "Pin diameter tolerance, pin grade, R-pin size, and edge distances: HOLD",
            ),
        ),
        InterfaceRecord(
            interface_id="AI-08",
            connected_components=(
                "LIGHTWEIGHT-SERVICE-COVER",
                "PRINTED-THUMB-LATCH",
            ),
            primary_secondary="SECONDARY",
            function_classification="COVER ONLY",
            assembly_direction="Press cover down (-Z) until latch clicks",
            removal_direction="Press thumb pad and lift cover (+Z)",
            fastener_candidate="Printed thumb latch; secondary retention only",
            visible_confirmation_point="Latch hook is visible through VERIFY window",
            positive_stop="Rigid cover flange, independent of latch flexure",
            anti_rotation_feature="Asymmetric cover hinge / tab spacing",
            dirt_water_escape="Open latch pocket with finger and washout access",
            failure_mode="Latch fracture releases only lightweight service cover",
            human_intervention_method="Gloved thumb press; tool pry notch for mud release",
            authority_source=(
                (LANE_RELATIVE / "README.md").as_posix(),
            ),
            unresolved_values=(
                "Latch thickness and clearance remain coupon comparison values",
            ),
            manufacturing_geometry_status="FIT_TEST_COUPON_ONLY",
        ),
        InterfaceRecord(
            interface_id="AI-09",
            connected_components=(
                "V22939-BATTERY-CASSETTE",
                "V22939-BBOX",
                "RESERVED-CONNECTOR-SHUTTLE",
            ),
            primary_secondary="PRIMARY + SECONDARY",
            function_classification="SEATING + LATCH SEQUENCE RESERVATION",
            assembly_direction="Insert and guide cassette to seat before connector motion",
            removal_direction=(
                "De-energize, retract connector shuttle, release safety then primary latch"
            ),
            fastener_candidate=(
                "Primary mechanical latch plus independent safety latch; both unresolved"
            ),
            visible_confirmation_point=(
                "Seat witness mark, primary indicator, safety indicator, sensor result"
            ),
            positive_stop="Mechanical cassette seat; connector is not a stop",
            anti_rotation_feature="Asymmetric guide reservation prevents reverse insertion",
            dirt_water_escape="Reserved lower drain path; sealing remains waterproof HOLD",
            failure_mode=(
                "Latch/sensor failure blocks connector motion and drive authorization"
            ),
            human_intervention_method=(
                "Manual mechanical isolation and glove-accessible latch sequence"
            ),
            authority_source=(
                _src("fixed_body_dimension_authority.json"),
                _src("hardware_envelope_registry.json"),
                _src("known_hold_registry.json"),
            ),
            unresolved_values=(
                "Latch geometry, seat hardpoints, sensors, and shuttle location: HOLD",
                "No electrical connector implementation or manufacturing shape in v0.1",
            ),
            manufacturing_geometry_status="RESERVATION_ONLY",
        ),
    )


def architecture_comparison() -> list[dict[str, Any]]:
    dimensions = (
        "authority alignment",
        "existing slot-zone conflicts",
        "load path",
        "part count",
        "assembly clarity",
        "field repair",
        "mud accumulation",
        "water drainage",
        "printed material",
        "metal material",
        "box removal",
        "float removal",
        "implement interference",
        "failure consequence",
    )
    rows = [
        (
            "OPTION A",
            "FPB rail-mounted CBOX saddles + independent rear BBOX bridge",
            (
                "PARTIAL: FPB is authoritative; rear bridge is not",
                "HIGH: CBOX spans motor/input rail-top zones",
                "Good for CBOX; BBOX bridge attachment remains HOLD",
                "Medium",
                "Good",
                "Good at front; bridge-specific at rear",
                "Moderate around top saddles",
                "Good with open saddles",
                "Medium",
                "Medium",
                "Good",
                "Independent",
                "Rail-top competition with front implements",
                "Local saddle or bridge failure; BBOX must remain independent",
            ),
        ),
        (
            "OPTION B",
            "Front-to-rear metal LOWER-FRAME cradle + drop-in CBOX/BBOX saddles",
            (
                "BEST CONCEPT FIT: existing lower-adapter relation; rear tie remains HOLD",
                "LOW if restricted to registered BOTTOM_SLOT adapter relation",
                "Continuous metal cradle; boxes independently clamped",
                "Medium",
                "BEST: one visible backbone and numbered drop-in seats",
                "Good: replaceable printed saddles and accessible metal members",
                "Low with open longitudinal members",
                "BEST: unobstructed downward paths",
                "Low to medium",
                "Medium to high",
                "BEST: vertical drop-in after visible clamps",
                "BEST: slide + pin remains separate",
                "Lower placement needs implement envelope validation",
                "Cradle damage affects both boxes; independent clamps limit propagation",
            ),
        ),
        (
            "OPTION C",
            "Replaceable printed undertray + metal longitudinal supports",
            (
                "PARTIAL: metal supports plausible; tray geometry is not authoritative",
                "Medium; support attachments unregistered",
                "Metal members carry load; tray positions only",
                "High",
                "Good, but tray can hide fasteners",
                "Good tray replacement; difficult hidden support inspection",
                "HIGH: tray collects paddy mud",
                "Requires many drains",
                "HIGH",
                "Medium",
                "Good if tray remains open",
                "Good",
                "Broad undertray has highest implement interference risk",
                "Tray damage can obscure locks and trap debris",
            ),
        ),
    ]
    return [
        {
            "option_id": option,
            "architecture": name,
            "ratings": dict(zip(dimensions, values)),
        }
        for option, name, values in rows
    ]


def build_interface_manifest(context: AuthorityContext) -> dict[str, Any]:
    parameters = context.parameters
    zone_audit = {
        "registered_zone_ids": sorted(context.zone_by_id),
        "lower_adapter_zone_ids": [
            "LOWER-ADAPTER-L",
            "LOWER-ADAPTER-R",
        ],
        "lower_adapter_slot_face": "BOTTOM_SLOT",
        "lower_adapter_conflict_count": 0,
        "front_corner_reserved_interval_y_mm": context.slot_zones[
            "front_joint_reserved_interval_y_mm"
        ],
        "front_corner_conflict_count": 0,
        "output_bridge_zone_y_mm": context.zone_by_id[
            "OUTPUT-BRIDGE-L"
        ]["zone_interval"],
        "servo_bridge_zone_y_mm": context.zone_by_id[
            "SERVO-BRIDGE-L"
        ]["zone_interval"],
        "motor_zones_y_mm": {
            side: context.zone_by_id[f"MOTOR-ADAPTER-{side}"][
                "zone_interval"
            ]
            for side in ("L", "R")
        },
        "input_zones_y_mm": {
            side: context.zone_by_id[f"INPUT-CARTRIDGE-{side}"][
                "zone_interval"
            ]
            for side in ("L", "R")
        },
        "legacy_output_anchor_status": context.slot_zones[
            "legacy_output_anchor_y_minus_238_status"
        ],
        "new_anchor_count": 0,
        "direct_rail_holes_added": False,
    }
    interfaces = [asdict(record) for record in build_interfaces(context)]
    return {
        "schema": "PS_COMMON_ROVER_V229391_ASSEMBLY_INTERFACE_V0_1",
        "status": "PASS_WITH_HOLD",
        "purpose": (
            "Separate primary structure, printed positioning, removable locks, "
            "secondary latches, mistake-proofing, and human assembly sequence."
        ),
        "authority_version": parameters.version,
        "authority_source_tree": {
            "algorithm": context.authority_tree_algorithm,
            "expected_sha256": context.authority_tree_expected_sha256,
            "actual_sha256": context.authority_tree_actual_sha256,
        },
        "authority_sources": authority_sources(context),
        "exact_seed_solid_ids": list(context.seed_report["required_solid_ids"]),
        "coordinate_axes": {
            axis: values
            for axis, values in sorted(context.coordinate["axes"].items())
        },
        "dimensions_from_authority": {
            "component_dimensions_mm": context.fixed_body[
                "current_dimensions"
            ],
            "core_length_mm": parameters.core_length_mm,
            "bare_frame_width_mm": parameters.bare_frame_width_mm,
            "registered_maximum_interface_width_mm": (
                parameters.registered_interface_width_mm
            ),
            "operational_hard_limit_mm": parameters.operational_hard_limit_mm,
        },
        "width_classification": {
            "bare_frame_width_mm": parameters.bare_frame_width_mm,
            "registered_width_mm": parameters.registered_interface_width_mm,
            "hard_limit_mm": parameters.operational_hard_limit_mm,
        },
        "architecture_comparison": architecture_comparison(),
        "recommended_architecture": {
            "option_id": "OPTION B",
            "name": (
                "Metal LOWER-FRAME cradle with independent CBOX/BBOX "
                "drop-in saddles"
            ),
            "reason": (
                "It gives the clearest continuous metal load path, keeps printed "
                "parts sacrificial/positioning-only, preserves the registered "
                "BOTTOM_SLOT lower-adapter relation, and leaves the float slide "
                "lock independent."
            ),
            "manufacturing_status": "HOLD",
            "hold_reason": (
                "Rear BBOX bridge attachment and cradle dimensions are not "
                "established by authority."
            ),
        },
        "interfaces": interfaces,
        "slot_zone_audit": zone_audit,
        "assembly_markings": {
            "orientation": list(REQUIRED_MARKINGS),
            "connections": list(REQUIRED_CONNECTION_MARKINGS),
            "operations": list(REQUIRED_OPERATION_MARKINGS),
            "left_right_keys_asymmetric": True,
            "front_rear_stops_asymmetric": True,
            "reverse_insertion_reaches_stop": False,
            "pin_alignment_only_at_positive_stop": True,
            "lock_state_visible": True,
            "hidden_fasteners_allowed": False,
        },
        "fastener_policy": {
            "candidate_set": [
                "M5 T-slot fasteners",
                "one hex-key size",
                "6 mm-class removable metal pin",
                "metal R-pin",
            ],
            "purchase_approved": False,
            "unknown_fastener_silently_accepted": False,
        },
        "thumb_latch_policy": {
            "classification": "SECONDARY_ONLY",
            "allowed": [
                "lightweight cover",
                "inspection lid",
                "dummy model",
                "secondary anti-separation",
                "pin-loss cover",
            ],
            "forbidden": [
                "float primary fixing",
                "box primary fixing",
                "aluminum frame joint",
                "motor support",
                "PTO support",
                "heavy primary fixing",
            ],
        },
        "electrical_policy": {
            "connector_structural_load": False,
            "connector_implementation": "NOT_IN_SCOPE",
        },
        "unresolved_dimension_policy": {
            "status": "HOLD",
            "manufacturing_dimensions_created": [],
            "rule": (
                "Unresolved values remain symbolic or coupon candidates; none "
                "become manufacturing dimensions."
            ),
        },
        "required_diagrams": list(REQUIRED_DIAGRAMS),
        "required_coupons": list(REQUIRED_COUPONS),
        "printed_part_identification_policy": {
            "required": True,
            "filename_only_identification_allowed": False,
            "physical_marking_required": True,
            "missing_part_number_result": "FAIL",
            "duplicate_part_number_result": "FAIL",
            "part_number_geometry_mismatch_result": "FAIL",
        },
        "printed_parts": printed_part_manifest_records(),
        "coupon_policy": {
            "fit_test_only": True,
            "full_rover_part": False,
            "load_test_part": False,
            "target_printer": "Bambu Lab A1",
            "scale_percent": 100,
            "support_preference": "NO_SUPPORT",
        },
        "output_policy": {
            "repository_generated_files_allowed": False,
            "full_size_structural_stl_allowed": False,
            "generated_output_location": "EXTERNAL_ARTIFACT_DIRECTORY_ONLY",
        },
        "release_holds": {
            key: value
            for key, value in sorted(context.holds.items())
            if key != "version"
        },
        "additional_holds": {
            "FULL_DUMMY_PRINT": "HOLD",
            "ELECTRICAL_SAFETY_STATUS": "NOT_VALIDATED",
        },
    }


def clone_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(manifest)
