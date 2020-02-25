""" See base class module for general documentation on factories.
"""
from __future__ import print_function, division

import numpy as np
import pandas as pd
import logging

from traits.api import Any, Constant
from .plot_config import BAR_PLOT_TYPE
from .bar_plot_style import IGNORE_DATA_DUPLICATES
from .base_factories import StdXYPlotFactory

BAR_SQUEEZE_FACTOR = 0.8

ERROR_BAR_COLOR = "black"

ERROR_BAR_DATA_KEY_PREFIX = "__error_"

logger = logging.getLogger(__name__)


class BarPlotFactory(StdXYPlotFactory):
    """ Factory to build a bar plot.
    """
    #: Plot type as used by Plot.plot
    plot_type_name = Constant("bar")

    #: Plot type as selected by user
    plot_type = Constant(BAR_PLOT_TYPE)

    #: Optional error bars (when multiple values contribute to a single bar)
    error_bars = Any  # Either(Array, Dict)

    def add_renderers(self, plot):
        """ Generate all bar renderers and optional error bars sticks.
        """
        # Now that the x_values have been laid out, compute the appropriate bar
        # width:
        if not self.plot_style.bar_width:
            self.plot_style.bar_width = self._compute_bar_width()

        super(BarPlotFactory, self).add_renderers(plot)

        if self.error_bars is not None and len(self.error_bars):
            self._draw_error_bars(plot)

    def _add_arrays_for_hue(self, data_map, x_arr, y_arr, hue_val, hue_val_idx,
                            adtl_arrays):
        """ Build and collect all arrays to add to ArrayPlotData for hue value.
        """
        hue_name = str(hue_val)
        x_name = self._plotdata_array_key(self.x_col_name, hue_name)
        y_name = self._plotdata_array_key(self.y_col_name, hue_name)

        x = x_arr[hue_val]
        y = y_arr[hue_val]
        if self.x_labels:
            _, y, errors = _split_avg_for_bar_heights(
                x, y, force_index=self.x_labels
            )
            show_error_bars = self.plot_style.show_error_bars
            if show_error_bars:
                self.error_bars[hue_name] = errors

            # Strings along x: replace with equi-distant positions...
            x = np.arange(len(self.x_labels), dtype="float64")
            # shifted so the bars are side by side if that's the chosen style:
            if self.plot_style.bar_style == "group":
                bar_width = BAR_SQUEEZE_FACTOR / len(x_arr)
                x = x + hue_val_idx * bar_width
            else:
                raise NotImplementedError()

        data_map[x_name], data_map[y_name] = x, y
        return hue_name, x_name, y_name

    def _draw_error_bars(self, plot):
        """ Add data and renderers for drawing error bars around bar heights.
        """
        if not self.z_col_name:
            self._draw_error_bars_single_renderer(plot)
        else:
            self._draw_error_bars_multi_renderer(plot)

    def _draw_error_bars_single_renderer(self, plot):
        """ Add data and renderers for drawing error bars around bar heights.
        """
        bar_height = self.plot_data.arrays[self.y_col_name]
        bar_positions = self.plot_data.arrays[self.x_col_name]
        for i, (y_val, stddev) in enumerate(zip(bar_height, self.error_bars)):
            x = bar_positions[i]
            x_data_name = ERROR_BAR_DATA_KEY_PREFIX + "{}_x".format(i)
            y_data_name = ERROR_BAR_DATA_KEY_PREFIX + "{}_y".format(i)
            self.plot_data.set_data(x_data_name, [x, x])
            self.plot_data.set_data(y_data_name,
                                    [y_val+stddev/2., y_val-stddev/2.])
            error_bar_renderer_name = "plot{}".format(i+1)
            plot.plot((x_data_name, y_data_name), type="line",
                      color=ERROR_BAR_COLOR, name=error_bar_renderer_name)

    def _draw_error_bars_multi_renderer(self, plot):
        """ Add data and renderers for drawing error bars around bar heights.
        """
        for j, hue_name in enumerate(self._hue_values):
            x_key = self._plotdata_array_key(self.x_col_name, hue_name)
            y_key = self._plotdata_array_key(self.y_col_name, hue_name)
            bar_height = self.plot_data.arrays[y_key]
            bar_positions = self.plot_data.arrays[x_key]
            errors = self.error_bars[hue_name]
            for i, (y_val, stddev) in enumerate(zip(bar_height, errors)):
                x = bar_positions[i]
                renderer_num = j*len(bar_positions) + i
                x_data_name = ERROR_BAR_DATA_KEY_PREFIX + "{}_x".format(
                    renderer_num
                )
                y_data_name = ERROR_BAR_DATA_KEY_PREFIX + "{}_y".format(
                    renderer_num
                )
                self.plot_data.set_data(x_data_name, [x, x])
                self.plot_data.set_data(y_data_name,
                                        [y_val+stddev/2., y_val-stddev/2.])
                name = "plot{}".format(renderer_num)
                plot.plot((x_data_name, y_data_name), type="line",
                          color=ERROR_BAR_COLOR, name=name)

    def _compute_bar_width(self):
        """ Compute the width of each bar.

        Values computed from the distance between x values, the number of bars
        per x value and the plot_style.bar_style (side by side vs stacked).
        """
        if self._hue_values:
            hue_name0 = self._hue_values[0]
            x_name = self._plotdata_array_key(self.x_col_name, hue_name0)
        else:
            x_name = self.x_col_name

        index_vals = self.plot_data.arrays[x_name]
        if len(index_vals) == 1:
            width = 1.
        else:
            width = BAR_SQUEEZE_FACTOR * (index_vals[1:] -
                                          index_vals[:-1]).min()

        if self._hue_values:
            width /= len(self._hue_values)

        return width

    def _plot_data_single_renderer(self, x_arr=None, y_arr=None, z_arr=None,
                                   **adtl_arrays):
        """ Build the data_map to build the plot data for single renderer case.

        For bar plots, if the index is made of strings, place them equally
        spaced along the x axis. If there are duplicates, and styling specifies
        it, recompute bar heights as averages of y values and optionally
        compute y error bars.
        """
        # Collect all labels and reset x_arr as an int list
        if x_arr.dtype in [object, bool]:
            duplicates_present = len(set(x_arr)) != len(x_arr)
            data_duplicate = self.plot_style.data_duplicate
            handle_duplicates = data_duplicate != IGNORE_DATA_DUPLICATES
            if duplicates_present and handle_duplicates:
                if self.x_labels:
                    x_arr, y_arr, errors = _split_avg_for_bar_heights(
                        x_arr, y_arr, force_index=self.x_labels
                    )
                else:
                    x_arr, y_arr, errors = _split_avg_for_bar_heights(
                        x_arr, y_arr
                    )
                show_error_bars = self.plot_style.show_error_bars
                if show_error_bars:
                    self.error_bars = errors

            if not self.x_labels:
                self.x_labels = list(x_arr)

            x_arr = np.arange(len(self.x_labels))

        return super(BarPlotFactory, self)._plot_data_single_renderer(
            x_arr, y_arr, z_arr, **adtl_arrays
        )

    def _plot_data_multi_renderer(self, x_arr=None, y_arr=None, z_arr=None,
                                  **adtl_arrays):
        """ Built the data_map to build the plot data for multiple renderers.
        """
        self.error_bars = {}

        # Collect all possible labels
        if not self.x_labels:
            if list(x_arr.values())[0].dtype in [object, bool]:
                x_labels = set()
                for x_array in x_arr.values():
                    x_labels.update(x_array)

                self.x_labels = sorted(x_labels)

        return super(BarPlotFactory, self)._plot_data_multi_renderer(
            x_arr=x_arr, y_arr=y_arr, z_arr=z_arr, **adtl_arrays
        )

    # Trait initialization methods --------------------------------------------

    def _plot_tools_default(self):
        return {"zoom", "pan", "legend"}


def _split_avg_for_bar_heights(x_arr, y_arr, force_index=None):
    """ Recompute y_arr grouping all values by their x value, and averaging

    Uses pandas' groupby functionality.

    Parameters
    ----------
    x_arr : np.array
        Content of the column to display along the x dimension.

    y_arr : np.array
        Content of the column to display as bar heights.

    force_index : list
        List of index values to force the computation of the values and errors
        for.

    Returns
    -------
    tuple
        Labels to display along the x axis, the averaged bar heights and
        the error bars.
    """
    df = pd.DataFrame({"x": x_arr, "y": y_arr})
    grpby = df.groupby(by="x")
    grouped_avg_y = grpby.mean()["y"]

    if force_index:
        grouped_avg_y = grouped_avg_y.reindex(list(force_index))

    labels = list(grouped_avg_y.index)
    y_arr = grouped_avg_y.values

    if force_index:
        error_bars = grpby.std()["y"].reindex(list(force_index)).values
    else:
        error_bars = grpby.std()["y"].values

    return labels, y_arr, error_bars
