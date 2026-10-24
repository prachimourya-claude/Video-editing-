"""Style frames for the Diwali 01 teaser, matched to the client's references: night-blue sky fading to
purple and pink, glowing gold lettering, sky lanterns, kandils, a gold Mughal arch, line fireworks, diyas.

usage: cd tools && python3 style_frames_teaser01.py <workdir> <outdir>
Same <workdir> as render_diwali01.py, plus fonts yeseva.ttf montserrat_sb.ttf allura.ttf tiro.ttf.
"""
import math, os, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import render_diwali01 as R
from render_diwali01 import W, H, paste_center, text_mask, blob

BASE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
F = BASE + "/fonts/"
yeseva = lambda s: ImageFont.truetype(F + "yeseva.ttf", s)
mont = lambda s: ImageFont.truetype(F + "montserrat_sb.ttf", s)
allura = lambda s: ImageFont.truetype(F + "allura.ttf", s)
tiro = lambda s: ImageFont.truetype(F + "tiro.ttf", s)

NAVY = (14, 24, 52)
TEAL = (32, 86, 128)
PURPLE = (104, 84, 168)
PINK = (232, 128, 166)
MAGENTA = (150, 24, 96)
GOLD = (255, 196, 80)
GOLD_L = (255, 228, 150)
AMBER = (255, 150, 50)
CREAM = (255, 242, 220)
COPPER = (196, 110, 70)


def grad_bg(stops, pos, seed=1):
    g = np.linspace(0, 1, H)
    col = np.stack([np.interp(g, pos, [s[c] for s in stops]) for c in range(3)], 1)
    a = np.broadcast_to(col[:, None, :], (H, W, 3)).copy()
    rng = np.random.default_rng(seed)
    a += cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.0)[..., None] * 2.5
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")


def stars(base, n, seed, ymax=H, alpha=1.0):
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(base)
    for k in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, ymax)
        r = rng.choice([1.5, 2, 2.5, 3.5], p=[0.4, 0.3, 0.2, 0.1])
        a = int(rng.uniform(120, 255) * alpha)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 236, 190, a))
        if r > 3:
            paste_center(base, blob(8, (255, 220, 150), 120), x, y)


def bokeh(base, n, seed, cols, ymin=0, ymax=H):
    rng = np.random.default_rng(seed)
    for k in range(n):
        r = int(rng.uniform(14, 40))
        im = Image.new("RGBA", (r * 2 + 4, r * 2 + 4), (0, 0, 0, 0))
        c = cols[k % len(cols)]
        ImageDraw.Draw(im).ellipse((2, 2, 2 + 2 * r, 2 + 2 * r), fill=c + (int(rng.uniform(50, 110)),), outline=c + (140,), width=2)
        paste_center(base, im.filter(ImageFilter.GaussianBlur(1.5)), rng.uniform(0, W), rng.uniform(ymin, ymax))


def sky_lantern(h, blur=0):
    """Paper sky lantern: warm trapezoid, brightest at the open bottom, with a halo."""
    w = int(h * 0.75)
    im = Image.new("RGBA", (w * 3, h * 3), (0, 0, 0, 0))
    paste_center(im, blob(int(h * 0.7), AMBER, 150), im.width / 2, im.height / 2)
    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(w * 0.06, 0), (w * 0.94, 0), (w * 0.8, h), (w * 0.2, h)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1))
    g = np.linspace(0, 1, h)[:, None]
    col = np.stack([np.interp(g[:, 0], [0, 0.6, 1], [c1, c2, c3]) for c1, c2, c3 in zip((235, 100, 30), (255, 170, 60), (255, 236, 160))], 1)
    body = Image.fromarray(np.broadcast_to(col[:, None, :], (h, w, 3)).astype(np.uint8)).convert("RGBA")
    body.putalpha(m)
    paste_center(im, body, im.width / 2, im.height / 2)
    paste_center(im, blob(int(h * 0.18), (255, 250, 220), 230), im.width / 2, im.height / 2 + h * 0.45)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return im


def lanterns_sky(base, seed, n=9, ymin=200, ymax=1500, avoid=None):
    rng = np.random.default_rng(seed)
    for k in range(n):
        h = int(rng.choice([36, 48, 60, 80, 110]))
        x, y = rng.uniform(60, W - 60), rng.uniform(ymin, ymax)
        if avoid and avoid[0] < x < avoid[2] and avoid[1] < y < avoid[3]:
            x = rng.choice([rng.uniform(40, avoid[0]), rng.uniform(avoid[2], W - 40)])
        paste_center(base, sky_lantern(h, blur=0 if h < 100 else 2), x, y)


