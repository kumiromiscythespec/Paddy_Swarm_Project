"""Render reproducible engineering preview PNGs from generated BH_V006 STLs."""

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


def load(name: str) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(STL / name, process=True)
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    return mesh


def draw_mesh(ax, mesh: trimesh.Trimesh, color: str, alpha: float = 1.0) -> None:
    triangles = mesh.vertices[mesh.faces]
    poly = Poly3DCollection(
        triangles,
        facecolor=color,
        edgecolor="#253238",
        linewidth=0.035,
        alpha=alpha,
        rasterized=True,
    )
    ax.add_collection3d(poly)


def fit_axes(ax, meshes: list[trimesh.Trimesh], pad: float = 0.06) -> None:
    mins = np.min(np.vstack([m.bounds[0] for m in meshes]), axis=0)
    maxs = np.max(np.vstack([m.bounds[1] for m in meshes]), axis=0)
    center = (mins + maxs) / 2.0
    span = np.max(maxs - mins) * (1.0 + pad)
    ax.set_xlim(center[0] - span / 2.0, center[0] + span / 2.0)
    ax.set_ylim(center[1] - span / 2.0, center[1] + span / 2.0)
    ax.set_zlim(center[2] - span / 2.0, center[2] + span / 2.0)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    body = load("BH_V006_main_body_94mm_squircle_rope4p8_PETG.stl")
    collar = load("BH_V006_neck_collar_slide_tab_ID26p0_PETG.stl")
    collar_placed = collar.copy()
    collar_placed.apply_translation([0.0, 0.0, 187.1])

    fig = plt.figure(figsize=(14, 11), facecolor="#f4f1e8")
    panels = [
        ("Front / bottle side", 18, -58, [body], ["#d9a441"]),
        ("Rear / body side", 18, 122, [body], ["#d9a441"]),
        ("Nominal assembly", 12, -86, [body, collar_placed], ["#d9a441", "#2f6f9f"]),
        ("Bottle-side neck collar + key", 24, -55, [collar], ["#2f6f9f"]),
    ]
    for index, (title, elev, azim, meshes, colors) in enumerate(panels, start=1):
        ax = fig.add_subplot(2, 2, index, projection="3d")
        for mesh, color in zip(meshes, colors):
            draw_mesh(ax, mesh, color)
        fit_axes(ax, meshes, pad=0.08)
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=13, color="#263238", pad=2)
    fig.suptitle("BH_V006 CAD visual review", fontsize=18, color="#263238", y=0.98)
    fig.text(
        0.5,
        0.025,
        "94 mm rounded-square cup | phi4.8 rope slots | bottle-side C collar | top slide-in captured key",
        ha="center",
        fontsize=11,
        color="#455a64",
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.06, wspace=0.02, hspace=0.06)
    fig.savefig(DOCS / "BH_V006_visual_review.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
