# Common Rover v2.29.3.5 Known Holds

## LOOP-001

Active part:

`V2292-FPB-RAIL-L`

Part process:

`METAL_PART_CAD_VALIDATION`

This part is not a production print target.

## Fastener authority

Rail-referencing fastener instances:

- total: 24
- required rail through holes: 4
- measurement holds: 8
- design contradictions: 12

Known group status:

- FG-002 lower adapter: design contradiction or measurement hold
- FG-004 front crossmember: joint type undefined
- FG-006 motor bracket: rail hole pattern valid candidate
- FG-008 input cartridge: hole-pattern design contradiction
- FG-009 output bridge: hole-pattern design contradiction
- FG-020 servo bridge: hole-pattern design contradiction

## Hole-layout concerns

Static candidates:

- fully interior hole candidates: 4
- edge-breakout candidates: 5
- rail-exterior or contradiction candidates: 15

The five edge-boundary candidates must not be treated as normal circular holes without explicit slot, notch, host, or coordinate authority.

## Structural-joint hold

The FPB rail/front-crossmember joint remains:

`UNDEFINED_MEASUREMENT_HOLD`

A butt joint, lap joint, tab-and-slot joint, bracket joint, or other construction has not been approved.

## Execution holds

CadQuery/OCP was unavailable during artifact generation.

The following remain unexecuted:

- Solid generation
- required-hole subtraction
- STEP export and reimport
- visualization STL verification
- actual PNG rendering
- automated image QA
- minimum-assembly inspection
- service sweeps
- external image review

## Safety and release holds

- waterproof: not validated
- electrical safety: not validated
- thermal safety: not validated
- structural strength: not validated
- manufacturing: not approved
- purchase: not approved
- field deployment: not approved
