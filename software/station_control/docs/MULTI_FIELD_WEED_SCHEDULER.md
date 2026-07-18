# Multi-Field Weed Scheduler

## 1. Status

ST-010 is experimental, simulation-only software. It is offline only and does not certify production readiness, field deployment, unattended operation, or purchasing.

## 2. Purpose

The scheduler compares deterministic ways to share twelve weed rovers across nineteen operational fields. It evaluates a full-pass target over ten work days, reports actual simulated completion without inflating it, and calculates design targets for speed and rover count.

## 3. Safety Boundary

The program has no rover, network, GPIO, serial, motor, PTO, charger, BMS, ARM, or mission-assignment authority. It does not approve field operation. Physical ESTOP remains independent. Autonomous field transfer, autonomous road crossing, rover-carried station transport, automatic work start, and physical ESTOP release remain prohibited.

`ADJACENT_FIELD_SELF_TRANSFER` and `ROVER_SWARM_STATION_TRANSPORT` are reserved names only; both remain disabled. All inter-field movement is manual.

## 4. R4 Area Reference

The retained R4 reference contains 20 parcels and a total declared area of 31,950 m2. Its rice subset contains 16 parcels totaling 22,040 m2. Three grass parcels total 6,780 m2, and self-conservation area is 3,130 m2. This reference is not treated as the current field inventory.

## 5. Current Operational Field Estimate

The current planning model contains 19 operational fields totaling approximately 27,000 m2. One provisional field is 1,422 m2 and eighteen are 1,421 m2. These equalized areas are provisional, mapping to the R4 parcels is unresolved, and no exact field geometry or actual coordinates are present. Actual field measurement is required.

## 6. Five Field Groups

The fields are divided into five separated groups in fixed order: `GROUP-HOME` (9), `GROUP-OTHER-CONSIGNED` (3), `GROUP-CONSIGNED` (2), `GROUP-OWN-A` (2), and `GROUP-OWN-B` (3). A schedule may change groups at most once per work day. Two simultaneously active fields must be in the same group.

## 7. Planning Distance

ST-010 preserves the ST-008 full-pass meaning. It scales the 2,990,000 mm reference distance for 780 m2 with upward integer rounding per field. A 1,421 m2 field is 5,447,167 mm and a 1,422 m2 field is 5,451,000 mm. The field-level total is 103,500,006 mm; the area-level exact value is 103,500,000 mm. The six-millimetre difference is per-field ceiling. Priority treatment is excluded from this target.

## 8. Ten-Day Target

`FULL_PASS_ALL_19_WITHIN_10_WORK_DAYS` requires all nineteen fields and the full 103,500,006 mm within ten work days. The three scheduled windows are 150, 300, and 480 minutes per day with 60 percent availability after deployment and recovery overhead. An incomplete target is a valid simulation outcome and does not by itself make execution fail.

## 9. Shared Twelve-Rover Fleet

Twelve weed rovers are shared, with at most two simultaneously active fields. Rover states in the report are simulation states only. The scheduler never changes a real rover state.

## 10. Allocation Policies

The fixed policies are `ONE_FIELD_CONCENTRATED`, `TWO_FIELDS_EQUAL`, `TWO_FIELDS_WEIGHTED`, `FINISH_FIRST`, and `ROAD_SIDE_BATCHED`. They compare one-field concentration, 6/6 allocation, 8/4 weighted allocation, completion-first ordering, and fixed group batching. Every completion-triggered reallocation consumes manual handling time; unused distance is never moved automatically to another field.

## 11. Manual Vehicle Transfer

One vehicle and 1, 2, or 3 operators are compared. Vehicle capacity options are 6, 8, and 10 rovers; the 10-rover capacity is a provisional upper bound, not a measured payload. Loading and unloading use four minutes per rover with operator parallelism. Driving remains serial because there is one vehicle. Actual vehicle payload measurement is required.

## 12. Daily Deployment and Recovery

Morning deployment and evening recovery are required every work day. Rovers are loaded, secured, driven, unloaded, and checked by humans. At the end of the day they are stopped, batteries and the station are recovered, and rovers return to the depot. No rover is modeled as remaining in a field overnight.

## 13. Mobile Charging Station

There is one mobile charging station with four chargers. It serves one primary field at a time. Station transfer is manual and uses a dedicated vehicle trip. The station cannot move itself and cannot be carried by a rover.

## 14. Battery Model

The comparison uses 16, 24, or 36 batteries, 150 minutes of runtime, a three-minute swap, and 180-minute charging. Four chargers can complete at most 16 sessions in the 720-minute overnight window. Battery state carries across days and is not reset automatically. Service windows are morning deployment and evening recovery. There is no midday battery shuttle; a secondary field relies on batteries positioned in the morning.

## 15. Required Speed

For every policy, daily window, operator count, vehicle capacity, and battery-pool combination, integer speeds from 100 through 10,000 mm/min are searched monotonically. Any reported minimum is re-run through the formal scheduler. It is a design target, not proof of achieved performance. Actual rover speed measurement is required.

## 16. Required Rover Count

The representative comparison uses `ROAD_SIDE_BATCHED`, 700 mm/min, a 480-minute day, two operators, and vehicle capacity 10. Rover counts 1 through 60 are evaluated with twice as many batteries and four fixed chargers. A not-found result is reported directly rather than converted to a false success.

## 17. Manual Drone Scout Reservation

The formal scout source is `PRELOADED_MAP` because the completion target is a full pass. `MANUAL_DRONE`, `GROUND_SCOUT`, and `NO_SCOUT` are reserved source labels. ST-010 performs no flight control, automatic takeoff or landing, route generation, image analysis, or autonomous flight. A detailed manual-drone study is reserved for a future phase.

## 18. Report Interpretation

All 1,215 configurations are evaluated: five policies, three speeds, three daily windows, three operator counts, three vehicle capacities, and three battery pools. `PASS` means deterministic execution succeeded. Feasibility is separately classified as `FEASIBLE`, `MARGINAL`, or `INFEASIBLE`. Configuration, field, day, diagnostic, bottleneck, and recommendation ordering is fixed.

## 19. Orange Pi Validation

The same six source artifacts, plan, tests, and CLI are validated with Python 3.11 on the Orange Pi. Formal A/B reports must be byte-identical locally, byte-identical remotely, and identical across Windows and Orange Pi. Validation does not grant hardware or network authority to the scheduler.

## 20. CLI Usage

Run from the repository root and place both reports outside the repository:

```text
python3 -I -B software/station_control/station/multi_field_weed_scheduler.py --repository-root . --plan software/station_control/config_examples/multi-field-weed-plan.example.json --json-report <external-directory>/multi-field-weed-report.json --text-report <external-directory>/multi-field-weed-report.txt
```

The report parent must already exist. JSON and text paths must differ. The report contains no timestamp, host name, user name, absolute path, credential material, network address, hardware address, or exact field coordinates.

## 21. Measurement Replacement Plan

Replace the equalized areas only after measuring all nineteen current fields and resolving their mapping to the R4 source. Measure vehicle payload, rover loading time, actual rover operating speed, weed power consumption, battery runtime, and station handling time. Re-run the complete deterministic matrix after each accepted measurement update.

## 22. Current Non-Goals

ST-010 does not implement actual assignment, rover communication, autonomous inter-field transfer, autonomous public-road crossing, station transport by rover, charger control, production certification, purchasing, field-deployment approval, or unattended-operation approval.
