# Single-Bay Validation Plan

## Status and authority boundary

Status: **DESIGN ONLY — validation has not been executed or approved.**

```text
design_only=true
hardware_output_performed=false
mains_work_approved=false
battery_connection_approved=false
field_operation_approved=false
night_operation_approved=false
automatic_restart_approved=false
unattended_operation_approved=false
licensed_electrical_review_required=true
physical_estop_independent=true
```

Every phase requires a separate written authorization after its entry conditions and hazards are reviewed. A PASS in this document means that a future test may advance to the next review gate; it is not authorization for construction, battery connection, mains work, field use, night use, automatic restart, or unattended use.

## Fixed scope of the first bay

The initial validation unit is exactly one forward-entry/forward-exit bay with one common rover, one charger, one connector pair, wheel guides, a mechanical stop, holding-brake confirmation, motor-inhibit indication, PTO-inhibit indication, connector-lock detection, pilot or presence contacts, temperature monitoring, charging-current measurement, an independent physical ESTOP, and a manual disconnect. The motor and PTO signals are inhibit evidence only and confer no motion or implement authority. The initial energized path is `GRID-AC` and contains no station cassette.

Direct station-cassette-to-rover-battery and battery-to-battery charging are prohibited. The A/B cassette mechanism is validated separately using dummy frames, limited-energy sources, and a dummy load before any integrated off-grid phase.

## Global phase rules

1. Phases execute only in the exact order `PHASE-0` through `PHASE-9`; no phase may be skipped, merged, or run concurrently.
2. Entry requires accepted evidence from every preceding phase, a phase-specific hazard review, named human supervision, and explicit authorization for the planned energy source.
3. Equipment must have current calibration or functional-check evidence applicable to the measurement.
4. Test configurations are mutually exclusive: unpowered, limited-energy, `GRID-AC`, and PACK configurations may not be connected together.
5. Physical ESTOP and upstream isolation are independent of normal software, communications, and charger logic.
6. Power restoration, controller restart, or communication restoration never resumes a test automatically.
7. Any failed guard, invalid sensor, unexpected movement, current, voltage, heat, odor, sound, water ingress, damage, latch contradiction, communication loss, or ESTOP operation aborts the phase.
8. Aborted or failed phases remain failed until the cause is recorded, the setup is safely isolated, corrective action is reviewed, and the complete affected phase is deliberately authorized again.
9. No acceptance result changes an unresolved design value into a certified rating.

## Global provisional acceptance limits

- Docking speed: `≤0.05 m/s`.
- Connector-plane translational error: `±15 mm` maximum.
- Connector-plane angular error: `±3°` maximum.
- The mechanical guide engages before the connector; the connector mates last.
- The connector carries no rover body, alignment, docking, or latch load.
- Cycle program: 100 dry cycles, 20 wet cycles, and 20 mud cycles.
- False-positive latch indications: 0.
- Connector, guide, mount, cable, and seal damage events: 0.
- Cable, termination, or strain-relief overload events: 0.
- No energized unmating, direct battery-to-battery path, A/B overlap, hot insertion, hot removal, automatic restart, or automatic resume is accepted.

Electrical voltage, current, temperature, leakage, insulation, contact-resistance, ramp, zero-current, precharge, timeout, and protective-device limits remain unresolved until equipment data and licensed review define them.

The exact provisional electrical acceptance rules are:

- no charge without lock confirmation;
- no contactor close on voltage incompatibility;
- no cassette switch under nonzero charger current;
- no simultaneous `ACTIVE` slots;
- an active cassette cannot unlatch;
- every fault causes charger inhibit;
- every fault requires manual reset;
- power restoration does not auto-resume charging;
- ESTOP opens the charging-permission path independently.

## PHASE-0 — Documentation and electrical review

### Entry conditions

All six ST-013A documents exist as a controlled review set, ST-012 assumptions are identified as simulation values, and no hardware procurement or work has begun.

### Equipment

Document register, architecture comparison, hazard log, requirements traceability matrix, battery/BMS/charger manufacturer data when available, and review checklists. No test hardware is required.

### Procedure

Review every assumption, source topology, energy boundary, protective function, ESTOP independence, interlock transition, connector unknown, measurement need, and authorization boundary. Assign owners to unresolved items without selecting unverified ratings or products. A licensed electrical reviewer assesses mains, battery, isolation, grounding/bonding, conductor, protection, enclosure, and fault-energy questions.

### Pass criteria

No direct battery-to-battery path is proposed; ARCH-A conditions and GRID/PACK separation are accepted; all critical hazards have a prevention, detection, safe response, and evidence plan; unresolved ratings remain explicitly open; and the reviewer signs only the scope eligible for PHASE-1.

