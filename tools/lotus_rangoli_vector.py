#!/usr/bin/env python3
"""Solid lotus rangoli filling board, drawn as clean vector petals.

Each petal is a smooth closed curve (mirrored left/right for perfect
symmetry). Petals are stacked back-to-front: a petal's outline is hidden
where a petal in front of it covers it, so borders meet in clean joins.
The outlines become raised ridges on a solid, hole-free floor.

Usage:
  python3 tools/lotus_rangoli_vector.py OUT_DIR [--stl] [--overlay REF.png]
Without --stl it only writes preview images (approve those first).
Needs: pip install numpy pillow opencv-python-headless manifold3d matplotlib
"""
import sys
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold

import lotus_rangoli_board as render   # preview + STL helpers

# --- Parameters (mm) ---------------------------------------------------------
WIDTH = 150.0          # overall width
BASE_T = 2.2           # solid floor thickness
RIDGE_H = 1.8          # ridge height above the floor
RIDGE_W = 2.8          # border width

# --- Petals, in reference-image pixels (x right, y down, centre x = 768) -----
# Each petal: points along one side from base to tip, then the other side from
# tip back to base. Sides are smoothed separately so tips stay pointed.
CX = 768
LEFT_PETALS = {
    # name: (side_a base->tip, side_b tip->base)
    "outer_low": ([(690, 700), (560, 700), (420, 688), (300, 645), (200, 590), (115, 532)],
                  [(115, 532), (175, 500), (250, 488), (330, 500), (430, 545), (560, 620), (690, 700)]),
    "rear_side": ([(640, 560), (560, 470), (500, 400), (472, 320), (478, 252), (487, 205)],
                  [(487, 205), (535, 228), (585, 275), (622, 340), (650, 430), (660, 520), (640, 560)]),
    "outer_up": ([(700, 702), (600, 690), (480, 645), (390, 580), (335, 495), (300, 400), (283, 297)],
                 [(283, 297), (350, 303), (420, 335), (475, 385), (520, 450), (580, 560), (650, 650), (700, 702)]),
    "inner": ([(735, 702), (640, 690), (565, 652), (515, 590), (492, 515), (498, 435), (515, 380), (535, 342)],
              [(535, 342), (585, 370), (630, 410), (680, 470), (720, 560), (740, 650), (735, 702)]),
    "low_side": ([(690, 712), (600, 702), (480, 702), (380, 715), (300, 750), (248, 800)],
                 [(248, 800), (320, 822), (420, 835), (520, 828), (600, 805), (660, 770), (690, 712)]),
}
# Centre petals (symmetric about x = CX): left half only, base (on axis) -> tip (on axis).
CENTER_PETALS = {
    "rear_top": [(CX, 660), (680, 620), (626, 520), (606, 420), (614, 330), (648, 248), (700, 172), (742, 112), (CX, 62)],
    "bottom": [(CX, 945), (725, 900), (670, 845), (632, 785), (628, 735), (660, 705), (CX, 698)],
    "center": [(CX, 705), (690, 692), (645, 640), (628, 560), (645, 470), (690, 395), (735, 335), (CX, 298)],
}
# Back-to-front drawing order.
ORDER = [("outer_low", "L"), ("outer_low", "R"), ("rear_side", "L"), ("rear_side", "R"),
         ("rear_top", "C"), ("outer_up", "L"), ("outer_up", "R"), ("low_side", "L"),
         ("low_side", "R"), ("inner", "L"), ("inner", "R"), ("bottom", "C"), ("center", "C")]


def catmull_rom(pts, n=24):
    """Smooth open curve through pts (endpoints kept)."""
    p = np.asarray(pts, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.array(out)


def petal_outline(name, side):
    if side == "C":
        half = catmull_rom(CENTER_PETALS[name])           # base -> tip, left half
        right = half[::-1].copy()
        right[:, 0] = 2 * CX - right[:, 0]                # tip -> base, right half
        loop = np.vstack([half, right[1:-1]])
    else:
        a, b = LEFT_PETALS[name]
        loop = np.vstack([catmull_rom(a), catmull_rom(b)[1:-1]])
        if side == "R":
            loop = loop[::-1].copy()
            loop[:, 0] = 2 * CX - loop[:, 0]
    return loop


def to_mm(loop, s):
    return [((x - CX) * s, -y * s) for x, y in loop]


def build():
    loops = [petal_outline(n, sd) for n, sd in ORDER]
    allx = np.concatenate([l[:, 0] for l in loops])
    s = WIDTH / (allx.max() - allx.min() + RIDGE_W / (WIDTH / 1430))   # include stroke width
    petals = [CrossSection([to_mm(l, s)], FillRule.NonZero) for l in loops]
    petals = [p if p.area() > 0 else CrossSection([to_mm(l[::-1], s)], FillRule.NonZero)
              for p, l in zip(petals, loops)]

    hw = RIDGE_W / 2
    rnd = JoinType.Round
    ridge = CrossSection()
    for i, p in enumerate(petals):
        band = p.offset(hw, rnd) - p.offset(-hw, rnd)
        front = CrossSection()
        for q in petals[i + 1:]:
            front += q.offset(-hw, rnd)
        ridge += band - front

    base = CrossSection()
    for p in petals:
        base += p.offset(hw, rnd)
    # Keep only outer boundaries: fill any pocket enclosed between petals.
    outers = [poly for poly in base.to_polygons()
              if CrossSection([poly], FillRule.NonZero).area() > 0]
    base = CrossSection(outers, FillRule.NonZero)
    # Smooth hairline nicks where outlines touch at a tangent.
    ridge = ridge.offset(0.3, rnd).offset(-0.3, rnd) ^ base

    model = Manifold.extrude(base, BASE_T)
    model += Manifold.extrude(ridge, RIDGE_H + 0.3).translate((0, 0, BASE_T - 0.3))
    model = model.simplify(0.01)
    bb = model.bounding_box()
    model = model.translate((-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2]))
    return model, loops


def overlay(loops, ref, path):
    import cv2
    im = cv2.imread(ref)
    for l in loops:
        cv2.polylines(im, [np.round(l).astype(np.int32)], True, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.imwrite(path, im)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    render.BASE_T, render.RIDGE_H = BASE_T, RIDGE_H
    model, loops = build()
    bb = model.bounding_box()
    print(f"size {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm, "
          f"volume {model.volume()/1000:.1f} cm^3 (~{model.volume()/1000*1.24:.0f} g PLA at 100% infill), "
          f"genus {model.genus()}, parts {len(model.decompose())}")
    if "--overlay" in sys.argv:
        overlay(loops, sys.argv[sys.argv.index("--overlay") + 1], str(out / "overlay_check.png"))
    render.heightmap_preview(model, out / "lotus_rangoli_preview_top.png")
    render.angled_preview(model, out / "lotus_rangoli_preview_angle.png")
    if "--stl" in sys.argv:
        render.write_stl(model, out / "lotus_rangoli_board.stl")
        print("wrote", out / "lotus_rangoli_board.stl")
