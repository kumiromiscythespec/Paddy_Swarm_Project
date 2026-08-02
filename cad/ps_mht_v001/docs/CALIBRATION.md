# PS-MHT-V001 Calibration

All rows below are **CALIBRATION_PENDING**. No physical fit, leakage, strength,
or crop-load result has been measured.

## Phase 3R physical print results — Bambu Lab A1 / white PETG / 0.4 mm

These observations are measured print outcomes, not assumptions.

| Printed coupon | Result | Failure mode | Observation / decision |
|---|---|---|---|
| index_key_fit_coupon | FAIL | KEY_ROOT_FRACTURE | Thin key projections fractured at their roots before fit clearance could be evaluated. Thin cantilever keys are rejected. |
| m4_cartridge_fit_coupon | FAIL_WITH_ONE_SURVIVOR | SMALL_GATE_COLLAPSE | Thin L-parts and the middle candidate collapsed. Only the thickest candidate completed, with rough surfaces; the small independent gate/cartridge method is rejected for production. |
| angled_port_print_coupon | FAIL | OVERHANG_SAG_AND_OUT_OF_ROUND | The upper inner overhang sagged; burrs and stringing formed; roundness was insufficient and the adapter could not be inserted. The integrated angled circular receiver is rejected. |

General observation: large circular rings, annular parts, simple arcs, broad
contact faces and continuous walls printed well. Almost all small compound
parts with holes, cut-outs, narrow bases or cantilevers failed. Phase 3R
therefore changes the design to large integrated rings and commercial metal
retention hardware.

The old `index_key_fit_coupon`, `m4_cartridge_fit_coupon`,
`m3_port_cartridge_fit_coupon` and `angled_port_print_coupon` are
`DO_NOT_REPRINT_DEPRECATED_AFTER_PHYSICAL_FAILURE`.

Coupon symbol key:

- One raised dot: 0.30 mm/side interface, hex-nut test, or 2.0 mm groove
- Two raised dots: 0.40 mm/side interface, heat-set test, or 2.2 mm groove
- Three raised dots: 0.50 mm/side interface or 2.4 mm groove

| Interface / item | Design clearance | Measured clearance | Insertion force | Play | Leak | Damage | Reprint correction | Filament | Printer | Nozzle | Print date |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|
| module_interface_coupon 0.30 | 0.30 mm/side | — | — | — | — | — | — | — | Bambu Lab A1 | — | — |
| module_interface_coupon 0.40 | 0.40 mm/side | — | — | — | — | — | — | — | Bambu Lab A1 | — | — |
| module_interface_coupon 0.50 | 0.50 mm/side | — | — | — | — | — | — | — | Bambu Lab A1 | — | — |
| netpot_adapter_coupon | 0.3 mm nominal | — | — | — | — | — | — | — | Bambu Lab A1 | — | — |
| M4_insert_coupon hex nut | 7.0 mm AF assumption | — | — | — | N/A | — | — | — | Bambu Lab A1 | — | — |
| M4_insert_coupon heat-set | 5.6×6.0 mm assumption | — | — | — | N/A | — | — | — | Bambu Lab A1 | — | — |
| M5_clamp_coupon | TBD from knob/bolt | — | — | — | N/A | — | — | — | Bambu Lab A1 | — | — |
| TPU_gasket_coupon 2.0 | 3.0 mm cord / 2.0 mm groove | — | — | — | — | — | — | TPU 95A or EPDM | Bambu Lab A1 | — | — |
| TPU_gasket_coupon 2.2 | 3.0 mm cord / 2.2 mm groove | — | — | — | — | — | — | TPU 95A or EPDM | Bambu Lab A1 | — | — |
| TPU_gasket_coupon 2.4 | 3.0 mm cord / 2.4 mm groove | — | — | — | — | — | — | TPU 95A or EPDM | Bambu Lab A1 | — | — |
| module_body_roundness_coupon | OD200 / wall3 / H28 | — | N/A | — | N/A | — | — | White PETG | Bambu Lab A1 | — | — |
| hose_clip_coupon | 8/16 mm OD assumptions | — | — | — | — | — | — | — | Bambu Lab A1 | — | — |

