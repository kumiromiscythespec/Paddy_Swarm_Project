# Common Rover v0.9.1 handoff

This exact 37-path package contains only the v0.9.1 outboard-pod and inward
independent-PTO delta.

Recommended candidate:
`S9-B1-F2040A-FRAMEE-PTOX210-Z320-PY85.0-DY40.0-LX70-GAP60-C1`

Key candidate values:

- motor centers X=-60/Y=±100/Z=370 mm
- PTO 20T X=0/Y=±85/Z=370 mm
- PTO 60T X=150/Y=±85/Z=320 mm
- DRIVE planes Y=±125 mm
- F2040-A rails Y=±48 mm
- left/right inward PTO ends Y=+30/-30 mm (60 mm gap)
- belt/fixed 11.5 mm; PTO/fixed 10.0 mm
- total width 290 mm; PTO rotation bottom Z=260 mm
- E2 X=180/Z=455/bottom Z=440 mm

Search candidates: 704  
Stage 9 fine candidates: 326

Use:

`python -B build_common_rover_outboard_inward_pto_v091.py --verify`

`python -B tests/test_common_rover_outboard_inward_pto_v091_contract.py`

These files are envelope-level design evidence only.

`PHYSICAL_FIT_HOLD`  
`SUPPORT_PLATE_MACHINING_HOLD`  
`SHAFT_CUTTING_HOLD`  
`MANUFACTURING_HOLD`  
`FIELD_DEPLOYMENT_NOT_APPROVED`  
`NOT_FOR_MANUFACTURING`
