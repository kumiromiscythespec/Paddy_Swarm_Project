# ACOUSTIC TEST PROTOCOL

Status: `TPU_RAIN_NOISE_REDUCTION_PHYSICAL_PASS = PENDING`

## Objective

低減対象は`PETG_ROOF_IMPACT_CLICK`。残す対象はrice-field ambient、insects、wind、natural rainfall、water、rover/mechanical field sound。完全無音や自然雨音の除去を目的にしない。

## Samples

- bare PETG reference: 同じPETG材、壁厚、支持状態のscrap。利用できなければ現行hoodの安全な上面をreferenceにする。
- `stl/tpu_acoustic_coupon_1p0.stl`
- `stl/tpu_acoustic_coupon_1p5.stl`
- `stl/tpu_acoustic_coupon_2p0.stl`

TPU各couponは同じ主面積を持つ。ID tab/holeは滴下領域の外に置く。TPU Shore、銘柄、乾燥状態、print settingsを記録する。

## Controlled setup

1. 静かな室内または風の弱い同一場所で、camera/microphone、gain、codec、距離、角度を固定する。auto gainを無効化できない場合は各sample前に同じambientを30秒入れる。
2. PETG referenceをfield hoodと近い支持条件にする。foam tableへ直接置いて結果を過度に良くしない。
3. TPUはPETGへfull/near-full contactで重ね、粘着剤は使わない。気泡、皺、水膜を除く。
4. 同じdropper/nozzle、同じ高さ、同じ水量、同じ位置で試す。推奨初期条件は一定高さから単滴10回、次に一定流量30秒。実測高さと滴数を記録する。
5. bare PETG、1.0、1.5、2.0の順をrandomizeまたは2巡目で逆順にし、background変化を見分ける。
6. sample間にPETGを乾燥させる。残水をdamping layerにしない。

## Required record

```text
DATE / LOCATION:
MIC / CAMERA:
GAIN / CODEC:
DROP HEIGHT:
DROP COUNT / FLOW:
PETG SAMPLE:
TPU FILAMENT / LOT:
TPU SHORE MARKING (if known):
PRINT SETTINGS:

SAMPLE: BARE PETG / TPU 1.0 / TPU 1.5 / TPU 2.0
HIGH-FREQUENCY CLICK: HIGH / MEDIUM / LOW / NONE
LOW-FREQUENCY THUMP: HIGH / MEDIUM / LOW / NONE
NATURAL AMBIENT SOUND: NORMAL / REDUCED
TPU FLUTTER: NONE / YES
COMMENTS:
```

可能なら同じaudio segmentへfile nameとtime rangeを付け、peak levelだけでなくspectrogramの高周波transientも比較する。ただし測定器がない場合はblind listeningを優先し、最低2人または同じ人の別日に再評価する。

## Minimum acoustic PASS

- bare PETGと比べ人工的な高周波clickが明瞭に低減する。
- low-frequency thumpが新たな主要騒音にならない。
- ambient reproductionが実用上`NORMAL`である。
- fitted skinのflutterが`NONE`である。

1.5 mmでclick低減不足なら2.0 mmを検討する。1.5 mmで十分なら重量/柔軟性を増やさず維持する。1.0 mmが同等に有効でも、anchor/耐候/creep評価を別に行う。

## Full-hood confirmation

coupon PASSだけでは最終音響PASSにしない。full skin装着後、light rainまたは再現滴下で以下を確認する。

```text
PETG ARTIFICIAL CLICK: CLEARLY REDUCED / NOT REDUCED
NATURAL RAIN: PRESENT / UNNATURALLY REDUCED
AMBIENT: NORMAL / REDUCED
FLUTTER / SLAP: NONE / YES
WATER-FILM SOUND: ACCEPTABLE / PROBLEM
```

heavy rain、wind-driven rain、長時間の含水/汚れ、UV aging後の音は独立してPENDINGとする。

