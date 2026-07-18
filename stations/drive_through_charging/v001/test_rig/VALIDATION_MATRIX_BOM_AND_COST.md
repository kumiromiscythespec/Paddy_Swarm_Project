# Validation Matrix, BOM, and Cost

## Status and fixed flags

Status: **DESIGN ONLY — record templates and planning values only**

```text
design_only=true
mechanical_test_rig_only=true
low_energy_interlock_design_only=true
hardware_output_performed=false
battery_connection_approved=false
mains_work_approved=false
charging_approved=false
field_operation_approved=false
night_operation_approved=false
automatic_restart_approved=false
unattended_operation_approved=false
physical_estop_independent=true
licensed_electrical_review_required=true
```

The matrices define future validation after separate authorization. ST-013B performs no experiment, purchase, fabrication, wiring, charging, or hardware operation.

## Validation governance

- Every case begins in an inspected, unpowered condition unless a separately approved low-energy case explicitly uses the current-limited indicator chain.
- The conceptual electrical ceiling is 12 V DC, 1 A source current, and 1 A branch fuse; output is the `PERMIT` lamp only.
- Mechanical approaches are hand-pushed at no more than `0.05 m/s`.
- Any unexpected motion, heat, odor, sound, loose ballast, structural damage, pinch exposure, source-limit failure, ESTOP failure, or invalid instrument state aborts the case.
- A failed or aborted case cannot advance by operator judgment; the cause is recorded, the rig is isolated, and a new review is required.
- No personal name, address, or actual site coordinate belongs in example evidence.

## Fault injection matrix

Each row contains the required initial state, injected fault, expected immediate state, expected indicator, `PERMIT` expectation, manual recovery, and pass condition. Actual count: **32**.

