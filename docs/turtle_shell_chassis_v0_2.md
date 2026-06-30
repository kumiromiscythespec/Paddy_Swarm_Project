# Paddy Swarm Standard Turtle Shell + Chassis v0.2

## Purpose

This revision changes the turtle shell from a future solar luxury part into a standard protective body cover.

The shell is intended to protect expensive electronics and motors from direct rain, mud splash, shallow waterline contact during tilt, and light rollover scuffing.

## Design decision

The shell is a first defense layer, not the final waterproof container.

```text
Standard Turtle Shell = first defense
Inner Dry Cassette = second defense
Battery Cassette = protected power module
Chassis = low-center structure and float/motor interface
```

## Why the chassis needed an update

A standard shell requires new hardpoints:

- shell mount rails
- orientation key so the shell cannot be installed backwards
- inner dry cassette bay
- low-center battery tray interface
- charge module / charge scute reserved area
- future solar-ready surface planning

## Charge Scute

The Charge Scute is a non-metallic window zone for future top wireless charging.

Rules:

- do not put metal screws near the coil window
- do not charge directly into a lithium battery
- use a receiver module, voltage regulation, CC/CV charger, BMS, fuse, and temperature monitoring
- keep cassette charging and wired charging compatible through the common Power Bay concept

## Solar-ready shell

The v0.2 shell does not include solar panels. It only reserves upper surface area for:

- future removable solar panel mount
- perovskite coating experiments
- adhesive panel tests

The rover must remain fully useful without solar.

## Tilt and waterline test

Recommended first tests:

1. Mount shell to chassis with no electronics.
2. Put paper towels inside the dry cassette dummy.
3. Add ballast equivalent to expected electronics/battery weight.
4. Float in water tray/tank.
5. Tilt to 5°, 10°, and 15°.
6. Confirm water runs off the shell and does not pool.
7. Confirm no water drips into the dry cassette zone.
8. Log whether shell lips touch water and whether the rover self-righting tendency worsens.

## Remaining risks

- Shell raises center of gravity if printed too thick.
- Shell can catch wind.
- Shell can hold heat if ventilation is poor.
- Shell can trap condensation if sealed incorrectly.
- FDM print layer lines are not waterproof by default.
- Motor shaft exits still need separate mud and water guards.
