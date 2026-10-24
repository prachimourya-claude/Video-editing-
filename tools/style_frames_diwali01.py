"""Pastel style frames for Diwali 01 (Psone Labs Kalash stencil): powder blue + butter yellow, soft and airy.

usage: cd tools && python3 style_frames_diwali01.py <workdir> <outdir>
Same <workdir> as render_diwali01.py, plus fonts cormorant_i.ttf cormorant_b.ttf poppins_m.ttf tiro.ttf caveat.ttf.
"""
import math, os, subprocess, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import render_diwali01 as R
from render_diwali01 import W, H, paste_center, text_mask

BASE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
F = BASE + "/fonts/"
corm_i = lambda s: ImageFont.truetype(F + "cormorant_i.ttf", s)
corm_b = lambda s: ImageFont.truetype(F + "cormorant_b.ttf", s)
pop_m = lambda s: ImageFont.truetype(F + "poppins_m.ttf", s)
tiro = lambda s: ImageFont.truetype(F + "tiro.ttf", s)
caveat = lambda s: ImageFont.truetype(F + "caveat.ttf", s)

SKY = (214, 232, 248)      # powder blue
BLUE = (168, 203, 236)     # baby blue
BLUE_D = (120, 164, 214)
BUTTER = (252, 232, 160)   # butter yellow
LEMON = (255, 243, 196)
CREAM = (255, 250, 238)
HONEY = (232, 184, 90)     # soft gold, used sparingly
NAVY = (46, 62, 99)        # text ink


def pastel_bg(seed=1, top=SKY, bottom=LEMON):
    g = np.linspace(0, 1, H)[:, None]
    col = np.stack([np.interp(g[:, 0], [0, 0.55, 1], [top[c], CREAM[c], bottom[c]]) for c in range(3)], 1)
    a = np.broadcast_to(col[:, None, :], (H, W, 3)).copy()
    rng = np.random.default_rng(seed)
    tex = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.0)
    a += (tex * 3)[..., None]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")
    for k in range(18):  # soft bokeh
        r = int(rng.uniform(30, 90))
        c = (255, 255, 255) if k % 3 else BUTTER
        paste_center(im, R.blob(r, c, int(rng.uniform(60, 130))), rng.uniform(0, W), rng.uniform(0, H))
    return im


def text(t, font, fill=NAVY, track=0):
    if not track:
        m = text_mask(t, font)
    else:
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        wds = [d.textlength(ch, font=font) for ch in t]
        m = Image.new("L", (int(sum(wds) + track * len(t)) + 24, int(font.size * 1.5)), 0)
        x = 12
        for ch, w in zip(t, wds):
            ImageDraw.Draw(m).text((x, m.height / 2), ch, font=font, fill=255, anchor="lm")
            x += w + track
    im = Image.new("RGBA", m.size, fill + (0,))
    im.putalpha(m)
    return im


def swash(w, h, col=BUTTER, seed=2):
    """Hand-painted highlighter stroke behind a word."""
    rng = np.random.default_rng(seed)
    m = Image.new("L", (w + 40, h + 40), 0)
    d = ImageDraw.Draw(m)
    pts = [(20 + w * k / 30, 20 + h / 2 + 6 * math.sin(k / 4) + rng.uniform(-3, 3)) for k in range(31)]
    d.line(pts, fill=255, width=h, joint="curve")
    m = m.filter(ImageFilter.GaussianBlur(2))
    im = Image.new("RGBA", m.size, col + (0,))
    im.putalpha(m.point(lambda v: v * 230 // 255))
    return im


def card(w, h, fill=CREAM, alpha=235, r=40):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=fill + (alpha,))
    return R.with_shadow(im, offset=(0, 10), blur=20, alpha=50, color=(90, 120, 170))


def chip(t, font, bg, fg=NAVY, pad=(34, 16)):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.textbbox((0, 0), t, font=font)
    w, h = bb[2] - bb[0] + 2 * pad[0], bb[3] - bb[1] + 2 * pad[1]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg + (255,))
    ImageDraw.Draw(im).text((w / 2, h / 2), t, font=font, fill=fg, anchor="mm")
    return R.with_shadow(im, offset=(0, 6), blur=12, alpha=45, color=(90, 120, 170))


