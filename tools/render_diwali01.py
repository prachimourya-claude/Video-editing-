"""Render Diwali 01 (Psone Labs Kalash rangoli stencil) as a 30s 9:16 reel with Diwali motion graphics.

usage: python3 render_diwali01.py <workdir> <out.mp4> [segment ...]
<workdir> must contain src/A.mp4 B.mp4 C.mp4 (WA0009/10/11), fonts/ and music/Vadodora.mp3.
Fonts (Google Fonts): poppins_sb.ttf poppins_xb.ttf playfair_xb.ttf greatvibes.ttf yatra.ttf kalam.ttf
Pass segment names (s1..s6) to re-render only those; the reel is always re-assembled.
"""
import math, os, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:]
SEG = os.path.join(BASE, "segments")
os.makedirs(SEG, exist_ok=True)
W, H, FPS = 1080, 1920, 30
TOTAL = 30.0

F = BASE + "/fonts/"
pop_sb = lambda s: ImageFont.truetype(F + "poppins_sb.ttf", s)
pop_xb = lambda s: ImageFont.truetype(F + "poppins_xb.ttf", s)
playfair = lambda s: ImageFont.truetype(F + "playfair_xb.ttf", s)
vibes = lambda s: ImageFont.truetype(F + "greatvibes.ttf", s)
yatra = lambda s: ImageFont.truetype(F + "yatra.ttf", s)

CREAM = (255, 244, 224)
GOLD = (245, 192, 74)
GOLD_L = (255, 236, 170)
GOLD_D = (196, 128, 26)
MARIGOLD = (255, 140, 26)
SAFFRON = (255, 201, 60)
MAROON = (110, 16, 36)
NIGHT = (27, 7, 16)
PINK = (228, 69, 123)
LEAF = (63, 143, 58)
INK = (60, 14, 24)

# (name, start, end) on the reel timeline; one voiceover line per segment.
SEGMENTS = [
    ("s1", 0.0, 3.2),    # opener: Diwali aa rahi hai / kuch unique
    ("s2", 3.2, 7.2),    # market stencils, sab ek jaise
    ("s3", 7.2, 13.2),   # humne khud design kiya (printer)
    ("s4", 13.2, 19.2),  # upar shubh kalash, neeche kamal
    ("s5", 19.2, 25.2),  # rakho, rang bharo, rangoli ready (animated fill)
    ("s6", 25.2, 30.0),  # Dhanteras se pehle order karo + end card
]
CUTS = [s for _, s, _ in SEGMENTS[1:]]

GRADE = (
    "eq=contrast=1.06:saturation=1.15:brightness=0.01,"
    "colorbalance=rs=0.05:bs=-0.05:rm=0.04:bm=-0.04:rh=0.02:bh=-0.03,vignette=PI/5"
)


# ---------------------------------------------------------------- easing / helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_back(x):
    x = clamp(x)
    c = 1.6
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def win(t, t0, t1, fin=0.25, fout=0.25):
    """1 inside [t0, t1], eased ramps at both ends."""
    return min(ease_out((t - t0) / fin), ease_out((t1 - t) / fout))


def paste_center(base, im, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    if alpha <= 0.002 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.002:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.998:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


def with_shadow(layer, offset=(0, 8), blur=14, alpha=120, color=(20, 4, 8)):
    p = blur * 2 + max(abs(offset[0]), abs(offset[1]))
    out = Image.new("RGBA", (layer.width + 2 * p, layer.height + 2 * p), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0)
    m.paste(layer.getchannel("A"), (p + offset[0], p + offset[1]))
    sh = Image.new("RGBA", out.size, color + (0,))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255))
    out.alpha_composite(sh)
    out.alpha_composite(layer, (p, p))
    return out


def blob(r, color, strength=255):
    m = Image.new("L", (r * 4, r * 4), 0)
    ImageDraw.Draw(m).ellipse((r, r, 3 * r, 3 * r), fill=strength)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.6))
    im = Image.new("RGBA", m.size, color + (0,))
    im.putalpha(m)
    return im


