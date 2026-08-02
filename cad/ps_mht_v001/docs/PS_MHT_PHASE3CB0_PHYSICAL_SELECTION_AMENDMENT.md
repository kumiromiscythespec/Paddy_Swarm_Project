# PS-MHT Phase 3CB-0 Physical Selection Amendment

Phase: **3H-A entry amendment**  
Date: **2026-08-02**

## Historical status retained

- `phase3cb0_audit_status = CONFLICT_FOUND`
- `phase3cb0_cad_generation = PROHIBITED`
- The original seven Phase 3CB-0 documents and YAML remain unchanged.
- The 0.8 L shallow buffer conflict is not resolved by this amendment.

Scoped next-phase CAD is allowed only when its own entry conditions pass.
Phase 3H-A excludes planting holes, pot seats, buffer trays, overflow, drain,
wick, root ring, irrigation, production fasteners and the 170 mm five-band
module.

## c805 physical result

The printed c805 coupon was checked with three Siawadeky pots:

- tool-free insertion,
- no rib catching,
- full-circumference flange seating,
- no visible tilt,
- approximately 1 mm lateral play,
- play measurement method not standardized,
- play not judged excessive.

Therefore:

- `netpot_body_passage_selected = 80.5`
- `netpot_body_passage_selection_status = PASS_BODY_PASSAGE_PHYSICAL`
- c800/c810 are `NOT_REQUIRED_AFTER_C805_PASS`.

The 20-cycle, 27-degree, wet-medium and 500 g tests remain pending. The final
port assembly remains `REDESIGN_REQUIRED`; 80.5 mm is not a complete port
approval.

## Buffer target disposition

- 0.4 L/module: `PRIMARY_TARGET`
- 0.6 L/module: `STRETCH_TARGET`
- 0.8 L/module: `REJECTED_FOR_15_TO_25MM_SHALLOW_BUFFER`

At 194 mm unobstructed diameter, 0.8 L requires 27.06 mm depth before root,
fastener, screen, drain and freeboard deductions. Phase 3H-A generates no
buffer geometry.
