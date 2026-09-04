# 60T / KP000 overhang derivation

KP000_PHYSICAL_SPAN = 66.1 mm (PHYSICAL_DIRECT).
60T_PHYSICAL_MAX = 100.1 mm (PHYSICAL_DIRECT).

60T_OVERHANG_RELATIVE_TO_KP000_PER_SIDE = (100.1 - 66.1)/2 = 17.0 mm.
Classification: PHYSICAL_DERIVED, centered projected-envelope comparison.
It does not prove coincident physical centers or a directly measured clearance.

P20 nominal residual = 20 - 17 = 3 mm.
P22 nominal residual = 22 - 17 = 5 mm.
P25 nominal residual = 25 - 17 = 8 mm.

These are DERIVED_NOMINAL_CLEARANCE, not PASS results. Real minimum clearance
depends on offset direction, axis position, asymmetry, axial overlap, runout,
hardware protrusions, bearing orientation and frame registration.
No runout tolerance has been silently invented or included in those values.
Do not infer a full 3D clearance from one scalar outside-span difference.
