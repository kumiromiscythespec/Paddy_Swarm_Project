# Paddy Swarm v5.7 model dense sets

This output is intended for a working/fit-check printed model.

Dense sets:

- `dense_rigid_plus_metal/`: PETG/PLA rigid parts + `reference_metal_stl/*.stl` as printable rigid surrogate rods.
- `dense_rigid_only/`: PETG/PLA rigid parts only, no printed metal surrogate rods.
- `dense_tpu_only/`: TPU wheels, gaskets, plugs, and other flexible parts only.

Important:

- Printed metal replacements are **not** a substitute for real metal in load/field testing.
- Use printed replacements for assembly sequence, spacing, fit, and low-load moving model checks.
- Replace rods with the metal BOM before real mud/water/field load tests.

## Counts

- rigid_plus_metal: total=51 rigid=51 tpu=0 printed_metal_replacement=3 plates=20
- rigid_only: total=48 rigid=48 tpu=0 printed_metal_replacement=0 plates=19
- tpu_only: total=10 rigid=0 tpu=10 printed_metal_replacement=0 plates=8
