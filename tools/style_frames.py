import math, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

BASE = sys.argv[1]
OUT = sys.argv[2]
W, H = 1080, 1920
F = BASE + "/fonts/"
caveat = lambda s: ImageFont.truetype(F + "f1.ttf", s)
corm_i = lambda s: ImageFont.truetype(F + "g1.ttf", s)
corm_l = lambda s: ImageFont.truetype(F + "g2.ttf", s)
corm_m = lambda s: ImageFont.truetype(F + "f5.ttf", s)
jost_l = lambda s: ImageFont.truetype(F + "g3.ttf", s)
jost = lambda s: ImageFont.truetype(F + "g3.ttf", s)

CREAM = (251, 243, 230)
PEACH = (246, 213, 193)
BLUSH = (242, 196, 196)
BUTTER = (247, 227, 168)
MINT = (207, 229, 214)
SAGE = (169, 200, 180)
POWDER = (207, 221, 234)
SUN = (245, 192, 74)
INK = (86, 54, 42)


def grade(img, warmth=1.0):
    """Warm peach film grade: lifted blacks, softened saturation, bloom, grain."""
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    lum = a.mean(axis=2, keepdims=True)
    a = lum + (a - lum) * 0.9                        # desaturate a touch
    a = a * np.array([1.06, 1.0, 0.90]) ** warmth    # warm shift
    a = 0.07 + a * 1.08                              # lift blacks, brighten
    a = a + np.array([0.03, 0.012, -0.005]) * warmth  # peach tint in shadows
    a = np.clip(a, 0, 1)
    out = Image.fromarray((a * 255).astype(np.uint8))
    hi = out.point(lambda v: max(0, v - 170) * 3).filter(ImageFilter.GaussianBlur(30))
    out = ImageChops.screen(out, hi.point(lambda v: int(v * 0.35)))
    return out


def grain(img, amt=10, seed=1):
    rng = np.random.default_rng(seed)
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    n = rng.normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