| ID | Initial state | Injected fault | Expected immediate state | Expected indicator | PERMIT expected | Manual recovery | Pass condition |
|---|---|---|---|---|---|---|---|
| FI-001 | Valid reset, one A request, all guards true | ESTOP opens | `FAULT_ISOLATED`; low-energy chain open | `ESTOP_OK` OFF, `FAULT` ON, `RESET_REQUIRED` ON | OFF | Release ESTOP, inspect both contacts, release reset input, deliberate reset | PERMIT drops immediately and never returns from ESTOP release alone |
| FI-002 | Valid reset, all guards true | ESTOP channel disagreement | `FAULT_ISOLATED` | `ESTOP_OK` OFF, `FAULT` ON | OFF | Inspect channel pair, restore agreement, deliberate reset | Disagreement cannot be interpreted as ESTOP OK |
| FI-003 | Source unavailable, reset held | Power becomes available while reset remains held | Reset inhibited | `POWER_AVAILABLE` ON, `RESET_REQUIRED` ON | OFF | Release reset, verify guards, make a new deliberate reset action | Held reset never creates PERMIT |
| FI-004 | A active simulated, stopped and seated | Stop sensor opens | `FAULT_ISOLATED` | `STOP_ENGAGED` OFF, `FAULT` ON | OFF | Inspect stop/load path and sensor, restore plausible stop, reset | PERMIT drops immediately |
| FI-005 | Stop physically absent | Stop sensor reports engaged contrary to companion observation | `FAULT_ISOLATED` | `STOP_ENGAGED` inconsistent, `FAULT` ON | OFF | Isolate, correct target/sensor, prove both observations, reset | Contradiction never permits connector sequence |
| FI-006 | A active simulated | Connector presence opens | `FAULT_ISOLATED` | `CONNECTOR_SEATED` OFF, `FAULT` ON | OFF | Inspect carrier and presence sensor, return neutral, reset | Loss removes PERMIT immediately |
| FI-007 | A active simulated | Connector latch opens | `FAULT_ISOLATED` | `CONNECTOR_LATCHED` OFF, `FAULT` ON | OFF | Re-secure after simulated safe state, inspect latch, reset | No active-equivalent unlatch is accepted |
| FI-008 | A active simulated | Pilot opens | `FAULT_ISOLATED` | `PILOT_PRESENT` OFF, `FAULT` ON | OFF | Inspect simulated pilot, restore only after separation policy, reset | Pilot loss removes PERMIT immediately |
| FI-009 | SLOT-A inserted/latched | A insertion sensor opens | `FAULT_ISOLATED` | `SLOT_A_READY` OFF, `FAULT` ON | OFF | Inspect insertion, rail, sensor and latch agreement, reset | Inserted state cannot rely on latch alone |
| FI-010 | SLOT-B inserted/latched | B insertion sensor opens | `FAULT_ISOLATED` | `SLOT_B_READY` OFF, `FAULT` ON | OFF | Inspect insertion, rail, sensor and latch agreement, reset | Inserted state cannot rely on latch alone |
| FI-011 | SLOT-A active simulated | A latch sensor opens | `FAULT_ISOLATED` | `SLOT_A_ACTIVE_SIMULATED` OFF, `FAULT` ON | OFF | Prove mechanical latch, selector neutral, safe simulated state, reset | Active latch loss cannot retain PERMIT |
| FI-012 | SLOT-B active simulated | B latch sensor opens | `FAULT_ISOLATED` | `SLOT_B_ACTIVE_SIMULATED` OFF, `FAULT` ON | OFF | Prove mechanical latch, selector neutral, safe simulated state, reset | Active latch loss cannot retain PERMIT |
| FI-013 | Both slots ready | A and B active requests applied together | `FAULT_ISOLATED` | Both active lamps OFF, `FAULT` ON | OFF | Remove both requests, inspect selector, return NEUTRAL, reset | No simultaneous active simulation occurs |
| FI-014 | Both slots ready, valid guards | No active request | Standby, no active state | Both active lamps OFF; `FAULT` may remain OFF | OFF | Select exactly one valid request; deliberate reset if policy requires | Absence of a request never creates PERMIT |
| FI-015 | SLOT-A active simulated | Removal request for A | `FAULT_ISOLATED`; removal lock remains engaged | A active lamp OFF, `FAULT` ON | OFF | Cancel request, prove simulated zero current/depleted-safe, selector NEUTRAL, reset | Cassette cannot be removed |
| FI-016 | SLOT-B active simulated | Active latch-release request | `FAULT_ISOLATED`; latch remains blocked | B active lamp OFF, `FAULT` ON | OFF | Cancel request, inspect cover/linkage, prove safe simulation, reset | Release-capable output is absent and latch stays blocked |
| FI-017 | SLOT-A empty | Wrong cassette mechanical key presented | Insertion rejected before mock engagement | `SLOT_A_READY` OFF, `FAULT` ON | OFF | Withdraw dummy, inspect key and damage, reset | Wrong key cannot reach latched/identified state |
| FI-018 | Correct mechanical insertion, wrong ID mock | Wrong cassette ID presented | `FAULT_ISOLATED` | Ready and active lamps OFF, `FAULT` ON | OFF | Remove request, correct ID/key pairing, repeat insertion, reset | Mechanical fit alone cannot grant readiness |
| FI-019 | Cassette partly inserted | Full-insertion condition absent but latch request applied | `FAULT_ISOLATED` | Ready/active OFF, `FAULT` ON | OFF | Withdraw, inspect rail/latch/sensor, complete new insertion, reset | Partial insertion never appears complete |
| FI-020 | Sensor should be inactive | Sensor simulated stuck active | `FAULT_ISOLATED` on implausible sequence | Related state lamp invalid, `FAULT` ON | OFF | Isolate simulation, repair/replace sensor path, reset | Stuck-active signal cannot bypass sequence |
| FI-021 | Sensor should be active | Sensor simulated stuck inactive | `FAULT_ISOLATED` or safe standby | Related condition lamp OFF, `FAULT` ON where contradictory | OFF | Inspect open path, restore valid signal, reset | Stuck-inactive signal fails safe |
| FI-022 | PERMIT lamp ON in valid A state | Source power lost | All indicators and PERMIT de-energized | `POWER_AVAILABLE` OFF | OFF | Restore source, inspect conditions, release reset, deliberate reset | Energy loss removes PERMIT without stored command |
| FI-023 | Power lost after FI-022 | Source power restored | Reset-required inhibited state | `POWER_AVAILABLE` ON, `RESET_REQUIRED` ON | OFF | Validate guards, new deliberate reset | Restoration alone never resumes |
| FI-024 | PERMIT lamp ON | Connector mock removed/seating opens | `FAULT_ISOLATED` | `CONNECTOR_SEATED` OFF, `FAULT` ON | OFF | Stop movement, inspect mock and latch, safe re-engagement, reset | PERMIT drops before separation continues |
| FI-025 | PERMIT lamp ON | Mechanical stop disengages | `FAULT_ISOLATED` | `STOP_ENGAGED` OFF, `FAULT` ON | OFF | Stabilize sled, inspect stop, restore structural stop, reset | Stop loss immediately removes permission |
| FI-026 | PERMIT lamp ON | Pilot lost | `FAULT_ISOLATED` | `PILOT_PRESENT` OFF, `FAULT` ON | OFF | Inspect sequence, restore pilot in safe order, reset | Pilot loss immediately removes permission |
| FI-027 | Reset input released in normal use | Reset input simulated shorted/held | Reset action rejected; fault latched if detected | `RESET_REQUIRED` ON, `FAULT` ON | OFF | Repair input, prove released state, deliberate reset | Constant reset cannot acknowledge a fault |
| FI-028 | SLOT-A signals mixed | Impossible slot state such as ID true while insertion false | `FAULT_ISOLATED` | Slot ready/active OFF, `FAULT` ON | OFF | Correct mechanical/sensor cause, restart from empty, reset | Impossible state never permits |
| FI-029 | Selector moving through NEUTRAL | Mechanical selector jam simulated | `FAULT_ISOLATED`; both requests absent | Both active lamps OFF, `FAULT` ON | OFF | Isolate, clear jam under guarded recovery, inspect linkage, reset | Jam cannot leave or create two active selections |
| FI-030 | Valid stopped/connected state | One required cable disconnected | Safe open state or `FAULT_ISOLATED` | Related condition OFF, `FAULT` ON as applicable | OFF | Inspect and restore disconnected path, continuity review, reset | Cable disconnection cannot be interpreted true |
| FI-031 | Fault latched after any case | Operator requests restart without correcting fault | Remain `FAULT_ISOLATED` | `FAULT` and `RESET_REQUIRED` ON | OFF | Correct and inspect cause, restore guards, deliberate reset | Restart request alone changes no safety state |
| FI-032 | Valid A active simulation | Microcontroller/display record becomes invalid or silent | Hardwired safety state unchanged; record fault indication if available | Hardwired lamps remain authoritative; `FAULT` ON if monitored | Unchanged only if all hardwired guards remain valid; never software-forced ON | Repair record/display path without bypassing hardwired chain | Software cannot create, latch, or restore PERMIT |

