# Paddy Swarm Turtle Shell Chassis CAD Pack v0.2

This pack updates the Paddy Swarm amphibious rover test body with a **standard turtle shell cover** and a revised center chassis interface.

## Concept

The turtle shell is now treated as a standard first-defense layer:

- rain guard
- mud splash guard
- shallow waterline / tilt guard
- rollover scuff guard
- future solar/perovskite mounting surface
- mascot/trademark shape

It is **not** treated as the only waterproof enclosure in v0.2. The correct early structure is:

```text
outer standard turtle shell
↓
inner dry cassette / battery cassette
↓
low center battery tray and chassis
```

## Important safety rule

Do not remove the inner waterproof/dry cassette yet. FDM printed shells can leak through layer lines, seams, cracks, screw holes, and cable openings. Use this CAD pack for fit, float, tilt, splash, and handling tests before adding electronics.

## Main files

- `stl/hull_v0_2/PSR-HU-020-R00_center_chassis_segment_v0_2.stl`
- `stl/hull_v0_2/PSR-SHL-001F-R00_standard_turtle_shell_front.stl`
- `stl/hull_v0_2/PSR-SHL-001R-R00_standard_turtle_shell_rear.stl`
- `stl/hull_v0_2/PSR-PWR-010-R00_inner_dry_cassette_dummy.stl`
- `stl/hull_v0_2/PSR-PWR-011-R00_low_center_battery_tray.stl`
- `stl/hull_v0_2/PSR-SHL-003-R00_charge_scute_window_insert.stl`
- `stl/hull_v0_2/PSR-ASM-001-R00_full_rover_turtle_shell_reference_assembly.stl`

## Print priority

1. `PSR-SHL-000-R00_shell_mount_base_gauge.stl` in PLA
2. `PSR-HU-020-R00_center_chassis_segment_v0_2.stl` in PLA
3. `PSR-PWR-010-R00_inner_dry_cassette_dummy.stl` in PLA
4. `PSR-SHL-001F/R` shell halves in PLA for fit check
5. Repeat shell halves in PETG for water-adjacent tests
6. Print `PSR-SHL-003` Charge Scute insert only after confirming top-charge placement

## Bambu Lab A1 note

The shell is split into front/rear halves so printable parts stay near or below the A1 print area. The full assembly STL is a visual reference and is not meant to be printed as one piece.

## Field-use warning

This is Grade 0 / early Grade 1 CAD. Do not mount a live battery or controller until dry tests, splash tests, tilt tests, and paper-towel leak checks are complete.
