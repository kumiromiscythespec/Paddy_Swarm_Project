# Connector Requirements

## Status

Status: **DESIGN ONLY — no connector product is selected.**

The purpose of this document is to define evidence needed for later selection. It is not a purchase specification, pinout, wiring instruction, or approval to mate an energized connector.

```text
design_only=true
hardware_output_performed=false
mains_work_approved=false
battery_connection_approved=false
field_operation_approved=false
night_operation_approved=false
automatic_restart_approved=false
unattended_operation_approved=false
licensed_electrical_review_required=true
physical_estop_independent=true
```

## Interface boundary

The bay interface is high-mounted, forward-entry/forward-exit, and mechanically guided. Structure and guide features accept docking loads before connector engagement. The connector is the last component to mate and the first electrical component to break. It carries no rover body load, alignment load, towing load, or latch retention load.

Mains voltage is prohibited at the blind-mate interface. Direct station-cassette-to-rover-battery and battery-to-battery connection are prohibited. An approved charger remains between the station source and rover battery.

## Functional requirements

- A mechanically independent guide must enter its capture range before connector contact.
- Provisional docking speed is at or below `0.05 m/s`.
- Provisional connector-plane misalignment is within `±15 mm` lateral/vertical translation and `±3°` angular error only after the candidate's allowable engagement envelope is confirmed.
- Connector engagement must not correct gross chassis misalignment.
- A positive mechanical latch must retain the dock without loading the connector shell.
- A replaceable sacrificial connector block must protect the permanent bay and rover structure from normal alignment wear.
- The interface must provide a presence/pilot contact that makes before power contacts and breaks before power contacts.
- The pilot must support charger inhibit, latch supervision, and hot-unplug prevention without being the only independent safety layer.
- Mating sequence, unmating sequence, insertion force, withdrawal force, float travel, wipe distance, and final position must be inspectable and testable.
- Polarity and incompatible mating must be mechanically keyed.
- Service access must allow inspection and replacement without disturbing protected mains or cassette circuits.

## Electrical requirements

- Voltage category, continuous current, peak current, inrush, duty cycle, temperature derating, and prospective fault current must be derived from measured charger behavior and approved topology.
- Power contacts must not be used as pilot contacts.
- Protective earth, bonding, signal reference, shields, and galvanic isolation must be defined by licensed review before pin assignment.
- Creepage, clearance, insulation coordination, contact resistance, temperature rise, touch safety, and fault containment must be evaluated for the actual voltage and pollution environment.
- A contactor or equivalent reviewed isolation device must keep the blind-mate power contacts de-energized until presence, latch, identity, voltage, temperature, BMS-ready, and precharge guards pass.
- Unmating is prohibited until charger current ramps down, independent zero-current evidence passes, and the contactor is proven open.
- Loss of pilot, latch, sensing, controller health, required communication, or measurement plausibility removes charging permission.
- No event, reboot, power restoration, or communication restoration may automatically re-energize the interface.

## Mechanical requirements

- Guides and stops must react longitudinal, lateral, vertical, and angular docking loads independently of the connector.
- A compliant or floating mount may absorb only the residual misalignment within the connector manufacturer's reviewed limits.
- Cable mass, bend radius, strain relief, torsion, vibration, and repeated flexing must not load terminations or sealing faces.
- The connector must have guarded contacts and no finger-accessible energized surface in any permitted state.
- The mounting concept must prevent fastener loosening, rotation, incorrect depth, and partial latch from appearing valid.
- The rover must be able to leave forward without cable drag or a captive obstruction after safe release.
- Replaceable wear parts and inspection references must be identifiable without exact field coordinates.

## Environmental and material requirements

