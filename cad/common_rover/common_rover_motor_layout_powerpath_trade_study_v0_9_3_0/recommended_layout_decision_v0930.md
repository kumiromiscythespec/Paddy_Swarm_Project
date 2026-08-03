# Recommended layout decision v0.9.3.0

## First candidate

**A_LATERAL_FRONT_DIRECT + P1**. Motor front plates are at left [68.0, -185.0, 105.0] mm and right [-68.0, -185.0, 105.0] mm in the current +X-left/+Y-rear/+Z-up frame. Fixed guarded rover width is 290.0 mm, controlled by the inherited 290 mm track proxy. The motor+G1 subsystem itself is narrower. No right-angle stage is required.

## Second candidate

**E_LONGITUDINAL_FRONT_PTO + P4**. It keeps fixed width inside the same proxy and provides two simple forward PTO outputs, but requires an explicit bevel/miter pair on each DRIVE branch.

## Decision state

`TOP_2_CANDIDATES_PHYSICAL_MOCKUP_REQUIRED`. This is not a design-authority update. Actual track solid, motor/bracket mounting detail, 60T/bearing stack, connector/cable sweep, guards, metal clutch, brake, and load path are unresolved. No purchase, machining, drilling, powered test, or field deployment is approved.
