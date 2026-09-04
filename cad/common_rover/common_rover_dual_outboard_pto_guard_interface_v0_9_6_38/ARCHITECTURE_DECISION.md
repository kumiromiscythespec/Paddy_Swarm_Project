# Common Rover dual outboard PTO guard interface v0.9.6.38

## Decision

`DUAL_INDEPENDENT_OUTBOARD_PTO` is selected for the new physical-layout constraint. Left exits outward -X; right exits outward +X. The shafts and torque paths remain independent and a common PTO shaft is prohibited.

The v0.9.3.0 two-inward-X-shaft candidate remains immutable history and is marked `SUPERSEDED_BY_NEW_PHYSICAL_LAYOUT_CONSTRAINT`; it is not erased or rewritten.

## Preserved safety

DRIVE must be disengaged and the rover mechanically locked/braked before PTO engagement. Work-unit weight and reaction loads go to dedicated hitch/guide structure, never PTO shafts or box walls.
