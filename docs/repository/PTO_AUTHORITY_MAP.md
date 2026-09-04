# PTO authority map

## Decision summary

The PTO output-direction conflict is closed by the scoped 2026-09-05 physical
authority. The current as-built direction is PTO-L `-X` outward and PTO-R `+X`
outward. The two outputs, support arrangements and torque paths remain
independent, and a common PTO shaft remains prohibited.

This is direction-only physical authority. Final output-shaft length and
projection, powered behavior, torque capacity, retention and field
configuration remain HOLD.

## Required authority fields

| Field | Repository finding |
|---|---|
| Authority name | `PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY_2026_09_05_V001`; current physical pulley envelope: `PTO_20T_OD10_PHYSICAL_ENVELOPE_V001`; preserved base design lineage: `common_rover_inward_pto_coupling_cad_verified_v0_9_2_1` |
| Authority path | [direction physical authority](../../cad/common_rover/pto/physical_authority/pto_outward_direction_physical_authority_2026_09_05_v001/PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY_2026_09_05.md); [`../../CURRENT_COMMON_ROVER_AUTHORITY.md`](../../CURRENT_COMMON_ROVER_AUTHORITY.md); [20T physical envelope](../../cad/common_rover/pto/pto_20t_od10_physical_envelope_v001/authority_report.md) |
| Source path | Direct user-confirmed 2026-09-05 as-built inspection; [source trace](../../cad/common_rover/pto/physical_authority/pto_outward_direction_physical_authority_2026_09_05_v001/SOURCE_TRACE.md); v0.9.2.1 CAD lineage; v0.9.6.38 outward interface evidence; Front Interface V002 |
| Output shaft specification | Two independent, fixed, double-supported Ø10 output shafts are recorded in the PTO clutch hardware register. Exact shaft length, final projection, bearing, retention hardware and product selection are HOLD. No common PTO shaft is allowed. |
| Attachment/interface specification | PTO carries rotational torque only. Unit weight/reaction/impact uses a separate four-point portal. Front Interface V002 uses four KP000 references and a 400 mm 2040 transverse beam; manufacture/installation is not proven. |
| Physical validation status | Direction-only PASS: PTO-L `-X` outward, PTO-R `+X` outward; inward physical space rejected. Ø10 shafts are owned and the 20T pulley envelope was directly measured. Output-shaft final length/projection, installed fit, retention, torque, load and powered tests remain pending. The separate 12 mm shaft-shortening PASS is scoped to the Candidate-C crawler torque path and is not promoted to PTO. |
| CAD validation status | v0.9.6.38 provides supporting outward reference/interface evidence only. v0.9.2.1 central coupling and 0–10 mm sweep remain preserved actual-CAD history. Front Interface V002 and 20T envelope report CAD/contract PASS. No production shaft/guard CAD is promoted. |
| Superseded predecessor | The inward direction scope of v0.9.2.1 is `SUPERSEDED_IN_DIRECTION_SCOPE_BY PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY_2026_09_05`. v0.8–v0.8.5 and v0.9.0–v0.9.2.1 otherwise remain design ancestry and preserved CAD evidence. |
| Unresolved items | Exact output-shaft length/projection, shaft end/interface product, bearing and retention, set-screw specification/capacity, axial spacer, P20/P22/P25 placement result, P25 slot-fit selection, clutch envelope, guard production geometry, powered/torque/load/durability/field validation |

## Physical authority

The measured HTD5M 20T pulley envelope is:

- nominal shaft Ø10 mm; measured bore 9.8 mm;
- flange OD 34.8 mm;
- toothed-region maximum OD 30.5 mm;
- toothed/body width 19.8 mm plus two 1.6 mm flanges, 23.0 mm overall;
- no keyway;
- two approximately Ø4.4 mm radial set-screw regions at 90 degrees;
- set-screw thread, installed length, torque capacity, spacer selection and shaft protrusion pending.

These are physical envelope facts, not manufacturing tooth CAD and not a
powered PTO PASS.

## CURRENT PTO DIRECTION PHYSICAL AUTHORITY

- `PTO_OUTPUT_DIRECTION = OUTWARD_PHYSICAL_AUTHORITY`
- `PTO_LEFT_DIRECTION = -X`
- `PTO_RIGHT_DIRECTION = +X`
- `INWARD_PTO_DIRECTION = PHYSICAL_SPACE_REJECTED`
- `AUTHORITY_CONFLICT_INWARD_VS_OUTWARD = RESOLVED_OUTWARD`

The direct 2026-09-05 as-built inspection established that the required
two-support shaft arrangement and actual torque-transmission path leave
insufficient physical space for an inward output configuration. The canonical
decision and full scope boundary are in the
[PTO outward-direction physical authority](../../cad/common_rover/pto/physical_authority/pto_outward_direction_physical_authority_2026_09_05_v001/PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY_2026_09_05.md).

## Resolved direction-conflict history

- v0.9.2.1 recorded left `-Y` and right `+Y` inward design/CAD geometry. That
  direction scope is now physically rejected and superseded; its other evidence
  remains preserved.
- v0.9.6.38 recorded PTO-L `-X` and PTO-R `+X` outward as a documentation and
  reference-interface candidate. Its direction agrees with the physical
  decision, but no other v0.9.6.38 scope is promoted.
- The former `AUTHORITY_CONFLICT` is retained as development history with final
  disposition `RESOLVED_OUTWARD`.

## Pending gauge and positioning lanes

- `pto_axial_shim_spacer_test_v001`: 0.5/1.0 mm shim set CAD/contract PASS;
  physical spacer authority pending.
- `pto_offset_spacer_test_v001`: P20/P22/P25 are non-load-bearing placement
  gauges; all physical result fields are pending.
- `pto_p25_slide_in_positioning_v002`: 25.000000 mm positioning candidate and
  A/B/C slot coupons; the result sheet is blank and structural load is pending.
- `pto_servo_sliding_idler_clutch_v001`: selected clutch architecture and
  parameter study; one-side physical validation, powered test and torque PASS
  remain prohibited/pending.
