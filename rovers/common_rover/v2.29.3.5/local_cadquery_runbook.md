> [!WARNING]
> **Status: EXPERIMENTAL_PREFLIGHT_SOURCE**
>
> This revision is a design-authority and pre-CadQuery validation snapshot.
> CadQuery/OCP execution has not yet been performed.
>
> No actual Solid, STEP, STL, rendered PNG, collision result,
> minimum-assembly result, structural-strength result, waterproof result,
> manufacturing release, purchase approval, or field-deployment approval
> is provided by this revision.
# v2.29.3.5 local CadQuery runbook

One execution authority is used for every stage:

1. `python run_loop001_stage.py --stage preflight --output run_output`
2. `python run_loop001_stage.py --stage solid --output run_output`
3. `python run_loop001_stage.py --stage holes --output run_output`
4. `python run_loop001_stage.py --stage export --output run_output`
5. `python run_loop001_stage.py --stage render --output run_output`
6. `python run_loop001_stage.py --stage minimum-assembly --output run_output`
7. `python run_loop001_stage.py --stage review-pack --output run_output`
8. Obtain an independent external image review receipt.
9. `python run_loop001_full.py --stage finalize --output run_output --review-receipt receipt.json`

For a complete run use `python run_loop001_full.py --stage all --output
run_output`. `run_all.ps1` invokes that command once.

CadQuery absence exits 20. Undefined structural joint blocking exits 71 after
the permitted rail-only stages. Neither condition is an exit-0 PASS.

