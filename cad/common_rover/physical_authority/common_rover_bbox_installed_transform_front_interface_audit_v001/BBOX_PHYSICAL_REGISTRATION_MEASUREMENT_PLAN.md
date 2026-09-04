# BBOX physical registration measurement plan

Purpose: close the current BBOX and Front Interface transforms without disassembly where possible. Use the current installed rover. First-registration accuracy is `±1 mm`; `±0.5 mm` is preferred where caliper access permits. Do not imply sub-0.1 mm field-frame precision.

## Datum setup

- Z: crawler/floor contact plane = `Z0`.
- X: choose the **front face of one clearly identified current upper 2040 crossmember**; mark it and call it `X_REF=0`. Photograph the chosen face and record whether +X is vehicle-forward.
- Y: do not invent a centerline. Measure from identified left/right upper-rail inner and outer faces.

Top view:

```text
                         +X vehicle front
                                ^
 X_REF = chosen 2040 face  ------|----------------
                                |<-- A --> [BBOX front face]
                                |<------- B ------>[BBOX rear face]

 left rail outer |inner|    C ->+-------------------+<- D   |inner|outer right rail
                                 |       BBOX        |
                                 +-------------------+
                       record which rail face each value uses
```

Side view:

```text
 Z
 ^                         H = chimney highest
 |                    +----+----+
 |        G = flat lid+---------+          K = Front Interface highest solid
 |        F = rim/mating region
 |        E = true shell/body lowest       J = nearest rearward face X
 |____________________________________________ crawler/floor = Z0
                                               I/J/K use actual installed solid only
```

## Measurement sheet

| ID | Measure on current rover | Record |
|---|---|---|
| A | `X_REF` face to BBOX front outer face | value, tool, repeated min/max, sign |
| B | `X_REF` face to BBOX rear outer face | value, tool, repeated min/max, sign |
| C | identified left upper-rail inner **and/or outer** face to BBOX left outer face | value and exact rail face used |
| D | identified right upper-rail inner **and/or outer** face to BBOX right outer face | value and exact rail face used |
| E | BBOX shell/body true lowest Z | identify whether shell floor, lug, support, or other feature |
| F | BBOX top body rim / lid mating-region Z | state accessible feature and lid installed/removed |
| G | flat lid top Z, away from chimney/hardware | at least two points; record tilt/range |
| H | chimney highest Z | identify printed chimney vs gland/hardware |
| I | `X_REF` to Front Interface nearest rearward **physical solid** face | value and component name |
| J | Front Interface lowest physical solid Z | value and component name |
| K | Front Interface highest physical solid Z | value and component name |
| L | Is Front Interface V002 actually installed? | `YES / NO / PARTIAL`; list installed/superseded components |

Also record:

1. BBOX specimen identity: body revision/lane if known, lid revision/lane, visible markings, photos.
2. Whether V003 chimney and PG9 gland are installed during G/H.
3. Whether any cradle, spacer, strap, rubber pad, rail, or fastener lies below the printed body.
4. BBOX yaw: compare A/B at left and right edges if accessible.
5. Front Interface identification: beam length/section, unit-mount crossrails present, support plates present, and fastener count.

## Closure criteria

Registration may be promoted only when:

- A and B establish BBOX X and longitudinal extent against the same X reference;
- C and D establish BBOX Y relative to both rails without assuming centerline;
- E/F/G/H identify the physical surfaces corresponding to V002/V003 CAD datums;
- I/J/K/L establish that the Front Interface exists and locate it in the same physical frame system;
- repeated values agree within ±1 mm (±0.5 mm preferred);
- specimen identity matches the exact V002/V003 sources or is explicitly reclassified.

Until then: `BBOX_INSTALLED_TRANSFORM_PARTIAL / PHYSICAL_XY_MEASUREMENT_REQUIRED`.
