# Models

Workflow: preview image first → approve → print the STL.

## Lotus rangoli filling board (`lotus_rangoli/`) — approved

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
