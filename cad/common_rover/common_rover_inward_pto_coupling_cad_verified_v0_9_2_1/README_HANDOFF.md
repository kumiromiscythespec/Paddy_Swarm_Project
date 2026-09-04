# Common Rover v0.9.2.1 handoff

This 55-path differential package replaces fixed expected-clearance evidence
with actual CadQuery/OCP Shape calculations in the central coupling region and
replaces the invalid common-shaft dummy with two independent shaft references.

- matrix pairs: 138
- matrix PASS/FAIL/ERROR: 138/0/0
- sampled sweep calculations: 420
- full-sweep minimum: 5.000 mm
- center gap: 36.0 mm
- left/right stub: 12.5/12.5 mm
- dry-fit states: DF0–DF8

Scope: `CENTRAL_COUPLING_ACTUAL_CAD_VERIFIED`.
Upstream frame/belt/clutch/pulley/track Shapes are parametric reconstructions,
so `UPSTREAM_POWERTRAIN_GEOMETRY_INHERITED_CONDITIONAL` remains in force.
`ACTUAL_CAD_FULL_SYSTEM_VERIFIED` is not claimed.

All STEP/STL dry-fit artifacts are no-load geometry references. Keep physical
fit, load capacity, cutting, machining, manufacturing, powered testing, and
field deployment on HOLD/NOT_APPROVED.
