# Paddy Swarm Amphibious Hull CAD Pack v0.1 / 水陸両用型ローバー船体CADパック

This pack adds the first printable CAD/STL set for the Paddy Swarm Amphibious Hull concept.

このパックは、Paddy Swarm Project の「水陸両用型ローバー船体 v0.1」をGrade 0試験用に3Dプリントできる形へ落としたものです。

## Important / 重要

These parts are **experimental Grade 0 parts**. They are not waterproof, not field-proven, and not a finished rover.

- Do not put electronics or batteries in water.
- Do not use these parts in a real paddy field first.
- Start with PLA fit checks, then PETG water-tank tests.
- Use foam inside float trays during water tests.
- Seal seams only for controlled tests using tape/silicone.
- If a paper towel placed in the waterproof-box position gets wet, the design fails the water-ingress test.

## Contents

- `stl/hull_v0_1/` — printable STL files
- `cad/hull_v0_1/generate_amphibious_hull_v0_1.py` — source generator used to create the STL files
- `docs/amphibious_hull_v0_1.md` — design notes and assembly concept
- `docs/print_notes/PSR-HU-R00.md` — print notes
- `print_manifest.csv` — part sizes and print notes
- `kit_index.csv` — repo index entries

## First print recommendation

Print in this order:

1. `PSR-HU-001-R00_central_hull_short_frame.stl` in PLA
2. `PSR-HU-013-R00_ballast_test_tray.stl` in PLA
3. One float tray, e.g. `PSR-HU-003-R00_left_float_mid_tray.stl`, in PLA
4. Same float tray in PETG
5. Float lid and seam joiner clips
6. Water-tank test with no electronics

## Repository merge

From the repo root:

```powershell
Expand-Archive -Path .\paddy_swarm_amphibious_hull_cad_v0_1.zip -DestinationPath . -Force
git add .
git commit -m "Add amphibious hull Grade 0 CAD pack v0.1"
git push
```
