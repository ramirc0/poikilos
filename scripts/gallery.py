"""Render every theme across common plot types into assets/gallery/<theme>.{svg,png}.

Also prints the contrast of spines, ticks and cycle colors against the
background. Only text contrast is tested; the rest is reported here.
"""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator, NullLocator

import poikilos as pk
from poikilos.themes import _contrast

OUT = Path(__file__).resolve().parent.parent / "assets" / "gallery"


def report_contrast(theme):
    palette = pk.PALETTES[pk.THEMES[theme][1]]
    ratios = {
        "frame": _contrast(palette.frame, palette.background),
        "ticks": _contrast(palette.ticks, palette.background),
        **{c: _contrast(c, palette.background) for c in palette.cycle},
    }
    low = [name for name, ratio in ratios.items() if ratio < 3]
    print(
        f"{theme}: frame {ratios['frame']:.1f}, ticks {ratios['ticks']:.1f}, "
        f"cycle {min(ratios[c] for c in palette.cycle):.1f} to "
        f"{max(ratios[c] for c in palette.cycle):.1f}; under 3:1: {low or 'none'}"
    )


def draw(axes, look, rng):
    """Draw one panel per plot type. Return the scatter, its labels and the categorical axes."""
    marker = "o" if look == "lilaq" else None
    x = np.linspace(0, 10, 21)

    ax = axes["line"]
    for k in range(3):
        ax.plot(x, 3 * np.exp(-x / (k + 2)), marker=marker, label=f"series {k}")
    ax.set(title="Lines", xlabel="time (s)", ylabel="signal")
    ax.legend()

    ax = axes["scatter"]
    xs, ys = rng.uniform(0, 1, (2, 8))
    points = ax.scatter(xs, ys)
    ax.set(title="Labelled scatter", xlabel="x", ylabel="y")
    names = ["HepG2", "K562", "A549", "H1", "HeLa", "MCF-7", "GM12878", "IMR-90"]

    ax = axes["bar"]
    ax.bar(["a", "b", "c", "d"], [3.2, 1.4, 4.8, 2.6], color=["C0", "C1", "C2", "C3"])
    ax.set(title="Bars", ylabel="count")

    ax = axes["hist"]
    for shift in (0, 1.5):
        ax.hist(rng.normal(shift, 1, 500), bins=np.arange(-3, 5.5, 0.5), alpha=0.7)
    ax.set(title="Histograms", xlabel="value", ylabel="count")

    ax = axes["heatmap"]
    image = ax.imshow(rng.uniform(0, 1, (4, 6)), cmap="viridis")
    ax.set(title="Heatmap", xticks=range(6), yticks=range(4))
    ax.set_xticklabels(list("ABCDEF"))
    ax.set_yticklabels(["w", "x", "y", "z"])
    ax.grid(False)
    ax.figure.colorbar(image, ax=ax)

    ax = axes["box"]
    ax.boxplot(
        [rng.normal(m, 1, 40) for m in (0, 1, 0.5)],
        tick_labels=["ctrl", "drug", "both"],
        showmeans=True,
    )
    ax.set(title="Boxplot", ylabel="score")

    ax = axes["errorbar"]
    ax.errorbar(x[::2], x[::2] * 0.8 + 1, yerr=0.8, marker=marker, label="fit")
    ax.set(title="Error bars", xlabel="dose", ylabel="response")

    ax = axes["band"]
    mean = np.sin(x / 2)
    (line,) = ax.plot(x, mean)
    ax.fill_between(x, mean - 0.3, mean + 0.3, color=line.get_color(), alpha=0.3)
    ax.set(title="Band", xlabel="time (s)", ylabel="signal")

    ax = axes["dense"]
    ax.plot(np.cumsum(rng.normal(0, 1, 2000)))
    ax.set(title="Dense line", xlabel="step", ylabel="walk")

    categorical = {"bar": (True, False), "heatmap": (True, True), "box": (True, False)}
    return points, names, categorical


def render(theme):
    look = pk.THEMES[theme][0]
    rng = np.random.default_rng(0)
    with pk.context(theme):
        fig, axes = plt.subplot_mosaic(
            [
                ["line", "scatter", "bar"],
                ["hist", "heatmap", "box"],
                ["errorbar", "band", "dense"],
            ],
            figsize=(10, 7.5),
        )
        fig.suptitle(theme)
        points, names, categorical = draw(axes, look, rng)
        for name, ax in axes.items():
            cat_x, cat_y = categorical.get(name, (False, False))
            if look == "plain":
                pk.despine(ax, categorical_x=cat_x, categorical_y=cat_y)
            else:
                for axis, cat in ((ax.xaxis, cat_x), (ax.yaxis, cat_y)):
                    if cat:
                        axis.set_minor_locator(NullLocator())
                    else:
                        axis.set_major_locator(MaxNLocator(7, steps=[1, 2, 5, 10]))
        pk.label_points(axes["scatter"], points, names, fontsize=8)
        for path in pk.save_figure(fig, OUT / theme, dpi=150):
            print(f"wrote {path}")
        plt.close(fig)


def main():
    for theme in pk.THEMES:
        render(theme)
        report_contrast(theme)


if __name__ == "__main__":
    main()
