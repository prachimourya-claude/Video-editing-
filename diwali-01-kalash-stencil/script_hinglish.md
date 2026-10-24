# Diwali 01 — Kalash Rangoli Stencil (PS1)

Vertical 9:16, ~30s, one edit for Instagram Reels, YouTube Shorts and Facebook Reels. Hinglish voiceover, original clip audio muted (only room noise).

Product: 3D-printed Kalash + lotus rangoli stencil, designed in-house for Dhanteras and Diwali, reusable on any day.

## Voiceover script

| Time | Footage | On-screen text | Voiceover |
|---|---|---|---|
| 0–3s | **Hook.** Clip B 0:00–0:03, stencil held up, fast push-in | "Is Diwali, kuch unique? 🪔" | Is Diwali, aapki rangoli ho kuch unique! |
| 3–8s | Clip C 0:00–0:05, printer head over finished stencil on the bed | "Market ke stencils = same old designs" | Market mein stencils toh bahut hain… par sab ek jaise. |
| 8–14s | Clip C 0:05–0:11 → match cut to Clip B 0:09–0:12 (lotus pieces printing) | "Designed & 3D printed by Psone Labs" | Isliye humne khud design kiya — special Dhanteras aur Diwali ke liye. |
| 14–20s | Clip B 0:00–0:04 slow-mo, labels pop on the kalash and the lotus | "Upar: shubh kalash" · "Neeche: kamal" | Ye hai hamara Kalash stencil. Upar shubh kalash, aur neeche kamal. |
| 20–25s | Animated colour fill on a still of the stencil (Clip A 0:03), labelled "Design preview" | "1 Rakho · 2 Rang bharo · 3 Rangoli ready" | Bas stencil rakho, rang bharo… aur perfect rangoli ready! |
| 25–30s | Clip A 0:04–0:07, stencil in front of the curtain, warm glow + diya sparkles | "Order now · DM / link in bio" | Dhanteras se pehle apna order karo — abhi DM karo! |

Voiceover in Devanagari (for TTS / your own voice): `voiceover_devanagari.txt`.

## Storyboard

1. **Hook (0–3s)**: start mid-motion, punch from 100% → 115% on the stencil, golden light leak and hand-drawn diya doodles in the corners. Big text over the top third: "Is Diwali, kuch unique? 🪔".
2. **Problem (3–8s)**: printer shot, a bit desaturated. Strike-through animation on the text "same old designs".
3. **Reveal (8–14s)**: colour comes back with a soft flash at the voice line "khud design kiya". Bambu printer move → match cut on the lotus shapes being printed. Small badge: "Made in-house · 3D printed".
4. **Product hero (14–20s)**: 0.6× slow-mo on the hand-held turn. Thin gold arrows draw onto the kalash ("Upar: shubh kalash") and the lotus ("Neeche: kamal"). A gentle glow on the stencil edges.
5. **How to use (20–25s)**: no real fill footage, so this is animated. A clean still of the stencil from Clip A is cut out onto a floor-tile background, then each section fills with rangoli colour in turn (kalash in marigold and maroon, lotus in pink and green, gold dots on the rim), with a powder-grain texture. Number chips 1·2·3 pop in turn. A small "Design preview" tag stays in the corner so it isn't mistaken for a real rangoli photo. Hold the finished colour version for 1.5s.
6. **CTA (25–30s)**: curtain shot, warm grade, sparkles falling, brand handle + "DM to order" pill. End card holds 1s so the loop back to the hook feels clean.

Visual style: festive warm grade (marigold, maroon, gold), cream paper captions to match the existing reels, Devanagari accents only for "शुभ दीपावली".
Music: light festive instrumental (shehnai/sitar + soft percussion), ducked under the voice. Royalty-free; credit goes in the caption.

## Footage map

| Clip | File | Use |
|---|---|---|
| A | VID-20261024-WA0009.mp4 (6.8s) | Stencil held in front of the wall/curtain → CTA |
| B | VID-20261024-WA0010.mp4 (12.0s) | Hand-held turn in front of the printer (0–4s hero), back side 0:05, lotus pieces printing 0:09–0:12 |
| C | VID-20261024-WA0011.mp4 (15.3s) | Finished stencil on the Bambu Lab bed, printer head moving |

## Captions

**Instagram / Facebook**
> Is Diwali, rangoli ho kuch unique ✨🪔
> Hamara in-house designed Kalash + Kamal stencil, special for Dhanteras & Diwali. Rakho, rang bharo, rangoli ready!
> Reusable, so you can use it on any festival or any day.
> 📦 DM to order / link in bio. Order before Dhanteras!
>
> #Diwali2026 #Dhanteras #RangoliStencil #RangoliDesign #KalashRangoli #DiwaliDecor #EasyRangoli #3DPrinting #HandmadeInIndia #FestiveDecor #SmallBusinessIndia

**YouTube Shorts**
- Title: `A Unique Diwali Rangoli: Kalash Stencil 🪔 #shorts`
- Description: the caption above, plus the music credit.

## Draft v1 (motion-graphics cut)

`diwali01_draft_v1_music_only.mp4`: 30s, 1080x1920, music only, waiting for the voiceover.
Render: `python3 tools/render_diwali01.py <workdir> <workdir>/diwali01_video_only.mp4`, then `tools/mix_diwali01.sh <workdir>`.

| Time | Scene | Voiceover line |
|---|---|---|
| 0.0–3.2 | Night sky, fireworks, marigold toran drops in, 5 diyas light up. "Diwali aa rahi hai!" / "Is baar rangoli ho kuch UNIQUE" | 1 |
| 3.2–7.2 | 3x3 grid of identical grey market stencils, "sab ek jaise!"; centre tile flips to our coloured kalash and zooms in | 2 |
| 7.2–13.2 | Printer clip + lotus pieces printing. "Humne khud design kiya!", "Designed & 3D printed by Psone Labs", "Special: Dhanteras & Diwali" | 3 |
| 13.2–19.2 | Hand-held stencil, slow-mo. "Kalash Rangoli Stencil", pointers "Upar: Shubh Kalash" and "Neeche: Kamal" | 4 |
| 19.2–25.2 | Stencil drops on a red-oxide floor, fills with rangoli colours zone by zone, diyas + fireworks. Steps 1-2-3, "Perfect rangoli!", "Design preview" tag | 5 |
| 25.2–30.0 | Stencil clip, "Dhanteras se pehle order karo!", "DM to order", then end card: Psone Labs, शुभ दीपावली | 6 |

The marigold toran, floating sparkles and a warm flash on each cut run across the whole reel.

Music: "Vadodora" by Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0. Put this in the caption / description:
`Music: "Vadodora" Kevin MacLeod (incompetech.com) — Licensed under Creative Commons: By Attribution 4.0 — http://creativecommons.org/licenses/by/4.0/`
