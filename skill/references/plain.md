# The plain look

Used by `plain`, `plain-dark` and the three Rosé Pine themes. The look sets a
sans-serif font chain, removes the top and right spines, and points all ticks
inward, major and minor. The tick direction is an rcParam, so it covers
colorbars too. The rest of the look comes from `despine`.

## despine

`pk.despine(ax)` offsets the left and bottom spines by 10 pt and trims them to
the end ticks. Call it on every axes after everything on the figure is drawn,
titles and legends included. It lays out the figure first, so the ticks fit the
axes size after layout.

| Plot | Call | Result |
| --- | --- | --- |
| Line, scatter, histogram, hexbin | `despine(ax)` | left and bottom spines, offset and trimmed |
| Bar (categorical x) | `despine(ax, categorical_x=True)` | left spine only; no x spine or tick marks |
| Horizontal bar (categorical y) | `despine(ax, categorical_y=True)` | bottom spine only; no y spine or tick marks |
| Heatmap (both categorical) | `despine(ax, categorical_x=True, categorical_y=True)` | no spines or tick marks |
| Boxplot, violin (categorical x) | `despine(ax, categorical_x=True)` | left spine only |

Bar charts and heatmaps carry their categories in the tick labels, so that axis
needs no spine. Its labels get no offset and sit by the bars or cells. A
categorical axis also loses its minor ticks. `despine` hides
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
and line width in half. When the limits hold all the data, `despine` turns
clipping off, so edge markers draw whole into the 10 pt offset. This holds on
shared axes and seaborn facets too. Lines without data stay clipped. An empty
line, such as the flier line of a boxplot with no outliers, would otherwise
pull constrained layout to the figure corner.

Limits that cut data off keep clipping on, so zoomed or cropped data stays
hidden. A log axis leaves values at or below 0 out of its limits, such as the
base of every bar. `despine` keeps clipping on there too. Unclipped, the bars
would reach far below the figure and collapse constrained layout. Markers wider
than the offset can still reach titles or tick labels.

Keep data edges on round numbers where you can. Integer histogram bins centred
on whole numbers put the first edge at -0.5, which widens the axis to the tick
below 0. Start such bins at 0.

### Twin axes

`despine` styles the left and bottom spines of the axes it gets. Style a
`twinx()` axes by hand, and call `despine` on the host after the twin is drawn.

```python
ax2 = ax.twinx()
ax2.plot(x, y2, clip_on=False)  # despine never sees the twin
ax2.set_ylim(0, 100)  # limits on ticks, so the spine ends on one
ax2.spines[["left", "bottom"]].set_visible(False)
ax2.spines["right"].set_visible(True)  # the look hides right spines
ax2.spines["right"].set_position(("outward", 10))
pk.despine(ax)  # last, once the twin is drawn
```

## label_points

`pk.label_points(ax, points, labels)` takes the collection `ax.scatter` returns
and starts each label at its marker. [adjustText](https://github.com/Phlya/adjustText)
then moves the labels apart and off the markers' full extent, not just their
centres. It keeps a small gap between labels and draws a thin leader line back
to each marker, in the axes edge color.

Each label sits in a box with the legend frame's face, transparency and
corners, on every look. The box outline and the leader line share one thin
stroke in the axes edge color, and the line starts at the box edge. adjustText
keeps the boxes apart, not just the text. Pass `bbox=None` for bare labels, or a `bbox`
dict to restyle the box.

Call it last, after `despine` and every title, axis label, suptitle and legend
on the figure. adjustText places labels in pixels. Anything added afterwards
makes constrained layout reshape the axes, which moves the labels back into
each other. Extra keyword arguments go to `matplotlib.text.Text`, for example
`fontsize=8`.

adjustText sizes its steps in pixels, with defaults tuned for the screen. At
300 dpi those defaults pulled labels back onto their own markers, so
`label_points` converts them from points. It also pushes labels apart harder
than the default, which leaves near-identical labels stacked.

Labels stay inside the axes. `despine` fits the axes to the data, so the
outermost points sit at or near the edge. Their labels can only move inward,
and one may still touch a marker. Check those points in the PNG.

`offsets=[(dx, dy), ...]` skips adjustText and puts each label at a fixed
offset in points from its marker. The side facing the marker anchors the
label, so `(6, 4)` sets its bottom left corner there. `ha=` and `va=` override
that. The leader line stops 1.5 pt short of the marker. `leader=False` drops
the lines in either mode, and `bbox=None` drops the boxes.

Past about 10 labels per panel in a dense cluster, adjustText cannot keep them
readable. Label only the points that matter, or use a categorical plot with the
names on an axis.
