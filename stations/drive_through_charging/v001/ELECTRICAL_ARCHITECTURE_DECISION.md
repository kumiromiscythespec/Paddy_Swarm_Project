# Electrical Architecture Decision

## Status and decision

Status: **DESIGN ONLY**

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

Decision: **CONDITIONAL_RECOMMENDATION — ARCH-A, Individual Module Isolation, for the first cassette interlock and conversion prototype.**

The initial energized single-bay validation path is separately frozen as `GRID-AC`. It does not include a station cassette. ARCH-A becomes eligible only for the low-voltage cassette bench and later off-grid work after the conditions below are satisfied.

This recommendation does not approve a final product topology or a five-bay PACK station.

## Decision conditions

ARCH-A may proceed beyond paper review only when all of the following are available and accepted:

1. authoritative module and BMS limits, including permitted series or parallel behavior, charge and discharge limits, short-circuit behavior, reset behavior, and protective-device coordination;
2. a licensed electrical review of isolation, protective devices, conductor sizing, grounding or bonding, enclosure segregation, fault energy, thermal limits, and emergency isolation;
3. an architecture that prevents output backfeed and module-to-module equalization current;
4. individual module fuse protection located to minimize unprotected conductor length;
5. either independently isolated converter channels or a break-before-make selector whose failure cannot connect modules together;
6. current-limited operation with verified voltage compatibility, temperature supervision, and fail-closed loss-of-control behavior;
7. a certified or otherwise specifically reviewed charger between station source and rover battery;
8. successful PHASE-0 through PHASE-7 evidence before integrated off-grid charging.

If these conditions cannot be demonstrated, the PACK path remains `NOT APPROVED`; it does not fall back to uncontrolled ARCH-B parallel connection or direct battery-to-battery charging.

## Calculation basis

The ST-012 values are planning assumptions:

- each module: nominal 12.8 V, 10 Ah, 128 Wh class;
- seven modules: nominal stored energy 896 Wh before reserve and conversion losses;
- provisional delivered-energy assumption: 685.44 Wh per cassette;
- provisional complete cassette mass: 9.6 kg;
- rover usable-energy assumption: 102.4 Wh;
- charge-duration assumption: 180 minutes.

Let `P_CHG` be measured charger input power for one bay and `η_PATH` be measured end-to-end conversion efficiency. Expected source current must be calculated from measured values, not guessed:

- 12.8 V bus: `I ≈ P_CHG / (12.8 × η_PATH)`;
- 89.6 V nominal series bus: `I ≈ P_CHG / (89.6 × η_PATH)`;
- five-bay source: replace `P_CHG` with the measured coincident demand, including startup and derating cases.

No conductor, fuse, contactor, connector, converter, or enclosure rating is selected from these formulas in ST-013A.

## Architecture comparison

| Criterion | ARCH-A — Individual Module Isolation | ARCH-B — Low-Voltage Parallel Bus | ARCH-C — Series High-Voltage Bus |
|---|---|---|---|
| Nominal bus voltage | 12.8 V at each isolated module interface; common output is converter-defined and unresolved | 12.8 V nominal common bus | 89.6 V nominal for seven 12.8 V modules, subject to actual module/BMS approval |
| Expected current | Total input is approximately `P_CHG/(12.8×η_PATH)` and is divided only by controlled isolated channels; channel sharing must be measured | Approximately `P_CHG/(12.8×η_PATH)` for one bay and coincident five-bay demand divided by the same low voltage; potentially very high | Approximately `P_CHG/(89.6×η_PATH)` before downstream conversion; lower distribution current but higher touch and arc risk |
| Conversion stages | Individual isolated DC-DC channels or break-before-make selection, then approved inverter/charger or isolated charger | Reverse-current protection or ideal-diode equivalent, bus protection, then inverter/charger or isolated charger | Series monitoring and protection, isolated DC-DC or inverter, then approved charger |
| Required isolation | Channel-to-channel and output isolation, or proven galvanic separation through selection; charger isolation remains required | Charger isolation required; module branches need reverse-current isolation and fault containment | Reinforced segregation and touch protection appropriate to the reviewed voltage category; isolated conversion required |
| Fuse strategy | One fuse per module plus protected combined output; fuse coordination prevents a failed channel energizing another | One fuse per module at the terminal, branch disconnect, protected bus, and verified clearing under worst-case parallel fault contribution | Series-string protection, service disconnect, per-module monitoring, and reviewed arc interruption; individual fuse behavior must match BMS design |
| BMS strategy | Each module BMS remains independent and observable; channel may be inhibited without joining modules | Every BMS must explicitly permit parallel operation; voltage and SOC matching alone are insufficient without manufacturer data | Every BMS must explicitly permit series operation and common-mode voltage; isolated communications may be required |
| Connector risk | More internal connectors and wiring; faults are easier to localize and external bus can remain current-limited | Low voltage but high current, heating, large conductors, and damaging make/break current | Lower current but increased shock, insulation, creepage, arc, and maintenance risk |
| Wet-environment risk | Many sealed internal interfaces; external connector risk depends on converted output | Conductive contamination plus high fault current can produce heating and corrosion | Wet contamination has the highest consequence because voltage and arcing potential are increased |
| Repairability | Channel-level isolation and replacement are possible, but troubleshooting is more complex | Simple conceptual bus, but one branch fault can involve all modules and heavy buswork | Specialized procedures, isolation checks, and trained service are required |
| Cost | High: multiple protected channels, sensors, and wiring | Medium initially, potentially high after proper current protection and copper are included | High: isolation, rated switching, touch safety, and specialist review |
| Weight | Medium to high due to converters, fuses, and harnesses | High copper and busbar mass at useful power | Potentially lower distribution copper, offset by insulation and isolated conversion hardware |
| Failure containment | Best of the three when every channel fails isolated and backfeed is impossible | Weak without verified reverse-current blocking; a bus fault can collect energy from seven modules | A single open stops the string, but insulation or switching failure can expose the full series voltage |
| First-prototype suitability | **Conditional preferred baseline** for controlled bench validation | Not suitable until module parallel permission, matching limits, inrush control, and fault-current tests are established | Not suitable for the first Paddy Swarm prototype |

