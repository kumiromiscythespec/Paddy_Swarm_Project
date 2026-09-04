# Exact source geometry and depth regression

Read-only parent: `cad/common_rover/bbox/bbox_compact_field_goldenmate_v003/`.

Sources: selected body STEP, selected lid STEP, Coupon A/B STEP/STL, and the parent builder's rounded-section functions. No parent generator or file is modified.

| Feature | Source | Dummy |
|---|---|---|
| Groove outer rounded rectangle | 160 × 74, R6.0 | 60 × 58, R6.0 |
| Groove inner rounded rectangle | 155.8 × 69.8, R3.9 | 55.8 × 53.8, R3.9 |
| Groove centerline radius | R4.95 | R4.95 |
| Rim opening / flange / lid corner radii | R4 / R8 / R8 | unchanged |
| Flange | 170 × 86 × 4 | 70 × 70 × 4 |
| Wall / floor / lid | 3.5 / 3.5 / 8 | unchanged |
| Four corner M4 centers | (±84, ±42) | (±34, ±34) |
| M4 tower / clearance | Ø12 / Ø4.5 | unchanged |
| Rim → hard stop | 0.895 | unchanged |
| Groove depth | existing full body 0.50 | G055 0.55; G065 0.65, explicitly authorized |

Straight runs alone are shortened by 100 mm in X and 16 mm in Y. Every corner quadrant is translated by 50 mm in X and 8 mm in Y, not scaled. The four corner geometry comparisons use the actual imported full-body STEP and show zero symmetric-difference volume outside the authorized groove-depth region. Lid corners are also compared against imported source STEP. Source mid-side towers are omitted under the explicitly permitted four-corner fastener architecture.

Nominal clearances: external M4 hole edge to uncompressed cord 6.7661 mm; tower to groove 2.8661 mm. These are calculated geometric distances, not allowances for deformed rubber or driver hardware variability.

## Why the previous depth test was insufficient

The old coupon cutter used height `depth + 0.2` at center `rim - depth/2`. Its bottom was therefore `rim - depth - 0.1`, causing a systematic +0.10 mm actual cut. The new cutter starts at `rim - requested_depth`; any overshoot is placed only ABOVE the rim.

The mandatory regression independently imports the saved STEP. It probes actual rim and groove bottom material surfaces, cross-checks the unique annular floor face, and requires `abs(actual - requested) <= 0.000001 mm`. A negative test exports/reloads a recreation of the old centered-tool error and verifies rejection. Parameters alone cannot pass this test.

STEP reproducibility normalizes only file metadata, generic OCCT PRODUCT counters and assembly occurrence labels. Geometric entities, topology, entity references and assembly transforms are unchanged. The fixed header timestamp is an explicit deterministic placeholder, not a claimed build date.
