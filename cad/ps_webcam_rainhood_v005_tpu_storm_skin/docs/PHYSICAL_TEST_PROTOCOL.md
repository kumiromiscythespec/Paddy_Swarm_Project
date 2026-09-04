# PHYSICAL TEST PROTOCOL

Status: `PHYSICAL_VALIDATION_PENDING`

## Safety and preparation

- カメラ、USB cable、carrier electronicsを外した状態で荷重試験を行う。
- 吊り荷をcamera、clip、USB、pipe mountへ掛けない。PETG hoodを独立した堅いfixtureへ固定する。
- 落下範囲へ手、足、機材を置かず、bottleは二重袋または落下防止cordを使う。
- 水1 Lを約1 kg、約10 Nとして扱う。家庭用bottle法は概算であり校正試験ではない。
- 亀裂、白化、層間剥離、鋭いedgeを発見した試験片はfull testへ進めない。

## Mandatory order and gates

1. anchor couponを印刷する。
2. anchor pull/peel testを行う。
3. preload 0/0.5/1.0%を選定する。
4. TPU acoustic thickness 1.0/1.5/2.0 mmを比較する。
5. 1–4合格後だけfull TPU storm skinを印刷する。
6. hoodへfitする。
7. cameraを一時装着しoptical previewを確認後、荷重試験前に再び外す。
8. static front peel / uplift testを行う。
9. outdoor windを低リスク条件から観察する。
10. rainを観察する。
11. wind-driven rainを独立して観察する。

Gateを飛ばしてfull skinを最初に印刷しない。

## A. Anchor coupon

Print:

- `stl/storm_skin_anchor_coupon_v005_petg.stl`
- `stl/storm_skin_anchor_coupon_v005_tpu.stl`

同じPETG wall/cage厚、2.5 mm TPU tab、12 mm T-head、10 mm root/neck、R2 root、0.4 mm depth clearance、片側0.2 mm lateral clearanceを代表する。TPU tabを下開口から挿入し、neckをslotへ通す。

Record before load:

```text
FILAMENT / LOT:
TPU SHORE MARKING (if known):
SLICER PROFILE:
ASSEMBLY BY HAND: EASY / ACCEPTABLE / TOO TIGHT / TOO LOOSE
FREE PLAY: NONE / SMALL / LARGE
TAB SURFACE DAMAGE: NONE / YES
PETG CAGE DAMAGE: NONE / YES
```

### Coupon pull and peel

1. PETG couponのwall sectionをviseへsoft jawで固定する。cage自体を潰さない。
2. TPU neckへ幅広いsoft loopを掛け、T-headを切らないよう面で荷重する。
3. cage開口から抜く方向、side peel方向、T-head shoulderへ掛かる方向を別々に試す。
4. 1 L bottleをゆっくり持ち上げ、10秒保持する。衝撃荷重を掛けない。
5. 除荷後、T-head root、neck、PETG cage、sidewall junctionを拡大観察する。

Coupon gate PASS:

```text
NO DISENGAGEMENT
NO PERMANENT TEAR
NO PETG CRACK / LAYER SPLIT
NO LARGE PERMANENT SET
REPEATABLE REMOVE / INSTALL >= 5 cycles
```

不合格ならfull skinを印刷しない。tearならtab厚/幅/filletを増す。抜けならshoulder engagementまたはclearanceを修正する。PETG破損ならcage load pathを広げる。

## B. Preload selection

Print `stl/tpu_preload_strap_coupon_v005.stl`。3本は0.0%、0.5%、1.0%の長さをgeometry markで区別する。

各strapを同じ基準間隔へ最低5回装着し、次を記録する。

```text
PRELOAD: 0.0 / 0.5 / 1.0 %
ASSEMBLY FORCE: LOW / MEDIUM / HIGH
LOOSENESS: NONE / YES
FLUTTER BY HAND AIRFLOW: NONE / YES
WHITE STRESS MARK: NONE / YES
PERMANENT SET AFTER 10 MIN: NONE / SMALL / LARGE
```

