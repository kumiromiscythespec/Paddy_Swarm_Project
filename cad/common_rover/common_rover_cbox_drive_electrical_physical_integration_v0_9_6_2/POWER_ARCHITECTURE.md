# Common Rover CBOX DRIVE Electrical Physical Integration v0.9.6.2

Status: **NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING**  
Classification: `DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION`

This lane preserves the v0.9.6.0 above-water CBOX role and its power/signal separation. It does not approve powered rotation, live-battery submersion, or field deployment.

## Power path

`BBOX battery → main fuse near Battery+ → purchased 2PNCT 1.25sq ×2C → above-water connector → human-accessible software-independent hardware cut → CBOX STAR distribution`.

The star positive bus branches independently to MD10C-L, MD10C-R, and DC-DC. Battery negative terminates at STAR GND, which branches to both driver POWER- inputs, DC-DC input-, and logic reference. Motor current must never traverse ESP32 ground wiring. The 7.5 A main and 5 A branch values are engineering candidates only; all final ratings and commercial hardware remain HOLD.
