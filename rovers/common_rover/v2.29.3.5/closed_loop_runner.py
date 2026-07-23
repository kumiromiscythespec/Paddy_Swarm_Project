"""Compatibility API delegating to the v2.29.3.5 single full-loop authority."""

from __future__ import annotations

from full_loop_runner import (
    EXIT_CODES,
    STAGES,
    run_full_loop,
    run_static_authority,
)


def run_static_preflight(registries, source_root, output_root=None):
    return run_static_authority(registries, source_root)


def run_cad_stage(registries, source_root, output_root, stage):
    return run_full_loop(
        registries,
        source_root,
        output_root,
        stage=stage,
        review_receipt=None,
    )
