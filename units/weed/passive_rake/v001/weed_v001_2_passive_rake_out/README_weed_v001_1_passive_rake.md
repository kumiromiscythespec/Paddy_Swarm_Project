# Paddy Swarm Weed Unit V001 Passive Rake

`Paddy Swarm Weed Unit V001.2 Passive Rake Gauge Reference Fix Width Gauge Split` / `weed-v001.1-passive-rake-width-gauge-split`

## Purpose

This is the first front-mounted weeding-unit study for Paddy Swarm Common Rover v2.28.2.
It is a passive comb / rake / hand-rake style unit.  It is intentionally not a
complex rotary weeder.

## Core design rule

- The rover body stays afloat and moves forward.
- The weeding unit reaches down to shallow mud.
- PTO is **not** used for continuous weeding.
- PTO is only used as an optional one-time DROP / latch-release assist.
- MANUAL_DROP must work without PTO for the first safety tests.

## Operation modes

### MANUAL_DROP

1. Raise the rake.
2. Hold it with the latch.
3. Pull the manual lever or cord.
4. Rake drops by gravity.
5. Depth skids limit tine engagement.
6. Rover propulsion performs passive weeding.

### PTO_DROP

1. Rake is latched in the raised state.
2. Run front PTO briefly.
3. PTO drop cam pushes the drop link.
4. Drop latch releases.
5. Rake drops by gravity.
6. Stop PTO.
7. Rover propulsion performs passive weeding.

PTO_DROP is a release/deploy mechanism only.  Do not use V001 PTO parts for
continuous rotary weeding.

## Row spacing / dimensions

- Target row spacing: 300mm.
- Initial work width target: 140-180mm.
- Maximum work width target: about 220mm.
- Unit body must stay under 300mm envelope.
- Tine depth targets: 10 / 20 / 30mm.

## Safety notes

- Not for real paddy field deployment.
- First tests: bench, tank, shallow mud, low speed only.
- Keep PTO, motor boxes, notches, and electronics above water.
- If the rake catches, unit-side shear pins/tines should yield before rover core damage.
- Mini floats are optional trim parts and are not waterproof without seal/coat/foam.

## Generated files

- `stl/*.stl`
- `step/*.step`
- `reference_metal_stl/*.stl` when full CadQuery export is run
- `print_manifest.csv`
- `print_manifest_generic_marked.csv`
- `plate_manifest.csv`
- `paddy_swarm_weed_v001_1_passive_rake_design_contract.json`
- `SHA256SUMS`

## Commands

Metadata-only:

```powershell
python .\paddy_swarm_weed_v001_2_passive_rake_cadquery.py --metadata-only --out .\weed_v001_2_passive_rake_meta --make-zip
```

Full CAD export:

```powershell
python .\paddy_swarm_weed_v001_2_passive_rake_cadquery.py --out .\weed_v001_2_passive_rake_out --make-zip
```

Dense model sets:

```powershell
python .\paddy_swarm_a1_dense_project_tools_v5_7_3_model_sets_paddy_fix.py --manifest .\weed_v001_2_passive_rake_out\print_manifest_generic_marked.csv --out .\weed_v001_2_passive_rake_model_dense_sets --group-mode all --ignore-manifest-plates --split-tpu --make-model-dense-sets --safe 240 --support-orient-fit-safe 244 --gap 4 --bambu-template-plate-inner-margin 12 --bambu-plate-inner-margin 12 --make-3mf --make-bambu-template-project-3mf --bambu-template-3mf .\blank_a1_plates_4.3mf --make-zip
```

## v001.2 width gauge dense fix

The 300mm row-width gauge and the 150mm A/B gauge halves are retained as metadata/reference parts only.  Dense printing excludes them because they are inspection aids, not rover/weed-unit hardware.  For row-width checking, use a ruler/tape measure or print a separate simple gauge outside the dense workflow.

## Known limits

- The PTO cam / latch is a first-fit mechanism.  Expect hand tuning after print.
- Printed shear pins are for safety/release testing, not final load-bearing pins.
- Real mud may require metal tines or softer replaceable tine variants.
- This generator cannot prove waterproofing or actual weeding performance.
