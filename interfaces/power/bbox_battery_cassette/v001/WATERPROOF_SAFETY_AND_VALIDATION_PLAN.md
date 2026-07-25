# PS-BBOX-CASSETTE-V001 Waterproof, Safety, and Validation Plan

Status: DOCUMENTATION_CANDIDATE_ONLY

Version: v001

This plan validates the contract progressively. It does not assert physical
waterproofing, electrical safety, battery safety, fire containment,
manufacturing readiness, purchase approval, or field readiness. Only Stage 0
document validation is performed by this lane.

The controlled three-layer architecture is BBOX-FRAME,
BBOX-WET-CRADLE, and BBOX-BATTERY-CASSETTE.

## 1. Stop and fail-closed policy

Any unexpected motion, latch release, electrical potential, heat, odor, smoke,
pressure event, water beyond its expected zone, sensor contradiction, loss of
required evidence, damaged enclosure, connector half-mate, drain retention,
uncontrolled tilt, or operator hazard stops the activity.

The immediate safe response is:

1. remove drive and charge permission;
2. command and prove main contactor open where an approved test architecture
   exists;
3. keep or return the shuttle retracted;
4. retain the cassette mechanically until electrical isolation is proven;
5. stop PTO and motor outputs;
6. prevent rover motion;
7. record the fault;
8. inspect, quarantine, and require deliberate recovery.

No test restores power automatically after a fault, reboot, sensor recovery, or
communication recovery.

## 2. Safety boundaries

The primary cassette waterproof barrier is the independently sealed cassette
enclosure. The connector electrical barrier is the secondary compression seal
plus D4 dry chamber behind the D3 moat and detection zone. The CBOX boundary is
a fixed sealed feedthrough and D5 dry core with no shared drain or cavity.
Water sensing supplements these barriers and never replaces them.

No test may:

- use a bottom exposed connector;
- suspend or align a cassette by connector contacts or shell;
- energize with either latch invalid;
- energize with water sensor state other than DRY;
- perform traction hot-swap;
- expose an energized removed-cassette terminal;
- authorize removal before contactor-open, discharged-bus, and full-retraction
  proof;
- exchange in a flooded paddy, deep mud, rice row, steep levee, SOFT_TRAP,
  moving rover, running PTO, energized motor, or unstable floating condition;
- treat a printed shell, gasket appearance, or connector IP claim as proof;
- select chemistry, voltage, capacity, connector, gasket, vent, BMS, charger,
  conductor, fuse, or current rating without a later evidence review.

## 3. Validation stages

| Stage | Name | Minimum content | Gate to next stage |
|---:|---|---|---|
| 0 | DOCUMENT_CONTRACT_VALIDATION | JSON structure, names, zones, state machine, ownership, decision matrix, FMEA, mutation tests, cross-document consistency | All standard-library tests pass; no unexpected skip |
| 1 | GEOMETRIC_DUMMY | Inert full-envelope and full-mass candidate; insertion, keying, seat, latches, handle | Datums and load paths demonstrated; no connector load |
| 2 | DRY_MECHANICAL_CYCLING | Repeated insertion, latch wear, shuttle mock cycling, alignment, inert drop/impact | No false latch, jam, damaging force trend, or lost datum |
| 3 | WATERPROOF_DUMMY | No energized contacts; rain, spray, splash, drain, blockage, contaminated and damaged seals | D4 and D5 remain dry; water faults fail closed |
| 4 | LOW_VOLTAGE_CURRENT_LIMITED | Separately approved safe low voltage; sequence and sensor fault injection | Interlocks, pre-charge logic, and fault recovery reviewed |
| 5 | DUMMY_LOAD_POWER | No traction; controlled current, contact heat, voltage drop, repeated mate | Approved temperature, resistance, and isolation limits met |
| 6 | SEALED_BATTERY_PROTOTYPE | Workshop, protected test area, supervised controlled charge/discharge | Separate battery/fire/electrical specialist approval |
| 7 | ROVER_DRY_GROUND_SWAP | Stopped rover, human exchange, no mud | Full 32-step procedure and recovery proven |
| 8 | FIELD_EDGE_PAD | Outdoor supervised rain/mud at dry pad | Environmental controls and quarantine proven |
| 9 | BATTERY_MULE_DELIVERY | One delivery cassette, human exchange | Mule retention, role separation, and traceability proven |
| 10 | SEMI_AUTOMATIC_DOCK_FUTURE | Future only | Separate project; V001 does not approve it |

