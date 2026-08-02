"""Exploded Phase 3R split planting-port reference."""

from __future__ import annotations

from ps_mht_v001.assembly.planting_port_phase3r import (
    build_planting_port_phase3r,
)


def build_port_exploded_phase3r():
    return build_planting_port_phase3r(exploded_gap=12.0)
