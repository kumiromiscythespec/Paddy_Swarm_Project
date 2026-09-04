# Phase 3I-A Bambu Studio Review Checklist

Status: `BAMBU_STUDIO_REVIEW_PENDING`.

Load `plate_01_integrated_stage_full_SLICER_REVIEW_ONLY_phase3ia.stl` vertically with the sump floor on the build plate. Do not rotate sideways, tilt, split, sectorize, or enable automatic support as a design dependency.

Record the following from Bambu Studio without substituting CAD estimates:

1. XY envelope is at most 238 mm and Z is 170 mm.
2. One object and one connected component are present.
3. Mesh repair reports no non-manifold or boundary edges.
4. Every automatically proposed support location is inspected; none may be trapped internally.
5. Port teardrop roofs, cradle undersides, flange seats, wick paths, sump corners, rear channel, weir, guides, and gusset roots are reviewed layer by layer.
6. No unsupported bridge over 8 mm, thin isolated island, interrupted wall, or Y-axis slender free wall is present.
7. The sump floor remains continuous and the rear/open overflow route remains unobstructed.
8. Estimated print time and filament mass are recorded.
9. Abrupt layer-area changes are recorded, especially at cradle engagement and teardrop closure.

The full model stays `DO_NOT_PRINT` until this checklist passes. The lower coupon becomes the first print only after the same review is applied to Plate 02.
