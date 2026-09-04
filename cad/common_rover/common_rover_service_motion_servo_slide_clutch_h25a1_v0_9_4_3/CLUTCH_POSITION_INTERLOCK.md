# Clutch position and interlock

Version: `0.9.4.3`  
Classification: `SERVICE_AND_DRIVETRAIN_ARCHITECTURE`  
Release: `HOLD`  
Status: `SERVICE_AND_DRIVETRAIN_ARCHITECTURE_COMPLETE / PHYSICAL_MEASUREMENTS_PENDING`

The only sequence is DRIVE ↔ NEUTRAL ↔ PTO. A single carriage geometry cannot occupy both engagement ends. DRIVE and PTO have positive structural hard stops; NEUTRAL has a positive center definition/detent. Operating belt reaction terminates in frame/carriage stops, never continuous servo gear hold. Hall+magnet zones are reserved for all three positions; software alone is insufficient. SAFE_NEUTRAL_BIAS remains a comparison pending belt mechanics.
