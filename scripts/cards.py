"""Builders for every picture on the profile. Each returns an SVG string."""
from __future__ import annotations

import random
from datetime import date

import ascii_art as art
from svgkit import Canvas, frames_css
from term import Term, cells, parse, plain, resolve
from themes import gradient, mix

W = 840  # every card is 840 px wide; GitHub scales it to the column width
MARGIN = 10  # room for the window shadow
TITLE_H = 34
PAD = 24


# ----------------------------------------------------------------- helpers

class Clock:
    """Turns time windows inside one looping animation into CSS classes."""

    def __init__(self, c: Canvas, total: float, name: str):
        self.c, self.total, self.name = c, total, name
        self._cache: dict[tuple, str] = {}

    def show(self, start: float, end: float, static: bool = False) -> str:
        """Class that is visible from `start` to `end` seconds of every loop.

        static: whether the element shows when animations are turned off.
        """
        key = (round(start, 3), round(end, 3), static)
        if key in self._cache:
            return self._cache[key]
        cls = f"{self.name}{len(self._cache)}"
        a = max(0.0, start) / self.total * 100
        b = min(end, self.total) / self.total * 100
        kf = ["0%{opacity:0}"] if a > 0 else []
        kf.append(f"{a:.3f}%{{opacity:1}}")
        if b < 100:
            kf.append(f"{b:.3f}%{{opacity:0}}")
            kf.append("100%{opacity:0}")
        self.c.style(
            f".{cls}{{opacity:{1 if static else 0};animation:{cls}k {self.total:.2f}s step-end infinite}}"
            f"@keyframes {cls}k{{{''.join(kf)}}}"
        )
        self._cache[key] = cls
        return cls


def window(c: Canvas, P: dict, h: float, title: str) -> tuple[float, float]:
    """Draw a terminal window filling the canvas. Returns the content origin."""
    x, y, w = MARGIN, MARGIN, c.w - 2 * MARGIN
    wh = h - 2 * MARGIN
    dark = P["name"] == "dark"
    c.define(
        "shadow",
        '<filter id="shadow" x="-6%" y="-8%" width="112%" height="125%">'
        f'<feDropShadow dx="0" dy="5" stdDeviation="6" flood-color="{P["shadow"]}" '
        f'flood-opacity="{0.45 if dark else 0.13}"/></filter>',
    )
    c.add(
        f'<rect x="{x}" y="{y}" width="{w}" height="{wh}" rx="12" fill="{P["base"]}" filter="url(#shadow)"/>',
        f'<path d="M{x},{y + TITLE_H} V{y + 12} a12,12 0 0 1 12,-12 H{x + w - 12} a12,12 0 0 1 12,12 V{y + TITLE_H} Z" '
        f'fill="{P["mantle"]}"/>',
        f'<path d="M{x},{y + TITLE_H} H{x + w}" stroke="{P["crust"]}" stroke-width="1"/>',
        f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{wh - 1}" rx="11.5" fill="none" '
        f'stroke="{P["surface0"]}"/>',
    )
    for i, col in enumerate(("red", "yellow", "green")):
        c.add(f'<circle cx="{x + 20 + i * 20}" cy="{y + TITLE_H / 2}" r="6" fill="{P[col]}"/>')
    t = Term(c, P, 0, y + (TITLE_H - 12.5 * 1.4) / 2, size=12.5, lh=1.4)
    tw = cells(title) * t.cw
    t.x = x + (w - tw) / 2
    c.add(t.text(0, 0, title, "subtext0"))
    return x + PAD, y + TITLE_H + 16


def prompt(cfg: dict) -> str:
    user = cfg["profile"]["user"]
    return f"[mauve b]{user}[/][overlay1]@[/][pink b]github[/] [teal b]~[/] [green b]❯[/] "


