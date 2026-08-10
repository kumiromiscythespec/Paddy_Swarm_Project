# Measurement ledger

Version: v0.9.5.2  
Classification: `PHYSICAL_MEASUREMENT_RECORD`  
Release: `HOLD`  
Design modification: `NONE`  

Classification follows the closed vocabulary in `measurement_ledger.json`. IMAGE_REPORTED_MEASUREMENT means the user supplied the measurement through image context; it never means Codex performed image metrology.

| ID | Subsystem | Measurement | Value | Unit | Classification | Date | Source | Status | Supersedes | Notes |
|---|---|---|---:|---|---|---|---|---|---|---|
| CBOX-PRINT-BODY | CBOX | body print | COMPLETED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-PRINT-LID | CBOX | lid print | COMPLETED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-PRINT-PLATE02 | CBOX | Plate 02 print | COMPLETED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-WARP | CBOX | major visible warp | NONE_REPORTED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-WALL-COLLAPSE | CBOX | wall collapse | NONE_REPORTED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-CORNER-LIFT | CBOX | corner lift | NONE_REPORTED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-LID-ROCK | CBOX | lid/body rocking | NONE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-OPPOSITE-LIFT | CBOX | opposite-side lift when pressed | NONE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-RATTLE | CBOX | lid rattle | NONE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-LIFT | CBOX | lid lift | NONE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-LID-M4 | CBOX | all lid M4 holes | NO_SNAG / ALIGNMENT_PASS_USER_REPORTED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | PHYSICAL_PASS_REPORTED_SCOPE_ONLY | NONE |  |
| CBOX-LID-GAP | CBOX | unclamped/lightly seated center gap | 0.4 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | APPROXIMATE / GASKET_TEST_PENDING | NONE | Not waterproof evidence. |
| CBOX-HEIGHT-A1 | CBOX | body height Row/Side A point 1 | 39.8 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE | Raw label preserved; no directional remap. |
| CBOX-HEIGHT-A2 | CBOX | body height Row/Side A point 2 | 40.1 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE | Raw label preserved; no directional remap. |
| CBOX-HEIGHT-A3 | CBOX | body height Row/Side A point 3 | 40.0 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE | Raw label preserved; no directional remap. |
| CBOX-HEIGHT-B1 | CBOX | body height Row/Side B point 1 | 40.0 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE | Raw label preserved; no directional remap. |
| CBOX-HEIGHT-B2 | CBOX | body height Row/Side B point 2 | 40.3 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE | Raw label preserved; no directional remap. |
| CBOX-HEIGHT-B3 | CBOX | body height Row/Side B point 3 | 39.5 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE | Raw label preserved; no directional remap. |
| CBOX-HEIGHT-COUNT | CBOX | body height sample count | 6 | count | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | RECORDED | NONE |  |
| CBOX-HEIGHT-MEAN | CBOX | body height mean | 39.95 | mm | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | RECORDED | NONE |  |
| CBOX-HEIGHT-MIN | CBOX | body height minimum | 39.5 | mm | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | RECORDED | NONE |  |
| CBOX-HEIGHT-MAX | CBOX | body height maximum | 40.3 | mm | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | RECORDED | NONE |  |
| CBOX-HEIGHT-RANGE | CBOX | body height range | 0.8 | mm | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | RECORDED | NONE |  |
| CBOX-HEIGHT-CAD | CBOX | CAD nominal body height | 40.0 | mm | CAD_NOMINAL | 2026-08-09..2026-08-10 | V0.9.5.0_PARENT | RECORDED | NONE |  |
| CBOX-HEIGHT-MEAN-ERROR | CBOX | mean minus CAD nominal | -0.05 | mm | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | RECORDED | NONE |  |
| CBOX-SEAL-FLATNESS | CBOX | sealing flatness | CONDITIONAL / PHYSICAL_GASKET_TEST_PENDING | status | HOLD | 2026-08-09..2026-08-10 | ASSESSMENT | RECORDED | NONE |  |
| CBOX-WATERPROOF | CBOX | waterproof | NOT_TESTED | status | HOLD | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| CBOX-DRY-ASSEMBLY | CBOX | dry assembly | PHYSICAL_PASS_CANDIDATE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | CANDIDATE_ONLY | NONE |  |
| BBOX-RING-PARALLEL | BBOX | service ring parallel | YES | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| BBOX-RING-M4 | BBOX | service ring M4 hole clearance sufficient | YES | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| BBOX-PAD-M3 | BBOX | wear pad M3 hole clearance sufficient | YES | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| BBOX-BODY-PRINT | BBOX | lower body print | COMPLETED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | PHYSICAL_PRINT_PASS_CANDIDATE | NONE |  |
| BAT-LABEL-V | Battery | nominal label voltage | 12.8 | V | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | PARENT_RECORD | NOMINAL_LABEL_NOT_ELECTRICAL_TEST | NONE |  |
| BAT-LABEL-AH | Battery | nominal label capacity | 10.0 | Ah | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | PARENT_RECORD | NOMINAL_LABEL_NOT_CAPACITY_TEST | NONE |  |
| BAT-LABEL-WH | Battery | nominal label energy | 128.0 | Wh | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | PARENT_RECORD | NOMINAL_LABEL | NONE |  |
| BAT-DIM-1 | Battery | physical body dimension 1 | 150.9 | mm | MEASURED | 2026-08-09..2026-08-10 | PARENT_MEASUREMENT | RECORDED | NONE | Axis naming retained as parent dimension order; no remap. |
| BAT-DIM-2 | Battery | physical body dimension 2 | 99.4 | mm | MEASURED | 2026-08-09..2026-08-10 | PARENT_MEASUREMENT | RECORDED | NONE | Axis naming retained as parent dimension order; no remap. |
| BAT-DIM-3 | Battery | physical body dimension 3 | 92.5 | mm | MEASURED | 2026-08-09..2026-08-10 | PARENT_MEASUREMENT | RECORDED | NONE | Axis naming retained as parent dimension order; no remap. |
| BAT-MASS | Battery | mass | 1.2 | kg | MEASURED | 2026-08-09..2026-08-10 | PARENT_MEASUREMENT | RECORDED | NONE |  |
| BBOX-LONG-FIT | BBOX/Battery | long-side fit | FULL_LENGTH_FIT_USER_REPORTED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE | Does not assert zero clearance. |
| BBOX-LATERAL-LEFT | BBOX/Battery | reported left lateral clearance | 20.0 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE |  |
| BBOX-LATERAL-RIGHT | BBOX/Battery | reported right lateral clearance | 25.0 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE |  |
| BBOX-LATERAL-TOTAL | BBOX/Battery | total lateral free space | 45.0 | mm | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | RECORDED | NONE |  |
| BBOX-LATERAL-DIFF | BBOX/Battery | right minus left clearance | 5.0 | mm | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | RECORDED | NONE |  |
| BBOX-LATERAL-OFFSET | BBOX/Battery | half-difference from equal-center reference | 2.5 | mm | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | DERIVED_REFERENCE_ONLY | NONE | Left/right datum not established. |
| BBOX-BAT-INSERT | BBOX/Battery | insertion/removal in current 150 mm frame | POSSIBLE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | PRIOR_USER_TEST | RECORDED | NONE |  |
| BBOX-BAT-HANDLING | BBOX/Battery | removal handling | GRIP_UNDERSIDE_AND_TILT_TOP_TOWARD_FRAME | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | PRIOR_USER_TEST | RECORDED | NONE | Not final cassette mechanism PASS. |
| TERM-INITIAL-ORIENTATION | Battery terminal | initial terminal orientation | TOWARD_IDLER_SHAFT_SIDE | status | SUPERSEDED | 2026-08-09..2026-08-10 | USER_REPORT | SUPERSEDED_BY_REAR_DOWN_CANDIDATE | NONE |  |
| TERM-INITIAL-IDLER-CLEAR | Battery terminal | initial terminal-to-idler minimum clearance | 4.0 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | SUPERSEDED | TERM-REARDOWN-IDLER-CLEAR | Approximate. |
| TERM-REARDOWN-ORIENTATION | Battery terminal | rear/down orientation | PREFERRED_PHYSICAL_CANDIDATE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| TERM-REARDOWN-IDLER-CLEAR | Battery terminal | battery body-to-idler shaft clearance | 10.0 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | PREFERRED_CANDIDATE / HARNESS_HOLD | NONE | Approximate. |
| TERM-REAR-WALL-CLEAR | Battery terminal | terminal-to-BBOX rear wall horizontal clearance | 37.0 | mm | IMAGE_REPORTED_MEASUREMENT | 2026-08-09..2026-08-10 | USER_REPORTED_IMAGE_CONTEXT | CABLE_BEND_HOLD | NONE |  |
| BBOX-BODY-H-PHYS | BBOX | lower body physical height | 97.0 | mm | IMAGE_REPORTED_MEASUREMENT | 2026-08-09..2026-08-10 | USER_REPORTED_IMAGE_CONTEXT | APPROXIMATE / NOT_DIMENSIONAL_AUTHORITY | NONE |  |
| BBOX-BODY-H-CAD | BBOX | lower body CAD nominal height | 97.5 | mm | CAD_NOMINAL | 2026-08-09..2026-08-10 | V0.9.5.0_PARENT | RECORDED | NONE |  |
| BBOX-BOTTOM-TERM-EXTREME | BBOX/Battery | assembly bottom datum to terminal extreme | 103.9 | mm | IMAGE_REPORTED_MEASUREMENT | 2026-08-09..2026-08-10 | USER_REPORTED_IMAGE_CONTEXT | RECORDED | NONE | Raw datum retained; no subtraction. |
| BAT-TAB-WIDTH | Battery terminal | male tab width | 6.3 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_MEASUREMENT | RECORDED | NONE | 6.3 mm-class female quick-disconnect candidate only. |
| BAT-TAB-THICK | Battery terminal | male tab thickness | 0.7 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_MEASUREMENT | RECORDED | NONE |  |
| FEMALE-OUTER-W | Battery terminal | candidate female receptacle outer metal width | 10.6 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_MEASUREMENT | PHYSICAL_MATING_REQUIRED | NONE |  |
| BAT-BOTTOM-TERM-TOP | Battery terminal | battery bottom to installed terminal top envelope | 99.4 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_MEASUREMENT | RECORDED | NONE |  |
| BAT-BODY-H | Battery | body height for common-datum terminal derivation | 92.5 | mm | MEASURED | 2026-08-09..2026-08-10 | PARENT_MEASUREMENT | RECORDED | NONE |  |
| BAT-TERM-PROTRUSION | Battery terminal | terminal protrusion above battery body | 6.9 | mm | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | RECORDED | NONE |  |
| TERM-PAIR-OUTER | Battery terminal | terminal pair outer span | 29.5 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_USER_MEASUREMENT | RECORDED | NONE |  |
| TERM-PAIR-INNER | Battery terminal | terminal pair inner gap | 20.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_USER_MEASUREMENT | RECORDED | NONE | Individual terminal width not derived. |
| TERM-PROTECTOR-W | Battery terminal | protector internal width | 13.0 | mm | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | PRIOR_DISCUSSION | FINAL_FALSE | NONE | Based on10.6 mm terminal width; no CAD generated. |
| HARNESS-HOLD-01 | Battery harness | actual crimped wire | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-02 | Battery harness | wire gauge | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-03 | Battery harness | wire insulation OD | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-04 | Battery harness | crimp barrel length | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-05 | Battery harness | completed receptacle axial length | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-06 | Battery harness | bend start distance | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-07 | Battery harness | cable bend radius | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-08 | Battery harness | strain relief dimensions | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-09 | Battery harness | fuse | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-10 | Battery harness | final connector | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| HARNESS-HOLD-11 | Battery harness | waterproof boot/insulation | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_MEASURED | HOLD_CRIMP_TOOL_AND_HARNESS | NONE |  |
| BBOX-BAT-FIT-GATE | BBOX | battery fit | PHYSICAL_PASS_CANDIDATE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | CANDIDATE_ONLY | NONE |  |
| BBOX-TERM-PACKAGING | BBOX | terminal packaging | CONDITIONAL_PASS_CANDIDATE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | ASSESSMENT | HARNESS_HOLD | NONE |  |
| BBOX-WATERPROOF | BBOX | waterproof | NOT_TESTED | status | HOLD | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| FRAME-UPPER-OUTER-1 | Frame | upper outer dimension 1 | 540.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-UPPER-OUTER-2 | Frame | upper outer dimension 2 | 181.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-LOWER-OUTER-1 | Frame | lower outer dimension 1 | 442.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-LOWER-OUTER-2 | Frame | lower outer dimension 2 | 181.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-HEIGHT | Frame | compact frame height | 150.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-UPPER-CLEAR-1 | Frame | upper clear dimension 1 | 500.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-UPPER-CLEAR-2 | Frame | upper clear dimension 2 | 100.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-LOWER-CLEAR-1 | Frame | lower clear dimension 1 | 400.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-LOWER-CLEAR-2 | Frame | lower clear dimension 2 | 140.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-VERTICAL-L | Frame | vertical member length | 110.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-GROUND-REF | Frame | frame-bottom-to-ground/crawler-bottom reference | 68.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-INSERT-DATUM | Frame | idler-side observation datum to upper frame underside | 108.0 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-ALT-DATUM | Frame | previous different-datum passage measurement | 90.7 | mm | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE | Parent axis/datum naming retained. |
| FRAME-VERTICAL-QTY | Frame | vertical member count | 4 | count | MEASURED | 2026-08-09..2026-08-10 | PRIOR_PHYSICAL_AUTHORITY | RECORDED | NONE |  |
| FRAME-150-STATE | Frame | 150 mm frame state | PRIMARY_COMPACT_BASELINE_CANDIDATE | status | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | ASSESSMENT | RECORDED | NONE |  |
| FRAME-190-STATE | Frame | 190 mm frame state | ALTERNATIVE_HOLD | status | HOLD | 2026-08-09..2026-08-10 | ASSESSMENT | RECORDED | NONE |  |
| FRAME-BAT-PASS | Frame/Battery | battery physical passage | PHYSICAL_PASS_USER_REPORTED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | PRIOR_USER_TEST | RECORDED | NONE |  |
| H25-COUPON-COLLAR | H2.5-A1-2S | collar/full-hardware narrowest coupon clearance | VISIBLE_USABLE_CLEARANCE | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| H25-COUPON-REACTION | H2.5-A1-2S | reaction/related narrowest coupon clearance | CLEARANCE_PRESENT | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | RECORDED | NONE |  |
| H25-CAND-W90 | H2.5-A1-2S | coupon candidate code | W90 | candidate_code | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | PARENT_CANDIDATE_SET | NOT_SELECTED | NONE |  |
| H25-CAND-W92 | H2.5-A1-2S | coupon candidate code | W92 | candidate_code | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | PARENT_CANDIDATE_SET | NOT_SELECTED | NONE |  |
| H25-CAND-W94 | H2.5-A1-2S | coupon candidate code | W94 | candidate_code | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | PARENT_CANDIDATE_SET | NOT_SELECTED | NONE |  |
| H25-CAND-R41 | H2.5-A1-2S | coupon candidate code | R41 | candidate_code | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | PARENT_CANDIDATE_SET | NOT_SELECTED | NONE |  |
| H25-CAND-R42 | H2.5-A1-2S | coupon candidate code | R42 | candidate_code | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | PARENT_CANDIDATE_SET | NOT_SELECTED | NONE |  |
| H25-CAND-R43 | H2.5-A1-2S | coupon candidate code | R43 | candidate_code | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | PARENT_CANDIDATE_SET | NOT_SELECTED | NONE |  |
| H25-FINAL-TOL | H2.5-A1-2S | final selected tolerance | None | HOLD | HOLD | 2026-08-09..2026-08-10 | NOT_REPORTED | HOLD | NONE |  |
| H25-HAND-ROT | H2.5-A1-2S | aggressive hand rotation shaft shift | NONE_REPORTED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | NO_SHAFT_SHIFT_REPORTED | NONE |  |
| H25-STATIC-INITIAL | H2.5-A1-2S | initial1.2 kg static lever observation shaft shift | NONE_REPORTED | status | USER_REPORTED_PHYSICAL | 2026-08-09..2026-08-10 | USER_REPORT | PRELIMINARY_ONLY / CREEP_NOT_CLOSED | NONE |  |
| H25-LOAD-MASS | H2.5-A1-2S | preliminary static-load battery mass | 1.2 | kg | MEASURED | 2026-08-09..2026-08-10 | PARENT_MEASUREMENT | RECORDED | NONE |  |
| H25-LEVER | H2.5-A1-2S | later observation lever point | 70.0 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE |  |
| H25-G | H2.5-A1-2S | nominal gravitational acceleration reference | 9.80665 | m/s^2 | DERIVED | 2026-08-09..2026-08-10 | STANDARD_CONSTANT | REFERENCE_ONLY | NONE |  |
| H25-TORQUE-CALC | H2.5-A1-2S | nominal vertical/perpendicular torque calculation | 0.8237586 | N*m | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | DERIVED_NOMINAL_REFERENCE_ONLY | NONE | Not formal torque PASS. |
| H25-TORQUE-ROUND | H2.5-A1-2S | rounded nominal torque reference | 0.824 | N*m | DERIVED | 2026-08-09..2026-08-10 | CALCULATION | DERIVED_NOMINAL_REFERENCE_ONLY | NONE |  |
| H25-CREEP | H2.5-A1-2S | 1.2 kg at70 mm creep observation | PHYSICAL_OBSERVATION_PENDING / DO_NOT_CLOSE | status | HOLD | 2026-08-09..2026-08-10 | USER_REPORT | PENDING | NONE |  |
| H25-FULL-SPROCKET | H2.5-A1-2S | full sprocket | HOLD | status | HOLD | 2026-08-09..2026-08-10 | PARENT_GATE | RECORDED | NONE |  |
| DRIVE-SMALL-T | DRIVE | small pulley tooth count | 20 | teeth | CAD_NOMINAL | 2026-08-09..2026-08-10 | PARENT_CAD | RECORDED | NONE |  |
| DRIVE-LARGE-T | DRIVE | large pulley tooth count | 60 | teeth | CAD_NOMINAL | 2026-08-09..2026-08-10 | PARENT_CAD | RECORDED | NONE |  |
| DRIVE-PITCH | DRIVE | HTD5M pitch | 5.0 | mm | CAD_NOMINAL | 2026-08-09..2026-08-10 | PARENT_CAD | RECORDED | NONE |  |
| DRIVE-CENTER | DRIVE | 20T-to-60T center distance | 180.0 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | RECORDED | NONE |  |
| DRIVE-STRING | DRIVE | vinyl string loop | 583.0 | mm | MEASURED | 2026-08-09..2026-08-10 | USER_REPORTED | CONFLICT_RETAINED | NONE |  |
| DRIVE-113-TEETH | DRIVE | 113T candidate tooth count | 113 | teeth | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | V0.9.5.1_DISCUSSION | PRIMARY_TPU_TRIAL_CANDIDATE | NONE |  |
| DRIVE-113-LENGTH | DRIVE | 113T candidate pitch length | 565.0 | mm | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | V0.9.5.1_DISCUSSION | PRIMARY_TPU_TRIAL_CANDIDATE | NONE |  |
| DRIVE-114-TEETH | DRIVE | 114T candidate tooth count | 114 | teeth | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | V0.9.5.1_DISCUSSION | COMPARISON_CANDIDATE | NONE |  |
| DRIVE-114-LENGTH | DRIVE | 114T candidate pitch length | 570.0 | mm | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | V0.9.5.1_DISCUSSION | COMPARISON_CANDIDATE | NONE |  |
| DRIVE-112-TEETH | DRIVE | 112T candidate tooth count | 112 | teeth | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | V0.9.5.1_DISCUSSION | COMPARISON_CANDIDATE | NONE |  |
| DRIVE-112-LENGTH | DRIVE | 112T candidate pitch length | 560.0 | mm | DESIGN_CANDIDATE | 2026-08-09..2026-08-10 | V0.9.5.1_DISCUSSION | COMPARISON_CANDIDATE | NONE |  |
| DRIVE-CONFLICT | DRIVE | 583 mm string versus two-pulley geometry | UNRESOLVED | status | HOLD | 2026-08-09..2026-08-10 | ASSESSMENT | PHYSICAL_BELT_TEST_REQUIRED | NONE |  |
| DRIVE-TPU | DRIVE | 113T TPU trial | PHYSICAL_TEST_PENDING | status | HOLD | 2026-08-09..2026-08-10 | V0.9.5.1_PARENT | RECORDED | NONE |  |
| DRIVE-COMMERCIAL | DRIVE | commercial belt final | HOLD | status | HOLD | 2026-08-09..2026-08-10 | ASSESSMENT | NO_PURCHASE_APPROVAL | NONE |  |
| POWERED | System | powered rotation | NOT_APPROVED | status | HOLD | 2026-08-09..2026-08-10 | PROTECTED_GATE | RECORDED | NONE |  |
| FIELD | System | field deployment | NOT_APPROVED | status | HOLD | 2026-08-09..2026-08-10 | PROTECTED_GATE | RECORDED | NONE |  |

## Prompt numeric exclusions

- `0..49` (prompt section numbers): document structure, not engineering data
- `1..42` (requested final-report numbering): output structure, not engineering data
- `v0.9.4.0..v0.9.5.2` (lane versions): version identifiers; parent hashes are audited separately
- `20260725` (historical branch identifier): identifier component, not measurement
- `facb4f63...` (Git commit hash): identifier; recorded by repository audit
- `4 tracked changes` (pre-existing worktree state): repository count; recorded by repository audit, not measurement ledger
- `Plate 02` (printed artifact name): part identifier; print result is ledgered
- `M3/M4` (fastener/hole designation): thread nominal designation, not a measured diameter
- `YYYYMMDD_HHMMSS` (ZIP filename format): timestamp template, not engineering data
- `6.3mm-class` (connector reference class): compatibility label only; measured tab6.3 mm is ledgered
