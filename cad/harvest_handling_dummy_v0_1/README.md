# PS-HARVEST-HANDLING-DUMMY-V001

Version: `v0.1.0-fixed-root-layout`
Internal code: `HHD-V001`

This independent CadQuery package models a repeatable 24-stem fixed-root bench
dummy for evaluating gathering, holding, and transport behaviour.  It represents
dense roots and independently tilted, directed, and height-classified stems.

It is not the CUT-DUMMY in `cad/dummy_panicle_v0_1`, does not import from that
package, and does not share its interfaces or outputs.  Normal HHD generation
does not locate, hash, or require CUT-DUMMY.  It succeeds when CUT-DUMMY is
absent, independently revised, or when this HHD package is copied by itself.

## Scope and safety boundary

This revision contains:

- four six-socket base modules;
- two workbench mount halves;
- fixed 0/10/20/30-degree indexed sockets;
- five commercial-rod plug candidates;
- fit coupons, flat angle gauge, generic height markers, and layout plates;
- one authoritative fixed S01-S24 CSV/JSON layout;
- a non-printable 24-stem STEP preview.

It contains no release mechanism, flexible socket, leaf, panicle, guide, belt,
roller, blade, motor, sensor, electrical system, or autonomous control.

**Powered cutting is not authorized.  This is a fixed-root handling bench
dummy only.**

## Runtime

Validated environment:

- Python 3.12
- CadQuery 2.8.0
- Bambu Lab A1 printable-parts envelope: 240 × 240 × 220 mm
- 0.4 mm nozzle, 0.20 mm layer, PETG minimum wall 2.0 mm

Generate outputs:

```powershell
& 'C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe' `
  cad\harvest_handling_dummy_v0_1\generate_harvest_handling_dummy_v0_1.py
```

Run tests:

```powershell
& 'C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe' -m unittest discover `
  -s cad\harvest_handling_dummy_v0_1\tests -v
```

Importing modules never exports files.

### Optional CUT-DUMMY development audit

CUT-DUMMY protection is separate from normal generation and normal HHD tests.
Run it only when an explicit repository-development audit is wanted:

```powershell
& 'C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe' `
  cad\harvest_handling_dummy_v0_1\audit_protected_dummy.py `
  cad\dummy_panicle_v0_1 `
  --report cad\harvest_handling_dummy_v0_1\out\reports\audit\protected_dummy_panicle_hashes.json
```

The optional audit uses individual relative-path SHA-256 comparisons as its
pass/fail basis.  Its aggregate SHA-256 is diagnostic only.  A missing
CUT-DUMMY directory raises `FileNotFoundError` only when this audit is
explicitly invoked.  Neither the audit nor its report is part of
`generate_all()` or `export_manifest.csv`.

## Output structure

```text
out/
├─ step/PETG/
├─ stl/PETG/
├─ preview/
└─ reports/
```

Every printable filename ends in `_PETG`.  Purchased simulated stems are not
STL parts.  `HU-H0-HHD_standard_fixed_root.step` is a non-printable assembly
preview and has no STL.

## CALIBRATION_PENDING

`CALIBRATION_PENDING` means that nominal CAD clearances exist but printed
insertion force, pull force, repeatability, wear, fracture, and material
damage have not been measured.  It never means proven retention.

Provisional connections:

- `BASE-SOCKET-IF-V001`: Ø12.8 shank in Ø13.2 receiver, 16.0/16.4 mm
  octagonal index, 12 mm insertion, and 0.25 mm standard shallow-bead candidate.
- `HHD-STEM-PLUG-V001`: Ø6.0 common shank in provisional Ø6.25 receiver,
  18 mm insertion.
- Commercial-rod adapters: 2/3/4/5 mm presets plus a solid custom blank.
  No dry-rice-straw-specific plug is supplied because no measured straw data
  exists.

## Mandatory initial print order

1. `HU-H0-HHD-CPN-SOCKET-LOCK_PETG`
2. `HU-H0-HHD-CPN-STEM-PLUG-FIT_PETG`
3. `HU-H0-HHD-GAG-ANGLE_PETG`
4. `HU-H0-HHD-BAS-A_PETG`
5. One each of the 0/10/20/30-degree sockets
6. Two or three stem-plug presets
7. Six fixed roots using BASE-A only
8. BASE-B through D only if the six-root test succeeds
9. Remaining sockets
10. The full 24-root standard layout

Do not batch-print 24 or more sockets before calibration.

## Standard assembly

- BASE-A: S01-S06
- BASE-B: S07-S12
- BASE-C: S13-S18
- BASE-D: S19-S24
- Tilt quantities: 0° ×8, 10° ×8, 20° ×6, 30° ×2
- Direction quantities: each of 0/45/90/135/180/225/270/315° ×3
- Virtual heights: LOW 650 mm ×8, STANDARD 750 mm ×10, HIGH 850 mm ×6

Each stem has its own socket.  S01-S24 are never merged into a common thick
bundle or hub.  The base fixes the roots; after a handling force is removed,
the purchased stem material—not a CAD release mechanism—determines recovery.

## Authoritative layout

`out/reports/layout_standard_v001.csv` and `.json` are the design authority.
They record:

- socket ID and base module;
- X/Y coordinate;
- fixed tilt and eight-direction index;
- height class;
- `UNASSIGNED` stem class;
- `NONE` pre-bend, panicle, and leaf state;
- fixed release group.

MAP-A through MAP-D are removable transfer aids only.  They are not the sole
source of layout truth.

## Assembly summary

1. Join left and right mounts using the printed tongue/pocket seam.
2. Fix the mount to the bench through four M6 holes.
3. Register BASE-A through D on the mount pins.
4. Install four M4 fixings per module.
5. Check the physical locations with MAP-A through D.
6. Select socket tilt and rotate its octagonal index to the CSV/JSON direction.
7. Fit a calibrated common-shank plug and purchased simulated-stem material.
8. Set LOW/STANDARD/HIGH length with a purchased ruler/stick and generic marker.
9. Recheck every S01-S24 row before the handling test.
10. Inspect split sections, beads, bolts, keys, and stem damage after testing.

The nominal mount plates are 105 × 210 × 6 mm.  Their complete feature
envelopes are 110 × 210 × 9 mm on the tongue side and 105 × 210 × 9 mm on the
pocket side because of the seam tongue and 3 mm locating pins.  The joined
footprint remains 210 × 210 mm and both parts remain inside the A1 envelope.

Detailed steps are generated in
`out/reports/print_assembly_guide.md`.

## Limitations

- Root release is not implemented.
- Leaves and drooping panicles are not implemented.
- Commercial stem material, diameter, stiffness, damping, and surface finish
  must be selected and measured separately.
- The preview may exceed A1 dimensions because it is not printable.
- This package does not change any rover, PTO, harvest tool, or CUT-DUMMY.
