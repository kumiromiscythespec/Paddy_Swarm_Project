# Common Rover CBOX DRIVE Electrical Physical Integration v0.9.6.2

Status: **NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING**  
Classification: `DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION`

This lane preserves the v0.9.6.0 above-water CBOX role and its power/signal separation. It does not approve powered rotation, live-battery submersion, or field deployment.

## Control and encoder signals

SIGN-MAGNITUDE PWM uses PWM-L/DIR-L and PWM-R/DIR-R, with PWM low as the motor-output-off startup reference. No GPIO numbers are released. Encoder candidate channels are V+, GND, A, B; `ENCODER_VCC TBD` is mandatory because supply voltage is unverified. Encoder and motor wiring stay in separate corridors and cross at approximately 90 degrees where unavoidable.
