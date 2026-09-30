"""Rosé Pine matplotlib styles."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.style  # noqa: F401  (registers mpl.style)

VARIANTS = ("rose-pine", "rose-pine-moon", "rose-pine-dawn")

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