## Mechanical validation matrix

Each row contains setup, repetitions, observation, measurement, pass, fail, abort, and evidence. Actual count: **30**.

| ID | Setup | Repetitions | Observation | Measurement | Pass | Fail | Abort | Evidence |
|---|---|---:|---|---|---|---|---|---|
| MV-001 | Centered dry hand-pushed sled, nominal measured geometry | 5 | Guide-first, two-point stop, carrier engagement order | Speed, center offset, stop contact, residual X/Z travel | ≤0.05 m/s, stop first, no damage/load at mock | Wrong order, false sensor, mock load, damage | Any global abort condition | Setup revision, five result rows, measurements, images reserved |
| MV-002 | `LATERAL_LEFT_5MM` | 5 | Left guide capture and stable stop | Offset, speed, guide contact, residual travel | Captures without ride-up/damage | Ride-up, sharp load, bottoming | Instability or damage | Offset gauge and cycle records |
| MV-003 | `LATERAL_RIGHT_5MM` | 5 | Right guide capture and stable stop | Same as MV-002 | Same as MV-002 | Same as MV-002 | Same as MV-002 | Offset gauge and cycle records |
| MV-004 | `LATERAL_LEFT_10MM` | 5 | Progressive guide correction | Offset, speed, contact path, travel | No damage, stop first, mock unload | Abrupt contact or bottoming | Same as global | Measurements and inspection |
| MV-005 | `LATERAL_RIGHT_10MM` | 5 | Progressive guide correction | Same as MV-004 | Same as MV-004 | Same as MV-004 | Same as global | Measurements and inspection |
| MV-006 | `LATERAL_LEFT_15MM` provisional maximum | 5 | Capture at target boundary | Offset verified ± measurement uncertainty, speed, travel | No damage/ride-up; connector unloaded | Bypass, damage, overload, travel limit | Any unstable approach | Boundary evidence and review |
| MV-007 | `LATERAL_RIGHT_15MM` provisional maximum | 5 | Capture at target boundary | Same as MV-006 | Same as MV-006 | Same as MV-006 | Same as MV-006 | Boundary evidence and review |
| MV-008 | `YAW_LEFT_1_DEG` | 5 | Symmetric stop progression | Yaw, speed, left/right pad contact | Both stop faces plausible, no bind | Single hard impact or mock load | Instability | Angle gauge and witness marks |
| MV-009 | `YAW_RIGHT_1_DEG` | 5 | Symmetric stop progression | Same as MV-008 | Same as MV-008 | Same as MV-008 | Same as MV-008 | Angle gauge and witness marks |
| MV-010 | `YAW_LEFT_2_DEG` | 5 | Guide/stop/carrier response | Yaw, pad sequence, residual travel | No damage, stop first, no bottoming | Bind, guide ride-up, overload | Instability or damage | Angle and travel records |
| MV-011 | `YAW_RIGHT_2_DEG` | 5 | Guide/stop/carrier response | Same as MV-010 | Same as MV-010 | Same as MV-010 | Same as MV-010 | Angle and travel records |
| MV-012 | `YAW_LEFT_3_DEG` provisional maximum | 5 | Boundary response | Yaw with uncertainty, both stops, carrier travel | No damage and connector remains unloaded | Damage, bottoming, one-side structural anomaly | Any unstable approach | Boundary review package |
| MV-013 | `YAW_RIGHT_3_DEG` provisional maximum | 5 | Boundary response | Same as MV-012 | Same as MV-012 | Same as MV-012 | Same as MV-012 | Boundary review package |
| MV-014 | `COMBINED_LEFT_15MM_YAW_3_DEG` | 5 | Worst provisional left combination | Offset, yaw, speed, stop order, all carrier axes | No damage/ride-up/bottoming | Any order or load-path failure | Instability, damage, pinch risk | Combined-condition record |
| MV-015 | `COMBINED_RIGHT_15MM_YAW_3_DEG` | 5 | Worst provisional right combination | Same as MV-014 | Same as MV-014 | Same as MV-014 | Same as MV-014 | Combined-condition record |
| MV-016 | Sled mass configured to 15 kg, centered | 5 | Ballast retention and stopping | Verified mass, speed, stop witness, frame movement | Retention secure; stop first; no frame motion | Ballast shift, loose retention, deformation | Retention concern | Scale record and retention checklist |
| MV-017 | Sled mass configured to 30 kg, centered | 5 | Same as MV-016 | Same as MV-016 | Same as MV-016 | Same as MV-016 | Same as MV-016 | Scale record and retention checklist |
| MV-018 | Sled mass configured to 45 kg, centered | 5 | Same as MV-016 | Same as MV-016 | Same as MV-016 | Same as MV-016 | Same as MV-016 | Scale record and retention checklist |
| MV-019 | Left guide set 5 mm wider than nominal reference | 5 | Independent adjustment behavior | Left/right scales, clear width, wheel path | Setting retained; no ride-up; asymmetry documented | Loose lock or unexpected contact | Guide movement | Scale and fastener evidence |
| MV-020 | Right guide set 5 mm wider than nominal reference | 5 | Same as MV-019 | Same as MV-019 | Same as MV-019 | Same as MV-019 | Same as MV-019 | Scale and fastener evidence |
| MV-021 | Reviewed worn-strip simulation installed | 5 | Wear detectability and capture | Simulated wear amount, wheel contact, fastener state | Inspection identifies condition; no structural damage | Hidden wear, loose strip, ride-up | Strip detachment | Before/after inspection record |
| MV-022 | Replaceable brush removed while unpowered | 1 inspection plus 5 dry cycles only if review permits | Cleaning protection absence | Debris-access visibility and mock condition | Missing brush is obvious and recorded; no false readiness | Hidden missing part or damage | Debris enters protected zone | Configuration and inspection record |
| MV-023 | Defined small inert debris at guide entrance, unpowered | 5 after separate debris approval | Guide cleaning and ride-up risk | Debris definition, wheel path, clearance | Debris visible/removable; no ride-up | Entrapment, projectile, guide climb | Uncontrolled debris movement | Debris definition and cleaning record |
| MV-024 | Carrier positioned at a provisional travel limit before approach | 1 inspection; no approach if residual margin absent | Fail-closed pre-use detection | Axis position and remaining travel | Inspection blocks approach when margin <5 mm | Approach allowed with bottomed/limited carrier | Any attempted unsafe approach | Travel gauge and stop decision |
| MV-025 | One stop pad removed, rig unpowered | 1 inspection only | Pre-use fail-closed detection | Pad-presence evidence and stop symmetry | Trial blocked; stop sensor cannot imply ready | Approach allowed or ready shown | Any sled movement toward rig | Inspection and inhibit record |
| MV-026 | `DUMMY-CASSETTE-A`, correct key, SLOT-A | 50 insertion/removal cycles | Rail, key, latch, ID, force, mass support | Mass, insertion/removal force, cycle count, sensor sequence | 50 cycles; no false latch/damage/mass on mock | Key bypass, high force trend, damage, false state | Pinch, ballast movement, jam | Per-cycle log and force trend |
| MV-027 | `DUMMY-CASSETTE-B`, correct key, SLOT-B | 50 insertion/removal cycles | Same as MV-026 | Same as MV-026 | Same as MV-026 | Same as MV-026 | Same as MV-026 | Per-cycle log and force trend |
| MV-028 | Selected active-equivalent dummy, guarded pull attempt | 5 | Mechanical removal lock | Pull force at defined point and displacement | Successful removal count 0; no damage | Any extraction or latch release | Instability, excessive force, pinch risk | Force/displacement and latch evidence |
| MV-029 | Wrong-key dummy presented to opposite slot | 5 per direction | Rejection before mock engagement | Insertion depth, key contact, damage | Bypass count 0; no damage | Latch/ID or mock engagement succeeds | Wedge or damage | Keying and insertion-depth record |
| MV-030 | Fault-isolated, `PERMIT` OFF, guarded manual emergency release | 5 | Recovery access and NEUTRAL requirement | Selector position, cover action, latch state | Release only from reviewed safe state; procedure complete | Active-equivalent release or permission restoration | Unexpected movement or pinch risk | Ordered recovery record and review |

