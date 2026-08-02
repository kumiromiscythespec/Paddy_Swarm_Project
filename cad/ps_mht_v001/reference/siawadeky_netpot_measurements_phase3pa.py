"""Authoritative Phase 3P-A Siawadeky physical measurements."""

from __future__ import annotations

from ps_mht_v001.parameters import (
    netpot_siawadeky_body_height_below_flange,
    netpot_siawadeky_deepest_reachable_inner_diameter,
    netpot_siawadeky_external_rib_projection,
    netpot_siawadeky_flange_outer_diameter,
    netpot_siawadeky_flange_radial_overhang,
    netpot_siawadeky_flange_thickness,
    netpot_siawadeky_lower_inner_diameter_reachable,
    netpot_siawadeky_max_body_outer_diameter,
    netpot_siawadeky_max_rib_outer_diameter,
    netpot_siawadeky_measurement_date,
    netpot_siawadeky_measurements_equal,
    netpot_siawadeky_overall_height,
    netpot_siawadeky_sample_count,
    netpot_siawadeky_upper_inner_diameter,
)


STATUS = "PHYSICAL_MEASUREMENT_AUTHORITATIVE_PHASE3PA"
OUTSIDE_MEASUREMENT_METHOD = "CALIPER_OUTSIDE_JAWS"
INSIDE_MEASUREMENT_METHOD = "CALIPER_INSIDE_JAWS"


def siawadeky_measurements_phase3pa() -> dict[str, object]:
    return {
        "status": STATUS,
        "measurement_date": netpot_siawadeky_measurement_date,
        "sample_count": netpot_siawadeky_sample_count,
        "all_samples_same_within_caliper_resolution":
            netpot_siawadeky_measurements_equal,
        "outside_measurement_method": OUTSIDE_MEASUREMENT_METHOD,
        "inside_measurement_method": INSIDE_MEASUREMENT_METHOD,
        "measured_mm": {
            "flange_outer_diameter":
                netpot_siawadeky_flange_outer_diameter,
            "flange_thickness": netpot_siawadeky_flange_thickness,
            "overall_height": netpot_siawadeky_overall_height,
            "maximum_body_outer_diameter":
                netpot_siawadeky_max_body_outer_diameter,
            "maximum_rib_outer_diameter":
                netpot_siawadeky_max_rib_outer_diameter,
            "upper_inner_diameter":
                netpot_siawadeky_upper_inner_diameter,
            "lower_inner_diameter_reachable":
                netpot_siawadeky_lower_inner_diameter_reachable,
            "deepest_reachable_inner_diameter":
                netpot_siawadeky_deepest_reachable_inner_diameter,
        },
        "derived_mm": {
            "body_height_below_flange":
                netpot_siawadeky_body_height_below_flange,
            "flange_radial_overhang_from_max_body":
                netpot_siawadeky_flange_radial_overhang,
            "maximum_external_rib_projection":
                netpot_siawadeky_external_rib_projection,
        },
        "inner_diameter_usage": "REFERENCE_ONLY_NOT_EXTERNAL_ENVELOPE",
    }
