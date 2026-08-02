"""Design-authority parameters for the linked low-profile sump zone."""

from __future__ import annotations


PROJECT = "PS-MHT-8T-LINKED-SUMP-V001"
PHASE = "4T-LS-A"
STATUS = (
    "ARCHITECTURE_AND_REFERENCE_CAD_COMPLETE_"
    "PHYSICAL_COMPONENT_MEASUREMENT_PENDING"
)
REFERENCE_ONLY = True
FINAL_PRINT_PARTS_GENERATED = False
STL_GENERATION_ALLOWED = False

maximum_tower_count = 8
initial_indoor_tower_count = 4
test_tower_counts = (4, 6, 8)
circulation_pump_count = 1
hydraulic_connection = "PARALLEL_BRANCH_EQUALIZATION"
serial_daisy_chain_allowed = False
management_zone = "ONE_SHARED_NUTRIENT_ZONE_MAXIMUM_8_TOWERS"

local_sump_commercial_materials = ("PP", "PE")
local_sump_watertight_authority = "PURCHASED_PP_OR_PE_CONTAINER"
local_sump_measurement_status = "MEASUREMENT_PENDING"
local_sump_vented = True
local_sump_airtight_allowed = False
local_sump_gross_capacity_l = (12.0, 16.0)
local_sump_normal_volume_l = (5.0, 7.0)
local_sump_emergency_freeboard_l = (4.0, 6.0)
local_sump_outer_height_mm = (110.0, 130.0)
local_sump_reference_outer_size_mm = (420.0, 320.0, 120.0)
local_sump_reference_normal_depth_mm = (40.0, 55.0)
local_sump_reference_maximum_depth_mm = (75.0, 85.0)
local_sump_high_level_reference_mm = 100.0
local_sump_supports_tower_load = False
local_sump_openable_for_cleaning = True
local_sump_complete_drain_required = True

tower_support_deck_elevation_mm = (160.0, 170.0, 180.0)
tower_bottom_drain_elevation_mm = (190.0, 205.0, 220.0)
tower_reference_load_kg = 20.0
tower_load_path = "DRY_FOUR_CORNER_SUPPORT_DIRECT_TO_FLOOR"
pipe_load_supported_by_sump_wall = False

local_sump_branch_inner_diameter_mm = (25.0, 32.0)
common_trunk_inner_diameter_mm = (32.0, 40.0)
common_trunk_slope_candidates = (0.0, 1.0 / 200.0, 1.0 / 100.0)
common_trunk_slope_selected = None
common_trunk_route = "PROTECTED_REAR_SERVICE_ROUTE"
equalization_valve_count = 8
upper_supply_valve_count = 8
branch_identifiers = tuple("ABCDEFGH")
commercial_valve_status = "PHYSICAL_MEASUREMENT_PENDING"
commercial_bulkhead_status = "PHYSICAL_MEASUREMENT_PENDING"
printed_sliding_valve_allowed = False
printed_thread_only_watertight_joint_allowed = False
printed_small_petg_check_valve_allowed = False

emergency_overflow_count = 8
emergency_overflow_inner_diameter_mm = (25.0, 32.0)
emergency_overflow_destination = "NON_CIRCULATING_EMERGENCY_RECEIVER"
emergency_overflow_reconnects_circulation = False
common_safety_trough_normally_dry = True

common_pump_well_present = True
common_pump_well_location = "NEAR_TRUNK_MIDPOINT"
common_pump_well_outer_height_mm = (150.0, 200.0)
common_pump_well_watertight_authority = "PURCHASED_PP_OR_PE_CONTAINER"
common_pump_well_measurement_status = "PHYSICAL_MEASUREMENT_PENDING"

pump_model_reference = "Tencen_submersible"
pump_voltage_v = 12.0
pump_power_nameplate_w = 20.0
pump_zero_head_maximum_flow_l_h = 700.0
pump_maximum_head_m = 6.0
pump_discharge_nipple_nominal_mm = 13.0
pump_eight_tower_capacity_status = "NOT_QUALIFIED"
pump_bypass_always_available = True
per_tower_target_flow_l_min = (0.5, 1.0)
zone_target_flow_l_min = {
    4: (2.0, 4.0),
    6: (3.0, 6.0),
    8: (4.0, 8.0),
}
zone_target_flow_l_h = {
    4: (120.0, 240.0),
    6: (180.0, 360.0),
    8: (240.0, 480.0),
}

fresh_water_tank_volume_l = 10.0
fresh_water_system_separate_from_circulation = True
fresh_water_to_tower_at_night = "CLOSED"
fresh_water_tank_load_supported_by_tower = False
room_ceiling_height_mm = 2300.0
upper_fresh_water_tank_shelf_elevation_mm = (1650.0, 1700.0, 1750.0)
upper_tank_maximum_top_elevation_mm = 2050.0
minimum_ceiling_clearance_mm = 250.0

room_length_mm = "MEASUREMENT_PENDING"
room_width_mm = "MEASUREMENT_PENDING"
minimum_human_aisle_width_mm = 600.0
preferred_human_aisle_width_mm = (700.0, 800.0)

tower_buffer_per_band_l = 0.4
tower_band_count = 5
tower_buffer_per_tower_l = tower_buffer_per_band_l * tower_band_count
pipe_volume_status = "MEASUREMENT_PENDING"
pump_well_operating_volume_status = "MEASUREMENT_PENDING"

circulation_energy_measurement_name = "CIRCULATION_PUMP_ONLY_Wh"
circulation_energy_includes_fresh_water_equipment = False
circulation_energy_includes_sensors = False
circulation_energy_includes_timer_standby = False

