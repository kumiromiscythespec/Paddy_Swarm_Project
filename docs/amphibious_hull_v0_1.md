# docs/amphibious_hull_v0_1.md

# Paddy Swarm Amphibious Hull v0.1

## Purpose

This is the first Grade 0 CAD pack for the Paddy Swarm amphibious hull concept.

Design principle:

```text
Instead of attaching floats to a vehicle,
design a floating small hull and attach drive/working modules to it.
```

日本語で言えば、これは「車体にフロートを足す」のではなく、**浮く船体に足回りと作業アームを付ける**設計です。

## Target

- 30cm rice-row spacing awareness
- Narrow hull, around 220–240mm max concept width
- Left/right side floats as primary buoyancy
- Low center of gravity
- Open-top float trays for foam insertion and inspection
- No electronics during Grade 0 water tests

## Parts

| Part No. | Name |
|---|---|
| PSR-HU-001-R00 | Central hull short frame |
| PSR-HU-002-R00 | Left float front tray |
| PSR-HU-003-R00 | Left float mid tray |
| PSR-HU-004-R00 | Left float rear tray |
| PSR-HU-005-R00 | Right float front tray |
| PSR-HU-006-R00 | Right float mid tray |
| PSR-HU-007-R00 | Right float rear tray |
| PSR-HU-008-R00 | Bow mud deflector concept |
| PSR-HU-010-R00 | Waterproof box dummy |
| PSR-HU-012-R00 | Belly module rail sample |
| PSR-HU-013-R00 | Ballast test tray |
| PSR-HU-015-R00 | Generic float segment lid |
| PSR-HU-016-R00 | Float seam joiner clip |

## Float structure

Each float segment is an open tray with:

- bottom plate
- side walls
- internal baffles
- foam insertion space
- waterline raised bands
- lid part
- seam clips for multi-segment tests

This is not a sealed boat hull. It is a Grade 0 test structure.

## Buoyancy test concept

Use no electronics. Put foam inside trays, mount lids, temporarily seal seams with tape or silicone, then test in a water tank.

Minimum checks:

```text
normal posture
front-up 10 degrees
front-down 10 degrees
left tilt 10 degrees
right tilt 10 degrees
light rocking
paper towel at waterproof-box position
```

Pass condition:

```text
paper towel stays dry
waterline stays below danger area
no sudden sinking if one segment leaks
```

## Print notes

- PLA: fit test and visual test
- PETG: water-tank test parts
- TPU: not used in this pack
- Use brim for tall float trays
- Print float trays upright/open-side up
- Do not assume FDM parts are watertight

## Next iteration ideas

- Add readable embossed labels
- Improve seam connector geometry
- Add true dovetail keys
- Create scaled full assembly jig
- Add optional wide-test float
- Add side-charge cutout version
- Add watertight lid gasket channel
