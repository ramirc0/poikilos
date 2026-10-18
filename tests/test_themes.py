import re
import subprocess
import sys
from itertools import permutations
from pathlib import Path

import matplotlib as mpl
import pytest
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, findfont

import poikilos as pk
from poikilos.themes import _ROLES, _contrast

PACKAGE = Path(pk.__file__).parent
STYLES = [PACKAGE / "base.mplstyle", *sorted((PACKAGE / "looks").glob("*.mplstyle"))]


def test_public_api():
    assert sorted(pk.__all__) == [
        "PALETTES",
        "THEMES",
        "context",
        "despine",
        "fit_legend",
        "label_points",
        "rc_params",
        "save_figure",
        "use",
        "zero_line",
    ]
    assert list(pk.THEMES) == [
        "plain",
        "plain-dark",
        "rose-pine",
        "rose-pine-moon",
        "rose-pine-dawn",
        "lilaq",
        "lilaq-moon",
        "pgl",
        "zed",
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
def test_style_file_sets_no_color(path):
    rc = mpl.rc_params_from_file(path, use_default_template=False)
    assert not [key for key in rc if "color" in key or key == "axes.prop_cycle"]


@pytest.mark.parametrize("theme", pk.THEMES)
def test_theme_references_existing_look_and_palette(theme):
    look, palette = pk.THEMES[theme]
    assert (PACKAGE / "looks" / f"{look}.mplstyle").exists()
    assert palette in pk.PALETTES


@pytest.mark.parametrize("name", pk.PALETTES)
def test_palette_colors_are_hex(name):
    palette = pk.PALETTES[name]
    roles = [c for role in _ROLES if (c := getattr(palette, role)) is not None]
    assert palette.cycle
    for color in [*roles, *palette.cycle, *palette.colors.values()]:
        assert re.fullmatch("#[0-9a-f]{6}", color)


def test_scatter_edge_is_optional():
    assert pk.PALETTES["plain"].scatter_edge is None
    assert "scatter.edgecolors" not in pk.rc_params("plain")
    pk.use("plain")
    assert mpl.rcParams["scatter.edgecolors"] == "face"


@pytest.mark.parametrize("name", pk.PALETTES)
def test_text_contrast(name):
    palette = pk.PALETTES[name]
    assert _contrast(palette.foreground, palette.background) >= 4.5


@pytest.mark.parametrize("theme", pk.THEMES)
def test_theme_never_sets_savefig_format(theme):
    assert "savefig.format" not in pk.rc_params(theme)


@pytest.mark.parametrize("theme", pk.THEMES)
def test_figure_edge_matches_background(theme):
    pk.use(theme)
    assert mpl.rcParams["figure.edgecolor"] == mpl.rcParams["figure.facecolor"]


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


def test_pgl_look_keeps_skill_rules():
    pk.use("pgl")
    rc = mpl.rcParams
    assert rc["font.family"] == ["sans-serif"]
    assert rc["font.sans-serif"] == ["Overpass", "Arial", "Arimo", "DejaVu Sans"]
    assert not any(
        rc[f"axes.spines.{side}"] for side in ("left", "bottom", "top", "right")
    )
    assert not any(
        rc[key] for key in ("xtick.bottom", "xtick.top", "ytick.left", "ytick.right")
    )
    assert rc["axes.grid"] and rc["axes.axisbelow"] is True
    assert rc["grid.linestyle"] == "--"
    assert not rc["legend.frameon"]


def test_zed_look_keeps_reference_values():
    pk.use("zed")
    rc = mpl.rcParams
    assert rc["font.sans-serif"] == [
        "Helvetica Neue",
        "Helvetica",
        "Nimbus Sans",
        "Arial",
        "DejaVu Sans",
    ]
    assert rc["mathtext.fontset"] == "custom"
    sizes = {
        "font.size": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.labelsize": 10,
        "axes.titlesize": 12,
        "figure.labelsize": 12,
        "figure.titlesize": 14,
    }
    assert {key: rc[key] for key in sizes} == sizes
    assert rc["axes.titleweight"] == rc["figure.titleweight"] == "medium"
    assert not rc["axes.spines.top"] and not rc["axes.spines.right"]
    for axis in ("xtick", "ytick"):
        assert rc[f"{axis}.direction"] == "in"
        assert (rc[f"{axis}.major.size"], rc[f"{axis}.minor.size"]) == (5, 3)
        assert rc[f"{axis}.major.width"] == rc[f"{axis}.minor.width"] == 0.75
    assert rc["axes.linewidth"] == 0.75
    assert rc["lines.linewidth"] == 0.5
    assert rc["lines.solid_capstyle"] == "round"
    assert (rc["lines.markersize"], rc["lines.markeredgewidth"]) == (2, 0.25)
    assert not rc["lines.scale_dashes"] and rc["lines.dashed_pattern"] == [2, 1]
    assert rc["grid.linewidth"] == 0.25 and not rc["axes.grid"]
    assert not rc["legend.frameon"]
    assert rc["boxplot.patchartist"] and not rc["boxplot.showfliers"]
    assert rc["boxplot.boxprops.linewidth"] == 0
    assert rc["boxplot.medianprops.linewidth"] == 1.5
    assert rc["boxplot.medianprops.color"] == "#ffffff"
    assert rc["boxplot.whiskerprops.linewidth"] == rc["boxplot.capprops.linewidth"]
    assert rc["boxplot.whiskerprops.linewidth"] == 0.5
    assert (rc["errorbar.capsize"], rc["errorbar.capthick"]) == (2, 0.5)
    assert rc["scatter.edgecolors"] == "#ffffff"


def test_zed_palette_starts_with_warm_black_and_red():
    palette = pk.PALETTES["zed"]
    assert palette.foreground == palette.frame == palette.ticks == "#231f20"
    assert palette.cycle == (
        "#231f20",
        "#ed1c24",
        "#2e3192",
        "#f7941d",
        "#00a651",
        "#92278f",
    )
    assert palette.scatter_edge == "#ffffff"


def test_pgl_zero_line_is_solid_black_at_1_6_pt():
    pk.use("pgl")
    (line,) = pk.zero_line(Figure().subplots())
    assert line.get_color() == "#000000"
    assert line.get_linewidth() == 1.6
    assert line.get_linestyle() == "-"


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


def test_lilaq_font_is_the_10_pt_cut():
    family = pk.rc_params("lilaq")["font.serif"][0]
    try:
        path = findfont(FontProperties(family=family), fallback_to_default=False)
    except ValueError:
        pytest.skip(f"{family} is not installed")
    assert Path(path).name == "NewCM10-Regular.otf"
