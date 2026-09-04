# Common Rover CBOX DRIVE Electrical Physical Integration v0.9.6.2

Status: **NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING**  
Classification: `DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION`

This lane preserves the v0.9.6.0 above-water CBOX role and its power/signal separation. It does not approve powered rotation, live-battery submersion, or field deployment.

## Dual MD10C layout

Internal X/Y coordinates use the 210 × 72 mm tray. MD10C-L occupies X20..95, Y24..67; MD10C-R occupies X115..190, Y24..67 and rotates 180°. Thus each short-end service zone is 20 mm and the logic-side center gap is 20 mm. Four drawing-reference points per board use the 69 × 35 mm pattern. Underside clearance is a 3 mm candidate.

Six D8 mm reference cylinders preserve vertical screwdriver paths over terminal screws. The outer 20 mm spaces remain reserved for ferrules, conductor bends, inspection, and tools. If the real harness needs more, classification becomes `SERVICE_SPACE_CONFLICT`; geometry must not be silently reduced. Final M3-class retention and physical maximum component height remain HOLD.
