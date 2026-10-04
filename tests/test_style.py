import datetime as dt
from itertools import combinations

import matplotlib as mpl
import pytest

from matplotlib_rosepine import (
    VARIANTS,
    apply_style,
    despine,
    label_points,
    save_figure,
    style_path,
)

apply_style()

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.transforms import Bbox


@pytest.mark.parametrize("variant", VARIANTS)
def test_style_file_loads_without_warnings(variant, caplog):
    mpl.rc_params_from_file(style_path(variant), use_default_template=False)
    assert not caplog.records


@pytest.mark.parametrize("variant", VARIANTS)
def test_style_file_sets_skill_rc(variant):
    rc = mpl.rc_params_from_file(style_path(variant), use_default_template=False)
    assert rc["font.family"] == ["sans-serif"]
    assert rc["font.sans-serif"] == [
        "Anthropic Sans Text",
        "Google Sans Flex",
        "Arimo",
        "Arial",
        "DejaVu Sans",
    ]
    assert not rc["axes.spines.top"] and not rc["axes.spines.right"]
    assert rc["xtick.direction"] == rc["ytick.direction"] == "in"
    assert rc["svg.fonttype"] == "none"
    assert rc["figure.constrained_layout.use"]
    assert "savefig.format" not in rc


@pytest.mark.parametrize("variant", VARIANTS)
def test_style_file_uses_one_background_without_grid(variant):
    rc = mpl.rc_params_from_file(style_path(variant), use_default_template=False)
    assert rc["axes.facecolor"] == rc["legend.facecolor"] == rc["figure.facecolor"]
    assert not rc.get("axes.grid", False)


def test_save_figure_writes_svg_and_png(tmp_path):
    fig = plt.figure()
    written = save_figure(fig, tmp_path / "sub" / "plot")
    assert [p.name for p in written] == ["plot.svg", "plot.png"]
    assert all(p.stat().st_size > 0 for p in written)
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
    start = dt.datetime(2026, 8, 27, tzinfo=dt.timezone.utc)
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
    fig, ax = plt.subplots(figsize=(3, 2))
    (line,) = ax.plot([0, 1, 2, 3], [0, 1, 4, 9], marker="o", markersize=8, linewidth=3)
    despine(ax)
    assert line.get_clip_on() is False
    outside, inside = edge_marker_pixels(ax, (0, 0), line.get_color())
    assert inside > 0
    assert outside > 0.5 * inside
    plt.close(fig)


def test_despine_keeps_clipping_with_explicit_limits():
    fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1, 2, 3], [0, 1, 4, 9])
    ax.set_xlim(1, 2)
    despine(ax)
    assert line.get_clip_on() is True
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
        boxes = [t.get_window_extent().padded(gap / 2) for t in ax.texts]
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
        assert not any(t.get_window_extent().overlaps(marker) for t in texts)
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
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
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
            assert not any(t.get_window_extent().overlaps(marker) for t in ax.texts)
    plt.close(fig)


def test_label_points_leader_lines_use_edge_color():
    fig, ax = plt.subplots(figsize=(3, 3))
    points = ax.scatter([0.5, 0.5, 0.51], [0.5, 0.51, 0.5])
    despine(ax)
    label_points(ax, points, ["alpha", "beta", "gamma"])
    arrows = ax.patches
    assert arrows
    assert all(
        np.allclose(a.get_edgecolor()[:3], to_rgb(plt.rcParams["axes.edgecolor"]))
        for a in arrows
    )
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
