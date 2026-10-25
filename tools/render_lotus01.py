"""Render the Lotus stencil reel (Diwali 02) in the chosen Rose & Gold look: footage plays inside a gold ring framed by
slowly turning lotus petals; blush-to-rose background with gold mandala corners, drifting petals and bokeh.
~24.5s; the client's three voiceover lines sit in scenes 1, 2 and 6, the rest is visuals + on-screen text.

usage: cd tools && python3 render_lotus01.py <workdir> <out.mp4> [segment ...]
<workdir>/src holds L3.mp4 L4.mp4 L5.mp4 (VID-20261025-WA0003/4/5); fonts/ as for render_reel01_night.py.
"""
import math, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw

import render_diwali01 as R
import render_teaser01 as TT
import style_frames_teaser01 as T
import style_options_lotus01 as O
from render_diwali01 import W, H, FPS, clamp, ease_out, ease_io, ease_back, paste_center

OUT = sys.argv[2]
ONLY = sys.argv[3:]
CLEAN = "eq=contrast=1.05:saturation=1.1:brightness=0.02,unsharp=5:5:0.5"
SEGMENTS = [
    ("l1", 0.0, 3.0),    # VO: New day, new product!
    ("l2", 3.0, 7.0),    # VO: Toh is baar humne banaya hai lotus stencil.
    ("l3", 7.0, 10.5),   # printer bed, another angle
    ("l4", 10.5, 14.0),  # white lotus, slow motion
    ("l5", 14.0, 16.5),  # hand-held close-up
    ("l6", 16.5, 20.5),  # VO: Just fill in the colours and you're good to go!
    ("l7", 20.5, 24.5),  # end card: Order now!
]
RC = (540, 1130)   # ring centre
D = 760            # ring (photo) diameter


class Backdrop:
    """Rose gradient + gold mandala corners (static), with petals and bokeh drifting up (animated)."""
    def __init__(self, seed):
        f = O.grad(O.ROSE_D, (186, 50, 106), seed, c3=(232, 128, 160))
        mand = R.make_mandala(420)
        mand.putalpha(mand.getchannel("A").point(lambda v: v * 120 // 255))
        for x in (0, W):
            paste_center(f, mand.rotate(seed * 7, resample=Image.BICUBIC), x, 0)
        self.base = f
        rng = np.random.default_rng(seed)
        self.petals = [(rng.uniform(40, W - 40), rng.uniform(500, 2000), rng.uniform(0, 360), rng.uniform(25, 60),
                        rng.uniform(-40, 40), rng.uniform(0, 6.3)) for _ in range(12)]
        p = Image.new("RGBA", (50, 90), (0, 0, 0, 0))
        ImageDraw.Draw(p).ellipse((5, 0, 45, 90), fill=(255, 200, 215, 200))
        self.petal = p
        self.bokeh = []
        for k in range(26):
            r = int(rng.uniform(14, 40))
            c = [O.PINK, (255, 200, 210), T.GOLD][k % 3]
            im = Image.new("RGBA", (r * 2 + 4, r * 2 + 4), (0, 0, 0, 0))
            ImageDraw.Draw(im).ellipse((2, 2, 2 + 2 * r, 2 + 2 * r), fill=c + (int(rng.uniform(50, 110)),), outline=c + (140,), width=2)
            self.bokeh.append((im, rng.uniform(0, W), rng.uniform(700, 2000), rng.uniform(10, 30), rng.uniform(0, 6.3)))

    def frame(self, t):
        f = self.base.copy()
        for im, x, y, v, ph in self.bokeh:
            paste_center(f, im, x + 10 * math.sin(t * 0.7 + ph), 700 + (y - v * t - 700) % 1300, 0.7 + 0.3 * math.sin(t * 2 + ph))
        for x, y, rot, v, spin, ph in self.petals:
            yy = 500 + (y - v * t - 500) % 1500
            paste_center(f, self.petal, x + 25 * math.sin(t * 0.8 + ph), yy, 0.9, rot=rot + spin * t)
        return f


class Ring:
    """Gold ring photo window with a turning halo of lotus petals (as in style option B)."""
    def __init__(self, d=D):
        self.d = d
        S = d + 300
        c = S / 2
        pet = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        for k in range(16):
            a = 2 * math.pi * k / 16
            p = Image.new("RGBA", (120, 220), (0, 0, 0, 0))
            ImageDraw.Draw(p).ellipse((6, 0, 114, 220), fill=(255, 190, 210, 235), outline=T.GOLD + (255,), width=3)
            p = p.rotate(-math.degrees(a) - 90, expand=True, resample=Image.BICUBIC)
            paste_center(pet, p, c + (d / 2 + 40) * math.cos(a), c + (d / 2 + 40) * math.sin(a))
        paste_center(pet, R.blob(int(d * 0.4), T.GOLD, 160), c, c)
        self.petals = pet
        ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ring)
        dr.ellipse((150 - 6, 150 - 6, 150 + d + 6, 150 + d + 6), outline=T.GOLD + (255,), width=10)
        dr.ellipse((150 - 20, 150 - 20, 150 + d + 20, 150 + d + 20), outline=T.GOLD_L + (200,), width=3)
        self.ring = ring
        m = Image.new("L", (d, d), 0)
        ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255)
        self.mask = m

    def draw(self, f, fr, src, s, t, alpha=1.0, scale=1.0):
        """fr: W x H footage frame; the circle shows a d/s square of it centred on src."""
        box = self.d / s
        x0 = clamp(src[0] - box / 2, 0, W - box)
        y0 = clamp(src[1] - box / 2, 0, H - box)
        ph = fr.resize((self.d, self.d), Image.BILINEAR, box=(x0, y0, x0 + box, y0 + box))
        ph.putalpha(self.mask)
        out = self.petals.rotate(t * 6, resample=Image.BILINEAR)
        out.alpha_composite(ph, (150, 150))
        out.alpha_composite(self.ring)
        paste_center(f, out, RC[0], RC[1], alpha, scale)


