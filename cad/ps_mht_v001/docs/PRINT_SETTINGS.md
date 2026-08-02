# PS-MHT-V001 Print Settings

## Phase 1 printable part

| Part | Material | Quantity | Orientation | Supports | Status |
|---|---|---:|---|---|---|
| ps_mht_v001_planting_module_A | White PETG | 5 | Cylinder axis vertical; lower annular edge on bed | None expected | Geometry generated; physical print pending |

Initial slicer targets:

- Printer: Bambu Lab A1
- Nozzle: 0.4 mm
- Layer height: 0.20 mm initial
- Walls: use enough perimeters to realize the modeled 3.0 mm wall
- Top/bottom layers: slicer-dependent; shell is intentionally open in Phase 1
- Brim: evaluate for 200 mm circular footprint and PETG adhesion
- Color: white; do not use black PETG for the main shell
- Scale: 100%

The shell also supports later 0.6 mm-nozzle evaluation because its nominal wall
is 3.0 mm. Do not print five production shells before checking one Phase 1
dimensional sample and the Phase 2 coupons.

## Phase 2 mandatory first prints

| Order | Part | Material | Orientation | Supports |
|---:|---|---|---|---|
| 1 | module_interface_coupon | White PETG | Sector contact faces on bed | None |
| 2 | M4_insert_coupon | White PETG | Flat plate on bed | None |
| 3 | TPU_gasket_coupon fixture | White PETG | Flat plate on bed | None |
| 4 | module_body_roundness_coupon | White PETG | Ring axis vertical | None |

The groove fixture is PETG; fit it with purchased 3 mm TPU/EPDM cord or a
separately prepared TPU cord sample. Do not print the full
`planting_module_interface_phase2` for production until all four coupons pass.

The nut cartridge should be printed with its broad side on the bed and the
radial nut-feed opening horizontal. Print retainers flat. Their retention and
wash durability remain `CALIBRATION_PENDING`.

## Phase 3A mandatory calibration order

| Order | Part | Material | Orientation | Supports |
|---:|---|---|---|---|
| 1 | index_key_fit_coupon | White PETG | Contact sectors on bed | None |
| 2 | m4_cartridge_fit_coupon | White PETG | Blocks and loose parts flat | None |
| 3 | gasket_compression_leak_coupon | White PETG + purchased 3 mm EPDM cord | Arc faces on bed | None |
| 4 | netpot_adapter_coupon | White PETG | Adapter axes vertical | None |
| 5 | port_receiver_adapter_coupon | White PETG | Section faces on bed | None |
| 6 | angled_port_print_coupon | White PETG | Tower axis vertical | Evaluate without internal support |

The gasket coupon is a small-volume, non-pressurized leak fixture. Purchased
3 mm EPDM cord is the first candidate; printed TPU cord is comparison only.

Do not print
`ps_mht_v001_three_port_module_DO_NOT_PRINT_UNTIL_CALIBRATION_phase3a.stl`.
Approve purchased net-pot measurements, common-adapter fit, M3 hardware,
gasket, and angled underside first. The 170 mm full module is a provisional CAD
interference model, not a production print.

## Phase 3A.1 revised mandatory print order

| Order | Part | Material | Orientation | Supports |
|---:|---|---|---|---|
| 1 | index_key_fit_coupon | White PETG | Contact sectors on bed | None |
| 2 | m4_cartridge_fit_coupon | White PETG | Blocks and loose parts flat | None |
| 3 | gasket_compression_leak_coupon | White PETG + purchased 3 mm EPDM cord | Arc faces on bed | None |
| 4 | angled_port_print_coupon | White PETG | Tower axis vertical | Evaluate without internal support |
| 5 | m3_port_cartridge_fit_coupon_phase3a1 | White PETG | Receiver sections and all loose parts flat | None target |
| 6 | port_receiver_adapter_coupon_phase3a1 | White PETG | Section faces on bed | None |
| 7 | complete_port_passage_coupon_phase3a1 | White PETG | Component axes vertical | Minimum |
| 8 | root_ring_passage_coupon_phase3a1 | White PETG | Rings and gauges flat | None |
| 9 | netpot_adapter_coupon, after actual pot measurement | White PETG | Adapter axes vertical | None |

Print the M3 cartridge and rigid gate with their broad sides on the bed. Record
all results in `CALIBRATION.md` before Phase 3B. The complete-port assembly,
exploded assembly, passage probe and section are references, not printable
deliverables. The full module remains
`DO_NOT_PRINT_UNTIL_CALIBRATION`.

## Phase 3R large-part print order

Printer baseline: Bambu Lab A1, white PETG, 0.4 mm nozzle.

