"""Render Bali Diary 01 (Mumbai -> Bali on Malaysia Airlines) as a 9:16 reel.

usage: python3 render_bali01.py <workdir> <out.mp4>
<workdir> must contain drive/ (source clips) and fonts/ (see style_frames.py).
"""
import math, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

BASE, OUT = sys.argv[1], sys.argv[2]
SEG = os.path.join(BASE, "segments")
os.makedirs(SEG, exist_ok=True)
W, H, FPS = 1080, 1920, 30
TOTAL = 52.0
SW, SH = 1188, 2112  # footage rendered 10% larger than frame for push-ins

F = BASE + "/fonts/"
caveat = lambda s: ImageFont.truetype(F + "f1.ttf", s)
corm_i = lambda s: ImageFont.truetype(F + "g1.ttf", s)
corm = lambda s: ImageFont.truetype(F + "g2.ttf", s)
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

CLIP = {
    "A": "drive/DJI_20261006234428_0017_D~2.mp4",
    "B": "drive/DJI_20261007012656_0018_D~2.mp4",
    "C": "drive/DJI_20261007044857_0019_D.MP4",
    "D": "drive/DJI_20261007044927_0020_D.MP4",
    "E": "drive/DJI_20261007073147_0039_D.MP4",
}

# Same warm grade as the approved style frames, plus highlight bloom.
GRADE = (
    "eq=saturation=0.9,format=gbrp,"
    "lutrgb=r='clip(val*1.145+25.5,0,255)':g='clip(val*1.08+20.9,0,255)':b='clip(val*0.972+16.6,0,255)',"
    "split[g0][g1];[g1]scale=iw/4:-2,lutrgb=r='max(val-170,0)*3':g='max(val-170,0)*3':b='max(val-170,0)*3',"
    "gblur=sigma=8,scale={w}:{h}[gl];[g0][gl]blend=all_mode=screen:all_opacity=0.35,format=yuv420p"
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
    c = 1.4
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def paper_bg(c1, c2, seed=7):
    g = np.linspace(0, 1, H)[:, None, None]
    a = np.array(c1)[None, None] * (1 - g) + np.array(c2)[None, None] * g
    a = np.broadcast_to(a, (H, W, 3)).copy()
    rng = np.random.default_rng(seed)
    tex = Image.fromarray(rng.normal(128, 40, (H // 3, W // 3)).clip(0, 255).astype(np.uint8))
    tex = np.asarray(tex.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32)
    a += ((tex - 128) / 128 * 5)[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")


def with_shadow(layer, offset=(0, 10), blur=14, alpha=60, color=(120, 80, 60)):
    """Return a padded RGBA of layer with a soft paper shadow under it."""
    p = blur * 2 + max(abs(offset[0]), abs(offset[1]))
    out = Image.new("RGBA", (layer.width + 2 * p, layer.height + 2 * p), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0)
    m.paste(layer.getchannel("A"), (p + offset[0], p + offset[1]))
    sh = Image.new("RGBA", out.size, color + (0,))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255))
    out.alpha_composite(sh)
    out.alpha_composite(layer, (p, p))
    return out


def shadow_onto(base, mask, offset=(0, 14), blur=26, alpha=70, color=(120, 80, 60)):
    sh = Image.new("RGBA", base.size, color + (0,))
    m = Image.new("L", base.size, 0)
    m.paste(mask, offset)
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255))
    base.alpha_composite(sh)


def make_pill(text, font, fg=INK, bg=CREAM, pad=(34, 18), rot=0, alpha=235):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + pad[0] * 2, th + pad[1] * 2
    layer = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((4, 4, 4 + w, 4 + h), radius=h // 2, fill=bg + (alpha,))
    ld.text((4 + w / 2, 4 + h / 2), text, font=font, fill=fg, anchor="mm")
    if rot:
        layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    return with_shadow(layer)


def text_img(text, font, fill, shadow=None):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.textbbox((0, 0), text, font=font)
    im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), text, font=font, fill=fill)
    if shadow:
        return with_shadow(im, offset=(0, 3), blur=10, alpha=shadow, color=(70, 40, 30))
    return im


