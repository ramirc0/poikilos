# The plain look

Used by `plain`, `plain-dark` and the three Rosé Pine themes. The look sets a
sans-serif font chain, removes the top and right spines, and points all ticks
inward, major and minor. The tick direction is an rcParam, so it covers
colorbars too. The rest of the look comes from `despine`.

## despine

`pk.despine(ax)` offsets the left and bottom spines by 10 pt and trims them to
the end ticks. Call it on every axes after everything is drawn on it.

| Plot | Call | Result |
| --- | --- | --- |
| Line, scatter, histogram, hexbin | `despine(ax)` | left and bottom spines, offset and trimmed |
| Bar (categorical x) | `despine(ax, categorical_x=True)` | left spine only; no x spine or tick marks |
| Horizontal bar (categorical y) | `despine(ax, categorical_y=True)` | bottom spine only; no y spine or tick marks |
| Heatmap (both categorical) | `despine(ax, categorical_x=True, categorical_y=True)` | no spines or tick marks |
| Boxplot, violin (categorical x) | `despine(ax, categorical_x=True)` | left spine only |

Bar charts and heatmaps carry their categories in the tick labels, so that axis
needs no spine. A categorical axis also loses its minor ticks. `despine` hides
the top and right tick marks too, so it works on a look that mirrors ticks.

Give a heatmap colorbar its own `subplot_mosaic` cell. `fig.colorbar(ax=...)`
sizes the bar from the heatmap, so a heatmap with few rows gets a colorbar too
small for its labels.

### Why not `sns.despine(trim=True)`

`trim` cuts a spine at the outermost ticks inside the axis limits. Two things go
wrong:

- **The trim goes too far.** If the data runs past the last tick, the spine
  ends short of the data.
- **The axis gets too wide.** matplotlib's default margins push the limits past
  a tick, so widening to the next tick adds a whole empty step. An axis whose
  data starts at 0 gets a -20.

`despine` fixes both. It fits each continuous axis to its data with
`margins(0)`, widens it to the nearest ticks enclosing the data, and fixes the
ticks there. Then it offsets and trims. The spine always spans the data and
ends on a tick.

When the locator has no tick beyond the data, as on date axes, the data edge
becomes the end tick. The first and last dates then get labels. An edge date one
day from a locator tick can overlap its label. Start the window on a locator
tick or widen the figure.

### Clipping

Data at the limits sits on the axes edge, where matplotlib clips each marker
and line width in half. When both axes were fitted to the data, `despine` turns
clipping off, so edge markers draw whole into the 10 pt offset. Lines without
data stay clipped. An empty line, such as the flier line of a boxplot with no
outliers, would otherwise pull constrained layout to the figure corner.

Explicit limits set before `despine` keep clipping on, so zoomed or cropped data
stays hidden. Markers wider than the offset can still reach titles or tick
labels.

Keep data edges on round numbers where you can. Integer histogram bins centred
on whole numbers put the first edge at -0.5, which widens the axis to the tick
below 0. Start such bins at 0.

## label_points

`pk.label_points(ax, points, labels)` takes the collection `ax.scatter` returns
and starts each label at its marker. [adjustText](https://github.com/Phlya/adjustText)
then moves the labels apart and off the markers' full extent, not just their
centres. It keeps a small gap between labels and draws a thin leader line back
to each marker, in the axes edge color.

Call it last, after `despine` and every title, axis label, suptitle and legend
on the figure. adjustText places labels in pixels. Anything added afterwards
makes constrained layout reshape the axes, which moves the labels back into
each other. Extra keyword arguments go to `ax.text`, for example `fontsize=8`.

adjustText sizes its steps in pixels, with defaults tuned for the screen. At
300 dpi those defaults pulled labels back onto their own markers, so
`label_points` converts them from points. It also pushes labels apart harder
than the default, which leaves near-identical labels stacked.

Past about 10 labels per panel in a dense cluster, adjustText cannot keep them
readable. Label only the points that matter, or use a categorical plot with the
names on an axis.
