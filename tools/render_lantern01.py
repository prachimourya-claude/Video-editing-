"""Render the Star Lantern reel (Diwali 03), look F "Glow Night": the client's whole clip plays full screen in order,
with quiet labels and twinkling string lights; when the room lights go off the shot tints to a purple-pink night,
sky lanterns float up and soft line fireworks burst, then "STAR LANTERN · Order now · DM to order". 32.5s, cut to
the client's voiceover (add it with tools/mix_lantern01_vo.sh). Shot 2 is a short look ahead at the finished, lit
lantern so "star pattern top, terracotta-look base" plays over both parts.

usage: cd tools && python3 render_lantern01.py <workdir> <out.mp4> [segment ...]
<workdir>/src/T1.mp4 = VID-20261026-WA0001 (44s); fonts/ as for render_reel01_night.py.
"""
import math, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw

import render_diwali01 as R
import render_teaser01 as TT
import style_frames_teaser01 as T
from render_diwali01 import W, H, FPS, clamp, ease_out, ease_io, ease_back, paste_center

OUT = sys.argv[2]
ONLY = sys.argv[3:]
CLEAN = "eq=contrast=1.04:saturation=1.08,unsharp=5:5:0.5"
CREAM = (255, 246, 230)
PINK = (255, 105, 160)
SKYBLUE = (120, 220, 255)
LIGHTS_OFF = 39.1   # source second at which the room lights go off
# (name, reel start, reel end, source start, source end); cut to the client's voiceover (tools/mix_lantern01_vo.sh)
SEGMENTS = [
    ("t1", 0.0, 8.0, 0.0, 7.5),      # shade on the printer bed, picked up, turned       | VO 1-3
    ("t2", 8.0, 13.4, 30.0, 35.4),   # preview: the finished lantern, lit (top + base)   | VO 4-5
    ("t3", 13.4, 19.0, 7.5, 23.5),   # inner piece, tea light switched on, into the base | VO 6
    ("t4", 19.0, 23.5, 23.5, 30.0),  # shade goes on, star pattern lights up             | VO 6 end, VO 7
    ("t6", 23.5, 32.5, 37.6, 44.0),  # lights off: glow night + order                    | VO 8
]


def label(t, size=96):
    return T.glow_text(t, T.allura(size), CREAM, glow=(255, 150, 200), ga=110)


class Lights:
    """String lights across the top; bulbs twinkle."""
    def __init__(self, y0=30, sag=80, n=16):
        self.wire = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
        pts = [(W * k / 60, y0 + sag * math.sin(math.pi * k / 60)) for k in range(61)]
        ImageDraw.Draw(self.wire).line(pts, fill=(80, 60, 50, 255), width=3)
        self.bulbs = [(W * (k + 0.5) / n, y0 + sag * math.sin(math.pi * (k + 0.5) / n) + 14, k * 1.7) for k in range(n)]
        self.glow = R.blob(18, (255, 220, 140), 170)

    def draw(self, f, t, alpha=1.0):
        f.alpha_composite(self.wire)
        d = ImageDraw.Draw(f)
        for x, y, ph in self.bulbs:
            tw = 0.65 + 0.35 * math.sin(t * 3 + ph)
            paste_center(f, self.glow, x, y, alpha * tw)
            d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=(255, 236, 180, int(255 * alpha * (0.75 + 0.25 * tw))))


def frames(ss, se, dur, zoom=(1.0, 1.03)):
    return R.footage("T1", ss, se - ss, dur, zoom, (0.5, 0.45), grade=CLEAN)


def day_segment(t0, t1, ss, se, texts):
    lights = Lights()
    dur = t1 - t0
    for i, f in enumerate(frames(ss, se, dur)):
        t = t0 + i / FPS
        lt = t - t0
        lights.draw(f, t)
        texts(f, lt, dur)
        yield f


def fade_out(lt, dur, t_out=0.3):
    """Labels fade just before a cut so they don't pop off."""
    return clamp((dur - lt) / t_out)


def seg_t1(t0, t1, ss, se):
    a = label("Another day, another product", 82)
    b = T.glow_text("STAR LANTERN", T.yeseva(110), (T.GOLD_L, T.GOLD))
    c = T.glow_text("3D PRINTED", T.mont(38), CREAM, ga=0, track=12)

    def texts(f, lt, dur):
        o = fade_out(lt, dur)
        TT.wipe(f, a, W / 2, 270, ease_io((lt - 0.2) / 0.8), clamp((2.2 - lt) / 0.3))
        if lt > 2.3:
            paste_center(f, b, W / 2, 330, ease_out((lt - 2.3) / 0.5) * o, 0.75 + 0.25 * ease_back((lt - 2.3) / 0.6))
        if lt > 6.9:
            paste_center(f, c, W / 2, 450, ease_out((lt - 6.9) / 0.4) * o)
    return day_segment(t0, t1, ss, se, texts)


