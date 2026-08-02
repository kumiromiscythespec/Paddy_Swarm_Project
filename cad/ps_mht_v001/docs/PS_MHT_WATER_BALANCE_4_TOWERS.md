# PS-MHT Water Balance — Four-Tower Audit

Phase: **3CB-0**  
Status: **VARIABLE MODEL / NO TANK SELECTED**

## 1. Variables and boundary

The current shell OD is 200 mm with a 3 mm wall, so this audit uses a
conservative clear diameter `D_i = 194 mm`. Water density is 1 kg/L.

| Symbol | Meaning | Audit candidates |
|---|---|---|
| `T` | Upper tank volume per tower | 3, 4, 5 L |
| `b` | Buffer volume per module | 0.4, 0.6, 0.8 L |
| `B=5b` | Five-module buffer total per tower | 2, 3, 4 L |
| `P` | Four-tower free-draining pipe inventory | Unknown; 2 L sensitivity case |
| `L_min` | Pump/sediment minimum in lower tank | Unknown; 8 L sensitivity case |
| `M_d` | Drainable media/root water for four towers | Unknown; zero in base table |
| `s` | Abnormal capacity margin | 10–20%; table uses 20% |

Retained medium water is part of total system inventory but is not assumed to
return by gravity. Only its measured drainable fraction enters `M_d`.

## 2. Buffer-section formula

For a full circular plan area:

`A_gross = pi D_i^2 / 4 = pi(194)^2/4 = 29,559 mm²`

For an annulus with central exclusion diameter `D_e`, angular fraction `f_a`,
and additional obstruction area `A_o`:

`A_eff = f_a * pi(D_i^2 - D_e^2)/4 - A_o`

`V_L = A_eff * h / 1,000,000`

`h_mm = 1,000,000 * V_L / A_eff`

The variables `D_e`, `f_a` and `A_o` must come from the Phase 3CB-A tray
coupon; they are not guessed into a final design here.

## 3. Gross and effective-area sensitivity

| Effective fraction of gross circle | 15 mm | 20 mm | 25 mm | Depth for 0.4 L | Depth for 0.6 L | Depth for 0.8 L |
|---:|---:|---:|---:|---:|---:|---:|
| 100% | 0.443 L | 0.591 L | 0.739 L | 13.53 mm | 20.30 mm | 27.06 mm |
| 80% | 0.355 L | 0.473 L | 0.591 L | 16.92 mm | 25.37 mm | 33.83 mm |
| 65% | 0.288 L | 0.384 L | 0.480 L | 20.82 mm | 31.23 mm | 41.64 mm |
| 50% | 0.222 L | 0.296 L | 0.369 L | 27.06 mm | 40.60 mm | 54.13 mm |

Therefore 0.8 L is impossible at 25 mm even before exclusions. A 0.6 L
buffer at 25 mm requires more than 81.2% of the gross circle, leaving little
room for roots, supports, overflow, drain and service clearance. The 0.4 L
candidate is the only one plausibly compatible with a 15–25 mm shallow tray,
but it still requires a measured effective area and freeboard.

Annular sensitivity before secondary obstructions:

| Central exclusion `D_e` | Effective area | Gross fraction | 15 mm | 20 mm | 25 mm |
|---:|---:|---:|---:|---:|---:|
| 80 mm | 24,533 mm² | 83.0% | 0.368 L | 0.491 L | 0.613 L |
| 100 mm | 21,705 mm² | 73.4% | 0.326 L | 0.434 L | 0.543 L |
| 120 mm | 18,250 mm² | 61.7% | 0.274 L | 0.365 L | 0.456 L |

## 4. Overflow and drain sensitivity

For a clear, sharp-edged idealized outlet:

`Q = C_d A sqrt(2 g h)`

The table uses `C_d=0.62` and clean water. It is an upper-bound comparison,
not a pass value for a screened, rooted or fouled outlet.

| Overflow ID | 10 mm head | 20 mm head | 30 mm head |
|---:|---:|---:|---:|
| 12 mm | 1.86 L/min | 2.64 L/min | 3.23 L/min |
| 14 mm | 2.54 L/min | 3.59 L/min | 4.39 L/min |
| 16 mm | 3.31 L/min | 4.68 L/min | 5.74 L/min |

