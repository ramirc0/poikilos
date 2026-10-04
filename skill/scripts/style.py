"""Shared matplotlib style for pipeline plots."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.style  # registers mpl.style

FONT_STACK = [
    "Anthropic Sans Text",
    "Google Sans Flex",
    "Arimo",
    "Arial",
    "DejaVu Sans",
]

FORMATS = ("svg", "png")


def apply_style():
    """Set the project plotting style (call before importing pyplot)."""
    mpl.use("Agg")
    mpl.style.use("default")
    mpl.rcParams["figure.dpi"] = 300
    mpl.rcParams["font.family"] = "sans-serif"
    mpl.rcParams["font.sans-serif"] = FONT_STACK
    mpl.rcParams["svg.fonttype"] = "none"
    mpl.rcParams["figure.constrained_layout.use"] = True
    mpl.rcParams["axes.spines.top"] = False
    mpl.rcParams["axes.spines.right"] = False
    mpl.rcParams["xtick.direction"] = "in"
    mpl.rcParams["ytick.direction"] = "in"


def despine(ax, categorical_x=False, categorical_y=False):
    """Offset left and bottom spines by 10 pt and trim them to the end ticks.

    Each continuous axis is fitted to its data without margins. It is then
    widened to the nearest ticks enclosing the data. The trimmed spine
    therefore never ends short of the data. When the locator has no
    enclosing tick (e.g. dates), the data edge becomes the end tick. A
    categorical x or y axis (bar, horizontal bar, heatmap) has no spine or
    tick marks. Its labels carry the categories.

    Data at the limits sits on the axes edge, where matplotlib would clip half
    of each marker and line width. When both axes are fitted to the data, the
    plotted artists are unclipped. They then draw whole into the spine
    offset. Lines without data stay clipped. Explicit limits set by the
    caller keep clipping on.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to despine, after everything is drawn on it.
    categorical_x : bool, default False
        Treat the x axis as categorical.
    categorical_y : bool, default False
        Treat the y axis as categorical.
    """
    import seaborn as sns

    fitted = ax.get_autoscalex_on() and ax.get_autoscaley_on()
    ax.margins(0)
    ax.autoscale_view()
    sns.despine(ax=ax, bottom=categorical_x, left=categorical_y, offset=10)
    axes = []
    if not categorical_y:
        axes.append((ax.yaxis, ax.get_ylim, ax.set_ylim, "left"))
    if not categorical_x:
        axes.append((ax.xaxis, ax.get_xlim, ax.set_xlim, "bottom"))
    for axis, get_lim, set_lim, spine in axes:
        lo, hi = sorted(get_lim())
        # Calling the locator reads the view limits itself. Date locators reject
        # raw floats.
        ticks = axis.get_major_locator()()
        # lo and hi become the enclosing ticks, or stay at the data edges when
        # the locator has none (e.g. dates).
        lo = max((t for t in ticks if t <= lo), default=lo)
        hi = min((t for t in ticks if t >= hi), default=hi)
        axis.set_ticks(sorted({lo, hi, *(t for t in ticks if lo <= t <= hi)}))
        set_lim(sorted((lo, hi), reverse=axis.get_inverted()))
        ax.spines[spine].set_bounds(lo, hi)
    if fitted:
        # An empty line's marker-padded extent sits at the figure origin. Unclipped,
        # it drags constrained layout there (e.g. boxplot fliers with no outliers).
        lines = [line for line in ax.lines if len(line.get_xydata())]
        for artist in [*lines, *ax.collections, *ax.patches]:
            artist.set_clip_on(False)
    if categorical_x:
        ax.tick_params(axis="x", length=0)
    if categorical_y:
        ax.tick_params(axis="y", length=0)


def label_points(ax, points, labels, **kwargs):
    """Label the markers of scatter `points` so no label overlaps another or a marker.

    Each label starts at its marker. adjustText then moves labels off each
    other and off the markers' full extent, with a gap between labels. It
    draws a grey leader line back to each marker. Call last on the figure,
    after `despine()` and every title, label and legend. Labels are placed in
    the figure's final layout. Anything added later reshapes the axes and
    moves them.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes holding the scatter.
    points : matplotlib.collections.PathCollection
        Collection returned by `ax.scatter`.
    labels : sequence of str
        One label per point, in point order.
    **kwargs
        Passed to `ax.text`.

    Returns
    -------
    list of matplotlib.text.Text
        The label artists.
    """
    import numpy as np
    from adjustText import adjust_text

    # adjustText measures steps in pixels with screen-sized defaults. Convert them from
    # points so a 300 dpi figure does not pull labels back onto their markers.
    px = ax.figure.dpi / 72
    clear = (np.sqrt(points.get_sizes().max()) / 2 + 2) * px
    texts = [
        ax.text(x, y, label, **kwargs)
        for (x, y), label in zip(points.get_offsets(), labels)
    ]
    adjust_text(
        texts,
        objects=points,
        ax=ax,
        expand=(1.3, 1.6),
        force_text=(0.5, 1.0),
        pull_threshold=clear,
        max_move=10 * px,
        min_arrow_len=clear,
        arrowprops={"arrowstyle": "-", "color": "0.5", "lw": 0.5},
    )
    return texts


def save_figure(fig, path, **kwargs):
    """Write `fig` to `path` as both SVG and PNG.

    A `.svg` or `.png` extension on `path` is dropped. Each format's extension
    is then appended. A dotted stem therefore keeps its dots: `x.curve.svg`
    and `x.curve` both give `x.curve.svg` and `x.curve.png`.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to save.
    path : str or pathlib.Path
        Output path, with or without a `.svg` or `.png` extension.
    **kwargs
        Passed to `Figure.savefig`.

    Returns
    -------
    list of pathlib.Path
        The SVG and PNG paths written.
    """
    path = Path(path)
    stem = path.with_suffix("") if path.suffix[1:].lower() in FORMATS else path
    stem.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt in FORMATS:
        out = Path(f"{stem}.{fmt}")
        fig.savefig(out, format=fmt, **kwargs)
        written.append(out)
    return written
