# PS-MHT-V001 Phase 3I-G Lower Return Buffer

This package is the prototype authority for the terminal collection tray, vented
downcomer, removable bottom diffuser, side buffer tank, wide normal overflow,
open-gutter air break, independent emergency overflow, and blank cleanout pads.

The functional sequence is bottom inlet → upward displacement → 112 mm top weir
at Z82 → open gutter → one independent 25 mm hose per tower. The emergency crest
is Z94 and the tank top is Z105. The Ø100 central core remains dry.

Print status:

- `exports/diagnostics/plate_01` through `plate_07`: print only after Bambu Studio review.
- Every file beginning `hold_`: **HOLD / DO_NOT_PRINT** until its prerequisite coupons pass.
- Full five-stage tower, four-tower reference, metal frame reference, and Phase 3I-F full stage: **DO_NOT_PRINT**.
- D08 transparent-container adapter is not instantiated because container dimensions are pending.

Run `src/export_models.py` with the `paddy-cad` environment. The generated reports
record STEP round trips, STL manifold checks, A1 envelopes, volumes, topology,
interference, and inherited SHA non-regression.

The normal outlet and cleanout interfaces are deliberately un-drilled. Do not
drill them until a physical fitting is measured and a D05 coupon passes.

