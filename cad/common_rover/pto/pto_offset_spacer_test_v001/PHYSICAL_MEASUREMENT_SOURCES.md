# Physical measurement sources

Latest user task:

|Feature|Value|Classification|
|---|---:|---|
|KP000 relevant outside span|66.1 mm|PHYSICAL_DIRECT|
|60T maximum measured outside dimension|100.1 mm|PHYSICAL_DIRECT|
|20T relevant ring outside no larger than KP000|Qualitative only|PHYSICAL_FIT_OBSERVATION|
|Front L-bracket cannot be inserted structurally|Rejected for current assembly|USER_PHYSICAL_ASSEMBLY_DECISION|

Derived per-side overhang = (100.1-66.1)/2 = 17.0 mm, PHYSICAL_DERIVED.
It is not a directly measured gap. Candidate residuals are GEOMETRIC DESIGN
REFERENCES only. No new exact 20T OD is inferred from the qualitative statement.

Repository comparison, measured from loaded CAD:

- KP000 source `cad/common_rover/frame/front_interface_dual_pto_20t_v001/build_front_interface_dual_pto_20t_v001.py` gives
  67 x17 x35 mm; X delta CAD-physical = +0.9 mm. Simplified housing omits
  unmeasured current collar/hardware details. Reference bore10, axis height18.5.
- `cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26/artifacts/temp_htd5m_60t_dual_shaft_collar_embedded_m4_provisional_v0_9_6_26.step` gives 102 x102 x26 mm;
  radial maximum delta CAD-physical = +1.9 mm. This is a PROVISIONAL candidate;
  repository evidence does not identify it as the user's actual installed part.
  Earlier v0951 source is 102 x102 x20 mm, same radial discrepancy.
- `cad/common_rover/pto/pto_20t_od10_physical_envelope_v001/artifacts/pto_20t_od10_physical_envelope.step` is an earlier independent physical-envelope
  source, flange34.8, total axial23, measured bore9.8 versus nominal shaft10.
  It is retained unchanged as REFERENCE, not inferred from the latest observation.
- Existing PTO shim lane uses thickness0.5/1.0, ID10.2/OD13.8, only between
  rotating inner-ring and pulley faces. It does not identify this offset interface.
- Physical dimensional authority 2026-09-01 retains drive centers122/123 and
  nominal/PTO target122.5 mm from floor. No installed X/Y transform follows.
- MISUMI shaft/key record retains effective key16.7, original19.7 minus3.0 mm.
  Current exact purchased shaft length remains unresolved. No shaft cut is released.

The new 100.1 mm cylinder is a radial comparison envelope; 26 mm display width
is a CAD-only reference. Runout, current axial hardware and frame-relative axis
registration must be measured to create a conservative installed 3D sweep.
