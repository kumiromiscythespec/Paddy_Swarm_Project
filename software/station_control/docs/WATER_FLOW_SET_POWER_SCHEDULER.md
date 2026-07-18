# Water-Flow Set Power Scheduler

## 1. Status

ST-011 is an experimental, deterministic, offline planning simulator. Its reports are engineering evidence, not authorization to operate machinery, charge batteries, cross roads, or perform unattended work.

## 2. Purpose

The scheduler compares persistent operation of 12 dummy weed rovers across 19 estimated fields and seven provisional water-flow sets. It evaluates 10-, 14-, and 21-day targets under separate grid-only and portable-pack-only power assumptions.

## 3. Safety Boundary

The process performs no network, rover, GPIO, serial, motor, PTO, charger, or BMS communication. It does not assign or arm missions. Battery swaps, rover transfers, and station transfers remain manual. Automatic restart, automatic battery swap, autonomous inter-field transfer, and autonomous public-road crossing are prohibited. Physical ESTOP remains independent.

Field, night, and unattended operation are not approved. All output represents offline calculations only.

## 4. ST-010 Reuse

The implementation loads the checked-in ST-010 module with the standard library and verifies its `ST-010` phase marker and public validation functions. ST-010 remains the source of the 19-field model and field-level planning distance. ST-011 does not copy or silently replace that algorithm.

## 5. Water-Flow Set Model

The fixed provisional sets are `SET-HOME-01`, `SET-HOME-02`, `SET-HOME-03`, `SET-OTHER-CONSIGNED-01`, `SET-CONSIGNED-01`, `SET-OWN-A-01`, and `SET-OWN-B-01`. Their sizes are 3, 3, 3, 3, 2, 2, and 3 fields. Together they cover 19 fields, 27,000 square metres, and 103,500,006 millimetres of planning distance.

This mapping is provisional and contains no exact coordinates. Actual water-flow relationships require measurement and human review.

## 6. Persistent Deployment

At the start of a set, all 12 rovers are manually delivered and the station is delivered on a separate trip. Rovers and station remain at the set over successive simulated days until that set completes. The model does not assume daily rover recovery or daily station removal. Overnight parking and security require validation.

## 7. Set Transfer

A set transfer can be recorded only after every field in the current set completes and the rovers stop. Rover and station movement are manual and separate. At most one set transfer is allowed per simulated day. The simulator never issues movement authority.

## 8. Work Blocks

The fixed order is `EARLY_MORNING`, `MIDDAY`, and `EVENING_NIGHT`, each with a nominal maximum of 150 minutes. Human service events occur before each corresponding block. Availability is 6,000 basis points. The arithmetic uses integer minutes and integer base units.

## 9. Heat Profiles

`COOL_DAY` permits 150/150/150 minutes. `HOT_DAY` permits 150/0/150 minutes. `EXTREME_HEAT` permits 120/0/120 minutes. These profiles are deterministic stress cases, not weather probabilities or forecasts.

## 10. Night Operation

Night speed factors are 7,000, 8,500, and 10,000 basis points. The 10,000-basis-point case is an upper comparison bound, not a measured approval value. Night operation always requires field testing and remains unapproved.

## 11. Rover Battery Model

The dummy LiFePO4 battery has 128,000 mWh nominal energy, 102,400 mWh usable energy, 150 minutes of runtime, a 180-minute full-charge assumption, and a three-minute manual swap. Pools of 16, 24, and 36 batteries are compared. State carries across blocks, days, and sets; there is no daily reset. FIFO ordering is deterministic, and a rover may hold only one battery.

## 12. Five-Charger Model

Five identical chargers are modeled. Each full recharge requires 102,400 mWh over 180 minutes, represented exactly as `Fraction(102400, 180)` mWh per minute. Charger ordering is deterministic. The software models availability; it never controls a charger.

## 13. Grid Always-On Mode

`GRID_ALWAYS_ON` assumes uninterrupted input to five chargers for 24 hours. Its theoretical ceiling is 40 full sessions or 4,096,000 mWh per day. Portable modules are zero in this mode. This is an electrical planning assumption, not approval of an installation.

