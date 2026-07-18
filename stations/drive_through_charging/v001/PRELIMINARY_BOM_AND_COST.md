# Preliminary BOM and Cost

## Status and purchasing boundary

Status: **DESIGN ONLY — planning estimate, not a purchase list.**

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

No supplier, product, electrical rating, quantity release, or order is approved. All quantities are provisional for one validation bay and the A/B dummy bench. Candidate components must be selected only after their unresolved ratings are established and reviewed.

## Planning assumptions

- One non-field validation bay is built first.
- One rover connector interface and one charger are evaluated.
- Two mechanically representative dummy cassette frames support the A/B interlock bench.
- The first energized bay uses `GRID-AC`; GRID and PACK equipment are never connected together.
- PACK integration is conditional, later, and separately approved.
- Direct station-cassette-to-rover-battery and battery-to-battery connection are prohibited.
- ST-012 voltage, energy, timing, mass, and efficiency figures are simulation assumptions, not purchasing ratings.

## Provisional BOM categories

### Mechanical bay

| Provisional item | Planning quantity | Purpose | Selection status |
|---|---:|---|---|
| Stable single-bay base/frame | 1 | Supports guide and stop loads without using the connector | Dimensions, material, anchoring, and load rating TBD |
| Entry wheel guides and mechanical stop | 1 set | Captures the approved docking envelope before connector contact | Geometry, wear surface, and force rating TBD |
| Independent mechanical latch | 1 | Retains final position without loading the connector | Architecture, force, manual recovery, and sensor TBD |
| Floating connector mount | 1 | Accepts only residual alignment error | Travel, stiffness, hard stops, and life TBD |
| Sacrificial alignment parts | 1 set | Takes repeatable guide/connector wear | Material and replacement limit TBD |
| Replaceable cleaning brushes | 1 set | Supports isolated contamination removal | Material and cleaning method TBD |
| Drip shield and drainage | 1 set | Diverts water and mud away from contact surfaces | Geometry and material TBD |
| Guards and pinch-point barriers | 1 set | Separates people from docking and latch hazards | Hazard review and dimensions TBD |
| Fasteners and strain-relief supports | 1 set | Retains structure and cables under repeated cycles | Material, locking method, and ratings TBD |
| Anchor points | 1 set | Secures the bay against docking loads | Site-independent proof-load basis TBD |

### Connector and environmental protection

| Provisional item | Planning quantity | Purpose | Selection status |
|---|---:|---|---|
| Blind-mate connector pair | 1 pair | Rover charging and pilot interface | Product, voltage, current, pins, IP, and materials unresolved |
| First-mate/last-break pilot contacts | 1 set | Enables inhibit and sequence supervision | Contact design and diagnostic coverage TBD |
| Unmated caps or shutters | 2 | Protects both halves from contamination | Seal and drainage behavior TBD |
| Drainage and debris exclusion features | 1 set | Prevents retained water and mud | Materials and geometry TBD |
| Replaceable wear/guide inserts | 1 set | Supports maintainable cycle testing | Product and service interval TBD |
| Material-compatible cleaning kit | 1 | Supports approved isolated cleaning | Chemistry and disposal method TBD |

### Control

| Provisional item | Planning quantity | Purpose | Selection status |
|---|---:|---|---|
| Safety relay or equivalent design category | 1 conceptual set | Implements reviewed fail-closed permission outside ordinary control | Required performance and architecture TBD |
| Contactor coils and suppression provisions | 1 set per reviewed contactor | Operates isolation device without unsafe transient | Coil voltage, suppression, and monitoring TBD |
| Presence, latch, and final-position sensors | 1 set per tested interface | Detects valid mechanical sequence | Technology, redundancy, and safe state TBD |
| Pilot-contact input | 1 independent channel | Observes first-mate/last-break sequence | Input architecture and diagnostics TBD |
| Voltage and polarity observation | 1 set | Proves compatibility and safe isolation | Range, accuracy, isolation, and self-test TBD |
| Independent current observation | 1 set | Confirms ramp-down and zero current | Range, threshold, redundancy, and accuracy TBD |
| Connector/cassette temperature sensing | 1 set | Detects abnormal heating | Locations, range, and trip limits TBD |
| Precharge path components | 1 reviewed set | Limits connection transient | Resistance, power, timing, and protection TBD |
| Source contactor with auxiliary proof | 1 per source channel | Provides controlled isolation | Voltage/current/fault rating and failure detection TBD |
| Individually coordinated fuses/protection | 1 per energy branch plus output as reviewed | Limits unprotected fault energy | Ratings and coordination study TBD |
| Physical ESTOP chain | 1 independent set | Removes charging permission independently | Performance level, contacts, and reset design TBD |
| Status lights | 1 reviewed set | Shows isolated, ready, active, and fault states without granting permission | Colors, meanings, and diagnostics TBD |
| Manual reset and fault indication | 1 set | Prevents automatic restart/resume | Device and human-factors design TBD |

