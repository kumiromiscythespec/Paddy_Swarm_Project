# Crawler tracking patch design report v0.9.3.5

## Source selection

Selected `cad/crawler_h1/track_module/pretest_candidate_v0_1` because its tracked STLs and generator encode the observed 12T, 20 mm pitch, 10.3 mm drive bore and 26.2 mm bearing seat. Legacy Common Rover and authority lanes do not contain the matching printable link/guide contract.

## Preserved geometry

| Item | Value |
|---|---:|
| Tooth count | 12 |
| Link pitch | 20.0 mm |
| Pitch diameter | 76.394373 mm |
| CAD outside diameter | 66.14 mm |
| Axial tooth width | 44.0 mm |
| Tangential tip width | 7.5 mm |
| Source link count candidate | 40 |
| Nominal loop length | 800.0 mm |

## Recovery geometry

The original guide was a 3.0 mm high, 2.5 mm thick vertical wall with a broad 2.5 mm top. The corrected guide retains a 2.0 mm vertical lower zone and adds a 1.0 mm upper recovery slope. Angles are explicitly measured from vertical; therefore the 40 degree candidate has a larger lateral than vertical surface-normal component. The channel-facing top edge is filleted R0.75 mm. Left/right guides and the X envelope are symmetric.

- centered tooth collision: 0.000000 mm³
- source support-roller envelope collision: 0.000000 mm³ (50 mm OD × 44 mm axial width)
- displaced tooth contact: 1.647670 mm³
- guide/screw collision: 0.000000 mm³
- corrected drive minimum radial wall to bolt-hole envelope: 4.750 mm

The geometric contact sequence is a proxy. Physical return within one to two pitches remains a coupon and hand-test requirement.
