# BBOX TALL FIELD BODY V002 — fail-closed integration report

Final status: `TALL_BBOX_INTEGRATION_TRANSFORM_AND_FRAME_CONFLICT / RELEASE_CAD_WITHHELD / ZIP_WITHHELD`

The V002 top seal can be preserved exactly while extending its simple lower walls, and every requested height clears the GoldenMate terminal in local section analysis. None of the four variants passes the required installed-frame gate under the current Cross Saddle registration. In addition, the exact V002-body/V003-lid transform and the direct as-built Z148–254 record differ by 27.105 mm. No release STEP, STL, cradle, or ZIP was generated.

## Repository preflight

- Repository: `D:\Paddy_Swarm_Project`
- Branch: `agent/organize-untracked-cad-assets-20260725`
- HEAD: `7c149a65053f2292bc4cc0ed06d8941c96852f2b`
- Staged paths: `0`
- Tracked dirty paths: `4` (pre-existing and unchanged)
- Existing untracked files before this report: `4145`
- Existing-untracked aggregate SHA-256: `de4c9c4419721ca6538c13ad631d6f8afb92fd20ddbb089e39b66f4937e5b02b`

## Protected authorities

- Tested body: `bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8`
- Body STEP SHA-256: `9101bce93c2da8c1b9f87bfd38ae184451a7d1bfead4fb3a26ab9f8b36a176b9`
- Protected lid: `bbox_lid_wiring_chimney_v003_full_lid_2p4_authority`
- Lid STEP SHA-256: `11582cab5641591f385b521252fe2feeb3f43bba7ed0e72c3591c56bf5ab5c9c`
- GoldenMate source: `common_rover_electrical_hardware_physical_authority_v001`
- Current physical datum source: `common_rover_physical_dimensional_authority_2026_09_01_v001`
- Current integration convention: `cbox_transverse_cross_saddle_bbox_alignment_v001`
- Previous failure: `bbox_field_box_goldenmate_v001/BBOX_FIELD_BODY_CONFLICT_REPORT.md`

The previous `192 × 142 × 65 mm` usable cavity and GoldenMate `150.9 × 99.4 × 92.5 mm`, terminal-high `99.4 mm`, are retained without reinterpretation.

## Candidate construction audit

The analytical candidate generator used the exact V002 body above local `Z58` as an immutable Boolean source. Only the simple lower 4 mm walls and 5 mm floor were extended toward local `-Z`; no scaling was used.

For H108, H110, H112, and H116:

- upper-interface source volume: `70022.593646 mm^3`
- upper-interface candidate volume: `70022.593646 mm^3`
- mutual upper-interface volume: `70022.593646 mm^3`
- upper-interface symmetric delta: `0.0 mm^3`
- gasket interface delta: `0`
- M4 pattern delta: `0`
- hard-stop delta: `0`
- wall thickness: `4 mm`
- floor thickness: `5 mm`
- new penetration count: `0`

This proves that the local seal-preservation method is feasible; it does not resolve installed-coordinate conflicts.

## Height comparison

Installed bottoms below use the task's requested incremental convention:

`NEW_BOTTOM_Z = physical old bottom 148 - (H - 65)`.

Terminal clearances are `H - support - 99.4`.

| Variant | Support | Terminal/lid clearance | Battery-body/lid clearance | Installed bottom Z | Margin to frame-bottom Z64 | Print bbox Z | Added material | External core volume | Added displacement | Water depth at Z150 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H108 | 3 mm | 5.6 mm | 12.5 mm | 105 mm | 41 mm | 113.895 mm | 117648 mm^3 | 3.39 L | 1.29 L / ideal 1.29 kgf | 45 mm |
| H108 | 4 mm | 4.6 mm | 11.5 mm | 105 mm | 41 mm | 113.895 mm | 117648 mm^3 | 3.39 L | 1.29 L / ideal 1.29 kgf | 45 mm |
| H110 | 3 mm | 7.6 mm | 14.5 mm | 103 mm | 39 mm | 115.895 mm | 123120 mm^3 | 3.45 L | 1.35 L / ideal 1.35 kgf | 47 mm |
| H110 | 4 mm | 6.6 mm | 13.5 mm | 103 mm | 39 mm | 115.895 mm | 123120 mm^3 | 3.45 L | 1.35 L / ideal 1.35 kgf | 47 mm |
| H112 | 3 mm | 9.6 mm | 16.5 mm | 101 mm | 37 mm | 117.895 mm | 128592 mm^3 | 3.51 L | 1.41 L / ideal 1.41 kgf | 49 mm |
| H112 | 4 mm | 8.6 mm | 15.5 mm | 101 mm | 37 mm | 117.895 mm | 128592 mm^3 | 3.51 L | 1.41 L / ideal 1.41 kgf | 49 mm |
| H116 | 3 mm | 13.6 mm | 20.5 mm | 97 mm | 33 mm | 121.895 mm | 139536 mm^3 | 3.63 L | 1.53 L / ideal 1.53 kgf | 53 mm |
| H116 | 4 mm | 12.6 mm | 19.5 mm | 97 mm | 33 mm | 121.895 mm | 139536 mm^3 | 3.63 L | 1.53 L / ideal 1.53 kgf | 53 mm |

