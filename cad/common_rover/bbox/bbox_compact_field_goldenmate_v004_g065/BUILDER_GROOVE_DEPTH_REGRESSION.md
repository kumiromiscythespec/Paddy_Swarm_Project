# Actual geometry depth regression

The cutter is bottom-anchored at rim - requested depth; overshoot is above the rim only.
Requests 0.50, 0.55 and 0.65 each generate an actual STEP and ASCII STL and measure their geometry, not parameter labels.
STEP uses two independent solid probes at rim (20,38.5) and groove (20,35.95), plus one planar annular floor face with two boundary wires.
STL uses point-in-triangle surface queries at the same XY locations, not a BRep assumption.
Tolerance 1e-6 mm; expected V004 rim Z113.5, bottom Z112.85, depth0.65.
For every request, an additional STEP with +0.10 actual depth must be REJECTED by the requested-depth validator.
The full V004 actual depth is also checked after STEP reload and STL export.
ASCII STL avoids float32 quantization at Z112.85. Tessellation chordal error is separate from planar depth measurement.