- Environmental qualification must address rain, splash, washdown, condensation, mud, silt, fertilizer residue, dust, corrosion, UV, vibration, temperature cycling, freeze/thaw where applicable, and standing-water drainage.
- An IP rating must not be inferred from appearance; the required rating and its mated/unmated applicability remain unresolved until the installation and cleaning method are defined.
- Materials must be compatible across shell, contacts, plating, seals, guides, fasteners, and cleaning agents and must avoid unacceptable galvanic couples.
- The orientation must drain away from contacts and must not form a mud pocket.
- An unmated protective cap or shutter must keep contamination out without trapping water.
- A drip path and downward- or side-facing water escape must prevent liquid from collecting on the contact face.
- A replaceable, material-compatible cleaning brush must be evaluated without allowing debris to be pushed into contacts.
- A mud shield must protect the approach and must be removable for inspection.
- Cleaning must be possible with the energy path isolated. No cleaning procedure may require live probing or mating to clear debris.
- Seals must not hide conductive contamination or prevent inspection of critical contact surfaces.

## Sensing and interlock requirements

- First-mate/last-break pilot status must be electrically distinct from power continuity.
- Presence, pilot, mechanical latch, and final-position sensing must be cross-checked; any contradictory combination is fail-closed.
- Insertion detection must be independent from charge-current measurement; current alone never proves a valid mate.
- Temperature sensing is required at the connector or at a justified thermally representative location.
- Current and voltage measurements used for safe unmating must have a defined self-test or plausibility check.
- A welded-contactor indication, unexpected voltage, or unexpected current must inhibit release and latch a fault.
- Physical ESTOP remains independent and removes charging permission without relying on a network message or normal software state.
- Sensor or communication restoration permits diagnosis only; it does not resume charging.

## Provisional acceptance targets

These values are screening targets, not certified product limits:

| Item | Provisional target |
|---|---|
| Docking speed | `≤0.05 m/s` |
| Translational tolerance at connector plane | `±15 mm` |
| Angular tolerance | `±3°` |
| Mechanical sequence | Guide engages before connector; connector mates last |
| Structural load | No rover body or docking load carried by connector |
| Dry cycles | 100 completed cycles |
| Wet cycles | 20 completed cycles after an approved unenergized wet protocol |
| Mud cycles | 20 completed cycles after an approved unenergized contamination protocol |
| False-positive latch indications | 0 |
| Connector, guide, or mounting damage | 0 |
| Cable or termination strain events | 0 |

Any partial mate, bent contact, seal displacement, contamination bridge, abnormal contact resistance, abnormal temperature rise, pilot sequencing error, latch contradiction, or connector-borne structural load is a failed result and an immediate stop condition.

## Inspection, cleaning, and release concept

Before mating, the interface is isolated and inspected for damage, moisture, mud, conductive residue, foreign objects, seal condition, guide condition, and cap/shutter function. Cleaning uses only a later approved material-compatible process while isolated. After cleaning, dryness and contact condition are independently accepted before the connector can re-enter validation.

Release requires a deliberate request, charger disable, current ramp-down, independent zero-current confirmation, contactor-open proof, safe voltage, and mechanical latch release. A manual emergency release is required for recovery, but its architecture is unresolved; it must be separately hazard-reviewed, guarded against casual use, and unable to bypass electrical isolation.

## Candidate evaluation matrix

Each future candidate must be scored with documentary evidence for electrical ratings and derating, first-mate/last-break contacts, touch safety, environmental rating in both mated and unmated states, corrosion compatibility, cleaning limits, mating-cycle life, float tolerance, insertion force, strain relief, service availability, replaceable wear parts, manufacturer traceability, and certification applicability. A sample passing dimensional fit alone is insufficient.

No brand, series, vendor, or product identifier is selected in ST-013A.

## Exact unresolved selection data

The following remain explicitly unknown and must not be guessed:

- exact connector voltage;
- exact continuous and peak current;
- exact pin count and pin allocation;
- exact IP rating and whether it applies mated, unmated, or both;
- exact product or manufacturer;
- exact shell, contact, plating, seal, guide, and fastener materials.

Also unresolved are contact-resistance limit, allowable temperature rise, insertion/withdrawal force, float mechanism, cable size, bend radius, cleaning chemistry, service interval, and mating-cycle qualification. Selection requires measured system loads, the architecture decision, hazard review, and licensed electrical review.

## Approval boundary

This requirements set does not authorize purchase, fabrication, CAD, pin assignment, wiring, mains work, battery connection, energized mating, field operation, night operation, automatic restart, or unattended operation.