Before Phase 2 production geometry is frozen, measure the actual M4/M5 knobs,
inserts, 2020 slot profile, PETG shrinkage, and TPU compression. Before Phase 3,
measure the commercial nominal-60 mm net pot and flange. Before Phases 4–5,
measure drain and irrigation hose outside diameters.

The 18×8 mm M4 knob, 22 mm bolt, 9 mm washer, 7 mm-AF nut, 5.6 mm insert
pilot, cartridge clearance, and slide-gate retention are provisional. Test
external removal, inverted washing, repeated assembly, and nut loss before
approving the full module.

## Phase 3A coupon records

| Coupon / station | Design value | Measured fit / leak | Correction |
|---|---:|---|---|
| index_key_fit_coupon | 0.20 / 0.30 / 0.40 mm | — | — |
| m4_cartridge_fit_coupon | 0.20 / 0.30 / 0.40 mm | — | — |
| gasket_compression_leak_coupon | 2.0 / 2.2 / 2.4 mm groove | — | — |
| netpot_adapter_coupon | 0.20 / 0.35 / 0.50 mm/side | — | — |
| port_receiver_adapter_coupon | 0.20 / 0.35 / 0.50 mm/side | — | — |
| angled_port_print_coupon | Actual 27-degree shell section | — | — |

## Phase 3A.1 correction coupon records

| Coupon / station | Design value | Measured insertion force | Measured removal force | Play / inversion | Wash / debris | Damage | Correction |
|---|---:|---:|---:|---|---|---|---|
| m3_port_cartridge_fit_coupon, one dot | 0.20 mm/side; M3 nut AF 5.5 mm assumption | — | — | — | — | — | — |
| m3_port_cartridge_fit_coupon, two dots | 0.30 mm/side; M3 nut AF 5.5 mm assumption | — | — | — | — | — | — |
| m3_port_cartridge_fit_coupon, three dots | 0.40 mm/side; M3 nut AF 5.5 mm assumption | — | — | — | — | — | — |
| port_receiver_adapter_coupon_phase3a1 | 0.20 / 0.35 / 0.50 mm/side | — | — | — | — | — | — |
| complete_port_passage_coupon_phase3a1 | φ60 pot axis / φ48 folded-root gauge | — | — | — | — | — | — |
| root_ring_passage_coupon, one dot | 0.35 mm/side, tab-inclusive | — | — | — | — | — | — |
| root_ring_passage_coupon, two dots | 0.50 mm/side, tab-inclusive selected | — | — | — | — | — | — |
| root_ring_passage_coupon, three dots | 0.70 mm/side, tab-inclusive | — | — | — | — | — | — |
| netpot_adapter_coupon after pot measurement | 0.20 / 0.35 / 0.50 mm/side | — | — | Rotation acceptable | — | — | — |

For each M3 station, record whether the loose cartridge survives a light
inverted test with the bolt removed, whether the normal bolt positively
captures the rigid gate, and whether brush or flowing water reaches the nut
chamber. Do not approve an interference fit that requires bending a printed
tab.

For each root ring, insert it together with the folded flexible sleeve, place
the captive sleeve fold at the common-adapter inner-end datum, rotate it
through a full turn, remove both from the exterior, and inspect the sleeve for
snagging or cuts. Record axial migration under wet root load. Phase 3A.1 has
no solid inward seat because one would constrict the required φ66 adapter
passage.

## Phase 3R large-part calibration records