## Acceptance criteria

The following are provisional rig criteria, not product certification:

- mechanical stop contacts first at no more than `0.05 m/s`;
- connector mock receives no stop, vehicle, sled, latch, or cassette-weight load;
- lateral `±15 mm` and yaw `±3°` position without damage within the measured envelope;
- guide ride-up count: 0;
- cable strain failure count: 0;
- latch false-positive count: 0;
- simultaneous `ACTIVE_SIMULATED` count: 0;
- successful active dummy cassette removal count: 0;
- power-restoration automatic `PERMIT` count: 0;
- recovery caused only by ESTOP release count: 0;
- `PERMIT` ON with an open sensor path: 0;
- `PERMIT` ON in an impossible state: 0;
- dry connector-mock cycles: 100;
- 20 wet unpowered cycles;
- 20 mud contamination inspection cycles;
- cassette insertion/removal cycles: 50 per slot;
- successful mechanical-key bypasses: 0;
- connector block and wear strip are independently replaceable;
- documented manual recovery returns through an isolated, `PERMIT`-OFF state.

## Future evidence record template

This is a field list, not a completed record:

| Field | Placeholder rule |
|---|---|
| test ID | Use matrix ID only |
| rig revision | Controlled revision placeholder |
| operator | Role identifier only; no personal name in examples |
| date | `YYYY-MM-DD` placeholder only |
| sled mass | 15 kg, 30 kg, 45 kg, or measured applicable value |
| guide setting | Measurement variable and observed value |
| lateral offset | Signed measured offset with uncertainty |
| yaw offset | Signed measured angle with uncertainty |
| approach speed | Measured value and instrument resolution |
| connector mock revision | Controlled mock revision |
| cassette revision | A/B controlled revision or not applicable |
| sensor state | Ordered observed inputs |
| expected result | Matrix-derived expectation |
| actual result | Blank until an authorized future test |
| photos | Repository-external filename placeholder |
| video filename | Repository-external filename placeholder |
| damage notes | Inspection result placeholder |
| cleaning performed | Method/revision placeholder |
| pass/fail | Blank until review |
| reviewer sign-off | Role and approval reference; no personal example |

