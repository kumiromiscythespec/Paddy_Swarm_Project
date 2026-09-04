# USB接続部防滴カバー v003 — SIDE-LOAD LABYRINTH

Status: `CAD_COMPLETE_SIDE_LOAD_LABYRINTH_PHYSICAL_VALIDATION_PENDING`

v002 measured-envelope laneをAuthorityとして維持し、Physical Testで判明したassembly-path failureだけを修正した独立laneです。v001/v002は変更していません。

## Physical disposition

- connector chamber 102 × 24 × 16 mm: `PASS`
- camera/extension cable OD: Ø3.8 / Ø4.0 mm
- 4.4 mm channel physical fit: `PASS`
- v002 labyrinth assembly path: `FAIL_END_THREADING_REQUIRED`
- connector removal: impossible / cable cutting: forbidden

4.4 mm径は変更していません。v003 lowerはlabyrinth全長が上向きに開いたU-channel、upperは下向きに開いた補完coverです。continuous cableをlowerへ上/横から置いた後にupperを閉じて、4.4 mm nominal passageを完成させます。どちらの単品にもclosed cable ringはありません。

外端ではcableが6 mm skirt下で下向きになり、8 mm lateral dogleg、split cap、lower drip vestibule、offset weep、Ø2.5 mm drain×2で水路を制御します。本品は `SPLASH_RESISTANT_NOT_WATERPROOF` です。

## NEXT_PRINT

最初に印刷するものは次のcoupon pairのみです。

- `stl/split_labyrinth_side_load_coupon_lower_v003.stl`
- `stl/split_labyrinth_side_load_coupon_upper_v003.stl`

connector chamber couponとcable diameter couponは再印刷しません。side-load、no pinch、no threading、drain、witness DRYが全PASSするまでfull shellを本番化しません。