Stages are strictly ordered. Passing a stage does not waive its unresolved
parameters or automatically authorize the next. V001 never approves automatic
exchange in a paddy.

## 4. Stage 0 document tests

Stage 0 verifies:

- canonical name and v001 version;
- 5-file add-only scope and no tracked-file modification;
- commercial-box compatibility removal;
- fixed front/rear core and D5 CBOX protection;
- three-layer responsibilities;
- D0 through D5 ordering and ownership;
- vertical top insertion and repository-native axes;
- UPPER_REAR candidate with UPPER_LEFT/UPPER_RIGHT comparison;
- independent structural and connector load paths;
- dual seal, labyrinth, moat, sensing, dry chamber, and recessed contacts;
- drain direction, accessibility, blockage case, and CBOX separation;
- datums, tolerance responsibility, floating mount, and compression policy;
- dead-front, hot-swap prohibition, both latches, dry interlock, identity,
  compatibility, pre-charge, contactor, drive, de-energize, and removal order;
- all 25 states, allowed transitions, prohibited transitions, and fail-closed
  recovery;
- all 32 human swap steps;
- cassette, rover BBOX, CBOX, Mule, and rack ownership;
- Mule propulsion/delivery separation and clean/dirty/quarantine bays;
- rack state and authorization sequence;
- fleet inventory/queue/health functions without local bypass;
- open parameters and all not-approved flags;
- failure-mode and waterproof-matrix coverage;
- mutation detection, deterministic outputs, replay, source protection, and ZIP
  safety.

## 5. Waterproof validation matrix

The canonical JSON contains the machine-readable matrix. The controlled summary
is:

| Condition | Expected containment | Energize permission | Required fail-safe |
|---|---|---|---|
| Clean/dry | D0-D1 | Conditional after every guard | FAULT on contradiction |
| Rain-wet | D1-D2 | Only if D3/D4 dry | WET_FAULT |
| Muddy exterior | D1 | After clean and dry check | FAULT |
| Muddy wiping lip | D1-D3 moat | Prohibited until cleaned | WET_FAULT |
| Blocked primary drain | D2 | Prohibited | WET_FAULT |
| Partially blocked drain | D2 | Prohibited if retained water | WET_FAULT |
| First seal damaged | D3 moat | Prohibited if moisture | WET_FAULT |
| Second seal damaged | D3 | Prohibited | WET_FAULT |
| Latch half-closed | D3 | Prohibited | FAULT |
| Connector half-mated | D3 | Prohibited | FAULT |
| Cassette tilted | D1-D2 | Prohibited until seated | FAULT |
| Rover tilted | D2 | Only inside later validated limit | WET_FAULT |
| Temperature cycle | Cassette barrier | After dry/temperature gate | FAULT |
| Repeated insertion | D1-D3 | Per-cycle conditional | FAULT |
| Vibration | No barrier breach | After inspection | FAULT |
| Rollover orientation | Cassette primary enclosure | Prohibited | FAULT |
| Shallow standing water | D0-D2 | Swap prohibited | WET_FAULT |
| Pressure differential | Cassette pressure system | After inspection | FAULT |
| Water sensor failed | D3 | Prohibited | WET_FAULT |
| Water sensor disconnected | D3 | Prohibited | WET_FAULT |

Every detailed case records ingress path, expected zone, energization rule, pass
criterion, safe state, and inspection method. Tests use inert or de-energized
hardware until a separately approved energized stage.

## 6. Waterproof test method controls

