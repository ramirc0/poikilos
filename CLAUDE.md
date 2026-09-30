# CLAUDE.md

Rosé Pine matplotlib styles (`rose-pine`, `rose-pine-moon`, `rose-pine-dawn`) plus figure helpers. Built with hatchling; managed with `uv`.

## Commands

```bash
uv sync                                        # dev env (pytest, adjustText, numpy)
uv run pytest                                  # tests/test_style.py
uv run python scripts/build_template.py        # matplotlib default rc -> template.mplstyle
rose-pine-bloom -t template.mplstyle -o src/matplotlib_rosepine/styles -f hex-ns
uv run python scripts/preview.py               # regenerate assets/preview-*.{svg,png}
```

`rose-pine-bloom` is a Go binary on `PATH`, not a Python dependency. No linter config.

## Architecture

- `src/matplotlib_rosepine/style.py` holds the whole public API: `VARIANTS`, `style_path`, `register`, `apply_style`, `despine`, `label_points`, `save_figure`.
- `__init__.py` calls `register()` on import, adding all three styles to `mpl.style.library`.
- `apply_style()` forces the Agg backend, resets to `default`, then applies the style. It MUST run before `matplotlib.pyplot` is imported.
- No fonts ship with the package. The style sets `font.sans-serif` to a fallback chain resolved from system fonts.

## Relation to the `matplotlib-style` skill

Styling follows the user's `matplotlib-style` skill (`~/.claude/skills/matplotlib-style/`). Its `scripts/style.py` is the upstream for `despine`, `label_points`, `save_figure` and their tests. Deliberate deviations:

- `despine` sets spine visibility and `("outward", 10)` directly instead of calling `sns.despine`, so seaborn is not a dependency.
- `label_points` draws leader lines in `rcParams["axes.edgecolor"]` (Rosé Pine `muted`) instead of grey.
- `adjustText` is imported lazily and ships as the optional `labels` extra.

rc-level rules live in `FIXED_VALUES`; data-dependent rules live in the helpers. `savefig.format` MUST stay unset because `save_figure` writes both SVG and PNG.

## Style generation pipeline

The `.mplstyle` files under `src/matplotlib_rosepine/styles/` and `template.mplstyle` are generated. You MUST NOT hand-edit them. To change the theme:

1. Edit `COLOR_TOKENS`, `CYCLE`, or `FIXED_VALUES` in `scripts/build_template.py`. The script exits with an error if any listed key is not set in the template.
2. Run `build_template.py`, `rose-pine-bloom`, and `preview.py` in order, then `uv run pytest`. Commit template, styles, and previews together.

Gotchas:

- matplotlib's rc parser treats `#` as a comment unless it sits inside double quotes. Color values are written as `"#$role"`. `prop_cycle` entries use single-quoted bare hex (`'$role'`), so bloom MUST run with `-f hex-ns`.
- `build_template.py` copies the installed matplotlib's `matplotlibrc` verbatim, so the template tracks the matplotlib version in `.venv`. Re-run it after upgrading matplotlib and check the diff.
- Styles set `svg.fonttype: none`, so SVGs reference the font by name. Previews render with whatever font resolves on the machine that generates them.

## Tests

- `tests/test_style.py` calls `apply_style()` (variant `rose-pine`) at import, before importing pyplot. Tests share that global rc state.
- `test_style_file_sets_skill_rc` reads each `.mplstyle` directly, so it catches template or bloom regressions.
- `edge_marker_pixels` matches the drawn line's own color, not a fixed hex, so it survives palette changes.