def letters(text, font, fill, tracking, cx, cy, shadow=None):
    """Per-letter images positioned for a letter-spaced line centred at (cx, cy)."""
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    out, widths = [], []
    for ch in text:
        widths.append(font.size * 0.9 if ch == "→" else d.textlength(ch, font=font))
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        if ch != " ":
            im = Image.new("RGBA", (int(w) + 40, int(font.size * 1.6)), (0, 0, 0, 0))
            dd = ImageDraw.Draw(im)
            my = im.height / 2
            if ch == "→":
                lw = max(2, font.size // 30)
                dd.line((20, my, 20 + w, my), fill=fill, width=lw)
                dd.line((20 + w - font.size * 0.22, my - font.size * 0.16, 20 + w, my), fill=fill, width=lw)
                dd.line((20 + w - font.size * 0.22, my + font.size * 0.16, 20 + w, my), fill=fill, width=lw)
            else:
                dd.text((20, my), ch, font=font, fill=fill, anchor="lm")
            if shadow:
                im = with_shadow(im, offset=(0, 3), blur=8, alpha=shadow, color=(70, 40, 30))
            out.append((im, x + w / 2, cy))
        x += w + tracking
    return out


def paste_center(base, im, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.002:
        return
    if abs(scale - 1) > 0.002:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.BILINEAR)
    if alpha < 0.998:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


def draw_letters(base, items, t, t0, stagger=0.045, dur=0.45, rise=14):
    for k, (im, x, y) in enumerate(items):
        a = ease_out((t - t0 - k * stagger) / dur)
        paste_center(base, im, x, y + (1 - a) * rise, a)


def plane_icon(size, color):
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    d.ellipse((c - s * 0.06, s * 0.08, c + s * 0.06, s * 0.92), fill=color)
    d.polygon([(c, s * 0.38), (s * 0.04, s * 0.58), (s * 0.04, s * 0.65), (c, s * 0.55), (s * 0.96, s * 0.65), (s * 0.96, s * 0.58)], fill=color)
    d.polygon([(c, s * 0.78), (s * 0.3, s * 0.9), (s * 0.3, s * 0.94), (c, s * 0.88), (s * 0.7, s * 0.94), (s * 0.7, s * 0.9)], fill=color)
    return im


PLANE = plane_icon(70, INK + (255,))


def make_blob(r, color, strength):
    m = Image.new("L", (r * 4, r * 4), 0)
    ImageDraw.Draw(m).ellipse((r, r, 3 * r, 3 * r), fill=strength)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.6))
    im = Image.new("RGBA", m.size, color + (0,))
    im.putalpha(m)
    return im


LEAK = make_blob(420, (255, 206, 150), 200)


def make_cloud(scale):
    w, h = int(300 * scale), int(150 * scale)
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for ex, ey, er in [(0.3, 0.62, 0.22), (0.52, 0.45, 0.3), (0.74, 0.62, 0.2)]:
        d.ellipse(((ex - er) * w, ey * h - er * w, (ex + er) * w, ey * h + er * w), fill=255)
    d.rounded_rectangle((0.1 * w, 0.55 * h, 0.9 * w, 0.92 * h), radius=int(0.18 * h), fill=255)
    im = Image.new("RGBA", (w, h), (255, 250, 242, 0))
    im.putalpha(m)
    return with_shadow(im, offset=(0, 8), blur=12, alpha=55)


# ---------------------------------------------------------------- route map
ROUTE = [(170, 900), (540, 860), (900, 940)]


