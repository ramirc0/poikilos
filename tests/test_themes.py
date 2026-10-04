import re
import subprocess
import sys
from itertools import permutations
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pytest
from matplotlib.colors import to_rgb

import poikilos as pk
from poikilos.themes import _ROLES

PACKAGE = Path(pk.__file__).parent
STYLES = [PACKAGE / "base.mplstyle", *sorted((PACKAGE / "looks").glob("*.mplstyle"))]
PALETTE_KEYS = {key for keys in _ROLES.values() for key in keys} | {"axes.prop_cycle"}


def luminance(color):
    rgb = np.array(to_rgb(color))
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return linear @ [0.2126, 0.7152, 0.0722]


def contrast(a, b):
    """WCAG 2 contrast ratio between two colors."""
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_public_api():
    assert sorted(pk.__all__) == [
        "PALETTES",
        "THEMES",
        "context",
        "despine",
        "label_points",
        "rc_params",
        "save_figure",
        "use",
    ]
    assert list(pk.THEMES) == [
        "plain",
        "plain-dark",
        "rose-pine",
        "rose-pine-moon",
        "rose-pine-dawn",
    ]


def test_import_has_no_side_effects():
    code = (
        "import matplotlib as mpl; before = dict(mpl.rcParams); import poikilos; "
        "from matplotlib import style; "
        "assert dict(mpl.rcParams) == before; assert 'rose-pine' not in style.library"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


@pytest.mark.parametrize("path", STYLES, ids=lambda p: p.stem)
def test_style_file_loads_without_warnings(path, caplog):
    mpl.rc_params_from_file(path, use_default_template=False)
    assert not caplog.records


@pytest.mark.parametrize("path", STYLES, ids=lambda p: p.stem)
def test_style_file_sets_no_palette_key(path):
    rc = mpl.rc_params_from_file(path, use_default_template=False)
    assert not PALETTE_KEYS & set(rc)


@pytest.mark.parametrize("theme", pk.THEMES)
def test_theme_references_existing_look_and_palette(theme):
    look, palette = pk.THEMES[theme]
    assert (PACKAGE / "looks" / f"{look}.mplstyle").exists()
    assert palette in pk.PALETTES


@pytest.mark.parametrize("name", pk.PALETTES)
def test_palette_colors_are_hex(name):
    palette = pk.PALETTES[name]
    roles = [getattr(palette, role) for role in _ROLES]
    assert palette.cycle
    for color in [*roles, *palette.cycle, *palette.colors.values()]:
        assert re.fullmatch("#[0-9a-f]{6}", color)


@pytest.mark.parametrize("name", pk.PALETTES)
def test_text_contrast(name):
    palette = pk.PALETTES[name]
    assert contrast(palette.foreground, palette.background) >= 4.5


@pytest.mark.parametrize("theme", pk.THEMES)
def test_theme_never_sets_savefig_format(theme):
    assert "savefig.format" not in pk.rc_params(theme)


@pytest.mark.parametrize(
    "theme", [t for t, (look, _) in pk.THEMES.items() if look == "plain"]
)
def test_plain_look_keeps_skill_rules(theme):
    rc = pk.rc_params(theme)
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
    assert rc["savefig.dpi"] == 300
    assert not rc.get("axes.grid", False)


@pytest.mark.parametrize(("first", "second"), list(permutations(pk.THEMES, 2)))
def test_use_replaces_the_previous_theme(first, second):
    pk.use(second)
    alone = dict(mpl.rcParams)
    pk.use(first, rc={"axes.grid": True})
    pk.use(second)
    assert dict(mpl.rcParams) == alone


def test_use_keeps_the_backend():
    backend = mpl.rcParams["backend"]
    pk.use("rose-pine")
    assert mpl.rcParams["backend"] == backend


def test_context_restores_rc():
    before = dict(mpl.rcParams)
    with pk.context("rose-pine-dawn"):
        assert (
            mpl.rcParams["axes.facecolor"] == pk.PALETTES["rose-pine-dawn"].background
        )
    assert dict(mpl.rcParams) == before


def test_palette_override():
    pk.use("rose-pine", palette="rose-pine-dawn")
    dawn = pk.PALETTES["rose-pine-dawn"]
    assert mpl.rcParams["axes.facecolor"] == dawn.background
    assert mpl.rcParams["axes.prop_cycle"].by_key()["color"] == list(dawn.cycle)


def test_rc_override():
    pk.use("rose-pine", rc={"axes.grid": True, "text.color": "red"})
    assert mpl.rcParams["axes.grid"]
    assert mpl.rcParams["text.color"] == "red"


@pytest.mark.parametrize(
    ("rc", "error"),
    [
        ({"axes.facecolour": "red"}, KeyError),
        ({"axes.facecolor": "not a color"}, ValueError),
    ],
)
def test_bad_rc_changes_nothing(rc, error):
    pk.use("rose-pine-dawn")
    before = dict(mpl.rcParams)
    with pytest.raises(error):
        pk.use("rose-pine", rc=rc)
    assert dict(mpl.rcParams) == before


@pytest.mark.parametrize(
    "kwargs", [{"theme": "rose-pine-noon"}, {"theme": "rose-pine", "palette": "noon"}]
)
def test_unknown_name_lists_choices(kwargs):
    with pytest.raises(ValueError, match="choose from .*rose-pine-dawn"):
        pk.rc_params(**kwargs)
