# Current Common Rover Design Authority

## Current authority

**Paddy Swarm Common Rover v2.29.3.5**

This revision is the current shared authority for:

- coordinate systems
- fixed body dimensions
- component IDs
- assembly transforms
- interface definitions
- fastener registries
- opening registries
- design holds
- closed-loop CAD validation source

Use v2.29.3.5 instead of v2.28 or earlier values whenever a v2.29 authority value exists.

## Fixed core geometry

Repository axes:

- X: lateral direction, +X is left
- Y: longitudinal direction, -Y is front
- Z: upward

CBOX:

- X = 130 mm
- Y = 140 mm
- Z = 105 mm

BBOX:

- X = 150 mm
- Y = 220 mm
- Z = 150 mm

Battery cassette:

- X = 125 mm
- Y = 180 mm
- Z = 120 mm

Core arrangement:

- CBOX and BBOX are arranged front-to-rear
- CBOX is forward
- BBOX is rearward
- total core length is 360 mm
- open-center FPB architecture is retained
- front dual-PTO architecture is retained

## Current validation status

Validated:

- static source validation
- registry preservation
- fastener requirement accounting: 24/24
- required rail holes: 4
- measurement holds: 8
- retained design contradictions: 12
- 24-stage full-runner source wiring
- test and mutation framework
- deterministic replay
- package sealing

Not validated:

- CadQuery/OCP execution
- actual Solid geometry
- actual STEP or STL output
- actual rendered images
- FPB rail/front-crossmember joint
- minimum-assembly collision
- structural strength
- waterproofing
- electrical safety
- thermal safety
- manufacturing
- purchasing
- field deployment

## Release classification

- Design authority sharing: approved
- Executable CAD release: not approved
- Manufacturing release: not approved
- Purchase approval: not approved
- Field deployment: not approved
