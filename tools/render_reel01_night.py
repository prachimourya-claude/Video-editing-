"""Render the Diwali 01 main reel (Psone Labs Kalash rangoli stencil) in the approved teaser style:
night-blue sky to purple/pink, gold Mughal arches, sky lanterns, kandils, line fireworks, diyas.
Footage plays inside gold arch windows. 30s, 9:16, one voiceover line per segment.

usage: cd tools && python3 render_reel01_night.py <workdir> <out.mp4> [segment ...]
<workdir>/src needs A.mp4 B.mp4 C.mp4 (WA0009/10/11, white stencil) and E.mp4 (WA0013, real rangoli; used once).
"""
import math, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import render_diwali01 as R
import render_teaser01 as TT
import style_frames_teaser01 as T
from render_diwali01 import W, H, FPS, clamp, ease_out, ease_io, ease_back, paste_center

BASE, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:]
SEGMENTS = [
    ("n1", 0.0, 3.2),    # Is Diwali, aapki rangoli ho kuch unique!
    ("n2", 3.2, 7.2),    # Market mein stencils toh bahut hain... par sab ek jaise.
    ("n3", 7.2, 13.2),   # Isliye humne khud design kiya, special Dhanteras aur Diwali ke liye.
    ("n4", 13.2, 19.2),  # Ye hai hamara Kalash stencil. Upar shubh kalash, aur neeche kamal.
    ("n5", 19.2, 25.2),  # Bas stencil rakho, rang bharo... aur perfect rangoli ready!
    ("n6", 25.2, 30.0),  # Dhanteras se pehle apna order karo, abhi DM karo! + end card
]
# clean, slightly rich grade for the phone clips (no warm cast; the night frame supplies the mood)
CLEAN = "eq=contrast=1.05:saturation=1.12:brightness=0.02,unsharp=5:5:0.6"


