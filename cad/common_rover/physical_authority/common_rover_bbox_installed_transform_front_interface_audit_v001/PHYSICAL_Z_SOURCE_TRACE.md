# Physical Z source trace

## Direct source

- Source file: `C:/Users/yu_ki/.codex/attachments/34965dab-05df-4c7c-9cb1-2702e7314258/pasted-text.txt`
- Source SHA-256: `517410358ea2ea1199e3fee0f5519c1eb47792f38cfef64b44cbbb73eb569c1f`
- Source date: `2026-09-01`
- Datum: `CRAWLER_BOTTOM / FLOOR = Z0`
- Context: “current as-built rover” and “current real BBOX assembly measurement”; this supports that the assembly was installed on the current rover when measured.

The source introduces exactly:

```text
BBOX_LID_HIGHEST_Z = 254 mm
BBOX_BODY_LOWEST_Z = 148 mm
BBOX_INSTALLED_Z_ENVELOPE = 254 - 148 = 106 mm
```

The generated dated authority preserves these at:

`cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001/physical_dimensions_2026_09_01.json`

Its wording is “Measured highest BBOX lid point from Z0” and “Measured lowest BBOX body point from Z0.”

## Point-definition audit

The source does **not** state:

- whether `Z254` is the 8 mm flat lid upper surface, the 50 mm chimney top, gland hardware, or another lid feature;
- whether the chimney was installed at the time of measurement;
- whether `Z148` is the printed shell floor, a lug/hard-stop/support feature, or another lowest body-associated component;
- a specimen/lane identifier proving the measured assembly is exactly the V002 body plus V003 lid.

Therefore:

- `BBOX_FLAT_LID_TOP_Z = UNKNOWN`
- `BBOX_CHIMNEY_TOP_Z = UNKNOWN`
- `BBOX_BODY_BOTTOM_Z = 148 mm only at the source's unspecified “lowest body point”`
- `PHYSICAL_POINT_DEFINITION_AMBIGUOUS`
- `BBOX_SPECIMEN_IDENTITY = HOLD`

No reinterpretation of 254 or 148 is made. The reported physical envelope remains protected raw evidence, while its mapping to exact CAD faces remains unresolved.
