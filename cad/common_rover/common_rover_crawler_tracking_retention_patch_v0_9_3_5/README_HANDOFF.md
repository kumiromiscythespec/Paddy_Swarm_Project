# Common Rover crawler tracking retention patch v0.9.3.5

Physical-fit correction lane derived from the tracked crawler_h1 pretest candidate. It preserves 12 teeth, 20.0 mm link pitch, 66.14 mm CAD sprocket OD, tooth profile, source link count candidate, and loop length. The direct drive-sprocket shaft passage becomes exactly 10.1 mm. The 6000-2RS inner race and 26.2 mm printed bearing seat are not silently resized.

The recovery guide uses a 66.7% vertical lower retention zone, a 33.3% upper slope measured from vertical, symmetric forward/reverse geometry, a provisional 40 degree recommendation, 0.4 mm centered clearance per side, and R0.75 mm channel-side apex relief.

Run:

```text
python -B build_crawler_tracking_retention_patch_v0935.py --verify
python -B tests/test_crawler_tracking_retention_patch_v0935.py
```

All STL files are no-load fit-test coupons. No powered, load, manufacturing, mud, water, field, or authority approval is included.
