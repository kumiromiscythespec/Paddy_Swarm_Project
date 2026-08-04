# README_HANDOFF — v0.9.3.4

Standalone trade-study package comparing outboard crossmember end-tap joints and underside 3 mm full-width tie plates. It incorporates the latest two-plain-washer/one-height-nut M5×16 stack, the 4.3…4.5 mm gap range, full T-nut thread traversal, the primary H4P3…H4P5 height case, and a 24-hour creep plan. The superseded H3P8…H3P9 two-nut case remains historical. It contains 24 STEP files, 19 SVG files, eight CSV reports, source, tests, ledgers, and parent/source provenance.

Run in the validated CadQuery environment:

```text
python -B build_powertrain_frame_joint_trade_study_v0934.py --verify
python -B tests/test_powertrain_frame_joint_trade_study_v0934.py
```

Recommendation: `A_AND_B_PHYSICAL_MOCKUP_REQUIRED`. The latest stack and M5×16 are physical no-load PASS; 24-hour creep remains required before belt tension. No authority, manufacturing, powered, tension, load, or field approval is included.
