# Electrical architecture

Version: `v0.9.6.32`  
Classification: `CBOX_246X150X80_MODULAR_WATERPROOF_CONTROL_BOX`  
Status: `CBOX_246x150x80_CAD_PASS/A1_SINGLE_PIECE_PRINTABLE/BBOX_TO_CBOX_TWO_WIRE_POWER_INTERFACE/BBOX_LID_STRUCTURAL_INDEPENDENCE/REMOVABLE_UNIVERSAL_CARRIER/POWER_LOGIC_ZONING_DEFINED/GLAND_FIELDS_SOLID_NO_HOLES/LID_PENETRATION_ZERO/SEALED_FLOOR_PENETRATION_ZERO/EXTERNAL_ESTOP_ARCHITECTURE/SHELL_PRINT_APPROVED/CARRIER_PRINT_APPROVED/LID_PRINT_HOLD/WATER_NOT_YET/THERMAL_NOT_YET/POWERED_NOT_YET/COMMIT_READY_NOT_STAGED`

BBOX contains only LiFePO4 12.8 V battery, MAIN FUSE at battery positive, and CBOX power output. BBOX→CBOX is exactly two conductors: +12.8 V and GND. Signal/PWM/DIR/encoder/communication are prohibited at this interface.

CBOX zones: rear POWER INPUT/SAFETY; center-left MD10C-L; center-right MD10C-R; front/center ESP32/logic. DC-DC stays away from the motor-driver zones. Separate POWER and LOGIC routing corridors are reserved. Left driver exits left and right driver exits right; right motor direction correction, if needed, is only in the MD10C-R→MOTOR-R two-wire harness. E-stop contact controls a relay coil and never carries motor main current. Relay and fuse ratings remain HOLD.
