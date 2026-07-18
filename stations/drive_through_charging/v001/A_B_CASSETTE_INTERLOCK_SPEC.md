# A/B Cassette Interlock Specification

## Status and safety boundary

Status: **DESIGN ONLY**

This specification defines a fail-closed state model for two exchange slots, A and B. It does not command hardware, authorize construction, or certify a circuit. The physical ESTOP remains independent of the controller and removes the charging-permission path without relying on state-machine execution.

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

## Invariants

1. At most one slot is `ACTIVE`.
2. Slots A and B are never directly paralleled.
3. `ACTIVE`, `SWITCH_REQUESTED`, `CURRENT_RAMP_DOWN`, and `ZERO_CURRENT_CONFIRMED` inhibit mechanical release.
4. A cassette is removable only in `REMOVAL_ALLOWED` after its contactor is proven open and stored-energy hazards are reviewed.
5. Precharge is mandatory before a power contactor may close.
6. A switch requires charger-current ramp-down, independent zero-current confirmation, and source-contactor opening before another slot may become active.
7. Missing, stale, contradictory, or out-of-range sensing is a fault, never permission.
8. Communication loss, controller restart, ESTOP operation, or return of power never causes automatic activation, restart, or resumption.
9. Manual reset is accepted only after isolation, inspection, cause recording, and restoration of all guards.
10. The controller has charging-permission authority only. It has no rover motion authority.
11. `INSERTED` can never transition directly to `ACTIVE`.
12. The main contactor can never close before successful `PRECHARGE` completion.
13. An `ACTIVE` designation cannot be released before zero current is independently confirmed.

## Required independent inputs and outputs

The design must independently observe slot presence, mechanical latch, connector pilot, identity, source voltage, source polarity, cassette temperature, BMS-ready status, precharge voltage convergence, source-contactor auxiliary state, charger current, ESTOP loop, controller health, and communication health. Redundant or plausibility-checked measurement is required where a single false reading could permit hot opening.

Conceptual outputs are limited to permission signals for precharge, a source contactor, charger enable, and a mechanically independent release inhibit. Their electrical implementation, safe state, diagnostic coverage, and emergency-energy removal require licensed review. This document produces no output.

## State definitions

| State | Definition and permitted condition |
|---|---|
| `EMPTY` | No cassette is detected; contactor and precharge paths are open and release is inhibited from moving unexpectedly. |
| `INSERTED` | Presence and mechanical seating are detected, but identity and electrical compatibility are not accepted. |
| `IDENTIFIED` | Cassette identity is valid, unique, permitted, and bound to the physical slot. |
| `VOLTAGE_CHECK` | Source voltage, polarity, and measurement plausibility are being checked with the power path open. |
| `TEMPERATURE_CHECK` | Cassette and relevant connector temperatures are being checked against reviewed limits. |
| `BMS_READY_CHECK` | Independent BMS permission and fault status are being checked; silence is not readiness. |
| `PRECHARGE` | A current-limited path is enabled while the main contactor remains open and voltage convergence is supervised. |
| `READY_STANDBY` | All entry checks passed; the slot is safe to wait but is not connected as the active source. |
| `ACTIVE` | The slot is the sole permitted source; its latch and release are inhibited. |
| `SWITCH_REQUESTED` | A deliberate source-change request is latched; no second source is enabled. |
| `CURRENT_RAMP_DOWN` | Charger demand is being reduced under supervision; the source contactor remains controlled. |
| `ZERO_CURRENT_CONFIRMED` | Independent current evidence satisfies the reviewed zero-current threshold and dwell time. |
| `CONTACTOR_OPEN` | The source contactor is commanded open and auxiliary plus electrical evidence prove isolation. |
| `DEPLETED_SAFE` | The cassette is isolated and judged safe for the reviewed removal sequence. |
| `REMOVAL_ALLOWED` | Mechanical removal may be deliberately enabled; no power path may close. |
| `FAULT_ISOLATED` | Charging permission is removed, power paths are commanded open, release remains inhibited until the safe recovery condition is known, and the fault is latched. |

All 16 state names are exact and normative. Implementations must not add an implicit `RUNNING`, `AUTO`, or restart state.

## Timeout policy

