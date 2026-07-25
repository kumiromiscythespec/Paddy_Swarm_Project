# GitHub取り込みメモ

推奨repository path:

`cad/crawler_h1/track_module/pretest_candidate_v0_1/`

このpackageは履歴保存用です。上流STLはbyte-identicalで、再生成・再修復していません。

取り込み前確認:

- `__pycache__`, `.pyc`, `.pyo` が0
- 5個のcandidate STLのみ
- SHA256SUMS一致
- source_snapshotsは履歴参照用であり、self-contained generatorを主張しない
- production / manufacturing / field releaseを付与しない
- mainへのmerge前にfeature branchでreviewする
