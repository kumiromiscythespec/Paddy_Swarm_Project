# Common Rover Front-Drive Dual-PTO Design Authority v0.8

Document ID: `PS-CR-FRONT-DRIVE-DUAL-PTO-DESIGN-AUTHORITY-V008`  
Status: `FIXED_SPEC_WITH_LAYOUT_AND_MEASUREMENT_HOLDS`  
Release: `NOT_APPROVED`

## 1. Authority scope

This document is the current design authority for the Common Rover architecture:

> Front-mounted two-motor drive, two independent three-position slide clutches,
> two independent forward PTO ports, elevated CBOX/BBOX, and independent
> inverted-trapezoid crawlers.

It fixes architecture and dimensional relationships. It does **not** release
aluminum cutting, drilling, clutch fabrication, powered testing, water/mud
testing, or field deployment. The STEP file is an envelope inspection model,
not manufacturing CAD.

## 2. Coordinate system and order

- Length unit: mm; angle unit: degree.
- +X is rover front, -X rear.
- +Y is rover left when facing forward, -Y right.
- +Z is up and ground is Z=0.
- Legacy mapping is `X_v008=-Y_legacy`, `Y_v008=X_legacy`,
  `Z_v008=Z_legacy`; direct import of legacy coordinates is prohibited.
- Fixed order:
  `X_PTO > X_POWER_TRANSMISSION > X_MOTOR > X_CBOX > X_BBOX`.
- Power transmission is concentrated forward of CBOX. CBOX underside,
  BBOX underside, the CBOX/BBOX connection zone, and rear service space are
  prohibited transmission locations.

## 3. Fixed outer dimensions and height relations

| Item | X fore-aft | Y lateral | Z height | Bottom Z | Top Z |
|---|---:|---:|---:|---:|---:|
| CBOX | 130 | 140 | 105 | 200 | 305 |
| BBOX | 150 | 220 | 150 | 200 | 350 |
| Battery cassette | 125 | 180 | 120 | candidate inside BBOX | candidate inside BBOX |

CBOX and BBOX are centered at Y=0, arranged front/rear, and face each other
with their short X faces. Their principal guide/contact/latch region stays
inside the central 140 mm. Neither box is structural and neither may receive
motor reaction, PTO bearing load, crawler load, or belt tension.

The BBOX/cassette external differences are X=25, Y=40, Z=30. These are **not**
internal clearances. The BBOX must physically measure at least
129 x 184 x 125 effective millimetres after wall, lid, gasket, base, guide,
contact and latch allowances. Until measured, cassette fit is
`FIELD_MEASUREMENT_REQUIRED`.

The cassette contact face points forward toward CBOX. The mechanical guide
engages first; electrical contact engages only during final travel; an
independent latch retains the cassette. Contacts carry no cassette weight,
are not locating pins, and are never disconnected under power.

Water=150 and mud sink allowance=50 fix both box bottoms at Z>=200.
The axis relationship is:

`Z_PTO_AXIS >= Z_MOTOR_AXIS >= Z_BOX_TOP_MAX(350)`.

Equal motor/PTO axis height is preferred. The inspection candidate uses
Z=370 for both axes, but final height remains parameterized.

## 4. Width authority

- Nominal row spacing: 300.
- Hard maximum including PTO ends, couplings, bolts, track protrusions,
  latches, brackets and guards: 299.
- Strict condition: completed width is less than 300.
- Target: 286–290.
- Each crawler: 55.
- Central lower structure: at most 180.

The candidate track envelope is 286 wide and the candidate PTO end planes
produce a 290 overall envelope. This leaves only 5 mm per side to a nominal
300 mm row and is **not** physical width release. Real couplings, fasteners,
guards, mud and track runout remain unmeasured.

## 5. Motors and slide clutches

Exactly two high-mounted motors are used. The left shaft points inward in -Y;
the right shaft points inward in +Y. A third PTO motor, outward motor shafts,
and a common left/right motor shaft are prohibited.

