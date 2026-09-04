# Common Rover Physical Integration v0.9.4.0

Classification: `PHYSICAL_INTEGRATION_REFERENCE`  
Release: `HOLD`  
Final: `CAD_REFERENCE_COMPLETE / PHYSICAL_VALIDATION_PENDING`

- BBOX_vs_frame: `HOLD_FINAL_BBOX_DIMENSIONS`
- BBOX_vs_crawler_KP000_shaft_belt_diagonal: `HOLD_TRANSFORMS`
- BBOX_vs_CBOX_support: `CAD_PASS_REFERENCE_ZONE_ONLY`
- CBOX_vs_frame: `CAD_PASS_REFERENCE_ZONE_ONLY`
- CBOX_vs_motor_clutch_servo_pulley_belt_PTO: `HOLD_FINAL_TRANSFORMS`
- H25A1_vs_link: `HOLD_PHYSICAL_LINK_MOTION_ENVELOPE`
- H25A1_vs_guide: `HOLD_GUIDE_REGISTRATION`
- H25A1_vs_bearing: `CAD_PASS_REFERENCE_AXIS_ONLY`
- H25A1_vs_neighbor_hardware: `HOLD_HARDWARE_STACK`
- BBOX_X_sweep_vs_all: `HOLD_BOX_DIMENSIONS_AND_SERVICE_SIDE`

Only reference-zone non-intersections receive CAD_PASS. Unknown transforms and physical envelopes remain HOLD and are never reported as zero interference.
