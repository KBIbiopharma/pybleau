""" See base class module for general documentation on factories.
"""

from __future__ import print_function, division

import numpy as np
import logging

from traits.api import Array, Constant, Int, Str
from chaco.api import ArrayPlotData

from .plot_config import HIST_PLOT_TYPE
from .histogram_plot_style import HistogramPlotStyle
from .base_factories import StdXYPlotFactory

HISTOGRAM_Y_LABEL = "Frequency"

logger = logging.getLogger(__name__)


class HistogramPlotFactory(StdXYPlotFactory):
    """ Factory to build a histogram plot of the distribution of an array of
    values.

    This is designed to be used by the DataFramePlotter but it can be used as a
    standalone chaco histogram factory. See example below.

    NOTE: WARNING! If we try to use an inspector on this plot, we will have to
    worry about the fact that this plot's datasources aren't aligned with the
    other plots, since the NANs are removed from the array passed to create the
    plot.

    Examples
    --------
    >>> x = array([1, 2, 3, 2])
    >>> h = HistogramPlotFactory("age", x)
    >>> h.generate_plot()
    (<chaco.plot.Plot at 0x12278a590>,
     {'ndim': 1,
      'plot': <chaco.plot.Plot at 0x12278a590>,
      ...})

    Or a style object can be passed:
    >>> plot_style = HistogramPlotStyle(alpha=0.5)
    >>> h = HistogramPlotFactory("age", x, plot_style=plot_style)
    >>> h.generate_plot()
    (<chaco.plot.Plot at 0x12278a590>,
     {'ndim': 1,
      'plot': <chaco.plot.Plot at 0x12278a590>,
      ...})
    """
    #: Label to display along the y-axis
    y_axis_title = Str(HISTOGRAM_Y_LABEL)

    #: Plot type as used by Plot.plot
    plot_type_name = Constant("bar")

    #: String description of the type of plot this generates
    plot_type = Constant(HIST_PLOT_TYPE)

    #: Number of DF columns involved in making the plot
    ndim = Int(1)

    #: Edges of the histogram bars
    bin_edges = Array

    def __init__(self, x_arr=None, **traits):
        """ Build a factory from a data array, its name, and some styling info.
        """
        if not traits or "plot_style" not in traits:
            traits["plot_style"] = HistogramPlotStyle()
        elif isinstance(traits["plot_style"], HistogramPlotStyle):
            traits["plot_style"] = traits["plot_style"]

        traits["y_col_name"] = HISTOGRAM_Y_LABEL
        super(HistogramPlotFactory, self).__init__(x_arr=x_arr, **traits)

    def adjust_plot_style(self):
        """ Translate general plotting style information into histogram params.
        """
        # Adjust the bar width
        bar_width_factor = self.plot_style.bar_width_factor
        num_bins = self.plot_style.num_bins
        bar_width = self.compute_bar_width(self.bin_edges, num_bins,
                                           bar_width_factor=bar_width_factor)
        self.plot_style.bar_width = bar_width

    def initialize_plot_data(self, x_arr=None, y_arr=None, z_arr=None,
                             **adtl_arrays):
        """ Set the plot_data and the list of renderer descriptions.
        """
        # Compute the bin edges and probabilities and create the PlotData:
        bin_lims = self.plot_style.bin_limits
        num_bins = self.plot_style.num_bins
        data_map, self.bin_edges = self.build_hist_data(
            self.x_col_name, x_arr, num_bins, bin_lims=bin_lims
        )
        self.plot_data = ArrayPlotData(**data_map)

        color = self.plot_style.renderer_styles[0].color
        renderer_data = {"x": self.x_col_name, "y": HISTOGRAM_Y_LABEL,
                         "color": color, "name": None}
        self.renderer_desc = [renderer_data]
        return data_map

    @staticmethod
    def build_hist_data(x_col_name, x_arr, num_bins=10, bin_lims=None):
        """ Chaco histogram building helper: build ArrayPlotData input from
        array and compute bar heights/edges.

        Parameters
        ----------
        x_col_name : str
            Name of the column to build the histogram of. Used as key to
            returned data map.

        x_arr : numpy array
            Array of data to build the histogram of.

        num_bins : int
            Number of bins to build histogram with.

        bin_lims : tuple
            Boundaries to bin the data.
        """
        if bin_lims:
            bins = np.linspace(bin_lims[0], bin_lims[1], num_bins+1)
        else:
            bins = num_bins

        clean_data = x_arr[~np.isnan(x_arr)]
        prob, bin_edges = np.histogram(clean_data, bins=bins)
        bar_locs = (bin_edges[1:] + bin_edges[:-1]) / 2.
        data_map = {x_col_name: bar_locs, HISTOGRAM_Y_LABEL: prob}
        return data_map, bin_edges

    @staticmethod
    def compute_bar_width(bin_edges, num_bins, bar_width_factor=1.):
        """ Chaco histogram building helper: compute the bar widths.
        """
        return bar_width_factor * (bin_edges[-1] - bin_edges[0]) / num_bins

    def _plot_tools_default(self):
        return {"zoom", "pan"}
