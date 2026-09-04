# BBOX installed-transform audit

Final status: `TRANSFORM_PARTIAL_PHYSICAL_MEASUREMENT_REQUIRED`

## Exact local assembly

- V002 body STEP bounds: `X=-120..120`, `Y=-95..95`, `Z=0..70.895 mm`.
- V003 lid STEP bounds: `X=-120..120`, `Y=-95..95`, `Z=0..58 mm` (the importer reports a numerical lower tolerance near `-0.0000001 mm`).
- Correct seal-interface join: `V003_LID_RELATIVE_TO_V002_BODY = Tx0, Ty0, Tz70.895, Rx0, Ry0, Rz0`.
- Combined bounds: `Z=0..128.895 mm`.
- `CAD_COMBINED_BBOX_HEIGHT = 128.895 mm`.

## Direct physical record

- `BBOX_BODY_LOWEST_Z = 148.0 mm` (`DIRECT_PHYSICAL`).
- `BBOX_LID_HIGHEST_Z = 254.0 mm` (`DIRECT_PHYSICAL`).
- `PHYSICAL_COMBINED_BBOX_HEIGHT = 254 - 148 = 106.0 mm` (`PHYSICAL_DERIVED`).
- `CAD_COMBINED_BBOX_HEIGHT - PHYSICAL_COMBINED_BBOX_HEIGHT = 22.895 mm`.

The task’s `Z_CONFLICT_DELTA = 175.105 - 148 = 27.105 mm` is also preserved exactly. It arises only when the V003 **flat lid top** at assembly-local `Z78.895` is aligned to global `Z254`; that translation places the V002 body bottom at `Z175.105`.

## Z-transform candidates

| Candidate | Assumption | Global translation Tz | Resulting body bottom | Flat lid top | Chimney top | Residual against protected source |
|---|---|---:|---:|---:|---:|---|
| Z-P | exact CAD body bottom is physical Z148 | 148.000 | 148.000 | 226.895 | 276.895 | flat-to-254 = -27.105; chimney-to-254 = +22.895 |
| Z-L-FLAT | physical Z254 means flat lid top | 175.105 | 175.105 | 254.000 | 304.000 | body-bottom residual = +27.105 |
| Z-L-CHIMNEY | physical Z254 means chimney top | 125.105 | 125.105 | 204.000 | 254.000 | body-bottom residual = -22.895 |

No candidate satisfies both protected physical values. No averaging or compromise transform is authorized.

## XY and Front Interface gates

- Physical BBOX X datums found: `0`.
- Physical BBOX Y datums found: `0`.
- Independent physical XY locator pairs found: `0` (minimum required: `2`).
- Cross Saddle `(X,Y)=(0,0)` is `DERIVED_MOUNT_ASSUMPTION`, not physical authority.
- Front Interface V002 installed state: `NOT_PROVEN_MANUFACTURED_OR_INSTALLED`.
- Front Interface installed transform: `PHYSICAL_PENDING`.

Because both registered objects lack a common physical XY transform and the Front Interface’s installed transform is unresolved, Section 15’s permission condition is false. No collision rerun or physical-conflict promotion is allowed.

## Decision

The exact CAD sources and their local join are known, but the installed object’s measured feature definitions, physical XY placement, and Front Interface installed transform are not. A specimen/revision mismatch is possible, but the ambiguous Z254/Z148 point definitions prevent promoting it to `BBOX_SPECIMEN_GEOMETRY_MISMATCH` yet.

Authority state:

`BBOX_INSTALLED_TRANSFORM_PARTIAL / PHYSICAL_XY_MEASUREMENT_REQUIRED / PHYSICAL_POINT_DEFINITION_AMBIGUOUS`
