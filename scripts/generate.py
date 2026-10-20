"""Draw every picture used by README.md.

    python scripts/generate.py            # everything (needs GITHUB_TOKEN)
    python scripts/generate.py --static   # only the pictures that don't need GitHub data
    python scripts/generate.py --sample --out /tmp/preview   # fake numbers, for trying layouts
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cards  # noqa: E402
import github_stats  # noqa: E402
from themes import THEMES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def write(path: Path, svg: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    print(f"  {path.relative_to(path.parent.parent)}  ({len(svg) // 1024} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true", help="skip the cards that need GitHub data")
    ap.add_argument("--sample", action="store_true", help="use made-up numbers (local preview only)")
    ap.add_argument("--out", default=str(ROOT), help="where to write assets/ and profile/")
    a = ap.parse_args()

    with open(ROOT / "config.toml", "rb") as f:
        cfg = tomllib.load(f)
    out = Path(a.out)

    stats = None
    if not a.static:
        if a.sample:
            stats = github_stats.sample()
        else:
            print("fetching GitHub stats ...")
            stats = github_stats.fetch(cfg["profile"]["github"], cfg["neofetch"].get("exclude_repos", []))

    for theme, P in THEMES.items():
        print(f"[{theme}]")
        write(out / "assets" / f"header-{theme}.svg", cards.header(cfg, P))
        write(out / "assets" / f"skills-{theme}.svg", cards.skills(cfg, P))
        write(out / "assets" / f"footer-{theme}.svg", cards.footer(cfg, P))
        for b in cfg["badges"]:
            write(out / "assets" / f"badge-{b['name']}-{theme}.svg", cards.badge(b["label"], b["value"], b["color"], P))
        if stats:
            write(out / "profile" / f"neofetch-{theme}.svg", cards.neofetch(cfg, P, stats))
            write(out / "profile" / f"activity-{theme}.svg", cards.activity(cfg, P, stats))


if __name__ == "__main__":
    main()
