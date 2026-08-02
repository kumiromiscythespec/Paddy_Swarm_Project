"""Phase 1 parameter-contract tests."""

from __future__ import annotations

from math import isclose

from ps_mht_v001 import parameters as p


REQUIRED_PARAMETER_NAMES = (
    "tower_body_diameter",
    "tower_max_diameter",
    "module_height",
    "module_count",
    "irrigation_top_height",
    "plant_port_count",
    "plant_port_diameter",
    "plant_port_flange_diameter",
    "plant_port_angle",
    "module_rotation_offset",
    "module_wall_thickness",
    "plant_port_wall_thickness",
    "interface_lip_height",
    "interface_radial_clearance",
    "index_station_count",
    "index_station_step",
    "interface_station_offset",
    "gasket_cord_diameter",
    "gasket_diameter",
    "gasket_groove_width",
    "gasket_groove_depth",
    "fastener_count",
    "module_fastener_size",
    "m4_star_knob_envelope_diameter",
    "m4_star_knob_envelope_height",
    "m4_bolt_length",
    "m4_washer_diameter",
    "drain_slope",
    "drain_outlet_diameter",
    "drain_base_height",
    "drain_base_volume_target",
    "root_basket_volume_target",
    "root_slot_width",
    "root_drain_hole_diameter",
    "frame_profile_size",
    "frame_base_width",
    "frame_base_depth",
    "frame_height",
    "frame_post_offset",
    "lower_clamp_height",
    "middle_clamp_height",
    "upper_clamp_height",
    "main_irrigation_tube_od",
    "branch_irrigation_tube_od",
    "irrigation_nozzle_diameter",
    "chain_collar_height",
    "chain_mount_count",
    "chain_mount_angle",
    "print_bed_x",
    "print_bed_y",
    "print_bed_z",
    "fit_clearance_xy",
    "fit_clearance_z",
)


def test_required_parameter_names_are_centralized() -> None:
    assert all(hasattr(p, name) for name in REQUIRED_PARAMETER_NAMES)


def test_fixed_v001_dimensions() -> None:
    assert p.tower_body_diameter == 200.0
    assert p.tower_max_diameter == 240.0
    assert p.module_height == 170.0
    assert p.module_count == 5
    assert p.irrigation_top_height == 100.0
    assert p.total_plant_ports == 15
    assert p.plant_port_angle == 27.0
    assert p.frame_base_width == 450.0
    assert p.frame_base_depth == 450.0
    assert p.frame_height == 1250.0
    assert p.print_bed_x == 245.0
    assert p.print_bed_y == 245.0
    assert p.print_bed_z == 240.0


def test_nominal_tower_height_stack() -> None:
    assert isclose(
        p.drain_base_height
        + p.module_count * p.module_height
        + p.irrigation_top_height,
        p.tower_nominal_height,
    )
    assert p.tower_nominal_height == 1090.0


def test_module_rotation_sequence() -> None:
    rotations = tuple(item.rotation_deg for item in p.module_placements())
    assert rotations == (0.0, 60.0, 0.0, 60.0, 0.0)


def test_calibration_pending_items_are_not_claimed_as_final() -> None:
    required = {
        "commercial_netpot_60_actual_dimensions",
        "petg_shrinkage",
        "tpu_gasket_compression_ratio",
        "m4_star_knob_actual_dimensions",
        "m5_star_knob_actual_dimensions",
        "heat_set_insert_actual_dimensions",
        "2020_extrusion_slot_profile",
        "drain_hose_actual_od",
        "mature_crop_spread",
        "actual_root_mass",
        "actual_saturated_mass",
    }
    assert required.issubset(p.CALIBRATION_ITEMS)
    assert all(
        p.CALIBRATION_ITEMS[name]["status"] == p.CALIBRATION_PENDING
        for name in required
    )
