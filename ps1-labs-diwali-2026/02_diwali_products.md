# 02 — The Diwali Collection: "Roshni by PS1 Labs"

With 15 days left, sell **few products, done well**. Pick 4–5 from the list below: one hero, two fast sellers, one personalised item and one bulk item. Hampers raise your average order value without new designs.

> ⚠️ **Safety rule for every lighting product: LED tealights only, never a real flame.** PLA softens at about 55–60 °C, so a burning candle will warp or melt it and can catch fire. Put "Use with the included LED tealight only" on the product card and the box. Buy warm-flicker LED tealights in bulk (roughly ₹8–15 each wholesale) and include them, so the product works out of the box.

## The products

Print times are rough figures for a 0.4 mm nozzle at 0.2 mm layers on a modern printer. **Time your own sample and replace them.**

| # | Product | What it is | Print time / pc | Role | Suggested price |
|---|---|---|---|---|---|
| 1 | **Jaali Lantern (Kandil)** | Lattice/voronoi lantern, ~15 cm, LED inside, throws patterns on the wall | 5–8 h | **Hero**: the reel star and premium buy | ₹899–1,299 |
| 2 | **Diya Set of 4** | Geometric diya shells holding LED tealights, in marigold/ivory/silk-gold PLA | 40–60 min each | Fast seller | ₹599–699 per set |
| 3 | **Rangoli Stencil Tiles** | Reusable interlocking stencils (set of 3 sizes). Pour colour or rice through them | 30–60 min each | Fast seller, low-cost add-on | ₹299–449 per set |
| 4 | **Personalised Nameplate** | Family name + Om / Swastik / Shubh-Labh, two-colour print, wall or door | 2–3 h | Personalised, high margin | ₹799–1,499 |
| 5 | **Shubh-Labh / Toran Wall Hangings** | Pair of Shubh & Labh plaques or a modular toran strip | 1.5–2.5 h | Décor add-on | ₹449–699 per pair |
| 6 | **Logo / Name Keychains** | Two-colour keychain with a name or company logo | 15–25 min (batch 20+ per plate) | **Bulk** + Bhai Dooj | ₹99–199 retail; ₹45–90 bulk |
| 7 | **Logo Coasters / Desk Stand** | Set of 4 coasters with cork base, or a pen + phone stand with a logo | 1–2 h | **Bulk / corporate** | ₹399–699 retail; ₹180–350 bulk |

**If you have a resin printer**, add a small **minimal Ganesh-Lakshmi** idol pair (painted gold) as a premium item. On FDM, layer lines on faces look cheap, so skip idols unless your finish is excellent.

## Hampers (higher order value, no new designs)

| Hamper | Contents | Price | Pitch |
|---|---|---|---|
| **Roshni Box** | 2 diyas + 1 rangoli stencil + LED tealights | ₹699 | "The ₹700 Diwali gift that isn't sweets" |
| **Ghar Box** | Lantern + diya set of 4 + Shubh-Labh pair | ₹1,999 (worth ₹2,400) | Housewarming / family gift |
| **Bhai Dooj Box** | 2 personalised keychains + 1 diya + card | ₹449 | Pre-book from 4 Nov, deliver 9–10 Nov |

## Pricing formula (use it for every quote)

```
Material      = grams used × (₹ per kg ÷ 1000)          e.g. 120 g × ₹1.1 = ₹132
Machine time  = print hours × ₹25–40/hour                (power + wear + printer payback)
Add-ons       = LED tealight + magnet/keyring/cork + box + sticker + card
Failure buffer= +10% of the above
─────────────────────────────────────────
Cost          = sum of the above
Retail price  = Cost × 2.5 to 3                           (round to ₹_99)
Bulk price    = Cost × 1.6 to 2                           (by quantity tier, see file 04)
```

Worked example, Diya Set of 4:
- First version: 4 × 35 g = 140 g PLA (₹155) + 3.5 h × ₹30 (₹105) + 4 LEDs (₹50) + box/sticker/card (₹45) = ₹355, plus 10% = **₹390 cost**. At ×2.5 that's ₹975, too high for a diya set.
- Cheaper version: lighter 25 g shells, all 4 on one plate, bulk LEDs: 100 g (₹110) + 2.5 h × ₹30 (₹75) + LEDs (₹40) + packaging (₹35) = ₹260, plus 10% = **₹286 cost → ₹699 retail** (×2.4). ✅

Do this maths for every product before you post prices. Check your slicer for real grams and hours.

Courier cost: Shiprocket/Delhivery charge roughly ₹60–120 per 0.5 kg within India. Either price it in ("Free shipping above ₹999") or charge it at checkout. Don't absorb it silently.

## Capacity: the number that decides everything

```
Printer-hours per day ≈ number of printers × 20
```

| Product | Hours/pc | Per printer per day | 1 printer × 10 days |
|---|---|---|---|
| Lantern | 6 | ~3 | ~30 |
| Diya (single) | 0.75 | ~25 | ~250 diyas = ~60 sets |
| Keychain (plate of 20) | 0.2 | ~100 | ~1,000 |
| Coaster set | 1.5 | ~13 | ~130 sets |

Rules that follow from this:
- **Lanterns are made to order and capped.** "Only 25 lanterns this Diwali." Scarcity sells, and it protects your machines.
- **Bulk orders should be keychains and coasters**, which are fast prints. Never accept 200 lanterns.
- Keep a **print queue** (a Google Sheet: order ID · item · colour · personalisation · printer · status · dispatch date).
- For overflow, line up **one other local print shop or a print farm** now as backup, at an agreed per-gram rate.

## Production checklist

- [ ] Filament ordered: marigold/orange, ivory/white, silk gold, indigo/black. 2 kg of each to start, more for your bestseller
- [ ] LED tealights (warm, flicker) × 200
- [ ] Kraft boxes in 2 sizes, crinkle paper, stickers, thank-you cards
- [ ] One finished sample of every product, photographed and weighed
- [ ] Slicer profile saved per product (so reprints are identical)
- [ ] Print queue sheet live
