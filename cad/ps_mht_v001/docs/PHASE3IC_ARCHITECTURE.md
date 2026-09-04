# Phase 3I-C architecture

Phase 3I-C freezes all 46 Phase 3I-B artifacts as a historical failed baseline. The Phase 3I-B sump, inner dam, water level, overflow, port recess, cradle, cascade, wick routes, and stacking guides are reused without modification.

The corrected authority is `build_integrated_stage_corrected_phase3ic(...)`. D01 through D05 call this one builder with cumulative boolean flags. D05 and the corrected full output call the same builder with all flags true.

The only full-model design change relative to Phase 3I-B is the retention-lug Boolean. Six lugs are cut individually with 5.6 mm teardrop holes and fused individually without the Phase 3I-B Glue shortcut. Each starts above the operating water surface and overlaps an existing floor-connected side buttress by 0.85 mm, preserving the physical water volume within numerical tolerance.

The horseshoe keeper V2 remains inside the measured Ø108 pot flange envelope. It distributes the 5 mm cord load without expanding the installed-pot envelope.

