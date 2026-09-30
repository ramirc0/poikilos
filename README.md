# matplotlib-rosepine

[Rosé Pine](https://rosepinetheme.com) styles for matplotlib, in all three
variants (`rose-pine`, `rose-pine-moon`, `rose-pine-dawn`).

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

`apply_style()` sets the Agg backend and applies the style. Importing the
package alone registers every style, so you can select one by name instead:

```python
import matplotlib_rosepine        # noqa: F401  (registers styles)
import matplotlib.pyplot as plt
plt.style.use("rose-pine-moon")
```

Helpers: `rp.VARIANTS`, `rp.style_path(variant)`, `rp.register()`.

### Fonts

No font ships with the package. Matplotlib uses the first installed family
from: Anthropic Sans Text, Google Sans Flex, Arimo, Arial, DejaVu Sans.

The styles use `svg.fonttype: none`, so SVGs reference the font by name rather
than embedding it; a viewer needs the same font installed to render it. PNGs
embed the glyphs and always render correctly.

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

MIT (see `LICENSE`).