### 6.1 Instrumentation and witnesses

Use later-approved visible witness media, absorbent indicators, humidity or
moisture measurement, water sensor logs, before/after mass where suitable,
controlled tilt, and visual access. Instrument uncertainty and calibration
status must be recorded. Do not infer D4 dryness solely from a sensor.

### 6.2 Drain tests

Test primary drain open, partially blocked, and blocked. Record inflow, retained
volume candidate, time-to-drain, tilt, exit direction, visible cleaning access,
and any reverse or capillary path. No water may drain under the CBOX, under the
connector, into the lower hull, through the feedthrough, or into a blind pocket.

### 6.3 Seal tests

Test clean seals, contaminated first seal, first-seal damage, second-seal
damage, uneven compression, half latch, half mate, repeated cycles, temperature
cycles, and pressure differential. The first seal is expected to reduce mud
and splash; D4 protection must not rely on it. Gasket compression limits remain
TBD until material data exist.

### 6.4 Orientation tests

Use controlled cassette tilt, rover tilt, and rollover candidate fixtures with
inert contents. Demonstrate that the drain does not become a route to D3/D4/D5
and that abnormal orientation causes safe isolation. Rollover does not authorize
continued operation or exchange.

### 6.5 Cleaning tests

Validate brush, cloth, inspection, wiper removal, and drain probing while
isolated. A low-pressure rinse remains a candidate and needs a separate method.
Never direct high-pressure water into D4 or require routine CBOX opening.

## 7. Mechanical validation

The geometric dummy represents the later approved external envelope, center of
mass, and handling mass without cells. Validate:

- negative-Z insertion and positive-Z removal;
- front/rear, left/right, upside-down, wrong-key, and partial-insertion
  rejection;
- DATUM A through DATUM E repeatability;
- guide capture before connector mock engagement;
- bottom seat, rail, primary latch, and frame load path;
- independent safety latch;
- sensor agreement and false-positive count of zero;
- shuttle mock retracted during insertion;
- floating connector response within candidate limits;
- no cassette, impact, recovery, or alignment load on connector mock;
- glove access, pinch protection, two-hand/lift-assist candidate, and no
  accidental latch actuation;
- one-latch retention against cassette drop;
- inspection, replacement, and cleaning access.

Exact cycle count, load, impact, drop, force, and tolerance acceptance values
belong to later test specifications. They are not invented here.

## 8. Electrical and interlock validation

Before any energized stage, an approved electrical design must provide voltage,
continuous/peak/inrush/fault current, isolation, conductor, protective device,
contactor, pre-charge, discharge, measurement, creepage/clearance, touch,
thermal, grounding/bonding, and emergency-stop evidence.

Required fault injections eventually include:

- primary or safety latch open;
- seated/latch sensor disagreement;
- water sensor moisture, water, fault, unknown, and disconnected;
- shuttle jam and half-mate;
- unknown ID and ID communication loss;
- wrong voltage, battery/chemistry/profile, polarity, and connector class;
- pre-charge timeout or non-convergence;
- welded contactor and open fuse;
- unexpected bus voltage or current;
- overtemperature, overvoltage, and undervoltage;
- controller reboot, power loss/restoration, and communication loss/restoration;
- removal request while energized.

Every case must leave power permission off unless all required guards are valid
in sequence. Restoration allows diagnosis only and never automatic restart.

## 9. FMEA coverage

The canonical FMEA covers 38 named failures:

1. cassette dropped;
2. cassette enclosure cracked;
3. cassette lid seal damaged;
4. cassette vent blocked;
5. cassette inserted backward;
6. incompatible cassette;
7. cassette half-seated;
8. primary latch open;
9. safety latch open;
10. latch sensor disagreement;
11. connector shuttle jammed;
12. connector half-mated;
13. connector seal damaged;
14. connector contaminated with mud;
15. drain blocked;
16. water in moat;
17. water in dry chamber;
18. feedthrough leakage;
19. CBOX moisture alarm;
20. overtemperature;
21. undervoltage;
22. overvoltage;
23. polarity fault;
24. pre-charge timeout;
25. welded contactor;
26. open fuse;
27. ID communication failure;
28. Battery Mule wrong cassette delivery;
29. charged/dirty rack cross-contamination;
30. rover rolls during exchange;
31. shell closed on incomplete latch;
32. removal attempted while energized;
33. pressure vent event;
34. fire or smoke event;
35. water sensor failed;
36. water sensor disconnected;
37. connector overtemperature;
38. CBOX feedthrough harness strain.

