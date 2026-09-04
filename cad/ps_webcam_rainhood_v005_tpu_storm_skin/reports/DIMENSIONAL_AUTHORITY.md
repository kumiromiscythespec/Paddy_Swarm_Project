# DIMENSIONAL AUTHORITY

## Upstream v004

Authority lane: `cad/ps_webcam_rainhood_v004_b15_position_retention/`

| Authority artifact | SHA256 |
|---|---|
| `cad/ps_webcam_rainhood_v004.py` | `0d0a2979c6a3b38ed40585bcddb6d64aa167995e6413cc3cb94ad7bcabd99c94` |
| `reports/validation_report.json` | `ab23b0c902bdc43a8a2a96da67397f620d1760ab6000212d4d857308c3e80187` |
| `step/rainhood_b15_position_retention_v004.step` | `51acb7fcc67dcd4785247f70470ef583aa72446036c9110d3f031fa07baa86f4` |

v004 status: `CAD_COMPLETE_B15_POSITION_RETENTION_PHYSICAL_VALIDATION_PENDING`。

## Locked interface and optical dimensions

```text
OPTICAL_VARIANT = B_setback15
FINAL_SETBACK = 15.0 mm
FINAL_FRONT_Y = -45.4 mm
FINAL_BEVEL_DEG = 40.0 deg
FINAL_BEVEL_RUN = 2.080 mm
FINAL_FRONT_LENGTH = 15.0 mm
```

```text
A_setback10: FAIL_OPTICAL
B_setback15: NOMINAL_OPTICAL_PASS / SELECTED_CONDITIONAL
C_setback20: OPTICAL_ROBUST_PASS / KNOWN_FALLBACK
```

tripod datum、carrier seating plane、tripod axis、carrier M4 interface、USB route、sidewall optical envelope、camera clearanceはv004から変更しない。

Latest physical observation: カメラ本体を意図的に捻ってもフードの映り込みは確認されなかった。

## v005 controlled additions

| Feature | Authority candidate |
|---|---:|
| TPU main membrane | 1.5 mm |
| Acoustic comparison | 1.0 / 1.5 / 2.0 mm |
| Preload X/Y | 0.5% / 0.5%, parameterized |
| Preload comparison | 0 / 0.5 / 1.0% |
| Side/rear skirt | 9.0 / 9.0 mm |
| External nose wrap down | 1.0 mm |
| Mechanical anchors | 4 |
| Anchor stations | Y -26.0 / +24.0 mm on left/right |
| TPU tab | 2.5 mm thick |
| T-head / root-neck | 12.0 / 10.0 mm wide |
| Tab root | R2.0 mm |
| PETG cavity clearance | 0.4 mm nominal |
| Neck lateral clearance | 0.2 mm per side |
| Roof penetration | none |
| Printed flat roof pattern | 117.410 x 87.988 mm |
| Installed STEP numerical contact clearance | 0.10 mm |

0.10 mmはCAD接触面の数値表現だけであり、flat-print STLの寸法Authorityではない。flat patternは0.5% X/Y preloadを与える。

## Computed delta and interference

```text
v004 hood removed volume: 0.000000 mm3
external PETG anchor geometry added: 1795.641 mm3
TPU vs camera: 0.000000 mm3
TPU vs optical exclusion envelope: 0.000000 mm3
TPU vs USB route: 0.000000 mm3
TPU vs carrier: 0.000000 mm3
TPU nose margin above B optical interior: 2.000 mm
```

PETG変更は4個の外付けsidewall cageだけである。上面穴、内部optical geometry cut、carrier modificationはない。

## Material hold

```text
MATERIAL = TPU
TPU_SHORE = UNKNOWN_PHYSICAL
GEOMETRY_ASSUMPTION = approximately 95A, not Authority
PRINTER = Bambu Lab A1
NOZZLE = 0.4 mm
```

実TPU filament、収縮、creep、層間接着をcouponで確定するまで0.5% preloadと0.4 mm clearanceはPhysical Authorityではない。

## Legacy failure authority

```text
PRINTED_PIPE_CLAMP: REJECTED
FAIL_BOLT_REACH: TRUE
FAIL_PRINT_ROBUSTNESS: TRUE
STATIC_LOAD_TEST: NOT_TESTED
```

細いPETG earを再発させない。今回のcageは連続top capと両shoulderを持ち、4点へ荷重分散するが、coupon破壊試験前は物理PASSではない。

## Current print and field status

現行rainhood前端の約1 mm未満にminor spaghetti defectがある。

```text
STRUCTURAL_QUALITY: ACCEPTED
OPTICAL_OPERATION: PASS
FIELD_INSTALLATION: PROCEEDED
OUTDOOR_INSTALLATION: COMPLETE
YOUTUBE_LIVE_TEST: OPERATIONAL
RAIN: OBSERVED
RAIN_IMPACT_CLICK: OBSERVED
```

v005 noseはこの領域へ点荷重を集中せず、storm skinは着脱可能とする。field systemへの交換はcoupon/bench gateの後に行う。

## Status boundary

CAD geometry authority candidateは完成。anchor retention、preload choice、acoustic thickness、full-skin peel/uplift、field wind/rain、water trapping、UV/weather agingはPhysical Authority未確定。
