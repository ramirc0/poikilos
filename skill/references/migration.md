# Migrating to poikilos

Two kinds of projects predate poikilos:

- projects that depend on `matplotlib-rosepine` (import `matplotlib_rosepine`)
- projects with a copied `style.py` from the old `matplotlib-style` skill
  (`from style import apply_style, despine, ...`)

Both move to the same calls. Work through the sections that apply, then run the
checks at the end.

## 1. Dependency

Replace the old distribution in `pyproject.toml`. With uv:

```bash
uv remove matplotlib-rosepine
uv add "poikilos[labels] @ git+https://github.com/ramirc0/poikilos"
```

If the project pins the old repo in `[tool.uv.sources]`
(`matplotlib-rosepine = { git = ".../matplotlib-rosepine.git" }`), delete that
entry. `uv add` writes the new one. Drop `[labels]` if the project never calls
`label_points`. A copied `style.py` needed seaborn for `despine`. Remove seaborn
too if nothing else uses it.

poikilos needs Python 3.11 or later and matplotlib 3.11 or later. Raise
`requires-python` if it is lower.

## 2. Calls

| Before | After |
| --- | --- |
| `import matplotlib_rosepine as rp` | `import poikilos as pk` |
| `from matplotlib_rosepine import despine` | `from poikilos import despine` |
| `from style import apply_style, despine, label_points, save_figure` | `import poikilos as pk`, then delete `style.py` |
| `rp.apply_style("rose-pine-dawn")` | `pk.use("rose-pine-dawn")` |
| `apply_style()` from `style.py` | `pk.use("plain")` |
| `rp.VARIANTS` | `pk.THEMES` (7 themes, Rosé Pine and others) |
| `rp.style_path(v)` with `mpl.rc_params_from_file(...)` | `pk.rc_params(v)` |
| `rp.register()` and `plt.style.use("rose-pine")` | `pk.use("rose-pine")` |
| Rosé Pine hex values typed into the code | `pk.PALETTES["rose-pine-dawn"].colors["love"]` |
| `despine`, `label_points`, `save_figure` | same names and arguments under `pk.` |

Notes:

- **Import order no longer matters.** `apply_style()` had to run before
  importing pyplot. `pk.use()` works anywhere. Keep the call before any figure is
  created, and drop comments that explain the old ordering.
- **The backend.** `apply_style()` forced Agg, and `pk.use()` never touches the
  backend. A script that ran headless only because of that needs
  `matplotlib.use("Agg")` before importing pyplot, or `MPLBACKEND=Agg` in its
  environment. Most headless machines pick Agg on their own.
- **Theme lists.** Code that validated names against `rp.VARIANTS` can check
  `name in pk.THEMES`, or call `pk.use(name)` and let its `ValueError` speak. To
  keep a Rosé-Pine-only choice, filter: `[t for t in pk.THEMES if t.startswith("rose-pine")]`.
- **Reading settings from the style file.** `pk.rc_params(v)` returns a dict,
  for example `pk.rc_params("rose-pine-dawn")["font.sans-serif"]` for the font
  chain. Typst code that shares the plot fonts can keep reading it from there.
- **Copied palette values.** A dict of Rosé Pine hex values duplicates
  `pk.PALETTES[name].colors`. Replace it. Hex values typed into plotting calls,
  such as `color="#797593"`, are copies too. The palette's roles give the colors the
  theme applies: `.background`, `.foreground`, `.frame`, `.ticks`, `.grid`,
  `.cycle`. Colors the project chose itself, such as a nine-color batch list,
  can stay but should come from `.colors[...]` names.
- **Palette files.** The palettes are TOML files inside the package, at
  `importlib.resources.files("poikilos") / "palettes" / "<name>.toml"`. Typst can
  read them with `toml()` if the file sits inside the Typst root.

## 3. Behavior changes to check

- **DPI.** The old styles set `figure.dpi: 300`. Themes now set
  `savefig.dpi: 300` and leave `figure.dpi` at 100. Saved files keep 300 dpi,
  including `PdfPages.savefig`. A figure made with `dpi=150` used to save at
  150 dpi and now saves at 300. Pass `dpi=` to `save_figure` instead. Code
  that reads `fig.dpi` to compute pixel sizes now gets 100. Use
  `mpl.rcParams["savefig.dpi"]` for output pixels. A test that multiplies
  `fig.get_size_inches()` by `fig.dpi` still passes, but it now checks 100 dpi
  instead of the 300 dpi output.
- **`pdf.fonttype: 42`.** Projects often force it after applying the style,
  some to keep PDF text searchable. matplotlib's default Type 3 output is
  already searchable, and `pdftotext` extracts its text. With the default fonts
  Type 42 is wrong. They are CFF (`.otf`), and Type 42 is for TrueType. Remove
  the override, or pass a TrueType font with it:
  `pk.use(theme, rc={"font.sans-serif": ["Arimo"], "pdf.fonttype": 42})`. A
  logging tweak that silences fontTools subsetting for Type 42 can go too. See
  [fonts.md](fonts.md).
- **Other rcParams set after `apply_style()`.** Move them into
  `pk.use(theme, rc={...})`. Then a misspelled key raises `KeyError` instead of
  passing silently, and the next `use()` call cannot wipe them.
- **`save_figure` and dots.** `save_figure(fig, "x.curve")` now writes
  `x.curve.svg` and `x.curve.png`. `matplotlib_rosepine` wrote `x.svg` and
  `x.png`. Check callers that relied on the old names.
- **`despine` and boxplots.** A boxplot with no outliers no longer drags the
  layout to the figure corner. Workarounds for that, such as dropping empty
  flier lines by hand, can go.
- **Leader lines.** `label_points` draws leader lines in `axes.edgecolor`. The
  copied `style.py` drew them grey (`0.5`). On `plain` they are now black.
- **Title, legend and savefig colors** inherit from the palette's root colors.
  2D Rosé Pine figures render pixel-identical at the same save dpi.
- **3D panes** take the background color instead of matplotlib's translucent
  grey.

## 4. Checks

1. Search for leftovers. None of these should match:
   `rg -n "matplotlib_rosepine|matplotlib-rosepine|apply_style|style_path|rp\.VARIANTS|from style import"`
   Then list hard-coded colors with `rg -n "#[0-9a-fA-F]{6}"` and replace the
   Rosé Pine ones with palette names.
2. Run the project's tests. Fix tests that assume `fig.dpi == 300`, the old
   `save_figure` names or a forced `pdf.fonttype` of 42.
3. Regenerate the figures and compare them with the old ones. Expect the same
   look. Differences come from the DPI, font and 3D pane notes above.
4. Check that the theme's font resolves on the machine, as in
   [fonts.md](fonts.md).
