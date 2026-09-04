# PS-WP TPU Face Gasket V001

CAD_PASS/CONTRACT_TEST_PASS/PS_WP_TPU_FACE_GASKET_DUMMY_PRINT_READY/G25_S20_PRIMARY_TEST_READY/WATER_PHYSICAL_TEST_PENDING/BBOX_V005_PENDING/CBOX_FIELD_BOX_PENDING

NEW common lane: `cad/common/waterproof/ps_wp_tpu_face_gasket_v001`. No BBOX/CBOX conversion and no historical artifact mutation.

First print: TPU thickness calibration pads -> measure -> G25 gasket -> T1-T8 -> S20 PETG stops -> measure -> common body/lid -> dry10 cycles -> closed water test. Do not print every variant before primary evidence.

Primary G25/S20: one-piece5 mm-wide,2.5 mm-thick TPU loop and four2 mm PETG collars; nominal20% compression. Body and lid are reusable for all candidates. Two thin external locating ears register around the stop collars without interrupting the seal. Fit without adhesive.
Flat PETG land10 mm accommodates nominal lateral bulging; there is NO old2.1 mm round-cord groove. Lid6 mm selected from the4-6 range by section-stiffness comparison. No actual TPU brand or Shore is invented.

Latest round-cord history: small G065 dummy PASS remains valid; full V00460-minute water test FAIL with UNRESOLVED_SLOW_INGRESS. User old EPDM nominal3 mm / light-caliper approximately3.4 mm replaces the1.8 physical assumption. None of those diameters drive TPU geometry.

CAD:14 STEP /11 STL /8 SVG. Primary assembly uses the FREE2.5 mm gasket reference, so its0.5 mm overlap with the closed lid is intended nominal elastic compression, not a rigid collision or deformation prediction. Only individual printable STL files are printed; never print the assembly.

Python3.12 / CadQuery2.8 / OCCT7.9; use -B to keep caches out of protected lanes:

```
python -B build_ps_wp_tpu_face_gasket_v001.py --build
python -B tests/test_ps_wp_tpu_face_gasket_v001.py
python -B build_ps_wp_tpu_face_gasket_v001.py --verify
python -B build_ps_wp_tpu_face_gasket_v001.py --zip
```

Geometry generator is standalone; repository verification needs the preserved authority paths in audit_start.json. ZIP contains only this lane. Git add/commit/push/branch changes are forbidden during this task. COMMIT_PATHS is an inventory, not staging permission.
See TPU_PRINT_MEASUREMENT_PLAN.md for orientations/support/slicer review and measured-compression calculator. No water, BBOX, CBOX, durability or field PASS is claimed.
