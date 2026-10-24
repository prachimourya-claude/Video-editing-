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
HEIGHT = None          # overall height; None keeps the natural proportions (~0.66 x width)
BASE_T = 2.2           # solid floor thickness
RIDGE_H = 1.8          # ridge height above the floor
RIDGE_W = 2.2          # border width

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
    "outer_up": ([(722, 716), (688, 702), (650, 692), (600, 676), (548, 655), (500, 626), (450, 590),
                  (398, 540), (355, 488), (328, 442), (315, 405), (309, 368), (298, 328),
                  (284, 302), (272, 292)],
                 [(272, 292), (300, 299), (342, 310), (390, 330), (432, 356), (466, 390),
                  (494, 428), (530, 490), (590, 580), (660, 665), (720, 718)]),
    "inner": ([(722, 694), (688, 702), (660, 692), (625, 672), (580, 645), (545, 614), (515, 575),
               (495, 530), (486, 481), (488, 440), (498, 400), (514, 363), (530, 340)],
              [(530, 340), (552, 347), (590, 370), (622, 396), (650, 430), (685, 495),
               (712, 580), (724, 650), (720, 690)]),
    "low_side": ([(705, 742), (700, 720), (688, 704), (650, 698), (600, 690), (540, 684),
                  (470, 683), (410, 690), (360, 705), (322, 727), (292, 750), (266, 777), (245, 805)],
                 [(245, 805), (285, 803), (335, 814), (390, 834), (450, 849), (510, 847),
                  (565, 832), (612, 808), (660, 775), (705, 742)]),
}
# Centre petals (symmetric about x = CX): left half only, base (on axis) -> tip (on axis).
CENTER_PETALS = {
    "rear_top": [(CX, 660), (660, 600), (622, 500), (612, 420), (614, 360), (624, 300),
                 (642, 248), (668, 202), (700, 165), (730, 135), (750, 108), (760, 85), (CX, 62)],
    "bottom": [(CX, 715), (748, 706), (722, 696), (696, 698), (674, 712), (660, 738), (656, 768),
               (665, 802), (686, 836), (716, 866), (742, 890), (757, 910), (CX, 932)],
    "center": [(CX, 715), (735, 711), (705, 698), (680, 678), (660, 652), (642, 615), (632, 570),
               (632, 520), (642, 470), (662, 428), (690, 390), (722, 350), (748, 320), (CX, 300)],
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


def to_mm(loop, sx, sy):
    return [((x - CX) * sx, -y * sy) for x, y in loop]


def build():
    """Build at WIDTH x HEIGHT: scale the petal curves (not the border width) to fit."""
    loops = [petal_outline(n, sd) for n, sd in ORDER]
    pts = np.concatenate(loops)
    span = pts.max(0) - pts.min(0)
    sx = sy = WIDTH / span[0]
    if HEIGHT is not None:
        sy = HEIGHT / span[1]
    for _ in range(2):          # second pass corrects for the border sticking out past the curves
        model = _build(loops, sx, sy)
        bb = model.bounding_box()
        sx *= (WIDTH - (bb[3] - bb[0] - span[0] * sx)) / (span[0] * sx)
        if HEIGHT is not None:
            sy *= (HEIGHT - (bb[4] - bb[1] - span[1] * sy)) / (span[1] * sy)
        else:
            sy = sx
    return _build(loops, sx, sy), loops


def _build(loops, sx, sy):
    petals = [CrossSection([to_mm(l, sx, sy)], FillRule.NonZero) for l in loops]
    petals = [p if p.area() > 0 else CrossSection([to_mm(l[::-1], sx, sy)], FillRule.NonZero)
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
    # (also fills gold gaps under ~0.8 mm, which a 0.4 mm nozzle can't print anyway).
    ridge = (ridge.offset(0.4, rnd).offset(-0.4, rnd) ^ base).simplify(0.02)
    base = base.simplify(0.02)

    # Floor 0.05 mm proud of the borders so no wall meets the edge at a single point.
    model = Manifold.extrude(base.offset(0.05, rnd), BASE_T)
    model += Manifold.extrude(ridge, RIDGE_H + 0.3).translate((0, 0, BASE_T - 0.3))
    model = model.simplify(0.03)
    bb = model.bounding_box()
    return model.translate((-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2]))


def overlay(loops, ref, path):
    import cv2
    im = cv2.imread(ref)
    for l in loops:
        cv2.polylines(im, [np.round(l).astype(np.int32)], True, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.imwrite(path, im)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    opt = lambda name, default: (float(sys.argv[sys.argv.index(name) + 1])
                                 if name in sys.argv else default)
    WIDTH, HEIGHT = opt("--width", WIDTH), opt("--height", HEIGHT)
    BASE_T, RIDGE_H = opt("--floor", BASE_T), opt("--ridge-h", RIDGE_H)
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
