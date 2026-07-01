# Paddy Swarm Attachment Interface Standard v0.1

## Core decision

The rover body should have four fixed attachment positions:

1. Front Left
2. Front Right
3. Rear Left
4. Rear Right

These positions should remain fixed across body revisions. If a future body changes shape, it should provide adapter plates rather than moving the attachment interface.

## Why this standard is needed

Without a fixed interface, each chassis version and attachment version can become incompatible. A fixed interface allows:

- Old attachments to fit newer bodies.
- New attachments to fit older bodies through adapters.
- Community-made modules to share the same mounting assumptions.
- CAD updates without destroying kit compatibility.
- Field repair by swapping only the module that failed.

## Work allocation

### Front ports

Recommended for:
- High-cut harvest arm
- Camera-guided operations
- Head / panicle guide tools
- Inspection and scout tools

Reason: the front camera can see the tool and the crop before the rover body touches it.

### Rear ports

Recommended for:
- Direct seeding with germinated seed
- Planting / replanting modules
- Light post-wheel soil settling tools

Reason: wheels pass first, then seed or seedlings are placed. This avoids running over freshly placed seed.

### Belly rail

Recommended for:
- Weeding stirrer
- Shallow mud agitation
- Underbody low-force work modules

Reason: forces are near the rover center of mass and easier to manage.

## Nominal v0.1 port coordinates

- Front-left:  X=-70 mm, Y=+230 mm, Z=65 mm
- Front-right: X=+70 mm, Y=+230 mm, Z=65 mm
- Rear-left:   X=-70 mm, Y=-230 mm, Z=65 mm
- Rear-right:  X=+70 mm, Y=-230 mm, Z=65 mm

These are reference dimensions for CAD alignment. They are not yet field-qualified mechanical load specifications.

## PTO policy

The v0.1 standard fixes the physical port positions first. PTO drive routing remains a mock-up in this release.

Planned direction:
- Left/right motor systems may feed left/right PTO paths.
- Rear direct seeding can be driven by a rear transverse shaft.
- Front high-cut harvest can use a front bridge shaft or dedicated actuator.
- If the PTO geometry changes later, adapter gearboxes should be used rather than moving the attachment ports.

## Safety

Do not test direct seeding in a production field before tray tests, mud tests and recovery planning. Real field versions may need metal shafts, bushings, bearings, seals, emergency stops and guarded pinch points.
