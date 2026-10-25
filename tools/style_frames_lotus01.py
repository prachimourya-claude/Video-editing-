"""Style frames for Diwali 02 (Psone Labs Lotus rangoli stencil), in the same night style as the Kalash reel.

usage: cd tools && python3 style_frames_lotus01.py <workdir> <outdir>
<workdir>/src holds L3.mp4 L4.mp4 L5.mp4 (VID-20261025-WA0003/4/5), plus fonts/ and music/ as for render_reel01_night.py.
"""
import os, subprocess, sys
from PIL import Image

import render_diwali01 as R
import render_reel01_night as N
import style_frames_teaser01 as T
from render_diwali01 import W, H, paste_center

BASE, OUTDIR = sys.argv[1], sys.argv[2]


def still(name, t):
    path = f"{BASE}/still_{name}_{t}.png"
    if not os.path.exists(path):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", f"{BASE}/src/{name}.mp4", "-vf",
                        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},{N.CLEAN}", "-frames:v", "1", path], check=True)
    return Image.open(path).convert("RGBA")


def frame_hook():
    """0-2.6s: NEW DAY, new product! over the white lotus in the arch."""
    aw, ah, ay = 900, 1180, 620
    f = N.fit(still("L4", 12.5), 0.78, (520, 700), (540, 1300))
    f.alpha_composite(N.night_frame(aw, ah, ay, 21))
    lan = N.TT.Lanterns(10, 23, 500, 1900, avoid=(90, 620, 990, 1800))
    lan.draw(f, 0.0)
    paste_center(f, T.glow_text("NEW DAY,", T.mont(48), T.CREAM, ga=0, track=18), W / 2, 230)
    paste_center(f, T.glow_text("new product!", T.yeseva(150), (T.GOLD_L, T.GOLD)), W / 2, 380)
    paste_center(f, N.chip("Lotus Rangoli Stencil", T.mont(40), fill=(120, 26, 96)), W / 2, 530)
    return f


def frame_printer():
    """6.4-11.4s: printed lotuses on the bed; title + made-by badge."""
    aw, ah, ay = 900, 1220, 520
    f = N.fit(still("L4", 3.0), 1.0, (540, 960), (540, 1100))
    f.alpha_composite(N.night_frame(aw, ah, ay, 25))
    paste_center(f, T.glow_text("Pesh hai hamara", T.allura(110), T.CREAM, glow=(255, 220, 160), ga=90), W / 2, 210)
    paste_center(f, T.glow_text("Lotus Stencil", T.yeseva(130), (T.GOLD_L, T.GOLD)), W / 2, 350)
    paste_center(f, N.chip("Designed & 3D printed by Psone Labs", T.mont(30)), W / 2, 1810)
    return f


def frame_steps():
    """15.4-21.4s: real rangoli being filled (the only coloured footage), steps chip."""
    aw, ah, ay = 920, 1280, 400
    f = N.fit(still("L5", 2.0), 0.95, (550, 870), (540, 1150))
    f.alpha_composite(N.night_frame(aw, ah, ay, 27))
    paste_center(f, T.glow_text("Bas 3 steps!", T.yeseva(110), (T.GOLD_L, T.GOLD)), W / 2, 230)
    paste_center(f, N.chip("2  Rang bharo", T.mont(40)), W / 2, 1790)
    return f


def frame_end():
    """22.4-26s: dusk end card."""
    f = T.grad_bg(T.DUSK, [0, 0.35, 0.65, 1], 10)
    T.bokeh(f, 26, 12, [T.PINK, (255, 170, 200), (200, 140, 230)], 900, 1900)
    T.stars(f, 90, 11, ymax=1100)
    N.TT.Lanterns(9, 13, 300, 1600, avoid=(120, 250, 960, 1350)).draw(f, 0.0)
    arch = T.gold_arch(820, 1100, [(70, 20, 80), (120, 26, 96), (150, 40, 110)])
    f.alpha_composite(arch, ((W - arch.width) // 2, 230 - 60))
    paste_center(f, N.lotus(0.6), W / 2, 560)
    paste_center(f, T.glow_text("Psone Labs", T.yeseva(140), (T.GOLD_L, T.GOLD)), W / 2, 760)
    paste_center(f, T.glow_text("LOTUS RANGOLI STENCIL", T.mont(34), T.CREAM, ga=0, track=8), W / 2, 890)
    paste_center(f, N.chip("DM to order", T.mont(44), pad=(50, 20)), W / 2, 1060)
    for k, (x, y, w) in enumerate(((300, 1560, 220), (780, 1560, 220), (540, 1680, 240))):
        T.diya_glow(f, x, y, w)
    paste_center(f, T.glow_text("शुभ दीपावली", T.tiro(80), T.GOLD_L, ga=120), W / 2, 1830)
    return f


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    frames = [("lotus_1_hook", frame_hook), ("lotus_2_printer", frame_printer), ("lotus_3_steps", frame_steps), ("lotus_4_end", frame_end)]
    thumbs = []
    for name, fn in frames:
        im = fn().convert("RGB")
        im.save(f"{OUTDIR}/{name}.png")
        thumbs.append(im.resize((W // 2, H // 2), Image.LANCZOS))
    sheet = Image.new("RGB", (W // 2 * 4 + 50, H // 2 + 20), (255, 255, 255))
    for k, t in enumerate(thumbs):
        sheet.paste(t, (10 + k * (W // 2 + 10), 10))
    sheet.save(f"{OUTDIR}/lotus_sheet.png")
    print("wrote", OUTDIR)
