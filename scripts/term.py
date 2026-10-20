"""Monospace "terminal grid" text, drawn as vector outlines.

GitHub shows README images in a sandbox that cannot load web fonts, so every
character is converted to a path here (glyphs are defined once per file and
reused with <use>). Wide characters (CJK) take two cells like in a real
terminal, so ASCII art and mixed Chinese/Japanese text always line up.
"""
from __future__ import annotations

import os
import re
import unicodedata
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from svgkit import Canvas

# Google Fonts repository pinned to one commit, so the URLs never move.
GOOGLE_FONTS = "https://raw.githubusercontent.com/google/fonts/47d54ca1ebb14fd864695f1d39dc734f39017c33/ofl/"

FONT_FILES = {
    # key: (path inside google/fonts, variable-font location)
    "jbm": ("jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf", {"wght": 420}),
    "jbm_b": ("jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf", {"wght": 760}),
    "sc": ("notosanssc/NotoSansSC%5Bwght%5D.ttf", {"wght": 450}),
    "sc_b": ("notosanssc/NotoSansSC%5Bwght%5D.ttf", {"wght": 750}),
    "sym": ("notosanssymbols2/NotoSansSymbols2-Regular.ttf", None),
    "thai": ("notosansthai/NotoSansThai%5Bwdth,wght%5D.ttf", {"wght": 450, "wdth": 100}),
}
CHAINS = {False: ["jbm", "sc", "sym", "thai"], True: ["jbm_b", "sc_b", "sym", "thai"]}

ASC, DESC = 1.02, 0.30  # JetBrains Mono line metrics (em)
CELL = 0.6  # JetBrains Mono advance (em)
Y_NUDGE = {"sc": 0.05, "sc_b": 0.05}  # CJK sits a little low next to Latin


def _num(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Font:
    def __init__(self, key: str, path: Path, location):
        self.key = key
        self.tt = TTFont(str(path), lazy=True)
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.gs = self.tt.getGlyphSet(location=location) if location else self.tt.getGlyphSet()

    def has(self, ch: str) -> bool:
        return ord(ch) in self.cmap

    def advance(self, g: str) -> float:
        return self.gs[g].width / self.upm  # em

    def path(self, g: str, size: float) -> str:
        s = size / self.upm
        pen = SVGPathPen(self.gs, ntos=_num)
        self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, 0, 0)))
        return pen.getCommands()


def _font_dir() -> Path:
    d = Path(os.environ.get("FONT_CACHE", Path(__file__).resolve().parent.parent / ".cache" / "fonts"))
    d.mkdir(parents=True, exist_ok=True)
    return d


_FONTS: dict[str, Font] = {}


def font(key: str) -> Font:
    if key not in _FONTS:
        rel, loc = FONT_FILES[key]
        name = rel.split("/")[-1].replace("%5B", "[").replace("%5D", "]")
        dest = _font_dir() / name
        if not dest.exists():
            print(f"  downloading {name} ...", flush=True)
            tmp = dest.with_name(dest.name + ".part")
            with urllib.request.urlopen(GOOGLE_FONTS + rel, timeout=300) as r, open(tmp, "wb") as f:
                f.write(r.read())
            tmp.rename(dest)
        _FONTS[key] = Font(key, dest, loc)
    return _FONTS[key]


_WARNED: set[str] = set()


def resolve(ch: str, bold: bool = False, prefer: tuple = ()):
    """Pick the font for a character and how many cells it takes."""
    for k in (*prefer, *CHAINS[bold]):
        f = font(k)
        if f.has(ch):
            g = f.cmap[ord(ch)]
            adv = f.advance(g)
            wide = unicodedata.east_asian_width(ch) in ("W", "F") or adv > 0.78
            return f, g, adv, 2 if wide else 1
    if ch not in _WARNED:  # e.g. colour emoji: draw a box like a terminal would
        _WARNED.add(ch)
        print(f"  warning: no font has {ch!r} (U+{ord(ch):04X}), drawing □ instead")
    return resolve("□", bold)


def _gid(f: Font, g: str, size: float) -> str:
    return f"{f.key}{int(size * 10)}-{re.sub(r'[^A-Za-z0-9_-]', '_', g)}"


def glyph(c: Canvas, ch: str, x: float, y: float, size: float, bold: bool = True, prefer: tuple = (),
          attrs: str = "") -> str:
    """One character with the left edge of its advance at x and its baseline at y."""
    f, g, adv, n = resolve(ch, bold, prefer)
    gid = _gid(f, g, size)
    if gid not in c.defs:
        c.define(gid, f'<path id="{gid}" d="{f.path(g, size)}"/>')
    a = f" {attrs}" if attrs else ""
    return f'<use href="#{gid}" x="{_num(x)}" y="{_num(y)}"{a}/>'


def glyph_box(ch: str, size: float, bold: bool = True, prefer: tuple = ()) -> tuple[float, float, float, float]:
    """Ink bounds (x0, y0, x1, y1) in px, relative to the glyph origin, y pointing down."""
    from fontTools.pens.boundsPen import BoundsPen
    f, g, adv, n = resolve(ch, bold, prefer)
    pen = BoundsPen(f.gs)
    f.gs[g].draw(pen)
    k = size / f.upm
    x0, y0, x1, y1 = pen.bounds or (0, 0, 0, 0)
    return x0 * k, -y1 * k, x1 * k, -y0 * k


