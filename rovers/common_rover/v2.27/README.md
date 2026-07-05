# Paddy Swarm Common Rover v2.27

## 日本語

### 概要

このフォルダは、Paddy Swarm Project / 田んぼロボット群プロジェクト向けの **Common Rover v2.27** 印刷・組み立て用データです。

v2.27は、実田んぼ投入機ではなく、以下を確認するための **低負荷3Dプリント模型 / 試作検証機** です。

- 足回りの組み立て確認
- ギアボックス内部模型の確認
- TPU一体タイヤの取り付け確認
- BBOX / CBOX の前後配置確認
- PTOと緊急停止ボタンの干渉確認
- フロート装備時の浮力・姿勢確認
- 15cm水深を想定した水槽・たらい試験
- 部品干渉、組み立て順、修正点の発見

このデータは、完成品・実用品・防水保証品ではありません。

---

### 重要な安全注意

このv2.27は、**組み立て確認・浮力確認・干渉確認用の低負荷3Dプリント模型**です。

以下を必ず守ってください。

- 電子部品を搭載した状態で水試験をしないでください。
- 実田んぼに投入しないでください。
- 3Dプリント防水BOXを、そのまま実用防水筐体として扱わないでください。
- 水試験では、バッテリー・基板・モーターを入れず、重りで重量だけを再現してください。
- 15cm水深試験では、フロート装備を必須としてください。
- PTO、モーター駆動、バッテリー、防水、充電系、非常停止系は実地検証済みではありません。
- 緊急停止ボタンは、PTOユニット装着時でも必ず押せる位置にしてください。
- フロートは標準装備として扱いますが、実際に浮くかどうかは水槽試験で確認してください。

---

### v2.27の重要設計方針

#### 1. BBOX / CBOX は前後方向に配置する

BBOX-BDY と CBOX-BDY は、車体の左右方向に並べてはいけません。

正しい配置:

```text
前方 FRONT
  BBOX-BDY  電源 / バッテリー系
  CBOX-BDY  制御 / 通信系
後方 REAR
```

禁止配置:

```text
BBOX-BDY + CBOX-BDY を左右横並び
```

横並びにすると、30cm条間の幅制限を超える可能性が高くなります。

---

#### 2. タイヤは別体ゴムタイヤ前提ではない

v2.27の以下の部品は、TPUで印刷する **一体タイヤ / 接地ホイール模型** です。

```text
PS-RV227-WHL-FL
PS-RV227-WHL-FR
PS-RV227-WHL-RL
PS-RV227-WHL-RR
```

市販ゴムタイヤを別途履かせる設計ではありません。

将来的に市販ゴムタイヤ仕様にする場合は、別バージョンとして、ホイールリム・タイヤ内径・外径・ビード形状を再設計してください。

---

#### 3. フロートは標準装備

15cm水深 + 泥への沈み込みを想定すると、タイヤと防水BOXだけでは水没リスクがあります。

v2.27では、以下のフロート関連部品を標準装備として扱います。

```text
PS-RV227-FLT-L
PS-RV227-FLT-R
PS-RV227-HULL-SKID
PS-RV227-FLT-BRACKET-S
PS-RV227-FLT-RCV-L
PS-RV227-FLT-RCV-R
PS-RV227-FLT-RCV-FR-S
PS-RV227-FLT-STRAP-S
```

ただし、3Dプリント品は積層隙間やピンホールから浸水する可能性があります。

水試験では、必要に応じて以下を併用してください。

- 発泡材
- 密閉PETボトル
- EVA / 発泡ブロック
- 防水塗装
- エポキシ封止
- ウレタンコート
- シリコンシール

---

#### 4. PTOと緊急停止ボタンは分離する

v2.27では、PTO接続部と緊急停止ボタンの干渉を避けるため、以下の方針にしています。

- PTOは前面下側の接続部に配置
- 緊急停止ボタン / 操作パネルは高置き
- `PS-RV227-RCP-BRKT` により、操作パネルをPTOから離す
- PTOユニットを装着した状態でも、緊急停止ボタンを押せることを必須条件とする