### Fail criteria

Missing authoritative limits, an uncontained hazard, incompatible battery/BMS behavior, dependence on software as the sole emergency layer, an implicit automatic restart, or pressure to infer a product rating is a FAIL.

### Abort conditions

Discovery that hardware work, purchasing, mains work, or battery connection has already been initiated under this document immediately stops the review and escalates the scope breach.

### Evidence

Reviewed document hashes, issue register, hazard log, assumption register, traceability matrix, reviewer role and decision, explicit exclusions, and phase authorization record. Personal secrets and unnecessary personal data are excluded.

### Cleanup

Close document access, preserve the immutable review package, leave all equipment unbuilt and unenergized, and record unresolved actions. No purchase order or work instruction is released.

## PHASE-1 — Mechanical docking only

No electrical connector energy is present.

### Entry conditions

PHASE-0 is PASS; mechanical drawings and risk assessment are separately approved for a non-electrical fixture; the connector is absent or replaced by a non-contact dimensional gauge; the rover cannot energize propulsion unexpectedly.

### Equipment

One bay fixture, non-electrical connector gauge, independent speed measurement, displacement and angle gauges, force indication suitable for detecting structural contact, wheel restraint, physical stop, and observation recording tools.

### Procedure

Perform supervised manual or otherwise separately approved low-speed approaches from the planned tolerance envelope. Verify guide-first capture, final position, forward exit, structural load path, latch geometry, and recovery from an incomplete approach. Do not install a live connector, charger, cassette, or battery interface.

### Pass criteria

All approaches are `≤0.05 m/s`; the fixture accepts `±15 mm` and `±3°` within its approved envelope; guide engagement precedes the connector gauge; the gauge mates last; the connector plane carries no body load; latch false positives, damage, and strain events are all zero.

### Fail criteria

Excess speed, connector-first contact, fixture instability, body load through the connector gauge, trapping, inability to exit forward, false latch, permanent deformation, or abnormal force is a FAIL.

### Abort conditions

Unexpected rover motion, restraint failure, person entering a pinch zone, loosened fixture, damage, or measurement loss requires immediate stop and mechanical securing.

### Evidence

Fixture revision, gauge calibration, approach matrix, measured speed/offset/angle, load-path observations, latch results, damage inspection, and deviations.

### Cleanup

Secure the rover, remove the gauge if required, release stored mechanical energy, inspect and quarantine damaged parts, and leave all electrical interfaces absent and isolated.

## PHASE-2 — Unpowered connector mating cycles

### Entry conditions

PHASE-1 is PASS; a candidate connector is accepted for unpowered evaluation only; dimensions, material restrictions, cleaning limitations, and mating instructions are available; all contacts are proven de-energized and disconnected.

### Equipment

One connector pair, approved floating mount and guide, continuity-only test instrument with energy limited for measurement, cycle counter, insertion/withdrawal force measurement, inspection magnification, and strain indicators.

### Procedure

Complete 100 dry guided mating/unmating cycles within the mechanical acceptance envelope. At defined intervals inspect pilot sequencing, keying, contact alignment, seal position, float travel, latch state, cable strain, and wear. This phase introduces no water, mud, charger, battery, cassette energy, or mains connection.

### Pass criteria

All 100 dry cycles complete with guide-first/connector-last sequencing, correct first-mate/last-break pilot continuity, zero false-positive latch indications, zero damage, zero strain events, no unacceptable force trend, and no structural load through the connector.

### Fail criteria

Any bent or displaced contact, seal damage, partial mate accepted as complete, pilot sequence error, key bypass, abnormal wear, rising force outside reviewed limits, false latch, or cable strain is a FAIL.

### Abort conditions

Unexpected voltage/current, damaged insulation, trapped person, mechanical instability, instrument fault, or evidence of connector-borne docking load requires immediate stop.

### Evidence

Candidate identity without secret data, manufacturer documentation revision, cycle log 1–100, force measurements, continuity sequence, inspection records, calibration evidence, and failure photographs if separately permitted.

### Cleanup

Prove contacts de-energized, separate and cap the connector, relieve cable strain, quarantine failed parts, and store the dry evidence without approving product selection.

## PHASE-3 — Pilot contacts and lock detection

SELV/current-limited control only.

### Entry conditions

PHASE-2 is PASS; the pilot, latch, presence, temperature, voltage, and current observation concept has passed review; a SELV, current-limited, non-battery source and independent emergency removal are approved for this phase.

### Equipment

