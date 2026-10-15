# Changelog

Versions follow these rules:

- A new theme, palette or look is a minor release.
- A visual change to an existing theme is a minor release. It comes with new
  image baselines and a line here.
- Renaming or removing a theme, or any public name, is a major release.

## 0.1.0 (unreleased)

`matplotlib-rosepine` 0.2.0 is now `poikilos`. The version restarts at 0.1.0.
The distribution and the import package are both `poikilos`.

### Added

- Themes `plain`, `plain-dark`, `lilaq`, `lilaq-moon` and `pgl`, next to the
  three Rosé Pine themes.
- `use(theme, *, palette=None, rc=None)`, `context(...)` and `rc_params(...)`.
  Any look takes any palette, and `rc` overrides any rcParam.
- `PALETTES`, with each palette's colors as hex, and `THEMES`.
- `zero_line(ax, axis="y")` draws a bold line at zero, for values that change
  sign.
- `label_points(..., offsets=[(dx, dy), ...])` places labels at fixed offsets
  in points, without adjustText. `leader=False` drops the leader lines.
- `save_figure(..., formats=("pdf", "png"))` picks the formats to write.
- `save_figure` writes SVG and PDF files without a creation date. The themes
  fix `svg.hashsalt`. Reruns write the same bytes.

### Changed

| `matplotlib_rosepine` 0.2.0 | `poikilos` 0.1.0 |
| --- | --- |
| `import matplotlib_rosepine as rp` | `import poikilos as pk` |
| `rp.apply_style(v)` before importing pyplot | `pk.use(v)`, before or after importing pyplot |
| `rp.style_path(v)` | `pk.rc_params(v)` returns the settings as a dict |
| `rp.VARIANTS` | `pk.THEMES` (now 8 themes) |
| `rp.register()`, `plt.style.use("rose-pine")` | removed; use `pk.use("rose-pine")` |
| Rosé Pine hex values copied by hand | `pk.PALETTES["rose-pine-dawn"].colors["love"]` |

- `use()` never sets the backend. `apply_style()` forced Agg.
- Importing the package no longer registers styles or changes rcParams.
- The themes set `savefig.dpi: 300` instead of `figure.dpi: 300`. Saved files
  keep their resolution. Figures on screen and in notebooks use matplotlib's
  100 dpi, and `fig.dpi` reads 100 unless you pass `dpi=`.
- A figure's own dpi no longer sets the saved resolution. `plt.figure(dpi=150)`
  used to save at 150 dpi and now saves at 300. Pass `dpi=` to `save_figure`
  to change it.
- As before, no theme sets `pdf.fonttype`, so PDFs use matplotlib's Type 3 fonts.
  `rc={"pdf.fonttype": 42}` gives TrueType. The default fonts are CFF, and with
  them it writes a PDF that breaks the spec.
- `despine` hides top and right tick marks, so it works on looks that mirror
  ticks. On a categorical axis it hides minor ticks too.
- `despine` leaves lines without data clipped, such as the flier line of a
  boxplot with no outliers. Unclipped, it pulled constrained layout to the
  figure corner.
- `label_points` runs a fixed 1000 adjustText iterations instead of adjustText's
  1 s time limit. The same figure with the same fonts now gets the same labels
  on any machine. Markers push labels away twice as hard as adjustText's
  default.
- `label_points` draws each label in a rounded box with the legend frame's
  face. The box outline and the leader line to the marker share one stroke
  in the axes edge color. adjustText keeps the boxes apart and off the
  markers. `bbox=None` gives bare labels.
- `save_figure` keeps dots in the stem: `x.curve` gives `x.curve.svg` and
  `x.curve.png`. It used to write `x.svg` and `x.png`.
- Title, legend label, legend face and `savefig` face colors now inherit from
  the palette's root colors instead of repeating them. 2D Rosé Pine figures
  render pixel-identical at the same save dpi.
- 3D panes take the background color instead of matplotlib's translucent grey.
- Needs Python 3.11 and matplotlib 3.11.

### Removed

- `template.mplstyle`, the generated `.mplstyle` files and the rose-pine-bloom
  step. Palettes are TOML files now.

### Fixed

- `despine` raised `TypeError` on Python 3.11 with numpy 2.3 or later.
- `despine` keeps clipping on when a log axis leaves out values at or below 0,
  such as the base of each bar. Unclipped, log bar charts collapsed constrained
  layout and lost tick labels.
- `despine` unclips every panel of shared axes, such as seaborn facets. Only
  the first panel used to draw edge markers whole. Explicit limits that hold
  all the data now unclip too.
- `despine` picks ticks for the axes size after layout. It picked them before
  layout, so an axes that layout shrank, such as one beside long category
  names, kept too many ticks and their labels overlapped. Axes that layout
  resizes can get a different tick step.
- `despine` fixes the limits of a categorical axis. A twin drawn after
  `despine` refitted them with its own margins and moved the bars off the
  spine.
- `despine` no longer offsets a categorical axis. Its labels sat 10 pt farther
  from the bars or cells than the tick padding.
- `despine` keeps styling set on tick labels, such as rotation. Moving the
  spines used to reset rotated labels to horizontal. Long category names then
  overlapped.
