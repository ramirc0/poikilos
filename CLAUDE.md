# CLAUDE.md

`poikilos`: matplotlib themes (look + palette) plus the helpers `despine`, `label_points`, `save_figure`. Built with hatchling, managed with `uv`. Was `matplotlib-rosepine` up to tag `v0.2.0`.

## Commands

```bash
uv sync
uv run pytest                          # includes image tests (marker `images`)
uv run ruff check && uv run ruff format --check
uv run python scripts/gallery.py       # assets/gallery/<theme>.{svg,png}, prints contrast
uv run python scripts/lilaq_parity.py  # build/parity/, lilaq 0.6.0 via typst-py vs the lilaq looks
```

Ruff is pinned in the dev group and has no config. CI (`.github/workflows/ci.yml`) runs ruff, pytest, a wheel content check, and pytest at `--resolution lowest-direct`.

## Composition

- `src/poikilos/themes.py` holds the theme API. `helpers.py` holds the helpers. `__init__.py` only re-exports. Importing MUST NOT change rcParams.
- `rc_params()` merges `base.mplstyle`, then `looks/<look>.mplstyle`, then the palette's colors. `use()` validates with `mpl.RcParams` first, then calls `style.use(["default", params])`. That keeps the backend.
- Looks MUST NOT set a palette key or `axes.prop_cycle`. A palette sets root color keys only (`_ROLES` in `themes.py`). Inheriting keys such as `legend.facecolor: inherit` and `axes.titlecolor: auto` then follow them.
- `savefig.format` MUST stay unset because `save_figure` writes SVG and PNG. `figure.dpi` stays at matplotlib's 100; the base sets `savefig.dpi`.
- Per-axes behavior (lilaq tick steps, dots on lines, `despine`) is a documented recipe, not a look setting.

## Adding a theme

1. New palette: add `palettes/<name>.toml` (`[colors]` may be empty; `[roles]` names every role) and a `THEMES` entry.
2. New look: add `looks/<name>.mplstyle`. Put any per-axes code in the README and skill recipes.
3. Run `uv run pytest`. It writes the missing baseline in `tests/baseline/<mpl>/` and fails once. Read the image, then rerun.
4. Run `scripts/gallery.py`. Add the image to the README, add a CHANGELOG line (minor bump), update the `THEMES` snapshot in `test_public_api` and the skill's theme table.

## Gotchas

- matplotlib only logs a bad key or value in a style file, then skips it. `test_style_file_loads_without_warnings` turns that into a failure.
- `#` starts a comment in `.mplstyle` files unless quoted. Colors belong in the TOML palettes, not in looks.
- Use `from matplotlib import style`. Bare `mpl.style` fails unless something imported `matplotlib.style`.
- matplotlib names New Computer Modern `NewComputerModern`. The 8 pt, 10 pt and Book cuts share family and weight, so install only the 10 pt cuts. `test_lilaq_font_is_the_10_pt_cut` checks this and skips without the font.
- `lines.markeredgewidth: 0` hides errorbar caps, since caps are markers.
- Image baselines pin DejaVu fonts and are tied to one matplotlib minor version. The tests skip on another version.
- `tests/conftest.py` sets Agg and wraps every test in `mpl.rc_context()`.
- `ruff format` also formats Python blocks in Markdown, and CI checks them.

## References

- rc keys and defaults: matplotlib's [default `matplotlibrc`](https://matplotlib.org/stable/users/explain/customizing.html#the-default-matplotlibrc-file). For the installed version's copy, run `uv run python -c "import matplotlib; print(matplotlib.matplotlib_fname())"`.
- lilaq: source in `~/Git_Repos/lilaq`, target `@preview/lilaq:0.6.0`. The doc comments' defaults are stale. Read the elembic `fields:` instead.
- Rosé Pine palette: https://rosepinetheme.com/palette/ingredients/
