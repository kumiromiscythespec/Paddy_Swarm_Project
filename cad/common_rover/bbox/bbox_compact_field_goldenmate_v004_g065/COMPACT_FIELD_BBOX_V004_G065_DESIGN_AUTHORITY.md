# Compact Field BBOX V004 G065 design authority

COMPACT_SEAL_G065_WATER_PHYSICAL_PASS/LOCAL_BBOX_V004_CAD_PASS/CONTRACT_TEST_PASS/FULL_BODY_PRINT_READY/FULL_LID_PRINT_READY/FULL_BBOX_WATERPROOF_PHYSICAL_PENDING/GLOBAL_VEHICLE_INTEGRATION_PHYSICAL_PENDING

Release labels apply only with contract_test_report.json PASS and successful builder --verify.
# G065 physical water result promotion

Source: user's V004 task; specimen WATER_DUMMY_G065, not the full V004 box.
Actual groove width 2.1 mm; actual depth 0.650000 mm; cord diameter 1.8 mm; hard-stop 0.895 mm.

- 60 min upright: PASS.
- Front, rear, left and right tilt >10 degrees: PASS for every direction.
- Witness: COMPLETELY_DRY; leak: NONE.
- Gasket movement: NONE; PETG damage: NONE.
- Witness-paper tear: TEST_ARTIFACT_NOT_WATER_INGRESS; caused by adhesive handling after disassembly.

Classification: COMPACT_SEAL_G065_WATER_PHYSICAL_PASS.
This promotes the tested seal cross-section / closed perimeter only. Full-box and chimney/gland water performance remain PHYSICAL_PENDING.

# V003 G050 supersession

Read-only V003 actual full-body STEP groove depth is 0.500000 mm; it has NOT been physically water tested.
V003_FULL_BODY_G050 = SUPERSEDED_UNVALIDATED_SEAL_GEOMETRY. Existing artifacts remain intact.

History:

- Coupon A: documented 0.45, actual 0.55, dry mechanical PASS, water NOT TESTED.
- Coupon B: documented 0.55, actual 0.65, dry mechanical PASS; G065 closed dummy water PASS.
- V003 selected full body: actual 0.50, unvalidated.
- V004: actual 0.65, inherited G065 seal authority; full-box water test still PENDING.

V003 -> V004 full-body depth change is +0.150000 mm. The historical coupon builder +0.10 mm error is a DIFFERENT fact.

# Exact G065 seal traceability

Read-only measured authority: `D:\Paddy_Swarm_Project\cad\common_rover\bbox\bbox_compact_seal_b_water_dummy_v001`. Generated G065 STEP measures 0.650000000 mm, not an old parameter label.
V004 has width 2.1, actual depth 0.65, hard-stop 0.895, cord OD1.8, outer R6.0, inner R3.9 and centerline R4.95.
Nominal cord compression reference is 0.255 mm (14.166667%); this is not a prediction of rubber deformation.
Full centerline perimeter 451.101767 mm, versus dummy 219.101767 mm. Trim the physical cord/joint to fit; do not use a stretched cord as a dimensional workaround.

Actual translated straight section symmetric difference: 0 mm3.
Four actual corner seal-wall symmetric differences: [0, 0, 0, 0] mm3.
The broader left/front corner comparison includes 41.047500 mm3 of allowed chimney-mouth difference INSIDE the seal; this is separately reported and excluded only from the seal-wall comparison.
Allowed differences are perimeter length, body size, eight rather than four external M4 compression stations, and chimney presence.

M4 architecture remains external vertical through-bolts, flat lid and 0.895 hard-stop. Hole-to-cord minimum is 1.900000 mm, and intersection is zero. This is smaller than the corner-only dummy distance; full-box clamping uniformity must be physically checked.

Two necessary local top-interface corrections (task section 6) are NOT hidden:

1. Extend the groove cutter upward beyond hard-stop to remove four obsolete mid-boss roofs. The naive depth-only body intersects nominal cord by 18.406304 mm3. New intersection is zero. The groove bottom alone moves down 0.15 mm.
2. Restore a 42 x9.5 x8 mm lid-thickness bridge outside the 155 x69 battery opening. V003 was missing 42 x2.1 mm of lid seal land beneath its chimney opening. V004 has zero missing seal land. The lower chimney mouth changes from 42 x37 to 42 x27.5 mm; the chimney ABOVE the 8 mm lid, PG9 hole, 2.4 wall, recess and counterbore are exactly unchanged.

The new lid contains 3192.000000 mm3 additional material and no removed material. Body removed volume 165.576219 mm3; no added body material; zero body delta outside groove envelope. These are local seal corrections, not a battery/upper-chimney redesign.

# Battery clearance audit

GoldenMate: 150.9 x65.5 plan; body height 92.5; terminal-inclusive height 99.4; mass 1.2 kg. The 99.4 dimension is NEVER a plan width.
Cavity 155 x69 x110; wall/floor 3.5 PETG. TPU 1.0 beneath battery; battery datum bottom Z4.5.

- X total clearance 4.1 mm (2.05 per side).
- Y total clearance 3.5 mm (1.75 per side).
- Terminal-to-rim 9.6 mm.
- Actual terminal-to-lid minimum 10.495000 mm.
- Actual battery-to-upper-chimney BRep distance 25.395000 mm.
- Actual battery-to-M4-tower BRep distance 3.010399 mm.

For comparison, conservative plan-only tower estimate is 2.55 mm and terminal-height-to-chimney-base estimate is 18.495 mm; those old scalar estimates are not the actual 3D minima for this asymmetric battery. Do not mislabel the updated distance calculations as a geometry movement.
Battery/body, battery/lid, battery/chimney and battery/M4 intersections: zero. Fixed-body vertical removal sweep intersection: zero with lid REMOVED and strap RELEASED.
No lid battery loading. The strap/anchors remain reservation geometry, not qualified load-carrying hardware. Secure physical restraint before dry tilt.


Battery packaging, upper chimney, output references and parent lanes are protected. Local print release does not release full-box waterproofing or global integration.