Each motor has its own mechanical axial slide clutch with exactly three
positions: DRIVE, NEUTRAL and PTO. Same-side DRIVE/PTO simultaneous engagement
is mechanically prohibited. Every DRIVE/PTO transition passes through
NEUTRAL. The rover and motor stop before shifting. Left and right clutches are
independent and may not collide at the center. Sensor/limit-switch mounting
must remain possible, and power-loss-to-NEUTRAL is the preferred safety
direction.

Actual shaft diameter, stroke, dog form, engagement length, spring,
actuation, sensor position and pulley stack order are
`PART_MEASUREMENT_REQUIRED`.

## 6. Two independent forward PTO ports

There are two and only two ports. Left output is +Y, right output is -Y; both
axes remain lateral. They are independent shafts and may not be joined.
Each side uses the initial candidate sequence:

`inner KP000 -> clearance -> 60T -> clearance -> outer KP000 -> short shaft -> coupling`.

The 60T is between the two bearings. The shaft is aligned through both
bearings before final tightening. A collar or retaining ring provides axial
location; KP000 set screws alone do not. The work unit weight is not carried
only by the PTO shaft.

The target end plane is |Y|<=145 and the absolute condition is |Y|<150.
The candidate uses +/-145. Actual shaft, coupling, cap, pin and fastener
dimensions block release. KP000 load, speed, sealing, mud and life capability
also remain HOLD.

## 7. Belt and pulley authority

- HTD 5M STANDARD, 5 mm pitch, 15 mm belt.
- 20T driver, 60T driven, nominal 3:1.
- Four independent runs:
  LEFT_DRIVE, RIGHT_DRIVE, LEFT_PTO, RIGHT_PTO.
- Left/right runs may not cross and the PTO runs may not share one belt.
- PTO belts are central; DRIVE belts are outboard over the crawler side.
- DRIVE windows stay outside the 2040 root crossmember.
- PTO horizontal frame members stay below the PTO pulley envelope.
- Belts do not run in T-slots; 2040 is not notched for belt passage.

The user-reported 60T maximum dimension is 102 mm with unresolved meaning.
v0.8 supersedes the 102 mm-only rotation envelope and uses diameter 120,
radius 60 for all initial checks. At candidate axis Z=370 the lower edge is
Z=310. PTO horizontal members are Z=220–240, giving a simplified 70 mm
lower-edge separation. Actual flange diameter, pulley width, runout and belt
sway must be measured.

Minimum/recommended clearances (mm):

| Pair | Minimum | Recommended |
|---|---:|---:|
| Belt side–frame | 5 | 8 |
| Belt–diagonal | 8 | 10 |
| Belt–bolt head | 5 | 8 |
| Pulley flange–frame | 5 | 8 |
| 60T envelope–fixed part | 8 | 10 |
| Belt–wiring | 10 | 15 |
| PTO pulley–KP000 | 5 | 8 |
| DRIVE belt–crawler cover | 8 | 12 |
| BOX bottom–track dynamic envelope | 10 | 20 |

## 8. Front PTO frame and load path

The front frame uses one 2040 root crossmember, two 2020 spars, one 2020
front crossbar, two 2020 diagonal braces, necessary vertical 2020 supports,
and metal brackets/gussets. Left and right form independent outer triangles;
a center X brace is prohibited. No single 2040 cantilever and no printed-only
primary-load bracket is allowed.

Load path:
`PTO output -> shaft -> KP000 -> 2020 spar -> 2020 diagonal ->
2040 root -> two 2040 main rails -> lower rover frame`.

## 9. Inverted-trapezoid crawlers

Each side is independent and has one front-upper drive wheel, one rear-upper
idler, three or four lower rollers, and one continuous track. The top run is
longer than the bottom contact run; front/rear runs are diagonal. The rear
idler has tension adjustment. A rectangular tank track, four-wheel tire
conversion and common left/right drive shaft are prohibited.

Each side frame has a longer upper 2040, shorter lower 2040, front/rear 2020
diagonal posts, drive/idler supports, individually serviceable lower rollers,
and an idler adjustment. It is not a rectangle or sealed plate. Mud drainage,
washing, outside track replacement and straw-removal disassembly are required.
The DRIVE 60T and crawler sprocket on the same nominal 10 mm shaft is a
candidate, not released hardware.

