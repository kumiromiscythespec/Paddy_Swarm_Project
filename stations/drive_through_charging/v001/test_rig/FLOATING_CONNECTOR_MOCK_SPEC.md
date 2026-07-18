# Floating Connector Mock Specification

## Status and fixed flags

Status: **DESIGN ONLY — unpowered mock only**

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

No live connector product is selected or used. This document supplies interfaces and validation targets, not CAD, manufacturing details, or experiment permission.

## MODULE-D — Floating connector mock mount

### Purpose

Represent final high-mounted connector engagement after wheel guidance and a structural mechanical stop have already brought the hand-pushed sled to rest.

### Interfaces

- `STATION_FIXED_FRAME` bolts to the docking rig without permanent adhesive.
- `FLOATING_CARRIER` moves only within guarded provisional travel.
- `SACRIFICIAL_CONNECTOR_BLOCK` is the station-side replaceable unpowered mock.
- `ROVER_TARGET_BLOCK` mounts on the adjustable dummy-sled target plate at `H_CONNECTOR_TARGET` and `X_CONNECTOR_TARGET`.
- MODULE-C provides the stop datum and carries all longitudinal stop load.
- MODULE-F observes dry presence, seating, latch, and simulated pilot contacts only.

### Adjustment range

Provisional carrier travel targets are lateral X `±20 mm`, vertical Z `±15 mm`, limited yaw `±5°`, and limited pitch `±3°`. After MODULE-C stop engagement, at least 5 mm provisional unused travel remains on every active axis. Final travel, stiffness, force, and hard-stop locations require measurement and review.

### Replaceable parts

Sacrificial connector block, front guide/funnel, brush, mud shield, drip shield, carrier bushings or compliant elements, sensor targets, cable strain-relief mock, and quick-change fasteners.

### Failure modes

Rigid load transfer, travel bottoming, failure to return, excessive restoring force, jam, pitch/yaw bind, loose block, hidden debris, blocked drain, cable tension holding position, false seated/latch indication, or connector-first stop contact.

### Inspection points

Axis travel marks, residual-travel gauges, centering return, hard stops, fastener capture, sacrificial wear, drain opening, brush/shield access, cable slack and strain relief, sensor target alignment, and visible contact area.

### Transport and storage

Lock the carrier at a neutral transport position using a removable transport restraint, remove the target block, cap contact-like surfaces, protect sensors, and store dry with the spring/elastomer unloaded where practicable.

### ST-013C CAD boundary

Fixed-frame bolt interface, target datum, carrier envelope, X/Z/yaw/pitch travel stops, sacrificial-block bolt pattern, service clearances, drain and cleaning zones, cable keep-out, sensors, and transport restraint. Exact connector geometry remains unresolved.

## Centering architecture comparison

| Criterion | Spring return | Elastomer centering |
|---|---|---|
| Centering force | More predictable when independently guided and measured | Nonlinear and sensitive to compression geometry |
| Travel repeatability | Good with defined guides and hard stops | Can drift with compression set |
| Mud sensitivity | Exposed springs/guides require shields and cleaning access | Broad surfaces may trap mud unless fully inspectable |
| Temperature/aging | Metal spring behavior is easier to characterize | Material aging and temperature response require more evidence |
| Replaceability | Individual springs can be matched and replaced | Pads can be simple but must be replaced as a characterized set |
| Failure visibility | Broken or detached spring can be visually evident | Cracking, swelling, or set may be less obvious |
| Shock isolation | Limited unless damping is added | Natural damping can reduce rebound |
| Adjustment | Preload and rate can be measured but must be guarded | Geometry can tune response but is harder to predict |

**Recommendation: symmetric spring return with independent low-friction guides and replaceable damping pads, conditional on guarded pinch points and measured engagement force.** Springs provide inspectable, repeatable centering for a test mock. Elastomer-only centering remains a comparison option, not the baseline. Neither option may carry stop load or hold position through cable tension.

## Fixed engagement order

1. mechanical stop engages;
2. stop sensor reports a plausible engaged condition;
3. floating carrier makes initial contact;
4. sacrificial guide engages;
5. unpowered connector mock engages;
6. mechanical latch engages;
7. latch sensor reports engaged;
8. presence sensor reports seated;
9. simulated pilot contact reports present.

Any out-of-order, contradictory, or missing indication keeps the conceptual `PERMIT` indicator OFF and requires manual fault recovery.

## Fixed separation and forward-exit order

1. simulated charging permission is OFF;
2. simulated zero-current is confirmed;
3. simulated pilot is OFF;
4. latch is deliberately released;
5. connector mock separates;
6. sled reverse movement remains prohibited;
7. forward exit is simulated by hand push only.

ST-013B passes no charging current and performs none of these physical trials.

## Protection and service requirements

- downward- or side-facing drip path;
- removable mud shield;
- replaceable material-compatible brush;
- replaceable sacrificial front guide;
- visual inspection opening for all contact-like faces;
- manual debris-removal access while fully unpowered;
- carrier drain opening that cannot become a mud pocket;
- cable strain-relief mock that does not locate the carrier;
- guarded manual emergency release that cannot imply electrical permission;
- quick replacement of the connector block without disturbing MODULE-C;
- no closed cavity that cannot be cleaned and inspected.

Wet and mud validation must begin unpowered. Environmental observations do not establish an ingress-protection rating.

## Prohibited design features

- connector body or mock used as the mechanical stop;
- vehicle, sled, latch, or docking load supported by the connector;
- cable-only position retention;
- rigid-only mount;
- exposed energized contacts;
- adhesive-only mock retention;
- inaccessible cleaning volume;
- a bottomed carrier interpreted as successful seating;
- any exact live connector product selection.

## Acceptance targets for later validation

- mechanical stop contacts first at no more than `0.05 m/s`;
- no structural stop load reaches the connector mock;
- lateral `±15 mm` and yaw `±3°` approaches complete without damage within the measured rig envelope;
- 100 dry unpowered cycles, 20 wet unpowered cycles, and 20 mud-inspection cycles;
- cable strain failures, false latch indications, broken sacrificial blocks, and unintended carrier retention: zero;
- block, guide, brush, and shield are individually replaceable;
- carrier returns to a reviewed neutral zone and retains at least 5 mm provisional travel after stop engagement.

These are test-rig screening targets, not certified connector limits.

## Approval boundary

No connector, sensor, carrier, spring, latch, or emergency release is fabricated, bought, energized, or operated by ST-013B.
