# P25 Slide-In Positioning Block V002

CAD_PASS/CONTRACT_TEST_PASS/2040_SLIDE_FIT_COUPONS_PRINT_READY/P25_SLIDE_B_PROVISIONAL_PRINT_READY/PHYSICAL_FIT_SELECTION_PENDING/STRUCTURAL_LOAD_AUTHORITY_PENDING

## Outcome

This lane converts the selected P25 placement distance into a removable,
end-inserted T-slot positioning interface.  The two explicit P25 datum patches
remain exactly 25.000000 mm apart and do not depend on tongue width.

The controlling physical inputs are the user's direct measurements: entrance
6.4 mm, maximum internal width 10.8 mm, and surface-to-bottom depth 6.4 mm.
The complete lip section is not known.  The reference STEP contains only five
constraint markers; its marker thickness is display-only.  It is not a generic
2040 authority or a manufactured rail reconstruction.

|Coupon|Stem|Head|Depth|Stem H|Bottom|Entrance/side|Head/side|Capture/side|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|A|5.6|9.8|5.8|3.8|0.6|0.4|0.5|2.1|
|B|5.8|10.0|5.9|3.9|0.5|0.3|0.4|2.1|
|C|6.0|10.2|6.0|4.0|0.4|0.2|0.3|2.1|

Coupon B supplies the provisional full P25 tongue.  Print A, then B, then C as
needed, and select the tightest candidate that still inserts from the extrusion
end and slides smoothly by hand without PETG/aluminum damage.  Never hammer,
press, lever or use pliers.  Do not push a coupon vertically through the slot.

## Print

PETG / Bambu A1.  Each printable STL is already oriented with the flat insertion
end on the plate and logical +X toward print +Z.  Critical head/stem width and
slot depth therefore lie in XY.  The end-only 0.4 mm lead-in occupies the first
0.4 mm; all later fit sections are exact and untapered.  Support OFF.  The
coupon footprint is about 14 x 10 mm and height20 mm; P25 footprint is18 x13.9
mm and height25 mm.  Add brim only if the slicer/operator requires it; keep it
off the fit section after removal.  Slicer review remains HOLD_SLICER_NOT_RUN.

Labels A/B/C and the P25/slide-arrow marks are recessed only into non-fit top
surfaces.  No text or chamfer touches the designated P25 datum patches.

## Safety / scope

This PETG tongue is a positioning and assembly gauge.  It is not responsible
for belt tension, PTO torque, KP000 load, shock or field impact.  Structural
loads require future approved metal fasteners, T-nuts, frame and support.  No
plastic set screw, snap, wedge or cam lock is present.

If B wins, the provisional P25 block may proceed to the documented physical
position test.  If A or C wins, create a new corrected artifact later; do not
silently modify V002.  Parent V001 and all protected lanes are read-only.

Run with Python 3.12.13 / CadQuery 2.8.0:

```
python -B build_p25_slide_in_positioning_v002.py --build
python -B tests/test_p25_slide_in_positioning_v002.py
python -B build_p25_slide_in_positioning_v002.py --verify
python -B build_p25_slide_in_positioning_v002.py --zip
```

COMMIT_PATHS is an inventory, not permission to stage.  Git add/commit/push were
not performed.