def kandil(h):
    """Hanging hexagonal kandil (akash kandil) with lattice windows and a tassel."""
    w = int(h * 0.62)
    im = Image.new("RGBA", (w + 20, int(h * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = im.width / 2
    t, mid, b = 10, 10 + h * 0.5, 10 + h
    d.polygon([(cx - w * 0.22, t), (cx + w * 0.22, t), (cx + w / 2, mid), (cx + w * 0.22, b), (cx - w * 0.22, b), (cx - w / 2, mid)], fill=COPPER + (255,))
    d.polygon([(cx - w * 0.18, t + h * 0.12), (cx + w * 0.18, t + h * 0.12), (cx + w * 0.34, mid), (cx + w * 0.18, b - h * 0.12), (cx - w * 0.18, b - h * 0.12), (cx - w * 0.34, mid)], fill=(255, 214, 140, 255))
    for k in range(-4, 5):  # lattice
        o = k * w * 0.08
        d.line((cx - w * 0.3 + o, mid - h * 0.3, cx + w * 0.3 + o, mid + h * 0.3), fill=COPPER + (255,), width=3)
        d.line((cx + w * 0.3 + o, mid - h * 0.3, cx - w * 0.3 + o, mid + h * 0.3), fill=COPPER + (255,), width=3)
    d.line((cx - w / 2, mid, cx + w / 2, mid), fill=(150, 70, 50, 255), width=5)
    for k in range(9):
        x = cx - w * 0.2 + w * 0.4 * k / 8
        d.line((x, b, x + (k - 4) * 1.5, b + h * 0.55), fill=(170, 60, 70, 255), width=5)
    out = Image.new("RGBA", (im.width * 2, im.height * 2), (0, 0, 0, 0))
    paste_center(out, blob(int(h * 0.45), AMBER, 110), out.width / 2, out.height / 2 - h * 0.25)
    paste_center(out, im, out.width / 2, out.height / 2)
    return out


def hang_kandil(base, x, y, h):
    ImageDraw.Draw(base).line((x, 0, x, y - h * 0.3), fill=(220, 180, 120, 200), width=3)
    k = kandil(h)
    paste_center(base, k, x, y + k.height / 2 - h * 0.65)


def string_lights(base, y0, sag, n=16):
    d = ImageDraw.Draw(base)
    pts = [(W * k / 60, y0 + sag * math.sin(math.pi * k / 60)) for k in range(61)]
    d.line(pts, fill=(80, 60, 50, 255), width=3)
    for k in range(n):
        u = (k + 0.5) / n
        x, y = W * u, y0 + sag * math.sin(math.pi * u) + 14
        paste_center(base, blob(18, (255, 220, 140), 160), x, y)
        d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=(255, 236, 180, 255))


def bez(p0, p1, p2, p3, n=30):
    return [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d
                  for a, b, c, d in zip(p0, p1, p2, p3)) for t in np.linspace(0, 1, n)]


def arch_mask(w, h):
    """Mughal onion-dome arch (straight sides, swelling dome, pointed finial) as an L mask w x h."""
    ys = 0.62 * w
    left = bez((0, ys), (0, ys - 0.3 * w), (0.12 * w, ys - 0.42 * w), (0.32 * w, ys - 0.45 * w)) + \
        bez((0.32 * w, ys - 0.45 * w), (0.44 * w, ys - 0.47 * w), (0.49 * w, ys - 0.53 * w), (0.5 * w, 0))
    right = [(w - x, y) for x, y in reversed(left)]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(0, h)] + left + right + [(w, h)], fill=255)
    return m


def gold_arch(w, h, fill_stops=None, line=8):
    """Arch window: optional gradient inside, gold outline with a warm glow."""
    p = 60
    m = arch_mask(w, h)
    out = Image.new("RGBA", (w + 2 * p, h + 2 * p), (0, 0, 0, 0))
    if fill_stops:
        g = np.linspace(0, 1, h)
        col = np.stack([np.interp(g, [0, 0.5, 1], [s[c] for s in fill_stops]) for c in range(3)], 1)
        f = Image.fromarray(np.broadcast_to(col[:, None, :], (h, w, 3)).astype(np.uint8)).convert("RGBA")
        f.putalpha(m)
        out.alpha_composite(f, (p, p))
    edge = np.asarray(m).astype(np.uint8)
    ring = edge - cv2.erode(edge, np.ones((line, line), np.uint8), borderType=cv2.BORDER_CONSTANT, borderValue=0)
    ring[-line:] = 0
    rm = Image.new("L", out.size, 0)
    rm.paste(Image.fromarray(ring), (p, p))
    glow = Image.new("RGBA", out.size, AMBER + (0,))
    glow.putalpha(rm.filter(ImageFilter.GaussianBlur(14)).point(lambda v: min(255, v * 2)))
    out.alpha_composite(glow)
    gl = Image.new("RGBA", out.size, GOLD + (0,))
    gl.putalpha(rm)
    out.alpha_composite(gl)
    return out