def dip(f, lt, dur, fin=0.25, fout=0.2):
    a = max(clamp(1 - lt / fin), clamp(1 - (dur - lt) / fout))
    if a > 0:
        f.alpha_composite(Image.new("RGBA", (W, H), (70, 10, 40, int(255 * ease_io(a)))))


def footage_scene(t0, t1, seed, shots, texts, ring_in=False):
    """shots: list of (clip, ss, src_dur, out_dur, src_point, s); texts: callable(f, lt) drawing the text."""
    bd, rg = Backdrop(seed), Ring()
    frames = []
    for name, ss, sd, od, src, s in shots:
        frames += [(fr, src, s) for fr in R.footage(name, ss, sd, od, (1.0, 1.0), grade=CLEAN)]
    dur = t1 - t0
    for i, (fr, src, s) in enumerate(frames[:int(round(dur * FPS))]):
        t = t0 + i / FPS
        lt = t - t0
        f = bd.frame(t)
        p = ease_out(lt / 0.6) if ring_in else 1.0
        rg.draw(f, fr, src, s * (1 + 0.04 * lt / dur), t, p, 0.85 + 0.15 * ease_back(lt / 0.7) if ring_in else 1.0)
        texts(f, lt)
        dip(f, lt, dur)
        yield f


def seg_l1(t0, t1):
    a = T.glow_text("New day,", T.allura(140), T.CREAM, glow=(255, 200, 220), ga=90)
    b = T.glow_text("NEW PRODUCT!", T.yeseva(120), (T.GOLD_L, T.GOLD))

    def texts(f, lt):
        TT.wipe(f, a, W / 2, 260, ease_io((lt - 0.15) / 0.7))
        TT.rise(f, b, W / 2, 420, lt, 0.7, 0.6, dy=0, scale_from=0.7)
    return footage_scene(t0, t1, 4, [("L4", 12.0, 1.8, t1 - t0, (540, 720), 0.72)], texts, ring_in=True)


def seg_l2(t0, t1):
    a = T.glow_text("Is baar humne banaya...", T.allura(110), T.CREAM, glow=(255, 200, 220), ga=90)
    b = T.glow_text("LOTUS STENCIL", T.yeseva(130), (T.GOLD_L, T.GOLD))
    c = R.pill("Designed & 3D printed by us", T.mont(36), fg=O.ROSE_D, bg=T.GOLD_L, pad=(40, 18))

    def texts(f, lt):
        TT.wipe(f, a, W / 2, 260, ease_io((lt - 0.15) / 0.8))
        TT.rise(f, b, W / 2, 410, lt, 1.0, 0.6, dy=0, scale_from=0.7)
        TT.rise(f, c, W / 2, 1780, lt, 1.6, 0.45, dy=0, scale_from=0.7)
    return footage_scene(t0, t1, 14, [("L4", 0.0, 4.0, t1 - t0, (540, 960), 0.95)], texts)


def seg_l3(t0, t1):
    a = T.glow_text("Fresh from our 3D printer", T.allura(92), T.CREAM, glow=(255, 200, 220), ga=90)

    def texts(f, lt):
        TT.wipe(f, a, W / 2, 330, ease_io((lt - 0.2) / 0.9))
    return footage_scene(t0, t1, 15, [("L3", 0.0, 3.5, t1 - t0, (560, 480), 0.8)], texts)


