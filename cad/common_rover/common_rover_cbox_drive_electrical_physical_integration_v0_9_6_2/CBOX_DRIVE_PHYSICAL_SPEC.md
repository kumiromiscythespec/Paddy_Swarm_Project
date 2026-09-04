# Common Rover CBOX DRIVE Electrical Physical Integration v0.9.6.2

Status: **NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING**  
Classification: `DRIVE_ELECTRICAL_PHYSICAL_INTEGRATION`

This lane preserves the v0.9.6.0 above-water CBOX role and its power/signal separation. It does not approve powered rotation, live-battery submersion, or field deployment.

## Enclosure and tray

| item | candidate |
|---|---:|
| external | 230 × 92 × 55 mm |
| body | 230 × 92 × 50 mm |
| lid | 230 × 92 × 4.2 mm |
| compressed gasket | 0.8 mm |
| tray | 210 × 72 × 2.4 mm |

The width stays 92 mm while length grows from 180 to 230 mm and height from 45 to 55 mm. The body has no penetration, the lid is one piece, and the gasket loop is continuous. Known measured-component geometry clears the lid, but final height is `HOLD_MD10C_PHYSICAL_MAX_HEIGHT`.

On the Bambu A1 256 mm bed, a 230 mm part has 13 mm nominal margin at each long end. A 5 mm brim is recommended, leaving 8 mm each side. This is geometric entry only; corner lift, first layer, sealing-face protection, and long-wall warp remain physical-print risks.
