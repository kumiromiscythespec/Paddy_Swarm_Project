# ACOUSTIC RAIN-NOISE RECORD

Status: `TPU_RAIN_NOISE_REDUCTION_PHYSICAL_PASS = PENDING`

## Authority observation

現行v004 rainhoodの屋外YouTube Live試験中、小規模な通り雨で雨滴がbare PETG roofへ衝突する人工的な「カチカチ」という打撃音がcamera microphoneへ明瞭に入った。

```text
BARE_PETG_RAIN_IMPACT_NOISE: OBSERVED
LIGHT_RAIN: AUDIBLE_CLICKING
HEAVY_RAIN: UNTESTED
HEAVY_RAIN_RISK: POTENTIAL_HIGH_NOISE_RISK
```

この観察はv005要求の根拠であり、TPU効果のPASS証拠ではない。

## Signal intent

Reduce:

```text
PETG_ROOF_IMPACT_CLICK
```

Preserve:

```text
rice-field ambient sound
insects
wind
natural rainfall
water
rover/mechanical field sound
```

## Coupon comparison record

未試験欄をPASSとして扱わない。

| Sample | High-frequency click | Low-frequency thump | Natural ambient | TPU flutter | Result |
|---|---|---|---|---|---|
| BARE PETG | HIGH observed in light field rain | UNRECORDED | NORMAL/field reference | N/A | REFERENCE |
| TPU 1.0 mm | UNTESTED | UNTESTED | UNTESTED | UNTESTED | PENDING |
| TPU 1.5 mm | UNTESTED | UNTESTED | UNTESTED | UNTESTED | PENDING |
| TPU 2.0 mm | UNTESTED | UNTESTED | UNTESTED | UNTESTED | PENDING |

## Full-skin record

```text
FILAMENT / LOT: NOT YET RECORDED
TPU SHORE: UNKNOWN_PHYSICAL
SELECTED THICKNESS: 1.5 mm CAD CANDIDATE
PRELOAD: 0.5% X/Y CAD CANDIDATE
FULL CONTACT: UNTESTED
PETG ARTIFICIAL CLICK CLEARLY REDUCED: UNTESTED
NATURAL AMBIENT PRACTICALLY PRESERVED: UNTESTED
FLUTTER: UNTESTED
LIGHT RAIN: UNTESTED WITH TPU
HEAVY RAIN: UNTESTED
WIND-DRIVEN RAIN: UNTESTED
LONG-DURATION ACOUSTIC BEHAVIOR: UNTESTED
```

## Acceptance rule

人工的なPETG clickingが明瞭に低減し、自然環境音が実用上失われず、TPU flutter/slapが新しい主要音源にならない場合だけ`TPU_RAIN_NOISE_REDUCTION_PHYSICAL_PASS`へ更新する。完全無音は要求しない。