Current-limited SELV source, protected test harness, dummy contacts or loads, pilot and latch sensors, temperature stimulus simulator, voltage/current simulators, independent measurement instruments, fault-insertion switches, and physical ESTOP demonstrator independent of controller logic.

### Procedure

Exercise every valid and contradictory combination of presence, pilot, latch, final position, voltage, temperature, current, controller health, communication, reboot, ESTOP, and power restoration. Verify that only a complete valid chain can create a permission indication and that no permission drives a real charger or contactor.

### Pass criteria

Every missing, stale, contradictory, out-of-range, or lost input fails closed; first-mate/last-break sequencing is correctly detected; ESTOP independently removes permission; reboot and restoration remain inhibited; manual reset is deliberate; no output reaches hardware beyond the approved limited-energy demonstrator.

### Fail criteria

Any false permission, automatic reset, automatic resume, single-point bypass of ESTOP, stale-data acceptance, undetected contradiction, unsafe default, or unexpected output is a FAIL.

### Abort conditions

Source current limit failure, unexpected heat, insulation damage, ESTOP path failure, uncontrolled actuator motion, or loss of independent measurement requires source isolation.

### Evidence

Input truth table, fault-insertion matrix, source limits, independent readings, reboot/restoration results, ESTOP independence result, manual-reset record, and identified diagnostic gaps.

### Cleanup

Remove the limited-energy source, discharge approved test components, return all outputs to inhibited state, cap interfaces, and quarantine any failed sensor or harness.

## PHASE-4 — A/B cassette interlock bench

Dummy low-voltage source and dummy load only.

### Entry conditions

PHASE-3 is PASS; two mechanically representative dummy cassette frames, individually protected limited-energy sources, and a dummy load are approved; no real battery, charger, inverter, or mains source is present.

### Equipment

Two dummy cassette frames, two isolated/current-limited simulators, dummy load, two slot fixtures, precharge simulator, contactor-state simulators or reviewed low-energy devices, independent current/voltage observation, fault insertion, and physical ESTOP.

### Procedure

Exercise all 16 exact states and every transition in `A_B_CASSETTE_INTERLOCK_SPEC.md` for A-to-B and B-to-A changes. Inject each guard loss, timeout, welded/open mismatch, sensor contradiction, communication loss, controller reboot, ESTOP, and restoration case. Attempt prohibited overlap, hot removal, and premature latch release only through safe simulation.

### Pass criteria

At most one slot is `ACTIVE`; no direct parallel state exists; PRECHARGE is mandatory; transition requires ramp-down, independent zero-current confirmation, and contactor-open proof; ACTIVE removal is impossible; all faults isolate and latch; restart/restoration never resumes; manual recovery restarts checks from a safe state.

### Fail criteria

Simultaneous ACTIVE slots, overlap, skipped precharge, false zero-current, release before open proof, automatic recovery, incomplete fault coverage, or a state/transition not represented in evidence is a FAIL.

### Abort conditions

Unexpected simulator energy, contactor or actuator response outside the reviewed envelope, heat, frame instability, ESTOP failure, or loss of independent current/voltage evidence requires isolation.

### Evidence

State/transition coverage matrix, ordered event logs, timeout and fault-injection results, A-to-B/B-to-A traces, overlap attempts, ESTOP/reboot/restoration traces, and manual-recovery records.

### Cleanup

Set both slots to isolated, remove limited-energy sources, discharge as approved, prove dummy load current zero, inhibit releases, and store dummy frames unenergized.

## PHASE-5 — Single charger with current-limited source

### Entry conditions

PHASE-4 is PASS; charger documentation and intended battery profile have been reviewed; a non-battery programmable load or approved battery simulator is used; source and output are current-limited; no blind energized mating is allowed.

### Equipment

One charger, approved current-limited source appropriate to the charger, non-battery programmable load or battery simulator, independent voltage/current/power/temperature measurements, isolation and leakage test equipment selected by the reviewer, physical ESTOP, and upstream disconnect.

### Procedure

Characterize startup, inrush, steady operation, partial-charge emulation, demand ramp-down, zero-current threshold/dwell, disable, power loss, communication loss if applicable, restoration, fault shutdown, and thermal behavior. Connections remain fixed and guarded before energization.

### Pass criteria

Measured values remain within manufacturer and reviewed limits; protective and isolation behavior is accepted; ramp-down reaches the reviewed zero-current criteria before isolation; every fault, reboot, and power restoration remains disabled pending manual reset; no direct battery-to-battery path exists.

### Fail criteria

Unexpected inrush, unstable output, failed current limiting, excessive temperature, isolation concern, nonzero current after disable, automatic restart, incompatible partial-charge behavior, or missing independent evidence is a FAIL.