def petals(c: Canvas, P: dict, n: int, x0: float, y0: float, x1: float, y1: float, seed: int = 3) -> str:
    """Pink flower characters drifting down behind the text."""
    rnd = random.Random(seed)
    t = Term(c, P, 0, 0, size=13)
    out = []
    for i in range(n):
        ch = rnd.choice("✿❀✿❀*·")
        sx = rnd.uniform(x0, x1)
        dx = rnd.uniform(30, 120)
        sway = rnd.uniform(8, 22)
        dur = rnd.uniform(10, 18)
        delay = -rnd.uniform(0, dur)
        op = rnd.uniform(0.25, 0.55)
        name = c.uid("pt")
        h = y1 - y0
        c.style(
            f"@keyframes {name}{{"
            f"0%{{transform:translate({sx:.0f}px,{y0:.0f}px)}}"
            f"30%{{transform:translate({sx + dx * .3 + sway:.0f}px,{y0 + h * .3:.0f}px)}}"
            f"65%{{transform:translate({sx + dx * .65 - sway:.0f}px,{y0 + h * .65:.0f}px)}}"
            f"100%{{transform:translate({sx + dx:.0f}px,{y1:.0f}px)}}}}"
            f".{name}{{animation:{name} {dur:.1f}s linear {delay:.1f}s infinite;"
            f"transform:translate({sx + dx * .5:.0f}px,{y0 + h * rnd.uniform(.1, .9):.0f}px)}}"
        )
        color = rnd.choice(["pink", "pink", "flamingo", "mauve"])
        glyph = t.text(0, 0, ch, color, attrs='class="spin"')
        out.append(f'<g class="{name}" opacity="{op:.2f}">{glyph}</g>')
    c.style(
        ".spin>use{animation:spin 6s linear infinite;transform-box:fill-box;transform-origin:center}"
        "@keyframes spin{to{transform:rotate(360deg)}}",
        key="spin",
    )
    return "".join(out)


def cursor(c: Canvas, P: dict, t: Term, col: float, row: float, cls: str = "") -> str:
    c.style(".blink{animation:blink 1.06s step-end infinite}@keyframes blink{50%{opacity:0}}", key="blink")
    x, y = t.col_x(col), t.row_y(row) + (t.lh - t.size * 1.3) / 2
    k = f' class="{cls}"' if cls else ""
    return (
        f'<g{k}><rect class="blink" x="{x:.1f}" y="{y:.1f}" width="{t.cw:.1f}" height="{t.size * 1.3:.1f}" '
        f'rx="1.5" fill="{P["rosewater"]}" opacity=".85"/></g>'
    )


# ----------------------------------------------------------------- header