The inspection model shows four rollers. The three/four decision and every
track, sprocket, idler, roller and tension dimension remain HOLD.

## 10. Candidate interference result

The generated simplified model contains four independent belt safety
envelopes and a full-stroke placeholder for each clutch. It checks belt/frame,
belt/representative-fastener, clutch/frame, track/upper-structure, PTO
pulley/KP000, lid service and rear cassette withdrawal.

- Candidate solid-intersection checks reporting zero: 33.
- FAIL checks: 0.
- HOLD checks: 51.
- Physical release: `NOT_APPROVED`.

Zero candidate intersections are not a physical PASS. Actual motor, clutch,
20T/60T widths, flanges, KP000, shafts, couplings, fasteners, tensioners,
belt sway, track runout, guards and wiring are missing.

## 11. Aluminum stock allocation

Declared inventory is 2020 x 400 x 8 and 2040 x 400 x 8. The candidate plan
uses all eight 2020 bars and seven 2040 bars, leaving one 400 mm 2040 reserve.
No candidate member exceeds 400. The upper crawler rail is 400 and the lower
is 260. The root and rear 2040 crossmembers are paired as 156+156 from one
stock bar. Four independent 2020 vertical supports provide one load path for
each KP000 candidate position. Detailed cuts are in `common_rover_front_drive_dual_pto_aluminum_allocation_v008.csv`.

This is only a layout feasibility result. All cutting, drilling, final angles,
kerf, end preparation, metal splice/gusset selection and structural
calculation remain HOLD.

No metal connection-plate/bracket/gusset inventory was declared. Such
hardware is an additional-purchase requirement; its exact count, thickness,
material and hole pattern remain `PART_MEASUREMENT_REQUIRED` pending the load
case and structural calculation. This is separate from the zero-shortage
candidate result for 2020/2040 extrusion bars.

## 12. Superseded architecture

- `LEGACY_COORDINATE_X_LATERAL_Y_LONGITUDINAL`
- `LEGACY_LOW_MOTOR_AND_PTO_AXIS_COORDINATES`
- `BBOX_220MM_AXIS_FORE_AFT`
- `BBOX_200_X_150_X_120_MM`
- `CBOX_AND_BBOX_SAME_SIZE`
- `CBOX_BBOX_SIDE_BY_SIDE`
- `LEFT_RIGHT_PTO_COMMON_SHAFT`
- `ONE_CENTER_60T_PULLEY_FOR_BOTH_PTO_PORTS`
- `DEDICATED_THIRD_PTO_MOTOR`
- `MOTOR_SHAFTS_POINTING_OUTWARD`
- `PTO_SHAFTS_POINTING_FORE_AFT`
- `PTO_BEHIND_MOTOR`
- `AMBIGUOUS_DRIVE_PTO_SWITCHING`
- `UNAPPROVED_NON_SLIDE_CLUTCH_SWITCHING`
- `COMMON_SYNCHRONIZED_CLUTCH_SELECTOR`
- `RECTANGULAR_TANK_TRACK`
- `FOUR_WHEEL_TIRE_LAYOUT`
- `EQUAL_LENGTH_RECTANGULAR_CRAWLER_FRAME`
- `SINGLE_ALUMINUM_MEMBER_LONGER_THAN_400_MM`
- `BOX_AS_PRIMARY_STRUCTURE`
- `PTO_60T_102MM_ONLY_ROTATION_ENVELOPE`
- `FRAME_595_X_155_LAYOUT_AS_CURRENT_AUTHORITY`

## 13. Measurement and release holds

