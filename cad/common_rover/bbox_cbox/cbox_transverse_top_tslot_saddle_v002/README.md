# CBOX Transverse Top-T-Slot Independent Saddle V002

CAD_PASS/CONTRACT_TEST_PASS/TOP_T_SLOT_MOUNT_COUPON_PRINT_READY/FULL_LEFT_RIGHT_SADDLE_CAD_READY/FULL_SADDLE_PRINT_HOLD_UNTIL_COUPON_PASS/PHYSICAL_FIT_PENDING/LOAD_CAPACITY_PENDING

V001's independent/transverse CBOX concept remains useful, but its side-wall
rail interface and side M5 alignment are PHYSICAL_FIT_FAIL.  V002 removes every
side fastener hole and uses two vertical M5 adjustment slots per saddle into the
upper rail's top T-slot.  Left/right saddles remain independent; no bridge forces
189 mm spacing or coplanarity.

The physical authority gives each current upper rail a20 mm Y width from the
outside/inside spans and20 mm Z height from top/bottom readings.  The repository
does not prove a complete named2040 cross-section.  One current top slot is the
task's physical context, but its center relative to rail edges remains pending.
The design therefore uses local Y0 only as a reference with ±1.5 mm adjustment.

Direct slot constraints are entrance6.4, internal maximum10.8 and depth6.4 mm.
The rail reference STEP uses those bounds but an explanatory1 mm lip-depth split;
that split, lip angles and radii are NOT physical authority.

Each saddle is140 mm long with vertical M5 centers X=±50 (pitch100 mm), through
slot5.8×8.8 and service pocket12×15 in plan,4.5 deep.  Hardware dimensions are
not physically established in this stack.  The 8 mm support rise is the minimum
studied candidate retaining3.5 mm PETG below the service pocket; +4/+6 are held.
The retained support follows the measured1 mm/189 mm rail-plane slope (0.303°).
An open-edge Ø16 mm local notch preserves the existing BBOX inner-M4 driver
path; it does not change the coupon's top-slot/M5 authority region.
The assembly STEP carries a documented0.02 mm numerical face separation so
coincident CAD faces are not misreported as solid overlap; it is not a spacer.

FIRST PRINT ONLY: `cbox_top_tslot_mount_coupon_v002.stl`.  PETG, Bambu A1,
rail-contact face down, support OFF.  Do not print either full saddle until the
coupon passes flat seating, top-slot alignment, T-nut engagement, tightening,
head clearance, rocking, tool access and damage checks.

The full left/right CAD/STL exists for review but has
FULL_SADDLE_PRINT_HOLD_UNTIL_COUPON_PASS.  No CBOX physical/load/field PASS is
claimed.  BBOX lid/gasket/chimney/M4 are unchanged and non-load-bearing.
`COMMIT_PATHS.txt` is an inventory, not permission to stage.