## Why ARCH-B is not the default

Low nominal voltage is not equivalent to low risk. Seven modules on a parallel bus can contribute fault and equalization current. Individual fuses alone do not prevent backfeed or guarantee safe hot insertion. ARCH-B requires authoritative parallel-operation approval, enforced voltage-difference limits, controlled precharge or branch connection, reverse-current blocking, thermal validation, and fault-current coordination. It remains a comparison candidate, not an approved fallback.

## Why ARCH-C is deferred

ARCH-C reduces distribution current but creates a nominal 89.6 V string before tolerance and charging effects are considered. Module BMS series compatibility is unknown, and wet-environment insulation, touch safety, arc interruption, connector segregation, and maintenance burdens increase. It is disproportionate for the first prototype and requires a new hazard review if reconsidered.

## Charger topology comparison

Direct station-cassette-to-rover-battery connection is prohibited in every architecture.

| Criterion | GRID-AC | PACK-INVERTER-AC | PACK-ISOLATED-DC |
|---|---|---|---|
| Path | Commercial AC supply → certified AC charger → rover battery | Station cassette → inverter → certified AC charger → rover battery | Station cassette → isolated DC-DC charger → rover battery |
| Conversion loss | One charger conversion stage | Inverter plus AC charger; normally the greatest conversion loss | Potentially lower than inverter plus charger, but only after a compatible charger is validated |
| Charger availability | Widest availability and simplest service replacement | Reuses the same certified charger class as GRID | Specialized voltage range and battery profile; availability may be limited |
| Isolation | Certified charger isolation plus reviewed mains installation | Inverter isolation characteristics and charger isolation must both be verified | Galvanic isolation must be specified and tested in the DC charger |
| Waterproofing | Charger and mains equipment stay in a reviewed enclosure; only approved low-voltage charging interface reaches the bay | Cassette, inverter, charger, and ventilation add wet-zone enclosure challenges | DC converter and input/output segregation require a sealed thermal design |
| Repairability | Best for the first test because source and charger can be isolated independently | Modular replacement is possible but two conversion devices complicate diagnosis | Specialized replacement and battery-profile verification are required |
| Cost | Lowest uncertainty for one bay; mains work and licensed review are excluded from ST-013A approval | Medium to high because inverter surge and charger compatibility both matter | High development and validation cost despite possible future efficiency benefit |
| Heat | Charger heat only | Inverter heat plus charger heat | Concentrated DC-DC charger heat; derating remains unresolved |
| Five-bay expansion | Requires branch protection, supply-capacity study, diversity review, and independent bay isolation | Inverter startup, coincident load, and thermal sizing can become large | Modular isolated chargers may scale well if each bay remains independent and certified compatibility is established |
| Starting surge | Charger inrush must be measured and branch protection coordinated | Inverter startup plus charger inrush is the most demanding case | Converter soft-start and input precharge must be verified |
| Partial charge behavior | Determined by the certified charger and rover BMS; must be measured | Same charger behavior, with inverter low-voltage cutoff interactions added | Charger firmware/profile behavior must be independently validated |

## Charger recommendations

### Initial one-bay test

Use `GRID-AC` only after PHASE-0 licensed review and separate authorization for mains work and battery connection. The certified AC charger remains outside the blind-mate connector's mechanical load path and wet contamination path. Mains voltage is never routed through the rover blind-mate connector.

### First off-grid one-bay test

Use `PACK-INVERTER-AC` as the conditional integration baseline because it preserves the already-characterized charger between source and rover. Proceed only after inverter isolation, startup surge, low-voltage cutoff, fault shutdown, enclosure heat, and charger compatibility are measured. This is not an efficiency recommendation.

### Future five-bay design

Prefer evaluation of independent `PACK-ISOLATED-DC` charger channels only if measured power, module input range, galvanic isolation, charger/BMS compatibility, fault containment, thermal derating, and service availability are accepted. Otherwise retain independently protected `PACK-INVERTER-AC` channels. No common five-bay converter, shared protection, or final power rating is frozen in ST-013A.

## Fail-closed design rules

- Loss of pilot, latch, identity, voltage, temperature, BMS-ready, current-sensor validity, controller health, or required communication inhibits charging.
- The disconnected connector is touch-safe, with no exposed energized contacts.
- Power restoration and controller reboot never resume charging automatically.
- A fault is latched until the energy path is isolated, inspected, and manually reset.
- The physical ESTOP removes charging permission independently of normal software logic.
- Charger current must be ramped to zero and independently confirmed before source contactor opening, connector release, or cassette transfer.
- No active slot can unlatch, and slots A and B can never be directly paralleled or simultaneously ACTIVE.

## Safety boundary

This decision performs no hardware output and grants no approval for mains work, battery connection, charger control, contactor operation, purchase, CAD, field operation, night operation, automatic restart, or unattended operation. Licensed electrical review remains mandatory.
