# Physical water test plan

Run this plan separately for G065 (PRIMARY) and G055 (comparison). Record the actual geometry identity, lid identity, cord identity, joint method, water level and temperature. No water PASS is prefilled.

## Preparation

1. print body and lid in PETG
2. visually inspect:
   - seal groove
   - hard stops
   - M4 towers
   - layer defects
   - corner quality
3. install Ø1.8 mm rubber cord
4. place gasket butt joint on a straight side, not a corner
5. insert completely dry witness paper/tissue
6. close lid
7. tighten M4 screws evenly to hard-stop
8. verify:
   - gasket not visibly displaced
   - no major extrusion
   - lid fully seated
   - PETG no whitening/crack

## Test stages

STAGE 1: UPRIGHT / 10 min

STAGE 2: UPRIGHT / cumulative 30 min

STAGE 3: UPRIGHT / cumulative 60 min

After each stage: inspect only if test protocol requires opening; otherwise continue cumulative exposure to avoid disturbing seal.

Preferred: one uninterrupted 60-minute upright test, with visual external checks at 10 and 30 minutes.

Then if upright PASS:

STAGE 4: tilt front >10°

STAGE 5: tilt rear >10°

STAGE 6: tilt left >10°

STAGE 7: tilt right >10°

Use enough time at each tilt to wet the corresponding seal region. Suggested: 10 minutes each. Do not use excessive external pressure.

For the uninterrupted protocol, the 10/30-minute entries record external observations only; internal dryness is NOT OBSERVED until opening after the run. Do not invent an internal PASS at those times. Note every opening/reclosure and replace wet witness paper before a new independent run.

## Water test safety

No battery. No electronics. No live wiring.

Use only:

- PETG dummy
- rubber gasket
- M4 hardware
- dry paper/tissue

After removal from water: **WIPE EXTERIOR COMPLETELY DRY BEFORE OPENING.**

This is critical to avoid dripping external water into the cavity and creating a false failure.

## Promotion criteria

Only if the 60-minute upright test and all required tilt tests pass, witness paper remains completely dry, the gasket stays seated with no cut, and PETG has no structural damage, may the corresponding actual depth receive a user-recorded water PASS.

- G065: `COMPACT_SEAL_G065_WATER_PHYSICAL_PASS`
- G055: record its independent `COMPACT_SEAL_G055_WATER_PHYSICAL_PASS` only after its own successful test.

If both pass, compare retention/compression/repeatability separately. If only G065 passes, choose 0.65 for a new full-body correction. If only G055 passes, choose 0.55 and document the deeper groove's failure. If both fail, retain full BBOX PRINT HOLD.

This test does not establish FULL_BBOX_WATERPROOF_PASS, CHIMNEY_WATERPROOF_PASS, PG9_WATERPROOF_PASS or FIELD_BBOX_PASS. A winning depth authorizes a NEXT-phase NEW corrected full-box lane, not a patch to the protected existing V003.