The symbolic limits `T_IDENTIFY`, `T_CHECK`, `T_PRECHARGE`, `T_RAMP`, `T_ZERO_DWELL`, `T_OPEN`, and `T_REMOVE` are unresolved engineering values. They must be derived from measured equipment behavior and approved during licensed review. A missing timeout, an expired timeout, or an invalid timer source causes `FAULT_ISOLATED`. A reboot invalidates every in-progress timer and requires manual recovery; elapsed time is never reconstructed to resume a transition.

## Transition table

| Current state | Next state | Trigger | Guard | Fail-closed action | Timeout | Failure result | Manual recovery |
|---|---|---|---|---|---|---|---|
| `EMPTY` | `INSERTED` | Stable presence is detected | Contactors open; no contradictory presence or latch signal | Keep charger and contactors inhibited | Debounce within `T_CHECK` | `FAULT_ISOLATED` on implausible sensing | Isolate, inspect sensor and seating, reset |
| `INSERTED` | `IDENTIFIED` | Identity read completes | Identity is valid, unique, allowed, and agrees with slot binding | Keep all energy paths open | `T_IDENTIFY` | `FAULT_ISOLATED` | Remove energy, inspect identity path, reset |
| `IDENTIFIED` | `VOLTAGE_CHECK` | Validation request | Identity remains valid; connector pilot and latch agree | Begin passive measurement only | `T_CHECK` | `FAULT_ISOLATED` | Inspect connector and measurement chain, reset |
| `VOLTAGE_CHECK` | `TEMPERATURE_CHECK` | Voltage check passes | Voltage, polarity, channel agreement, and allowed difference are within reviewed limits | Keep main contactor open | `T_CHECK` | `FAULT_ISOLATED` | Isolate, record readings, correct cause, reset |
| `TEMPERATURE_CHECK` | `BMS_READY_CHECK` | Temperature check passes | All required temperatures valid and within reviewed limits | Keep main contactor open | `T_CHECK` | `FAULT_ISOLATED` | Cool or repair under approved procedure, inspect, reset |
| `BMS_READY_CHECK` | `PRECHARGE` | BMS-ready check passes | Explicit BMS ready; no BMS, ESTOP, controller, communication, or sensor fault; other slot not `ACTIVE` | Enable only reviewed current-limited precharge path | `T_CHECK` | `FAULT_ISOLATED` | Isolate, diagnose BMS/communications, reset |
| `PRECHARGE` | `READY_STANDBY` | Voltage convergence is proven | Convergence rate and final difference pass; no thermal/current fault; main contactor auxiliary proves open before command | Close source contactor only under reviewed interlock, prove closed, then open precharge path | `T_PRECHARGE` | `FAULT_ISOLATED` | Open all paths, discharge as reviewed, inspect, reset |
| `READY_STANDBY` | `ACTIVE` | Deliberate activation request | No other slot `ACTIVE`; charger initially disabled; all checks fresh; contactor proof valid; ESTOP healthy; manual restart permission present | Latch sole-active token, inhibit release, then grant charger permission | `T_CHECK` | Remain inhibited or enter `FAULT_ISOLATED` on contradiction | Resolve contention or fault; deliberate request required |
| `ACTIVE` | `SWITCH_REQUESTED` | Deliberate switch, depletion, shutdown, ESTOP, communication loss, or fault request | Request is latched independently; no release request is honored | Remove new charge-demand permission and inhibit release | Immediate transition required | `FAULT_ISOLATED` if state cannot be proven | Isolate and inspect; never resume automatically |
| `SWITCH_REQUESTED` | `CURRENT_RAMP_DOWN` | Controlled shutdown begins | Charger control path is responsive or emergency isolation path has taken precedence | Command charger demand toward zero; keep release inhibited | `T_CHECK` | `FAULT_ISOLATED` | Use approved isolation procedure; inspect, reset |
| `CURRENT_RAMP_DOWN` | `ZERO_CURRENT_CONFIRMED` | Current falls below reviewed threshold | Independent current channels agree for `T_ZERO_DWELL`; sensor is healthy | Remove charger enable; retain source contactor until zero is proven | `T_RAMP` plus `T_ZERO_DWELL` | `FAULT_ISOLATED` | Emergency isolate only as reviewed; investigate current path |
| `ZERO_CURRENT_CONFIRMED` | `CONTACTOR_OPEN` | Open request | Zero-current proof remains valid; no welded-contactor indication | Command source contactor open; keep release inhibited | `T_OPEN` | `FAULT_ISOLATED` | Isolate upstream, inspect contactor, licensed recovery |
| `CONTACTOR_OPEN` | `DEPLETED_SAFE` | Open proof completes | Auxiliary contact says open; bus and load-side voltage decay pass reviewed plausibility limits | Revoke sole-active token; keep charger inhibited | `T_CHECK` | `FAULT_ISOLATED` | Prove isolation by approved method, inspect, reset |
| `DEPLETED_SAFE` | `REMOVAL_ALLOWED` | Deliberate release request | Contactor open proof, safe voltage, safe temperature, valid latch state, no active energy path | Permit reviewed mechanical release only | `T_CHECK` | `FAULT_ISOLATED` | Re-inhibit release, isolate, inspect, reset |
| `REMOVAL_ALLOWED` | `EMPTY` | Stable absence is detected | Pilot broke before power contacts; no current; contactor remains open | Revoke release permission and retain all energy inhibits | `T_REMOVE` | `FAULT_ISOLATED` on timeout or sequence error | Inspect connector/latch and reset after safe absence |
| Any non-fault state | `FAULT_ISOLATED` | Guard loss, timeout, ESTOP, reboot, communication loss, contradictory sensor, unexpected current, overtemperature, BMS fault, or contactor mismatch | None; fault transition has priority | Remove charger permission, command energy paths open where safe, latch fault, inhibit release until isolation is known | Immediate; hardware independent path must not depend on software timing | Remain `FAULT_ISOLATED` | Isolate, inspect, record cause/evidence, restore guards, deliberate manual reset |
| `FAULT_ISOLATED` | `EMPTY` | Manual reset with cassette absent | Absence stable; contactors proven open; safe voltage; ESTOP reset deliberately; fault cause closed | Clear fault latch but do not activate or restart | `T_CHECK` | Remain `FAULT_ISOLATED` | Repeat isolation and diagnosis |
| `FAULT_ISOLATED` | `INSERTED` | Manual reset with cassette retained | Presence and latch stable; contactors proven open; safe voltage; fault cause closed; identity must be repeated | Clear fault latch and restart checks from insertion; no previous approval reused | `T_CHECK` | Remain `FAULT_ISOLATED` | Repeat isolation and diagnosis |

