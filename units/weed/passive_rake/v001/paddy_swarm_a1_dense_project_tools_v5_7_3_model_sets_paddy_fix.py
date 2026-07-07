#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paddy Swarm A1 Dense Project Tools v5.7.3 Model Sets Paddy fix
TPU tire split / material-aware dense pack / Bambu Studio multi-plate 3MF project writer
v5.7.1 fix: explicit HARD/RIGID manifest rows are no longer reclassified as TPU by notes containing tire/tread words.
v5.7.2 fix: safety phrases such as dummy-weight water test no longer make printable BBOX/CBOX bodies look like reference dummy parts.
v5.7.3 fix: model-dense-set workflow is the Paddy Swarm standard again: rigid_plus_metal, rigid_only, and tpu_only are generated together for complete model printing.

目的:
  既に生成済みの print_manifest*.csv + STL群を読み込み、
  Bambu Lab A1の1プレート内へできるだけ密に再配置した3MFを再生成する。

v3/v4の追加機能:
  - タイヤ/ゴム系部品をTPUプレートへ自動分離
  - それ以外をRIGIDプレートへ分離
  - material列つき manifest / placement CSV 出力
  - material別フォルダ出力:
      3mf_dense_pack_rigid/
      3mf_dense_pack_tpu/
  - all_plates_single_scene_reference.3mf も materialを離して配置
  - v4: Bambu Studioで複数プレートとして開ける単一 project .3mf の生成
  - v4.2: project 3MF内の各plateをワークスペース上のグリッド座標へ物理オフセット
  - v4.3: Bambu/Orcaで観測される約303mm・2列plateグリッドに合わせたabsolute-grid配置と、A1に入らない大型/参照部品の自動除外CSV出力を追加
  - v4.7: Bambu Studio A1テンプレートで観測される3列×縦増加plateグリッドを標準化。template plate数を読み取り、不足plateを警告。
  - v4.8: TPU/硬質材を同一Bambu project 3MFに混在させず、素材別project 3MFを標準出力。
  - v4.9: A1の境界をさらに安全側に見積もるため、デフォルトsafeを200mm、gapを10mmに変更し、Bambu template project配置にplate内側マージンを追加。
  - v5.4: サポート発生を抑えるため、STLを軸直交24姿勢で自動評価し、大きな平面をベッド面へ向ける support-aware orientation を追加。
  - v5.4: Bambu Studioのテンプレートplate数からceil(sqrt(N))で6x6までの正方形グリッド列数を自動推定し、9/16/25/36枚テンプレートの座標ずれを低減。
  - v5.4: support-aware orientation のfit判定を少し広めに取り、220mm級の平置き部品を幅制限で誤って直立させない。
  - v5.4: auto-flat の評価順を修正。低いZ高さを優先し、直立不要な板状/背面フラット部品が立つ問題を抑制。
  - v5.7: 稼動模型向けに3種のdenseセットを一括生成する `--make-model-dense-sets` を追加。
  - v5.7: MCR-L/Rを市販/reference扱いしない。印刷対象が除外された場合は標準で停止する。
          1) rigid_plus_metal: PETG/PLA系硬質部品 + reference_metal_stlを3Dプリント代替部品として追加
          2) rigid_only: PETG/PLA系硬質部品のみ
          3) tpu_only: TPU部品のみ
          目的は、金属ロッドを3Dプリント部品で置き換えた稼動模型/組立検証モデル。

対象:
  - Paddy Swarm Common Tools 系の出力フォルダ
  - rover / transport / harvest / weeding など、manifestに stl / qty / part_id / plate_group があるもの

重要:
  - Bambu Studioの本物の「複数プレートタブ付き3MF」を作る処理ではありません。
  - v2は「密配置された個別3MFプレート」をmaterial別に出力します。
  - 本物のBambu複数プレートプロジェクト化は、Bambu Studio保存済みテンプレート3MFへ差し込む方式が安全です。v4.8では硬質材とTPUは標準で別project 3MFとして出力します。

推奨実行:
  python paddy_swarm_a1_dense_project_tools_v5_1.py --manifest ./rover_v14_out/print_manifest_generic_marked.csv --out ./rover_v14_dense_v4 --group-mode all --split-tpu --make-3mf --make-zip

TPU対象を追加指定:
  python paddy_swarm_a1_dense_project_tools_v5_1.py --manifest ./rover_v14_out/print_manifest_generic_marked.csv --out ./rover_v14_dense_v4 --group-mode all --split-tpu --tpu-pattern WHL --tpu-pattern TIRE --make-3mf --make-zip

必要:
  pip install trimesh numpy networkx lxml