def route_path(pts):
    path = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - 90
        for t in np.linspace(0, 1, 300, endpoint=i == len(pts) - 2):
            path.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1,
                         (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1))
    cum = [0.0]
    for a, b in zip(path, path[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    L = cum[-1]
    frac = [c / L for c in cum]
    dots, acc = [], 0.0
    for i in range(1, len(path)):
        acc += cum[i] - cum[i - 1]
        if acc >= 24:
            acc = 0
            dots.append((path[i], frac[i]))
    return path, frac, dots


PATH, FRAC, DOTS = route_path(ROUTE)
KUL_FRAC = FRAC[299]


def path_at(f):
    i = int(np.searchsorted(FRAC, clamp(f)))
    i = min(max(i, 3), len(PATH) - 4)
    (x0, y0), (x1, y1) = PATH[i - 3], PATH[i + 3]
    return PATH[i], math.degrees(math.atan2(y1 - y0, x1 - x0))


CITY = [("Mumbai", BLUSH), ("Kuala Lumpur", POWDER), ("Bali", BUTTER)]
CITY_LABELS = [text_img(n, corm_i(46), INK) for n, _ in CITY]


def draw_route(base, draw_frac, city_t, t, plane_frac=None, pulse=None):
    """draw_frac: how much of the dotted line is visible; city_t: appear times per city."""
    d = ImageDraw.Draw(base)
    for (x, y), f in DOTS:
        if f <= draw_frac:
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(196, 150, 130, 255))
    for k, ((x, y), (name, col)) in enumerate(zip(ROUTE, CITY)):
        a = ease_back((t - city_t[k]) / 0.4)
        if a <= 0:
            continue
        r = 18 * a
        d.ellipse((x - r - 6, y - r - 6, x + r + 6, y + r + 6), fill=(255, 255, 255, 255))
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,))
        paste_center(base, CITY_LABELS[k], x, y + 56, clamp(a))
    if pulse:
        k, pt = pulse
        p = clamp((t - pt) / 0.9)
        if 0 < p < 1:
            x, y = ROUTE[k]
            r = 22 + 70 * ease_out(p)
            ring = Image.new("RGBA", base.size, (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse((x - r, y - r, x + r, y + r), outline=(196, 150, 130, int(200 * (1 - p))), width=4)
            base.alpha_composite(ring)
    if plane_frac is not None:
        (px, py), ang = path_at(plane_frac)
        pl = PLANE.rotate(-ang - 90, expand=True, resample=Image.BICUBIC)
        paste_center(base, pl, px, py)


# ---------------------------------------------------------------- footage segments
class Seg:
    def __init__(self, name, clip, ss, tl_dur, speed=1.0, x=1312, pan=None, size=(SW, SH), cw=1215):
        self.name, self.clip, self.ss, self.tl_dur = name, clip, ss, tl_dur
        self.speed, self.x, self.pan, self.size, self.cw = speed, x, pan, size, cw
        self.path = os.path.join(SEG, name + ".mp4")

    def render(self):
        src_dur = self.tl_dur * self.speed + 0.2
        if isinstance(self.pan, str):
            cx = f"'{self.pan}'"
        elif self.pan:
            x0, x1 = self.pan
            cx = f"'{x0}+({x1}-{x0})*min(t/{self.tl_dur},1)'"
        else:
            cx = str(self.x)
        w, h = self.size
        vf = (f"[0:v:0]setpts=(PTS-STARTPTS)/{self.speed},fps={FPS},crop={self.cw}:2160:{cx}:0,"
              f"scale={w}:{h}:flags=lanczos," + GRADE.format(w=w, h=h))
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(self.ss), "-t", str(src_dur), "-i", os.path.join(BASE, CLIP[self.clip]),
               "-filter_complex", vf, "-an", "-c:v", "libx264", "-crf", "12", "-preset", "veryfast", self.path]
        subprocess.run(cmd, check=True)
        return self.name


class Reader:
    def __init__(self, seg):
        self.w, self.h = seg.size
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", seg.path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE)
        self.idx, self.frame = -1, None

    def get(self, i):
        n = self.w * self.h * 3
        while self.idx < i:
            buf = self.p.stdout.read(n)
            if len(buf) < n:
                break
            self.frame = Image.frombuffer("RGB", (self.w, self.h), buf, "raw", "RGB", 0, 1)
            self.idx += 1
        return self.frame


# ---------------------------------------------------------------- scenes
class Footage:
    def __init__(self, seg, zoom=(1.0, 1.06)):
        self.seg, self.zoom, self.reader = seg, zoom, None

    def frame(self, tl, dur):
        if self.reader is None:
            self.reader = Reader(self.seg)
        im = self.reader.get(int(round(tl * FPS)))
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * ease_io(tl / dur)
        vw = W * 1.1 / z
        vh = H * 1.1 / z
        x0, y0 = (SW - vw) / 2, (SH - vh) / 2
        return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + vw, y0 + vh)).convert("RGBA")


