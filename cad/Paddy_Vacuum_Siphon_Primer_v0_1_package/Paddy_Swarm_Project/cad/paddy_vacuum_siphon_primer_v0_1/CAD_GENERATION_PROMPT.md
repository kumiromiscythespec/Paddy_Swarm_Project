# CAD生成プロンプト

以下を、CadQuery 2.8.0 を使用して実装してください。

## 目的

`Paddy Vacuum Siphon Primer v0.1` の3Dプリント部品を、Bambu Lab A1の造形範囲内でパラメトリックCAD化する。
対象は、PETG製水分離タンク、TPU 95A製交換式蛇腹、上下板、押さえリング、支持部品、校正試験片である。

## リポジトリ

- ルート: `D:\Paddy_Swarm_Project`
- 新規配置: `cad\paddy_vacuum_siphon_primer_v0_1\`
- 派生成果物: `cad\paddy_vacuum_siphon_primer_v0_1\exports\stl\` および `exports\step\`
- 公開用STLコピー先: `stl\paddy_vacuum_siphon_primer_v0_1\`

## 重要ルール

1. 既存ファイルを変更しない。新規フォルダだけを作成する。
2. 寸法は `parameters.py` に集約し、各部品ファイルへ直書きしない。
3. すべての部品に `build()` を実装する。
4. `build_all.py` でSTEPとSTLを一括生成する。
5. STLだけを正本にせず、Pythonソースを設計正本とする。
6. 完全真空、高圧、飲用水、無人運転に使えると表現しない。
7. `DESIGN_STATUS=PROTOTYPE_ONLY`、`MANUFACTURING_RELEASE=False`、`FIELD_DEPLOYMENT_STATUS=NOT_APPROVED` を維持する。
8. 購入部品未確定の穴は、校正試験片で決定するまで製造確定しない。
9. FDM積層面を主要気密シールとして信用しない。市販Oリングまたはシリコン平パッキンを使う。
10. 逆止弁本体は市販品とし、3Dプリントは固定ブラケットだけにする。

## CAD v0.1での設計補正

元仕様から以下を補正して実装する。

- TPU蛇腹フランジ外径: 188mm → **200mm**
- 蛇腹M4ボルト円: 174mm → **188mm**
- 理由: M4穴と蛇腹最大外径172mmの間に必要な肉厚を確保するため
- 水分離タンク側面ポートを廃止し、入口・出口・真空計ポートを上蓋へ集約する
- 入口は上蓋から内径12mmのディップチューブを下部へ伸ばす
- 理由: タンク側壁の横穴による積層割れと空気漏れを減らすため
- タンク底ドレンは購入継手確定まで貫通穴にせず、中心パイロットマークのみとする

## 部品

### 水分離タンク

- `PVSP-WT-001 tank_body`
  - PETG
  - 内径90mm、壁5mm、内高150mm、底6mm
  - 上部フランジ外径126mm、厚さ10mm
  - M4穴8個、PCD112mm
  - 縦補強リブ8本
- `PVSP-WT-002 tank_lid`
  - PETG、外径126mm、厚さ8mm
  - M4穴8個、PCD112mm
  - G1/2相当校正前穴22mmを2個
  - 真空計仮穴12mmを1個
  - 上面放射リブ8本
- `PVSP-WT-003 baffle`
  - PETG、幅60mm、高さ75mm、厚さ3mm
- `PVSP-WT-004 tank_stand`
  - PETG、140×140mm、排水逃げ穴35mm
- `PVSP-WT-005 sight_tube_guard`
- `PVSP-WT-006 dip_tube`
  - 外径16mm、内径12mm、長さ108mm

### 足踏み蛇腹

- `PVSP-BL-001 bellows_tpu`
  - TPU 95A
  - 最大外径172mm、最小外径142mm
  - 自由高さ132mm、7山
  - 基本壁1.6mm、谷部2.0mm
  - フランジ外径200mm、厚さ3.2mm
  - M4穴8個、PCD188mm
  - 波形は鋭いV字を避け、滑らかな周期曲線で近似する
- `PVSP-BL-002 fixed_base`
  - PETG、230×230×10mm
  - 吸排気穴22mm×2
- `PVSP-BL-003 foot_plate`
  - PETG、230×230×10mm
- `PVSP-BL-004 clamp_ring`
  - PETG、外径200mm、内径176mm、厚さ6mm
- `PVSP-BL-006 guide_bushing`
- `PVSP-BL-007 spring_anchor`
- `PVSP-BL-008 stroke_stop`
- `PVSP-BL-009 foot_pad_tpu`

### アダプターと校正部品

- `PVSP-AD-001 hose_support`
- `PVSP-AD-002 check_valve_bracket`
- `PVSP-CAL-001 bulkhead_hole_coupon`
  - 21.6 / 21.8 / 22.0 / 22.2mm
- `PVSP-CAL-002 gasket_compression_coupon`
- `PVSP-CAL-003 bellows_wall_coupon`
  - 壁厚1.4 / 1.6 / 1.8mmを比較する

## 検証

- 全Pythonファイルを `python -m compileall` で構文検査する
- `python build_all.py` を実行する
- 各STEP/STLが生成されたことを確認する
- 各ソリッドが空でないこと、寸法範囲内であることを確認する
- タンク蓋と本体のボルト穴位置が一致することを確認する
- 蛇腹、上下板、押さえリングの穴位置が一致することを確認する
- 部品同士が貫通・干渉していないことを確認する
- 校正部品を本体より先に印刷する手順をREADMEへ記載する

## 出力報告

最後に以下を報告する。

1. 作成ファイル一覧
2. 使用した主要寸法
3. 元仕様からの補正内容
4. 構文検査結果
5. STEP/STL生成結果
6. 未検証事項
7. 印刷前に購入・実測すべき市販部品
8. `MANUFACTURING_RELEASE` と `FIELD_DEPLOYMENT_STATUS` が false / NOT_APPROVED のままであること
