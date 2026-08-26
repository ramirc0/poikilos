# matplotlib-rosepine

[Rosé Pine](https://rosepinetheme.com) styles for matplotlib, in all three
variants (`rose-pine`, `rose-pine-moon`, `rose-pine-dawn`), with the
[Google Sans Flex](https://fonts.google.com/specimen/Google+Sans+Flex) font
vendored so plots look the same everywhere.

![rose-pine](assets/preview-rose-pine.png)

## Install

```bash
uv add matplotlib-rosepine        # or: uv pip install matplotlib-rosepine
```

From a local checkout:

```bash
uv pip install .
```

## Usage

```python
import matplotlib_rosepine as rp
rp.apply_style("rose-pine")       # rose-pine | rose-pine-moon | rose-pine-dawn

import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([0, 1, 2], [0, 1, 0])
fig.savefig("plot.svg")
```

`apply_style()` sets the Agg backend, registers the vendored font, and applies
the style. Importing the package alone also registers everything, so you can
select a style by name instead:

```python
import matplotlib_rosepine        # noqa: F401  (registers styles + font)
import matplotlib.pyplot as plt
plt.style.use("rose-pine-moon")
```

Helpers: `rp.VARIANTS`, `rp.style_path(variant)`, `rp.register()`,
`rp.register_fonts()`.

### Fonts in saved figures

The styles use `svg.fonttype: none`, so SVGs reference the font by name rather
than embedding it; a viewer needs Google Sans Flex installed to render it. PNGs
embed the glyphs and always render correctly. To install the font system-wide:

```bash
cp src/matplotlib_rosepine/fonts/*.ttf ~/.local/share/fonts/ && fc-cache -f
```

## Development

Styles are generated from matplotlib's default rc with
[rose-pine-bloom](https://github.com/rose-pine/rose-pine-bloom):

```bash
python scripts/build_template.py   # default rc -> template.mplstyle
rose-pine-bloom -t template.mplstyle -o src/matplotlib_rosepine/styles -f hex-ns
python scripts/preview.py          # regenerate assets/preview-*.{svg,png}
```

`-f hex-ns` is required: matplotlib only honors `#` inside double quotes, so
`prop_cycle` needs bare hex.

## License

MIT (see `LICENSE`). The vendored Google Sans Flex font is licensed separately
under the SIL Open Font License 1.1 (`src/matplotlib_rosepine/fonts/OFL.txt`).
