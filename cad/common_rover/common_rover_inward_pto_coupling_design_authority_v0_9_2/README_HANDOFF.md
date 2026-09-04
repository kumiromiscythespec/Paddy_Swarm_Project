# Common Rover v0.9.2 handoff

This exact 45-path package contains only the inward-PTO shaft-stub, coupling,
state, and central-work-unit-bay delta over protected v0.9.1.

Recommended: `S12-C1-SMALL-STUB12.5-SHIFT00-GAP36-RES2-S1-E1`

- C1 unit-side dual independent sliding sleeves
- SMALL sensitivity envelope OD20 × body25
- stub 12.5 each, no stack shift, ends ±18, end gap 36
- required engagement 8, reserve 2, margin 2.5
- body gap 11, full-sweep gap 12, width 290
- 1,512 center-bay combinations; 9166 recorded
  stage evaluations
- only SMALL fits; commercial coupling selection is critical and remains HOLD

Run:

`python -B build_common_rover_inward_pto_coupling_v092.py --verify`

`python -B tests/test_common_rover_inward_pto_coupling_v092_contract.py`

Artifacts are simplified envelopes. The dummy STEP/STL is hand-fit/no-load
geometry only.

`PHYSICAL_FIT_HOLD`  
`SHAFT_CUTTING_HOLD`  
`MACHINING_HOLD`  
`LOAD_AND_POWERED_ROTATION_HOLD`  
`WATER_MUD_TEST_HOLD`  
`FIELD_DEPLOYMENT_NOT_APPROVED`  
`NOT_FOR_MANUFACTURING`
