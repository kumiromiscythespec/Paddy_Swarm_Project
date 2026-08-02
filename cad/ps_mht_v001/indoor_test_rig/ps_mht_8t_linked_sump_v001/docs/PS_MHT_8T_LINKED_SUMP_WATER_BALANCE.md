# Linked Sump Water Balance

Status: `VARIABLE_BALANCE_COMPLETE_MEASUREMENTS_PENDING`

## Definitions

- `N`: connected tower count, evaluated at 4, 6 and 8.
- `V_local_normal`: 5-7 L per connected local sump.
- `V_local_gross`: 12-16 L per sump.
- `V_tower_buffer`: 0.4 L x 5 bands = 2 L per tower, reference only.
- `V_pipe`, `V_pipe_return`: measured pipe inventory and stop return.
- `V_pump_well`: measured operating inventory in the common pump well.

Normal zone inventory is:

`N × (5..7 + 2) + V_pipe + V_pump_well`

| Towers | Local normal | Tower buffers | Known subtotal | Total formula |
|---:|---:|---:|---:|---|
| 4 | 20-28 L | 8 L | 28-36 L | 28-36 + pipe + pump well |
| 6 | 30-42 L | 12 L | 42-54 L | 42-54 + pipe + pump well |
| 8 | 40-56 L | 16 L | 56-72 L | 56-72 + pipe + pump well |

## Stop return and freeboard

Known tower return at pump stop is `2N` L. Total stop return is
`2N + V_pipe_return`. At the conservative combination of 12 L gross and 7 L
normal, geometric empty capacity is 5 L per sump: 20, 30 and 40 L for 4, 6
and 8 towers. After accepting only the known tower-buffer return, the
remaining conservative headroom is 12, 18 and 24 L respectively, before pipe
return. The configured system must independently maintain at least 4 L
emergency freeboard per sump.

The common pump-well requirement remains a formula until pump measurement:

`V_minimum_submergence + V_operational_drawdown + max(0, V_stop_return + V_pipe_return - V_local_available) + V_abnormal_margin`

Neither `V_pipe` nor `V_pump_well` is silently assigned a value.

## Isolation cases

Isolation always follows supply closure and complete tower drain. One isolated
sump removes 5-7 L of stable local inventory and one 2 L tower buffer from the
active zone. Two isolated sumps remove 10-14 L and two buffers. No other branch
is disconnected because every branch reaches the common trunk independently.

At four towers, unused E-H branches are closed. Fluid volume beyond each
closed valve is treated as zero; the fittings still require drainable,
cleanable commissioning practice.

## Erroneous upper supply during isolation

If supply is mistakenly open after the equalization valve closes, liquid must
leave through that sump's HIGH outlet and the non-circulating emergency
receiver. Receiver demand before safety margin is:

| Detection time | At 0.5 L/min | At 1.0 L/min |
|---:|---:|---:|
| 5 min | 2.5 L | 5 L |
| 10 min | 5 L | 10 L |
| 15 min | 7.5 L | 15 L |

Final receiver volume requires an agreed detection/response time, simultaneous
fault count and margin.

## Flow targets

| Towers | Zone L/min | Zone L/h | Qualification |
|---:|---:|---:|---|
| 4 | 2-4 | 120-240 | physical test required |
| 6 | 3-6 | 180-360 | physical test required |
| 8 | 4-8 | 240-480 | not qualified |

The nameplate 700 L/h value is not substituted for measured flow at actual
head.
