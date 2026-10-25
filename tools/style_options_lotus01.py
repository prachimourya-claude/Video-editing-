"""Three alternative looks for the Lotus stencil reel (hook + end card each), for the client to pick from.

  A  Brand Beige   - PSOne Labs' own palette: warm beige, terracotta and olive, botanical line art, rounded photo card
(no logo block on the end cards: the reel is posted on the brand's own page, so they end on "Order now!" + "DM to order")
  B  Rose & Gold   - blush to deep rose, gold mandala corners, footage in a gold ring framed by lotus petals
  C  Mint Pop      - mint and peach blobs, polaroid photo with washi tape, sticker badges, handwritten notes

usage: cd tools && python3 style_options_lotus01.py <workdir> <outdir>   (same <workdir> as style_frames_lotus01.py)
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import render_diwali01 as R
import style_frames_teaser01 as T
import style_frames_lotus01 as L
from render_diwali01 import W, H, paste_center, text_mask, blob

BASE, OUTDIR = sys.argv[1], sys.argv[2]
F = BASE + "/fonts/"
font = lambda name, s: ImageFont.truetype(F + name, s)

ROSE_D = (128, 22, 70)
ROSE = (214, 92, 138)
BLUSH = (252, 226, 232)
MINT = (210, 238, 224)
MINT_D = (46, 110, 90)
PEACH = (255, 210, 190)
PINK = (244, 150, 180)


def txt(t, f, fill, shadow=0, track=0):
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
    return R.with_shadow(im, offset=(0, 4), blur=8, alpha=shadow, color=(60, 30, 30)) if shadow else im


def grad(c1, c2, seed=1, c3=None):
    g = np.linspace(0, 1, H)
    stops = [c1, c2] if c3 is None else [c1, c2, c3]
    pos = np.linspace(0, 1, len(stops))
    col = np.stack([np.interp(g, pos, [s[c] for s in stops]) for c in range(3)], 1)
    a = np.broadcast_to(col[:, None, :], (H, W, 3)).copy()
    rng = np.random.default_rng(seed)
    a += rng.normal(0, 2.2, (H, W))[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")


def lotus_icon(col, edge, scale=1.0):
    lot = Image.new("RGBA", (300, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(lot)
    for ang, ln in ((-68, 95), (68, 95), (-36, 125), (36, 125), (0, 150)):
        th = math.radians(ang)
        side = [(30 * math.sin(math.pi * u) ** 0.9 * (1 - 0.3 * u), ln * u) for u in np.linspace(0, 1, 30)]
        pts = side + [(-x, y) for x, y in reversed(side)]
        pts = [(150 + x * math.cos(th) + y * math.sin(th), 160 + x * math.sin(th) - y * math.cos(th)) for x, y in pts]
        d.polygon(pts, fill=col + (255,), outline=edge + (255,), width=3)
    return lot.resize((int(300 * scale), int(170 * scale)), Image.LANCZOS)


def photo(name, t, src, s, size):
    """Crop the clip still around src at scale s into a size=(w, h) photo."""
    st = L.still(name, t)
    w, h = size
    im = st.resize((int(W * s), int(H * s)), Image.LANCZOS)
    x0, y0 = int(src[0] * s - w / 2), int(src[1] * s - h / 2)
    return im.crop((x0, y0, x0 + w, y0 + h))


def rounded(im, r, border=0, bcol=(255, 255, 255)):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=255)
    out = Image.new("RGBA", (im.width + 2 * border, im.height + 2 * border), (0, 0, 0, 0))
    if border:
        ImageDraw.Draw(out).rounded_rectangle((0, 0, out.width - 1, out.height - 1), radius=r + border, fill=bcol + (255,))
    im = im.copy()
    im.putalpha(m)
    out.alpha_composite(im, (border, border))
    return out


def branch(base, x, y, ang, length, col, alpha=150, flip=1):
    """Botanical line-art sprig: a curved stem with paired leaves."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pts = []
    for k in range(41):
        u = k / 40
        a = math.radians(ang) + flip * 0.5 * u
        pts.append((x + length * u * math.cos(a), y + length * u * math.sin(a)))
    d.line(pts, fill=col + (alpha,), width=3)
    for k in range(4, 40, 6):
        px, py = pts[k]
        a = math.atan2(pts[k + 1][1] - py, pts[k + 1][0] - px)
        for side in (-1, 1):
            la = a + side * 0.9
            lx, ly = px + 46 * math.cos(la), py + 46 * math.sin(la)
            nx, ny = -math.sin(la) * 12, math.cos(la) * 12
            d.polygon([(px, py), ((px + lx) / 2 + nx, (py + ly) / 2 + ny), (lx, ly), ((px + lx) / 2 - nx, (py + ly) / 2 - ny)],
                      outline=col + (alpha,), width=3)
    base.alpha_composite(lay)


