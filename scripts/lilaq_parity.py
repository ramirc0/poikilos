"""Render the same data with lilaq 0.6.0 (Typst) and the lilaq looks, side by side.

Writes build/parity/<theme>-<case>.png: lilaq on the left, poikilos on the
right, both at 300 ppi. The first run downloads the Typst package.
"""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import typst
from matplotlib.ticker import MaxNLocator

import poikilos as pk

OUT = Path(__file__).resolve().parent.parent / "build" / "parity"
PPI = 300

# Page fill, text fill and extra rules: lilaq's default, and its moon theme on #242424.
TYPST = {
    "lilaq": ("white", "black", ""),
    "lilaq-moon": ('rgb("#242424")', "white", "#show: lq.theme.moon"),
}

rng = np.random.default_rng(1)
x = np.linspace(0, 10, 11)
CASES = {
    "lines": {
        "title": "Two curves",
        "xlabel": "time (s)",
        "ylabel": "signal",
        "plots": [
            ("plot", x, np.round(np.sin(x / 2) * 2 + 3, 4), "sine"),
            ("plot", x, np.round(np.cos(x / 3) + 2, 4), "cosine"),
        ],
    },
    "scatter": {
        "title": "Scatter and errors",
        "xlabel": "dose",
        "ylabel": "response",
        "plots": [
            ("scatter", *np.round(rng.uniform(0, 100, (2, 25)), 4), "samples"),
            ("errorbar", x * 10, np.round(x * 7 + 10, 4), "fit"),
        ],
    },
}


def typst_array(values):
    return "(" + ", ".join(f"{v:g}" for v in values) + ",)"


def typst_source(theme, case):
    plots = []
    for kind, xs, ys, label in case["plots"]:
        args = f"{typst_array(xs)}, {typst_array(ys)}, label: [{label}]"
        if kind == "scatter":
            plots.append(f"lq.scatter({args})")
        elif kind == "errorbar":
            plots.append(f"lq.plot({args}, yerr: 8)")
        else:
            plots.append(f"lq.plot({args})")
    page, text, rules = TYPST[theme]
    return f"""#import "@preview/lilaq:0.6.0" as lq
#set page(width: auto, height: auto, margin: 6pt, fill: {page})
#set text(fill: {text}, font: "New Computer Modern", size: 11pt)
{rules}
#lq.diagram(
  title: [{case["title"]}],
  xlabel: [{case["xlabel"]}],
  ylabel: [{case["ylabel"]}],
  {", ".join(plots)},
)
"""


def render_matplotlib(theme, case, path):
    with pk.context(theme):
        fig, ax = plt.subplots()
        for kind, xs, ys, label in case["plots"]:
            if kind == "scatter":
                ax.scatter(xs, ys, label=label)
            elif kind == "errorbar":
                ax.errorbar(xs, ys, yerr=8, marker="o", label=label)
            else:
                ax.plot(xs, ys, marker="o", label=label)
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10]))
        ax.set(title=case["title"], xlabel=case["xlabel"], ylabel=case["ylabel"])
        ax.legend()
        fig.savefig(path, dpi=PPI)
        fig.canvas.draw()
        size = ax.get_window_extent().size / fig.dpi * 2.54
        plt.close(fig)
    return size


def side_by_side(left, right, path):
    images = [plt.imread(p)[..., :3] for p in (left, right)]
    height = max(img.shape[0] for img in images)
    background = images[0][0, 0]
    padded = [
        np.vstack(
            [img, np.broadcast_to(background, (height - len(img), img.shape[1], 3))]
        )
        for img in images
    ]
    gap = np.broadcast_to(background, (height, 40, 3))
    plt.imsave(path, np.hstack([padded[0], gap, padded[1]]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in TYPST:
        for name, case in CASES.items():
            stem = OUT / f"{theme}-{name}"
            lilaq = stem.with_name(f"{stem.name}.lilaq.png")
            lilaq.write_bytes(
                typst.compile(typst_source(theme, case).encode(), format="png", ppi=PPI)
            )
            mine = stem.with_name(f"{stem.name}.poikilos.png")
            width, height = render_matplotlib(theme, case, mine)
            side_by_side(lilaq, mine, stem.with_suffix(".png"))
            print(
                f"wrote {stem}.png (poikilos data area {width:.2f} x {height:.2f} cm)"
            )


if __name__ == "__main__":
    main()
