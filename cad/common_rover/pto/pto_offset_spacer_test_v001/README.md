# PTO Front Output Offset Spacer Test V001

CAD_PASS/CONTRACT_TEST_PASS/PLACEMENT_GAUGE_PRINT_READY/STRUCTURAL_SPACER_INTERFACE_PENDING/PHYSICAL_CLEARANCE_TEST_PENDING/SLIDE_CLUTCH_FINAL_ENVELOPE_PENDING

## Important outcome

These are NON-LOAD-BEARING PLACEMENT GAUGES, not permanent structural spacers.
The requested file stems retain `pto_offset_spacer_20/22/25`, but each part only
establishes a directly measurable separation between its two parallel end faces.
Do not install one under a bearing, on a shaft or in a loaded drivetrain.

Repository evidence does not prove the new frame-end/KP000 second mounting face,
offset direction, support load path or installed rigid transforms. The existing
Front Interface V002 is explicitly NOT_PROVEN_MANUFACTURED_OR_INSTALLED. Its
old global coordinates cannot supply those missing measurements.

The user rejects the front L-bracket. Local X0 is the physical member-end face,
not a triangular joint, L-bracket, global vehicle origin or old CAD X value.
The nominal 500 mm member length remains a reference candidate, not promoted
physical authority. Identify the exact mating face B before using a gauge.

|Candidate|Working length mm|Nominal residual mm|Role|Installed clearance / winner|
|---|---:|---:|---|---|
|P20|20.0|3.0|MINIMUM_SPACE_CANDIDATE|HOLD / PHYSICAL_TEST_PENDING|
|P22|22.0|5.0|BALANCED_CANDIDATE|HOLD / PHYSICAL_TEST_PENDING|
|P25|25.0|8.0|HIGHER_CLEARANCE_CANDIDATE|HOLD / PHYSICAL_TEST_PENDING|

Residuals are L - (100.1 - 66.1)/2, not measured or installed-CAD clearances.
No winner is selected. Available clutch corridor and PTO local shaft X remain
N/A / PHYSICAL_PENDING; the gauge alone does not define them.

## Print first

PETG; flat bottom down; support OFF. Individual bounds are 20/22/25 x 18 x 8 mm.
Top engraving is 20/22/25, 0.6 mm deep, clear of both end faces. Measure at
Y=-5..+5 and Z=2..6 mm to avoid first-layer elephant foot. Optional triplet STL
contains three separate gauges; no sprue connects any working surfaces.
Use an actual Bambu A1 slicer review; slicer has NOT been run. No invented print
time or load rating. Inspect both working faces for warp, burrs and parallelism.

Secure the PTO assembly independently. Use gauges only while stopped; REMOVE
ALL GAUGES before any hand rotation. Never operate a motor with these gauges.
If the actual bearing/support cannot be safely secured, keep rotation HOLD.

## Package / verification

15 STEP, 4 printable STL, 9 SVG, source, tests and reports. Reference assembly
STEPs are EXPLODED COMPONENT BOARDS, not a mounted rover or printable assembly.
The 60T physical envelope uses diameter 100.1; its displayed 26 mm axial extent
is from provisional CAD and is NOT a complete measured rotating envelope.
Source 20T and Candidate C/MISUMI geometry are reused as reference only.

Python 3.12.13 / CadQuery 2.8.0. Use -B; do not create cache in protected lanes.

```
python -B build_pto_offset_spacer_test_v001.py --build
python -B tests/test_pto_offset_spacer_test_v001.py
python -B build_pto_offset_spacer_test_v001.py --verify
python -B build_pto_offset_spacer_test_v001.py --zip
```

Builder requires the original protected repository references. It never runs
their builders' write entry points. COMMIT_PATHS is an inventory, not permission
to stage. No BBOX, CBOX, frame, PTO, drivetrain or physical authority was patched.