### Abort conditions

Smoke, odor, abnormal sound, temperature excursion, instrument overload, unexpected accessible voltage, ESTOP failure, source-limit failure, or protective-device operation requires upstream isolation.

### Evidence

Charger documentation, configuration revision, source/load limits, calibrated traces for startup/steady/ramp/zero/open/restoration, temperatures, protective responses, and calculated uncertainty.

### Cleanup

Disable and isolate input, confirm output zero current and safe voltage, discharge under the approved method, disconnect only after proof, cap interfaces, and quarantine any failed equipment.

## PHASE-6 — GRID single-bay battery charging

### Entry conditions

PHASE-5 is PASS; licensed electrical review is complete; separate written approvals explicitly cover mains work and this battery connection; the charger and rover battery/BMS are compatible by authoritative data; the bay remains dry and controlled; no PACK equipment is connected.

### Equipment

Reviewed mains installation and upstream protective/isolation devices, one certified or specifically accepted AC charger, one rover battery/BMS assembly, guarded bay interface, independent voltage/current/temperature measurements, physical ESTOP, fire and emergency provisions selected by the responsible reviewer.

### Procedure

Qualified personnel verify isolation and configuration, make connections under the approved work instruction, conduct one supervised charging session through the fixed connector, observe startup/steady/partial/termination behavior, request a controlled stop, prove zero current and isolation, and verify that restoration does not resume. Blind mating or unmating while energized is prohibited.

### Pass criteria

All manufacturer, BMS, licensed-review, temperature, current, voltage, isolation, interlock, ramp-down, zero-current, and manual-restart limits pass; ESTOP is independent; connector temperature and condition remain acceptable; no PACK path, automatic resume, or unattended interval occurs.

### Fail criteria

Any BMS fault, charger incompatibility, unexpected current/voltage/temperature, connector heating or damage, failure to reach zero before opening, automatic restart/resume, protective-device anomaly, or evidence gap is a FAIL.

### Abort conditions

Any global abort condition, water or mud entry, mains concern, battery swelling/venting/odor/noise, BMS trip, unexpected rover movement, loss of supervision, or emergency-system concern requires the approved emergency response.

### Evidence

Authorizations, licensed review record, equipment/certification references, pre-use inspection, calibrated electrical/thermal traces, BMS observations, interlock sequence, ESTOP and restoration results, post-use connector/battery inspection, and deviations.

### Cleanup

Perform controlled shutdown, prove zero current and safe voltage, isolate mains by the approved device, disconnect only under the approved work instruction, restore caps/barriers, inspect for heat or contamination, and leave the system incapable of automatic restart.

## PHASE-7 — Mud/water contamination recovery tests

The unenergized connector is tested first.

### Entry conditions

PHASE-6 is PASS; an environmental protocol, fluids/soil simulants, cleaning agents, drainage, containment, disposal, PPE, and requalification criteria are approved; the first exposure and all mating cycles are unenergized.

### Equipment

Connector/guide fixture, defined wet medium, defined mud simulant, controlled application and containment, approved cleaning/drying materials, inspection tools, contact-resistance/insulation instruments selected by the reviewer, and only later the PHASE-3 limited-energy demonstrator if requalification passes.

### Procedure

Complete 20 wet and 20 mud guided cycles while unenergized. After each defined exposure, inspect contamination paths, drainage, seals, pilot, latch, guides, cable strain, cleaning effectiveness, drying, and damage. Reintroduce only the limited-energy pilot test after documented clean/dry/requalification acceptance; no battery or mains charging occurs in this phase.

### Pass criteria

All 20 wet and 20 mud cycles complete with zero false latch, zero damage, zero strain events, no retained contamination bridge or water pocket, successful approved cleaning/drying, acceptable post-clean electrical inspection, and fail-closed pilot behavior.

### Fail criteria

Water or mud reaching a prohibited zone, trapped contamination, corrosion initiation, seal displacement, cleaning damage, unsafe residue, false latch/pilot, abnormal resistance/insulation, or inability to prove dryness is a FAIL.

### Abort conditions

Unexpected energy, uncontrolled spill, unsafe chemical interaction, loss of containment, damaged PPE, live contact, or inability to isolate the fixture requires stop and environmental response.

### Evidence

Medium definitions, application and cycle log, inspection checkpoints, drainage observations, before/after measurements, cleaning/drying record, pilot requalification, damage and residue findings, and waste disposition.

### Cleanup

Keep all interfaces de-energized, collect and dispose of media under the approved plan, clean and dry the area and fixture, cap the connector, quarantine failed components, and do not infer field or IP approval.

## PHASE-8 — Integrated off-grid single-bay

