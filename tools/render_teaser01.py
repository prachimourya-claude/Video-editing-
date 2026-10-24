"""Render the 10s teaser for Diwali 01 (Kalash rangoli stencil): hints and a backlit silhouette, no reveal, no handle.

usage: python3 render_teaser01.py <workdir> <out.mp4>
Same <workdir> as render_diwali01.py; reuses its sprites, text styles and footage reader.
"""
import math, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
import cv2
import numpy as np
from PIL import Image, ImageFilter

import render_diwali01 as R
from render_diwali01 import W, H, FPS, clamp, ease_out, ease_io, paste_center, pop, plain_text, gold_text, draw_diya

BASE, OUT = sys.argv[1], sys.argv[2]
SEGMENTS = [
    ("t1", 0.0, 2.2),   # Is Diwali... kuch naya aa raha hai
    ("t2", 2.2, 4.6),   # glimpses of the printer: kuch khaas ban raha hai
    ("t3", 4.6, 7.9),   # backlit silhouette: guess karo, kya hai?
    ("t4", 7.9, 10.0),  # coming soon
]
R.CUTS = [s for _, s, _ in SEGMENTS[1:]]


def seg_t1(t0, t1):
    bg = R.night_bg(12)
    a = gold_text("Is Diwali...", R.vibes(160), stroke=2)
    b = plain_text("kuch naya aa raha hai", R.pop_sb(70))
    bursts = [(260, 520, 0.5, (255, 190, 80), 41), (830, 430, 1.1, (255, 110, 160), 42)]
    for i in range(int(round((t1 - t0) * FPS))):
        t = t0 + i / FPS
        f = bg.copy()
        R.draw_fireworks(f, t, bursts)
        pop(f, a, W / 2, 860, t, 0.2, 0.6)
        pop(f, b, W / 2, 1040, t, 0.8, 0.4, rise=20, from_scale=0.9)
        for k in range(5):
            draw_diya(f, 160 + k * 190, 1450, 150, t, k, clamp((t - 0.1 - k * 0.15) / 0.3))
        R.overlay_common(f, t, toran_drop=clamp(t / 0.7))
        yield f


def seg_t2(t0, t1):
    # three tight, dark glimpses so the product never shows whole
    shots = [("C", 6.0, 0.8, (2.8, 3.0), (0.4, 0.3)),
             ("B", 9.4, 0.8, (1.7, 1.9), (0.5, 0.62)),
             ("C", 11.0, 0.8, (2.8, 3.0), (0.62, 0.5))]
    txt_a = plain_text("Kuch khaas", R.pop_sb(84))
    txt_b = gold_text("ban raha hai...", R.playfair(120))
    frames = []
    for name, ss, d, z, c in shots:
        frames += list(R.footage(name, ss, d, d, z, c))
    n = int(round((t1 - t0) * FPS))
    frames = (frames + frames[-1:] * n)[:n]
    dark = Image.new("RGBA", (W, H), (10, 2, 6, 110))
    for i, f in enumerate(frames):
        t = t0 + i / FPS
        lt = t - t0
        f.alpha_composite(dark)
        R.top_scrim(f, 600, 140)
        R.bottom_scrim(f, 900, 220)
        pop(f, txt_a, W / 2, 1290, lt, 0.15, 0.4, rise=20, from_scale=0.9)
        pop(f, txt_b, W / 2, 1430, lt, 0.45, 0.5)
        # quick white pop between the glimpses
        for c in (0.8, 1.6):
            fl = max(0, 1 - abs(lt - c) / 0.08)
            if fl > 0:
                f.alpha_composite(Image.new("RGBA", (W, H), (255, 236, 200, int(140 * fl))))
        R.overlay_common(f, t, sparkles=0.5)
        yield f


