# Crawler H1 Track Module — Pretest Candidate v0.1

## 目的

このlaneは、別々に設計された以下の最終試験候補STLを、試験前段階の設計軌跡として1つにまとめたものです。

- 駆動スプロケット
- アイドラスプロケット
- 支持ローラー
- PETGリンク
- TPU LUG

統合時に形状変更や再生成は行っていません。アップロードされた `cad.zip` 内の選定STLをbyte-identicalで収録しています。

## 選定した試験候補

| 役割 | 材料 | 上流版 | STL |
|---|---|---|---|
| Drive sprocket | PETG | v0.13.1 | `DRIVE_SPROCKET_V0131_INTEGRATED_B10_3_PCD24_M4.stl` |
| Idler sprocket | PETG | v0.13.1 | `IDLER_SPROCKET_V0131_INTEGRATED_6000_SEAT_B.stl` |
| Support roller | PETG | v0.13.1 / v0.13.0 | `SUPPORT_ROLLER_W44_OD50_6000_VERIFIED.stl` |
| Track link | PETG | v0.12.5 | `STANDARD_V0125_WIDE_46_LINK.stl` |
| Ground LUG | TPU 95A | v0.11.4 | `PS-TRH1-LUG-0114-STANDARD.stl` |

## 設計軌跡

1. **v0.11.4** — TPU LUGの保持高さとφ3 mm軸挿入性を対象にした候補。
2. **v0.12.5** — 3ナックル支持幅を46 mmへ拡大したPETGリンク候補。
3. **v0.13.0** — 40リンク、20 mmピッチ、280 mm軸間距離候補、12 mmテンションストローク、6000-2RSローラー候補を統合。
4. **v0.13.1** — スプロケット歯根のゼロ体積接触を修正し、歯と本体を1シェルへ統合。

## このlaneで確定しないもの

- Powered engagement
- 接地面積の最終幅
- スプロケットとリンクの噛み合い調整
- 支持ローラー位置
- クローラー全高
- テンション最終値
- 荷重、泥、水、耐久性
- 40+8個の量産
- 実機搭載承認

これらは実験結果から次revisionで更新します。

## 物理品番刻印

この統合ではSTLを変更していないため、物理的な固有品番刻印は未検証です。
Paddy Swarmの固定ルール上、印刷解禁前に各STLの物理刻印を確認し、不足する場合は新revisionとして再出力します。

## バイト同一性

上流 `cad.zip` SHA-256:

`c515421ce9f8f486cff53cd2eb1f161eedccb32842b78359a9d1caf92ae9ecd8`

個別STLのSHA-256は `manifest/candidate_parts.csv` と `manifest/SHA256SUMS.txt` に記録しています。

## Status

```text
PRETEST_HISTORY_PACKAGE = PASS
GEOMETRY_MODIFIED_DURING_CONSOLIDATION = NO
STATIC_MESH_AUDIT = PASS
POWERED_ENGAGEMENT = NOT_VALIDATED
LOAD_TEST = NOT_VALIDATED
MUD_WATER_TEST = NOT_VALIDATED
TRACK_HEIGHT = NOT_FIXED
BATCH_PRINT = HOLD
PRINT_RELEASE = HOLD_PENDING_MARKING_AND_USER_REVIEW
MANUFACTURING_STATUS = NOT_APPROVED
FIELD_DEPLOYMENT_STATUS = NOT_APPROVED
```
