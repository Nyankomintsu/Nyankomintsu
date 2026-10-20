"""ASCII art: the cats, their animation frames, and the big title banner."""
from __future__ import annotations

import pyfiglet

# Mirror a left half to build a symmetric picture.
_MIRROR = str.maketrans("/\\()<>[]{}`'", "\\/)(><][}{'`")


def mirror(rows: list[tuple[str, str]]) -> list[str]:
    return [left + mid + left[::-1].translate(_MIRROR) for left, mid in rows]


# ---------------------------------------------------------------- neofetch cat
# Outline only; eyes, nose, mouth, blush and whiskers are separate layers so
# the face can change expression without redrawing the head.
FACE = mirror([
    ("      ,-.       ", " "),
    ("     /   \\      ", " "),
    ("    /     `-----", "-"),
    ("   |            ", " "),
    ("   |            ", " "),
    ("   |            ", " "),
    ("   |            ", " "),
    ("    \\           ", " "),
    ("     `-._       ", " "),
    ("         `------", "-"),
])
FACE[0] = FACE[0][:17] + FACE[0][17:].replace(".-,", ",-.")
FACE_W = len(FACE[0])  # 33
_C = FACE_W // 2  # centre column (16)
_EYE_L, _EYE_R = 9, FACE_W - 1 - 9

FACE_WHISKERS = [(5, 1, "=="), (6, 1, "=="), (5, FACE_W - 3, "=="), (6, FACE_W - 3, "==")]


def face_features(expr: str) -> list[tuple[int, int, str, str]]:
    """(row, col, text, colour) for one expression."""
    eye = {"normal": "o", "blink": "-", "happy": "^", "meow": "o", "wink": "o"}[expr]
    feats = [(4, _EYE_L, eye, "text"), (4, _EYE_R, "-" if expr == "wink" else eye, "text")]
    feats.append((5, _C, "v", "pink"))
    feats.append((6, _C, "o" if expr == "meow" else "ω", "pink"))
    if expr in ("happy", "wink"):
        feats += [(5, _EYE_L - 1, "///", "red"), (5, _EYE_R - 1, "///", "red")]
    return feats


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