"""

from __future__ import annotations

import argparse
import csv
import math
import zipfile
import json
import copy
import xml.etree.ElementTree as ET
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any


@dataclass
class Item:
    part_id: str
    filename: str
    stl: Path
    plate_group: str
    module: str
    title: str
    instance: int
    qty: int
    w: float
    h: float
    z: float
    material: str
    original_row: dict


@dataclass
class Placement:
    item: Item
    plate_no: int
    plate_name: str
    x: float
    y: float
    rotated: bool
    w: float
    h: float
    pack_w: float
    pack_h: float


@dataclass
class FreeRect:
    x: float
    y: float
    w: float
    h: float


def safe_name(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in s)


def detect_material(row: dict, tpu_patterns: List[str], default_material: str = "RIGID") -> str:
    """
    Returns TPU only for actual rubber tire outer parts.

    v3 policy:
      - TPU: TIR / TIRE / TYRE / TPU / RUBBER
      - RIGID override: HUB / AXL / AXLE / SPC / CLP / GEAR / GEA / PTO / CAP / SHAFT

    This prevents rigid wheel hubs or wheel-axis parts from being moved to TPU plates.
    """
    text = " ".join([
        row.get("part_id", ""),
        row.get("filename", ""),
        row.get("title", ""),
        row.get("module", ""),
        row.get("notes", ""),
    ]).upper()

    rigid_override = [
        "HUB", "AXL", "AXLE", "SPC", "SPACER", "CLP", "CLIP",
        "GEAR", "GEA", "PTO", "CAP", "SHAFT", "PIN", "BUSH", "BEARING"
    ]
    if any(pat in text for pat in rigid_override):
        # Exception: an explicit TPU tire part can still be TPU
        if "TIR" in text or "TIRE" in text or "TYRE" in text or "RUBBER" in text:
            if "HUB" not in text and "AXL" not in text and "AXLE" not in text:
                return "TPU"
        return default_material.upper()

    for pat in tpu_patterns:
        if pat.upper() in text:
            return "TPU"
    return default_material.upper()


def _first_nonempty(row: dict, keys: List[str], default: str = "") -> str:
    for key in keys:
        val = row.get(key, "")
        if val is not None and str(val).strip() != "":
            return str(val).strip()
    return default


def _float_or_zero(value: Any) -> float:
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def compute_mesh_bbox_mm(stl_path: Path) -> Tuple[float, float, float]:
    """Compute axis-aligned bounding box from STL when manifest bbox columns are absent."""
    mesh = load_mesh(stl_path)
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    return float(dims[0]), float(dims[1]), float(dims[2])


def read_manifest(manifest: Path, base_dir: Optional[Path] = None, tpu_patterns: Optional[List[str]] = None) -> List[Item]:
    base_dir = base_dir or manifest.parent
    tpu_patterns = tpu_patterns or ["TIR", "TIRE", "TYRE", "TPU", "RUBBER"]

    rows: List[Item] = []
    with manifest.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            stl_str = _first_nonempty(r, [
                "stl", "stl_file", "stl_path", "file", "filename", "path",
                "file_path", "source_file", "source_path", "output_stl"
            ])
            if not stl_str:
                raise ValueError(f"Manifest row has no STL path: {r}")
            stl_str = stl_str.replace("\\", "/")
            stl_path = Path(stl_str)

            if not stl_path.is_absolute():
                if stl_path.exists():
                    pass
                else:
                    stl_path = base_dir / stl_path
                    if not stl_path.exists() and stl_path.parts and stl_path.parts[0] == base_dir.name:
                        stl_path = base_dir.parent / Path(*stl_path.parts)

            if not stl_path.exists():
                raise FileNotFoundError(f"STL not found for {_first_nonempty(r, ['part_id','part_no','part_code'])}: {stl_path}")

            qty = int(float(_first_nonempty(r, ["qty", "quantity", "count"], "1")))
            w = _float_or_zero(_first_nonempty(r, ["bbox_x", "bbox_x_mm", "size_x", "size_x_mm", "width_mm", "bbox_w", "bbox_l", "width", "w", "footprint_x_mm"]))
            h = _float_or_zero(_first_nonempty(r, ["bbox_y", "bbox_y_mm", "size_y", "size_y_mm", "depth_mm", "bbox_h", "bbox_d", "depth", "h", "footprint_y_mm"]))
            z = _float_or_zero(_first_nonempty(r, ["bbox_z", "bbox_z_mm", "size_z", "size_z_mm", "height_mm", "height", "z"]))
            if w <= 0 or h <= 0 or z <= 0:
                w, h, z = compute_mesh_bbox_mm(stl_path)

            material_hint = _first_nonempty(r, ["material_group", "group", "split_group", "material", "material_hint"], "RIGID").upper()
            is_tpu_flag = r.get("is_tpu", "").strip() in {"1", "true", "TRUE", "yes", "YES"}

            # v5.7.1 Paddy fix:
            # Trust explicit manifest material classification before keyword guessing.
            # The v2.27.3 HQ manifest has HARD parts whose notes mention "tire"
            # only for clearance checks.  The old keyword detector moved those
            # HARD parts into TPU plates.  That breaks RIGID/TPU dense outputs.
            explicit_rigid_hints = {
                "HARD", "RIGID", "PETG", "PLA", "ASA", "ABS",
                "PETG/ASA", "PETG/PLA", "PLA/PETG", "PETG ASA",
            }
            if is_tpu_flag or material_hint == "TPU":
                material = "TPU"
            elif material_hint in explicit_rigid_hints:
                material = "RIGID"
            else:
                material = detect_material(r, tpu_patterns)

            plate_group = _first_nonempty(r, ["plate_group", "plate_id", "plate", "group", "split_group"], "generic")
            part_id = _first_nonempty(r, ["part_id", "part_no", "part_code", "label", "label_text"], stl_path.stem)
            filename = _first_nonempty(r, ["filename", "stl_file", "stl", "file"], stl_path.name)
            module = _first_nonempty(r, ["module", "part_family", "system"], "")
            title = _first_nonempty(r, ["title", "name", "part_name", "label_text"], part_id)

            for i in range(1, qty + 1):
                rows.append(Item(
                    part_id=part_id,
                    filename=filename,
                    stl=stl_path,
                    plate_group=plate_group,
                    module=module,
                    title=title,
                    instance=i,
                    qty=qty,
                    w=w,
                    h=h,
                    z=z,
                    material=material,
                    original_row=r,
                ))
    return rows



# -----------------------------------------------------------------------------
# Support-aware orientation
# -----------------------------------------------------------------------------

def _axis_aligned_rotation_matrices_4x4():
    """Return the 24 right-handed axis-aligned rotation matrices.

    These are safe 90-degree rotations only: no scaling and no mirroring.
    The dense packer uses them to lay flat-backed parts on the build plate
    before 2D packing, reducing supports and often making tall parts fit.
    """
    import itertools
    import numpy as np

    out = []
    seen = set()
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product([-1.0, 1.0], repeat=3):
            m = np.zeros((3, 3), dtype=float)
            for new_axis, old_axis in enumerate(perm):
                m[new_axis, old_axis] = signs[new_axis]
            det = round(float(np.linalg.det(m)))
            if det != 1:
                continue
            key = tuple(int(round(v)) for v in m.flatten())
            if key in seen:
                continue
            seen.add(key)
            t = np.eye(4, dtype=float)
            t[:3, :3] = m
            out.append(t)
    return out


def _matrix_to_jsonable(matrix) -> str:
    import numpy as np
    arr = np.array(matrix, dtype=float)
    return json.dumps(arr.tolist(), separators=(",", ":"))


def _matrix_from_jsonable(value: str):
    if not value:
        return None
    try:
        import numpy as np
        arr = np.array(json.loads(value), dtype=float)
        if arr.shape == (4, 4):
            return arr
    except Exception:
        return None
    return None


def _oriented_mesh_copy(item: Item):
    """Load an STL and apply its precomputed support orientation, if any."""
    mesh = load_mesh(item.stl).copy()
    transform = _matrix_from_jsonable(item.original_row.get("_support_orient_transform", ""))
    if transform is not None:
        mesh.apply_transform(transform)
    mesh.apply_translation(-mesh.bounds[0])
    return mesh


def _bottom_contact_area(mesh, tol: float = 0.35) -> float:
    """Heuristic bottom contact area in mm^2 after orientation.

    We prefer orientations that expose a large, nearly horizontal face at Z-min,
    because these usually need fewer supports and better match "flat back on bed".
    This is intentionally conservative and independent of slicer internals.
    """
    try:
        import numpy as np
        zmin = float(mesh.bounds[0][2])
        centers = mesh.triangles_center
        normals = mesh.face_normals
        areas = mesh.area_faces
        if len(areas) == 0:
            return 0.0
        near_bottom = np.abs(centers[:, 2] - zmin) <= tol
        horizontal = np.abs(normals[:, 2]) >= 0.70
        return float(np.sum(areas[near_bottom & horizontal] * np.abs(normals[near_bottom & horizontal, 2])))
    except Exception:
        return 0.0


def _choose_support_orientation_for_item(
    item: Item,
    safe: float,
    gap: float,
    allow_rotate: bool,
    min_contact_fraction: float = 0.035,
    z_window_ratio: float = 0.25,
    z_window_min_mm: float = 10.0,
    support_fit_safe: float | None = None,
):
    """Choose a 90-degree orientation that reduces supports and still fits A1.

    v5.4 policy:
      1. Prefer orientations that fit a slightly wider orientation-fit square.
         This prevents 220mm-class flat chassis parts from being rejected by an
         overly conservative pack-safe value and then incorrectly stood upright.
      2. Among fitting orientations, first restrict to the low-Z window.
      3. Inside the low-Z window, choose the largest real bottom contact area.
      4. Then prefer lower Z and compact footprint.

    Packing still uses --safe, but orientation selection may use
    --support-orient-fit-safe so flat printable faces are not lost before packing.

    Returns (transform, orient_name, dims_xyz, score_info).
    """
    import numpy as np

    base_mesh = load_mesh(item.stl)
    identity = np.eye(4)
    candidates = []
    fit_safe = max(float(safe), float(support_fit_safe or safe))

    for idx, mat in enumerate(_axis_aligned_rotation_matrices_4x4()):
        mesh = base_mesh.copy()
        mesh.apply_transform(mat)
        mesh.apply_translation(-mesh.bounds[0])
        dims = mesh.bounds[1] - mesh.bounds[0]
        x, y, z = float(dims[0]), float(dims[1]), float(dims[2])
        fits_plain = (x + gap <= fit_safe + 1e-6 and y + gap <= fit_safe + 1e-6)
        fits_rot = allow_rotate and (y + gap <= fit_safe + 1e-6 and x + gap <= fit_safe + 1e-6)
        fits = fits_plain or fits_rot
        contact = _bottom_contact_area(mesh)
        footprint = max(x * y, 1e-6)
        contact_fraction = contact / footprint
        max_side = max(x, y)
        area = x * y
        is_identity = bool(np.allclose(mat, identity))
        candidates.append({
            "idx": idx,
            "mat": mat,
            "name": f"AXIS24_{idx:02d}" if not is_identity else "IDENTITY",
            "dims": (x, y, z),
            "fits": fits,
            "fits_plain": fits_plain,
            "fits_rot": fits_rot,
            "contact_area": contact,
            "contact_fraction": contact_fraction,
            "footprint_area": area,
            "max_side": max_side,
            "is_identity": is_identity,
        })

    if not candidates:
        return identity, "IDENTITY", (item.w, item.h, item.z), {"fits": False}

    fit_pool = [c for c in candidates if c["fits"]]
    pool = fit_pool if fit_pool else candidates

    min_z = min(c["dims"][2] for c in pool)
    z_window = max(z_window_min_mm, min_z * z_window_ratio)
    low_z_pool = [c for c in pool if c["dims"][2] <= min_z + z_window + 1e-6]
    if not low_z_pool:
        low_z_pool = pool

    # Avoid knife-edge candidates when a stable low-Z option exists.
    stable_pool = [
        c for c in low_z_pool
        if c["contact_fraction"] >= min_contact_fraction or c["contact_area"] >= 80.0
    ]
    select_pool = stable_pool if stable_pool else low_z_pool

    # If the CAD-exported orientation is already a low-Z fitting orientation,
    # never replace it with a much taller orientation. This is a guard against
    # flat brackets/plates standing upright in Bambu Studio.
    identity_candidates = [c for c in pool if c["is_identity"]]
    identity_c = identity_candidates[0] if identity_candidates else None

    def score(c):
        x, y, z = c["dims"]
        # Contact first inside the low-Z window, then lower Z.
        contact_score = c["contact_area"]
        if c["contact_fraction"] < min_contact_fraction:
            contact_score *= 0.20
        return (
            1 if c["fits"] else 0,
            contact_score,
            c["contact_fraction"],
            -z,
            -c["max_side"],
            -c["footprint_area"],
            -c["idx"],
        )

    best = max(select_pool, key=score)

    if identity_c is not None and identity_c["fits"]:
        id_z = identity_c["dims"][2]
        best_z = best["dims"][2]
        # Keep identity when it is already within the low-Z window and the
        # alternative would make the part meaningfully taller. This especially
        # protects flat plates and low brackets.
        if id_z <= min_z + z_window + 1e-6 and best_z > id_z + max(8.0, id_z * 0.20):
            best = identity_c

    info = {
        "fits": best["fits"],
        "contact_area": best["contact_area"],
        "contact_fraction": best["contact_fraction"],
        "footprint_area": best["footprint_area"],
        "height_z": best["dims"][2],
        "min_candidate_z": min_z,
        "z_window_mm": z_window,
        "candidate_count": len(candidates),
        "fit_candidate_count": len(fit_pool),
        "low_z_candidate_count": len(low_z_pool),
        "stable_low_z_candidate_count": len(stable_pool),
        "selection_policy": "v5.4_wider_fit_low_z_then_contact",
        "support_fit_safe": fit_safe,
        "pack_safe": safe,
    }
    return best["mat"], best["name"], best["dims"], info


def apply_support_aware_orientation(
    items: List[Item],
    safe: float,
    gap: float,
    allow_rotate: bool,
    out_dir: Path,
    mode: str = "auto-flat",
    support_orient_fit_safe: float | None = None,
) -> List[Item]:
    """Update item bbox dimensions and mesh transform for support-aware printing.

    mode:
      off       : keep STL orientation exactly as exported by CADQuery.
      auto-flat : choose an axis-aligned orientation with large flat bottom and low Z.

    The chosen transform is stored in item.original_row and applied later during
    both individual 3MF export and Bambu template project export.
    """
    if mode == "off":
        rows = []
        for it in items:
            it.original_row["_support_orient_mode"] = "off"
            it.original_row["_support_orient_name"] = "IDENTITY"
            it.original_row["_support_orient_transform"] = _matrix_to_jsonable([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
            rows.append({
                "part_id": it.part_id,
                "mode": "off",
                "orientation": "IDENTITY",
                "bbox_x": round(it.w, 3),
                "bbox_y": round(it.h, 3),
                "bbox_z": round(it.z, 3),
                "note": "support-aware orientation disabled",
            })
        write_csv(rows, out_dir / "support_orientation_report.csv")
        return items

    rows = []
    for it in items:
        old_dims = (it.w, it.h, it.z)
        mat, orient_name, dims, info = _choose_support_orientation_for_item(
            it, safe=safe, gap=gap, allow_rotate=allow_rotate, support_fit_safe=support_orient_fit_safe
        )
        it.original_row["_support_orient_mode"] = mode
        it.original_row["_support_orient_name"] = orient_name
        it.original_row["_support_orient_transform"] = _matrix_to_jsonable(mat)
        it.original_row["_support_old_bbox_x"] = str(old_dims[0])
        it.original_row["_support_old_bbox_y"] = str(old_dims[1])
        it.original_row["_support_old_bbox_z"] = str(old_dims[2])
        it.w, it.h, it.z = float(dims[0]), float(dims[1]), float(dims[2])
        rows.append({
            "part_id": it.part_id,
            "filename": it.filename,
            "material": it.material,
            "mode": mode,
            "orientation": orient_name,
            "old_bbox_x": round(old_dims[0], 3),
            "old_bbox_y": round(old_dims[1], 3),
            "old_bbox_z": round(old_dims[2], 3),
            "new_bbox_x": round(it.w, 3),
            "new_bbox_y": round(it.h, 3),
            "new_bbox_z": round(it.z, 3),
            "height_reduction_mm": round(old_dims[2] - it.z, 3),
            "fits_safe_area": info.get("fits", ""),
            "selection_policy": info.get("selection_policy", ""),
            "pack_safe_mm": info.get("pack_safe", ""),
            "support_fit_safe_mm": info.get("support_fit_safe", ""),
            "min_candidate_z": round(float(info.get("min_candidate_z", 0.0)), 3),
            "z_window_mm": round(float(info.get("z_window_mm", 0.0)), 3),
            "bottom_contact_area_mm2": round(float(info.get("contact_area", 0.0)), 3),
            "bottom_contact_fraction": round(float(info.get("contact_fraction", 0.0)), 4),
            "source_stl": str(it.stl),
        })
    write_csv(rows, out_dir / "support_orientation_report.csv")
    return items


def item_fits_a1(item: Item, safe: float, gap: float, allow_rotate: bool) -> bool:
    """Return True if the item footprint can fit inside the usable A1 square.

    The dense packer can place large parts across multiple plates only if the CAD
    model is already split. It must not silently force an oversized one-piece STL
    onto a plate, because Bambu Studio will show the boundary error and slicing is
    unsafe.
    """
    w1 = item.w + gap
    h1 = item.h + gap
    if w1 <= safe + 1e-6 and h1 <= safe + 1e-6:
        return True
    if allow_rotate and h1 <= safe + 1e-6 and w1 <= safe + 1e-6:
        return True
    return False


def is_reference_or_purchased_dummy(item: Item) -> bool:
    """Identify non-print production references such as purchased waterproof box envelopes.

    v5.7 exception:
      REF-METAL rows created by --make-model-dense-sets are intentionally
      printable plastic surrogates for a low-load working model, so they must
      not be excluded as reference-only objects.
    """
    if (
        item.original_row.get("_dense_set_kind", "") == "printed_metal_replacement"
        or item.original_row.get("_source_kind", "") == "reference_metal_stl"
        or item.plate_group == "A1-HARD-METAL-PRINT"
        or item.part_id.upper().startswith("REF-METAL-")
    ):
        return False

    text = " ".join([
        item.part_id,
        item.filename,
        item.title,
        item.module,
        item.plate_group,
        item.original_row.get("name", ""),
        item.original_row.get("part_name", ""),
        item.original_row.get("notes", ""),
        item.original_row.get("compatibility", ""),
    ]).upper()

    # v5.7.2 Paddy fix:
    # Safety documentation often says "dummy-weight water test" or
    # "dummy weights only".  That word must not turn an otherwise explicit
    # printable BBOX/CBOX body into a reference/dummy part.
    safety_phrase_replacements = [
        "DUMMY-WEIGHT", "DUMMY WEIGHT", "DUMMY_WEIGHTS", "DUMMY WEIGHTS",
        "DUMMY-WEIGHT WATER TEST", "DUMMY WEIGHT WATER TEST",
    ]
    for phrase in safety_phrase_replacements:
        text = text.replace(phrase, "SAFETY-WEIGHT")

    # Keep printable mount rails / locators. Exclude only envelope/reference/dummy
    # objects that represent purchased hardware or design clearance volumes.
    # v5.7: PS-WBX-MCR-L/R names mention "commercial or dual printed boxes",
    # but they are printable cradle rails and must not be filtered out.
    explicit_printable_tokens = [
        "PS-WBX-MCR", "MCR-L", "MCR-R", "MULTI-CRADLE",
        "CRADLE", "RAIL", "LOCATOR", "BRACKET", "CLAMP", "HOLDER",
        "WBASE", "LOWER-FRAME", "DRIVE-", "GBOX-INTERNAL",
        # v5.7.2: G1/G2 fullset printable box bodies are real print targets,
        # even when their safety notes mention dummy-weight water tests.
        "FULLSET-BOX", "BBOX-BDY", "CBOX-BDY", "BOX-BDY",
        "PRINTED WATERPROOF BATTERY/POWER BOX BODY",
        "PRINTED WATERPROOF CONTROL/COMMUNICATION BOX BODY",
    ]
    if any(k in text for k in explicit_printable_tokens):
        return False

    reference_words = [
        "REFERENCE", "DUMMY", "ENVELOPE", "PURCHASED", "COMMERCIAL",
        "市販", "参照", "ダミー", "外形目安", "購入品",
    ]
    if any(k in text for k in reference_words):
        return True

    # Common rover v2.1 old manifest used PS-RV21-WBX for the entire waterproof
    # box envelope. That is not a production print part.
    if item.part_id in {"PS-RV21-WBX", "WBX"}:
        return True
    return False



def is_manifest_print_target(item: Item) -> bool:
    """True when manifest says this row is meant to be printed."""
    row = item.original_row or {}
    values = [
        row.get("printable", ""),
        row.get("print_target", ""),
        row.get("marked", ""),
    ]
    normalized = {str(v).strip().lower() for v in values}
    if normalized & {"1", "true", "yes", "y"}:
        return True
    # Most rows in the common rover print manifest are print targets.  Reference
    # rows generally do not appear here, but keep a conservative fallback.
    if row.get("stl") or row.get("stl_file") or row.get("path"):
        if row.get("material_group", "").upper() != "REFERENCE":
            return True
    return False


def classify_and_filter_items(
    items: List[Item],
    safe: float,
    gap: float,
    allow_rotate: bool,
    out_dir: Path,
    oversize_policy: str = "exclude",
    include_reference_parts: bool = False,
    allow_excluded_print_targets: bool = False,
) -> List[Item]:
    """Filter items before packing and write an audit CSV for excluded parts."""
    kept: List[Item] = []
    excluded: List[dict] = []

    for it in items:
        reasons: List[str] = []
        if not include_reference_parts and is_reference_or_purchased_dummy(it):
            reasons.append("reference_or_purchased_dummy_not_for_print")
        if not item_fits_a1(it, safe=safe, gap=gap, allow_rotate=allow_rotate):
            reasons.append("oversized_for_A1_safe_area")

        if reasons and oversize_policy == "exclude":
            if "reference_or_purchased_dummy_not_for_print" in reasons:
                action = "Do not print as a dense plate part. Use purchased waterproof box/envelope as reference; print only rails, locators, brackets, or split adapters."
            elif "oversized_for_A1_safe_area" in reasons:
                action = "Split this CAD part into smaller printable sections, reduce model size only if it is a non-functional dummy, or keep it as reference-only."
            else:
                action = "Review before printing."
            excluded.append({
                "part_id": it.part_id,
                "filename": it.filename,
                "material": it.material,
                "plate_group": it.plate_group,
                "is_manifest_print_target": "1" if is_manifest_print_target(it) else "0",
                "bbox_x": round(it.w, 3),
                "bbox_y": round(it.h, 3),
                "bbox_z": round(it.z, 3),
                "safe_area": safe,
                "gap": gap,
                "reason": ";".join(reasons),
                "recommended_action": action,
                "source_stl": str(it.stl),
                "notes": it.original_row.get("notes", ""),
            })
        else:
            kept.append(it)

    if excluded:
        write_csv(excluded, out_dir / "oversized_or_reference_parts.csv")
        print(f"[WARN] excluded oversized/reference parts: {len(excluded)} -> {out_dir / 'oversized_or_reference_parts.csv'}")
        blocked = [r for r in excluded if r.get("is_manifest_print_target") == "1"]
        if blocked and not allow_excluded_print_targets:
            ids = ", ".join(r["part_id"] for r in blocked[:12])
            more = "" if len(blocked) <= 12 else f" ... +{len(blocked)-12} more"
            raise SystemExit(
                "Print-target parts were excluded from dense output. "
                "Fix CAD split/classification before printing, or pass "
                "--allow-excluded-print-targets only for deliberate debugging. "
                f"Excluded print targets: {ids}{more}"
            )
    return kept

def rect_contains(a: FreeRect, b: FreeRect) -> bool:
    return a.x <= b.x + 1e-6 and a.y <= b.y + 1e-6 and a.x + a.w >= b.x + b.w - 1e-6 and a.y + a.h >= b.y + b.h - 1e-6


def prune_free_rects(free: List[FreeRect]) -> List[FreeRect]:
    out = []
    for i, r in enumerate(free):
        if r.w <= 1e-6 or r.h <= 1e-6:
            continue
        contained = False
        for j, other in enumerate(free):
            if i != j and rect_contains(other, r):
                contained = True
                break
        if not contained:
            out.append(r)
    return out


def split_free_rect(free: FreeRect, used: FreeRect) -> List[FreeRect]:
    if used.x >= free.x + free.w or used.x + used.w <= free.x or used.y >= free.y + free.h or used.y + used.h <= free.y:
        return [free]

    new_rects = []

    if used.x > free.x:
        new_rects.append(FreeRect(free.x, free.y, used.x - free.x, free.h))
    if used.x + used.w < free.x + free.w:
        new_rects.append(FreeRect(used.x + used.w, free.y, free.x + free.w - (used.x + used.w), free.h))
    if used.y > free.y:
        new_rects.append(FreeRect(free.x, free.y, free.w, used.y - free.y))
    if used.y + used.h < free.y + free.h:
        new_rects.append(FreeRect(free.x, used.y + used.h, free.w, free.y + free.h - (used.y + used.h)))

    return [r for r in new_rects if r.w > 1e-6 and r.h > 1e-6]


def best_fit(free_rects: List[FreeRect], item: Item, gap: float, allow_rotate: bool) -> Optional[Tuple[FreeRect, bool, float, float, float, float]]:
    candidates = []
    dims = [(item.w, item.h, False)]
    if allow_rotate and abs(item.w - item.h) > 1e-6:
        dims.append((item.h, item.w, True))

    for fr in free_rects:
        for w, h, rot in dims:
            pw = w + gap
            ph = h + gap
            if pw <= fr.w + 1e-6 and ph <= fr.h + 1e-6:
                leftover_short = min(fr.w - pw, fr.h - ph)
                leftover_long = max(fr.w - pw, fr.h - ph)
                area_waste = fr.w * fr.h - pw * ph
                score = (leftover_short, area_waste, leftover_long, fr.y, fr.x)
                candidates.append((score, fr, rot, pw, ph, w, h))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    _, fr, rot, pw, ph, w, h = candidates[0]
    return fr, rot, pw, ph, w, h


def sort_items(items: List[Item]) -> List[Item]:
    def key(it: Item):
        area = it.w * it.h
        long_side = max(it.w, it.h)
        short_side = min(it.w, it.h)
        is_long = long_side > 115 and short_side < 35
        is_large = area > 12000 or long_side > 150
        # TPU tires can be tall; keep biggest first.
        return (is_large, is_long, area, long_side)
    return sorted(items, key=key, reverse=True)


def pack_items(items: List[Item], safe: float, gap: float, allow_rotate: bool, group_name: str, plate_start: int) -> Tuple[List[Placement], int]:
    remaining = sort_items(items[:])
    placements: List[Placement] = []
    plate_no = plate_start

    while remaining:
        free_rects = [FreeRect(0.0, 0.0, safe, safe)]
        page_placements = []

        while True:
            best = None
            best_idx = None

            for idx, item in enumerate(remaining):
                bf = best_fit(free_rects, item, gap, allow_rotate)
                if bf is None:
                    continue
                fr, rot, pw, ph, w, h = bf
                candidate_score = (item.w * item.h, max(item.w, item.h), -fr.y, -fr.x)
                if best is None or candidate_score > best[0]:
                    best = (candidate_score, fr, rot, pw, ph, w, h, item)
                    best_idx = idx

            if best is None:
                break

            _, fr, rot, pw, ph, w, h, item = best
            used = FreeRect(fr.x, fr.y, pw, ph)

            x = fr.x + gap / 2.0
            y = fr.y + gap / 2.0

            page_name = f"{plate_no:02d}_{group_name}"
            page_placements.append(Placement(
                item=item,
                plate_no=plate_no,
                plate_name=page_name,
                x=x,
                y=y,
                rotated=rot,
                w=w,
                h=h,
                pack_w=pw,
                pack_h=ph,
            ))

            new_free = []
            for r in free_rects:
                new_free.extend(split_free_rect(r, used))
            free_rects = prune_free_rects(new_free)
            remaining.pop(best_idx)

        if not page_placements:
            item = remaining.pop(0)
            rot = False
            w, h = item.w, item.h
            if allow_rotate and item.h <= safe and item.w <= safe and (item.w > safe or item.h > safe):
                rot = True
                w, h = item.h, item.w

            page_name = f"{plate_no:02d}_{group_name}_forced"
            page_placements.append(Placement(
                item=item,
                plate_no=plate_no,
                plate_name=page_name,
                x=max(0, (safe - w) / 2),
                y=max(0, (safe - h) / 2),
                rotated=rot,
                w=w,
                h=h,
                pack_w=w,
                pack_h=h,
            ))

        placements.extend(page_placements)
        plate_no += 1

    return placements, plate_no


def _is_meaningful_manifest_plate_group(value: str) -> bool:
    v = (value or "").strip().lower()
    if not v:
        return False
    generic = {"generic", "unknown", "plate_group_unknown", "rigid", "hard", "tpu", "petg", "pla", "abs"}
    return v not in generic


def group_items(
    items: List[Item],
    mode: str,
    split_tpu: bool,
    respect_manifest_plates: bool = True,
) -> Dict[str, List[Item]]:
    """Group items before packing.

    v4.6 policy:
      - For large Paddy Swarm assemblies, the manifest's plate_id/plate_group is
        a design contract, not just a comment.
      - Therefore, even when the user passes --group-mode all, the default is to
        keep meaningful manifest plate groups separate.
      - Use --ignore-manifest-plates to restore the old v4.6 behaviour that merges
        all rigid parts into one dense plate when they fit.
    """
    groups: Dict[str, List[Item]] = {}

    def add(key: str, item: Item):
        groups.setdefault(key, []).append(item)

    has_manifest_plates = respect_manifest_plates and any(_is_meaningful_manifest_plate_group(it.plate_group) for it in items)

    for it in items:
        mat_prefix = f"{it.material.lower()}_" if split_tpu else ""

        if has_manifest_plates and mode == "all":
            # Keep A1-HARD-01 / A1-HARD-02 / A1-TPU-01 style groups separate.
            add(f"{mat_prefix}{safe_name(it.plate_group or 'plate_group_unknown')}", it)
        elif mode == "all":
            add(f"{mat_prefix}all_dense", it)
        elif mode == "module":
            add(f"{mat_prefix}{safe_name(it.module or 'module_unknown')}", it)
        elif mode == "plate_group":
            add(f"{mat_prefix}{safe_name(it.plate_group or 'plate_group_unknown')}", it)
        else:
            raise ValueError(f"Unknown group mode: {mode}")

    # Print RIGID first, TPU last to make workflow natural.
    ordered = {}
    for k in sorted(groups.keys(), key=lambda x: (0 if x.startswith("rigid_") else 1 if x.startswith("tpu_") else 0, x)):
        ordered[k] = groups[k]
    return ordered


def load_mesh(path: Path):
    import trimesh
    mesh = trimesh.load_mesh(str(path))
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    return mesh


def material_dir_name(material: str) -> str:
    return "3mf_dense_pack_tpu" if material.upper() == "TPU" else "3mf_dense_pack_rigid"


def export_plates(placements: List[Placement], out_dir: Path, safe: float, make_all_in_one: bool = False):
    import trimesh

    by_plate: Dict[int, List[Placement]] = {}
    for p in placements:
        by_plate.setdefault(p.plate_no, []).append(p)

    placement_rows = []
    plate_files = []

    for plate_no in sorted(by_plate):
        ps = by_plate[plate_no]
        plate_name = ps[0].plate_name

        # A plate should be single material because grouping includes material prefix.
        material = ps[0].item.material
        out_3mf_dir = out_dir / material_dir_name(material)
        out_3mf_dir.mkdir(parents=True, exist_ok=True)

        scene = trimesh.Scene()

        for p in ps:
            mesh = _oriented_mesh_copy(p.item)
            if p.rotated:
                mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [0, 0, 1]))
                mesh.apply_translation(-mesh.bounds[0])
            mesh.apply_translation([p.x - safe/2.0, p.y - safe/2.0, 0])

            node = f"{p.item.part_id}_{p.item.instance}"
            scene.add_geometry(mesh, geom_name=node, node_name=node)

            placement_rows.append({
                "plate_no": plate_no,
                "plate_name": plate_name,
                "material": p.item.material,
                "part_id": p.item.part_id,
                "filename": p.item.filename,
                "instance": p.item.instance,
                "plate_group": p.item.plate_group,
                "module": p.item.module,
                "rotated_90": p.rotated,
                "x_min": round(p.x - safe/2.0, 3),
                "y_min": round(p.y - safe/2.0, 3),
                "x_max": round(p.x - safe/2.0 + p.w, 3),
                "y_max": round(p.y - safe/2.0 + p.h, 3),
                "bbox_x": round(p.w, 3),
                "bbox_y": round(p.h, 3),
                "bbox_z": round(p.item.z, 3),
                "support_orientation": p.item.original_row.get("_support_orient_name", "IDENTITY"),
                "support_orient_mode": p.item.original_row.get("_support_orient_mode", ""),
                "printed_status": "not_printed",
                "slice_status": "not_sliced",
                "assembly_status": "not_assembled",
                "notes": p.item.original_row.get("notes", ""),
            })

        out_3mf = out_3mf_dir / f"{plate_no:02d}_{safe_name(plate_name)}_{material.lower()}.3mf"
        scene.export(str(out_3mf))
        plate_files.append(out_3mf)
        print(f"[3MF] {out_3mf} material={material} objects={len(ps)}")

    write_csv(placement_rows, out_dir / "plate_placement_dense_material.csv")

    if make_all_in_one:
        scene = trimesh.Scene()
        offset_step = safe + 35.0
        material_gap = 80.0

        for plate_no in sorted(by_plate):
            ps = by_plate[plate_no]
            material = ps[0].item.material
            offset_x = (plate_no - 1) * offset_step
            offset_y = material_gap if material.upper() == "TPU" else 0.0

            for p in ps:
                mesh = _oriented_mesh_copy(p.item)
                if p.rotated:
                    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [0, 0, 1]))
                    mesh.apply_translation(-mesh.bounds[0])
                mesh.apply_translation([p.x - safe/2.0 + offset_x, p.y - safe/2.0 + offset_y, 0])
                node = f"plate{plate_no}_{material}_{p.item.part_id}_{p.item.instance}"
                scene.add_geometry(mesh, geom_name=node, node_name=node)

        all_path = out_dir / "all_plates_single_scene_reference_material_split.3mf"
        scene.export(str(all_path))
        print(f"[REF] {all_path}  # not real Bambu multi-plate tabs")

    return plate_files


def write_csv(rows: List[dict], path: Path):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)



def _fmt_float(v: float) -> str:
    if abs(v) < 1e-9:
        v = 0.0
    return (f"{v:.6f}".rstrip("0").rstrip(".")) or "0"


def compute_plate_workspace_offsets(placements: List[Placement], safe: float, plate_gap: float = 67.0, columns: int = 3, plate_step: float = 303.0, row_direction: str = "down") -> Dict[int, Tuple[float, float]]:
    """Return absolute XY offsets for each plate in the Bambu Studio workspace.

    Bambu/Orca project 3MF files contain plate assignments in
    Metadata/model_settings.config, but some generated files are displayed with all
    object geometry piled on the first visible plate unless the geometry is also
    placed in the same workspace grid used by the plates.

    v4.2 therefore writes two layers of information:
      1. model_settings.config plate/model_instance mapping
      2. physical workspace XY offsets for every plate in 3D/3dmodel.model

    This keeps the per-plate fallback 3MF files unchanged while making the single
    project 3MF open in Bambu Studio with parts visually separated by plate.
    """
    plate_ids = sorted({p.plate_no for p in placements})
    if not plate_ids:
        return {}
    # Bambu Studio A1 projects saved from Studio have been observed as a
    # 3-column grid, increasing by rows in the vertical/Y direction.
    # Use 3 columns by default rather than 2; otherwise objects land on the
    # wrong visible plate even when model_settings.config has plate metadata.
    if columns <= 0:
        columns = 3
    step = plate_step if plate_step > 0 else safe + plate_gap
    offsets: Dict[int, Tuple[float, float]] = {}
    for plate_no in plate_ids:
        idx = plate_no - 1
        col = idx % columns
        row = idx // columns
        y_sign = -1.0 if str(row_direction).lower() in {"down", "negative", "-", "neg"} else 1.0
        offsets[plate_no] = (col * step, y_sign * row * step)
    return offsets




def infer_bambu_template_plate_count(template_3mf: Path) -> int:
    """Infer how many build plates exist in a Bambu Studio template 3MF.

    Bambu Studio stores plate thumbnails such as Metadata/plate_1.png and
    may also store <plate> records in Metadata/model_settings.config or
    Metadata/slice_info.config. The template is treated as the source of truth
    because Studio reflows plates into square-like grids as plate count grows:
    9=3x3, 16=4x4, 25=5x5, 36=6x6.
    """
    import re
    max_plate = 0
    if not template_3mf.exists():
        return 0
    try:
        with zipfile.ZipFile(template_3mf, 'r') as z:
            names = z.namelist()
            for name in names:
                m = re.fullmatch(r'Metadata/plate_(\d+)\.png', name)
                if m:
                    max_plate = max(max_plate, int(m.group(1)))
            for cfg_name in ('Metadata/model_settings.config', 'Metadata/slice_info.config'):
                if cfg_name in names:
                    txt = z.read(cfg_name).decode('utf-8', 'ignore')
                    max_plate = max(max_plate, txt.count('<plate'))
                    for m in re.finditer(r'plater_id"\s+value="(\d+)"', txt):
                        max_plate = max(max_plate, int(m.group(1)))
                    for m in re.finditer(r'key="index"\s+value="(\d+)"', txt):
                        max_plate = max(max_plate, int(m.group(1)))
    except Exception:
        return max_plate
    return max_plate


def auto_square_columns_for_plate_count(plate_count: int, max_columns: int = 6) -> int:
    """Return Bambu Studio square-like template columns for N plates."""
    if plate_count <= 0:
        return 4
    return max(1, min(int(max_columns), int(math.ceil(math.sqrt(plate_count)))))


def resolve_template_columns(template_3mf: Path, requested_columns: int, grid_mode: str = 'auto-square', required_plate_count: int = 0) -> Tuple[int, int, int]:
    """Resolve Bambu template columns.

    v5.5 policy:
      - Bambu Studio reflows plates as a square-like grid based on the TOTAL
        plates in the project: 5->3 columns, 10->4, 17->5, 26->6.
      - The generated template project rewrites model_settings to the required
        print plates, so the relevant count is the print plate count, not the
        number of blank plates in the source template.
      - If fixed mode is requested, the user supplied column count wins.
    """
    detected = infer_bambu_template_plate_count(template_3mf)
    required = max(0, int(required_plate_count or 0))
    if str(grid_mode).lower() in {'auto', 'auto-square', 'square', 'auto-print'}:
        count_for_grid = required or detected
        return auto_square_columns_for_plate_count(count_for_grid), detected, count_for_grid
    return max(1, int(requested_columns or 4)), detected, (required or detected)

def _mesh_for_placement(p: Placement, safe: float, plate_offsets: Optional[Dict[int, Tuple[float, float]]] = None, project_coordinate_mode: str = "centered", plate_inner_margin: float = 0.0):
    import trimesh
    mesh = _oriented_mesh_copy(p.item)
    if p.rotated:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [0, 0, 1]))
        mesh.apply_translation(-mesh.bounds[0])
    ox, oy = (0.0, 0.0)
    if plate_offsets is not None:
        ox, oy = plate_offsets.get(p.plate_no, (0.0, 0.0))

    if project_coordinate_mode == "bambu-absolute":
        # For Bambu/Orca multi-plate projects, coordinates are absolute across
        # the plate grid. Keep plate-local packing coordinates positive
        # (0..safe), then add the 303 mm plate origin offset.
        # Keep objects away from the physical build-plate outline.
        # Bambu Studio template plates are absolute workspaces; p.x/p.y are
        # local dense-pack coordinates from 0..safe. A positive margin shifts
        # the entire packed group inward so skirts/brims and UI plate bounds do
        # not flag borderline objects.
        tx = p.x + ox + plate_inner_margin
        ty = p.y + oy + plate_inner_margin
    else:
        # Standard standalone 3MF fallback keeps each single plate centered.
        tx = p.x - safe / 2.0 + ox
        ty = p.y - safe / 2.0 + oy
    mesh.apply_translation([tx, ty, 0])
    return mesh


def _build_3dmodel_xml(placements: List[Placement], safe: float, plate_offsets: Optional[Dict[int, Tuple[float, float]]] = None, project_coordinate_mode: str = "centered", plate_inner_margin: float = 0.0) -> bytes:
    ET.register_namespace('', 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02')
    ET.register_namespace('p', 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06')
    ET.register_namespace('m', 'http://schemas.microsoft.com/3dmanufacturing/material/2015/02')
    ET.register_namespace('s', 'http://schemas.microsoft.com/3dmanufacturing/slice/2015/07')
    ET.register_namespace('b', 'http://schemas.bambulab.com/package/2021')

    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    root = ET.Element(f'{{{ns}}}model', {'unit': 'millimeter', '{http://www.w3.org/XML/1998/namespace}lang': 'en-US'})
    ET.SubElement(root, f'{{{ns}}}metadata', {'name': 'Application'}).text = 'BambuStudio-01.10.02.76'
    ET.SubElement(root, f'{{{ns}}}metadata', {'name': 'BambuStudio:3mfVersion'}).text = '1'
    ET.SubElement(root, f'{{{ns}}}metadata', {'name': 'Title'}).text = 'Paddy Swarm A1 multi-plate project v5.7'
    resources = ET.SubElement(root, f'{{{ns}}}resources')
    build = ET.SubElement(root, f'{{{ns}}}build')

    for object_id, p in enumerate(placements, start=1):
        mesh_obj = _mesh_for_placement(p, safe, plate_offsets=plate_offsets, project_coordinate_mode=project_coordinate_mode, plate_inner_margin=plate_inner_margin)
        obj = ET.SubElement(resources, f'{{{ns}}}object', {'id': str(object_id), 'type': 'model'})
        ET.SubElement(obj, f'{{{ns}}}metadata', {'name': 'name'}).text = f'{p.item.part_id}_{p.item.instance}'
        mesh_el = ET.SubElement(obj, f'{{{ns}}}mesh')
        verts_el = ET.SubElement(mesh_el, f'{{{ns}}}vertices')
        for v in mesh_obj.vertices:
            ET.SubElement(verts_el, f'{{{ns}}}vertex', {
                'x': _fmt_float(float(v[0])),
                'y': _fmt_float(float(v[1])),
                'z': _fmt_float(float(v[2])),
            })
        tris_el = ET.SubElement(mesh_el, f'{{{ns}}}triangles')
        for f in mesh_obj.faces:
            ET.SubElement(tris_el, f'{{{ns}}}triangle', {
                'v1': str(int(f[0])),
                'v2': str(int(f[1])),
                'v3': str(int(f[2])),
            })
        ET.SubElement(build, f'{{{ns}}}item', {'objectid': str(object_id), 'transform': '1 0 0 0 0 1 0 0 0 0 1 0'})

    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def _build_model_settings_xml(placements: List[Placement]) -> bytes:
    config = ET.Element('config')
    by_plate: Dict[int, List[Tuple[int, Placement]]] = {}

    for object_id, p in enumerate(placements, start=1):
        extruder = '2' if p.item.material.upper() == 'TPU' else '1'
        name = f'{p.item.part_id}_{p.item.instance}'
        obj = ET.SubElement(config, 'object', {'id': str(object_id)})
        ET.SubElement(obj, 'metadata', {'key': 'name', 'value': name})
        ET.SubElement(obj, 'metadata', {'key': 'extruder', 'value': extruder})
        ET.SubElement(obj, 'metadata', {'face_count': '0'})
        part = ET.SubElement(obj, 'part', {'id': str(object_id), 'subtype': 'normal_part'})
        ET.SubElement(part, 'metadata', {'key': 'name', 'value': name})
        ET.SubElement(part, 'metadata', {'key': 'extruder', 'value': extruder})
        ET.SubElement(part, 'metadata', {'key': 'matrix', 'value': '1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'})
        ET.SubElement(part, 'metadata', {'key': 'source_file', 'value': Path(p.item.filename).name})
        ET.SubElement(part, 'metadata', {'key': 'source_object_id', 'value': str(object_id)})
        ET.SubElement(part, 'metadata', {'key': 'source_volume_id', 'value': '0'})
        ET.SubElement(part, 'mesh_stat', {'face_count': '0'})
        by_plate.setdefault(p.plate_no, []).append((object_id, p))

    for plate_no in sorted(by_plate):
        ps = by_plate[plate_no]
        plate = ET.SubElement(config, 'plate')
        plate_name = ps[0][1].plate_name
        material = ps[0][1].item.material.upper() if ps else 'RIGID'
        ET.SubElement(plate, 'metadata', {'key': 'plater_id', 'value': str(plate_no)})
        ET.SubElement(plate, 'metadata', {'key': 'plater_name', 'value': plate_name})
        ET.SubElement(plate, 'metadata', {'key': 'locked', 'value': 'false'})
        ET.SubElement(plate, 'metadata', {'key': 'filament_map_mode', 'value': 'Auto For Flush'})
        ET.SubElement(plate, 'metadata', {'key': 'filament_maps', 'value': '2' if material == 'TPU' else '1'})
        ET.SubElement(plate, 'metadata', {'key': 'filament_volume_maps', 'value': '0'})
        ET.SubElement(plate, 'metadata', {'key': 'gcode_file', 'value': ''})
        ET.SubElement(plate, 'metadata', {'key': 'thumbnail_file', 'value': ''})
        ET.SubElement(plate, 'metadata', {'key': 'thumbnail_no_light_file', 'value': ''})
        ET.SubElement(plate, 'metadata', {'key': 'top_file', 'value': ''})
        ET.SubElement(plate, 'metadata', {'key': 'pick_file', 'value': ''})
        for object_id, p in ps:
            mi = ET.SubElement(plate, 'model_instance')
            ET.SubElement(mi, 'metadata', {'key': 'object_id', 'value': str(object_id)})
            ET.SubElement(mi, 'metadata', {'key': 'instance_id', 'value': '0'})
            ET.SubElement(mi, 'metadata', {'key': 'identify_id', 'value': str(100000 + object_id)})

    return ET.tostring(config, encoding='utf-8', xml_declaration=True)


def _build_project_settings_json(printer_model: str, nozzle: str, preset_mode: str = 'studio-default') -> bytes:
    """Build Bambu project settings.

    preset_mode='studio-default' intentionally writes no printer/filament preset
    definitions. Bambu Studio should then open the project using the user's
    currently selected printer/process/filament presets instead of warning about
    imported custom presets.

    preset_mode='embedded' preserves the earlier v4 behavior and writes simple
    A1/PETG/TPU hints into project_settings.config.
    """
    if preset_mode == 'studio-default':
        return json.dumps({}, ensure_ascii=False, indent=2).encode('utf-8')

    data = {
        'printer_model': printer_model,
        'printer_variant': nozzle,
        'nozzle_diameter': [nozzle],
        'filament_type': ['PETG', 'TPU'],
        'filament_colour': ['#2F2F2F', '#111111'],
        'filament_diameter': ['1.75', '1.75'],
        'filament_density': ['1.27', '1.20'],
        'print_compatible_printers': [f'{printer_model} {nozzle} nozzle'],
        'upward_compatible_machine': [],
        'enable_support': '0',
    }
    return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')


def _content_types_xml() -> bytes:
    return b'''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
  <Default Extension="config" ContentType="application/octet-stream"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
</Types>
'''


def _rels_xml() -> bytes:
    return b'''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model" Id="rel0"/>
</Relationships>
'''


def _custom_gcode_xml() -> bytes:
    return b'''<?xml version="1.0" encoding="UTF-8"?>
<custom_gcodes_per_layer/>
'''


def export_bambu_project_3mf(placements: List[Placement], out_dir: Path, safe: float, project_name: str, printer_model: str, nozzle: str, max_plates: int = 36, preset_mode: str = 'studio-default', plate_gap: float = 67.0, plate_columns: int = 4, plate_step: float = 303.0, geometry_mode: str = 'bambu-absolute-grid', plate_inner_margin: float = 18.0) -> Path:
    # Create a single Bambu/Orca-style unsliced project 3MF with multiple plate tabs.
    if not placements:
        raise ValueError('No placements to export')
    plate_count = len({p.plate_no for p in placements})
    if plate_count > max_plates:
        raise ValueError(f'Plate count {plate_count} exceeds requested Bambu max plates {max_plates}')

    out_dir.mkdir(parents=True, exist_ok=True)
    project_path = out_dir / f'{safe_name(project_name)}_bambu_multiplate_project.3mf'
    if project_path.exists():
        project_path.unlink()

    project_coordinate_mode = "centered"
    if geometry_mode == 'bambu-absolute-grid':
        plate_offsets = compute_plate_workspace_offsets(placements, safe=safe, plate_gap=plate_gap, columns=plate_columns, plate_step=plate_step, row_direction="down")
        project_coordinate_mode = "bambu-absolute"
    elif geometry_mode == 'workspace-grid':
        plate_offsets = compute_plate_workspace_offsets(placements, safe=safe, plate_gap=plate_gap, columns=plate_columns, plate_step=(safe + plate_gap), row_direction="down")
        project_coordinate_mode = "centered"
    elif geometry_mode == 'metadata-only':
        plate_offsets = None
        project_coordinate_mode = "centered"
    else:
        raise ValueError(f'Unknown Bambu project geometry mode: {geometry_mode}')

    with zipfile.ZipFile(project_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', _content_types_xml())
        z.writestr('_rels/.rels', _rels_xml())
        z.writestr('3D/3dmodel.model', _build_3dmodel_xml(placements, safe, plate_offsets=plate_offsets, project_coordinate_mode=project_coordinate_mode, plate_inner_margin=plate_inner_margin if project_coordinate_mode == 'bambu-absolute' else 0.0))
        z.writestr('Metadata/model_settings.config', _build_model_settings_xml(placements))
        # In studio-default mode, keep project settings empty so Bambu Studio uses
        # the user's currently selected printer/filament/process presets and does
        # not import custom presets from the 3MF.
        z.writestr('Metadata/project_settings.config', _build_project_settings_json(printer_model, nozzle, preset_mode=preset_mode))
        z.writestr('Metadata/custom_gcode_per_layer.xml', _custom_gcode_xml())

    print(f'[BAMBU_PROJECT_3MF] {project_path} plates={plate_count} objects={len(placements)} geometry_mode={geometry_mode}')
    return project_path


def _tag_local(tag: str) -> str:
    return tag.split('}', 1)[-1] if '}' in tag else tag


def _set_metadata(el: ET.Element, key: str, value: str):
    for ch in list(el):
        if _tag_local(ch.tag) == 'metadata' and ch.attrib.get('key') == key:
            ch.set('value', value)
            return ch
    return ET.SubElement(el, 'metadata', {'key': key, 'value': value})


def _remove_children_by_local_name(el: ET.Element, names: set):
    for ch in list(el):
        if _tag_local(ch.tag) in names:
            el.remove(ch)


def _clear_template_model_settings(root: ET.Element) -> List[ET.Element]:
    """Remove old objects/instances while preserving native Bambu plate metadata."""
    for ch in list(root):
        if _tag_local(ch.tag) == 'object':
            root.remove(ch)
    plates: List[ET.Element] = []
    for ch in list(root):
        if _tag_local(ch.tag) == 'plate':
            _remove_children_by_local_name(ch, {'model_instance'})
            plates.append(ch)
    return plates


def _clone_or_create_template_plate(root: ET.Element, plates: List[ET.Element], plate_no: int, plate_name: str) -> ET.Element:
    if plate_no <= len(plates):
        plate = plates[plate_no - 1]
    elif plates:
        plate = copy.deepcopy(plates[-1])
        _remove_children_by_local_name(plate, {'model_instance'})
        root.append(plate)
        plates.append(plate)
    else:
        plate = ET.SubElement(root, 'plate')
        plates.append(plate)
    _set_metadata(plate, 'plater_id', str(plate_no))
    _set_metadata(plate, 'plater_name', plate_name)
    _set_metadata(plate, 'locked', 'false')
    _remove_children_by_local_name(plate, {'model_instance'})
    return plate


def _append_template_object(root: ET.Element, object_id: int, p: Placement, source_file: str):
    extruder = '2' if p.item.material.upper() == 'TPU' else '1'
    name = f'{p.item.part_id}_{p.item.instance}'
    obj = ET.Element('object', {'id': str(object_id)})
    ET.SubElement(obj, 'metadata', {'key': 'name', 'value': name})
    ET.SubElement(obj, 'metadata', {'key': 'extruder', 'value': extruder})
    ET.SubElement(obj, 'metadata', {'face_count': '0'})
    part = ET.SubElement(obj, 'part', {'id': str(object_id), 'subtype': 'normal_part'})
    ET.SubElement(part, 'metadata', {'key': 'name', 'value': name})
    ET.SubElement(part, 'metadata', {'key': 'extruder', 'value': extruder})
    ET.SubElement(part, 'metadata', {'key': 'matrix', 'value': '1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'})
    ET.SubElement(part, 'metadata', {'key': 'source_file', 'value': source_file})
    ET.SubElement(part, 'metadata', {'key': 'source_object_id', 'value': str(object_id)})
    ET.SubElement(part, 'metadata', {'key': 'source_volume_id', 'value': '0'})
    ET.SubElement(part, 'mesh_stat', {'face_count': '0'})
    insert_index = len(list(root))
    for idx, ch in enumerate(list(root)):
        if _tag_local(ch.tag) == 'plate':
            insert_index = idx
            break
    root.insert(insert_index, obj)


def _build_model_settings_from_template(template_bytes: bytes, placements: List[Placement]) -> bytes:
    try:
        root = ET.fromstring(template_bytes)
    except Exception:
        root = ET.Element('config')
    plates = _clear_template_model_settings(root)
    by_plate: Dict[int, List[Tuple[int, Placement]]] = {}
    for object_id, p in enumerate(placements, start=1):
        _append_template_object(root, object_id, p, Path(p.item.filename or p.item.stl.name).name)
        by_plate.setdefault(p.plate_no, []).append((object_id, p))
    for plate_no in sorted(by_plate):
        ps = by_plate[plate_no]
        plate_name = ps[0][1].plate_name if ps else f'plate_{plate_no:02d}'
        plate = _clone_or_create_template_plate(root, plates, plate_no, plate_name)
        material = ps[0][1].item.material.upper() if ps else 'RIGID'
        _set_metadata(plate, 'filament_maps', '2' if material == 'TPU' else '1')
        _set_metadata(plate, 'gcode_file', '')
        _set_metadata(plate, 'thumbnail_file', '')
        _set_metadata(plate, 'thumbnail_no_light_file', '')
        _set_metadata(plate, 'top_file', '')
        _set_metadata(plate, 'pick_file', '')
        for object_id, p in ps:
            mi = ET.SubElement(plate, 'model_instance')
            ET.SubElement(mi, 'metadata', {'key': 'object_id', 'value': str(object_id)})
            ET.SubElement(mi, 'metadata', {'key': 'instance_id', 'value': '0'})
            ET.SubElement(mi, 'metadata', {'key': 'identify_id', 'value': str(100000 + object_id)})
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def export_bambu_template_project_3mf(placements: List[Placement], out_dir: Path, safe: float, template_3mf: Path, project_name: str, template_geometry_mode: str = 'absolute-grid', template_plate_step: float = 303.0, template_plate_columns: int = 0, template_row_direction: str = 'down', template_plate_inner_margin: float = 18.0, template_grid_mode: str = 'auto-square') -> Path:
    """Inject dense-packed objects into a blank Bambu Studio multi-plate template.

    This is the recommended v4.6 method. Scratch-generated project 3MF files can
    open as one plate because Bambu Studio relies on additional native metadata.
    A template saved by Bambu Studio already has that metadata, so this function
    preserves the template package and replaces only the model and model_settings.
    """
    if not placements:
        raise ValueError('No placements to export')
    if not template_3mf.exists():
        raise FileNotFoundError(f'Template 3MF not found: {template_3mf}')
    out_dir.mkdir(parents=True, exist_ok=True)
    project_path = out_dir / f'{safe_name(project_name)}_bambu_template_multiplate_project.3mf'
    if project_path.exists():
        project_path.unlink()
    if template_geometry_mode == 'centered':
        plate_offsets = None
        project_coordinate_mode = 'centered'
    elif template_geometry_mode == 'positive':
        plate_offsets = None
        project_coordinate_mode = 'bambu-absolute'
    elif template_geometry_mode == 'absolute-grid':
        max_needed_plate = max((p.plate_no for p in placements), default=0)
        resolved_columns, detected_plate_count, count_for_grid = resolve_template_columns(
            template_3mf,
            template_plate_columns,
            template_grid_mode,
            required_plate_count=max_needed_plate,
        )
        if detected_plate_count and max_needed_plate > detected_plate_count:
            print(f'[WARN] template has {detected_plate_count} plates but placements require {max_needed_plate}; add more plates in Bambu Studio template')
        print(f'[BAMBU_TEMPLATE_GRID] mode={template_grid_mode} detected_plates={detected_plate_count} required_plates={max_needed_plate} grid_count={count_for_grid} columns={resolved_columns} step={template_plate_step} row_direction={template_row_direction}')
        plate_offsets = compute_plate_workspace_offsets(placements, safe=safe, plate_gap=67.0, columns=resolved_columns, plate_step=template_plate_step, row_direction=template_row_direction)
        project_coordinate_mode = 'bambu-absolute'
    else:
        raise ValueError(f'Unknown template geometry mode: {template_geometry_mode}')
    with zipfile.ZipFile(template_3mf, 'r') as zin:
        names = set(zin.namelist())
        template_model_settings = zin.read('Metadata/model_settings.config') if 'Metadata/model_settings.config' in names else b'<config/>'
        with zipfile.ZipFile(project_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for name in zin.namelist():
                if name in {'3D/3dmodel.model', 'Metadata/model_settings.config'}:
                    continue
                zout.writestr(name, zin.read(name))
            if '[Content_Types].xml' not in names:
                zout.writestr('[Content_Types].xml', _content_types_xml())
            if '_rels/.rels' not in names:
                zout.writestr('_rels/.rels', _rels_xml())
            zout.writestr('3D/3dmodel.model', _build_3dmodel_xml(placements, safe, plate_offsets=plate_offsets, project_coordinate_mode=project_coordinate_mode, plate_inner_margin=template_plate_inner_margin if project_coordinate_mode == 'bambu-absolute' else 0.0))
            zout.writestr('Metadata/model_settings.config', _build_model_settings_from_template(template_model_settings, placements))
    print(f'[BAMBU_TEMPLATE_PROJECT_3MF] {project_path} plates={len({p.plate_no for p in placements})} objects={len(placements)} template={template_3mf} geometry_mode={template_geometry_mode}')
    return project_path

def write_project_manifest(placements: List[Placement], out_dir: Path):
    rows = []
    for p in placements:
        rows.append({
            "print_order": p.plate_no,
            "plate_name": p.plate_name,
            "material": p.item.material,
            "part_id": p.item.part_id,
            "filename": p.item.filename,
            "instance": p.item.instance,
            "qty_total": p.item.qty,
            "source_stl": str(p.item.stl),
            "plate_group": p.item.plate_group,
            "module": p.item.module,
            "title": p.item.title,
            "rotated_90": p.rotated,
            "support_orientation": p.item.original_row.get("_support_orient_name", "IDENTITY"),
            "support_orient_mode": p.item.original_row.get("_support_orient_mode", ""),
            "printed_status": "not_printed",
            "slice_status": "not_sliced",
            "assembly_status": "not_assembled",
            "notes": p.item.original_row.get("notes", ""),
        })
    write_csv(rows, out_dir / "print_project_manifest_dense_material.csv")



def write_boundary_safety_report(placements: List[Placement], out_dir: Path, safe: float, gap: float, plate_inner_margin: float, nominal_plate_size: float = 256.0):
    """Write a conservative per-object local plate-boundary report.

    This is a geometry-independent check based on packed bbox dimensions. It is
    intended for GitHub/CI review before opening in Bambu Studio. PASS here does
    not guarantee slicing success, but FAIL indicates the dense parameters are
    too aggressive or the CAD part needs splitting.
    """
    rows = []
    usable_max = nominal_plate_size - plate_inner_margin
    for p in placements:
        local_x_min = p.x + plate_inner_margin
        local_y_min = p.y + plate_inner_margin
        local_x_max = p.x + p.w + plate_inner_margin
        local_y_max = p.y + p.h + plate_inner_margin
        ok = (
            local_x_min >= plate_inner_margin - 1e-6 and
            local_y_min >= plate_inner_margin - 1e-6 and
            local_x_max <= usable_max + 1e-6 and
            local_y_max <= usable_max + 1e-6
        )
        rows.append({
            "plate_no": p.plate_no,
            "plate_name": p.plate_name,
            "material": p.item.material,
            "part_id": p.item.part_id,
            "rotated_90": p.rotated,
            "bbox_x": round(p.w, 3),
            "bbox_y": round(p.h, 3),
            "safe": safe,
            "gap": gap,
            "plate_inner_margin": plate_inner_margin,
            "nominal_plate_size": nominal_plate_size,
            "local_x_min": round(local_x_min, 3),
            "local_y_min": round(local_y_min, 3),
            "local_x_max": round(local_x_max, 3),
            "local_y_max": round(local_y_max, 3),
            "status": "PASS" if ok else "CHECK_OR_SPLIT",
        })
    write_csv(rows, out_dir / "plate_boundary_safety_report.csv")

def make_zip(out_dir: Path) -> Path:
    zip_path = out_dir.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in out_dir.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(out_dir.parent))

    print(f"[ZIP] {zip_path}")
    return zip_path


def write_readme(out_dir: Path, mode: str, split_tpu: bool, make_all_in_one: bool, tpu_patterns: List[str]):
    text = f"""# Paddy Swarm A1 Dense Pack v5.7 Output

