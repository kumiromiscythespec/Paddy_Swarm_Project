# Common Rover CBOX DRIVE Electrical Physical Integration v0.9.6.2

Status: **NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING**  
Classification: `DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION`

This lane preserves the v0.9.6.0 above-water CBOX role and its power/signal separation. It does not approve powered rotation, live-battery submersion, or field deployment.

## Authority boundary

Measured authority is limited to the ESP32 envelope and purchased-cable identity/length. MD10C board and 69 × 35 mm mounting pattern are drawing references. The 55 mm CBOX height, PETG cradle, standoffs, service envelopes, DC-DC zone, fuse zones, and keep-outs are design candidates. MD10C height, cable OD, all gland geometry, final fasteners, DC-DC, fuses, connector, hardware cut, GPIO, encoder VCC, thermal limit, and RF keepout remain HOLD.

The v0.9.5.3 and v0.9.6.0 lanes and all four current-authority files are read-only parents. This delta does not supersede their physical measurements except for selecting the resized CBOX candidate.
