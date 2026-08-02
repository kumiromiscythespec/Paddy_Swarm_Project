# PS-MHT Existing Specification Compatibility

Phase: **3CB-0**  
Status: **CONFLICT_FOUND / NEXT CAD BLOCKED BY ENTRY CONDITIONS**

## A. Maintained specifications

| Specification | State | Reason |
|---|---|---|
| Nominal tower body diameter about 200 mm | MAINTAINED | Core system and A1 packaging datum |
| Maximum installed diameter 240 mm | MAINTAINED | Hard limit; 238 mm remains production target |
| Planting-port upward angle 27 degrees | MAINTAINED | Explicit immutable functional input |
| White PETG | MAINTAINED | Opaque, existing material/process basis |
| Five 170 mm planting modules | MAINTAINED_FOR_AUDIT | System target; band subdivision pending |
| Module-level disassembly, cleaning and replacement | MAINTAINED | Required service architecture |
| Opaque nutrient path with inspectable service points | MAINTAINED | Algae and cleaning control |
| Circular/annular, flat-print parts preferred | MAINTAINED | Supported by physical print history |
| Bambu Lab A1, 0.4 mm nozzle | MAINTAINED | Manufacturing envelope |
| Measured Siawadeky dimensions | MAINTAINED | Three samples equal within caliper resolution |
| Net-pot body passage selected value | `None` | c800/c805/c810 physical calibration still pending |

## B. Changed specifications

| Former direction | New direction |
|---|---|
| Integrated vertical cylinder | Horizontally sliced full-circumference bands |
| Three 120-degree production panels | Removed from production candidacy after c060 result |
| Vertical labyrinth seam | Horizontal joint with return skirt and controlled compression |
| Continuous 24-hour circulation reference | Intermittent pumped lift plus passive local moisture hold |
| Pot-adjacent M4 layout | New service route outside the measured flange/removal envelope |
| 50 mm-ID root ring | Root-zone and wick/screen interface must be re-sized |
| One architecture carrying top water mass | Upper tank supported independently by aluminium structure |

## C. Deprecated or rejected specifications

- Fine keys, small L-shaped printed parts and small M3/M4 cartridges.
- Small PETG clips, snaps, claws and gates as wick or seal retainers.
- Integrated-cylinder vertical printing.
- c060 full-length vertical seam: seated and unwhitened, but excessive play
  and water leakage; rejected.
- c040 continuation for production vertical seams; not printed because the
  vertical split architecture itself is removed from production candidacy.
- Image-derived 78.5 mm pot flange and 72.0 mm body.
- Treating the existing 84 mm hole as a final fit.
- Using capillarity as the mechanism that lifts solution from bottom to top.
- Assuming printed PETG walls alone provide permanent watertightness.
- Assuming 80–90% energy reduction before measured trials.

## D. Calibration pending

- Horizontal band count and heights.
- Joint clearance 0.3/0.5/0.7 mm, compression load and gasket/return-skirt
  geometry.
- Body passage 80.0/80.5/81.0 mm.
- Final pot cassette and fastener route within 238 mm target/240 mm limit.
- Buffer shape, usable cross-section, retained volume and freeboard.
- Overflow ID 12/14/16 mm and drain ID 8/10/12 mm.
- Upper tank 3/4/5 L and common lower tank 40/50/60 L.
- Pump, manifold, tube and flow-control dimensions.
- Root-screen open area and service interval.

## E. Experiment required

- Wick material, diameter/width, count, immersion and delivered mass flow.
- Coir and coir/perlite moisture curves for parsley and chive.
- Pump runtime, actual head-flow curve, start current and Wh/day.
- Off-time progression through 1/3/6/9/12 hours.
- Outlet fouling under real canal water and Hypnica A/B solution.
- Joint leakage, creep, cleaning time and repeated assembly.
- Root intrusion, algae and screen pressure/flow loss through a 30-day trial.
- Tower-level agronomic response with treatment replication.

## F. Existing-design conflicts

1. **Diameter:** measured installed pot envelope is 241.215 mm, 1.215 mm
   above the hard limit.
2. **Port service:** the existing 50 mm-radius M4 axes lie inside the measured
   54 mm flange radius; bolt, washer, head, nut, tool and removal paths conflict.
3. **Shell:** conservative pot envelope intersects the existing shell/frame by
   4,788.534 mm³.
4. **Buffer capacity:** 0.8 L requires 27.06 mm even in an unobstructed
   194 mm-ID circle and therefore conflicts with the 25 mm depth ceiling.
5. **Trial design:** four unique tower recipes provide no replicated
   circulation treatment and confound medium/wick with architecture.

These conflicts are carried forward as blockers; measured geometry, the
27-degree axis and the 240 mm limit are not adjusted to force compatibility.
