"""Rosé Pine matplotlib styles."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.style  # noqa: F401  (registers mpl.style)
import numpy as np

VARIANTS = ("rose-pine", "rose-pine-moon", "rose-pine-dawn")
FORMATS = ("svg", "png")

_STYLES = Path(__file__).resolve().parent / "styles"


def style_path(variant):
    """Return the path to a variant's ``.mplstyle`` file.

    Parameters
    ----------
    variant : str
        One of the names in :data:`VARIANTS`.

    Raises
    ------
    ValueError
        If ``variant`` is unknown.
    """
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; choose from {VARIANTS}")
    return _STYLES / f"{variant}.mplstyle"


def register():
    """Add every variant to matplotlib's style library.

    After calling this, styles are usable by name, e.g.
    ``plt.style.use("rose-pine-moon")``.
    """
    for variant in VARIANTS:
        mpl.style.library[variant] = mpl.rc_params_from_file(
            style_path(variant), use_default_template=False
        )


def apply_style(variant="rose-pine"):
    """Set the Agg backend and apply a Rosé Pine style.

    MUST run before ``matplotlib.pyplot`` is imported; the backend cannot
    change afterwards.

    Parameters
    ----------
    variant : str
        One of ``rose-pine`` (main dark), ``rose-pine-moon`` (dim dark),
        or ``rose-pine-dawn`` (light). Defaults to ``rose-pine``.

    Raises
    ------
    ValueError
        If ``variant`` is unknown.
    """
    mpl.use("Agg")
    mpl.style.use("default")
    mpl.style.use(style_path(variant))


def despine(ax, categorical_x=False, categorical_y=False):
    """Offset the left and bottom spines by 10 pt and trim them to the end ticks.

    Each continuous axis is fitted to its data without margins, then widened
    to the nearest ticks enclosing the data, so the trimmed spine never ends
    short of the data. When the locator has no enclosing tick (e.g. dates),
    the data edge becomes the end tick. A categorical axis has no spine or
    tick marks; its labels carry the categories.

    When both axes are fitted to the data, the plotted artists are unclipped
    so markers and lines at the limits draw whole into the spine offset.
    Explicit limits set by the caller keep clipping on. Call after everything
    is drawn on ``ax``.

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
    hidden = {"top", "right"}
    if categorical_x:
        hidden.add("bottom")
    if categorical_y:
        hidden.add("left")
    for side, spine in ax.spines.items():
        spine.set_visible(side not in hidden)
        spine.set_position(("outward", 10))
    axes = []
    if not categorical_y:
        axes.append((ax.yaxis, ax.get_ylim, ax.set_ylim, "left"))
    if not categorical_x:
        axes.append((ax.xaxis, ax.get_xlim, ax.set_xlim, "bottom"))
    for axis, get_lim, set_lim, spine in axes:
        lo, hi = sorted(get_lim())
        # Calling the locator reads the view limits itself; date locators reject raw floats.
        ticks = axis.get_major_locator()()
        lo = max((t for t in ticks if t <= lo), default=lo)
        hi = min((t for t in ticks if t >= hi), default=hi)
        axis.set_ticks(sorted({lo, hi, *(t for t in ticks if lo <= t <= hi)}))
        set_lim(lo, hi)
        ax.spines[spine].set_bounds(lo, hi)
    if fitted:
        for artist in [*ax.lines, *ax.collections, *ax.patches]:
            artist.set_clip_on(False)
    if categorical_x:
        ax.tick_params(axis="x", length=0)
    if categorical_y:
        ax.tick_params(axis="y", length=0)


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
    texts = [ax.text(x, y, label, **kwargs) for (x, y), label in zip(points.get_offsets(), labels)]
    adjust_text(
        texts,
        objects=points,
        ax=ax,
        expand=(1.3, 1.6),
        force_text=(0.5, 1.0),
        pull_threshold=clear,
        max_move=10 * px,
        min_arrow_len=clear,
        arrowprops={"arrowstyle": "-", "color": mpl.rcParams["axes.edgecolor"], "lw": 0.5},
    )
    return texts


def save_figure(fig, path, **kwargs):
    """Write ``fig`` as both SVG and PNG.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to save.
    path : str or pathlib.Path
        Output path without suffix; one is added per format. Missing parent
        directories are created.
    **kwargs
        Passed to ``fig.savefig``.

    Returns
    -------
    list of pathlib.Path
        The paths written, in :data:`FORMATS` order.
    """
    stem = Path(path).with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt in FORMATS:
        out = stem.with_suffix(f".{fmt}")
        fig.savefig(out, format=fmt, **kwargs)
        written.append(out)
    return written
