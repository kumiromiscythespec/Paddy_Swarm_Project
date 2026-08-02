"""Single source of dimensional truth for PS-MHT-V001.

Linear dimensions are millimetres, angles are degrees, and volumes are mm^3.
Values tagged CALIBRATION_PENDING are provisional until physical coupons or
purchased parts have been measured.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan, degrees, isclose


CALIBRATION_PENDING = "CALIBRATION_PENDING"
ASSUMPTION = "ASSUMPTION"
FIXED_SPECIFICATION = "FIXED_SPECIFICATION"

# Tower fixed specification.
tower_body_diameter = 200.0
tower_max_diameter = 240.0
module_height = 170.0
module_count = 5
irrigation_top_height = 100.0
plant_port_count = 3
total_plant_ports = module_count * plant_port_count
plant_port_center_angle = 120.0
plant_port_diameter = 60.0
plant_port_flange_diameter = 68.0
plant_port_angle = 27.0
plant_port_local_angles = (0.0, 120.0, 240.0)
plant_port_center_z = 85.0
port_z_offset_pattern_candidate_a = (0.0, 0.0, 0.0)
port_z_offset_pattern_candidate_b = (-15.0, 0.0, 15.0)
selected_port_z_offset_pattern = "A"
module_rotation_offset = 60.0
tower_nominal_height = 1090.0

# Printed shell and future module interface.
module_wall_thickness = 3.0
plant_port_wall_thickness = 4.0
interface_lip_height = 8.0
interface_radial_clearance = 0.4  # per side
gasket_cord_diameter = 3.0
# Deprecated compatibility alias. Use gasket_cord_diameter in new code.
gasket_diameter = gasket_cord_diameter
gasket_groove_width = 3.6
gasket_groove_depth = 2.2
fastener_count = 3
module_fastener_size = "M4"
fit_clearance_xy = 0.30
fit_clearance_z = 0.20

# Phase 3A common planting-port receiver.  The tower-side receiver remains
# independent of any purchased net-pot dimensions.
port_receiver_bore_diameter = 72.0
port_receiver_outer_diameter = 86.0
port_receiver_length = 12.0
port_receiver_start_radius = 87.0
port_saddle_outer_diameter = 94.0
port_saddle_length = 5.0
port_saddle_blend_radius_target = 4.0
port_receiver_key_width = 5.0
port_receiver_key_depth = 2.0
port_adapter_outer_diameter = 71.30
port_adapter_inner_diameter = 66.0
port_adapter_body_length = 10.0
port_adapter_flange_diameter = 80.0
port_adapter_flange_thickness = 4.0
port_adapter_fit_clearance = (
    0.5 * (port_receiver_bore_diameter - port_adapter_outer_diameter)
)
port_rain_return_lip_height = 2.0
port_gasket_outer_diameter = 78.0
port_gasket_inner_diameter = 72.0
port_gasket_thickness = 1.5
m3_clearance_diameter = 3.4
m3_fastener_pitch_radius = 43.0
m3_fastener_boss_radius = 7.5
m3_fastener_count = 2
m3_metal_nut_across_flats = 5.5
m3_metal_nut_thickness = 2.4
m3_port_cartridge_clearance = 0.30
m3_port_cartridge_clearance_candidates = (0.20, 0.30, 0.40)
m3_port_cartridge_length = 9.4
m3_port_cartridge_width = 8.4
m3_port_cartridge_height = 4.8
m3_port_cartridge_fastener_x = -1.0
m3_port_cartridge_center_offset = 1.0
m3_port_cartridge_bottom_z = 3.0
m3_port_retainer_gate_thickness = 2.6
m3_port_retainer_gate_width = 12.6
m3_port_retainer_gate_height = 7.0
m3_port_retainer_arm_length = 10.0
m3_port_retainer_arm_width = 9.0
m3_port_retainer_arm_thickness = 2.4
m3_port_retainer_center_offset = 7.2
m3_port_retainer_bottom_z = 2.0
m3_port_slot_minimum_wall = 3.0
m3_port_lug_housing_width = 19.0
m3_port_lug_housing_length = 15.0
port_service_sweep_length = 130.0
finger_access_diameter = 30.0
m3_tool_access_diameter = 10.0

# Phase 3A purchased nominal-60 net-pot reference.  These are ASSUMPTION
# values, not measurements.  All remain CALIBRATION_PENDING.
netpot_nominal_size = 60.0
netpot_flange_outer_diameter = 68.0
netpot_body_top_outer_diameter = 60.0
netpot_body_bottom_outer_diameter = 42.0
netpot_body_height = 55.0
netpot_flange_thickness = 2.0
netpot_lip_height = 3.0
netpot_taper_angle = degrees(
    atan(
        0.5
        * (
            netpot_body_top_outer_diameter
            - netpot_body_bottom_outer_diameter
        )
        / netpot_body_height
    )
)
netpot_slot_width = 3.0
netpot_slot_count = 12
netpot_fit_clearance = 0.35
netpot_insertion_clearance = 1.0
netpot_adapter_outer_diameter = (
    port_adapter_inner_diameter - 2.0 * netpot_fit_clearance
)
netpot_adapter_seat_diameter = (
    netpot_body_top_outer_diameter + 2.0 * netpot_fit_clearance
)
netpot_adapter_flange_diameter = 72.0
netpot_adapter_body_length = 8.0

# Phase 3A foldable purchased PP/PE mesh root-sleeve references.
root_sleeve_material_reference = "PURCHASED_PP_OR_PE_FLEXIBLE_MESH"
root_sleeve_sector_angle = 110.0
root_sleeve_inner_radius = 5.0
root_sleeve_outer_radius = 95.0
root_sleeve_height = 104.0
root_sleeve_bottom_z = 30.0
root_sleeve_collapsed_diameter = 48.0
root_sleeve_collapsed_length = 105.0
root_sleeve_overlap_limit = 1_000.0
rear_drain_service_wedge_center = 90.0
rear_drain_service_wedge_angle = 20.0
rear_drain_service_inner_radius = 45.0
root_ring_passage_clearance = 0.50
root_ring_passage_clearance_candidates = (0.35, 0.50, 0.70)
root_sleeve_retaining_ring_outer_diameter = 63.5
root_sleeve_retaining_ring_max_diameter = (
    port_adapter_inner_diameter - 2.0 * root_ring_passage_clearance
)
root_sleeve_retaining_ring_inner_diameter = 60.7
root_sleeve_retaining_ring_thickness = 4.0
root_stop_insert_outer_diameter = 60.0
root_stop_insert_thickness = 3.0

# Phase 2 external module interface.
index_station_count = 6
index_station_step = 60.0
interface_station_offset = 30.0
interface_outer_diameter = 220.0
interface_flange_height = 8.0
interface_socket_roof_thickness = 2.0
interface_spigot_inner_diameter = (
    tower_body_diameter - 2.0 * module_wall_thickness
)
interface_spigot_outer_diameter = 206.0
interface_socket_outer_diameter = (
    interface_spigot_outer_diameter + 2.0 * interface_radial_clearance
)
interface_key_radial_height = 2.0
interface_key_tangential_width = 8.0
interface_key_axial_height = 2.2
interface_key_clearance = 0.30
interface_load_contact_width = (
    0.5 * interface_outer_diameter
    - 0.5 * interface_socket_outer_diameter
)
interface_boss_diameter = 16.0
interface_fastener_pitch_radius = 110.0
m4_clearance_diameter = 4.5
m4_star_knob_envelope_diameter = 18.0
m4_star_knob_envelope_height = 8.0
m4_bolt_length = 22.0
m4_washer_diameter = 9.0
m4_nut_across_flats = 7.0
m4_nut_thickness = 3.2
m4_heat_set_insert_hole_diameter = 5.6
m4_heat_set_insert_depth = 6.0
cartridge_fit_clearance = 0.30
available_fastener_angles = tuple(
    interface_station_offset + index * index_station_step
    for index in range(index_station_count)
)
used_fastener_angles = (30.0, 150.0, 270.0)
future_plant_port_angles = tuple(
    index * index_station_step for index in range(index_station_count)
)
rear_service_angle = 90.0

# Phase 3R print-result-driven refactoring.  These coexist with the immutable
# Phase 1 through Phase 3A.1 parameters above.
phase3r_min_isolated_footprint = 200.0
phase3r_min_independent_width = 15.0
phase3r_min_structural_wall = 3.0
phase3r_min_root_thickness = 4.0
phase3r_min_small_hole_surround = 3.0
phase3r_min_rib_width = 5.0
phase3r_preferred_root_fillet = 3.5
phase3r_max_cantilever = 10.0
vertical_thin_plate_allowed = False

index_design_type = "SIX_LOBE_CONTINUOUS_WAVE_RING"
wide_key_count = 3
wide_key_arc_width = 20.0
wide_key_height = 2.5
wide_key_root_radius = 3.5
wave_lobe_count = 6
wave_amplitude = 2.0
wave_transition_radius = 3.5
wave_ring_base_radius = 102.0
wave_ring_inner_diameter = 170.0
wave_ring_height = 4.0
large_ring_clearance_candidates = (0.35, 0.45, 0.55)
large_ring_selected_clearance = 0.45

module_nut_ring_outer_diameter = 220.0
module_nut_ring_inner_diameter = 188.0
module_nut_ring_thickness = 7.0
module_nut_pocket_clearance_candidates = (0.15, 0.25, 0.35)
module_nut_pocket_selected_clearance = 0.25
phase3r_m4_pitch_radius = 102.0
module_clamping_ring_outer_diameter = 220.0
module_clamping_ring_inner_diameter = 188.0
module_clamping_ring_thickness = 6.0
module_gasket_ring_outer_diameter = 218.0
module_gasket_ring_inner_diameter = 188.0
module_gasket_ring_thickness = 5.0
phase3r_gasket_groove_depth_candidates = (2.0, 2.2, 2.4)

port_shell_opening_type = "TEARDROP_45_DEGREE_SELF_SUPPORTING"
port_shell_max_overhang_angle = 45.0
port_shell_coupon_height = 140.0
port_shell_opening_width = 88.0
port_shell_opening_height = 92.0
port_shell_reinforcement_thickness = 4.0
port_function_ring_outer_diameter = 116.0
port_function_ring_inner_diameter = 84.0
port_function_ring_thickness = 8.0
port_function_ring_fastener_pitch = 50.0
port_backing_ring_width = 16.0
port_backing_ring_thickness = 6.0
port_backing_ring_outer_diameter = 120.0
port_backing_ring_inner_diameter = 88.0
port_backing_drain_gap_angle = 60.0

netpot_siawadeky_flange_diameter_assumed = 78.5
netpot_siawadeky_height_assumed = 70.0
netpot_siawadeky_body_diameter_pending = None
netpot_siawadeky_body_diameter_preliminary = 72.0
netpot_siawadeky_body_clearance_candidates = (0.35, 0.50, 0.65)
netpot_siawadeky_body_clearance_selected = 0.50
netpot_seat_ring_outer_diameter = 83.0
netpot_seat_ring_flange_diameter = 96.0
netpot_seat_ring_height = 8.0
netpot_seat_ring_flange_thickness = 4.0

root_mesh_initial_length = 135.0
root_mesh_foldover_length = 20.0
root_sleeve_ring_outer_diameter_phase3r = 82.0
root_sleeve_ring_inner_diameter_phase3r = 50.0
root_sleeve_ring_thickness_phase3r = 4.0

# Phase 3P-A physical Siawadeky measurements recorded 2026-08-01.
# The older image-derived values above remain for historical Phase 3R output
# reproducibility only and are explicitly rejected as final design inputs.
netpot_siawadeky_measurement_date = "2026-08-01"
netpot_siawadeky_sample_count = 3
netpot_siawadeky_measurements_equal = True
netpot_siawadeky_flange_outer_diameter = 108.0
netpot_siawadeky_flange_thickness = 4.0
netpot_siawadeky_overall_height = 68.0
netpot_siawadeky_body_height_below_flange = 64.0
netpot_siawadeky_max_body_outer_diameter = 78.6
netpot_siawadeky_max_rib_outer_diameter = 78.6
netpot_siawadeky_upper_inner_diameter = 77.2
netpot_siawadeky_lower_inner_diameter_reachable = 75.8
netpot_siawadeky_deepest_reachable_inner_diameter = 69.6
netpot_siawadeky_flange_radial_overhang = 14.7
netpot_siawadeky_external_rib_projection = 0.0
netpot_body_passage_candidates = [80.0, 80.5, 81.0]
netpot_body_passage_preferred_precalibration = 80.5
netpot_body_passage_selected = 80.5
netpot_body_passage_selection_status = "PASS_BODY_PASSAGE_PHYSICAL"
netpot_body_passage_observed_lateral_play_mm = "APPROXIMATELY_1_0"
netpot_body_passage_observed_lateral_play_value_mm = 1.0
netpot_body_passage_observed_play_measurement_method = "NOT_STANDARDIZED"
netpot_fit_status = "BODY_PASSAGE_SELECTED_REMAINING_TESTS_PENDING"
netpot_c800_status = "NOT_REQUIRED_AFTER_C805_PASS"
netpot_c805_status = "PASS_BODY_PASSAGE_PHYSICAL"
netpot_c810_status = "NOT_REQUIRED_AFTER_C805_PASS"
netpot_20_cycle_test = "CALIBRATION_PENDING"
netpot_27deg_retention_test = "CALIBRATION_PENDING"
netpot_wet_media_test = "CALIBRATION_PENDING"
netpot_500g_load_test = "CALIBRATION_PENDING"
final_port_assembly = "REDESIGN_REQUIRED"
netpot_siawadeky_flange_diameter_assumed_78_5 = (
    "REJECTED_BY_PHYSICAL_MEASUREMENT"
)
netpot_siawadeky_body_diameter_assumed_72_0 = (
    "REJECTED_BY_PHYSICAL_MEASUREMENT"
)
phase3r1_port_inner_diameter_84_0 = "NOT_FINAL_EXCESS_CLEARANCE"
phase3pa_coupon_outer_diameter = 116.0
phase3pa_coupon_thickness = 8.0
phase3pa_m4_tool_access_diameter = 18.0
phase3pa_m4_finger_access_diameter = 24.0

# Phase 3CB-0 remains a historical no-CAD audit. Phase 3H-A is the first
# explicitly scoped next-phase coupon implementation after its entry audit.
phase3cb0_audit_status = "CONFLICT_FOUND"
phase3cb0_cad_generation = "PROHIBITED"
scoped_next_phase_cad = "ALLOWED_WHEN_ENTRY_CONDITIONS_PASS"
module_buffer_0_4L_status = "PRIMARY_TARGET"
module_buffer_0_6L_status = "STRETCH_TARGET"
module_buffer_0_8L_status = "REJECTED_FOR_15_TO_25MM_SHALLOW_BUFFER"

# Phase 3H-A horizontal full-ring joint calibration.
phase3ha_status = "HORIZONTAL_FULL_RING_JOINT_CALIBRATION"
phase3ha_scope = "JOINT_ONLY_NO_PORT_NO_BUFFER"
horizontal_joint_nominal_outer_diameter = 200.0
horizontal_joint_structural_wall = 3.0
horizontal_joint_nominal_inner_diameter = 194.0
horizontal_joint_axis = "ASSEMBLY_Z"
horizontal_joint_band_axial_contribution_height = 40.0
horizontal_joint_skirt_overlap_length = 10.0
horizontal_joint_upper_physical_print_height = 50.0
horizontal_joint_lower_physical_print_height = 40.0
horizontal_joint_skirt_thickness = 2.8
horizontal_joint_skirt_minimum_thickness = 2.4
horizontal_joint_skirt_root_radius = 3.0
horizontal_joint_lead_chamfer = 1.0
horizontal_joint_drip_edge_angle_candidates = (30.0, 45.0)
horizontal_joint_hard_stop_width = 4.0
horizontal_joint_stop_collar_outer_diameter = 202.0
horizontal_joint_clearance_candidates = (0.30, 0.50, 0.70)
horizontal_joint_clearance_selected = None
horizontal_joint_arc_coupon_angle = 90.0
horizontal_joint_small_part_count = 0
horizontal_joint_planting_port_count = 0
horizontal_joint_buffer_tray_count = 0
phase3ha_compression_ring_outer_diameter = 224.0
phase3ha_compression_ring_inner_diameter = 188.0
phase3ha_compression_ring_thickness = 8.0
phase3ha_m4_angle_positions = (60.0, 180.0, 300.0)
phase3ha_m4_pitch_radius = 106.0
phase3ha_m4_clearance_hole = 4.8
phase3ha_test_fixture_status = "TEST_FIXTURE_ONLY"
phase3ha_test_membrane_status = "REFERENCE_TEMPORARY_TEST_MEMBRANE"

# Phase 3S-A three-sector split-shell printability and seam calibration.
# Values marked by the adjacent status remain provisional until the physical
# seam and capture-ring coupons have been printed.
phase3sa_sector_count = 3
phase3sa_sector_angle_deg = 120.0
phase3sa_panel_height = 170.0
phase3sa_short_panel_height = 60.0
phase3sa_shell_outer_radius = 100.0
phase3sa_shell_wall = 3.0
phase3sa_chord_length = 173.20508075688772
phase3sa_sagitta = 50.0
phase3sa_seam_overlap = 12.0
phase3sa_seam_clearance_candidates = (0.4, 0.6, 0.8)
phase3sa_seam_clearance_selected = None
phase3sa_seam_root_thickness = 4.0
phase3sa_seam_root_radius = 3.0
phase3sa_seam_rail_width = 15.0
phase3sa_seam_rail_radial_depth = 45.0
phase3sa_seam_rail_min_contact_area = 3500.0
phase3sa_seam_rail_target_contact_area = 4000.0
phase3sa_water_return_height = 4.0
phase3sa_water_return_thickness = 3.0
phase3sa_panel_capture_depth = 12.0
phase3sa_temporary_ring_clearance = 0.6
phase3sa_print_height_target = 100.0
phase3sa_print_height_audit_limit = 110.0
phase3sa_port_axis_angle = 27.0
phase3sa_max_print_overhang = 27.0
phase3sa_external_band_reference_width = 12.0

# Phase 3S-A.2 full-length seam calibration. The global selected clearance
# remains None until a full-length physical test passes.
phase3sa2_seam_clearance_candidates = (0.4, 0.6)
phase3sa2_effective_seam_length = 170.0
phase3sa2_panel_remaining_width = 48.0
phase3sa2_fixture_capture_depth = 12.0
phase3sa2_fixture_arc_half_angle_deg = 38.0
phase3sa2_fixture_seam_relief_half_angle_deg = 9.0
phase3sa2_fixture_outer_radius = 118.0
phase3sa2_fixture_inner_radius = 58.0
phase3sa2_fixture_height = 15.0

# Drainage and root zone.
drain_slope = 4.0
drain_outlet_diameter = 25.0
drain_base_height = 140.0
drain_base_volume_target = 2_500_000.0  # 2.5 L
root_basket_volume_target = 850_000.0  # 0.85 L / plant
root_slot_width = 2.5
root_drain_hole_diameter = 6.0

# Purchased 2020 aluminium frame reference geometry.
frame_profile_size = 20.0
frame_base_width = 450.0
frame_base_depth = 450.0
frame_height = 1250.0
frame_post_height = frame_height
frame_post_offset = 150.0  # tower centre to rear-post centre along +Y
frame_side_member_length = frame_base_depth - 2.0 * frame_profile_size
frame_center_member_length = frame_side_member_length
support_plate_diameter = 220.0
support_plate_thickness = 3.0

# Clamp elevations from the tower support plane; geometry starts in Phase 6.
lower_clamp_height = 110.0
middle_clamp_height = 565.0
upper_clamp_height = 970.0

# Irrigation references; actual purchased tubing must be measured.
main_irrigation_hose_id_min = 10.0
main_irrigation_hose_id_max = 13.0
branch_irrigation_hose_id_min = 4.0
branch_irrigation_hose_id_max = 6.0
main_irrigation_tube_od = 16.0
branch_irrigation_tube_od = 8.0
irrigation_nozzle_diameter = 1.8

# Drain hose purchasing range.
drain_hose_id_min = 20.0
drain_hose_id_max = 25.0

# Chain collar references; geometry starts in Phase 6.
chain_collar_height = 50.0
chain_mount_count = 3
chain_mount_angle = 120.0

# Bambu Lab A1 absolute build limits from the task specification.
print_bed_x = 245.0
print_bed_y = 245.0
print_bed_z = 240.0
design_target_xy = 240.0

# Phase 1 visualization details. The shallow datum groove leaves 2.5 mm wall.
phase1_datum_groove_width = 8.0
phase1_datum_groove_depth = 0.5
phase1_datum_groove_height = 20.0
phase1_datum_groove_bottom = 142.0

# Export tessellation.
stl_linear_tolerance = 0.05
stl_angular_tolerance = 0.10


PARAMETER_UNITS: dict[str, str] = {
    "linear": "mm",
    "angle": "degree",
    "volume": "mm^3",
}


CALIBRATION_ITEMS: dict[str, dict[str, object]] = {
    "commercial_netpot_60_actual_dimensions": {
        "status": CALIBRATION_PENDING,
        "value": {
            "nominal_size": netpot_nominal_size,
            "flange_outer_diameter": netpot_flange_outer_diameter,
            "body_top_outer_diameter": netpot_body_top_outer_diameter,
            "body_bottom_outer_diameter": netpot_body_bottom_outer_diameter,
            "body_height": netpot_body_height,
            "flange_thickness": netpot_flange_thickness,
            "lip_height": netpot_lip_height,
            "taper_angle": netpot_taper_angle,
            "slot_width": netpot_slot_width,
            "slot_count": netpot_slot_count,
            "source": ASSUMPTION,
        },
    },
    "plant_port_flange_diameter": {
        "status": CALIBRATION_PENDING,
        "value": plant_port_flange_diameter,
    },
    "netpot_adapter_fit_clearance": {
        "status": CALIBRATION_PENDING,
        "value": netpot_fit_clearance,
    },
    "port_adapter_fit_clearance": {
        "status": CALIBRATION_PENDING,
        "value": port_adapter_fit_clearance,
    },
    "m3_port_fastener_actual_dimensions": {
        "status": CALIBRATION_PENDING,
        "value": {
            "clearance_diameter": m3_clearance_diameter,
            "nut_across_flats": m3_metal_nut_across_flats,
            "nut_thickness": m3_metal_nut_thickness,
        },
    },
    "m3_port_cartridge_fit": {
        "status": CALIBRATION_PENDING,
        "value": {
            "selected_clearance_per_side": m3_port_cartridge_clearance,
            "candidate_clearances_per_side":
                m3_port_cartridge_clearance_candidates,
            "nut_across_flats": m3_metal_nut_across_flats,
        },
    },
    "root_ring_passage_fit": {
        "status": CALIBRATION_PENDING,
        "value": {
            "selected_clearance_per_side": root_ring_passage_clearance,
            "candidate_clearances_per_side":
                root_ring_passage_clearance_candidates,
        },
    },
    "root_sleeve_purchased_product": {
        "status": CALIBRATION_PENDING,
        "value": {
            "material": root_sleeve_material_reference,
            "expanded_target_mm3": root_basket_volume_target,
            "collapsed_diameter": root_sleeve_collapsed_diameter,
        },
    },
    "siawadeky_netpot_actual_dimensions": {
        "status": CALIBRATION_PENDING,
        "value": {
            "flange_diameter_assumed":
                netpot_siawadeky_flange_diameter_assumed,
            "height_assumed": netpot_siawadeky_height_assumed,
            "body_diameter": netpot_siawadeky_body_diameter_pending,
            "body_diameter_preliminary":
                netpot_siawadeky_body_diameter_preliminary,
            "source": ASSUMPTION,
        },
    },
    "phase3r_large_index_ring_fit": {
        "status": CALIBRATION_PENDING,
        "value": {
            "selected_clearance_per_side":
                large_ring_selected_clearance,
            "candidate_clearances_per_side":
                large_ring_clearance_candidates,
            "design": index_design_type,
        },
    },
    "phase3r_annular_m4_nut_ring_fit": {
        "status": CALIBRATION_PENDING,
        "value": {
            "selected_pocket_clearance":
                module_nut_pocket_selected_clearance,
            "candidate_pocket_clearances":
                module_nut_pocket_clearance_candidates,
        },
    },
    "phase3r_root_mesh_load": {
        "status": CALIBRATION_PENDING,
        "value": {
            "material": "PURCHASED_PP_OR_PE_VEGETABLE_MESH_BAG",
            "initial_length": root_mesh_initial_length,
            "foldover_length": root_mesh_foldover_length,
            "test_loads_g": (500, 1000),
        },
    },
    "phase3sa_vertical_seam_fit": {
        "status": CALIBRATION_PENDING,
        "value": {
            "selected_clearance": phase3sa_seam_clearance_selected,
            "candidate_clearances":
                phase3sa_seam_clearance_candidates,
            "overlap": phase3sa_seam_overlap,
        },
    },
    "phase3sa_temporary_capture_ring_fit": {
        "status": CALIBRATION_PENDING,
        "value": {
            "radial_clearance": phase3sa_temporary_ring_clearance,
            "capture_depth": phase3sa_panel_capture_depth,
        },
    },
    "petg_shrinkage": {"status": CALIBRATION_PENDING, "value": None},
    "tpu_gasket_compression_ratio": {
        "status": CALIBRATION_PENDING,
        "value": None,
    },
    "m4_star_knob_actual_dimensions": {
        "status": CALIBRATION_PENDING,
        "value": {
            "diameter": m4_star_knob_envelope_diameter,
            "height": m4_star_knob_envelope_height,
            "bolt_length": m4_bolt_length,
            "washer_diameter": m4_washer_diameter,
        },
    },
    "m5_star_knob_actual_dimensions": {
        "status": CALIBRATION_PENDING,
        "value": None,
    },
    "heat_set_insert_actual_dimensions": {
        "status": CALIBRATION_PENDING,
        "value": {
            "pilot_diameter": m4_heat_set_insert_hole_diameter,
            "depth": m4_heat_set_insert_depth,
        },
    },
    "2020_extrusion_slot_profile": {
        "status": CALIBRATION_PENDING,
        "value": "20 x 20 reference solid only",
    },
    "main_irrigation_tube_od": {
        "status": ASSUMPTION,
        "value": main_irrigation_tube_od,
    },
    "branch_irrigation_tube_od": {
        "status": ASSUMPTION,
        "value": branch_irrigation_tube_od,
    },
    "drain_hose_actual_od": {
        "status": CALIBRATION_PENDING,
        "value": None,
    },
    "clamp_tpu_pad_thickness": {
        "status": CALIBRATION_PENDING,
        "value": None,
    },
    "mature_crop_spread": {"status": CALIBRATION_PENDING, "value": None},
    "actual_root_mass": {"status": CALIBRATION_PENDING, "value": None},
    "actual_saturated_mass": {"status": CALIBRATION_PENDING, "value": None},
}


@dataclass(frozen=True)
class ModulePlacement:
    """Nominal location of one replaceable growing module."""

    module_number: int
    z_bottom: float
    rotation_deg: float


def module_rotation_degrees(module_number: int) -> float:
    """Return 0 degrees for odd modules and 60 degrees for even modules."""

    if not 1 <= module_number <= module_count:
        raise ValueError(
            f"module_number must be in 1..{module_count}, got {module_number}"
        )
    return 0.0 if module_number % 2 else module_rotation_offset


def module_placements() -> tuple[ModulePlacement, ...]:
    """Return all five bottom-up module placements."""

    return tuple(
        ModulePlacement(
            module_number=number,
            z_bottom=drain_base_height + (number - 1) * module_height,
            rotation_deg=module_rotation_degrees(number),
        )
        for number in range(1, module_count + 1)
    )


def rear_post_front_clearance() -> float:
    """Nominal radial gap between tower body and front face of rear post."""

    return (
        frame_post_offset
        - 0.5 * frame_profile_size
        - 0.5 * tower_body_diameter
    )


def rear_post_max_envelope_clearance() -> float:
    """Gap between the rear post front face and the 240 mm tower envelope."""

    return (
        frame_post_offset
        - 0.5 * frame_profile_size
        - 0.5 * tower_max_diameter
    )


def interface_maximum_diameter_with_knob() -> float:
    """Absolute XY diameter of the three provisional knob envelopes."""

    return 2.0 * (
        interface_fastener_pitch_radius
        + 0.5 * m4_star_knob_envelope_diameter
    )


def angular_distance_degrees(first: float, second: float) -> float:
    """Return the smallest unsigned circular angular separation."""

    delta = abs((first - second) % 360.0)
    return min(delta, 360.0 - delta)


def minimum_fastener_to_port_angle() -> float:
    """Return the minimum separation of any M4 and future plant-port axis."""

    return min(
        angular_distance_degrees(fastener, port)
        for fastener in available_fastener_angles
        for port in future_plant_port_angles
    )


def validate_parameters() -> None:
    """Raise ValueError when the Phase 1 parameter contract is inconsistent."""

    if not isclose(
        tower_nominal_height,
        drain_base_height
        + module_count * module_height
        + irrigation_top_height,
    ):
        raise ValueError("tower_nominal_height does not match base + modules + top")
    if total_plant_ports != 15:
        raise ValueError("PS-MHT-V001 must have 15 plant ports")
    if plant_port_local_angles != (0.0, 120.0, 240.0):
        raise ValueError("Phase 3A module must contain only 0/120/240 ports")
    if selected_port_z_offset_pattern != "A":
        raise ValueError("Phase 3A must retain equal-height candidate A")
    if not isclose(plant_port_count * plant_port_center_angle, 360.0):
        raise ValueError("three plant ports must divide the circumference")
    if module_wall_thickness < 2.4:
        raise ValueError("module wall is below the PETG design minimum")
    if plant_port_wall_thickness < 4.0:
        raise ValueError("plant-port root wall must be at least 4 mm")
    if tower_body_diameter > tower_max_diameter:
        raise ValueError("tower body exceeds maximum tower diameter")
    if tower_max_diameter > design_target_xy:
        raise ValueError("tower maximum diameter exceeds the 240 mm design target")
    if not 0.3 <= interface_radial_clearance <= 0.5:
        raise ValueError("module interface clearance must remain 0.3-0.5 mm/side")
    if not 3.0 <= drain_slope <= 5.0:
        raise ValueError("drain slope must remain 3-5 degrees")
    if rear_post_front_clearance() <= 0.0:
        raise ValueError("rear post intersects the nominal tower body")
    if rear_post_max_envelope_clearance() <= 0.0:
        raise ValueError("rear post intersects the 240 mm tower envelope")
    if len(module_placements()) != module_count:
        raise ValueError("module placement count mismatch")
    if index_station_count != 6 or not isclose(index_station_step, 60.0):
        raise ValueError("Phase 2 index must have six 60-degree stations")
    if available_fastener_angles != (30.0, 90.0, 150.0, 210.0, 270.0, 330.0):
        raise ValueError("Phase 2 M4 station set mismatch")
    if used_fastener_angles != (30.0, 150.0, 270.0):
        raise ValueError("Phase 2 must use three 120-degree M4 stations")
    if rear_service_angle in used_fastener_angles:
        raise ValueError("rear 90-degree service region cannot carry a normal knob")
    if minimum_fastener_to_port_angle() < 30.0:
        raise ValueError("M4 axes must remain at least 30 degrees from port axes")
    if interface_load_contact_width < 6.0:
        raise ValueError("interface load contact band must be at least 6 mm")
    if interface_maximum_diameter_with_knob() > tower_max_diameter:
        raise ValueError("provisional knob envelope exceeds 240 mm")
    if not isclose(
        port_receiver_bore_diameter - port_adapter_outer_diameter,
        2.0 * port_adapter_fit_clearance,
    ):
        raise ValueError("port adapter diametral clearance mismatch")
    if not isclose(port_adapter_fit_clearance, 0.35, abs_tol=1.0e-9):
        raise ValueError("Phase 3A selected receiver clearance must be 0.35 mm")
    if not 0.7 <= root_basket_volume_target / 1_000_000.0 <= 1.0:
        raise ValueError("root-zone target must remain 0.7-1.0 L per plant")
    if not isclose(
        root_sleeve_retaining_ring_max_diameter
        + 2.0 * root_ring_passage_clearance,
        port_adapter_inner_diameter,
    ):
        raise ValueError("root-ring passage clearance mismatch")
    if m3_port_retainer_arm_thickness < 2.4:
        raise ValueError("M3 retainer gate arm is below 2.4 mm")
    if phase3r_min_isolated_footprint < 200.0:
        raise ValueError("Phase 3R isolated footprint is below 200 mm^2")
    if phase3r_min_independent_width < 15.0:
        raise ValueError("Phase 3R independent width is below 15 mm")
    if phase3r_min_structural_wall < 3.0:
        raise ValueError("Phase 3R structural wall is below 3 mm")
    if phase3r_min_root_thickness < 4.0:
        raise ValueError("Phase 3R root thickness is below 4 mm")
    if phase3r_min_rib_width < 5.0:
        raise ValueError("Phase 3R rib width is below 5 mm")
    if phase3r_preferred_root_fillet < 3.0:
        raise ValueError("Phase 3R preferred root fillet is below 3 mm")
    if phase3r_max_cantilever > 10.0:
        raise ValueError("Phase 3R cantilever exceeds 10 mm")
    if vertical_thin_plate_allowed:
        raise ValueError("Phase 3R vertical thin plates must remain disabled")
    if index_design_type != "SIX_LOBE_CONTINUOUS_WAVE_RING":
        raise ValueError("Phase 3R selected index must be the wave ring")
    if wave_lobe_count != 6:
        raise ValueError("Phase 3R wave ring must have six lobes")
    if port_shell_max_overhang_angle > 45.0:
        raise ValueError("Phase 3R shell opening exceeds 45 degrees")
    if (
        module_nut_ring_outer_diameter
        - module_nut_ring_inner_diameter
    ) / 2.0 < phase3r_min_independent_width:
        raise ValueError("Phase 3R nut-ring radial width is below 15 mm")
    if (
        port_backing_ring_outer_diameter
        - port_backing_ring_inner_diameter
    ) / 2.0 < port_backing_ring_width:
        raise ValueError("Phase 3R backing-ring width mismatch")
    if netpot_body_passage_selected != 80.5:
        raise ValueError("Phase 3H-A requires the physically selected 80.5 mm passage")
    if horizontal_joint_structural_wall < 3.0:
        raise ValueError("Phase 3H-A structural wall is below 3 mm")
    if not isclose(
        horizontal_joint_nominal_outer_diameter
        - 2.0 * horizontal_joint_structural_wall,
        horizontal_joint_nominal_inner_diameter,
    ):
        raise ValueError("Phase 3H-A nominal ring diameters do not match the wall")
    if horizontal_joint_skirt_overlap_length != 10.0:
        raise ValueError("Phase 3H-A skirt overlap must remain 10 mm")
    if horizontal_joint_skirt_thickness < horizontal_joint_skirt_minimum_thickness:
        raise ValueError("Phase 3H-A skirt is below its minimum thickness")
    if horizontal_joint_skirt_root_radius < 3.0:
        raise ValueError("Phase 3H-A skirt root radius is below R3")
    if horizontal_joint_hard_stop_width < 4.0:
        raise ValueError("Phase 3H-A hard-stop width is below 4 mm")
    if not isclose(
        horizontal_joint_band_axial_contribution_height
        + horizontal_joint_skirt_overlap_length,
        horizontal_joint_upper_physical_print_height,
    ):
        raise ValueError("Phase 3H-A upper physical height accounting mismatch")
    if phase3ha_compression_ring_outer_diameter > tower_max_diameter:
        raise ValueError("Phase 3H-A compression fixture exceeds 240 mm")
    if (
        phase3ha_m4_pitch_radius - 0.5 * phase3ha_m4_clearance_hole
        <= 0.5 * horizontal_joint_nominal_inner_diameter
    ):
        raise ValueError("Phase 3H-A M4 envelope enters the 194 mm root envelope")


validate_parameters()