The approximate old external core displacement is `2.10 L`. Top lugs/flange/hard stops are unchanged and cancel in the added-displacement comparison.

Local packaging preference before frame checks would be H110 with a 4 mm support: it is the shortest candidate exceeding the preferred 6 mm terminal clearance. It is not selected because the installed-frame gate fails.

## Exact 3D collision audit

Registration convention:

- BBOX X/Y origin follows the current Cross Saddle reference, `(0, 0)`.
- incremental body-bottom placement follows the direct old bottom `Z148` record.
- frame core: `frame_170mm_core_reference_v0_9_6_6.step`
- current upper rails: Cross Saddle `current_upper_rails_physical_reference.step`
- front interface: `front_interface_dual_pto_20t_v002.step` (interface structure only; obsolete 500 mm frame/crawler assembly references excluded)
- crawler: Cross Saddle `crawler_reference.step`

| Variant | Narrow frame core intersection | Current upper rails intersection | Current front-interface intersection | Current crawler intersection | Result |
|---|---:|---:|---:|---:|---|
| H108 | 0 mm^3 | 0 mm^3 | 7860.074623 mm^3 | 0 mm^3 | FAIL |
| H110 | 0 mm^3 | 0 mm^3 | 14309.012693 mm^3 | 0 mm^3 | FAIL |
| H112 | 0 mm^3 | 0 mm^3 | 27206.888834 mm^3 | 0 mm^3 | FAIL |
| H116 | 12000.0 mm^3 | 0 mm^3 | 40726.888834 mm^3 | 0 mm^3 | FAIL |

H108 already intersects the current upper unit-mount crossrail and its upper fastener references. H116 additionally intersects the 170 mm narrow-frame core. Z-overlap alone was not used for the crawler result; actual 3D intersection is zero for all four.

Moving the BBOX in X/Y could change these results, but current physical authority supplies no direct BBOX X/Y center or BBOX-to-front-interface transform. Relocating it to force a PASS would be an invented placement and could invalidate the protected CBOX/Cross Saddle architecture.

## Installed-Z transform conflict

The existing exact source relationship is:

- V002 body hard-stop top: local `Z70.895`
- V003 lid underside: local `Z0`
- Cross Saddle maps V003 lid plate top local `Z8` to physical `Z254`, so lid underside is physical `Z246`
- this exact source relationship maps the old V002 body bottom to `Z175.105`

The direct as-built authority instead records old body bottom `Z148`.

Difference:

`175.105 - 148 = 27.105 mm`.

Both records are retained. The prompt's incremental bottom convention was used conservatively for collision checks, but a release assembly cannot simultaneously claim the exact V002/V003 mating transform and the unresolved Z148–254 span without a physical datum reconciliation.

## Fail-closed decision

No height variant clears every required frame component. The installed transform is also not uniquely closed. Therefore:

- selected height: none
- selected cradle: none
- strap interface: not released
- TPU candidate: not selected
- cable/strain relief: not released
- service-hardware zone: not released
- printable parts: 0
- release STEP/STL: 0
- ZIP: not generated
- CBOX/Cross Saddle: unchanged
- V003 lid/chimney: unchanged

## Required next measurements/authority

1. Measure BBOX center or two locating faces in X and Y relative to the current frame/front-interface datum.
2. Identify whether the current upper unit-mount crossrail is installed, planned, or superseded.
3. Reconcile the exact V002 hard-stop-to-V003-lid underside datum with direct body-bottom `Z148` and lid plate-top `Z254` measurements.
4. If relocation is intended, explicitly authorize the BBOX X/Y transform and re-check Cross Saddle/CBOX service.
5. Only after those are closed, rerun H108/H110/H112/H116 and select the shortest passing body.

New tall-body waterproof qualification, slicer review, cradle physical fit, strap/TPU selection, cable bend/retention, battery vibration, tilt, water, mud, powered, and field tests all remain pending.

Final status: `TALL_BBOX_INTEGRATION_TRANSFORM_AND_FRAME_CONFLICT / RELEASE_CAD_WITHHELD / ZIP_WITHHELD`
