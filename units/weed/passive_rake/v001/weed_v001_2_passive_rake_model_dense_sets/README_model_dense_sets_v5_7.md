# Paddy Swarm v5.7.3 model dense sets

This output is intended for a complete working/fit-check printed model. Paddy Swarm's current fabrication goal is a complete model including printable metal-surrogate parts when reference_metal_stl is available.

Dense sets:

- `dense_rigid_plus_metal/`: PETG/PLA rigid parts + `reference_metal_stl/*.stl` as printable rigid surrogate rods. This is the primary complete-model set.
- `dense_rigid_only/`: PETG/PLA rigid parts only, no printed metal surrogate rods.
- `dense_tpu_only/`: TPU wheels, gaskets, plugs, and other flexible parts only.

Important:

- Printed metal replacements are **not** a substitute for real metal in load/field testing.
- Use printed replacements for assembly sequence, spacing, fit, and low-load moving model checks. This is the default target for complete model fabrication.
- Replace rods with the metal BOM before real mud/water/field load tests.

## Counts

- rigid_plus_metal: total=38 rigid=38 tpu=0 printed_metal_replacement=6 plates=2
- rigid_only: total=32 rigid=32 tpu=0 printed_metal_replacement=0 plates=2
- tpu_only: total=2 rigid=0 tpu=2 printed_metal_replacement=0 plates=1
