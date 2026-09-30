"""Rosé Pine matplotlib styles.

Importing this package adds every style to matplotlib's library, so
``plt.style.use("rose-pine")`` works. Use :func:`apply_style` for the full
setup (Agg backend + style).
"""

from .style import (
    FORMATS,
    VARIANTS,
    apply_style,
    despine,
    label_points,
    register,
    save_figure,
    style_path,
)

__all__ = [
    "FORMATS",
    "VARIANTS",
    "apply_style",
    "despine",
    "label_points",
    "register",
    "save_figure",
    "style_path",
]

register()
