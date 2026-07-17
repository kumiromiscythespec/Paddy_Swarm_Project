# Seasonal Capacity Sweep

## 1. Status

ST-009 is experimental and offline only. It is not production certification, purchasing approval, or field approval.

## 2. Purpose

The tool compares equipment capacity for one abstract 780m² field using three targets and deterministic engineering assumptions.

## 3. Safety Boundary

There is no hardware control, rover communication, motor, PTO, charger, BMS, ARM, mount, unmount, purchase, or work-start authority. Physical ESTOP remains independent.

## 4. ST-008 Model Reuse

ST-009 loads ST-008 and calls its exact phase simulation functions. The ST-008 source and algorithm are not copied or modified. Final candidates are validated by ST-008; compatibility adaptation only permits the ST-009 equipment dimensions.

## 5. Search Space

There are 2041200 raw combinations: broadcast fixed at 4, weed 2～6, high cut 4～12, carrier 2～8, batteries 16～48, chargers 4～12, cassette 1／2／4kg, carrier batch 1／2／4／6, slots 50／100／150／200, and manual 0／10／20.

## 6. Three Targets

The three targets independently test baseline, baseline plus wet resilience, and all six ST-008 scenarios.

## 7. Candidate Configuration

Common rover and attachment counts are quantity metrics, not monetary cost claims. Cassette inventory is proxy, not a confirmed bill of materials.

## 8. Staged Exact Search

The exact staged search validates input, gates every target against fixed broadcast capacity, applies safe phase bounds, evaluates power combinations, and classifies exact ST-008 results. A fixed broadcast failure makes the affected target not found and is reported in both diagnostics and recommendations.

## 9. Safe Upper-Bound Pruning

Upper-bound pruning never proves success. It only removes configurations that cannot succeed even under ideal battery-free phase capacity. Nearest-miss pruning additionally requires a lexicographic lower-bound proof; otherwise the candidate receives formal ST-008 evaluation. There is no arbitrary top-N pruning.

## 10. Power Sweep

The exact power sweep compares 9 battery counts and 5 charger counts. Its cache is deterministic, memory-only, and never persisted.

## 11. Equipment-Min Selection

Equipment quantity minimum follows the documented quantity lexicographic order and makes no monetary cost claim.

## 12. Human-Min Selection

Human minimum first minimizes daily manual cassette recovery, then operational shortfalls and equipment tie-breakers.

## 13. Pareto Frontier

The internal frontier is exact and uncapped. Only the first 20 deterministically sorted results are displayed.

## 14. Mechanical Review Flags

4kg and large batch require mechanical review. Payload and mud test required, and center-of-gravity test required. Flags do not change simulation completion.

## 15. Nearest-Miss Results

Every target retains the globally exact first 10 non-satisfying candidates in nearest-key order. The search streams candidates and does not derive wet or all-scenario misses from baseline-selected candidates. A reduced brute-force oracle independently checks status, counts, selections, Pareto results, and nearest misses.

## 16. Report Interpretation

Results are design comparisons. They do not prove physical mounting, safe cassette weight, mud mobility, waterproofing, production readiness, or field approval.

## 17. Orange Pi Validation

Windows and Orange Pi runs compare byte-identical reports, hashes, targets, selections, Pareto results, nearest misses, diagnostics, and recommendations.

## 18. CLI Usage

Run `python3 -I -B software/station_control/station/seasonal_capacity_sweep.py --repository-root <repository> --base-plan software/station_control/config_examples/seasonal-field-plan.example.json --sweep-plan software/station_control/config_examples/seasonal-capacity-sweep-plan.example.json --json-report <external>/sweep.json --text-report <external>/sweep.txt`.

## 19. Measurement Replacement Plan

Field current measurement required before power sizing. Payload, mud, attachment, cassette handling, and center-of-gravity measurements must replace assumptions before physical design decisions.

## 20. Current Non-Goals

No weather probability, Monte Carlo, network, autonomous purchase, physical feasibility claim, unattended operation, or deployment is included.
