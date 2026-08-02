# PS-MHT Capillary Buffer Architecture

Phase: **3CB-0 — Architecture audit only**  
Status: **CONFLICT_FOUND**  
CAD/STEP/STL/print plates: **NOT GENERATED**

## 1. Architectural intent

The capillary element is not a circulation engine. A short pump cycle raises
nutrient solution from the common lower recovery tank to a removable upper
distribution tank on each tower. Gravity then feeds five planting modules.
Each module holds a shallow, inspectable buffer and uses short replaceable
wicks to bridge that buffer to the growing medium. Excess solution returns by
independent overflows to the lower tank.

The architecture therefore has two energy domains:

1. Pump on: lift, distribute, flush, mix and restore buffer levels.
2. Pump off: retain moisture locally by capillary transport without claiming
   upward circulation.

It also has two structural load paths:

- The nominal 200 mm PETG planting stack carries its own modules and plants.
- The aluminium support carries every 3/4/5 L upper tank, hose reaction and
  service load. Upper-tank weight must not enter the PETG shell.

## 2. Water path

`common lower tank -> screened pump -> four branches -> upper tanks ->
top modules -> module buffers/wicks -> module overflows -> next modules ->
common return -> settling zone -> coarse screen -> pump zone`

Every module requires a visible, cleanable overflow. A root screen is a
service item, not a guarantee against blockage. The primary overflow must be
at least a 12 mm-ID test candidate; 16 mm ID is the preferred first hydraulic
coupon because canal water, precipitate, algae and fine roots are credible.

## 3. State model

| State | Pump | Upper tank | Module buffers | Lower tank | Required behavior |
|---|---|---|---|---|---|
| FILL/FLUSH | On | Filling, then overflowing | Refilled and mixed | Falling toward minimum level | No branch starvation; overflow capacity exceeds branch inflow |
| GRAVITY FEED | Off or transition | Draining by metered outlets | Receiving solution | Recovering return | No siphon capable of emptying an unintended tank |
| CAPILLARY HOLD | Off | May be empty | Retains a calibrated volume | Stable | Wicks wet media; pot is not continuously submerged |
| ABNORMAL HIGH LEVEL | On/off | Emergency overflow active | Primary overflow may be restricted | Receives maximum free return | No external continuous leak; no shell loading by tank |
| POWER LOSS | Off | Free-draining volume returns | Only intended residual remains | Accepts free return | Common tank has verified usable capacity and freeboard |
| CLEANING | Locked out | Removed from support | Bands/tray open and drained | Pump removed tool-free | Drain, screen, wick and flow control are directly accessible |

## 4. Tank roles

### Upper distribution tank

- Batch/level buffer that decouples pump flow from gravity branch flow.
- Removable, opaque and lidded, with a visible serviceable outlet and
  emergency overflow.
- Candidate gross volumes are 3, 4 and 5 L; none is selected.
- Four towers therefore suspend 12, 16 or 20 L of water above the crop, plus
  tank and hardware mass, on aluminium supports.

### Module capillary buffer

- Short-duration moisture reserve, not a deep-water culture bath.
- Independently overflows and drains; water level remains below the net-pot
  body in normal operation.
- Candidate target volumes are 0.4, 0.6 and 0.8 L per module. The 0.8 L value
  conflicts with a 25 mm maximum water depth even before internal exclusions
  and cannot be treated as geometrically feasible.

### Common lower recovery tank

- Combines four returns, provides pump submergence, settling and coarse
  screening, and accepts the maximum credible free return.
- Gross label capacity is not usable capacity. Pump dead volume, sediment
  zone and freeboard must be measured.
- 40, 50 and 60 L remain comparison candidates. The architecture audit does
  not select one.

## 5. Flow-control comparison

| Method | Clogging exposure | Balance adjustment | Cleaning | Audit position |
|---|---|---|---|---|
| 0.8–1.5 mm replaceable orifice | High; area is only 0.503–1.767 mm² | Repeatable after calibration | Requires removal and gauge check | Coupon comparison only; never below 0.8 mm |
| Transparent tube + pinch valve | Larger water path; visible deposit | Continuously adjustable | Flushable/replacable | Preferred first system comparison, shield from light in service |
| Standpipe/overflow weir | Low pressure sensitivity | Set by level | Large accessible geometry | Preferred for upper-tank abnormal overflow |
| Replaceable nozzle | Medium to high | Discrete sizes | Serviceable if large and keyed | Secondary candidate, no micro printed key |

