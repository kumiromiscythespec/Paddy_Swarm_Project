# TPU print and measurement plan

Material: CURRENT_TPU_SPECIMEN. Exact manufacturer/product and Shore hardness PHYSICAL_PENDING. Search evidence is in material_authority_audit.json. Existing approximate95A design assumptions do not identify the current spool. Record brand, spool label, lot, hardness if documented, drying and actual slicer settings; do not invent95A.

First print order:

1. TPU thickness calibration coupon: three14 x14 pads at X=-20,0,+20, nominal2.0/2.5/3.0 mm. They are separate pads, not a structural part. Print flat without support; keep pad order identified. Measure with light contact.
2. G25 complete gasket only. Flat on plate; nominal Z thickness2.5 mm. No support, adhesive joint or cut.
3. S20 PETG stop set only: four2.0 mm collars, flat. Do not sand selectively to hide unequal thickness without recording the new dimensions.
4. Common PETG body and lid after dimensional checks.

TPU: inspect elephant foot, closed holes, width/perimeter accuracy, stringing, layer gaps, face roughness and tears. Record BUILD_PLATE_FACE and TOP_PRINT_FACE separately. PRIMARY orientation: BUILD_PLATE_FACE toward BODY. If needed compare the reverse orientation later while keeping other variables constant; log each orientation as a separate run.

Use light caliper contact only. Do not squeeze TPU to obtain a target reading.
T1-T4: straight midpoints(+29,0),(0,+29),(-29,0),(0,-29).
T5-T8: near-corners at (+/+),(-/+),(-/-),(+/-) coordinates approximately27.096194 mm each axis.
Record T1-T8; calculate MIN/MAX/MEAN/RANGE. Measure all four PETG spacers S1-S4. With gentle even closure to stops, measure effective local gaps G1-G4; do not assume perfectly rigid/parallel printed faces.

Copy physical_measurement_template.json outside the protected lane for actual observations. Fill measured arrays only with actual values, then:

`python -B build_ps_wp_tpu_face_gasket_v001.py --measurements <filled-result.json>`

The calculator requires8 thickness readings,4 stop readings and4 closed-gap readings. It rejects missing, non-finite or non-positive values. Output includes range-based compression estimates; it does not grant water approval.

Printer: Bambu A1,256-cube build envelope. Body open-up; floor down. Lower wall/floor3.5; broad seal land has a45-degree outer flare plus a1 mm flat cap. External M4 lug undersides may need build-plate-only support. Keep all support away from the seal, cavity and stop datum faces.
Lid6 mm: flat on plate, preferred future sealing face UP to avoid plate-texture assumptions. Its two flat faces and through-hole pattern allow installation inverted. Body/lid print orientation is independent from TPU face orientation.
TPU and all spacers: flat, support OFF. Stop faces and gasket faces must not be damaged by brim removal. Use separately labeled bags for spacer sets; no label is on a working face.
SLICER_NOT_RUN / PROCESS_PENDING. Review watertight toolpaths, solid skins, material settings, support blockers and flatness in the actual slicer. Nominal CAD precision is not printer accuracy. No invented universal TPU print profile.
