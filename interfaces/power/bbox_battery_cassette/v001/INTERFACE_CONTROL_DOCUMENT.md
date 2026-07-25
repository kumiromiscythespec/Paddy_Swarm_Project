# PS-BBOX-CASSETTE-V001 Interface Control Document

Status: DOCUMENTATION_CANDIDATE_ONLY

Version: v001

This ICD controls names, ownership, boundaries, datums, sequence, and fail-safe
behavior. It is not a CAD drawing, pinout, wiring instruction, product
selection, manufacturing release, purchase release, or field-use approval.

## 1. Controlled interface and coordinate frame

The controlled interface is between the fixed rover BBOX-FRAME, its serviceable
BBOX-WET-CRADLE, the exchanged BBOX-BATTERY-CASSETTE, the fixed CBOX sealed
feedthrough, the Battery Mule transport rack, and the charging rack.

Repository-native axes govern all later CAD work:

- X: lateral; negative left, positive right.
- Y: longitudinal; negative front/forward, positive rear/aft.
- Z: vertical; positive upward.
- Cassette insertion: negative Z.
- Cassette removal: positive Z.

No dimension in this document changes v2.28 CAD. Existing 200 x 150 x 120 mm
BBOX/CBOX bodies, their front/rear serial arrangement, LOWER-FRAME, WBASE,
turtle shell, high side motor-pod, and high forward dual-PTO relationships are
reference constraints.

## 2. Controlled names and ownership

| Owner | Controlled responsibility |
|---|---|
| CASSETTE | Containment, fuse, BMS, contactor, ID, temperature, primary enclosure seal, recessed mating port, pressure management |
| ROVER BBOX | Frame, wet cradle, drain, guide, primary latch, safety latch, sensors, shuttle, CBOX feedthrough, vehicle interlock |
| CBOX | Keep-alive candidate, state authority candidate, bus monitoring, drive authorization, event log |
| BATTERY MULE | Clean/dirty separation, retention, delivery tracking, reserve protection |
| CHARGING RACK | Cooldown, inspection, charge authorization, charge, quarantine, inventory |

The CBOX owns no wet-cradle volume. The connector owns no cassette structural
load. Fleet software owns no local safety bypass.

## 3. Three controlled layers

### 3.1 BBOX-FRAME

The frame is fixed. It carries the body, cassette, impact, vibration, recovery,
latch, and cradle reactions to the LOWER-FRAME. It supports but does not use the
connector as a structural member. It retains the front BBOX/rear CBOX central
core and preserves the upper shell, motor-pod, PTO, WBASE, and hull
relationships.

### 3.2 BBOX-WET-CRADLE

The cradle is a wet, dirty, gravity-drained service volume. It provides tapered
lead-in, asymmetric mechanical coding, wear rails, structural seat, latches,
wiper, drain access, and inspection access. Water entry is allowed; pooled
water, a blind pocket, a capillary path to the connector, or a route to the
CBOX is not.

### 3.3 BBOX-BATTERY-CASSETTE

The cassette is the only routine exchange item. Its continuous enclosure and
service-lid gasket are the primary waterproof barrier. The service lid remains
closed during routine exchange. The cassette provides a recessed port,
pressure-equalization candidate, abnormal vent path away from CBOX, connector,
and hand position, sealed fastener paths, keying, bumpers, skid, and handle.
The printed outer shell alone is not battery-fire containment.

## 4. Zone boundary control

| From | To | Normal mechanism | Energization rule |
|---|---|---|---|
| D0 external dirty | D1 entry | Shield, wiper, scraper | No electrical claim |
| D1 entry | D2 wet cradle | Debris shedding and open drain | Pooling prohibited |
| D2 wet cradle | D3 vestibule | First labyrinth and contamination barrier | Inspect and sense |
| D3 vestibule | D4 dry chamber | Moat, water sensing, secondary compression gasket | D3 water, moisture, fault, or unknown blocks power |
| D4 dry chamber | D5 CBOX dry core | Fixed sealed bulkhead feedthrough | No shared cavity or drain |

D0/D1/D2 water may not reach D4/D5. D3 is a protection and detection zone, not
a permission to tolerate energized water. D4 and D5 are dry-required zones.

## 5. Connector and seal control

The selected documentation baseline is
UPPER_REAR_HORIZONTAL_CONNECTOR_SHUTTLE. It is a candidate at the high BBOX/CBOX
boundary and must remain retracted while the cassette moves vertically.
UPPER_LEFT and UPPER_RIGHT are alternates only because the repository preserves
high left/right motor-pod zones. Bottom blind-mate is prohibited.

Outside-to-inside barrier order:

1. coarse contamination shield;
2. replaceable wiping lip;
3. first labyrinth;
4. drain moat;
5. water-detection zone;
6. secondary compression gasket;
7. connector dry chamber;
8. recessed electrical contacts.

The first seal wipes mud and reduces splash and debris. It is not the primary
electrical waterproof barrier. The secondary gasket and dry chamber protect the
electrical interface. Seal target compression remains
TBD_BY_GASKET_SELECTION; uniform compression is required and both over- and
under-compression are prohibited.

