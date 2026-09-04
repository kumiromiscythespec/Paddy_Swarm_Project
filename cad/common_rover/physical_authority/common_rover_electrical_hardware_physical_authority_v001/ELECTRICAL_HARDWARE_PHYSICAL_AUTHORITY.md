# Common Rover Electrical Hardware Physical Authority

Authority ID: `COMMON_ROVER_ELECTRICAL_HARDWARE_PHYSICAL_AUTHORITY_V001`  
Date: 2026-09-01  
Scope: BBOX/CBOX electrical packaging documentation only.

## Classification contract

Every number must remain coupled to its source class. `PHYSICAL_DIRECT` means a direct user measurement. `PHYSICAL_FIT_RESULT` means an observed fit or passage. `DATASHEET_AUTHORITY` is manufacturer documentation. `PURCHASE_RECORD` establishes what was purchased. `DESIGN_SERVICE_REQUIREMENT` establishes a design/service target. Pending and historical classes must not be promoted without new evidence.

## Physical direct authority

| Item | Value | Source |
|---|---:|---|
| GoldenMate battery body | 150.9 x 99.4 x 92.5 mm | v0.9.5.2 physical measurement ledger |
| GoldenMate battery mass | 1.2 kg | v0.9.5.0 battery reference |
| Male battery tab | 6.3 mm wide x 0.7 mm thick | v0.9.5.2 terminal record |
| Female receptacle outer metal width | 10.6 mm | v0.9.5.2 terminal record |
| Battery bottom to terminal top | 99.4 mm | v0.9.5.2 terminal record |
| Freenove ESP32 WROOM v1.3 | 56.8 x 28.2 x 12.9 mm | v0.9.6.2 physical integration |
| ESP32 mounting holes | none observed | v0.9.6.2 physical integration |
| ESP32 long-side headers | present | user physical authority, 2026-09-01 task |
| Unidentified BBOX/CBOX cable OD | approximately 9.6 mm | chimney v001 physical measurements |
| Gland male-thread OD | 14.9 mm | chimney v001 physical measurements |
| Current physical CBOX | 150 x 246 x 80 mm | v0.9.6.36 manual-service authority |

The battery dimension order is preserved as reported. Packaging CAD must establish its intended axis mapping explicitly.

## Physical fit authority

The terminal-equipped GoldenMate battery physically passed the then-current 108 mm frame passage. This is a fit result, not a claim that every future 108 mm envelope is sufficient. The repository also records 90.7 mm at another datum; that value must not replace the 108 mm insertion result.

## Datasheet authority

Cytron MD10C Revision 3 family board plan envelope is 75 x 43 mm. This value comes from the manufacturer manual/drawing record and remains `DATASHEET_AUTHORITY`. No independent physical board X/Y measurement was found.

The repository also carries a 69 x 35 mm drawing-reference mounting pattern, but the searched authority set does not contain the primary vendor drawing itself. It is therefore retained as `UNVERIFIED_HISTORICAL / HOLD_SOURCE_CONFIRMATION`, not a manufacturing hole authority.

## Purchase authority

Taiyo Cabletec 2PNCT, 1.25 sq x 2C, 3 m was purchased. Identity, conductor specification, and purchased length are known. Actual OD is not known. The measured 9.6 mm cable is a separate specimen until identity evidence proves otherwise.

GoldenMate product label values 12.8 V, 10 Ah, and 128 Wh identify the current battery article but are not direct dimensional measurements.

## Design/service authority

CBOX service cable length is 900 mm. It supports manual CBOX movement, BBOX battery access, and routing slack. Repository text describes the arrangement as physically checked, but no evidence was found that a completed harness was measured end-to-end. It is therefore classified `DESIGN_SERVICE_REQUIREMENT`.

The optional 5 A branch-fuse value and 7.5 A main-fuse value in v0.9.6.2/v0.9.6.7 remain engineering candidates. Final ratings and holders are HOLD.

## SAFE_TO_USE_FOR_CAD

### Physical

- Battery: 150.9 x 99.4 x 92.5 mm; 1.2 kg.
- Battery terminals: male tab 6.3 x 0.7 mm; female receptacle outer width 10.6 mm; bottom-to-terminal-top 99.4 mm.
- ESP32: 56.8 x 28.2 x 12.9 mm, no mounting holes observed.
- Cable: OD approximately 9.6 mm for the measured, unidentified specimen only.
- Gland: male-thread OD 14.9 mm for the measured specimen.
- CBOX: 150 x 246 x 80 mm.

### Datasheet

- MD10C: 75 x 43 mm plan envelope.

### Design only

- CBOX service cable: 900 mm.

### HOLD

- MD10C physical X/Y, installed height, terminals, ferrules, wire bend, tool clearance, and source-confirmed holes.
- ESP32 USB plug, cable bend, header-connector, antenna/RF, and full service envelope.
- Actual Taiyo 2PNCT OD and bend radius.
- DC-DC, relay, E-stop, fuse holders, XT60, capacitors, crimp terminals, and final gland models/envelopes.

## Separation from historical envelopes

- Battery cassette 125 x 180 x 120 mm is a design envelope, not battery-body authority.
- CBOX 130 x 140 x 105 mm is historical CAD, not the current 150 x 246 x 80 mm physical CBOX.
- BBOX 150 x 220 x 150 mm is a historical design envelope, not a battery dimension.
- v0.9.6.37's 102 x 99.4 x 99 mm fitting-article keep-out is not silently merged with the 150.9 x 99.4 x 92.5 mm historical physical record; specimen/axis reconciliation remains pending.

## Status

`DOCUMENTATION_COMPLETE / ELECTRICAL_HARDWARE_AUTHORITY_RECORDED / PHYSICAL_GAPS_REMAIN`

This lane does not claim `PHYSICAL_VALIDATION_COMPLETE`.

