"""Three minimal looks for the tea-light lantern reel (Diwali 03). The client's full clip stays full screen and real;
only light text and one small accent per look. Hook + glow end card for each.

  A  Warm Minimal  - clean cuts, soft warm grade, small cream serif text with a thin gold rule
  B  Diya Glow     - moody: edges gently darkened, gold glowing serif title, a few tiny floating sparks
  C  Terracotta    - matches the product: terracotta + chocolate pills, handwritten notes, tiny hand-drawn stars
  D  Festive Frame - colourful: clip in a white-edged rounded frame on saffron-to-magenta, string lights, sticker banners
  E  Star Pattern Pop - the lantern's own star lattice drawn in saffron/teal/pink at the corners, bold sticker titles
  F  Glow Night    - string lights; at lights-off a purple-pink night with sky lanterns and line fireworks

usage: cd tools && python3 style_options_lantern01.py <workdir> <outdir> [letters, e.g. DEF]   (<workdir>/src/T1.mp4 = VID-20261026-WA0001)
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import render_diwali01 as R
import style_frames_teaser01 as T
from render_diwali01 import W, H, paste_center, text_mask, blob

BASE, OUTDIR = sys.argv[1], sys.argv[2]
F = BASE + "/fonts/"
font = lambda name, s: ImageFont.truetype(F + name, s)

CREAM = (255, 246, 230)
GOLD = (240, 190, 96)
TERRA = (196, 104, 58)
CHOC = (74, 36, 30)


def still(t, grade="eq=contrast=1.04:saturation=1.08,unsharp=5:5:0.5"):
    path = f"{BASE}/still_T1_{t}.png"
    if not os.path.exists(path):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", f"{BASE}/src/T1.mp4", "-vf",
                        f"scale={W}:{H}:flags=lanczos,{grade}", "-frames:v", "1", path], check=True)
    return Image.open(path).convert("RGBA")


def txt(t, f, fill, shadow=190, track=0):
    if track:
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        wds = [d.textlength(ch, font=f) for ch in t]
        m = Image.new("L", (int(sum(wds) + track * len(t)) + 24, int(f.size * 1.5)), 0)
        x = 12
        for ch, w in zip(t, wds):
            ImageDraw.Draw(m).text((x, m.height / 2), ch, font=f, fill=255, anchor="lm")
            x += w + track
    else:
        m = text_mask(t, f)
    im = Image.new("RGBA", m.size, fill + (0,))
    im.putalpha(m)
    return R.with_shadow(im, offset=(0, 4), blur=10, alpha=shadow, color=(15, 8, 6)) if shadow else im


def warm(im, k=0.06):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    a = a * np.array([1 + k, 1.0, 1 - k])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")


def vignette(im, strength=0.55):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - strength * np.clip((((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2) * 2.6, 0, 1)
    a = np.asarray(im.convert("RGB")).astype(np.float32) * v[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")


def rule(f, y, w=260, col=GOLD):
    ImageDraw.Draw(f).line((W / 2 - w / 2, y, W / 2 + w / 2, y), fill=col + (230,), width=3)


def star(f, x, y, r, col, width=3):
    d = ImageDraw.Draw(f)
    for k in range(6):
        a = math.pi * k / 6
        d.line((x - r * math.cos(a), y - r * math.sin(a), x + r * math.cos(a), y + r * math.sin(a)), fill=col + (230,), width=width)


def chip(t, f, bg, fg=CREAM, pad=(34, 16)):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.textbbox((0, 0), t, font=f)
    w, h = bb[2] - bb[0] + 2 * pad[0], bb[3] - bb[1] + 2 * pad[1]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg + (240,))
    ImageDraw.Draw(im).text((w / 2, h / 2), t, font=f, fill=fg, anchor="mm")
    return R.with_shadow(im, offset=(0, 6), blur=12, alpha=110, color=(15, 8, 6))


# ---------------------------------------------------------------- A: Warm Minimal
def a_hook():
    f = warm(still(4.5))
    paste_center(f, txt("NEW DAY, NEW PRODUCT", font("montserrat_sb.ttf", 40), CREAM, track=10), W / 2, 240)
    rule(f, 300)
    paste_center(f, txt("Jaali Lantern", font("cormorant_i.ttf", 120), CREAM), W / 2, 390)
    return f


def a_end():
    f = warm(still(40.0), 0.03)
    paste_center(f, txt("Order now", font("cormorant_i.ttf", 130), CREAM), W / 2, 330)
    rule(f, 420)
    paste_center(f, txt("DM TO ORDER", font("montserrat_sb.ttf", 40), CREAM, track=10), W / 2, 480)
    paste_center(f, txt("Happy Diwali", font("cormorant_i.ttf", 90), GOLD), W / 2, 1680)
    return f


# ---------------------------------------------------------------- B: Diya Glow
def sparks(f, seed, n=18, y0=500, y1=1500):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y, r = rng.uniform(150, W - 150), rng.uniform(y0, y1), rng.uniform(2, 4.5)
        paste_center(f, blob(10, (255, 200, 110), 150), x, y)
        ImageDraw.Draw(f).ellipse((x - r, y - r, x + r, y + r), fill=(255, 236, 190, 230))


def b_hook():
    f = vignette(still(4.5), 0.45)
    paste_center(f, T.glow_text("New day, new product", T.allura(110), CREAM, glow=(255, 190, 110), ga=80), W / 2, 250)
    paste_center(f, T.glow_text("JAALI LANTERN", T.yeseva(110), (T.GOLD_L, T.GOLD)), W / 2, 390)
    return f


def b_end():
    f = vignette(still(40.0), 0.35)
    sparks(f, 3)
    paste_center(f, T.glow_text("Roshni wali Diwali", T.allura(120), CREAM, glow=(255, 190, 110), ga=90), W / 2, 300)
    paste_center(f, T.glow_text("ORDER NOW", T.yeseva(110), (T.GOLD_L, T.GOLD)), W / 2, 440)
    paste_center(f, T.glow_text("DM to order", T.mont(40), CREAM, ga=0, track=6), W / 2, 1700)
    return f


# ---------------------------------------------------------------- C: Terracotta
def c_hook():
    f = still(4.5)
    paste_center(f, chip("NEW DAY, NEW PRODUCT!", font("poppins_xb.ttf", 44), TERRA), W / 2, 250)
    paste_center(f, txt("our jaali lantern", font("caveat.ttf", 120), CREAM), W / 2, 400)
    for x, y, r in ((200, 360, 22), (880, 330, 16), (860, 470, 12)):
        star(f, x, y, r, CREAM)
    return f


def c_end():
    f = still(40.0)
    paste_center(f, txt("ab Diwali hogi aur roshan", font("caveat.ttf", 104), CREAM), W / 2, 300)
    for x, y, r in ((170, 260, 20), (920, 230, 14), (900, 380, 10)):
        star(f, x, y, r, GOLD)
    paste_center(f, chip("Order now · DM to order", font("poppins_xb.ttf", 46), TERRA), W / 2, 1700)
    return f


# ---------------------------------------------------------------- D: Festive Frame
SAFFRON = (255, 153, 51)
MAGENTA = (214, 40, 120)
TEAL = (0, 150, 150)
PINK = (255, 105, 160)


def grad_bg(c1, c2):
    g = np.linspace(0, 1, H)
    col = np.stack([np.interp(g, [0, 1], [c1[c], c2[c]]) for c in range(3)], 1)
    return Image.fromarray(np.broadcast_to(col[:, None, :], (H, W, 3)).astype(np.uint8)).convert("RGBA")


def framed(t, w=940, h=1560, y=1070):
    """The full clip, slightly smaller, in a rounded white-edged frame on a saffron-to-magenta background."""
    f = grad_bg(SAFFRON, MAGENTA)
    T.bokeh(f, 24, 5, [(255, 230, 150), (255, 190, 220), (255, 255, 255)], 0, H)
    st = still(t)
    sc = max(w / W, h / H)
    im = st.resize((int(W * sc), int(H * sc)), Image.LANCZOS)
    im = im.crop(((im.width - w) // 2, (im.height - h) // 2, (im.width - w) // 2 + w, (im.height - h) // 2 + h))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=44, fill=255)
    im.putalpha(m)
    card = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, w + 19, h + 19), radius=54, fill=(255, 250, 240, 255))
    card.alpha_composite(im, (10, 10))
    paste_center(f, R.with_shadow(card, offset=(0, 14), blur=24, alpha=120, color=(90, 20, 40)), W / 2, y)
    T.string_lights(f, 30, 70, n=14)
    return f


def banner(t, f_, bg, fg=CREAM, rot=-3):
    return chip(t, f_, bg, fg, pad=(44, 20)).rotate(rot, expand=True, resample=Image.BICUBIC)


def d_hook():
    f = framed(4.5)
    paste_center(f, banner("NEW DAY, NEW PRODUCT!", font("poppins_xb.ttf", 46), TEAL), W / 2, 330)
    paste_center(f, txt("Jaali Lantern", font("caveat.ttf", 130), CREAM), W / 2, 1750)
    return f


def d_end():
    f = framed(40.0)
    paste_center(f, banner("ORDER NOW!", font("poppins_xb.ttf", 60), TEAL, rot=3), W / 2, 330)
    paste_center(f, txt("DM to order · Happy Diwali", font("caveat.ttf", 92), CREAM), W / 2, 1750)
    return f


# ---------------------------------------------------------------- E: Star Pattern Pop
def asanoha(size, col, alpha=200, cell=90, width=4):
    """The lantern's own star-lattice (asanoha) pattern as line art."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    hgt = cell * math.sqrt(3) / 2
    for r in range(-1, int(size / hgt) + 2):
        for c in range(-1, int(size / cell) + 2):
            x0 = c * cell + (r % 2) * cell / 2
            y0 = r * hgt
            tri = [(x0, y0), (x0 + cell, y0), (x0 + cell / 2, y0 + hgt)]
            cx, cy = sum(p[0] for p in tri) / 3, sum(p[1] for p in tri) / 3
            for px, py in tri:
                d.line((cx, cy, px, py), fill=col + (alpha,), width=width)
            d.line(tri + [tri[0]], fill=col + (alpha,), width=width)
    return im


