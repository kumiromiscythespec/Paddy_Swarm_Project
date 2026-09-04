# Power Distribution Topology

Version: `0.9.6.0`  
Classification: `SUBMERGED_POWER_ARCHITECTURE + EMPTY_WATERPROOF_PROTOTYPE`  
`NOT_FOR_LIVE_BATTERY_WATER_TEST`


Battery+ → shortest practical lead → MAIN FUSE → BBOX pigtail → ABOVE-WATER CONNECTOR → HARDWARE MASTER DISCONNECT → distribution → DRIVER L/R → MOTOR L/R. Battery− routes directly to the pigtail return.

Main/branch fuse ratings, connector current rating and disconnect/E-stop component remain HOLD until motor/driver current measurements exist. Software-only motor power removal is prohibited. Human-accessible, identifiable, software-independent hardware motor-power cut is required before powered DRIVE testing.
