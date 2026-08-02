# PS-MHT-V001 Design Decisions

## DD-001 — Metal load path datum

The tower support plane is Z=0. The 2020 base members occupy Z=-20..0 and a
220 mm diameter, 3 mm aluminium load-spreader plate terminates at Z=0. The
drain-base envelope starts at Z=0. This keeps the printed drain base on a broad
metal support rather than a PETG point contact.

## DD-002 — Rear-post location

The rear post center is Y=150 mm. With a 20 mm profile, its front-face
clearance is 40 mm from the 200 mm body and 20 mm from the 240 mm maximum
tower envelope. This is an **ASSUMPTION** for the future clamp bridge and must
be rechecked with actual planting ports, hoses, and knobs.

## DD-003 — Phase 1 module shell

The printable shell is an open 200 x 170 mm tube with a 3 mm wall. It has no
water-retaining floor, plant ports, interface lip, gasket groove, or fastener
bosses. A 0.5 mm shallow witness groove identifies assembly rotation while
leaving 2.5 mm local wall. The groove is a Phase 1 datum, not the Phase 2 key.

## DD-004 — Reference envelopes are not parts

Solid cylinders representing the 140 mm drain base and 100 mm irrigation top
exist only to validate stack height and frame placement. They are marked
`REFERENCE_ENVELOPE_ONLY` and are never exported as STL.

## DD-005 — Existing-code reuse boundary

The implementation follows the tracked Paddy Swarm patterns for centralized
parameters, single-solid validation, A1 BoundingBox checks, STEP re-import, and
separate printable/assembly exports. The older reusable helpers enforce a
different 240 x 240 x 220 mm project envelope, so PS-MHT keeps a local
validation module with the specified 245 x 245 x 240 mm absolute limit.

## DD-006 — External Phase 2 interface

The module interior remains a continuous 194 mm nominal diameter. The male
spigot occupies R97..103 mm outside that opening and enters a female socket
with 0.4 mm radial clearance. A 220 mm annular flange provides a nominal
6.6 mm radial load/contact band outside the socket. Six local M4 bosses extend
the fixed printed envelope to 236 mm.

The socket has a 2 mm solid roof above its 8 mm depth. This joins the external
socket ring back to the shell without creating an inward root-zone shelf.

## DD-007 — Sixfold index and three fasteners

Six shallow, broad keys are placed at 0/60/120/180/240/300 degrees near the
spigot tip. Matching grooves have radial and tangential fit allowance. Six M4
station candidates occupy the 30-degree intermediate axes. Normal fasteners
use 30/150/270 degrees, leaving the rear 90-degree service region free.

The M4 fasteners clamp two flange faces; they do not carry the nominal vertical
load alone. A conservative 18 mm knob envelope gives a 238 mm absolute radial
envelope.

## DD-008 — Radial cord seal and hard stop

The adopted Phase 2 seal is a 3 mm TPU/EPDM cord ring in a 3.6 mm axial-width,
2.2 mm radial-depth groove on the spigot. With the provisional socket clearance,
nominal radial compression is 0.4 mm. The 6.6 mm flange band is the hard axial
stop, so bolt torque cannot indefinitely crush the cord.

This is for non-pressurized splash and leakage reduction. It is not a pressure
vessel seal. A thin flat TPU gasket remains a documented comparison candidate
but is not the adopted Phase 2 geometry.

## DD-009 — Replaceable M4 nut cartridge

The M4 nut sits in a separate side-load cartridge with a roof and floor. The
cartridge enters through an external radial pocket and is blocked by a separate
vertical slide-gate retainer. A locking arm on that retainer is pierced by the
normal M4 bolt, positively preventing retainer loss while assembled. Six
pockets exist, but only three are normally populated. Nut, heat-set insert,
and retainer fit remain
`CALIBRATION_PENDING`; the slide gate is not approved for production until
inversion and wash tests pass.

## DD-010 — Phase 2 keep-outs

The 240 mm absolute tower cylinder, six tilted φ60 port axes, rear post, drain
service zone, clamp zone, and main hose zone are reference solids only. They
are exported in a STEP reference and never included in printable STL files.

## DD-011 — Exactly three physical Phase 3A ports

The reusable module has physical bores only at local 0/120/240 degrees. Odd
levels use those angles and the same part is rotated 60 degrees on even levels,
producing 60/180/300 degrees. The selected height pattern is candidate A,
85/85/85 mm. Candidate B, 70/85/100 mm, produces the same 0.770–0.898 L
non-overlapping root envelopes but moves two port structures 15 mm toward the
interface bands and gives a visibly staggered datum. It is not selected.

## DD-012 — Integrated shallow saddle selected

