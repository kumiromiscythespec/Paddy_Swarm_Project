# Dummy Panicle Head v0.1

This CadQuery package retains the v0.1.2 interface/calibration parts and adds
the panicle head only:

- DR-H01 — flat TPU 95A branch panel
- DR-H02 — PETG four-panel hub (`upright` and fixed `droop20`)
- DR-H03 — PETG removable weight-pocket cap
- non-printable upright and droop20 panicle-only STEP previews

It does not implement a full 900 mm plant, test stand, multi-plant layout,
blade, rover change, or powered-cutting system.

**Powered cutting is not authorized.  Never bring the TPU branch panels or the
PETG marking gauge into contact with, or near, a rotating blade.**

## Runtime

The checked environment is Python 3.12 with CadQuery 2.8.0:

```powershell
& 'C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe' `
  cad\dummy_panicle_v0_1\generate_dummy_panicle_v0_1.py

& 'C:\Users\yu_ki\Miniforge\envs\paddy-cad\python.exe' -m unittest discover `
  -s cad\dummy_panicle_v0_1\tests -v
```

Importing a module does not export files.  The generator writes printable
files by material:

```text
out/
├─ step/
│  ├─ TPU/
│  └─ PETG/
├─ stl/
│  ├─ TPU/
│  └─ PETG/
├─ preview/       # STEP only; not printable
└─ reports/
```

Every printable filename ends in `_TPU` or `_PETG`.

## Head composition and print quantities

| Part | Material | Assembly qty | Recommended print qty | Purpose |
|---|---|---:|---:|---|
| DR-H01 standard | TPU 95A | 4 | 6 | 10-branch/14-grain flexible panel |
| DR-H02 upright | PETG | 1 | 1 | Fixed 0-degree four-slot hub |
| DR-H02 droop20 | PETG | 1 | 1 | Fixed 20-degree four-slot hub |
| DR-H03 | PETG | 1 | 2 | Removable mass-pocket cap plus spare |

Use only one DR-H02 preset per assembly.  The preview adds a simple 4 mm stem
only to check orientation and dimensions; it is not the full dummy panicle and
must not be sliced as a print part.

## Calibration-first assembly

`PANICLE-TAB-V001` remains `CALIBRATION_PENDING`: TPU tab
8.0 x 2.0 x 14 mm and PETG slot 8.4 x 2.4 x 12 mm are provisional.  No saved
successful print-fit result was found, so retention is not guaranteed.

1. Print only one DR-H01 panel first.
2. Check the tab with the slot coupon and one hub, without forcing it.
3. Record printer, material, measured tab/slot dimensions, insertion force,
   pull force, and visible damage.
4. Print the remaining panels only after selecting a calibrated fit.

DR-H03 likewise uses an unverified 0.20 mm diametral bead-interference
candidate.  Verify that it can be removed and survives a hand shake test.
Secure metal washers or nuts so they cannot move or escape.  Do not treat the
cap as retained until printed testing confirms it.

The DR-H02 stem receiver is a provisional 4.3 mm hole for a 4.0 mm shaft.
Use one M3 bolt/nut in the split clamp and avoid over-tightening, especially
with paper tube.  The hub has no moving hinge: `droop20` tilts the entire head
through a fixed stem interface.

## Mass status

The 4–6 g head target must be judged from a real printed head.  Reports include
CAD volume and estimates using separately configured provisional density
values, but those estimates are not measured mass and are not acceptance
evidence.  Weigh DR-H01 x4, the selected DR-H02, DR-H03, and any metal contents
separately and together; record centre of gravity as well.

## Existing interface parts retained

The generator still creates the material-classified stem clearance coupon,
TPU tab coupon, PETG slot coupon, DR-B01 root socket, DR-S03
`tube_id_3p6_calibration` plug, two DR-C01 holders, and the DR-C01 paper-tube
marking gauge.

The DR-C01 cartridge remains 170 mm:

```text
2 x 15 mm holder insertion
+ 2 x 30 mm from the cartridge-side PETG holder face nearest the nominal zone
+ 80 mm central nominal zone
= 170 mm
```

The 4.10 mm cartridge bore and 4.30 mm stem bore are calibration candidates;
they do not guarantee retention.  DR-S03's unmeasured 3.6 mm tube-ID candidate
is not guaranteed to use the same material or stock as the DR-C01 nominal
4.0 mm OD / 2.5 mm ID paper tube.

Use the removable PETG gauge only to draw lines directly on paper tube, or for
non-cutting bench visualization, then remove it.  The gauge is prohibited for
powered cutting and must never be left near a blade.

Python caches are not deliverables.  Repository ignore rules exclude
`__pycache__/` and `*.pyc`.