---

### 推奨印刷セット

このフォルダには、複数の印刷セットが含まれる場合があります。

低負荷の稼動模型として印刷する場合:

```text
dense_rigid_plus_metal
dense_tpu_only
```

実物の金属軸を用意する場合:

```text
dense_rigid_only
dense_tpu_only
```

注意:

```text
dense_rigid_plus_metal と dense_rigid_only を両方印刷しないでください。
部品が重複します。
```

---

### 材料と印刷量の目安

撮影されたスライサー表示を元にした概算では、v2.27一式は以下の規模です。

```text
PETG/PLA:
  約 84h22m
  約 2781.91g

TPU:
  約 21h05m
  約 302.32g

合計:
  約 105h27m
  約 3084.23g
```

実際の印刷時間と材料量は、プリンター、ノズル径、積層ピッチ、インフィル、サポート設定、フィラメント種類によって変わります。

---

### 組み立て前の確認

印刷前・組み立て前に、必ず以下を確認してください。

```text
1. BBOX/CBOXが前後方向に配置されているか
2. 横並びBOX配置になっていないか
3. WHL系がTPU一体タイヤとして扱われているか
4. フロート部品が印刷対象に含まれているか
5. RCP-G1操作パネルがPTOと干渉しない位置にあるか
6. PTOユニット装着時でも緊急停止ボタンを押せるか
7. フロートとタイヤが干渉しないか
8. ギアボックス内部模型の向きが左右で合っているか
9. 配線穴・上部ノッチが水面に近づきすぎないか
10. 水試験では電子部品を外しているか
```

---

### 水槽・たらい浮力試験の推奨手順

最初の水試験では、電子部品を搭載しないでください。

推奨手順:

```text
1. LOWER-FRAME、タイヤ、フロート、HULL-SKIDを組む
2. BBOX/CBOXを載せる
3. 電子部品の代わりに重りを入れる
4. 15cm水深のたらい・浴槽・水槽に入れる
5. 静止時の水線を確認する
6. 前後に傾ける
7. 左右に傾ける
8. 軽く揺らす
9. 配線穴・フタ・BOX底面に水が近づくか確認する
10. 浮力不足ならフロート・発泡材・前後浮力体を追加する
```

合格目安:

```text
- BOX底面が水面に近づきすぎない
- 上部配線穴 / ノッチに水が届かない
- 前後どちらかだけ大きく沈まない
- 左右に傾けても復元する
- フロートがタイヤの回転を邪魔しない
- 回収しやすい
```

---

### 画像・説明図について

このフォルダに含まれる組み立て説明画像は、視覚的な補助資料です。

正式な部品名・寸法・印刷対象は、以下を正としてください。

```text
STL
STEP
print_manifest
plate_manifest
design_contract
CadQuery source
```

画像内の一部ラベルや形状は、模式図・簡略表記を含む場合があります。

---

### 既知の注意点

- 一部の自動生成CSVやレポートファイル名に、古い `v2_25` 表記が残っている場合があります。
- 部品番号が `PS-RV227-...` になっているものをv2.27部品として扱ってください。
- GitHub公開時は、README内でこの注意点を明記してください。
- 実機投入前には、必ず新しい設計レビューを行ってください。

---

### 推奨フォルダ構成

例:

```text
rover_v227/
  README.md
  rover_v227_out/
  rover_v227_dense_v5_7_model/
  docs/
  images/
  src/
```

可能であれば、以下も追加してください。

```text
src/
  paddy_swarm_common_rover_v2_27_cadquery.py
  paddy_swarm_a1_dense_project_tools_v5_7.py

docs/
  SAFETY.md
  PRINTING.md
  ASSEMBLY.md
  FLOAT_TEST.md
  CHANGELOG.md
```

---

### ライセンス・利用条件

現時点では試作・検証用データです。

公開ライセンスを設定する場合は、別途 `LICENSE` ファイルを追加してください。

ライセンス未設定のまま公開する場合、第三者が自由に再利用できるとは限らないため、GitHub上ではライセンス方針を明記してください。

---

