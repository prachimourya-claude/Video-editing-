#!/usr/bin/env python3
"""Lotus diya shell for a standard LED tealight, exported as STL.

Usage: python3 tools/diya_lotus.py [out.stl] [preview.png]
Needs: pip install manifold3d numpy (matplotlib for the preview)

Designed for FDM in PLA (Bambu A1): flat base, no supports needed,
petals lean out at <= 40 degrees from vertical.
"""
import math
import sys

import numpy as np
from manifold3d import Manifold, Mesh, set_circular_segments

set_circular_segments(96)

# --- Parameters (mm) ---------------------------------------------------------
TEALIGHT_D = 38.0      # standard LED tealight; measure yours
CLEARANCE = 1.2        # added to diameter so it drops in easily
POCKET_DEPTH = 16.0    # tealight body height; flame sticks out above
FLOOR = 2.4            # floor thickness under the tealight
PUSH_HOLE_D = 22.0     # hole in the floor: push the light out, reach its switch
BASE_R = 24.0          # footprint radius
BODY_TOP_R = 25.0      # radius of the cup rim
BODY_H = FLOOR + POCKET_DEPTH
OUTER_PETALS = 8
INNER_PETALS = 8
PETAL_T = 2.0          # petal thickness


def petal(length, width, tilt_deg, base_r, z0, angle_deg):
    """A pointed, slightly cupped petal: hull of spheres along a leaf outline."""
    pts = []
    n = 9
    for i in range(n + 1):
        t = i / n                       # 0 = root, 1 = tip
        w = width / 2 * math.sin(math.pi * t ** 0.75) ** 0.6   # broad, ovate
        y = t * length
        cup = 3.0 * (1 - (2 * t - 1) ** 2)  # bow the middle outwards a little
        for sx in (-1, 1):
            pts.append((sx * w, cup, y))
    pts.append((0, 1.0, length + 2.5))  # pointed tip
    blob = Manifold.sphere(PETAL_T / 2, 12)
    leaf = Manifold.batch_hull([blob.translate(p) for p in pts])
    return (leaf.rotate((-tilt_deg, 0, 0))   # lean outwards (+y)
                .translate((0, base_r, z0))
                .rotate((0, 0, angle_deg)))


def build():
    # Cup body: a cone frustum on a slightly flared foot.
    foot = Manifold.cylinder(2.0, BASE_R + 1.0, BASE_R + 1.0)
    body = Manifold.cylinder(BODY_H, BASE_R, BODY_TOP_R)
    solid = foot + body

    # Two rings of petals, offset so the inner ones show between the outer.
    for i in range(OUTER_PETALS):
        solid += petal(26, 30, 38, BASE_R - 2.5, 1.0, i * 360 / OUTER_PETALS)
    for i in range(INNER_PETALS):
        solid += petal(25, 25, 18, BODY_TOP_R - 3.0, 5.0,
                       (i + 0.5) * 360 / INNER_PETALS)

    pocket_r = (TEALIGHT_D + CLEARANCE) / 2
    pocket = Manifold.cylinder(100, pocket_r, pocket_r).translate((0, 0, FLOOR))
    push = Manifold.cylinder(10, PUSH_HOLE_D / 2, PUSH_HOLE_D / 2).translate((0, 0, -1))
    # Trim anything below the bed (petal roots) so the base is flat.
    below = Manifold.cube((200, 200, 50), True).translate((0, 0, -25))
    return solid - pocket - push - below


def write_stl(manifold, path):
    mesh = manifold.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    tri = v[f]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-12
    data = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    data["n"], data["v"] = normals, tri
    with open(path, "wb") as fh:
        fh.write(b"PSOne Labs lotus diya".ljust(80, b" "))
        fh.write(np.uint32(len(f)).tobytes())
        fh.write(data.tobytes())


def preview(manifold, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    mesh = manifold.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    tri = v[np.asarray(mesh.tri_verts)]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    light = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])
    shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
    gold = np.array([0.88, 0.65, 0.15])
    fig = plt.figure(figsize=(6, 6), dpi=150, facecolor="#FBF6EE")
    ax = fig.add_subplot(projection="3d", facecolor="#FBF6EE")
    ax.add_collection3d(Poly3DCollection(tri, facecolors=shade[:, None] * gold, linewidths=0))
    lim = 36
    ax.set(xlim=(-lim, lim), ylim=(-lim, lim), zlim=(-20, 52))
    ax.view_init(elev=28, azim=-60)
    ax.set_axis_off()
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "diya_lotus.stl"
    diya = build()
    write_stl(diya, out)
    bb = diya.bounding_box()
    print(f"{out}: {diya.num_tri()} triangles, "
          f"{bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm, "
          f"volume {diya.volume()/1000:.1f} cm^3 (~{diya.volume()/1000*1.24:.0f} g PLA solid)")
    if len(sys.argv) > 2:
        preview(diya, sys.argv[2])
