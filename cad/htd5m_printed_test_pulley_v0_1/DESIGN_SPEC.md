# Design specification — HTD 5M pre-calibration artifacts v0.1

## Scope and stop condition

This package deliberately stops before the 20T/60T pulley bodies, bores,
keyways, hubs, fasteners, flanges, and load interfaces. It produces only bore
gauge bars and curved belt-contact coupons. Automated geometric validation does
not establish belt fit or shaft fit; those statuses remain
`CALIBRATION_PENDING` until human measurements are recorded and approved.

## Bore gauges

| Gauge | Candidates (mm) | Thickness | Center spacing | Minimum edge wall |
|---|---|---:|---:|---:|
| 6 mm shaft | 6.00, 6.10, 6.20, 6.30, 6.40 | 8 mm | 14 mm | 3 mm |
| 10 mm shaft | 10.00, 10.10, 10.20, 10.30, 10.40, 10.50 | 10 mm | 18 mm | 4 mm |

All holes are modeled as Z-axis true circles. The surrounding bar is chamfered
0.5 mm and both bore entrances are chamfered 0.3 mm. Candidate letters and
diameters are recessed into the top face, so they do not increase nominal
thickness. No slicer XY or hole compensation is assumed.

## HTD 5M curve basis

The pitch diameter is fixed by:

`PD = N × 5 / π`

| Curve | Pitch diameter (mm) | Pitch-line differential a (mm) | Nominal OD = PD − 2a (mm) |
|---|---:|---:|---:|
| 20T | 31.830988618 | 0.572 | 30.686988618 |
| 60T | 95.492965856 | 0.572 | 94.348965856 |

The implementation uses the H5M nominal groove dimensions from ISO
13050:2022 Table 14:

| Tooth-count band | Hg | X | R1 | φ | R2 |
|---|---:|---:|---:|---:|---:|
| 17–25 (20T coupon) | 2.009 | 0.320 | 1.270 | 6° | 0.508 |
| 26–80 (60T coupon) | 2.052 | 0.081 | 1.438 | 2° | 0.488 |

The groove is a symmetric pair of circular R1 arcs with offset centers, joined
to the outside-diameter region by R2 circular transitions. It is not a
triangle, trapezoid, sine approximation, semicircular array, or straight-sided
tooth. The center depth is derived as:

`center_depth = Hg − sqrt(R1² − X²)`

ISO states that nominal groove profiles approximate the true generated profile
over tooth-count bands. This model is therefore a calibration coupon
construction, not proof of a production hob-generated groove.

References:

- [ISO 13050:2022 — Synchronous belt drives — Metric pitch, curvilinear profile systems G, H, R and S, belts and pulleys](https://www.iso.org/standard/82453.html)
- [Gates Light Power & Precision manual](https://www.gates.com/content/dam/documents-library/catalogs/light-power-and-precision-manual.pdf)
- [JIS B 1857-2:2015 profile illustration and terminology](https://kikakurui.com/b1/B1857-2-2015-01.html)

## Coupon construction

- Belt pitch: 5.000 mm, unchanged by fit variant
- Nominal belt width: 15 mm
- Printed tooth face width: 16.2 mm
- Six groove stations, equally spaced by `360/N`
- Sector span: six pitches, leaving half a pitch from each end station to the
  radial end face
- No flange
- Inner backing rib: 5.5 mm radially inward from the nominal groove root
- Identification recessed on the non-contact top/inner rib: `20T-T`,
  `20T-S`, `20T-L`, `60T-T`, `60T-S`, `60T-L`

Clearance is applied as a normal contact-surface adjustment to the paired main
arc and transition radii; it does not change 5 mm pitch, tooth station angles,
pitch diameter, or nominal outside diameter:

| Fit | Code | Normal clearance |
|---|---|---:|
| Tight | T | 0.05 mm |
| Standard | S | 0.10 mm |
| Loose | L | 0.15 mm |

These clearance labels describe CAD variants only. “Tight”, “standard”, and
“loose” are not verified physical outcomes.

## Automated acceptance checks

The validator checks:

- bore count, candidate values, spacing, edge wall, thickness, one valid solid;
- 20T/60T curvature, exact pitch-diameter formula, six stations and 5 mm pitch;
- 16.2 mm face width and distinct clearance geometry with invariant stations;
- paired circular contact arcs and nonzero transition radii;
- single valid solids without accidental disconnected labels;
- individual STEP round trips;
- nonempty, readable STL meshes and sensible Bambu A1 bounding boxes;
- absence of any complete-pulley STEP/STL export.

## Human acceptance boundary

Only a person using the actual shafts and belt may select a bore and groove
variant. Record printer, filament, slicer, orientation, measured bores, fit
feel, belt seating, backlash impression, insertion/removal effort, and visible
damage. No result may be copied to a full pulley model without explicit
approval.
