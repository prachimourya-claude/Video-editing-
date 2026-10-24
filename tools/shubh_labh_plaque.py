#!/usr/bin/env python3
"""Shubh / Labh hanging plaques: solid floor, raised border + Devanagari text,
hanging loops with real through-holes. One STL per plaque.

Usage:
  python3 tools/shubh_labh_plaque.py OUT_DIR FONT.ttf [--stl]
Without --stl it only writes preview images (approve those first).
Needs: pip install numpy manifold3d uharfbuzz fonttools opencv-python-headless pillow matplotlib
"""
import sys
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold

import lotus_rangoli_board as render
from devanagari_text import text_polygons
from lotus_rangoli_vector import catmull_rom

# --- Parameters (mm) ---------------------------------------------------------
HEIGHT = 120.0         # overall height including both loops
FLOOR_T = 2.0          # solid floor thickness
RAISED_H = 1.5         # border + lettering height above the floor
BORDER_W = 2.5         # border width
LOOP_OD = 11.0         # hanging loop outer diameter
LOOP_ID = 4.5          # hanging loop hole diameter
TEXT_MAX_W = 0.60      # lettering width as a fraction of plaque width
TEXT_MAX_H = 0.38      # lettering height as a fraction of plaque height (without loops)
TEXT_GAP = 1.5         # minimum gap between lettering and border
WORDS = {"shubh": "शुभ", "labh": "लाभ"}

# Top-right quarter of the outline, read off the reference (px, centre origin,
# y down): top point -> shoulder lobe -> inward cusp -> side lobe -> side point.
SHOULDER = [(0, -297), (23, -283), (50, -257), (83, -230), (110, -213), (130, -197),
            (143, -177), (146, -157), (140, -140), (123, -127)]
SIDE = [(123, -127), (156, -137), (190, -130), (223, -117), (250, -90), (270, -57),
        (286, -23), (306, 0)]
TIP_TO_LOOP = 26       # px from the outer tip to the loop centre


def outline_px():
    q = np.vstack([catmull_rom(SHOULDER), catmull_rom(SIDE)[1:]])   # top -> right point
    tr = q
    br = (q * [1, -1])[::-1][1:]                                     # right point -> bottom
    bl = (q * [-1, -1])[1:]                                          # bottom -> left point
    tl = (q * [-1, 1])[::-1][1:-1]                                   # left point -> top
    return np.vstack([tr, br, bl, tl])


def section(polys):
    cs = CrossSection(polys, FillRule.NonZero)
    if cs.area() <= 0:
        cs = CrossSection([p[::-1] for p in polys], FillRule.NonZero)
    return cs


def _extent(text, font):
    pts = np.concatenate(text_polygons(text, font))
    return pts.min(0), pts.max(0)


def _place(text, font, k):
    mn, mx = _extent(text, font)
    lmn, lmx = _extent(WORDS["labh"], font)
    cx, cy = (mn[0] + mx[0]) / 2, (lmn[1] + lmx[1]) / 2
    return section([[((x - cx) * k, (y - cy) * k) for x, y in p]
                    for p in text_polygons(text, font)])


def build(word, font):
    rnd = JoinType.Round
    px_h = 2 * (297 + TIP_TO_LOOP) + 0       # loop centre to loop centre
    s = (HEIGHT - LOOP_OD) / px_h            # mm per reference px
    out = outline_px() * s
    plaque = section([[(x, -y) for x, y in out]])
    w = out[:, 0].max() - out[:, 0].min()
    h = out[:, 1].max() - out[:, 1].min()

    # Border: a band just inside the silhouette.
    border = plaque - plaque.offset(-BORDER_W, rnd)

    # Loops (top and bottom) with a reinforcing neck into the pointed tip.
    loop_y = (297 + TIP_TO_LOOP) * s
    hole = CrossSection.circle(LOOP_ID / 2, 64)
    loops, holes = CrossSection(), CrossSection()
    for sign in (1, -1):
        c = (0, sign * loop_y)
        ring = CrossSection.circle(LOOP_OD / 2, 96).translate(c)
        neck = CrossSection.batch_hull([
            CrossSection.circle(1.8, 32).translate((0, sign * (loop_y - 4.6))),
            CrossSection.circle(2.0, 32).translate((0, sign * (loop_y - 6.5)))])
        loops += ring + neck
        holes += hole.translate(c)

    # Lettering: shaped Devanagari, same size on both plaques. Centred horizontally on
    # the word, vertically on the main letter body (shared by both words) so शुभ's ु
    # hangs below the line like the reference. Shrunk until every word clears the border.
    inner = plaque.offset(-BORDER_W - TEXT_GAP, rnd)
    k = min(min(TEXT_MAX_W * w / (b[1][0] - b[0][0]), TEXT_MAX_H * h / (b[1][1] - b[0][1]))
            for b in (_extent(t, font) for t in WORDS.values()))
    while any((_place(t, font, k) - inner).area() > 1e-6 for t in WORDS.values()):
        k *= 0.98
    text = _place(WORDS[word], font, k)

    floor = (plaque + loops) - holes
    raised = (border + loops + text) - holes
    model = Manifold.extrude(floor, FLOOR_T)
    model += Manifold.extrude(raised, RAISED_H + 0.3).translate((0, 0, FLOOR_T - 0.3))
    model = model.simplify(0.02)
    bb = model.bounding_box()
    return model.translate((-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2]))


if __name__ == "__main__":
    out, font = Path(sys.argv[1]), sys.argv[2]
    out.mkdir(parents=True, exist_ok=True)
    render.BASE_T, render.RIDGE_H = FLOOR_T, RAISED_H
    for word in WORDS:
        m = build(word, font)
        bb = m.bounding_box()
        print(f"{word}: {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm, "
              f"~{m.volume()/1000*1.24:.0f} g PLA at 100% infill, genus {m.genus()}, "
              f"parts {len(m.decompose())}")
        render.heightmap_preview(m, out / f"{word}_preview_top.png")
        render.angled_preview(m, out / f"{word}_preview_angle.png", elev=50, azim=-80)
        if "--stl" in sys.argv:
            render.write_stl(m, out / f"{word}_plaque.stl")
            print("wrote", out / f"{word}_plaque.stl")
