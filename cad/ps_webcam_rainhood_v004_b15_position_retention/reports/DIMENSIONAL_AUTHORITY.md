# DIMENSIONAL AUTHORITY

## v002 source

- Commit: `17a703694d5b2e127b5f7bccf8bfe3c5f1f0f2b9`
- Source: `cad/ps_webcam_rainhood_v002_tripod_mount/cad/ps_webcam_rainhood_v002.py`
- Blob: `43cd3b5197be19add694b078bd655b0c3a8c75d8`

## v003 local authority hashes

- Source SHA256: `0077640c864f09080b51ecd23b1ecd6bfcce88f14e1fdda818f94cf0fcc49b15`
- Validation JSON SHA256: `72ef6d68c5be0cb3427aa51b0b166d5150814bea12ebfc1d65a6cd12db9c9473`
- B STL SHA256: `0bab2bbba49622ba3aadc0f0579259bc3029595b20e84506aac6c734bdf8703a`

## Fixed v002 dimensions

| Datum | Value |
|---|---:|
| Camera W/H/D | 101.5 / 35.5 / 34.0 mm |
| Folded clip W | 49.2 mm |
| Folded clip below body | 17.2 mm |
| Folded depth measured / safe | 52.2 / 56.4 mm |
| Tripod X from left | 50.9 mm |
| Tripod Y from front/rear | 30.4 / 26.0 mm |
| Tripod axis X/Y | 0.15 / 0.0 mm |
| Thread-hole depth | 4.8 mm |
| Carrier W/D/T | 110.8 / 74 / 6 mm |
| Hood outer/inner/wall | 118 / 112 / 3 mm |
| Top clearance | 4 mm |
| Guide clearance/height | 0.7 / 2.8 mm |
| USB cable/channel | 3.6 / 6 mm |
| Shell M4 centers | X=±44, Y=33 mm |

Tripod thread assumption: 1/4-20 UNC. Candidate screw length 3/8 inch gives calculated insertion 3.525 mm and calculated bottom clearance 1.275 mm. `TRIPOD_THREAD_PHYSICAL = PENDING` unless separately verified.

## Selected B dimensions

- setback: 15.0 mm from v002 front;
- front Y: -45.4 mm;
- bevel: 40 degrees;
- bevel run: 2.080 mm;
- front length: 15.0 mm.

## v004 controlled delta

- Side guides extend from 44.0 to 52.4 mm.
- Inner X clearance stays 0.7 mm.
- Height stays 2.8 mm.
- Low outward foot and two front corner/yaw stops are additions only.
- Existing rear stops are unchanged.
- v002 carrier geometry removed by CAD comparison: 0 mm³.
- Tripod axis/hole, carrier seating plane, adapter holes, shell M4 holes, USB cut, hood rails/stops/nut traps remain unchanged.

Any required change to those fixed interfaces must be reported as `INTERFACE_CHANGE_REQUIRED` rather than silently applied.

