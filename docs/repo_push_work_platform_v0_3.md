# GitHub push手順

ローカルの `C:\Paddy_Swarm_Project` にZIPを置いた前提です。

```powershell
cd C:\Paddy_Swarm_Project
Expand-Archive -Path .\paddy_swarm_work_platform_chassis_cad_v0_3.zip -DestinationPath . -Force
git status
git add .
git commit -m "Add four-wheel work platform chassis CAD v0.3"
git push
```

## 推奨コミット内容

- `stl/work_platform_v0_3/`
- `cad/work_platform_v0_3/generate_work_platform_v0_3.py`
- `docs/work_platform_chassis_v0_3.md`
- `docs/print_notes/PSR-WP-R00.md`
- `print_manifest_work_platform_v0_3.csv`
- `kit_index_work_platform_v0_3.csv`