Concept A, an integrated shallow saddle, is selected over a separate saddle.
The common receiver starts at R87, is 12 mm long, and uses an 86 mm main
outside diameter plus a 94 mm shallow root land. The real Phase 3A module stays
inside R120. The root land distributes load into the cylindrical shell and the
through-bore leaves no sealed cleaning cavity.

| Criterion | A: integrated saddle | B: separate saddle |
|---|---|---|
| Supports | Short angled underside; coupon required | Can print separately flat |
| Part count | No extra structural saddle | Three saddles plus hardware |
| Root strength | Continuous shell load path | Depends on M3 clamp transfer |
| Cleaning | Open through-bore | Additional joint crevice |
| Replacement | Adapter remains replaceable | Saddle and adapter replaceable |
| Maximum diameter | Passes 240 mm | Can pass 240 mm |
| Material | More module material | Less module, more separate material |
| Failure risk | Angled underside quality | Assembly, leak path, loose part |

The 94-to-86 mm curved/conical root transition is the current R4-class design
target. A mathematically constant R4 fillet is not claimed; underside quality,
crack initiation, and the final blend are **CALIBRATION_PENDING** on the
angled-port print coupon.

## DD-013 — Common receiver and replaceable adapters

The tower-side bore is 72 mm and is independent of the purchased net-pot
dimensions. A keyed common adapter has a 71.3 mm body, 0.35 mm/side nominal
fit, two M3 through axes, and an external replaceable metal-nut retainer. A
separate nominal-60 net-pot insert fits the common adapter. The blank cap uses
the same keyed body and M3 pattern and includes an external rain-return lip.
No large perimeter thread, fine bayonet finger, glue joint, or repeatedly
threaded PETG hole is used.

## DD-014 — Purchased flexible root sleeve

The primary root enclosure is a purchased/replaceable PP or PE flexible mesh
sleeve. PETG is used only for its retaining ring and optional perforated root
stop. Expanded references are three 110-degree sectors with a rear service
notch; CAD volumes are approximately 0.898/0.770/0.898 L and pair overlap is
zero. The 48 mm collapsed envelope fits through the 72 mm common receiver.
Expanded and collapsed references are STEP-only purchased-part envelopes,
never printable STL.

## DD-015 — Phase 3A service corridor

The Phase 2 provisional external hose zone at XY=(28,130) intersects the
nominal-60 removal sweep of a 60-degree even module. Phase 3A therefore
reserves an internal rear service corridor centered at XY=(0,60), with the root
sleeve notched around it. This is an **ASSUMPTION**, not final irrigation
routing; actual tube routing remains Phase 5 work. With this corridor, 130 mm
extraction sweeps at both 0 and 60 degrees have zero measured intersection with
neighboring ports, M4 knobs, rear post, hose corridor, and module interfaces.

## DD-016 — Phase 3A.1 continuous planting passage

The common-adapter flange is an annulus with the same 66 mm inner diameter as
the adapter body. A real φ60 envelope now runs continuously from the purchased
net-pot entrance, through the nominal-60 liner, common adapter and receiver,
and into the tower. The complete-port reference places the purchased net pot,
collapsed sleeve and root stop at their actual axial stations and reports
prohibited Boolean intersection volume rather than relying on diameter
arithmetic alone.

## DD-017 — Independent external M3 cartridges

The Phase 3A annular `port_adapter_retainer` cannot be removed through its own
φ72 receiver and is now
`DEPRECATED_NOT_EXTERNALLY_SERVICEABLE`. Its source and Phase 3A exports remain
unchanged for reproducibility, but Phase 3A.1 uses two independent side-load
M3 cartridges. Each cartridge has a roof and floor around the assumed 5.5 mm
AF metal nut, and each open receiver-lug slot is closed by a rigid gate whose
2.4 mm arm is captured by the normal M3 bolt. The cartridge, gate and slot
remain `CALIBRATION_PENDING` until external extraction, inverted retention and
wash tests pass.

## DD-018 — Root-ring passage and inner-end datum

The root-ring maximum diameter is controlled by a per-side passage-clearance
parameter. The selected value is 0.50 mm/side; 0.35 and 0.70 mm/side variants
remain on the coupon. Maximum diameter is measured from tessellated geometry,
including three rounded tabs. The ring's nominal plane is the adapter inner
end, and the flexible sleeve is folded around the ring so the ring withdraws
with the sleeve from the planting-port exterior.

A solid inward seat was evaluated and rejected because any ledge capable of
stopping a sub-66 mm rigid ring would violate the higher-priority requirement
for an uninterrupted 66 mm adapter bore. Phase 3A.1 therefore has no solid
seat or debris shelf inside that bore. Sleeve-fold axial retention remains a
physical `CALIBRATION_PENDING` gate; a future positive retainer must remain
separate/removable and must not be represented as a φ66 through-passage.

