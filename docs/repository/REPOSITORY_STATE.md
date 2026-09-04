# Repository state at normalization

## Pre-flight

| Field | Measured value |
|---|---|
| Repository | `D:/Paddy_Swarm_Project` |
| Remote | `origin = https://github.com/kumiromiscythespec/Paddy_Swarm_Project.git` |
| START_BRANCH | `agent/organize-untracked-cad-assets-20260725` |
| START_HEAD | `7c149a65053f2292bc4cc0ed06d8941c96852f2b` |
| Upstream state | ahead of `origin/agent/organize-untracked-cad-assets-20260725` by 3 commits |
| Initial tracked modifications | 4 files |
| Initial untracked files | 4,616 |
| Initial untracked bytes | 1,443,808,762 (about 1,376.92 MiB) |
| Largest untracked file | 67,039,221 bytes (about 63.93 MiB) |
| Files at or above 95 MiB HOLD threshold | 0 |
| Publication date | 2026-09-05, Asia/Tokyo |

The four initial tracked modifications were
`CURRENT_COMMON_ROVER_AUTHORITY.md`, `README.md`,
`docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md`, and
`rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md`.

The three commits already ahead of the remote before normalization were:

- `3269fe6 cad(common-rover): add v0.9.5.0 BBOX CBOX printable prototypes`
- `d085027 cad(common-rover): add v0.9.5.1 HTD5M TPU drive belt trial`
- `7c149a6 docs(common-rover): record v0.9.5.2 physical measurements`

No checkout, switch, pull, merge, rebase, reset, restore, clean, deletion, force
push, LFS introduction, CAD geometry edit, or branch change is part of this
normalization.

## Untracked audit

The exhaustive initial-file snapshot is
[`UNTRACKED_FILE_AUDIT.json`](UNTRACKED_FILE_AUDIT.json). Every captured file has
path, byte size, extension, project/lane, source/generated likelihood,
classification, authority relevance, and large-file HOLD flag.

Git could not inspect the pre-existing `.pytest_cache/` directory because the
operating system denied access. It was not counted among the 4,616 files and is
now covered by the standard generated-cache ignore rule. No attempt was made to
open, modify, or delete it.

## Authority-document roles

The three similarly named Common Rover documents are not byte-identical copies:

- `CURRENT_COMMON_ROVER_AUTHORITY.md`: primary repository-root design pointer.
- `docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md`: compact docs-local pointer.
- `rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md`: compatibility pointer under the historical rover namespace.

All three point to the same explicitly declared v0.9.2.1 design authority. The
ChatGPT index is the primary entry for physical and component-level precedence.