class Hook:
    """Sunrise wing inside a paper airplane window, title types on."""

    def __init__(self, seg):
        self.seg, self.reader = seg, None
        self.bg = paper_bg((250, 224, 208), (253, 238, 228))
        b = self.bg
        b.alpha_composite(make_blob(420, (255, 214, 160), 120), (980 - 840, 160 - 840))
        b.alpha_composite(make_blob(300, (255, 190, 140), 60), (300 - 600, 700 - 600))
        b.alpha_composite(make_blob(380, BLUSH, 90), (80 - 760, 1700 - 760))
        self.ww, self.wh = 720, 1000
        gw, gh = self.ww + 140 + 120, self.wh + 140 + 120
        self.gox, self.goy = 130, 130  # window origin inside group
        frame = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
        for i, (pad, col) in enumerate([(70, CREAM), (40, (240, 226, 210))]):
            m = Image.new("L", (self.ww + pad * 2, self.wh + pad * 2), 0)
            ImageDraw.Draw(m).rounded_rectangle((0, 0, m.width - 1, m.height - 1), radius=330 + pad, fill=255)
            if i == 0:
                shadow_onto(frame, m, (self.gox - pad, self.goy - pad + 22), blur=36, alpha=90)
            lay = Image.new("RGBA", m.size, col + (255,))
            lay.putalpha(m)
            frame.alpha_composite(lay, (self.gox - pad, self.goy - pad))
        self.group_bg = frame
        vm = Image.new("L", (self.ww, self.wh), 0)
        ImageDraw.Draw(vm).rounded_rectangle((0, 0, self.ww - 1, self.wh - 1), radius=330, fill=255)
        self.vmask = vm
        inner = Image.new("L", (self.ww, self.wh), 0)
        ImageDraw.Draw(inner).rounded_rectangle((10, 10, self.ww - 11, self.wh - 11), radius=320, fill=255)
        ring = ImageChops.subtract(vm, inner.filter(ImageFilter.GaussianBlur(18)))
        glass = Image.new("RGBA", (self.ww, self.wh), (90, 60, 50, 0))
        glass.putalpha(ring.point(lambda v: v * 120 // 255))
        sheen = Image.new("L", (self.ww, self.wh), 0)
        ImageDraw.Draw(sheen).polygon([(self.ww * 0.55, 0), (self.ww * 0.75, 0), (self.ww * 0.25, self.wh), (self.ww * 0.05, self.wh)], fill=40)
        sheen = ImageChops.multiply(sheen.filter(ImageFilter.GaussianBlur(30)), vm)
        sl = Image.new("RGBA", (self.ww, self.wh), (255, 245, 230, 0))
        sl.putalpha(sheen)
        glass.alpha_composite(sl)
        self.glass = glass
        self.cy = 260 + self.wh / 2
        self.kicker = letters("FLIGHT DIARY  ·  01", jost(34), INK, 7, W / 2, 150)
        self.title = letters("MUMBAI → BALI", corm(96), INK, 14, W / 2, 1400)
        self.via = text_img("via Kuala Lumpur", corm_i(58), (150, 92, 70))
        self.codes = [text_img(c, jost(32), INK) for c in ("BOM", "KUL", "DPS")]

    def frame(self, tl, dur):
        if self.reader is None:
            self.reader = Reader(self.seg)
        base = self.bg.copy()
        v = self.reader.get(int(round(tl * FPS)))
        z = 1.0 + 0.08 * ease_io(tl / dur)
        vw, vh = v.width / z, v.height / z
        x0, y0 = (v.width - vw) / 2, (v.height - vh) / 2
        view = v.resize((self.ww, self.wh), Image.BILINEAR, box=(x0, y0, x0 + vw, y0 + vh)).convert("RGBA")
        view.putalpha(self.vmask)
        g = self.group_bg.copy()
        g.alpha_composite(view, (self.gox, self.goy))
        g.alpha_composite(self.glass, (self.gox, self.goy))
        s = 0.94 + 0.06 * ease_out(tl / 1.2)
        paste_center(base, g, W / 2, self.cy + (g.height / 2 - self.goy - self.wh / 2) * s, 1.0, s)
        draw_letters(base, self.kicker, tl, 0.15, 0.03)
        draw_letters(base, self.title, tl, 0.5, 0.06, 0.5, 18)
        a = ease_out((tl - 1.4) / 0.5)
        paste_center(base, self.via, W / 2, 1490 + (1 - a) * 12, a)
        # mini route
        d = ImageDraw.Draw(base)
        pts = [(250, 1640), (540, 1640), (830, 1640)]
        p = ease_io((tl - 1.6) / 1.0)
        for (x, y) in pts[:-1]:
            for k in range(int(x) + 30, int(x) + 262, 22):
                if (k - 250) / 580 <= p:
                    d.ellipse((k - 4, y - 4, k + 4, y + 4), fill=(200, 150, 130, 255))
        for i, ((x, y), col) in enumerate(zip(pts, [BLUSH, MINT, BUTTER])):
            a = ease_back((tl - 1.6 - i * 0.45) / 0.35)
            if a > 0:
                r = 16 * a
                d.ellipse((x - r - 5, y - r - 5, x + r + 5, y + r + 5), fill=CREAM + (255,))
                d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,))
                paste_center(base, self.codes[i], x, y + 50, clamp(a))
        if p > 0:
            px = 250 + 580 * p
            pl = PLANE.resize((54, 54), Image.BICUBIC).rotate(-90, expand=True, resample=Image.BICUBIC)
            paste_center(base, pl, px, 1640)
        return base