Group mode: `{mode}`
TPU split: `{split_tpu}`
TPU patterns: `{", ".join(tpu_patterns)}`

## Files

- `3mf_dense_pack_rigid/*.3mf`
  - PLA / PETG / ABSなど硬質部品用
- `3mf_dense_pack_tpu/*.3mf`
  - TPUタイヤ/ゴム系部品用
- `plate_placement_dense_material.csv`
  - 各部品の配置座標
- `print_project_manifest_dense_material.csv`
  - 印刷/スライス/組み立て進捗管理用
- `support_orientation_report.csv`
  - サポート発生を抑えるために自動選択した向き、元寸法、新寸法、ベッド接触面積の記録


## v5.4 plate grid note

Bambu Studio A1 template projects were observed to arrange plates in a 4-column grid.
Therefore v5.4 defaults `--bambu-template-plate-columns` and `--bambu-plate-columns` to 4.
If your local template uses a different grid, override these options explicitly.

## Recommended workflow

1. Print rigid plates first.
2. Change filament/profile to TPU.
3. Print TPU tire plates separately.
4. Use STL files for repair/replacement parts.

## Important

`all_plates_single_scene_reference_material_split.3mf` がある場合、それはBambu Studioの本物の複数プレートタブではありません。  
全プレートを1つの3Dシーンに横並びで入れた参照用です。