# ---------------------------------------------------------------- A: Brand Beige
def a_bg(seed):
    f = grad((251, 245, 236), (240, 226, 208), seed)
    branch(f, 1000, 120, 150, 380, L.OLIVE, 110)
    branch(f, 60, 1840, -40, 360, L.OLIVE, 110, flip=-1)
    paste_center(f, blob(260, (255, 236, 214), 160), 880, 300)
    return f


def a_hook():
    f = a_bg(1)
    paste_center(f, txt("NEW DAY,", font("quicksand_b.ttf", 56), L.TAUPE, track=16), W / 2, 230)
    paste_center(f, txt("new product!", font("quicksand_b.ttf", 140), L.TERRA), W / 2, 360)
    paste_center(f, txt("Lotus Rangoli Stencil", font("allura.ttf", 96), L.OLIVE), W / 2, 500)
    ph = rounded(photo("L4", 12.5, (540, 720), 0.78, (840, 1000)), 44, border=14, bcol=(255, 252, 246))
    ph = R.with_shadow(ph.rotate(-2, resample=Image.BICUBIC, expand=True), offset=(0, 16), blur=26, alpha=90, color=(120, 90, 60))
    paste_center(f, ph, W / 2, 1180)
    paste_center(f, lotus_icon(L.TERRA, (170, 90, 64), 0.45), 140, 640)
    return f


def a_end():
    f = a_bg(2)
    paste_center(f, lotus_icon(L.TERRA, (170, 90, 64), 0.6), W / 2, 520)
    paste_center(f, txt("Order now!", font("quicksand_b.ttf", 160), L.TERRA), W / 2, 740)
    paste_center(f, txt("LOTUS RANGOLI STENCIL", font("quicksand_b.ttf", 40), L.OLIVE, track=8), W / 2, 920)
    paste_center(f, R.pill("DM to order", font("quicksand_b.ttf", 52), fg=(255, 250, 240), bg=L.TERRA, pad=(56, 22)), W / 2, 1070)
    paste_center(f, txt("शुभ दीपावली", font("tiro.ttf", 90), L.TERRA), W / 2, 1380)
    for x in (360, 540, 720):
        T.diya_glow(f, x, 1580, 150)
    return f