def seg_l4(t0, t1):
    a = T.glow_text("LOTUS RANGOLI STENCIL", T.mont(40), T.CREAM, ga=0, track=10)

    def texts(f, lt):
        TT.rise(f, a, W / 2, 1760, lt, 0.3, 0.6)
        TT.burst(f, 170, 620, 70, T.GOLD, lt, 0.6)
        TT.burst(f, 900, 1620, 60, T.GOLD_L, lt, 1.6)
    return footage_scene(t0, t1, 16, [("L4", 10.5, 2.0, t1 - t0, (540, 690), 0.76)], texts)


def seg_l5(t0, t1):
    a = T.glow_text("Diwali special", T.allura(120), T.GOLD_L, glow=(255, 200, 120), ga=120)

    def texts(f, lt):
        TT.wipe(f, a, W / 2, 330, ease_io((lt - 0.2) / 0.8))
    return footage_scene(t0, t1, 17, [("L3", 5.8, 1.6, t1 - t0, (560, 1250), 0.72)], texts)


def seg_l6(t0, t1):
    a = T.glow_text("Just fill in the colours", T.allura(110), T.CREAM, glow=(255, 200, 220), ga=90)
    b = T.glow_text("& you're good to go!", T.yeseva(96), (T.GOLD_L, T.GOLD))

    def texts(f, lt):
        TT.wipe(f, a, W / 2, 260, ease_io((lt - 0.1) / 0.9))
        TT.rise(f, b, W / 2, 400, lt, 2.0, 0.6, dy=0, scale_from=0.7)
        TT.burst(f, 180, 700, 70, T.GOLD, lt, 2.2)
        TT.burst(f, 900, 640, 60, O.PINK, lt, 2.6)
    return footage_scene(t0, t1, 18, [("L5", 0.5, 2.0, 2.0, (550, 870), 0.85), ("L5", 6.0, 2.0, 2.0, (550, 750), 0.85)], texts)


def seg_l7(t0, t1):
    bd = Backdrop(6)
    lot = O.lotus_icon(T.GOLD, T.AMBER, 0.7)
    a = T.glow_text("Order now!", T.yeseva(150), (T.GOLD_L, T.GOLD))
    b = T.glow_text("LOTUS RANGOLI STENCIL", T.mont(36), T.CREAM, ga=0, track=8)
    c = R.pill("DM to order", T.mont(48), fg=O.ROSE_D, bg=T.GOLD_L, pad=(56, 22))
    d = T.glow_text("शुभ दीपावली", T.tiro(84), T.GOLD_L, ga=120)
    dur = t1 - t0
    for i in range(int(round(dur * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bd.frame(t)
        bl = ease_out((lt - 0.1) / 0.6)
        if bl > 0:
            paste_center(f, lot, W / 2, 500, bl, 0.4 + 0.6 * bl)
        TT.rise(f, a, W / 2, 730, lt, 0.3, 0.6, dy=0, scale_from=0.7)
        TT.rise(f, b, W / 2, 950, lt, 0.6, 0.5)
        if lt > 0.9:
            pulse = 1 + 0.04 * math.sin((lt - 0.9) * 7)
            paste_center(f, c, W / 2, 1110, ease_out((lt - 0.9) / 0.3), pulse * (0.7 + 0.3 * ease_back((lt - 0.9) / 0.4)))
        for k, (x, y, w) in enumerate(((300, 1500, 220), (780, 1500, 220), (540, 1620, 240))):
            T.diya_glow(f, x, y, w, 0.92 + 0.06 * math.sin(t * 11 + k * 2) + 0.04 * math.sin(t * 23 + k))
        TT.rise(f, d, W / 2, 1800, lt, 1.2, 0.5)
        dip(f, lt, dur, fin=0.25, fout=0.01)
        fo = clamp((lt - (dur - 0.4)) / 0.4)
        if fo > 0:
            f.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fo))))
        yield f


def render(seg):
    name, t0, t1 = seg
    out = f"{R.SEG}/{name}.mp4"
    gen = globals()[f"seg_{name}"](t0, t1)
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
    return f"{name}: {count}/{n} frames"


if __name__ == "__main__":
    todo = [s for s in SEGMENTS if not ONLY or s[0] in ONLY]
    with ProcessPoolExecutor(4) as ex:
        for r in ex.map(render, todo):
            print(r, flush=True)
    lst = f"{R.SEG}/lotus_list.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{name}.mp4'\n" for name, _, _ in SEGMENTS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT], check=True)
    print("wrote", OUT)
