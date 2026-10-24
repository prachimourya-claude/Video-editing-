# Models

Workflow: preview image first → approve → print the STL.

## Lotus rangoli board 150 × 110 (`lotus_rangoli_150x110/`) — final, chosen size

Same approved design, stretched to 150 × 110 mm (petal curves scale; border stays 2.2 mm wide).

- Size 150.0 × 110.0 × 4.0 mm: **2.0 mm solid floor + 2.0 mm raised border**, 2.2 mm wide
- ~27 g PLA at 100 % infill
- Mesh checked: one watertight part, every edge shared by exactly two faces, no degenerate faces, no floating parts
- Rebuild: `python3 tools/lotus_rangoli_vector.py ps1-labs-diwali-2026/models/lotus_rangoli_150x110 --width 150 --height 110 --floor 2.0 --ridge-h 2.0 --stl`
- Print: flat side down, no supports, 0.2 mm layers. Two colours: filament change at 2.0 mm (start of layer 11) for the borders.
- `lotus_rangoli_166x110/` holds the unchosen 166 × 110 preview only.

## Lotus rangoli filling board 150 × 99.4 (`lotus_rangoli/`) — earlier version

Solid board (no through-holes) with raised petal outlines, drawn as smooth mirrored
vector petals based on `reference.png`. Rangoli powder sits on the floor; the ridges
make the compartments.

- Size 149.9 × 99.4 × 4.0 mm: 2.2 mm solid floor + 1.8 mm raised borders, 2.2 mm wide, single straight wall
- ~26 g PLA at 100 % infill (less with normal infill)
- Mesh checked: one part, watertight, every edge shared by exactly two faces, no degenerate faces, no floating parts
- Previews: `lotus_rangoli_preview_top.png`, `lotus_rangoli_preview_angle.png`
- Rebuild: `python3 tools/lotus_rangoli_vector.py ps1-labs-diwali-2026/models/lotus_rangoli --stl`
  (edit `WIDTH`, `BASE_T`, `RIDGE_H`, `RIDGE_W` or the petal points at the top of the script)
- Print: flat side down, no supports, 0.2 mm layers. Two colours: filament change at 2.2 mm (start of layer 12) for the borders.

## Lotus diya (`diya_lotus.stl`) — draft, not print-ready

Test shell for a 38 mm LED tealight, from `tools/diya_lotus.py`. The low petals have
overhangs steeper than 45°; fix before printing.
