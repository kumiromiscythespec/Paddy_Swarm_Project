# P5M28 exact-vendor core fit coupons — v0.9.6.34

This independent untracked lane converts the exact AP203 external tooth section from ordered MISUMI `PTPK28P5M150-A-N10-NFC` into three fit-only PETG coupons. No P5M tooth approximation and no XYZ scaling is used.

The source assembly contains five solids. The unique largest solid is the main pulley body; two 50 mm thin solids are separate flange candidates in CAD, and two small solids remain unnamed accessory solids. Only the main-body external envelope drives the pocket. Flanges and accessory solids are excluded.

| Coupon | radial-equivalent clearance mm | permanent notches | minimum wall mm | estimated PETG g | gate |
|---|---:|---:|---:|---:|---|
| C1 | +0.15 | 1 | 6.20 | 23.34 | CAD PASS / print approved |
| C2 | +0.25 | 2 | 6.10 | 23.04 | CAD PASS / print approved |
| C3 | +0.35 | 3 | 6.00 | 22.75 | CAD PASS / print approved |

First print: `p5m28_fit_coupon_C1_015_notch1.stl`, `p5m28_fit_coupon_C2_025_notch2.stl`, and `p5m28_fit_coupon_C3_035_notch3.stl`, one each, same PETG settings and orientation. Axis vertical, flat stop face down; place no support on a mating surface. Slicer has not been run, so slicer-specific state remains `PHYSICAL_USER_HOLD`.

Winner rule after the part arrives: select the smallest clearance allowing hand insertion and removal without hammer/press, whitening, crack, or clear play. No winner is selected in CAD.

`FULL_DRIVE_PRINT_HOLD`, `STATIC_TORQUE_HOLD`, and `POWERED_NOT_APPROVED` remain active.
