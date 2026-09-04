# DESIGN SPECIFICATION

## 1. Design intent

雨滴の入力を`rain drop -> TPU deformation -> distributed PETG load`として伝え、裸PETGの高周波clickを低減する。自然雨、稲、虫、風、水、rover/mechanical field soundを意図的に遮断しない。完全防音は要求しない。

## 2. Authority

- Upstream: `cad/ps_webcam_rainhood_v004_b15_position_retention/`
- Optical variant: `B_setback15`
- Final setback: 15.0 mm
- Final front Y: -45.4 mm
- Bevel: 40.0 deg
- Bevel run: 2.080 mm
- Front length: 15.0 mm
- Latest physical observation: カメラ本体を意図的に捻ってもフードの映り込みは確認されなかった。

v005はtripod datum、carrier seating plane、tripod axis、USB route、carrier M4 interface、B15 optical geometry、sidewall optical envelope、rainhood-camera clearanceを変更しない。

## 3. Selected storm-skin geometry

| Parameter | Value |
|---|---:|
| Main TPU thickness | 1.5 mm |
| Acoustic alternatives | 1.0 / 1.5 / 2.0 mm |
| X preload | 0.5% parameterized |
| Y preload | 0.5% parameterized |
| Preload coupon | 0 / 0.5 / 1.0% |
| Side skirt | 9.0 mm |
| Rear skirt | 9.0 mm |
| External nose wrap | 1.0 mm down |
| Anchor count | 4 |
| Anchor stations Y | -26.0 / +24.0 mm, left and right |
| TPU tab local thickness | 2.5 mm |
| T-head width | 12.0 mm |
| Root/neck width | 10.0 mm |
| Root fillet | R2.0 mm |
| PETG cavity clearance | 0.4 mm nominal |
| Neck lateral clearance | 0.2 mm per side |

flat-print skinはroof、左右flap、rear flap、front nose flap、4個のlocal reinforced T-headを一体化した閉solidです。平置きで大量supportを要求しません。取付時にflapを曲げ、TPUの弾性で上面へ張ります。

## 4. Attachment trade study

### Option A — existing M4 capture

金属締結で長期保持しやすい一方、v004の利用可能点が後方2点だけです。front peelを止めるには前方から長いstrapを引き回す必要があり、carrier serviceとUSB route付近の作業空間を悪化させます。不採用です。

### Option B — dogbone/T-head in PETG sidewall cage

左右前後4点を独立配置でき、屋根穴なし、部品点数追加なし、下側から着脱可能です。幅12 mm head、最小10 mm root/neck、局所厚2.5 mm、R2 rootでTPU tear starterを避け、外付けcageでsidewallの広い領域へ荷重を伝えます。採用です。

### Option C — removable PETG retainer

保持調整は容易ですが、retainerと締結部品が増え、硬い露出面と脱落部品を増やします。couponでOption Bが不合格の場合のfallbackです。

Selected attachment: `TPU_DOGBONE_T_HEAD_IN_EXTERNAL_PETG_SIDEWALL_CAGE`。

## 5. Retention functions

- Elastic preload: X/Yとも初期0.5%。全/ほぼ全面接触とflutter抑制。
- Mechanical side retention: 左右前後の4 cage。接着剤がなくても飛散防止。
- Leading-edge peel prevention: 前端外面へ1.0 mm wrap。自由端へ風を入りにくくする。

`PRIMARY_RETENTION_BY_ADHESIVE = FORBIDDEN`。将来の非永久tack layerは補助だけであり、機械保持を置換しない。

## 6. PETG controlled delta

v004 hoodへ外付けsidewall cageだけを加算する。上面や内部へ穴を開けない。元のv004 hood除去体積は0.000000 mm3、加算されたPETG anchor geometryは1795.641 mm3。cageは薄い単独earではなく、top capと両側shoulderをsidewallへ連続させる。

v001 printed clamp failure Authority (`FAIL_BOLT_REACH=TRUE`, `FAIL_PRINT_ROBUSTNESS=TRUE`, static load未試験)を継承し、細いPETG耳を再利用しない。

## 7. Optical and service safeguards

- TPU vs optical exclusion: 0.0 mm3
- TPU vs camera: 0.0 mm3
- TPU vs carrier: 0.0 mm3
- TPU vs USB route: 0.0 mm3
- TPU nose margin above B optical interior: 2.0 mm
- Front wrapは外面だけ。camera-side interiorへ折り込まない。
- rear skirtはUSB routeから離し、rear cornersへ8 mm reliefを残す。

current rainhoodのfront edgeにある約1 mm未満のminor spaghetti defectは構造品質accepted、光学operation pass、field installation proceededである。nose wrapはこの局所欠陥へ点荷重を掛けず、面接触と側壁anchorへ保持を分配する。

## 8. Contact and drainage

Target: `FULL_OR_NEAR_FULL_CONTACT`。undersideへ大きなrib/bossや意図的なair gapを設けない。rear skirtは中央を閉鎖せず、両rear corner reliefから水と空気が抜ける。閉鎖pocket、上向きgutterは設けない。

installed STEPのroof間には、接触ブーリアンの数値不安定性を除く0.10 mm clearanceがある。これは組立参照表現だけであり、印刷用flat skin STLの予圧寸法ではない。

## 9. Material authority

- Material: TPU
- Shore: `UNKNOWN_PHYSICAL`
- Geometry assumption: approximately 95A, not material Authority
- Printer: Bambu Lab A1
- Nozzle: 0.4 mm

TPU銘柄、乾燥、line width、temperature、layer bondingによる保持差はCAD PASSに含めない。couponの破壊モードをAuthorityとする。

## 10. Acceptance separation

`CAD_PASS`はgeometry/mesh/STEP/interfaceだけを意味する。以下は独立したPhysical PASSが必要:

- `TPU_ANCHOR_PHYSICAL_PASS`
- `TPU_RAIN_NOISE_REDUCTION_PHYSICAL_PASS`
- `TPU_STORM_SKIN_BENCH_RETENTION_PASS`
- field wind
- wind-driven rain
- trapped-water behavior
- long-duration acoustic behavior
- UV/weather aging