`*_bambu_multiplate_project.3mf` がある場合、それはv4.3のBambu Studio複数プレートproject 3MFです。v4.3標準では `bambu-absolute-grid` 方式で、Bambu/Orca系で観測される約303mm間隔・2列のplateグリッド座標に各plateの部品を配置します。A1に入らない大型部品や市販品参照ダミーは標準でprojectから除外され、`oversized_or_reference_parts.csv` に出力されます。標準では printer/filament preset を埋め込まず、Bambu Studio側の現在設定を使用します。開けない場合は、同時出力される個別3MFをフォールバックとして使用してください。
"""
    (out_dir / "README_dense_pack_v3_material_split.md").write_text(text, encoding="utf-8")



def reindex_placements_by_material(placements: List[Placement], material: str) -> List[Placement]:
    """Return placements for one material, renumbered from plate 1.

    Bambu Studio template projects behave more predictably when each material file
    starts at plate 1.  This is also the intended shop workflow: open/print the
    RIGID project first, then open/print the TPU project with TPU filament/profile.
    """
    selected = [p for p in placements if p.item.material.upper() == material.upper()]
    old_to_new: Dict[int, int] = {}
    out: List[Placement] = []
    for p in sorted(selected, key=lambda q: (q.plate_no, q.plate_name, q.item.part_id, q.item.instance)):
        if p.plate_no not in old_to_new:
            old_to_new[p.plate_no] = len(old_to_new) + 1
        new_no = old_to_new[p.plate_no]
        # Keep the useful original plate/group name, but make the leading number match the new file.
        old_name = p.plate_name or f"plate_{p.plate_no:02d}_{material.lower()}"
        suffix = old_name
        if len(old_name) >= 3 and old_name[:2].isdigit() and old_name[2] == "_":
            suffix = old_name[3:]
        new_name = f"{new_no:02d}_{suffix}"
        out.append(replace(p, plate_no=new_no, plate_name=new_name))
    return out


def split_placements_by_material(placements: List[Placement]) -> Dict[str, List[Placement]]:
    mats: Dict[str, List[Placement]] = {}
    for p in placements:
        mats.setdefault(p.item.material.upper(), []).append(p)
    return {k: mats[k] for k in sorted(mats.keys(), key=lambda m: (0 if m == "RIGID" else 1 if m == "TPU" else 2, m))}



# -----------------------------------------------------------------------------
# v5.7 model-dense-set workflow
# -----------------------------------------------------------------------------

def discover_reference_metal_items(
    manifest: Path,
    metal_reference_dir: Optional[Path] = None,
) -> List[Item]:
    """Create RIGID printable-model Items from reference_metal_stl/*.stl.

    These are NOT real metal.  They are deliberately treated as PETG/PLA rigid
    surrogate parts so a moving/fit-check model can be printed without buying
    rods yet.  For real field testing, replace them with the metal BOM.
    """
    base_dir = manifest.parent
    candidates: List[Path] = []
    if metal_reference_dir:
        candidates.append(Path(metal_reference_dir))
    candidates.extend([
        base_dir / "reference_metal_stl",
        base_dir.parent / "reference_metal_stl",
        base_dir / "reference_stl" / "reference_metal_stl",
    ])

    metal_dir = None
    for d in candidates:
        if d and d.exists() and d.is_dir():
            metal_dir = d
            break

    if metal_dir is None:
        return []

    out: List[Item] = []
    for stl in sorted(metal_dir.glob("*.stl")):
        try:
            w, h, z = compute_mesh_bbox_mm(stl)
        except Exception:
            # Conservative fallback for rods.
            w, h, z = (180.0, 8.0, 8.0)
        part_id = stl.stem
        row = {
            "part_id": part_id,
            "part_no": part_id,
            "filename": stl.name,
            "stl": str(stl),
            "material": "RIGID",
            "material_group": "RIGID",
            "plate_group": "A1-HARD-METAL-PRINT",
            "module": "printed_metal_replacement_model",
            "title": f"3D printed replacement model for {part_id}",
            "notes": "MODEL ONLY: reference metal rod printed as rigid plastic surrogate; replace with real metal for load/field tests",
            "_dense_set_kind": "printed_metal_replacement",
            "_source_kind": "reference_metal_stl",
        }
        out.append(Item(
            part_id=part_id,
            filename=stl.name,
            stl=stl,
            plate_group="A1-HARD-METAL-PRINT",
            module="printed_metal_replacement_model",
            title=f"3D printed replacement model for {part_id}",
            instance=1,
            qty=1,
            w=w,
            h=h,
            z=z,
            material="RIGID",
            original_row=row,
        ))
    return out


def is_printed_metal_replacement_item(item: Item) -> bool:
    text = " ".join([
        item.part_id,
        item.filename,
        item.plate_group,
        item.module,
        item.original_row.get("_dense_set_kind", ""),
        item.original_row.get("_source_kind", ""),
        item.original_row.get("notes", ""),
    ]).upper()
    return (
        "PRINTED_METAL_REPLACEMENT" in text
        or "REFERENCE_METAL_STL" in text
        or "A1-HARD-METAL-PRINT" in text
        or item.part_id.upper().startswith("REF-METAL-")
    )


def clone_items(items: List[Item]) -> List[Item]:
    # Use copy.deepcopy so support-orientation transforms for one dense set do not
    # leak into the other dense sets.
    return copy.deepcopy(items)


def _dense_subset_counts(items: List[Item]) -> Dict[str, int]:
    return {
        "total": len(items),
        "rigid": sum(1 for x in items if x.material.upper() != "TPU"),
        "tpu": sum(1 for x in items if x.material.upper() == "TPU"),
        "printed_metal_replacement": sum(1 for x in items if is_printed_metal_replacement_item(x)),
    }


def run_dense_subset_pipeline(
    subset_items: List[Item],
    subset_out_dir: Path,
    args,
    subset_name: str,
    split_tpu: bool = True,
) -> List[Placement]:
    """Run the normal dense pipeline for one v5.7 output subset."""
    subset_out_dir.mkdir(parents=True, exist_ok=True)
    items = clone_items(subset_items)

    if not items:
        (subset_out_dir / "EMPTY_DENSE_SET.txt").write_text(
            f"No printable items in dense set: {subset_name}\n",
            encoding="utf-8",
        )
        print(f"[DENSE_SET] {subset_name}: empty")
        return []

    items = apply_support_aware_orientation(
        items,
        safe=args.safe,
        gap=args.gap,
        allow_rotate=not args.no_rotate,
        out_dir=subset_out_dir,
        mode=args.support_orient,
        support_orient_fit_safe=args.support_orient_fit_safe,
    )

    print(f"[DENSE_SET] {subset_name}: items expanded before filter: {len(items)}")
    items = classify_and_filter_items(
        items,
        safe=args.safe,
        gap=args.gap,
        allow_rotate=not args.no_rotate,
        out_dir=subset_out_dir,
        oversize_policy=args.oversize_policy,
        include_reference_parts=args.include_reference_parts,
        allow_excluded_print_targets=args.allow_excluded_print_targets,
    )
    if not items:
        (subset_out_dir / "EMPTY_AFTER_FILTER.txt").write_text(
            f"No printable items remain after filtering in dense set: {subset_name}\n",
            encoding="utf-8",
        )
        print(f"[DENSE_SET] {subset_name}: empty after filter")
        return []

    print(f"[DENSE_SET] {subset_name}: items after filter: {len(items)} counts={_dense_subset_counts(items)}")

    groups = group_items(
        items,
        args.group_mode,
        split_tpu=split_tpu,
        respect_manifest_plates=not args.ignore_manifest_plates,
    )

    all_placements: List[Placement] = []
    plate_no = 1
    for group_name, group_items_list in groups.items():
        print(f"[PACK:{subset_name}] group={group_name} items={len(group_items_list)} material={group_items_list[0].material if group_items_list else '?'}")
        placements, plate_no = pack_items(
            group_items_list,
            safe=args.safe,
            gap=args.gap,
            allow_rotate=not args.no_rotate,
            group_name=safe_name(group_name),
            plate_start=plate_no,
        )
        all_placements.extend(placements)

    write_project_manifest(all_placements, subset_out_dir)
    write_boundary_safety_report(
        all_placements,
        out_dir=subset_out_dir,
        safe=args.safe,
        gap=args.gap,
        plate_inner_margin=args.bambu_template_plate_inner_margin,
    )

    if args.make_3mf:
        export_plates(all_placements, subset_out_dir, safe=args.safe, make_all_in_one=args.make_all_in_one_reference)
    else:
        rows = []
        for p in all_placements:
            rows.append({
                "plate_no": p.plate_no,
                "plate_name": p.plate_name,
                "material": p.item.material,
                "part_id": p.item.part_id,
                "instance": p.item.instance,
                "rotated_90": p.rotated,
                "x_min": round(p.x - args.safe/2.0, 3),
                "y_min": round(p.y - args.safe/2.0, 3),
                "x_max": round(p.x - args.safe/2.0 + p.w, 3),
                "y_max": round(p.y - args.safe/2.0 + p.h, 3),
            })
        write_csv(rows, subset_out_dir / "plate_placement_dense_material.csv")

    if args.make_bambu_project_3mf:
        export_bambu_project_3mf(
            all_placements,
            out_dir=subset_out_dir,
            safe=args.safe,
            project_name=f"{args.bambu_project_name}_{subset_name}",
            printer_model=args.bambu_printer_model,
            nozzle=args.bambu_nozzle,
            max_plates=args.bambu_max_plates,
            preset_mode=args.bambu_preset_mode,
            plate_gap=args.bambu_plate_gap,
            plate_columns=args.bambu_plate_columns,
            plate_step=args.bambu_plate_step,
            geometry_mode=args.bambu_project_geometry_mode,
            plate_inner_margin=args.bambu_plate_inner_margin,
        )

    if args.make_bambu_template_project_3mf:
        if not args.bambu_template_3mf:
            raise SystemExit("--make-bambu-template-project-3mf requires --bambu-template-3mf <blank_bambu_project.3mf>")
        export_bambu_template_project_3mf(
            all_placements,
            out_dir=subset_out_dir,
            safe=args.safe,
            template_3mf=Path(args.bambu_template_3mf),
            project_name=f"{args.bambu_template_project_name}_{subset_name}",
            template_geometry_mode=args.bambu_template_geometry_mode,
            template_plate_step=args.bambu_template_plate_step,
            template_plate_columns=args.bambu_template_plate_columns,
            template_row_direction=args.bambu_template_row_direction,
            template_plate_inner_margin=args.bambu_template_plate_inner_margin,
            template_grid_mode=args.bambu_template_grid_mode,
        )

    write_readme(subset_out_dir, args.group_mode, split_tpu, args.make_all_in_one_reference, args.tpu_pattern or ["TIR", "TIRE", "TYRE", "TPU", "RUBBER"])
    return all_placements


def write_model_dense_sets_summary(out_dir: Path, summary_rows: List[dict]):
    write_csv(summary_rows, out_dir / "model_dense_sets_summary.csv")
    lines = [
        "# Paddy Swarm v5.7.3 model dense sets",
        "",
        "This output is intended for a complete working/fit-check printed model. Paddy Swarm's current fabrication goal is a complete model including printable metal-surrogate parts when reference_metal_stl is available.",
        "",
        "Dense sets:",
        "",
        "- `dense_rigid_plus_metal/`: PETG/PLA rigid parts + `reference_metal_stl/*.stl` as printable rigid surrogate rods. This is the primary complete-model set.",
        "- `dense_rigid_only/`: PETG/PLA rigid parts only, no printed metal surrogate rods.",
        "- `dense_tpu_only/`: TPU wheels, gaskets, plugs, and other flexible parts only.",
        "",
        "Important:",
        "",
        "- Printed metal replacements are **not** a substitute for real metal in load/field testing.",
        "- Use printed replacements for assembly sequence, spacing, fit, and low-load moving model checks. This is the default target for complete model fabrication.",
        "- Replace rods with the metal BOM before real mud/water/field load tests.",
        "",
    ]
    if summary_rows:
        lines.append("## Counts")
        lines.append("")
        for r in summary_rows:
            lines.append(f"- {r['dense_set']}: total={r['total_items']} rigid={r['rigid_items']} tpu={r['tpu_items']} printed_metal_replacement={r['printed_metal_replacement_items']} plates={r['plates']}")
    (out_dir / "README_model_dense_sets_v5_7.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_model_dense_sets_workflow(args):
    """v5.7: write rigid+metal, rigid-only, and TPU-only dense outputs."""
    manifest = Path(args.manifest)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    tpu_patterns = args.tpu_pattern or ["TIR", "TIRE", "TYRE", "TPU", "RUBBER"]
    base_items = read_manifest(manifest, tpu_patterns=tpu_patterns)

    # In this workflow TPU split is forced because the output contract is three
    # material/use-case-specific dense sets.
    rigid_items = [it for it in base_items if it.material.upper() != "TPU" and not is_printed_metal_replacement_item(it)]
    tpu_items = [it for it in base_items if it.material.upper() == "TPU"]
    metal_items = discover_reference_metal_items(manifest, Path(args.metal_reference_dir) if args.metal_reference_dir else None)

    if args.no_metal_replacement_dense:
        metal_items = []

    if not metal_items and not args.no_metal_replacement_dense:
        print("[WARN] no reference_metal_stl parts found; dense_rigid_plus_metal will match dense_rigid_only unless the CAD output includes reference_metal_stl/*.stl or --metal-reference-dir is supplied")

    rigid_plus_metal_items = rigid_items + metal_items

    dense_sets = [
        ("rigid_plus_metal", rigid_plus_metal_items, "RIGID + printed metal surrogate rods"),
        ("rigid_only", rigid_items, "RIGID only, no printed metal surrogate rods"),
        ("tpu_only", tpu_items, "TPU only"),
    ]

    summary_rows = []
    for set_name, subset, description in dense_sets:
        subdir = out_dir / f"dense_{set_name}"
        placements = run_dense_subset_pipeline(
            subset,
            subset_out_dir=subdir,
            args=args,
            subset_name=set_name,
            split_tpu=True,
        )
        counts = _dense_subset_counts(subset)
        summary_rows.append({
            "dense_set": set_name,
            "description": description,
            "total_items": counts["total"],
            "rigid_items": counts["rigid"],
            "tpu_items": counts["tpu"],
            "printed_metal_replacement_items": counts["printed_metal_replacement"],
            "plates": len({p.plate_no for p in placements}),
            "output_dir": str(subdir),
        })

    write_model_dense_sets_summary(out_dir, summary_rows)

    if args.make_zip:
        make_zip(out_dir)

    print("")
    print(f"Done model dense sets: {out_dir.resolve()}")



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="print_manifest*.csv from common tools output")
    ap.add_argument("--out", default="paddy_swarm_dense_pack_v2_out")
    ap.add_argument("--group-mode", choices=["all", "plate_group", "module"], default="all")
    ap.add_argument("--ignore-manifest-plates", action="store_true", help="old behaviour: with --group-mode all, merge all printable rigid parts if they fit; default v4.6 respects manifest plate_id/plate_group")
    ap.add_argument("--safe", type=float, default=232.0, help="usable square area per A1 plate in mm; v5.4 default 232 to allow 220mm-class flat parts while retaining A1 margin")
    ap.add_argument("--gap", type=float, default=8.0, help="gap between packed parts in mm; v5.4 default 8 with material/project split")
    ap.add_argument("--no-rotate", action="store_true")
    ap.add_argument("--support-orient", choices=["auto-flat", "off"], default="auto-flat", help="auto-flat uses v5.4 wider-fit low-Z-first support-aware orientation; off preserves CAD STL orientation")
    ap.add_argument("--support-orient-fit-safe", type=float, default=232.0, help="orientation-only fit square in mm; prevents flat 220mm-class parts from being stood upright by too-small packing safe")
    ap.add_argument("--split-tpu", action="store_true", help="separate TPU-like parts into TPU plates")
    ap.add_argument("--tpu-pattern", action="append", default=None, help="substring pattern for TPU parts; can be repeated")
    ap.add_argument("--make-3mf", action="store_true")
    ap.add_argument("--make-all-in-one-reference", action="store_true")
    ap.add_argument("--make-bambu-project-3mf", action="store_true", help="write one Bambu Studio compatible multi-plate project .3mf")
    ap.add_argument("--bambu-project-name", default="paddy_swarm_a1_dense", help="base name for the multi-plate project 3MF")
    ap.add_argument("--bambu-printer-model", default="Bambu Lab A1")
    ap.add_argument("--bambu-nozzle", default="0.4")
    ap.add_argument("--bambu-max-plates", type=int, default=36)
    ap.add_argument("--bambu-preset-mode", choices=["studio-default", "embedded"], default="studio-default", help="studio-default keeps printer/filament presets unspecified so Bambu Studio uses current settings; embedded writes simple preset hints and may show a custom preset warning")
    ap.add_argument("--bambu-project-geometry-mode", choices=["bambu-absolute-grid", "workspace-grid", "metadata-only"], default="bambu-absolute-grid", help="bambu-absolute-grid uses Bambu/Orca-like 303 mm absolute plate coordinates; workspace-grid keeps v4.2 centered-offset behavior; metadata-only keeps v4.1 behavior")
    ap.add_argument("--bambu-plate-gap", type=float, default=67.0, help="fallback XY gap between project plates; ignored when --bambu-plate-step is positive")
    ap.add_argument("--bambu-plate-step", type=float, default=303.0, help="absolute spacing between Bambu/Orca plate origins; default 303 mm")
    ap.add_argument("--bambu-plate-columns", type=int, default=0, help="number of plate columns in bambu-absolute-grid mode; 0 = auto-square from required plate count")
    ap.add_argument("--oversize-policy", choices=["exclude", "force"], default="exclude", help="exclude oversized/reference parts from dense packing by default; force keeps old behavior and may trigger Bambu boundary errors")
    ap.add_argument("--include-reference-parts", action="store_true", help="include reference/dummy/purchased-envelope parts in dense packing; not recommended for common rover")
    ap.add_argument("--make-bambu-template-project-3mf", action="store_true", help="write a template-based Bambu Studio multi-plate project .3mf; requires --bambu-template-3mf")
    ap.add_argument("--bambu-template-3mf", default=None, help="blank Bambu Studio .3mf project with enough plates; recommended for reliable multi-plate tabs")
    ap.add_argument("--bambu-template-project-name", default="paddy_swarm_a1_dense", help="base name for the template-based multi-plate project 3MF")
    ap.add_argument("--bambu-template-geometry-mode", choices=["centered", "positive", "absolute-grid"], default="absolute-grid", help="geometry coordinate mode used inside the Bambu template project; absolute-grid is the v4.6 default for Bambu Studio template plates")
    ap.add_argument("--bambu-template-plate-step", type=float, default=303.0, help="XY interval between Bambu Studio template plates; default 303mm")
    ap.add_argument("--bambu-template-plate-columns", type=int, default=0, help="template plate grid columns; 0 = auto-square from generated print plate count, e.g. 5->3, 10->4, 17->5, 26->6")
    ap.add_argument("--bambu-template-grid-mode", choices=["auto-square", "fixed"], default="auto-square", help="auto-square infers columns from generated print plate count using ceil(sqrt(N)); fixed uses --bambu-template-plate-columns")
    ap.add_argument("--bambu-template-row-direction", choices=["down", "up"], default="down", help="template plate row direction on Y axis; Bambu Studio A1 observed default is down/negative Y")
    ap.add_argument("--bambu-template-plate-inner-margin", type=float, default=12.0, help="extra inward XY shift inside each Bambu template plate; v5.4 default 12mm with safe=232")
    ap.add_argument("--bambu-plate-inner-margin", type=float, default=12.0, help="extra inward XY shift for scratch Bambu project 3MF; v5.4 default 12mm with safe=232")
    ap.add_argument("--bambu-template-split-by-material", action=argparse.BooleanOptionalAction, default=True, help="write separate template project 3MF files per material; default true so TPU and rigid parts are not mixed in one Bambu project")
    ap.add_argument("--make-model-dense-sets", action="store_true", help="v5.7.3 standard: write three dense sets: rigid_plus_metal, rigid_only, and tpu_only for complete model fabrication")
    ap.add_argument("--metal-reference-dir", default=None, help="directory containing reference metal STL files to print as rigid surrogate rods; default auto-detects reference_metal_stl beside manifest")
    ap.add_argument("--no-metal-replacement-dense", action="store_true", help="with --make-model-dense-sets, do not add reference_metal_stl parts to rigid_plus_metal")
    ap.add_argument("--allow-excluded-print-targets", action="store_true", help="debug only: allow manifest print-target rows to be excluded from dense output")
    ap.add_argument("--make-zip", action="store_true")
    args = ap.parse_args()

    if args.make_model_dense_sets:
        run_model_dense_sets_workflow(args)
        return

    manifest = Path(args.manifest)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    tpu_patterns = args.tpu_pattern or ["TIR", "TIRE", "TYRE", "TPU", "RUBBER"]
    items = read_manifest(manifest, tpu_patterns=tpu_patterns)

    if not args.split_tpu:
        # force all material RIGID unless explicitly splitting
        items = [Item(**{**it.__dict__, "material": "RIGID"}) for it in items]

    items = apply_support_aware_orientation(
        items,
        safe=args.safe,
        gap=args.gap,
        allow_rotate=not args.no_rotate,
        out_dir=out_dir,
        mode=args.support_orient,
        support_orient_fit_safe=args.support_orient_fit_safe,
    )

    print(f"[INFO] items expanded before filter: {len(items)}")
    items = classify_and_filter_items(
        items,
        safe=args.safe,
        gap=args.gap,
        allow_rotate=not args.no_rotate,
        out_dir=out_dir,
        oversize_policy=args.oversize_policy,
        include_reference_parts=args.include_reference_parts,
        allow_excluded_print_targets=args.allow_excluded_print_targets,
    )
    if not items:
        raise SystemExit("No printable items remain after oversize/reference filtering. Check oversized_or_reference_parts.csv or use --oversize-policy force for debugging only.")
    print(f"[INFO] items after filter: {len(items)}")
    print(f"[INFO] material counts: RIGID={sum(1 for x in items if x.material=='RIGID')} TPU={sum(1 for x in items if x.material=='TPU')}")

    groups = group_items(
        items,
        args.group_mode,
        split_tpu=args.split_tpu,
        respect_manifest_plates=not args.ignore_manifest_plates,
    )

    all_placements: List[Placement] = []
    plate_no = 1

    for group_name, group_items_list in groups.items():
        print(f"[PACK] group={group_name} items={len(group_items_list)} material={group_items_list[0].material if group_items_list else '?'}")
        placements, plate_no = pack_items(
            group_items_list,
            safe=args.safe,
            gap=args.gap,
            allow_rotate=not args.no_rotate,
            group_name=safe_name(group_name),
            plate_start=plate_no,
        )
        all_placements.extend(placements)

    write_project_manifest(all_placements, out_dir)
    write_boundary_safety_report(
        all_placements,
        out_dir=out_dir,
        safe=args.safe,
        gap=args.gap,
        plate_inner_margin=args.bambu_template_plate_inner_margin,
    )

    if args.make_3mf:
        export_plates(all_placements, out_dir, safe=args.safe, make_all_in_one=args.make_all_in_one_reference)
    else:
        rows = []
        for p in all_placements:
            rows.append({
                "plate_no": p.plate_no,
                "plate_name": p.plate_name,
                "material": p.item.material,
                "part_id": p.item.part_id,
                "instance": p.item.instance,
                "rotated_90": p.rotated,
                "x_min": round(p.x - args.safe/2.0, 3),
                "y_min": round(p.y - args.safe/2.0, 3),
                "x_max": round(p.x - args.safe/2.0 + p.w, 3),
                "y_max": round(p.y - args.safe/2.0 + p.h, 3),
            })
        write_csv(rows, out_dir / "plate_placement_dense_material.csv")

    if args.make_bambu_project_3mf:
        export_bambu_project_3mf(
            all_placements,
            out_dir=out_dir,
            safe=args.safe,
            project_name=args.bambu_project_name,
            printer_model=args.bambu_printer_model,
            nozzle=args.bambu_nozzle,
            max_plates=args.bambu_max_plates,
            preset_mode=args.bambu_preset_mode,
            plate_gap=args.bambu_plate_gap,
            plate_columns=args.bambu_plate_columns,
            plate_step=args.bambu_plate_step,
            geometry_mode=args.bambu_project_geometry_mode,
            plate_inner_margin=args.bambu_plate_inner_margin,
        )

    if args.make_bambu_template_project_3mf:
        if not args.bambu_template_3mf:
            raise SystemExit("--make-bambu-template-project-3mf requires --bambu-template-3mf <blank_bambu_project.3mf>")
        if args.bambu_template_split_by_material and len(split_placements_by_material(all_placements)) > 1:
            print("[BAMBU_TEMPLATE_PROJECT_3MF] split-by-material enabled: writing separate RIGID/TPU project files")
            for material, material_ps_original in split_placements_by_material(all_placements).items():
                material_ps = reindex_placements_by_material(all_placements, material)
                export_bambu_template_project_3mf(
                    material_ps,
                    out_dir=out_dir,
                    safe=args.safe,
                    template_3mf=Path(args.bambu_template_3mf),
                    project_name=f"{args.bambu_template_project_name}_{material.lower()}",
                    template_geometry_mode=args.bambu_template_geometry_mode,
                    template_plate_step=args.bambu_template_plate_step,
                    template_plate_columns=args.bambu_template_plate_columns,
                    template_row_direction=args.bambu_template_row_direction,
                    template_plate_inner_margin=args.bambu_template_plate_inner_margin,
                    template_grid_mode=args.bambu_template_grid_mode,
                )
        else:
            export_bambu_template_project_3mf(
                all_placements,
                out_dir=out_dir,
                safe=args.safe,
                template_3mf=Path(args.bambu_template_3mf),
                project_name=args.bambu_template_project_name,
                template_geometry_mode=args.bambu_template_geometry_mode,
                template_plate_step=args.bambu_template_plate_step,
                template_plate_columns=args.bambu_template_plate_columns,
                template_row_direction=args.bambu_template_row_direction,
                template_plate_inner_margin=args.bambu_template_plate_inner_margin,
                template_grid_mode=args.bambu_template_grid_mode,
            )

    write_readme(out_dir, args.group_mode, args.split_tpu, args.make_all_in_one_reference, tpu_patterns)

    if args.make_zip:
        make_zip(out_dir)

    print("")
    print(f"Done: {out_dir.resolve()}")


if __name__ == "__main__":
    main()

