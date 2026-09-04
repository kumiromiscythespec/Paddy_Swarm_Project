# DESIGN SPEC — v004 B15 position retention

## Scope

The deliverable consists of:

1. a low-material integrated position-retention/optical-reference coupon;
2. the v004 tripod carrier with camera-side restraint additions;
3. a full B15 rainhood prototype preserving v002 shell interfaces;
4. camera and side-assembly STEP references for inspection.

The φ26.2 mm commercial metal pipe clamp and its product-specific adapter remain outside scope.

## Authority hierarchy

1. v002 commit `17a703694d5b2e127b5f7bccf8bfe3c5f1f0f2b9`: camera/tripod/carrier/shell interface.
2. v003 lane: A/B/C CAD geometry and mechanical non-interference.
3. User-provided v003 physical test: A rejected; B nominal clear/shift fail; C robust clear.
4. v004: B15 full hood plus controlled camera-side retention additions.

If tripod axis, base seating plane, shell rails, rear stops, M4 pattern, nut traps, or USB route must change, stop with `INTERFACE_CHANGE_REQUIRED`.

## Role separation

- 1/4-20 screw: vertical retention.
- PETG extended side guides: X location and yaw lever arm.
- Shallow front corner stops plus unchanged rear stops: Y repeatability and yaw resistance.
- Carrier mechanical/shell stops: hood-to-carrier repeatability.

No PETG feature is intended to clamp the camera by hard interference.

## Position geometry

The side-guide inner face remains 0.7 mm outside the folded clip authority envelope. Guide height remains 2.8 mm. The guide extends from Y=-28.4 to Y=24.0, length 52.4 mm, compared with 44 mm in v002. A low 1.2 mm outward-only foot reinforces the root without moving the inner contact datum.

Two 12 x 3 x 2.8 mm front pads sit 0.7 mm forward of the safe clip front and at X offsets ±18 mm about the tripod axis. The v002 rear pads remain at the same 0.7 mm rear gap. The shallow four-sided relation guides seating but is not a deep pocket.

Expected nominal contact: none. Light contact caused by physical tolerance is acceptable for testing. Hard press fit, case marking, or housing deformation is a failure.

## Optical geometry

The v004 front roof is generated from the same B object and bevel equation used by v003:

- front Y=-45.4 mm;
- 15 mm setback from v002;
- 40-degree upward underside bevel;
- calculated run 2.080 mm;
- 15 mm roof length ahead of the folded-safe-front datum.

The full hood does not extend the v003 B sidewall forward. Rear roof and baffle are restored behind the optical region. Any future front edge, drip, or sidewall extension requires renewed optical physical validation.

## Rain strategy

B is selected because it retains 5 mm more forward cover than C. The upper roof, full width, lateral walls, rear baffle, and USB drip-loop outlet remain. The B sharp leading edge and upward bevel act as the rain cut; a downward v002 lip is not added into the verified optical zone.

Required tests remain top spray, 45-degree spray, cable-side/rear splash, wind-driven rain, and long-duration outdoor exposure. CAD does not establish field protection.

## Coupon fidelity

The coupon integrates the v004 carrier and optical reference in one solid, eliminating assembly tolerance between a test carrier and a separate front clip. Coupon-only outer side spines join the carrier to the B reference and form a side-print datum. They are outside the camera envelope and are not present on the production carrier or full hood.

Four exterior ribs identify v004 and distinguish it from v003 A/B/C one/two/three-rib coupons.

## FDM robustness

- Low 2.8 mm guides replace tall tabs.
- Long continuous guides distribute load.
- Outward feet reinforce roots without reducing camera clearance.
- Rounded guide and stop plan corners reduce crack starters.
- No product-specific pipe-clamp ears are modeled.

Physical PETG strength remains pending.

## Status indicator limitation

At excessive mount displacement, the B hood may appear at the image top. This can prompt inspection, but it is neither a calibrated displacement gauge nor a safety mechanism.

`SAFETY_FEATURE = FALSE`; `STATUS_INDICATOR_ONLY = TRUE`.

