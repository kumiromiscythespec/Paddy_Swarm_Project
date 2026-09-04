# Paddy Vacuum Siphon Primer v0.1 CAD

足踏み蛇腹式・真空呼び水サイフォンポンプの3Dプリント部品です。

## 状態

- `PROTOTYPE_ONLY`
- 製造リリース: HOLD
- 圃場投入: NOT APPROVED
- 完全真空・正圧・飲料水用途には使用しない

## 生成環境

- Python 3.11系を想定
- CadQuery 2.8.0
- Bambu Lab A1の256mm角造形範囲内

## 生成方法

```powershell
cd D:\Paddy_Swarm_Project\cad\paddy_vacuum_siphon_primer_v0_1
python -m pip install -r requirements.txt
python -m compileall .
python build_all.py
```

## 最初に印刷する部品

1. `PVSP-CAL-001_bulkhead_hole_coupon`
2. `PVSP-CAL-002_gasket_compression_coupon`
3. `PVSP-CAL-003_bellows_wall_coupon`
4. 校正結果を `parameters.py` へ反映
5. 水分離タンク
6. 蛇腹
7. 上下板・支持部品

## 重要な設計補正

- 蛇腹フランジを外径200mm、PCD188mmへ拡大した
- タンクの配管穴を上蓋へ集約した
- 入口は内部ディップチューブでタンク下部へ導く
- 底ドレンは市販部品確定までパイロットマークのみ

詳細は `DESIGN_DEVIATIONS.md` を参照してください。

## 生成済みプレビューSTL

この配布ZIPには、CadQueryを実行できない環境で形状確認用に生成したプレビューSTLも含まれます。
これらは寸法検討・画面確認用であり、製造正本ではありません。
製造前にはユーザー環境のCadQuery 2.8.0で `build_all.py` を実行し、再生成してください。
