import datetime as dt
from itertools import combinations, pairwise

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_rgb, to_rgba
from matplotlib.patches import BoxStyle
from matplotlib.transforms import Bbox

import poikilos as pk
from poikilos import despine, label_points, save_figure, zero_line


@pytest.fixture(autouse=True)
def theme():
    # Label placement depends on text widths; a bundled font keeps it the same everywhere.
    with pk.context("rose-pine", rc={"font.sans-serif": ["DejaVu Sans"]}):
        yield


def test_save_figure_writes_svg_and_png(tmp_path):
    fig = plt.figure()
    written = save_figure(fig, tmp_path / "sub" / "plot")
    assert [p.name for p in written] == ["plot.svg", "plot.png"]
    assert all(p.stat().st_size > 0 for p in written)
    plt.close(fig)


def test_save_figure_writes_the_given_formats(tmp_path):
    fig = plt.figure()
    written = save_figure(fig, tmp_path / "plot.svg", formats=("pdf", "png"))
    assert [p.name for p in written] == ["plot.pdf", "plot.png"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["plot.pdf", "plot.png"]
    plt.close(fig)


def test_despine_numeric_axis_ends_on_ticks():
    fig, ax = plt.subplots()
    ax.plot([0.3, 9.2], [1.1, 7.7])
    despine(ax)
    for (lo, hi), ticks, (dmin, dmax) in [
        (ax.get_xlim(), ax.get_xticks(), (0.3, 9.2)),
        (ax.get_ylim(), ax.get_yticks(), (1.1, 7.7)),
    ]:
        assert (lo, hi) == (ticks[0], ticks[-1])
        assert lo <= dmin and hi >= dmax
    assert tuple(ax.spines["bottom"].get_bounds()) == ax.get_xlim()
    assert tuple(ax.spines["left"].get_bounds()) == ax.get_ylim()
    assert not ax.spines["top"].get_visible() and not ax.spines["right"].get_visible()
    assert ax.spines["left"].get_position() == ("outward", 10)
    plt.close(fig)


def test_despine_date_axis():
    fig, ax = plt.subplots()
    start = dt.datetime(2026, 8, 27, tzinfo=dt.UTC)
    days = [start + dt.timedelta(days=i) for i in range(30)]
    ax.plot(days, range(30))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    despine(ax)
    lo, hi = ax.get_xlim()
    ticks = ax.get_xticks()
    assert (lo, hi) == (mdates.date2num(days[0]), mdates.date2num(days[-1]))
    assert (ticks[0], ticks[-1]) == (lo, hi)
    assert tuple(ax.spines["bottom"].get_bounds()) == (lo, hi)
    assert all(mdates.num2date(t).weekday() == 0 for t in ticks[1:-1])
    plt.close(fig)


def edge_marker_pixels(ax, point, color):
    """Count ``color`` pixels just outside and just inside the axes' left edge at ``point``."""
    fig = ax.figure
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].astype(int)
    x, y = ax.transData.transform(point)
    col, row = round(x), round(img.shape[0] - y)
    match = (np.abs(img - np.array(to_rgb(color)) * 255) < 40).all(axis=-1)
    rows = slice(row - 20, row + 20)
    return match[rows, col - 20 : col].sum(), match[rows, col : col + 20].sum()


def test_despine_does_not_clip_edge_markers():
    fig, ax = plt.subplots(figsize=(3, 2), dpi=300)
    (line,) = ax.plot([0, 1, 2, 3], [0, 1, 4, 9], marker="o", markersize=8, linewidth=3)
    despine(ax)
    assert line.get_clip_on() is False
    outside, inside = edge_marker_pixels(ax, (0, 0), line.get_color())
    assert inside > 0
    assert outside > 0.5 * inside
    plt.close(fig)


def test_despine_keeps_clipping_when_limits_crop_data():
    fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1, 2, 3], [0, 1, 4, 9])
    ax.set_xlim(1, 2)
    despine(ax)
    assert line.get_clip_on() is True
    plt.close(fig)


def test_despine_unclips_within_explicit_limits():
    fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1, 2, 3], [0, 1, 4, 9])
    ax.set_ylim(0, 10)
    despine(ax)
    assert line.get_clip_on() is False
    plt.close(fig)


