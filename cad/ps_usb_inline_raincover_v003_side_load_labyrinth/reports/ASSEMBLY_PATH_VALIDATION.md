# ASSEMBLY PATH VALIDATION

## ASSEMBLY_PATH_CHECK

- `lower cable path open from above`: PASS
- `no single-part closed ring`: PASS
- `continuous cable side-load path`: PASS
- `connector body placement path`: PASS
- `upper closure after cable placement`: PASS
- `CLOSED CABLE LOOP IN LOWER`: NONE
- `CLOSED CABLE LOOP IN UPPER`: NONE

The lower placement sweep models an attached cable moving vertically from above into every dogleg segment.
The upper release sweep models the complementary part remaining open downward. Both have 0 mm³ interference.
The upper may therefore close after cable placement; no cable end, connector removal, or cutting is required.
Physical remove/reinstall ×5 is still mandatory before this becomes `ASSEMBLY_PATH_PASS`.
