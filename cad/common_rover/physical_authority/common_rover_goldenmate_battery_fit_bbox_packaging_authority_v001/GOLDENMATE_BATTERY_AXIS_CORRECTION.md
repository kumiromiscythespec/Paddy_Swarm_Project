# GoldenMate battery axis correction

## Correct physical roles

| Quantity | Value | Classification |
|---|---:|---|
| battery long dimension | 150.9 mm | PHYSICAL_DIRECT |
| battery short width | 65.5 mm | PHYSICAL_DIRECT, new role-closing measurement |
| battery body height | 92.5 mm | PHYSICAL_DIRECT |
| bottom to terminal highest | 99.4 mm | PHYSICAL_DIRECT |
| mass | 1.2 kg | PHYSICAL_DIRECT |
| terminal tab width | 6.3 mm | PHYSICAL_DIRECT |
| terminal tab thickness | 0.7 mm | PHYSICAL_DIRECT |
| female receptacle outer width | 10.6 mm | PHYSICAL_DIRECT |

Purchase identity: `GoldenMate LiFePO4`, `12.8 V`, `10 Ah`, `128 Wh`.

Formal geometry:

```text
BATTERY_PLAN_ENVELOPE = 150.9 × 65.5 mm
BATTERY_BODY_VERTICAL_HEIGHT = 92.5 mm
BATTERY_TERMINAL_INCLUSIVE_HEIGHT = 99.4 mm
```

`150.9 × 99.4 × 92.5 mm` must not be encoded as an XYZ battery-body envelope.

## Supersession scope

The read-only electrical authority stores `[150.9, 99.4, 92.5]` under `overall_body_dimensions_mm`, labels the set as “battery body,” repeats it in CSV/Markdown, and contract-tests the list. It also cautions that order was preserved and axes must not be silently remapped. Thus the original lane did not prove an explicit axis map, but its body-dimension labeling enabled downstream XYZ-style use.

The Field Box V001 report then explicitly used `99.4 mm` as BBOX plan-Y width in Orientation A and as plan-X width in Orientation B. That dimensional-role use is now:

`OLD_99P4_AS_PLAN_WIDTH = SUPERSEDED_AXIS_INTERPRETATION`

The numbers themselves are not declared false:

- `150.9 = VALID_PHYSICAL_MEASUREMENT`
- `65.5 = NEW_VALID_PHYSICAL_MEASUREMENT`
- `92.5 = VALID_PHYSICAL_MEASUREMENT`
- `99.4 = VALID_PHYSICAL_MEASUREMENT_AS_TERMINAL_INCLUSIVE_HEIGHT`

Existing authority files remain read-only. This lane is the correction/supersession record.
