# Physical optical test protocol

Status before testing: `PHYSICAL_OPTICAL_VALIDATION_PENDING`

RAIN_TEST: `NOT_TESTED`

Use one camera, one already-established v002 carrier, the same tripod screw/hardware, the same preview settings, and the same support pose for A/B/C. Do not compensate by tilting the camera downward between candidates.

## Preparation

1. Confirm candidate identity by permanent exterior ribs: A=1, B=2, C=3. Do not rely only on a filename or handwritten label.
2. Inspect the leading bevel, rails, stops, M4 holes, and nut traps for print defects.
3. Remove only support material and obvious stringing; do not sand the rail datum differently between candidates.
4. Set camera preview to the same resolution, crop/zoom, stabilization, rotation, and aspect ratio for all tests. Record those settings.
5. Mark a repeatable near-horizontal support attitude. The purpose is comparison at the normal tripod position, not hiding intrusion by tilt.

## Per-candidate procedure

1. Attach the v002 carrier to the camera.
2. Install the tripod screw with the already-established safe hardware and insertion practice.
3. Slide the hood/coupon into the normal v002 position until both rear stops seat; install both shell-retention fasteners.
4. Display live camera preview.
5. Fix the assembly at the near-horizontal reference attitude.
6. Inspect the image top edge.
7. Inspect upper-left, upper-center, and upper-right separately.
8. Record whether hood material is visible, including blur, arc, shadow, or reflected highlight.
9. Apply a small hand load through the available mount play in each direction without loosening the screw. Reinspect all three upper regions.
10. Release the load and verify the assembly returns to its seated datum.
11. Visually note front/top/lateral rain coverage. This observation is not a rain test and cannot produce `RAIN_PASS`.
12. Record `PASS_CANDIDATE`, `FAIL_OPTICAL`, or `HOLD`.

`PASS_CANDIDATE` means only that the candidate can advance. It is not final selection. A final geometry needs additional clearance beyond a just-invisible boundary to cover print, screw, camera, and assembly variation; do not guess that margin before the A/B/C result is measured.

## Result sheet

Common setup:

- Camera model/serial:
- Preview resolution/aspect/crop:
- Stabilization/digital zoom:
- Tripod screw:
- Carrier:
- Support attitude reference:
- Operator/date:

### A — 1 rib — setback 10 mm / bevel 35 deg

- CENTER intrusion:
- LEFT intrusion:
- RIGHT intrusion:
- mount play intrusion:
- return-to-seat repeatability:
- rain coverage visual:
- result: `PASS_CANDIDATE / FAIL_OPTICAL / HOLD`
- image/video evidence path:
- notes:

### B — 2 ribs — setback 15 mm / bevel 40 deg

- CENTER intrusion:
- LEFT intrusion:
- RIGHT intrusion:
- mount play intrusion:
- return-to-seat repeatability:
- rain coverage visual:
- result: `PASS_CANDIDATE / FAIL_OPTICAL / HOLD`
- image/video evidence path:
- notes:

### C — 3 ribs — setback 20 mm / bevel 45 deg

- CENTER intrusion:
- LEFT intrusion:
- RIGHT intrusion:
- mount play intrusion:
- return-to-seat repeatability:
- rain coverage visual:
- result: `PASS_CANDIDATE / FAIL_OPTICAL / HOLD`
- image/video evidence path:
- notes:

## Test-state separation

- CAD_PASS:
- PRINT_PENDING / printed:
- FIT_PENDING / checked:
- OPTICAL_PENDING / checked:
- RAIN_PENDING: `YES`
- FIELD_PENDING: `YES`
- RAIN_TEST: `NOT_TESTED`

Never infer `OPTICAL_PASS`, `RAIN_PASS`, or `FIELD_PASS` from CAD or a rain-coverage visual check.

