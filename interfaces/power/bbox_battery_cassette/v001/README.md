# PS-BBOX-CASSETTE-V001

Status: DOCUMENTATION_CANDIDATE_ONLY

This directory defines the interface contract for a Paddy Swarm-specific,
direct-swap BBOX battery cassette. Commercial waterproof-box compatibility is
removed by project decision. No battery, connector, gasket, vent, BMS, charger,
voltage, capacity, current rating, manufacturing operation, purchase, or field
deployment is selected or approved here.

## Repository basis and bounded scope

The declared C:\Paddy_Swarm_Project path was absent during the audit. The
available D:\Paddy_Swarm_Project worktree was clean but was on main at
e25590724d66ce499122fc9d8760fd83555744b8, not the expected branch and HEAD.
The expected commit was nevertheless available locally and verified at
refs/remotes/origin/software/station-control-foundation:

    b16aded01102f94a9e718f4165c5e098d846c8c6

All engineering evidence was read from that commit through read-only Git object
queries. No branch switch, index write, network access, package installation,
tracked-file edit, or hardware action was performed. The requested Battery Mule
v001 and battery-mule motor-selection v003_1 lanes do not exist in that commit
or the available worktree; their missing geometry is an explicit evidence gap.

The fallback interface path is used because the intended revision contains no
general interface directory with an applicable naming convention. Exactly five
source files belong to this add-only lane.

## Repository geometry carried into this contract

The v2.28 evidence fixes a repository-native coordinate system:

- X is lateral: negative X is left and positive X is right.
- Y is longitudinal: negative Y is front/forward and positive Y is rear/aft.
- Z is vertical: positive Z is upward.

The existing BBOX is the front box and the CBOX is the rear box. They remain in
front/rear series, never side-by-side. Each current box body is 200 mm wide in X,
150 mm front/back in Y, and 120 mm high in Z. The current lid reference is
216 x 166 x 16 mm and the gasket reference is 204 x 154 x 3 mm. These are audit
facts, not new cassette dimensions. This phase changes no CAD dimension.

The fixed-core relationships preserved are the LOWER-FRAME, WBASE side rails,
upper split turtle shell, left/right upper side-wall motor pod mounts, high
forward dual PTO, lower belly hull, water/mud exposure assumptions, and the CBOX
as the protected dry control core.

The current BBOX/CBOX front/rear faces contain top-open wire-drop notches whose
repository documentation explicitly says they are only drip-resistant helpers.
The new contract does not treat those notches as a battery interface or a
waterproof barrier.

## Three-layer architecture

1. BBOX-FRAME is fixed to the rover. It carries cassette, impact, recovery, and
   vehicle loads into the LOWER-FRAME and supports the cradle, latches, and
   connector module. It is not exchanged routinely.
2. BBOX-WET-CRADLE is a drainable water/mud-tolerant service zone. It guides,
   seats, keys, retains, wipes, drains, and exposes wear parts for inspection.
   It is not claimed to remain dry.
3. BBOX-BATTERY-CASSETTE is the only routine exchange item. It has its own
   continuous primary waterproof enclosure, recessed interface, fuse, BMS,
   contactor, sensing, identity, pressure-management candidates, bumpers, skid,
   and transport handle.

The cassette load path is cassette body to bottom structural seat to side guide
and wear rail to primary latch to BBOX-FRAME to LOWER-FRAME. The connector sees
mate and unmate force only. Connector pins, shells, terminals, gasket friction,
and seal compression never locate, suspend, or retain the cassette.

## Dirty, wet, and dry boundaries

The ordered zones are:

| Zone | Name | Contract |
|---|---|---|
| D0 | EXTERNAL_DIRTY_ENVIRONMENT | Rain, mud, paddy water, debris |
| D1 | DIRTY_ENTRY_ZONE | Coarse wiping, scraping, inspection |
| D2 | DRAINABLE_WET_CRADLE | Water allowed; pooling prohibited |
| D3 | CONNECTOR_PROTECTION_VESTIBULE | First barrier, moat, sensing, second seal |
| D4 | CONNECTOR_DRY_CHAMBER | Recessed power, signals, ID, pre-charge |
| D5 | CBOX_DRY_CORE | Fixed sealed bulkhead; no shared cavity or drain |

Water from D0, D1, or D2 may not reach D4 or D5. Water, moisture, sensor fault,
or unknown sensor state at D3 blocks energization. Water detection is an
interlock, not a primary seal.

The connector interface is ordered from outside to inside as contamination
shield, replaceable wiping lip, first labyrinth, drain moat, water-detection
zone, secondary compression gasket, connector dry chamber, and recessed
contacts. A single seal or a connector product's claimed sealing alone is not
accepted.

All cradle and moat drainage is by inspectable, cleanable, large gravity paths
directed away from the CBOX and dry chamber. No drain may share a CBOX
feedthrough, empty under the CBOX or connector, or terminate in a blind lower
hull pocket.

## Insertion and connector decision

