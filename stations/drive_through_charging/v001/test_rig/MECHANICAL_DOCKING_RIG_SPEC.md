# Mechanical Docking Rig Specification

## Status and fixed flags

Status: **DESIGN ONLY**

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

This specification creates no CAD, fabrication instruction, purchase authority, or experiment approval.

## Measurement-first register

```text
actual_measurement_required=true
```

Final dimensions must not be inferred from photographs, earlier CAD, or nominal values. Before ST-013C, record the measurement method, instrument resolution, repeated observations, maximum/minimum, uncertainty, and reviewer disposition for every variable.

| Variable | Required physical measurement | Use in ST-013B | Freeze condition |
|---|---|---|---|
| `W_ROVER_MAX` | Maximum rover width including protected protrusions | Rig clear width and obstruction envelope | Repeated measurement and protrusion audit accepted |
| `W_WHEEL_OUTER` | Outside-to-outside wheel width | Guide references and sled adjustment | Loaded and unloaded observations accepted |
| `W_WHEEL` | Wheel tread width | Guide contact face and sled wheel selection | All relevant wheels measured |
| `D_WHEEL` | Wheel diameter | Provisional guide height calculation | Loaded radius and tolerance accepted |
| `L_WHEELBASE` | Axle-center spacing | Sled geometry and guide capture | Both sides checked for agreement |
| `L_ROVER` | Total rover length | Approach and forward-exit clear lengths | Maximum configuration measured |
| `H_CLEARANCE` | Minimum ground clearance | No-contact envelope for guides and stop | Full underside sweep accepted |
| `H_CONNECTOR_TARGET` | Charging target height from floor datum | Adjustable target plate and MODULE-D datum | Loaded ride height measured and reviewed |
| `X_CONNECTOR_TARGET` | Lateral charging target from rover center datum | Adjustable target plate | Center datum and repeatability accepted |
| `M_ROVER_TEST_MAX` | Maximum expected controlled test mass | Future structural review only; not a guessed load rating | Weighing method and configuration accepted |

Also measure front approach geometry, every part protruding beyond the wheel envelope, and safe emergency manual push points. No actual field coordinate or road location belongs in this register.

## MODULE-A — Docking base and approach lane

### Purpose

Provide one stable, dry, flat, non-slip, forward-entry/forward-exit lane for a hand-pushed dummy sled.

### Interfaces

Floor datum, removable MODULE-B guide fasteners, MODULE-C structural load path, centerline, speed marks, and future anchor zones.

### Adjustment range

- approach clear length: at least `2 × L_ROVER`;
- forward-exit clear length: at least `1.5 × L_ROVER`;
- total clear width: at least `W_ROVER_MAX + 300 mm`;
- one lane only; bypass lane is deferred beyond ST-013B.

### Replaceable parts

Anti-slip deck panels, adjustable feet, centerline markers, speed-marking tape, and anchor brackets.

### Failure modes

Base movement, uneven support, slippery surface, raised edge, debris obstruction, insufficient exit clearance, or guide/stop load bypass into MODULE-D.

### Inspection points

Level and step-free surface, foot locking, anchor zones, deck friction, centerline visibility, lane clearance, drainage isolation, and fastener condition.

### Transport and storage

Use bolted liftable sections; restrain loose feet and brackets; keep dry; do not store ballast on an unsupported panel.

### ST-013C CAD boundary

Freeze only the measured envelope, base datum, split lines, bolt interfaces, feet, anchor zones, and reserved clearances. No foundation or field installation is authorized.

## DOCKING_DUMMY_SLED

The initial approach object is a four-wheel, non-self-propelled, manual-push-only sled.

Required features:

- adjustable wheel width and outside wheel envelope representing `W_WHEEL` and `W_WHEEL_OUTER`;
- adjustable wheelbase where needed to cover the measured `L_WHEELBASE` interface;
- adjustable target plate for `H_CONNECTOR_TARGET` and `X_CONNECTOR_TARGET`;
- securely retained ballast configurations of 15 kg, 30 kg, and 45 kg total test mass;
- low fixed center of gravity, enclosed or guarded ballast, bolted primary retention, and a second independent retention feature;
- external mass label and pre-use retention inspection;
- manual stopping handle and safe push points usable from front or rear without entering pinch zones;
- replaceable unpowered connector target block;
- dedicated stop face that sends no stop load into the connector target;
- forward exit by hand only; reverse departure after simulated connection is prohibited.

The first entire validation sequence uses manual push. Motorized approach, rover propulsion, steering, PTO, and automatic motion are outside ST-013B.

## MODULE-B — Adjustable wheel-guide system

### Purpose

Align wheel sidewalls gradually while avoiding the electrical box, PTO, lower hull, and all non-wheel protrusions.

### Interfaces

MODULE-A adjustment slots and datum scale, the measured wheel envelope, sled wheels, and MODULE-C approach corridor.

### Adjustment range