def paper_bg(c1, c2):
    g = np.linspace(0, 1, H)[:, None, None]
    a = np.array(c1)[None, None] * (1 - g) + np.array(c2)[None, None] * g
    a = np.broadcast_to(a, (H, W, 3)).copy()
    rng = np.random.default_rng(7)
    tex = Image.fromarray((rng.normal(128, 40, (H // 3, W // 3))).clip(0, 255).astype(np.uint8))
    tex = np.asarray(tex.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32)
    a += ((tex - 128) / 128 * 5)[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def cover(img, w, h, cx=0.5, cy=0.5):
    s = max(w / img.width, h / img.height)
    im = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = int((im.width - w) * cx)
    y = int((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))


def shadow(base, mask, offset=(0, 14), blur=26, alpha=70, color=(120, 80, 60)):
    sh = Image.new("RGBA", base.size, color + (0,))
    m = Image.new("L", base.size, 0)
    m.paste(mask, offset)
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255))
    base.alpha_composite(sh)


def spaced(draw, xy, text, font, fill, tracking, anchor="mm"):
    """Letter-spaced text centred on xy."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = xy[0] - total / 2 if anchor == "mm" else xy[0]
    for ch, w in zip(text, widths):
        if ch == "→":  # fonts lack the glyph, draw a thin arrow instead
            w = font.size * 0.9
            y = xy[1]
            draw.line((x, y, x + w, y), fill=fill, width=max(2, font.size // 30))
            draw.line((x + w - font.size * 0.22, y - font.size * 0.16, x + w, y), fill=fill, width=max(2, font.size // 30))
            draw.line((x + w - font.size * 0.22, y + font.size * 0.16, x + w, y), fill=fill, width=max(2, font.size // 30))
        else:
            draw.text((x, xy[1]), ch, font=font, fill=fill, anchor="lm")
        x += w + tracking


def pill(base, center, text, font, fg=INK, bg=CREAM, pad=(34, 18), rot=0, alpha=235):
    d = ImageDraw.Draw(base)
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + pad[0] * 2, th + pad[1] * 2
    layer = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((40, 40, 40 + w, 40 + h), radius=h // 2, fill=bg + (alpha,))
    ld.text((40 + w / 2, 40 + h / 2), text, font=font, fill=fg, anchor="mm")
    if rot:
        layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    pos = (int(center[0] - layer.width / 2), int(center[1] - layer.height / 2))
    shadow(base, layer.getchannel("A"), (pos[0], pos[1] + 8), blur=14, alpha=60)
    base.alpha_composite(layer, pos)


def light_leak(base, center, radius, color, strength=110):
    m = Image.new("L", base.size, 0)
    ImageDraw.Draw(m).ellipse((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), fill=strength)
    m = m.filter(ImageFilter.GaussianBlur(radius * 0.6))
    layer = Image.new("RGBA", base.size, color + (0,))
    layer.putalpha(m)
    base.alpha_composite(layer)


def plane_icon(size, color):
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    d.ellipse((c - s * 0.06, s * 0.08, c + s * 0.06, s * 0.92), fill=color)
    d.polygon([(c, s * 0.38), (s * 0.04, s * 0.58), (s * 0.04, s * 0.65), (c, s * 0.55), (s * 0.96, s * 0.65), (s * 0.96, s * 0.58)], fill=color)
    d.polygon([(c, s * 0.78), (s * 0.3, s * 0.9), (s * 0.3, s * 0.94), (c, s * 0.88), (s * 0.7, s * 0.94), (s * 0.7, s * 0.9)], fill=color)
    return im


def dotted_curve(d, pts, color, r=5, step=26):
    # quadratic-ish smooth path through points
    path = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - 90
        for t in np.linspace(0, 1, 200):
            x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1
            y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1
            path.append((x, y))
    acc, last = 0, path[0]
    for p in path[1:]:
        acc += math.dist(p, last)
        last = p
        if acc >= step:
            acc = 0
            d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=color)
    return path


# ---------- Frame 1: hook, sunrise wing in an airplane window ----------
def frame1():
    base = paper_bg((250, 224, 208), (253, 238, 228)).convert("RGBA")
    light_leak(base, (980, 160), 420, (255, 214, 160), 120)
    light_leak(base, (300, 700), 300, (255, 190, 140), 60)
    light_leak(base, (80, 1700), 380, BLUSH, 90)

    ww, wh = 720, 1000
    wx, wy = (W - ww) // 2, 330
    # bezel (paper-cut layers)
    for i, (pad, col) in enumerate([(70, CREAM), (40, (240, 226, 210))]):
        m = Image.new("L", (ww + pad * 2, wh + pad * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, ww + pad * 2 - 1, wh + pad * 2 - 1), radius=330 + pad, fill=255)
        if i == 0:
            shadow(base, m, (wx - pad, wy - pad + 22), blur=36, alpha=90)
        layer = Image.new("RGBA", m.size, col + (255,))
        layer.putalpha(m)
        base.alpha_composite(layer, (wx - pad, wy - pad))

    src = Image.open(BASE + "/src/wing.png")
    # take a crop that keeps the wing tip and glowing horizon
    view = cover(src.crop((900, 0, 3840, 2160)), ww, wh, cx=0.35, cy=0.5)
    view = grade(view, warmth=1.3)
    vm = Image.new("L", (ww, wh), 0)
    ImageDraw.Draw(vm).rounded_rectangle((0, 0, ww - 1, wh - 1), radius=330, fill=255)
    inner = Image.new("L", (ww, wh), 0)
    ImageDraw.Draw(inner).rounded_rectangle((10, 10, ww - 11, wh - 11), radius=320, fill=255)
    vl = view.convert("RGBA")
    vl.putalpha(vm)
    base.alpha_composite(vl, (wx, wy))
    # inner shadow for depth + glass sheen
    ring = ImageChops.subtract(vm, inner.filter(ImageFilter.GaussianBlur(18)))
    sh = Image.new("RGBA", (ww, wh), (90, 60, 50, 0))
    sh.putalpha(ring.point(lambda v: v * 120 // 255))
    base.alpha_composite(sh, (wx, wy))
    sheen = Image.new("L", (ww, wh), 0)
    ImageDraw.Draw(sheen).polygon([(ww * 0.55, 0), (ww * 0.75, 0), (ww * 0.25, wh), (ww * 0.05, wh)], fill=40)
    sheen = ImageChops.multiply(sheen.filter(ImageFilter.GaussianBlur(30)), vm)
    sl = Image.new("RGBA", (ww, wh), (255, 245, 230, 0))
    sl.putalpha(sheen)
    base.alpha_composite(sl, (wx, wy))

    d = ImageDraw.Draw(base)
    spaced(d, (W / 2, 175), "FLIGHT DIARY  ·  01", jost_l(34), INK, 7)
    spaced(d, (W / 2, 1490), "MUMBAI → BALI", corm_l(96), INK, 14)
    d.text((W / 2, 1585), "via Kuala Lumpur", font=corm_i(58), fill=(150, 92, 70), anchor="mm")

    # mini route
    pts = [(250, 1735), (540, 1735), (830, 1735)]
    for x, y in pts[:-1]:
        for k in range(int(x) + 30, int(x) + 262, 22):
            d.ellipse((k - 4, y - 4, k + 4, y + 4), fill=(200, 150, 130))
    for (x, y), lab, col in zip(pts, ["BOM", "KUL", "DPS"], [BLUSH, MINT, BUTTER]):
        d.ellipse((x - 16, y - 16, x + 16, y + 16), fill=col, outline=CREAM, width=5)
        spaced(d, (x, y + 50), lab, jost(32), INK, 6)
    pl = plane_icon(54, INK + (255,)).rotate(-90, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(pl, (380, 1735 - pl.height // 2))

    out = grain(base.convert("RGB"), 7, 1)
    out.save(OUT + "/style_frame_1_hook.png")


# ---------- Frame 2: meal, full-bleed footage + sticker labels + caption ----------
def frame2():
    src = Image.open(BASE + "/src/meal_9.5.png")
    view = cover(src.crop((820, 0, 2035, 2160)), W, H, cx=0.5)
    view = grade(view, warmth=1.15)
    base = view.convert("RGBA")
    # soft vignette in peach
    vg = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vg).ellipse((-260, -200, W + 260, H + 200), fill=255)
    vg = ImageChops.invert(vg.filter(ImageFilter.GaussianBlur(160))).point(lambda v: v * 150 // 255)
    vl = Image.new("RGBA", (W, H), (120, 70, 55, 0))
    vl.putalpha(vg)
    base.alpha_composite(vl)
    light_leak(base, (1040, 300), 360, (255, 205, 150), 110)

    d = ImageDraw.Draw(base)
    # top label
    pill(base, (W / 2, 210), "FLIGHT 1  ·  MUMBAI TO KL", jost(34), fg=INK, bg=CREAM, pad=(40, 20))
    pill(base, (W / 2, 300), "1:00 am dinner", corm_i(46), fg=INK, bg=PEACH, pad=(30, 10), alpha=220)
    # handwritten stickers
    pill(base, (300, 1180), "paratha", caveat(66), fg=INK, bg=BUTTER, rot=6)
    pill(base, (770, 600), "veg meal", caveat(58), fg=INK, bg=MINT, rot=-5)
    pill(base, (790, 700), "theek-thaak ~", caveat(50), fg=INK, bg=BLUSH, rot=-3)
    # subtitle, kept above the bottom UI safe zone
    pill(base, (W / 2, 1495), "Maine veg liya,", jost(54), fg=INK, bg=CREAM, pad=(38, 16), alpha=240)
    pill(base, (W / 2, 1600), "husband ne non-veg", jost(54), fg=INK, bg=CREAM, pad=(38, 16), alpha=240)

    out = grain(base.convert("RGB"), 9, 2)
    out.save(OUT + "/style_frame_2_meal.png")


# ---------- Frame 3: paper-cut outro, route complete, next stop Bali ----------
def frame3():
    base = paper_bg((223, 238, 228), CREAM).convert("RGBA")
    light_leak(base, (820, 520), 380, (255, 236, 200), 120)

    # sun
    sm = Image.new("L", (140, 140), 0)
    ImageDraw.Draw(sm).ellipse((0, 0, 139, 139), fill=255)
    shadow(base, sm, (790, 470), blur=18, alpha=60)
    sun = Image.new("RGBA", (140, 140), SUN + (255,))
    sun.putalpha(sm)
    base.alpha_composite(sun, (790, 452))

    # route map up top
    d = ImageDraw.Draw(base)
    pts = [(170, 860), (540, 820), (900, 900)]
    path = dotted_curve(d, pts, (196, 150, 130), r=5, step=24)
    for (x, y), lab, col in zip(pts, ["Mumbai", "Kuala Lumpur", "Bali"], [BLUSH, POWDER, BUTTER]):
        d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=col, outline=(255, 255, 255), width=6)
        d.text((x, y + 54), lab, font=corm_i(46), fill=INK, anchor="mm")
    # plane approaching Bali
    i = int(len(path) * 0.86)
    (x0, y0), (x1, y1) = path[i - 3], path[i + 3]
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    pl = plane_icon(70, INK + (255,)).rotate(-ang - 90, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(pl, (int(path[i][0] - pl.width / 2), int(path[i][1] - pl.height / 2)))

    # layered paper waves from the bottom
    layers = [
        (1150, 70, 0.0045, 0.0, (247, 236, 214)),
        (1240, 80, 0.0040, 1.3, BUTTER),
        (1330, 75, 0.0050, 2.1, (248, 200, 170)),
        (1420, 70, 0.0042, 3.0, BLUSH),
        (1520, 65, 0.0048, 4.2, (240, 225, 210)),
        (1630, 60, 0.0040, 5.0, MINT),
        (1740, 50, 0.0052, 0.7, (226, 190, 200)),
    ]
    for y0, amp, freq, ph, col in layers:
        poly = [(x, y0 + amp * math.sin(x * freq + ph) + 25 * math.sin(x * freq * 2.3 + ph * 1.7)) for x in range(-10, W + 11, 6)]
        poly += [(W + 10, H + 10), (-10, H + 10)]
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        shadow(base, m, (0, -10), blur=18, alpha=85)
        lay = Image.new("RGBA", (W, H), col + (255,))
        lay.putalpha(m)
        base.alpha_composite(lay)
        edge = Image.new("L", (W, H), 0)
        ImageDraw.Draw(edge).line(poly[:-2], fill=110, width=3)
        el = Image.new("RGBA", (W, H), (255, 255, 255, 0))
        el.putalpha(edge.filter(ImageFilter.GaussianBlur(1)))
        base.alpha_composite(el)

    # little paper palm on the second wave
    d = ImageDraw.Draw(base)
    px, py = 150, 1265
    palm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(palm)
    trunk = [(px + 10 * math.sin(t / 40), py - t) for t in range(0, 200, 4)]
    pd.line(trunk, fill=SAGE, width=18, joint="curve")
    tx, ty = trunk[-1]
    for a, l in [(-160, 110), (-120, 120), (-60, 120), (-20, 110), (-90, 90)]:
        r = math.radians(a)
        ex, ey = tx + l * math.cos(r), ty + l * math.sin(r) + 30
        pd.polygon([(tx, ty), ((tx + ex) / 2 + 18 * math.sin(r), (ty + ey) / 2 - 22), (ex, ey), ((tx + ex) / 2, (ty + ey) / 2 + 6)], fill=(150, 192, 165))
    shadow(base, palm.getchannel("A"), (8, 10), blur=10, alpha=70)
    base.alpha_composite(palm)

    d = ImageDraw.Draw(base)
    spaced(d, (W / 2, 250), "NEXT STOP", jost_l(44), INK, 18)
    d.text((W / 2, 400), "Bali", font=corm_i(200), fill=INK, anchor="mm")
    d.text((W / 2, 1830), "baaki trip ke liye follow karte raho", font=caveat(62), fill=INK, anchor="mm")

    out = grain(base.convert("RGB"), 7, 3)
    out.save(OUT + "/style_frame_3_outro.png")


frame1()
frame2()
frame3()
print("ok")