ST-013B creates no experiment record and stores no report in the repository.

## ST-013C interface control document

All values remain unresolved until their freeze condition is met. Actual count: **15**.

| ID | Interface | Owner module | Mating module | Value or variable | Tolerance | Measurement source | Unresolved status | Freeze condition |
|---|---|---|---|---|---|---|---|---|
| ICD-001 | Rover wheel envelope | MODULE-B | Dummy sled/rover reference | `W_WHEEL_OUTER`, `W_WHEEL`, `D_WHEEL`, `L_WHEELBASE` | Measurement uncertainty TBD | Repeated physical wheel measurements | OPEN | Loaded/unloaded envelope reviewed |
| ICD-002 | Rover front stop face | MODULE-C | Sled/rover reference | Measured front approach geometry | Flatness and left/right agreement TBD | Physical contact-face survey | OPEN | Structural face and keep-outs accepted |
| ICD-003 | Connector target coordinate | MODULE-D | Sled/rover target plate | `H_CONNECTOR_TARGET`, `X_CONNECTOR_TARGET` | Repeatability and loaded-height tolerance TBD | Floor/center-datum physical measurement | OPEN | Loaded target measurement reviewed |
| ICD-004 | Guide adjustment range | MODULE-B | MODULE-A | `W_ROVER_MAX + 10 mm` to `W_ROVER_MAX + 50 mm` | Scale increment ≤5 mm provisional | Rover width register and guide gauge | OPEN | Envelope and lock method accepted |
| ICD-005 | Floating mount travel | MODULE-D | MODULE-C/target block | X ±20 mm, Z ±15 mm, yaw ±5°, pitch ±3° provisional | Axis-specific stop tolerance TBD | Carrier gauge and engagement study | OPEN | Measured force/travel and 5 mm residual margin accepted |
| ICD-006 | Connector mock bolt pattern | MODULE-D | Sacrificial block | Variable `PATTERN_CONNECTOR_MOCK` | Position tolerance TBD | Mock interface measurement | OPEN | Replaceable block candidate reviewed |
| ICD-007 | Cassette outer envelope | MODULE-E | SLOT-A/SLOT-B | Variable `ENVELOPE_CASSETTE` | Mass target 9600 g ±100 g; dimensions TBD | Dummy mass/envelope measurement | OPEN | Two identical dummies measured |
| ICD-008 | Cassette handle keep-out | MODULE-E | Operator access/base | Variable `KEEP_OUT_HANDLE` | Finger clearance TBD | Handling mock and risk review | OPEN | Two-hand handling review accepted |
| ICD-009 | Slot rail spacing | MODULE-E | Dummy cassettes | Variable `SPACING_SLOT_RAIL` | Parallelism and clearance TBD | Rail/cassette measurement | OPEN | Force trend and 50-cycle plan accepted |
| ICD-010 | Slot latch interface | MODULE-E | Cassette latch plate/selector | Variable `INTERFACE_SLOT_LATCH` | Engagement and wear tolerance TBD | Latch mock measurement | OPEN | Active-removal prevention reviewed |
| ICD-011 | Sensor mounting zones | MODULE-C/D/E | MODULE-F input targets | Variable `ZONE_SENSOR` | Position repeatability TBD | Sensor target and mechanism survey | OPEN | Contradiction/fault coverage accepted |
| ICD-012 | ESTOP panel mounting zone | MODULE-F | MODULE-A/operator | Variable `ZONE_ESTOP_PANEL` | Reach and guard clearance TBD | Human-reach review on measured rig | OPEN | Independent access review accepted |
| ICD-013 | Rig anchor points | MODULE-A | Floor/test-area interface | Variable `ZONE_RIG_ANCHOR` | Load and position tolerance TBD | Structural review using measured test mass | OPEN | No field installation implied; bench restraint accepted |
| ICD-014 | Drainage and cleaning zones | MODULE-A/D/E | Environmental/service access | Variable `ZONE_DRAIN_CLEAN` | No retained pocket; dimensions TBD | Visual/drainage mock review | OPEN | Unpowered wet/mud protocol accepted |
| ICD-015 | Replaceable sacrificial parts | MODULE-B/C/D | Wear strips, pads, guide/block | Variable `INTERFACE_SACRIFICIAL` | Replacement fit tolerance TBD | Part-interface and inspection study | OPEN | Tool access and independent replacement demonstrated |