def lantern(h, body=BUTTER, band=BLUE):
    """Pastel akash kandil on a thin string, with a tassel."""
    w = int(h * 0.62)
    im = Image.new("RGBA", (w + 20, h + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = im.width / 2
    top, bot = 20, 20 + h
    d.rectangle((cx - w * 0.18, top, cx + w * 0.18, top + h * 0.08), fill=HONEY + (255,))
    d.polygon([(cx, top + h * 0.08), (cx + w / 2, top + h * 0.45), (cx, bot - h * 0.1), (cx - w / 2, top + h * 0.45)], fill=body + (255,))
    d.polygon([(cx, top + h * 0.2), (cx + w * 0.3, top + h * 0.45), (cx, bot - h * 0.22), (cx - w * 0.3, top + h * 0.45)], fill=band + (255,))
    d.polygon([(cx, top + h * 0.3), (cx + w * 0.14, top + h * 0.45), (cx, bot - h * 0.32), (cx - w * 0.14, top + h * 0.45)], fill=CREAM + (255,))
    d.rectangle((cx - w * 0.14, bot - h * 0.1, cx + w * 0.14, bot - h * 0.04), fill=HONEY + (255,))
    for k in range(7):
        x = cx - w * 0.12 + w * 0.24 * k / 6
        d.line((x, bot - h * 0.04, x + (k - 3) * 2, bot + 90), fill=(band if k % 2 else body) + (255,), width=4)
    glow = R.blob(int(h * 0.35), (255, 236, 170), 120)
    out = Image.new("RGBA", (max(im.width, glow.width), max(im.height, glow.height)), (0, 0, 0, 0))
    paste_center(out, glow, out.width / 2, out.height / 2 - 40)
    paste_center(out, im, out.width / 2, out.height / 2)
    return R.with_shadow(out, offset=(0, 8), blur=14, alpha=40, color=(90, 120, 170))


def hang(base, x, y_end, h, body, band):
    d = ImageDraw.Draw(base)
    d.line((x, 0, x, y_end), fill=NAVY + (110,), width=2)
    lt = lantern(h, body, band)
    paste_center(base, lt, x, y_end + lt.height / 2 - 60)


def diya(base, x, y, w):
    """Pastel diya: pale yellow bowl, blue dots, honey flame with a soft glow."""
    h = int(w * 0.42)
    paste_center(base, R.blob(int(w * 0.6), (255, 220, 140), 170), x, y - w * 0.25)
    im = Image.new("RGBA", (w + 20, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.chord((10, 10 - h, 10 + w, 10 + h), 0, 180, fill=BUTTER + (255,))
    d.ellipse((10, 10 - h * 0.16, 10 + w, 10 + h * 0.16), fill=(240, 205, 120, 255))
    for k in range(7):
        fx = 0.18 + 0.64 * k / 6
        r = w * 0.03
        yy = 10 + h * 0.42
        d.ellipse((10 + w * fx - r, yy - r, 10 + w * fx + r, yy + r), fill=BLUE_D + (255,))
    paste_center(base, R.with_shadow(im, offset=(0, 6), blur=8, alpha=50, color=(90, 120, 170)), x, y + w * 0.12)
    fl = R.flame_sprite(int(w * 0.5))
    paste_center(base, fl, x + w * 0.08, y - w * 0.04 - fl.height / 2 + 6)


def petals(base, n, seed, avoid=None):
    rng = np.random.default_rng(seed)
    for k in range(n):
        x, y = rng.uniform(40, W - 40), rng.uniform(H * 0.75, H - 60)
        r = int(rng.uniform(7, 12))
        p = Image.new("RGBA", (r * 3, r * 3), (0, 0, 0, 0))
        ImageDraw.Draw(p).ellipse((r * 0.5, r, r * 2.5, r * 2), fill=(BUTTER if k % 2 else BLUE) + (255,))
        paste_center(base, p.rotate(rng.uniform(0, 180), expand=True), x, y)


def dot_rangoli(R0=380, col=(255, 255, 255)):
    """Fine line-art mandala in white, very light."""
    S = R0 * 2 + 20
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    for rf, n in ((0.3, 8), (0.55, 12), (0.8, 16)):
        r = R0 * rf
        d.ellipse((c - r, c - r, c + r, c + r), outline=col + (150,), width=2)
        for k in range(n):
            a = 2 * math.pi * k / n
            x, y = c + r * math.cos(a), c + r * math.sin(a)
            pr = R0 * 0.09 * rf / 0.55
            d.ellipse((x - pr, y - pr, x + pr, y + pr), outline=col + (140,), width=2)
            x2, y2 = c + (r + pr * 1.6) * math.cos(a), c + (r + pr * 1.6) * math.sin(a)
            d.ellipse((x2 - 4, y2 - 4, x2 + 4, y2 + 4), fill=col + (170,))
    return im


def arch(w, h, col=BLUE, alpha=150):
    """Temple-window arch behind the stencil so the white stencil stands off the light background."""
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.pieslice((20, 20, 20 + w, 20 + w), 180, 360, fill=col + (alpha,))
    d.rectangle((20, 20 + w / 2, 20 + w, 20 + h), fill=col + (alpha,))
    d.arc((34, 34, 6 + w, 6 + w), 180, 360, fill=(255, 255, 255, 220), width=3)
    d.line((34, 20 + w / 2, 34, 6 + h), fill=(255, 255, 255, 220), width=3)
    d.line((6 + w, 20 + w / 2, 6 + w, 6 + h), fill=(255, 255, 255, 220), width=3)
    return im


def step(n, label, col):
    im = Image.new("RGBA", (300, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((110, 4, 190, 84), fill=col + (255,), outline=(255, 255, 255, 255), width=4)
    d.text((150, 44), str(n), font=corm_b(54), fill=NAVY, anchor="mm")
    d.text((150, 125), label, font=pop_m(34), fill=NAVY, anchor="mm")
    return im


def stencil_soft(S, height):
    st = R.stencil_img(S, height / S.height)
    return R.with_shadow(st, offset=(0, 22), blur=28, alpha=90, color=(80, 115, 170))


def frame_hook(S):
    f = pastel_bg(1)
    paste_center(f, dot_rangoli(420), W / 2, 1150)
    hang(f, 150, 210, 170, BUTTER, BLUE)
    hang(f, 930, 300, 150, BLUE, BUTTER)
    hang(f, 300, 90, 110, BLUE, LEMON)
    paste_center(f, text("DIWALI SPECIAL", pop_m(30), NAVY, track=8), W / 2, 420)
    paste_center(f, text("Is Diwali, rangoli ho", corm_i(84)), W / 2, 520)
    big = text("kuch unique", corm_i(150))
    paste_center(f, swash(big.width - 40, 60), W / 2, 680)
    paste_center(f, big, W / 2, 640)
    paste_center(f, arch(700, 900), W / 2, 1220)
    paste_center(f, stencil_soft(S, 760), W / 2, 1190)
    for k, x in enumerate((300, 540, 780)):
        diya(f, x, 1690, 120)
    petals(f, 26, 3)
    return f


def frame_product(S):
    src = f"{BASE}/style_B.png"
    if not os.path.exists(src):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.5", "-i", f"{BASE}/src/B.mp4", "-frames:v", "1", src], check=True)
    ph = Image.open(src).convert("RGB")
    sc = max(W / ph.width, H / ph.height)
    ph = ph.resize((int(ph.width * sc), int(ph.height * sc)), Image.LANCZOS)
    ph = ph.crop(((ph.width - W) // 2, (ph.height - H) // 2, (ph.width - W) // 2 + W, (ph.height - H) // 2 + H))
    # airy pastel grade: lift shadows, cool highlights a touch, wash with cream
    a = np.asarray(ph).astype(np.float32)
    a = 40 + a * 0.84
    a = a * np.array([0.98, 1.0, 1.04]) * 0.86 + np.array(CREAM) * 0.14
    f = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")
    c = card(820, 250)
    paste_center(f, c, W / 2, 400)
    paste_center(f, text("ye hai hamara", caveat(56), BLUE_D), W / 2, 335)
    paste_center(f, text("Kalash Rangoli Stencil", corm_b(86)), W / 2, 420)
    d = ImageDraw.Draw(f)
    d.line([(760, 690), (690, 650), (600, 640)], fill=CREAM + (255,), width=5, joint="curve")
    d.ellipse((588, 628, 612, 652), fill=BUTTER + (255,), outline=CREAM + (255,), width=4)
    paste_center(f, chip("Upar: Shubh Kalash", pop_m(42), BUTTER), 800, 720)
    d.line([(790, 1460), (700, 1300), (620, 1200)], fill=CREAM + (255,), width=5, joint="curve")
    d.ellipse((608, 1188, 632, 1212), fill=BLUE + (255,), outline=CREAM + (255,), width=4)
    paste_center(f, chip("Neeche: Kamal", pop_m(42), BLUE), 800, 1490)
    paste_center(f, chip("Designed & 3D printed by Psone Labs", pop_m(32), CREAM), W / 2, 1700)
    return f


def frame_steps(S):
    f = pastel_bg(4, top=LEMON, bottom=SKY)
    paste_center(f, text("Bas 3 steps", corm_i(110)), W / 2, 380)
    paste_center(f, arch(740, 1000, BLUE, 120), W / 2, 1080)
    paste_center(f, stencil_soft(S, 820), W / 2, 1060)
    cols = [(244, 196, 214), BUTTER, (196, 230, 200), BLUE, (255, 214, 170), (214, 200, 240)]
    for k, ((x, y), c) in enumerate(zip([(105, 820), (975, 820), (105, 1060), (975, 1060), (105, 1300), (975, 1300)], cols)):
        b = R.bowl_sprite(58, c, k)
        paste_center(f, b, x, y)
    for k, (t, c) in enumerate((("Stencil rakho", CREAM), ("Rangoli bharo", BUTTER), ("Rangoli ready", BLUE))):
        paste_center(f, step(k + 1, t, c), 200 + k * 340, 1680)
    return f


def frame_end(S):
    f = pastel_bg(7)
    paste_center(f, dot_rangoli(440), W / 2, 820)
    hang(f, 140, 160, 150, BLUE, BUTTER)
    hang(f, 940, 220, 170, BUTTER, BLUE)
    paste_center(f, arch(460, 600, BLUE, 130), W / 2, 830)
    paste_center(f, stencil_soft(S, 470), W / 2, 820)
    paste_center(f, text("Psone Labs", corm_b(150)), W / 2, 1200)
    paste_center(f, text("KALASH RANGOLI STENCIL", pop_m(32), BLUE_D, track=6), W / 2, 1310)
    paste_center(f, chip("DM to order", pop_m(46), BUTTER, pad=(54, 22)), W / 2, 1440)
    paste_center(f, text("शुभ दीपावली", tiro(96), NAVY), W / 2, 1620)
    for x in (230, 850):
        diya(f, x, 1640, 110)
    return f


if __name__ == "__main__":
    S = R.build_stencil()
    frames = [("style_1_hook", frame_hook), ("style_2_product", frame_product), ("style_3_steps", frame_steps), ("style_4_end", frame_end)]
    thumbs = []
    for name, fn in frames:
        im = fn(S).convert("RGB")
        im.save(f"{OUTDIR}/{name}.png")
        thumbs.append(im.resize((W // 2, H // 2), Image.LANCZOS))
    sheet = Image.new("RGB", (W // 2 * 4 + 50, H // 2 + 20), (255, 255, 255))
    for k, t in enumerate(thumbs):
        sheet.paste(t, (10 + k * (W // 2 + 10), 10))
    sheet.save(f"{OUTDIR}/style_sheet.png")
    print("wrote", OUTDIR)
