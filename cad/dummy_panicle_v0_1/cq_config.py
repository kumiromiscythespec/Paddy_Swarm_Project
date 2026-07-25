"""Shared FDM and export settings for the dummy panicle CAD parts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrintConfig:
    """Bambu Lab A1 conservative print envelope and process limits in mm."""

    max_x: float = 240.0
    max_y: float = 240.0
    max_z: float = 220.0
    petg_min_wall: float = 2.0
    tpu_min_wall: float = 0.8
    nozzle_diameter: float = 0.4
    layer_height: float = 0.20


@dataclass(frozen=True)
class ExportConfig:
    """Default tessellation settings for STL export."""

    tolerance: float = 0.05
    angular_tolerance: float = 0.1


@dataclass(frozen=True)
class MaterialDensityConfig:
    """Provisional density settings used only for CAD mass estimates."""

    petg_g_cm3: float = 1.27
    tpu_95a_g_cm3: float = 1.21
    status: str = "ESTIMATE_ONLY_MEASURE_PRINTED_PARTS"


PRINT = PrintConfig()
EXPORT = ExportConfig()
DENSITY = MaterialDensityConfig()


def estimated_mass_g(volume_mm3: float, material: str) -> float:
    """Estimate mass from provisional density; never treat this as measured."""

    densities = {
        "PETG": DENSITY.petg_g_cm3,
        "TPU": DENSITY.tpu_95a_g_cm3,
    }
    try:
        density = densities[material]
    except KeyError as exc:
        raise ValueError(f"unsupported material for mass estimate: {material!r}") from exc
    return volume_mm3 * density / 1000.0
