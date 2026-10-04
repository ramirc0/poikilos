"""Figure helpers: spine trimming, point labels and SVG + PNG export."""

from pathlib import Path

import matplotlib as mpl
import numpy as np


def despine(ax, categorical_x=False, categorical_y=False):
    """Offset the left and bottom spines by 10 pt and trim them to the end ticks.

    Each continuous axis is fitted to its data without margins, then widened
    to the nearest ticks enclosing the data, so the trimmed spine never ends
    short of the data. When the locator has no enclosing tick (e.g. dates),
    the data edge becomes the end tick. A categorical axis has no spine or
    tick marks, major or minor; its labels carry the categories. Top and
    right tick marks are hidden with their spines.

    When both axes are fitted to the data, the plotted artists are unclipped
    so markers and lines at the limits draw whole into the spine offset.
    Lines without data stay clipped. Explicit limits set by the caller keep
    clipping on. Call after everything is drawn on ``ax``.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to style.
    categorical_x : bool, default False
        Hide the bottom spine and x tick marks (bar charts, heatmaps).
    categorical_y : bool, default False
        Hide the left spine and y tick marks (horizontal bars, heatmaps).
    """
    fitted = ax.get_autoscalex_on() and ax.get_autoscaley_on()
    ax.margins(0)
    ax.autoscale_view()
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[:].set_position(("outward", 10))
    ax.tick_params(which="both", top=False, right=False)
    for axis, set_lim, spine, categorical in [
        (ax.yaxis, ax.set_ylim, ax.spines["left"], categorical_y),
        (ax.xaxis, ax.set_xlim, ax.spines["bottom"], categorical_x),
    ]:
        spine.set_visible(not categorical)
        if categorical:
            axis.set_tick_params(which="both", length=0)
            continue
        lo, hi = sorted(axis.get_view_interval())
        # Calling the locator reads the view limits itself; date locators reject raw floats.
        ticks = axis.get_major_locator()()
        lo = max((t for t in ticks if t <= lo), default=lo)
        hi = min((t for t in ticks if t >= hi), default=hi)
        axis.set_ticks(sorted({lo, hi, *(t for t in ticks if lo <= t <= hi)}))
        # Python 3.11 reads reverse= through __index__, which numpy >= 2.3 rejects on np.bool_.
        set_lim(sorted((lo, hi), reverse=bool(axis.get_inverted())))
        spine.set_bounds(lo, hi)
    if fitted:
        # An empty line's marker-padded extent sits at the figure origin. Unclipped,
        # it drags constrained layout there (e.g. boxplot fliers with no outliers).
        lines = [line for line in ax.lines if len(line.get_xydata())]
        for artist in [*lines, *ax.collections, *ax.patches]:
            artist.set_clip_on(False)


def label_points(ax, points, labels, **kwargs):
    """Label scatter markers so no label overlaps another label or a marker.

    Each label starts at its marker; adjustText then moves labels apart and
    off the markers' full extent and draws a leader line, in the axes edge
    color, back to each marker. Call last on the figure, after
    :func:`despine` and every title, label and legend: anything added later
    reshapes the constrained layout and moves the labels back together.
    Requires the ``labels`` extra (``adjustText``).

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes holding ``points``.
    points : matplotlib.collections.PathCollection
        Collection returned by ``ax.scatter``.
    labels : sequence of str
        One label per point, in the order of ``points``.
    **kwargs
        Passed to ``ax.text`` (e.g. ``fontsize=8``).

    Returns
    -------
    list of matplotlib.text.Text
        The label artists.
    """
    from adjustText import adjust_text

    # adjustText measures steps in pixels with screen-sized defaults; convert from points
    # so a 300 dpi figure does not pull labels back onto their markers.
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
        force_static=(0.2, 0.4),
        pull_threshold=clear,
        max_move=10 * px,
        min_arrow_len=clear,
        # adjustText's default is a 1 s time limit, which made placement depend on CPU speed.
        iter_lim=1000,
        arrowprops={
            "arrowstyle": "-",
            "color": mpl.rcParams["axes.edgecolor"],
            "lw": 0.5,
        },
    )
    return texts


def save_figure(fig, path, **kwargs):
    """Write ``fig`` as both SVG and PNG.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to save.
    path : str or pathlib.Path
        Output path, with or without a ``.svg`` or ``.png`` suffix. Any other
        suffix is part of the stem, so ``x.curve`` gives ``x.curve.svg`` and
        ``x.curve.png``. Missing parent directories are created.
    **kwargs
        Passed to ``fig.savefig``.

    Returns
    -------
    list of pathlib.Path
        The SVG path, then the PNG path.
    """
    path = Path(path)
    stem = path.with_suffix("") if path.suffix.lower() in (".svg", ".png") else path
    stem.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt in ("svg", "png"):
        out = Path(f"{stem}.{fmt}")
        fig.savefig(out, format=fmt, **kwargs)
        written.append(out)
    return written
