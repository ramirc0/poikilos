"""Render an SVG and PNG preview for each Rosé Pine style into assets/."""

from pathlib import Path

import numpy as np

from matplotlib_rosepine import VARIANTS, apply_style
import matplotlib.pyplot as plt

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def main():
    ASSETS.mkdir(exist_ok=True)
    x = np.linspace(0, 2 * np.pi, 100)
    for variant in VARIANTS:
        apply_style(variant)
        fig, ax = plt.subplots(figsize=(4, 3))
        for k in range(6):
            ax.plot(x, np.sin(x + k / 2), label=f"s{k}")
        ax.set_title(variant)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True)
        ax.legend(ncol=3, fontsize=6)
        for ext in ("svg", "png"):
            out = ASSETS / f"preview-{variant}.{ext}"
            fig.savefig(out)
            print(f"wrote {out}")
        plt.close(fig)


if __name__ == "__main__":
    main()