## Preliminary BOM

No item is purchased or selected to an exact product.

### Docking base

- plywood versus steel/aluminum frame comparison;
- adjustable feet;
- anchor brackets;
- anti-slip deck;
- centerline markers.

### Wheel guides

- steel angle versus extrusion comparison;
- tapered entry pieces;
- sacrificial strips;
- adjustment slots;
- bolts and lock nuts.

### Mechanical stop

- stop beam;
- replaceable elastomer pads;
- stop sensor brackets;
- reinforcement plates.

### Floating connector mock

- linear slide versus compliant plate comparison;
- springs versus elastomer comparison;
- mock connector blocks;
- replaceable guide funnel;
- strain-relief mock;
- brush;
- drip shield.

### Dummy cassette rig

- two cassette frames;
- enclosed, double-retained ballast;
- two-hand handles;
- rails and rollers;
- latches;
- keying parts;
- sensor targets.

### Low-energy panel

- current-limited source no greater than 12 V DC and 1 A;
- branch fuse no greater than 1 A;
- physical ESTOP;
- separate reset device;
- small relay candidates;
- terminal blocks;
- labeled indicator lamps;
- buzzer;
- microswitch candidates;
- cable;
- enclosure.

### Measurement

- ruler;
- caliper;
- angle gauge;
- luggage scale or force gauge;
- weighing scale;
- speed-marking tape;
- camera tripod.