@pytest.mark.parametrize("share", ["sharex", "sharey"])
def test_despine_unclips_every_shared_axes(share):
    # Setting limits on one axes turns autoscaling off on the axes sharing them.
    fig, axes = plt.subplots(1, 2, **{share: True})
    lines = [ax.plot([0, 1, 2, 3], [0, 1, 4, 9], marker="o")[0] for ax in axes]
    for ax in axes:
        despine(ax)
    assert [line.get_clip_on() for line in lines] == [False, False]
    plt.close(fig)


@pytest.mark.parametrize(
    "draw",
    [
        lambda ax: ax.bar([0, 1], [1e7, 1e5]),
        lambda ax: ax.errorbar([1, 2], [10, 1e3], yerr=20),
    ],
    ids=["bar", "errorbar"],
)
def test_despine_keeps_clipping_when_a_log_axis_drops_data(draw):
    # A log axis leaves values <= 0 out of its limits. Unclipped, a bar's base at 0
    # drew 90,000 px below the axes and collapsed constrained layout.
    fig, ax = plt.subplots(figsize=(6, 3.5))
    draw(ax)
    ax.set_yscale("log")
    despine(ax)
    fig.canvas.draw()
    assert all(a.get_clip_on() for a in [*ax.lines, *ax.collections, *ax.patches])
    assert ax.get_tightbbox(fig.canvas.get_renderer()).y0 >= 0
    plt.close(fig)


def test_despine_unclips_positive_data_on_a_log_axis():
    fig, ax = plt.subplots()
    (line,) = ax.plot([1, 2, 3], [10, 1e3, 1e4], marker="o")
    ax.set_yscale("log")
    despine(ax)
    assert line.get_clip_on() is False
    plt.close(fig)


def test_despine_keeps_inverted_axis():
    fig, ax = plt.subplots()
    ax.imshow(np.arange(12).reshape(3, 4))
    despine(ax)
    assert ax.yaxis_inverted()
    plt.close(fig)


def test_despine_categorical_y_drops_left_spine():
    fig, ax = plt.subplots()
    ax.barh(["a", "b", "c"], [3.2, 1.0, 7.5])
    despine(ax, categorical_y=True)
    assert not ax.spines["left"].get_visible()
    assert all(t.tick1line.get_markersize() == 0 for t in ax.yaxis.get_major_ticks())
    assert ax.get_xlim()[1] >= 7.5
    assert tuple(ax.spines["bottom"].get_bounds()) == ax.get_xlim()
    plt.close(fig)


@pytest.mark.parametrize("axis", ["x", "y"])
def test_despine_keeps_categorical_labels_by_the_data(axis):
    fig, ax = plt.subplots()
    (ax.bar if axis == "x" else ax.barh)(["a", "b", "c"], [3.2, 1.0, 7.5])
    despine(ax, **{f"categorical_{axis}": True})
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    edge = ax.get_window_extent(renderer)
    boxes = [
        t.get_window_extent(renderer) for t in getattr(ax, f"get_{axis}ticklabels")()
    ]
    if axis == "x":
        gap = edge.y0 - max(b.y1 for b in boxes)
    else:
        gap = edge.x0 - max(b.x1 for b in boxes)
    gap *= 72 / fig.dpi
    assert gap == pytest.approx(mpl.rcParams[f"{axis}tick.major.pad"], abs=0.5)
    plt.close(fig)


def test_despine_picks_ticks_for_the_laid_out_axes():
    # Constrained layout shrinks the axes to fit long category labels. Ticks picked
    # for the axes before layout then overlapped.
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.barh(
        ["representative present, below final support threshold", "no peak", "peak"],
        [206000, 82000, 4700],
    )
    despine(ax, categorical_y=True)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(renderer) for t in ax.get_xticklabels()]
    assert all(a.x1 < b.x0 for a, b in pairwise(boxes))
    plt.close(fig)


def test_despine_keeps_categorical_limits_under_a_twin():
    # A twin refitted the shared axis with its own 5% margin, moving the bars off the spine.
    fig, ax = plt.subplots()
    ax.bar([1, 2, 3], [3.2, 1.0, 7.5])
    despine(ax, categorical_x=True)
    xlim = ax.get_xlim()
    twin = ax.twinx()
    twin.plot([1, 2, 3], [10, 50, 90])
    twin.set_ylim(0, 100)
    assert ax.get_xlim() == xlim
    plt.close(fig)


