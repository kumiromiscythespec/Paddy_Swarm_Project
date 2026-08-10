# HTD5M source geometry

Version: v0.9.5.1  
Classification: `DRIVE_BELT_PHYSICAL_FIT_PROTOTYPE`  
Release: `HOLD`  

Profile `STANDARD`; protected candidate name `HTD-5M PRINTED TEST CANDIDATE`; pitch5.0 mm. Belt tooth depth 2.05 mm, root width 3.15 mm, tip width 1.6 mm, radial overlap 0.2 mm. Existing `belt_family.py` fixes the trial backing candidate at 2.2 mm, with annulus inner radius pitch+0.25 and outer radius pitch+2.20; therefore fallback2.0/2.5/3.0 comparisons are recorded but not used. The repository source itself uses this polygonal test representation, so the coupon is its exact `_straight_tooth` section—not a newly approximated triangle. Physical coupon fit remains required.
