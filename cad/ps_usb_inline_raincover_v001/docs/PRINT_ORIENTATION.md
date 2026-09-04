# PRINT ORIENTATION

Printer: Bambu Lab A1  
Material: PETG  
Nozzle: 0.4 mm  
Layer: 0.20 mm

Initial process: walls >=4、top/bottom >=5、infill 25–35%。dry PETG、強いlayer bonding、perimeter優先。寸法補正前にcouponを印刷する。

## Cable channel coupons

平らな底面をbedへ置き、半円grooveを上向きにする。supportなし。edge notchを潰す強いelephant footを避ける。small/largeは同一plate可。

## Connector chamber fit coupon

STLにupper/lower 2 bodiesを離して配置済み。lowerはflat outside bottomをbedへ。upper couponはroof外面側をbedへ向けたprint layoutだが、3°面のfirst-layer接触をpreviewし、必要なら長側面へ回転する。tongue/grooveへsupportを生成しない。

## Labyrinth drain coupon

Flat lower outside bottomをbedへ、open sectionを上へ。2.5 mm drainはbuild Z方向。supportなしを第一候補とし、drain first layersとbaffle passageをslice previewする。造形後に2.5 mm gaugeまたは手回しdrillでstringingだけを除去し、穴径を拡大しない。

## Full lower shell

Flat exterior bottomをbedへ、chamberを上向きにする。これにより2°floor、weep、vestibule、tongueが上向きに積層される。side flange undersideだけに外部supportが必要なら、build plate only/manual supportを限定使用する。以下にはsupport blockerを置く。

- 4.6 mm small passage
- 9.0 mm large passage
- 2.5 mm drains
- low weeps
- drip pockets
- tongue perimeter
- cable saddles
- nut-trap内部

Flange supportは外側から完全除去できること。nut trapへ残渣を押し込まない。

## Full upper shell

Roofを水平bridgeにしないため、長い外側side wallをbedへ置く90°side orientationを第一候補にする。roof面がほぼverticalになり、terminal bafflesも下から連続して造形される向きをslice previewで選ぶ。wide brimを用い、外側M3 lugにだけ必要最小supportを許可する。

禁止:

- chamber開口をbedへ置いてroof全幅をbridgeするorientation
- internal skirt/grooveに除去不能supportを入れる設定
- drainやsmall labyrinth内へtree supportを成長させる設定

## Post-print inspection

```text
WALL DELAMINATION: NONE / YES
ROOF PINHOLE: NONE / YES
PARTING TONGUE STRINGING: NONE / YES
SMALL CHANNEL OPEN: YES / NO
LARGE CHANNEL OPEN: YES / NO
DRAIN 1 OPEN: YES / NO
DRAIN 2 OPEN: YES / NO
NUT TRAPS CLEAN: YES / NO
SHELL CLOSES WITHOUT FORCE: YES / NO
```

Closed meshやwater beadだけでwaterproofと判断しない。print porosity、seam、screw distortionをstaged water testで確認する。

