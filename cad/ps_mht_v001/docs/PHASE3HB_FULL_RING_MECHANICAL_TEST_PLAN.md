# Phase 3H-B C050 Full-Ring Mechanical Test Plan

## State and scope

The Phase 3H-A C050 arc coupon passed the reported physical checks. C050 is therefore the first 360-degree mechanical-test candidate, not a production clearance selection. The production selection remains `None`; full-ring, compression-ring, and water results remain `PENDING`.

`HOLE_1` records the least-misaligned physical arc-coupon pairing. It does not add a hole, key, or indexing feature to either full ring. The accepted light free-arc springback does not authorize a radius correction.

## Candidate dimensions

All dimensions come from the unchanged Phase 3H-A implementation. The lower receiver inner radius is 97.0 mm. C030/C050/C070 mean radial clearances of 0.30/0.50/0.70 mm per side, producing upper-skirt outer radii of 96.70/96.50/96.30 mm and diameters of 193.40/193.00/192.60 mm. A larger token is a smaller skirt and a looser fit: C030 is tightest, C070 is loosest.

Consequently, C030 may be considered only after a dimensionally sound C050 pair is demonstrably too loose. C070 may be considered only after a dimensionally sound C050 pair is demonstrably too tight. C070 cannot provide extra retention; any instruction to use it for that purpose conflicts with the authoritative dimensions. Ovality, warping, or print defects require print-process correction, not candidate substitution.

## Plate 01 inspection — lower ring

Print Plate 01 alone. Record bed adhesion, circumferential cracking, receiver debris/stringing/sag/burrs, hard-stop cleanliness, visible ovality, diameters at 0/45/90/135 degrees, maximum-minus-minimum diameter, base rocking, and whitening. Plate 01 alone cannot establish fit.

## Plate 02 inspection — upper ring

Print only after Plate 01 inspection. Confirm skirt-up posture, no skirt-tip sag, no major strings or protrusions on the skirt, clean hard stop, no circumferential cracking, no visible major ovality, diameters at 0/45/90/135 degrees, maximum-minus-minimum diameter, base rocking, and no whitening.

## Full-ring mechanical test

Place the lower ring on a level surface and return the upper ring to its assembly posture. Do not use a hammer, vise, press, clamp-assisted insertion, heat, sanding, lubricant, file, skirt removal, or receiver enlargement.

Record all 15 checks:

1. Tool-free insertion.
2. Full-circumference seating with light two-hand pressure.
3. No local binding.
4. Full-circumference hard-stop contact.
5. No large local gap.
6. No self-separation under gravity.
7. No abnormal lateral play.
8. Twenty attachment/removal cycles.
9. No whitening after 20 cycles.
10. No cracking after 20 cycles.
11. No abnormal wear debris after 20 cycles.
12. No sudden increase in attachment/removal force.
13. Joint-line condition at eight angular positions.
14. Assembled height.
15. Outer-surface step at eight angular positions.

Allowed result states are `PASS_FULL_RING_MECHANICAL`, `FAIL_TOO_TIGHT`, `FAIL_TOO_LOOSE`, `FAIL_OVALITY`, `FAIL_STOP_NOT_SEATED`, `FAIL_DAMAGE`, and `HOLD_MEASUREMENT_REQUIRED`.

## Compression-ring release gate

Plate 03 remains `HOLD_UNTIL_FULL_RING_PAIR_PASS`. Release requires both printed rings to pass inspection, tool-free assembly, full-circumference seating, 20-cycle operation, no whitening, cracking, abnormal wear, major local gap, or abnormal ovality. Release is a later physical decision and is never automatic.

The existing temporary membrane stays reference-only. Water testing is outside this mechanical phase and remains pending.