class MapScene:
    """Pastel paper map. mode 'intro' draws the route, mode 'layover' flies BOM->KUL."""

    def __init__(self, mode):
        self.mode = mode
        b = paper_bg((223, 238, 228), CREAM, seed=11)
        b.alpha_composite(make_blob(380, (255, 236, 200), 120), (820 - 760, 520 - 760))
        b.alpha_composite(make_blob(320, BLUSH, 70), (100 - 640, 1600 - 640))
        self.bg = b
        self.clouds = [(make_cloud(1.0), 120, 1250, 9), (make_cloud(0.7), 760, 1420, -7), (make_cloud(0.55), 860, 640, 6)]
        if mode == "intro":
            self.kicker = letters("2 FLIGHTS  ·  1 LAYOVER", jost(36), INK, 9, W / 2, 330)
            self.title = letters("MUMBAI → BALI", corm(92), INK, 12, W / 2, 470)
            self.sub = text_img("via Kuala Lumpur", corm_i(58), (150, 92, 70))
        else:
            self.kicker = letters("LAYOVER", jost(40), INK, 18, W / 2, 330)
            self.title = letters("Kuala Lumpur", corm_i(110), INK, 2, W / 2, 470)
            self.sub = text_img("chhota sa break", caveat(58), (150, 92, 70))

    def frame(self, tl, dur):
        base = self.bg.copy()
        for im, x, y, sp in self.clouds:
            paste_center(base, im, x + sp * tl, y)
        draw_letters(base, self.kicker, tl, 0.1, 0.025)
        draw_letters(base, self.title, tl, 0.3, 0.05)
        a = ease_out((tl - 0.9) / 0.5)
        paste_center(base, self.sub, W / 2, 580 + (1 - a) * 12, a)
        if self.mode == "intro":
            f = ease_io((tl - 0.4) / 2.0)
            draw_route(base, f, [0.25, 0.4 + 2.0 * 0.45, 2.35], tl, plane_frac=f if tl > 0.4 else None)
        else:
            f = KUL_FRAC * ease_io((tl - 0.3) / 1.7)
            draw_route(base, 1.0, [-1, -1, -1], tl, plane_frac=f, pulse=(1, 2.0))
        return base


