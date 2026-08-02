# Paddy Swarm Modular Herb Tower — PS-MHT-V001

This folder contains the parametric CadQuery implementation of the modular
herb tower. Current implementation status: **Phase 3A.1 correction CAD
complete; physical calibration pending**.

## Phase 1 scope

- Centralized fixed and provisional parameters
- Simplified purchased 2020 aluminium base and 1250 mm rear post
- One printable open PETG module shell
- Five individually placed module solids at alternating 0/60-degree rotations
- Non-printable drain-base and irrigation-top envelope references
- Nominal 1090 mm tower and 450 x 450 mm frame assembly
- Bambu Lab A1 bounding-box, solid-validity, and STEP round-trip checks
- STEP, STL, and SVG generation

The drain-base and irrigation-top cylinders in the Phase 1 assembly are
**REFERENCE_ENVELOPE_ONLY**. They are not printable parts and do not claim
drainage, water-tightness, or production readiness. Planting ports begin in
Phase 3; module keys, M4 fixings, and gaskets begin in Phase 2.

## Environment

Validated with CadQuery 2.8.0:

```powershell
C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe `
  cad\ps_mht_v001\build_phase1.py
```

Run tests from the repository root:

```powershell
C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe -m pytest `
  cad\ps_mht_v001\tests -q
```

Generated artifacts are written under `exports/step`, `exports/stl`, and
`exports/preview`. The only Phase 1 printable output is
`ps_mht_v001_planting_module_A.stl`; quantity is five.

## Coordinate system

- Tower axis: X=0, Y=0
- Rear: +Y
- Support plane / tower bottom: Z=0
- 2020 base members: Z=-20 to 0
- Rear post: Y=150, Z=0 to 1250
- Drain-base envelope: Z=0 to 140
- Modules 01–05: Z=140 to 990
- Irrigation-top envelope: Z=990 to 1090

The simplified rear post leaves 40 mm to the 200 mm body and 20 mm to the
future 240 mm maximum tower envelope. Future clamp geometry bridges the body
gap in Phase 6.

The height authority is:

`tower_nominal_height = drain_base_height + module_count * module_height + irrigation_top_height`

## Phase 2 scope

- External 194 mm-ID spigot/socket interface with 0.4 mm/side clearance
- Six robust 60-degree index keys and matching socket reliefs
- Six available M4 stations at 30/90/150/210/270/330 degrees
- Three normal-use M4 knobs at 30/150/270 degrees
- Replaceable side-load M4 nut cartridge and external slide-gate retainer
- Radial 3 mm TPU/EPDM cord groove and 6.6 mm hard contact stop
- 0-degree, 60-degree, exploded, section, and keep-out references
- Four calibration coupons

Generate Phase 2 without overwriting Phase 1:

```powershell
C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe `
  cad\ps_mht_v001\build_phase2.py
```

The full 170 mm module remains **DO_NOT_PRINT_FOR_PRODUCTION** until the four
Phase 2 coupons have been printed, measured, and recorded. The φ60 planting
ports, drainage, irrigation, support clamps, and chain are keep-outs only.

## Phase 3A scope

- Exactly three integrated 27-degree ports at local 0/120/240 degrees
- One reusable module alternated by a 60-degree whole-part rotation
- Keyed φ72 common receiver, generic carrier, nominal-60 insert, blank cap,
  TPU/EPDM gasket, and the historical annular two-M3 retainer
- Purchased net-pot and PP/PE root-sleeve STEP references (no reference STL)
- Root retaining ring and optional perforated root-stop insert
- 0/60-degree 130 mm external service sweeps
- Six mandatory calibration coupon families and strengthened Phase 2 coupons
- Actual wall probes, radial search, STEP re-import, and STL manifold checks

Generate Phase 3A without overwriting Phase 1 or Phase 2:

```powershell
C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe `
  cad\ps_mht_v001\build_phase3a.py
```

The full module output is explicitly named
`DO_NOT_PRINT_UNTIL_CALIBRATION`. Print the six coupons in the documented
order; do not print the 170 mm module before measuring the purchased pot and
approving the keyed receiver, M3 retention, gasket, and angled underside.

## Phase 3A.1 correction scope

- Corrected annular common-adapter flange with a continuous φ66 passage
- Actual one-axis receiver-to-tower passage and interference model
- Two independent, externally replaceable M3 nut cartridges and rigid gates
- Deprecated Phase 3A annular M3 retainer retained for reproducibility only
- Tab-inclusive root-ring clearances of 0.35/0.50/0.70 mm per side
- Root ring at the inner-end datum, captive in the removable sleeve fold
- Tool-free, gravity-seated nominal-60 net-pot replacement liner
- Four Phase 3A.1 calibration coupons and immutable Phase 1–3A hash gates

Generate Phase 3A.1 without overwriting Phase 1, Phase 2, or Phase 3A:

```powershell
C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe `
  cad\ps_mht_v001\build_phase3a1.py
```

The complete and exploded planting-port STEP files are assembly references,
not print plates. The full module remains
**DO_NOT_PRINT_UNTIL_CALIBRATION**.

## Phase 3R — circular integration after physical print failure

Physical A1 prints rejected the old thin keys, small M3/M4 cartridges,
L-gates and integrated angled circular receiver. They remain in source and in
immutable Phase 2–3A.1 outputs, but are
`DO_NOT_REPRINT_DEPRECATED_AFTER_PHYSICAL_FAILURE`.

Phase 3R uses:

- a flat continuous six-lobe module alignment ring;
- 220 mm annular M4 nut and clamping rings;
- commercial washers or a metal plate instead of printed micro-gates;
- a 45-degree self-supporting teardrop shell opening;
- a separate flat circular planting-port function ring and replaceable liner;
- a large internally serviced backing C-ring;
- a continuous flat root-mesh foldover ring.

Generate Phase 3R without overwriting Phase 1 through Phase 3A.1:

```powershell
C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe `
  cad\ps_mht_v001\build_phase3r.py
```

Only the four Phase 3R coupon families are print candidates. The full 170 mm
module remains `DO_NOT_PRINT_UNTIL_PHASE3R_PHYSICAL_CALIBRATION`.
