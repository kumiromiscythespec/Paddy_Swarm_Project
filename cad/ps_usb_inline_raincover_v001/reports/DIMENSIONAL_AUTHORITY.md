# DIMENSIONAL AUTHORITY

## Authority priority

```text
1. actual physical measurement
2. successful physical coupon
3. CAD nominal
4. provisional assumption
```

Physical結果がCAD nominalと矛盾する場合はPhysicalをAuthorityとする。

## Measured Authority

| Item | Value | Status |
|---|---:|---|
| Connector maximum width | 18.7 mm | measured |
| Small cable OD | 3.6 mm | measured |
| Large cable OD | 7.9 mm | measured |

写真Authority: 2本の異径cableが屋外中間接続され、簡易tape保護状態で雨天に濡れる位置へ露出している。

## UNKNOWN_PHYSICAL

```text
CONNECTOR_BODY_LENGTH
CONNECTOR_BODY_HEIGHT
CONNECTOR_SHAPE_DETAIL
CONNECTOR_RIGID/FLEXIBLE_BOUNDARY
CABLE_ENTRY_STRAIN_RELIEF_LENGTH
```

これらを推測でPhysical Authorityへ昇格しない。

## Provisional chamber

```text
CHAMBER_INNER_L = 50.0 mm
CHAMBER_INNER_W = 24.0 mm
CHAMBER_INNER_H_MIN = 16.0 mm
STATUS = PROVISIONAL_PHYSICAL_VALIDATION_REQUIRED
```

Known width total clearance = 5.3 mm、nominal side clearance = 2.65 mm/side。length/height clearanceとconnector compressionはfit couponで決定する。

## Cable Authority candidates

| Side | Physical OD | CAD main channel | Diametral clearance | Coupon candidates |
|---|---:|---:|---:|---|
| Small | 3.6 mm | 4.6 mm | 1.0 mm | 4.4 / 4.6 / 4.8 mm |
| Large | 7.9 mm | 9.0 mm | 1.1 mm | 8.8 / 9.0 / 9.2 mm |

Main valuesはcoupon未合格のCAD candidate。cable jacket compression、printer XY compensation、material shrinkを実物で確認する。

## Shell and labyrinth nominal

```text
WALL_T = 3.0 mm
MAIN_FLANGE_T = 4.0 mm
TOP_OVERLAP_SKIRT = 6.0 mm
PARTING_STEP_H = 2.0 mm
PARTING_OVERLAP = 3.0 mm
PARTING_CLEARANCE = 0.30 mm
LABYRINTH_HORIZONTAL_RUN = 10.0 mm
LABYRINTH_VERTICAL_OFFSET = 5.0 mm
MIN_CABLE_BEND_SPACE_R = 4.0 mm
ROOF_SLOPE = 3.0 deg
FLOOR_SLOPE = 2.0 deg, two-way
FLOOR_CENTER_CROWN = 0.873 mm
DRAIN_D = 2.5 mm
DRAIN_COUNT = 2
```

Closure: M3 x4、clearance 3.4 mm、hex trap AF 5.8 mm、depth 2.5 mm。screw centers x +/-18、y +/-22 mmでroof projection外。

## CAD envelopes

| Artifact | BRep solids | Bounding box X x Y x Z |
|---|---:|---|
| Upper shell | 1 | 82.604 x 52.000 x 22.204 mm |
| Lower shell | 1 | 76.003 x 52.000 x 13.003 mm |
| Fit coupon print layout | 2 | 18.000 x 97.300 x 20.509 mm |

52 mm overall widthは左右external M3 flangeを含む。雨umbrella本体は36.6 mm nominal width、lower trayは30.0 mm nominal width。

## Controlled geometric findings

```text
UPPER vs LOWER SOLID INTERFERENCE = 0.00000000 mm3
ROOF SCREW PENETRATION = NONE
STRAIGHT OUTSIDE-TO-CONNECTOR LINE = NONE BY CAD PATH ARRANGEMENT
HARD CABLE CLAMP = FORBIDDEN / NOT DESIGNED
CONNECTOR COMPRESSION = NONE TARGET / PHYSICAL PENDING
```

Direct-line checkは水圧、capillary action、print porosity、surface tensionを証明しない。

## Rating and holds

```text
RATING = SPLASH_RESISTANT_NOT_WATERPROOF
IP RATING = NOT CLAIMED
IMMERSION = OUT OF SCOPE
HIGH PRESSURE WASH = OUT OF SCOPE
WATERTIGHT_STL != WATERPROOF_PRINT
```

CAD終了時BLOCKER: connector chamber physical fit、cable channel fit、labyrinth drain effectiveness。

