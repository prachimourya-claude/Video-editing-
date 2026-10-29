"""Three new looks for the can-opener reel (round 2: nothing like the earlier arches/pills/frames).

  1  Group Chat    - the story told as phone chat bubbles over the real footage (friends, then a salon owner)
  2  Salon Receipt - a torn paper receipt in mono type slides up over the footage, with a red rubber stamp
  3  Magazine      - fashion-editorial cover: huge condensed type in black blocks, film grain, red marker scribbles

usage: cd tools && python3 style_options_opener02.py <workdir> <outdir>   (same <workdir> as style_options_opener01.py)
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import render_diwali01 as R
import style_options_opener01 as O
from render_diwali01 import W, H, paste_center

BASE, OUTDIR = sys.argv[1], sys.argv[2]
F = BASE + "/fonts/"
font = lambda name, s: ImageFont.truetype(F + name, s)
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
RED = (226, 32, 52)
INK = (20, 20, 22)


def emoji(ch, size):
    """Colour emoji (Noto only renders at 109px; scale it)."""
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    return im.resize((int(im.width * size / 109), int(im.height * size / 109)), Image.LANCZOS)


# ---------------------------------------------------------------- 1: Group Chat
def bubble(text, right=False, emo=None, name=None, maxw=760):
    f = font("inter_m.ttf", 44)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = d.textlength(text, font=f)
    ew = 56 if emo else 0
    w, h = int(min(maxw, tw + ew + 64)), 104 + (40 if name else 0)
    im = Image.new("RGBA", (w + 20, h + 10), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    bg = (10, 132, 255) if right else (236, 236, 240)
    fg = (255, 255, 255) if right else INK
    dd.rounded_rectangle((0, 0, w, h), radius=46, fill=bg + (255,))
    # tail
    tx = w - 18 if right else 18
    dd.polygon([(tx - 14, h - 30), (tx + (22 if right else -22), h + 6), (tx + 14, h - 12)], fill=bg + (255,))
    y = h - 52
    if name:
        dd.text((32, 34), name, font=font("inter_b.ttf", 30), fill=(200, 80, 140))
    dd.text((32, y), text, font=f, fill=fg, anchor="lm")
    if emo:
        e = emoji(emo, 46)
        im.alpha_composite(e, (int(32 + tw + 10), int(y - e.height / 2)))
    return R.with_shadow(im, offset=(0, 6), blur=12, alpha=70, color=(0, 0, 0))


def chat_header(title, sub):
    im = Image.new("RGBA", (W, 150), (248, 248, 250, 240))
    d = ImageDraw.Draw(im)
    d.ellipse((40, 30, 130, 120), fill=(255, 190, 215, 255))
    paste_center(im, emoji("💅", 52), 85, 75)
    d.text((160, 52), title, font=font("inter_b.ttf", 42), fill=INK, anchor="lm")
    d.text((160, 102), sub, font=font("inter_m.ttf", 30), fill=(140, 140, 150), anchor="lm")
    d.line((0, 149, W, 149), fill=(210, 210, 216, 255), width=2)
    return im


def c1_hook():
    f = O.still("O20", 15.0)
    f.alpha_composite(chat_header("nail gang", "Riya, Sana, you"), (0, 0))
    y = 210
    for text, right, emo in (("just got my nails done", False, "💅"), ("but can't open my can", False, "😭"),
                             ("bro use this", True, "👇")):
        b = bubble(text, right, emo)
        x = W - b.width - 30 if right else 30
        f.alpha_composite(b, (x, y))
        y += b.height + 14
    return f


def c1_b2b():
    f = O.photo_full("P2", 0.42)
    f.alpha_composite(chat_header("Your Nail Studio", "business account"), (0, 0))
    y = 200
    for text, right, emo, name in (("can you put my salon name on it?", False, None, "Your Nail Studio"),
                                   ("yes, any name", True, "✨", None), ("bulk for salons too", True, "🎀", None)):
        b = bubble(text, right, emo, name)
        x = W - b.width - 30 if right else 30
        f.alpha_composite(b, (x, y))
        y += b.height + 14
    b = bubble("DM to order", True, "📩")
    f.alpha_composite(b, (W - b.width - 30, H - b.height - 90))
    return f


# ---------------------------------------------------------------- 2: Salon Receipt
def receipt(lines, w=820, stamp=None):
    f1, fb = font("spacemono.ttf", 34), font("spacemono_b.ttf", 38)
    lh = 52
    h = 70 + lh * len(lines) + (170 if stamp else 60)
    im = Image.new("RGBA", (w, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    teeth = [(x, 20 + (12 if (x // 24) % 2 else 0)) for x in range(0, w + 24, 24)]
    poly = [(0, 20)] + teeth + [(w, h + 20)] + [(x, h + 20 - (12 if (x // 24) % 2 else 0)) for x in range(w, -24, -24)]
    d.polygon(poly, fill=(252, 250, 244, 255))
    y = 70
    for kind, a, b in lines:
        if kind == "title":
            d.text((w / 2, y), a, font=fb, fill=INK, anchor="mm")
        elif kind == "rule":
            d.text((w / 2, y), "-" * 38, font=f1, fill=(120, 120, 120), anchor="mm")
        else:
            dots = "." * max(2, 30 - len(a) - len(b))
            d.text((50, y), f"{a} {dots} {b}", font=f1, fill=INK, anchor="lm")
        y += lh
    im = R.with_shadow(im, offset=(0, 14), blur=20, alpha=120, color=(0, 0, 0))
    if stamp:
        s = Image.new("RGBA", (420, 150), (0, 0, 0, 0))
        sd = ImageDraw.Draw(s)
        sd.rounded_rectangle((6, 6, 414, 144), radius=18, outline=RED + (230,), width=8)
        sd.text((210, 75), stamp, font=font("marker.ttf", 58), fill=RED + (235,), anchor="mm")
        s = s.rotate(-12, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(s, (im.width - s.width - 40, im.height - s.height - 20))
    return im


def c2_hook():
    f = O.still("O18", 9.0)
    r = receipt([("title", "NAIL DAY  #2026", ""), ("rule", "", ""), ("item", "1x fresh gel set", "OK"),
                 ("item", "1x cold drink", "OK"), ("item", "0x broken nails", "OK"), ("rule", "", ""),
                 ("item", "opener", "heart+choco")], stamp="NAIL SAFE")
    paste_center(f, r.rotate(2, expand=True, resample=Image.BICUBIC), W / 2, 330 + r.height / 2 - 60)
    return f


def c2_b2b():
    f = O.photo_full("P2", 0.55)
    r = receipt([("title", "SALON ORDER", ""), ("rule", "", ""), ("item", "name", "YOUR SALON"),
                 ("item", "shapes", "heart, choco"), ("item", "next", "bow, cat"), ("item", "qty", "bulk"),
                 ("rule", "", ""), ("title", "DM TO ORDER", "")], stamp="CUSTOM")
    paste_center(f, r.rotate(-2, expand=True, resample=Image.BICUBIC), W / 2, 60 + r.height / 2)
    return f


# ---------------------------------------------------------------- 3: Magazine
def grain(im, amt=10, seed=1):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    a = (a - 128) * 1.08 + 128 + np.random.default_rng(seed).normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")


def block(text, f, fg=(255, 255, 255), bg=INK, pad=(24, 6)):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.textbbox((0, 0), text, font=f)
    w, h = bb[2] - bb[0] + 2 * pad[0], bb[3] - bb[1] + 2 * pad[1]
    im = Image.new("RGBA", (w, h), bg + (255,))
    ImageDraw.Draw(im).text((pad[0] - bb[0], pad[1] - bb[1]), text, font=f, fill=fg)
    return im


def scribble_circle(f, cx, cy, rx, ry, col=RED, width=8, seed=2):
    rng = np.random.default_rng(seed)
    pts = []
    for k in range(80):
        t = 2 * math.pi * k / 72 - 0.4
        j = 1 + rng.uniform(-0.04, 0.04)
        pts.append((cx + rx * j * math.cos(t), cy + ry * j * math.sin(t)))
    ImageDraw.Draw(f).line(pts, fill=col + (255,), width=width, joint="curve")


def note(f, text, x, y, rot=0, size=64):
    from render_diwali01 import text_mask
    m = text_mask(text, font("marker.ttf", size))
    im = Image.new("RGBA", m.size, RED + (0,))
    im.putalpha(m)
    paste_center(f, im.rotate(rot, expand=True, resample=Image.BICUBIC), x, y)


def c3_hook():
    f = grain(O.still("O20", 15.0))
    f.alpha_composite(block("ISSUE 04  ·  THE NAIL DROP", font("spacemono_b.ttf", 30), pad=(18, 8)), (40, 60))
    big = font("anton.ttf", 210)
    f.alpha_composite(block("FRESH", big, pad=(22, 0)), (40, 140))
    f.alpha_composite(block("NAILS.", big, fg=INK, bg=(255, 255, 255), pad=(22, 0)), (40, 400))
    f.alpha_composite(block("Zero broken ones.", font("playfair_bi.ttf", 58), fg=(255, 255, 255), bg=RED, pad=(20, 10)), (40, 670))
    scribble_circle(f, 470, 1030, 190, 150)
    note(f, "the heart one!", 820, 860, -8)
    return f


def c3_b2b():
    f = grain(O.photo_full("P2", 0.5))
    f.alpha_composite(block("FOR NAIL TECHS", font("anton.ttf", 150), pad=(22, 0)), (40, 120))
    f.alpha_composite(block("Your salon's name. On every one.", font("playfair_bi.ttf", 50), fg=INK, bg=(255, 255, 255), pad=(20, 10)), (40, 330))
    scribble_circle(f, 375, 960, 150, 125, seed=5)
    note(f, "your name here", 330, 1180, 6)
    note(f, "bows + cats next", 760, 1500, -6, 58)
    f.alpha_composite(block("DM TO ORDER  ·  BULK OK", font("anton.ttf", 84), fg=(255, 255, 255), bg=RED, pad=(26, 4)),
                      (W // 2 - 330, H - 200))
    return f


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    opts = [("1_group_chat", c1_hook, c1_b2b), ("2_salon_receipt", c2_hook, c2_b2b), ("3_magazine", c3_hook, c3_b2b)]
    thumbs = []
    for name, a, b in opts:
        for part, fn in (("hook", a), ("b2b", b)):
            im = fn().convert("RGB")
            im.save(f"{OUTDIR}/option_{name}_{part}.png")
            thumbs.append(im.resize((W // 3, H // 3), Image.LANCZOS))
    sheet = Image.new("RGB", (W // 3 * 6 + 70, H // 3 + 20), (255, 255, 255))
    for k, t in enumerate(thumbs):
        sheet.paste(t, (10 + k * (W // 3 + 10), 10))
    sheet.save(f"{OUTDIR}/options_sheet.png")
    print("wrote", OUTDIR)
