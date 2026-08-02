# PS-MHT-V001 Phase 3H-A Physical Test Plan

Status: `CALIBRATION_PENDING`  
Scope: horizontal joint and external test fixture only

## Geometry under test

- Nominal body: OD 200 mm, ID 194 mm, structural wall 3 mm.
- Axial contribution: 40 mm per band.
- Upper physical print height: 50 mm, including 10 mm overlap skirt.
- Lower physical print height: 40 mm.
- Skirt: 2.8 mm nominal, 2.4 mm intentional tip minimum, R3 continuous root.
- Candidate radial-per-side clearances: c030, c050 and c070.
- Selected clearance: `None` until a full-ring physical test passes.

The 10 mm skirt is an overlap and is not added twice to assembled stack
height. The future 25/40/40/40/25 band contributions therefore total 170 mm.

## Print sequence

1. Print `horizontal_joint_arc_coupon_c050_phase3ha.stl`.
2. If c050 is loose, print c030; if it is tight, print c070.
3. After an arc passes, generate the matching full-ring pair with an explicit
   clearance argument.
4. Print two copies of the common compression ring.
5. Do not print the assembly references or temporary membrane reference.

All ring parts print flat with continuous bed contact. The upper specimen STL
is already oriented skirt-up. Initial slicing uses no supports.

## Full-ring evaluation

### A. Assembly

- No tools or impact.
- Verify full-circumference hard-stop seating and no local binding.
- Record axial play, radial play and assembly time.

### B. Compression

- Install three purchased M4 threaded rods, washers and nuts at 60/180/300°.
- Tighten incrementally and evenly until the hard stop seats.
- Do not crush PETG; record height before and after tightening.

### C. Repetition

- Complete ten disassembly/reassembly cycles.
- Inspect whitening, cracks, edge chipping, wear and permanent deformation.
- Record play growth and assembly-force change.

### D. Static leak

- Use a purchased PE or silicone membrane; do not use a printed bottom wall.
- Separate membrane leakage from horizontal-seam leakage.
- Hold water 20 mm above the joint for 12 hours.
- Pass: no continuous jet and leakage no greater than 5 mL/joint/12 h.

### E. Flow-down

- Flow 2 L down the inner wall at approximately 1 L/min.
- Record direct outside discharge and water travelling on the outer seam.
- Confirm discharge from the skirt to the lower-ring interior.

### F. Compression hold

- Hold for 24 hours.
- Record creep, permanent deformation, disassembly and reassembled play.

## Selection rule

c050 is preferred when it passes all criteria. Test c030 if c050 leaks or has
excessive play. Test c070 if c050 cannot be assembled or causes whitening. An
arc coupon alone never selects the clearance.

## Excluded authority

This calibration does not authorize a planting port, net-pot seat, buffer,
overflow, drain, wick, root ring, production M4 route, 170 mm module, water
system or five-stage tower. The compression fixture is `TEST_FIXTURE_ONLY`.
