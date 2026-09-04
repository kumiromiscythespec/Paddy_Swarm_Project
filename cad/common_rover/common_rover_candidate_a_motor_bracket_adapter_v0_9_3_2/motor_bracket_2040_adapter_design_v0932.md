# Candidate A motor-bracket to 2040 adapter v0.9.3.2

## Scope

`PS_CR_V0932_MOTOR_BRACKET_TO_2040_ADAPTER` is a flat, no-load PETG mockup adapter. Two identical parts are intended after a one-part fit test. It supports the existing 40.2×40.0 mm metal bracket footprint and does not touch or clamp the motor cylinder.

`OLD_CRADLE_JIG_STATUS=DEPRECATED_BY_V0932_ADAPTER_PLATE`

## Exact geometry

- plate: 42.0×80.0×8.0 mm, XY corner radius 3.0 mm, base Z=0
- bracket holes: X=±12, Y=±15 mm; measured pitch 24×30 mm
- frame holes: X=±10, Y=±30 mm; pitch 20×60 mm; Ø5.7 through
- variants: Ø3.60 and Ø3.70 M4 pilot, 7.0 mm blind depth, 1.0 mm bottom floor
- bracket and frame local origins/centerlines coincide

## Verified clearances

- M4/M5 actual-shape intersection: 0 mm³ for all 16 pairs
- Ø9.5 washer keep-out/bracket footprint: 0 mm³; boundary gap 5.25 mm
- Ø11 tool keep-out/bracket footprint: 0 mm³; boundary gap 4.5 mm
- washer keep-out/plate edge minimum: 5.25 mm
- C370 pilot outside residual to plate edge: 7.15 mm

## Frame proxy

No repository solid proves the exact physical 2040 T-slot cross-section. The v0.9.3.2 proxy is only 40×120×20 mm with X=±10 mm centerline witnesses. `T_SLOT_EXACT_PROFILE=MEASUREMENT_HOLD`.

## Release state

`ADAPTER_CAD=CONDITIONAL_PASS_CANDIDATE`; `PHYSICAL_FIT=NOT_YET_PERFORMED`; `M4_THREAD_DIAMETER=CALIBRATION_REQUIRED`; `M5_FRAME_INTERFACE=NO_LOAD_CANDIDATE`; `POWERED_ROTATION=NOT_APPROVED`; `BELT_TENSION=NOT_APPROVED`; `TORQUE_LOAD=NOT_APPROVED`; `METAL_ADAPTER_RELEASE=NOT_APPROVED`; `FIELD_DEPLOYMENT=NOT_APPROVED`.
