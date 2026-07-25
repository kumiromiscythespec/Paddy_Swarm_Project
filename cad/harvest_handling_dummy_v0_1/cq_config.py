"""Independent print and export settings for HHD-V001."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrintConfig:
    """Bambu Lab A1 conservative printable envelope and process limits."""

    max_x_mm: float = 240.0
    max_y_mm: float = 240.0
    max_z_mm: float = 220.0
    nozzle_diameter_mm: float = 0.4
    layer_height_mm: float = 0.20
    petg_min_wall_mm: float = 2.0


@dataclass(frozen=True)
class ExportConfig:
    """STL tessellation settings."""

    linear_tolerance_mm: float = 0.05
    angular_tolerance_rad: float = 0.1


PRINT = PrintConfig()
EXPORT = ExportConfig()