- `ACTUAL_MOTOR_ENVELOPE`
- `MOTOR_SHAFT_DIAMETER`
- `MOTOR_EFFECTIVE_SHAFT_LENGTH`
- `MOTOR_MASS`
- `SLIDE_CLUTCH_DETAIL_GEOMETRY`
- `SLIDE_CLUTCH_STROKE`
- `DOG_ENGAGEMENT_LENGTH`
- `CLUTCH_ACTUATION_MECHANISM`
- `CLUTCH_SENSOR_POSITION`
- `PULLEY_AXIAL_STACK_ORDER`
- `20T_PULLEY_ACTUAL_WIDTH`
- `60T_PULLEY_ACTUAL_WIDTH`
- `PULLEY_FLANGE_OUTSIDE_DIAMETER`
- `BELT_LENGTH`
- `BELT_LATERAL_SWAY`
- `TENSIONER_POSITION_AND_FULL_RANGE`
- `KP000_ACTUAL_DIMENSIONS_AND_LOAD_RATING`
- `PTO_BEARING_SPACING`
- `PTO_FORWARD_OVERHANG`
- `PTO_SHAFT_DIMENSIONS`
- `PTO_COUPLING_OUTSIDE_DIAMETER_AND_LENGTH`
- `BBOX_EFFECTIVE_INTERIOR`
- `BATTERY_CASSETTE_GUIDE_THICKNESS`
- `BATTERY_CASSETTE_CONTACT_TYPE`
- `BATTERY_CASSETTE_LATCH_GEOMETRY`
- `CRAWLER_FORE_AFT_LENGTH`
- `UPPER_TRACK_LENGTH`
- `LOWER_GROUND_CONTACT_LENGTH`
- `TRACK_PITCH`
- `DRIVE_SPROCKET_DIAMETER`
- `IDLER_DIAMETER`
- `ROLLER_DIAMETER`
- `ROLLER_COUNT_THREE_OR_FOUR`
- `UPPER_AND_LOWER_2040_FINAL_CUT_LENGTHS`
- `FRONT_REAR_DIAGONAL_POST_ANGLES`
- `TRACK_LATERAL_DYNAMIC_RUNOUT`
- `IDLER_TENSION_ADJUSTMENT_FULL_RANGE`
- `FASTENER_HEAD_WASHER_COLLAR_RETAINING_RING_ENVELOPES`
- `METAL_BRACKET_GUSSET_DIMENSIONS_AND_LOAD_RATING`
- `WIRING_ROUTE`
- `COMPLETED_MASS`
- `CENTER_OF_GRAVITY`
- `BUOYANCY`
- `ACTUAL_MUD_SINK`
- `FIELD_TRAVEL_FEASIBILITY`

Final gates:

- ALUMINUM_CUTTING: `HOLD`
- ADDITIONAL_DRILLING: `HOLD`
- MOTOR_FIXING: `HOLD`
- CLUTCH_FABRICATION: `HOLD`
- BBOX_CONTAINMENT_MEASUREMENT: `HOLD`
- CASSETTE_CONTACT_SELECTION: `HOLD`
- CRAWLER_MANUFACTURING: `HOLD`
- POWERED_PTO_TEST: `HOLD`
- WATER_TEST: `HOLD`
- MUD_TEST: `HOLD`
- FIELD_DEPLOYMENT: `NOT_APPROVED`

## 14. Interference correction order

1. Move belt planes axially: PTO inward and DRIVE outward.
2. Move frame below or fore/aft of envelopes; move diagonals below; reverse
   bracket/bolt direction.
3. Shorten the root crossmember, split outer brackets, preserve belt windows.
4. Change axial stack, bearing/collar/clutch spacing, or tensioner position.
5. Only then propose added metal frame or a dedicated metal plate.

Never resolve interference by exceeding 299, lowering motors, moving PTO
behind motors, adding a third motor, joining PTO shafts, structuralizing
boxes, heavily cutting 2040, simultaneous DRIVE/PTO engagement, or changing
the crawler to a rectangle.

## 15. Validation sequence

1. Measure BBOX effective interior and battery path.
2. Measure both motors, shafts and brackets.
3. Measure both 20T and all 60T pulleys including flange and axial stack.
4. Measure clutch stroke and all three engagement states.
5. Measure KP000, shaft, collars, rings, coupling and fasteners.
6. Select belts and tensioners; inspect min/nominal/max positions.
7. Inflate CAD for +/-1 axial play, +/-1 assembly error, 2 mm deformation,
   measured belt sway and measured track dynamics.
8. Re-run all four belt/frame and belt/fastener intersections.
9. Verify completed width including every protrusion is <=299.
10. Only after structural review may aluminum cut/drill release be considered.

Until every applicable HOLD is closed, this architecture is not a completed
specification and field deployment is `NOT_APPROVED`.
