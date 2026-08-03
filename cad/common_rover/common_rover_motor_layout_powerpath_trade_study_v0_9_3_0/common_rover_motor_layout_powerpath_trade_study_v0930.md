# Common Rover motor-layout and powerpath trade study v0.9.3.0

## Decision

`RECOMMENDED_LAYOUT_FOR_NEXT_CAD=A_LATERAL_FRONT_DIRECT`

`SECONDARY_LAYOUT=E_LONGITUDINAL_FRONT_PTO`

`RECOMMENDED_POWERPATH=P1_LATERAL_DIRECT_COMMON_SELECTOR_PATTERN_LEFT_RIGHT_INDEPENDENT`

`SECONDARY_POWERPATH=P4_LONGITUDINAL_FRONT_PTO`

`DECISION_CLASS=TOP_2_CANDIDATES_PHYSICAL_MOCKUP_REQUIRED`

The word “common” in P1 means a common selector **pattern**, not a physical shaft joining left and right. Both sides remain mechanically independent. Candidate A has no right-angle stage and keeps the fixed guarded rover width at 290 mm because the existing track proxy, not the motor guard, controls width. Candidate E gives simpler forward unit input but adds a DRIVE-only bevel stage.

## Scope and releases

This lane is an envelope trade study, not a manufacturing drawing. `DESIGN_AUTHORITY_UPDATE=PROHIBITED`, `MANUFACTURING_RELEASE=NOT_APPROVED`, `PURCHASE_APPROVAL=NOT_APPROVED`, `POWERED_TEST=NOT_APPROVED`, and `FIELD_DEPLOYMENT=NOT_APPROVED`.

## Measurements and envelope policy

The physical motor record uses 36.9 mm cylinder diameter, 60.9 mm body-to-front-plate length, 16.9 mm shaft projection, 5.9 mm shaft diameter, 12.0 × 2.7 mm boss, and 9.2 mm rear terminal projection. Fixed axial length is 87.0 mm. Bracket values are 40.1 × 45.5 × 42.8 mm, thickness 3.1 mm. K is 3.4 mm. The 27.7 mm value belongs only to the bearing slot placeholder; exact slot geometry remains `MEASUREMENT_HOLD`. Measurement uncertainty is `USER_NOT_REPORTED`.

S0–S3 rear service extras (10/15/20/25 mm) and G0–G3 guard margins (3/5/8/10 mm) are swept separately. Fixed, guard, connector/tool, and removal envelopes are never merged into one width claim.

## Search result

| candidate | grid | feasible AABB | actual status | guarded width | rank |
|---|---|---|---|---|---|
| A_LATERAL_FRONT_DIRECT | 1190 | 956 | CONDITIONAL_PASS | 290.0 | 1 |
| B_LATERAL_ABOVE_CBOX_DIRECT | 3213 | 2562 | CONDITIONAL_PASS_SERVICE_HOLD | 290.0 | 4 |
| C_LATERAL_FORE_AFT_STAGGERED | 2448 | 1230 | FAIL_HARD_CONSTRAINT | 290.0 | 6 |
| D_LONGITUDINAL_SIDE_RAIL | 918 | 612 | CONDITIONAL_PASS | 290.0 | 3 |
| E_LONGITUDINAL_FRONT_PTO | 1122 | 935 | CONDITIONAL_PASS | 290.0 | 2 |
| F_VERTICAL_MOTOR | 2261 | 1615 | CONDITIONAL_PASS_HIGH_CG_HOLD | 290.0 | 5 |
| G_CURRENT_REPOSITORY_LAYOUT_REPRODUCTION | 1 | 0 | FAIL_HARD_CONSTRAINT | 290.0 | 7 |

The grid uses 2 or 5 mm X spacing and 5 mm Y/Z spacing. AABB is only a screening stage. The selected A–G points are rechecked with actual CadQuery common-volume calculations against CBOX, BBOX, frame, transformed track proxy, battery extraction keep-out, unit mating keep-out, and drainage keep-outs.

## Powerpaths

| path | motor | selector | PTO | 90° | bearings |
|---|---|---|---|---|---|
| P1 | X | X | INWARD_X_INDEPENDENT | 0 | 8 |
| P2 | X | X | INWARD_X_INDEPENDENT | 0 | 12 |
| P3 | Y | X | INWARD_X_INDEPENDENT | 1 | 12 |
| P4 | Y | Y | FORWARD_NEGATIVE_Y_INDEPENDENT | 1 | 10 |
| P5 | Z | X | INWARD_X_INDEPENDENT | 1 | 10 |
| P6 | FUTURE_PRODUCT | X_OR_Y | PRODUCT_SELECTION_HOLD | 1 | 8 |

Belts and chains only connect parallel axes. P3, P4, and P5 explicitly include bevel/miter gear candidates for every 90-degree transfer. All dog clutch parts are coaxial with their selector shaft. DRIVE and PTO simultaneous engagement is mechanically prohibited; switching requires motor stop and zero-speed confirmation. PTO work requires a brake or mechanical track lock.

## PTO and service

The recommended P1 interface is two independent inward X-axis PTO outputs. The secondary P4 interface is two independent forward (-Y) PTO outputs. A unit is supported by dedicated hitch/guide rails, never by PTO shafts. The actual 60T physical envelope is 100 mm OD and the inherited safety check is 120 mm OD; pulley bore/product fit and guard clearance remain HOLD.

Candidate B is not rejected geometrically, but its outward removal sweep crosses the transformed track proxy. Candidate C fails the right track proxy at the staggered point. Candidate F has a high-CG/weather penalty. Candidate G fails measured-motor-to-input-axis coaxiality.

## Clutch evidence

`S2_10P30=NO_LOAD_PRINTED_SLIDE_REFERENCE_ONLY`. The reported 10.30 mm printed S2 moved smoothly without twist, hang-up, visible radial play, or self-drop at 30–45 degrees. `METAL_TORQUE_CLUTCH_TOLERANCE=NOT_DERIVED_FROM_S2`.