def header(cfg: dict, P: dict) -> str:
    rows = art.banner(cfg["profile"]["banner"])
    bw = max(len(r) for r in rows)
    inner = W - 2 * MARGIN - 2 * PAD
    size = min(14.4, inner / bw / 0.6)
    lines = cfg["header"]["commands"]
    H = 380 + (14 * 1.5) * max(0, max(len(x["output"]) for x in lines) - 2)
    c = Canvas(W, H)
    ox, oy = window(c, P, H, cfg["header"]["title"])

    # falling petals (drawn first so they stay behind the text)
    c.add(petals(c, P, 16, MARGIN + 8, MARGIN + TITLE_H, W - MARGIN - 40, H - MARGIN - 20))

    small = Term(c, P, ox, oy, size=14, lh=1.5)
    c.add(small.text(0, 0, cfg["header"]["last_login"].format(date=date.today().strftime("%a %b %d")), "overlay1"))

    # banner, centred, with a light sweeping across it now and then
    bt = Term(c, P, 0, oy + 3 * size * 1.32 - 4, size=size, lh=1.32)
    bt.x = (W - bw * bt.cw) / 2
    stops = [P["pink"], P["mauve"], P["blue"], P["teal"]]
    grad = c.uid("bgrad")
    bx1 = bt.x + bw * bt.cw
    c.define(grad, f'<linearGradient id="{grad}" gradientUnits="userSpaceOnUse" x1="{bt.x:.0f}" x2="{bx1:.0f}" '
                   f'y1="0" y2="0">' + "".join(f'<stop offset="{i / (len(stops) - 1):.2f}" stop-color="{s}"/>'
                                              for i, s in enumerate(stops)) + "</linearGradient>")
    shade, blocks = [], []
    for r, line in enumerate(rows):
        # the shadow lines (╔═╗║╚╝) get a dimmed colour per column
        for col, ch in enumerate(line):
            if ch not in " █":
                shade.append(bt.text(col, r, ch, mix(gradient(stops, col / (bw - 1)), P["base"], 0.5)))
        # the solid blocks are drawn as rectangles filled with one smooth gradient
        masked = "".join(ch if ch == "█" else " " for ch in line)
        blocks += [u for u, _ in bt.chars(0, r, masked)]
    c.add("".join(shade), f'<g fill="url(#{grad})">{"".join(blocks)}</g>')
    clip = c.uid("bclip")
    c.define(clip, f'<clipPath id="{clip}">{"".join(blocks)}</clipPath>')
    shine = c.uid("shine")
    c.define(
        shine,
        f'<linearGradient id="{shine}" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity="{0.55 if P["name"] == "dark" else 0.7}"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
    )
    bx0, by0 = bt.x, bt.row_y(0)
    c.style(
        f"@keyframes sweep{{0%{{transform:translateX({bx0 - 160:.0f}px)}}"
        f"22%,100%{{transform:translateX({bx0 + bw * bt.cw + 40:.0f}px)}}}}"
        f".sweep{{animation:sweep 7s ease-in-out 1.2s infinite;transform:translateX(-400px)}}"
    )
    c.add(
        f'<g clip-path="url(#{clip})"><rect class="sweep" x="0" y="{by0:.0f}" width="120" '
        f'height="{len(rows) * bt.lh:.0f}" fill="url(#{shine})"/></g>'
    )

    # little cat sitting on top of the last letter
    top = rows[0]
    end = top.rfind("█")
    start = end
    while start > 0 and top[start - 1] == "█":
        start -= 1
    centre_x = bt.x + (start + end + 1) / 2 * bt.cw
    sit_w = len(art.SIT[0]) * 14 * 0.6
    ct = Term(c, P, centre_x - sit_w / 2, by0 - 3 * 14 * 1.32 + 4, size=14, lh=1.32)
    for r, line in enumerate(art.SIT):
        c.add(ct.text(0, r, line, "pink", bold=True))
    timeline = [("normal", 3.2), ("blink", .14), ("normal", .2), ("blink", .14), ("normal", 2.4),
                ("look", 1.1), ("normal", 1.6), ("happy", 1.4)]
    names = list(art.SIT_EYES)
    cls = frames_css(c, "sit", [(names.index(n), d) for n, d in timeline], len(names))
    er, ec = art.SIT_EYE_POS
    for k, n in enumerate(names):
        c.style(f".{cls[k]}{{opacity:{1 if k == 0 else 0}}}")
        c.add(f'<g class="{cls[k]}">{ct.text(ec, er, art.SIT_EYES[n], "text", bold=True)}</g>')

    # subtitle under the banner
    sub_y = by0 + len(rows) * bt.lh + 12
    st = Term(c, P, 0, sub_y, size=14, lh=1.5)
    m = cfg["header"]["subtitle"]
    st.x = (W - cells(plain(m)) * st.cw) / 2
    c.add(st.markup(0, 0, m)[0])

    # typing terminal
    tt = Term(c, P, ox, sub_y + 2.2 * st.lh, size=14, lh=1.5)
    pm = prompt(cfg)
    pcols = cells(plain(pm))
    c.add(tt.markup(0, 0, pm)[0])
    per_char, gap_out, hold, gap_next = 0.055, 0.35, 2.8, 0.45
    seq, t = [], 0.4
    for item in lines:
        n = len(item["cmd"])
        seq.append((t, item))
        t += n * per_char + gap_out + hold + gap_next
    total = t
    clock = Clock(c, total, "ty")
    moves = []
    for k, (t0, item) in enumerate(seq):
        cmd = item["cmd"]
        n = len(cmd)
        t_typed = t0 + n * per_char
        t_out = t_typed + gap_out
        t_clear = t_out + hold

        def char_cls(i, t0=t0, t_clear=t_clear, first=(k == 0)):
            return clock.show(t0 + (i + 1) * per_char, t_clear, static=first)

        c.add(tt.text(pcols, 0, cmd, "text", cls=char_cls))
        for j, out in enumerate(item["output"]):
            cls_o = clock.show(t_out + j * 0.12, t_clear, static=(k == 0))
            c.add(f'<g class="{cls_o}">{tt.markup(0, 1 + j, out)[0]}</g>')
        # cursor positions while typing
        col = pcols
        moves.append((t0, col))
        for i, ch in enumerate(cmd):
            col += 1 if ch == " " else resolve(ch)[3]
            moves.append((t0 + (i + 1) * per_char, col))
        moves.append((t_clear, pcols))
    kf = [f"{tm / total * 100:.3f}%{{transform:translateX({(cl - pcols) * tt.cw:.1f}px)}}" for tm, cl in moves]
    first_end = (cells(lines[0]["cmd"]) + 0) * tt.cw
    c.style(f"@keyframes curmove{{0%{{transform:translateX(0)}}{''.join(kf)}}}"
            f".curmove{{animation:curmove {total:.2f}s step-end infinite;transform:translateX({first_end:.1f}px)}}")
    c.add(cursor(c, P, tt, pcols, 0, "curmove"))
    return c.svg(cfg["header"]["alt"])


