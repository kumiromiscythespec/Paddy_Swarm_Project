# Historical dimension precedence audit

Precedence for the current as-built rover:

DIRECT_PHYSICAL_2026_09_01 > older physical/derived mounting assumptions > CAD-only/provisional.

| Value/source | Previous classification | Current disposition | Reason |
|---|---|---|---|
| BBOX lid/frame top Z257 in BBOX v002/v003/v004 | DERIVED_MOUNT_ASSUMPTION / CAD | SUPERSEDED_FOR_CURRENT_AS_BUILT_2026_09_01 | direct BBOX lid highest Z254 and rail tops Z255/254 |
| upper rail centers Y=±100.5 in narrow-frame v0.9.6.6 | CAD_ONLY / derived outboard move | SUPERSEDED_FOR_CURRENT_AS_BUILT_2026_09_01 | direct spans give center separation 188–190 but no absolute Y origin |
| upper rail centers Y=±80.5 in earlier frame lanes | CAD_ONLY / DERIVED_MOUNT_ASSUMPTION | SUPERSEDED_FOR_CURRENT_AS_BUILT_2026_09_01 | same reason; do not promote ±94.5 |
| drive shaft Z178 in v0.9.4.0 | PROVISIONAL | PROVISIONAL_OBSOLETE | direct physical 122/123 record already supersedes it |
| drive shaft Z175 in v0.9.6.6 | CAD_ONLY | CAD_ONLY_NOT_PHYSICAL_AUTHORITY | direct physical nominal 122.5 |
| drive shaft Z122/123, nominal122.5 in Front Interface v001/V002 | CURRENT_PHYSICAL | RETAINED_CURRENT_PHYSICAL | reused without duplication conflict |

Historical source files are not deleted or edited. This lane records precedence only.