At equal pressure, ideal orifice flow scales with area. Relative to 0.8 mm,
the 1.0/1.2/1.5 mm candidates have 1.56/2.25/3.52 times the area. Those ratios
do not account for debris and are not flow promises.

## 6. Controls, pump and battery

Pump power and flow are measured at the actual four-branch static head with a
DC integrating wattmeter. The controller records pump voltage, current,
runtime, upper-tank fill time and lower-tank level. DC-DC loss, timer standby,
sensor duty cycle and cold battery derating are separate budget lines.

The nominal 20 W and 80 min/day example gives 26.7 Wh/day pump energy. A
40–50 Wh/day total is a test target, not an achieved result. A 12-hour night
stop is introduced only after shorter hold tests pass.

## 7. Cleaning architecture

- Horizontal bands are individually removable after the module is drained.
- No enclosed buffer cavity is accepted without a removable top or a hand/tool
  access opening.
- The drain reaches the actual low point and passes visible solids.
- Root screens slide out toward a clear service side; roots may not have to be
  pulled through a small hole.
- Wick retention uses a broad removable plate, large ring, commercial grommet
  or commercial tie. Small PETG clips, claws, snaps and cartridges remain
  prohibited.
- Printed walls provide shape and a water-return path; replaceable gasket,
  liner or secondary containment owns long-duration leak control.

## 8. Architecture conflicts and disposition

1. A 194 mm internal circle contains only 0.739 L at 25 mm depth before pot,
   root, rod, overflow, drain and baffle exclusions. Therefore 0.8 L at
   15–25 mm is impossible as stated.
2. The measured pot at the fixed 27-degree Phase 3R.1 datum produces a
   241.215 mm installed envelope, exceeding the immutable 240 mm limit.
3. Existing M4 port axes and service envelopes overlap the measured flange;
   horizontal stacking must not reuse that fastener layout.
4. A four-tower trial that changes circulation, medium and wick simultaneously
   cannot attribute an observed difference to the circulation architecture.

No numerical input is silently changed. Phase 3H-A and Phase 3CB-A may begin
only as isolated coupons after their entry conditions are approved. Integrated
Phase 3H-B remains blocked until the joint, tray, hydraulic and pot-envelope
conflicts are resolved.

## 9. Scaling to 80 towers

The four-tower rig is a hydraulic and agronomic experiment, not a 1:20
production manifold. Scaling requires branch zoning, isolation valves, fault
containment, tank redundancy, service routes and measured diversity factors.
At 3/4/5 L per upper tank, 80 towers would suspend 240/320/400 L of water.
This alone prevents direct replication of a light four-tower support detail.
No 80-tower components are authorized by Phase 3CB-0.

## 10. Next-phase split, entry and stop gates

| Phase | Start condition | Stop condition |
|---|---|---|
| Phase 3H-A — Horizontal Ring Joint Calibration | Joint datum, 0.3/0.5/0.7 mm candidates, compression load and leak/cycle protocol approved; planting holes excluded | Any path needs <3 mm wall, exceeds 240 mm, occupies root/service space, or no joint passes leak/cycle/cleaning |
| Phase 3CB-A — Capillary Buffer Tray Coupon | Effective-area budget, candidate target volumes, verified inflow test range and removable wick/screen/drain paths declared | Claimed volume exceeds measured volume, pot must be submerged, overflow <150% of verified inflow, or tray cannot be inspected/drained |
| Phase 3CB-B — Top Tank and Flow Control | Aluminium support load cases, actual pump head-flow range, 3/4/5 L and flow-control test matrix declared | Tank load reaches PETG shell, control cannot be cleaned, or four branches cannot be balanced |
| Phase 3CB-C — Four-Tower Hydraulic Mock-up | Tray/top-tank candidates pass, lower usable volume exceeds measured return, wattmeter and rescue procedures installed | Uncontained overflow/electrical hazard, insufficient return capacity, repeated starvation or complete blockage |
| Phase 3H-B — Integrated Horizontal Stack Module | 3H-A joint, 3CB-A tray and net-pot passage selected; pot/fastener design meets 238 mm target and 240 mm hard limit | Requires changing measured pot/27-degree axis, exceeds 240 mm, or is not cleanable, disassemblable and A1-printable |

These gates authorize only their named scope. Passing Phase 3H-A does not
authorize an integrated planting module before the other Phase 3H-B entry
conditions are also satisfied.