# ---------------------------------------------------------------- B: Rose & Gold
def b_bg(seed):
    f = grad(ROSE_D, (186, 50, 106), seed, c3=(232, 128, 160))
    mand = R.make_mandala(420)
    mand.putalpha(mand.getchannel("A").point(lambda v: v * 120 // 255))
    for x, y in ((0, 0), (W, 0)):
        paste_center(f, mand, x, y)
    T.bokeh(f, 30, seed + 3, [PINK, (255, 200, 210), T.GOLD], 700, 1900)
    rng = np.random.default_rng(seed)
    for k in range(10):  # floating petals
        p = Image.new("RGBA", (50, 90), (0, 0, 0, 0))
        ImageDraw.Draw(p).ellipse((5, 0, 45, 90), fill=(255, 200, 215, 200))
        paste_center(f, p.rotate(rng.uniform(0, 360), expand=True), rng.uniform(40, W - 40), rng.uniform(600, 1850))
    return f


def ring_photo(name, t, src, s, d_):
    ph = photo(name, t, src, s, (d_, d_))
    m = Image.new("L", (d_, d_), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d_ - 1, d_ - 1), fill=255)
    ph.putalpha(m)
    out = Image.new("RGBA", (d_ + 300, d_ + 300), (0, 0, 0, 0))
    c = out.width / 2
    for k in range(16):  # lotus petals behind the ring
        a = 2 * math.pi * k / 16
        p = Image.new("RGBA", (120, 220), (0, 0, 0, 0))
        ImageDraw.Draw(p).ellipse((6, 0, 114, 220), fill=(255, 190, 210, 235), outline=T.GOLD + (255,), width=3)
        p = p.rotate(-math.degrees(a) - 90, expand=True, resample=Image.BICUBIC)
        paste_center(out, p, c + (d_ / 2 + 40) * math.cos(a), c + (d_ / 2 + 40) * math.sin(a))
    paste_center(out, blob(int(d_ * 0.4), T.GOLD, 160), c, c)
    out.alpha_composite(ph, (150, 150))
    d = ImageDraw.Draw(out)
    d.ellipse((150 - 6, 150 - 6, 150 + d_ + 6, 150 + d_ + 6), outline=T.GOLD + (255,), width=10)
    d.ellipse((150 - 20, 150 - 20, 150 + d_ + 20, 150 + d_ + 20), outline=T.GOLD_L + (200,), width=3)
    return out


def b_hook():
    f = b_bg(4)
    paste_center(f, T.glow_text("New day,", T.allura(140), T.CREAM, glow=(255, 200, 220), ga=90), W / 2, 260)
    paste_center(f, T.glow_text("NEW PRODUCT!", T.yeseva(120), (T.GOLD_L, T.GOLD)), W / 2, 420)
    paste_center(f, ring_photo("L4", 12.5, (540, 720), 0.72, 760), W / 2, 1120)
    paste_center(f, T.glow_text("LOTUS RANGOLI STENCIL", T.mont(40), T.CREAM, ga=0, track=10), W / 2, 1720)
    return f


def b_end():
    f = b_bg(6)
    paste_center(f, lotus_icon(T.GOLD, T.AMBER, 0.7), W / 2, 500)
    paste_center(f, T.glow_text("Order now!", T.yeseva(150), (T.GOLD_L, T.GOLD)), W / 2, 730)
    paste_center(f, T.glow_text("LOTUS RANGOLI STENCIL", T.mont(36), T.CREAM, ga=0, track=8), W / 2, 950)
    paste_center(f, R.pill("DM to order", T.mont(48), fg=ROSE_D, bg=T.GOLD_L, pad=(56, 22)), W / 2, 1110)
    for k, (x, y, w) in enumerate(((300, 1500, 220), (780, 1500, 220), (540, 1620, 240))):
        T.diya_glow(f, x, y, w)
    paste_center(f, T.glow_text("शुभ दीपावली", T.tiro(84), T.GOLD_L, ga=120), W / 2, 1800)
    return f


# ---------------------------------------------------------------- C: Mint Pop
def c_bg(seed):
    f = grad((222, 244, 234), MINT, seed)
    for x, y, r, c in ((120, 260, 260, PEACH), (980, 900, 300, (255, 196, 206)), (200, 1700, 280, PEACH), (900, 1820, 200, (255, 232, 170))):
        b = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
        ImageDraw.Draw(b).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=c + (200,))
        paste_center(f, b, x, y)
    ic = lotus_icon((255, 255, 255), (255, 255, 255), 0.22)
    ic.putalpha(ic.getchannel("A").point(lambda v: v * 120 // 255))
    for yy in range(80, H, 260):
        for xx in range(60 + (yy // 260 % 2) * 130, W, 260):
            paste_center(f, ic, xx, yy)
    return f


def sticker(t, f_, fg, bg, rot):
    s = R.pill(t, f_, fg=fg, bg=bg, pad=(40, 18))
    return s.rotate(rot, expand=True, resample=Image.BICUBIC)


def starburst(r, col, t, f_):
    im = Image.new("RGBA", (2 * r + 20, 2 * r + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = im.width / 2
    pts = [(c + (r if k % 2 == 0 else r * 0.8) * math.cos(math.pi * k / 12), c + (r if k % 2 == 0 else r * 0.8) * math.sin(math.pi * k / 12)) for k in range(24)]
    d.polygon(pts, fill=col + (255,))
    d.text((c, c), t, font=f_, fill=(255, 255, 255), anchor="mm")
    return R.with_shadow(im.rotate(14, expand=True, resample=Image.BICUBIC), offset=(0, 6), blur=10, alpha=80, color=(40, 60, 50))


def polaroid(name, t, src, s, w, h, note):
    ph = photo(name, t, src, s, (w, h))
    card = Image.new("RGBA", (w + 60, h + 220), (255, 255, 252, 255))
    card.alpha_composite(ph, (30, 30))
    ImageDraw.Draw(card).text((card.width / 2, h + 125), note, font=font("caveat.ttf", 84), fill=MINT_D, anchor="mm")
    card = R.with_shadow(card, offset=(0, 14), blur=20, alpha=90, color=(40, 60, 50)).rotate(3, expand=True, resample=Image.BICUBIC)
    for x, rot in ((card.width * 0.28, -18), (card.width * 0.72, 16)):  # washi tape
        tape = Image.new("RGBA", (200, 56), (244, 150, 180, 170))
        paste_center(card, tape.rotate(rot, expand=True), x, 60)
    return card


def c_hook():
    f = c_bg(7)
    paste_center(f, txt("NEW DAY,", font("poppins_xb.ttf", 120), MINT_D), W / 2, 250)
    paste_center(f, sticker("new product!", font("caveat.ttf", 110), (255, 255, 255), ROSE, -4), W / 2, 420)
    paste_center(f, polaroid("L4", 12.5, (540, 720), 0.73, 780, 760, "Lotus Rangoli Stencil"), W / 2, 1140)
    paste_center(f, starburst(110, (240, 110, 150), "NEW!", font("poppins_xb.ttf", 54)), 880, 640)
    return f


def c_end():
    f = c_bg(9)
    paste_center(f, lotus_icon(ROSE, (190, 60, 110), 0.6), W / 2, 500)
    paste_center(f, txt("Order now!", font("poppins_xb.ttf", 140), MINT_D), W / 2, 720)
    paste_center(f, txt("LOTUS RANGOLI STENCIL", font("caveat.ttf", 90), ROSE), W / 2, 900)
    paste_center(f, sticker("DM to order", font("poppins_xb.ttf", 56), (255, 255, 255), ROSE, 3), W / 2, 1140)
    paste_center(f, txt("Happy Diwali!", font("caveat.ttf", 130), ROSE), W / 2, 1480)
    paste_center(f, txt("शुभ दीपावली", font("tiro.ttf", 80), MINT_D), W / 2, 1640)
    return f


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    opts = [("A_brand_beige", a_hook, a_end), ("B_rose_gold", b_hook, b_end), ("C_mint_pop", c_hook, c_end)]
    thumbs = []
    for name, hook, end in opts:
        for part, fn in (("hook", hook), ("end", end)):
            im = fn().convert("RGB")
            im.save(f"{OUTDIR}/option_{name}_{part}.png")
            thumbs.append(im.resize((W // 3, H // 3), Image.LANCZOS))
    sheet = Image.new("RGB", (W // 3 * 6 + 70, H // 3 + 20), (255, 255, 255))
    for k, t in enumerate(thumbs):
        sheet.paste(t, (10 + k * (W // 3 + 10) + (k // 2) * 0, 10))
    sheet.save(f"{OUTDIR}/options_sheet.png")
    print("wrote", OUTDIR)