def test_despine_heatmap_has_no_spines():
    fig, ax = plt.subplots()
    ax.pcolormesh(np.arange(6).reshape(2, 3))
    despine(ax, categorical_x=True, categorical_y=True)
    assert not any(spine.get_visible() for spine in ax.spines.values())
    plt.close(fig)


def test_label_points_leaves_a_gap_between_labels():
    rng = np.random.default_rng(0)
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.suptitle("title")
    for ax in axes:
        x, y = rng.normal(0.5, 0.02, 8), rng.normal(0.5, 0.02, 8)
        ax.plot([0.4, 0.6], [0.4, 0.6])
        points = ax.scatter(x, y)
        ax.set_title("panel")
        despine(ax)
        label_points(ax, points, [f"label {i}" for i in range(8)], fontsize=8)
    fig.canvas.draw()
    gap = 2 * fig.dpi / 72
    for ax in axes:
        boxes = [
            t.get_bbox_patch().get_window_extent().padded(gap / 2) for t in ax.texts
        ]
        assert not any(a.overlaps(b) for a, b in combinations(boxes, 2))
    plt.close(fig)


def test_label_points_keeps_labels_off_markers():
    fig, ax = plt.subplots(figsize=(3, 3))
    x, y = np.array([0.5, 0.5, 0.51, 0.52]), np.array([0.5, 0.51, 0.5, 0.52])
    points = ax.scatter(x, y)
    despine(ax)
    texts = label_points(ax, points, ["alpha", "beta", "gamma", "delta"])
    fig.canvas.draw()
    radius = plt.rcParams["lines.markersize"] / 2 * fig.dpi / 72
    for px, py in ax.transData.transform(np.column_stack([x, y])):
        marker = Bbox.from_extents(px - radius, py - radius, px + radius, py + radius)
        assert not any(
            t.get_bbox_patch().get_window_extent().overlaps(marker) for t in texts
        )
    plt.close(fig)


def test_label_points_keeps_labels_off_markers_at_print_dpi():
    # adjustText sizes its pull and move steps in pixels; at 300 dpi its screen-sized
    # defaults pulled labels back onto their own markers on this real figure.
    panels = [
        (
            [0.677, 0.585, 0.722, 0.529, 0.695, 0.592, 0.545, 0.499],
            [0.67, 0.572, 0.722, 0.514, 0.692, 0.571, 0.528, 0.481],
        ),
        (
            [0.24, 0.309, 0.235, 0.263, 0.225, 0.238, 0.244, 0.335],
            [0.247, 0.317, 0.238, 0.269, 0.228, 0.243, 0.25, 0.347],
        ),
        (
            [0.65, 0.637, 0.695, 0.856, 0.627, 0.947, 0.775, 0.614],
            [0.638, 0.588, 0.688, 0.853, 0.601, 0.929, 0.753, 0.562],
        ),
        (
            [0.58, 0.447, 0.664, 0.173, 0.886, 0.125, 0.202, 0.448],
            [0.971, 0.902, 0.994, 0.32, 1.354, 0.196, 0.54, 1.456],
        ),
    ]
    labels = ["HepG2", "MCF-7", "A549", "SK-N-SH", "HeLa-S3", "H1", "K562", "GM12878"]
    fig, axes = plt.subplots(1, 4, figsize=(16, 4), dpi=300)
    fig.suptitle("title")
    scatters = []
    for ax, (x, y) in zip(axes, panels):
        ax.plot([min(x + y), max(x + y)], [min(x + y), max(x + y)], ls="--")
        scatters.append(ax.scatter(x, y))
        ax.set_title("panel")
        despine(ax)
    for ax, points in zip(axes, scatters):
        label_points(ax, points, labels, fontsize=8)
    fig.canvas.draw()
    radius = plt.rcParams["lines.markersize"] / 2 * fig.dpi / 72
    for ax in axes:
        for px, py in ax.transData.transform(ax.collections[0].get_offsets()):
            marker = Bbox.from_extents(
                px - radius, py - radius, px + radius, py + radius
            )
            assert not any(
                t.get_bbox_patch().get_window_extent().overlaps(marker)
                for t in ax.texts
            )
    plt.close(fig)