| Order | Part | Orientation | Status |
|---:|---|---|---|
| 1 | large_index_ring_coupon_phase3r | Both wave rings flat | Print |
| 2 | annular_nut_ring_coupon_phase3r | Flat, nut pockets up | Print |
| 3 | self_supporting_port_shell_coupon_phase3r | Shell axis vertical; nested function ring flat | Print |
| 4 | port_function_ring_coupon_phase3r | Both rings flat | `REFERENCE_PRELIMINARY`; defer until pot arrives if preferred |

The large rings require separate A1 jobs. The
`print_plate_layout_phase3r` file is a multi-plate orientation reference with
15 mm virtual-zone gaps, not one physical A1 print. Do not print the old key,
M3/M4 cartridge, L-gate or angled-port coupons again.

## Phase 3S-A split-shell calibration order

Printer baseline: Bambu Lab A1, white PETG, 0.4 mm nozzle. Use support-free
printing as the first candidate.

| Order | Plate | Quantity / action | Orientation |
|---:|---|---|---|
| 1 | plate_01_sector_seam_coupons_phase3sa.stl | One plate; test all three clearances | Both real-curvature seam pieces chord-rail down |
| 2 | plate_02_panel_capture_coupon_phase3sa.stl | Print once; repeat the full temporary ring when the fit passes | Ring flat; capture coupon flat |
| 3 | plate_03_sector_panel_single_phase3sa.stl | One full-height panel only | Assembly Z → print Y; radial outward → print Z; permanent rails on bed |
| 4 | plate_04_three_sector_short_parts_phase3sa.stl | Only after the single panel succeeds | Three identical 60 mm blank calibration panels, rail plane down |

Use a minimum 15 mm spacing between separate parts on multi-part plates.
Record the actual print height, first-layer rail continuity, warping, nozzle
contact, seam straightness and port-frame distortion. Do not print three
full-height panels until both the single-panel gate and short three-panel
assembly pass.

The temporary capture ring is flat printed and may be paired with a purchased
reusable external band. The external band is never exported as printable STL.
The full-height three-panel reference, exploded reference and any five-stage
tower are `DO_NOT_PRINT_AS_ASSEMBLY`.

## Phase 3S-A.1 selected-seam print workflow

`phase3sa_seam_clearance_selected` remains `None` until the physical seam
coupon test passes. Plate 02 through Plate 04 must be regenerated with one
explicit value from `0.4`, `0.6`, or `0.8` mm. Their file names contain
`c040`, `c060`, or `c080`; an unqualified Plate 02 through Plate 04 is not a
Phase 3S-A.1 print target.

| Order | Action | Quantity / gate |
|---:|---|---|
| 1 | `plate_01_sector_seam_coupons_phase3sa1.stl` | Print one plate |
| 2 | Select the seam clearance | Physical coupon pass required |
| 3 | Regenerate and print selected Plate 02 | One plate with explicit clearance |
| 4 | Print selected Plate 03 | Only after Plate 02 passes |
| 5 | Print `ps_mht_v001_temporary_panel_capture_ring_additional_phase3sa1.stl` | One additional ring, only after Plate 03 passes |
| 6 | Print selected Plate 04 | One plate |
| 7 | Build the short three-panel assembly | Plate 02 ring + additional ring = two rings |

Plate 02 contains one temporary capture ring. The short three-panel assembly
requires two identical temporary capture rings, so the additional standalone
ring STL has quantity one. The authoritative machine-readable quantities and
gates are in `print_manifest_phase3sa1.json`.

## Phase 3S-A.2 full-length seam calibration

The short coupons did not resolve full-length assembly force. c080 is rejected
for leakage and must not be reprinted. Print c040 and c060 at full 170 mm
length, with the real permanent rails down and no support as the first
candidate.

| Order | File | Quantity |
|---:|---|---:|
| 1 | `plate_01_full_length_seam_c040_phase3sa2.stl` | 1 |
| 2 | `plate_02_full_length_seam_c060_phase3sa2.stl` | 1 |
| 3 | `plate_03_full_length_seam_capture_fixtures_phase3sa2.stl` | 1 for sequential reuse; 2 for simultaneous c040/c060 tests |

The optional combined plate
`plate_optional_full_length_seam_c040_c060_phase3sa2.stl` replaces Plates 01
and 02 when the user prefers one four-part job. Plate 03 contains two identical
fixtures: one upper and one lower. Use four fixtures for simultaneous c040 and
c060 tests, or reuse two fixtures sequentially.

Follow the free-state, captured-state, ten-cycle, 24-hour and 500 mL water
procedures in `print_manifest_phase3sa2.json`. The combined assembly STEP is a
reference only and must not be sliced as one print.
