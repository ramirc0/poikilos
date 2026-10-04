# The lilaq look

Used by `lilaq` and `lilaq-moon`. It reproduces the diagrams of the Typst
package [lilaq](https://lilaq.org), version 0.6.0, so matplotlib figures can
sit next to lilaq figures in a Typst document. It was tuned side by side
against lilaq renders. The repository's `scripts/lilaq_parity.py` redoes that
comparison.

## What the look sets

- New Computer Modern at 11 pt for all text, the font Typst documents usually
  use. Math uses matplotlib's Computer Modern.
- A full box: all four spines at 0.5 pt, ticks pointing in on all four sides,
  labels only on the bottom and left. Minor ticks are on: 4 between majors on
  steps of 1 or 5, 3 on steps of 2, as in lilaq.
- A light grid at major ticks, below the data.
- Lines 0.7 pt wide. Markers 2.6 pt across, the size of lilaq's dots, which also
  sets the default scatter size.
- Legend in the upper right, 2 pt from the corner, with a 0.5 pt frame and
  tight rows.
- Title at text size. Error bar caps 2.5 pt wide.
- A shared exponent such as ×10³ once tick values reach 1000. Small values get
  one from 0.0001 down. lilaq derives the exponent from the tick step, so the
  two differ in edge cases.
- A figure size that gives lilaq's 6 × 4 cm data area for a plot with a title
  and both axis labels. rcParams cannot fix the data area itself, so a plot
  without labels gets a larger one. Leave out `figsize` for a single plot, so
  it matches lilaq figures in the same document. Pass it only for several
  panels.

`lilaq-moon` uses lilaq's moon colors on `#242424`, with white text, spines and
ticks.

Do not call `despine` on this look. lilaq draws the full box, and `despine`
removes it. `label_points` works on any look.

## Recipes

Two lilaq habits need code per axes. They are not in the look on purpose.

```python
from matplotlib.ticker import MaxNLocator, NullLocator

ax.plot(x, y, marker="o")  # lilaq puts a dot on every data point of a line
for axis in (ax.xaxis, ax.yaxis):
    axis.set_major_locator(MaxNLocator(7, steps=[1, 2, 5, 10]))
```

- **Dots on lines.** Pass `marker="o"` to `plot` and `errorbar`. Leave it off
  for dense lines with hundreds of points. A marker in `axes.prop_cycle` would
  make `plot(color="k")` use up a cycle slot and bead every dense line. seaborn
  would also apply it unevenly. `scatterplot` and `pointplot` drop it.
  `lineplot` keeps it but leaves it out of the legend, and without `hue` takes
  the marker from the wrong cycle slot.
- **Tick steps.** lilaq rounds the step to 1, 2 or 5. matplotlib's default
  locator also allows 2.5. lilaq aims for one tick per 3.3 em of x axis and per
  2 em of y axis, about five ticks on its 6 × 4 cm plot. At that size
  `MaxNLocator(7, steps=[1, 2, 5, 10])` switches steps at nearly the same data
  ranges as lilaq. Set it on every continuous axis.
- **Categorical axes.** Bars, boxplots and heatmaps should not get minor ticks.
  Set `axis.set_minor_locator(NullLocator())` on the categorical axis instead
  of the `MaxNLocator`. Heatmaps also need `ax.grid(False)`, or the grid draws
  over the image.

matplotlib's `scatter` takes colors from its own cycle, separate from `plot`.
lilaq shares one cycle. Pass `color="C1"` and so on when a scatter and a line in
one axes must differ.

## Known differences

- lilaq rounds the legend corners at 1.5 pt. matplotlib's rounding follows the
  legend padding.
- lilaq-moon's legend fill is translucent black. The poikilos legend uses the
  background color.
- lilaq scales the tick count with the axis length, while `nbins=7` stays
  fixed. Axes larger or smaller than the default get a different count than in
  lilaq. Near a switch point the two can pick different steps even at the
  default size.
