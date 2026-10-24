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
    # name: (side_a base->tip, side_b tip->base); points read off the reference.
    "outer_low": ([(700, 725), (560, 725), (470, 718), (400, 700), (340, 676), (290, 655),
                   (250, 628), (215, 595), (190, 565), (160, 541), (128, 531), (107, 525)],
                  [(107, 525), (122, 513), (150, 495), (190, 482), (240, 479), (280, 485),
                   (330, 503), (420, 550), (520, 615), (620, 675), (700, 725)]),
    "rear_side": ([(650, 560), (560, 470), (500, 410), (474, 370), (463, 325), (461, 280),
                   (465, 235), (475, 196)],
                  [(475, 196), (500, 210), (535, 230), (572, 256), (612, 292), (650, 360),
                   (670, 450), (650, 560)]),
    "outer_up": ([(710, 712), (650, 697), (590, 681), (540, 656), (490, 621), (440, 581),
                  (390, 531), (350, 481), (326, 440), (315, 405), (309, 368), (298, 328),
                  (284, 302), (272, 292)],
                 [(272, 292), (300, 299), (342, 310), (390, 330), (432, 356), (466, 390),
                  (494, 428), (530, 490), (590, 580), (660, 660), (710, 712)]),
    "inner": ([(735, 704), (680, 700), (620, 686), (575, 656), (540, 621), (511, 580),
               (491, 531), (483, 481), (486, 440), (496, 400), (513, 363), (530, 340)],
              [(530, 340), (552, 347), (590, 370), (622, 396), (650, 430), (690, 500),
               (725, 600), (740, 680), (735, 704)]),
    "low_side": ([(690, 716), (610, 702), (520, 692), (440, 690), (380, 694), (335, 704), (300, 726),
                  (271, 759), (255, 787), (245, 805)],
                 [(245, 805), (290, 798), (350, 801), (400, 815), (450, 826), (500, 822),
                  (550, 806), (600, 782), (640, 750), (690, 710)]),
}
# Centre petals (symmetric about x = CX): left half only, base (on axis) -> tip (on axis).
CENTER_PETALS = {
    "rear_top": [(CX, 660), (660, 600), (620, 500), (604, 420), (604, 360), (612, 300),
                 (630, 245), (655, 195), (686, 150), (720, 114), (748, 86), (CX, 62)],
    "bottom": [(CX, 702), (735, 703), (700, 705), (668, 710), (644, 722), (628, 745), (623, 772), (635, 803),
               (660, 832), (692, 862), (728, 886), (752, 910), (762, 930), (CX, 950)],
    "center": [(CX, 705), (720, 700), (676, 657), (650, 621), (635, 581), (630, 531),
               (635, 481), (650, 441), (676, 405), (706, 370), (740, 331), (CX, 300)],
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
