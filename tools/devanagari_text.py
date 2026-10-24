"""Shape Devanagari text with HarfBuzz and return its outline as polygons.

Uses real OpenType shaping, so matras and conjuncts (e.g. the ु under श)
come out correctly. Needs: pip install uharfbuzz fonttools
"""
import numpy as np
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont


class _PolyPen(BasePen):
    """Flattens glyph contours into polygons (lists of (x, y))."""

    def __init__(self, glyphset, steps=12):
        super().__init__(glyphset)
        self.polys, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, self.steps + 1)[1:]:
            u = 1 - t
            self.cur.append(tuple(u**3 * np.array(p0) + 3 * u * u * t * np.array(p1)
                                  + 3 * u * t * t * np.array(p2) + t**3 * np.array(p3)))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, self.steps + 1)[1:]:
            u = 1 - t
            self.cur.append(tuple(u * u * np.array(p0) + 2 * u * t * np.array(p1) + t * t * np.array(p2)))

    def _closePath(self):
        if len(self.cur) > 2:
            self.polys.append(self.cur)
        self.cur = []

    _endPath = _closePath


def text_polygons(text, font_path):
    """Polygons (font units, y up) for the shaped text, in even-odd/nonzero form."""
    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {})

    tt = TTFont(font_path)
    glyphset = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    polys, x, y = [], 0, 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = _PolyPen(glyphset)
        glyphset[order[info.codepoint]].draw(pen)
        ox, oy = x + pos.x_offset, y + pos.y_offset
        polys += [[(px + ox, py + oy) for px, py in p] for p in pen.polys]
        x += pos.x_advance
        y += pos.y_advance
    return polys
