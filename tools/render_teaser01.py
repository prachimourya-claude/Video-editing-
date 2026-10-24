"""Render the 10s teaser for Diwali 01 (Kalash rangoli stencil) in the approved reference style:
night-blue sky to purple/pink, gold Mughal arches, sky lanterns, kandils, line fireworks, diyas. No reveal, no handle.

usage: cd tools && python3 render_teaser01.py <workdir> <out.mp4>
Same <workdir> as render_diwali01.py; drawing helpers come from style_frames_teaser01.py.
"""
import math, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import render_diwali01 as R
import style_frames_teaser01 as T
from render_diwali01 import W, H, FPS, clamp, ease_out, ease_io, paste_center

BASE, OUT = sys.argv[1], sys.argv[2]
SEGMENTS = [
    ("t1", 0.0, 2.2),   # Is Diwali... kuch naya aa raha hai
    ("t2", 2.2, 4.6),   # glimpse through the arch: kuch khaas ban raha hai
    ("t3", 4.6, 7.9),   # glowing silhouette: guess karo, kya hai?
    ("t4", 7.9, 10.0),  # coming soon
]


# ---------------------------------------------------------------- animated pieces
class Stars:
    def __init__(self, n, seed, ymax=H):
        rng = np.random.default_rng(seed)
        self.s = [(rng.uniform(0, W), rng.uniform(0, ymax), rng.choice([1.5, 2, 2.5, 3.5], p=[0.4, 0.3, 0.2, 0.1]),
                   rng.uniform(1.5, 4), rng.uniform(0, 6.3)) for _ in range(n)]

    def draw(self, f, t, alpha=1.0):
        d = ImageDraw.Draw(f)
        for x, y, r, sp, ph in self.s:
            a = int(255 * alpha * (0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * sp + ph))))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 236, 190, a))
            if r > 3:
                paste_center(f, T.cblob(8, (255, 220, 150), 120), x, y, a / 255)


class Lanterns:
    """Sky lanterns drifting upwards with a gentle sway; bigger ones are nearer and faster."""
    def __init__(self, n, seed, ymin, ymax, avoid=None):
        rng = np.random.default_rng(seed)
        self.l = []
        for _ in range(n):
            h = int(rng.choice([36, 48, 60, 80, 110]))
            x, y = rng.uniform(60, W - 60), rng.uniform(ymin, ymax)
            if avoid and avoid[0] < x < avoid[2] and avoid[1] < y < avoid[3]:
                x = rng.choice([rng.uniform(40, avoid[0]), rng.uniform(avoid[2], W - 40)])
            self.l.append((x, y, h, 20 + h * 0.45, rng.uniform(0, 6.3)))
        self.spr = {h: T.sky_lantern(h, blur=0 if h < 100 else 2) for h in {l[2] for l in self.l}}

    def draw(self, f, t):
        for x, y, h, v, ph in self.l:
            paste_center(f, self.spr[h], x + 10 * math.sin(t * 0.9 + ph), y - v * t, 0.85 + 0.15 * math.sin(t * 5 + ph))


def swing(f, spr, x, y, t, ph=0.0, amp=3.0):
    """Hanging kandil (placed as in T.hang_kandil) swaying about the top of its string."""
    h = spr.height / 3.2
    ang = amp * math.sin(t * 1.6 + ph)
    dx = y * math.sin(math.radians(ang))
    ImageDraw.Draw(f).line((x, 0, x + dx, y - h * 0.3), fill=(220, 180, 120, 200), width=3)
    paste_center(f, spr, x + dx * 1.25, y + spr.height / 2 - h * 0.65, rot=-ang)


def wipe(f, im, cx, cy, p, alpha=1.0):
    """Left-to-right handwriting reveal with a soft edge."""
    if p <= 0:
        return
    w = int(im.width * clamp(p))
    if w < 2:
        return
    part = im.crop((0, 0, w, im.height))
    a = np.asarray(part.getchannel("A")).astype(np.float32)
    edge = min(60, w)
    a[:, w - edge:] *= np.linspace(1, 0, edge)[None, :] if p < 1 else 1
    part.putalpha(Image.fromarray((a * alpha).astype(np.uint8)))
    f.alpha_composite(part, (int(cx - im.width / 2), int(cy - im.height / 2)))


def rise(f, im, cx, cy, t, t0, dur=0.6, dy=30, scale_from=1.0):
    p = ease_out((t - t0) / dur)
    if p > 0:
        paste_center(f, im, cx, cy + dy * (1 - p), p, scale_from + (1 - scale_from) * p)