ISOLATION_SEQUENCE = (
    "CLOSE_UPPER_SUPPLY",
    "WAIT_FOR_TOWER_DRAIN_TO_LOCAL_SUMP",
    "CONFIRM_LOCAL_LEVEL_STABLE",
    "CLOSE_EQUALIZATION_VALVE",
    "DISCONNECT_OR_SERVICE_TOWER_AND_SUMP",
)
RECONNECTION_SEQUENCE = (
    "VERIFY_SUMP_CLEAN",
    "VERIFY_EC_AND_PH_COMPATIBLE",
    "MATCH_LOCAL_WATER_LEVEL_TO_ZONE",
    "OPEN_EQUALIZATION_VALVE_SLOWLY",
    "CHECK_FOR_LEAKS",
    "OPEN_UPPER_SUPPLY",
    "CONFIRM_RETURN_FLOW",
)
equalization_first_isolation_allowed = False

shared_zone_constraints = (
    "DO_NOT_MIX_DIFFERENT_FERTILIZER_CONCENTRATIONS",
    "DO_NOT_MIX_DIFFERENT_TREATMENT_CONDITIONS",
    "ISOLATE_SUSPECTED_DISEASE_IMMEDIATELY",
    "CLEAN_ISOLATED_SUMP_BEFORE_RECONNECTION",
    "CLEAN_NUTRIENT_SOLUTION_PATH_AND_TRUNK_AS_REQUIRED",
    "CLEANING_DOES_NOT_REDUCE_DISEASE_TRANSMISSION_RISK_TO_ZERO",
)

commercial_watertight_authority = (
    "PP_OR_PE_LOCAL_SUMP",
    "PP_OR_PE_COMMON_PUMP_WELL",
    "FULL_PORT_UNION_BALL_VALVE",
    "BULKHEAD_FITTING",
    "EPDM_GASKET",
    "25_TO_32MM_FLEXIBLE_HOSE",
    "32_TO_40MM_COMMON_TRUNK",
    "HOSE_CLAMP",
    "WATERTIGHT_CLEANING_CAP",
    "CIRCULATION_PUMP",
)
printed_reference_candidates = (
    "BULKHEAD_REINFORCEMENT_PLATE",
    "EXTERNAL_LOAD_DISTRIBUTION_PLATE",
    "VALVE_GUARD",
    "TRUNK_SUPPORT",
    "HOSE_SUPPORT",
    "SUMP_INTERNAL_PARTITION",
    "SETTLING_BAY",
    "PUMP_MOUNT",
    "INTAKE_STRAINER",
    "WATER_LEVEL_GUIDE",
    "HIGH_LEVEL_FLOAT_GUIDE",
    "TOWER_BOTTOM_RECEIVER_CUP",
    "SPLASH_COVER",
    "DRY_SUPPORT_DECK",
    "SAFETY_TROUGH_SUPPORT",
    "A_TO_H_LABELS",
)
printed_reference_candidates_status = "NOT_FINAL_MEASUREMENT_PENDING"
petg_watertight_15l_tank_allowed = False


def validate_parameters() -> None:
    if maximum_tower_count != 8 or circulation_pump_count != 1:
        raise ValueError("Phase 4T-LS-A must remain an eight-tower, one-pump zone")
    if hydraulic_connection != "PARALLEL_BRANCH_EQUALIZATION":
        raise ValueError("linked sumps must use parallel equalization")
    if serial_daisy_chain_allowed:
        raise ValueError("serial sump daisy chains are prohibited")
    if not local_sump_vented or local_sump_airtight_allowed:
        raise ValueError("local sumps must be vented and non-airtight")
    if local_sump_gross_capacity_l != (12.0, 16.0):
        raise ValueError("local sump gross-capacity reference changed")
    if local_sump_normal_volume_l != (5.0, 7.0):
        raise ValueError("local sump normal-volume reference changed")
    if local_sump_emergency_freeboard_l[0] < 4.0:
        raise ValueError("local sump emergency freeboard is below 4 L")
    if local_sump_branch_inner_diameter_mm[0] < 25.0:
        raise ValueError("branch ID is below 25 mm")
    if common_trunk_inner_diameter_mm[0] < 32.0:
        raise ValueError("trunk ID is below 32 mm")
    if not (
        equalization_valve_count
        == upper_supply_valve_count
        == emergency_overflow_count
        == maximum_tower_count
    ):
        raise ValueError("each tower requires supply, equalization and overflow")
    if emergency_overflow_reconnects_circulation:
        raise ValueError("emergency overflow must not reconnect circulation")
    if local_sump_supports_tower_load or pipe_load_supported_by_sump_wall:
        raise ValueError("sump walls must not carry tower or pipe loads")
    if upper_tank_maximum_top_elevation_mm > (
        room_ceiling_height_mm - minimum_ceiling_clearance_mm
    ):
        raise ValueError("upper tank violates ceiling clearance")
    if room_length_mm != "MEASUREMENT_PENDING" or room_width_mm != "MEASUREMENT_PENDING":
        raise ValueError("room floor dimensions must remain measurement-pending")
    if pump_eight_tower_capacity_status != "NOT_QUALIFIED":
        raise ValueError("nameplate flow cannot qualify eight-tower operation")
    if FINAL_PRINT_PARTS_GENERATED or STL_GENERATION_ALLOWED:
        raise ValueError("Phase 4T-LS-A must not generate print parts or STL")
    if petg_watertight_15l_tank_allowed:
        raise ValueError("printed PETG is not the watertight tank authority")


validate_parameters()
