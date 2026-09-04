# Print instructions

Printer envelope: Bambu A1 256 x256 x256 mm. Material: PETG body/lid; removable runners TPU.

First full-box print set after CAD/contracts PASS:

1. `artifacts/compact_field_bbox_v004_g065_body.stl`
2. `artifacts/compact_field_bbox_v004_g065_lid.stl`
3. `artifacts/tpu_runners.stl` later for dry battery fitting (two independent 30 x55 x1 runners).

Body 180 x96 x114.395: floor down, open side up. Exterior flange and tower undersides may need build-plate-only supports. Block supports from groove, inside sealing surfaces and battery cavity. No groove support.
Lid 180 x104 x58: flat seal face at Z0 on a clean flat build plate, chimney upright. This avoids printing the large lid suspended on its chimney. Inspect plate texture, flatness and first-layer artifacts on the sealing face; do not release a distorted seal surface. Support hood/outer details only if required; do not leave trapped support in the chimney. The lower opening is 42 x27.5 mm after the sealing bridge correction; check access and support removal in slicer.
TPU combined layout 126 x55 x1: pads flat at Z0; no permanent bond required.

STL uses ASCII 9-decimal vertices to preserve actual groove depth to 1e-6 mm at CAD scale. This precision is not a claim of printer accuracy.
Slicer NOT RUN: HOLD_SLICER_NOT_RUN / PROCESS_PENDING. Confirm walls, bridge/hood support and watertight extrusion paths in Bambu Studio before starting. CAD print-ready is not a physical or field qualification.
Never overtighten M4 to flatten warped PETG. Metal washers/nuts; select actual bolt stack from printed hardware, not a fictitious fastener measurement.