The shuttle has a short horizontal stroke, cam or lever candidate actuation,
floating final alignment, replaceable connector module, and replaceable seal
module. Product, stroke, force, pin count, current, voltage, materials, sealing
claim, and compression are open.

## 6. Mechanical datum and tolerance control

| Datum | Definition | Primary use |
|---|---|---|
| DATUM A | Cassette bottom structural seat plane | Z seating and mass reaction |
| DATUM B | Cassette rear alignment plane | Y registration |
| DATUM C | Cassette lateral key plane | X registration and coding |
| DATUM D | Connector mating plane | Residual alignment and seal control |
| DATUM E | Handle/lift center reference | Manual or assisted lift planning |

Coarse alignment belongs to guides, tapered lead-in, and asymmetric keying.
Fine alignment belongs to datum pads, the floating connector mount, and a short
shuttle stroke. Structural retention belongs to seat, rail, and latch. Seal
compression belongs to the cam/shuttle. Printed dimensions or connector pins
alone cannot correct the tolerance stack.

Mechanical load path:

    cassette body
    -> bottom structural seat
    -> side guide and wear rail
    -> primary latch
    -> BBOX-FRAME
    -> LOWER-FRAME

Connector load path:

    controlled mate force
    -> controlled unmate force

## 7. Latch and removal interlock

Three independent forms of evidence are required:

1. primary structural latch;
2. independent safety latch;
3. electronic seated/latch detection with agreement checks.

The shuttle cannot advance until both latches and their required sensors are
valid. A remaining latch must prevent a cassette drop. The handle cannot
casually actuate a latch.

Removal order is fixed:

1. stop traction and PTO;
2. open main contactor;
3. prove bus below the approved threshold;
4. retract connector shuttle;
5. prove electrical disconnect and full retraction;
6. release safety latch;
7. release primary latch;
8. grant REMOVAL_AUTHORIZED;
9. lift in positive Z.

Any welded-contactor indication, unexpected bus voltage/current, half-mate,
sensor disagreement, water state other than DRY, or failed retraction leaves
the cassette mechanically retained and enters a fault state.

## 8. Electrical sequence

Traction hot-swap is prohibited. The removed cassette is REMOVED_SAFE:
contactor open, external output unenergized, internal energy isolated, fault
state retained. The rover side is retracted and isolated. A keep-alive/hold-up
candidate may preserve CBOX communications and logs; it cannot drive traction.

Energization sequence:

1. cassette insertion;
2. guide positioning;
3. structural seat;
4. primary latch;
5. safety latch;
6. latch sensor agreement;
7. water sensor acceptance;
8. connector shuttle advance;
9. secondary seal compression;
10. low-energy signal connection;
11. cassette identity;
12. voltage, polarity, and temperature check;
13. pre-charge;
14. voltage-difference convergence;
15. main contactor close;
16. drive authorization.

Power contacts never prove presence or latch. Current alone never proves full
mate. Unknown ID, wrong voltage class, wrong chemistry/profile, invalid
polarity, over/under-voltage, overtemperature, wet state, sensor fault, sensor
unknown, or pre-charge failure blocks the contactor.

## 9. State machine control

The 25 controlled states are:

| Group | States |
|---|---|
| Mechanical entry | ABSENT, INSERTING, SEATED_UNLATCHED, PRIMARY_LATCHED, SAFETY_LATCHED |
| Wet/connection | WET_CHECK, WET_FAULT, CONNECTOR_ADVANCING, SIGNAL_CONNECTED |
| Qualification | IDENTITY_CHECK, COMPATIBILITY_CHECK, PRECHARGE, PRECHARGE_FAILED, READY_TO_ENERGIZE |
| Operation/removal | ENERGIZED, RUNNING, DEENERGIZING, CONNECTOR_RETRACTING, REMOVAL_AUTHORIZED |
| Faults | FAULT, OVERTEMPERATURE, OVERVOLTAGE, UNDERVOLTAGE, POLARITY_FAULT, UNKNOWN_CASSETTE |

Nominal path:

    ABSENT -> INSERTING -> SEATED_UNLATCHED -> PRIMARY_LATCHED
    -> SAFETY_LATCHED -> WET_CHECK -> CONNECTOR_ADVANCING
    -> SIGNAL_CONNECTED -> IDENTITY_CHECK -> COMPATIBILITY_CHECK
    -> PRECHARGE -> READY_TO_ENERGIZE -> ENERGIZED -> RUNNING
    -> DEENERGIZING -> CONNECTOR_RETRACTING
    -> REMOVAL_AUTHORIZED -> ABSENT

Prohibited direct or effective transitions include ABSENT to ENERGIZED,
unlatched to ENERGIZED, WET_FAULT to ENERGIZED, half-mated to ENERGIZED,
unknown cassette to RUNNING, any compatibility fault to ENERGIZED, and
ENERGIZED/RUNNING to REMOVAL_AUTHORIZED. Fault recovery requires correction,
inspection, and deliberate reset; power or communication restoration never
automatically resumes.

## 10. Water sensor control

