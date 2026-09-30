# CLAUDE.md

Rosé Pine matplotlib styles (`rose-pine`, `rose-pine-moon`, `rose-pine-dawn`). Built with hatchling; managed with `uv` (`.venv/` holds the dev env).

## Commands

```bash
uv pip install -e .                 # local install
python scripts/build_template.py    # matplotlib default rc -> template.mplstyle
rose-pine-bloom -t template.mplstyle -o src/matplotlib_rosepine/styles -f hex-ns
python scripts/preview.py           # regenerate assets/preview-*.{svg,png}
uv run pytest                       # tests/test_style.py
```

No linter config.

## Architecture

- `src/matplotlib_rosepine/style.py` holds the whole public API: `VARIANTS`, `FORMATS`, `style_path`, `register`, `apply_style`, `despine`, `label_points`, `save_figure`.
- Styling follows the user's `matplotlib-style` skill. rc-level rules (font stack, no top/right spines, inward ticks, `svg.fonttype: none`, constrained layout) live in `FIXED_VALUES`; data-dependent rules live in the helpers. `savefig.format` MUST stay unset because `save_figure` writes SVG and PNG.
- `label_points` imports `adjustText` lazily; it ships as the optional `labels` extra.
- `__init__.py` calls `register()` on import, so importing the package adds all three styles to `mpl.style.library`.
- `apply_style()` also forces the Agg backend and resets to `default` before applying the style.

## Style generation pipeline

The `.mplstyle` files under `src/matplotlib_rosepine/styles/` are generated. You MUST NOT hand-edit them. To change the theme:

1. Edit `COLOR_TOKENS`, `CYCLE`, or `FIXED_VALUES` in `scripts/build_template.py`. The script exits with an error if any listed key is not set in the template.
2. Run `build_template.py`, `rose-pine-bloom`, and `preview.py` in order, then `uv run pytest`. Commit the template, styles, and previews together.

Gotchas:

- matplotlib's rc parser treats `#` as a comment unless it sits inside double quotes. Color values are written as `"#$role"`. `prop_cycle` entries use single-quoted bare hex (`'$role'`), so bloom MUST run with `-f hex-ns`.
- `build_template.py` copies the installed matplotlib's `matplotlibrc` verbatim, so the template tracks the matplotlib version in the env. Re-run it after upgrading matplotlib.
- Styles set `svg.fonttype: none`, so SVGs reference the font by name. They render correctly only where the resolved font is installed.
