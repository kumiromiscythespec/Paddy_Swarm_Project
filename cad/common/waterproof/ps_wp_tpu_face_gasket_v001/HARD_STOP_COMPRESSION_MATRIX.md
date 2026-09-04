# Hard-stop compression matrix

All ratios below are NOMINAL_DESIGN_REFERENCE, not physical results.

| Gasket | S16 | S18 | S20 | S22 | S24 |
|---|---:|---:|---:|---:|---:|
|G20|20.0%|10.0%|0.0%|-10.0%|-20.0%|
|G25|36.0%|28.0%|20.0%|12.0%|4.0%|
|G30|46.7%|40.0%|33.3%|26.7%|20.0%|

Primary G25/S20:20%. Adjacent later G25/S18:28%, G25/S22:12%. Nominal20% comparisons G20/S16 and G30/S24.
Zero/negative compression combinations are NOT sealing tests; configurations over30% are high-compression physical HOLD, not an approved operating window. Do not force the gasket or damage PETG to reach a stop.

The same body and lid fit every spacer set; all four collars must be from ONE set. Files contain four separate collars, OD8 / bore4.5, at22 x22 mm print-set bounds. No marks alter flat working faces. Label bags/files rather than sealing/stop surfaces. Do not print every set initially.

Flat PETG land is10 mm rather than the suggested5.5-6: an area-conserving, constant-perimeter rectangular estimate needs width5*t/gap. G25/S20 gives6.25 mm, G25/S18 gives6.944444 mm. A nominal registration budget includes0.25 body-hole/bolt +0.25 stop-hole/bolt +0.30 ear/stop =0.80 mm; printed distortion is additional and unmeasured. Land margins after this budget are1.075 and0.727778 mm respectively. The planned configurations have independent eight-direction CAD reservation-support checks. Actual TPU bulging, porosity and stretch are NOT simulated by this estimate.
The extreme G30/S16 needs9.375 mm and has NEGATIVE0.4875 mm land margin after the0.80 budget: UNSUPPORTED_EXTREME_NOT_APPROVED. It is a mathematical reference, NOT a test configuration. All provided parts remain interchangeable for their intended pairings, but not all15 cross-combinations are acceptable sealing configurations. Test a window physically later; none is claimed now.

Actual compression uses FREE measured TPU thickness and independently measured CLOSED face gap:

`r = (t_free - gap_closed) / t_free`

Conservative range: `r_min = 1 - gap_max/t_min`; mean estimate `1 - gap_mean/t_mean`; `r_max = 1 - gap_min/t_max`.
Measure S1-S4 AND closed gaps G1-G4: unequal spacers or lid warp can make nominal spacer thickness an invalid global-gap assumption. Missing measurements remain PENDING; no automatic physical promotion.
