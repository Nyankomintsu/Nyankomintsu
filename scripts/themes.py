"""Catppuccin colours (https://catppuccin.com, MIT): Latte for light mode, Mocha for dark mode."""

LATTE = dict(
    name="light",
    rosewater="#dc8a78", flamingo="#dd7878", pink="#ea76cb", mauve="#8839ef", red="#d20f39",
    maroon="#e64553", peach="#fe640b", yellow="#df8e1d", green="#40a02b", teal="#179299",
    sky="#04a5e5", sapphire="#209fb5", blue="#1e66f5", lavender="#7287fd",
    text="#4c4f69", subtext1="#5c5f77", subtext0="#6c6f85", overlay2="#7c7f93", overlay1="#8c8fa1",
    overlay0="#9ca0b0", surface2="#acb0be", surface1="#bcc0cc", surface0="#ccd0da",
    base="#eff1f5", mantle="#e6e9ef", crust="#dce0e8",
    # contribution heat levels 0..4 (mint)
    heat=["#d5d9e2", "#a8e3cf", "#5fcaa8", "#1fa883", "#0e7c5f"],
    shadow="#4c4f69",
)

MOCHA = dict(
    name="dark",
    rosewater="#f5e0dc", flamingo="#f2cdcd", pink="#f5c2e7", mauve="#cba6f7", red="#f38ba8",
    maroon="#eba0ac", peach="#fab387", yellow="#f9e2af", green="#a6e3a1", teal="#94e2d5",
    sky="#89dceb", sapphire="#74c7ec", blue="#89b4fa", lavender="#b4befe",
    text="#cdd6f4", subtext1="#bac2de", subtext0="#a6adc8", overlay2="#9399b2", overlay1="#7f849c",
    overlay0="#6c7086", surface2="#585b70", surface1="#45475a", surface0="#313244",
    base="#1e1e2e", mantle="#181825", crust="#11111b",
    heat=["#2a2b3d", "#2d5e57", "#3f9a83", "#6fd1b4", "#a8f0dc"],
    shadow="#000000",
)

THEMES = {"light": LATTE, "dark": MOCHA}


def mix(a: str, b: str, t: float) -> str:
    """Blend two #rrggbb colours."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def gradient(stops: list[str], t: float) -> str:
    """Colour at position t (0..1) along several stops."""
    if t <= 0:
        return stops[0]
    if t >= 1:
        return stops[-1]
    seg = t * (len(stops) - 1)
    i = int(seg)
    return mix(stops[i], stops[i + 1], seg - i)
