# Common Rover Rapid Dry BBOX/CBOX v0.9.6.7

Classification: `DRY_TEST_FIXTURE_ONLY`  
Priority: `SPEED > WATERPROOF > APPEARANCE`  

BATTERY+→inline7.5A engineering-candidate fuse→reachable DC-rated hardware cut≥10A→STAR+→two MD10Cs. BATTERY-→STAR-→two MD10Cs. Optional5A branch fuses may be used if available. Fuse holder and cutoff remain external. ESP32 uses separate regulated USB5V; logic GND is shared, while motor current never flows through ESP32 ground. Sign-Magnitude PWM/DIR/GND is retained.
