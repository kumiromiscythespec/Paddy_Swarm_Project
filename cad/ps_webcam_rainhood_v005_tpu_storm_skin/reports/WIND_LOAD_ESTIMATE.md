# WIND LOAD ESTIMATE

Status: `ENGINEERING_ESTIMATE_ONLY`

This is not a certified wind rating. Projected areas are conservative CAD bounding-projection envelopes. Cd is uncertain; gust, edge suction, local peel, turbulence, installation tolerance, and material aging are not resolved.

## Projected areas

- `plan_xy_m2`: 0.011242 m^2
- `front_xz_m2`: 0.001508 m^2
- `side_yz_m2`: 0.001120 m^2

## Dynamic pressure and force range

| Wind | q | Direction | Cd 0.8 | Cd 1.4 |
|---:|---:|---|---:|---:|
| 10 m s | 61.2 Pa | uplift_plan | 0.55 N | 0.96 N |
| 10 m s | 61.2 Pa | front | 0.07 N | 0.13 N |
| 10 m s | 61.2 Pa | side | 0.05 N | 0.10 N |
| 20 m s | 245.0 Pa | uplift_plan | 2.20 N | 3.86 N |
| 20 m s | 245.0 Pa | front | 0.30 N | 0.52 N |
| 20 m s | 245.0 Pa | side | 0.22 N | 0.38 N |
| 30 m s | 551.2 Pa | uplift_plan | 4.96 N | 8.68 N |
| 30 m s | 551.2 Pa | front | 0.66 N | 1.16 N |
| 30 m s | 551.2 Pa | side | 0.49 N | 0.86 N |

Bench targets remain independent: front peel >=10 N and distributed uplift >=20 N for 60 s. Passing those targets does not certify a wind speed.
