# Validation report

- Automated checks: **101/101 passed**
- Physical fit status: **CALIBRATION_PENDING**
- Scope: bore gauges and six-tooth curved coupons only; no full pulley.

## Pitch and outside-diameter references

| Curve | Requested pitch ref. | Calculated/adopted pitch dia. | Pitch diff. | Requested OD ref. | Adopted OD | OD diff. |
|---|---:|---:|---:|---:|---:|---:|
| 20T | 31.830988 | 31.830988618 | +0.000000618 | 30.69 | 30.686988618 | -0.003011382 |
| 60T | 95.492966 | 95.492965855 | -0.000000145 | 94.35 | 94.348965855 | -0.001034145 |

## Checks

| Result | Check | Detail |
|---|---|---|
| PASS | htd5m_bore_gauge_6mm_v0_1: one valid solid | solids=1, valid=True |
| PASS | htd5m_bore_gauge_6mm_v0_1: thickness | actual=8.000000 mm, expected=8.000000 mm |
| PASS | htd5m_bore_gauge_6mm_v0_1: center spacing | 14.000 mm |
| PASS | htd5m_bore_gauge_6mm_v0_1: minimum edge wall | end=3.000 mm, side=6.800 mm, minimum=3.000 mm |
| PASS | htd5m_bore_gauge_6mm_v0_1: bore count | 5 true-circle candidates |
| PASS | htd5m_bore_gauge_6mm_v0_1: center locations | -28.000, -14.000, 0.000, 14.000, 28.000 |
| PASS | htd5m_bore_gauge_6mm_v0_1: candidate diameters | 6.00 mm, 6.10 mm, 6.20 mm, 6.30 mm, 6.40 mm |
| PASS | htd5m_bore_gauge_6mm_v0_1: modeled cylindrical bores | D6.00@(-28.00,0.00), D6.10@(-14.00,0.00), D6.20@(0.00,0.00), D6.30@(14.00,0.00), D6.40@(28.00,0.00) |
| PASS | htd5m_bore_gauge_6mm_v0_1: both bore entries chamfered | conical faces=10 |
| PASS | htd5m_bore_gauge_6mm_v0_1: sensible A1 XY bounding box | 68.400 x 20.000 mm |
| PASS | htd5m_bore_gauge_10mm_v0_1: one valid solid | solids=1, valid=True |
| PASS | htd5m_bore_gauge_10mm_v0_1: thickness | actual=10.000000 mm, expected=10.000000 mm |
| PASS | htd5m_bore_gauge_10mm_v0_1: center spacing | 18.000 mm |
| PASS | htd5m_bore_gauge_10mm_v0_1: minimum edge wall | end=4.000 mm, side=8.750 mm, minimum=4.000 mm |
| PASS | htd5m_bore_gauge_10mm_v0_1: bore count | 6 true-circle candidates |
| PASS | htd5m_bore_gauge_10mm_v0_1: center locations | -45.000, -27.000, -9.000, 9.000, 27.000, 45.000 |
| PASS | htd5m_bore_gauge_10mm_v0_1: candidate diameters | 10.00 mm, 10.10 mm, 10.20 mm, 10.30 mm, 10.40 mm, 10.50 mm |
| PASS | htd5m_bore_gauge_10mm_v0_1: modeled cylindrical bores | D10.00@(-45.00,0.00), D10.10@(-27.00,0.00), D10.20@(-9.00,0.00), D10.30@(9.00,0.00), D10.40@(27.00,0.00), D10.50@(45.00,0.00) |
| PASS | htd5m_bore_gauge_10mm_v0_1: both bore entries chamfered | conical faces=12 |
| PASS | htd5m_bore_gauge_10mm_v0_1: sensible A1 XY bounding box | 108.500 x 28.000 mm |
| PASS | 20T: pitch diameter formula | 31.830988618 mm |
| PASS | 20T: requested pitch-diameter tolerance | calculated=31.830988618 mm, reference=31.830988 mm, difference=+0.000000618 mm |
| PASS | 20T: pitch preserved | pitch-circle arc=5.000000000 mm |
| PASS | 20T: six pitch stations | -45.000 deg, -27.000 deg, -9.000 deg, 9.000 deg, 27.000 deg, 45.000 deg |
| PASS | 20T: curved coupon span | 108.000 deg |
| PASS | 60T: pitch diameter formula | 95.492965855 mm |
| PASS | 60T: requested pitch-diameter tolerance | calculated=95.492965855 mm, reference=95.492966 mm, difference=-0.000000145 mm |
| PASS | 60T: pitch preserved | pitch-circle arc=5.000000000 mm |
| PASS | 60T: six pitch stations | -15.000 deg, -9.000 deg, -3.000 deg, 3.000 deg, 9.000 deg, 15.000 deg |
| PASS | 60T: curved coupon span | 36.000 deg |
| PASS | 20T/60T: curvature differs | OD=30.686989/94.348966 mm, pitch angle=18.000/6.000 deg |
| PASS | htd5m_20t_coupon_tight_v0_1: one valid solid | solids=1, valid=True |
| PASS | htd5m_20t_coupon_tight_v0_1: face width | actual=16.200000 mm, expected=16.200000 mm |
| PASS | htd5m_20t_coupon_tight_v0_1: curved paired-arc groove | R1'=1.320, R2'=0.558, depth=2.061 mm |
| PASS | htd5m_20t_coupon_tight_v0_1: six actual paired-arc groove stations | main-arc faces=12, transition-arc faces=12 |
| PASS | htd5m_20t_coupon_tight_v0_1: sensible A1 bounding box | 10.738 x 24.826 x 16.200 mm |
| PASS | htd5m_20t_coupon_standard_v0_1: one valid solid | solids=1, valid=True |
| PASS | htd5m_20t_coupon_standard_v0_1: face width | actual=16.200000 mm, expected=16.200000 mm |
| PASS | htd5m_20t_coupon_standard_v0_1: curved paired-arc groove | R1'=1.370, R2'=0.608, depth=2.112 mm |
| PASS | htd5m_20t_coupon_standard_v0_1: six actual paired-arc groove stations | main-arc faces=12, transition-arc faces=12 |
| PASS | htd5m_20t_coupon_standard_v0_1: sensible A1 bounding box | 10.738 x 24.826 x 16.200 mm |
| PASS | htd5m_20t_coupon_loose_v0_1: one valid solid | solids=1, valid=True |
| PASS | htd5m_20t_coupon_loose_v0_1: face width | actual=16.200000 mm, expected=16.200000 mm |
| PASS | htd5m_20t_coupon_loose_v0_1: curved paired-arc groove | R1'=1.420, R2'=0.658, depth=2.163 mm |
| PASS | htd5m_20t_coupon_loose_v0_1: six actual paired-arc groove stations | main-arc faces=12, transition-arc faces=12 |
| PASS | htd5m_20t_coupon_loose_v0_1: sensible A1 bounding box | 10.738 x 24.826 x 16.200 mm |
| PASS | htd5m_60t_coupon_tight_v0_1: one valid solid | solids=1, valid=True |
| PASS | htd5m_60t_coupon_tight_v0_1: face width | actual=16.200000 mm, expected=16.200000 mm |
| PASS | htd5m_60t_coupon_tight_v0_1: curved paired-arc groove | R1'=1.488, R2'=0.538, depth=2.102 mm |
| PASS | htd5m_60t_coupon_tight_v0_1: six actual paired-arc groove stations | main-arc faces=12, transition-arc faces=12 |
| PASS | htd5m_60t_coupon_tight_v0_1: sensible A1 bounding box | 9.491 x 29.155 x 16.200 mm |
| PASS | htd5m_60t_coupon_standard_v0_1: one valid solid | solids=1, valid=True |
| PASS | htd5m_60t_coupon_standard_v0_1: face width | actual=16.200000 mm, expected=16.200000 mm |
| PASS | htd5m_60t_coupon_standard_v0_1: curved paired-arc groove | R1'=1.538, R2'=0.588, depth=2.152 mm |
| PASS | htd5m_60t_coupon_standard_v0_1: six actual paired-arc groove stations | main-arc faces=12, transition-arc faces=12 |
| PASS | htd5m_60t_coupon_standard_v0_1: sensible A1 bounding box | 9.491 x 29.155 x 16.200 mm |
| PASS | htd5m_60t_coupon_loose_v0_1: one valid solid | solids=1, valid=True |
| PASS | htd5m_60t_coupon_loose_v0_1: face width | actual=16.200000 mm, expected=16.200000 mm |
| PASS | htd5m_60t_coupon_loose_v0_1: curved paired-arc groove | R1'=1.588, R2'=0.638, depth=2.202 mm |
| PASS | htd5m_60t_coupon_loose_v0_1: six actual paired-arc groove stations | main-arc faces=12, transition-arc faces=12 |
| PASS | htd5m_60t_coupon_loose_v0_1: sensible A1 bounding box | 9.491 x 29.155 x 16.200 mm |
| PASS | 20T: clearance changes contact geometry | tight=2314.129941 mm^3, standard=2287.036844 mm^3, loose=2259.536330 mm^3 |
| PASS | 20T: clearance does not change pitch stations | clearances=0.05, 0.10, 0.15 mm |
| PASS | 60T: clearance changes contact geometry | tight=2843.966142 mm^3, standard=2813.678633 mm^3, loose=2782.882153 mm^3 |
| PASS | 60T: clearance does not change pitch stations | clearances=0.05, 0.10, 0.15 mm |
| PASS | htd5m_bore_gauge_6mm_v0_1.step: present and nonempty | bytes=2597543 |
| PASS | htd5m_bore_gauge_6mm_v0_1.step: readable geometry | roundtrip solids=1, valid=True |
| PASS | htd5m_bore_gauge_6mm_v0_1.stl: present and nonempty | bytes=2222984 |
| PASS | htd5m_bore_gauge_6mm_v0_1.stl: readable geometry | points=22221, triangles=44458 |
| PASS | htd5m_bore_gauge_10mm_v0_1.step: present and nonempty | bytes=3061427 |
| PASS | htd5m_bore_gauge_10mm_v0_1.step: readable geometry | roundtrip solids=1, valid=True |
| PASS | htd5m_bore_gauge_10mm_v0_1.stl: present and nonempty | bytes=2277884 |
| PASS | htd5m_bore_gauge_10mm_v0_1.stl: readable geometry | points=22768, triangles=45556 |
| PASS | htd5m_20t_coupon_tight_v0_1.step: present and nonempty | bytes=467517 |
| PASS | htd5m_20t_coupon_tight_v0_1.step: readable geometry | roundtrip solids=1, valid=True |
| PASS | htd5m_20t_coupon_tight_v0_1.stl: present and nonempty | bytes=315584 |
| PASS | htd5m_20t_coupon_tight_v0_1.stl: readable geometry | points=3157, triangles=6310 |
| PASS | htd5m_20t_coupon_standard_v0_1.step: present and nonempty | bytes=625877 |
| PASS | htd5m_20t_coupon_standard_v0_1.step: readable geometry | roundtrip solids=1, valid=True |
| PASS | htd5m_20t_coupon_standard_v0_1.stl: present and nonempty | bytes=447084 |
| PASS | htd5m_20t_coupon_standard_v0_1.stl: readable geometry | points=4472, triangles=8940 |
| PASS | htd5m_20t_coupon_loose_v0_1.step: present and nonempty | bytes=459510 |
| PASS | htd5m_20t_coupon_loose_v0_1.step: readable geometry | roundtrip solids=1, valid=True |
| PASS | htd5m_20t_coupon_loose_v0_1.stl: present and nonempty | bytes=312784 |
| PASS | htd5m_20t_coupon_loose_v0_1.stl: readable geometry | points=3129, triangles=6254 |
| PASS | htd5m_60t_coupon_tight_v0_1.step: present and nonempty | bytes=514475 |
| PASS | htd5m_60t_coupon_tight_v0_1.step: readable geometry | roundtrip solids=1, valid=True |
| PASS | htd5m_60t_coupon_tight_v0_1.stl: present and nonempty | bytes=385584 |
| PASS | htd5m_60t_coupon_tight_v0_1.stl: readable geometry | points=3857, triangles=7710 |
| PASS | htd5m_60t_coupon_standard_v0_1.step: present and nonempty | bytes=675104 |
| PASS | htd5m_60t_coupon_standard_v0_1.step: readable geometry | roundtrip solids=1, valid=True |
| PASS | htd5m_60t_coupon_standard_v0_1.stl: present and nonempty | bytes=512284 |
| PASS | htd5m_60t_coupon_standard_v0_1.stl: readable geometry | points=5124, triangles=10244 |
| PASS | htd5m_60t_coupon_loose_v0_1.step: present and nonempty | bytes=506435 |
| PASS | htd5m_60t_coupon_loose_v0_1.step: readable geometry | roundtrip solids=1, valid=True |
| PASS | htd5m_60t_coupon_loose_v0_1.stl: present and nonempty | bytes=380384 |
| PASS | htd5m_60t_coupon_loose_v0_1.stl: readable geometry | points=3805, triangles=7606 |
| PASS | htd5m_bore_gauges_plate_v0_1.step: optional disconnected plate | bytes=5631762, disconnected solids=2, bbox=184.900 x 28.000 x 10.000 mm |
| PASS | htd5m_tooth_coupons_plate_v0_1.step: optional disconnected plate | bytes=3340876, disconnected solids=6, bbox=100.729 x 29.155 x 16.200 mm |
| PASS | htd5m_calibration_all_plate_v0_1.step: optional disconnected plate | bytes=9109441, disconnected solids=8, bbox=222.382 x 65.156 x 16.200 mm |
| PASS | No complete pulley export | none |