選定基準はloose edgeなし、容易に装着可能、stress markなし、永久伸びなし。初期CAD候補は0.5% X/Yだが、実物結果を優先する。

## C. Full fit check

Couponとacoustic comparison合格後に`stl/rainhood_tpu_storm_skin_v005.stl`を印刷する。4個のT-headを対角順にcageへ装着し、front nose wrap、side skirts、rear skirtを整える。工具でTPUを刺さない。

```text
FULL CONTACT: YES / NO
LOOSE EDGE: NONE / LOCATION
FRONT EDGE PEEL: NONE / YES
SIDE PEEL: NONE / YES
FLUTTER BY HAND AIRFLOW: NONE / YES
DRAINAGE BLOCKED: NO / YES
USB INTERFERENCE: NONE / YES
CAMERA FOV INTRUSION: NONE / YES
REAR CORNER EXIT OPEN: YES / NO
```

FOVは通常姿勢に加えて、v004で確認した意図的camera twist相当でもpreviewする。intrusionが1 pixelでも疑われる場合はv005 FAILとし、TPU geometryを後退させる。

## D. Front peel >= 10 N

1. cameraとUSBを取り外す。
2. hoodをfixtureへ固定し、pipe clampやcarrierに荷重を流さない。
3. front noseの中央へ、edgeを切らない幅広loopを掛ける。風が下へ入り剥がす方向へゆっくり引く。
4. 水1 L入りbottle（約1 kg、約10 N）をゆっくり支持し、10秒保持する。
5. 除荷後、4 anchors、front wrap、PETG sidewallを確認する。

PASS: load中のdisengagementなし、永久tearなし、anchor pulloutなし、PETG fractureなし、永久的大変形なし。

## E. Distributed uplift >= 20 N / 60 s

1. cameraとUSBを取り外す。
2. skin上面へ軟らかい幅広slingまたは軽い板を置き、少なくとも4点へ荷重を分配する。細い紐1本でTPUを切らない。
3. slingを上方へ引くfixtureを使い、水2 L（約2 kg、約20 N）を静かに負荷する。装置を横倒しにしてbottleを吊る方式でも、荷重方向と固定が明確ならよい。
4. 20 N相当を60秒保持する。人が手で保持しない。
5. 除荷後、T-head root、cages、sidewall、front/rear edgesを確認する。

PASS:

```text
NO DISENGAGEMENT
NO PERMANENT TEAR
NO ANCHOR PULLOUT
NO PETG FRACTURE
NO PERMANENT LARGE DEFORMATION
```

このPASSは風速保証ではない。

## F. Drainage and water-trap check

水平からfield取付姿勢まで複数角度でroofへ100–200 mLをゆっくり注ぐ。rear corner exitsから排出し、10分後に大きなpoolが残らないことを確認する。TPUを外して裏面の閉じ込め水、mud line、capillary retentionを確認する。

```text
DRAINAGE EXIT: CLEAR / BLOCKED
VISIBLE POOL AFTER 10 MIN: NONE / YES
TRAPPED WATER AFTER REMOVAL: NONE / TRACE / SIGNIFICANT
```

## G. Outdoor observation

bench PASS後だけ実施する。初回は人や道路へ落下しない位置でsecondary tetherを使い、低風から開始する。

```text
FIELD WIND: PENDING / PASS FOR OBSERVED CONDITION / FAIL
OBSERVED WIND CONDITION:
FLUTTER: NONE / YES
EDGE LIFT: NONE / LOCATION
ANCHOR MOVEMENT: NONE / YES
RAIN: PENDING / OBSERVED
WIND-DRIVEN RAIN: PENDING / OBSERVED
WATER TRAP: NONE / YES
```

特定日の観察PASSを認証風速へ変換しない。strong wind、wind-driven rain、長期UV/weather、長期音響挙動は個別に未確認のまま残す。