def two_labels(top, bottom, t_top, t_bottom):
    a, b = label(top), label(bottom)

    def texts(f, lt, dur):
        o = fade_out(lt, dur)
        TT.wipe(f, a, W / 2, 280, ease_io((lt - t_top) / 0.7), o)
        TT.wipe(f, b, W / 2, 390, ease_io((lt - t_bottom) / 0.7), o)
    return texts


def simple_label(text, t_in=0.2):
    im = label(text)

    def texts(f, lt, dur):
        TT.wipe(f, im, W / 2, 300, ease_io((lt - t_in) / 0.7), fade_out(lt, dur))
    return texts


def seg_t2(t0, t1, ss, se):
    return day_segment(t0, t1, ss, se, two_labels("Star pattern top", "Terracotta-look base", 0.4, 1.9))


def seg_t3(t0, t1, ss, se):
    return day_segment(t0, t1, ss, se, simple_label("Tea light inside", 2.6))


def seg_t4(t0, t1, ss, se):
    return day_segment(t0, t1, ss, se, simple_label("Replaceable tea light", 0.6))


def seg_t6(t0, t1, ss, se):
    """Lights off: night tint fades in, sky lanterns float up, line fireworks, then name + order."""
    dur = t1 - t0
    off = (LIGHTS_OFF - ss) * dur / (se - ss)       # reel-local second of the lights going off
    lights = Lights()
    lan = TT.Lanterns(9, 31, 900, 2100, avoid=(330, 500, 750, 1500))
    yy = np.linspace(0, 1, H)[:, None, None]
    tint = (np.array([60, 20, 90], np.float32) * (1 - yy) + np.array([120, 20, 80], np.float32) * yy)
    tint = np.broadcast_to(tint, (H, W, 3)).astype(np.float32)
    a = label("Lights off", 120)
    b = T.glow_text("STAR LANTERN", T.yeseva(110), (T.GOLD_L, T.GOLD))
    c = T.glow_text("3D printed tea-light lantern", T.allura(84), CREAM, glow=(255, 150, 200), ga=90)
    d = R.pill("Order now  ·  DM to order", T.mont(44), fg=(90, 20, 60), bg=T.GOLD_L, pad=(46, 22))
    sh = T.glow_text("Happy Diwali", T.allura(110), CREAM, glow=(255, 150, 200), ga=110)
    for i, f in enumerate(frames(ss, se, dur, (1.0, 1.08))):
        t = t0 + i / FPS
        lt = t - t0
        night = ease_io((lt - off - 0.2) / 1.0)
        if lt < off + 0.2:
            lights.draw(f, t)
        if night > 0:
            px = np.asarray(f.convert("RGB")).astype(np.float32)
            px = px * (1 - 0.15 * night) + tint * 0.35 * night
            f = Image.fromarray(px.clip(0, 255).astype(np.uint8)).convert("RGBA")
            # lanterns rise in from below once it is dark
            lan.draw(f, max(0.0, lt - off))
            TT.burst(f, 220, 420, 90, PINK, lt, off + 1.0)
            TT.burst(f, 860, 360, 80, T.GOLD, lt, off + 1.6)
            TT.burst(f, 880, 1500, 70, SKYBLUE, lt, off + 2.4)
            TT.burst(f, 200, 1380, 60, T.GOLD_L, lt, off + 3.4)
        e = lt - off
        if 0.6 < e < 3.4:
            TT.wipe(f, a, W / 2, 330, ease_io((e - 0.6) / 0.8), clamp((3.4 - e) / 0.3))
        TT.rise(f, b, W / 2, 300, e, 3.6, 0.7, dy=0, scale_from=0.75)
        TT.wipe(f, c, W / 2, 420, ease_io((e - 4.1) / 0.8))
        if e > 4.6:
            pulse = 1 + 0.035 * math.sin((e - 4.6) * 6)
            paste_center(f, d, W / 2, 1600, ease_out((e - 4.6) / 0.35), pulse * (0.7 + 0.3 * ease_back((e - 4.6) / 0.45)))
        TT.rise(f, sh, W / 2, 1760, e, 5.2, 0.6)
        fo = clamp((lt - (dur - 0.4)) / 0.4)
        if fo > 0:
            f.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fo))))
        yield f


def render(seg):
    name, t0, t1, ss, se = seg
    out = f"{R.SEG}/{name}.mp4"
    gen = globals()[f"seg_{name}"](t0, t1, ss, se)
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
    lst = f"{R.SEG}/lantern_list.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{s[0]}.mp4'\n" for s in SEGMENTS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT], check=True)
    print("wrote", OUT)
