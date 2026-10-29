"""'Pick your shape' grid for the can-opener reel: original flat illustrations (drawn here, not copied from photos)
of made-to-order shapes, with colour swatches and a custom-name note.

usage: cd tools && python3 shape_grid_opener.py <workdir> <out.png>
"""
import math, sys
from PIL import Image, ImageDraw, ImageFont

import render_diwali01 as R
from render_diwali01 import W, H, paste_center

BASE, OUT = sys.argv[1], sys.argv[2]
F = BASE + "/fonts/"
font = lambda name, s: ImageFont.truetype(F + name, s)
S = 280  # tile size
OUTLINE = (60, 40, 50, 255)


def canvas():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def heart_pts(cx, cy, r):
    pts = []
    for k in range(80):
        t = 2 * math.pi * k / 80
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * r / 17, cy - y * r / 17))
    return pts


def face(d, cx, cy, s=1.0):
    for ex in (-1, 1):
        d.ellipse((cx + ex * 26 * s - 7 * s, cy - 8 * s, cx + ex * 26 * s + 7 * s, cy + 6 * s), fill=OUTLINE)
        d.ellipse((cx + ex * 42 * s - 9 * s, cy + 10 * s, cx + ex * 42 * s + 9 * s, cy + 20 * s), fill=(240, 140, 150, 255))
    d.arc((cx - 10 * s, cy, cx + 10 * s, cy + 16 * s), 20, 160, fill=OUTLINE, width=max(2, int(4 * s)))


def lemon():
    im, d = canvas()
    c = S / 2
    d.ellipse((40, 40, 240, 240), fill=(255, 214, 40, 255), outline=OUTLINE, width=5)
    d.ellipse((58, 58, 222, 222), fill=(255, 246, 200, 255))
    d.ellipse((68, 68, 212, 212), fill=(255, 220, 60, 255))
    for k in range(8):
        a = math.pi * k / 4
        d.line((c, c, c + 72 * math.cos(a), c + 72 * math.sin(a)), fill=(255, 246, 200, 255), width=6)
    face(d, c, c + 10, 0.9)
    return im


def ghost():
    im, d = canvas()
    pts = [(70, 140)]
    for k in range(31):
        a = math.pi + math.pi * k / 30
        pts.append((140 + 70 * math.cos(a), 140 + 80 * math.sin(a)))
    pts += [(210, 140), (210, 230), (188, 214), (164, 236), (140, 214), (116, 236), (92, 214), (70, 230)]
    d.polygon(pts, fill=(255, 255, 255, 255), outline=OUTLINE, width=5)
    face(d, 140, 140)
    d.polygon([(150, 60), (190, 40), (190, 80)], fill=(245, 110, 160, 255), outline=OUTLINE, width=3)
    d.polygon([(150, 60), (115, 40), (115, 80)], fill=(245, 110, 160, 255), outline=OUTLINE, width=3)
    d.ellipse((140, 50, 160, 70), fill=(245, 110, 160, 255), outline=OUTLINE, width=3)
    return im


def daisy():
    im, d = canvas()
    c = S / 2
    for k in range(6):
        a = 2 * math.pi * k / 6
        x, y = c + 62 * math.cos(a), c + 62 * math.sin(a)
        d.ellipse((x - 50, y - 50, x + 50, y + 50), fill=(255, 252, 240, 255), outline=OUTLINE, width=4)
    d.ellipse((c - 44, c - 44, c + 44, c + 44), fill=(245, 170, 190, 255), outline=OUTLINE, width=4)
    return im


def butterfly():
    im, d = canvas()
    c = S / 2
    col = (205, 185, 240, 255)
    for sx in (-1, 1):
        d.ellipse((c + sx * 20 - (100 if sx < 0 else 0), 50, c + sx * 20 + (0 if sx < 0 else 100), 150), fill=col, outline=OUTLINE, width=4)
        d.ellipse((c + sx * 20 - (80 if sx < 0 else 0), 135, c + sx * 20 + (0 if sx < 0 else 80), 225), fill=col, outline=OUTLINE, width=4)
    d.rounded_rectangle((c - 12, 60, c + 12, 220), radius=12, fill=(150, 120, 200, 255), outline=OUTLINE, width=4)
    d.line((c - 4, 64, c - 30, 30), fill=OUTLINE, width=4)
    d.line((c + 4, 64, c + 30, 30), fill=OUTLINE, width=4)
    return im