### プロジェクトについて

Paddy Swarm Project は、家族経営・小規模稲作農家が高額な大型農機に依存しすぎず、壊れても直せる小型ロボット群を段階的に開発するためのプロジェクトです。

最初から万能ロボットを作るのではなく、まずは以下を目指します。

```text
田んぼで生き残る
水に沈まない
泥で詰まりにくい
人間が回収できる
壊れても修理できる
少しずつ作業を補助する
```

---

# Paddy Swarm Common Rover v2.27

## English

### Overview

This folder contains print and assembly data for **Paddy Swarm Common Rover v2.27**.

v2.27 is **not a field-ready rice paddy robot**.  
It is a **low-load 3D printed mockup / prototype test platform** for checking the following:

- Undercarriage assembly
- Gearbox internal mockup
- TPU integrated wheel/tire installation
- Front/rear BBOX and CBOX placement
- PTO and emergency-stop clearance
- Float module installation
- Buoyancy and posture in a 15 cm water-depth mockup test
- Interference, assembly order, and design issues

This data is not a finished product, not a waterproof guarantee, and not a field-deployable machine.

---

### Important safety notice

This v2.27 design is a low-load printed mockup for assembly, buoyancy, and fit-check testing.

Please follow these rules:

- Do not perform water tests with electronics installed.
- Do not deploy this model in a real rice field.
- Do not treat 3D printed waterproof boxes as field-ready waterproof enclosures.
- For water tests, remove batteries, boards, and motors. Use dummy weights instead.
- Float modules are mandatory for 15 cm water-depth tests.
- PTO, motor drive, battery, waterproofing, charging, and emergency-stop systems are not field-validated.
- The emergency-stop button must remain reachable even when a PTO unit is attached.
- Float modules are treated as standard equipment, but actual buoyancy must be verified by tank testing.

---

### Key v2.27 design rules

#### 1. BBOX and CBOX must be placed front-to-rear

BBOX-BDY and CBOX-BDY must not be placed side by side.

Correct layout:

```text
FRONT
  BBOX-BDY  power / battery system
  CBOX-BDY  control / communication system
REAR
```

Prohibited layout:

```text
BBOX-BDY + CBOX-BDY side by side
```

Side-by-side placement can exceed the 30 cm rice-row spacing width limit.

---

#### 2. The wheels are not designed for separate rubber tires

The following v2.27 parts are **TPU printed integrated wheel/tire mockups**:

```text
PS-RV227-WHL-FL
PS-RV227-WHL-FR
PS-RV227-WHL-RL
PS-RV227-WHL-RR
```

They are not designed to accept separate commercial rubber tires.

If commercial rubber tires are used in a future version, the wheel rim, tire inner diameter, tire outer diameter, bead geometry, and mounting method should be redesigned as a separate version.

---

#### 3. Float modules are standard equipment

Assuming 15 cm water depth plus mud sink-in, wheels and waterproof boxes alone may not provide enough freeboard.

In v2.27, the following float-related parts are treated as standard equipment:

```text
PS-RV227-FLT-L
PS-RV227-FLT-R
PS-RV227-HULL-SKID
PS-RV227-FLT-BRACKET-S
PS-RV227-FLT-RCV-L
PS-RV227-FLT-RCV-R
PS-RV227-FLT-RCV-FR-S
PS-RV227-FLT-STRAP-S
```

However, 3D printed floats may leak through layer gaps or pinholes.

For water testing, use additional sealing or buoyancy aids as needed:

- Closed-cell foam
- Sealed PET bottles
- EVA foam blocks
- Waterproof coating
- Epoxy sealing
- Urethane coating
- Silicone sealant

---

#### 4. PTO and emergency-stop must be separated

In v2.27, the PTO connection and emergency-stop button are separated.

Design intent:

- PTO remains on the lower front attachment face.
- The emergency-stop / control panel is mounted higher.
- `PS-RV227-RCP-BRKT` separates the control panel from the PTO area.
- The emergency-stop button must remain accessible even when a PTO-driven unit is installed.

---

### Recommended print sets

