# PHYSICAL TEST PROTOCOL — v002

Do not infer a higher-level PASS from a lower-level result. Mount with long axis approximately horizontal, drains downward, and cover suspended above ground. Ground placement is not standard operation.

## 1. V002 CONNECTOR CHAMBER TEST

Measured Authority: L = 95.1 mm, W = 18.7 mm, H = 10.8 mm  
Chamber: 102 × 24 × 16 mm

| Record | Result |
|---|---|
| connector insertion | PASS / FAIL |
| left axial clearance | ___ mm |
| right axial clearance | ___ mm |
| side clearance | GOOD / TIGHT / LOOSE |
| height clearance | GOOD / TIGHT / LOOSE |
| camera cable transition | NATURAL / BENT / PINCHED |
| extension cable transition | NATURAL / BENT / PINCHED |
| connector compression | NONE / YES |
| shell datum closes | YES / NO |
| RESULT | PASS / FAIL / HOLD |

Print `connector_chamber_fit_coupon_v002.stl` first. Lay in the real connected assembly, confirm both rigid→flex exits and natural transitions, close the upper datum without force, and measure end clearances. Any compression or pinching is FAIL.

## 2. V002 LABYRINTH/DRAIN TEST

| Record | Camera side | Extension side |
|---|---|---|
| water introduced | ___ mL | ___ mL |
| drain exits | YES / NO | YES / NO |
| witness bay | DRY / TRACE / WET | DRY / TRACE / WET |

| Additional record | Result |
|---|---|
| pooling after 5 min | NONE / YES |
| test at level | PASS / FAIL |
| test +5deg | PASS / FAIL |
| test -5deg | PASS / FAIL |
| RESULT | PASS / FAIL / HOLD |

Use colored water and fresh dry tissue in `WITNESS_BAY`. Check that the Ø2.5 mm exit is not blocked before each run. `TRACE` does not pass the full-shell gate.

The coupon is the common symmetric 4.4 mm end module. Run it twice: once with the actual camera-side cable and once with the actual extension-side cable, reversing the recorded side label while keeping the drain physically downward.

## 3. Full-shell dry and unpowered spray test

Gate to full-shell test: connector fit PASS, both transitions NATURAL, shell datum fit YES, labyrinth drain PASS, witness bay DRY.

Assemble dry with M3×6 tightened evenly. Verify no visible central bowing and continuous parting-labyrinth engagement. With USB unpowered, spray in this order and open the connector chamber after each case:

1. TOP
2. 45 DEG
3. SIDE
4. CABLE TRACKING
5. BOTTOM SPLASH

Minimum PASS: connector surface DRY, witness area DRY, drain FUNCTIONAL, pooling NONE, shell closure MAINTAINED. Any TRACE prevents powered testing.

## 4. Powered USB gate and test

Proceed only after `FIT PASS`, `DRAIN PASS`, and `UNPOWERED SPRAY PASS`.

| Record | Result |
|---|---|
| camera stream uninterrupted | YES / NO |
| USB disconnect | NONE / EVENT |
| reconnect required | NO / YES |
| connector visibly dry | YES / NO |
| RESULT | PASS / FAIL / HOLD |

## 5. Ordered progression

1. connector chamber fit coupon
2. connector physical fit
3. labyrinth/drain coupon
4. colored-water drain test
5. full upper/lower shell
6. dry assembly
7. unpowered spray test
8. controlled powered USB test
9. outdoor rain
10. heavy / wind-driven rain

Status progression: `MEASURED_CONNECTOR_CHAMBER_PHYSICAL_PASS` → `LABYRINTH_DRAIN_PHYSICAL_PASS` → `USB_RAINCOVER_UNPOWERED_WATER_PASS` → `USB_RAINCOVER_LIVE_OPERATIONAL_PASS`. Field heavy rain remains a separate status.
