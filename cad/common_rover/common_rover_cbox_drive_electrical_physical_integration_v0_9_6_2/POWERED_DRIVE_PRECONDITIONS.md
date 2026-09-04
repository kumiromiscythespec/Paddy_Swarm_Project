# Common Rover CBOX DRIVE Electrical Physical Integration v0.9.6.2

Status: **NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING**  
Classification: `DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION`

This lane preserves the v0.9.6.0 above-water CBOX role and its power/signal separation. It does not approve powered rotation, live-battery submersion, or field deployment.

## Required closure before first powered DRIVE

1. Close the 565 mm belt hand test and 20T tooth-lift evaluation.
2. Define the H2.5 full-drive load qualification strategy.
3. Install a verified hardware motor-power cut and correct fuses.
4. Verify polarity, MD10C wiring, shared logic reference, encoder VCC, and ESP32 PWM=0 failsafe.
5. Begin on a current-limited supply with crawler off the ground, direct emergency access, and temperature observation.

`POWERED_ROTATION = NOT_APPROVED`; live-battery submersion and field deployment are also NOT_APPROVED.
