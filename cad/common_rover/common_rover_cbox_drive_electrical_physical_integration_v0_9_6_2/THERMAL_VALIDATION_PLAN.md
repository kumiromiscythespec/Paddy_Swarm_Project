# Common Rover CBOX DRIVE Electrical Physical Integration v0.9.6.2

Status: **NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING**  
Classification: `DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION`

This lane preserves the v0.9.6.0 above-water CBOX role and its power/signal separation. It does not approve powered rotation, live-battery submersion, or field deployment.

## Sealed-box thermal gate

No vent is added to the waterproof baseline. Record ambient, driver case/board maxima, CBOX internal air, ESP32, DC-DC, and motor currents during staged operation: idle, single motor no-load, dual no-load, stepped representative load, then fault-abort observation. Stop on unexpected odor, connector heating, current excursion, control reset, or enclosure softening. Final limit and duration remain HOLD; electrical driver oversizing does not close sealed-enclosure thermal validation.
