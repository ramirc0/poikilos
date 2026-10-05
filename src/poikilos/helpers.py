"""Figure helpers: spine trimming, point labels, zero lines and SVG + PNG export."""

from pathlib import Path

import matplotlib as mpl
import numpy as np
from matplotlib import cbook
from matplotlib.lines import Line2D


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
    clipping on. So does a log axis with values at or below 0, such as a
    bar's base. Call after everything is drawn on ``ax``.

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
    # A log axis leaves values <= 0 out of its limits, such as a bar's base at 0.
    if fitted and all(ax.viewLim.contains(*xy) for xy in ax.dataLim.get_points()):
        # An empty line's marker-padded extent sits at the figure origin. Unclipped,
        # it drags constrained layout there (e.g. boxplot fliers with no outliers).
        lines = [line for line in ax.lines if len(line.get_xydata())]
        for artist in [*lines, *ax.collections, *ax.patches]:
            artist.set_clip_on(False)


def label_points(ax, points, labels, **kwargs):
    """Label scatter markers, moving the labels off each other and the markers.

    Each label starts at its marker; adjustText then moves labels apart and
    off the markers' full extent and draws a leader line, in the axes edge
    color, back to each marker. Labels stay inside the axes, so a label near
    the axes edge can still touch a marker. Call last on the figure, after
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


def zero_line(ax, axis="y", **kwargs):
    """Draw a bold line at zero to show where a scale changes sign.

    The line spans the axes, in the axes edge color at twice the grid line
    width. The axis limits widen to include zero.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to draw on.
    axis : {"y", "x", "both"}, default "y"
        As in ``ax.grid``: ``"y"`` draws the line y = 0, ``"x"`` the line
        x = 0.
    **kwargs
        Passed to ``ax.axhline`` and ``ax.axvline`` (e.g. ``lw=1``).

    Returns
    -------
    list of matplotlib.lines.Line2D
        The y = 0 line, then the x = 0 line, for those drawn.

    Raises
    ------
    ValueError
        If ``axis`` is not ``"x"``, ``"y"`` or ``"both"``.
    """
    if axis not in ("x", "y", "both"):
        raise ValueError(f"axis must be 'x', 'y' or 'both', not {axis!r}")
    # Normalized so aliases such as lw= and c= override the defaults below.
    kwargs = cbook.normalize_kwargs(kwargs, Line2D)
    kwargs.setdefault("color", mpl.rcParams["axes.edgecolor"])
    kwargs.setdefault("linewidth", 2 * mpl.rcParams["grid.linewidth"])
    return [
        draw(0, **kwargs)
        for name, draw in (("y", ax.axhline), ("x", ax.axvline))
        if axis in (name, "both")
    ]
