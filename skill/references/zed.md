# The zed look

Used by `zed`. It reproduces figures drawn in Adobe Illustrator at 1:1 and
printed as drawn. The values were measured from vector artwork and tuned until
a matplotlib render matched it within 0.1 pt.

## What the look sets

- Helvetica Neue. Tick labels 8 pt, axis labels, text and legends 10 pt,
  `supxlabel` and `supylabel` 12 pt. Titles are 12 pt Medium, figure titles
  14 pt Medium. Mathtext uses the same font, so `$p$` and `$n$` come out in
  Helvetica Neue Italic.
- Left and bottom spines at 0.75 pt. Ticks point in: major 5 pt, minor 3 pt,
  each 0.75 pt wide. Tick labels sit 2 pt from the spine.
- Data lines 0.5 pt with round caps. Dashes are 2 pt on, 1 pt off, whatever
  the line width.
- Markers 2 pt across. Scatter markers get a white edge.
- Filled box plots with a white 1.5 pt median, 0.5 pt whiskers and caps, and no
  outliers or outline.
- Error bars 0.5 pt with 4 pt caps. Legends without a frame. No grid.
- A figure size that gives a 150 pt square data area to one plot with a title
  and both axis labels.

The palette holds Illustrator's default CMYK swatches as Illustrator shows
them on screen. The cycle runs black, red, blue, orange, green, purple. Black
is `#231F20`, Illustrator's rendering of 100 % K. Use `zed["black"]` for it,
because matplotlib's `"black"` is `#000000`. Greys are named by their K
percentage: `k5`, `k10`, `k20`, `k40`, `k50`, `k70`, `k90`. `silver` is
`#BFBFBF`, for a control or background series.

## Recipes

```python
import numpy as np
from matplotlib.ticker import FixedLocator, FuncFormatter, StrMethodFormatter

import poikilos as pk

pk.use("zed")
zed = pk.PALETTES["zed"].colors
```

- **Spines.** Call `pk.despine(ax, offset=7.5)` on every axes, last. The
  7.5 pt offset is 1.5 times the major tick. Categorical axes take
  `categorical_x=True` or `categorical_y=True` as usual.
- **Scatter.** Pass colors with `c=` or `facecolors=`. `color=` sets the edge
  too and drops the white edge. matplotlib takes the scatter edge width from
  `lines.linewidth`, 0.5 pt here, so pass `linewidths=0.25`. Background points
  are often 1.5 pt with a 0.15 pt edge: `s=1.5**2, linewidths=0.15`.

```python
ax.scatter(x, y, c=zed["silver"], linewidths=0.25)
ax.scatter(x2, y2, facecolors="white", edgecolors=zed["black"], linewidths=0.25)
```

The second call draws open circles: white fill, edge in the series color.

- **Sparse tick labels.** A cumulative fraction gets ticks every 0.2 and labels
  only at the ends. Zero reads `0`, not `0.0`. Thousands get commas. A unit can
  sit on the last tick label.

```python
ax.set_yticks(np.linspace(0, 1, 6), ["0", "", "", "", "", "1"])
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}" if v else "0"))
ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,g}"))
ticks = [0, 5, 10, 15, 20]
ax.set_xticks(ticks, [*map(str, ticks[:-1]), "20%"])
```

- **Log axes.** Base 10 reads 1, 10, 100, 1,000. Base 2 reads ⅛ ¼ ½ 1 2 4 8.
  matplotlib draws no minor ticks on base 2, so place them. Label minor ticks,
  if at all, at 6 pt.

```python
ax.set_xscale("log", base=2)
fractions = {0.125: "⅛", 0.25: "¼", 0.5: "½"}
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fractions.get(v, f"{v:g}")))
ax.xaxis.set_minor_locator(FixedLocator([0.6, 0.7, 0.8, 0.9, 1.2, 1.4, 1.6, 1.8]))
ax.tick_params(which="minor", labelsize=6)
```

- **Direct labels.** Name each series in its own color next to the data
  instead of a legend. Write *n* and *p* in the text: `"$n$ = 1,024"`,
  `"KS test $p$ = 0.64"`.

```python
(line,) = ax.plot(x, y, color=zed["red"])
ax.text(x[-1], y[-1], " mutant", color=line.get_color(), va="center")
```

- **Box plots.** Thick boxes on a 12 pt pitch take `widths=0.67`. Color the
  box, whiskers and caps of each group alike. Horizontal boxes read top down.

```python
bp = ax.boxplot(data, orientation="horizontal", widths=0.67)
for i, name in enumerate(["black", "red", "blue"]):
    bp["boxes"][i].set_facecolor(zed[name])
    for part in bp["whiskers"][2 * i : 2 * i + 2] + bp["caps"][2 * i : 2 * i + 2]:
        part.set_color(zed[name])
ax.invert_yaxis()
pk.despine(ax, categorical_y=True, offset=7.5)
```

- **Distributions.** `ax.ecdf(values)` draws the 0.5 pt step. Draw a control in
  `silver` under a test set in `red`. Bars take `width=0.67` and no outline.
  Overlaid histograms use `histtype="step"`.
- **Reference lines.** y = x in solid black, fold-change lines dashed, a grey
  crosshair at 1. `pk.zero_line(ax)` draws a 0.5 pt black line at zero.

```python
ax.axline((1, 1), (2, 2), color=zed["black"])
ax.axline((1, 2), (2, 4), color=zed["black"], linestyle="--")
ax.axhline(1, color=zed["k20"], linewidth=0.25)
```

- **Bands.** Shade rows to highlight with `k10`, or group categories on `k5`:
  `ax.axhspan(1.5, 2.5, color=zed["k10"], linewidth=0, zorder=0)`.
- **Panel letters.** Bold, uppercase, 20 pt:
  `ax.text(-0.3, 1.05, "A", transform=ax.transAxes, size=20, weight="bold", va="bottom")`.
- **Nucleotides.** A `amber`, C `emerald`, G `azure`, U `magenta`.
- **Illustrator.** `save_figure` writes SVG with live text, which Illustrator
  opens as editable type.

## Known differences

- The default scatter edge is 0.5 pt, since matplotlib ties it to the line
  width. Pass `linewidths=0.25`.
- Mathtext scripts are 70 % of the text size. Illustrator's are 58.3 %.
- Spines end in butt caps. Illustrator's projecting caps reach 0.375 pt past the
  end ticks.
- The y-axis label sits about 1 pt closer to its tick labels than in the
  source. matplotlib has one label pad for both axes, set for the x axis.
- Without Helvetica Neue, Nimbus Sans or Arial stands in. Titles then lose the
  Medium weight.
