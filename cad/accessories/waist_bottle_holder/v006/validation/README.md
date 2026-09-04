# Validation method

`source/build_bh_v006.py` は生成後に次を自動検査し、root の `validation_report.json` へ保存します。

- 各 STEP を CadQuery 2.8.0 で再読込し、solid 数、B-rep validity、正体積を確認
- 各 STL を trimesh で vertex merge 後、watertight、winding、edge incidence、正体積、body 数を確認
- solid signature による artifact 内重複 body 検査
- nominal main/collar intersection と、Z +30 mm から 0 mm までの離散上差し経路検査
- receiver floor、cup bounds、functional cavity bounds、neck gauge、rope gauge、cap envelope、tab stop gap の解析検査

`artifact_manifest.json` は生成対象の STEP/STL 一覧です。slide coupon は receiver と tab の意図した 2 shell、assembly preview は main と collar の意図した 2 shell です。物理 fit と field test は自動 PASS にしません。