def advance(ch: str, size: float, bold: bool = True, prefer: tuple = ()) -> float:
    return resolve(ch, bold, prefer)[2] * size


def cells(s: str) -> int:
    return sum(resolve(ch)[3] if ch != " " else 1 for ch in s)


MARK = re.compile(r"\[(/|[a-z0-9_ ]+)\]")


def parse(markup: str, default: str = "text") -> list[tuple[str, str, bool]]:
    """'[pink b]Nyan[/]ko' -> [('Nyan', 'pink', True), ('ko', 'text', False)].

    Write '[[' for a literal '['.
    """
    out = []
    stack = [(default, False)]
    pos = 0
    s = markup.replace("[[", "\x00")
    for m in MARK.finditer(s):
        if m.start() > pos:
            out.append((s[pos:m.start()].replace("\x00", "["), *stack[-1]))
        tag = m.group(1)
        if tag == "/":
            if len(stack) > 1:
                stack.pop()
        else:
            parts = tag.split()
            color = next((p for p in parts if p != "b"), stack[-1][0])
            stack.append((color, "b" in parts))
        pos = m.end()
    if pos < len(s):
        out.append((s[pos:].replace("\x00", "["), *stack[-1]))
    return [o for o in out if o[0]]


def plain(markup: str) -> str:
    return "".join(t for t, _, _ in parse(markup))


class Term:
    """A grid of character cells starting at (x, y) on a canvas."""

    def __init__(self, c: Canvas, P: dict, x: float, y: float, size: float = 14.0, lh: float = 1.55):
        self.c, self.P = c, P
        self.x, self.y, self.size = x, y, size
        self.cw = size * CELL
        self.lh = size * lh

    def col_x(self, col: float) -> float:
        return self.x + col * self.cw

    def row_y(self, row: float) -> float:
        """Top of a row."""
        return self.y + row * self.lh

    def baseline(self, row: float) -> float:
        return self.row_y(row) + (self.lh - (ASC + DESC) * self.size) / 2 + ASC * self.size

    def _glyph(self, f: Font, g: str) -> str:
        gid = _gid(f, g, self.size)
        if gid not in self.c.defs:
            self.c.define(gid, f'<path id="{gid}" d="{f.path(g, self.size)}"/>')
        return gid

    def chars(self, col: float, row: float, s: str, bold: bool = False, cls=None, start: int = 0):
        """Yield (svg_use, cells) per character. cls(i) -> class for char i."""
        cx = col
        i = -1
        skip_to = 0
        for i, ch in enumerate(s):
            if i < skip_to:
                continue
            if ch == " ":
                cx += 1
                continue
            if ch == "█":  # full blocks become one rectangle per run, so no seams show
                j = i
                while j < len(s) and s[j] == "█":
                    j += 1
                top = self.baseline(row) - ASC * self.size
                k = cls(start + i) if cls else None
                kc = f' class="{k}"' if k else ""
                yield (f'<rect x="{_num(self.col_x(cx))}" y="{_num(top)}" width="{_num((j - i) * self.cw + .4)}" '
                       f'height="{_num((ASC + DESC) * self.size + .4)}"{kc}/>'), j - i
                cx += j - i
                skip_to = j
                continue
            f, g, adv, n = resolve(ch, bold)
            gid = self._glyph(f, g)
            x = self.col_x(cx) + (n * self.cw - adv * self.size) / 2
            y = self.baseline(row) + Y_NUDGE.get(f.key, 0) * self.size
            k = cls(start + i) if cls else None
            kc = f' class="{k}"' if k else ""
            yield f'<use href="#{gid}" x="{_num(x)}" y="{_num(y)}"{kc}/>', n
            cx += n

    def block_runs(self, col: float, row: float, s: str) -> list[tuple[float, float, float, float]]:
        """(x, y, w, h) of every run of █ in s."""
        out, i = [], 0
        while i < len(s):
            if s[i] != "█":
                i += 1
                continue
            j = i
            while j < len(s) and s[j] == "█":
                j += 1
            top = self.baseline(row) - ASC * self.size
            out.append((self.col_x(col + i), top, (j - i) * self.cw, (ASC + DESC) * self.size))
            i = j
        return out

    def text(self, col: float, row: float, s: str, color: str = "text", bold: bool = False, cls=None,
             start: int = 0, attrs: str = "") -> str:
        fill = self.P.get(color, color)
        uses = "".join(u for u, _ in self.chars(col, row, s, bold, cls, start))
        a = f" {attrs}" if attrs else ""
        return f'<g fill="{fill}"{a}>{uses}</g>' if uses else ""

    def markup(self, col: float, row: float, m: str, cls=None, default: str = "text") -> tuple[str, int]:
        """Draw '[pink]colored[/] text'. Returns (svg, cells used)."""
        out, cx, i = [], col, 0
        for t, color, bold in parse(m, default):
            out.append(self.text(cx, row, t, color, bold, cls, start=i))
            cx += cells(t)
            i += len(t)
        return "".join(out), int(cx - col)
