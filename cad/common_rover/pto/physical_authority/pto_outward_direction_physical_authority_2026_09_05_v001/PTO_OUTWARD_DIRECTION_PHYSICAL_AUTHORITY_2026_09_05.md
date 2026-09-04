# Common Rover PTO outward-direction physical authority — 2026-09-05

Authority ID: `PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY_2026_09_05_V001`

## Status

- `PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY`
- `INWARD_DIRECTION_PHYSICAL_SPACE_REJECTED`
- `DUAL_INDEPENDENT_PTO_RETAINED`
- `TWO_SUPPORT_SHAFT_ARCHITECTURE_RETAINED`
- `POWERED_TEST_PENDING`
- `TORQUE_VALIDATION_PENDING`
- `MANUFACTURING_NOT_APPROVED`
- `FIELD_DEPLOYMENT_NOT_APPROVED`

## Binding direction decision

```text
PTO_OUTPUT_DIRECTION = OUTWARD_PHYSICAL_AUTHORITY
PTO_LEFT_DIRECTION = -X
PTO_RIGHT_DIRECTION = +X
INWARD_PTO_DIRECTION = PHYSICAL_SPACE_REJECTED
AUTHORITY_CONFLICT_INWARD_VS_OUTWARD = RESOLVED_OUTWARD
```

The left and right PTO output shafts remain independent. Each output retains
the required two-support shaft architecture and its own bearing/support and
torque path. A common single PTO shaft is prohibited.

## Physical finding

Current as-built inspection shows that the PTO transmission architecture
requires two independently supported output shafts.

When the required bearing/support arrangement and actual transmission path are
applied to the current rover, the center/inward region does not provide
sufficient physical space for a valid inward PTO output configuration.

Therefore PTO-L exits outward toward `-X`, and PTO-R exits outward toward `+X`.
The inward configuration is rejected for the current as-built architecture.

現在の実機では、左右独立のPTO出力軸、必要な2支持構成、実際の動力伝達経路、
支持部、プーリー、軸、中央構造および必要クリアランスを同時に成立させると、
中央／内向き側に有効なPTO出力を構成する物理スペースがありません。このため、
左PTOは`-X`、右PTOは`+X`へ外向きに出力し、現在実機に対するinward配置を
物理スペース不成立として棄却します。

Decision basis:

```text
TWO_SUPPORT_SHAFT_REQUIREMENT
+ ACTUAL_TORQUE_TRANSMISSION_PATH
+ AS_BUILT_PHYSICAL_SPACE_CONSTRAINT
```

## Scope boundary

This physical promotion applies only to:

1. left/right PTO output direction; and
2. rejection of inward PTO output placement for the current as-built rover.

It is not full PTO physical authority, a production release, or a manufacturing
approval. Exact shaft length and projection, bearing product/type and final
mount, shaft and pulley retention, axial spacer, guard production geometry,
alignment tolerance, coupling/tool envelope, torque capacity, powered
operation, durability, mud/water testing, manufacturing and field deployment
remain `HOLD` or `NOT_APPROVED`.

## Relationship to preserved design evidence

The inward direction in
`common_rover_inward_pto_coupling_cad_verified_v0_9_2_1` is
`SUPERSEDED_IN_DIRECTION_SCOPE_BY_PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY_2026_09_05`.
Its coupling studies, CAD evidence and design history remain preserved as
historical/inherited evidence and are not deleted or rewritten.

The outward direction in
`common_rover_dual_outboard_pto_guard_interface_v0_9_6_38` agrees with this
physical decision and remains supporting CAD/interface evidence. No other
v0.9.6.38 scope is promoted by this authority.

## Closure statement

The PTO direction conflict is closed. The current Common Rover physical PTO
output direction is outward: left `-X` and right `+X`. This promotion applies
to direction only. Shaft length, projection, retention, torque and powered
validation remain `HOLD`.

