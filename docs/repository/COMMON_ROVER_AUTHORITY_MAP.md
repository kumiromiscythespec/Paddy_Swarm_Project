# Common Rover authority map

## Current and scoped authorities

| Component | State | Primary path | Boundary |
|---|---|---|---|
| Overall design pointer | CURRENT, explicit design declaration | [`../../CURRENT_COMMON_ROVER_AUTHORITY.md`](../../CURRENT_COMMON_ROVER_AUTHORITY.md) | v0.9.2.1 inward-PTO design; not full-system physical authority |
| Physical dimensions | CURRENT_PHYSICAL_AUTHORITY | [`../../cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001/COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01.md`](../../cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001/COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01.md) | Direct/current as-built values; derived midpoints remain derived |
| Frame physical geometry | CURRENT_PHYSICAL_AUTHORITY | same dated physical-dimensional authority | Rail spans/Z and static crawler clearance; absolute Y and dynamic behavior pending |
| Front frame/PTO interface | CURRENT_DESIGN_AUTHORITY_CANDIDATE | [`../../cad/common_rover/frame/front_interface_dual_pto_20t_v002/DESIGN_AUTHORITY.md`](../../cad/common_rover/frame/front_interface_dual_pto_20t_v002/DESIGN_AUTHORITY.md) | CAD/contract PASS; physical manufacture/install/fit pending |
| PTO | AUTHORITY_CONFLICT / scoped physical facts | [`PTO_AUTHORITY_MAP.md`](PTO_AUTHORITY_MAP.md) | Inward versus outward direction unresolved; final shaft/load/powered pending |
| Drivetrain drive sprocket | CURRENT_SOURCE / PRINT_READY | [`../../cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003/README.md`](../../cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003/README.md) | Candidate-C carrier CAD/contract PASS; spacer stack and full physical validation pending |
| Crawler tooth profile | CURRENT_BASELINE / HOLD_NEAR_PASS | [`../../cad/common_rover/drivetrain/crawler_candidate_c_full_12t_sprocket_v001/CANDIDATE_C_PHYSICAL_RESULT.md`](../../cad/common_rover/drivetrain/crawler_candidate_c_full_12t_sprocket_v001/CANDIDATE_C_PHYSICAL_RESULT.md) | Candidate B failed loose; C reduced play but is not full crawler PASS |
| Crawler idler | CURRENT_DESIGN_CANDIDATE | [`../../cad/common_rover/drivetrain/crawler_idler_candidate_c_v001/README.md`](../../cad/common_rover/drivetrain/crawler_idler_candidate_c_v001/README.md) | CAD/contract PASS; slicer/physical pending |
| BBOX design | CURRENT_DESIGN_AUTHORITY | [`../../cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065/COMPACT_FIELD_BBOX_V004_G065_DESIGN_AUTHORITY.md`](../../cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065/COMPACT_FIELD_BBOX_V004_G065_DESIGN_AUTHORITY.md) | V004 G065; full box/chimney/gland/global validation pending |
| BBOX seal | CURRENT_PHYSICAL_AUTHORITY, scoped | [`../../cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065/G065_WATER_PHYSICAL_RESULT_PROMOTION.md`](../../cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065/G065_WATER_PHYSICAL_RESULT_PROMOTION.md) | Closed G065 dummy only; 60 min + four tilts PASS |
| BBOX battery packaging | CURRENT_PHYSICAL_AUTHORITY, scoped | [`../../cad/common_rover/physical_authority/common_rover_goldenmate_battery_fit_bbox_packaging_authority_v001/README.md`](../../cad/common_rover/physical_authority/common_rover_goldenmate_battery_fit_bbox_packaging_authority_v001/README.md) | Temporary specimen insertion/presence only; axis correction applies |
| CBOX enclosure | CURRENT_DESIGN_AUTHORITY | [`../../cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/docs/DESIGN_AUTHORITY.md`](../../cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/docs/DESIGN_AUTHORITY.md) | 246×150×80 CAD; lid/water/thermal/powered/placement pending |
| CBOX rail mount | CURRENT_CORRECTIVE_CANDIDATE | [`../../cad/common_rover/bbox_cbox/cbox_transverse_top_tslot_saddle_v002/README.md`](../../cad/common_rover/bbox_cbox/cbox_transverse_top_tslot_saddle_v002/README.md) | Replaces failed V001 side interface; coupon must pass before full saddle |

## Physical facts that must remain scoped

- Rail outside span 208–210 mm, inside span 168–170 mm; derived rail-center
  separation 188–190 mm. Absolute rail Y remains pending.
- Left rail top/bottom Z255/Z235; right Z254/Z234.
- BBOX observed highest/lowest points Z254/Z148, but exact CAD feature identity
  and X/Y transform remain unresolved.
- Static crawler highest Z181 left/Z180 right yields 54 mm static clearance to
  the respective rail bottom; this is not dynamic clearance.
- Drive centers Z122/Z123 and nominal derived midpoint Z122.5 are retained.
- Two Candidate-C drivetrain shafts shortened 12.0 mm each fit KP000; exact
  original order length and final absolute shaft length remain procurement HOLD.
- GoldenMate body mapping is 150.9 × 65.5 × 92.5 mm with terminal top 99.4 mm
  above battery bottom. Older use of 99.4 mm as plan width is superseded.

## Historical / superseded / experimental map

| Lane group | Classification | Reason retained |
|---|---|---|
| `front_drive_dual_pto_design_authority_v0_8*` | HISTORICAL / SUPERSEDED ancestry | Records early envelope, clearance, support/orientation and axial studies |
| `common_rover_powertrain_frame_belt_design_authority_v0_9_0` through inward v0.9.2 | DESIGN ancestry | Establishes contracts leading to declared v0.9.2.1 |
| v0.9.3 motor-layout, mockup, bracket and frame-joint lanes | TRADE STUDY / VALIDATION EVIDENCE | Preserves rejected alternatives and measured candidate work |
| v0.9.4–v0.9.5 integration and physical-measurement lanes | PHYSICAL / DESIGN PROVENANCE | Some observations are current inputs; integrated releases were not automatically promoted |
| v0.9.6.x frame, drive, pulley, service and enclosure lanes | COMPONENT CANDIDATE / HOLD unless explicitly scoped above | Higher version numbers alone do not establish overall authority |
| `common_rover_temp_htd5m_60t_*` | EXPERIMENTAL / HISTORICAL | Temporary pulley/retention studies; retain failures and comparisons |
| BBOX V003 G050 full-body seal | SUPERSEDED_UNVALIDATED_SEAL_GEOMETRY | V004 uses G065; successful water test was the G065 dummy |
| CBOX saddle V001 side interface | PHYSICAL_FIT_FAIL / SUPERSEDED BY V002 candidate | Failure is required provenance |

No folder is renamed or moved by this publication.

## Known authority conflicts

1. PTO direction: declared inward v0.9.2.1 versus later outward v0.9.6.38
   documentation/interface candidate.
2. GoldenMate axis semantics: the earlier unordered 150.9/99.4/92.5 record is
   corrected by the later 150.9/65.5/92.5 body plus 99.4 terminal-height record.
3. BBOX Z148/Z254 are direct observations but their exact CAD face/specimen
   registration is unresolved; previous registered collisions are CAD conflicts,
   not physical-solid collisions.
4. Later component CAD does not compose into a single promoted full-rover
   authority. The root v0.9.2.1 pointer remains the explicit design declaration.
