# ps_webcam_rainhood_v005_tpu_storm_skin

Status: `CAD_COMPLETE_TPU_STORM_SKIN_PHYSICAL_VALIDATION_PENDING`

Paddy Swarm屋外Webカメラ用rainhood v004 B15を変更せずに継承し、PETG屋根へ交換可能なTPU storm skinと、その機械保持用PETG側壁アンカーを追加するlaneです。目的は自然の雨音や環境音を消すことではなく、PETGへ雨滴が直接当たる高周波の人工的なクリック音を低減することです。

## 重要な判定

- CAD検証: PASS
- TPUアンカー実物保持: PENDING
- 雨音低減効果: PENDING
- full skinベンチ保持: PENDING
- 屋外風、吹込み雨、UV/耐候: PENDING
- 認証風速: なし

TPU storm skinは接着剤だけでは保持せず、機械保持を持つ設計です。

最初に印刷するものはfull storm skinではなくanchor retention couponです。

## 採用構成

`1.5 mm TPU near-full-contact skin + 0.5% X/Y preload + 9 mm side/rear skirts + 4 external sidewall dogbone/T-head captures + 1 mm external nose wrap`

TPUとPETGの間に意図的な空気層を設けません。前端の自由な平板edgeも設けません。TPUの各T-headは、左右側壁の前後に追加した外付けPETG cageへ下側から装着します。12 mm headと最小10 mm root/neckを持ち、接着がなくても4点で飛散を防ぎます。屋根上面への穴はありません。

既存M4は金属保持として検討しましたが、利用可能なのが後方2点で、前端剥離を止めるための長いTPU strapが整備性とUSB周辺を妨げるため不採用です。v004 carrier M4 interface自体は変更していません。

## 印刷・試験順序

1. `stl/storm_skin_anchor_coupon_v005_petg.stl`
2. `stl/storm_skin_anchor_coupon_v005_tpu.stl`
3. anchor pull/peel test
4. `stl/tpu_preload_strap_coupon_v005.stl`による0/0.5/1.0%比較
5. `stl/tpu_acoustic_coupon_1p0.stl`、`1p5`、`2p0`の雨滴比較
6. coupon合格後だけ`stl/rainhood_tpu_storm_skin_v005.stl`
7. full fit、光学preview、10 N front peel、20 N/60 s uplift
8. 屋外風、雨、吹込み雨をそれぞれ独立判定

詳細は`docs/PHYSICAL_TEST_PROTOCOL.md`と`docs/ACOUSTIC_TEST_PROTOCOL.md`を参照してください。

## 印刷方位の初期案

- PETG anchor coupon: 最大の平面をbedへ置き、cageの開口を横向きにする。無理なbridgeが出る場合だけ通常supportを使用。
- TPU anchor coupon: 2.5 mm tabの広い面をbedへ平置き。TPU supportは使用しない。
- TPU preload/acoustic coupons: 平置き、supportなし。
- TPU full skin: 展開状態の大面をbedへ平置き、supportなし。装着時にskirtとtabを弾性変形させる。
- PETG anchor hood: v004と同じ印刷判断を継承し、側壁cageの開口と積層方向を確認する。full hoodより先にcouponを破壊試験する。

TPU Shore硬度は`UNKNOWN_PHYSICAL`です。geometryは約95A級を仮定しましたが材料Authorityではありません。Bambu Lab A1、0.4 mm nozzleを想定します。実フィラメントとスライサ設定に合わせ、couponから決定してください。

## CAD再生成

CadQuery 2.8.0環境でlane rootから実行します。

```powershell
& 'C:\Users\yu_ki\Miniforge\envs\paddy-cadquery-280-py312\python.exe' cad\ps_webcam_rainhood_v005.py
```

生成器はSTL、STEP、parameters、レンダー、validation、wind estimate、SHA256 manifestを再生成し、検証失敗時は終了コード1を返します。

## Authorityと非変更項目

Authorityは`cad/ps_webcam_rainhood_v004_b15_position_retention/`です。B15 front Y -45.4 mm、setback 15.0 mm、bevel 40 deg、bevel run 2.080 mm、front length 15.0 mm、tripod datum、carrier seating plane、M4 interface、USB route、camera clearanceは変更していません。PETG変更は外側側壁cageの加算だけで、v004 hoodからの除去体積は0.0 mm3です。

取付状態STEPでは接触面のブーリアン誤検出を避けるため0.10 mmの数値クリアランスを置きます。印刷用flat STLは0.5%予圧寸法を保持し、この数値隙間を付加していません。

## 成果物の読み方

- `cad/parameters.json`: 寸法Authority、material hold、bench targets
- `DESIGN_SPEC.md`: geometryとinterface delta
- `reports/VALIDATION_REPORT.md`: BRep/STL/STEP/干渉検証
- `reports/WIND_LOAD_ESTIMATE.md`: dynamic-pressure概算。認証値ではない
- `reports/ACOUSTIC_RAIN_NOISE_RECORD.md`: 既知観察と未試験欄
- `reports/DIMENSIONAL_AUTHORITY.md`: v004継承値とv005 controlled delta
- `SHA256SUMS.txt`: lane内成果物のハッシュ