# ----------------------------------------------------------------- neofetch

def neofetch(cfg: dict, P: dict, stats: dict) -> str:
    info = info_lines(cfg, stats)
    size, lh = 14, 1.45
    rows_needed = 2 + max(len(info), len(art.FACE) + 1)
    H = MARGIN * 2 + TITLE_H + 16 + rows_needed * size * lh + 20
    c = Canvas(W, H)
    ox, oy = window(c, P, H, "neofetch")
    t = Term(c, P, ox, oy, size=size, lh=lh)
    c.add(t.markup(0, 0, prompt(cfg) + "neofetch")[0])

    # the cat, vertically centred next to the info column
    fx, fy = 1, 2 + max(0.6, (len(info) - len(art.FACE)) / 2)
    stops = [P["pink"], P["mauve"], P["lavender"]]
    for r, line in enumerate(art.FACE):
        color = gradient(stops, r / (len(art.FACE) - 1))
        c.add(t.text(fx, fy + r, line, color, bold=True))
    for r, col, s in art.FACE_WHISKERS:
        c.add(t.text(fx + col, fy + r, s, "overlay2", bold=True))
    exprs = ["normal", "blink", "happy", "meow", "wink"]
    timeline = [("normal", 2.8), ("blink", .13), ("normal", .16), ("blink", .13), ("normal", 2.6),
                ("happy", 1.6), ("normal", 2.2), ("meow", 1.3), ("normal", 2.4), ("wink", 0.9)]
    total = sum(d for _, d in timeline)
    cls = frames_css(c, "face", [(exprs.index(n), d) for n, d in timeline], len(exprs))
    for k, e in enumerate(exprs):
        c.style(f".{cls[k]}{{opacity:{1 if k == 0 else 0}}}")
        parts = "".join(t.text(fx + col, fy + r, s, color, bold=True) for r, col, s, color in art.face_features(e))
        c.add(f'<g class="{cls[k]}">{parts}</g>')
    # a heart floats up while it's happy, "にゃ～" while it meows
    t_happy = sum(d for _, d in timeline[:5])
    t_meow = sum(d for _, d in timeline[:7])
    clock = Clock(c, total, "fx")
    heart = t.text(fx + art.FACE_W - 3, fy + 1, "♡", "red", bold=True)
    a, b = t_happy / total * 100, (t_happy + 1.6) / total * 100
    c.style(
        f"@keyframes floaty{{0%,{a:.2f}%{{transform:translateY(8px)}}{b:.2f}%,100%{{transform:translateY(-12px)}}}}"
        f".floaty{{animation:floaty {total:.2f}s linear infinite}}"
    )
    c.add(f'<g class="{clock.show(t_happy, t_happy + 1.6)}"><g class="floaty">{heart}</g></g>')
    c.add(f'<g class="{clock.show(t_meow, t_meow + 1.3)}">'
          f'{t.markup(fx + art.FACE_W - 1, fy + 7, "[pink b]にゃ～[/]")[0]}</g>')
    # twinkling stars around the head
    c.style(".tw{animation:tw 2.6s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}", key="tw")
    for (r, col, ch, color, d) in [(0, 0, "+", "yellow", 0), (2, 31, "*", "pink", .9), (8, -1, "·", "teal", 1.7),
                                   (-0.6, 24, "·", "mauve", .4), (10, 30, "+", "teal", 1.2)]:
        c.add(f'<g class="tw" style="animation-delay:{d}s">{t.text(fx + col, fy + r, ch, color, bold=True)}</g>')

    # info column
    ix = fx + art.FACE_W + 5
    for r, m in enumerate(info):
        if isinstance(m, str):
            c.add(t.markup(ix, 2 + r, m)[0])
        else:  # callable drawing something special (bars, palette)
            c.add(m(t, ix, 2 + r))
    return c.svg("neofetch: about Nyankomint and GitHub stats")


