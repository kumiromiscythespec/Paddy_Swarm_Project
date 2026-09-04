# PHYSICAL TEST PROTOCOL

Status before testing: `CAD_COMPLETE_OUTWARD_DRAIN_LABYRINTH_PHYSICAL_VALIDATION_PENDING`

Test only the lower/upper coupon pair first. Keep full-shell printing and testing on HOLD until the coupon gate passes. Use actual Ø3.8 and Ø4.0 mm cables, dry tissue in the `WITNESS_BAY`, and record water volume for each application. Suggested pipette volume is 1–3 mL.

## 1. Assembly test

```text
V004 OUTWARD-DRAIN ASSEMBLY

Ø3.8 cable side-load:
PASS / FAIL

Ø4.0 cable side-load:
PASS / FAIL

upper closes:
YES / NO

cable pinch:
NONE / YES

end threading:
NONE / REQUIRED

cable cutting:
NONE / REQUIRED

remove/reinstall ×5:
PASS / FAIL

RESULT:
PASS / FAIL
```

Assembly PASS status: `OUTWARD_DRAIN_ASSEMBLY_PHYSICAL_PASS`

## 2. Water test

Run each required test separately with a fresh dry witness. Record the applied amount. Run the principal gravity-water sequence at LEVEL, +5°, and -5°. If possible, repeat at the Installation Authority orientation: vertical support pipe, drip loop below the cover, drains downward.

Order:

1. TOP SPRAY
2. SIDE SPRAY
3. CABLE TRACKING WATER
4. WEAK DIRECT PIPETTE
5. STRONG DIRECT PIPETTE — RECORD ONLY

```text
V004 WATER TEST

orientation: LEVEL / +5deg / -5deg / INSTALLED

TOP SPRAY:
water introduced: ___ mL
witness = DRY / TRACE / WET

SIDE SPRAY:
water introduced: ___ mL
witness = DRY / TRACE / WET

CABLE TRACKING:
water introduced: ___ mL
witness = DRY / TRACE / WET

WEAK DIRECT JET:
water introduced: ___ mL
witness = DRY / TRACE / WET

STRONG DIRECT JET:
water introduced: ___ mL
witness = DRY / TRACE / WET
PASS REQUIRED = NO

DRAIN:
YES / NO

POOLING AFTER 5 MIN:
NONE / YES

RESULT:
PASS / FAIL / HOLD
```

## 3. Coupon PASS gate

All required conditions must pass:

```text
SIDE LOAD = PASS
CABLE PINCH = NONE
TOP = DRY
SIDE = DRY
CABLE TRACKING = DRY
WEAK DIRECT = DRY
DRAIN = FUNCTIONAL
POOLING AFTER 5 MIN = NONE
```

A WET strong-direct result alone does not fail the coupon when every required condition above passes. Record it as `PRESSURE_JET_LIMIT_OBSERVED`. Do not represent it as pressure-jet performance.

Water coupon PASS status: `OUTWARD_DRAIN_LABYRINTH_WATER_PHYSICAL_PASS`

## 4. Full-shell gate and progression

Only after assembly and water coupon PASS may the full shell proceed:

1. Dry assembly and witness placement
2. Unpowered top, side, cable-tracking, and weak-direct spray testing
3. Open shell and inspect connector/witness after every condition
4. Require dry connector and witness, functional drains, no pooling, and maintained closure
5. Only after unpowered PASS, perform controlled powered USB testing

Statuses are independent:

- `OUTWARD_DRAIN_ASSEMBLY_PHYSICAL_PASS`
- `OUTWARD_DRAIN_LABYRINTH_WATER_PHYSICAL_PASS`
- `USB_RAINCOVER_V004_UNPOWERED_RAIN_PASS`
- `USB_RAINCOVER_V004_LIVE_OPERATIONAL_PASS`
- Heavy/wind-driven/long-duration field rain: separate status

## 5. After-print order

1. Side-load cable fit
2. Upper closure
3. Remove/reinstall ×5
4. Top spray
5. Side spray
6. Cable tracking water
7. Weak direct pipette
8. Strong pipette record-only
9. ±5° test
10. Full-shell GO/NO-GO