def corner_pattern(col, size=420, flip=False):
    pat = asanoha(size, col, 220, 80, 4)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    fade = np.clip(1.25 - np.hypot(xx, yy) / size, 0, 1)
    if flip:
        fade = fade[:, ::-1]
    a = np.asarray(pat.getchannel("A")).astype(np.float32) * fade
    pat.putalpha(Image.fromarray(a.astype(np.uint8)))
    return pat


def e_hook():
    f = still(4.5)
    f.alpha_composite(corner_pattern(SAFFRON), (0, 0))
    f.alpha_composite(corner_pattern(TEAL, flip=True), (W - 420, 0))
    paste_center(f, banner("NEW DAY,", font("poppins_xb.ttf", 64), MAGENTA, rot=-4), W / 2 - 120, 260)
    paste_center(f, banner("NEW PRODUCT!", font("poppins_xb.ttf", 64), TEAL, rot=3), W / 2 + 90, 390)
    paste_center(f, chip("Jaali Lantern", font("caveat.ttf", 84), SAFFRON, pad=(40, 6)), W / 2, 1730)
    return f


def e_end():
    f = still(40.0)
    for col, x, y, flip in ((PINK, 0, H - 420, False), (SAFFRON, W - 420, H - 420, True)):
        cp = corner_pattern(col, flip=flip).transpose(Image.FLIP_TOP_BOTTOM)
        f.alpha_composite(cp, (x, y))
    paste_center(f, banner("ORDER NOW!", font("poppins_xb.ttf", 70), MAGENTA, rot=-3), W / 2, 300)
    paste_center(f, banner("DM to order", font("poppins_xb.ttf", 48), TEAL, rot=2), W / 2, 450)
    return f


