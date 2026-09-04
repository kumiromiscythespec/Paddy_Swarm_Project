# Common Rover CBOX DRIVE Electrical Physical Integration v0.9.6.2

Status: **NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING**  
Classification: `DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION`

This lane preserves the v0.9.6.0 above-water CBOX role and its power/signal separation. It does not approve powered rotation, live-battery submersion, or field deployment.

## Trace

| source | use | protection |
|---|---|---|
| v0.9.5.0 | printable BBOX/CBOX prototype baseline | historical committed parent |
| v0.9.5.2 | physical measurement closure | committed parent |
| v0.9.5.3 | follow-up measurements | 25-path untracked read-only lane |
| v0.9.6.0 | submerged-power architecture and waterproof/power rules | 40-path untracked read-only lane |

ESP32 dimensions are physical measured. MD10C outline/pattern and electrical capabilities are drawing references. Motor/vendor current and torque values are reference data. Cable identity and purchased length are known while cable OD is not. Every unknown is retained explicitly rather than inferred.
