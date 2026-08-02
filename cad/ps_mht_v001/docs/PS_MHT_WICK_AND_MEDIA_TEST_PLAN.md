# PS-MHT Wick and Media Test Plan

Phase: **3CB-0 test definition**  
Status: **EXPERIMENT_REQUIRED**

## 1. Purpose

Select a short, per-plant wick and growing-medium combination that maintains
moisture during pump-off periods without keeping the whole net pot submerged.
Capillary performance belongs to the wick/medium geometry and wetting history,
not to the fibre name alone.

## 2. Fixed test rules

- No common wick from bottom to top.
- Initial architecture: two wicks per planting port.
- Candidate wick length: 80–150 mm.
- Candidate buffer immersion: 20–30 mm.
- The wick reaches the middle or lower medium region but remains removable.
- Normal buffer water level stays below the net-pot body by a measured margin.
- No cotton as the long-duration first candidate.
- No small PETG clip, snap, claw, key or cartridge.

With three ports per module and five modules, the two-wick architecture uses
30 wicks/tower and 120 wicks/four towers. At 80–150 mm each this is
2.4–4.5 m/tower and 9.6–18.0 m/four towers.

## 3. Wick candidates

| Candidate | Expected strengths | Main risks | First-screen position |
|---|---|---|---|
| Braided polyester watering cord | Dimensional stability, low biological decay, widely replaceable | Product-to-product finish changes wetting | Primary baseline |
| Braided nylon cord | Strong, abrasion resistant | Water uptake depends strongly on finish; creep possible | Secondary |
| Polyester/polypropylene nonwoven strip | High contact area and easy width variation | Root entanglement, fraying and excessive delivery | High-flow comparison |
| Commercial absorbent rope | Available in larger serviceable sizes | Unknown fibre blend and lot variation | Procurement-controlled comparison |
| Cotton | Strong initial wetting | Rot, biofilm and strength loss | Short reference only, not long-term candidate |

Record supplier, product code, lot, nominal diameter/width, dry mass per metre,
construction and prewash procedure. A material label without these fields is
not a reproducible specimen.

## 4. Retention and replacement comparison

| Method | Print-risk compatibility | Root service | Recommendation |
|---|---|---|---|
| Large circular retaining ring | Good flat print; no micro feature | Remove entire ring with root mass | Compare in tray coupon |
| Commercial grommet | No precision PETG clip | Replaceable if accessible from wet side | Preferred purchased reference |
| Broad insertion slot with rounded edges | Simple geometry | Wick can slide out sideways | Preferred printed feature candidate |
| Large removable perforated plate | Broad, cleanable, supports screen | Best for roots tangled around several wicks | Leading architecture candidate |
| Commercial cable tie/retainer | Robust and replaceable | Must remain reachable and not shed into water | Reference option |

The selected mechanism must survive 20 wick replacements without cracking,
must not move more than 5 mm under the later calibrated pull test, and must be
removable with roots present. The final pull load is experiment-required.

## 5. Staged test matrix

### Stage W0 — Product wetting screen

- Five specimens per wick product.
- Record dry dimensions/mass, prewash, time to first wetting, rise height at
  15/30/60/120 minutes and 24 hours.
- Use both canal water and the intended Hyponica A/B EC range.
- Reject specimens with non-wetting surface treatment or visible degradation.

### Stage W1 — Delivery-rate bench test

Test one and two wicks, 80/115/150 mm length and 20/25/30 mm immersion. Hold
reservoir head and air conditions constant. Determine delivered mass by tank
mass loss corrected by an unwetted evaporation control:

`q_wick = (Delta m_test - Delta m_evaporation_control) / Delta t`.

Record g/h for the first hour, 6 hours and 12 hours; repeat after drying and
after seven wet/dry cycles.

### Stage M0 — Medium water-retention screen

Initial media:

- washed coir baseline,
- coir/perlite candidate with ratio recorded by dry volume,
- one alternate medium only after the first two are characterized.

For each pot measure dry mass, saturated/drained mass, container capacity and
mass during 1/3/6/9/12-hour holds. Gravimetric water content is:

`GWC = (m_wet - m_dry) / m_dry`.

Any moisture sensor must be calibrated against gravimetric samples for each
medium. Raw sensor units cannot be compared across media.

### Stage WM1 — Pot-level combined test

Use the measured Siawadeky pot, actual 27-degree orientation, chosen wick
retainer and a visible buffer. Progress off-time through 1, 3, 6, 9 and 12
hours. Stop escalation when a rescue criterion is reached.

### Stage WM2 — Fouling and roots

Run the leading pair for at least 30 days with real nutrient solution. Record
flow loss, salt deposit, algae, root penetration, wick removal time and damage.
Do not infer root-service performance from root-free coupons.

## 6. Controlled variables

- Pot lot and measured geometry.
- Medium dry mass, compaction and initial moisture.
- Wick lot, prewash, length, immersion and number.
- Reservoir water depth and temperature.
- EC, pH and solution age.
- Ambient temperature, RH, air speed and light.
- Plant species, age, starting leaf area and root mass.
- Module elevation and port azimuth.

Only one wick/medium factor changes within a comparison. The four-tower
architecture trial must not also be the first broad wick/material screen.

## 7. Candidate measurable criteria

These thresholds are proposals for the physical protocol, not passed results:

- Twelve-hour end VWC at least 60% of that medium's post-drain starting VWC.
- Wilt score no more than 1 on a documented 0–4 scale.
- No normal standing-water contact with the net-pot body; target clearance
  at least 5 mm, to be confirmed by the tray coupon.
- Wick delivery coefficient of variation no more than 20% among five samples.
- No wick displacement greater than 5 mm during a hold cycle.
- At least 80% of clean baseline delivery after seven wet/dry cycles.
- Removal/replacement in no more than 5 minutes per planting port with no
  printed-part fracture.

If both crops require materially different moisture bands, retain separate
wick/media specifications instead of averaging them.