# ---------------------------------------------------------------- F: Glow Night
def f_hook():
    f = still(4.5)
    T.string_lights(f, 30, 80, n=16)
    paste_center(f, T.glow_text("New day, new product", T.allura(110), CREAM, glow=(255, 150, 200), ga=110), W / 2, 270)
    paste_center(f, T.glow_text("JAALI LANTERN", T.yeseva(110), (T.GOLD_L, T.GOLD)), W / 2, 410)
    return f


def f_end():
    f = still(40.0)
    a = np.asarray(f.convert("RGB")).astype(np.float32)
    g = np.linspace(0, 1, H)[:, None, None]
    tint = np.array([60, 20, 90], np.float32) * (1 - g) + np.array([120, 20, 80], np.float32) * g
    f = Image.fromarray(np.clip(a * 0.85 + tint * 0.35, 0, 255).astype(np.uint8)).convert("RGBA")
    for x, y, h in ((140, 700, 90), (920, 560, 70), (240, 1250, 60), (860, 1150, 100), (520, 260, 50)):
        paste_center(f, T.sky_lantern(h), x, y)
    T.line_burst(f, 220, 420, 90, PINK)
    T.line_burst(f, 860, 360, 80, T.GOLD)
    T.line_burst(f, 900, 1500, 70, (120, 220, 255))
    paste_center(f, T.glow_text("Roshni wali Diwali", T.allura(120), CREAM, glow=(255, 150, 200), ga=110), W / 2, 1600)
    paste_center(f, T.glow_text("ORDER NOW · DM", T.yeseva(90), (T.GOLD_L, T.GOLD)), W / 2, 1740)
    return f


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    opts = [("A_warm_minimal", a_hook, a_end), ("B_diya_glow", b_hook, b_end), ("C_terracotta", c_hook, c_end),
            ("D_festive_frame", d_hook, d_end), ("E_star_pattern_pop", e_hook, e_end), ("F_glow_night", f_hook, f_end)]
    if len(sys.argv) > 3:
        opts = [o for o in opts if o[0][0] in sys.argv[3]]
    thumbs = []
    for name, hook, end in opts:
        for part, fn in (("hook", hook), ("end", end)):
            im = fn().convert("RGB")
            im.save(f"{OUTDIR}/option_{name}_{part}.png")
            thumbs.append(im.resize((W // 3, H // 3), Image.LANCZOS))
    sheet = Image.new("RGB", (W // 3 * len(thumbs) + 10 * (len(thumbs) + 1), H // 3 + 20), (255, 255, 255))
    for k, t in enumerate(thumbs):
        sheet.paste(t, (10 + k * (W // 3 + 10), 10))
    sheet.save(f"{OUTDIR}/options_sheet.png")
    print("wrote", OUTDIR)