| Coupon | Candidate | Result | 10-cycle fit | 30° rejection | Nut/metal retention | Roundness / overhang | Correction |
|---|---:|---|---|---|---|---|---|
| large_index_ring_coupon_phase3r | 0.35 mm/side | — | — | — | N/A | — | — |
| large_index_ring_coupon_phase3r | 0.45 mm/side selected | — | — | — | N/A | — | — |
| large_index_ring_coupon_phase3r | 0.55 mm/side | — | — | — | N/A | — | — |
| annular_nut_ring_coupon_phase3r | 0.15 / 0.25 / 0.35 mm pockets | — | N/A | N/A | — | N/A | — |
| self_supporting_port_shell_coupon_phase3r | 27° teardrop / 45° upper faces | — | N/A | N/A | N/A | — | — |
| port_function_ring_coupon_phase3r | preliminary 72 mm body assumption | — | — | N/A | N/A | — | — |

For the purchased PP/PE vegetable mesh bag, begin with 135 mm length and a
20 mm foldover. Test axial retention at 500 g and 1 kg. Do not add a printed
positive snap in Phase 3R.

## Purchased nominal-60 net-pot measurement record

The current CAD values are **ASSUMPTION / CALIBRATION_PENDING**, not actual
measurements: flange OD 68 mm, flange thickness 2 mm, top body OD 60 mm,
bottom body OD 42 mm, body height 55 mm, taper 9.293 degrees, 3 mm-wide
representative slots, and 12 slots.

| Required field | Measured value |
|---|---|
| Flange maximum diameter | — |
| Flange thickness | — |
| Upper body diameter | — |
| Bottom body diameter | — |
| Overall height | — |
| Taper | — |
| Protrusions / molding flash | — |
| Slot arrangement | — |
| Purchased manufacturer | — |
| Product model / SKU | — |
| Measurement date | — |

Also measure M3 bolt shank/head, nut across-flats/thickness, washer, and tool
envelope. Verify keyed adapter insertion/removal, inversion retention, wash
access, rain-return behavior, and gasket compression. Preferred port-gasket
material and food-contact suitability remain unresolved.

For the flexible root sleeve, record manufacturer, product model, PP/PE grade,
expanded volume, collapsed diameter, seam strength, root snagging, wash life,
food-contact declaration, and replacement interval. The STEP reference is not
a printable root mesh.

## Phase 3R.2 integrated-cylinder print-stability audit

`result = ABORTED`

`reason = GEOMETRIC_REQUIREMENT_CONFLICT`

`status = ABORTED_BY_REQUIREMENT_CONFLICT`

`superseded_by = PHASE_3S_THREE_SECTOR_SPLIT_SHELL`

Physical failure:

- The integrated cylindrical shell shifted during its vertical print and
  produced extensive spaghetti failure.
- Bed warping or nozzle contact is the probable source of the position shift.
- The approximately 218.7 x 199.9 x 140 mm coupon had insufficient real bed
  contact and lateral print stability for its height.

Geometric audit:

- Existing reinforcement-frame Z extent: 100.349 mm.
- Existing 27-degree teardrop-void Z extent: 113.650 mm.
- Minimum with a nominal 75 mm shell and 0.8 mm base while retaining the full
  frame: approximately 101.15 mm.
- An 80 mm maximum height cannot coexist with exact preservation of the
  opening, reinforcement frame and 27-degree axis.

Next design:

- Three 120-degree split shell panels.
- Lower print height.
- Broad bed-contact geometry.
- Upper and lower annular assembly rings.

No Phase 3R.2 CAD, STEP, STL or coupon is generated. The Phase 1 through
Phase 3R.1 artifacts remain unchanged, and implementation is stopped pending
the Phase 3S instructions.

## Phase 3S-A sector-seam and temporary-ring calibration

`status = CALIBRATION_PENDING`

Print and test each seam clearance independently:

| Coupon | Dimple ID | Clearance | Hand assembly | 10 cycles | Whitening/crack | Lateral play | Seam step | 500 mL inward drip | Direct outward flow | Brush access |
|---|---:|---:|---|---|---|---|---|---|---|---|
| sector_seam_coupon_c040_phase3sa | 1 | 0.4 mm | — | — | — | — | — | — | — | — |
| sector_seam_coupon_c060_phase3sa | 2 | 0.6 mm | — | — | — | — | — | — | — | — |
| sector_seam_coupon_c080_phase3sa | 3 | 0.8 mm | — | — | — | — | — | — | — | — |

Reject any candidate requiring impact or prying tools. Record assembly and
disassembly time, white stress marks, permanent step, direct outward nutrient
path and post-test cleaning access. The seam is a drip-return labyrinth, not
a certified waterproof joint.

After seam calibration, print the panel-end capture coupon and verify the
temporary ring can be installed and removed without damaging the panel end.
Then measure lower and upper diameters, roundness and seam step on the short
three-panel assembly. The reusable external band is a purchased reference,
not a printed component.

Do not print three full-height production panels until the single full-height
panel and short assembly both pass. Final M4 fastening, wave stacking rings,
drainage, irrigation and net-pot liner fit remain unresolved.

## Phase 3S-A.2 full-length seam physical-test record

`selected_clearance = None`

### Short-coupon results inherited from Phase 3S-A

| Candidate | Leak test | Assembly force | Stress whitening | Full-length behavior | Selection status |
|---|---|---|---|---|---|
| c040 | `PASS_ON_SHORT_COUPON_WHEN_MANUALLY_SEATED` | `UNRESOLVED` | `UNRESOLVED` | `CALIBRATION_PENDING` | `PENDING_FULL_LENGTH_TEST` |
| c060 | `PASS_ON_SHORT_COUPON_WHEN_MANUALLY_SEATED` | `UNRESOLVED` | `UNRESOLVED` | `CALIBRATION_PENDING` | `PENDING_FULL_LENGTH_TEST` |
| c080 | `FAIL` (`WATER_LEAK_WHEN_SEATED`) | — | — | `NOT_RETESTED` | `REJECTED` |

Common findings:

- All three candidates left a visible mating-face gap when only the guide
  geometry was followed.
- Manually closing the mating faces stopped leakage on c040 and c060.
- c080 leaked even while the mating faces were manually closed.
- The short coupons cannot measure full 170 mm insertion force, whitening,
  panel bow, or upper/lower capture-ring restraint.
- c080 is rejected and is not included in Phase 3S-A.2.
- `selected_clearance` remains `None` until the full-length procedure passes.

For c040 and c060, record free-state insertion and top/middle/bottom gaps,
then repeat with identical upper and lower local capture fixtures at nominal
diameter 200 mm. Perform ten removal cycles, a 24-hour assembled hold and a
500 mL inward drip test. Inspect whitening, cracks, edge chipping, permanent
deformation, creep, play, direct outward leakage and water-return behavior.

c060 is preferred only if it assembles without tools, shows no whitening,
survives ten cycles, has no large fixture-constrained gap or direct leak, and
remains removable after 24 hours. If c060 fails from play or leakage and c040
passes without excessive force, select c040. If both fail, stop for guide or
capture-method redesign instead of choosing another numerical clearance.

## Phase 3P-A Siawadeky net-pot physical-fit calibration

`status = PHYSICAL_FIT_CALIBRATION_PENDING`

`netpot_body_passage_selected = None`

Measurement date: 2026-08-01. Three Siawadeky net pots were measured and all
three gave the same values within the caliper display resolution. External
dimensions were measured with the caliper outside jaws; internal dimensions
were measured with the inside jaws. The internal values are reference data and
must not be interpreted as external interference-envelope diameters.

| Measurement | Value |
|---|---:|
| Flange outside diameter | 108.0 mm |
| Flange thickness | 4.0 mm |
| Overall height | 68.0 mm |
| Body height below flange | 64.0 mm |
| Maximum body outside diameter | 78.6 mm |
| Maximum rib outside diameter | 78.6 mm |
| Upper inside diameter | 77.2 mm |
| Reachable lower inside diameter | 75.8 mm |
| Deepest reachable inside diameter | 69.6 mm |
| Flange radial overhang from maximum body | 14.7 mm |
| Maximum external rib projection | 0.0 mm |