- clear width: `W_ROVER_MAX + 10 mm` through `W_ROVER_MAX + 50 mm`;
- left and right sides independently adjustable;
- scale increment no greater than 5 mm with a symmetric reference line;
- provisional taper length at least 300 mm;
- provisional guide height `0.25 × D_WHEEL / 2` through `0.40 × D_WHEEL / 2`, replaced by actual wheel measurement and ride-up review.

### Replaceable parts

Tapered entry pieces, sacrificial wear strips, scale labels, bolts, and lock nuts.

### Failure modes

Wheel ride-up, sharp-edge damage, abrupt lateral load, contact outside the wheel sidewall, asymmetric adjustment, loosened guide, debris jam, or different left/right height.

### Inspection points

Smooth taper, rounded edges, equal height, symmetric scale position, tool-adjusted dual locking, wear-strip retention, debris access, and clearance to electrical box/PTO/lower hull.

### Transport and storage

Unbolt from MODULE-A, protect edges and scales, pair left/right parts by revision label, and prevent stacked guides from distorting wear strips.

### ST-013C CAD boundary

Guide cross-section, taper, adjustment slots, hard limits, datum scale, fastener capture, sacrificial-strip interface, and keep-out envelope.

## MODULE-C — Mechanical stopping system

### Purpose

Bring the sled to zero motion using a structural stop before any connector-mock final engagement.

### Interfaces

Sled dedicated stop face, MODULE-A frame and reinforcement, stop-engaged sensor target, MODULE-D engagement datum, and at least 5 mm provisional residual travel on every active floating axis after stop contact.

### Adjustment range

Stop height, depth, and lateral position remain functions of measured front approach geometry and keep-out zones. Adjustment must be mechanically locked and must never use the connector carrier as a reaction surface.

### Replaceable parts

Stop faces, elastomer pads, sensor brackets/targets, reinforcement plates, and visible witness markers.

### Failure modes

Late stop engagement, one-sided overload, pad loss, sensor false positive, structural yielding, loose adjustment, bottomed connector carrier, or load transfer into the connector mount.

### Inspection points

Pad presence, stop-face position, reinforcement, fasteners, frame witness marks, left/right contact evidence, sensor target, and residual travel indication.

### Transport and storage

Remove elastomer and sensors where vulnerable, secure the beam against impact, and preserve datum labels and matched reinforcement parts.

### ST-013C CAD boundary

Structural load path, stop-face datum, replaceable-pad pocket, reinforcement and fastener interface, sensor zone, and MODULE-D clearance envelope.

## Stop architecture comparison and recommendation

| Criterion | Left/right two-point stop | Wide central stop |
|---|---|---|
| Load distribution | Symmetric when both measured faces engage; exposes skew | Concentrated near center; less sensitive to small yaw |
| Rover/sled compatibility | Requires two verified stop faces clear of wheels and protrusions | Requires a verified strong central face and underside clearance |
| Misalignment evidence | Left/right witness marks reveal yaw and single-side contact | Can hide modest yaw unless separately sensed |
| Adjustment | Two linked settings must remain coplanar | One principal setting is simpler |
| Failure consequence | One missing pad can create asymmetric load and must fail inspection | A narrow or misplaced face can create local overload |
| Service | Two replaceable pads and brackets | One wider replaceable pad and bracket |

**Recommendation: left/right two-point stop, conditional on measured matching stop faces and a cross-check that both pads engage before connector seating.** It gives clearer skew evidence and keeps the center available for a high connector target. If the actual front geometry cannot provide two structurally reviewed faces, the design remains unresolved; it does not silently switch to an unreviewed central stop.

## Mandatory engagement sequence

1. wheel guides begin alignment;
2. sled direction stabilizes;
3. mechanical stop faces engage;
4. sled motion becomes zero;
5. stop-engaged sensing confirms a plausible stop condition;
6. floating connector carrier begins final engagement with at least 5 mm provisional residual travel available;
7. connector-seated sensing confirms.

The connector is never the mechanical stop and carries no vehicle or sled stop load.

## Approach conditions

Provisional manual-push speed is at most `0.05 m/s` (`50 mm/s`). The fixed condition set is:

`CENTERED`, `LATERAL_LEFT_5MM`, `LATERAL_RIGHT_5MM`, `LATERAL_LEFT_10MM`, `LATERAL_RIGHT_10MM`, `LATERAL_LEFT_15MM`, `LATERAL_RIGHT_15MM`, `YAW_LEFT_1_DEG`, `YAW_RIGHT_1_DEG`, `YAW_LEFT_2_DEG`, `YAW_RIGHT_2_DEG`, `YAW_LEFT_3_DEG`, `YAW_RIGHT_3_DEG`, `COMBINED_LEFT_15MM_YAW_3_DEG`, and `COMBINED_RIGHT_15MM_YAW_3_DEG`.

Each condition requires at least five future repetitions. Dry nominal connector-mock cycles total 100. Lateral 15 mm and yaw 3 degrees are provisional rig acceptance targets, not rover or product guarantees.

## Floor and operating boundary

The future dry test surface must be indoor, level, non-slip, drained only after an approved later contamination protocol, step-free, and configured so wheels cannot climb onto a guide. This document performs no approach trial and approves no experiment.
