"""'More shapes' glimpse for the can-opener reel: tight product crops of reference designs (client checks licences;
shown as made-to-order references, watermarked/overlaid photos left out), tagged "reference designs · made to order".

usage: cd tools && python3 more_shapes_opener.py <workdir> <out.png>   (<workdir>/refs/crop_*.jpg)
"""
import sys
from PIL import Image, ImageDraw, ImageFont
import render_diwali01 as R
from render_diwali01 import W, H, paste_center

B, OUT = sys.argv[1], sys.argv[2]
F = B + "/fonts/"
NAMES = ["ghost", "lemon", "polish", "daisy", "bow", "butterfly", "mermaid", "bow_can", "flowers"]


def tile(n, tw=310, th=390):
    im = Image.open(f"{B}/refs/crop_{n}.jpg").convert("RGBA")
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    im = im.crop(((im.width - tw) // 2, (im.height - th) // 2, (im.width - tw) // 2 + tw, (im.height - th) // 2 + th))
    m = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, tw - 1, th - 1), radius=34, fill=255)
    im.putalpha(m)
    card = Image.new("RGBA", (tw + 16, th + 16), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, tw + 15, th + 15), radius=42, fill=(255, 255, 255, 255))
    card.alpha_composite(im, (8, 8))
    return R.with_shadow(card, offset=(0, 8), blur=14, alpha=60, color=(160, 80, 120))


def grid():
    f = Image.new("RGBA", (W, H), (255, 240, 246, 255))
    d = ImageDraw.Draw(f)
    d.text((W / 2, 170), "More shapes", font=ImageFont.truetype(F + "poppins_xb.ttf", 100), fill=(60, 40, 50), anchor="mm")
    d.text((W / 2, 270), "any colour · your name on it", font=ImageFont.truetype(F + "inter_m.ttf", 42), fill=(150, 90, 120), anchor="mm")
    for k, n in enumerate(NAMES):
        r, c = divmod(k, 3)
        paste_center(f, tile(n), W / 2 + (c - 1) * 340, 590 + r * 430)
    tag = R.pill("reference designs · made to order", ImageFont.truetype(F + "inter_m.ttf", 34), fg=(255, 255, 255),
                 bg=(60, 40, 50), pad=(30, 14))
    paste_center(f, tag, W / 2, 1840)
    return f


if __name__ == "__main__":
    grid().convert("RGB").save(OUT)
    print("wrote", OUT)
