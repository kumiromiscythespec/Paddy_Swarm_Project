# Drive-Through Charging v001

## Phase status

**DESIGN ONLY — ST-013A**

This directory freezes a reviewable electrical topology, safety boundary, interlock concept, connector requirements, phased validation plan, and provisional planning BOM before any CAD, wiring, battery connection, purchase, or field experiment.

The phase flags are fixed:

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

## ST-012 inheritance

ST-012 is a deterministic capacity simulation, not a hardware specification. ST-013A retains these planning assumptions while marking them for measurement or licensed review:

- one rover battery is provisionally 12.8 V, 10 Ah, and 128 Wh class;
- usable energy is provisionally 102.4 Wh;
- full charge time is provisionally 180 minutes;
- the eventual station concept has five independent drive-through bays;
- rover entry and exit are forward-only;
- the connector is high-mounted;
- a station cassette has seven modules and a provisional complete mass of 9.6 kg;
- cassette slots A and B are never directly paralleled and have at most one ACTIVE slot;
- switching requires precharge, charger-current ramp-down, zero-current confirmation, and contactor interlock;
- an ACTIVE cassette cannot be unlatched or removed;
- faults and controller restart require manual recovery; automatic restart is not approved.

Simulation energy, timing, efficiency, and mass values are not treated as certified component ratings or measured hardware values.

## Why electrical architecture precedes CAD

Bus voltage, fault energy, current, isolation, protective-device clearing, creepage, enclosure segregation, contact sequence, cable bend radius, thermal limits, and connector pin allocation determine the safe mechanical envelope. Freezing CAD first could lock in an unsafe connector, inadequate conductor space, insufficient drainage, or an A/B mechanism that permits hot removal. CAD therefore remains out of scope until the electrical decision and validation gates are accepted.

## Why the first test has one bay

One rover, one charger, and one connector pair isolate docking, latch, pilot, inhibit, temperature, and charge-current behavior. Five-bay concurrency would multiply fault energy and obscure root causes before single-bay protections are demonstrated. The first energized test does not include an A/B cassette.

## Why GRID and PACK remain separate

`GRID-AC` validates the rover, certified charger, and bay connector without cassette conversion or exchange risks. PACK testing adds module topology, DC fault energy, conversion, A/B interlock, thermal load, and cassette handling. The two sources are mutually exclusive in a test configuration; there is no hybrid or automatic transfer between them in ST-013A.

Direct station-cassette-to-rover-battery connection and direct battery-to-battery charging are prohibited. A charger with the required isolation, current limiting, voltage profile, and fault behavior must remain between the station source and rover battery.

## Frozen decisions and unresolved items

Frozen for the design-only phase:

- initial physical validation starts with one `GRID-AC` bay;
- cassette bench work uses a conditional `ARCH-A — Individual Module Isolation` baseline;
- seven-module topology is electrically unresolved until module and BMS data are reviewed;
- A/B direct parallel is prohibited;
- no simultaneous ACTIVE slots;
- no hot unplug or ACTIVE-slot removal;
- physical ESTOP independently removes the charging-permission path;
- every fault and power restoration requires deliberate manual reset.

Still unresolved:

- exact battery and BMS charge limits;
- charger output, continuous current, peak current, and thermal derating;
- converter and isolation architecture for a five-bay PACK station;
- connector voltage, current, pin count, environmental rating, material, and product selection;
- protective-device ratings, conductor sizes, enclosure category, grounding, bonding, and mains installation details.

## Document map

- `ELECTRICAL_ARCHITECTURE_DECISION.md` compares ARCH-A/B/C and GRID/PACK charger paths.
- `SINGLE_BAY_VALIDATION_PLAN.md` defines the mandatory PHASE-0 through PHASE-9 sequence.
- `A_B_CASSETTE_INTERLOCK_SPEC.md` defines fail-closed slot states and transitions.
- `CONNECTOR_REQUIREMENTS.md` defines selection requirements without choosing a product.
- `PRELIMINARY_BOM_AND_COST.md` defines planning categories and non-purchase cost bands.

## Approval boundary

These documents do not authorize hardware output, GPIO, serial access, charger control, BMS communication, contactor operation, battery connection, mains wiring, CAD, purchase, experiment execution, rover modification, field deployment, night operation, automatic restart, or unattended operation. A licensed electrical review and separate human approval are required before each applicable energized phase.