def silhouette(S, height):
    st = R.stencil_img(S, height / S.height)
    a = np.asarray(st.getchannel("A")).astype(np.float32) / 255
    rim = np.clip(a - cv2.erode(a, np.ones((9, 9), np.uint8)), 0, 1)
    rim = cv2.GaussianBlur(rim, (0, 0), 2.5) * 1.8
    sil = np.zeros(a.shape + (4,), np.float32)
    sil[..., :3] = (22, 5, 10)
    sil[..., :3] += np.clip(rim, 0, 1)[..., None] * (np.array(R.GOLD_L, np.float32) - (22, 5, 10))
    sil[..., 3] = a * 255
    glow = Image.new("RGBA", (st.width + 200, st.height + 200), (255, 170, 60, 0))
    gm = Image.new("L", glow.size, 0)
    gm.paste(st.getchannel("A"), (100, 100))
    glow.putalpha(gm.filter(ImageFilter.GaussianBlur(45)).point(lambda v: v * 190 // 255))
    return Image.fromarray(sil.clip(0, 255).astype(np.uint8), "RGBA"), st, glow


def seg_t3(t0, t1, S):
    bg = R.night_bg(14)
    mand = R.make_mandala(560)
    sil, white, glow = silhouette(S, 900)
    q1 = plain_text("Guess karo...", R.pop_sb(76))
    q2 = gold_text("kya hai?", R.playfair(140))
    yy, xx = np.mgrid[0:white.height, 0:white.width].astype(np.float32)
    diag = (xx + yy * 0.6) / (white.width + white.height * 0.6)
    wa = np.asarray(white.getchannel("A")).astype(np.float32)
    for i in range(int(round((t1 - t0) * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bg.copy()
        paste_center(f, mand.rotate(lt * 12, resample=Image.BICUBIC), W / 2, 1000, 0.3, 1.05)
        a = ease_out(lt / 0.6)
        s = 1.08 - 0.08 * ease_io(lt / (t1 - t0))
        paste_center(f, glow, W / 2, 1000, a * (0.75 + 0.25 * math.sin(lt * 4)), s)
        frame = sil.copy()
        # a narrow light sweep crosses the stencil once, showing just a hint of the design
        sweep = -0.3 + 1.6 * ease_io((lt - 1.0) / 1.4)
        band = np.clip(1 - np.abs(diag - sweep) / 0.07, 0, 1) * 0.55
        hint = white.copy()
        hint.putalpha(Image.fromarray((wa * band).astype(np.uint8)))
        frame.alpha_composite(hint)
        paste_center(f, frame, W / 2, 1000, a, s)
        pop(f, q1, W / 2, 330, lt, 0.3, 0.4, rise=20, from_scale=0.9)
        pop(f, q2, W / 2, 470, lt, 0.6, 0.5)
        for k, x in enumerate((120, W - 120)):
            draw_diya(f, x, 1650, 130, t, k + 11, 1)
        R.overlay_common(f, t, toran_drop=0, sparkles=0.8)
        yield f


def seg_t4(t0, t1):
    bg = R.night_bg(16)
    mand = R.make_mandala(560)
    a = plain_text("Launching this Diwali", R.pop_sb(64))
    b = gold_text("Coming Soon", R.playfair(140))
    c = plain_text("Dhanteras se pehle", R.pop_sb(56))
    d = gold_text("शुभ दीपावली", R.yatra(110), stroke=2)
    bursts = [(220, 420, 0.15, (255, 190, 80), 51), (860, 360, 0.45, (255, 110, 160), 52),
              (540, 280, 0.9, (140, 220, 255), 53), (300, 600, 1.3, (255, 220, 120), 54)]
    for i in range(int(round((t1 - t0) * FPS))):
        t = t0 + i / FPS
        lt = t - t0
        f = bg.copy()
        paste_center(f, mand.rotate(lt * 10, resample=Image.BICUBIC), W / 2, 960, 0.4 * ease_out(lt / 0.5))
        R.draw_fireworks(f, lt, bursts)
        pop(f, a, W / 2, 800, lt, 0.1, 0.4, rise=20, from_scale=0.9)
        pop(f, b, W / 2, 960, lt, 0.3, 0.6, from_scale=0.3)
        pop(f, c, W / 2, 1110, lt, 0.7, 0.4, rise=20, from_scale=0.9)
        pop(f, d, W / 2, 1400, lt, 0.9, 0.5)
        for k in range(5):
            draw_diya(f, 160 + k * 190, 1620, 130, t, k + 20, 1)
        R.overlay_common(f, t, sparkles=1.0)
        # fade out on the last frames
        fo = clamp((lt - (t1 - t0 - 0.35)) / 0.35)
        if fo > 0:
            f.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fo))))
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