At 20 mm head the same ideal model gives 1.17/1.83/2.64 L/min for
8/10/12 mm drains. Real flow is lower. Phase 3CB-A must verify the complete
screened assembly at 150% of maximum measured branch inflow and again after a
fouling/root challenge. The test stops if the root screen is inaccessible or
if the outlet can become a single hidden failure point. ID16 overflow and ID12
drain are the preferred first coupons, not selected production values.

## 5. One- and four-tower retained water

| Per-module candidate | One tower, five buffers | Four towers, twenty buffers | Water mass per tower |
|---:|---:|---:|---:|
| 0.4 L | 2 L | 8 L | 2 kg |
| 0.6 L | 3 L | 12 L | 3 kg |
| 0.8 L | 4 L | 16 L | 4 kg |

This mass is vertically distributed over five stages. It lowers the system
center of gravity relative to an equivalent upper-tank volume, but exact CG
requires dry module, plant, support and water elevations:

`z_CG = sum(m_i z_i) / sum(m_i)`.

The known mobile water mass per tower is `T+B = 5–9 kg`. Full operating tower
mass remains:

`m_full = m_dry_hardware + m_plants + m_dry_media + m_retained_media_water + T + B`.

Those first four terms are unmeasured, so Phase 3CB-0 does not publish a false
total weight. Four towers contain 20–36 kg of upper-plus-buffer water before
pipe, lower-tank and medium inventories.

## 6. Normal lower-tank peak

When all upper tanks drain but module buffers retain their intended water:

`C_normal = (L_min + 4T + P) * (1+s)`

Using `L_min=8 L`, `P=2 L`, `s=20%`:

| Upper tank per tower | Four upper tanks | Normal lower-tank requirement |
|---:|---:|---:|
| 3 L | 12 L | 26.4 L |
| 4 L | 16 L | 31.2 L |
| 5 L | 20 L | 36.0 L |

## 7. Full free-return sensitivity

If upper tanks, pipe inventory and all intended module-buffer water return:

`C_return = (L_min + 4T + P + 20b + M_d) * (1+s)`

Base table uses `M_d=0` and 20% margin:

| Upper tank `T` | Buffer 0.4 L | Buffer 0.6 L | Buffer 0.8 L |
|---:|---:|---:|---:|
| 3 L | 36.0 L | 40.8 L | 45.6 L |
| 4 L | 40.8 L | 45.6 L | 50.4 L |
| 5 L | 45.6 L | 50.4 L | 55.2 L |

Each additional 1 L of drainable medium water per tower adds 4.8 L after the
20% margin. For example, the 4 L upper/0.6 L buffer case rises from 45.6 L to
50.4 L when `M_d=4 L` total.

## 8. 40/50/60 L comparison

| Nominal tank | Normal operation | Full return | Audit result |
|---:|---|---|---|
| 40 L | Covers the modeled 3–5 L upper-tank normal peaks | Fails several full-return combinations | Not acceptable without strict inventory reduction and measured usable volume |
| 50 L | Covers modeled normal peaks | Covers low cases; nominal 4 L/0.6 L case has only 4.4 L before drainable media | Conditional only |
| 60 L | Covers base-table combinations | High 5 L/0.8 L case leaves 4.8 L, before drainable media and unusable volume | Preferred first mock-up size class, not selected; measured usable capacity may require a larger rated vessel |

## 9. Abnormal states

- **Power loss:** count all gravity-returning upper/pipe water; verify whether
  module buffers retain or siphon.
- **Overflow blockage:** upper emergency overflow must route to containment,
  not the PETG shell.
- **Broken branch:** include pump-delivered volume until sensor/operator stop.
- **Siphon:** test anti-siphon behavior; do not assume pump shutdown stops flow.
- **Media release:** measure `M_d` after saturation; do not add all retained
  media water unless the failure can actually release it.
- **Rated versus usable volume:** mark pump dead volume, sediment volume and
  mandatory freeboard on the physical tank.

No 40/50/60 L value is approved until these quantities and the actual tank
inside dimensions are measured.
