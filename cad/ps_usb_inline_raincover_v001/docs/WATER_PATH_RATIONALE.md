# WATER PATH RATIONALE

Rating: `SPLASH_RESISTANT_NOT_WATERPROOF`

## Path hierarchy

```text
rain / splash
  -> 3 deg upper roof
  -> 6 mm downward umbrella skirt
  -> offset 2 mm tongue/groove step
  -> baffled connector chamber

cable-tracked water
  -> local downward cable segment
  -> drip vestibule
  -> low pocket
  -> offset 2.5 mm drain
  -> gravity discharge
```

完全sealではなく、端子へ届く前に水を外面またはdrip vestibuleへ落とし、最低点から排出する。

## Failure modes

### TOP RAIN

Roof上に穴を設けず、3°で一方向へ排出する。parting seamはroof edgeより内側かつ6 mm skirtの上側に隠れる。証拠はtop spray。

### SIDE RAIN

Side waterがchamberへ達するにはskirt下端を上へ回り、0.30 mm clearanceのoffset grooveを通り、2 mm tongueを越える必要がある。M3 flange notchはこのlabyrinth外側にある。証拠は45°/side spray。

### WIND-DRIVEN RAIN

各endのterminal baffleはlower floorからupper roofまで続き、cable用低位置passage以外の直進を止める。強風時の圧力差、mist、bounceはCADで証明できないためfield PENDING。

### CABLE-TRACKED WATER

Cableはcover直前で下向きに転向し、10 mm vestibuleを通る。water filmはconnector側へ上がる前にpocketへ落ちる。hard gasketではないためcable-water testが必要。

### BOTTOM SPLASH

Drainはconnector chamber外側のvestibuleに開き、baffleと位置offsetによりdrain軸からconnectorへ直線視通路がない。下からdrainへ高圧jetを当てる用途は対象外。

### WATER POOLING

Chamber floorはcenter crown 0.873 mmから両endへ2°で落ちる。baffle下のlow weepからz=-0.75 mm pocketへ落ち、左右2.5 mm drainで排出する。取付傾斜、PETG stringing、mud blockageは実物確認する。

### CAPILLARY ENTRY

Overlap長と方向変換で経路を延ばすが、FDM layer、汚れ、長時間wettingではcapillary transportがあり得る。multi-hour testまでLONG_DURATION PASSを出さない。

## Direct-line review

- Roof-to-chamber: none; continuous roof.
- Side-to-chamber: none; skirt plus tongue/groove.
- Downward port-to-connector: none; 10 mm horizontal offset and terminal baffle.
- Drain-to-connector: none; x outside chamber、Y-offset weep、terminal baffle。

このreviewは流体解析、IP test、storm certificationではない。

## Installation dependencies

- Suspended above ground。
- Drains and cable ports downward。
- Cable approximately horizontal outside with a local drip loop。
- Drain clearance maintained。
- M3 screws seated evenly without shell distortion。
- Periodic inspection for mud、insects、algae、PETG cracks。

## v002 TPU fallback

吹込みが残る場合はreplaceable TPU slit bushingを検討する。ただしconnector chamberを完全sealせず、drainとair escapeを維持する。

