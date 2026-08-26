"""Rosé Pine matplotlib styles with a vendored Google Sans Flex font.

Importing this package registers the vendored font and adds every style
to matplotlib's library, so ``plt.style.use("rose-pine")`` works. Use
:func:`apply_style` for the full setup (Agg backend + style).
"""

from .style import (
    VARIANTS,
    apply_style,
    register,
    register_fonts,
    style_path,
)

__all__ = [
    "VARIANTS",
    "apply_style",
    "register",
    "register_fonts",
    "style_path",
]

register()
