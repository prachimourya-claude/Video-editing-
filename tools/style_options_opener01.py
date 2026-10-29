"""Three looks for the can-opener reel (heart + chocolate bar ring-pull openers for long nails, PSOne Labs).
Real footage stays the hero in all three; each gets a hook still and a B2B / personalisation still.

  1  Pink Glam       - nail-girl POV: blush pink + cocoa, bold rounded text on pink pills, tiny drawn hearts and sparkles
  2  Chocolate Studio - made-in-our-studio: cream + cocoa, elegant serif and small caps, nothing else on the footage
  3  Lilac Salon     - B2B for nail techs: lilac + rose gold band with the footage in a rounded card, sticker labels,
                       drawn bow and cat icons for the "more shapes coming" teaser

usage: cd tools && python3 style_options_opener01.py <workdir> <outdir>
<workdir>/src holds O18-O22.mp4 (VID-20261029-WA0018..22) and P1.jpg P2.jpg (the two photos); fonts/ as before.
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import render_diwali01 as R
from render_diwali01 import W, H, paste_center, text_mask

BASE, OUTDIR = sys.argv[1], sys.argv[2]
F = BASE + "/fonts/"
font = lambda name, s: ImageFont.truetype(F + name, s)

BLUSH = (255, 214, 226)
PINK = (240, 120, 160)
COCOA = (78, 44, 36)
CREAM = (255, 246, 232)
LILAC = (206, 182, 236)
LILAC_D = (120, 86, 170)
ROSEGOLD = (222, 160, 140)


def still(name, t):
    path = f"{BASE}/still_{name}_{t}.png"
    if not os.path.exists(path):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", f"{BASE}/src/{name}.mp4", "-vf",
                        f"scale={W}:{H}:flags=lanczos,eq=contrast=1.04:saturation=1.08,unsharp=5:5:0.5", "-frames:v", "1", path],
                       check=True)
    return Image.open(path).convert("RGBA")


def photo_full(name, cy=0.5):
    """A 3:4 photo on a 9:16 frame: fit the width, fill the rest with a blurred copy."""
    ph = Image.open(f"{BASE}/src/{name}.jpg").convert("RGBA")
    bg = ph.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(30))
    fit = ph.resize((W, int(ph.height * W / ph.width)), Image.LANCZOS)
    bg.alpha_composite(fit, (0, int((H - fit.height) * cy)))
    return bg


def txt(t, f, fill, shadow=0):
    m = text_mask(t, f)
    im = Image.new("RGBA", m.size, fill + (0,))
    im.putalpha(m)
    return R.with_shadow(im, offset=(0, 4), blur=10, alpha=shadow, color=(20, 10, 10)) if shadow else im


def pill(t, f, bg, fg, rot=0, border=None, pad=(40, 18)):
    p = R.pill(t, f, fg=fg, bg=bg, pad=pad, alpha=245, border=border)
    return p.rotate(rot, expand=True, resample=Image.BICUBIC) if rot else p


def heart(f, x, y, r, col, alpha=255, outline=False):
    lay = Image.new("RGBA", (int(r * 4), int(r * 4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = r * 2
    pts = []
    for k in range(60):
        t = 2 * math.pi * k / 60
        hx = 16 * math.sin(t) ** 3
        hy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((c + hx * r / 17, c - hy * r / 17))
    if outline:
        d.line(pts + [pts[0]], fill=col + (alpha,), width=max(2, int(r / 6)))
    else:
        d.polygon(pts, fill=col + (alpha,))
    paste_center(f, lay, x, y)


def sparkle(f, x, y, r, col):
    d = ImageDraw.Draw(f)
    d.polygon([(x, y - r), (x + r * 0.25, y), (x, y + r), (x - r * 0.25, y)], fill=col + (255,))
    d.polygon([(x - r, y), (x, y - r * 0.25), (x + r, y), (x, y + r * 0.25)], fill=col + (255,))


def bow_icon(size, col):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    d.polygon([(c, c), (size * 0.08, size * 0.25), (size * 0.08, size * 0.75)], fill=col + (255,))
    d.polygon([(c, c), (size * 0.92, size * 0.25), (size * 0.92, size * 0.75)], fill=col + (255,))
    d.ellipse((c - size * 0.12, c - size * 0.12, c + size * 0.12, c + size * 0.12), fill=col + (255,))
    d.polygon([(c - 6, c), (c - size * 0.25, size * 0.95), (c - size * 0.08, size * 0.9)], fill=col + (255,))
    d.polygon([(c + 6, c), (c + size * 0.25, size * 0.95), (c + size * 0.08, size * 0.9)], fill=col + (255,))
    return im


def cat_icon(size, col):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((size * 0.12, size * 0.28, size * 0.88, size * 0.95), fill=col + (255,))
    d.polygon([(size * 0.16, size * 0.45), (size * 0.2, size * 0.08), (size * 0.45, size * 0.32)], fill=col + (255,))
    d.polygon([(size * 0.84, size * 0.45), (size * 0.8, size * 0.08), (size * 0.55, size * 0.32)], fill=col + (255,))
    for ex in (0.36, 0.64):
        d.ellipse((size * ex - size * 0.05, size * 0.55, size * ex + size * 0.05, size * 0.66), fill=(255, 255, 255, 255))
    return im


# ---------------------------------------------------------------- 1: Pink Glam
def g1_hook():
    f = still("O20", 15.0)
    paste_center(f, pill("POV: fresh nails", font("poppins_xb.ttf", 60), BLUSH, COCOA, rot=-3), W / 2, 250)
    paste_center(f, pill("+ a can you can't open", font("poppins_xb.ttf", 46), PINK, CREAM, rot=2), W / 2, 380)
    for x, y, r in ((150, 200, 26), (930, 330, 20), (880, 170, 14)):
        heart(f, x, y, r, PINK)
    sparkle(f, 210, 420, 22, (255, 255, 255))
    sparkle(f, 980, 470, 16, (255, 255, 255))
    return f


def g1_b2b():
    f = photo_full("P2", 0.35)
    paste_center(f, pill("Nail techs, this one's for you", font("poppins_xb.ttf", 46), BLUSH, COCOA, rot=-2), W / 2, 230)
    paste_center(f, pill("Your salon's name on every opener", font("poppins_sb.ttf", 40), PINK, CREAM, rot=1), W / 2, 340)
    d = ImageDraw.Draw(f)
    d.line([(330, 1330), (380, 1170), (440, 1010)], fill=(255, 255, 255, 255), width=6, joint="curve")
    paste_center(f, pill("your name here", font("caveat.ttf", 76), PINK, CREAM, pad=(34, 4)), 330, 1400)
    for x, y, r in ((140, 1700, 24), (940, 1650, 18)):
        heart(f, x, y, r, PINK)
    paste_center(f, pill("Bulk orders · DM us", font("poppins_xb.ttf", 44), COCOA, CREAM), W / 2, 1800)
    return f


# ---------------------------------------------------------------- 2: Chocolate Studio
def g2_hook():
    f = still("O22", 18.0)
    paste_center(f, pill("Printed in our studio", font("cormorant_i.ttf", 92), COCOA, CREAM, pad=(50, 10)), W / 2, 260)
    paste_center(f, pill("HEART & CHOCOLATE CAN OPENERS", font("montserrat_sb.ttf", 34), CREAM, COCOA), W / 2, 390)
    return f


def g2_end():
    f = photo_full("P1", 0.3)
    paste_center(f, pill("Made for long nails", font("cormorant_i.ttf", 92), COCOA, CREAM, pad=(50, 10)), W / 2, 230)
    card = Image.new("RGBA", (860, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, 859, 299), radius=40, fill=COCOA + (225,))
    d.text((430, 75), "Custom names", font=font("cormorant_b.ttf", 64), fill=CREAM, anchor="mm")
    d.text((430, 155), "For salons & nail techs · bulk orders", font=font("montserrat_sb.ttf", 32), fill=(240, 210, 190), anchor="mm")
    d.text((430, 235), "DM TO ORDER", font=font("montserrat_sb.ttf", 38), fill=CREAM, anchor="mm")
    paste_center(f, R.with_shadow(card, offset=(0, 10), blur=18, alpha=120, color=(20, 10, 10)), W / 2, 1680)
    return f


# ---------------------------------------------------------------- 3: Lilac Salon
def g3_frame(still_im, top_h=520):
    """Lilac band on top with the footage below in a rounded card."""
    g = np.linspace(0, 1, H)
    col = np.stack([np.interp(g, [0, 1], [LILAC[c], (240, 220, 245)[c]]) for c in range(3)], 1)
    f = Image.fromarray(np.broadcast_to(col[:, None, :], (H, W, 3)).astype(np.uint8)).convert("RGBA")
    w, h = 980, H - top_h - 60
    sc = max(w / still_im.width, h / still_im.height)
    im = still_im.resize((int(still_im.width * sc), int(still_im.height * sc)), Image.LANCZOS)
    im = im.crop(((im.width - w) // 2, (im.height - h) // 2, (im.width - w) // 2 + w, (im.height - h) // 2 + h))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=48, fill=255)
    im.putalpha(m)
    card = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, w + 15, h + 15), radius=56, fill=ROSEGOLD + (255,))
    card.alpha_composite(im, (8, 8))
    paste_center(f, R.with_shadow(card, offset=(0, 12), blur=22, alpha=90, color=(80, 50, 110)), W / 2, top_h + h / 2 + 20)
    return f


def g3_hook():
    f = g3_frame(still("O18", 9.0))
    paste_center(f, txt("Long nails?", font("poppins_xb.ttf", 110), LILAC_D), W / 2, 200)
    paste_center(f, pill("No more broken nails on cans", font("poppins_sb.ttf", 42), (255, 255, 255), LILAC_D), W / 2, 340)
    for x, y in ((120, 120), (960, 420)):
        sparkle(f, x, y, 26, (255, 255, 255))
    heart(f, 960, 130, 26, ROSEGOLD)
    return f


def g3_more():
    f = g3_frame(photo_full("P2", 0.45))
    paste_center(f, txt("Custom for your salon", font("poppins_xb.ttf", 72), LILAC_D), W / 2, 170)
    paste_center(f, txt("More shapes coming soon", font("caveat.ttf", 86), (150, 100, 170)), W / 2, 300)
    for k, (fn, x) in enumerate(((bow_icon, W / 2 - 170), (cat_icon, W / 2), (None, W / 2 + 170))):
        if fn:
            paste_center(f, fn(110, LILAC_D), x, 430)
        else:
            heart(f, x, 430, 50, LILAC_D)
    paste_center(f, pill("Bulk & custom names · DM us", font("poppins_xb.ttf", 42), LILAC_D, (255, 255, 255)), W / 2, 1810)
    return f


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    opts = [("1_pink_glam", g1_hook, g1_b2b), ("2_chocolate_studio", g2_hook, g2_end), ("3_lilac_salon", g3_hook, g3_more)]
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