class Outro:
    """Paper waves rise over the last shot, sun comes up, plane reaches Bali."""

    def __init__(self, under_dur):
        self.under_dur = under_dur
        b = paper_bg((223, 238, 228), CREAM, seed=5)
        b.alpha_composite(make_blob(380, (255, 236, 200), 120), (820 - 760, 620 - 760))
        self.bg = b
        specs = [
            (1150, 70, 0.0045, 0.0, (247, 236, 214)),
            (1240, 80, 0.0040, 1.3, BUTTER),
            (1330, 75, 0.0050, 2.1, (248, 200, 170)),
            (1420, 70, 0.0042, 3.0, BLUSH),
            (1520, 65, 0.0048, 4.2, (240, 225, 210)),
            (1630, 60, 0.0040, 5.0, MINT),
            (1740, 50, 0.0052, 0.7, (226, 190, 200)),
        ]
        self.waves = []
        for y0, amp, freq, ph, col in specs:
            top = int(y0 - amp - 40 - 60)
            poly = [(x, y0 + amp * math.sin(x * freq + ph) + 25 * math.sin(x * freq * 2.3 + ph * 1.7) - top) for x in range(-10, W + 11, 6)]
            hh = H - top + 400
            poly += [(W + 10, hh), (-10, hh)]
            lay = Image.new("RGBA", (W, hh), (0, 0, 0, 0))
            m = Image.new("L", (W, hh), 0)
            ImageDraw.Draw(m).polygon(poly, fill=255)
            sm = Image.new("L", (W, hh), 0)
            sm.paste(m, (0, -10))
            sh = Image.new("RGBA", (W, hh), (120, 80, 60, 0))
            sh.putalpha(sm.filter(ImageFilter.GaussianBlur(18)).point(lambda v: v * 85 // 255))
            lay.alpha_composite(sh)
            fill = Image.new("RGBA", (W, hh), col + (255,))
            fill.putalpha(m)
            lay.alpha_composite(fill)
            edge = Image.new("L", (W, hh), 0)
            ImageDraw.Draw(edge).line(poly[:-2], fill=110, width=3)
            el = Image.new("RGBA", (W, hh), (255, 255, 255, 0))
            el.putalpha(edge.filter(ImageFilter.GaussianBlur(1)))
            lay.alpha_composite(el)
            self.waves.append((lay, top))
        sm = Image.new("L", (140, 140), 0)
        ImageDraw.Draw(sm).ellipse((0, 0, 139, 139), fill=255)
        sun = Image.new("RGBA", (140, 140), SUN + (255,))
        sun.putalpha(sm)
        self.sun = with_shadow(sun, offset=(0, 14), blur=18, alpha=60)
        palm = Image.new("RGBA", (300, 320), (0, 0, 0, 0))
        pd = ImageDraw.Draw(palm)
        px, py = 150, 310
        trunk = [(px + 10 * math.sin(t / 40), py - t) for t in range(0, 200, 4)]
        pd.line(trunk, fill=SAGE, width=18, joint="curve")
        tx, ty = trunk[-1]
        for a, l in [(-160, 110), (-120, 120), (-60, 120), (-20, 110), (-90, 90)]:
            r = math.radians(a)
            ex, ey = tx + l * math.cos(r), ty + l * math.sin(r) + 30
            pd.polygon([(tx, ty), ((tx + ex) / 2 + 18 * math.sin(r), (ty + ey) / 2 - 22), (ex, ey), ((tx + ex) / 2, (ty + ey) / 2 + 6)], fill=(150, 192, 165))
        self.palm = with_shadow(palm, offset=(8, 10), blur=10, alpha=70)
        self.kicker = letters("NEXT STOP", jost(44), INK, 18, W / 2, 250)
        self.bali = text_img("Bali", corm_i(200), INK)
        self.follow = text_img("baaki trip ke liye follow karte raho", caveat(58), INK)

    def frame(self, tl, dur, under=None):
        bg_a = ease_io((tl - 0.45) / 0.7)
        if under is not None and bg_a < 1:
            base = under.copy()
            if bg_a > 0:
                base = Image.blend(base, self.bg, bg_a)
        else:
            base = self.bg.copy()
        n = len(self.waves)
        # sky elements (behind waves)
        a = ease_out((tl - 1.1) / 1.0)
        paste_center(base, self.sun, 890, 700 + (1 - a) * 160, a)
        if tl > 0.9:
            draw_route(base, ease_io((tl - 0.9) / 0.6), [0.9, 1.0, 1.1], tl,
                       plane_frac=KUL_FRAC + (1 - KUL_FRAC) * 0.96 * ease_io((tl - 1.3) / 2.0), pulse=(2, 3.3))
        draw_letters(base, self.kicker, tl, 1.2, 0.05)
        a = ease_out((tl - 1.8) / 0.8)
        paste_center(base, self.bali, W / 2, 400 + (1 - a) * 30, a, 0.92 + 0.08 * a)
        a = ease_out((tl - 2.7) / 0.6)
        paste_center(base, self.follow, W / 2, 545 + (1 - a) * 10, a)
        for i, (lay, top) in enumerate(self.waves):
            p = ease_out((tl - 0.07 * i) / 1.1)
            y = top + (1 - p) * (H - top + 80)
            if y < H:
                base.alpha_composite(lay, (0, int(y)))
            if i == 1:
                a = ease_back((tl - 1.6) / 0.6)
                if a > 0:
                    pm = self.palm.resize((self.palm.width, max(1, int(self.palm.height * a))), Image.BILINEAR)
                    base.alpha_composite(pm, (110 - self.palm.width // 2, int(1385 - pm.height + (1 - p) * (H - top + 80))))
        return base


# ---------------------------------------------------------------- overlays (timeline-level)
class Sticker:
    def __init__(self, im, x, y, t0, t1):
        self.im, self.x, self.y, self.t0, self.t1 = im, x, y, t0, t1

    def draw(self, base, t):
        if t < self.t0 or t > self.t1:
            return
        a_in = ease_back((t - self.t0) / 0.4)
        a_out = clamp((self.t1 - t) / 0.25)
        s = (0.8 + 0.2 * a_in) * (0.95 + 0.05 * a_out)
        paste_center(base, self.im, self.x, self.y, clamp(a_in) * a_out, s)


class Letters:
    def __init__(self, items, t0, t1, stagger=0.05):
        self.items, self.t0, self.t1, self.stagger = items, t0, t1, stagger

    def draw(self, base, t):
        if t < self.t0 or t > self.t1:
            return
        a_out = clamp((self.t1 - t) / 0.4)
        for k, (im, x, y) in enumerate(self.items):
            a = ease_out((t - self.t0 - k * self.stagger) / 0.5) * a_out
            paste_center(base, im, x, y + (1 - a) * 14, a)


class Leak:
    def __init__(self, tc, dur=1.0, y=500, direction=1):
        self.tc, self.dur, self.y, self.dir = tc, dur, y, direction

    def draw(self, base, t):
        p = (t - (self.tc - self.dur / 2)) / self.dur
        if not 0 < p < 1:
            return
        a = math.sin(math.pi * p) * 0.85
        x = W / 2 + self.dir * (p - 0.5) * 900
        paste_center(base, LEAK, x, self.y, a)


class Doodles:
    """Crescent moon and drifting z's for the sleepy screen shot."""

    def __init__(self, t0, t1):
        self.t0, self.t1 = t0, t1
        m = Image.new("L", (130, 130), 0)
        ImageDraw.Draw(m).ellipse((5, 5, 125, 125), fill=255)
        ImageDraw.Draw(m).ellipse((40, -10, 150, 100), fill=0)
        moon = Image.new("RGBA", (130, 130), BUTTER + (255,))
        moon.putalpha(m)
        self.moon = with_shadow(moon, offset=(0, 6), blur=10, alpha=80)
        self.z = [text_img("z", caveat(s), CREAM, shadow=120) for s in (56, 72, 92)]

    def draw(self, base, t):
        if t < self.t0 or t > self.t1:
            return
        tl = t - self.t0
        a = ease_out(tl / 0.6) * clamp((self.t1 - t) / 0.3)
        paste_center(base, self.moon, 860, 330 + 8 * math.sin(tl * 2), a)
        for i, im in enumerate(self.z):
            ph = (tl * 0.6 + i * 0.33) % 1.0
            za = math.sin(math.pi * ph) * a
            paste_center(base, im, 720 - i * 60 + 30 * math.sin(ph * 6), 560 - ph * 220, za)


# ---------------------------------------------------------------- build timeline
def build():
    segs = {
        "hook": Seg("hook", "D", 2.0, 3.5, x=1384, size=(792, 1100), cw=1555),
        "A1": Seg("A1", "A", 0.0, 5.3, speed=1.5, x=1312),
        "A2": Seg("A2", "A", 8.4, 4.4, pan="1192+730*clip((t-1.6)/0.6,0,1)"),
        "B1": Seg("B1", "B", 0.0, 2.0, x=543),
        "B2": Seg("B2", "B", 4.5, 2.5, speed=0.625, x=1150),
        "B3": Seg("B3", "B", 8.6, 2.9, x=820),
        "B5": Seg("B5", "B", 48.0, 4.0, x=600),
        "C": Seg("C", "C", 6.5, 4.8, x=1312),
        "D": Seg("D", "D", 3.5, 7.5, pan=(1100, 2300)),
        "E1": Seg("E1", "E", 7.5, 4.2, x=1444),
        "E2": Seg("E2", "E", 14.0, 4.4, x=1181),
    }
    todo = [s for s in segs.values() if not os.path.exists(s.path) or os.environ.get("RESEG")]
    with ThreadPoolExecutor(4) as ex:
        for n in ex.map(lambda s: s.render(), todo):
            print("segment", n, flush=True)

    # (start, end, scene, transition-in duration, leak)
    scenes = [
        (0.0, 3.0, Hook(segs["hook"]), 0),
        (3.0, 6.0, MapScene("intro"), 0.5),
        (6.0, 11.0, Footage(segs["A1"], (1.0, 1.04)), 0.5),
        (11.0, 15.0, Footage(segs["A2"], (1.0, 1.08)), 0.3),
        (15.0, 17.0, Footage(segs["B1"], (1.0, 1.05)), 0.4),
        (17.0, 19.5, Footage(segs["B2"], (1.03, 1.0)), 0),
        (19.5, 22.4, Footage(segs["B3"], (1.0, 1.06)), 0),
        (22.4, 26.0, Footage(segs["B5"], (1.0, 1.06)), 0),
        (26.0, 30.0, Footage(segs["C"], (1.0, 1.06)), 0.4),
        (30.0, 37.0, Footage(segs["D"], (1.0, 1.05)), 0.8),
        (37.0, 40.0, MapScene("layover"), 0.5),
        (40.0, 44.0, Footage(segs["E1"], (1.0, 1.05)), 0.5),
        (44.0, 47.0, Footage(segs["E2"], (1.0, 1.05)), 0.2),
        (47.0, 52.0, Outro(1.4), "waves"),
    ]
    P = lambda *a, **k: make_pill(*a, **k)
    overlays = [
        Leak(3.0, 1.0, 400), Leak(15.0, 0.9, 300, -1), Leak(30.0, 1.4, 520), Leak(40.0, 1.0, 400, -1),
        # flight 1 boarding
        Sticker(P("FLIGHT 1  ·  MUMBAI TO KL", jost(34), pad=(40, 20)), W / 2, 210, 6.3, 10.85),
        Sticker(P("midnight boarding", corm_i(46), bg=PEACH, pad=(30, 10), alpha=225), W / 2, 305, 6.7, 10.85),
        Sticker(P("batik kebaya", caveat(64), bg=MINT, rot=-5), 300, 560, 11.5, 14.85),
        Sticker(P("Malaysia wali feel ~", caveat(54), bg=BLUSH, rot=3), 340, 670, 12.1, 14.85),
        # meal
        Sticker(P("1:00 am dinner", corm_i(48), bg=PEACH, pad=(32, 12), alpha=230), W / 2, 210, 15.3, 25.85),
        Sticker(P("Maine veg liya,", jost(54), pad=(38, 16), alpha=240), W / 2, 1330, 16.9, 19.8),
        Sticker(P("husband ne non-veg", jost(54), pad=(38, 16), alpha=240), W / 2, 1430, 17.3, 19.8),
        Sticker(P("paratha", caveat(66), bg=BUTTER, rot=6), 300, 1180, 19.7, 22.35),
        Sticker(P("veg meal", caveat(58), bg=MINT, rot=-5), 770, 560, 20.2, 25.85),
        Sticker(P("theek-thaak ~", caveat(50), bg=BLUSH, rot=-3), 790, 660, 20.6, 25.85),
        Sticker(P("rice + curry", caveat(58), bg=BUTTER, rot=4), 330, 1000, 22.6, 25.85),
        # old screens
        Doodles(26.2, 29.9),
        Sticker(P("purane screens", caveat(62), bg=MINT, rot=-4), 330, 300, 26.4, 29.85),
        Sticker(P("letdown :(", caveat(62), bg=BLUSH, rot=4), 360, 420, 27.6, 29.85),
        # sunrise
        Letters(letters("subah ka view", corm_i(84), CREAM, 3, W / 2, 1300, shadow=150), 32.0, 36.8, 0.06),
        # flight 2
        Sticker(P("FLIGHT 2  ·  KL TO BALI", jost(34), pad=(40, 20)), W / 2, 210, 40.3, 46.85),
        Sticker(P("ekdum upgrade!", caveat(64), bg=BUTTER, rot=-5), 760, 520, 41.0, 43.85),
        Sticker(P("naya plane", caveat(60), bg=MINT, rot=4), 300, 520, 44.2, 46.85),
        Sticker(P("bade screens", caveat(60), bg=BLUSH, rot=-4), 330, 630, 44.6, 46.85),
    ]
    return scenes, overlays


def main():
    scenes, overlays = build()
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-vf", "noise=alls=6:allf=t,format=yuv420p", "-c:v", "libx264", "-crf", "19", "-maxrate", "18M", "-bufsize", "36M", "-preset", "medium",
         "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    nframes = int(TOTAL * FPS)
    for fi in range(nframes):
        t = fi / FPS
        k = max(i for i, s in enumerate(scenes) if s[0] <= t + 1e-9)
        st, en, sc, tr = scenes[k]
        tl = t - st
        prev = scenes[k - 1] if k > 0 else None
        if tr == "waves":
            under = None
            if tl < sc.under_dur and prev:
                under = prev[2].frame(t - prev[0], prev[1] - prev[0])
            img = sc.frame(tl, en - st, under)
        else:
            img = sc.frame(tl, en - st)
            if tr and tl < tr and prev:
                a = ease_io(tl / tr)
                pimg = prev[2].frame(t - prev[0], prev[1] - prev[0])
                img = Image.blend(pimg, img, a)
        for o in overlays:
            o.draw(img, t)
        enc.stdin.write(img.convert("RGB").tobytes())
        if fi % 60 == 0:
            print(f"frame {fi}/{nframes}", flush=True)
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    main()
