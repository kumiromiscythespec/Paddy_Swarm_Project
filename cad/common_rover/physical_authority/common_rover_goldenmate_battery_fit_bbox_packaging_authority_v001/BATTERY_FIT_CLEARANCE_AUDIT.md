# Battery-fit clearance audit

The audit uses corrected dimensional roles and direct temporary-specimen dimensions.

| Check | Calculation | Result |
|---|---|---:|
| X total nominal clearance | `152 - 150.9` | 1.1 mm |
| X nominal per side if perfectly centered | `1.1 / 2` | 0.55 mm/side |
| Y total nominal clearance | `65.5 - 65.5` | 0.0 mm |
| body-only Z margin | `104 - 92.5` | 11.5 mm |
| terminal-inclusive Z margin | `104 - 99.4` | 4.6 mm |
| measured terminal below rim | direct approximate field result | 3.0 mm |
| measured-vs-derived residual | `4.6 - 3.0` | 1.6 mm |

The 3 mm physical observation and 4.6 mm geometric difference are preserved independently. They are not forced to agree; the residual may include rim/datum interpretation, battery seating, local geometry, and field measurement precision.

Interpretation:

- internal Y `65.5 mm` is `PHYSICAL_MINIMUM_SUCCESSFUL_SPECIMEN`, not `RECOMMENDED_FIELD_INTERNAL_Y`;
- internal X `152 mm` is `PHYSICAL_SUCCESSFUL_SPECIMEN` with only 1.1 mm total nominal clearance;
- physical insertion PASS does not include tolerance, debris, TPU pad, restraint, cable, or removal-force allowance.
