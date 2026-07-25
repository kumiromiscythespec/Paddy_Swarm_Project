# HTD 5M printed pulley calibration artifacts v0.1

This directory contains **calibration-only** artifacts for the Paddy Swarm
Project's future 20T and 60T printed HTD 5M pulleys:

- one 6 mm bore gauge bar;
- one 10 mm bore gauge bar;
- six curved, six-groove belt-fit coupons (20T/60T × tight/standard/loose).

The 20T and 60T pulley bodies have **not** been created. These parts are not
PTO/load-test parts and must not be used for rotating or torque tests.
All physical fit decisions are `CALIBRATION_PENDING`.

## Build

Use the repository's CAD environment:

```powershell
C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe build_all.py --validate
```

The build writes individual STEP and STL files to `exports/`, plus three
optional disconnected STEP presentation plates. The individual files are the
authoritative print inputs.

No 3MF is emitted because this environment has no established direct 3MF
generation/verification path. No empty or renamed “fake 3MF” is created.

## Recommended print settings

- Printer: Bambu Lab A1
- Material: PETG
- Nozzle: 0.4 mm
- Layer height: 0.16 mm
- Wall loops: 5 or more
- Bore gauges: 100% infill
- Tooth coupons: 50% infill for screening, or 100% for the final comparison
- XY scaling/compensation: disabled
- Hole compensation: disabled
- Print the engraved face upward
- Bore gauges: place the large unengraved face flat on the bed; bores stay on Z
- Coupons: place the unengraved sector face flat on the bed; tooth-face width
  stays on Z and the recessed ID remains on the upper, non-contact face

Do not change slicer XY scale or hole correction between candidates. Test the
gauge bores with the real 6 mm and 10 mm shafts. Test coupons by hand against
the actual HTD 5M belt only—do not rotate, motor-drive, or load the coupon.

## Calibration sequence

1. Print the two bore gauges and record shaft feel.
2. Print the 20T-S and 60T-S standard coupons.
3. Print tight/loose variants only if needed, or print all six when the extra
   material/time cost is acceptable.
4. Complete `reports/calibration_record_template.md`.
5. Obtain explicit human approval before carrying any selected value into a
   full pulley design.

No selection is propagated automatically. The actual belt, shaft, printer,
material batch, orientation, and slicer settings remain part of the result.

## File guide

- `parameters.py`: central dimensions and candidate values
- `htd5m_profile.py`: H5M pitch, nominal OD, profile bands, paired-arc cutter
- `bore_gauges.py`: true-circular bore gauge bars
- `tooth_fit_coupons.py`: curved six-station fit coupons
- `build_all.py`: STEP/STL generation
- `validation.py`: geometric, round-trip STEP, and STL mesh checks
- `render_previews.py`: optional visual-QA sheet renderer
- `DESIGN_SPEC.md`: assumptions, standards basis, and acceptance boundary
- `reports/calibration_record_template.md`: human measurement record