## DD-019 — Net-pot liner operating definition

The nominal-60 adapter is a tool-free, gravity-seated replacement liner. It
may withdraw together with the purchased net pot and may rotate during
cultivation without loss of function. No thin snap tabs are used. Insertion
and withdrawal force must be recorded on the net-pot adapter coupon after the
actual purchased pot is measured.

## DD-020 — Physical print failure changes the architecture

White PETG prints on the Bambu Lab A1 with a 0.4 mm nozzle showed a clear
split: large rings, annuli, arcs and broad continuous walls printed reliably;
small L-gates, M3/M4 cartridges, thin plates, narrow keys and the integrated
27-degree circular receiver failed by detachment, collapse, root fracture,
stringing or hole distortion. Phase 3R prioritizes print success over maximum
external serviceability. The old mechanisms remain reproducible but are
`DEPRECATED_AFTER_PRINT_FAILURE`.

## DD-021 — Wide three-key versus continuous six-lobe ring

| Criterion | A: three broad keys | B: continuous six-lobe wave |
|---|---|---|
| Flat printing | Good | Excellent; one continuous annulus |
| Root fracture | Much lower than old keys, but three stress concentrations remain | Lowest; no isolated key root |
| 0° / 60° seating | Achievable with repeated socket sectors | Exact 60° periodicity |
| 30° rejection | Three local collisions | Distributed real-shape collision |
| Load contact | Three local ribs plus annular face | Full circumference |
| Cleaning | Three transitions | Smooth continuous boundary |
| Material | Slightly lower | Slightly higher |
| Calibration | Separate key-width/root variables | One radial-clearance variable |
| Gasket coexistence | Requires sector coordination | Concentric separation is simple |
| Full-module implementation | Additional local unions | Separate flat rings |

Phase 3R selects **B, the continuous six-lobe wave ring**. CAD intersection is
zero at 0° and 60° and positive at 30°. The wave amplitude is 2 mm, the
continuous radial root is at least 15 mm, and the part is printed flat.

## DD-022 — Large annular M4 load and nut system

The Phase 2 M4 cartridges and L-gates are replaced by a 220 mm OD annular nut
ring, matching clamping ring, separate wave alignment rings and a flat gasket
carrier. Three metal nuts enter deep top-open hex pockets. Commercial washers
or a reference metal plate provide retention; no PETG snap or gate is used.
The ring has a 3 mm root-side floor and remains washable from the open pocket
side. Vertical load is carried by broad annular contact, not by M4 bolts alone.

## DD-023 — Integrated angled receiver versus split planting port

| Criterion | Integrated circular saddle | Split teardrop shell + flat ring |
|---|---|---|
| Shell print | Failed upper overhang and roundness | 45° self-supporting upper faces |
| Circular datum | Depends on vertical/angled shell print | Generated in a flat XY ring |
| Replacement | Whole module feature | Front ring/liner by ring unit |
| Hardware | Small external cartridges | Large internal C-ring nut plate |
| Cleaning | Saddle crevices | Broad drain gap and open root passage |
| Calibration | Coupled shell and adapter error | Shell and circular fit are separated |

The split design is selected. The shell opening is deliberately non-circular;
the flat `port_function_ring` owns roundness. A separate preliminary liner
owns the purchased-pot body fit.

## DD-024 — Serviceability is relaxed to remove small parts

The net pot, liner and front functional ring remain externally replaceable.
The large backing C-ring is serviced only after module disassembly. This is an
intentional relaxation of complete external replacement: fewer, larger,
flat-print parts are preferred over many fragile precision parts.

## DD-025 — Siawadeky and root-mesh assumptions

Only the Siawadeky maximum upper diameter, 78.5 mm, and height, 70 mm, are
image-derived. The preliminary body diameter is 72 mm solely to generate a
reference coupon; flange thickness, lower diameter, taper and rib envelope are
`CALIBRATION_PENDING`. The PP/PE vegetable mesh starts at 135 mm with a 20 mm
foldover and uses an 82 x 50 x 4 mm continuous root ring. Axial retention must
pass 500 g and 1 kg tests without adding snap tabs.

## DD-026 — Commercial hardware and gasket policy

Commercial M4 nuts, washers or thin metal plate references replace printed
micro-retainers. The retained module seal is solid φ3 mm EPDM cord in a
3.6 mm-wide groove with 2.0/2.2/2.4 mm depth calibration and a hard annular
stop. The cord is rejected if the purchased product is not a solid round
section. This remains a non-pressurized leak-reduction seal.

