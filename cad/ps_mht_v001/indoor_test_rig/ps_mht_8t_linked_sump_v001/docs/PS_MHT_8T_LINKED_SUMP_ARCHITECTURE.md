# PS-MHT-8T-LINKED-SUMP-V001 Architecture

Status: `ARCHITECTURE_AND_REFERENCE_CAD_COMPLETE`  
Physical component state: `PHYSICAL_COMPONENT_MEASUREMENT_PENDING`

## Purpose and authority

This zone supports an initial four-tower indoor trial and later six- and
eight-tower trials with one circulation pump. Each tower drains openly into
its own low-profile local sump. All local sumps connect independently to a
common equalization trunk. The purchased PP/PE sumps, pump well, bulkheads,
EPDM gaskets, union ball valves and hose are the watertight authority.

All Phase 4T-LS-A CAD is `REFERENCE_ONLY`. It defines envelopes, topology,
service access and load paths. It is not a printable or watertight-part
definition. No STL or final print part is authorized.

## Adopted daytime path

```text
common pump well
  -> one circulation pump
  -> always-available discharge bypass
  -> eight-way upper manifold
  -> independent upper valve A..H
  -> open discharge at each tower top
  -> gravity flow through tower
  -> local sump A..H
  -> independent equalization valve A..H
  -> common equalization trunk
  -> common pump well
```

Every sump branch terminates independently at the common trunk. A serial
`sump A -> sump B -> sump C` return is prohibited. Isolating one branch must
not disconnect another branch downstream.

For the four-tower trial, branches A-D are active and E-H remain hydraulically
closed. Closure means isolation from the nutrient trunk, not sealing a sump
airtight. Every sump remains atmospheric or uses a vented light-blocking lid.

## Local sump reference

- Purchased PP or PE, gross 12-16 L; 16 L preferred.
- Normal volume 5-7 L.
- Emergency freeboard at least 4 L; 6 L preferred.
- Outer height 110-130 mm.
- Reference footprint 420 x 320 mm and envelope height 120 mm.
- Reference normal depth 40-55 mm; maximum operating depth 75-85 mm.
- Openable top, opaque/covered but vented, visible LOW/NORMAL/HIGH indication.
- Fully drainable and laterally removable for sediment inspection.
- No inaccessible closed cavity at the bottom.

The tower drains into the sump by an open fall. The sump neither supports the
tower nor carries hose or valve loads.

## Dry tower support

A dry four-corner frame, cross rails and load-distribution plate take tower
load directly to the floor. The support deck reference elevation is 170 mm
(allowable study range 160-180 mm); the tower-bottom outlet is 205 mm
(190-220 mm). A 20 kg tower is used only for load-path sensitivity. Final
capacity requires an actual tower mass and stability audit.

## Equalization and emergency systems

Each equalization branch uses at least 25 mm ID, preferably 32 mm. The common
trunk uses at least 32 mm ID, preferably 40 mm. Trunk slopes 0, 1/200 and 1/100
remain comparison candidates. Both ends or an end must provide brush/flush
access, with a low-point drain and independently supported protected route.

Each sump also has a separate HIGH overflow of at least 25 mm ID, preferably
32 mm. It drains to a normally dry safety trough and then a non-circulating
emergency receiver. It never reconnects to the equalization trunk or pump
well.

## Pump and delivery

The purchase reference is a Tencen DC12 V, 20 W submersible pump marked
700 L/h maximum flow and 6 m maximum head with a nominal 13 mm nipple. The
700 L/h value is near zero head and does not qualify six- or eight-tower
operation. Actual head, voltage, current, branch flow, CV, bypass flow and
drawdown must be measured at 4, then 6, then 8 towers.

The pump discharge tees to the upper eight-way manifold and an always-open
safety bypass to the common pump well. Closing all tower branches must never
dead-head the pump. Tower-top delivery is open to atmosphere to avoid siphon
and reverse flow.

## Fresh-water separation

The upper 10 L fresh-water tank is separate from the shared nutrient zone. It
supports make-up water and deliberate fresh-water flushing only. At night
`fresh_water_to_tower = CLOSED`. Its independent shelf is nominally 1700 mm;
the tank top must stay at or below 2050 mm under the confirmed 2300 mm ceiling,
leaving at least 250 mm. Its load is not placed on a tower.

## Shared-zone constraint

All connected towers share EC, pH, fertilizer, root exudates, algae,
microorganisms and pathogen risk. Different fertilizer concentrations or
treatment conditions must not share one zone. Suspected disease requires
immediate branch isolation; the local sump is cleaned before reconnection.
Cleaning does not reduce transmission risk to zero. One pump serving up to
eight towers is one management zone.

## Explicit exclusions

This phase does not finalize a tank, bulkhead hole, support adapter, valve,
hose fitting, pump mount, strainer or printed component. Printed sliding
valves, printed-thread-only watertight fittings, small PETG check valves and a
split PETG 15 L watertight tank are prohibited.
