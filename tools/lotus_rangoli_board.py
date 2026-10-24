#!/usr/bin/env python3
"""Solid lotus rangoli filling board, traced from a reference image.

The cream outlines in the reference become raised ridges; everything inside
the outer silhouette becomes a solid floor (no through-holes), so rangoli
powder sits on top.

Usage:
  python3 tools/lotus_rangoli_board.py REF.png OUT_DIR [--stl]
Without --stl it only writes preview images (approve those first).
Needs: pip install numpy pillow opencv-python-headless manifold3d matplotlib
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from manifold3d import CrossSection, FillRule, Manifold

# --- Parameters (mm) ---------------------------------------------------------
WIDTH = 150.0          # overall width
BASE_T = 2.2           # solid floor thickness
RIDGE_H = 1.8          # ridge height above the floor
RIDGE_GROW = 0.2       # mm added on each side of the traced outlines
OUTER_RIM = 2.6        # width of the outer wall
ROUND = 0.5            # top-edge rounding (stepped inset)


def masks(ref_path):
    im = np.asarray(Image.open(ref_path).convert("RGB")).astype(np.int16)
    v = im.mean(-1)
    sat = im[..., 0] - im[..., 2]
    cream = ((v > 198) & (sat < 70)).astype(np.uint8)
    obj = ((sat > 45) | (v > 200)).astype(np.uint8)

    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    # Object: largest blob, holes filled -> one solid silhouette.
    obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, k(4))
    obj = cv2.morphologyEx(obj, cv2.MORPH_OPEN, k(3))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(obj)
    obj = (lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    cnts, _ = cv2.findContours(obj, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    sil = np.zeros_like(obj)
    cv2.drawContours(sil, cnts, -1, 1, cv2.FILLED)

    cream &= sil
    cream = cv2.morphologyEx(cream, cv2.MORPH_OPEN, k(2))
    cream = cv2.morphologyEx(cream, cv2.MORPH_CLOSE, k(3))
    # Drop specks (highlights on the gold that aren't outlines).
    n, lab, stats, _ = cv2.connectedComponentsWithStats(cream)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] > 2000
    cream = keep[lab].astype(np.uint8)
    return sil, cream


def to_section(mask, mm_per_px, h):
    """Mask -> CrossSection in mm (y up), keeping holes (even-odd)."""
    cnts, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polys = []
    for c in cnts:
        if len(c) < 3:
            continue
        c = cv2.approxPolyDP(c, 1.0, True)[:, 0, :].astype(float)
        if len(c) < 3:
            continue
        polys.append([(x * mm_per_px, (h - y) * mm_per_px) for x, y in c])
    return CrossSection(polys, FillRule.EvenOdd)


def build(ref_path):
    sil, ridge = masks(ref_path)
    ys, xs = np.nonzero(sil)
    mm_per_px = WIDTH / (xs.max() - xs.min() + 1)
    h = sil.shape[0]

    base_cs = to_section(sil, mm_per_px, h)
    ridge_cs = to_section(ridge, mm_per_px, h)
    # Widen ridges slightly (traced lines are ~2.5 mm) and keep them inside the floor.
    ridge_cs = ridge_cs.offset(RIDGE_GROW, join_type=1) ^ base_cs
    # Outer wall: a ridge band right to the edge, so powder can't spill off.
    ridge_cs += base_cs - base_cs.offset(-OUTER_RIM, join_type=1)

    model = Manifold.extrude(base_cs, BASE_T)
    # Ridge: full-width body, then two inset steps for a softly rounded top.
    body_h = RIDGE_H - ROUND
    model += Manifold.extrude(ridge_cs, body_h + 0.3).translate((0, 0, BASE_T - 0.3))
    step = ROUND / 2
    for i, inset in enumerate((0.3, 0.7)):
        cs = ridge_cs.offset(-inset, join_type=1)
        z = BASE_T + body_h + i * step
        model += Manifold.extrude(cs, step + 0.1).translate((0, 0, z - 0.1))

    # Remove slivers so the float32 STL stays manifold.
    model = model.simplify(0.02)
    # Centre on the origin, flat on the bed.
    bb = model.bounding_box()
    model = model.translate((-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2]))
    return model, sil, ridge


def heightmap_preview(model, path, px=0.12):
    """Top-down shaded render of the actual geometry (raycast by slicing)."""
    bb = model.bounding_box()
    zs = [0.5, BASE_T + 0.3, BASE_T + RIDGE_H - 0.15]
    w = int((bb[3] - bb[0]) / px) + 40
    hgt = int((bb[4] - bb[1]) / px) + 40
    H = np.zeros((hgt, w), np.float32)
    for z in zs:
        cs = model.slice(z)
        # even-odd fill
        polys = [np.round(np.stack([(np.array(q)[:, 0] - bb[0]) / px + 20,
                                    hgt - ((np.array(q)[:, 1] - bb[1]) / px + 20)], 1)).astype(np.int32)
                 for q in cs.to_polygons()]
        acc = np.zeros((hgt, w), np.uint8)
        for q in polys:
            t = np.zeros_like(acc)
            cv2.fillPoly(t, [q], 1)
            acc ^= t
        H = np.where(acc > 0, z, H)
    Hs = cv2.GaussianBlur(H, (0, 0), 1.2)
    gy, gx = np.gradient(Hs)
    nrm = np.dstack([-gx / px * 0.12, -gy / px * 0.12, np.ones_like(Hs)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    light = np.array([-0.5, -0.6, 0.62]); light /= np.linalg.norm(light)
    shade = np.clip(nrm @ light, 0, 1)[..., None]
    floor = np.array([214, 160, 86]) / 255     # gold PLA
    ridge = np.array([246, 238, 222]) / 255    # ivory PLA
    bg = np.array([206, 202, 196]) / 255
    col = np.where((H > BASE_T)[..., None], ridge, floor)
    out = col * (0.45 + 0.75 * shade)
    # soft drop shadow
    sh = cv2.GaussianBlur((H > 0).astype(np.float32), (0, 0), 6)
    sh = np.roll(np.roll(sh, 10, 0), 8, 1)[..., None]
    bgimg = bg * (1 - 0.35 * sh)
    out = np.where((H > 0)[..., None], out, bgimg)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(path)


def angled_preview(model, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    mesh = model.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    tri = v[np.asarray(mesh.tri_verts)]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    keep = n[:, 2] > -0.5                       # skip the underside
    tri, n = tri[keep], n[keep]
    light = np.array([-0.4, -0.7, 0.6]); light /= np.linalg.norm(light)
    shade = 0.45 + 0.55 * np.clip(n @ light, 0, 1)
    zc = tri[:, :, 2].mean(1)
    base_col = np.where((zc > BASE_T + 0.05)[:, None],
                        np.array([[0.96, 0.93, 0.87]]), np.array([[0.84, 0.63, 0.34]]))
    fig = plt.figure(figsize=(10, 6), dpi=160, facecolor="#CECAC4")
    ax = fig.add_subplot(projection="3d", facecolor="#CECAC4")
    fc = base_col * shade[:, None]
    ax.add_collection3d(Poly3DCollection(tri, facecolors=fc, edgecolors=fc, linewidths=0.3))
    bb = model.bounding_box()
    ax.set(xlim=(bb[0], bb[3]), ylim=(bb[1], bb[4]), zlim=(-6, 10))
    ax.set_box_aspect((bb[3] - bb[0], bb[4] - bb[1], 16), zoom=1.1)
    ax.view_init(elev=38, azim=-80)
    ax.set_axis_off()
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())


def write_stl(model, path):
    mesh = model.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    tri = v[np.asarray(mesh.tri_verts)]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    data = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    data["n"], data["v"] = nrm, tri
    with open(path, "wb") as fh:
        fh.write(b"PSOne Labs lotus rangoli board".ljust(80, b" "))
        fh.write(np.uint32(len(tri)).tobytes())
        fh.write(data.tobytes())


if __name__ == "__main__":
    ref, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    model, sil, ridge = build(ref)
    bb = model.bounding_box()
    print(f"size {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm, "
          f"volume {model.volume()/1000:.1f} cm^3 (~{model.volume()/1000*1.24:.0f} g PLA at 100% infill), "
          f"genus {model.genus()}, parts {len(model.decompose())}")
    heightmap_preview(model, out / "lotus_rangoli_preview_top.png")
    angled_preview(model, out / "lotus_rangoli_preview_angle.png")
    if "--stl" in sys.argv:
        write_stl(model, out / "lotus_rangoli_board.stl")
        print("wrote", out / "lotus_rangoli_board.stl")
