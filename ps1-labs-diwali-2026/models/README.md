# Models

Workflow: preview image first → approve → print the STL.

## Lotus rangoli filling board (`lotus_rangoli/`)

Solid board (no through-holes) with raised outlines traced from `reference.png`.
Rangoli powder sits on the floor; the ridges make the compartments.

- Size 150 × 102.5 × 4.0 mm: 2.2 mm solid floor + 1.8 mm raised ridges (~2.5–3 mm wide, rounded top), outer wall all round
- ~29 g PLA at 100 % infill (less with normal infill)
- Mesh checked: one part, watertight (every edge shared by exactly two faces), no holes through the floor
- Previews: `lotus_rangoli_preview_top.png`, `lotus_rangoli_preview_angle.png`
- Rebuild: `python3 tools/lotus_rangoli_board.py ps1-labs-diwali-2026/models/lotus_rangoli/reference.png ps1-labs-diwali-2026/models/lotus_rangoli --stl`
  (change `WIDTH`, `BASE_T`, `RIDGE_H` at the top of the script)
- Print: flat side down, no supports, 0.2 mm layers. Two colours: pause at 2.2 mm (layer 12) and switch to ivory.

## Lotus diya (`diya_lotus.stl`) — draft, not print-ready

Test shell for a 38 mm LED tealight, from `tools/diya_lotus.py`. The low petals have
overhangs steeper than 45°; fix before printing.