The former image-derived 78.5 mm flange and preliminary 72.0 mm body
assumptions are rejected by physical measurement. The Phase 3R.1 84.0 mm
port bore is retained only as historical/reference geometry and is not a final
fit decision.

Flat coupons with body passages of 80.0, 80.5 and 81.0 mm will be compared.
The 80.5 mm coupon is the first print candidate, not a selected production
value. Record vertical insertion, full-circumference flange seating, body and
rotational play, 20 tool-free removal cycles, damage, inverted retention, and
27-degree retention with empty, wet-sponge-equivalent and 500 g reference
loads. If c805 is too loose test c800; if c805 is too tight test c810. The
final port function ring remains unresolved until the physical test is
complete.

## Phase 3H-A entry — c805 body-passage physical selection

The Phase 3P-A `plate_01_netpot_fit_c805_phase3pa.stl` coupon was printed and
tested with three measured Siawadeky net pots. All three inserted without
tools, rib catching or forced deformation. Each flange seated around the full
circumference with no visible tilt. Observed lateral play was approximately
1 mm and was not judged excessive, but the observation method was not
standardized.

`netpot_body_passage_selected = 80.5`

`netpot_body_passage_selection_status = PASS_BODY_PASSAGE_PHYSICAL`

`netpot_body_passage_observed_lateral_play_mm = APPROXIMATELY_1_0`

`netpot_body_passage_observed_play_measurement_method = NOT_STANDARDIZED`

`c800_status = NOT_REQUIRED_AFTER_C805_PASS`

`c810_status = NOT_REQUIRED_AFTER_C805_PASS`

This selects only the body passage. The 20-cycle removal test, 27-degree
retention, wet-medium test, 500 g load test and final port assembly remain
`CALIBRATION_PENDING` or `REDESIGN_REQUIRED`. The result does not approve the
existing M4, shell, root-zone or maximum-diameter geometry.

The Phase 3CB-0 architecture audit remains `CONFLICT_FOUND` and prohibited CAD
within its own scope. Phase 3H-A is separately allowed as a planting-hole-free,
buffer-free horizontal-joint calibration after its scoped entry conditions.

## Phase 3H-A horizontal full-ring joint calibration

`horizontal_joint_clearance_selected = None`

Candidate clearance is radial per side: c030 = 0.30 mm, c050 = 0.50 mm and
c070 = 0.70 mm. Print the c050 90-degree arc pair first. Print c030 only when
c050 is clearly loose, or c070 only when c050 is too tight. An arc result is a
preliminary insertion, section, water-return-direction and printability check;
it cannot select the final clearance.

After an arc passes, explicitly generate the same candidate's full-ring pair
and print two common compression rings. Assemble without tools or impact,
confirm continuous hard-stop seating and record assembly time plus axial and
radial play. Tighten the three M4 threaded-rod references incrementally and
evenly; stop at hard-stop seating without crushing PETG. Record height before
and after compression.

Perform ten disassembly/reassembly cycles and inspect whitening, cracking,
edge chipping, wear, play growth and assembly-force change. With a purchased
PE or silicone test membrane isolated from the joint, hold water 20 mm above
the seam for 12 hours. Acceptance is no continuous jet and no more than 5 mL
per seam per 12 hours. Then flow 2 L down the inner wall at approximately
1 L/min and confirm that water follows the internal skirt rather than exiting
directly outside. Finally hold axial compression for 24 hours and record
permanent deformation, creep, removability and reassembled play.

c050 is the first full-ring candidate. Test c030 if c050 leaks or has excessive
play; test c070 if c050 cannot assemble or whitens. Selection remains `None`
until one full-ring candidate passes every applicable criterion.
