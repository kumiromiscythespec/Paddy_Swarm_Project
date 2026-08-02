# PS-MHT Horizontal Stack Options

Phase: **3CB-0 architecture comparison**  
Status: **FIVE-BAND LEADING OPTION / NOT SELECTED**

## 1. Fixed geometry used by the audit

- Module height: 170 mm.
- Existing teardrop opening vertical extent: approximately 113.650 mm.
- If centered at module mid-height, opening limits are
  `85 +/- 113.650/2 = 28.175 to 141.825 mm`.
- Body OD target remains about 200 mm; installed maximum is 240 mm hard and
  238 mm preferred.
- Port axis remains 27 degrees.

## 2. Three/four/five-band comparison

| Option | Candidate heights | Horizontal joints | Joints crossing opening | Maximum individual height | Strengths | Primary risks |
|---|---|---:|---:|---:|---|---|
| 3 bands | 25/120/25 | 2 | 0 | 120 mm | Opening remains in one part; fewest leak paths | Tall port band repeats print-height/warping risk; difficult cleaning around integrated port |
| 4 bands | 25/60/60/25 | 3 | 1 at z=85 | 60 mm | Moderate print height and part count | Joint crosses widest opening section and complicates port datum/seal |
| 5 bands | 25/40/40/40/25 | 4 | 2 at z=65/105 | 40 mm | Lowest print height; widest opening region stays in central band; bottom end band can own buffer floor | Most joints and leak paths; two joints intersect opening; alignment stack-up |

All dimensions are candidates. The five-band layout is the leading coupon
planning option because physical history favors low, broad, annular prints and
because the central three bands span 120 mm, leaving 3.175 mm beyond each end
of the existing 113.650 mm opening. That 3.175 mm is not yet a validated
structural margin.

## 3. Candidate five-band functions

| Band | Height | Candidate function | Audit note |
|---|---:|---|---|
| Lower end/hydraulic band | 25 mm | Buffer floor, low-point drain, lower stack datum | Real water depth must subtract floor, freeboard and joint geometry; 0.8 L is impossible |
| Lower port/hydraulic band | 40 mm | Lower opening/frame segment, overflow pickup, removable screen | Do not create a hidden tray behind frame |
| Central port band | 40 mm | Widest opening segment, replaceable pot cassette datum | Avoid horizontal joint at opening maximum width |
| Upper port/hydraulic band | 40 mm | Upper opening/frame segment, gravity inlet, splash return | Keep inlet removable and shielded |
| Upper end band | 25 mm | Top module datum, service cover/next-module interface | No upper-tank load into shell |

The buffer may span a removable lower tray inserted between the lower two
bands, but the liquid cavity must remain open to inspection. The 25 mm lower
band cannot be treated as 25 mm usable water depth.

## 4. Buffer-plan comparison

| Plan | Capacity potential | Port/root conflict | Cleaning | Leak containment | Audit position |
|---|---|---|---|---|---|
| Full annulus | Highest | Highest central/root and rod conflict | Good only with full removable cover | Long joint perimeter | Capacity reference, not default |
| C-shaped annulus | Medium/high | Leaves service gap for drain/rods | Direct brush access through gap | Defined low point possible | Leading Phase 3CB-A coupon family |
| Rear half-annulus | Low/medium | Keeps front port service clear | Excellent | Shorter wetted perimeter | Useful low-volume control |
| Three pockets between ports | Medium | Can avoid three pot axes | Each pocket needs drain/overflow or flush path | Multiple stagnation zones | Compare only if pockets connect through large cleanable passages |

## 5. Joint and leakage architecture

Phase 3H-A isolates a short, planting-hole-free ring joint with:

- 0.3/0.5/0.7 mm explicit clearances,
- inward water-return skirt,
- hard compression stop,
- replaceable gasket or secondary liner,
- M4 all-thread compression reference,
- no small nut cartridge, snap or claw.

Printed mating walls do not own permanent watertightness. Joint acceptance
must cover static leakage, repeated assembly, creep, contamination and brush
access. Any all-thread route must be checked against the root volume and the
240 mm installed envelope. External rods that push the envelope near 240 mm
are not accepted merely because they fit a bare ring.

## 6. Printing audit

All candidate bands fit the A1 height limit when printed flat. The relevant
risk is not only nominal build height:

- Broad continuous bed contact is required.
- A closed 200 mm annulus is preferred over isolated feet.
- Tall 120 mm rings retain warping/nozzle-contact risk despite broad contact.
- Forty- and sixty-millimetre bands reduce lever arm and print time at risk.
- Joint count increases dimensional stack-up, assembly work and leak paths.
- Every production band requires a single-component, closed-manifold and
  orientation audit in its own later CAD phase.

## 7. Recommendation and blockers

Use 25/40/40/40/25 mm as the **leading architecture for interface and tray
coupon planning**, not as a frozen production specification. Do not start the
integrated Phase 3H-B module until:

1. Phase 3H-A selects or rejects the horizontal joint.
2. Phase 3CB-A measures actual tray area, volume, drain and overflow behavior.
3. The 241.215 mm pot envelope conflict is redesigned below 240 mm, targeting
   238 mm rather than the limit.
4. A port cassette spans or terminates the two opening-crossing joints without
   reintroducing small printed retainers.
5. The M4 compression path is outside pot service and root zones.

If the two opening-crossing joints cannot meet strength, leakage and service
criteria, stop and compare the three-band opening carrier rather than silently
changing the opening or 27-degree axis.
