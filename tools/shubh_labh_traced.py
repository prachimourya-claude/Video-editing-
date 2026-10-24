#!/usr/bin/env python3
"""Shubh / Labh hanging plaques traced from a reference image.

The calligraphic lettering (with its flourishes) and the plaque silhouette are
traced from the image and smoothed; the silhouette is mirrored so left and
right match exactly. The border is an even band inside the silhouette and the
hanging loops are true circles with through-holes.

Usage:
  python3 tools/shubh_labh_traced.py REF.png OUT_DIR [--stl]
Without --stl it only writes preview images (approve those first).
Needs: pip install numpy opencv-python-headless pillow manifold3d matplotlib
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold

import lotus_rangoli_board as render

# --- Parameters (mm) ---------------------------------------------------------
HEIGHT = 115.0         # overall height including both loops (width comes out ~109 mm)
FLOOR_T = 2.0          # solid floor thickness
RAISED_H = 1.5         # border + lettering height above the floor
BORDER_W = 3.0         # border width (matches the reference proportions)
LOOP_OD = 11.0         # hanging loop outer diameter
LOOP_ID = 4.5          # hanging loop hole diameter
UP = 4                 # tracing upscale factor (smoother curves)
PLAQUES = {"shubh": (230, 915), "labh": (905, 1600)}   # x-range of each plaque in the image


def masks(ref):
    im = cv2.imread(ref)[:, :, ::-1].astype(np.int16)
    v = im.mean(-1)
    sat = im[..., 0] - im[..., 2]
    cream = ((v > 192) & (sat < 85)).astype(np.uint8)
    gold = (sat > 95).astype(np.uint8)
    return cream, gold


def smooth_up(mask, sigma):
    """Upscale a binary mask and smooth its edges (removes pixel wobble)."""
    big = cv2.resize(mask.astype(np.float32), None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR)
    return (cv2.GaussianBlur(big, (0, 0), sigma * UP) > 0.5).astype(np.uint8)


def largest(mask):
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask)
    return (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)


def to_cs(mask, mm, origin, eps=0.6):
    """Binary mask (upscaled px) -> CrossSection in mm, y up, holes kept."""
    cnts, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    for c in cnts:
        c = cv2.approxPolyDP(c, eps, True)[:, 0, :].astype(float)
        if len(c) >= 3:
            polys.append([((x - origin[0]) * mm, (origin[1] - y) * mm) for x, y in c])
    return CrossSection(polys, FillRule.EvenOdd)


def build(ref, word):
    cream, gold = masks(ref)
    x0, x1 = PLAQUES[word]
    cream, gold = cream[:, x0:x1], gold[:, x0:x1]
    rnd = JoinType.Round

    # Plaque = largest cream/gold blob near the gold field (drops background speckle);
    # its enclosed background bits are the loop holes.
    g = largest(cv2.morphologyEx(gold, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)))
    gc, _ = cv2.findContours(g, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    near = np.zeros_like(g)
    cv2.drawContours(near, gc, -1, 1, cv2.FILLED)
    near = cv2.dilate(near, np.ones((3, 3), np.uint8), iterations=90)
    obj = cv2.morphologyEx((cream | gold) & near, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    obj = largest(cv2.morphologyEx(obj, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)))
    filled = obj.copy()
    cnts, _ = cv2.findContours(obj, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(filled, cnts, -1, 1, cv2.FILLED)
    n, lab, st, cen = cv2.connectedComponentsWithStats(((filled == 1) & (obj == 0)).astype(np.uint8))
    holes = sorted([cen[i] for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 150],
                   key=lambda c: c[1])
    top, bot = holes[0], holes[-1]                       # loop centres (image px)
    axis = (top[0] + bot[0]) / 2
    mm = (HEIGHT - LOOP_OD) / (bot[1] - top[1]) / UP     # mm per upscaled px
    origin = (axis * UP, (top[1] + bot[1]) / 2 * UP)

    # Plaque body without the loops, mirrored for perfect left/right symmetry.
    body = filled.copy()
    ring_r = int(round(LOOP_OD / 2 / (mm * UP) * 1.45))   # clears the traced ring fully
    for c in (top, bot):
        cv2.circle(body, (int(round(c[0])), int(round(c[1]))), ring_r, 0, -1)
    body = largest(body)
    big = smooth_up(body, 1.5).astype(np.float32)
    flip = cv2.warpAffine(big, np.float32([[-1, 0, 2 * origin[0]], [0, 1, 0]]),
                          (big.shape[1], big.shape[0]))
    body = ((big + flip) / 2 >= 0.5).astype(np.uint8)
    body_cs = to_cs(body, mm, origin)

    # Lettering: cream strokes inside the border, traced and smoothed.
    inner_px = cv2.erode(filled, np.ones((3, 3), np.uint8), iterations=int(BORDER_W / (mm * UP)) + 3)
    letters = cream & inner_px
    letters = cv2.morphologyEx(letters, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(letters)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] > 500        # letters only, not border curls
    letters = smooth_up(keep[lab].astype(np.uint8), 1.6)
    text_cs = to_cs(letters, mm, origin)

    # Loops sit right on the tips (as in the reference); scale so the overall
    # height, loop to loop, is exactly HEIGHT.
    sink = 1.2                                       # how far each ring overlaps its tip
    lo, hi = body_cs.bounds()[1], body_cs.bounds()[3]
    f = (HEIGHT - 2 * (LOOP_OD - sink)) / (hi - lo)
    body_cs, text_cs = body_cs.scale((f, f)), text_cs.scale((f, f))
    lo, hi = lo * f, hi * f
    text_cs = text_cs ^ body_cs.offset(-BORDER_W + 0.2, rnd)
    border_cs = body_cs - body_cs.offset(-BORDER_W, rnd)

    # Hanging loops: true circles + a short neck into the tip; holes go right through.
    loops, hole_cs = CrossSection(), CrossSection()
    for tip, toward in ((hi, -1), (lo, 1)):
        cy = tip - toward * (LOOP_OD / 2 - sink)
        loops += CrossSection.circle(LOOP_OD / 2, 96).translate((0, cy))
        loops += CrossSection.batch_hull([
            CrossSection.circle(1.8, 32).translate((0, cy + toward * (LOOP_ID / 2 + 1.6))),
            CrossSection.circle(2.2, 32).translate((0, tip + toward * 2.5))])
        hole_cs += CrossSection.circle(LOOP_ID / 2, 64).translate((0, cy))

    floor = (body_cs + loops) - hole_cs
    raised = (border_cs + text_cs + loops) - hole_cs
    model = Manifold.extrude(floor.offset(0.05, rnd), FLOOR_T)
    model += Manifold.extrude(raised, RAISED_H + 0.3).translate((0, 0, FLOOR_T - 0.3))
    model = model.simplify(0.02)
    bb = model.bounding_box()
    return model.translate((-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2]))


if __name__ == "__main__":
    ref, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    render.BASE_T, render.RIDGE_H = FLOOR_T, RAISED_H
    for word in PLAQUES:
        m = build(ref, word)
        bb = m.bounding_box()
        print(f"{word}: {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm, "
              f"~{m.volume()/1000*1.24:.0f} g PLA at 100% infill, genus {m.genus()}, "
              f"parts {len(m.decompose())}")
        render.heightmap_preview(m, out / f"{word}_preview_top.png")
        render.angled_preview(m, out / f"{word}_preview_angle.png", elev=50, azim=-80)
        if "--stl" in sys.argv:
            render.write_stl(m, out / f"{word}_plaque.stl")
            print("wrote", out / f"{word}_plaque.stl")