def line_burst(base, x, y, r, col, n=18):
    lay = Image.new("RGBA", (int(r * 2.4), int(r * 2.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = lay.width / 2
    for k in range(n):
        a = 2 * math.pi * k / n + 0.1
        r0, r1 = r * (0.3 if k % 2 else 0.45), r * (1.0 if k % 2 else 0.8)
        d.line((c + r0 * math.cos(a), c + r0 * math.sin(a), c + r1 * math.cos(a), c + r1 * math.sin(a)), fill=col + (255,), width=4)
        d.ellipse((c + r1 * 1.08 * math.cos(a) - 3, c + r1 * 1.08 * math.sin(a) - 3, c + r1 * 1.08 * math.cos(a) + 3, c + r1 * 1.08 * math.sin(a) + 3), fill=col + (220,))
    glow = lay.filter(ImageFilter.GaussianBlur(6))
    paste_center(base, glow, x, y)
    paste_center(base, lay, x, y)


def glow_text(t, font, fill=GOLD, glow=AMBER, ga=170, track=0):
    if track:
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        wds = [d.textlength(ch, font=font) for ch in t]
        m = Image.new("L", (int(sum(wds) + track * len(t)) + 24, int(font.size * 1.5)), 0)
        x = 12
        for ch, w in zip(t, wds):
            ImageDraw.Draw(m).text((x, m.height / 2), ch, font=font, fill=255, anchor="lm")
            x += w + track
    else:
        m = text_mask(t, font)
    p = 50
    out = Image.new("RGBA", (m.width + 2 * p, m.height + 2 * p), (0, 0, 0, 0))
    gm = Image.new("L", out.size, 0)
    gm.paste(m, (p, p))
    if ga:
        g = Image.new("RGBA", out.size, glow + (0,))
        g.putalpha(gm.filter(ImageFilter.GaussianBlur(16)).point(lambda v: v * ga // 255))
        out.alpha_composite(g)
    if isinstance(fill[0], tuple):  # vertical gradient
        h = out.height
        col = np.stack([np.interp(np.linspace(0, 1, h), [0.3, 0.7], [fill[0][c], fill[1][c]]) for c in range(3)], 1)
        tf = Image.fromarray(np.broadcast_to(col[:, None, :], (h, out.width, 3)).astype(np.uint8)).convert("RGBA")
    else:
        tf = Image.new("RGBA", out.size, fill + (255,))
    tf.putalpha(gm)
    out.alpha_composite(tf)
    return out


def diya_glow(base, x, y, w):
    """Deep-plum diya with gold bands and a big warm flame glow (ref 3)."""
    h = int(w * 0.45)
    paste_center(base, blob(int(w * 0.75), AMBER, 200), x, y - w * 0.2)
    im = Image.new("RGBA", (w + 20, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.chord((10, 10 - h, 10 + w, 10 + h), 0, 180, fill=(88, 24, 70, 255))
    d.arc((10 + w * 0.04, 10 - h * 0.7, 10 + w * 0.96, 10 + h * 0.7), 20, 160, fill=GOLD + (255,), width=4)
    d.arc((10 + w * 0.12, 10 - h * 0.45, 10 + w * 0.88, 10 + h * 0.45), 25, 155, fill=(230, 150, 70, 255), width=3)
    d.ellipse((10, 10 - h * 0.18, 10 + w, 10 + h * 0.18), fill=(255, 170, 70, 255))
    d.ellipse((10 + w * 0.06, 10 - h * 0.12, 10 + w * 0.94, 10 + h * 0.12), fill=(255, 214, 130, 255))
    paste_center(base, im, x, y + h * 0.3)
    fl = R.flame_sprite(int(w * 0.6))
    paste_center(base, fl, x, y - fl.height / 2 + 8)


def silhouette(S, height):
    st = R.stencil_img(S, height / S.height)
    a = np.asarray(st.getchannel("A")).astype(np.float32) / 255
    rim = cv2.GaussianBlur(np.clip(a - cv2.erode(a, np.ones((9, 9), np.uint8)), 0, 1), (0, 0), 2.5) * 1.8
    sil = np.zeros(a.shape + (4,), np.float32)
    base_c = np.array((40, 22, 60), np.float32)
    sil[..., :3] = base_c + np.clip(rim, 0, 1)[..., None] * (np.array(GOLD_L, np.float32) - base_c)
    sil[..., 3] = a * 255
    out = Image.new("RGBA", (st.width + 200, st.height + 200), (0, 0, 0, 0))
    gm = Image.new("L", out.size, 0)
    gm.paste(st.getchannel("A"), (100, 100))
    g = Image.new("RGBA", out.size, AMBER + (0,))
    g.putalpha(gm.filter(ImageFilter.GaussianBlur(40)).point(lambda v: v * 200 // 255))
    out.alpha_composite(g)
    out.alpha_composite(Image.fromarray(sil.clip(0, 255).astype(np.uint8), "RGBA"), (100, 100))
    return out


SKY = [(10, 22, 50), (22, 62, 102), (36, 92, 134)]
DUSK = [(12, 16, 44), (58, 52, 120), (120, 80, 150), (214, 112, 156)]


def frame_1():
    """Opener: night-blue sky full of sky lanterns (ref 1)."""
    f = grad_bg(SKY, [0, 0.5, 1], 1)
    stars(f, 140, 2)
    lanterns_sky(f, 3, 11, avoid=(150, 560, 930, 1180))
    paste_center(f, sky_lantern(240, blur=6), 120, 160)
    paste_center(f, glow_text("IS DIWALI", mont(40), CREAM, ga=0, track=18), W / 2, 700)
    paste_center(f, glow_text("kuch naya", yeseva(170), (GOLD_L, GOLD)), W / 2, 840)
    paste_center(f, glow_text("aa raha hai...", allura(130), CREAM, glow=(255, 220, 160), ga=90), W / 2, 1010)
    # rooftop silhouettes with tiny diya rows
    d = ImageDraw.Draw(f)
    for x0, x1, top in ((0, 360, 1640), (380, 600, 1720), (640, 860, 1690), (880, 1080, 1610)):
        d.rectangle((x0, top, x1, H), fill=(18, 22, 52, 255))
        for x in range(x0 + 20, x1 - 10, 40):
            paste_center(f, blob(9, AMBER, 220), x, top - 4)
            d.ellipse((x - 5, top - 9, x + 5, top + 1), fill=(255, 210, 120, 255))
    return f


def frame_2():
    """Glimpse: a dark close-up of the printing seen through the gold arch, with kandils (ref 2)."""
    f = grad_bg([(8, 10, 34), (20, 22, 60)], [0, 1], 4)
    stars(f, 60, 5, alpha=0.6)
    aw, ah = 860, 1180
    ph = Image.open(f"{BASE}/teaser_B.png").convert("RGB")
    sc = max(aw / ph.width, ah / ph.height) * 1.6
    ph = ph.resize((int(ph.width * sc), int(ph.height * sc)), Image.LANCZOS)
    cx, cy = ph.width * 0.5, ph.height * 0.55
    ph = ph.crop((int(cx - aw / 2), int(cy - ah / 2), int(cx + aw / 2), int(cy + ah / 2)))
    a = np.asarray(ph).astype(np.float32) * 0.42
    a = a * np.array([0.85, 0.85, 1.05]) + np.array([18, 6, 34])  # cool purple night grade
    ph = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")
    ph.putalpha(arch_mask(aw, ah))
    f.alpha_composite(ph, ((W - aw) // 2, 330))
    arch = gold_arch(aw, ah)
    f.alpha_composite(arch, ((W - arch.width) // 2, 330 - 60))
    for x, y, h in ((90, 150, 200), (990, 210, 220)):
        hang_kandil(f, x, y, h)
    paste_center(f, glow_text("KUCH KHAAS", mont(46), CREAM, ga=0, track=16), W / 2, 1620)
    paste_center(f, glow_text("ban raha hai...", allura(140), (GOLD_L, GOLD)), W / 2, 1740)
    return f


def frame_3(S):
    """Guess: stencil silhouette in a purple-to-pink arch window, line fireworks, kandils (ref 2 + 3)."""
    f = grad_bg([(10, 12, 40), (18, 18, 56)], [0, 1], 6)
    stars(f, 50, 7, alpha=0.6)
    string_lights(f, 40, 90)
    for x, y, h in ((100, 330, 190), (980, 330, 190)):
        hang_kandil(f, x, y, h)
    aw, ah = 880, 1300
    arch = gold_arch(aw, ah, [(40, 40, 110), (110, 80, 160), (220, 118, 160)])
    ay = 560
    f.alpha_composite(arch, ((W - arch.width) // 2, ay - 60))
    inside = Image.new("RGBA", f.size, (0, 0, 0, 0))
    stars(inside, 40, 8, ymax=H, alpha=0.8)
    bokeh(inside, 18, 9, [PINK, (255, 180, 200), GOLD], 900, 1600)
    m = Image.new("L", f.size, 0)
    m.paste(arch_mask(aw, ah), ((W - aw) // 2, ay))
    inside.putalpha(Image.fromarray(np.minimum(np.asarray(inside.getchannel("A")), np.asarray(m))))
    f.alpha_composite(inside)
    line_burst(f, 790, 960, 80, GOLD)
    line_burst(f, 280, 1060, 60, PINK)
    paste_center(f, silhouette(S, 720), W / 2, 1360)
    paste_center(f, glow_text("Guess karo...", allura(120), CREAM, glow=(255, 210, 170), ga=80), W / 2, 300)
    paste_center(f, glow_text("kya hai?", yeseva(150), (GOLD_L, GOLD)), W / 2, 440)
    return f


def frame_4():
    """Coming soon: dusk gradient, gold arch card, lotus, diyas, sky lanterns (ref 1 + 3)."""
    f = grad_bg(DUSK, [0, 0.35, 0.65, 1], 10)
    stars(f, 90, 11, ymax=1100)
    bokeh(f, 26, 12, [PINK, (255, 170, 200), (200, 140, 230)], 900, 1900)
    lanterns_sky(f, 13, 8, ymin=150, ymax=1300, avoid=(120, 250, 960, 1350))
    aw, ah = 820, 1100
    arch = gold_arch(aw, ah, [(70, 20, 80), (120, 26, 96), (150, 40, 110)])
    f.alpha_composite(arch, ((W - arch.width) // 2, 230 - 60))
    paste_center(f, glow_text("LAUNCHING THIS DIWALI", mont(34), CREAM, ga=0, track=10), W / 2, 640)
    paste_center(f, glow_text("Coming", yeseva(170), (GOLD_L, GOLD)), W / 2, 790)
    paste_center(f, glow_text("Soon", yeseva(170), (GOLD_L, GOLD)), W / 2, 970)
    # small lotus mark (ref 3)
    lot = Image.new("RGBA", (300, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(lot)
    bx, by = 150, 160
    for ang, ln in ((-68, 95), (68, 95), (-36, 125), (36, 125), (0, 150)):
        th = math.radians(ang)
        side = [(30 * math.sin(math.pi * u) ** 0.9 * (1 - 0.3 * u), ln * u) for u in np.linspace(0, 1, 30)]
        pts = side + [(-x, y) for x, y in reversed(side)]
        pts = [(bx + x * math.cos(th) + y * math.sin(th), by + x * math.sin(th) - y * math.cos(th)) for x, y in pts]
        d.polygon(pts, fill=GOLD + (255,), outline=AMBER + (255,), width=3)
    paste_center(f, lot, W / 2, 1090, scale=0.6)
    paste_center(f, glow_text("DHANTERAS SE PEHLE", mont(36), CREAM, ga=0, track=10), W / 2, 1240)
    for x, y, w in ((300, 1560, 220), (780, 1560, 220), (540, 1680, 240)):
        diya_glow(f, x, y, w)
    paste_center(f, glow_text("शुभ दीपावली", tiro(80), GOLD_L, ga=120), W / 2, 1830)
    return f


if __name__ == "__main__":
    S = R.build_stencil()
    frames = [("teaser_1_opener", frame_1), ("teaser_2_glimpse", frame_2),
              ("teaser_3_guess", lambda: frame_3(S)), ("teaser_4_coming_soon", frame_4)]
    thumbs = []
    for name, fn in frames:
        im = fn().convert("RGB")
        im.save(f"{OUTDIR}/{name}.png")
        thumbs.append(im.resize((W // 2, H // 2), Image.LANCZOS))
    sheet = Image.new("RGB", (W // 2 * 4 + 50, H // 2 + 20), (255, 255, 255))
    for k, t in enumerate(thumbs):
        sheet.paste(t, (10 + k * (W // 2 + 10), 10))
    sheet.save(f"{OUTDIR}/teaser_sheet.png")
    print("wrote", OUTDIR)
