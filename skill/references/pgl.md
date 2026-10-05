# The pgl look

Used by `pgl`. It follows the figures of the Programmable Genomics Laboratory
(the Schreiber lab), such as those in the ledidi paper. Those figures are
seaborn's `whitegrid` style with every spine removed.

## What the look sets

- Arial at matplotlib's default sizes. Arimo has Arial's metrics and stands in
  on Linux.
- No spines and no tick marks. The grid takes their place. Tick labels stay,
  7 pt from the data area.
- A dashed `#cccccc` grid on both axes, below the data.
- Text and tick labels in seaborn's `#262626`, and tab10 as the cycle.
- Legends without a frame.

The frame color is black although no spine draws. `zero_line`, colorbar
outlines and the leader lines of `label_points` use it. Colorbars keep their
tick marks, as in seaborn.

Do not call `despine` on this look. It turns the left and bottom spines back
on. `label_points` works on any look.

## Recipes

```python
ax.xaxis.grid(False)  # categorical x; seaborn's categorical plots already do this
pk.zero_line(ax)  # values change sign; axis="x" for x = 0
```

- **Categorical axes.** Bar charts and boxplots keep only the grid on the
  value axis. Call `ax.xaxis.grid(False)` for vertical bars and
  `ax.yaxis.grid(False)` for horizontal ones. seaborn's `barplot`, `boxplot`
  and other categorical plots do this already. Plain `ax.bar` does not.
- **Heatmaps.** Call `ax.grid(False)`, or the grid draws over the image.
- **Zero line.** When values change sign, `pk.zero_line(ax)` draws y = 0 in
  solid black at twice the grid width, 1.6 pt. Pass `axis="x"` for x = 0. The
  limits widen to include zero.
- **Signed tick labels.** On a scale that runs from − to +, sign the positive
  labels too:

```python
from matplotlib.ticker import ScalarFormatter


class SignedFormatter(ScalarFormatter):
    def __call__(self, x, pos=None):
        text = super().__call__(x, pos)
        return f"+{text}" if x > 0 and text.strip("0.") else text


ax.xaxis.set_major_formatter(SignedFormatter())
```

It keeps matplotlib's formatting, so `+1.50` sits next to `−0.50`. A
`"{:+g}"` format would drop the trailing zeros. Zero stays unsigned.

## Known differences

The look leaves out two habits of some lab figures. Add them per call:

- White gaps between histogram bars: `ax.hist(..., edgecolor="white")`.
- Boxplot fliers drawn as `x`: `ax.boxplot(..., flierprops={"marker": "x"})`.