## Provisional cost bands

These are planning ranges, not quotations or purchase authority.

| Category | Planning range |
|---|---:|
| Docking base and guides | JPY 15,000–45,000 |
| Mechanical stop | JPY 5,000–15,000 |
| Floating connector mock | JPY 8,000–25,000 |
| Two dummy cassettes and A/B rig | JPY 15,000–40,000 |
| Low-energy interlock panel | JPY 15,000–35,000 |
| Sensors, ESTOP, and indicators | JPY 10,000–25,000 |
| Measurement aids and consumables | JPY 5,000–20,000 |
| **Provisional total** | **JPY 73,000–205,000** |

Excluded are an actual rover, actual battery, actual charging connector, charger, mains electrical work, power cassette, battery mule, five-bay frame, outdoor-certified enclosure, CAD/printing cost, electrician fee, and product certification.

## Minimum viable rig planning band

The minimum viable rig contains only a hand-pushed dummy sled, one adjustable guide pair, one mechanical stop, one unpowered floating connector mock, one dummy cassette slot, and one hardwired 12 V `PERMIT` indicator chain. The planning band is **JPY 35,000–80,000**. It still requires separate review, purchase authority, fabrication authority, and experiment authority.

## Safety and approval boundary

This document recommends no battery, mains wiring, charger, live connector product, main contactor, motor, powered actuator, or release solenoid. It produces no hardware command and grants no approval for CAD, fabrication, purchase, experiment, field operation, night operation, automatic restart, or unattended operation.