### Power

| Provisional item | Planning quantity | Purpose | Selection status |
|---|---:|---|---|
| Fuse | 1 per energy branch | Limits unprotected branch fault energy | Rating and coordination TBD |
| Branch protection | 1 per source/load branch | Provides selective isolation | Technology and rating TBD |
| Main contactor | 1 per source channel | Opens the primary energy path | Voltage, current, fault, and auxiliary-contact ratings TBD |
| Precharge contactor | 1 per source channel | Controls the limited-energy precharge path | Ratings and failure response TBD |
| Precharge resistor | 1 per source channel | Limits connection transient | Resistance, pulse energy, and thermal limits TBD |
| Discharge resistor | 1 reviewed set | Brings stored voltage to a reviewed safe condition | Resistance, power, timing, and guarding TBD |
| Current-limited bench supply | 1 | Supports limited-energy phases | Output and protection limits TBD |
| Dummy load | 1 | Represents controlled demand without a real battery | Electrical and thermal ratings TBD |
| Charger | 1 | Provides the reviewed rover battery profile | Exact product and ratings unresolved |
| Insulated enclosure | 1 conceptual set | Segregates power and touch hazards | Insulation, ingress, thermal, and certification needs TBD |

### Sensors, measurement, and logging

| Provisional item | Planning quantity | Purpose | Selection status |
|---|---:|---|---|
| Docking speed measurement | 1 | Verifies `≤0.05 m/s` | Instrument and uncertainty TBD |
| Translation and angle gauges | 1 set | Verifies `±15 mm` and `±3°` | Instrument and calibration TBD |
| Force/strain indicators | 1 set | Detects connector-borne loads and cable strain | Range and placement TBD |
| Independent electrical instruments | 1 set | Cross-checks voltage, current, resistance, and safe state | Exact instruments follow phase hazard review |
| Temperature logger/sensors | 1 set | Records charger, connector, and enclosure heat | Range, channels, and calibration TBD |
| Cycle counter and evidence recorder | 1 set | Records dry, wet, and mud cycles deterministically | Implementation and retention TBD |

### Charger and limited-energy test equipment

| Provisional item | Planning quantity | Purpose | Selection status |
|---|---:|---|---|
| Current-limited SELV bench source | 1 | PHASE-3/4 pilot and interlock checks | Output limit and protection TBD |
| Dummy load or battery simulator | 1 | Charger characterization without a real battery | Power, voltage, and transient rating TBD |
| One approved AC charger | 1 | Initial `GRID-AC` single-bay path | Exact product and battery profile unresolved |
| Upstream isolation/protection | 1 reviewed set | Independently isolates the approved source | Mains details require licensed review |
| Guarded test harnesses/adapters | 1 set | Separates phase-specific test interfaces | Pinout, ratings, and construction TBD |
| Discharge and safe-voltage verification provision | 1 reviewed set | Supports controlled cleanup | Method and ratings TBD |

### Cassette bench

| Provisional item | Planning quantity | Purpose | Selection status |
|---|---:|---|---|
| Mechanically representative dummy cassette frame | 2 | Exercises A/B insertion, latch, and removal without real battery energy | Mass distribution, geometry, and materials TBD |
| Dummy weights totaling 9.6 kg per frame | 2 sets | Represents the provisional complete cassette mass mechanically | Weight distribution and retention TBD; no energy storage |
| Slot A/B fixtures | 2 | Supports mutual exclusion and release validation | Mechanical and sensor design TBD |
| Slide rails | 2 sets | Represents horizontal manual exchange motion | Load, travel, pinch protection, and wear TBD |
| Mechanical cassette latches | 2 | Prevents active or unsafe removal | Force, sensing, and release architecture TBD |
| Slot sensors | 1 set per slot | Observes presence, latch, and position | Technology and diagnostics TBD |
| ID simulation | 1 channel per dummy frame | Exercises identity checks without a real BMS | Method and fault cases TBD |
| Connector mockups | 1 per dummy frame plus slots | Exercises sequence without a production energized connector | Geometry and wear features TBD |
| Isolated/current-limited source simulators | 2 | Exercises A/B energy states at limited energy | Limits and isolation TBD |
| ARCH-A protected channel demonstrator | 1 conditional set | Later individual-module-isolation study | Not approved until module/BMS data and review pass |
| Inverter for PACK-INVERTER-AC | 1 conditional | Later off-grid single-bay path | Input range, surge, isolation, and thermal behavior TBD |
| Enclosure and ventilation demonstrator | 1 conditional | Later wet-zone/thermal study | Ingress, segregation, heat, and material design TBD |

