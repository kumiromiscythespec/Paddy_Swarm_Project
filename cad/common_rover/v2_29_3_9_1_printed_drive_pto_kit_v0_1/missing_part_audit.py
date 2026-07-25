from __future__ import annotations


ALLOWED_STATUSES = {
    "REQUIRED",
    "OPTIONAL",
    "PURCHASED_METAL_PART_REPLACES_THIS",
    "PRINTED_TEST_ONLY",
    "HOLD",
}


AUDIT_ROWS: tuple[dict[str, str], ...] = (
    {"item": "motor shaft split clamp", "status": "REQUIRED", "resolution": "Integrated in DRIVE-L/R 20T pulley; metal bolt or insert required"},
    {"item": "output hub adapter", "status": "REQUIRED", "resolution": "Generated unique DRIVE-L/R sacrificial PCD24 adapters"},
    {"item": "PTO shaft clamp", "status": "PRINTED_TEST_ONLY", "resolution": "Generated unique PTO-A/B split-clamp hub adapters; shaft measurement pending"},
    {"item": "pulley flange", "status": "REQUIRED", "resolution": "Pulley integral flanges plus unique removable 60T flange candidates"},
    {"item": "belt side guide", "status": "REQUIRED", "resolution": "Integral pulley flange; removable 60T outer flange candidate"},
    {"item": "shaft spacer", "status": "REQUIRED", "resolution": "Generated four unique labeled spacer candidates"},
    {"item": "center distance gauge", "status": "REQUIRED", "resolution": "Generated 112-130 mm parameterized gauge"},
    {"item": "pulley alignment gauge", "status": "REQUIRED", "resolution": "Generated face alignment gauge"},
    {"item": "parallelism gauge", "status": "REQUIRED", "resolution": "Generated shaft parallelism frame gauge"},
    {"item": "tensioner slider", "status": "REQUIRED", "resolution": "Generated four unique guides with >=12 mm usable stroke"},
    {"item": "tensioner idler", "status": "PURCHASED_METAL_PART_REPLACES_THIS", "resolution": "Use metal bearing, bolt, washers, and locknut; print is not bearing race"},
    {"item": "tension adjustment knob", "status": "OPTIONAL", "resolution": "Generated hand knob; metal nut or insert required"},
    {"item": "sacrificial torque fuse", "status": "PRINTED_TEST_ONLY", "resolution": "Generated geometry candidate; release torque calibration pending"},
    {"item": "belt guard", "status": "REQUIRED", "resolution": "Generated four temporary guards with parameterized mounting slots"},
    {"item": "shaft end guard", "status": "REQUIRED", "resolution": "Generated temporary cover; final mounting interface hold"},
    {"item": "motor slide drilling template", "status": "PRINTED_TEST_ONLY", "resolution": "Generated transfer template; do not drill before frame measurement"},
    {"item": "bearing block drilling template", "status": "PRINTED_TEST_ONLY", "resolution": "Generated transfer template; do not drill before authority confirmation"},
    {"item": "TPU belt joining jig", "status": "REQUIRED", "resolution": "Generated hand-fit jig; joiner never approved for powered use"},
    {"item": "belt storage fixture", "status": "OPTIONAL", "resolution": "Generated labeled storage fixture"},
    {"item": "main shaft", "status": "PURCHASED_METAL_PART_REPLACES_THIS", "resolution": "phi10 metal shaft required"},
    {"item": "bearing and pillow block", "status": "PURCHASED_METAL_PART_REPLACES_THIS", "resolution": "Purchased metal bearing and block required"},
    {"item": "high-load bolts nuts washers", "status": "PURCHASED_METAL_PART_REPLACES_THIS", "resolution": "Do not replace with printed hardware"},
    {"item": "electrical terminals", "status": "PURCHASED_METAL_PART_REPLACES_THIS", "resolution": "Do not replace with printed parts"},
    {"item": "PTO-A final continuous belt", "status": "HOLD", "resolution": "Center distance, shaft diameter, and usable shaft length unconfirmed"},
    {"item": "PTO-B final continuous belt", "status": "HOLD", "resolution": "Center distance, shaft diameter, and usable shaft length unconfirmed"},
)


def validate_audit() -> dict[str, object]:
    invalid = [
        row for row in AUDIT_ROWS if row["status"] not in ALLOWED_STATUSES
    ]
    duplicates = sorted(
        {
            row["item"]
            for row in AUDIT_ROWS
            if sum(item["item"] == row["item"] for item in AUDIT_ROWS) > 1
        }
    )
    if invalid or duplicates:
        raise ValueError(
            f"INVALID_MISSING_PART_AUDIT:invalid={invalid}:duplicates={duplicates}"
        )
    return {
        "status": "COMPLETE",
        "row_count": len(AUDIT_ROWS),
        "allowed_statuses": sorted(ALLOWED_STATUSES),
    }


validate_audit()