## A-to-B and B-to-A switch sequence

The sequence is symmetric. If A is `ACTIVE`, B may advance only to `READY_STANDBY`. A deliberate switch moves A through `SWITCH_REQUESTED`, `CURRENT_RAMP_DOWN`, `ZERO_CURRENT_CONFIRMED`, `CONTACTOR_OPEN`, and `DEPLETED_SAFE`. Only after A has relinquished the sole-active token and electrical isolation is proven may B receive a new deliberate activation request. B must revalidate freshness-sensitive guards before entering `ACTIVE`. The reverse sequence is identical.

There is no transition that closes B to bridge a falling A bus, overlaps contactors, resumes charging after a power interruption, or makes a depleted cassette removable while current flows.

## Reboot, communication, and ESTOP behavior

- Controller reboot initializes both slots as untrusted and charging-inhibited. Physical inputs are reacquired, contactors are proven open, and manual reset is required.
- Communication loss removes charging permission. It cannot be treated as a request to continue from the last state.
- Communication restoration only restores the ability to inspect and request recovery. It never transitions a slot to `ACTIVE`.
- ESTOP has an independent hardwired safety path suitable for the reviewed architecture. Software records the condition but is not the sole means of isolation.
- Resetting ESTOP does not reset the fault latch, close a contactor, grant charger permission, or release a cassette.

## Validation traceability

PHASE-3 verifies pilot, latch, sensor plausibility, and loss-of-signal behavior at limited energy. PHASE-4 exercises the entire A/B state sequence with dummy sources and a dummy load, including every timeout and fault transition. PHASE-5 validates current ramp-down and zero-current proof. No real battery or mains source is introduced until all applicable prior evidence passes and separate approvals are recorded.

## Unresolved engineering values

Voltage ranges, temperature limits, current thresholds, zero-current dwell, timeout values, contactor ratings, precharge impedance, discharge limits, diagnostic coverage, sensor redundancy, safe torque, fuse coordination, and performance level are intentionally unresolved. They require authoritative battery/BMS data, measurements, hazard analysis, and licensed electrical review.
