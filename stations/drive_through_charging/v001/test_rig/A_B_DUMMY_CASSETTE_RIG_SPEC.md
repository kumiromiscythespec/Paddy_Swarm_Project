# A/B Dummy Cassette Rig Specification

## Status and fixed flags

Status: **DESIGN ONLY — dummy mass and mechanical simulation only**

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

No real battery module, power cassette, charger, main contactor, or energized connector is present. The 9.6 kg target is a mechanical planning value inherited from ST-013A, not an ergonomic or electrical certification.

## MODULE-E — A/B dummy cassette slide rig

### Purpose

Validate two identical hand-handled dummy cassette envelopes, horizontal insertion/removal, mechanical keying, latch sensing, and physical prevention of simultaneous `ACTIVE_SIMULATED` states or active-equivalent removal.

### Interfaces

MODULE-A mounting datum, `DUMMY-CASSETTE-A`, `DUMMY-CASSETTE-B`, `SLOT-A`, `SLOT-B`, horizontal rails, mechanical selector, protected manual release, floating mock blocks, sensor targets, and dry contact simulations to MODULE-F.

### Adjustment range

Rail spacing, insertion depth, latch position, mock connector position, handle keep-out, and force-measurement points remain unresolved until the cassette envelope and handling study are measured. Adjustment is bolted and double-locked; no rail dimension is guessed final.

### Replaceable parts

Rollers, low-friction rail wear surfaces, tapered entries, mechanical keys, latch plates, sensor targets, mock connector blocks, drain/brush parts, selector linkage, and release cover.

### Failure modes

Wrong-key insertion, incomplete insertion reported complete, simultaneous active request, selector jam, active-equivalent latch release, removal under active state, connector supporting mass, ballast movement, pinch exposure, false ID, rail contamination, or inaccessible recovery.

### Inspection points

Cassette mass label and retention, handles, feet, center-of-gravity mark, rails, rollers, keys, end stops, latches, sensors, selector position, release cover, connector residual travel, drain, cleaning access, and insertion/removal force points.

### Transport and storage

Remove each cassette using two hands or a separately reviewed aid, place it on its feet, secure ballast, lock the slide rig empty, protect rails and keys, and store dry. Do not transport a cassette partly inserted.

### ST-013C CAD boundary

Cassette envelope, handle keep-out, feet, ballast retention zones, rail and roller datums, latch and key interfaces, selector/linkage envelope, sensor zones, mock bolt pattern, drain/cleaning access, and guarded recovery access.

## Dummy cassette definitions

`DUMMY-CASSETTE-A` and `DUMMY-CASSETTE-B` have identical dimensions and each target `9600 g ±100 g` complete.

Each mass allocation records frame, two-hand handle, ballast, mock connector, latch plate, and ID target. Ballast must be enclosed, bolted, independently retained a second way, externally labeled with verified total mass, and located to keep the center of gravity low. A/B identity uses both a physical mechanical key and an ID mock; color alone is insufficient.

The connector mock never supports cassette mass. The slide rails and structure receive the full weight before connector-mock engagement.

## Handling boundary

- A 9.6 kg cassette is not assumed safe for one-hand lifting.
- A two-hand handle and visible center-of-gravity mark are required.
- Finger-clearance and pinch keep-out zones are explicit interfaces.
- Stable feet permit floor placement without resting on a connector mock.
- The cassette first rests fully on rails, then is pushed horizontally.
- Insertion-force and removal-force measurement points are provided.
- A guarded manual emergency release supports recovery but cannot bypass active-equivalent removal prevention.
- An active-equivalent cassette resists pullout mechanically, not only through an indicator or software state.
- The under-10 kg goal is not an ergonomic approval.

## Slot identifiers and states

Slot identifiers are exactly `SLOT-A` and `SLOT-B`. The low-energy mechanical-rig states are:

`EMPTY`, `INSERTING`, `INSERTED`, `LATCHED`, `IDENTIFIED`, `READY_STANDBY`, `ACTIVE_SIMULATED`, `DEPLETED_SAFE_SIMULATED`, `REMOVAL_ALLOWED`, and `FAULT_ISOLATED`.