Each artifact FMEA row contains detection, prevention, safe state, operator
action, service action, logging, and field-deployment consequence. Default
consequence is stop and quarantine; fire/smoke and pressure events require their
separate emergency and specialist procedures.

## 10. Battery, thermal, pressure, and fire hold points

Before a sealed battery prototype:

- select cell chemistry through a specialist hazard review;
- establish nominal/min/max voltage, capacity, continuous/peak/fault current,
  charge profile, BMS limits, fuse coordination, contactor behavior, and
  thermal limits;
- validate cell restraint, insulation, support tray, separation, sensing, and
  service isolation;
- select and test pressure equalization and abnormal vent paths;
- demonstrate vent direction away from CBOX, connector, operator hand, and
  blind wet-cradle pocket;
- define condensation behavior without adding an assumed fan opening;
- obtain separate fire-safety specialist review and protected-area procedure.

Nothing in V001 claims that a 3D-printed shell contains a battery fire.

## 11. Mule, rack, and 30-rover validation

Mule validation waits for actual Mule geometry. It must demonstrate propulsion
cassette separation, one-to-two delivery-cassette candidate retention,
charged-clean/returned-dirty/quarantine segregation, ID traceability, wrong
delivery detection, and no transport load on the connector.

Rack validation demonstrates returned-warm cooldown, inspection, wet fault,
identity, compatibility, temperature gate, isolation candidate, charge
authorization, completion, reservation, fault, and quarantine states. Insertion
alone never starts charging.

Fleet validation models 30 rovers without fixing final cassette or charger
count. It validates queues, reservation, rover/Mule/station assignment,
staggered starts, health exclusion, priorities, reserve, overrides, and audit
logs while proving that no central command bypasses local interlocks.

## 12. Service-life evidence

Track cassette cycles, hours, temperature maximum, water exposure, fault
history, service/quarantine state, health proxy, connector mate cycles,
pre-charge time, convergence, intermittent contact, latch mismatch, connector
temperature, resistance proxy, and connector replacement. Replaceable wet-side
parts must not require replacement of the entire fixed BBOX.

## 13. Stage records and acceptance package

Every later test record identifies contract version, hardware revisions,
operator, approved location, environmental condition, instrumentation,
uncertainty, initial state, ordered observations, injected fault, expected and
actual state, energization permission, stop condition, photos or equivalent
evidence, service disposition, quarantine status, and reviewer decision.

The Stage 0 bundle additionally records repository audit, expected and observed
Git state, source hashes, unit-test count, mutation results, deterministic
generation, clean replay, artifact hashes, and ZIP safety checks.

## 14. Final approval status

- Cassette architecture: INTERFACE_CONTRACT_NOT_CAD_VALIDATED
- Cassette waterproofing: NOT_PHYSICALLY_VALIDATED
- Connector waterproofing: NOT_PHYSICALLY_VALIDATED
- CBOX boundary: CONTRACT_ONLY_NOT_LEAK_TESTED
- Battery cells, chemistry, voltage, capacity: NOT_SELECTED
- Connector, gasket, vent, BMS, charger: NOT_SELECTED
- Electrical current rating: NOT_DEFINED
- Thermal: NOT_VALIDATED
- Fire safety: REQUIRES_SEPARATE_SPECIALIST_REVIEW
- Printability: NOT_VALIDATED
- Manufacturing readiness: NOT_APPROVED
- Purchase approval: NOT_APPROVED
- Field deployment: NOT_APPROVED
