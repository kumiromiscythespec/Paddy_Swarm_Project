# PTO authority map

## Decision summary

PTO is not represented by one conflict-free, fully physical authority. The
repository safely establishes two independent ports and several scoped physical
facts, but it contains an unresolved direction conflict. The final output-shaft
length/projection, powered behavior, torque capacity, and field configuration
remain HOLD.

## Required authority fields

| Field | Repository finding |
|---|---|
| Authority name | Explicit Common Rover design pointer: `common_rover_inward_pto_coupling_cad_verified_v0_9_2_1`; current physical pulley envelope: `PTO_20T_OD10_PHYSICAL_ENVELOPE_V001`; later direction candidate: `common_rover_dual_outboard_pto_guard_interface_v0_9_6_38` |
| Authority path | [`../../CURRENT_COMMON_ROVER_AUTHORITY.md`](../../CURRENT_COMMON_ROVER_AUTHORITY.md); [`../../cad/common_rover/pto/pto_20t_od10_physical_envelope_v001/authority_report.md`](../../cad/common_rover/pto/pto_20t_od10_physical_envelope_v001/authority_report.md); [`../../cad/common_rover/common_rover_dual_outboard_pto_guard_interface_v0_9_6_38/PTO_INTERFACE_AUTHORITY.md`](../../cad/common_rover/common_rover_dual_outboard_pto_guard_interface_v0_9_6_38/PTO_INTERFACE_AUTHORITY.md) |
| Source path | v0.9.2.1 canonical CAD authority; `physical_measurements.json` in the 20T physical-envelope lane; v0.9.6.38 direction register and interface document; Front Interface V002 |
| Output shaft specification | Two independent, fixed, double-supported Ø10 output shafts are recorded in the PTO clutch hardware register. Exact shaft length, final projection, bearing, retention hardware and product selection are HOLD. No common PTO shaft is allowed. |
| Attachment/interface specification | PTO carries rotational torque only. Unit weight/reaction/impact uses a separate four-point portal. Front Interface V002 uses four KP000 references and a 400 mm 2040 transverse beam; manufacture/installation is not proven. |
| Physical validation status | Ø10 shafts are owned and the 20T pulley envelope was directly measured. Output-shaft final length/projection, installed fit, retention, torque, load and powered tests remain pending. The separate 12 mm shaft-shortening PASS is scoped to the Candidate-C crawler torque path and is not promoted to PTO. |
| CAD validation status | v0.9.2.1 central coupling and 0–10 mm sweep are actual-CAD verified; upstream system geometry remains inherited conditional. Front Interface V002 and 20T envelope report CAD/contract PASS. v0.9.6.38 contains reference envelopes, not production shaft/guard CAD. |
| Superseded predecessor | v0.8–v0.8.5 and v0.9.0–v0.9.2 remain design ancestry. v0.9.2.1 superseded v0.9.1's assumption that the 60 mm center gap was usable coupling engagement. v0.9.6.38 says the earlier inward direction is superseded by a new physical layout constraint, but also identifies itself as a documentation/interface candidate. |
| Unresolved items | Direction precedence, exact output-shaft length/projection, shaft end/interface product, bearing and retention, set-screw specification/capacity, axial spacer, P20/P22/P25 placement result, P25 slot-fit selection, clutch envelope, guard geometry, powered/torque/load/durability/field validation |

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

## AUTHORITY_CONFLICT: output direction

- The explicitly declared repository-root v0.9.2.1 design authority says left
  output `-Y` and right output `+Y`, both inward, with independent 12.5 mm
  candidate stubs and a 36 mm center end gap.
- v0.9.6.38 freezes a documentation/interface candidate with PTO-L `-X` and
  PTO-R `+X`, both outward. Its supersession register attributes the change to a
  new physical layout constraint but states that v0.9.2.1 was protected and not
  silently rewritten.

Because no explicit authority-promotion record resolves these statements,
neither direction is silently selected here. The conflict must be closed by a
scoped physical result and explicit authority promotion.

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
