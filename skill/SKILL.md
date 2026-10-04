---
name: poikilos
description: Style matplotlib and seaborn figures with the poikilos package (themes plain, plain-dark, rose-pine, rose-pine-moon, rose-pine-dawn, lilaq, lilaq-moon) and its helpers despine, label_points and save_figure. Use whenever you create, edit, review or migrate any matplotlib or seaborn figure or plotting code, including spines, ticks, fonts, colors, DPI, legends, labelled scatter plots and figure export, even if the user never names poikilos. Also use when a project imports matplotlib_rosepine or a copied style.py with apply_style().
---

# poikilos

Every figure uses a poikilos theme. A theme is a look (fonts, spines, ticks,
sizes) plus a palette (colors). The package also has the three helpers that
finish a figure: `despine`, `label_points` and `save_figure`.

```bash
uv add "poikilos[labels] @ git+https://github.com/ramirc0/poikilos"
```

The `labels` extra pulls in adjustText for `label_points`. Needs Python 3.11 or
later and matplotlib 3.11 or later.

## Rules

1. **Apply a theme with `pk.use(theme)` before drawing.** Keep the theme the
   project already uses. Otherwise pick `plain` for papers and reports. `use()`
   resets every style rcParam first, so it can run before or after importing
   pyplot. Anything set by hand before it is lost.
2. **Save with `pk.save_figure(fig, path)`.** It writes SVG and PNG side by
   side. Never set `savefig.format`. The SVG keeps text as text
   (`svg.fonttype: none`), and the PNG is for viewers without the fonts.
3. **Keep constrained layout.** The themes turn it on. Never call
   `tight_layout()`, which fights it.
4. **Do not style per script.** Style settings outside the theme (fonts,
   sizes, colors, tick and spine looks) go in `pk.use(theme, rc={...})`, so
   every figure in a project stays consistent and one line shows what
   deviates. If many scripts need the same override, change the theme in
   poikilos instead. Choices that depend on the data are fine per axes:
   legend placement (`ax.legend(loc="upper left")` when the data fills the
   default corner), `figsize`, limits, titles and labels.
5. **Plain look: call `pk.despine(ax)` on every axes**, after everything is
   drawn on it. It is what makes the plain look: spines offset by 10 pt and
   trimmed to the end ticks. See [references/plain.md](references/plain.md)
   for categorical axes.
6. **Label scatter points with `pk.label_points(ax, points, labels)`**, never
   with `ax.annotate` or `ax.text` per point. Fixed offsets collide as soon as
   two points sit close together. Call it last on the figure. With several
   labelled panels, finish every panel first (drawing, `despine`, titles,
   legends, suptitle), then call `label_points` once per panel.
7. **lilaq look: apply the tick and dot recipes** from
   [references/lilaq.md](references/lilaq.md).

## Themes

| Theme | Look | Use for |
| --- | --- | --- |
| `plain` | plain | default; matplotlib colors (tab10) on white |
| `plain-dark` | plain | dark slides; tab10 on `#242424` |
| `rose-pine-dawn` | plain | Rosé Pine, light |
| `rose-pine`, `rose-pine-moon` | plain | Rosé Pine, dark |
| `lilaq` | lilaq | figures next to Typst documents that use lilaq |
| `lilaq-moon` | lilaq | lilaq's dark moon theme |

`palette=` mixes them: `pk.use("lilaq", palette="rose-pine-dawn")` is the lilaq
look in Rosé Pine Dawn colors.

## API

```python
import poikilos as pk

pk.use(theme, *, palette=None, rc=None)      # apply globally
pk.context(theme, *, palette=None, rc=None)  # with-block; restores rcParams on exit
pk.rc_params(theme, palette=None)            # dict, applies nothing
pk.THEMES                                    # name -> (look, palette)
pk.PALETTES["rose-pine-dawn"].colors["love"] # palette colors as hex
pk.PALETTES["plain"].cycle                   # cycle colors, in order
pk.despine(ax, categorical_x=False, categorical_y=False)
pk.label_points(ax, points, labels, **text_kwargs)
pk.save_figure(fig, path, **savefig_kwargs)  # -> [svg path, png path]
```

Unknown theme or palette names raise `ValueError` with the valid names. A bad
key in `rc` raises `KeyError` before anything changes.

Take colors from `pk.PALETTES` rather than copying hex values. A palette's
`colors` holds its own names (Rosé Pine's `love`, `pine`, ...). Its roles
(`background`, `foreground`, `frame`, `ticks`, `grid`, `legend_edge`,
`median`, `mean`) and `cycle` are the colors the theme applies.

## Example

```python
import matplotlib.pyplot as plt
import poikilos as pk

pk.use("plain")

fig, ax = plt.subplots(figsize=(4, 3))
ax.bar(df["condition"], df["value"])
ax.set_ylabel("expression")
pk.despine(ax, categorical_x=True)
pk.save_figure(fig, "results/expression")

fig, ax = plt.subplots(figsize=(4, 4))
points = ax.scatter(df["x"], df["y"])
ax.set(xlabel="x", ylabel="y", title="Cell lines")
pk.despine(ax)
pk.label_points(ax, points, df["name"], fontsize=8)  # last: after despine and titles
pk.save_figure(fig, "results/labelled")
```

`save_figure` accepts the path with or without `.svg` or `.png`, so a Snakemake
rule can pass its declared SVG output. Other dots stay in the name.

For one figure in another theme, wrap it in `with pk.context("lilaq"):` and save
inside the block. matplotlib reads `savefig.dpi` when saving.

## Gotchas

- Themes set `savefig.dpi: 300` and leave `figure.dpi` at 100. Saved files are
  300 dpi. `fig.dpi` reads 100 unless you pass `dpi=`.
- poikilos never sets the backend. A batch script on a machine with a display
  may need `matplotlib.use("Agg")` before importing pyplot.
- seaborn: `sns.set_theme()` resets rcParams too. Call it before `pk.use()`, or
  not at all.
- Do not force `pdf.fonttype: 42` with the default fonts. They are CFF
  (`.otf`), and Type 42 is for TrueType. See [references/fonts.md](references/fonts.md).
- For a multi-page PDF of plots, collect the figures with
  `matplotlib.backends.backend_pdf.PdfPages`, one `pdf.savefig(fig)` per page,
  next to the per-figure `save_figure` call. Use Typst when the report needs
  text pages or tables.

## References

- [references/plain.md](references/plain.md): `despine` per plot type and why
  it beats `sns.despine(trim=True)`, plus `label_points` details. Read it when
  using the plain look.
- [references/lilaq.md](references/lilaq.md): what the lilaq look reproduces
  and the per-axes recipes. Read it when using `lilaq` or `lilaq-moon`.
- [references/fonts.md](references/fonts.md): font chains, installing New
  Computer Modern, checking that a font resolves, PDF and SVG font output.
- [references/migration.md](references/migration.md): moving a project from
  `matplotlib_rosepine` or a copied `style.py` to poikilos.