def burst(f, x, y, r, col, t, t0, n=18):
    """Line firework: rays shoot out, then thin and fade (ref 2)."""
    a = t - t0
    if not 0 <= a < 1.3:
        return
    g = ease_out(a / 0.45)
    fade = clamp(1 - (a - 0.5) / 0.8)
    lay = Image.new("RGBA", (int(r * 2.6), int(r * 2.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = lay.width / 2
    for k in range(n):
        an = 2 * math.pi * k / n + 0.1
        r1 = r * (1.0 if k % 2 else 0.8) * g
        r0 = max(r * (0.3 if k % 2 else 0.45), r1 - r * 0.55)
        d.line((c + r0 * math.cos(an), c + r0 * math.sin(an), c + r1 * math.cos(an), c + r1 * math.sin(an)),
               fill=col + (int(255 * fade),), width=4)
        if g > 0.9:
            px, py = c + r1 * 1.1 * math.cos(an), c + r1 * 1.1 * math.sin(an)
            d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=col + (int(220 * fade),))
    paste_center(f, lay.filter(ImageFilter.GaussianBlur(6)), x, y)
    paste_center(f, lay, x, y)


def dip(f, lt, dur, fin=0.25, fout=0.2):
    """Soft dip to night-navy at segment edges instead of hard cuts."""
    a = max(clamp(1 - lt / fin), clamp(1 - (dur - lt) / fout))
    if a > 0:
        f.alpha_composite(Image.new("RGBA", (W, H), (8, 10, 30, int(255 * ease_io(a)))))


# ---------------------------------------------------------------- segments
def seg_t1(t0, t1):
    bg = T.grad_bg(T.SKY, [0, 0.5, 1], 1)
    stars = Stars(140, 2)
    lan = Lanterns(12, 3, 300, 1750, avoid=(150, 560, 930, 1180))
    big = T.sky_lantern(240, blur=6)
    roofs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(roofs)
    lamps = []
    for x0, x1, top in ((0, 360, 1640), (380, 600, 1720), (640, 860, 1690), (880, 1080, 1610)):
        d.rectangle((x0, top, x1, H), fill=(18, 22, 52, 255))
        lamps += [(x, top) for x in range(x0 + 20, x1 - 10, 40)]
    a = T.glow_text("IS DIWALI", T.mont(40), T.CREAM, ga=0, track=18)
    b = T.glow_text("kuch naya", T.yeseva(170), (T.GOLD_L, T.GOLD))
    c = T.glow_text("aa raha hai...", T.allura(130), T.CREAM, glow=(255, 220, 160), ga=90)
    dur = t1 - t0
    for i in range(int(round(dur * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bg.copy()
        stars.draw(f, t)
        paste_center(f, big, 120 + 6 * math.sin(t), 160 - 25 * t)
        lan.draw(f, t)
        f.alpha_composite(roofs)
        dd = ImageDraw.Draw(f)
        for k, (x, top) in enumerate(lamps):
            fl = 0.75 + 0.25 * math.sin(t * 9 + k * 1.7)
            paste_center(f, T.cblob(9, T.AMBER, 220), x, top - 4, fl)
            dd.ellipse((x - 5, top - 9, x + 5, top + 1), fill=(255, 210, 120, 255))
        rise(f, a, W / 2, 700, lt, 0.25, 0.6)
        rise(f, b, W / 2, 840, lt, 0.5, 0.7, dy=0, scale_from=0.85)
        wipe(f, c, W / 2, 1010, ease_io((lt - 1.0) / 0.9))
        dip(f, lt, dur, fin=0.35)
        yield f


def seg_t2(t0, t1):
    bg = T.grad_bg([(8, 10, 34), (20, 22, 60)], [0, 1], 4)
    stars = Stars(60, 5)
    aw, ah, ay = 860, 1180, 330
    arch = T.gold_arch(aw, ah)
    mask = T.arch_mask(aw, ah)
    kand = [T.kandil(200), T.kandil(220)]
    a = T.glow_text("KUCH KHAAS", T.mont(46), T.CREAM, ga=0, track=16)
    b = T.glow_text("ban raha hai...", T.allura(140), (T.GOLD_L, T.GOLD))
    dur = t1 - t0
    clip = R.footage("C", 5.0, 2.4, dur, (2.8, 3.1), (0.62, 0.36))
    x0 = (W - aw) // 2
    for i in range(int(round(dur * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bg.copy()
        stars.draw(f, t, 0.6)
        fr = next(clip).crop((x0, 380, x0 + aw, 380 + ah))
        px = np.asarray(fr.convert("RGB")).astype(np.float32) * 0.45
        px = px * np.array([0.85, 0.85, 1.05]) + np.array([18, 6, 34])
        win = Image.fromarray(px.clip(0, 255).astype(np.uint8)).convert("RGBA")
        win.putalpha(mask)
        f.alpha_composite(win, (x0, ay))
        f.alpha_composite(arch, ((W - arch.width) // 2, ay - 60))
        swing(f, kand[0], 90, 150, t, 0.0)
        swing(f, kand[1], 990, 210, t, 1.3)
        rise(f, a, W / 2, 1620, lt, 0.25, 0.5)
        wipe(f, b, W / 2, 1740, ease_io((lt - 0.55) / 0.9))
        dip(f, lt, dur)
        yield f


def seg_t3(t0, t1, S):
    bg = T.grad_bg([(10, 12, 40), (18, 18, 56)], [0, 1], 6)
    stars = Stars(50, 7)
    aw, ah, ay = 880, 1300, 560
    arch = T.gold_arch(aw, ah, [(40, 40, 110), (110, 80, 160), (220, 118, 160)])
    m = Image.new("L", (W, H), 0)
    m.paste(T.arch_mask(aw, ah), ((W - aw) // 2, ay))
    inner_stars = Stars(40, 8)
    rng = np.random.default_rng(9)
    boke = [(rng.uniform(100, 980), rng.uniform(900, 1800), int(rng.uniform(14, 40)), [T.PINK, (255, 180, 200), T.GOLD][k % 3],
             rng.uniform(50, 110), rng.uniform(0, 6.3)) for k in range(18)]
    boke_spr = {}
    for x, y, r, c, al, ph in boke:
        im = Image.new("RGBA", (r * 2 + 4, r * 2 + 4), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((2, 2, 2 + 2 * r, 2 + 2 * r), fill=c + (int(al),), outline=c + (140,), width=2)
        boke_spr[(r, c, al)] = im
    sil = T.silhouette(S, 720)
    white = R.stencil_img(S, 720 / S.height)
    wa = np.asarray(white.getchannel("A")).astype(np.float32)
    yy, xx = np.mgrid[0:white.height, 0:white.width].astype(np.float32)
    diag = (xx + yy * 0.6) / (white.width + white.height * 0.6)
    kand = [T.kandil(190), T.kandil(190)]
    q1 = T.glow_text("Guess karo...", T.allura(120), T.CREAM, glow=(255, 210, 170), ga=80)
    q2 = T.glow_text("kya hai?", T.yeseva(150), (T.GOLD_L, T.GOLD))
    lights = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    T.string_lights(lights, 40, 90)
    dur = t1 - t0
    for i in range(int(round(dur * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bg.copy()
        stars.draw(f, t, 0.6)
        paste_center(f, lights, W / 2, 130, 0.8 + 0.2 * math.sin(t * 3))
        f.alpha_composite(arch, ((W - arch.width) // 2, ay - 60))
        inside = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        inner_stars.draw(inside, t, 0.8)
        for x, y, r, c, al, ph in boke:
            paste_center(inside, boke_spr[(r, c, al)], x + 12 * math.sin(t * 0.6 + ph), y - 18 * lt)
        burst(inside, 790, 960, 80, T.GOLD, lt, 0.5)
        burst(inside, 280, 1060, 60, T.PINK, lt, 1.2)
        burst(inside, 760, 1700, 70, T.GOLD_L, lt, 1.9)
        inside.putalpha(Image.fromarray(np.minimum(np.asarray(inside.getchannel("A")), np.asarray(m))))
        f.alpha_composite(inside)
        # silhouette rises in, its glow breathes, one light sweep hints at the design
        p = ease_out((lt - 0.15) / 0.7)
        s = 0.94 + 0.06 * ease_io(lt / dur)
        frame = sil.copy()
        sweep = -0.3 + 1.6 * ease_io((lt - 1.3) / 1.4)
        band = np.clip(1 - np.abs(diag - sweep) / 0.07, 0, 1) * 0.5
        hint = white.copy()
        hint.putalpha(Image.fromarray((wa * band).astype(np.uint8)))
        frame.alpha_composite(hint, (100, 100))
        paste_center(f, frame, W / 2, 1360 + 30 * (1 - p), p, s)
        swing(f, kand[0], 100, 330, t, 0.4)
        swing(f, kand[1], 980, 330, t, 2.0)
        wipe(f, q1, W / 2, 300, ease_io((lt - 0.3) / 0.8))
        rise(f, q2, W / 2, 440, lt, 0.9, 0.6, dy=0, scale_from=0.85)
        dip(f, lt, dur)
        yield f


def seg_t4(t0, t1):
    bg = T.grad_bg(T.DUSK, [0, 0.35, 0.65, 1], 10)
    T.bokeh(bg, 26, 12, [T.PINK, (255, 170, 200), (200, 140, 230)], 900, 1900)
    stars = Stars(90, 11, ymax=1100)
    lan = Lanterns(9, 13, 300, 1600, avoid=(120, 250, 960, 1350))
    aw, ah = 820, 1100
    arch = T.gold_arch(aw, ah, [(70, 20, 80), (120, 26, 96), (150, 40, 110)])
    a = T.glow_text("LAUNCHING THIS DIWALI", T.mont(34), T.CREAM, ga=0, track=10)
    b1 = T.glow_text("Coming", T.yeseva(170), (T.GOLD_L, T.GOLD))
    b2 = T.glow_text("Soon", T.yeseva(170), (T.GOLD_L, T.GOLD))
    c = T.glow_text("DHANTERAS SE PEHLE", T.mont(36), T.CREAM, ga=0, track=10)
    sh = T.glow_text("शुभ दीपावली", T.tiro(80), T.GOLD_L, ga=120)
    lot = Image.new("RGBA", (300, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(lot)
    for ang, ln in ((-68, 95), (68, 95), (-36, 125), (36, 125), (0, 150)):
        th = math.radians(ang)
        side = [(30 * math.sin(math.pi * u) ** 0.9 * (1 - 0.3 * u), ln * u) for u in np.linspace(0, 1, 30)]
        pts = side + [(-x, y) for x, y in reversed(side)]
        pts = [(150 + x * math.cos(th) + y * math.sin(th), 160 + x * math.sin(th) - y * math.cos(th)) for x, y in pts]
        d.polygon(pts, fill=T.GOLD + (255,), outline=T.AMBER + (255,), width=3)
    dur = t1 - t0
    for i in range(int(round(dur * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bg.copy()
        stars.draw(f, t)
        lan.draw(f, t)
        ap = ease_out(lt / 0.5)
        paste_center(f, arch, W / 2, 230 - 60 + arch.height / 2, ap, 0.96 + 0.04 * ap)
        rise(f, a, W / 2, 640, lt, 0.15, 0.5)
        rise(f, b1, W / 2, 790, lt, 0.3, 0.6, dy=0, scale_from=0.8)
        rise(f, b2, W / 2, 970, lt, 0.45, 0.6, dy=0, scale_from=0.8)
        bl = ease_out((lt - 0.75) / 0.5)
        if bl > 0:
            paste_center(f, lot, W / 2, 1090, bl, 0.6 * (0.3 + 0.7 * bl))
        rise(f, c, W / 2, 1240, lt, 0.9, 0.5)
        for k, (x, y, w) in enumerate(((300, 1560, 220), (780, 1560, 220), (540, 1680, 240))):
            T.diya_glow(f, x, y, w, 0.92 + 0.06 * math.sin(t * 11 + k * 2) + 0.04 * math.sin(t * 23 + k))
        rise(f, sh, W / 2, 1830, lt, 1.1, 0.5)
        fo = clamp((lt - (dur - 0.35)) / 0.35)
        if fo > 0:
            f.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fo))))
        if lt < 0.25:
            f.alpha_composite(Image.new("RGBA", (W, H), (8, 10, 30, int(255 * ease_io(1 - lt / 0.25)))))
        yield f


def render(seg):
    name, t0, t1 = seg
    out = f"{R.SEG}/{name}.mp4"
    S = R.build_stencil() if name == "t3" else None
    gen = {"t1": lambda: seg_t1(t0, t1), "t2": lambda: seg_t2(t0, t1),
           "t3": lambda: seg_t3(t0, t1, S), "t4": lambda: seg_t4(t0, t1)}[name]()
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
    with ProcessPoolExecutor(4) as ex:
        for r in ex.map(render, SEGMENTS):
            print(r, flush=True)
    lst = f"{R.SEG}/teaser_list.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{name}.mp4'\n" for name, _, _ in SEGMENTS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT], check=True)
    print("wrote", OUT)
