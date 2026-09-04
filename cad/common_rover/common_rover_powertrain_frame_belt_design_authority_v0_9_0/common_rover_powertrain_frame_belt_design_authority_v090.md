# Common Rover powertrain, frame and belt design authority v0.9.0

`PS-CR-PWR-FRAME-BELT-V090`  
`NOT_FOR_MANUFACTURING` · `PHYSICAL_FIT_HOLD` · `FIELD_DEPLOYMENT_NOT_APPROVED`

## Scope and parent protection

This differential authority preserves v0.8 through v0.8.5 byte-for-byte. It
adds the missing full powertrain, four belt corridors, belt-first frame layout,
parametric slide clutches, conditional lower PTO and high work-unit electrical
interface. Protected paths: 124.

## Superseded contract

`Z_PTO_AXIS >= Z_MOTOR_AXIS` is
`SUPERSEDED_BY_V090_CONDITIONAL_LOWER_PTO`.

The new contract is:

`PTO_AXIS_CAN_BE_LOWER_THAN_MOTOR_AXIS`

if `PTO_ROTATION_ENVELOPE_BOTTOM_Z >= 200` and the belt/frame contracts pass.
Z=260 is not a standard candidate; standard candidates start at Z=280.

## Fixed functional architecture

- Two motors, two independent PTO ports and no common PTO shaft.
- One mechanical DRIVE / NEUTRAL / PTO slide clutch per side.
- DRIVE and PTO cannot be engaged simultaneously.
- PTO operation requires both crawler drives disengaged and vehicle speed zero.
- Four independent HTD 5M 15 mm belts: two DRIVE and two PTO.
- CBOX is forward of BBOX; both bottoms remain at Z=200 or above.
- KP000 direct-to-2040 is `FAIL_PHYSICAL_FIT`; A5052 5 mm wide support plates are required.

## Architecture comparison

Architecture A retains a tight coaxial lateral stack and remains
`HOLD_AXIAL_STACK_AND_CANTILEVER`. Architecture B uses a short-stroke selector
and independent jackshaft candidates to separate belt planes in X/Z. Architecture
B is recommended, but bearing, dog and shaft details remain measurement holds.

## Search stages

Stage 0 reproduces the high-PTO baseline. Stage 1 relocates the frame while
remaining high. Stage 2 lowers PTO Z. Stage 3 adds PTO forward X motion. Stage 4
refines frame and support positions. Stage 5 compares A/B. Stage 6 is reserved
for extra metal supports and was not adopted because a conditional candidate
exists. Frame candidates evaluated: 1875.

## Selected candidates

| Selection | ID | Architecture | PTO X | PTO Z | rotation bottom | belt-frame | width |
|---|---|---:|---:|---:|---:|---:|---:|
| Recommended MID | S4-B-PTOX040.0-Z320.0-FX40.0-FY20.0-FZ20.0 | B | 100.0 | 320.0 | 260.0 | 4.75 | 290.0 |
| HIGH comparison | S1-A-PTOX020.0-Z370.0-FX40.0-FY20.0-FZ20.0 | A | 80.0 | 370.0 | 310.0 | 4.75 | 298.0 |
| LOW comparison | S3-B-PTOX040.0-Z280.0-FX40.0-FY20.0-FZ20.0 | B | 100.0 | 280.0 | 220.0 | 4.75 | 290.0 |

The recommended PTO axis is X=100.0 mm, Z=320.0 mm.
The OD120 safety envelope bottom is Z=260.0 mm, giving
60.0 mm above the water/mud limit.

## Belt-first frame

The physical, nominal and safety widths are 15, 21 and 31 mm. Installation,
removal, tensioner, guard and tool envelopes exist for all four belts. The
selected split 2040 rails sit in the lateral gap between PTO and DRIVE
corridors at Y=±88.75 mm. Long rail pieces are 290 and 170 mm;
no single member exceeds 400 mm.

## Slide clutch

Each side contains a motor input shaft, rotationally locked slider, DRIVE and
PTO dog hubs, neutral gap, shift-fork reservation, actuator reservation,
position-sensor reservation, axial stops and full-stroke envelope. Power loss
prioritizes NEUTRAL. Final torque dogs remain metal candidates; PETG-only final
torque transmission is prohibited.

## Work-unit electrical interface

E2, a high front electrical bridge centered at X=180, Z=455, is recommended.
Its bottom Z=440 is above BBOX top Z=350 and outside the belt, clutch and PTO
rotation envelopes. Physical presence sensing is separate from unit ID.
`UNIT_PRESENT != TRUE` disables PTO.

The unit umbilical rises in the protected front-center route, connects to E2,
then returns to CBOX without entering belt or track corridors. Voltage, pins,
connector and actual sensor envelopes remain HOLD.

## Release state

- Functional powertrain contract: FIXED
- Frame / belt / PTO height / unit interface: CONDITIONAL_PASS_CANDIDATE
- Physical fit, support machining, shaft cutting, drilling and manufacturing: HOLD
- Field deployment: NOT_APPROVED