This phase is eligible only after every prior phase is PASS.

### Entry conditions

PHASE-0 through PHASE-7 are PASS; ARCH-A conditions are satisfied; PACK-INVERTER-AC equipment, cassette/BMS limits, isolation, fusing, enclosure, thermal management, and emergency isolation have licensed review; separate battery and energized-test approvals exist; no GRID source is connected.

### Equipment

One reviewed ARCH-A cassette source, one reviewed inverter, the characterized AC charger, one rover battery/BMS, one bay, independent source/output measurements, thermal sensing, upstream and downstream isolation, physical ESTOP, barriers, and emergency provisions.

### Procedure

Qualified personnel prove GRID absence, verify topology and isolation, energize one fixed and guarded off-grid path, characterize inverter startup plus charger inrush, conduct a supervised charge interval, request controlled shutdown, prove zero current and isolation, and test fault/power restoration without automatic resume. A/B exchange is not performed with a rover charging unless separately validated and authorized.

### Pass criteria

Source, inverter, charger, BMS, connector, thermal, current, voltage, isolation, and interlock measurements pass reviewed limits; no backfeed or module equalization exists; shutdown proves zero current and open isolation; restart/restoration is inhibited; no direct battery-to-battery or GRID connection exists.

### Fail criteria

Inverter/charger incompatibility, surge outside limits, backfeed, thermal excursion, protection mismatch, loss of isolation, nonzero opening, automatic resume, cassette interlock contradiction, or missing evidence is a FAIL.

### Abort conditions

Any battery, inverter, charger, enclosure, connector, isolation, ESTOP, measurement, supervision, or contamination anomaly invokes the approved emergency isolation and response.

### Evidence

Topology verification, approvals, source/inverter/charger documentation, startup and load traces, efficiency and thermal measurements with uncertainty, fault/ESTOP/restoration results, isolation proof, and post-test inspection.

### Cleanup

Ramp demand to zero, prove zero current, isolate rover and station energy on both sides, apply reviewed discharge procedure, secure the cassette against removal or short circuit, cap interfaces, and leave automatic restart disabled.

## PHASE-9 — Five-bay expansion design review

### Entry conditions

PHASE-8 is PASS with accepted evidence; measured one-bay demand, startup, heat, efficiency, interlock, connector, contamination, and service data are available. This phase remains a design review, not a five-bay build or test.

### Equipment

One-bay evidence package, five-bay load and fault models, proposed independent bay diagrams, supply-capacity study, protective-device coordination study, thermal/enclosure model, service and evacuation review, and licensed reviewer checklist.

### Procedure

Evaluate `GRID-AC`, independent `PACK-INVERTER-AC`, and independent `PACK-ISOLATED-DC` channels for five bays using measured coincident demand, starting surge, diversity, single-fault containment, isolation, protection, heat, cable routing, emergency shutdown, maintenance, and partial availability. Preserve independent bay isolation and prohibit a common unreviewed converter or shared fault path.

### Pass criteria

A reviewable topology contains every bay fault, preserves physical ESTOP independence and manual restart, documents supply and thermal margin, defines protection coordination and service isolation, and resolves whether independent isolated DC chargers or independent inverter/charger channels are justified. All remaining unknowns have owners and evidence gates.

### Fail criteria

Extrapolating five times a simulation value without measurements, shared protection that defeats bay isolation, uncontained common-mode failure, unresolved supply capacity, automatic restart, inadequate thermal/service access, or use of an uncertified direct battery path is a FAIL.

### Abort conditions

Any request to purchase, fabricate, wire, energize, or field a five-bay station under this design-review phase stops the phase and requires a new authorized implementation contract.

### Evidence

Reviewed alternatives, measured-input inventory, load/fault/thermal studies, independence matrix, protection and isolation concept, updated hazard log, decision record, unresolved-item register, and explicit implementation exclusions.

### Cleanup

Archive the design-review package, keep the one-bay hardware isolated under its prior controls, release no construction or purchase package, and require a new phase contract for any five-bay implementation.

## Evidence acceptance and retention

Every phase record must identify document/configuration revision, equipment identity, calibration or functional-check status, expected and observed values, measurement uncertainty, pass/fail/abort decision, anomalies, cleanup completion, and approval boundary. Evidence must avoid secrets, credentials, network identifiers, unnecessary personal data, and actual field coordinates. A failed or missing record cannot be replaced by operator recollection.

## Final safety statement

This plan performs no validation and authorizes none. It defines future gates only. Hardware output, mains work, battery connection, field operation, night operation, automatic restart, and unattended operation all remain unapproved; licensed electrical review is mandatory.
