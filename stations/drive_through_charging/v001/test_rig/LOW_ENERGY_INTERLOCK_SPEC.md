# Low-Energy Interlock Specification

## Status and fixed flags

Status: **DESIGN ONLY — conceptual low-energy indicator chain only**

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
low_energy_only=true
```

ST-013B creates no circuit netlist, pinout, wiring command, firmware, source code, or actual control output. A licensed electrical review remains required before any physical implementation.

## MODULE-F — Low-energy interlock panel

### Purpose

Demonstrate, through a hardwired and fail-closed concept, whether mechanical, connector-mock, slot, ESTOP, and reset conditions are all valid. The sole conceptual output is a labeled `PERMIT` indicator lamp.

### Interfaces

Dry or simulated inputs for mechanical stop, connector seating, connector latch, pilot, SLOT-A/SLOT-B state, fault injection, manual reset, and an independent physical ESTOP. MODULE-F sends no permission to a charger, rover, motor, actuator, latch release, or contactor.

### Adjustment range

No user-adjustable safety threshold is frozen. Nominal control voltage is at most 12 V DC, source current limit at most 1 A, and every branch fuse at most 1 A. Actual component voltage, coil current, contact rating, enclosure, and safety category remain unresolved.

### Replaceable parts

Fuse, labeled lamps, buzzer, relay candidates, terminal blocks, manual reset device, physical ESTOP, fault-injection switches, cable, labels, and enclosure panel inserts.

### Failure modes

False `PERMIT`, welded or stuck indication relay, open-circuit interpreted safe, reset held during startup, power restoration resumption, simultaneous active request, contradictory sensor combination, ESTOP disagreement, crossed labels, or a release-capable output.

### Inspection points

Source ceiling label, fuse rating, ESTOP contacts and latch, reset separation, relay/contact identification, terminal guards, conductor condition, input labels, state lamps, fault lamp, `PERMIT` lamp, and absence of any actuator/load connector.

### Transport and storage

Disconnect and separately secure the conceptual source, guard terminals, protect ESTOP and reset from impact, keep the enclosure dry, and retain a revision/label schedule with the panel.

### ST-013C CAD boundary

Panel envelope, mounting zone, guarded cutouts, service clearance, cable-entry zones, labels, ESTOP reach envelope, and replacement access. Electrical implementation and wiring remain outside the CAD freeze.

## Low-energy power boundary

| Property | Maximum or rule |
|---|---|
| Nominal control voltage | `≤12 V DC` |
| Source current limit | `≤1 A` |
| Branch fuse | `≤1 A` |
| Output authority | Indicator lamp only |
| Energy source type | Reviewed current-limited bench source only; no battery |

Permitted conceptual loads are indicator lamps, small relay coils, a buzzer, sensor simulation, and state lamps. Prohibited loads are a battery charger, mains inverter, main contactor, high-current load, rover battery, cassette battery, motor, any cassette-moving actuator, and any solenoid capable of releasing an active-equivalent latch.

The inclusion of a component category in the planning BOM is not approval to purchase or energize it.

## Hardwired safety chain

The preferred conceptual chain uses normally-closed-oriented safety contacts where suitable so loss of continuity removes permission. Software is not in the safety path.

Required conditions are:

`ESTOP_OK`, `MANUAL_RESET_LATCHED`, `MECHANICAL_STOP_ENGAGED`, `CONNECTOR_SEATED`, `CONNECTOR_LATCHED`, `PILOT_PRESENT`, `SLOT_STATE_VALID`, `EXACTLY_ONE_ACTIVE_REQUEST`, and `NO_FAULT`.

The conceptual relation is:

```text
PERMIT =
ESTOP_OK
AND MANUAL_RESET_LATCHED
AND MECHANICAL_STOP_ENGAGED
AND CONNECTOR_SEATED
AND CONNECTOR_LATCHED
AND PILOT_PRESENT
AND SLOT_STATE_VALID
AND EXACTLY_ONE_ACTIVE_REQUEST
AND NO_FAULT
```

`PERMIT` illuminates a lamp only. It is never a real charger-permission, ARM, relay-operation, or contactor-operation output.

## Reset and fault principles

1. A sensor wire opening produces the safe state and `PERMIT` OFF.
2. Loss of source power produces `PERMIT` OFF.
3. Restoration of source power leaves `PERMIT` OFF and `RESET_REQUIRED` indicated.
4. Holding the reset input during power-up cannot complete reset; a release followed by a deliberate new action is required.
5. Releasing ESTOP alone does not restore `PERMIT`.
6. A simultaneous A/B active request is a latched fault.
7. No active request keeps `PERMIT` OFF but is not itself permission to bypass reset.
8. An impossible sensor combination is a latched fault.
9. An active-equivalent unlatch or removal request is a latched fault.
10. Loss of connector seating, connector latch, pilot, or stop confirmation removes `PERMIT` immediately.
11. Fault recovery requires cause inspection, valid safe inputs, reset-input release, and deliberate manual reset.
12. Automatic restart and automatic resume after any fault or reboot are prohibited.

If a microcontroller is later considered, it may record and display only. It is not selected in ST-013B and may not hold safety authority, mask open contacts, generate reset, or maintain `PERMIT`.

## Physical ESTOP concept

At least one physical ESTOP is required in any future rig implementation. The candidate is normally closed, dual-contact, latching mushroom style, manually twist/pull released, separate from the reset device, reachable from the operator position, and arranged so the mechanical rig is treated as stopped and the low-energy `PERMIT` chain opens.

ST-013B addresses only the low-energy indicator chain. Actual power isolation requires a later licensed design review. ESTOP contact disagreement is a fault. Release of the mushroom does not reset the fault latch.

## State and request interpretation

| Condition | Immediate conceptual result | Latched fault | Recovery |
|---|---|---|---|
| Exactly one valid `ACTIVE_SIMULATED` request and all guards valid after reset | `PERMIT` lamp may be ON | No | Normal deliberate transition |
| Neither slot requests active | `PERMIT` OFF | No | Select one valid request, then follow reset policy if required |
| Both slots request active | `PERMIT` OFF | Yes | Remove both requests, inspect selector, return mechanical selector to NEUTRAL, manual reset |
| Active-equivalent slot requests unlatch/removal | `PERMIT` OFF | Yes | Re-secure latch, prove simulated zero current and safe state, manual reset |
| Impossible insertion/latch/ID combination | `PERMIT` OFF | Yes | Correct mechanical/sensor cause and manually reset |
| Any required contact opens | `PERMIT` OFF | According to fault matrix | Restore only after inspection; manual reset where faulted |
| Power loss or panel restart | `PERMIT` OFF | Reset required | Inputs reacquired; deliberate manual reset |

## Indicators

The minimum labeled indicators are:

- `POWER_AVAILABLE`;
- `ESTOP_OK`;
- `RESET_REQUIRED`;
- `STOP_ENGAGED`;
- `CONNECTOR_SEATED`;
- `CONNECTOR_LATCHED`;
- `PILOT_PRESENT`;
- `SLOT_A_READY`;
- `SLOT_A_ACTIVE_SIMULATED`;
- `SLOT_B_READY`;
- `SLOT_B_ACTIVE_SIMULATED`;
- `FAULT`;
- `PERMIT`.

Color is supplemental only. Every indicator has a text label, and no lamp alone proves safety.

## Simulated precharge and zero-current boundary

ST-013A requires precharge and zero-current confirmation for a real source transition. ST-013B represents these solely as dry state inputs or indicators. No current path is precharged, no main contactor exists, and no current is switched. A source change cannot be represented complete until simulated current is zero, the prior active request is removed, and the shared mechanical selector passes through NEUTRAL.

## Fault-injection interface

Fault-injection controls only simulate open, stuck, contradictory, or request conditions within the 12 V/1 A ceiling. They cannot bypass the physical ESTOP, energize a load beyond indicators/small coils/buzzer, or actuate a latch. Each injection returns to a visibly safe neutral state before manual reset.

## Acceptance boundary

Later validation must show zero `PERMIT`-ON outcomes after sensor opens, impossible states, simultaneous active requests, power restoration, ESTOP release without reset, connector loss, stop loss, pilot loss, or active-equivalent removal attempts. ST-013B performs no validation.

## Approval boundary

No hardware output, wiring, relay actuation, fuse installation, ESTOP operation, fault injection, battery connection, mains connection, charger control, BMS communication, motor/steering/PTO control, fabrication, purchase, or experiment is performed or approved.
