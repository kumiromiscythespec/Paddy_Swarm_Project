# Common Rover dual outboard PTO guard interface v0.9.6.38

## Width arithmetic

| frame | pulley bodies only | guarded reference | target margin | 286 ceiling margin |
|---:|---:|---:|---:|---:|
| 200 | 240 | 258 | 7 | 28 |
| 205 worst case | 245 | 263 | 2 | 23 |

Each side uses 2 mm gap candidate + 20 mm pulley usable authority + 4 mm retention candidate + 3 mm guard candidate = 29 mm. The 200 mm frame has 5 mm additional total margin. `TARGET_WIDTH<=265`; registered ceiling remains `<=286`. The 286 mm record is not an actual-solid release.
