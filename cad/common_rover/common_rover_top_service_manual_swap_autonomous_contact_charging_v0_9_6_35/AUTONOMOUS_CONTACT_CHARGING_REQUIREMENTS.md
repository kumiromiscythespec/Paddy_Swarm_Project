# Autonomous contact-charging requirements

Sequence: rover approach → mechanical alignment → contact engagement → contact validation → charging enable → charge → charging disable → disengage → resume.

Charging output should remain inactive before valid docking. `CONTACT_DETECTED + POLARITY_VALID + POSITION_VALID → CHARGING_ENABLE`. Failed/partial docking, wet/short detection, sensor disagreement, or unknown state prevents charging and invokes safe isolation.

Prefer a location above the waterline with recessed, downward-facing, or sheltered geometry; provide mud/straw/water drainage and a wiping/self-cleaning motion candidate. Reverse polarity must be mechanically impossible. Avoid exposed live contacts. Require an independent fuse, charge-current monitoring, battery-voltage monitoring, temperature-monitoring candidate, and presence/docking confirmation.

Exact voltage/current, material, spring-contact model, connector SKU, contact geometry, and contamination performance remain `CHARGING_CONTACT_HARDWARE=HOLD`.
