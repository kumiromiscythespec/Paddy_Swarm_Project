# PS-MHT Four-Tower Experiment Plan

Phase: **3CB-0 protocol audit**  
Duration: **30 days after hydraulic commissioning**  
Status: **EXPERIMENT DESIGN PROPOSED / NOT STARTED**

## 1. Experimental question

Primary question: does the capillary-buffer circulation architecture reduce
battery-side Wh/day while maintaining acceptable moisture, plant condition,
hydraulic reliability and serviceability relative to conventional circulation?

The draft assignment with three different buffer/media/wick towers and one
control changes too many variables and has no replicated treatment. It may be
used only as an exploratory screen, not as evidence that the architecture
caused a result.

## 2. Recommended four-tower allocation

| Tower | Hydraulic treatment | Medium | Wick | Role |
|---|---|---|---|---|
| A | Capillary buffer | Selected common medium | Selected common wick | Replicate 1 |
| B | Capillary buffer | Same as A | Same as A | Replicate 2 |
| C | Conventional circulation | Same as A | Same geometry where applicable | Control 1 |
| D | Conventional circulation | Same as A | Same geometry where applicable | Control 2 |

Block towers spatially as two pairs, each containing one buffer and one
control. Randomize treatment within each block. Do not place both buffer towers
on the same sun/wind side.

Italian parsley and chive are distributed across corresponding stage/azimuth
positions in every tower using a mirrored allocation. Plant-level observations
are subsamples; the tower is the hydraulic experimental unit (`n=2` per
treatment). The low tower-level replication is reported explicitly and no
production-scale inference is made from p-values alone.

If media or wick must be compared, perform the bench/pot screening first or
run a later second 30-day block with new matched seedlings. Do not confound the
primary circulation comparison.

## 3. Commissioning before day 1

1. Measure usable lower-tank volume, pump minimum water, pipe inventory and
   free-return volume.
2. Measure each branch flow at actual lift and adjust to within +/-10% of the
   four-branch mean.
3. Verify emergency overflow at 150% of maximum measured branch inflow.
4. Perform power-loss and siphon tests with no plants.
5. Leak-test every joint for 12 hours and record collected external leakage.
6. Calibrate EC, pH, temperature, mass/volume and moisture instruments.
7. Establish rescue irrigation and pump-bypass procedures.

## 4. Controlled variables

- One mixed batch of canal water and Hyponica A/B solution for all towers.
- Same EC/pH target band and adjustment process.
- Matched seedling age, starting mass/leaf count and transplant date.
- Same pot lot, pot-passage candidate and medium dry mass.
- Same wick lot, count, length, prewash and immersion in buffer towers.
- Matched light and wind by blocking; record actual PAR/light proxy and air
  temperature instead of assuming equality.
- Same sampling time relative to pump cycle.
- Stage and azimuth allocation mirrored among towers.

## 5. Off-time progression

Night shutdown is not an initial pass condition. Advance only after the prior
step completes without rescue:

1. 1-hour hold.
2. 3-hour hold.
3. 6-hour hold.
4. 9-hour hold.
5. 12-hour hold.

Repeat each step at least three times under recorded weather. A rescue event
stops escalation, restores the last safe schedule and is retained in the data.

Schedule formulas remain variable:

- Stage-1 daily runtime: `25 + 10*N_day_2h + 5*N_night_3h` minutes.
- Stage-2 daily runtime: `25 + 10*N_day_3h` minutes.

For example only, `N_day_2h=4` and `N_night_3h=3` produces 80 minutes/day.

## 6. Measurements and frequency

| Variable | Frequency | Method |
|---|---|---|
| Pump voltage/current/Wh/runtime | Continuous/integrated daily | DC integrating wattmeter plus event log |
| Four branch flows and upper fill time | Daily first week, then 3x/week | Timed mass/volume |
| Lower and upper tank levels | Each cycle during commissioning; min/max daily | Calibrated level marks/sensor |
| Medium moisture | Before/after representative cycles; at 1/3/6/9/12 h tests | Medium-specific calibrated sensor plus gravimetric checks |
| Wilt score | Twice daily and end of hold | 0–4 photo-referenced scale |
| EC/pH/water temperature | In common tank daily; module top/mid/bottom 3x/week | Calibrated meters at fixed cycle phase |
| Water addition and collected leak | Daily | Mass or graduated volume |
| Growth | Weekly | Leaf count, canopy image, fresh mass only at scheduled harvest |
| Wick/overflow/root/algae condition | Weekly and at any flow alarm | Photo and obstruction/flow record |
| Cleaning/replacement time | Every service event | Stopwatch and operator notes |

## 7. Data record

Use one long-form CSV row per observation with at least:

`timestamp, day, tower, treatment, spatial_block, stage, port_azimuth,
crop, plant_id, medium_lot, wick_lot, schedule_id, pump_event_id,
voltage_V, current_A, energy_Wh, runtime_min, branch_flow_L_min,
upper_volume_L, lower_level_L, buffer_level_mm, VWC_percent,
EC_mS_cm, pH, water_temp_C, air_temp_C, RH_percent, light_proxy,
wilt_score_0_4, leak_mL, rescue_code, clog_code, root_code,
cleaning_minutes, operator, notes`

Never overwrite raw observations. Corrections are appended with reason and
source row identifier.

## 8. Candidate acceptance thresholds

Thresholds are protocol candidates and require approval before day 1:

- Twelve-hour VWC at least 60% of post-drain starting VWC for that medium.
- Wilt score <=1/4 and no rescue irrigation.
- Normal standing water at least 5 mm below the net-pot body.
- Branch flow within +/-10% of four-branch mean after adjustment.
- Overflow retains at least 80% of clean baseline flow after 30 days and never
  becomes fully blocked.
- Stage EC coefficient of variation <=10% and max-min <=0.4 mS/cm at the
  specified sample phase.
- Flow-control delivery loss <=20% over 72 hours without cleaning.
- External static leakage <=5 mL per joint per 12 hours and no continuous jet.
- Module drain/open/clean/reassemble <=15 minutes; wick replacement <=5
  minutes per port.
- Buffer treatment battery-side Wh/day at least 50% below continuous control
  over a stable seven-day window while all agronomic/hydraulic criteria pass.

The 50% energy threshold is a proposed experiment criterion, not an achieved
80–90% claim.

## 9. Emergency/rescue rules

Start rescue circulation and log the event if any of these occurs:

- wilt score reaches 2,
- VWC falls below the pre-approved crop/medium floor,
- any stage has no measurable inflow during a commanded cycle,
- normal water reaches the net-pot body,
- lower tank approaches the measured pump minimum,
- external leakage becomes a continuous stream,
- EC or temperature exceeds the agronomic operating band,
- pump current departs more than 20% from its commissioned value without an
  explained voltage change.

Rescued observations remain valid safety data but do not count as a successful
off-time repetition.

## 10. Stop conditions

Stop the trial for structural instability, exposed electrical hazard,
uncontained overflow, repeated complete root/overflow blockage, inability to
restore equal branch flow, or a lower tank unable to accept the measured
power-loss return. Stop the architecture decision if the treatment effect
cannot be separated from spatial, crop, medium or wick differences.
