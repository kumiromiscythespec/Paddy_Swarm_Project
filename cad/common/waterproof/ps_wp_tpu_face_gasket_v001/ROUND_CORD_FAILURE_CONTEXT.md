# Round-cord failure context — read-only history

Latest user physical update is recorded HERE only; no old lane is rewritten.

- G065 small closed dummy: ROUND_CORD_SMALL_DUMMY = PASS. Its previous successful water test is NOT revoked.
- Full BBOX V004: ROUND_CORD_FULL_BBOX_LONG_DURATION = FAIL. Temporary exposure passed, but the cumulative 60-minute full-box test developed gradual ingress.
- FAILURE_MODE = UNRESOLVED_SLOW_INGRESS. Exact entry location/cause is not proven. Do not blame the joint, chimney, PETG porosity or groove as an established cause.
- Old round rubber: user identified EPDM, nominal diameter3 mm; later light-caliper measurement approximately3.4 mm. Historical1.8 mm labels are NOT current physical rubber authority.

Read-only source review:

1. `cad/common_rover/bbox/bbox_compact_seal_b_water_dummy_v001`: records the G055/G065 actual-depth correction; later user G065 water PASS remains valid for that specimen.
2. `cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065`: its CAD-era record still says full-box water pending; the newer user60-minute FAIL supersedes that status in this delta record, without patching the protected package.
3. `cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8`: external vertical M4 architecture isolated intentional screw-hole water paths; its old material labels are historical, not new TPU inputs.
4. `cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority`:2.4 mm local-wall coupon selection; full-lid/gland water performance cannot be inferred from that local fit.

The TPU geometry is independent from ALL round-cord diameters. A one-piece loop removes the deliberate butt joint, but printed TPU waterproofing is still unproven. Neither the old small-dummy PASS nor a future common-dummy PASS qualifies BBOX/CBOX automatically.
