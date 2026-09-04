# Source provenance

## Read-only design authority

- Repository: `D:\Paddy_Swarm_Project`
- v002 source commit: `17a703694d5b2e127b5f7bccf8bfe3c5f1f0f2b9`
- v002 lane: `cad/ps_webcam_rainhood_v002_tripod_mount/`
- v002 source path: `cad/ps_webcam_rainhood_v002_tripod_mount/cad/ps_webcam_rainhood_v002.py`
- v002 Git blob: `43cd3b5197be19add694b078bd655b0c3a8c75d8`
- Access method: read-only `git ls-tree` and `git show`; no checkout or branch move.

The v003 source transcribes the exact fixed mechanical values and reconstructs the carrier only as a validation reference. It does not import or edit a working-tree copy of v002.

## Preserved authority

- camera W/H/D and folded clip safe envelope;
- tripod X/Y datum and through-hole diameter;
- carrier width/depth/thickness and position;
- anti-rotation guide geometry;
- hood inner/outer width and 3 mm wall;
- roof slope and top-clearance datum;
- lower/upper slide rails and clearances;
- rear stops;
- rear crossbar, M4 bosses, clearance paths, and nut traps;
- USB channel datum.

The generator contains a literal authority table and aborts if its active fixed values no longer match the transcribed v002 values.

## v003-owned geometry

- front setback: A/B/C = 10/15/20 mm from v002 Y=-60.4 mm;
- underside bevel: A/B/C = 35/40/45 degrees;
- 1.2 mm printable leading-edge thickness;
- roof test cutoff Y=22 mm, behind camera-body rear Y=14.8 mm;
- low rear side spines that connect the optical shell to the unchanged interface;
- one/two/three right-exterior identifier ribs.

## Toolchain

- Python 3.12.13
- CadQuery 2.8.0
- Pillow 12.3.0 for schematic side-view images
- STL tessellation tolerance: 0.08 mm linear / 0.12 rad angular

Generated reports record the runtime CadQuery version, BRep metrics, STL hashes, mesh checks, interference values, and per-candidate parameters.

## Repository-safety scope

The v003 lane is additive. v002 is reference-only. Existing tracked and unrelated untracked files are outside this task. The handoff ZIP is created separately in `D:\Downloads` and contains only this v003 lane.