# ---------------------------------------------------------------- text
def text_mask(text, font, stroke=0):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.textbbox((0, 0), text, font=font, stroke_width=stroke)
    pad = 12 + stroke
    m = Image.new("L", (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), text, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
    return m


def plain_text(text, font, fill=CREAM, shadow=150):
    m = text_mask(text, font)
    im = Image.new("RGBA", m.size, fill + (0,))
    im.putalpha(m)
    return with_shadow(im, offset=(0, 5), blur=10, alpha=shadow) if shadow else im


def gold_text(text, font, stroke=3, glow=True):
    """Gold-gradient lettering with a dark maroon edge, soft drop shadow and warm glow."""
    m = text_mask(text, font)
    ms = text_mask(text, font, stroke)
    # stroke mask is larger; centre the fill mask inside it
    off = ((ms.width - m.width) // 2, (ms.height - m.height) // 2)
    fill_m = Image.new("L", ms.size, 0)
    fill_m.paste(m, off)
    g = np.linspace(0, 1, ms.height)[:, None]
    stops = np.array([GOLD_L, GOLD, GOLD_D, GOLD], np.float32)
    pos = np.array([0, 0.45, 0.8, 1.0])
    grad = np.stack([np.interp(g[:, 0], pos, stops[:, c]) for c in range(3)], 1)
    grad = np.broadcast_to(grad[:, None, :], (ms.height, ms.width, 3)).astype(np.uint8)
    im = Image.new("RGBA", ms.size, MAROON + (0,))
    im.putalpha(ms)
    fill = Image.fromarray(grad).convert("RGBA")
    fill.putalpha(fill_m)
    im.alpha_composite(fill)
    out = with_shadow(im, offset=(0, 6), blur=12, alpha=170)
    if glow:
        p = 40
        gl = Image.new("RGBA", (out.width + 2 * p, out.height + 2 * p), (0, 0, 0, 0))
        gm = Image.new("L", gl.size, 0)
        gm.paste(ms, (p + (out.width - ms.width) // 2, p + (out.height - ms.height) // 2))
        gm = gm.filter(ImageFilter.GaussianBlur(18)).point(lambda v: v * 110 // 255)
        g2 = Image.new("RGBA", gl.size, (255, 170, 60, 0))
        g2.putalpha(gm)
        gl.alpha_composite(g2)
        gl.alpha_composite(out, (p, p))
        out = gl
    return out


def pill(text, font, fg=INK, bg=CREAM, pad=(36, 18), alpha=245, border=None):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + pad[0] * 2, th + pad[1] * 2
    layer = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((4, 4, 4 + w, 4 + h), radius=h // 2, fill=bg + (alpha,), outline=border, width=4 if border else 0)
    ld.text((4 + w / 2 - bb[0] / 2, 4 + h / 2), text, font=font, fill=fg, anchor="mm")
    return with_shadow(layer, offset=(0, 8), blur=14, alpha=130)


def pop(base, im, cx, cy, t, t0, dur=0.45, t_out=None, from_scale=0.55, rise=0):
    if t < t0:
        return
    a = ease_out((t - t0) / (dur * 0.6))
    s = from_scale + (1 - from_scale) * ease_back((t - t0) / dur)
    if t_out is not None:
        o = ease_out((t_out - t) / 0.25)
        a *= o
        s *= 0.9 + 0.1 * o
    paste_center(base, im, cx, cy + (1 - a) * rise, a, s)


# ---------------------------------------------------------------- Diwali sprites
def flame_sprite(h):
    w = int(h * 0.55)
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def drop(scale, col):
        pts = []
        for k in range(60):
            th = 2 * math.pi * k / 60
            x = math.sin(th) * math.sin(th / 2) ** 1.4 * w * 0.5 * scale
            y = -math.cos(th) * h * 0.5 * scale
            pts.append((10 + w / 2 + x, 10 + h / 2 + y + h * 0.5 * (1 - scale)))
        d.polygon(pts, fill=col)

    drop(1.0, (255, 120, 20, 235))
    drop(0.78, (255, 196, 50, 250))
    drop(0.5, (255, 246, 200, 255))
    return im.filter(ImageFilter.GaussianBlur(max(1, h / 40)))


def diya_sprite(w):
    h = int(w * 0.42)
    im = Image.new("RGBA", (w + 20, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 10, 10
    d.chord((x0, y0 - h, x0 + w, y0 + h), 0, 180, fill=(170, 70, 30, 255))
    # spout
    d.polygon([(x0 + w * 0.82, y0 + 2), (x0 + w * 1.02, y0 - h * 0.18), (x0 + w * 0.92, y0 + h * 0.25)], fill=(170, 70, 30, 255))
    d.ellipse((x0, y0 - h * 0.16, x0 + w, y0 + h * 0.16), fill=(120, 40, 18, 255))
    d.ellipse((x0 + w * 0.05, y0 - h * 0.1, x0 + w * 0.95, y0 + h * 0.1), fill=(200, 140, 40, 255))
    # painted band: gold dots and a maroon zigzag
    for k in range(9):
        fx = 0.14 + 0.72 * k / 8
        yy = y0 + h * 0.45 * math.sqrt(max(0, 1 - ((fx - 0.5) * 2) ** 2)) * 0.75
        r = w * 0.025
        d.ellipse((x0 + w * fx - r, yy - r, x0 + w * fx + r, yy + r), fill=GOLD + (255,))
    zig = [(x0 + w * (0.12 + 0.76 * k / 16), y0 + h * (0.18 if k % 2 else 0.28)) for k in range(17)]
    d.line(zig, fill=(255, 220, 120, 255), width=max(2, w // 60))
    # shading
    g = np.linspace(1.15, 0.65, im.height)[:, None, None]
    a = np.asarray(im).astype(np.float32)
    a[..., :3] = np.clip(a[..., :3] * g, 0, 255)
    return Image.fromarray(a.astype(np.uint8))


_DIYA, _FLAME, _GLOW = {}, {}, {}


def draw_diya(base, x, y, w, t, seed=0, lit=1.0):
    if w not in _DIYA:
        _DIYA[w] = diya_sprite(w)
        _FLAME[w] = flame_sprite(int(w * 0.5))
        _GLOW[w] = blob(int(w * 0.55), (255, 150, 50), 200)
    fl = 1 + 0.07 * math.sin(13 * t + seed) + 0.05 * math.sin(31 * t + 2.3 * seed)
    if lit > 0:
        paste_center(base, _GLOW[w], x, y - w * 0.3, lit * (0.6 + 0.35 * (fl - 0.88) / 0.24))
    paste_center(base, _DIYA[w], x, y + w * 0.12)
    if lit > 0:
        f = _FLAME[w]
        fh = int(f.height * fl * (0.4 + 0.6 * lit))
        fw = int(f.width * (0.85 + 0.15 * lit))
        f = f.resize((fw, max(2, fh)), Image.BILINEAR)
        sway = 2 * math.sin(7 * t + seed)
        paste_center(base, f, x + w * 0.08 + sway, y - w * 0.04 - f.height / 2 + 6, min(1, lit * 1.5))


def marigold(r, col, seed):
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (r * 2 + 6, r * 2 + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = r + 3
    d.ellipse((c - r, c - r, c + r, c + r), fill=tuple(int(v * 0.8) for v in col) + (255,))
    for k in range(70):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, r * 0.85)
        pr = rng.uniform(r * 0.18, r * 0.32)
        sh = rng.uniform(0.75, 1.15)
        cc = tuple(int(clamp(v * sh / 255) * 255) for v in col)
        x, y = c + rr * math.cos(a), c + rr * math.sin(a)
        d.ellipse((x - pr, y - pr * 0.7, x + pr, y + pr * 0.7), fill=cc + (255,))
    return im


def leaf(l):
    im = Image.new("RGBA", (int(l * 0.45), l), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = im.width
    pts = [(w / 2 + math.sin(math.pi * k / 20) * w * 0.48 * (1 if s else -1), l * k / 20) for s in (1, 0) for k in (range(21) if s else range(20, -1, -1))]
    d.polygon(pts, fill=(52, 128, 50, 255))
    d.line((w / 2, 2, w / 2, l - 2), fill=(120, 190, 90, 255), width=2)
    return im


def make_toran():
    """Marigold bandhanwar: top string of mango leaves, swags of marigolds, hanging strands."""
    im = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
    balls = [marigold(22, MARIGOLD if k % 2 else SAFFRON, k) for k in range(6)]
    small = [marigold(17, MARIGOLD if k % 2 else SAFFRON, 10 + k) for k in range(6)]
    lf = leaf(70)
    for k in range(17):
        x = -20 + k * 70
        paste_center(im, lf.rotate(180 + (k % 3 - 1) * 12, expand=True, resample=Image.BICUBIC), x, 62)
    for k in range(40):
        paste_center(im, small[k % 6], -10 + k * 28, 30)
    supports = [-60, 300, 780, 1140]
    i = 0
    for a, b in zip(supports, supports[1:]):
        n = int((b - a) / 30)
        for k in range(n + 1):
            u = k / n
            x = a + (b - a) * u
            y = 40 + 150 * math.sin(math.pi * u)
            paste_center(im, balls[i % 6], x, y)
            i += 1
    for x in supports[1:-1]:
        for k in range(7):
            paste_center(im, balls[(k + 3) % 6], x, 50 + k * 34)
        paste_center(im, lf, x, 50 + 7 * 34 + 20)
    return with_shadow(im, offset=(0, 10), blur=12, alpha=140)


def star(r):
    im = Image.new("RGBA", (r * 6, r * 6), (0, 0, 0, 0))
    c = r * 3
    g = blob(r, (255, 200, 110), 150)
    im.alpha_composite(g.resize((r * 6, r * 6)), (0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(c, c - r * 2.6), (c + r * 0.3, c), (c, c + r * 2.6), (c - r * 0.3, c)], fill=(255, 245, 210, 255))
    d.polygon([(c - r * 2.6, c), (c, c - r * 0.3), (c + r * 2.6, c), (c, c + r * 0.3)], fill=(255, 245, 210, 255))
    return im


STARS = None
SPARKS = np.random.default_rng(11).uniform(size=(46, 5))


def draw_sparkles(base, t, alpha=1.0, n=46, ymin=0, ymax=H):
    global STARS
    if STARS is None:
        STARS = [star(r) for r in (5, 8, 11)]
    for k in range(n):
        u = SPARKS[k]
        x = u[0] * W + 30 * math.sin(t * 0.7 + 6 * u[1])
        y = ymin + ((u[1] * (ymax - ymin) - t * (25 + 50 * u[2])) % (ymax - ymin))
        tw = 0.5 + 0.5 * math.sin(t * (2 + 3 * u[3]) + 10 * u[4])
        paste_center(base, STARS[k % 3], x, y, alpha * tw ** 2, rot=t * 40 * (u[3] - 0.5))


def make_mandala(R=520):
    S = R * 2 + 20
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    rings = [(0.18, 8, 0.12, SAFFRON), (0.34, 12, 0.14, MARIGOLD), (0.52, 16, 0.15, PINK), (0.72, 24, 0.14, GOLD), (0.9, 32, 0.1, SAFFRON)]
    for rf, n, pl, col in rings:
        r = R * rf
        for k in range(n):
            a = 2 * math.pi * k / n
            pts = []
            for j in range(25):
                s = j / 24
                rr = r + R * pl * s
                ww = math.sin(math.pi * s) * (math.pi / n) * 0.8
                pts.append((c + rr * math.cos(a + ww), c + rr * math.sin(a + ww)))
            for j in range(24, -1, -1):
                s = j / 24
                rr = r + R * pl * s
                ww = math.sin(math.pi * s) * (math.pi / n) * 0.8
                pts.append((c + rr * math.cos(a - ww), c + rr * math.sin(a - ww)))
            d.polygon(pts, outline=col + (200,), fill=col + (40,), width=3)
            dr = R * 0.012
            x, y = c + (r + R * pl + R * 0.03) * math.cos(a), c + (r + R * pl + R * 0.03) * math.sin(a)
            d.ellipse((x - dr, y - dr, x + dr, y + dr), fill=GOLD_L + (220,))
        d.ellipse((c - r, c - r, c + r, c + r), outline=col + (120,), width=2)
    return im


# fireworks: (x, y, t_burst, colour)
def draw_fireworks(base, t, bursts, alpha=1.0):
    lay = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    any_ = False
    for (x, y, t0, col, seed) in bursts:
        x, y = x / 2, y / 2
        a = t - t0
        if -0.55 < a < 0:  # rocket
            u = 1 + a / 0.55
            ry = H / 2 + (y - H / 2) * ease_out(u)
            d.line((x, ry, x, ry + 30), fill=(255, 230, 180, int(200 * alpha)), width=2)
            any_ = True
        if 0 <= a < 1.8:
            any_ = True
            rng = np.random.default_rng(seed)
            n = 34
            fade = (1 - a / 1.8) ** 1.5
            for k in range(n):
                ang = 2 * math.pi * k / n + rng.uniform(-0.08, 0.08)
                v = 210 * rng.uniform(0.75, 1.0)

                def pos(aa):
                    dist = v * (1 - math.exp(-3 * aa)) / 3
                    return x + dist * math.cos(ang), y + dist * math.sin(ang) + 40 * aa * aa

                p1, p0 = pos(a), pos(max(0, a - 0.12))
                c2 = tuple(int(c + (255 - c) * 0.4 * fade) for c in col)
                d.line((p0, p1), fill=c2 + (int(255 * fade * alpha),), width=3)
                if (k + int(a * 20)) % 3 == 0:
                    d.ellipse((p1[0] - 2.5, p1[1] - 2.5, p1[0] + 2.5, p1[1] + 2.5), fill=(255, 250, 230, int(255 * fade * alpha)))
    if not any_:
        return
    glow = lay.filter(ImageFilter.GaussianBlur(6))
    big = Image.alpha_composite(glow, lay).resize((W, H), Image.BILINEAR)
    base.alpha_composite(big)
    base.alpha_composite(glow.resize((W, H), Image.BILINEAR))


def night_bg(seed=3):
    g = np.linspace(0, 1, H)[:, None]
    stops = np.array([(18, 4, 22), (52, 8, 34), (92, 18, 38)], np.float32)
    col = np.stack([np.interp(g[:, 0], [0, 0.55, 1], stops[:, c]) for c in range(3)], 1)
    a = np.broadcast_to(col[:, None, :], (H, W, 3)).copy()
    im = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    rng = np.random.default_rng(seed)
    for k in range(26):
        r = int(rng.uniform(20, 70))
        b = blob(r, tuple(int(v) for v in rng.choice([(255, 170, 60), (255, 120, 80), (255, 210, 120)])), int(rng.uniform(40, 110)))
        paste_center(im, b, rng.uniform(0, W), rng.uniform(H * 0.25, H))
    return im


# ---------------------------------------------------------------- footage
def footage(name, ss, src_dur, out_dur, zoom=(1.0, 1.08), center=(0.5, 0.5)):
    """Yield graded RGBA frames (W x H) of a clip; src_dur of source stretched to out_dur, with a push-in."""
    n = int(round(out_dur * FPS))
    k = out_dur / src_dur
    vf = (f"setpts=(PTS-STARTPTS)*{k:.5f},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
          f"crop={W}:{H},{GRADE},tpad=stop_mode=clone:stop_duration=2,format=rgb24")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(src_dur + 0.2), "-i", f"{BASE}/src/{name}.mp4",
                          "-vf", vf, "-frames:v", str(n), "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    fr = None
    for i in range(n):
        buf = p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            fr = Image.frombuffer("RGB", (W, H), buf)
        z = zoom[0] + (zoom[1] - zoom[0]) * ease_io(i / max(1, n - 1))
        cw, ch = W / z, H / z
        cx, cy = center[0] * W, center[1] * H
        x0 = clamp(cx - cw / 2, 0, W - cw)
        y0 = clamp(cy - ch / 2, 0, H - ch)
        yield fr.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch)).convert("RGBA")
    p.wait()


def top_scrim(base, h=700, alpha=150):
    g = np.linspace(1, 0, h) ** 1.6 * alpha
    m = Image.fromarray(np.broadcast_to(g[:, None], (h, W)).astype(np.uint8))
    sc = Image.new("RGBA", (W, h), NIGHT + (0,))
    sc.putalpha(m)
    base.alpha_composite(sc)


def bottom_scrim(base, h=800, alpha=170):
    g = np.linspace(0, 1, h) ** 1.6 * alpha
    m = Image.fromarray(np.broadcast_to(g[:, None], (h, W)).astype(np.uint8))
    sc = Image.new("RGBA", (W, h), NIGHT + (0,))
    sc.putalpha(m)
    base.alpha_composite(sc, (0, H - h))


# ---------------------------------------------------------------- stencil cut-out + colour fill
def build_stencil():
    """Cut the stencil out of clip A at 3.0s, rebuild the hand-covered left half by mirroring, and
    prepare its rangoli colouring plus a per-pixel 'colour arrives' time map."""
    src = f"{BASE}/stencil_A3.png"
    if not os.path.exists(src):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "3.0", "-i", f"{BASE}/src/A.mp4", "-frames:v", "1", src], check=True)
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    R, B = im[..., 0], im[..., 2]
    L = im.mean(2)
    m = ((B - R > 4) & (L > 100)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    m = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
    h, w = m.shape
    ff = m.copy()
    cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1)
    m = m | (1 - ff)
    # symmetry axis from the rows above the hand
    ys = range(st[1 + np.argmax(st[1:, 4]), 1] + 20, 520)
    mids = []
    for y in ys:
        xs = np.where(m[y])[0]
        if len(xs):
            mids.append((xs[0] + xs[-1]) / 2)
    cx = int(round(np.median(mids)))
    xs = np.arange(w)
    mir = np.clip(2 * cx - xs, 0, w - 1)
    left = xs < cx
    im[:, left] = im[:, mir[left]]
    m[:, left] = m[:, mir[left]]
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    ysm, xsm = np.where(m)
    y0, y1, x0, x1 = ysm.min(), ysm.max() + 1, xsm.min(), xsm.max() + 1
    im, m, L = im[y0:y1, x0:x1], m[y0:y1, x0:x1], im[y0:y1, x0:x1].mean(2)
    cx -= x0
    # neutral white stencil (photo is a little blue)
    shade = L / np.percentile(L[m > 0], 90)
    white = np.clip(np.stack([shade * 248, shade * 244, shade * 238], 2), 0, 255)
    # grooves = raised walls' shadows; keep a white rim on the outer border too
    d = cv2.GaussianBlur(L, (0, 0), 5) - L
    walls = (d > 4).astype(np.uint8)
    rim = m - cv2.erode(m, np.ones((15, 15), np.uint8))
    paintable = (m & (1 - cv2.dilate(walls, np.ones((3, 3), np.uint8))) & (1 - rim)).astype(np.float32)
    paintable = cv2.GaussianBlur(paintable, (0, 0), 1.2)
    # colour zones, in cropped-still rows (stencil ~800px tall)
    hh = y1 - y0
    yy, xx = np.mgrid[0:hh, 0:(x1 - x0)].astype(np.float32)
    fy = yy / hh
    dx = np.abs(xx - cx) / (x1 - x0)
    col = np.zeros((hh, x1 - x0, 3), np.float32)
    zone_t = np.zeros((hh, x1 - x0), np.float32)

    def put(sel, c, t0):
        col[sel] = c
        zone_t[sel] = t0

    put(np.ones_like(fy, bool), (200, 30, 60), 0.0)
    put(fy >= 0.68, (228, 60, 130), 0.0)                       # lotus petals: rani pink
    put((fy >= 0.68) & (dx < 0.12) & (fy < 0.9), (255, 150, 190), 0.15)  # centre petal: light pink
    put((fy >= 0.92), (60, 150, 70), 0.3)                      # base: green
    put((fy >= 0.52) & (fy < 0.68), (205, 30, 45), 0.55)       # pot body: kumkum red
    put((fy >= 0.42) & (fy < 0.52), (255, 135, 20), 0.75)      # oval band: marigold
    put((fy >= 0.34) & (fy < 0.42), (120, 20, 60), 0.9)        # dot band: maroon
    put((fy >= 0.27) & (fy < 0.34), (250, 190, 40), 1.05)      # neck: haldi yellow
    put((fy >= 0.08) & (fy < 0.27), (50, 150, 60), 1.2)        # mango leaves: green
    put((fy >= 0.08) & (fy < 0.27) & (dx < 0.09), (255, 175, 40), 1.3)  # coconut / centre leaf
    put(fy < 0.08, (255, 120, 20), 1.45)                       # tip: saffron
    # powder grain
    rng = np.random.default_rng(5)
    grain = cv2.GaussianBlur(rng.normal(0, 1, fy.shape).astype(np.float32), (0, 0), 0.8)
    colored = np.clip(col * (0.82 + 0.18 * shade[..., None]) * (1 + 0.09 * grain[..., None]), 0, 255)
    # arrival time: each zone pours from its centre outwards, with a powdery noisy front
    noise = cv2.GaussianBlur(rng.uniform(0, 1, fy.shape).astype(np.float32), (0, 0), 6)
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    dist = np.hypot((xx - cx) / (x1 - x0), (fy - 0.5) * 0.3)
    arrive = zone_t + 0.35 * dist / dist.max() + 0.25 * noise
    return dict(white=white, colored=colored, paint=paintable, mask=m.astype(np.float32), arrive=arrive)


def stencil_frame(S, prog, scale):
    """RGBA image of the stencil, coloured up to fill-time prog (seconds into the fill)."""
    a = np.clip((prog - S["arrive"]) / 0.12, 0, 1) * S["paint"]
    rgb = S["white"] * (1 - a[..., None]) + S["colored"] * a[..., None]
    rgba = np.dstack([rgb, S["mask"] * 255]).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA")
    return im.resize((int(im.width * scale), int(im.height * scale)), Image.BILINEAR)


def floor_bg():
    rng = np.random.default_rng(9)
    g = np.linspace(0, 1, H)[:, None]
    stops = np.array([(96, 26, 22), (128, 38, 28), (84, 22, 20)], np.float32)
    col = np.stack([np.interp(g[:, 0], [0, 0.5, 1], stops[:, c]) for c in range(3)], 1)
    a = np.broadcast_to(col[:, None, :], (H, W, 3)).copy()
    tex = cv2.resize(rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32), (W, H))
    a *= (1 + 0.05 * tex)[..., None]
    for x in (0, 540, 1080):
        a[:, max(0, x - 2):x + 2] *= 0.8
    for y in (180, 720, 1260, 1800):
        a[y - 2:y + 2] *= 0.8
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.55 * (((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2) * 2.2
    a *= np.clip(v, 0, 1)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    # scattered marigold petals
    for k in range(60):
        r = int(rng.uniform(6, 12))
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if abs(x - W / 2) < 380 and 380 < y < 1560:
            continue
        p = Image.new("RGBA", (r * 3, r * 3), (0, 0, 0, 0))
        ImageDraw.Draw(p).ellipse((r * 0.5, r, r * 2.5, r * 2), fill=(MARIGOLD if k % 2 else SAFFRON) + (230,))
        paste_center(im, p.rotate(rng.uniform(0, 180), expand=True), x, y)
    return im


def generic_tile(size, kalash=None):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=26, fill=(70, 62, 66, 255), outline=(120, 110, 112, 255), width=3)
    c = size / 2
    if kalash is not None:
        k = kalash.resize((int(kalash.width * size * 0.8 / kalash.height), int(size * 0.8)), Image.BILINEAR)
        im.alpha_composite(k, (int(c - k.width / 2), int(c - k.height / 2)))
        return im
    for j in range(8):
        a = math.pi * j / 4
        x, y = c + size * 0.2 * math.cos(a), c + size * 0.2 * math.sin(a)
        r = size * 0.12
        d.ellipse((x - r, y - r, x + r, y + r), outline=(170, 160, 160, 255), width=6)
    d.ellipse((c - size * 0.09, c - size * 0.09, c + size * 0.09, c + size * 0.09), outline=(170, 160, 160, 255), width=6)
    return im


# ---------------------------------------------------------------- shared overlays
TORAN = None


def overlay_common(base, t, toran_drop=1.0, sparkles=0.8):
    global TORAN
    if TORAN is None:
        TORAN = make_toran()
    if sparkles:
        draw_sparkles(base, t, sparkles)
    if toran_drop > 0:
        top = -20 - TORAN.height * (1 - ease_back(toran_drop))
        paste_center(base, TORAN, W / 2, top + TORAN.height / 2 + 4 * math.sin(t * 1.3))
    # flash on every cut
    for c in CUTS:
        f = max(0, 1 - abs(t - c) / 0.14)
        if f > 0:
            fl = Image.new("RGBA", (W, H), (255, 236, 200, int(170 * f)))
            base.alpha_composite(fl)


# ---------------------------------------------------------------- segments
def seg_s1(t0, t1):
    bg = night_bg()
    mand = make_mandala(560)
    t_diwali = gold_text("Diwali aa rahi hai!", vibes(150), stroke=2)
    t_line = plain_text("Is baar rangoli ho", pop_sb(64))
    t_uniq = gold_text("kuch UNIQUE", playfair(150))
    bursts = [(250, 560, 0.25, (255, 190, 80), 1), (820, 420, 0.65, (255, 100, 150), 2),
              (560, 300, 1.25, (120, 220, 255), 3), (180, 340, 1.9, (255, 220, 120), 4), (880, 640, 2.3, (255, 140, 60), 5)]
    for i in range(int(round((t1 - t0) * FPS))):
        t = t0 + i / FPS
        f = bg.copy()
        paste_center(f, mand.rotate(t * 8, resample=Image.BICUBIC), W / 2, 1000, 0.35 * ease_out(t / 0.8), 0.9 + 0.05 * t)
        draw_fireworks(f, t, bursts)
        pop(f, t_diwali, W / 2, 760, t, 0.35, 0.6)
        pop(f, t_line, W / 2, 960, t, 0.95, 0.4, rise=20, from_scale=0.9)
        pop(f, t_uniq, W / 2, 1110, t, 1.25, 0.55, from_scale=0.3)
        for k in range(5):
            x = 160 + k * 190
            lit = clamp((t - 0.2 - k * 0.18) / 0.3)
            draw_diya(f, x, 1500, 150, t, k, lit)
        overlay_common(f, t, toran_drop=clamp(t / 0.7))
        yield f


def seg_s2(t0, t1, S):
    bg = night_bg(5)
    tile = generic_tile(270)
    kal = stencil_frame(S, 9, 1.0)
    gold_tile = Image.new("RGBA", (270, 270), (0, 0, 0, 0))
    ImageDraw.Draw(gold_tile).rounded_rectangle((0, 0, 269, 269), radius=26, fill=MAROON + (255,), outline=GOLD + (255,), width=6)
    k = kal.resize((int(kal.width * 230 / kal.height), 230), Image.BILINEAR)
    gold_tile.alpha_composite(k, ((270 - k.width) // 2, 20))
    h1 = plain_text("Market ke stencils...", pop_sb(70))
    h2 = gold_text("sab ek jaise!", playfair(110))
    for i in range(int(round((t1 - t0) * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bg.copy()
        pop(f, h1, W / 2, 420, lt, 0.1, 0.4, rise=20, from_scale=0.9)
        grey = clamp((lt - 2.6) / 0.3)
        for r in range(3):
            for c in range(3):
                x, y = W / 2 + (c - 1) * 300, 950 + (r - 1) * 300
                j = r * 3 + c
                if j == 4:
                    continue
                st = 0.3 + j * 0.07
                a = ease_out((lt - st) / 0.3) * (1 - grey)
                paste_center(f, tile, x, y + 40 * (1 - a) + grey * 200 * (j / 8), a, 0.7 + 0.3 * ease_back((lt - st) / 0.4))
        # centre tile: generic, then flips to our kalash and grows into the next scene
        a = ease_out((lt - 0.58) / 0.3)
        flip = clamp((lt - 2.6) / 0.35)
        sx = abs(math.cos(math.pi * flip))
        im = tile if flip < 0.5 else gold_tile
        grow = 1 + 3.2 * ease_io((lt - 3.3) / 0.7) ** 2
        if a > 0 and sx > 0.03:
            sq = im.resize((max(1, int(270 * sx)), 270))
            paste_center(f, sq, W / 2, 950, a, (0.7 + 0.3 * ease_back((lt - 0.58) / 0.4)) * grow)
        pop(f, h2, W / 2, 1460, lt, 1.3, 0.5, t_out=2.7)
        if lt > 2.9:
            pop(f, gold_text("Humara design", playfair(96)), W / 2, 1460, lt, 2.9, 0.45)
        overlay_common(f, t)
        yield f


def seg_s3(t0, t1):
    a_dur, b_dur = 3.8, 2.2
    t_a = plain_text("Humne khud", pop_sb(80))
    t_b = gold_text("design kiya!", playfair(130))
    badge = pill("Designed & 3D printed by Psone Labs", pop_sb(40), fg=CREAM, bg=MAROON, border=GOLD + (255,))
    spec = pill("Special: Dhanteras & Diwali", pop_sb(48), fg=INK, bg=SAFFRON)
    frames = list(zip(footage("C", 2.0, 3.6, a_dur, (1.0, 1.1), (0.5, 0.45)), [0] * 999)) + \
        list(zip(footage("B", 9.2, 2.6, b_dur, (1.05, 1.15), (0.5, 0.6)), [1] * 999))
    for i, (f, part) in enumerate(frames):
        t = t0 + i / FPS
        lt = t - t0
        top_scrim(f, 760, 170)
        bottom_scrim(f, 600, 150)
        pop(f, t_a, W / 2, 470, lt, 0.15, 0.4, rise=20, from_scale=0.9)
        pop(f, t_b, W / 2, 600, lt, 0.4, 0.5)
        pop(f, badge, W / 2, 1480, lt, 1.0, 0.45, t_out=a_dur + 0.1)
        pop(f, spec, W / 2, 1480, lt, a_dur + 0.15, 0.45)
        draw_diya(f, 120, 1690, 120, t, 1)
        draw_diya(f, W - 120, 1690, 120, t, 2)
        overlay_common(f, t)
        yield f


def arrow_label(base, text, lx, ly, tx, ty, t, t0):
    """Cream label at (lx, ly) with a gold curved line drawn out to the target point (tx, ty)."""
    if t < t0:
        return
    p = ease_out((t - t0) / 0.5)
    d = ImageDraw.Draw(base)
    lx0 = lx
    lx = lx - text.width / 2 + 60  # line leaves from the label's left end
    mx, my = (lx + tx) / 2, min(ly, ty) - 60
    pts = []
    for k in range(int(30 * p) + 1):
        u = k / 30
        x = (1 - u) ** 2 * lx + 2 * (1 - u) * u * mx + u * u * tx
        y = (1 - u) ** 2 * ly + 2 * (1 - u) * u * my + u * u * ty
        pts.append((x, y))
    if len(pts) > 1:
        d.line(pts, fill=GOLD + (255,), width=7, joint="curve")
    if p > 0.95:
        d.ellipse((tx - 12, ty - 12, tx + 12, ty + 12), fill=GOLD + (255,), outline=CREAM + (255,), width=4)
    pop(base, text, lx0, ly, t, t0, 0.45)


def seg_s4(t0, t1):
    title = gold_text("Kalash Rangoli Stencil", playfair(84))
    up = pill("Upar: Shubh Kalash", pop_sb(48), fg=INK, bg=CREAM)
    dn = pill("Neeche: Kamal", pop_sb(48), fg=CREAM, bg=PINK)
    for i, f in enumerate(footage("B", 0.0, 4.0, t1 - t0, (1.0, 1.08), (0.45, 0.5))):
        t = t0 + i / FPS
        lt = t - t0
        top_scrim(f, 640, 150)
        pop(f, title, W / 2, 400, lt, 0.15, 0.5)
        arrow_label(f, up, 800, 650, 560, 470, lt, 1.0)
        arrow_label(f, dn, 780, 1500, 590, 1140, lt, 2.6)
        overlay_common(f, t, sparkles=0.6)
        yield f


def seg_s5(t0, t1, S):
    bg = floor_bg()
    title = plain_text("Bas 3 steps!", pop_sb(72))
    chips = [pill(s, pop_sb(44), fg=INK, bg=c) for s, c in
             (("1  Rakho", CREAM), ("2  Rang bharo", SAFFRON), ("3  Rangoli ready!", (255, 170, 200)))]
    tag = pill("Design preview", pop_sb(30), fg=CREAM, bg=(40, 10, 16), pad=(22, 10), alpha=200)
    ready = gold_text("Perfect rangoli!", vibes(140), stroke=2)
    scale = 1040 / S["mask"].shape[0]
    bursts = [(300, 620, 3.25, (255, 200, 90), 21), (800, 560, 3.55, (255, 120, 170), 22)]
    for i in range(int(round((t1 - t0) * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bg.copy()
        drop = ease_out((lt - 0.2) / 0.6)
        fill_t = (lt - 1.3) * 1.45
        st = stencil_frame(S, fill_t, scale * (1.12 - 0.12 * drop))
        # shadow + stencil
        shd = Image.new("RGBA", st.size, (10, 2, 4, 0))
        shd.putalpha(st.getchannel("A").point(lambda v: v * 150 // 255))
        shd = shd.filter(ImageFilter.GaussianBlur(10 + 30 * (1 - drop)))
        paste_center(f, shd, W / 2 + 10, 1070 + 18 + 40 * (1 - drop), drop)
        paste_center(f, st, W / 2, 1070 - 60 * (1 - drop), drop)
        lit = clamp((lt - 3.0) / 0.4)
        for k, (x, y) in enumerate(((110, 520), (W - 110, 520), (110, 1560), (W - 110, 1560))):
            draw_diya(f, x, y, 130, t, k + 3, 0.25 + 0.75 * lit)
        draw_fireworks(f, lt, bursts, 0.8)
        pop(f, title, W / 2, 330, lt, 0.1, 0.4, rise=20, from_scale=0.9, t_out=3.15)
        for k, ct in enumerate((0.3, 1.2, 3.0)):
            pop(f, chips[k], W / 2, 1700, lt, ct, 0.35, t_out=(1.2, 3.0, 99)[k])
        pop(f, ready, W / 2, 360, lt, 3.2, 0.5)
        paste_center(f, tag, W - 170, 230, 0.9 * ease_out((lt - 1.2) / 0.3))
        overlay_common(f, t, toran_drop=0, sparkles=0.5 + 0.5 * lit)
        yield f


def seg_s6(t0, t1, S):
    a_dur = 2.4
    t_a = plain_text("Dhanteras se pehle", pop_sb(76))
    t_b = gold_text("order karo!", playfair(140))
    dm = pill("DM to order", pop_xb(56), fg=INK, bg=SAFFRON, pad=(54, 24))
    bg = night_bg(8)
    mand = make_mandala(560)
    brand = gold_text("Psone Labs", playfair(150))
    sub = plain_text("Kalash Rangoli Stencil", pop_sb(54))
    shubh = gold_text("शुभ दीपावली", yatra(120), stroke=2)
    ig = pill("Instagram: Psone Labs", pop_sb(40), fg=CREAM, bg=MAROON, border=GOLD + (255,))
    kal = stencil_frame(S, 9, 380 / S["mask"].shape[0])
    bursts = [(220, 380, a_dur + 0.4, (255, 190, 80), 31), (860, 330, a_dur + 0.9, (255, 110, 160), 32),
              (540, 250, a_dur + 1.5, (140, 220, 255), 33)]
    clip = footage("A", 3.0, 3.0, a_dur, (1.0, 1.08), (0.55, 0.42))
    n_a = int(round(a_dur * FPS))
    for i in range(int(round((t1 - t0) * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        if i < n_a:
            f = next(clip)
            top_scrim(f, 600, 120)
            bottom_scrim(f, 900, 200)
            pop(f, t_a, W / 2, 1300, lt, 0.1, 0.4, rise=20, from_scale=0.9)
            pop(f, t_b, W / 2, 1440, lt, 0.35, 0.5)
            pulse = 1 + 0.05 * math.sin(lt * 9) * clamp((lt - 1.2) / 0.2)
            if lt > 0.9:
                paste_center(f, dm, W / 2, 1640, ease_out((lt - 0.9) / 0.3), pulse * (0.6 + 0.4 * ease_back((lt - 0.9) / 0.4)))
            overlay_common(f, t, sparkles=0.7)
        else:
            e = lt - a_dur
            f = bg.copy()
            paste_center(f, mand.rotate(e * 10, resample=Image.BICUBIC), W / 2, 830, 0.4 * ease_out(e / 0.5), 0.95)
            draw_fireworks(f, lt, bursts)
            pop(f, kal, W / 2, 830, e, 0.0, 0.5)
            pop(f, brand, W / 2, 1180, e, 0.2, 0.5)
            pop(f, sub, W / 2, 1310, e, 0.45, 0.4, rise=20, from_scale=0.9)
            pop(f, ig, W / 2, 1420, e, 0.65, 0.4)
            pop(f, shubh, W / 2, 1600, e, 0.9, 0.5)
            for k, x in enumerate((140, W - 140)):
                draw_diya(f, x, 1650, 140, t, k + 7, 1)
            # flash into the end card
            fl = max(0, 1 - e / 0.18)
            if fl > 0:
                f.alpha_composite(Image.new("RGBA", (W, H), (255, 236, 200, int(170 * fl))))
            overlay_common(f, t, sparkles=0.9)
        yield f


# ---------------------------------------------------------------- render
def render(seg):
    name, t0, t1 = seg
    out = f"{SEG}/{name}.mp4"
    need_s = name in ("s2", "s5", "s6")
    S = build_stencil() if need_s else None
    gen = {"s1": lambda: seg_s1(t0, t1), "s2": lambda: seg_s2(t0, t1, S), "s3": lambda: seg_s3(t0, t1),
           "s4": lambda: seg_s4(t0, t1), "s5": lambda: seg_s5(t0, t1, S), "s6": lambda: seg_s6(t0, t1, S)}[name]()
    n = int(round((t1 - t0) * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-frames:v", str(n), "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    count = 0
    for f in gen:
        if count >= n:
            break
        p.stdin.write(f.convert("RGB").tobytes())
        count += 1
    p.stdin.close()
    p.wait()
    return f"{name}: {count} frames"


if __name__ == "__main__":
    todo = [s for s in SEGMENTS if not ONLY or s[0] in ONLY]
    with ProcessPoolExecutor(4) as ex:
        for r in ex.map(render, todo):
            print(r, flush=True)
    lst = f"{SEG}/list.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{name}.mp4'\n" for name, _, _ in SEGMENTS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT], check=True)
    print("wrote", OUT)
