# Battery-fit temporary BBOX physical packaging authority

Specimen identity: `BATTERY_FIT_TEMPORARY_BBOX`.

This is not the waterproof V002 specimen and is not proven compatible with V003. It records physical battery packaging only.

## Direct and derived dimensions

| Quantity | Value | Classification |
|---|---:|---|
| body true lowest Z | 144 mm | PHYSICAL_DIRECT |
| body rim Z | 254 mm | PHYSICAL_DIRECT |
| external body height | 110 mm | PHYSICAL_DERIVED (`254-144`) |
| X reference to BBOX front | 345 mm | PHYSICAL_DIRECT |
| X reference to BBOX rear | 500 mm | PHYSICAL_DIRECT |
| external X length | 155 mm | PHYSICAL_DERIVED (`500-345`) |
| left upper-rail inner face to BBOX left | 55 mm | PHYSICAL_DIRECT |
| BBOX right to right upper-rail inner face | 0 mm | PHYSICAL_DIRECT |
| external Y width | 71.9 mm | PHYSICAL_DIRECT |
| internal usable X | 152 mm | PHYSICAL_DIRECT |
| internal usable Y | 65.5 mm | PHYSICAL_DIRECT |
| internal usable Z | 104 mm | PHYSICAL_DIRECT |

`X_TRANSFORM_STATUS = PARTIAL_PHYSICAL`: the two measured distances and derived length are retained, but the X_REF physical feature has not been completely identified. No global X=0 is invented.

The Y measurements remain face-relative. They are not converted into absolute vehicle Y and do not promote local `±94.5 mm` to physical authority.

## Physical result

- `BATTERY_INSERTION = PHYSICAL_FIT_PASS`
- `BATTERY_PRESENT_IN_BOX = PHYSICAL_FIT_PASS`
- measured terminal highest point: approximately `3 mm` below rim (`PHYSICAL_DIRECT / FIELD_APPROXIMATE`)

Not measured for this specimen:

- `FLAT_LID_TOP_Z`
- `CHIMNEY_TOP_Z`
- `GLAND_CABLE_HIGHEST_Z`

No waterproof, lid-closure, restraint, vibration, powered, mud, durability, or field result is inferred.
