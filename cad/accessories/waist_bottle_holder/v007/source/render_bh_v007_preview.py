"""Render BH_V007 engineering review views from generated STL and CAD envelope."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
STL = ROOT / "stl"
DOCS = ROOT / "docs"
BUILD_SOURCE = ROOT / "source" / "build_bh_v007.py"


def load_stl(name: str) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(STL / name, process=True)
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    return mesh


def load_build_module():
    spec = importlib.util.spec_from_file_location("bh_v007_preview_build", BUILD_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load V007 build source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cq_to_mesh(workplane) -> trimesh.Trimesh:
    vertices, triangles = workplane.val().tessellate(0.35, 0.15)
    return trimesh.Trimesh(
        vertices=np.array([[v.x, v.y, v.z] for v in vertices]),
        faces=np.array(triangles),
        process=True,
    )


def draw(ax, mesh: trimesh.Trimesh, color: str, alpha: float = 1.0, edges: bool = True) -> None:
    triangles = mesh.vertices[mesh.faces]
    collection = Poly3DCollection(
        triangles,
        facecolor=color,
        edgecolor="#263238" if edges else "none",
        linewidth=0.025 if edges else 0.0,
        alpha=alpha,
        rasterized=True,
    )
    ax.add_collection3d(collection)


def fit(ax, meshes: list[trimesh.Trimesh], scale: float = 1.08) -> None:
    mins = np.min(np.vstack([mesh.bounds[0] for mesh in meshes]), axis=0)
    maxs = np.max(np.vstack([mesh.bounds[1] for mesh in meshes]), axis=0)
    center = (mins + maxs) / 2.0
    span = np.max(maxs - mins) * scale
    ax.set_xlim(center[0] - span / 2.0, center[0] + span / 2.0)
    ax.set_ylim(center[1] - span / 2.0, center[1] + span / 2.0)
    ax.set_zlim(center[2] - span / 2.0, center[2] + span / 2.0)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    body = load_stl("BH_V007_main_body_reinforced_integrated_slide_PETG.stl")
    collar = load_stl("BH_V007_neck_collar_ID26p2_long_tab_PETG.stl")
    coupon = load_stl("BH_V007_upper_structure_coupon_PETG.stl")
    placed = collar.copy()
    placed.apply_translation([0.0, 0.0, 187.1])

    build = load_build_module()
    bottle_cq, _ = build.make_bottle_clearance_envelope()
    bottle = cq_to_mesh(bottle_cq)

    fig = plt.figure(figsize=(16, 15), facecolor="#f2efe6")
    panels = [
        ("Front / bottle side", [body], ["#d9a441"], [1.0], 17, -58, None),
        ("Rear / body side", [body], ["#d9a441"], [1.0], 17, 122, None),
        (
            "Nominal bottle envelope + ID26.2 collar",
            [body, bottle, placed],
            ["#d9a441", "#6ab7b0", "#256b9e"],
            [1.0, 0.22, 1.0],
            12,
            -86,
            None,
        ),
        (
            "Integrated receiver side detail",
            [body, bottle, placed],
            ["#d9a441", "#6ab7b0", "#256b9e"],
            [1.0, 0.18, 1.0],
            8,
            2,
            ((-36, 36), (-58, 12), (118, 221)),
        ),
        ("ID26.2 collar + 30 mm ruled-tip tab", [collar], ["#256b9e"], [1.0], 24, -55, None),
        ("Upper structure coupon print layout", [coupon], ["#b97834"], [1.0], 19, -55, None),
    ]

    for index, (title, meshes, colors, alphas, elev, azim, limits) in enumerate(panels, start=1):
        ax = fig.add_subplot(3, 2, index, projection="3d")
        for mesh, color, alpha in zip(meshes, colors, alphas):
            draw(ax, mesh, color, alpha, edges=alpha > 0.5)
        if limits is None:
            fit(ax, meshes)
        else:
            ax.set_xlim(*limits[0])
            ax.set_ylim(*limits[1])
            ax.set_zlim(*limits[2])
            ax.set_box_aspect(
                (
                    limits[0][1] - limits[0][0],
                    limits[1][1] - limits[1][0],
                    limits[2][1] - limits[2][0],
                )
            )
            ax.set_axis_off()
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=13, color="#263238", pad=2)

    fig.suptitle("BH_V007 CAD VISUAL REVIEW", fontsize=20, color="#263238", y=0.985)
    fig.text(
        0.5,
        0.023,
        "38 x 8.5 upper spine | R10 root | integrated 34 mm receiver | 6 mm lead-in | 30 mm tab | 0.5 mm float",
        ha="center",
        fontsize=11,
        color="#455a64",
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.955, bottom=0.05, wspace=0.02, hspace=0.08)
    fig.savefig(DOCS / "BH_V007_visual_review.png", dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
