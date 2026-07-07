# Paddy Swarm Units

This directory contains interchangeable work units for the Paddy Swarm Common Rover.

The rover body itself is managed under:

```text
rovers/common_rover/
```

Work units are managed here:

```text
units/
```

## Purpose

Paddy Swarm units are optional attachments mounted to the common rover body.

The goal is not to redesign the rover core for every task.  
The goal is to keep the rover body common and swap task-specific units by season or experiment.

Examples:

- weeding unit
- direct seeding unit
- high-cut / corner cutting assist unit
- carrier / tray transport unit
- test gauges
- PTO adapters
- mounting fixtures

## Current compatible rover

The current unit interface is based on:

```text
Paddy Swarm Common Rover v2.28.2 Dual PTO Restart
```

See:

```text
units/UNIT_INTERFACE_v228.md
```

for the mechanical and safety rules that all v228-compatible units must follow.

## Directory structure

```text
units/
├─ README.md
├─ UNIT_INTERFACE_v228.md
│
├─ _common/
│  ├─ mounts/
│  ├─ pto_adapters/
│  ├─ pins_fasteners/
│  └─ test_gauges/
│
├─ weed/
│  └─ passive_rake/
│     └─ v001/
│
├─ direct_seeding/
│  └─ broadcast_dropper/
│     └─ v001/
│
├─ high_cut/
│  └─ corner_assist/
│     └─ v001/
│
└─ carrier/
   └─ tray_carrier/
      └─ v001/
```

## Unit categories

### Weeding units

```text
units/weed/
```

Initial target:

```text
units/weed/passive_rake/v001/
```

The first weeding unit is a passive rake / comb unit.

It does not use PTO as a continuous rotary weeding power source.  
Instead, the rover moves forward and the rake lightly disturbs the mud surface.

PTO may be used only to drop, unlock, or deploy the unit.

### Direct seeding units

```text
units/direct_seeding/
```

Future target:

```text
units/direct_seeding/broadcast_dropper/v001/
```

Initial direct seeding units should be simple seed dropping or seed broadcasting mechanisms.

Do not start with a complex planting arm.

### High-cut / corner assist units

```text
units/high_cut/
```

Future target:

```text
units/high_cut/corner_assist/v001/
```

These units are not intended to replace a combine.

They are for:

- corners
- edges
- small inaccessible areas
- high-cut assist experiments

Threshing, grain collection, and straw handling are out of scope for early units.

### Carrier units

```text
units/carrier/
```

Future target:

```text
units/carrier/tray_carrier/v001/
```

Carrier units may be used for:

- small tools
- small seedling trays
- test weights
- batteries
- replacement parts
- field-side transport

## Naming convention

Use this style:

```text
PS-<CATEGORY>-V<VERSION>-<PART-NAME>
```

Examples:

```text
PS-WEED-V001-PASSIVE-RAKE
PS-WEED-V001-FRONT-MOUNT
PS-WEED-V001-RAKE-TINE-S
PS-SEED-V001-BROADCAST-DROPPER
PS-HCUT-V001-CORNER-ASSIST
PS-CARR-V001-TRAY-CARRIER
```

## Version rule

Each unit should have its own version.

Example:

```text
units/weed/passive_rake/v001/
units/weed/passive_rake/v002/
```

Do not overwrite old tested unit versions unless the previous version is clearly marked as failed and removed from the public print path.

Hardware mistakes cost material, money, and time.  
Avoid leaving confusing failed CAD files in the public working tree.

## Safety policy

All units must follow these rules:

- Do not modify the rover fixed core without explicit design approval.
- Do not require BBOX/CBOX to be rearranged.
- Do not place PTO, motor boxes, or wiring notches below the expected waterline.
- Do not rely on printed parts alone for waterproofing.
- Do not assume field readiness.
- First water tests must use dummy weights only.
- First motion tests must be low-speed and supervised.
- Units must fail before damaging the rover body.
- Avoid sharp tools in early prototypes.
- Avoid mechanisms that can pull the floating rover underwater.
- Avoid designs that require the rover body to sink in order to work.

## Print policy

All unit CAD should aim for:

- Bambu Lab A1 compatibility
- no floating parts
- no slicer support requirement where possible
- no hidden internal support traps
- simple replacement parts
- field-repairable geometry
- clear manifest and README files

Dense output should generally use:

```text
blank_a1_plates_4.3mf
safe 240
support-orient-fit-safe 244
gap 4
```

## Field policy

The rice field is not an expendable test site.

Development order:

1. CAD review
2. slicer review
3. small part print
4. dry assembly
5. bench test
6. water tank test with dummy weight
7. shallow mud test
8. supervised outdoor test
9. field-edge test only after repeated success

Do not install electronics in the first water test.

## Current first unit

```text
units/weed/passive_rake/v001/
```

Current concept:

```text
PS-WEED-V001-PASSIVE-RAKE
```

Purpose:

- passive rake / comb weeding experiment
- manual drop test
- PTO drop / latch release test
- shallow mud resistance test
- front attachment trim test

This is not a production weeding unit.