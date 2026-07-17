# Seasonal Field Simulator

## 1. Status

ST-008 is experimental and offline only. It is not production certification or field-operation approval.

## 2. Purpose

The simulator compares six fixed engineering stress scenarios for broadcast, weed, high-cut, cassette logistics, and battery capacity.

## 3. Safety Boundary

There is no actual rover communication, motor, PTO, charger control, ARM, actual assignment, automatic operation start, or physical cassette action. The physical ESTOP remains independent.

## 4. Field Model

`FIELD-DEMO-001` is an abstract 52m × 15m, 780m² field model. A 300mm work width creates 50 lanes and a 2990m full-pass planning distance. These are planning inputs, not exact real coordinates.

## 5. Deterministic Time Model

Each phase uses one-minute resolution, integer base units, explicit integer rounding, and fixed availability. There is no weather probability and no Monte Carlo.

## 6. Broadcast Phase

The comparison uses 4 broadcast rovers, seed 3.0～3.5kg, and tank usable 0.8kg. Seed refills and battery delays consume modeled work time.

## 7. Weed Phase

The model uses 2 weed rovers, treats priority locations first, then the full pass, and always reports a third-rover comparison without registering a third rover.

## 8. Harvest Phase

The model uses 4 high-cut rovers and 2 carrier rovers against the 2990m target. Grain is 480kg, while harvested-material factors are engineering stress assumptions.

## 9. Cassette Logistics

Cassette capacity is 1kg. Single-side collection and temporary drop are allowed, with one active and one spare cassette per high-cut rover and 50 temporary slots. Full-field comparisons are 720／960／1200 cassette scenarios. Carrier capacity 1／2／4 and human recovery 0／10／20 are comparisons, not hardware certification.

## 10. Battery Model

The model starts each season with 16 batteries and 4 chargers. FIFO charging, role runtime, swap dwell, and wait time are deterministic. Battery current measurement required before any physical conclusion.

## 11. Fixed Scenarios

The exact order is BASELINE, CONSERVATIVE, WET_FIELD, ONE_ROVER_DOWN, CARRIER_BOTTLENECK, and COMBINED_BAD.

## 12. Completion Scores

`stress_scenario_completion_score` is completed fixed scenarios divided by six. It is not a success probability or actual completion probability.

## 13. Feasibility Classification

FEASIBLE, MARGINAL, and INFEASIBLE classify only this deterministic model. A PASS execution may legitimately report INFEASIBLE.

## 14. Report Interpretation

Biomass factor is not measured agronomic conversion. Field measurement required, and no agronomic certification is provided. Recommendations are planning rules, never device commands.

## 15. Orange Pi Validation

Windows and Orange Pi validation compares byte-identical JSON/text reports and canonical plan/simulation SHA-256 values.

## 16. CLI Usage

Run `python3 -I -B software/station_control/station/seasonal_field_simulator.py --repository-root <repository> --plan <plan.json> --json-report <external>/report.json --text-report <external>/report.txt`.

## 17. Measurement Replacement Plan

Replace runtime, speed, biomass, carrier handling, and cassette assumptions only after controlled field measurement. Cassette handling field test required.

## 18. Current Non-Goals

No network, live weather, physical sensing, hardware output, autonomous decision, field deployment, or unattended operation is included.
