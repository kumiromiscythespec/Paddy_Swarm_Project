# BBOX FIELD BOX V001 — fail-closed body-fit report

Status: `BBOX_FIELD_BODY_REDESIGN_REQUIRED`

No release CAD, printable STL, cradle, placement variant, or handoff ZIP was generated. The exact physically tested shell is uniquely traceable, but the GoldenMate battery cannot fit it without changing protected waterproof body geometry.

## Repository preflight

- Repository: `D:\Paddy_Swarm_Project`
- Branch: `agent/organize-untracked-cad-assets-20260725`
- HEAD: `7c149a65053f2292bc4cc0ed06d8941c96852f2b`
- Staged paths: `0`
- Tracked dirty paths: `4` (pre-existing; not modified)
- Existing untracked files before this report: `4144`
- Existing-untracked aggregate SHA-256: `98ac93a62959d7abdeb28111a272210493270db61248e3200722546d3fde31ec`

## Unique physical-body authority trace

The successful physical record is:

`cad/common_rover/bbox_lid_wiring_chimney_v001_above_water_gland/PHYSICAL_MEASUREMENTS.md`

It records `bbox shell WATER_PASS_OBSERVED`, rubber-cord gasket `WATER_PASS_OBSERVED`, screw/nut compression `WATER_PASS_OBSERVED`, and submerged tilt greater than 10 degrees `NO_LEAK_OBSERVED`.

The same lane's builder fixes:

- parent lane: `cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8`
- imported body: `v002.body_shape()`
- lid assembly datum: `Z = 70.895 mm`

Therefore the uniquely traceable tested body source is:

`cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8/artifacts/bbox_water_dummy_v002_body.step`

Body STEP SHA-256:

`9101bce93c2da8c1b9f87bfd38ae184451a7d1bfead4fb3a26ab9f8b36a176b9`

Supporting source hashes:

- physical measurements: `623428125a4da421d3818523019be951283eb804ed9b8aa8fb3134b2a8c45b2d`
- physical-record builder: `2b21d2c0e14d1959708b89a7dfc4ad4f0b8782c5714be18f3b7b4276cf74a34f`
- V002 body builder: `4eedbafc3c3ae4454f7af5e187764889a9ce44cba2fe91b857d7e672aee741eb`

The selected protected lid/chimney authority is:

`cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority/cad/bbox_lid_wiring_chimney_v003_local_wall_2p4.step`

Lid STEP SHA-256:

`11582cab5641591f385b521252fe2feeb3f43bba7ed0e72c3591c56bf5ab5c9c`

## Exact protected geometry audit

CadQuery 2.8.0 reloaded both STEP files as one valid solid each.

Tested V002 body:

- exact STEP bounds including external M4 lugs/hard stops: `240 × 190 × 70.895 mm`
- sealed core outside: `200 × 150 × 70 mm`
- wall: `4 mm`
- floor: `5 mm`
- internal cavity/opening: `192 × 142 mm`
- dry cavity height below the sealing plane: `65.000 mm`
- internal screw-column intrusion: `0` (M4 system is external to the sealed cavity)

Protected V003 lid/chimney:

- exact STEP bounds: `240 × 190 × 58 mm`
- assembled lid underside: `Z = 70.895 mm`
- floor-top to lid-underside geometric distance: `65.895 mm`
- protected gasket/hard-stop gap within that distance: `0.895 mm`

The `0.895 mm` gasket/hard-stop separation is not allocated as battery space. The governing content height below the sealing plane is therefore `65.000 mm`.

## GoldenMate authority

Source:

`cad/common_rover/physical_authority/common_rover_electrical_hardware_physical_authority_v001/electrical_hardware_authority.json`

Source SHA-256:

`79a008aa6339b3a2a1e9d4ccd071f0a485cabdc0476a7dfddc527b20306a903e`

Applied physical values:

- battery body: `150.9 × 99.4 × 92.5 mm`
- mass: `1.2 kg`
- male tab: `6.3 × 0.7 mm`
- female receptacle outer width: `10.6 mm`
- battery bottom to terminal highest point: `99.4 mm`
- terminal XY: `PHYSICAL_PENDING`

The historical `108 mm` passage result was not treated as battery height.

## Orientation results

### Orientation A — 150.9 mm along BBOX 192 mm direction

Plan fit without a cradle:

- X clearance: `(192 - 150.9) / 2 = 20.55 mm/side`
- Y clearance: `(142 - 99.4) / 2 = 21.30 mm/side`

