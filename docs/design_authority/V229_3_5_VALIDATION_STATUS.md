# Common Rover v2.29.3.5 Validation Status

## Artifact authority

Artifact:

`20260723T171141_common_rover_v229_3_5_loop001_hole_authority_full_runner_wiring_closure`

Result bundle SHA-256:

`f95292ffd325ccf6e61382db5cef5f9920ac819fac45557c35f3dcb150460725`

Independent ZIP inspection:

- ZIP entries: 233
- SHA256SUMS targets: 232
- internal hashes matched: 232/232
- proposed source/source snapshot matched: 75/75
- path traversal: 0
- absolute paths: 0
- duplicate entries: 0

## Static verification

- project-reported unit tests: 3,702
- project-reported mutation tests: 620
- deterministic replay: pass
- clean replay: pass
- package final seal: pass

## Runner classification

`FULL_RUNNER_STATUS = STATICALLY_WIRED_NOT_CADQUERY_EXECUTED`

`EXECUTION_RUNNER = EXPERIMENTAL_PREFLIGHT_SOURCE`

The runner must not be represented as an executed or manufacturing-qualified CAD pipeline.

## Current seeds

`EXECUTABLE_UPPER_CAD_SEED = NONE_NOT_EXECUTED`

`MANUFACTURING_CAD_SEED = NONE`
