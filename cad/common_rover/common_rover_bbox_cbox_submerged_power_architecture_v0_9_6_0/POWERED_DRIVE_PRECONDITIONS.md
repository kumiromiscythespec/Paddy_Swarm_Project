# Powered DRIVE Preconditions

Version: `0.9.6.0`  
Classification: `SUBMERGED_POWER_ARCHITECTURE + EMPTY_WATERPROOF_PROTOTYPE`  
`NOT_FOR_LIVE_BATTERY_WATER_TEST`


Required before powered operation: measured motor and driver current data; selected wire/cable; measured cable OD; fuse and connector ratings; hardware master cut/E-stop; guarded belts; verified routing; CBOX temperature monitoring; short-duration run plan and driver-spec stop threshold.

Current gates: `POWERED_DRIVE=NOT_APPROVED`, `LIVE_BATTERY_SUBMERSION=NOT_APPROVED`, `FIELD_DEPLOYMENT=NOT_APPROVED`. Empty shell printing or water testing does not change these gates.
