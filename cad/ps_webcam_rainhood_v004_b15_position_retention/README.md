# ps_webcam_rainhood_v004_b15_position_retention

Status: `CAD_COMPLETE_B15_POSITION_RETENTION_PHYSICAL_VALIDATION_PENDING`

This lane carries the physically tested v003 B optical front into a full rainhood and adds low-force camera-side position retention. It does not move the v002 tripod axis, carrier seating plane, shell rails/stops, M4 pattern, nut traps, or USB relief.

## Decision

- A setback 10: `FAIL_OPTICAL / REJECTED`.
- B setback 15: nominal FOV clear, shift FOV fail, `SELECTED_CONDITIONAL`.
- C setback 20: `OPTICAL_ROBUST_PASS`, retained as `KNOWN_FALLBACK`.

B keeps 5 mm more forward roof than C. v004 therefore holds the B optical edge at Y=-45.4 mm and addresses shift with extended lateral guides and shallow corner/yaw stops. It does not solve B by shortening it toward C.

`B_setback15` is not an optical robust pass. A visible hood edge after excessive displacement is only a possible status indication:

- `SAFETY_FEATURE = FALSE`
- `STATUS_INDICATOR_ONLY = TRUE`

## First print

Print this first:

`stl/b15_position_retention_coupon_v004.stl`

Do **not** print the full rainhood first. The coupon integrates the actual v004 carrier seating plane, tripod access, extended guides, front/rear shallow stops, a minimal B15 optical front reference, and four permanent exterior ribs. It tests seating, play, interference, and repeatability with less material than the complete hood/carrier test set.

Only after `PASS_POSITION_RETENTION`, print one `stl/rainhood_b15_v004.stl` and one `stl/tripod_carrier_b15_v004.stl`. Do not batch-produce.

## Position-retention change

| Feature | v002 | v004 | Intent |
|---|---:|---:|---|
| Side-guide clearance | 0.7 mm | 0.7 mm | No silent press-fit change |
| Guide height | 2.8 mm | 2.8 mm | Keep known low guide |
| Side-guide length | 44.0 mm | 52.4 mm | Longer yaw lever arm and lower flex |
| Rear stops | Existing | Unchanged | Y datum |
| Front corner stops | None | Two, 2.8 mm high, 0.7 mm gap | Shallow Y/yaw restraint |
| Guide root | Narrow guide | Low outward-only 1.2 mm foot | PETG reinforcement without reducing clearance |

Normal seating target is `NONE or LIGHT` contact. `HARD PRESS FIT` is prohibited.

## B15 optical authority

- setback from v002: 15.0 mm
- front Y: -45.4 mm
- underside bevel: 40.0 degrees
- calculated bevel run: 2.080 mm
- front length: 15.0 mm
- outer / inner width: 118 / 112 mm
- wall: 3 mm
- top-clearance datum: 4 mm

The full hood restores the v002 rear roof and rain baffle. The v002 downward front drip wall is not restored because it occupies the tested optical zone. The physically tested sharp 1.2 mm B leading edge and upward 40-degree underside bevel remain the front rain-cut geometry. Rain performance is pending physical spray and field tests.

## Generate

```powershell
& 'C:\Users\yu_ki\Miniforge\envs\paddy-cadquery-280-py312\python.exe' `
  'D:\Paddy_Swarm_Project\cad\ps_webcam_rainhood_v004_b15_position_retention\cad\ps_webcam_rainhood_v004.py'
```

The source generates all STL, STEP, parameters, engineering diagrams, validation reports, and `SHA256SUMS.txt`.
`SHA256SUMS.txt` follows the standard non-self-referential convention: it covers every other file in the lane; the manifest's own hash and the ZIP hash are reported separately at handoff.

## Print orientation

- Position-retention coupon: place the flat **left exterior side/spine** on the build plate, with the four identifier ribs facing upward. This makes the optical roof a vertical web and avoids a 118 mm horizontal roof bridge. Use a brim if needed; inspect the short guide/stop overhangs manually.
- Carrier: broad underside at Z=-6 mm on the build plate; guides upward. Normal through-holes need no internal support.
- Full rainhood: use the rear Y=43 mm face/baffle/crossbar datum on the build plate, matching the v002 rear-datum design intent. Inspect the bevel, rails, nut traps, and USB relief layer preview.
- Printer/material baseline: Bambu Lab A1, PETG, 0.4 mm nozzle, 0.20 mm layers, at least three walls.

Slicer auto-support output alone is not a printability pass.

## Pass separation

- CAD PASS: yes, see `reports/VALIDATION_REPORT.md`.
- PRINT / FIT / STATIC / POSITION RETENTION: pending.
- Full-hood optical: pending.
- Rain visual / water / field / durability: pending.
- Tripod-thread physical insertion: pending.
- Commercial metal pipe clamp: `HOLD_SELECTION`.

Current blocker: `mount lateral/yaw position retention`.
