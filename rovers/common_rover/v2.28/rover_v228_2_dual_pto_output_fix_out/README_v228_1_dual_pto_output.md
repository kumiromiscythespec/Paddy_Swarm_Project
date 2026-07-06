# Paddy Swarm v2.28.2 Dual PTO Output Clean Core Fix

Version: `v2.28.2-dual-pto-output-fix`

v2.27.4 is a box-notch orientation fix of the G1/v2274 fullset.  It keeps the G1 split hull,
split turtle shell, split sponsons, TPU tire candidates, and internal insert
parts, while improving BBOX/CBOX body cable passages.

## GitHub v2.27 reference used

The v2.27 reference design states that each printed box body has exactly two
top-open cable notches, one on each short/opposite side.  Two boxes total means
four ports.  The connector crosses over the open lid edge; only bundled wires
drop into the notch.  v2.27.4 corrects the physical orientation so each box is 200 mm wide and 150 mm front/back; the notches are on the 200 mm wide front/rear faces.

## v2.27.4 BBOX/CBOX notch rule

Each 200 x 150 x 120 mm box has exactly two top-open rounded-bottom wire-drop notches on the 200 mm wide faces:

- `INNER_SIDE_NOTCH`: the side facing the other box / rover center.
- `OUTER_SIDE_NOTCH`: the side facing the outside/end of the rover.

This is **not** a two-notches-on-one-side design.

Operational mapping:

- BBOX/front box, 200 mm wide face:
  - front / negative-Y side = `OUTER_SIDE_NOTCH`
  - rear / positive-Y side = `INNER_SIDE_NOTCH`
- CBOX/rear box, 200 mm wide face:
  - front / negative-Y side = `INNER_SIDE_NOTCH`
  - rear / positive-Y side = `OUTER_SIDE_NOTCH`

## Notch shape

- top-open U-style wire drop notch
- rounded/U bottom, no sharp bottom corner
- cable-bundle sized; connector does not pass through the notch
- no low horizontal hole near water/mud
- 45-degree triangular drip wedge
- local 45-degree triangular self-support/gusset geometry near notch and top wall

This is **drip-resistant helper geometry only**, not a waterproof guarantee.

The notch zones still require practical sealing such as:

- silicone
- cable boot
- cable gland where possible
- potting
- drip loop
- leak detection

## Shell panel policy

The shell is now a support-free lightweight panel structure.  It is not a
hollow dome and it is not a waterproof enclosure.  Panels are intended to print
flat on the bed with no trapped support, and broken panels can be reprinted
individually.

## Material saver shell policy

The shell/dome parts are open-bottom hollow shells.  They are material saver
splash covers only, not waterproof enclosures.  The design avoids trapped
support, trapped water, and closed mud pockets.

## TPU minimization policy

TPU is limited to the replaceable tread/contact surface.

- wheel hub/core/axle bore: HARD material
- external tread ring/contact lugs: TPU material

Do not print the old full-TPU wheel unless deliberately comparing prototypes.

## Clean restart notes

This clean version removes obsolete G1 retrofit shell/hull/sponson print targets
from the v228 restart manifest.  The old parts were not fitted to the new fixed
core turtle-hull layout and could appear as unrelated loose blocks on dense
plates.

The upper turtle shell and lower belly hull are intentionally smaller and
simpler than the previous concept parts.  They are external modules around the
200 x 150 x 120 mm BBOX/CBOX fixed core, not replacements for the boxes.

When CadQuery export is run, `reference_metal_stl/` is also generated with
plastic surrogate shaft/rod models for `rigid_plus_metal` dense output.  These
are fit-check placeholders only, not load-bearing metal.

## Dense-safe split shell / hull policy

The upper turtle shell and lower belly hull are split left/right because the
single half parts were at or above the safe 232mm dense packing limit.  This
does not change the fixed core.  It only splits the external shell/hull modules
to avoid oversized print-target exclusion.

## v228.1 dual PTO output policy

The high front PTO returns to a two-output layout.  The front PTO mount has two
high forward output holes intended as left/right power takeoff ports.  This is a
layout and fit-check design, not a final sealed gearbox or final bearing design.

- left PTO output hole
- right PTO output hole
- both stay high, away from the expected waterline
- the PTO unit must not be placed in the low belly hull
- heavy front PTO work units may need their own float

## v228 compatibility note

v228 is a restart/release version for the external turtle-hull/front-PTO layout.
The BBOX/CBOX core remains v227-compatible and keeps the `PS-RV227-BBOX-*` and
`PS-RV227-CBOX-*` part IDs to protect already printed and already planned core
parts.  New external shell, belly hull, side motor mount, buoyancy, and front PTO
parts use `PS-RV228-*` IDs.

## v228 restart fixed core policy

This generator returns to the v227 fixed-core rule:

- BBOX + CBOX are arranged front/rear in series, not side-by-side.
- The correct box body orientation is 200 mm wide x 150 mm front/back x 120 mm high.
- Wire-drop notches are on the upper area of the 200 mm wide front/rear wall faces.
- Each BBOX/CBOX has one notch on each 200 mm wide face: front and rear.
- Do not put notches on the 150 mm side faces.
- The old v227 notch orientation must be treated as rotated 90 degrees.
- Motor boxes mount high on the waterproof box side walls, not on box top.
- PTO is front/high.
- Tires exit from the hull sides.

## Turtle shell / belly hull policy

BBOX/CBOX are the primary waterproof enclosures.  The upper turtle shell and
lower belly hull are secondary splash protection, bottom protection, and
buoyancy aids.  Printed buoyancy chambers are not guaranteed waterproof without
sealing/coating/foam filling.

## Dense maxpack command

```powershell
python .\paddy_swarm_a1_dense_project_tools_v5_7_3_model_sets_paddy_fix.py --manifest .\rover_v228_1_dual_pto_output_out\print_manifest_generic_marked.csv --out .\rover_v228_1_dual_pto_output_model_dense_sets --group-mode all --ignore-manifest-plates --split-tpu --safe 240 --support-orient-fit-safe 244 --gap 4 --bambu-template-plate-inner-margin 12 --bambu-plate-inner-margin 12 --make-3mf --make-bambu-template-project-3mf --bambu-template-3mf .\blank_a1_plates_4.3mf --make-zip
```

## Safety

- Do not use real electronics in first water tests.
- Use dummy weights.
- Keep E-stop visible and reachable.
- Do not block PTO.
- Do not drill into BBOX/CBOX for first retrofit testing.
- Rice fields are income-producing land; test in stages before any field use.
