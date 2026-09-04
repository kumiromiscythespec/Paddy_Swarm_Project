from pathlib import Path
import pytest
from cadquery import importers

from ps_mht_v001_phase3ig_lower_return_buffer.src.export_models import STEP_MODELS
from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import PACKAGE_ROOT


@pytest.mark.parametrize("name,builder", STEP_MODELS.items())
def test_required_step_reloads_valid(name, builder):
    path = PACKAGE_ROOT / "exports/step" / name
    assert path.is_file() and path.stat().st_size > 0
    model = importers.importStep(str(path))
    solids = model.solids().vals()
    assert len(solids) == len(builder().solids().vals())
    assert all(s.isValid() and s.Volume() > 0 for s in solids)

