"""Tiny helpers for building one SVG file."""
from __future__ import annotations

from xml.sax.saxutils import escape


class Canvas:
    def __init__(self, w: float, h: float):
        self.w, self.h = w, h
        self.css: list[str] = []
        self._css_keys: set[str] = set()
        self.defs: dict[str, str] = {}
        self.body: list[str] = []
        self._n = 0

    def uid(self, p: str = "u") -> str:
        self._n += 1
        return f"{p}{self._n}"

    def add(self, *parts: str):
        self.body.extend(parts)

    def style(self, css: str, key: str | None = None):
        if key is not None:
            if key in self._css_keys:
                return
            self._css_keys.add(key)
        self.css.append(css)

    def define(self, did: str, content: str):
        self.defs.setdefault(did, content)

    def svg(self, title: str) -> str:
        t = escape(title, {'"': "&quot;"})
        css = "".join(self.css) + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:g}" height="{self.h:g}" '
            f'viewBox="0 0 {self.w:g} {self.h:g}" role="img" aria-label="{t}">'
            f"<title>{t}</title><style>{css}</style>"
            f'<defs>{"".join(self.defs.values())}</defs>'
            f'{"".join(self.body)}</svg>'
        )


def frames_css(c: Canvas, name: str, timeline: list[tuple[int, float]], n_frames: int) -> list[str]:
    """Flip-book animation.

    timeline: [(frame_index, seconds), ...] played in a loop.
    Returns the class name for every frame; frame k is visible only during
    its slots in the timeline.
    """
    total = sum(d for _, d in timeline)
    classes = []
    for k in range(n_frames):
        cls = f"{name}-f{k}"
        stops = []
        t = 0.0
        for idx, d in timeline:
            a, b = t / total * 100, (t + d) / total * 100
            if idx == k:
                stops.append((a, b))
            t += d
        if not stops:
            c.style(f".{cls}{{opacity:0}}")
            classes.append(cls)
            continue
        kf = []
        prev_end = 0.0
        for a, b in stops:
            if a > prev_end + 1e-6:
                kf.append(f"{prev_end:.3f}%{{opacity:0}}")
                kf.append(f"{a:.3f}%{{opacity:0}}")
            kf.append(f"{a:.3f}%{{opacity:1}}")
            kf.append(f"{b:.3f}%{{opacity:1}}")
            prev_end = b
        if prev_end < 100:
            kf.append(f"{prev_end:.3f}%{{opacity:0}}")
            kf.append("100%{opacity:0}")
        c.style(
            f"@keyframes {cls}{{{''.join(kf)}}}"
            f".{cls}{{animation:{cls} {total:.2f}s step-end infinite}}"
        )
        classes.append(cls)
    return classes