VERTICAL_TOP_INSERTION is the baseline: insertion is in negative Z and removal
is in positive Z. Exchange in water, deep mud, rice rows, a SOFT_TRAP, an
unstable floating state, or with motion/PTO/motors energized is prohibited.

UPPER_REAR_HORIZONTAL_CONNECTOR_SHUTTLE is recommended for the next CAD study.
It uses the high interface between the front BBOX and aft CBOX, gives the
shortest candidate fixed CBOX feedthrough, avoids both high side motor-pod
zones, and decouples vertical cassette handling from horizontal mating.
UPPER_LEFT and UPPER_RIGHT remain alternatives only.

This is not a final CAD location. The existing BBOX rear notch, CBOX front
notch, shell opening, 150 mm front/back envelope, fixed bulkhead, latch access,
drain fall, cable bend, and shuttle service sweep all require measurement.
No present BBOX dimension is modified in this phase.

The shuttle remains retracted during insertion. It may advance only after
structural seating, primary latch, independent safety latch, latch-sensor
agreement, and dry sensor states. Its stroke, connector, force, seal material,
and compression are open parameters. A floating mount absorbs only residual
alignment after cradle guides, tapered lead-ins, asymmetric keys, datum pads,
and structural seats do the gross work.

## Electrical contract

Traction hot-swap is prohibited. An absent cassette and a removed cassette are
dead-front: the cassette contactor is open, output contacts are not energized,
the rover connector is retracted, and the rover traction bus is isolated.

The controlled sequence is seating, both latches, sensor agreement, dry check,
shuttle advance, secondary seal compression, low-energy signal, identity,
compatibility, voltage/polarity/temperature checks, pre-charge, voltage
convergence, main contactor close, low-power self-test, and drive authorization.

The 25 canonical states are:

    ABSENT, INSERTING, SEATED_UNLATCHED, PRIMARY_LATCHED,
    SAFETY_LATCHED, WET_CHECK, WET_FAULT, CONNECTOR_ADVANCING,
    SIGNAL_CONNECTED, IDENTITY_CHECK, COMPATIBILITY_CHECK, PRECHARGE,
    PRECHARGE_FAILED, READY_TO_ENERGIZE, ENERGIZED, RUNNING,
    DEENERGIZING, CONNECTOR_RETRACTING, REMOVAL_AUTHORIZED, FAULT,
    OVERTEMPERATURE, OVERVOLTAGE, UNDERVOLTAGE, POLARITY_FAULT,
    UNKNOWN_CASSETTE

ABSENT, an unlatched state, WET_FAULT, half-mate, unknown identity, incompatible
class, failed pre-charge, or any fault cannot reach ENERGIZED or RUNNING.
REMOVAL_AUTHORIZED requires contactor-open proof, discharged bus, full shuttle
retraction, and electrical-disconnect proof before either latch can release the
cassette.

A small keep-alive or hold-up supply is a candidate for CBOX state retention.
It is not a traction source and remains unselected.

## Identity, Mule, rack, and fleet

Compatibility uses mechanical coding plus cassette identity, hardware revision,
battery class, voltage class, capacity class, charge profile, and BMS revision.
Software identity alone cannot prevent wrong orientation, voltage, chemistry,
connector family, service cassette, damaged cassette, or partial insertion.

The same cassette-side interface is the target for rover, Battery Mule transport,
and charging rack. A Mule propulsion cassette is never delivery inventory. Mule
bays are physically separated into charged clean, returned dirty, and fault
quarantine functions. Because the requested Mule repository lane is absent,
this is contractual compatibility only and not a Mule geometry validation.

The rack runs EMPTY, RETURNED_WARM, COOLING, INSPECTION, WET_FAULT, IDENTIFIED,
CHARGING, CHARGE_COMPLETE, READY, RESERVED, FAULT, and QUARANTINE states. It
cannot charge immediately after insertion; seating, latch, dry, identity,
compatibility, temperature, and isolation-candidate checks precede permission.

For 30 rovers the interface supports cassette inventory, separation, reservation,
assignments, swap queues, staggered starts, health exclusion, priority,
emergency reserve, override, and audit logging. Fleet selection never bypasses
local mechanical or electrical interlocks. Cassette and charger quantities
remain open.

## Human swap baseline

The allowed baseline locations are a dry field-edge pad, stable leveled service
area, or workshop test stand. A dry stable levee is conditional. The canonical
32-step sequence appears in the interface-control document and JSON contract.
Any abnormal step fails closed.

## Validation and use boundary

Only Stage 0 document/contract validation is completed by this lane. Stages 1
through 10 require separate authorization and start with inert geometry and
unenergized water testing before any low-voltage, load, sealed-battery, rover,
field-edge, Mule, or future semi-automatic work.

The authoritative values, states, zones, sequences, ownership, FMEA coverage,
open parameters, validation stages, approval flags, and artifact rules are in
PS_BBOX_CASSETTE_V001_INTERFACE_CONTRACT.json. The standard-library test module
validates the contract, runs the required mutation set, and can generate the
deterministic review bundle.

Manufacturing readiness: NOT_APPROVED

Purchase approval: NOT_APPROVED

Field deployment: NOT_APPROVED
