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
# Common Rover v2.29.3.5

Contract:
`PS-COMMON-ROVER-V229_3_5-LOOP001-HOLE-AUTHORITY-FULL-RUNNER-WIRING-CLOSURE-001`

This isolated lane determines rail-hole responsibility from attachment, joint,
load-path, part-role, and measurement authority before any reachability check.
Unreachable instances are never silently converted to stale records and no
coordinate is moved without authority.

The 24 rail-referencing instances account as:

- four required FG-006 rail through holes;
- eight measurement holds in FG-002 and FG-004;
- twelve design contradictions in FG-008, FG-009, and FG-020.

Static full-circle inspection identifies four interior candidates, five
edge-breakout candidates, and fifteen exterior/contradiction candidates. The
five boundary circles are not generated as normal holes or reinterpreted as
slots/notches.

`full_loop_runner.py` is the single 24-stage execution authority. It wires
required-hole generation, STEP reimport, visualization STL validation, actual
Solid rendering, minimum-assembly propagation, receipt consumption, final
gate, package, and final ZIP seal. CadQuery absence exits 20 and never claims
Solid, STEP, STL, PNG, or assembly PASS.

The rail remains `METAL_PART_CAD_VALIDATION`, not a production print target.
The rail/front-crossmember joint remains `UNDEFINED_MEASUREMENT_HOLD`, so
minimum-assembly and LOOP-001 final PASS are blocked.

