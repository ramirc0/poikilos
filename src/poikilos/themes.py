"""Themes: a look (fonts, spines, ticks, sizes) plus a palette (colors)."""

import tomllib
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import matplotlib as mpl
import numpy as np
from cycler import cycler
from matplotlib import style
from matplotlib.colors import to_hex, to_rgb

_HERE = Path(__file__).resolve().parent

# Only root keys: legend, title, savefig and hatch colors inherit from these.
_ROLES = {
    "background": (
        "figure.facecolor",
        "figure.edgecolor",
        "axes.facecolor",
        "axes3d.xaxis.panecolor",
        "axes3d.yaxis.panecolor",
        "axes3d.zaxis.panecolor",
    ),
    "foreground": (
        "text.color",
        "axes.labelcolor",
        "xtick.labelcolor",
        "ytick.labelcolor",
        "patch.edgecolor",
        "boxplot.boxprops.color",
        "boxplot.whiskerprops.color",
        "boxplot.capprops.color",
        "boxplot.flierprops.color",
        "boxplot.flierprops.markeredgecolor",
    ),
    "frame": ("axes.edgecolor",),
    "ticks": ("xtick.color", "ytick.color"),
    "grid": ("grid.color",),
    "legend_edge": ("legend.edgecolor",),
    "median": ("boxplot.medianprops.color",),
    "mean": (
        "boxplot.meanprops.color",
        "boxplot.meanprops.markerfacecolor",
        "boxplot.meanprops.markeredgecolor",
    ),
}


@dataclass(frozen=True)
class Palette:
    """Colors of a theme, each role resolved to a hex string.

    Attributes
    ----------
    background : str
        Figure face and edge, axes face and 3D panes.
    foreground : str
        Text, tick labels, patch edges and boxplot lines.
    frame : str
        Axes spines.
    ticks : str
        Tick marks.
    grid : str
        Grid lines.
    legend_edge : str
        Legend frame.
    median : str
        Boxplot median line.
    mean : str
        Boxplot mean marker and line.
    cycle : tuple of str
        Property cycle colors, in order.
    colors : Mapping[str, str]
        The palette's own named colors, e.g. ``"love"`` for Rosé Pine.
    """

    background: str
    foreground: str
    frame: str
    ticks: str
    grid: str
    legend_edge: str
    median: str
    mean: str
    cycle: tuple[str, ...]
    colors: Mapping[str, str]


def _load_palette(path):
    data = tomllib.loads(path.read_text())
    colors = {name: to_hex(value) for name, value in data["colors"].items()}

    def resolve(value):
        return colors[value] if value in colors else to_hex(value)

    roles = data["roles"]
    return Palette(
        **{role: resolve(value) for role, value in roles.items() if role != "cycle"},
        cycle=tuple(map(resolve, roles["cycle"])),
        colors=MappingProxyType(colors),
    )


PALETTES = MappingProxyType(
    {
        path.stem: _load_palette(path)
        for path in sorted((_HERE / "palettes").glob("*.toml"))
    }
)

THEMES = MappingProxyType(
    {
        "plain": ("plain", "plain"),
        "plain-dark": ("plain", "plain-dark"),
        "rose-pine": ("plain", "rose-pine"),
        "rose-pine-moon": ("plain", "rose-pine-moon"),
        "rose-pine-dawn": ("plain", "rose-pine-dawn"),
        "lilaq": ("lilaq", "lilaq"),
        "lilaq-moon": ("lilaq", "lilaq-moon"),
        "pgl": ("pgl", "pgl"),
    }
)


def _get(mapping, name, kind):
    if name not in mapping:
        raise ValueError(f"unknown {kind} {name!r}; choose from {', '.join(mapping)}")
    return mapping[name]


def rc_params(theme, palette=None):
    """Return the rcParams a theme sets.

    Parameters
    ----------
    theme : str
        A key of :data:`THEMES`.
    palette : str, optional
        A key of :data:`PALETTES` that replaces the theme's own palette.

    Returns
    -------
    dict
        The base settings, then the look's, then the palette's colors.

    Raises
    ------
    ValueError
        If ``theme`` or ``palette`` is unknown.
    """
    look, default = _get(THEMES, theme, "theme")
    colors = _get(PALETTES, default if palette is None else palette, "palette")
    params = {}
    for path in (_HERE / "base.mplstyle", _HERE / "looks" / f"{look}.mplstyle"):
        params.update(mpl.rc_params_from_file(path, use_default_template=False))
    for role, keys in _ROLES.items():
        params.update(dict.fromkeys(keys, getattr(colors, role)))
    params["axes.prop_cycle"] = cycler(color=colors.cycle)
    return params


def use(theme, *, palette=None, rc=None):
    """Reset matplotlib's style to its defaults, then apply a theme.

    Every style rcParam is reset first, so settings made before this call
    are lost; set them after it or pass them in ``rc``. The backend is kept,
    so this works before or after importing ``matplotlib.pyplot``. Invalid
    input raises before any rcParam changes.

    Parameters
    ----------
    theme : str
        A key of :data:`THEMES`.
    palette : str, optional
        A key of :data:`PALETTES` that replaces the theme's own palette.
    rc : dict, optional
        rcParams applied on top of the theme.

    Raises
    ------
    ValueError
        If ``theme`` or ``palette`` is unknown, or a value in ``rc`` is invalid.
    KeyError
        If a key in ``rc`` is not an rcParam.
    """
    params = mpl.RcParams({**rc_params(theme, palette), **(rc or {})})
    style.use(["default", params])


@contextmanager
def context(theme, *, palette=None, rc=None):
    """Apply a theme inside a ``with`` block and restore rcParams on exit.

    Save figures inside the block: settings such as ``savefig.dpi`` are read
    at save time.

    Parameters
    ----------
    theme : str
        A key of :data:`THEMES`.
    palette : str, optional
        A key of :data:`PALETTES` that replaces the theme's own palette.
    rc : dict, optional
        rcParams applied on top of the theme.

    Yields
    ------
    None

    Raises
    ------
    ValueError
        If ``theme`` or ``palette`` is unknown, or a value in ``rc`` is invalid.
    KeyError
        If a key in ``rc`` is not an rcParam.
    """
    with mpl.rc_context():
        use(theme, palette=palette, rc=rc)
        yield


def _luminance(color):
    rgb = np.array(to_rgb(color))
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return linear @ [0.2126, 0.7152, 0.0722]


def _contrast(a, b):
    """WCAG 2 contrast ratio between two colors."""
    hi, lo = sorted([_luminance(a), _luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)