def night_frame(aw, ah, ay, seed, stars=120):
    """Navy night overlay with an arch-shaped hole, baked stars and the gold arch border."""
    bg = T.grad_bg([(8, 12, 38), (22, 22, 66), (40, 28, 80)], [0, 0.6, 1], seed)
    T.stars(bg, stars, seed + 1, alpha=0.8)
    hole = Image.new("L", (W, H), 255)
    hole.paste(Image.fromarray(255 - np.asarray(T.arch_mask(aw, ah))), ((W - aw) // 2, ay))
    bg.putalpha(hole)
    arch = T.gold_arch(aw, ah)
    bg.alpha_composite(arch, ((W - arch.width) // 2, ay - 60))
    return bg


_FEATHER = {}


def fit(fr, s, src, dst):
    """Scale a footage frame by s so source point src lands at screen point dst (to frame the subject in an arch).
    Uncovered space is filled with a dark, blurred copy of the same frame and the clip's edges are feathered."""
    out = fr.resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
    out = Image.blend(out.convert("RGB"), Image.new("RGB", (W, H), (22, 20, 62)), 0.45).convert("RGBA")
    if abs(s - 1) < 0.001:
        return fr
    im = fr.resize((int(W * s), int(H * s)), Image.BILINEAR)
    if im.size not in _FEATHER:
        m = np.ones((im.height, im.width), np.float32)
        r = np.minimum(np.arange(im.width), np.arange(im.width)[::-1]) / 40
        c = np.minimum(np.arange(im.height), np.arange(im.height)[::-1]) / 40
        m = np.clip(np.minimum(r[None, :], c[:, None]), 0, 1)
        _FEATHER[im.size] = Image.fromarray((m * 255).astype(np.uint8))
    im.putalpha(_FEATHER[im.size])
    out.alpha_composite(im, (int(dst[0] - src[0] * s), int(dst[1] - src[1] * s)))
    return out


def chip(text, font, fill=(46, 30, 92), fg=T.CREAM, pad=(36, 18)):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.textbbox((0, 0), text, font=font)
    w, h = bb[2] - bb[0] + 2 * pad[0], bb[3] - bb[1] + 2 * pad[1]
    im = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle((4, 4, 4 + w, 4 + h), radius=h // 2, fill=fill + (235,), outline=T.GOLD + (255,), width=3)
    dd.text((4 + w / 2, 4 + h / 2), text, font=font, fill=fg, anchor="mm")
    return R.with_shadow(im, offset=(0, 6), blur=12, alpha=120, color=(4, 4, 20))


def pointer(f, im, lx, ly, tx, ty, t, t0):
    """Chip at (lx, ly) with a gold curve drawn out to (tx, ty) on the footage."""
    if t < t0:
        return
    p = ease_out((t - t0) / 0.5)
    sx = lx - im.width / 2 + 50
    mx, my = (sx + tx) / 2, min(ly, ty) - 60
    pts = [((1 - u) ** 2 * sx + 2 * (1 - u) * u * mx + u * u * tx, (1 - u) ** 2 * ly + 2 * (1 - u) * u * my + u * u * ty)
           for u in np.linspace(0, p, max(2, int(30 * p)))]
    d = ImageDraw.Draw(f)
    d.line(pts, fill=T.GOLD + (255,), width=6, joint="curve")
    if p > 0.95:
        d.ellipse((tx - 11, ty - 11, tx + 11, ty + 11), fill=T.GOLD + (255,), outline=T.CREAM + (255,), width=4)
    TT.rise(f, im, lx, ly, t, t0, 0.4, dy=0, scale_from=0.7)


def lotus(scale=0.6):
    lot = Image.new("RGBA", (300, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(lot)
    for ang, ln in ((-68, 95), (68, 95), (-36, 125), (36, 125), (0, 150)):
        th = math.radians(ang)
        side = [(30 * math.sin(math.pi * u) ** 0.9 * (1 - 0.3 * u), ln * u) for u in np.linspace(0, 1, 30)]
        pts = side + [(-x, y) for x, y in reversed(side)]
        pts = [(150 + x * math.cos(th) + y * math.sin(th), 160 + x * math.sin(th) - y * math.cos(th)) for x, y in pts]
        d.polygon(pts, fill=T.GOLD + (255,), outline=T.AMBER + (255,), width=3)
    return lot.resize((int(300 * scale), int(170 * scale)), Image.LANCZOS)


# ---------------------------------------------------------------- segments
def seg_n1(t0, t1):
    """Hook: the plain white stencil glowing in the arch, sky lanterns rising around it."""
    aw, ah, ay = 860, 1180, 600
    over = night_frame(aw, ah, ay, 1)
    lan = TT.Lanterns(10, 3, 500, 1900, avoid=(110, 560, 970, 1800))
    a = T.glow_text("IS DIWALI", T.mont(38), T.CREAM, ga=0, track=16)
    b = T.glow_text("rangoli ho", T.allura(120), T.CREAM, glow=(255, 220, 160), ga=90)
    c = T.glow_text("kuch unique!", T.yeseva(140), (T.GOLD_L, T.GOLD))
    dur = t1 - t0
    clip = R.footage("A", 2.2, 1.4, dur, (1.0, 1.0), grade=CLEAN)
    for i in range(int(round(dur * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = fit(next(clip), 0.82, (610, 720), (540, 1190))
        f.alpha_composite(over)
        lan.draw(f, t)
        TT.rise(f, a, W / 2, 200, lt, 0.1, 0.5)
        TT.wipe(f, b, W / 2, 310, ease_io((lt - 0.3) / 0.7))
        TT.rise(f, c, W / 2, 450, lt, 0.8, 0.6, dy=0, scale_from=0.8)
        TT.dip(f, lt, dur, fin=0.3)
        yield f


def seg_n2(t0, t1, S):
    """Market stencils all look the same: a dull grid; the centre tile turns into our stencil in a gold arch."""
    bg = T.grad_bg([(8, 12, 38), (24, 22, 68), (44, 30, 84)], [0, 0.6, 1], 5)
    T.stars(bg, 110, 6, alpha=0.7)
    tile = Image.new("RGBA", (270, 270), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle((0, 0, 269, 269), radius=28, fill=(58, 54, 92, 255), outline=(104, 96, 146, 255), width=3)
    c = 135
    for j in range(8):
        an = math.pi * j / 4
        x, y = c + 54 * math.cos(an), c + 54 * math.sin(an)
        d.ellipse((x - 32, y - 32, x + 32, y + 32), outline=(150, 140, 186, 255), width=5)
    d.ellipse((c - 24, c - 24, c + 24, c + 24), outline=(150, 140, 186, 255), width=5)
    ours = Image.new("RGBA", (270, 270), (0, 0, 0, 0))
    om = T.arch_mask(230, 250)
    face = Image.new("RGBA", (230, 250), (120, 26, 96, 255))
    face.putalpha(om)
    ours.alpha_composite(face, (20, 10))
    ga = T.gold_arch(230, 250, line=6)
    ours.alpha_composite(ga, (20 - 60, 10 - 60))
    k = R.stencil_img(S, 190 / S.height)
    ours.alpha_composite(k, ((270 - k.width) // 2, 60))
    h1 = T.glow_text("Market ke stencils...", T.allura(110), T.CREAM, glow=(255, 220, 160), ga=80)
    h2 = T.glow_text("sab ek jaise!", T.yeseva(120), (T.GOLD_L, T.GOLD))
    h3 = T.glow_text("Humara design", T.yeseva(110), (T.GOLD_L, T.GOLD))
    lan = TT.Lanterns(6, 21, 400, 1900, avoid=(60, 500, 1020, 1500))
    dur = t1 - t0
    for i in range(int(round(dur * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bg.copy()
        lan.draw(f, t)
        TT.wipe(f, h1, W / 2, 400, ease_io((lt - 0.1) / 0.7))
        grey = clamp((lt - 2.6) / 0.3)
        for r in range(3):
            for cc in range(3):
                j = r * 3 + cc
                if j == 4:
                    continue
                x, y = W / 2 + (cc - 1) * 300, 960 + (r - 1) * 300
                st = 0.3 + j * 0.07
                a = ease_out((lt - st) / 0.3) * (1 - grey)
                paste_center(f, tile, x, y + 40 * (1 - a) + grey * 160 * (j / 8), a * 0.9, 0.7 + 0.3 * ease_back((lt - st) / 0.4))
        a = ease_out((lt - 0.58) / 0.3)
        flip = clamp((lt - 2.6) / 0.35)
        sx = abs(math.cos(math.pi * flip))
        im = tile if flip < 0.5 else ours
        grow = 1 + 3.0 * ease_io((lt - 3.3) / 0.7) ** 2
        if a > 0 and sx > 0.03:
            paste_center(f, im.resize((max(1, int(270 * sx)), 270)), W / 2, 960, a, (0.7 + 0.3 * ease_back((lt - 0.58) / 0.4)) * grow)
        if lt < 2.75:
            TT.rise(f, h2, W / 2, 1480, lt, 1.3, 0.5, dy=0, scale_from=0.8)
        else:
            TT.rise(f, h3, W / 2, 1480, lt, 2.85, 0.5, dy=0, scale_from=0.8)
        TT.dip(f, lt, dur)
        yield f


def seg_n3(t0, t1):
    """Designed and printed in-house: printer footage in the arch, kandils, gold text."""
    aw, ah, ay = 900, 1220, 520
    over = night_frame(aw, ah, ay, 7)
    a = T.glow_text("Humne khud", T.allura(120), T.CREAM, glow=(255, 220, 160), ga=90)
    b = T.glow_text("design kiya!", T.yeseva(130), (T.GOLD_L, T.GOLD))
    badge = chip("Designed & 3D printed by Psone Labs", T.mont(30))
    spec = chip("Special: Dhanteras & Diwali", T.mont(34), fill=(120, 26, 96))
    a_dur, b_dur = 3.8, 2.2
    frames = [fit(f, 0.9, (540, 600), (540, 1050)) for f in R.footage("C", 2.0, 3.6, a_dur, (1.0, 1.1), (0.5, 0.4), grade=CLEAN)] + \
        [fit(f, 1.2, (540, 420), (540, 1050)) for f in R.footage("B", 9.2, 2.6, b_dur, (1.0, 1.0), grade=CLEAN)]
    dur = t1 - t0
    for i, f in enumerate(frames):
        t = t0 + i / FPS
        lt = t - t0
        f.alpha_composite(over)
        TT.wipe(f, a, W / 2, 210, ease_io((lt - 0.15) / 0.7))
        TT.rise(f, b, W / 2, 350, lt, 0.6, 0.6, dy=0, scale_from=0.8)
        if lt < a_dur:
            TT.rise(f, badge, W / 2, 1810, lt, 1.0, 0.45)
        else:
            TT.rise(f, spec, W / 2, 1810, lt, a_dur + 0.1, 0.45, dy=0, scale_from=0.7)
        TT.dip(f, lt, dur)
        yield f


def seg_n4(t0, t1):
    """Product: hand-held stencil in slow motion inside a tall arch, with gold pointers."""
    aw, ah, ay = 1000, 1560, 330
    over = night_frame(aw, ah, ay, 9, stars=60)
    title = T.glow_text("Kalash Rangoli Stencil", T.yeseva(84), (T.GOLD_L, T.GOLD))
    up = chip("Upar: Shubh Kalash", T.mont(38))
    dn = chip("Neeche: Kamal", T.mont(38), fill=(120, 26, 96))
    dur = t1 - t0
    for i, fr in enumerate(R.footage("B", 0.0, 4.0, dur, (1.0, 1.0), grade=CLEAN)):
        t = t0 + i / FPS
        lt = t - t0
        f = fit(fr, 0.75, (590, 750), (540, 1190))
        f.alpha_composite(over)
        TT.rise(f, title, W / 2, 190, lt, 0.15, 0.6, dy=0, scale_from=0.85)
        pointer(f, up, 790, 600, 535, 880, lt, 1.0)
        pointer(f, dn, 790, 1790, 535, 1420, lt, 2.6)
        TT.dip(f, lt, dur)
        yield f


def seg_n5(t0, t1):
    """Steps on the white stencil (cut-out, set down in the arch, pinches of powder), then a short
    look at the real finished rangoli (E) for "ready" - the only coloured shot in the reel."""
    aw, ah, ay = 920, 1280, 400
    over = night_frame(aw, ah, ay, 11)
    base = T.grad_bg([(8, 12, 38), (22, 22, 66), (40, 28, 80)], [0, 0.6, 1], 12)
    inner = T.gold_arch(aw, ah, [(40, 40, 110), (110, 80, 160), (220, 118, 160)])
    base.alpha_composite(inner, ((W - inner.width) // 2, ay - 60))
    base.alpha_composite(over)
    S = R.build_stencil()
    st = R.stencil_img(S, 880 / S.height)
    shd = Image.new("RGBA", st.size, (10, 4, 30, 0))
    shd.putalpha(st.getchannel("A").point(lambda v: v * 150 // 255))
    shd = shd.filter(ImageFilter.GaussianBlur(18))
    title = T.glow_text("Bas 3 steps!", T.yeseva(110), (T.GOLD_L, T.GOLD))
    ready = T.glow_text("Perfect rangoli!", T.allura(130), T.GOLD_L, glow=(255, 200, 120), ga=140)
    chips = [chip("1  Stencil rakho", T.mont(40)), chip("2  Rang bharo", T.mont(40)),
             chip("3  Rangoli ready!", T.mont(40), fill=(120, 26, 96))]
    rng = np.random.default_rng(4)
    pinch = [((150, 520), T.PINK), ((930, 560), T.GOLD), ((140, 1350), (90, 190, 110)), ((940, 1300), T.AMBER)]
    puffs = rng.uniform(size=(len(pinch), 12, 3))
    mg_dur, e_dur = 3.6, 2.4
    clip = R.footage("E", 5.2, 2.4, e_dur, (1.04, 1.0), (0.5, 0.42), grade=CLEAN)
    dur = t1 - t0
    for i in range(int(round(dur * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        if lt < mg_dur:
            f = base.copy()
            drop = ease_out((lt - 0.15) / 0.6)
            sc = 1.1 - 0.1 * drop
            paste_center(f, shd, W / 2 + 8, 1110 + 20 + 40 * (1 - drop), drop, sc)
            paste_center(f, st, W / 2, 1110 - 70 * (1 - drop), drop, sc)
            win = min(clamp((lt - 1.6) / 0.2), clamp((mg_dur - lt) / 0.3))
            for k, ((x, y), col) in enumerate(pinch):
                if win <= 0:
                    break
                for j in range(12):
                    u = puffs[k, j]
                    ph = ((lt - 1.6) * 1.2 + u[0]) % 1
                    tx, ty = W / 2 + (x - W / 2) * 0.25 + (u[1] - 0.5) * 160, y + (1110 - y) * 0.5 + (u[2] - 0.5) * 160
                    px, py = x + (tx - x) * ph, y + (ty - y) * ph - 120 * math.sin(math.pi * ph)
                    paste_center(f, T.cblob(8 + int(5 * u[2]), col, 255), px, py, win * math.sin(math.pi * ph))
            TT.rise(f, title, W / 2, 230, lt, 0.1, 0.5, dy=0, scale_from=0.85)
            for k, (ct, ce) in enumerate(((0.2, 1.6), (1.6, mg_dur))):
                if ct <= lt < ce:
                    TT.rise(f, chips[k], W / 2, 1790, lt, ct, 0.35, dy=0, scale_from=0.7)
            TT.dip(f, lt, mg_dur, fin=0.25, fout=0.15)
        else:
            e = lt - mg_dur
            f = fit(next(clip), 0.92, (520, 800), (540, 1080))
            f.alpha_composite(over)
            TT.wipe(f, ready, W / 2, 230, ease_io((e - 0.1) / 0.7))
            TT.rise(f, chips[2], W / 2, 1790, e, 0.0, 0.35, dy=0, scale_from=0.7)
            TT.burst(f, 200, 520, 70, T.GOLD, e, 0.3)
            TT.burst(f, 880, 600, 60, T.PINK, e, 0.7)
            TT.burst(f, 170, 1500, 55, T.GOLD_L, e, 1.2)
            TT.dip(f, e, e_dur, fin=0.15, fout=0.2)
        yield f

def seg_n6(t0, t1):
    """Order CTA over the white stencil, then the end card in the dusk style."""
    a_dur = 2.2
    aw, ah, ay = 860, 1180, 330
    over = night_frame(aw, ah, ay, 13)
    t_a = T.glow_text("Dhanteras se pehle", T.allura(110), T.CREAM, glow=(255, 220, 160), ga=90)
    t_b = T.glow_text("order karo!", T.yeseva(130), (T.GOLD_L, T.GOLD))
    dm = chip("DM to order", T.mont(48), fill=(120, 26, 96), pad=(50, 22))
    clip = R.footage("A", 2.4, 1.2, a_dur, (1.0, 1.0), grade=CLEAN)
    # end card
    bg = T.grad_bg(T.DUSK, [0, 0.35, 0.65, 1], 10)
    T.bokeh(bg, 26, 12, [T.PINK, (255, 170, 200), (200, 140, 230)], 900, 1900)
    stars = TT.Stars(90, 11, ymax=1100)
    lan = TT.Lanterns(9, 13, 300, 1600, avoid=(120, 250, 960, 1350))
    arch = T.gold_arch(820, 1100, [(70, 20, 80), (120, 26, 96), (150, 40, 110)])
    brand = T.glow_text("Psone Labs", T.yeseva(140), (T.GOLD_L, T.GOLD))
    sub = T.glow_text("KALASH RANGOLI STENCIL", T.mont(34), T.CREAM, ga=0, track=8)
    lot = lotus(0.6)
    dm2 = chip("DM to order", T.mont(44), fill=(46, 30, 92), pad=(50, 20))
    sh = T.glow_text("शुभ दीपावली", T.tiro(80), T.GOLD_L, ga=120)
    n_a = int(round(a_dur * FPS))
    dur = t1 - t0
    for i in range(int(round(dur * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        if i < n_a:
            f = fit(next(clip), 0.72, (610, 720), (540, 930))
            f.alpha_composite(over)
            TT.wipe(f, t_a, W / 2, 1600, ease_io((lt - 0.1) / 0.6))
            TT.rise(f, t_b, W / 2, 1720, lt, 0.45, 0.5, dy=0, scale_from=0.8)
            if lt > 0.9:
                pulse = 1 + 0.04 * math.sin((lt - 0.9) * 8)
                paste_center(f, dm, W / 2, 1850, ease_out((lt - 0.9) / 0.3), pulse * (0.7 + 0.3 * ease_back((lt - 0.9) / 0.4)))
            TT.dip(f, lt, a_dur, fin=0.25, fout=0.2)
        else:
            e = lt - a_dur
            f = bg.copy()
            stars.draw(f, t)
            lan.draw(f, t)
            ap = ease_out(e / 0.5)
            paste_center(f, arch, W / 2, 230 - 60 + arch.height / 2, ap, 0.96 + 0.04 * ap)
            paste_center(f, lot, W / 2, 560, ease_out((e - 0.2) / 0.5), 0.5 + 0.5 * ease_out((e - 0.2) / 0.5))
            TT.rise(f, brand, W / 2, 760, e, 0.3, 0.6, dy=0, scale_from=0.8)
            TT.rise(f, sub, W / 2, 890, e, 0.55, 0.5)
            TT.rise(f, dm2, W / 2, 1060, e, 0.8, 0.45, dy=0, scale_from=0.7)
            for k, (x, y, w) in enumerate(((300, 1560, 220), (780, 1560, 220), (540, 1680, 240))):
                T.diya_glow(f, x, y, w, 0.92 + 0.06 * math.sin(t * 11 + k * 2) + 0.04 * math.sin(t * 23 + k))
            TT.rise(f, sh, W / 2, 1830, e, 1.0, 0.5)
            if e < 0.25:
                f.alpha_composite(Image.new("RGBA", (W, H), (8, 10, 30, int(255 * ease_io(1 - e / 0.25)))))
            fo = clamp((lt - (dur - 0.4)) / 0.4)
            if fo > 0:
                f.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fo))))
        yield f


def render(seg):
    name, t0, t1 = seg
    out = f"{R.SEG}/{name}.mp4"
    S = R.build_stencil() if name == "n2" else None
    gen = {"n1": lambda: seg_n1(t0, t1), "n2": lambda: seg_n2(t0, t1, S), "n3": lambda: seg_n3(t0, t1),
           "n4": lambda: seg_n4(t0, t1), "n5": lambda: seg_n5(t0, t1), "n6": lambda: seg_n6(t0, t1)}[name]()
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
    lst = f"{R.SEG}/reel_night_list.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{name}.mp4'\n" for name, _, _ in SEGMENTS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT], check=True)
    print("wrote", OUT)
