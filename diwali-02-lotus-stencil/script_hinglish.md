# Diwali 02 — Lotus Rangoli Stencil (PSOne Labs)

Vertical 9:16, ~26s, for Instagram Reels (also YouTube Shorts / Facebook Reels). Posted 25 Oct 2026, the day after the Kalash reel,
so it opens with "New day, new product!". Same night style as the Kalash reel and teaser (night-blue sky to purple/pink,
gold Mughal arches, sky lanterns, kandils, diyas). The product sold is the plain white stencil: white footage everywhere,
the coloured rangoli only in the "rang bharo / ready" steps.
The creator records the voiceover; the reel goes out voice-only and music is added in the Instagram app.

## Voiceover script

| # | Time | Voiceover (Hinglish) | On-screen text |
|---|---|---|---|
| 1 | 0.0–2.6 | New day, new product! | "NEW DAY," / "new product!" / chip "Lotus Rangoli Stencil" |
| 2 | 2.6–6.4 | Is Diwali, aapke aangan mein khilega kamal. | "Is Diwali, aangan mein" / "khilega kamal" + gold lotus icon |
| 3 | 6.4–11.4 | Pesh hai hamara Lotus Rangoli Stencil, khud design kiya aur 3D print kiya. | "Pesh hai hamara" / "Lotus Stencil" / chip "Designed & 3D printed by us" |
| 4 | 11.4–15.4 | Ekdum unique kamal design, Diwali ke liye perfect. | "Unique kamal design" / chip "Diwali special" |
| 5 | 15.4–21.4 | Bas stencil rakho, rang bharo, aur sundar kamal rangoli ready! | "Bas 3 steps!" / chips 1-2-3 / "Perfect rangoli!" |
| 6 | 21.4–26.0 | Diwali se pehle apna order karo, abhi DM karo! | "Diwali se pehle" / "order karo!" / "DM to order", then end card |

Devanagari for recording: `voiceover_devanagari.txt`.

## Storyboard

1. **Hook (0–2.6s)**: white lotus stencil held up inside the gold arch (WA0004 ~12s), sky lanterns rising.
   "NEW DAY," fades up, "new product!" glows in, the "Lotus Rangoli Stencil" chip pops below. Soft dip into the next scene.
2. **Kamal (2.6–6.4s)**: three printed lotuses on the printer bed (WA0003 0–3s) in the arch, slow push-in. "Is Diwali, aangan mein"
   writes on, "khilega kamal" glows, a small gold lotus opens beside it. Kandils sway at the sides.
3. **Introducing (6.4–11.4s)**: printer bed with lotuses (WA0004 0–6s) in the arch. "Pesh hai hamara / Lotus Stencil";
   badge "Designed & 3D printed by us".
4. **Product (11.4–15.4s)**: hand-held white lotus in slow motion (WA0004 8–14s), whole stencil fitted in a tall arch.
   "Unique kamal design", chip "Diwali special", soft gold line fireworks.
5. **Steps (15.4–21.4s)**: "1 Stencil rakho" on the white stencil (WA0003 5–8s, hand-held); "2 Rang bharo" on the real filling shot
   (WA0005 0–4s); "3 Rangoli ready!" on the finished lotus rangoli (WA0005 6–9s) with "Perfect rangoli!" and line fireworks.
   This ~4s is the only coloured footage.
6. **CTA + end card (21.4–26s)**: white lotus (WA0004) with "Diwali se pehle order karo!" and a pulsing "DM to order"; then the dusk
   end card: gold lotus, "Order now!", LOTUS RANGOLI STENCIL, DM to order, three diyas, शुभ दीपावली, fade out.
   No logo block: the client posts on their own page, so the reel ends on the call to action.

Brand (from the client's own posts, `style_frames/reference_psone_labs_brand.jpg`): written **PSOne Labs**,
terracotta + olive on warm beige, rounded type (Quicksand). Option A borrows this palette.

Style frames: `style_frames/` (hook, printer, steps, end card). Regenerate with
`cd tools && python3 style_frames_lotus01.py <workdir> <outdir>`.

## Footage map

| Clip | File | Use |
|---|---|---|
| L3 | VID-20261025-WA0003.mp4 (8.0s) | Lotuses on the printer bed 0–4s; hand-held close-up 5–8s |
| L4 | VID-20261025-WA0004.mp4 (14.5s) | Bed with three lotuses 0–7s; hand-held white lotus 8–14s (hero, 12.5s) |
| L5 | VID-20261025-WA0005.mp4 (12.1s) | Hand filling rangoli 0–5s; finished pink/green lotus 6–12s |

## Caption

> New day, new product! 🪷✨
> Is Diwali, aapke aangan mein khilega kamal 🌸
> Introducing our **Lotus Rangoli Stencil**, designed & 3D printed by us 💛
>
> ✅ Stencil rakho
> ✅ Rang bharo
> ✅ Sundar kamal rangoli ready!
>
> 📩 DM "LOTUS" to order, Diwali se pehle!
> Kalash ya Kamal, aapka favourite kaunsa? Comment karo 👇
>
> #Diwali2026 #Dhanteras #RangoliStencil #LotusRangoli #KamalRangoli #EasyRangoli #DiwaliDecor #RangoliDesign
> #DiwaliVibes #3DPrinting #MadeInIndia #SmallBusinessIndia #NewLaunch #ReelsIndia

## Style options (client asked for something other than the night-blue arch look)

`style_options/` holds a hook and an end card for each; regenerate with `cd tools && python3 style_options_lotus01.py <workdir> <outdir>`.

| Option | Look |
|---|---|
| A — Brand Beige | PSOne Labs' own palette: warm beige, terracotta + olive, botanical line art, rounded photo card with a white border |
| B — Rose & Gold | Blush to deep rose, gold mandala corners, pink bokeh and floating petals; footage in a gold ring framed by lotus petals; glowing diyas |
| C — Mint Pop | Mint background with peach/pink blobs and a faint lotus pattern; footage as a tilted polaroid with washi tape, "NEW!" starburst, sticker-style pills, handwritten notes |

All end cards close on "Order now!" + "DM to order" (no logo block).
