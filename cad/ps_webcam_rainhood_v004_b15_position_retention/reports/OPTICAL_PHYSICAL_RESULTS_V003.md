# v003 optical physical results — inherited authority

These results are user-provided physical observations and are not inferred from CAD.

## Candidate A — setback 10 mm / one rib

- Normal top FOV intrusion: YES
- Result: `FAIL_OPTICAL`
- Selection: `REJECTED`

## Candidate B — setback 15 mm / two ribs

- Normal top FOV intrusion: NONE
- Lateral/mount-shift top intrusion: YES
- Result: `NOMINAL_OPTICAL_PASS / SHIFT_OPTICAL_FAIL`
- Selection: `SELECTED_CONDITIONAL`
- Prohibited interpretation: not `OPTICAL_ROBUST_PASS`

## Candidate C — setback 20 mm / three ribs

- Normal top FOV intrusion: NONE
- Lateral-shift top intrusion: NONE
- Result: `OPTICAL_ROBUST_PASS`
- Selection: `KNOWN_FALLBACK`

v004 preserves the B optical front and tests mechanical position retention. It does not invalidate the C fallback.

