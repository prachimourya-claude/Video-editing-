"""Render the can-opener reel (heart + chocolate ring-pull openers for long nails) in the "Group Chat" look:
the creator's own story, told as phone chat bubbles over the real footage. A trip chat with friends (nails done, can't
open a can, wish there was something small and cute for the keychain, so I made one), then a salon chat (custom names,
bulk), a quick "more shapes" glimpse and "DM to get yours now". 59s (~3s per bubble; both openers shown until the can
opens); floating "No broken nails!" as the chocolate one opens the can. Voice + chat sounds: tools/mix_opener01_vo.sh.

usage: cd tools && python3 render_opener01.py <workdir> <out.mp4> [segment ...]
<workdir>/src holds O18-O22.mp4, N1.mp4 (Pinterest nails clip) + P1/P2.jpg, <workdir>/refs/crop_*.jpg (see more_shapes_opener.py), fonts/ as before.
"""
import math, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw, ImageFont

import render_diwali01 as R
import style_options_opener01 as O
import style_options_opener02 as C
import more_shapes_opener as M
from render_diwali01 import W, H, FPS, clamp, ease_out, ease_back, paste_center

OUT = sys.argv[2]
ONLY = sys.argv[3:]
F = R.BASE + "/fonts/"
font = lambda name, s: ImageFont.truetype(F + name, s)
CLEAN = "eq=contrast=1.04:saturation=1.08,unsharp=5:5:0.5"
INK = (20, 20, 22)

# (name, start, end, footage) - footage: ("clip", source start, source end) or ("photo", P1/P2, zoom from, zoom to)
SEGMENTS = [
    ("c0", 0.0, 6.0, ("clip", "N1", 0.0, 4.45)),      # fresh nails (Pinterest clip): "got my nails done"
    ("c1", 6.0, 12.0, ("clip", "O20", 0.0, 2.5)),     # can in hand: "can't open my can"
    ("c1b", 12.0, 18.5, ("clip", "O22", 0.0, 14.0)),  # prints waiting on the bed: "wish I had something…"
    ("c2", 18.5, 22.5, ("clip", "O22", 15.0, 27.0)),  # bed flexed, openers pop off: "so I made one"
    ("c3", 22.5, 29.5, ("clip", "O20", 3.2, 20.8)),   # heart: hooked on, lifted, can open (tab ~20s)
    ("c4a", 29.5, 33.5, ("clip", "O18", 2.0, 16.0)),  # chocolate hooked on the tab
    ("c4b", 33.5, 38.5, ("clip", "O18", 16.0, 21.5)), # chocolate opening at near real speed (tab ~19.5s)
    ("c5", 38.5, 42.5, ("clip", "O19", 15.5, 23.5)),  # both held at the printer: keychain hole
    ("c6", 42.5, 51.5, ("photo", "P2", 1.0, 1.12)),   # salon chat over the initials close-up
    ("c7", 51.5, 55.5, ("shapes",)),                  # more shapes glimpse
    ("c8", 55.5, 59.0, ("photo", "P1", 1.0, 1.08)),   # DM to order
]
CHAT_SWITCH = 42.5  # trip chat -> salon chat

# chat bubbles: (appear time, chat, right side?, text, emoji, sender name); ~3s apart so each can be read
CHAT_A = ("trip gang", "Riya, Sana, you")
CHAT_B = ("Your Nail Studio", "business account")
BUBBLES = [
    (0.6, "A", False, "how's the trip?", "🏔", "Riya"),
    (3.4, "A", True, "amazing! got my nails done", "💅", None),
    (6.4, "A", True, "but now I can't open my can", "😭", None),
    (9.3, "A", False, "lol the long nail struggle", None, "Sana"),
    (12.3, "A", True, "wish I had something small + cute", None, None),
    (15.4, "A", True, "that I could just hang on my bag", "🔑", None),
    (18.8, "A", True, "so I made one", "🤭", None),
    (23.4, "A", False, "WAIT it works??", "😳", "Riya"),
    (30.0, "A", True, "chocolate one too", "🍫", None),
    (38.9, "A", True, "has a keychain hole", "✨", None),
    (43.1, "B", False, "can you put my salon name on it?", None, "Your Nail Studio"),
    (46.1, "B", True, "yes, any name", "✨", None),
    (48.9, "B", True, "bulk for salons too", "🎀", None),
    (55.9, "B", True, "DM to get yours now", "📩", None),
]
TOP = 175        # first bubble y
MAX_SHOWN = 4    # older bubbles scroll away


def header(title, sub):
    im = Image.new("RGBA", (W, 150), (248, 248, 250, 245))
    d = ImageDraw.Draw(im)
    d.text((40, 75), "‹", font=font("inter_b.ttf", 70), fill=(10, 132, 255), anchor="lm")
    d.ellipse((100, 30, 190, 120), fill=(255, 190, 215, 255))
    paste_center(im, C.emoji("💅", 52), 145, 75)
    d.text((215, 54), title, font=font("inter_b.ttf", 42), fill=INK, anchor="lm")
    d.text((215, 104), sub, font=font("inter_m.ttf", 30), fill=(140, 140, 150), anchor="lm")
    d.line((0, 149, W, 149), fill=(210, 210, 216, 255), width=2)
    return R.with_shadow(im, offset=(0, 4), blur=10, alpha=60, color=(0, 0, 0))


def typing():
    im = Image.new("RGBA", (170, 96), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, 160, 88), radius=44, fill=(236, 236, 240, 255))
    return im


