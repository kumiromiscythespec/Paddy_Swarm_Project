# WATER PATH VALIDATION

Rating: `SPLASH_RESISTANT_NOT_WATERPROOF`

CAD sections establish an offset geometric route; they do not prove a waterproof FDM print. Colored-water and staged spray tests remain required.

| Failure mode | CAD path control | Physical status |
|---|---|---|
| `TOP_RAIN` | umbrella roof plus 6 mm downward skirt; parting line is hidden | PENDING |
| `SIDE_RAIN` | skirt plus offset tongue/groove prevents straight path | PENDING |
| `WIND_DRIVEN_RAIN` | two terminal baffles and dogleg vestibules; physical spray pending | PENDING |
| `CABLE_TRACKED_WATER` | local downward port drops into drip vestibule before chamber | PENDING |
| `BOTTOM_SPLASH` | offset drain axes terminate in baffle-isolated vestibules, not the connector chamber | PENDING |
| `WATER_POOLING` | 2 deg two-way chamber floor, low weeps, two gravity drains | PENDING |
| `CAPILLARY_ENTRY` | 3 mm overlap and 0.30 mm offset path; long-duration physical test pending | PENDING |

## CAD path findings

- TOP RAIN: no direct line from roof to connector chamber; the seam is 6 mm behind a downward skirt.
- SIDE RAIN: water must turn under the skirt and again around the 2 mm tongue/groove step.
- CABLE WATER: each local cable path exits downward, turns through a drip vestibule, then crosses a full-height terminal baffle through a low cable passage.
- DRAIN: two 2.5 mm holes leave from vestibule low points; their axes are outside the connector chamber and laterally offset from chamber-floor weeps.
- POOLING: the chamber floor crowns 0.873 mm at center and slopes 2 deg toward both end weeps; the drip pockets are lower and drained.
- BOTTOM SPLASH: each drain axis terminates in a baffle-isolated vestibule and has no straight line to the connector chamber.

## Holds

Wind-driven rain, capillary ingress over hours, print porosity, debris-blocked drains, mud splash, and installation tilt are not resolved by CAD.