Vertical failure:

- battery body shortage to sealing plane: `92.5 - 65.0 = 27.5 mm`
- terminal-high shortage to sealing plane: `99.4 - 65.0 = 34.4 mm`
- battery body shortage to lid underside: `26.605 mm`
- terminal-high shortage to lid underside: `33.505 mm`
- exact centered battery-body/lid intersection: `118438.768 mm^3`
- conservative terminal-high-envelope/lid intersection: `121375.408 mm^3`

Result: `FAIL_BATTERY_AND_TERMINAL_TO_PROTECTED_LID`.

All rigid-clearance candidates still pass plan fit but cannot repair the vertical failure:

| Nominal clearance per side | Required cradle battery pocket XY | Remaining cavity clearance X/Y per side |
|---:|---:|---:|
| 0.8 mm | 152.5 × 101.0 mm | 19.75 / 20.50 mm |
| 1.2 mm | 153.3 × 101.8 mm | 19.35 / 20.10 mm |
| 1.6 mm | 154.1 × 102.6 mm | 18.95 / 19.70 mm |

Any cradle floor, TPU pad, keeper, or strap adds vertical stack and worsens the failure.

### Orientation B — 150.9 mm rotated 90 degrees

Plan fit without a cradle:

- X clearance: `(192 - 99.4) / 2 = 46.30 mm/side`
- Y clearance: `(142 - 150.9) / 2 = -4.45 mm/side`
- total Y shortage: `8.9 mm` before any rigid clearance
- exact centered battery-body/body-solid intersection: `52617.642 mm^3`
- exact centered battery-body/lid intersection: `120885.105295 mm^3`

Result: `FAIL_BODY_WALL_AND_PROTECTED_LID`.

## Fail-closed decision

No orientation passes the exact protected shell/lid pair before adding a cradle. Consequently:

- placement Variants A/B/C were not promoted
- no rigid-clearance winner was selected
- no TPU pad was selected
- no restraint architecture was released
- no cable route or strain-relief geometry was released
- no service-hardware reserved zone was released
- no printable part was generated
- no contract/reproducibility release run was performed
- no ZIP was generated

The minimum body-height change just to reach zero terminal clearance below the existing sealing plane is `+34.4 mm`. A real redesign would require more than this because positive terminal-to-lid clearance, cradle-floor thickness, restraint clearance, print tolerance, and cable service space must also be added. Such a change violates `BBOX_EXTERNAL_SHELL_DELTA = 0` and is not authorized in this task.

## Installation-reference conflict retained

The current physical dimensional authority records BBOX body lowest `Z148`, lid highest `Z254`, and an installed span of `106 mm`. The exact protected V002-body plus V003-lid/chimney STEP pair spans `128.895 mm` from body bottom to chimney top in its source assembly datum. These values were not silently reconciled. The `106 mm` as-built datum is retained as a separate placement record and cannot override exact source geometry for the fit calculation.

## Protected start hashes

Tree-hash method: sorted relative path, LF, file SHA-256, LF; cache/pyc excluded.

| Protected lane | Files | Tree SHA-256 |
|---|---:|---|
| `bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8` | 37 | `ddc50160ccd29a3c106f74c5d8625bde8d3bb4f1b4eb9adcb7c37efa4a1c24ab` |
| `bbox_lid_wiring_chimney_v003_full_lid_2p4_authority` | 18 | `253647717f05ed47329301b784a8247a41f6faa70d17411e05f990c4db305563` |
| `common_rover_electrical_hardware_physical_authority_v001` | 11 | `399696652b73ee5069d086d21987223c8058f0e203e9b3062cda744bea613724` |
| `common_rover_physical_dimensional_authority_2026_09_01_v001` | 15 | `9ff7d7fba15ce534fcaa03ae8f26a2baf6a19b8f7d6c690264c5df778ce95bef` |
| `cbox_transverse_cross_saddle_bbox_alignment_v001` | 45 | `9f05064864ceaf097f6e8380ebd25c1c316ff28fddad51b60b490a4613dc1c5e` |

End hashes must match these values exactly.

## Required next authority

A future task must explicitly authorize a new taller body (or a different uniquely identified physical BBOX body) and then repeat empty-shell waterproof validation. The tested V002 body, V003 lid/chimney, gasket path, M4 pattern, and CBOX Cross Saddle remain read-only in this task.

Final status: `BBOX_FIELD_BODY_REDESIGN_REQUIRED / RELEASE_CAD_WITHHELD / ZIP_WITHHELD`
