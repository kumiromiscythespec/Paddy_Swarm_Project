# DESIGN SPECIFICATION

## 1. Scope

雨、豪雨候補、斜め雨、cable-tracked water、水滴、軽いbottom splashから屋外USB中間接続部を防滴する。水没、高圧洗浄、完全IP保証、長時間水中使用は対象外。設計思想はsealingではなく`labyrinth + gravity + drainage`である。

## 2. Authority hierarchy

1. Actual physical measurement
2. Successful physical coupon
3. CAD nominal
4. Provisional assumption

Measured: connector max W 18.7 mm、small cable OD 3.6 mm、large cable OD 7.9 mm。

Unknown: connector length/height/detail、rigid-flexible boundary、strain-relief length。未知値はCADで確定しない。

## 3. Provisional envelope

| Parameter | Value | Authority |
|---|---:|---|
| Chamber inner L | 50.0 mm | provisional |
| Chamber inner W | 24.0 mm | provisional; 18.7 mm known widthに対しtotal 5.3 mm clearance |
| Chamber minimum H | 16.0 mm | provisional |
| Wall | 3.0 mm | CAD nominal |
| Main flange | 4.0 mm | CAD nominal |

Connectorをshellで圧縮しない。既知幅の片側nominal clearanceは2.65 mmだが、length/height合格はfit couponまで宣言しない。

## 4. Shell architecture

`PART A = upper_shell`、`PART B = lower_shell`。overall lower envelopeは76 x 30 mm、upper umbrella envelopeは82.6 x 36.6 mm。upper roofは最低3 mm厚で、長手に3°の勾配を持つ。upper skirtはparting planeより6 mm下へ降り、lower外周とのnominal gapは0.30 mm。

Lower chamber floorは中央を0.873 mm高くし、左右endへ2°で落とす。下面は突出物のない平面print datumとし、側壁の3本凹markでDOWNを示す。

## 5. Parting-line labyrinth

単純な平面突き合わせではない。lowerの2 mm tongueがupperのclearance grooveへ入り、skirtの下端からchamberまでに外周overlap、direction change、3 mm nominal overlapを作る。selected clearanceは0.30 mm。M3 flange reliefはtongue/grooveより外側に限定される。

## 6. Cable labyrinth

Smallは4.6 mm、largeは9.0 mm。各cableはconnector chamberからterminal baffleの低い通路を横切り、10 mm drip vestibule内で方向を変え、下向きportから外へ出る。狭いsharp 90° ductで強制曲げせず、開いたvestibule内にR4以上のbend spaceを与える。

Cable support saddleは実cableより直径0.8 mm大きく、位置決めだけを行う。hard clampとconnector compressionは禁止。

## 7. Drainage architecture

- Drip pocket bottom: z = -0.75 mm
- Drain: 2.5 mm x2
- Chamber floor: 2°、center crown 0.873 mm
- Weep: baffle下部、drainとはY方向にoffset
- Drain axis: connector chamberの外、baffle-isolated vestibule内

中央床へ入ったtrace waterは両endへ流れ、low weepを通ってlower drip pocketへ落ち、offset drainから下へ出る。closed low pocketやupward-facing gutterを意図的に作らない。

## 8. Closure

Selected: `M3_X4_SIDE_FLANGE_WITH_CAPTURED_HEX_NUTS`。x = +/-18 mm、y = +/-22 mm。3.4 mm clearance hole、5.8 mm AF nut trap、2.5 mm depth。screw holesはupper roof projectionより外にあり、connector chamberへ直通しない。snap-onlyは採用しない。nutは過度なpress fitにせず、coupon/printで保持を確認する。

## 9. Failure-mode controls

| Mode | Geometry control | Remaining proof |
|---|---|---|
| TOP RAIN | sloped roof、6 mm umbrella skirt | staged top spray |
| SIDE RAIN | skirt + offset tongue/groove | 45°/side spray |
| WIND-DRIVEN RAIN | terminal baffles、downward dogleg | field test |
| CABLE-TRACKED WATER | local downward port、drip vestibule | cable-water test |
| BOTTOM SPLASH | drain axes end outside chamber behind baffles | bottom splash test |
| WATER POOLING | 2° two-way floor、low weeps、2 drains | 5 min drain inspection |
| CAPILLARY ENTRY | 3 mm overlap、long offset path | multi-hour test |

## 10. FDM constraints

Functional wall >=3.0 mm、stress corners R1.5–R4相当、flat lower print datum、internal support禁止を基本とする。upperはroofをbridgeにしないside orientationを採用する。closed STLはprinted waterproof evidenceではない。

## 11. Future TPU interface

Cable vestibulesとreplaceable port regionには将来のTPU slit bushingを検討できる空間がある。v001ではTPUを必須とせず、追加する場合もdrainを塞ぐ完全sealにしない。

## 12. Status boundary

`CAD_PASS`はBRep/STL/STEPとnominal dimension/path checksのみ。fit、drain、spray、live operation、heavy rain、capillary、mud、UV/weatherはPhysical Authority未確定。

