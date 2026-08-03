# Candidate A physical mockup plan v0.9.3.1

## Decision and scope

This kit prepares the v0.9.3.0 recommendation `A_LATERAL_FRONT_DIRECT + P1` for a **non-powered, no-load, dimensional mockup**. It does not update design authority and does not release a motor mount, belt drive, shaft, clutch, frame hole, purchase, or manufacturing operation.

`PHYSICAL_MOCKUP_CLASS=NO_LOAD_LAYOUT_ONLY`

## Exact datums

- coordinate frame: +X left, +Y rear, +Z up
- left motor front plate: `(68.0, -185.0, 105.0) mm`
- right motor front plate: `(-68.0, -185.0, 105.0) mm`
- selector axes: X=±38, Y=-185, Z=166 mm
- DRIVE output witnesses: X=±66, Y=-185, Z=166 mm
- PTO witnesses: X=±14, Y=-185, Z=166 mm, inward and mechanically independent

CAD re-confirms motor fixed width 276.2 mm, G1 motor guard width 286.2 mm, transformed track-proxy width 290.0 mm, complete guarded width 290.0 mm, and S2 temporary service width 316.2 mm. Service width is not a fixed-width failure.

## Jig selection

`JIG-B_EXTERNAL_CRADLE` is recommended. It references the known 40.1×45.5×42.8 mm bracket/motor envelope with loose clearance and a soft TPU, rubber, or felt liner. It must not clamp the cylinder or carry torque.

JIG-A remains a comparison only: the four Ø3.4 mm candidate holes may be used through adjustable slots for a no-load mockup, but their origin, edge distances, and the complete 27.7 mm vertical-slot geometry are not known. JIG-A is not a manufacturing mount.

## Mockup architecture

Fourteen compact printable gauges fit individually inside the Bambu A1 256 mm class envelope. Large rover boundaries, CBOX/BBOX, track proxy, service sweep, unit bay, and cable bend regions are 1:1 SVG templates with tiling/registration marks. Existing STANDARD 20T and 60T full dummies are referenced by SHA and are not duplicated.

The authority-backed frame envelope is 20×20 T-slot class. A 2040 profile is not currently released; use an existing compatible T-nut, board/MDF, short printed dummy, or paper template without cutting or drilling.

## Powerpath mockup

Each side independently displays motor → 20T envelope → loose belt plane → 60T physical/safety envelope → selector → DRIVE/NEUTRAL/PTO witnesses. Belts remain untensioned. A left/right common shaft is prohibited. Unit weight is supported by a separate hitch/guide-frame region, never by PTO shafts.

## Completion state

- `CANDIDATE_A_MOCKUP_KIT=READY_FOR_PRINT_OR_TEMPLATE`
- `PHYSICAL_MOCKUP=NOT_YET_PERFORMED`
- `FIXED_WIDTH=CAD_RECONFIRMED`
- `GUARD_WIDTH=PHYSICAL_CONFIRMATION_REQUIRED`
- `MOTOR_SERVICE_ACCESS=PHYSICAL_CONFIRMATION_REQUIRED`
- `BELT_PLANE=PHYSICAL_CONFIRMATION_REQUIRED`
- `PTO_UNIT_CONNECTION=PHYSICAL_CONFIRMATION_REQUIRED`
- `LOAD_TEST=NOT_PERFORMED`
- `POWERED_TEST=NOT_APPROVED`
- `MANUFACTURING=HOLD`
- `FIELD_DEPLOYMENT=NOT_APPROVED`
