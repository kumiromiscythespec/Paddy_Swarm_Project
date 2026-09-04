# ps_usb_inline_raincover_v001

Status: `CAD_COMPLETE_USB_RAINCOVER_PHYSICAL_VALIDATION_PENDING`

屋外LIVEカメラのUSB延長中間接続部を、PETG製upper/lower 2分割クラムシェルで覆う初号CADです。完全密閉ではなく、上殻の傘、offset parting labyrinth、下向きcable port、drip vestibule、隔壁、重力排水によって端子室までの水経路を折り曲げます。

Rating: `SPLASH_RESISTANT_NOT_WATERPROOF`

`WATERTIGHT_STL != WATERPROOF_PRINT`

FDMの閉STL、外観、短時間散水だけからIP等級、水没、高圧洗浄、豪雨、長期水密を宣言しません。

## Measured Authority

- Connector maximum width: 18.7 mm
- Small cable OD: 3.6 mm
- Large cable OD: 7.9 mm

Connector body length、height、shape detail、rigid/flexible boundary、strain-relief lengthは`UNKNOWN_PHYSICAL`です。初号chamber 50 x 24 x 16 mmは`PROVISIONAL_PHYSICAL_VALIDATION_REQUIRED`であり、couponの実物結果を優先します。

## Selected architecture

- Upper shell: 3°一方向屋根勾配、6 mm downward overlap skirt。
- Parting line: 2 mm tongue/step、3 mm nominal overlap、0.30 mm FDM clearance。
- Lower shell: chamber中央が0.873 mm高い2°両方向床勾配。
- Small path: 4.6 mm channel for 3.6 mm cable。
- Large path: 9.0 mm channel for 7.9 mm cable。
- Each end: downward port、10 mm drip vestibule、terminal baffle、low weep。
- Drain: 左右最低部に2.5 mm x2、chamber floor weepと横方向offset。
- Closure: chamber外のside flangesへM3 x4、lower側captured hex nut。roof貫通なし。
- Cable support: channel径より0.8 mm大きい緩いsaddle。hard clampなし。

外部からconnector chamberまで直線視通路はありません。upper/lowerはCAD上でsolid interference 0 mm3です。

## Official mounting orientation

長手方向cableをほぼ水平にし、cable portsとdrainを真下へ向けて地面から吊ります。lower側壁下端の3本凹markがDOWNです。地面へ直接置かず、drainの下に排水空間を確保してください。ケーブルにはcover手前で小さいdrip loopを設け、connector jointへ張力を掛けません。

## Mandatory print order

1. `stl/cable_channel_coupon_small_v001.stl`
2. `stl/cable_channel_coupon_large_v001.stl`
3. `stl/connector_chamber_fit_coupon_v001.stl`
4. `stl/labyrinth_drain_coupon_v001.stl`
5. Physical fit/drain validation
6. Coupon gate合格後だけfull upper/lower shells

最初にfull shellを印刷しません。small couponは4.4/4.6/4.8 mm、large couponは8.8/9.0/9.2 mmを比較できます。edge notch 1/2/3本が昇順候補です。

## Initial print settings

- Printer: Bambu Lab A1
- Material: PETG
- Nozzle: 0.4 mm
- Layer: 0.20 mm
- Walls: 4以上
- Top/bottom: 5層以上
- Infill: 25–35%
- 防滴面はinfillよりperimeter、layer adhesion、乾燥したPETGを優先

詳細方位は`docs/PRINT_ORIENTATION.md`を参照してください。drain、small channel、tongue/groove、nut trap内にsupportを残さないでください。

## Physical gates

`CAD_PASS`だけが完了しています。PRINT、FIT、DRAIN、TOP RAIN、45 DEG RAIN、CABLE WATER、HEAVY RAIN FIELD、LONG DURATIONはすべて独立してPENDINGです。connector未接続の着色水試験から始め、dry tests合格後だけcontrolled live USB testへ進みます。

## Regeneration

Lane rootからCadQuery 2.8.0環境で実行します。

```powershell
& 'C:\Users\yu_ki\Miniforge\envs\paddy-cadquery-280-py312\python.exe' cad\ps_usb_inline_raincover_v001.py
```

生成器はSTL、STEP、5枚のsection PNG、parameters、validation、水経路report、SHA256 manifestを再生成し、検証不合格なら終了コード1を返します。

