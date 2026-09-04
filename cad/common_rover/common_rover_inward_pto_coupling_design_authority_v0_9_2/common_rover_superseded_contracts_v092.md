# v0.9.2 Superseded Contracts

The protected v0.9.1 geometric facts remain valid:

- inboard support faces: Y=+30.5/-30.5 mm
- shaft ends: Y=+30/-30 mm
- geometric end gap: 60 mm

The v0.9.1 inference that the 60 mm gap is a usable coupling bay is
superseded. It exposed only 0.5 mm of inward shaft stub per side and therefore
cannot provide the required engagement.

v0.9.2 separates:

1. support-face span;
2. exposed rover shaft stub;
3. center shaft-end gap;
4. coupling body envelope;
5. retracted/engaging/engaged/full-sweep envelopes;
6. central fixed structure, wiring, cap, guard, and installation path;
7. physical presence, unit identity, mechanical lock, and independent
   left/right engagement feedback.

The conditional replacement is a 12.5 mm stub per side with ends at ±18 mm,
36 mm end gap, C1 SMALL envelopes, and no stack shift. It becomes current only
after repository pointer, artifact, contract, and standalone-ZIP gates pass.

`PHYSICAL_FIT_HOLD` · `NOT_FOR_MANUFACTURING`
