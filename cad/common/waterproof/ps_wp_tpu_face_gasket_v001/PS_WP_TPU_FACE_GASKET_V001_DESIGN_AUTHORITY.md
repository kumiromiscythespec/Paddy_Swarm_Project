# PS-WP-TPU-FACE-GASKET-V001 design authority

Common-interface CAD development only. Physical gasket/compression/water performance remains pending.

- One common PETG body:80 x80 x28.5 mm nominal; one common lid80 x80 x6.
- Local floor undersideZ0; seal datumZ28.5. Cavity48 x48 x25; actual primary closed dry-air volume 63.142246 mL using a closure surrogate, not water simulation.
- Lower wall/floor3.5 mm. Outer45-degree flare terminates under a1 mm flat cap supporting the10 mm seal land.
- G20/G25/G30: flat active band5 mm, nominal free thickness2/2.5/3; same centerline58 x58 R6.5. OuterR9, innerR4. Perimeter 220.840704 mm. No cord groove, split or butt joint.
- Two external TPU ears0.8 thick; round8.6 hole and radial10.6 x8.6 slot register on removable stop OD8.0. No adhesive required. Full assembly including ears approximately81.707107 x81.707107 x36.5 for G25/S20.
- Four M4 through locations(+/-34,+/-34), bore4.5, exterior body lug thickness8. Stops OD8/bore4.5; S16/S18/S20/S22/S24 working thickness1.6/1.8/2/2.2/2.4. No integrated permanent gap stop. Body/lid reprint is not required for variant exchange.
- Primary G25/S20 gives nominal20%, not measured physical compression. Stop working faces do not clamp TPU ears.

Lid selection calculation: for an80 mm-wide strip, I=b*t^3/12 is426.666667 mm4 at4 mm,833.333333 at5 mm and1440 at6 mm. At equal material/span,6 mm has3.375 times the bending section stiffness of4 mm. Select6 mm within the requested4-6 range. Printed modulus, bolt force, warp and absolute deflection are unknown; this is not a pressure/stiffness qualification. Measure four closed gaps and test uniform seating.

CAD geometric isolation and measured exported dimensions are recorded in validation_report.json; negative+0.10 mm regressions cover every gasket and spacer. Separate STEP reload, STL topology/connectivity and byte reproduction checks are mandatory.
All pressure-boundary penetrations:0. M4/stop intersection with active seal:0. Closure-air separation is only a check that no intentional geometric path exists. FDM porosity, surface condition, TPU behavior and permanent set require actual tests.

Geometry avoids support on seal faces/gaskets/stops. External body ears may need supports; slicer NOT RUN. Stop/gasket measurement and dry-cycle tests precede water testing.

CAD_PASS/CONTRACT_TEST_PASS/PS_WP_TPU_FACE_GASKET_DUMMY_PRINT_READY/G25_S20_PRIMARY_TEST_READY/WATER_PHYSICAL_TEST_PENDING/BBOX_V005_PENDING/CBOX_FIELD_BOX_PENDING

These CAD labels apply only with contract_test_report PASS and builder --verify PASS. They do not mean TPU_WATERPROOF_PASS.