def _uptime(days: int) -> str:
    y, d = divmod(days, 365)
    parts = []
    if y:
        parts.append(f"{y} year{'s' if y > 1 else ''}")
    parts.append(f"{d} day{'s' if d != 1 else ''}")
    return ", ".join(parts)


def info_lines(cfg: dict, s: dict) -> list:
    login = cfg["profile"]["user"]
    k = lambda name: f"[mauve b]{name:<10}[/]"  # noqa: E731
    num = lambda v: f"[peach b]{v:,}[/]"  # noqa: E731
    dot = " [overlay1]·[/] "
    lines: list = [f"[pink b]{login}[/][overlay1]@[/][mauve b]github[/]",
                   f"[overlay0]{'─' * (len(login) + 7)}[/]"]
    for key, val in cfg["neofetch"]["about"]:
        lines.append(k(key) + val)
    lines += [
        k("uptime") + _uptime(s["days"]),
        k("repos") + num(s["repos"]) + " public" + dot + f"[yellow b]★[/] {num(s['stars'])}",
        k("commits") + num(s["commits"]) + f" in {s['year_label']}",
        k("prs") + num(s["prs"]) + dot + "issues " + num(s["issues"]),
        k("followers") + num(s["followers"]) + dot + "following " + num(s["following"]),
        k("streak") + num(s["streak"]) + f" day{'s' if s['streak'] != 1 else ''}"
        + f" [overlay1](best {s['best_streak']})[/]",
    ]
    total_size = sum(v for _, v in s["languages"]) or 1
    langs = [(n, v) for n, v in s["languages"] if v / total_size >= 0.01][:4]  # hide slivers under 1%
    accents = ["pink", "mauve", "blue", "teal", "peach", "yellow"]
    if langs:
        def bar(t: Term, col: float, row: float, langs=langs):
            n, out, x = 30, [], 0
            tot = sum(v for _, v in langs)
            widths = [max(1, round(v / tot * n)) for _, v in langs]
            widths[0] += n - sum(widths)
            out.append(t.markup(col, row, k("languages"))[0])
            for (name, _), wdt, a in zip(langs, widths, accents):
                out.append(t.text(col + 10 + x, row, "█" * wdt, a))
                x += wdt
            return "".join(out)

        def legend(t: Term, col: float, row: float, langs=langs):
            tot = sum(v for _, v in langs)
            m = "  ".join(f"[{a}]●[/] {name} [overlay1]{v / tot * 100:.0f}%[/]"
                          for (name, v), a in zip(langs[:3], accents))
            return t.markup(col + 10, row, m)[0]

        lines += [bar, legend]
    else:
        lines.append(k("languages") + "[overlay1]no public code yet[/]")
    lines.append("")

    def palette(t: Term, col: float, row: float):
        out = []
        for i, a in enumerate(["red", "peach", "yellow", "green", "teal", "blue", "mauve", "pink"]):
            out.append(t.text(col + i * 4, row, "███", a))
        return "".join(out)

    lines.append(palette)
    return lines


# ----------------------------------------------------------------- activity heatmap

MONTHS_JA = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]


def dither_defs(c: Canvas, P: dict):
    """Fill patterns that look like the shade characters ░ ▒ ▓ (2 px dots on a 4 px grid)."""
    h = P["heat"]
    t = 1 / 3
    q = t / 2

    def pat(pid, bg, fg, squares):
        sq = "".join(f'<rect x="{x * q:.4f}" y="{y * q:.4f}" width="{q:.4f}" height="{q:.4f}" fill="{fg}"/>'
                     for x, y in squares)
        c.define(pid, f'<pattern id="{pid}" width="{t:.4f}" height="{t:.4f}" patternContentUnits="objectBoundingBox">'
                      f'<rect width="{t:.4f}" height="{t:.4f}" fill="{bg}"/>{sq}</pattern>')

    pat("d1", h[0], h[2], [(0, 0)])
    pat("d2", h[1], h[3], [(0, 0), (1, 1)])
    pat("d3", h[2], h[4], [(0, 0), (1, 0), (0, 1)])


