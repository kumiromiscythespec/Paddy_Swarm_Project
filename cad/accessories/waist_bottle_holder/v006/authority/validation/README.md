# Physical Authority validation

`source/build_bh_v006_physical_authority.py`はproduction main、ID26.2 collar、assemblyを生成後、次を検査します。

- STEP再読込、B-rep validity、正体積
- STL watertight、non-manifold edge、winding、正体積
- duplicate solid signature
- nominal assembly intersection
- Z +30 mmから0 mmまでの上差し経路
- closed receiver floor
- ID26.2 gauge
- S3 coupon tabからproduction tabへのsolid転写
- receiver内部実測17.1 x 4.8 mm
- cup、drain、rope slotのnon-regression
- phi34 mm cap envelope
- 0.5 mm floatとcup-bottom load support
- start/end branch、HEAD、既存tracked statusの一致

物理試験のPASSはユーザー提供結果を記録したもので、CADが再判定したものではありません。摩擦保持はfield retention前なので`PASS_CANDIDATE`、残る5項目は`PENDING`です。
