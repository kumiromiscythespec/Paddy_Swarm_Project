# Geometry and Physical Selection Comparison

## What changed

Only the detachable collar coupon changed. The V007 main body, integrated long-slide receiver, production collar artifacts, and proven 16 x 4 x 30 mm tab remain untouched.

The coupon root replaces the original narrow ring-to-tab transition with:

1. a broad 26 x 16 mm saddle wrapping the rear outside of the phi26.2 bore;
2. R8 plan transitions at the saddle ends;
3. a 10 mm-wide bridge that passes through the existing 10.8 mm receiver stem slot;
4. two 4 x 14 mm rounded gusset rails tying the saddle/bridge to the tab.

The constant-throat B-rep slice increases from 97.947 to 134.000 mm2 (+36.81%). The saddle/bridge/gusset system occupies 4892.11 mm3 in each candidate.

## Why N-B is first

N-B combines the lower insertion demand of the 20 mm opening with the thicker 4 mm ring. Its theoretical total gap expansion is 6.199 mm (3.100 mm per arm under symmetric motion), compared with 8.200 mm for N-A and 21.200 mm for the broken original V007 opening.

N-C keeps the same 20 mm opening but reduces the arm thickness to 3.5 mm. It is a useful compliance comparison, not the first strength recommendation. N-A retains the thicker ring but uses the smaller 18 mm opening to test retention margin.

## Finished-tip authority

R1.5 tip blends enlarge the raw Boolean cut, especially on the 3.5 mm arm. Therefore the source uses calibrated pre-blend cuts:

| Candidate | Raw cut | Finished B-rep minimum | Target |
|---|---:|---:|---:|
| N-A | 17.966 | 18.0004 | 18.0 mm |
| N-B | 19.925 | 20.0008 | 20.0 mm |
| N-C | 19.705 | 20.0010 | 20.0 mm |

The validator searches the first solid boundary from the centerline at three mid-height free-tip stations. This avoids accepting an angle or an unfilleted sketch value as proof of opening width.

## Physical decision matrix

| State | N-A | N-B | N-C |
|---|---|---|---|
| Neck insertion / removal fit | PENDING | PENDING | PENDING |
| Root durability / whitening / cracking | PENDING | PENDING | PENDING |

The existing V007 root-strength state is FAIL. That known failure is not a CAD hard failure for this study; it remains visible as comparison evidence. Production authority stays undecided until the six PENDING states are measured.

Suggested physical sequence:

1. Print N-B first, or print the provided 3-up plate.
2. Verify receiver insertion and full vertical travel before loading a bottle.
3. Fit the actual bottle neck and inspect the R1.5 tips, arm whitening, and root.
4. Repeat insertion/removal, then run the intended bounce/pull durability cycle.
5. Compare N-A retention against N-B, and use N-C only to determine whether extra compliance is needed.

## CAD validation summary

- 27 CAD checks PASS, 0 CAD FAIL.
- STEP reload: all positive-volume valid solids.
- STL: all watertight, zero boundary edges, zero non-manifold edges, positive signed volume.
- All three eight-station vertical slide paths are collision-free against the existing V007 main body.
- Protected V007 main/collar STEP, STL, parameters, and source SHA-256 hashes are unchanged.
- Combined evidence state: 27 PASS / 1 known physical FAIL / 6 PENDING.

