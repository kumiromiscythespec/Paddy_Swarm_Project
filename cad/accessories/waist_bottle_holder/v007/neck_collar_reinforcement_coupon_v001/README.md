# BH_V007 Neck Collar Reinforcement Coupon Study

This lane contains three PETG functional coupons for selecting a stronger V007 neck collar. It does **not** update the V007 production main body, receiver, or collar. Production authority remains undecided until physical testing.

## Decision status

- First print recommendation: **N-B**.
- 3-up plate order: left-to-right N-A, N-B, N-C. If printing individually, test N-B, then N-A, then N-C.
- Existing V007 collar root strength: **FAIL** (comparison evidence only).
- Six candidate physical states—neck insertion fit and root durability for each of N-A/N-B/N-C—remain **PENDING**.

## Fixed receiver-fit authority

- Neck ID: 26.2 mm.
- Long tab: 16.0 x 4.0 x 30.0 mm, reused as the exact V007 B-rep.
- Receiver hold cavity: 17.1 x 4.8 mm, reference-only and not regenerated.
- Narrow root/gusset X envelope through the receiver front slot: 10.0 mm inside the existing 10.8 mm slot.

## Candidate comparison

| Item | Existing V007 | N-A | N-B | N-C |
|---|---:|---:|---:|---:|
| Finished clear opening | 5.000 | 18.000 | 20.001 | 20.001 mm |
| Nominal arm thickness | 3.0 | 4.0 | 4.0 | 3.5 mm |
| Collar height | 7.0 | 9.0 | 9.0 | 9.0 mm |
| Minimum root-throat section | 97.947 | 134.000 | 134.000 | 134.000 mm2 |
| Root-section increase | — | +36.81% | +36.81% | +36.81% |
| Total CAD volume | 6024.96 | 8594.38 | 8495.21 | 8229.33 mm3 |
| Saddle/bridge/gusset volume | bridge 2562.65 | 4892.11 | 4892.11 | 4892.11 mm3 |
| Total gap expansion to pass phi26.2 | 21.200 | 8.200 | 6.199 | 6.199 mm |
| Symmetric motion per free tip | 10.600 | 4.100 | 3.100 | 3.100 mm |

The finished gap is measured on the filleted B-rep, not inferred from an angle. The pre-fillet cuts are compensated to 17.966 / 19.925 / 19.705 mm so the finished R1.5 tips produce the target 18 / 20 / 20 mm gaps.

## Reinforced root geometry

All three variants use the same load path: a 26 x 16 mm broad rear saddle with R8 plan ends, a 10 mm-wide receiver-slot bridge, and two rounded gusset rails. Each gusset is 4 mm thick and 14 mm high. The rails extend below the collar while staying at or below the collar top, preserving cap-side clearance.

## Files

- `step/`: three individual functional STEP coupons and the N-A/N-B/N-C comparison STEP.
- `stl/`: three individual STL coupons and the plate-ready 3-up preview STL.
- `parameters.json`: dimensions, fixed authority, test state, protected V007 hashes, and start Git state.
- `validation_report.json`: B-rep, mesh, fit-path, comparison, protected-file, and Git checks.
- `validation/artifact_manifest.json`: artifact inventory.
- `docs/GEOMETRY_COMPARISON.md`: comparison and physical selection protocol.
- `source/`: reproducible CadQuery generator and preview renderer.

## Printing and test order

Material is PETG. Use 0.16–0.20 mm layers, at least 6 walls around the collar/root, 35–40% infill, a brim on the long-tab nose, and support under suspended ring/root surfaces as indicated by the slicer. Individual STLs retain functional coordinates with local Zmin = -7 mm; let the slicer drop them to the bed. The 3-up preview is already translated to mesh Zmin = 0.

For each coupon, record: (1) insertion over the actual 26.2 mm neck without cracking or severe whitening, and (2) root durability under the intended pull/bounce cycle. Do not promote a production collar from CAD results alone.

## Regeneration

Run from the repository root with the CadQuery 2.8 environment:

```powershell
conda run -n paddy-cadquery-280-py312 python cad/accessories/waist_bottle_holder/v007/neck_collar_reinforcement_coupon_v001/source/build_neck_collar_reinforcement_coupons.py
conda run -n paddy-cadquery-280-py312 python cad/accessories/waist_bottle_holder/v007/neck_collar_reinforcement_coupon_v001/source/render_coupon_preview.py
```