def paw():
    im, d = canvas()
    d.rounded_rectangle((70, 120, 210, 250), radius=40, fill=(120, 200, 240, 255), outline=OUTLINE, width=5)
    d.polygon(heart_pts(140, 172, 46), fill=(250, 170, 190, 255))
    for x, y in ((82, 100), (118, 72), (162, 72), (198, 100)):
        d.ellipse((x - 26, y - 28, x + 26, y + 28), fill=(120, 200, 240, 255), outline=OUTLINE, width=5)
        d.ellipse((x - 15, y - 16, x + 15, y + 16), fill=(250, 170, 190, 255))
    return im


def polish():
    im, d = canvas()
    d.rounded_rectangle((112, 30, 168, 130), radius=12, fill=(220, 40, 170, 255), outline=OUTLINE, width=5)
    d.rounded_rectangle((70, 120, 210, 250), radius=26, fill=(230, 60, 180, 255), outline=OUTLINE, width=5)
    d.polygon(heart_pts(140, 186, 40), fill=(255, 255, 255, 255))
    return im


def popsicle():
    im, d = canvas()
    d.rounded_rectangle((122, 180, 158, 260), radius=14, fill=(235, 200, 130, 255), outline=OUTLINE, width=4)
    d.rounded_rectangle((80, 40, 200, 200), radius=50, fill=(240, 130, 90, 255), outline=OUTLINE, width=5)
    d.ellipse((168, 36, 216, 84), fill=(0, 0, 0, 0))
    d.pieslice((168, 36, 216, 84), 90, 270, fill=(255, 255, 255, 255))
    d.rounded_rectangle((92, 52, 188, 80), radius=14, fill=(255, 245, 235, 255))
    return im


def bow():
    im, d = canvas()
    c = S / 2
    col, dark = (250, 170, 200, 255), (235, 70, 150, 255)
    d.polygon([(c, c - 10), (40, 60), (30, 170)], fill=col, outline=dark, width=6)
    d.polygon([(c, c - 10), (240, 60), (250, 170)], fill=col, outline=dark, width=6)
    d.polygon([(c - 10, c), (90, 250), (125, 230)], fill=col, outline=dark, width=6)
    d.polygon([(c + 10, c), (190, 250), (155, 230)], fill=col, outline=dark, width=6)
    d.ellipse((c - 28, c - 38, c + 28, c + 18), fill=dark)
    d.polygon(heart_pts(c, c - 12, 14), fill=(255, 255, 255, 255))
    return im


SHAPES = [("Lemon", lemon), ("Ghost", ghost), ("Daisy", daisy), ("Butterfly", butterfly),
          ("Paw", paw), ("Nail polish", polish), ("Popsicle", popsicle), ("Bow", bow)]


def grid():
    f = Image.new("RGBA", (W, H), (255, 240, 246, 255))
    d = ImageDraw.Draw(f)
    d.text((W / 2, 170), "Pick your shape", font=font("poppins_xb.ttf", 92), fill=(60, 40, 50), anchor="mm")
    d.text((W / 2, 270), "made to order · any colour · your name on it", font=font("inter_m.ttf", 40), fill=(150, 90, 120), anchor="mm")
    for k, (name, fn) in enumerate(SHAPES):
        r, c = divmod(k, 2)
        x, y = W / 2 + (c - 0.5) * 460, 520 + r * 330
        card = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle((0, 0, 399, 299), radius=40, fill=(255, 255, 255, 255))
        paste_center(card, fn().resize((210, 210), Image.LANCZOS), 200, 125)
        ImageDraw.Draw(card).text((200, 262), name, font=font("inter_b.ttf", 36), fill=(60, 40, 50), anchor="mm")
        paste_center(f, R.with_shadow(card, offset=(0, 8), blur=14, alpha=60, color=(160, 80, 120)), x, y)
    sw = [(245, 110, 160), (255, 214, 40), (120, 200, 240), (205, 185, 240), (90, 60, 50), (255, 255, 255), (120, 200, 140)]
    for k, col in enumerate(sw):
        x = W / 2 + (k - 3) * 96
        d.ellipse((x - 34, 1840 - 34, x + 34, 1840 + 34), fill=col + (255,), outline=(60, 40, 50, 255), width=3)
    return f


if __name__ == "__main__":
    grid().convert("RGB").save(OUT)
    print("wrote", OUT)
