# Fonts

poikilos ships no fonts. Each look names a fallback chain. matplotlib walks it
and uses the first family it finds. Every chain ends in a DejaVu family that
comes with matplotlib, so a missing font never fails. It falls back silently,
which is why checking matters.

## Chains

**plain** (`font.sans-serif`):

1. `Anthropic Sans Text`
2. `Google Sans Flex`
3. `Arimo`
4. `Arial`
5. `DejaVu Sans`

Use these exact family names. There is no family called `Anthropic Sans`. The
installed families are `Anthropic Sans Text` for body text and `Anthropic Sans
Display` for headings, and figures use `Text`. `Arimo` has Arial's metrics and
is the usual fallback on Linux, where Arial is rarely installed. `Arial` stays
in the chain for macOS and Windows.

**lilaq** (`font.serif`): `NewComputerModern`, then `DejaVu Serif`. Math uses
matplotlib's bundled Computer Modern (`mathtext.fontset: cm`).

**pgl** (`font.sans-serif`): `Arial`, `Arimo`, `DejaVu Sans`. All three are
TrueType, so `pdf.fonttype: 42` suits this chain.

## New Computer Modern

Typst calls it `New Computer Modern`. matplotlib names the family
`NewComputerModern`, with no spaces. The Typst name would fall back to DejaVu
Serif without a warning.

Get `newcomputermodern.zip` from [CTAN](https://ctan.org/pkg/newcomputermodern)
and install only these five files from its `otf/` folder:

- `NewCM10-Regular.otf`
- `NewCM10-Italic.otf`
- `NewCM10-Bold.otf`
- `NewCM10-BoldItalic.otf`
- `NewCMMath-Regular.otf`

These are the 10 pt cuts Typst uses. The zip has 41 fonts. `NewCM08-Regular`,
`NewCM10-Regular` and `NewCM10-Book` all register as `NewComputerModern`,
normal, weight 400, and matplotlib may pick any of them.

On Linux, put them in `~/.local/share/fonts/NewComputerModern/` and run
`fc-cache -f`.

## After installing a font

matplotlib caches its font list. Delete the cache so it rescans on the next
import:

```bash
rm "$(python -c 'import matplotlib; print(matplotlib.get_cachedir())')"/fontlist-*.json
```

Then check that the family resolves to the file you expect, without falling
back:

```python
from matplotlib.font_manager import FontProperties, findfont

findfont(FontProperties(family="NewComputerModern"), fallback_to_default=False)
# .../NewCM10-Regular.otf; raises ValueError if the family is missing
```

## Output formats

- **SVG.** Themes set `svg.fonttype: none`, so an SVG names its font instead of
  embedding outlines. A viewer without the font shows a substitute. For an SVG
  that leaves the project, ship the PNG next to it, or draw and save that
  figure inside `with pk.context(theme, rc={"svg.fonttype": "path"}):`.
- **PNG.** Glyphs are rasterized, so PNGs look the same everywhere.
- **PDF.** Themes leave `pdf.fonttype` at matplotlib's default, Type 3. Its
  text stays searchable, and `pdftotext` extracts it.
  `pdf.fonttype: 42` embeds TrueType and suits only TrueType fonts. Anthropic
  Sans Text and New Computer Modern are CFF (`.otf`) fonts, and Type 42 would
  write their CFF outlines into a stream meant for TrueType. Set
  `rc={"pdf.fonttype": 42}` only after switching to a TrueType font
  (`.ttf`), for example `rc={"font.sans-serif": ["Arimo"], "pdf.fonttype": 42}`.
