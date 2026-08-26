"""Rosé Pine matplotlib styles backed by a vendored Google Sans Flex font."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.style  # noqa: F401  (registers mpl.style)
from matplotlib import font_manager

VARIANTS = ("rose-pine", "rose-pine-moon", "rose-pine-dawn")

_PKG = Path(__file__).resolve().parent
_STYLES = _PKG / "styles"
_FONTS = _PKG / "fonts"


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


def register_fonts():
    """Register the vendored fonts so styles can reference them by name."""
    for path in sorted(_FONTS.glob("*.[ot]tf")):
        font_manager.fontManager.addfont(str(path))


def register():
    """Register fonts and add every variant to matplotlib's style library.

    After calling this, styles are usable by name, e.g.
    ``plt.style.use("rose-pine-moon")``.
    """
    register_fonts()
    for variant in VARIANTS:
        mpl.style.library[variant] = mpl.rc_params_from_file(
            style_path(variant), use_default_template=False
        )


def apply_style(variant="rose-pine"):
    """Set the Agg backend and apply a Rosé Pine style.

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
    register_fonts()
    mpl.style.use("default")
    mpl.style.use(style_path(variant))
