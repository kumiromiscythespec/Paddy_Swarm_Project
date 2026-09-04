# WIND RETENTION RATIONALE

Status: `ENGINEERING_RATIONALE_ONLY / PHYSICAL_VALIDATION_PENDING`

## Load model

CAD bounding projectionからplan 0.011242 m2、front 0.001508 m2、side 0.001120 m2を得た。空気密度1.225 kg/m3、`q = 0.5 rho V^2`、Cd 0.8–1.4を用いる。Cd、gust、turbulence、edge suction、local peel、installation variation、agingを解いていないため認証風速ではない。

30 m/s、Cd 1.4のbounding estimateはplan uplift 8.68 N、front 1.16 N、side 0.86 N。bench target 10 N front peelと20 N/60 s distributed upliftはmarginを意図したscreening loadだが、これを30 m/s ratingとは呼ばない。

## Failure-mode controls

| Failure mode | Initiation | Geometry mitigation | Required evidence |
|---|---|---|---|
| UPLIFT | roof上面の負圧 | near-full contact、0.5% X/Y preload、4 anchors | 20 N/60 s distributed bench |
| FRONT-EDGE PEEL | front edge下への流入 | free flat edgeなし、1 mm external nose wrap、front pair anchors | 10 N front peel、field observation |
| SIDE PEEL | crosswindがskirtを持上げ | 9 mm side skirt、左右各2 cage、10 mm neck capture | side-direction coupon test |
| FLUTTER | loose membrane / air gap | roofより小さいflat pattern、full/near-full contact、大ribなし | preload coupon、hand airflow、field audio |
| ANCHOR TEAR | neck/rootの応力集中 | 2.5 mm local thickness、12 mm head、10 mm root/neck、R2 root | destructive/repeat coupon |
| ANCHOR DISENGAGEMENT | T-headがshoulderを抜ける | 12 mm head対10.4 mm slot、0.4 mm depth clearance、bottom service opening | 10/20 N tests、5 install cycles |
| PETG SIDEWALL DAMAGE | cage rootへの集中荷重 | roof holeなし、top cap + two shoulders、wide sidewall load path、4点分散 | coupon fracture inspection、full bench |

## Why no floating secondary roof

浮かせた膜はedgeから風を取り込み、slap、flutter、uplift、water intrusion、共鳴を増やす。今回の音源はPETGへの衝撃clickなので、薄いTPUを面接触させ入力を時間/面積方向へ分散する方を第一案とした。

## Why no roof fastener

roof penetrationは水侵入経路、硬いacoustic point、局所応力を追加する。今回の4 cagesは側壁外側だけに置き、v004 roof/optical interiorを切らない。

## Why the existing M4 is not selected

既存M4は後方2点に限定される。front peel防止を成立させる長いTPU ear/strapはcarrier serviceとUSB周辺の作業性を悪化させ、membraneの局所張力差も増やす。M4位置やcarrier interfaceを変えるより、左右前後4点の外付けsidewall cageをcontrolled deltaとして加算する方が要求に合う。

## Retention hierarchy

1. 予圧が通常時の接触とflutterを制御する。
2. front wrapが風の初期侵入を抑える。
3. 4 T-headが予圧や補助tackを失っても飛散を防ぐ。
4. 接着剤はprimary load pathに含めない。

## Interpretation boundary

- CAD PASSは風荷重PASSではない。
- Coupon PASSはfull skin PASSではない。
- Bench PASSはfield wind PASSではない。
- 観察されたfield conditionのPASSは未観察stormの認証ではない。
- UV、water、温度、creep後は保持を再試験する。
