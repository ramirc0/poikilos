# CLAUDE.md

Rosé Pine matplotlib styles (`rose-pine`, `rose-pine-moon`, `rose-pine-dawn`) packaged with a vendored Google Sans Flex font. Built with hatchling; managed with `uv` (`.venv/` holds the dev env).

## Commands

```bash
uv pip install -e .                 # local install
python scripts/build_template.py    # matplotlib default rc -> template.mplstyle
rose-pine-bloom -t template.mplstyle -o src/matplotlib_rosepine/styles -f hex-ns
python scripts/preview.py           # regenerate assets/preview-*.{svg,png}
```

There is no test suite or linter config.

## Architecture

- `src/matplotlib_rosepine/style.py` holds the whole public API: `VARIANTS`, `style_path`, `register_fonts`, `register`, `apply_style`.
- `__init__.py` calls `register()` on import, so importing the package adds the font and all three styles to `mpl.style.library`.
- `apply_style()` also forces the Agg backend and resets to `default` before applying the style.

## Style generation pipeline

The `.mplstyle` files under `src/matplotlib_rosepine/styles/` are generated. You MUST NOT hand-edit them. To change the theme:

1. Edit `COLOR_TOKENS`, `CYCLE`, or `FIXED_VALUES` in `scripts/build_template.py`.
2. Run the three commands above in order. Commit the template, styles, and previews together.

Gotchas:

- matplotlib's rc parser treats `#` as a comment unless it sits inside double quotes. Color values are written as `"#$role"`. `prop_cycle` entries use single-quoted bare hex (`'$role'`), so bloom MUST run with `-f hex-ns`.
- `build_template.py` copies the installed matplotlib's `matplotlibrc` verbatim, so the template tracks the matplotlib version in the env. Re-run it after upgrading matplotlib.
- Styles set `svg.fonttype: none`, so SVGs reference the font by name. They render correctly only where Google Sans Flex is installed.
