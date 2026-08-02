# PS-MHT-V001 Test Plan

## Automated Phase 1 gates

1. Required parameters exist and fixed V001 values match the specification.
2. Stack arithmetic equals the nominal 1090 mm tower height.
3. Five module rotations are 0/60/0/60/0 degrees.
4. Planting module is one valid CadQuery solid.
5. Planting module bounding box is 200 x 200 x 170 mm.
6. The printable module fits 245 x 245 x 240 mm.
7. The Phase 1 tower has five separable module solids.
8. Frame and full assembly component solids are valid.
9. Frame base bounding box is 450 x 450 mm.
10. Rear post has positive body clearance and does not cross the root-zone axis.
11. Drain-base envelope contacts the broad aluminium support plane.
12. Exported STEP files re-import with the expected valid-solid counts.
13. Exported STL is non-empty and has no boundary or non-manifold mesh edges.

## Phase 2 automated gates

- One valid module solid inside the A1 envelope
- 6×60-degree indexing and 0/60-degree hole-set invariance
- Three normal M4 axes at 120-degree spacing
- 30-degree minimum M4-to-future-port angular separation
- No normal-use knob at rear 90 degrees
- 0.4 mm/side spigot/socket clearance
- 6.6 mm non-M4 load/contact and compression-stop band
- Gasket-groove separation from the M4 bore
- External cartridge access
- Zero module/module solid overlap at 0 and 60 degrees
- Four A1-safe coupon models
- STEP solid-count/validity and STL closed-manifold checks

## Deferred gates

- Phase 3B: calibrated net-pot fit and production-ready port refinement
- Phase 4: complete drainage, lowest outlet, screen and base capacity
- Phase 5: irrigation rings, hose routing, bend radius and access
- Phase 6: three clamps, pads, knob access, chain collar isolation
- Phase 7: full interference matrix, exploded assembly, BOM and print plates

## Phase 3A automated gates

- 30-degree real module interference and blocked seating; 0/60-degree seating
- Six real male keys, six socket grooves, and real intersection matching
- Six real M4 bore probes, non-hole rejection, and measured boss wall
- Exactly three 0/120/240-degree bores at a 27-degree upward axis
- 60-degree module rotation produces 60/180/300-degree port axes
- Actual radial maximum and three directional maxima stay inside R120 mm
- Zero saddle/saddle, saddle/M4, saddle/knob, and saddle/gasket intersections
- Boolean-contained 4 mm port, 5 mm M3, and 6 mm Phase 3A M4 wall probes
- Net-pot body clearance, flange stop, and common-receiver cap compatibility
- 130 mm service sweeps for pot, adapters, cap, sleeve, finger, and M3 tool
- Zero 0/60 service interference with neighbors and reserved services
- Purchased root envelopes at 0.7–1.0 L and zero pair overlap
- Rear service corridor remains open; 48 mm folded sleeve fits φ72 bore
- All printable parts and calibration coupons fit Bambu Lab A1
- Every STEP re-imports valid and every STL is a closed manifold
- Every captured Phase 1 and Phase 2 output SHA-256 remains unchanged

## Phase 3A.1 automated correction gates

1. Common-adapter center and flange remain open for the full φ66 length.
2. Actual purchased net-pot geometry clears the common adapter and liner.
3. Net-pot bottom reaches the tower-interior side of the receiver.
4. Actual net-pot liner assembles inside the common adapter.
5. Root ring reaches the inner-end datum without adapter overlap.
6. Folded root sleeve clears the ring and common adapter.
7. Root stop transits the common adapter.
8. The complete φ60 passage probe has zero structural intersection.
9. Complete and exploded one-axis references contain 14 valid solids.
10. Old annular M3 retainer is explicitly deprecated.
11. Both independent M3 cartridges have unobstructed external removal sweeps.
12. Cartridge floor prevents root-side metal-nut loss.
13. Normal M3 bolt axis passes the rigid gate capture hole.
14. Both cartridges clear net-pot removal and folded-root envelopes.
15. Actual receiver M3-boss wall probes are fully contained at 5 mm.
16. Actual receiver slot-wall probes are fully contained at 3 mm.
17. Gate minimum thickness is at least 2.4 mm without bend snaps.
18. Tab-inclusive root-ring clearance matches 0.35/0.50/0.70 mm per side.
19. Corrected module remains within the φ240 maximum envelope.
20. All four corrected coupons fit the Bambu Lab A1 envelope.
21. Phase 3A.1 STEP exports re-import with valid expected solid counts.
22. Phase 3A.1 STL exports are closed manifolds.
23. Captured Phase 1, Phase 2 and Phase 3A output SHA-256 values are unchanged.

The suite contains the existing 86 gates plus 28 Phase 3A.1 gates. Test files
may be run in separate fresh processes to prevent cumulative OCCT/VTK native
state from obscuring a geometric failure.

## Phase 3R automated gates

- No deprecated M3/M4 cartridge, L-gate or thin six-key part in new assemblies
- Every independent primary part has at least 200 mm² bed contact
- Every primary ring has at least 15 mm radial width
- Continuous six-lobe ring seats at 0°/60° and interferes at 30°
- Wave-ring continuous root is at least 4 mm thick
- 220 mm annular nut and clamping rings fit the A1
- Three M4 pockets use 0.15/0.25/0.35 mm calibration without printed gates
- Broad annular contact, not M4 bolts alone, carries vertical load
- Teardrop shell opening has 45° maximum upper faces and no circular datum
- Flat function ring owns CAD roundness and accepts the 78.5 mm flange
- Purchased-pot body diameter remains explicitly calibration-pending
- Backing C-ring clears the root passage and broad drain service gap
- Root-mesh ring is large, flat, continuous and snap-free
- Solid φ3 mm EPDM groove remains separated from M4 holes
- Full printed reference remains within φ240 and all parts within A1
- STEP round-trip, STL manifold and Phase 1–3A.1 SHA gates
- Analytic wave-root curvature radius ≥2 mm and actual gasket/M4 void separation
