"""Figure helpers: spine trimming, point labels, zero lines and multi-format export."""

from pathlib import Path

import matplotlib as mpl
import numpy as np
from matplotlib import cbook
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.transforms import Bbox


def despine(ax, categorical_x=False, categorical_y=False):
    """Offset the continuous axes' spines by 10 pt and trim them to the end ticks.

    Each continuous axis is fitted to its data without margins, then widened
    to the nearest ticks enclosing the data, so the trimmed spine never ends
    short of the data. When the locator has no enclosing tick (e.g. dates),
    the data edge becomes the end tick. A categorical axis has no spine, no
    offset and no tick marks, major or minor; its labels carry the categories
    and sit by the data. Top and right tick marks are hidden with their
    spines.

    When the limits hold all the data, the plotted artists are unclipped so
    markers and lines at the limits draw whole into the spine offset. Lines
    without data stay clipped. Limits that cut data off keep clipping on, such
    as a zoom or a log axis with values at or below 0 (e.g. a bar's base).

    Call after everything on the figure is drawn, titles and legends included.
    The figure is laid out first, so the ticks fit the axes size after layout.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to style.
    categorical_x : bool, default False
        Hide the bottom spine and x tick marks (bar charts, heatmaps).
    categorical_y : bool, default False
        Hide the left spine and y tick marks (horizontal bars, heatmaps).
    """
    ax.margins(0)
    ax.autoscale_view()
    ax.spines[["top", "right"]].set_visible(False)
    moved = [
        (axis, side)
        for axis, side, categorical in [
            (ax.xaxis, "bottom", categorical_x),
            (ax.yaxis, "left", categorical_y),
        ]
        if not categorical
    ]
    # Moving a spine rebuilds its axis's ticks, dropping label styling such as rotation.
    # A tick's parts depend on the spine only through their transforms.
    kept = [(axis, axis.majorTicks, axis.minorTicks) for axis, _ in moved]
    for _, side in moved:
        ax.spines[side].set_position(("outward", 10))
    for axis, major, minor in kept:
        for old, rebuilt in ((major, axis.majorTicks[0]), (minor, axis.minorTicks[0])):
            for tick in old:
                for part, moved in zip(tick.get_children(), rebuilt.get_children()):
                    part.set_transform(moved.get_transform())
        axis.majorTicks, axis.minorTicks = major, minor
    ax.tick_params(which="both", top=False, right=False)
    # The locator scales its tick count with the axes size, which layout can change a lot.
    ax.get_figure(root=True).draw_without_rendering()
    for axis, set_lim, spine, categorical in [
        (ax.yaxis, ax.set_ylim, ax.spines["left"], categorical_y),
        (ax.xaxis, ax.set_xlim, ax.spines["bottom"], categorical_x),
    ]:
        spine.set_visible(not categorical)
        if categorical:
            axis.set_tick_params(which="both", length=0)
            # Autoscaling, a twin would refit the shared axis with its own margins.
            set_lim(axis.get_view_interval())
            continue
        lo, hi = sorted(axis.get_view_interval())
        # Calling the locator reads the view limits itself; date locators reject raw floats.
        ticks = axis.get_major_locator()()
        lo = max((t for t in ticks if t <= lo), default=lo)
        hi = min((t for t in ticks if t >= hi), default=hi)
        axis.set_ticks(sorted({lo, hi, *(t for t in ticks if lo <= t <= hi)}))
        # Ticks added by layout or set_ticks copy the first tick's label styling,
        # except rotation_mode.
        first, *rest = axis.majorTicks
        for tick in rest:
            tick.label1.set_rotation_mode(first.label1.get_rotation_mode())
            tick.label2.set_rotation_mode(first.label2.get_rotation_mode())
        # Python 3.11 reads reverse= through __index__, which numpy >= 2.3 rejects on np.bool_.
        set_lim(sorted((lo, hi), reverse=bool(axis.get_inverted())))
        spine.set_bounds(lo, hi)
    # Unclipped, data outside the limits would draw. A log axis leaves values <= 0
    # outside, such as a bar's base at 0.
    if all(ax.viewLim.contains(*xy) for xy in ax.dataLim.get_points()):
        # An empty line's marker-padded extent sits at the figure origin. Unclipped,
        # it drags constrained layout there (e.g. boxplot fliers with no outliers).
        lines = [line for line in ax.lines if len(line.get_xydata())]
        for artist in [*lines, *ax.collections, *ax.patches]:
            artist.set_clip_on(False)


class _BoxedText(Text):
    """Text whose window extent includes its box, so adjustText keeps boxes apart."""

    def get_window_extent(self, renderer=None, dpi=None):
        extent = super().get_window_extent(renderer, dpi)
        box = self.get_bbox_patch()
        if box is None:
            return extent
        # Text places its box only when drawn.
        self.update_bbox_position_size(self._renderer)
        return Bbox.union([extent, box.get_window_extent()])