This folder may contain multiple dense print sets.

For the low-load moving mockup:

```text
dense_rigid_plus_metal
dense_tpu_only
```

If you are using real metal rods instead of printed rod surrogates:

```text
dense_rigid_only
dense_tpu_only
```

Important:

```text
Do not print both dense_rigid_plus_metal and dense_rigid_only.
They contain overlapping parts.
```

---

### Estimated print time and filament usage

Based on slicer screenshots, the approximate v2.27 print scale is:

```text
PETG/PLA:
  about 84h22m
  about 2781.91 g

TPU:
  about 21h05m
  about 302.32 g

Total:
  about 105h27m
  about 3084.23 g
```

Actual print time and filament usage depend on printer, nozzle size, layer height, infill, support settings, and filament type.

---

### Pre-assembly checklist

Before printing or assembly, check the following:

```text
1. BBOX and CBOX are placed front-to-rear.
2. The boxes are not placed side by side.
3. WHL parts are treated as TPU integrated wheel/tire parts.
4. Float parts are included in the print target.
5. The RCP-G1 control panel does not interfere with the PTO.
6. The emergency-stop button remains reachable with the PTO unit attached.
7. Float modules do not interfere with wheel rotation.
8. Left/right gearbox internal mockups are oriented correctly.
9. Upper wire-drop notches do not approach the waterline.
10. All electronics are removed before water testing.
```

---

### Recommended buoyancy test procedure

Do not install electronics for the first water test.

Recommended steps:

```text
1. Assemble LOWER-FRAME, wheels, float modules, and HULL-SKID.
2. Install BBOX and CBOX.
3. Add dummy weights instead of electronics.
4. Place the rover in a tub, bath, or tank with 15 cm water depth.
5. Check the waterline at rest.
6. Tilt it forward and backward.
7. Tilt it left and right.
8. Gently shake it.
9. Check whether water approaches the wire notches, lids, or box bottoms.
10. If buoyancy is insufficient, add float volume, foam, or front/rear buoyancy modules.
```

Pass criteria:

```text
- Box bottoms stay safely above the waterline.
- Upper wire notches do not contact water.
- Front or rear does not sink excessively.
- The rover self-recovers from small left/right tilts.
- Float modules do not block wheel rotation.
- The rover can be recovered easily.
```

---

### Assembly images and diagrams

Assembly images included in this folder are visual guides only.

The following files are the source of truth for official part names, dimensions, and print targets:

```text
STL
STEP
print_manifest
plate_manifest
design_contract
CadQuery source
```

Some labels or shapes in generated diagrams may be simplified or schematic.

---

### Known notes

- Some auto-generated CSV or report filenames may still contain an older `v2_25` suffix.
- Parts with `PS-RV227-...` part numbers should be treated as v2.27 parts.
- Please mention this clearly when publishing the folder on GitHub.
- A new design review is required before any real field deployment.

---

### Suggested folder structure

Example:

```text
rover_v227/
  README.md
  rover_v227_out/
  rover_v227_dense_v5_7_model/
  docs/
  images/
  src/
```

If possible, also include:

```text
src/
  paddy_swarm_common_rover_v2_27_cadquery.py
  paddy_swarm_a1_dense_project_tools_v5_7.py

docs/
  SAFETY.md
  PRINTING.md
  ASSEMBLY.md
  FLOAT_TEST.md
  CHANGELOG.md
```

---

### License and usage

At this stage, this is prototype and test data.

If you want to publish it under an open-source license, please add a separate `LICENSE` file.

If no license is provided, third parties may not have permission to freely reuse the data. Please state the license policy clearly on GitHub.

---

### About the project

Paddy Swarm Project aims to develop small, repairable robot swarms for small-scale and family rice farming.

The goal is not to immediately replace large agricultural machines.  
The first goal is to reduce heavy manual work step by step with low-cost, repairable, and modular robot systems.

The first milestone is not a universal rice-field robot.  
The first milestone is a rover that can:

```text
survive in a rice field
avoid sinking
avoid clogging with mud
be recovered by humans
be repaired after failure
assist work step by step
```