## Provisional cost bands

These rounded bands are for early Japanese-yen planning only. They are not quotes, budgets, purchase approvals, or promises that a compliant solution exists within the band.

| Category | Provisional range |
|---|---:|
| Mechanical bay, guide, latch, guards, and mounts | JPY 20,000–50,000 |
| Connector pair, pilot provisions, caps, and environmental protection | JPY 10,000–30,000 |
| Interlock, contactor/precharge demonstrator, ESTOP, and protective provisions | JPY 20,000–50,000 |
| Sensors, measurement accessories, and evidence logging | JPY 15,000–40,000 |
| Charger characterization and limited-energy instrumentation allowance | JPY 15,000–40,000 |
| Two dummy cassette frames and A/B fixtures | JPY 10,000–30,000 |
| **Total planning range** | **JPY 90,000–240,000** |

The total is the arithmetic sum of the listed category low and high bounds. It is not a contingency-adjusted project estimate.

## Exclusions

The ranges exclude real rover batteries, seven-module station cassettes, certified production chargers, production inverter or isolated DC chargers, five-bay construction, rover modification, CAD/manufacturing engineering, tooling, site work, trenching, foundations, commercial mains distribution, licensed electrician labor, permits, certification and laboratory fees, shipping, taxes, spares, software/hardware control development, environmental chamber access, fire-system changes, field trials, night trials, and unattended-operation provisions.

They also exclude cost consequences of unresolved voltage/current, fault energy, IP rating, materials, conductor size, protective-device coordination, isolation, thermal, and enclosure requirements.

## Minimum viable test procurement sequence

Procurement remains unapproved. If a future contract authorizes purchasing, the minimum sequence is:

1. measurement and review services needed to close PHASE-0 unknowns;
2. non-electrical one-bay frame, guides, gauge, guards, and measurement fixtures for PHASE-1;
3. one traceable connector candidate and unpowered accessories for PHASE-2 only;
4. current-limited SELV source, sensors, fault insertion, and independent ESTOP demonstrator for PHASE-3;
5. two dummy cassette frames, two limited-energy simulators, and dummy load for PHASE-4;
6. one charger plus non-battery load/simulator and measurement equipment for PHASE-5;
7. GRID equipment and rover battery interface only after licensed review and explicit PHASE-6 mains/battery authorization;
8. environmental consumables only after the PHASE-7 protocol is approved;
9. PACK equipment only after PHASE-0 through PHASE-7 pass and PHASE-8 receives separate approval.

No bulk order, five-bay quantity, final connector, cassette power components, or production tooling is part of the minimum viable test.

If funding is insufficient, the **minimum viable test is limited to exactly** mechanical docking, an unpowered connector, the low-voltage interlock, and dummy cassettes. It excludes GRID charging, a real rover battery connection, PACK equipment, a real seven-module cassette, and five-bay work.

## Cost-control gates

- Do not purchase a connector before voltage/current/pin/environment/material requirements are closed enough to evaluate it.
- Do not purchase contactors, fuses, precharge parts, conductors, or converters from ST-012 simulation values.
- Do not purchase PACK equipment until authoritative module/BMS behavior and ARCH-A conditions pass review.
- Do not purchase five-bay equipment by multiplying one-bay assumptions; use measured PHASE-5/6/8 demand and heat.
- A failed phase pauses later-category purchasing and triggers review; it does not justify substituting an unreviewed part.

## Approval boundary

This BOM performs no purchase or hardware output and grants no permission for CAD, fabrication, wiring, mains work, battery connection, charger operation, field work, night work, automatic restart, or unattended operation. Every selection and energized use requires the applicable separate approval and licensed electrical review.