## DD-027 — Phase 3R.2 integrated-cylinder coupon aborted

`STATUS = ABORTED_BY_REQUIREMENT_CONFLICT`

`SUPERSEDED_BY = PHASE_3S_THREE_SECTOR_SPLIT_SHELL`

The Phase 3R.1 27-degree self-supporting opening cannot be preserved in full
inside the requested 80 mm maximum print height. Measured from the actual CAD,
the existing reinforcement frame has a 100.349 mm Z extent and the teardrop
void has a 113.650 mm Z extent. A nominal 75 mm cylindrical shell with the
proposed 0.8 mm sacrificial base would therefore still require approximately
101.15 mm overall height when the complete reinforcement frame is retained.

The 80 mm print-height limit and exact preservation of the existing opening,
reinforcement and 27-degree axis are geometrically incompatible. Cropping,
scaling or compressing the frame would no longer reproduce the validated
functional geometry, so neither an 80 mm cropped coupon nor the approximately
101.15 mm integrated-cylinder compromise is authorized.

The full integrated cylindrical shell architecture is also discontinued
because its tall, low-contact vertical print has an unacceptable production
success rate. Phase 3S will replace it with three 120-degree shell sectors
designed for lower print height and broader bed contact, then assemble the
sectors with upper and lower annular rings. Phase 3R.2 produces no CAD, STEP,
STL or coupon artifact.

## DD-028 — Phase 3S-A uses three identical chord-down shell sectors

Phase 3S-A divides the nominal φ200 x 170 mm shell into three identical
120-degree replaceable panels. The assembled planting-port centers are
0/120/240 degrees and the vertical seams are 60/180/300 degrees. Each panel
uses the Phase 3R.1 structural teardrop opening and 27-degree port axis; the
separate flat function ring remains the owner of circular net-pot datums.

For printing, assembly Y maps to print X, assembly Z maps to print Y, and
assembly radial X maps to print Z. Two permanent full-height seam rails share
one plane parallel to the sector chord and provide 5100 mm2 real bed contact.
The measured full-panel print envelope is approximately
182.689 x 170.000 x 78.741 mm. The rails remain as washable seam structure
after printing and are not sacrificial feet.

The left edge is a broad external cover and the right edge is an inner
receiver with an inward drip return. The simple two-stage labyrinth does not
claim watertightness. Clearances 0.4/0.6/0.8 mm remain
`CALIBRATION_PENDING`; no snap, cartridge, vertical gasket or small retainer
is introduced.

Identical temporary flat rings hold the upper and lower panel datums for
roundness and short water tests. They contain no final wave stack, M4 nut
system or production fastener decision. Drainage, irrigation, the five-stage
tower and final net-pot liner remain outside Phase 3S-A.

## DD-029 — Phase 3P-A measured net-pot envelope supersedes image assumptions

Physical measurement found a 108.0 mm flange, substantially larger than the
former image-derived 78.5 mm assumption. The maximum body and maximum rib
outside diameters are both 78.6 mm, so the measured ribs add no further radial
projection to the conservative body envelope. The earlier 72.0 mm preliminary
body and 78.5 mm flange values remain in the source solely to reproduce old
artifacts and are rejected as final design inputs.

The replaceable liner, not the flange perimeter, will own body centering. A
flange-only datum would couple centering to a broad, potentially flexible
108 mm molded rim and would not directly control the 78.6 mm body that passes
through the opening. The Phase 3P-A 80.0/80.5/81.0 mm flat coupons therefore
calibrate only body passage and flange seating; no final liner is generated.

The circular functional ring remains a separate flat-printed part because it
provides a controlled circular seat independently of the split panel opening,
prints without small vertical retainers, and remains replaceable. Its final
M4 positions must be redesigned and re-audited: the existing 50 mm-radius axes,
bolt/washer/head envelopes, tool access and finger access overlap the measured
54 mm flange radius. Any redesign must also retain the 27-degree port axis,
minimum 3 mm structural material and the 240 mm maximum module diameter.
Reference comparisons of 116, 120 and 124 mm ring envelopes do not constitute
a final ring selection or authorize panel integration.

At the unchanged Phase 3R.1 seat datum and 27-degree axis, exact B-rep audit
of the measured conservative pot envelope produces a 241.215 mm installed
maximum diameter and 4,788.534 mm3 of shell/frame intersection. This is a
reference audit result, not authorization to push the pot into the shell.
The ring, port opening, root-zone interface and fastening scheme therefore
remain `REDESIGN_REQUIRED`; measured dimensions and the 27-degree axis are not
altered to make the legacy geometry pass.
