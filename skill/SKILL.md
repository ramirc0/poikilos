---
name: matplotlib-style
description: Apply the project's matplotlib figure style. Use when creating, editing or reviewing any matplotlib or seaborn figure, including axis spines, ticks, fonts, DPI and figure export.
---

# Matplotlib Style

Every figure MUST use this style. Call `apply_style()` before importing `pyplot`.

## Rules

1. `apply_style()` MUST run before `import matplotlib.pyplot`. The backend cannot change afterwards.
2. Figures MUST be saved as **both** SVG and PNG. Use `save_figure()`; do not set `savefig.format`.
3. Text in SVG MUST stay text (`svg.fonttype = "none"`), never paths.
4. The top and right spines MUST be removed on every axes.
5. Every axes MUST go through `despine()` after everything is drawn on it.
6. Layout MUST be constrained, never `tight_layout()`.
7. Figures MUST NOT be styled per-script. Change this skill instead.
8. Labelled scatter points MUST go through `label_points()`, never `ax.annotate` or `ax.text` per point.

## Spines and ticks

All ticks, major and minor, point inward. `apply_style()` sets this through `xtick.direction` and
`ytick.direction`, so it also covers colorbars.

`despine(ax)` offsets the left and bottom spines by 10 pt and trims them to the end ticks:

| Plot | Call | Result |
| --- | --- | --- |
| Default, scatter, line, histogram, hexbin | `despine(ax)` | left and bottom spines, offset and trimmed |
| Bar (categorical x) | `despine(ax, categorical_x=True)` | left spine only; no x spine or tick marks |
| Horizontal bar (categorical y) | `despine(ax, categorical_y=True)` | bottom spine only; no y spine or tick marks |
| Heatmap (both categorical) | `despine(ax, categorical_x=True, categorical_y=True)` | no spines or tick marks |

Bar charts and heatmaps carry categories in the tick labels, so that axis needs no spine.
Give a heatmap colorbar its own `subplot_mosaic` cell; `fig.colorbar(ax=...)` sizes it
from the heatmap, so a heatmap with few rows gets a colorbar too small for its labels.

### Why `despine()` and not `sns.despine(trim=True)`

`trim` cuts a spine at the outermost ticks inside the axis limits. Two things go wrong:

- **Trim too aggressive.** If the data runs past the last tick, the spine ends short of the data.
- **Axis too wide.** Matplotlib's default margins push the limits past a tick, so widening to the
  next tick adds a whole empty step (for example -20 on an axis whose data starts at 0).

`despine()` fixes both. It fits each continuous axis to its data with `margins(0)`, widens it to
the nearest ticks enclosing the data, fixes the ticks there, then offsets and trims. The spine
always spans the data and ends on a tick. When the locator has no tick beyond the data (date
axes), the data edge becomes the end tick, so the first and last dates are labelled. An edge
date one day from a locator tick can overlap its label; start the window on a locator tick
or widen the figure.

Data at the limits sits on the axes edge, and matplotlib clips every artist there, cutting markers
and line widths in half. When both axes were fitted to the data, `despine()` turns clipping off so
edge markers draw whole into the 10 pt offset. Explicit limits set before `despine()` keep clipping,
so zoomed or cropped data stays hidden. Markers wider than the offset can still reach titles or
tick labels.

Keep data edges on round numbers where you can. Integer histogram bins centred on whole numbers
put the first edge at -0.5, which widens the axis to the tick below 0. Start such bins at 0.

## Point labels

`label_points(ax, points, labels)` takes the collection `ax.scatter` returns and places each label
at its marker. [adjustText](https://github.com/Phlya/adjustText) then moves the labels apart and
off the markers' full extent, not just their centres, keeps a small gap between labels, and draws
a thin grey leader line back to each one. Fixed offsets such as `xytext=(4, 2)` overlap as soon as
two points sit close together.

Call it last, after `despine()` and every title, axis label, suptitle and legend on the figure.
adjustText places labels in pixel positions; anything added afterwards makes constrained layout
reshape the axes, which moves the labels back into each other. `label_points` settles the layout
before placing labels, so only later additions break this. Extra keyword arguments go to `ax.text`
(for example `fontsize=8`). The project environment needs `adjustText` installed.

adjustText sizes its steps in pixels with defaults tuned for screen resolution. At 300 dpi those
defaults stop pulling a label only when its anchor is within 2.4 pt of the marker centre, inside
the marker, so `label_points` converts them from points. It also pushes labels apart harder than
the default, which leaves near-identical labels stacked. Past about 10 labels per panel in a dense
cluster, adjustText cannot keep them readable; label only the points that matter, or use a
categorical plot with the names on an axis.

## Fonts

The fallback chain is ordered by preference. Matplotlib walks it until a family resolves:

1. `Anthropic Sans Text`
2. `Google Sans Flex`
3. `Arimo`
4. `Arial`
5. `DejaVu Sans`

Use the exact family names above. There is no family called `Anthropic Sans`; the installed families are `Anthropic Sans Text` (body) and `Anthropic Sans Display` (headings). Prefer `Text` for figures.

`Arimo` is metric-compatible with `Arial` and is the practical fallback on Linux, where `Arial` is usually absent. Keep `Arial` in the chain for macOS and Windows.

Because `svg.fonttype = "none"`, the SVG references fonts by name rather than embedding outlines. Anyone opening the SVG without these fonts sees a substitute. For figures leaving the project, either ship the PNG or set `svg.fonttype = "path"` for that export.

## Multi-page PDF

For a report of plots only, collect the same figures with
`matplotlib.backends.backend_pdf.PdfPages`, one `pdf.savefig(fig)` per page, beside the per-figure
`save_figure()` call. Use typst instead when the report needs text pages or tables.

## Reference implementation

`scripts/style.py` holds `apply_style()`, `despine()`, `label_points()` and `save_figure()`. Copy it into the project rather than importing across repositories.

```python
from style import apply_style, despine, label_points, save_figure

apply_style()

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(4, 3))
ax.bar(df["condition"], df["value"])
despine(ax, categorical_x=True)
save_figure(fig, "results/expression")

fig, ax = plt.subplots(figsize=(4, 3))
ax.hist(values, bins=bins)
despine(ax)
save_figure(fig, "results/distribution")

fig, ax = plt.subplots(figsize=(4, 4))
points = ax.scatter(df["x"], df["y"])
despine(ax)
label_points(ax, points, df["name"], fontsize=8)
save_figure(fig, "results/labelled")
```

`save_figure` writes `.svg` and `.png` beside each other. It takes the path with or without a
`.svg` or `.png` extension. A Snakemake rule can therefore pass its declared SVG output. Dots in
the stem are kept: `x.curve` gives `x.curve.svg` and `x.curve.png`.
`despine` imports seaborn inside the function, because importing seaborn loads `pyplot`.
