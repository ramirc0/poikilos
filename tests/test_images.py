import shutil
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.testing.compare import compare_images

import poikilos as pk

VERSION = "3.11"
BASELINE = Path(__file__).parent / "baseline" / VERSION
# Bundled fonts, so the images do not depend on what the machine has installed.
FONTS = {"font.serif": ["DejaVu Serif"], "font.sans-serif": ["DejaVu Sans"]}

pytestmark = [
    pytest.mark.images,
    pytest.mark.skipif(
        not mpl.__version__.startswith(f"{VERSION}."),
        reason=f"baselines are for matplotlib {VERSION}",
    ),
]


def reference_figure():
    width, height = mpl.rcParams["figure.figsize"]
    fig, (lines, box) = plt.subplots(1, 2, figsize=(2 * width, height))
    x = np.linspace(0, 10, 21)
    for k in range(4):
        lines.plot(x, np.sin(x / 2 + k) * (k + 1) * 300, label=f"series {k}")
    lines.set(title="Lines", xlabel="time (s)", ylabel="signal")
    lines.legend()
    data = [np.r_[np.linspace(1, 5, 15), 9], np.linspace(2, 4, 10)]
    box.boxplot(data, showmeans=True)
    box.bar([3, 4], [2, 3], color=["C0", "C1"])
    box.set(title="Boxes and bars", xlabel="group")
    return fig


@pytest.mark.parametrize("theme", pk.THEMES)
def test_theme_image(theme, tmp_path):
    expected = BASELINE / f"{theme}.png"
    actual = tmp_path / f"{theme}.png"
    with pk.context(theme, rc=FONTS):
        fig = reference_figure()
        fig.savefig(actual, dpi=100)
        plt.close(fig)
    if not expected.exists():
        expected.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(actual, expected)
        pytest.fail(f"wrote missing baseline {expected}; review and commit it")
    assert compare_images(expected, actual, tol=0) is None
