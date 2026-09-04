# PHYSICAL TEST PROTOCOL

Status: `PHYSICAL_VALIDATION_PENDING`

## Safety and test order

最初のfit、drain、spray試験はUSB connector、camera、PC、電源を入れずに行う。着色水は低圧で少量から始める。高圧jet、水没、屋内mains機器の近くでの散水は禁止する。

Mandatory order:

1. small/large cable channel coupons
2. connector chamber fit coupon
3. labyrinth drain coupon
4. dry fit + colored-water validation
5. coupon gate合格後にfull shells
6. full dry fit
7. top rain
8. 45-degree rain
9. side spray
10. cable-tracking water
11. bottom splash
12. dry physical tests合格後だけcontrolled live USB test
13. field rain / long-durationは独立判定

## A. Cable channel coupons

Print:

- `stl/cable_channel_coupon_small_v001.stl`: 4.4 / 4.6 / 4.8 mm
- `stl/cable_channel_coupon_large_v001.stl`: 8.8 / 9.0 / 9.2 mm

各groove横のedge notch 1/2/3本が昇順候補。実cableを押し潰さず置き、5回着脱する。

```text
FILAMENT / LOT:
SLICER PROFILE:
CABLE MEASURED OD:
CHANNEL CANDIDATE:
INSERTION: EASY / ACCEPTABLE / TIGHT / FAIL
FREE SLIDE: YES / NO
VISIBLE COMPRESSION: NONE / YES
JACKET MARK: NONE / YES
SELECTED CHANNEL:
RESULT: PASS / FAIL / HOLD
```

PASSはfree placement、visible compressionなし、jacket damageなし。cableを摩擦で固定する候補を選ばない。CAD本命はsmall 4.6、large 9.0 mm。

## B. Connector chamber fit coupon

`stl/connector_chamber_fit_coupon_v001.stl`はupper/lowerの2 bodiesをprint layoutに配置している。supportを除去し、tongue/grooveへ糸引きやelephant footがないことを確認して組み合わせる。

```text
CONNECTOR FIT

connector maximum width:
18.7 mm

actual body length:
actual body height:
rigid/flexible boundary notes:

insertion:
PASS / FAIL

side clearance:
GOOD / TIGHT / LOOSE

height clearance:
GOOD / TIGHT / LOOSE

small cable:
PASS / FAIL

large cable:
PASS / FAIL

connector compression:
NONE / YES

shell closes:
YES / NO

parting tongue fully seats:
YES / NO

RESULT:
PASS / FAIL / HOLD
```

長さ・高さを実測して`DIMENSIONAL_AUTHORITY.md`へ反映するまで、50 x 24 x 16 mmはprovisionalのまま扱う。connector compression、cable pinch、jointへの曲げ荷重があればFAIL。

## C. Labyrinth/drain coupon

`stl/labyrinth_drain_coupon_v001.stl`へsmall-sideのbaffle、downward port、offset weep、drip pocket、2.5 mm drainが含まれる。drainを真下にし、inner witness bayへ白いdry tissueを置く。

1. downward cable port側から1–3 mLずつ着色水を入れる。
2. drainから出る時間と量を確認する。
3. inner witness bayのtissueを確認する。
4. 5分後にpoolingを確認する。
5. couponを傾けず、次に取付許容誤差として+/-5°で繰り返す。

```text
DRAIN TEST

small side:
drain exits water:
YES / NO

water reaches chamber:
NONE / TRACE / YES

large side:
drain exits water:
YES / NO

water reaches chamber:
NONE / TRACE / YES

pooling after 5 min:
NONE / YES

drain blockage / stringing:
NONE / YES

RESULT:
PASS / FAIL / HOLD
```

Large側はfull lower shellまたは同断面を用いて確認する。TRACEが再現する場合はPASSにしない。

## D. Full shell dry fit

1. lowerへconnected cableを置き、connector jointが50 x 24 x 16 mm chamber内に自由状態で入ることを確認。
2. cableを両vestibuleからdownward portsへ、R4未満のsharp bendなしで導く。
3. upperを真上から合わせ、tongue/grooveを均等にseatさせる。
4. M3 x4を対角順に軽く締める。PETG flangeを曲げるtorqueは禁止。
5. cover両側でcableを軽く動かし、jointへ直接力が入らないことを確認。

```text
SHELL CLOSED: YES / NO
PARTING GAP: UNIFORM / LOCATION
CABLE PINCH: NONE / YES
CONNECTOR COMPRESSION: NONE / YES
STRAIN RELIEF SUPPORT: LIGHT / HARD / NONE
DRAINS FACE DOWN: YES / NO
DOWN MARK ORIENTATION: CORRECT / WRONG
SUSPENDED ABOVE GROUND: YES / NO
```

## E. Staged spray test — connector absent first

各段階は別判定。試験後に外面を拭いてからshellを開き、chamber tissueとpocketsを確認する。下位PASSから上位PASSを推測しない。

1. TOP RAIN: 上方から低圧mist/滴下を5分。
2. 45 DEG RAIN: 四方向から45°、各2分。
3. SIDE SPRAY: parting lineとflangesへ低圧で各2分。
4. CABLE-TRACKING WATER: cover外側cableへ20–30 mLをゆっくり流す。
5. BOTTOM SPLASH: 下方から少量の飛沫。drainへjetを当てない。

```text
TEST STAGE:
WATER ON CONNECTOR WITNESS AREA: NONE / TRACE / YES
DRAIN FLOW: YES / NO
DRIP POCKET WATER: NONE / DRAINED / POOLED
PARTING-LINE INGRESS: NONE / LOCATION
POOLING AFTER 5 MIN: NONE / YES
SHELL REMAINED CLOSED: YES / NO
RESULT: PASS / FAIL / HOLD
```

## F. Controlled electrical live test

全dry physical tests PASS後だけ行う。可能ならbattery動作PCを乾燥側に置き、AC adapter/mains接続を散水範囲から外す。最初はmist、次にtop rainの順とし、異常、映像停止、USB再接続、visible waterで直ちに停止・乾燥する。

Operational PASS:

```text
camera stream uninterrupted
USB reconnect not required
no visible water on connector
no pooled water in chamber
drain functioning
shell remains closed
```

## G. Status separation

```text
CAD_PASS: PASS
PRINT_PASS: PENDING
FIT_PASS: PENDING
DRAIN_PASS: PENDING
TOP_RAIN_PASS: PENDING
45_DEG_RAIN_PASS: PENDING
CABLE_WATER_PASS: PENDING
HEAVY_RAIN_FIELD_PASS: PENDING
LONG_DURATION_PASS: PENDING
```

Heavy rain、wind-driven rain、hours-long capillary ingress、mud、UV/weather agingは別試験で記録する。

