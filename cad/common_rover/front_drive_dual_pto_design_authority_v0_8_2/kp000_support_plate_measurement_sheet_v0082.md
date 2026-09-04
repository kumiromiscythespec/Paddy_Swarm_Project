# KP000 support-plate measurement sheet v0.8.2

**NOT_FOR_MANUFACTURING — PART_MEASUREMENT_REQUIRED**

Record `measured_value`, photograph the named reference faces, and retain left/right readings separately when they differ. Existing CAD envelopes are not physical measurements.

| ID | Part | Measurement | Direction | Nominal/reference | Accuracy | Method | Status |
|---|---|---|---|---:|---|---|---|
| M001 | KP000 | housing_overall_width | X | 45x15x35 envelope only | 0.1 mm | Measure extreme left face to extreme right face. | PART_MEASUREMENT_REQUIRED |
| M002 | KP000 | housing_overall_height | Z |  | 0.1 mm | Measure mounting base bottom to highest housing feature. | PART_MEASUREMENT_REQUIRED |
| M003 | KP000 | housing_depth | Y |  | 0.1 mm | Measure frontmost to rearmost housing face along shaft axis. | PART_MEASUREMENT_REQUIRED |
| M004 | KP000 | shaft_center_from_base | Z |  | 0.1 mm | Measure base bottom to bore center using half bore diameter. | PART_MEASUREMENT_REQUIRED |
| M005 | KP000 | mounting_hole_count | COUNT |  | 0.1 mm | Count all mounting holes; record slots separately. | PART_MEASUREMENT_REQUIRED |
| M006 | KP000 | mounting_hole_diameter | NORMAL_TO_BASE |  | 0.05 mm | Measure each hole at two directions. | PART_MEASUREMENT_REQUIRED |
| M007 | KP000 | mounting_hole_spacing_x | X |  | 0.1 mm | Measure center-to-center parallel to plate width. | PART_MEASUREMENT_REQUIRED |
| M008 | KP000 | mounting_hole_spacing_z | Z |  | 0.1 mm | Measure center-to-center parallel to plate height. | PART_MEASUREMENT_REQUIRED |
| M009 | KP000 | mounting_hole_shape | X/Z |  | 0.1 mm | Record ROUND or SLOT and slot direction. | PART_MEASUREMENT_REQUIRED |
| M010 | KP000 | mounting_bolt_nominal | THREAD |  | 0.1 mm | Confirm bolt marking and thread with gauge. | PART_MEASUREMENT_REQUIRED |
| M011 | KP000 | bearing_bore | Y_AXIS |  | 0.05 mm | Measure shaft or identify insert bearing marking. | PART_MEASUREMENT_REQUIRED |
| M012 | KP000 | set_screw_position | ANGULAR/Y |  | 0.1 mm | Measure from housing reference face and photograph. | PART_MEASUREMENT_REQUIRED |
| M013 | KP000 | grease_port_or_projection | X/Y/Z |  | 0.1 mm | Measure projection from housing envelope. | PART_MEASUREMENT_REQUIRED |
| M014 | KP000 | insert_projection_left | -Y |  | 0.1 mm | Measure housing face to insert extreme. | PART_MEASUREMENT_REQUIRED |
| M015 | KP000 | insert_projection_right | +Y |  | 0.1 mm | Measure housing face to insert extreme. | PART_MEASUREMENT_REQUIRED |
| M016 | KP000 | tool_access_direction | VECTOR |  | 0.1 mm | Photograph installed orientation and access path. | PART_MEASUREMENT_REQUIRED |
| M017 | PTO_SHAFT | actual_diameter | RADIAL | 10 candidate, not measured | 0.01 mm | Micrometer at three axial stations and two angles. | PART_MEASUREMENT_REQUIRED |
| M018 | PTO_SHAFT | diameter_tolerance | RADIAL |  | 0.01 mm | Record min/max from repeated micrometer readings. | PART_MEASUREMENT_REQUIRED |
| M019 | PTO_SHAFT | effective_length | Y |  | 0.1 mm | Measure usable shoulder-to-shoulder length. | PART_MEASUREMENT_REQUIRED |
| M020 | PTO_SHAFT | keyway_or_d_flat | RADIAL/AXIAL |  | 0.05 mm | Measure width, depth, and axial start/end. | PART_MEASUREMENT_REQUIRED |
| M021 | PTO_SHAFT | shaft_collar_width | Y |  | 0.05 mm | Measure both collars separately face-to-face. | PART_MEASUREMENT_REQUIRED |
| M022 | PTO_SHAFT | retaining_ring_position | Y |  | 0.1 mm | Measure reference shoulder to groove center. | PART_MEASUREMENT_REQUIRED |
| M023 | PTO_SHAFT | axial_play | Y |  | 0.05 mm | Push-pull shaft and measure indicator travel. | PART_MEASUREMENT_REQUIRED |
| M024 | PTO_SHAFT | coupling_fixing_method | TEXT |  | N/A | Record key, clamp, or set screws and photograph. | PART_MEASUREMENT_REQUIRED |
| M025 | PTO_60T_PULLEY | reported_max_dimension | MEANING_PENDING | 102.0 | 0.1 mm | Reidentify whether 102 mm is OD, flange OD, or axial length. | USER_REPORTED_DIMENSION_MEANING_CALIBRATION_PENDING |
| M026 | PTO_60T_PULLEY | overall_axial_width | Y |  | 0.1 mm | Measure extreme flange face to opposite extreme face. | PART_MEASUREMENT_REQUIRED |
| M027 | PTO_60T_PULLEY | tooth_face_width | Y |  | 0.1 mm | Measure usable toothed face between flanges. | PART_MEASUREMENT_REQUIRED |
| M028 | PTO_60T_PULLEY | flange_outer_diameter | RADIAL |  | 0.1 mm | Measure both flange diameters at two angles. | PART_MEASUREMENT_REQUIRED |
| M029 | PTO_60T_PULLEY | left_flange_thickness | Y |  | 0.1 mm | Measure left flange thickness. | PART_MEASUREMENT_REQUIRED |
| M030 | PTO_60T_PULLEY | right_flange_thickness | Y |  | 0.1 mm | Measure right flange thickness. | PART_MEASUREMENT_REQUIRED |
| M031 | PTO_60T_PULLEY | hub_width | Y |  | 0.1 mm | Measure hub axial projection. | PART_MEASUREMENT_REQUIRED |
| M032 | PTO_60T_PULLEY | hub_outer_diameter | RADIAL |  | 0.1 mm | Measure hub OD at two angles. | PART_MEASUREMENT_REQUIRED |
| M033 | PTO_60T_PULLEY | bore_diameter | RADIAL |  | 0.1 mm | Measure bore with bore gauge or pin gauges. | PART_MEASUREMENT_REQUIRED |
| M034 | PTO_60T_PULLEY | fixing_method | TEXT |  | 0.1 mm | Record key, clamp, set screw, or taper bush. | PART_MEASUREMENT_REQUIRED |
| M035 | PTO_60T_PULLEY | radial_runout | RADIAL |  | METHOD_AND_LIMIT_HOLD | Mount on intended shaft; rotate slowly against dial indicator. | PART_MEASUREMENT_REQUIRED |
| M036 | PTO_60T_PULLEY | axial_runout | Y |  | METHOD_AND_LIMIT_HOLD | Indicate flange face while rotating on intended shaft. | PART_MEASUREMENT_REQUIRED |
| M037 | FASTENER | bolt_head_diameter | RADIAL |  | 0.5 mm | Measure extreme faces of the exact production-intent item; identify thread. | PART_MEASUREMENT_REQUIRED |
| M038 | FASTENER | bolt_head_height | AXIAL |  | 0.5 mm | Measure extreme faces of the exact production-intent item; identify thread. | PART_MEASUREMENT_REQUIRED |
| M039 | FASTENER | nut_across_flats | RADIAL |  | 0.5 mm | Measure extreme faces of the exact production-intent item; identify thread. | PART_MEASUREMENT_REQUIRED |
| M040 | FASTENER | nut_height | AXIAL |  | 0.5 mm | Measure extreme faces of the exact production-intent item; identify thread. | PART_MEASUREMENT_REQUIRED |
| M041 | FASTENER | washer_outer_diameter | RADIAL |  | 0.5 mm | Measure extreme faces of the exact production-intent item; identify thread. | PART_MEASUREMENT_REQUIRED |
| M042 | FASTENER | washer_thickness | AXIAL |  | 0.5 mm | Measure extreme faces of the exact production-intent item; identify thread. | PART_MEASUREMENT_REQUIRED |
| M043 | FASTENER | t_nut_width_length_height | X/Y/Z |  | 0.5 mm | Measure extreme faces of the exact production-intent item; identify thread. | PART_MEASUREMENT_REQUIRED |
| M044 | FASTENER | spacer_dimensions | X/Y/Z |  | 0.5 mm | Measure extreme faces of the exact production-intent item; identify thread. | PART_MEASUREMENT_REQUIRED |
| M045 | TOOL | hex_key_envelope | INSERTION_AND_SWEEP |  | 0.5 mm | Measure the actual selected tool at its maximum swept section; photograph insertion path. | PART_MEASUREMENT_REQUIRED |
| M046 | TOOL | l_hex_bend_envelope | SWEEP |  | 0.5 mm | Measure the actual selected tool at its maximum swept section; photograph insertion path. | PART_MEASUREMENT_REQUIRED |
| M047 | TOOL | socket_outer_diameter | RADIAL |  | 0.5 mm | Measure the actual selected tool at its maximum swept section; photograph insertion path. | PART_MEASUREMENT_REQUIRED |
| M048 | TOOL | spanner_envelope | SWEEP |  | 0.5 mm | Measure the actual selected tool at its maximum swept section; photograph insertion path. | PART_MEASUREMENT_REQUIRED |
| M049 | TOOL | ratchet_head_envelope | SWEEP |  | 0.5 mm | Measure the actual selected tool at its maximum swept section; photograph insertion path. | PART_MEASUREMENT_REQUIRED |
| M050 | TOOL | finger_clearance | ACCESS_VOLUME |  | 0.5 mm | Measure the actual selected tool at its maximum swept section; photograph insertion path. | PART_MEASUREMENT_REQUIRED |
| M051 | TOOL | tightening_direction | VECTOR |  | 0.5 mm | Measure the actual selected tool at its maximum swept section; photograph insertion path. | PART_MEASUREMENT_REQUIRED |
| M052 | TOOL | bolt_removal_direction | VECTOR |  | 0.5 mm | Measure the actual selected tool at its maximum swept section; photograph insertion path. | PART_MEASUREMENT_REQUIRED |
| M053 | ALUMINUM_FRAME | 2020_t_slot_actual | CROSS_SECTION |  | 0.5 mm | Measure the actual profile/fixture from a named end face and slot centerline. | PART_MEASUREMENT_REQUIRED |
| M054 | ALUMINUM_FRAME | 2040_t_slot_actual | CROSS_SECTION |  | 0.5 mm | Measure the actual profile/fixture from a named end face and slot centerline. | PART_MEASUREMENT_REQUIRED |
| M055 | ALUMINUM_FRAME | t_nut_actual | X/Y/Z |  | 0.5 mm | Measure the actual profile/fixture from a named end face and slot centerline. | PART_MEASUREMENT_REQUIRED |
| M056 | ALUMINUM_FRAME | bracket_actual | X/Y/Z |  | 0.5 mm | Measure the actual profile/fixture from a named end face and slot centerline. | PART_MEASUREMENT_REQUIRED |
| M057 | ALUMINUM_FRAME | plate_mounting_face | X/Z |  | 0.5 mm | Measure the actual profile/fixture from a named end face and slot centerline. | PART_MEASUREMENT_REQUIRED |
| M058 | ALUMINUM_FRAME | drillable_position | X/Z |  | 0.5 mm | Measure the actual profile/fixture from a named end face and slot centerline. | PART_MEASUREMENT_REQUIRED |
| M059 | ALUMINUM_FRAME | hole_to_frame_end_distance | X/Z |  | 0.5 mm | Measure the actual profile/fixture from a named end face and slot centerline. | PART_MEASUREMENT_REQUIRED |
| M060 | SUPPORT_PLATE | actual_stock_thickness | Y | 5.0 | 0.05 mm | Measure plate stock at four corners and center before machining. | PART_MEASUREMENT_REQUIRED |

## Runout method

Mount the intended pulley on the intended shaft, support it in the intended bearing pair, preload the dial indicator lightly, rotate one revolution by hand, and record total indicator reading. Measure radial OD and axial flange face separately. Acceptance limits remain HOLD.

## Photo references

Include a scale, label left/right, mark +X/+Y/+Z, and photograph the exact faces used for each measurement. Do not infer hidden hole centers from the housing outline.
