# Design authority

Selected authority is the unique repository-native v2.28 fixed-core source matching the user-provided nominal dimensions:

- `rovers/common_rover/v2.28/paddy_swarm_v228_2_dual_pto_output_fix_cadquery.py`
- `rovers/common_rover/v2.28/rover_v228_2_dual_pto_output_fix_out/step/PS-RV227-BBOX-BDY.step`
- `rovers/common_rover/v2.28/rover_v228_2_dual_pto_output_fix_out/step/PS-RV227-BBOX-LID.step`
- `rovers/common_rover/v2.28/rover_v228_2_dual_pto_output_fix_out/step/PS-RV227-BBOX-GSK.step`
- `interfaces/power/bbox_battery_cassette/v001/README.md`

The source contract fixes body 200 × 150 × 120 mm, lid 216 × 166 × 16 mm nominal, and gasket 204 × 154 × 3 mm. The generated lid STEP's actual bbox is 216 × 166 × 18.5 mm because its source top ribs extend 2.5 mm above the nominal 16 mm plate body. Both facts are recorded; tower height uses the actual STEP bbox.

Later v0.9.6.0 waterproof architecture uses a conflicting 200 × 130 family and is not the authority for this physical 200 × 150 lid/gasket contract. The chosen source's body STEP has a 200 × 162 overall bbox because loose-layout floor ribs extend beyond the nominal Y envelope; those non-seal ribs are not copied.

The exact continuous rim before source notch cutting is outer 200 × 150, inner 192 × 142, width 4, and flat at the top. The dummy reproduces it with zero added and zero removed volume in a 1 mm section. Source notches are explicitly drip-resistant rather than waterproof and are closed by task instruction. Source lid, gasket, and builder contain no closure holes; exact empty pattern is retained. `HOLD_ACTUAL_CLOSURE_METHOD` remains active.

This authority releases CAD and first printing only. It does not release a leak result, closure hardware, ballast fixing, load, electronics, powered operation, field use, or production.
