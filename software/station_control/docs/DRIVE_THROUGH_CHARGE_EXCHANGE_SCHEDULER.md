# Drive-Through Charge Exchange Scheduler

## 1. Status

ST-012 is experimental, offline only, and simulation only. It is not production ready and does not approve field deployment, automatic restart, night operation, or unattended operation.

## 2. Purpose

The scheduler compares fixed-onboard rover charging through five independent drive-through bays with GRID reference power and station cassette exchange. It evaluates capacity only; it issues no hardware command.

## 3. Safety Boundary

The program has no rover or mule communication, network, GPIO, serial, motor, steering, PTO, charger, BMS, connector, or contactor authority. It performs no automatic ARM, dispatch, restart, road crossing, or ESTOP release. Physical ESTOP remains independent.

## 4. ST-011 Reuse

ST-011 is loaded through its public strict-JSON, validation, and ST-010 integration functions. Its 19 fields, 7 water-flow sets, 27,000 m2, 103,500,006 mm target, persistent deployment, and one-transfer-per-day boundary are retained under fixed `SET_SEQUENTIAL` allocation.

## 5. Fleet Profiles

The formal comparison uses 22 and 30 rover fleets with 12 target active rovers. Fleet IDs and rover IDs are deterministic; no active count is fabricated.

## 6. Fixed Rover Batteries

Each rover retains its 128,000 mWh nominal, 102,400 mWh usable battery. The 24 and 32 rover battery totals include two maintenance spares respectively. There is no routine rover battery swap or runtime battery transfer.

## 7. Drive-Through Station

Rovers enter, stop, connect, charge, disconnect, and clear a bay in the forward direction. Drive-through forward entry and exit and a queue bypass are required assumptions, not installed-hardware claims.

## 8. Five Independent Charging Bays

Five independent charging bays are split as three in lane A and two in lane B. There is no serial-five blocking model and no shared bay charger resource. Queue capacity is 12 rovers.

## 9. High-Mounted Connector

The model uses a high-mounted connector only after stationary, brake, motor-inhibit, and PTO-inhibit states. Connector identity, voltage, insulation, latch, zero-current, mud resistance, water ingress, and current capability require physical tests.

## 10. Return Energy Reserve

Return comparisons are 25, 50, and 75 m. Required return time is ceiling distance divided by effective speed, and the trigger adds a 10-minute emergency reserve. Insufficient reserve produces manual recovery; distance is never teleported.

## 11. Staggered Rover Rotation

Twelve initial work starts are spread across the 150-minute runtime with a 12-minute base interval and deterministic rover-ID remainder allocation. Staggering changes return peaks but never increases charger capacity.

## 12. Twenty-Two-Rover Operation

`FLEET_22` has 22 installed rover batteries, two maintenance spares, and 24 rover batteries total. It is the formal two-block reference.

## 13. Thirty-Rover Operation

`FLEET_30` has 30 installed rover batteries, two maintenance spares, and 32 rover batteries total. It is the formal three-block reference.

## 14. Station A/B Cassette Slots

Slots A and B allow one verified standby cassette before switching. A/B slots are never directly paralleled and never simultaneously active.

## 15. Horizontal Cassette Exchange

Exchange is a guided horizontal slide, not a robot arm. The sequence verifies latch, identity, voltage, temperature, BMS-ready and precharge, pauses chargers, opens the old contactor at zero current, activates the new slot, and removes the depleted-safe cassette.

## 16. Seven-Module Cassette

Each cassette contains seven common maintenance modules. It delivers 685,440 mWh after reserve and conversion assumptions and has a provisional 9.6 kg complete mass. Exact residual mWh is retained; runtime disassembly is prohibited.

## 17. Six／Eight Cassette Inventories

Six and eight cassette inventories contain 42 and 56 station modules. A cassette has one unique location among station slots, mule cargo, hub charging, hub ready storage, and fault isolation.

## 18. Four-Wheel Battery Mules

Two four-wheel Ackermann mules operate only on registered wide levee routes. There is no crawler assumption, paddy entry, free roaming, public road operation, or public road crossing.

## 19. One-Cassette Payload Rule

One mule carries one cassette. Each trip delivers one full cassette and recovers one depleted cassette; simultaneous two-cassette payload is outside the model.

## 20. Hub Charging

The reference hub has two whole-cassette charge ports and two mule charge ports. Cassette charge time is 180 minutes, and FIFO plus ready time and cassette ID determine selection.

## 21. Segment Reservation

The 50, 100, 200, 300, and 500 m hub routes use narrow-segment reservation. Passing and overtaking are forbidden. Route validity and edge detection require site validation.

## 22. Grid Reference

`GRID_DIRECT_REFERENCE` is an unlimited 24-hour planning reference with no cassette or mule modules. It is not an electrical installation approval and cannot be combined with cassette power as a hybrid.

## 23. Two／Three Work Blocks

The two-block schedule provides 300 nominal minutes; the three-block schedule provides 450. Environmental profiles may reduce these fixed windows.

## 24. Night and Heat Profiles

Cool, hot, and extreme fixed stress profiles use 100%, 85%, and 70% night-speed factors. They are not probabilities or weather forecasts. Night operation is not approved and cannot automatically start mule delivery.

## 25. Required Rover Count

The independent formal rover search covers 12 through 40. A not-found outcome is reported honestly and is not replaced by an analytical success claim.

## 26. Required Bay Count

The independent bay search covers 1 through 15 for both fleets under the GRID reference. Five-bay electrical capacity and connector cycle measurements remain unresolved.

## 27. Required Cassette Count

The independent cassette search covers 2 through 16, with seven modules per cassette, two nominal mules, and a 200 m route for each fleet and schedule.

## 28. Required Mule Count

The independent mule search covers 1 through 5 for the eight-cassette, 500 m, fleet-30, three-block representative. Mule energy and payload runtime require measurements.

## 29. Hardware Count Summary

The cassette combinations total 72, 86, 80, and 94 modules, corresponding to 86,400, 103,200, 96,000, and 112,800 g. GRID totals contain only 24 or 32 rover modules.

## 30. Report Interpretation

`result=PASS` means deterministic simulation completed. It does not mean `FEASIBLE`, purchase approval, field approval, electrical approval, or sustainability. Configuration results are sorted by ID and all corrected 10,044 configurations are evaluated: 324 GRID plus 9,720 cassette configurations.

## 31. Orange Pi Validation

Validation uses Python 3.11 isolated mode, transfers only the six new ST-012 files, writes reports below an external task directory, and compares two independent report runs. It does not install packages or modify tracked files.

## 32. CLI Usage

Create an external report directory, then run:

```text
python3 -I -B software/station_control/station/drive_through_charge_exchange_scheduler.py --repository-root <repository-root> --plan software/station_control/config_examples/drive-through-charge-exchange-plan.example.json --json-report <external-directory>/drive-through-charge-exchange-report.json --text-report <external-directory>/drive-through-charge-exchange-report.txt
```

## 33. Measurement Replacement Plan

Replace estimated return distance, rover return energy, runtime, charge curve, docking time, connector current and contamination behavior, cassette topology and mass, latch and A/B interlock behavior, mule route distance, braking, payload runtime, and segment safety with controlled physical measurements before any design approval.

## 34. Current Non-Goals

Current non-goals include hardware integration, charger or contactor control, real rover release, real mule dispatch, autonomous roads, buying decisions, field commissioning, approved automatic restart, approved night operation, and approved unattended operation. Physical validation is required.