## 14. Portable Pack-Only Mode

`PORTABLE_PACK_ONLY` assumes zero grid input. A delivered station pack can feed chargers only; it cannot connect directly to a rover or a rover battery. Pack replacement is manual. Unused energy is discarded at the next pack exchange, while partial charger progress is retained by the model. Depot recharge and depot inventory are outside scope.

## 15. Pack Energy and Weight

Each assumed module is 128,000 mWh and 1,200 g. After a 1,000-basis-point reserve and 8,500-basis-point conversion efficiency, delivered energy is 97,920 mWh per module. A provisional 1,200 g auxiliary mass is added.

Five, six, seven, and eight modules therefore deliver 489,600, 587,520, 685,440, and 783,360 mWh. Total masses are 7,200, 8,400, 9,600, and 10,800 g. Seven modules meet the 10 kg engineering target; eight do not. Module energy and complete-pack mass require measurement.

## 16. Pack Service Cadence

The matrix compares one morning delivery, morning-and-evening delivery, and three-service delivery. Each exchange assumes 10 minutes for the manual pack swap and 20 minutes for the vehicle visit. Formal variants never exceed three deliveries per day.

## 17. Energy Sustainability

Sustainability is evaluated separately from completion. It requires no daily energy shortfall or charger starvation and no declining effective battery supply over the final evaluation window. A simulation can execute successfully while its operating mode is infeasible.

## 18. Grid-versus-Pack Comparison

Every pack result is matched to the grid result with the same allocation policy, speed, heat profile, night factor, deadline, and battery pool. The report records completion, field, wait, and energy differences and the additional pack deliveries that would be required. GRID and PACK are mutually exclusive; hybrid operation is not evaluated.

## 19. Required Portable Capacity

Thirty-six full sessions require 3,686,400 mWh. At 97,920 mWh per module, the design requirement is 38 modules per day. That is six deliveries of a seven-module pack or five deliveries of an eight-module pack. Both exceed the formal maximum of three deliveries; the eight-module pack also exceeds the 10 kg target. The report must not describe any formal pack variant as grid-equivalent without satisfying the matched criteria.

## 20. Ten, Fourteen, and Twenty-One Day Targets

Each formal configuration contains exactly one 10-, 14-, or 21-day deadline. Completion percentage and feasibility are retained without converting an infeasible physical plan into a passing claim.

## 21. Report Interpretation

`result=PASS` means the deterministic offline evaluation completed and its contract checks passed. `FEASIBLE`, `MARGINAL`, and `INFEASIBLE` describe operating results by power mode. Diagnostics, bottlenecks, review flags, and recommendations remain ordered and reproducible.

## 22. Orange Pi Validation

The same six source files, plan, isolated Python invocation, and external report paths are used on Orange Pi. Source hashes, tests, fresh A/B reports, canonical hashes, configuration results, matched comparisons, selections, required capacity, diagnostics, and recommendations are compared with Windows output. No package installation or operating-system change is required.

## 23. CLI Usage

Run with Python 3.11 standard library only:

```text
python3 -I -B software/station_control/station/water_flow_set_power_scheduler.py --repository-root <repository> --plan software/station_control/config_examples/water-flow-set-power-plan.example.json --json-report <external>/water-flow-set-power-report.json --text-report <external>/water-flow-set-power-report.txt
```

Both report parents must already exist, the two paths must differ, and reports are rejected if they resolve inside the repository.

## 24. Measurement Replacement Plan

Replace provisional assumptions only after measuring actual water-flow sets, rover speed, rover energy use, night speed, portable module delivered capacity, complete pack mass, connector/fuse/BMS behavior, charger input compatibility, grid availability, field safety, and overnight security. Preserve the plan version and update the contract intentionally when measurements are approved.

## 25. Current Non-Goals

This phase does not implement live rovers, networking, hardware access, control authority, hybrid power, weather prediction, purchasing advice, field approval, night approval, unattended approval, automatic transfer, automatic charging actions, automatic battery swap, Web UI, databases, services, or deployment configuration.