def test_label_points_boxes_labels_like_the_legend():
    fig, ax = plt.subplots(figsize=(3, 3))
    points = ax.scatter([0.2, 0.8], [0.2, 0.8])
    despine(ax)
    texts = label_points(ax, points, ["alpha", "beta"])
    rc = plt.rcParams
    alpha = rc["legend.framealpha"]
    for text in texts:
        box = text.get_bbox_patch()
        assert isinstance(box.get_boxstyle(), BoxStyle.Round)
        assert np.allclose(box.get_facecolor(), to_rgba(rc["axes.facecolor"], alpha))
    plt.close(fig)


@pytest.mark.parametrize("font", ["DejaVu Sans", "DejaVu Serif"])
@pytest.mark.parametrize("label", ["A549", "HepG2", "ace"])
def test_label_points_centers_labels_in_their_boxes(label, font):
    # Text sits each line on the font's ascent and descent, so a label's space above
    # and below its ink depended on the font and on which letters it has.
    fig, ax = plt.subplots(figsize=(3, 2), dpi=200)
    points = ax.scatter([0.5], [0.5])
    (text,) = label_points(
        ax, points, [label], color="#ff0000", fontsize=20, fontfamily=font
    )
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].astype(int)
    ink = np.flatnonzero(((img[..., 0] > 150) & (img[..., 1:] < 100).all(-1)).any(1))
    box = text.get_bbox_patch().get_window_extent()
    top_gap = ink.min() - (img.shape[0] - box.y1)
    bottom_gap = (img.shape[0] - box.y0) - ink.max()
    assert abs(top_gap - bottom_gap) <= 1 * fig.dpi / 72
    plt.close(fig)


def test_label_points_boxes_labels_on_a_look_without_legend_frames():
    with pk.context("pgl"):
        fig, ax = plt.subplots(figsize=(3, 3))
        points = ax.scatter([0.2, 0.8], [0.2, 0.8])
        texts = label_points(ax, points, ["alpha", "beta"])
    assert all(t.get_bbox_patch() for t in texts)
    plt.close(fig)


def test_label_points_leaves_labels_bare_without_bbox():
    fig, ax = plt.subplots(figsize=(3, 3))
    points = ax.scatter([0.2, 0.8], [0.2, 0.8])
    texts = label_points(ax, points, ["alpha", "beta"], bbox=None)
    assert all(t.get_bbox_patch() is None for t in texts)
    plt.close(fig)


def test_label_points_outlines_boxes_like_their_leader_lines():
    fig, ax = plt.subplots(figsize=(3, 3))
    points = ax.scatter([0.5, 0.5, 0.51], [0.5, 0.51, 0.5])
    despine(ax)
    texts = label_points(ax, points, ["alpha", "beta", "gamma"])
    arrows = ax.patches
    assert arrows
    edge = to_rgba(plt.rcParams["axes.edgecolor"])
    for artist in [*arrows, *(t.get_bbox_patch() for t in texts)]:
        assert np.allclose(artist.get_edgecolor(), edge)
        assert artist.get_linewidth() == arrows[0].get_linewidth()
    plt.close(fig)


def test_label_points_leader_lines_touch_their_boxes():
    fig, ax = plt.subplots(figsize=(3, 3))
    points = ax.scatter([0.5, 0.5, 0.51], [0.5, 0.51, 0.5])
    despine(ax)
    label_points(ax, points, ["alpha", "beta", "gamma"])
    fig.canvas.draw()
    arrows = ax.patches
    assert arrows
    for arrow in arrows:
        start = arrow.get_transform().transform_path(arrow.get_path()).vertices[0]
        box = arrow.patchA.get_bbox_patch().get_window_extent()
        assert box.padded(1).contains(*start)
        assert not box.padded(-1).contains(*start)
    plt.close(fig)


def test_save_figure_keeps_dotted_stems(tmp_path):
    fig = plt.figure()
    written = save_figure(fig, tmp_path / "a.curve.svg") + save_figure(
        fig, tmp_path / "b.curve"
    )
    assert [p.name for p in written] == [
        "a.curve.svg",
        "a.curve.png",
        "b.curve.svg",
        "b.curve.png",
    ]
    assert all(p.exists() for p in written)
    plt.close(fig)


def test_despine_keeps_empty_lines_out_of_the_layout():
    # A boxplot without outliers has an empty flier line. Its marker-padded extent sits at
    # the figure origin. Unclipped, it dragged constrained layout down to that corner.
    fig, ax = plt.subplots(figsize=(3, 3))
    parts = ax.boxplot([0.33, 0.35, 0.36, 0.41, 0.46])
    despine(ax, categorical_x=True)
    fig.canvas.draw()
    assert parts["fliers"][0].get_clip_on() is True
    assert all(line.get_clip_on() is False for line in parts["whiskers"])
    assert ax.get_tightbbox(fig.canvas.get_renderer()).y0 >= 0
    plt.close(fig)


