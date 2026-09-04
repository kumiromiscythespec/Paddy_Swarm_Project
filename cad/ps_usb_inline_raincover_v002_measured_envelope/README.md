# USB接続部防滴カバー v002 — MEASURED CONNECTOR ENVELOPE

Status: `CAD_COMPLETE_MEASURED_ENVELOPE_PHYSICAL_VALIDATION_PENDING`

`ps_usb_inline_raincover_v001` のCAD検証済み防滴architectureを維持し、仮寸法だったconnector chamberとcable envelopeを実測Authorityへ置換した独立laneです。v001は参照専用で変更していません。本設計は `SPLASH_RESISTANT_NOT_WATERPROOF` であり、防水・通電・豪雨耐性をCAD結果から主張しません。

## Physical Authority

- connector envelope: 95.1 × 18.7 × 10.8 mm
- chamber: 102 × 24 × 16 mm
- camera cable: Ø3.8 mm
- extension cable: Ø4.0 mm
- common cable channel: Ø4.4 mm（v001 physical couponで両cable PASS）
- Authority priority: physical measurement → physical coupon result → v001 validated geometry → CAD nominal → provisional assumption

v001の50 mm chamberは `REJECTED_UNDERSIZED` ですがCAD failureではなく、`PROVISIONAL_DIMENSION_SUPERSEDED_BY_PHYSICAL_MEASUREMENT` です。v001の7.9 mm cable authorityは実測値に置換し、9.0 mm channelはv002 full geometryで使用しません。

## First print

最初に印刷するものは [connector_chamber_fit_coupon_v002.stl](stl/connector_chamber_fit_coupon_v002.stl) です。connector fit、両cable transition、upper/lower datumを確認後、[labyrinth_drain_coupon_v002.stl](stl/labyrinth_drain_coupon_v002.stl) を着色水で試験します。4.4 mm channelの再探索couponは印刷しません。

Full shellを本番試験へ進めるgateは、connector chamber fit、両cable transition、shell datum fit、labyrinth drain、witness bay dryの全PASSです。

## Physical status

| Gate | Status |
|---|---|
| CABLE_CHANNEL_PHYSICAL | PASS |
| CONNECTOR_DIMENSION_PHYSICAL | PASS_MEASURED |
| CHAMBER_PHYSICAL | PENDING |
| LABYRINTH_DRAIN_PHYSICAL | PENDING |
| FULL_SHELL_RAIN | PENDING |
| LIVE_USB_RAIN | PENDING |

詳細は `DESIGN_SPEC.md`、試験記録は `docs/PHYSICAL_TEST_PROTOCOL.md`、CAD検証値は `reports/VALIDATION_REPORT.md` を参照してください。