def heat_cell(P: dict, x: float, y: float, size: float, level: int) -> str:
    if level == 0:  # an empty day is just a dot, like '·'
        return f'<circle cx="{x + size / 2:g}" cy="{y + size / 2:g}" r="1.4" fill="{P["surface2"]}"/>'
    fill = P["heat"][4] if level == 4 else f"url(#d{level})"
    return f'<rect x="{x:g}" y="{y:g}" width="{size:g}" height="{size:g}" rx="1.5" fill="{fill}"/>'


def activity(cfg: dict, P: dict, stats: dict) -> str:
    weeks = stats["weeks"][-53:]  # list of weeks; each a list of (iso_date, level 0-4, count)
    nweeks = len(weeks)
    pitch, cell, label_w = 14, 12, 28
    y_grid = MARGIN + TITLE_H + 16 + 2 * 14 * 1.5
    y_cells = y_grid + 20
    y_run = y_cells + 7 * pitch + 10
    y_sum = y_run + 14 * 1.4 + 12
    H = y_sum + 14 * 1.5 + 18 + MARGIN
    c = Canvas(W, H)
    ox, oy = window(c, P, H, "nyan-log")
    dither_defs(c, P)
    t = Term(c, P, ox, oy, size=14, lh=1.5)
    c.add(t.markup(0, 0, prompt(cfg) + "nyan-log --heatmap --since '1 year ago'")[0])

    grid_x0 = round(ox + label_w)
    lt = Term(c, P, grid_x0, y_grid, size=11.5, lh=1.4)
    last_month = date.fromisoformat(weeks[0][0][0]).month
    for wi, week in enumerate(weeks):
        d0 = date.fromisoformat(week[0][0])
        if d0.month != last_month and wi < nweeks - 2:
            c.add(lt.text(wi * pitch / lt.cw, 0, MONTHS_JA[d0.month - 1], "subtext0"))
        last_month = d0.month
    dt = Term(c, P, ox, y_cells, size=11.5, lh=pitch / 11.5)
    for r, lab in ((1, "月"), (3, "水"), (5, "金")):
        c.add(dt.text(0, r, lab, "overlay1"))

    # kaomoji cat running underneath; every column hops when it passes
    rt = Term(c, P, 0, y_run, size=14, lh=1.4)
    run_w = cells(art.RUNNER["a"]) * rt.cw
    face_off = (cells("ε=ε=┏(=^･") + 0.5) * rt.cw
    grid_x1 = grid_x0 + nweeks * pitch
    run_secs = 12.0
    v = (grid_x1 - grid_x0) / run_secs
    s0 = MARGIN - run_w - 10
    s1 = W - MARGIN + 10
    total = (s1 - s0) / v
    c.style(
        "@keyframes hop{0%{transform:translateY(0)}1.5%{transform:translateY(-4px)}"
        "3.2%,100%{transform:translateY(0)}}"
    )
    for wi, week in enumerate(weeks):
        x = grid_x0 + wi * pitch
        parts = []
        for iso, level, count in week:
            wd = (date.fromisoformat(iso).weekday() + 1) % 7  # Sunday = 0
            parts.append(heat_cell(P, x, round(y_cells + wd * pitch), cell, level))
        t_hit = (x + cell / 2 - face_off - s0) / v
        c.add(f'<g style="animation:hop {total:.2f}s ease-out {t_hit:.2f}s infinite">{"".join(parts)}</g>')
    c.style(
        f"@keyframes run{{0%{{transform:translateX({s0:.0f}px)}}100%{{transform:translateX({s1:.0f}px)}}}}"
        f".run{{animation:run {total:.2f}s linear infinite;transform:translateX({s0:.0f}px)}}"
    )
    cls = frames_css(c, "leg", [(0, .2), (1, .2)], 2)
    c.style(f".{cls[1]}{{opacity:0}}")
    legs = "".join(f'<g class="{cls[i]}">{rt.text(0, 0, art.RUNNER[k], "pink", bold=True)}</g>'
                   for i, k in enumerate("ab"))
    clip = c.uid("win")
    c.define(clip, f'<clipPath id="{clip}"><rect x="{MARGIN + 1}" y="{MARGIN}" width="{W - 2 * MARGIN - 2}" '
                   f'height="{H - 2 * MARGIN}"/></clipPath>')
    c.add(f'<g clip-path="url(#{clip})"><g class="run">{legs}</g></g>')

    # summary + legend
    bt = Term(c, P, ox, y_sum, size=14, lh=1.5)
    streak = stats["streak"]
    s = (f"[green b]{stats['contributions']:,}[/] contributions in the last year [overlay1]·[/] "
         f"streak [peach b]{streak}[/] day{'s' if streak != 1 else ''}")
    c.add(bt.markup(0, 0, s)[0])
    right = W - MARGIN - PAD
    lx = right - (2 * 2 + 5 * 16 + 2 * 8) * 1.0 - 8
    cy = bt.row_y(0) + (bt.lh - cell) / 2
    out = [Term(c, P, lx, y_sum, size=14, lh=1.5).text(0, 0, "少", "overlay1")]
    x = lx + 2 * bt.cw + 6
    for lv in range(5):
        out.append(heat_cell(P, round(x), round(cy), cell, lv))
        x += 16
    out.append(Term(c, P, x + 2, y_sum, size=14, lh=1.5).text(0, 0, "多", "overlay1"))
    c.add("".join(out))
    return c.svg("Contribution heatmap drawn with characters")


