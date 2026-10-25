"""Storyboard stills for the Lotus reel in the chosen look (Option B, Rose & Gold), with the client's own script:
  "New day, new product! Toh is baar humne banaya hai Lotus Stencil. Just fill in the colours and you're good to go!"

usage: cd tools && python3 style_frames_lotus_b.py <workdir> <outdir>   (same <workdir> as style_frames_lotus01.py)
"""
import os
from PIL import Image

import style_options_lotus01 as O
import style_frames_teaser01 as T
from render_diwali01 import W, H, paste_center

OUTDIR = O.OUTDIR


def hook():
    """0-2.5s  New day, new product!"""
    f = O.b_bg(4)
    paste_center(f, T.glow_text("New day,", T.allura(140), T.CREAM, glow=(255, 200, 220), ga=90), W / 2, 260)
    paste_center(f, T.glow_text("NEW PRODUCT!", T.yeseva(120), (T.GOLD_L, T.GOLD)), W / 2, 420)
    paste_center(f, O.ring_photo("L4", 12.5, (540, 720), 0.72, 760), W / 2, 1150)
    return f


def intro():
    """2.5-6s  Toh is baar humne banaya hai Lotus Stencil."""
    f = O.b_bg(14)
    paste_center(f, T.glow_text("Is baar humne banaya...", T.allura(110), T.CREAM, glow=(255, 200, 220), ga=90), W / 2, 260)
    paste_center(f, T.glow_text("LOTUS STENCIL", T.yeseva(130), (T.GOLD_L, T.GOLD)), W / 2, 410)
    paste_center(f, O.ring_photo("L4", 3.0, (540, 960), 0.95, 760), W / 2, 1150)
    paste_center(f, O.R.pill("Designed & 3D printed by us", T.mont(36), fg=O.ROSE_D, bg=T.GOLD_L, pad=(40, 18)), W / 2, 1780)
    return f


def product():
    """6-8.5s  (no voice) slow-motion white lotus, the stencil itself."""
    f = O.b_bg(16)
    paste_center(f, O.ring_photo("L4", 11.0, (540, 690), 0.76, 820), W / 2, 1060)
    paste_center(f, T.glow_text("LOTUS RANGOLI STENCIL", T.mont(40), T.CREAM, ga=0, track=10), W / 2, 1720)
    return f


def fill():
    """8.5-12s  Just fill in the colours and you're good to go!"""
    f = O.b_bg(18)
    paste_center(f, T.glow_text("Just fill in the colours", T.allura(110), T.CREAM, glow=(255, 200, 220), ga=90), W / 2, 260)
    paste_center(f, T.glow_text("& you're good to go!", T.yeseva(96), (T.GOLD_L, T.GOLD)), W / 2, 400)
    paste_center(f, O.ring_photo("L5", 6.5, (550, 750), 0.85, 760), W / 2, 1150)
    return f


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    frames = [("b1_hook", hook), ("b2_intro", intro), ("b3_product", product), ("b4_fill", fill), ("b5_end", O.b_end)]
    thumbs = []
    for name, fn in frames:
        im = fn().convert("RGB")
        im.save(f"{OUTDIR}/{name}.png")
        thumbs.append(im.resize((W // 3, H // 3), Image.LANCZOS))
    sheet = Image.new("RGB", (W // 3 * 5 + 60, H // 3 + 20), (255, 255, 255))
    for k, t in enumerate(thumbs):
        sheet.paste(t, (10 + k * (W // 3 + 10), 10))
    sheet.save(f"{OUTDIR}/b_sheet.png")
    print("wrote", OUTDIR)