def test_despine_hides_mirrored_ticks():
    with mpl.rc_context(
        {
            "xtick.top": True,
            "ytick.right": True,
            "xtick.minor.visible": True,
            "ytick.minor.visible": True,
        }
    ):
        fig, ax = plt.subplots()
    ax.plot([0.3, 9.2], [1.1, 7.7])
    despine(ax)
    fig.canvas.draw()
    ticks = [
        *ax.xaxis.get_major_ticks(),
        *ax.xaxis.get_minor_ticks(),
        *ax.yaxis.get_major_ticks(),
        *ax.yaxis.get_minor_ticks(),
    ]
    assert not any(t.tick2line.get_visible() for t in ticks)
    assert all(t.tick1line.get_visible() for t in ticks)
    plt.close(fig)


def test_despine_categorical_axis_drops_minor_ticks():
    with mpl.rc_context({"xtick.minor.visible": True}):
        fig, ax = plt.subplots()
    ax.bar(["a", "b", "c"], [3.2, 1.0, 7.5])
    despine(ax, categorical_x=True)
    fig.canvas.draw()
    ticks = [*ax.xaxis.get_major_ticks(), *ax.xaxis.get_minor_ticks()]
    assert all(t.tick1line.get_markersize() == 0 for t in ticks)
    plt.close(fig)


@pytest.mark.parametrize(
    ("draw", "categorical_x", "figsize"),
    [
        (lambda ax: ax.bar(["first", "second", "third"], [3.2, 1.0, 7.5]), True, None),
        (lambda ax: ax.plot([0.3, 9.2], [1.1, 7.7]), False, None),
        # Constrained layout widens this axes, so laying it out adds ticks.
        (lambda ax: ax.plot([0.3, 9.2], [1.1, 7.7]), False, (2, 2)),
    ],
    ids=["categorical", "continuous", "continuous-small"],
)
def test_despine_keeps_rotated_tick_labels(draw, categorical_x, figsize):
    # Moving a spine rebuilds its axis's ticks. Rotation set on the old labels went back
    # to horizontal, so long category names overlapped.
    images = []
    for rotate_first in (True, False):
        fig, ax = plt.subplots(figsize=figsize)
        draw(ax)
        if rotate_first:
            plt.setp(
                ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
            )
            despine(ax, categorical_x=categorical_x)
        else:
            despine(ax, categorical_x=categorical_x)
            # Ticks rebuilt on the moved spines show where kept ticks belong.
            ax.xaxis.reset_ticks()
            ax.yaxis.reset_ticks()
            plt.setp(
                ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
            )
        fig.canvas.draw()
        assert all(t.get_rotation() == 45 for t in ax.get_xticklabels())
        images.append(np.asarray(fig.canvas.buffer_rgba()).copy())
        plt.close(fig)
    assert np.array_equal(*images)


@pytest.mark.parametrize(
    ("axis", "drawn"), [("y", ["y"]), ("x", ["x"]), ("both", ["y", "x"])]
)
def test_zero_line_defaults(axis, drawn):
    fig, ax = plt.subplots()
    ax.plot([1, 2], [3, 4])
    lines = zero_line(ax, axis)
    assert len(lines) == len(drawn)
    for line, name in zip(lines, drawn):
        data, (lo, _) = (
            (line.get_ydata(), ax.get_ylim())
            if name == "y"
            else (line.get_xdata(), ax.get_xlim())
        )
        assert list(data) == [0, 0]
        assert lo <= 0
        assert line.get_color() == plt.rcParams["axes.edgecolor"]
        assert line.get_linewidth() == 2 * plt.rcParams["grid.linewidth"]
    plt.close(fig)


def test_zero_line_aliases_override():
    fig, ax = plt.subplots()
    (line,) = zero_line(ax, lw=3, c="r")
    assert line.get_linewidth() == 3
    assert line.get_color() == "r"
    plt.close(fig)


def test_zero_line_rejects_unknown_axis():
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="axis must be"):
        zero_line(ax, "z")
    plt.close(fig)
