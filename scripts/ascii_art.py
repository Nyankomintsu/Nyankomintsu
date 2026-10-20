"""ASCII art: the cats, their animation frames, and the big title banner."""
from __future__ import annotations

import pyfiglet

# Mirror a left half to build a symmetric picture.
_MIRROR = str.maketrans("/\\()<>[]{}`'", "\\/)(><][}{'`")


def mirror(rows: list[tuple[str, str]]) -> list[str]:
    return [left + mid + left[::-1].translate(_MIRROR) for left, mid in rows]


# ---------------------------------------------------------------- neofetch cat
# The classic Japanese AA cat:
#
#      ／l、
#    （ﾟ､ 。７
#      l、 ~ヽ
#      じしf_, )ノ
#
# It was drawn for proportional fonts, so every character gets its own position
# (row, x in em). "l" comes from the CJK font, which draws it as a straight line.
AA_CAT = [
    (0, 1.00, "／", "ear"), (0, 2.02, "l", "ear"), (0, 2.30, "、", "ear_tip"),
    (1, 0.00, "(", "face"), (1, 0.55, "ﾟ", "eye_l"), (1, 1.05, "､", "nose"), (1, 1.75, "。", "eye_r"),
    (1, 2.62, "7", "face"),
    (2, 1.25, "l", "leg"), (2, 1.52, "、", "leg"), (2, 2.75, "~", "back"), (2, 3.35, "ヽ", "back"),
    (3, 1.10, "じ", "paw_l"), (3, 2.05, "し", "paw_r"), (3, 3.20, "f", "hind"), (3, 3.70, "_", "hind"),
    (3, 4.20, ",", "hind"), (3, 4.95, ")", "rump"), (3, 5.45, "ノ", "tail"),
]
AA_PREFER = {"l": ("sc_b",)}
# what the eyes turn into for each expression
AA_EYES = {"normal": ("ﾟ", "。"), "blink": ("-", "-"), "happy": ("^", "^")}


# ------------------------------------------------------------ small sitting cat
SIT = [r" /\_/\ ", r"(     )", r" > ^ < "]
SIT_EYES = {"normal": "o.o", "blink": "-.-", "happy": "^.^", "look": "o.O"}
SIT_EYE_POS = (1, 2)  # row, col

# ------------------------------------------------------------ kaomoji runner
RUNNER = {
    "a": "ε=ε=┏(=^･ω･^=)┛",
    "b": "ε=ε=┗(=^･ω･^=)┓",
}

# ------------------------------------------------------------ sleeping cat
SLEEP = [
    r"   /\_/\         ",
    r"  ( -.- )_______ ",
    r"   \  ω        )~",
    r"   (,,)_(,,)___/ ",
]
# z letters drifting up: (row, col, char) per frame, rows are above the cat
SLEEP_Z = [
    [(0, 10, "z")],
    [(0, 10, "z"), (-1, 12, "Z")],
    [(0, 10, "z"), (-1, 12, "Z"), (-2, 14, "z")],
    [(-1, 12, "Z"), (-2, 14, "z")],
]


def banner(text: str) -> list[str]:
    rows = pyfiglet.figlet_format(text, font="ansi_shadow", width=400).rstrip("\n").split("\n")
    rows = [r.rstrip() for r in rows]
    while rows and not rows[-1].strip():
        rows.pop()
    return rows