# ----------------------------------------------------------------- skills

def skills(cfg: dict, P: dict) -> str:
    files = cfg["skills"]["files"]
    H = MARGIN * 2 + TITLE_H + 16 + 14 * 1.5 * 2 + 14
    c = Canvas(W, H)
    ox, oy = window(c, P, H, "~/skills")
    t = Term(c, P, ox, oy, size=14, lh=1.5)
    c.add(t.markup(0, 0, prompt(cfg) + "ls ~/skills")[0])
    col = 0
    for name, color in files:
        c.add(t.text(col, 1, name, color, bold=True))
        col += cells(name) + 3
    return c.svg("Skills: " + ", ".join(n for n, _ in files))


# ----------------------------------------------------------------- footer

def footer(cfg: dict, P: dict) -> str:
    H = MARGIN * 2 + TITLE_H + 16 + 14 * 1.45 * 10 + 14
    c = Canvas(W, H)
    ox, oy = window(c, P, H, cfg["footer"]["title"])
    t = Term(c, P, ox, oy, size=14, lh=1.45)
    c.add(t.markup(0, 0, prompt(cfg) + "exit")[0])
    cx, cy = 3, 4
    for r, line in enumerate(art.SLEEP):
        c.add(t.text(cx, cy + r, line, "lavender", bold=True))
    cls = frames_css(c, "zz", [(i, 0.75) for i in range(len(art.SLEEP_Z))], len(art.SLEEP_Z))
    for k, frame in enumerate(art.SLEEP_Z):
        c.style(f".{cls[k]}{{opacity:{1 if k == 2 else 0}}}")
        z = "".join(t.text(cx + col, cy + r - 1, ch, ["teal", "sky", "blue"][i % 3], bold=True)
                    for i, (r, col, ch) in enumerate(frame))
        c.add(f'<g class="{cls[k]}">{z}</g>')
    tx = cx + len(art.SLEEP[0]) + 6
    for r, m in enumerate(cfg["footer"]["lines"]):
        c.add(t.markup(tx, cy - 1 + r * 1.2, m.format(date=date.today().isoformat()))[0])
    c.add(t.markup(0, 9, "[overlay1][[Process completed][/]")[0])
    return c.svg(cfg["footer"]["alt"])


# ----------------------------------------------------------------- badges

def badge(label: str, value: str, color: str, P: dict) -> str:
    size = 13
    lw = cells(label) * size * 0.6 + 22
    vw = cells(value) * size * 0.6 + 22
    h = 28
    c = Canvas(round(lw + vw), h)
    c.add(
        f'<rect width="{lw + vw:.0f}" height="{h}" rx="7" fill="{P["surface0"]}"/>',
        f'<path d="M7,0 H{lw:.0f} V{h} H7 a7,7 0 0 1 -7,-7 V7 a7,7 0 0 1 7,-7 Z" fill="{P[color]}"/>',
    )
    t = Term(c, P, 11, (h - size * 1.4) / 2, size=size, lh=1.4)
    c.add(t.text(0, 0, label, "crust" if P["name"] == "dark" else "base", bold=True))
    t2 = Term(c, P, lw + 11, (h - size * 1.4) / 2, size=size, lh=1.4)
    c.add(t2.text(0, 0, value, "text", bold=True))
    return c.svg(f"{label}: {value}")
