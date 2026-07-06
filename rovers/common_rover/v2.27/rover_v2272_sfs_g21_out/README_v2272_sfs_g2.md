# Paddy Swarm Retrofit Summer Float Shell G2 (v2.27.2-sfs-g2)

This is the G2 retrofit turtle-shell kit for the already printing Paddy Swarm
Common Rover v2.27.

## Main changes from G1

- The roof is treated as a faceted turtle-shell/dome, not just a flat open cover.
- PTO/front side remains open; use only the optional FRONT-VISOR if it clears the PTO/unit.
- Rear/CBOX side can be closed with the optional REAR-CAP, which includes drain notches.
- Side floats are separate left/right sponsons. They are not continuous walls around the gearboxes.
- The E-stop uses a high sloped doghouse instead of a simple top hole.
- `print_manifest_generic_marked.csv` is written directly for dense v5.7.

## First print order

1. Print `PS-RV2272-SFS-ROOF-F` or `PS-RV2272-SFS-ROOF-R` alone.
2. Place it on the v2.27 rover without fastening.
3. Confirm BBOX/CBOX lid, RCP/E-stop, DRC/DRIVE, tire sweep, and PTO clearance.
4. Print one side float only and use `CLEARANCE-GAUGE-S` before attaching it.
5. Add rear cap only if it does not trap mud/water and still allows cleaning.

## Important

- Raw FDM side floats are not guaranteed watertight. Seal, coat, or foam-fill before water testing.
- Do not run water tests with electronics installed.
- Use test weights first.
- Add water intrusion sensors and an independent high-current cutoff before powered water trials.

## Dense note

If Bambu Studio opens `*_bambu_multiplate_project.3mf` and shows objects outside the active plate, use the individual 3MF files under `3mf_dense_pack_rigid/` instead.  Those are the safer fallback for printing one plate at a time.
