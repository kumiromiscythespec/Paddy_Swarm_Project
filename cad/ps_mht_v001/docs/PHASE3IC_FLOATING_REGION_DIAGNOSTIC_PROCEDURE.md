# Phase 3I-C floating-region diagnostic procedure

Use Bambu Lab A1, 0.4 mm nozzle, PETG Basic, 0.20 mm layer height, support OFF, brim OFF, and the registered STL orientation.

For every stage, create a new Bambu Studio project and load exactly one STL:

1. Slice D01 and record warning presence, first warning layer/Z, visible location, and screenshot.
2. Close it and repeat in a new project for D02.
3. Repeat for D03, D04, and D05 without changing settings.
4. The first stage changing from `NONE` to `PRESENT` identifies the first suspect feature group.

Do not place multiple diagnostic STLs on one plate and do not print them. A CAD mesh pass is not a Bambu Studio warning pass.

