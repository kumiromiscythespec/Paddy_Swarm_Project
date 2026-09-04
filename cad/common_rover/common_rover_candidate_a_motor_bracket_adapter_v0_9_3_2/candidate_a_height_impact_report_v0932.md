# Candidate A height impact v0.9.3.2

The 8.0 mm adapter raises the existing metal bracket and motor if the 2040 frame datum is unchanged.

- adapter stack increase: +8.0 mm
- old Candidate A motor front-plate Z: 105.0 mm
- new local candidate: 113.0 mm
- motor-mounted 20T axis candidate: +8.0 mm, 105.0 → 113.0 mm
- 60T axis: not automatically moved; retaining Z=166 changes belt center geometry. A +8 mm alternative to Z=174 is a revalidation candidate only.
- belt plane: axial coplanarity is not released; path angle, center distance, belt length, and guard clearance require revalidation.
- selector shaft: remains Z=166 unless a later integration task moves it; Z=174 is not adopted here.
- motor guard: motor-relative guard rises +8.0 mm and requires physical confirmation.
- total rover height: cannot be increased automatically because the current controlling highest envelope must be recomputed.

`INTEGRATION_STATUS=HEIGHT_REVALIDATION_REQUIRED`. Candidate A authority and parent geometry are unchanged.