`ACTIVE_SIMULATED` carries no energy authority. At most one slot may occupy it. A fault or power loss removes the active simulation request, leaves `PERMIT` OFF, and requires deliberate manual reset.

## Physical slide requirements

- horizontal low-friction rail and rollers;
- tapered entry and end stop;
- cassette-specific mechanical key;
- positive latch, latch sensor, and full-insertion sensor;
- active-equivalent removal lock;
- protected manual release cover;
- floating connector mock mount with no weight-bearing function;
- drain and cleaning access;
- insertion/removal force measurement points;
- mechanical rejection of an incorrect key before mock engagement;
- no permanent adhesive between slot, rail, latch, or mock modules.

## Mechanical interlock alternatives

| Criterion | INTERLOCK-M1 shared mechanical selector bar | INTERLOCK-M2 key-transfer system | INTERLOCK-M3 independent locks with cross-blocking linkage |
|---|---|---|---|
| Simplicity | Highest; one visible A/NEUTRAL/B selector | Medium; controlled key sequence | Lowest; two locks plus linkage |
| Printability | Good for mock housings, but load parts still need reviewed material | Key hardware is not assumed printable | Linkage geometry may be printable for fit only, not load approval |
| Metal part count | Low to medium | Medium, depending on captive-key hardware | Medium to high |
| Jam risk | One accessible sliding member | Key and cylinder contamination can jam | Multiple joints increase jam points |
| Mud sensitivity | Low when open, shielded, and cleanable | Keyways are relatively sensitive | Exposed cross-link can trap contamination |
| Manual recovery | Visible neutral position and guarded release are straightforward | Recovery requires retained-key procedure | Requires access to both locks and linkage |
| False release risk | Low if bar physically blocks both active latch releases and position is sensed | Low with correct trapped-key sequence | Low only if linkage cannot disconnect unnoticed |
| Prevent simultaneous active | Direct physical A/NEUTRAL/B exclusion | Direct through exclusive key possession | Direct when linkage remains intact |
| Prevent active removal | Same bar blocks selected-slot release | Selected key remains trapped | Selected lock blocks release through linkage |

**Recommendation: INTERLOCK-M1 shared mechanical selector bar for the ST-013B test rig.** A three-position A/NEUTRAL/B bar is visually inspectable, cleanable, and directly prevents both selections. Its selected position physically blocks the corresponding active-equivalent latch release. The bar position is sensed for fault detection but sensing does not create the safety function. A guarded manual recovery can return the isolated rig to NEUTRAL only after `PERMIT` is OFF. The recommendation is for a dummy rig, not production hardware.

## Selector invariants

1. A and B cannot both be selected mechanically.
2. Changing A to B or B to A passes through NEUTRAL.
3. A selected slot cannot unlatch or be removed.
4. The alternate slot may be inserted and reach `READY_STANDBY`, but not `ACTIVE_SIMULATED`.
5. Simulated zero current and `DEPLETED_SAFE_SIMULATED` are required before release becomes eligible.
6. Wrong key, wrong ID, incomplete insertion, sensor contradiction, selector jam, or simultaneous electronic request causes `FAULT_ISOLATED` and `PERMIT` OFF.
7. Power restoration and ESTOP release alone never select a slot or restore `PERMIT`.

## Cycle and acceptance targets

- 50 insertion/removal cycles per slot after separate approval;
- two complete dummy cassettes at `9600 g ±100 g` each;
- wrong-key bypass successes: zero;
- simultaneous `ACTIVE_SIMULATED` observations: zero;
- successful active-equivalent removals: zero;
- connector-supported mass events: zero;
- ballast movement or retention failures: zero;
- latch false positives: zero;
- manual recovery procedure exists and returns through NEUTRAL with `PERMIT` OFF.

No physical cycle is performed in ST-013B.

## Approval boundary

This design does not authorize lifting, fabrication, ballast preparation, slide operation, low-energy wiring, fault injection, or any experiment.
