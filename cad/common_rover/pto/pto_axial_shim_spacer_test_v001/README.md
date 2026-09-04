# Common Rover PTO Axial Shim Spacer Test V001

Status: `CAD_PASS/CONTRACT_TEST_PASS/PTO_AXIAL_SHIM_TEST_SET_PRINT_READY/PTO_SPACER_PHYSICAL_AUTHORITY_PENDING`  
Classification: `PHYSICAL TEST SHIM / PETG PROTOTYPE / NOT FINAL FIELD AUTHORITY`

## Result

Two independent, square-edged annular shims were generated at exact CAD thicknesses 0.5 and 1.0 mm. Both reuse repository spacer cross-section authority ID 10.2 / OD 13.8 mm. The exact source is `cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9/SPACER_8MM_PHYSICAL_UPDATE.md`, which preserves the installed 8 mm reference. Earlier v0.9.6.4–v0.9.6.8 records agree; no newer conflicting current ID/OD was found.

The shim belongs only in the rotating stack: `bearing inner-ring rotating face -> shim -> PTO pulley rotating face`. It must never bridge to the KP000 housing, bearing outer ring, seal, frame, or stationary bracket. OD13.8 remains 0.2 mm radially inside the known OD14.2 rotating inner region. Exact KP000 inner-ring axial contact-face position is not measured, so `PHYSICAL_CONTACT_FACE_PENDING` remains.

Front Interface V002 and the PTO 20T physical authority are read-only and unchanged. The assembly STEP is non-printable and uses a simplified bearing-face reference plus the real measured PTO 20T envelope to show 0/0.5/1.0 arrangements; it does not release an installed axial datum.

## Print

Print each ring flat, axis vertical, PETG prototype, no support. Do not print on edge. Use no brim unless the slicer needs it. First-layer expansion can reduce the Ø10.2 opening; keep CAD ID unchanged and apply elephant-foot compensation only as a slicer/user setting. The exact 0.5 mm CAD was not thickened. Measure every printed part before use. PETG is not approved as the final long-term wear material.

## Selection

Compare no shim, one measured 0.5 mm shim, and one measured 1.0 mm shim. Two 0.5 mm parts are an optional nominal 1.0 mm cross-check, but their printed sum must be measured. Select the smallest spacing that rotates freely without rubbing/binding and retains belt alignment/service clearance. CAD does not preselect a winner.
