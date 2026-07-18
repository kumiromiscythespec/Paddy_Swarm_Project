# ST-013B Mechanical and Interlock Test Rig

## Phase status

Phase: **ST-013B**

Status: **DESIGN ONLY**

This directory defines a measurement-first, hand-pushed mechanical docking rig and a low-energy interlock demonstrator. It is an interface and validation-plan handoff for ST-013C; it is not permission to build, buy, wire, energize, charge, or test hardware.

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

## ST-013A inheritance

ST-013B retains the ST-013A safety boundary: one bay first; no live battery, charger, mains source, or direct battery-to-battery path; A/B direct parallel is prohibited; at most one slot is active; active removal is prohibited; precharge and zero-current behavior are represented only as simulated interlock conditions; faults and power restoration require manual reset; the connector remains high-mounted and structurally unloaded; guides and a mechanical stop act before connector engagement; and the physical ESTOP is independent of software.

The ST-013A simulation and planning values are not hardware ratings. The six ST-013A documents remain unchanged.

## Why a dummy sled precedes the rover

The first approach object is `DOCKING_DUMMY_SLED`, a non-self-propelled, hand-pushed, four-wheel platform. Adjustable wheel geometry, connector-target position, and securely retained 15 kg, 30 kg, or 45 kg ballast let the rig expose guide, stop, latch, and floating-mount faults without risking a rover, charging inlet, motor, steering system, or PTO. Every initial approach is manual; motorized approach is outside ST-013B.

## Four independent physical assemblies

The design has four independently removable physical assemblies while preserving the six contract modules:

1. docking mechanics assembly: MODULE-A docking base and approach lane, MODULE-B adjustable wheel guides, and MODULE-C mechanical stop;
2. connector-mock assembly: MODULE-D floating connector mock mount;
3. cassette assembly: MODULE-E A/B dummy cassette slide rig;
4. interlock assembly: MODULE-F low-energy interlock panel.

No module is permanently bonded to another. Bolts or other replaceable fasteners are the baseline so each assembly can be inspected, transported, replaced, and revised independently.

## Module control summary

| Module | Purpose | Interfaces | Adjustment range | Replaceable parts | Principal failure mode | Inspection points | Transport/storage | ST-013C CAD boundary |
|---|---|---|---|---|---|---|---|---|
| MODULE-A | Provides a stable single approach and forward-exit lane | Floor reference, MODULE-B, MODULE-C, centerline, anchor zones | Derived from measured rover envelope; no guessed final size | Deck panels, feet, markers, anchor brackets | Base movement, loss of level, slip, obstruction | Level, anchors, centerline, deck, clear path | Split into liftable bolted sections; dry indoor storage | Base envelope, datum scheme, bolt interfaces, anchor zones |
| MODULE-B | Aligns wheels gradually before final stop | MODULE-A slots, wheel envelope, MODULE-C approach | Independent left/right width; `W_ROVER_MAX + 10 mm` through `W_ROVER_MAX + 50 mm` | Taper entries and sacrificial wear strips | Ride-up, sharp load, loose adjustment, asymmetry | Scale, double locks, wear strips, equal height, debris access | Remove guides from base; protect scales and edges | Guide profile, slots, taper, scale datum, replaceable-strip interface |
| MODULE-C | Receives all longitudinal stop load before connector engagement | MODULE-A frame, sled stop face, stop sensor, MODULE-D clearance | Stop depth from measured front geometry; residual connector travel at least 5 mm provisional | Elastomer pads, stop faces, sensor brackets | Connector takes load, asymmetric impact, pad loss, frame yielding | Stop faces, reinforcement, pad retention, sensor plausibility | Remove pads/sensors; secure beam against rolling or bending | Stop load path, face datum, pad pocket, sensor zone, connector clearance |
| MODULE-D | Represents unpowered final connector engagement compliantly | MODULE-C stop datum, sled target block, mock cable, sensors | X ±20 mm, Z ±15 mm, yaw ±5°, pitch ±3° provisional | Sacrificial block, front guide, brush, shield, strain-relief mock | Bottoming, jam, rigid load transfer, debris retention | Travel marks, return behavior, drain, fasteners, wear, sensor targets | Lock carrier at neutral; cap and store dry | Fixed frame, carrier envelope, travel stops, bolt pattern, drainage and service zones |
| MODULE-E | Tests two horizontal dummy-cassette slots and mechanical mutual exclusion | Base datum, cassette envelopes, slot sensors, MODULE-F simulated requests | Rail spacing and latch positions remain measurement-derived | Rails, rollers, latches, keys, sensor targets, mock blocks | Dual active simulation, active removal, jam, wrong-key acceptance | Keys, latches, selector, rails, covers, insertion/removal force points | Remove and secure both 9.6 kg dummies separately; latch rails | Cassette envelope, handle keep-out, rails, latch, key, sensor and cleaning zones |
| MODULE-F | Displays a fail-closed PERMIT state at no more than 12 V DC and 1 A | Dry contacts/simulators from MODULE-C/D/E and physical ESTOP | No mechanical adjustment; thresholds and labels remain review-controlled | Fuse, lamps, labels, switches, relays, terminal blocks | False PERMIT, restart without reset, unsafe open-circuit behavior | Fuse, ESTOP, reset, labels, contact states, enclosure | Source disconnected; panel protected from moisture and impact | Panel zone, device cutouts, service clearances, cable-entry and label zones only |

## Low-energy boundary

The only conceptual source is no more than 12 V DC, limited to no more than 1 A, with branch protection no greater than 1 A. The only output is a `PERMIT` indicator lamp. No real charging permission, relay operation, contactor operation, actuator, battery, motor, or release solenoid is authorized. A hardwired normally-closed-oriented safety chain, separate physical ESTOP, and deliberate manual reset remain the design baseline. Software may later record or display state but has no safety authority.

## Document map

- `MECHANICAL_DOCKING_RIG_SPEC.md` defines the measured envelope, dummy sled, lane, wheel guides, and structural stop.
- `FLOATING_CONNECTOR_MOCK_SPEC.md` defines the unpowered compliant carrier, sequence, protection, and replacement boundaries.
- `A_B_DUMMY_CASSETTE_RIG_SPEC.md` defines two 9.6 kg dummies, horizontal slots, handling, and mechanical mutual exclusion.
- `LOW_ENERGY_INTERLOCK_SPEC.md` defines the conceptual 12 V/1 A ceiling, hardwired chain, physical ESTOP, reset, and indicators.
- `VALIDATION_MATRIX_BOM_AND_COST.md` defines future test records, at least 30 fault cases, at least 30 mechanical cases, acceptance, 15 ICD entries, and planning costs.

## ST-013C handoff and physical validation

ST-013C may create CAD only under a separate contract after the measurement register and ICD freeze conditions are satisfied. Every provisional travel, tolerance, mass, force, and cost requires physical validation and review; none is a certified product value.

## Approval boundary

No CAD, fabrication, purchase, wiring, hardware output, actual experiment, live battery, charger, mains connection, motor control, steering control, PTO control, ARM action, field use, night use, automatic restart, or unattended use is performed or approved by ST-013B.