def label_points(ax, points, labels, offsets=None, leader=True, **kwargs):
    """Label scatter markers, moving the labels off each other and the markers.

    Each label sits in a box with the legend frame's face, transparency and
    corners, even on a look that hides the legend frame. Labels start at
    their markers; adjustText then moves the boxes apart and off the markers'
    full extent and draws a leader line back to each marker. The line and the
    box outline share one stroke in the axes edge color. Labels stay inside
    the axes, so a label near the axes edge can still touch a marker. Call
    last on the figure, after :func:`despine` and every title, label and
    legend: anything added later reshapes the constrained layout and moves
    the labels back together. Requires the ``labels`` extra (``adjustText``).

    With ``offsets``, each label sits at its own fixed offset from its marker
    instead, and adjustText is neither run nor needed. The label's side
    facing the marker anchors it: an offset up and to the right aligns the
    label's bottom left corner, and a zero component centers it on that axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes holding ``points``.
    points : matplotlib.collections.PathCollection
        Collection returned by ``ax.scatter``.
    labels : sequence of str
        One label per point, in the order of ``points``.
    offsets : sequence of (float, float), optional
        One ``(dx, dy)`` offset in points per label, in the order of
        ``points``.
    leader : bool, default True
        Draw a line from each label to its marker. With ``offsets``, the line
        stops 1.5 pt short of the marker.
    **kwargs
        Passed to :class:`matplotlib.text.Text` (e.g. ``fontsize=8``). A
        ``bbox`` dict replaces the box; ``bbox=None`` leaves labels bare.
        ``ha`` and ``va`` override the alignment ``offsets`` sets.

    Returns
    -------
    list of matplotlib.text.Text
        The label artists.
    """
    rc = mpl.rcParams
    face = rc["legend.facecolor"]
    edge, width = rc["axes.edgecolor"], 0.5
    # The legend frame's face and corners, even where legend.frameon hides it, with less
    # padding than its borderpad: bigger boxes leave labels at a crowded axes edge no room
    # off the markers. The outline is the leader line's stroke, so the two read as one.
    kwargs = {
        "clip_on": False,
        # The default "normal" spacing sits text on the font's ascent and descent, so
        # the space above and below a label depends on its letters. A numeric spacing
        # splits the line's spare height evenly around the ink.
        "linespacing": 1,
        "bbox": {
            "boxstyle": "round,pad=0.25,rounding_size=0.2"
            if rc["legend.fancybox"]
            else "square,pad=0.25",
            "facecolor": to_rgba(
                rc["axes.facecolor"] if face == "inherit" else face,
                rc["legend.framealpha"],
            ),
            "edgecolor": edge,
            "linewidth": width,
        },
        # Normalized so aliases such as ha= override the alignment set below.
        **cbook.normalize_kwargs(kwargs, Text),
    }
    # FancyArrowPatch stops 2 pt short of the box by default.
    line = {"arrowstyle": "-", "color": edge, "lw": width, "shrinkA": 0}
    radius = np.sqrt(points.get_sizes().max()) / 2
    if offsets is not None:
        return [
            ax.annotate(
                label,
                xy,
                (dx, dy),
                textcoords="offset points",
                arrowprops={**line, "shrinkB": radius + 1.5} if leader else None,
                **{
                    "horizontalalignment": ("right", "center", "left")[
                        int(np.sign(dx)) + 1
                    ],
                    "verticalalignment": ("top", "center", "bottom")[
                        int(np.sign(dy)) + 1
                    ],
                    **kwargs,
                },
            )
            for xy, label, (dx, dy) in zip(points.get_offsets(), labels, offsets)
        ]

    from adjustText import adjust_text

    # adjustText measures steps in pixels with screen-sized defaults; convert from points
    # so a 300 dpi figure does not pull labels back onto their markers.
    px = ax.figure.dpi / 72
    clear = (radius + 2) * px
    texts = [
        ax.add_artist(_BoxedText(x, y, label, transform=ax.transData, **kwargs))
        for (x, y), label in zip(points.get_offsets(), labels)
    ]
    adjust_text(
        texts,
        objects=points,
        ax=ax,
        expand=(1.2, 1.4),
        force_text=(0.5, 1.0),
        force_static=(0.2, 0.4),
        pull_threshold=clear,
        max_move=10 * px,
        min_arrow_len=clear,
        # adjustText's default is a 1 s time limit, which made placement depend on CPU speed.
        iter_lim=1000,
        **({"arrowprops": line} if leader else {}),
    )
    return texts


# Backends that stamp the save time unless their metadata key is None.
_DATE_KEYS = {"svg": "Date", "svgz": "Date", "pdf": "CreationDate"}


def save_figure(fig, path, formats=("svg", "png"), **kwargs):
    """Write ``fig`` once per format, SVG and PNG by default.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to save.
    path : str or pathlib.Path
        Output path, with or without a suffix naming a format matplotlib can
        write, such as ``.svg`` or ``.pdf``. Any other suffix is part of the
        stem, so ``x.curve`` gives ``x.curve.svg`` and ``x.curve.png``.
        Missing parent directories are created.
    formats : sequence of str, default ("svg", "png")
        File formats to write, in order, e.g. ``("pdf", "png")``.
    **kwargs
        Passed to ``fig.savefig``. SVG and PDF files carry no creation date
        unless ``metadata`` sets one. With the themes' fixed ``svg.hashsalt``,
        reruns write the same bytes.

    Returns
    -------
    list of pathlib.Path
        The written paths, in the order of ``formats``.
    """
    path = Path(path)
    suffix = path.suffix.lower().removeprefix(".")
    stem = (
        path.with_suffix("") if suffix in fig.canvas.get_supported_filetypes() else path
    )
    stem.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt in formats:
        out = Path(f"{stem}.{fmt}")
        opts = dict(kwargs)
        if fmt in _DATE_KEYS:
            opts["metadata"] = {_DATE_KEYS[fmt]: None, **kwargs.get("metadata", {})}
        fig.savefig(out, format=fmt, **opts)
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