class Chat:
    def __init__(self):
        self.headers = {"A": header(*CHAT_A), "B": header(*CHAT_B)}
        self.imgs = [C.bubble(text, right, emo, name if not right else None, maxw=1010) for _, _, right, text, emo, name in BUBBLES]
        self.typing = typing()

    def draw(self, f, t, show=True):
        if not show:
            return
        chat = "B" if t >= CHAT_SWITCH else "A"
        f.alpha_composite(self.headers[chat], (-20, -20))
        shown = [i for i, b in enumerate(BUBBLES) if b[1] == chat and b[0] <= t][-MAX_SHOWN:]
        # typing dots before the next friend's (left) bubble
        nxt = [i for i, b in enumerate(BUBBLES) if b[1] == chat and t < b[0] <= t + 0.7 and not b[2]]
        y = TOP
        for k, i in enumerate(shown):
            at, _, right, *_ = BUBBLES[i]
            im = self.imgs[i]
            p = ease_out((t - at) / 0.3)
            s = 0.85 + 0.15 * ease_back((t - at) / 0.35)
            x = W - im.width - 24 if right else 24
            paste_center(f, im, x + im.width / 2, y + im.height / 2 + 20 * (1 - p), p, s)
            y += im.height + 8
        if nxt:
            d = ImageDraw.Draw(f)
            f.alpha_composite(self.typing, (34, int(y)))
            for j in range(3):
                a = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * 10 - j * 1.1))
                cx = 34 + 46 + j * 34
                d.ellipse((cx - 11, y + 33, cx + 11, y + 55), fill=(150, 150, 158, int(255 * a)))


def photo_frames(name, z0, z1, n):
    base = O.photo_full(name, 0.4)
    for i in range(n):
        z = z0 + (z1 - z0) * i / max(1, n - 1)
        cw, ch = W / z, H / z
        x0, y0 = (W - cw) / 2, (H - ch) * 0.45
        yield base.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


def shapes_frames(n):
    tiles = [M.tile(nm) for nm in M.NAMES]
    title = font("poppins_xb.ttf", 100)
    sub = font("inter_m.ttf", 42)
    tag = R.pill("reference designs · made to order", font("inter_m.ttf", 34), fg=(255, 255, 255), bg=(60, 40, 50), pad=(30, 14))
    for i in range(n):
        lt = i / FPS
        f = Image.new("RGBA", (W, H), (255, 240, 246, 255))
        d = ImageDraw.Draw(f)
        d.text((W / 2, 170), "More shapes", font=title, fill=(60, 40, 50), anchor="mm")
        d.text((W / 2, 270), "any colour · your name on it", font=sub, fill=(150, 90, 120), anchor="mm")
        for k, tl in enumerate(tiles):
            r, c = divmod(k, 3)
            st = 0.15 + k * 0.12
            p = ease_out((lt - st) / 0.3)
            if p > 0:
                paste_center(f, tl, W / 2 + (c - 1) * 340, 590 + r * 430 + 30 * (1 - p), p, 0.85 + 0.15 * ease_back((lt - st) / 0.4))
        paste_center(f, tag, W / 2, 1840, ease_out((lt - 1.4) / 0.3))
        yield f


def floating_text(f, lt):
    """'No broken nails!' floats up and bobs over the chocolate opener as the tab lifts (c4b)."""
    if lt < 3.0:
        return
    e = lt - 3.0
    if not hasattr(floating_text, "im"):
        from render_diwali01 import text_mask
        m = text_mask("No broken nails!", font("poppins_xb.ttf", 96))
        txt = Image.new("RGBA", m.size, (255, 255, 255, 0))
        txt.putalpha(m)
        w, h = txt.width + 80, txt.height + 40
        card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=(240, 90, 150, 240))
        card.alpha_composite(txt, (40, 20))
        floating_text.im = R.with_shadow(card, offset=(0, 10), blur=16, alpha=110, color=(60, 10, 30))
        floating_text.nail = C.emoji("💅", 90)
    a = ease_out(e / 0.35)
    y = 1450 - 60 * ease_out(e / 0.6) + 10 * math.sin(e * 4)
    paste_center(f, floating_text.im, W / 2, y, a, (0.7 + 0.3 * ease_back(e / 0.45)) * (1 + 0.02 * math.sin(e * 6)))
    paste_center(f, floating_text.nail, W / 2 + floating_text.im.width / 2 - 20, y - 70, a, 1, rot=12 * math.sin(e * 3))


def end_overlay(f, lt):
    pill = R.pill("Order now  ·  DM to order", font("poppins_xb.ttf", 50), fg=(255, 255, 255), bg=(10, 132, 255), pad=(50, 24))
    if lt > 0.7:
        pulse = 1 + 0.035 * math.sin((lt - 0.7) * 7)
        paste_center(f, pill, W / 2, 1780, ease_out((lt - 0.7) / 0.3), pulse * (0.7 + 0.3 * ease_back((lt - 0.7) / 0.4)))


def render(seg):
    name, t0, t1, src = seg
    n = int(round((t1 - t0) * FPS))
    if src[0] == "clip":
        frames = R.footage(src[1], src[2], src[3] - src[2], t1 - t0, (1.0, 1.04), (0.5, 0.55), grade=CLEAN)
    elif src[0] == "photo":
        frames = photo_frames(src[1], src[2], src[3], n)
    else:
        frames = shapes_frames(n)
    chat = Chat()
    out = f"{R.SEG}/{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-frames:v", str(n), "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    count = 0
    for i, f in enumerate(frames):
        if count >= n:
            break
        t = t0 + i / FPS
        chat.draw(f, t, show=src[0] != "shapes")
        if name == "c4b":
            floating_text(f, t - t0)
        if name == "c8":
            end_overlay(f, t - t0)
            fo = clamp((t - (t1 - 0.35)) / 0.35)
            if fo > 0:
                f.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fo))))
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
    lst = f"{R.SEG}/opener_list.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{s[0]}.mp4'\n" for s in SEGMENTS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT], check=True)
    print("wrote", OUT)
