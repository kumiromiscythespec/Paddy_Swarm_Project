# PHYSICAL RESULTS INHERITED FROM v001

## V001 CABLE COUPON PHYSICAL RESULT

```text
camera cable:
measured OD = 3.8 mm

extension cable:
measured OD = 4.0 mm

4.4 mm coupon:
PASS BOTH CABLES

result:
CABLE_CHANNEL_PHYSICAL_PASS
selected channel = 4.4 mm
```

Observation: both cables passed with clearance, without forced insertion or notable jacket compression. This is the Physical Authority for both v002 cable ports. It is not a compression waterproof seal. No 4.4/4.6/4.8 mm re-exploration coupon is required and no cable coupon is in `NEXT_PRINT`.

## V001 PROVISIONAL CHAMBER RECORD

```text
V001 CHAMBER
nominal length = 50.0 mm

physical required envelope length = 95.1 mm

RESULT:
REJECTED_UNDERSIZED
```

Disposition: `PROVISIONAL_DIMENSION_SUPERSEDED_BY_PHYSICAL_MEASUREMENT`. This is not a CAD failure of the v001 geometry validation. The provisional 7.9 mm cable Authority is likewise superseded by physical measurement, and the 9.0 mm large channel is no longer required.
