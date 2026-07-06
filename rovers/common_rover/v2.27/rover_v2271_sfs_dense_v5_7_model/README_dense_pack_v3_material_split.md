# Paddy Swarm A1 Dense Pack v5.7 Output

Group mode: `plate_group`
TPU split: `False`
TPU patterns: `TIR, TIRE, TYRE, TPU, RUBBER`

## Files

- `3mf_dense_pack_rigid/*.3mf`
  - PLA / PETG / ABSなど硬質部品用
- `3mf_dense_pack_tpu/*.3mf`
  - TPUタイヤ/ゴム系部品用
- `plate_placement_dense_material.csv`
  - 各部品の配置座標
- `print_project_manifest_dense_material.csv`
  - 印刷/スライス/組み立て進捗管理用
- `support_orientation_report.csv`
  - サポート発生を抑えるために自動選択した向き、元寸法、新寸法、ベッド接触面積の記録


## v5.4 plate grid note

Bambu Studio A1 template projects were observed to arrange plates in a 4-column grid.
Therefore v5.4 defaults `--bambu-template-plate-columns` and `--bambu-plate-columns` to 4.
If your local template uses a different grid, override these options explicitly.

## Recommended workflow

1. Print rigid plates first.
2. Change filament/profile to TPU.
3. Print TPU tire plates separately.
4. Use STL files for repair/replacement parts.

## Important

`all_plates_single_scene_reference_material_split.3mf` がある場合、それはBambu Studioの本物の複数プレートタブではありません。  
全プレートを1つの3Dシーンに横並びで入れた参照用です。

`*_bambu_multiplate_project.3mf` がある場合、それはv4.3のBambu Studio複数プレートproject 3MFです。v4.3標準では `bambu-absolute-grid` 方式で、Bambu/Orca系で観測される約303mm間隔・2列のplateグリッド座標に各plateの部品を配置します。A1に入らない大型部品や市販品参照ダミーは標準でprojectから除外され、`oversized_or_reference_parts.csv` に出力されます。標準では printer/filament preset を埋め込まず、Bambu Studio側の現在設定を使用します。開けない場合は、同時出力される個別3MFをフォールバックとして使用してください。
