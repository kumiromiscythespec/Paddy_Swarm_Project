from __future__ import annotations

import math
from typing import Mapping

from authority_loader import AuthorityParameters, Envelope


SIMPLIFIED_TSLOT_AUTHORITY_ENVELOPE = "SIMPLIFIED_TSLOT_AUTHORITY_ENVELOPE"


def require_cadquery():
    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError("CADQUERY_ENVIRONMENT_HOLD") from exc
    return cq


def validate_envelope_values(envelope: Envelope) -> None:
    values = (*envelope.minimum, *envelope.maximum)
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{envelope.component_id}: NONFINITE_PARAMETER")
    if any(dimension <= 0.0 for dimension in envelope.dimensions):
        raise ValueError(f"{envelope.component_id}: NONPOSITIVE_DIMENSION")


def build_rectangular_envelope(envelope: Envelope):
    validate_envelope_values(envelope)
    cq = require_cadquery()
    dx, dy, dz = envelope.dimensions
    return (
        cq.Workplane("XY")
        .box(dx, dy, dz, centered=(False, False, False))
        .translate(envelope.minimum)
        .val()
    )


def build_simplified_tslot_envelope(envelope: Envelope):
    return build_rectangular_envelope(envelope)


def build_minimum_assembly(
    parameters: AuthorityParameters,
) -> Mapping[str, object]:
    tslot_ids = {
        "V22939-FPB-RAIL-L",
        "V22939-FPB-RAIL-R",
        "V22939-FPB-FRONT-XMEMBER",
    }
    return {
        envelope.component_id: (
            build_simplified_tslot_envelope(envelope)
            if envelope.component_id in tslot_ids
            else build_rectangular_envelope(envelope)
        )
        for envelope in parameters.components
    }