Controlled sensor states are DRY, MOISTURE_DETECTED, WATER_PRESENT,
SENSOR_FAULT, and UNKNOWN. Only DRY may participate in energization permission.
Candidate sensor positions are the moat, vestibule low point, dry-chamber lower
boundary, and CBOX feedthrough outer pocket. A sensor does not replace either
waterproof barrier.

## 11. Identity and mechanical coding

Each cassette carries unique ID, hardware revision, battery class, voltage
class, capacity class, charge profile, BMS revision, manufacturing lot, cycle
count, hours, maximum temperature, fault history, water-exposure flag, service
and quarantine states, SoC, and health proxy. Drop-event history is a candidate.

Mechanical coding must make or help detect front/rear reverse, left/right
reverse, upside-down insertion, service cassette, wrong connector family,
damaged cassette, and partial seating. Electrical qualification independently
checks identity, voltage, chemistry/profile, temperature, and polarity.
Software ID alone is insufficient.

## 12. Standard human swap sequence

1. Receive swap request.
2. Move to dry swap pad.
3. Stop rover.
4. Apply wheel restraint.
5. Stop PTO.
6. Set selector NEUTRAL.
7. Open main contactor.
8. Confirm bus discharge.
9. Open upper shell.
10. Clean cassette top.
11. Retract connector shuttle.
12. Confirm electrical disconnect.
13. Release safety latch.
14. Release primary latch.
15. Remove cassette vertically in positive Z.
16. Visually inspect connector vestibule.
17. Check water and mud.
18. Put dirty cassette in dirty bay.
19. Confirm charged cassette ID.
20. Insert cassette in negative Z.
21. Confirm structural seating.
22. Close primary latch.
23. Close safety latch.
24. Perform dry check.
25. Advance connector shuttle.
26. Confirm signal and ID.
27. Perform pre-charge.
28. Close main contactor.
29. Perform low-power self-test.
30. Close shell.
31. Grant drive authorization.
32. Save swap log.

Every abnormal observation fails closed. The exchange locations are a dry
field-edge pad, stable level service area, or workshop stand; a dry stable levee
is conditional. Flooded paddy, deep mud, rice row interior, steep levee,
SOFT_TRAP, motion, powered PTO/motors, and unstable float conditions are
prohibited.

## 13. Battery Mule and rack compatibility

The interface names four roles:

- MULE_PROPULSION_CASSETTE;
- DELIVERY_CHARGED_CASSETTE;
- RETURNED_DIRTY_CASSETTE;
- FAULT_QUARANTINE_CASSETTE.

A propulsion cassette cannot enter delivery inventory. The Mule rack separates
CHARGED_CLEAN_BAY, RETURNED_DIRTY_BAY, and QUARANTINE_BAY. Initial planning is
one propulsion cassette and one or two delivery cassettes, not bulk transport.
Mule geometry is not validated because its requested repository lane is absent.

The charging rack uses the same cassette interface candidate and runs EMPTY,
RETURNED_WARM, COOLING, INSPECTION, WET_FAULT, IDENTIFIED, CHARGING,
CHARGE_COMPLETE, READY, RESERVED, FAULT, and QUARANTINE. Seating, latch,
dryness, identity, compatibility, temperature, and isolation-candidate evidence
precede charge authorization.

## 14. Service control

Serviceable wet-side items include wiper, guide rail, wear pad, corner bumper,
bottom skid, both latches, latch sensor, water sensor, shuttle, connector
module, secondary gasket, wet-side harness, drain-cover candidate, and
feedthrough candidate. These are sacrificial modules; the core frame and CBOX
remain protected.

Routine cleaning permits brushing, cloth wiping, drain probing, inspection,
wiper removal, and a later-approved low-pressure rinse candidate while isolated.
High-pressure water into D4, daily CBOX opening, hidden narrow mud pockets, or
drain disassembly as the normal cleaning method are prohibited.

## 15. CAD hold points

Before CAD placement is accepted, measure or derive:

1. actual top opening and structural frame envelope;
2. shell opening, hinge/removal, and lift sweep;
3. cassette mass center and handle/lift line;
4. seat, guide, latch, and recovery load cases;
5. BBOX rear/CBOX front notch and bulkhead conflict;
6. UPPER_REAR shuttle stroke, float, cam, and service sweep;
7. side motor-pod and PTO keep-out volumes;
8. sealed-feedthrough boss, drip loop, strain relief, and drain fall;
9. cassette vent route and operator/CBOX exclusion;
10. tilt/rollover drainage and no-pool behavior;
11. manual handling limit and lift-assist trigger;
12. connector candidate mate/unmate and seal requirements.

All exact dimensions beyond audited existing references remain TBD.

## 16. Approval boundary

Only the interface documentation candidate and its deterministic validation are
approved for review. Cassette waterproofing, connector waterproofing, CBOX
boundary leak performance, thermal behavior, fire safety, printability,
electrical safety, battery safety, manufacture, purchase, and field deployment
remain unvalidated or not approved exactly as recorded in the JSON contract.

Manufacturing readiness, purchase approval, and field deployment are
NOT_APPROVED.
