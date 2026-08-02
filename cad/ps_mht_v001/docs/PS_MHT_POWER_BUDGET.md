# PS-MHT Power Budget

Phase: **3CB-0 sensitivity audit**  
Status: **MEASUREMENT_REQUIRED / 40–50 Wh PER DAY TARGET NOT VERIFIED**

## 1. Energy model

Daily battery-side energy is:

`E_day = P_pump*t_pump/(60*eta_drive) + 24*P_standby +
sum(P_sensor_i*t_sensor_i) + E_control_switching`

where power is W, runtime is minutes or hours as appropriate, and
`eta_drive` includes DC-DC/wiring losses only if the wattmeter is downstream.
If the integrating wattmeter is at the battery, do not apply the loss twice.

The 20 W, 24-hour reference is `20*24 = 480 Wh/day`. The 20 W,
80-minute hypothesis is `20*80/60 = 26.7 Wh/day` for the pump only.

## 2. Pump sensitivity

| Measured pump input | 40 min/day | 80 min/day | 120 min/day |
|---:|---:|---:|---:|
| 15 W | 10.0 Wh | 20.0 Wh | 30.0 Wh |
| 20 W | 13.3 Wh | 26.7 Wh | 40.0 Wh |
| 30 W | 20.0 Wh | 40.0 Wh | 60.0 Wh |

The selected pump is not characterized by nameplate wattage alone. Record:

- battery-side and pump-side voltage/current,
- start current and start duration,
- static lift to each upper tank,
- four-branch flow at that lift,
- pressure/flow change as screens foul,
- time and energy to refill 3/4/5 L upper tanks,
- lower-tank minimum level and cavitation behavior.

For four upper tanks and a 2 L pipe sensitivity allowance, each batch is
14/18/22 L for 3/4/5 L tanks. Fill time is `V_batch/Q_actual`. Example only:
an 18 L batch takes 3.0/1.8/1.29 minutes at measured total flows of
6/10/14 L/min.

## 3. Ancillary power budget

The 40–50 Wh/day target is plausible only if standby loads are controlled.
For the 20 W/80-minute example:

| Budget line | Sensitivity |
|---|---:|
| Pump output/input reference | 26.7 Wh/day |
| 90% drive efficiency loss | 3.0 Wh/day |
| Timer/controller | 5–10 Wh/day candidate band |
| Sensors/data logging | 2–8 Wh/day candidate band |
| Total | 36.7–47.7 Wh/day |

These ancillary bands are assumptions for sizing, not measurements. A
controller drawing 1 W continuously consumes 24 Wh/day and would invalidate
the target by itself.

## 4. Candidate schedule equations

- Stage 1: `t_day = 25 + 10*N_day_2h + 5*N_night_3h` minutes.
- Stage 2: `t_day = 25 + 10*N_day_3h` minutes.

Counts depend on the actual daylight/night windows. Night shutdown is not
accepted until progressive 1/3/6/9/12-hour moisture tests pass.

## 5. Battery usable energy

For a conservative 12 V basis:

`E_nominal = 12*Ah`

`E_usable = E_nominal*DoD*k_temperature*k_aging`

The table uses 80% depth of discharge, `k_aging=1.0`, and either room
temperature or a 0.8 cold factor. Battery BMS limits, actual 12.8 V nominal,
aging and starting current still require vendor/bench verification.

| Battery | Nominal | Usable at 80% DoD | Usable with 0.8 cold factor |
|---|---:|---:|---:|
| 12 V 20 Ah | 240 Wh | 192.0 Wh | 153.6 Wh |
| 12 V 30 Ah | 360 Wh | 288.0 Wh | 230.4 Wh |

## 6. Runtime sensitivity

| Battery | 40 Wh/day room | 50 Wh/day room | 40 Wh/day cold | 50 Wh/day cold |
|---|---:|---:|---:|---:|
| 20 Ah | 4.80 d | 3.84 d | 3.84 d | 3.07 d |
| 30 Ah | 7.20 d | 5.76 d | 5.76 d | 4.61 d |

Both nominal sizes can cover a 2–3-day target in this arithmetic, but the
20 Ah cold/high-load case leaves little allowance for aging, rescue cycles or
failed starts. The 30 Ah candidate provides more experimental margin at higher
mass and cost. No battery is selected before measured `E_day`, surge current,
BMS behavior and cold capacity are available.

## 7. Upper-tank load and support moment

Water-only mass is 3/4/5 kg per tower and 12/16/20 kg for four towers. The
water-only cantilever moment is:

`M = rho*V*g*e`

| Tank water | e=0.10 m | e=0.15 m | e=0.20 m |
|---:|---:|---:|---:|
| 3 L | 2.94 Nm | 4.41 Nm | 5.88 Nm |
| 4 L | 3.92 Nm | 5.88 Nm | 7.85 Nm |
| 5 L | 4.90 Nm | 7.35 Nm | 9.81 Nm |

Add tank, lid, valve, hose and dynamic service loads before structural
selection, then apply an approved safety factor. The PETG tower shell is not
part of this load path.

## 8. Required measurements and stop rules

Phase 3CB-C must measure a complete 24-hour battery-side energy balance under
representative head and weather. Stop an energy claim if a meter boundary is
unclear, rescue cycles are excluded, lower flow is caused by clogging, or the
buffer/control comparison does not meet equal plant-moisture conditions.
Report energy reduction as measured paired data with uncertainty, never as an
assumed 80–90% result.
