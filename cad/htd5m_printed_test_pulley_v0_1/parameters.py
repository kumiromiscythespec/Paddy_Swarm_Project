"""Single source of truth for the HTD 5M calibration artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
EXPORT_DIR = PROJECT_DIR / "exports"
REPORT_DIR = PROJECT_DIR / "reports"
FONT_PATH = Path(r"C:\Windows\Fonts\arial.ttf")

CALIBRATION_STATUS = "CALIBRATION_PENDING"

HTD_PITCH_MM = 5.0
PITCH_LINE_DIFFERENTIAL_MM = 0.572
BELT_WIDTH_MM = 15.0
TOOTH_FACE_WIDTH_MM = 16.2
COUPON_TOOTH_COUNT = 6
COUPON_BACKING_THICKNESS_MM = 5.5
STL_LINEAR_TOLERANCE_MM = 0.02
STL_ANGULAR_TOLERANCE_RAD = 0.10

GAUGE_OUTER_EDGE_CHAMFER_MM = 0.5
GAUGE_HOLE_ENTRY_CHAMFER_MM = 0.3
GAUGE_ENGRAVING_DEPTH_MM = 0.35
COUPON_ENGRAVING_DEPTH_MM = 0.35

# Public design-input names retained exactly as stated in the calibration brief.
HTD_PITCH = HTD_PITCH_MM
BELT_WIDTH = BELT_WIDTH_MM
TOOTH_FACE_WIDTH = TOOTH_FACE_WIDTH_MM
BORE_6_CANDIDATES = [6.00, 6.10, 6.20, 6.30, 6.40]
BORE_10_CANDIDATES = [10.00, 10.10, 10.20, 10.30, 10.40, 10.50]
PROFILE_CLEARANCES = {
    "tight": 0.05,
    "standard": 0.10,
    "loose": 0.15,
}
PULLEY_CASES = {
    "20t": {"tooth_count": 20, "nominal_bore": 6.00},
    "60t": {"tooth_count": 60, "nominal_bore": 10.00},
}
EXPECTED_PITCH_DIAMETERS_MM = {
    20: 31.830988,
    60: 95.492966,
}
REFERENCE_OUTSIDE_DIAMETERS_MM = {
    20: 30.69,
    60: 94.35,
}


@dataclass(frozen=True)
class BoreGaugeSpec:
    key: str
    nominal_mm: float
    candidates_mm: tuple[float, ...]
    thickness_mm: float
    center_spacing_mm: float
    minimum_edge_wall_mm: float
    width_mm: float
    label_offset_y_mm: float
    label_size_mm: float

    @property
    def center_span_mm(self) -> float:
        return (len(self.candidates_mm) - 1) * self.center_spacing_mm

    @property
    def length_mm(self) -> float:
        return self.center_span_mm + max(self.candidates_mm) + 2.0 * self.minimum_edge_wall_mm

    @property
    def hole_centers_x_mm(self) -> tuple[float, ...]:
        start = -0.5 * self.center_span_mm
        return tuple(start + index * self.center_spacing_mm for index in range(len(self.candidates_mm)))


BORE_GAUGES: tuple[BoreGaugeSpec, ...] = (
    BoreGaugeSpec(
        key="htd5m_bore_gauge_6mm_v0_1",
        nominal_mm=6.0,
        candidates_mm=tuple(BORE_6_CANDIDATES),
        thickness_mm=8.0,
        center_spacing_mm=14.0,
        minimum_edge_wall_mm=3.0,
        width_mm=20.0,
        label_offset_y_mm=5.2,
        label_size_mm=2.0,
    ),
    BoreGaugeSpec(
        key="htd5m_bore_gauge_10mm_v0_1",
        nominal_mm=10.0,
        candidates_mm=tuple(BORE_10_CANDIDATES),
        thickness_mm=10.0,
        center_spacing_mm=18.0,
        minimum_edge_wall_mm=4.0,
        width_mm=28.0,
        label_offset_y_mm=9.0,
        label_size_mm=2.3,
    ),
)


@dataclass(frozen=True)
class CouponSpec:
    pulley_teeth: int
    fit_key: str
    fit_code: str
    clearance_mm: float

    @property
    def key(self) -> str:
        return f"htd5m_{self.pulley_teeth}t_coupon_{self.fit_key}_v0_1"

    @property
    def id_text(self) -> str:
        return f"{self.pulley_teeth}T-{self.fit_code}"


FIT_CLEARANCES_MM: dict[str, tuple[str, float]] = {
    "tight": ("T", PROFILE_CLEARANCES["tight"]),
    "standard": ("S", PROFILE_CLEARANCES["standard"]),
    "loose": ("L", PROFILE_CLEARANCES["loose"]),
}

COUPONS: tuple[CouponSpec, ...] = tuple(
    CouponSpec(pulley_teeth, fit_key, fit_code, clearance_mm)
    for pulley_teeth in (20, 60)
    for fit_key, (fit_code, clearance_mm) in FIT_CLEARANCES_MM.items()
)

EXPECTED_EXPORT_STEMS = tuple(spec.key for spec in BORE_GAUGES) + tuple(spec.key for spec in COUPONS)
OPTIONAL_COMBINED_STEP_STEMS = (
    "htd5m_bore_gauges_plate_v0_1",
    "htd5m_tooth_coupons_plate_v0_1",
    "htd5m_calibration_all_plate_v0_1",
)
