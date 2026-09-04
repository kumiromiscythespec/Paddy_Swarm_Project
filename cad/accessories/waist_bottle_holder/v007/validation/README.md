# BH_V007 validation method

`source/build_bh_v007.py`は生成後に次を検証します。

- STEP再読込、B-rep validity、正体積
- STL watertight、non-manifold edge、winding、正体積、shell数
- duplicate solid signatures
- cup、drain、rope slotのV006 non-regression
- ID26.2 C-ring gauge
- 16 x 4 x 30 mm long tabと4 mm ruled nose
- 17.1 x 4.8 mm hold cutter、34 mm receiver、6 mm entry loft
- +42 mmからnominal seatまでのZ直線挿入経路
- nominal main/collar intersection
- rounded-square bodyからphi26.2 neckへ遷移する保守的bottle shoulder envelope
- cup/bottle centerlineとreceiver/tab X alignment
- receiver/spine fused overlapと前方突出量
- 38 x 8.5 spine、R10 root、4.5 mm rib x2
- 0.5 mm floatとcup-bottom load support
- phi34 mm cap envelope
- coupon fixtureにactual upper structureがすべて含まれること
- Bambu A1 Z envelope
- V006/V007 section、protrusion、length、volume比較
- start/end Git branch、HEAD、pre-existing tracked status

Upper couponとassembly previewは意図した2 shellです。V007 physical state 8件はCADだけでPASSへ変更しません。
