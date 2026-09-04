"""Render a visual review sheet for the BH_V006 physical authority artifacts."""

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


def draw(ax, mesh: trimesh.Trimesh, color: str) -> None:
    triangles = mesh.vertices[mesh.faces]
    collection = Poly3DCollection(
        triangles,
        facecolor=color,
        edgecolor="#263238",
        linewidth=0.03,
        rasterized=True,
    )
    ax.add_collection3d(collection)


def fit(ax, meshes: list[trimesh.Trimesh]) -> None:
    mins = np.min(np.vstack([mesh.bounds[0] for mesh in meshes]), axis=0)
    maxs = np.max(np.vstack([mesh.bounds[1] for mesh in meshes]), axis=0)
    center = (mins + maxs) / 2.0
    span = np.max(maxs - mins) * 1.08
    ax.set_xlim(center[0] - span / 2.0, center[0] + span / 2.0)
    ax.set_ylim(center[1] - span / 2.0, center[1] + span / 2.0)
    ax.set_zlim(center[2] - span / 2.0, center[2] + span / 2.0)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    body = load("BH_V006_main_body_PHYSICAL_AUTHORITY_PETG.stl")
    collar = load("BH_V006_neck_collar_slide_tab_ID26p2_AUTHORITY_PETG.stl")
    placed = collar.copy()
    placed.apply_translation([0.0, 0.0, 187.1])

    fig = plt.figure(figsize=(16, 7), facecolor="#f2efe6")
    views = [
        ("Production main body\nreceiver 17.1 x 4.8", [body], ["#d7a23e"], 17, -58),
        ("Physical authority assembly\nfloat 0.5 mm", [body, placed], ["#d7a23e", "#246b9e"], 12, -86),
        ("ID26.2 collar + transferred S3 tab\ntab 16.0 x 4.0", [collar], ["#246b9e"], 24, -55),
    ]
    for index, (title, meshes, colors, elev, azim) in enumerate(views, start=1):
        ax = fig.add_subplot(1, 3, index, projection="3d")
        for mesh, color in zip(meshes, colors):
            draw(ax, mesh, color)
        fit(ax, meshes)
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=13, color="#263238")
    fig.suptitle("BH_V006 PHYSICAL AUTHORITY", fontsize=19, color="#263238", y=0.97)
    fig.text(
        0.5,
        0.035,
        "Physical result overrides nominal labels | ID26.2 | S3 actual dimensions | cup-bottom load support",
        ha="center",
        color="#455a64",
        fontsize=11,
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.09, wspace=0.02)
    fig.savefig(DOCS / "BH_V006_PHYSICAL_AUTHORITY_visual_review.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
