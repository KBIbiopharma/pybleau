""" See base class module for general documentation on factories.
"""

from __future__ import print_function, division

import logging
import pandas as pd

from traits.api import Constant, Dict, Float, Instance, Int, Tuple
from chaco.api import ArrayPlotData, ColorBar, DataRange1D, HPlotContainer, \
    LinearMapper, Plot
from chaco.default_colormaps import color_map_name_dict

from .plot_config import HEATMAP_PLOT_TYPE
from .base_factories import BasePlotFactory

BAR_SQUEEZE_FACTOR = 0.8

TWO_D_DATA_NAME = "img_data"

HISTOGRAM_Y_LABEL = "Frequency"

SELECTION_COLOR = "red"

DISCONNECTED_SELECTION_COLOR = "grey"

SELECTION_METADATA_NAME = 'selections'

ERROR_BAR_COLOR = "black"

ERROR_BAR_DATA_KEY_PREFIX = "__error_"

logger = logging.getLogger(__name__)


class HeatmapPlotFactory(BasePlotFactory):
    """ Factory to build a heatmap plot.
    """
    plot_type = Constant(HEATMAP_PLOT_TYPE)

    ndim = Int(3)

    #: cmap x bounds
    xbounds = Tuple

    #: cmap y bounds
    ybounds = Tuple

    #: Colorbar built to describe the data's heatmap
    colorbar = Instance(ColorBar)

    #: Lower limit of the colorbar
    colorbar_low = Float

    #: Upper limit of the colorbar
    colorbar_high = Float

    contour_style = Dict

    def __init__(self, data_source=None, x_col_name="", y_col_name="",
                 z_col_name="", **traits):

        if not isinstance(data_source, pd.DataFrame):
            msg = "Can't build a HeatmapPlotFactory without a data_source."
            logger.exception(msg)
            raise ValueError(msg)

        pivoted_data = data_source.pivot_table(index=y_col_name,
                                               columns=x_col_name,
                                               values=z_col_name)
        data_map = {TWO_D_DATA_NAME: pivoted_data}
        plot_data = ArrayPlotData(**data_map)
        traits["plot_data"] = plot_data

        x = data_source[x_col_name]
        y = data_source[y_col_name]
        traits["xbounds"] = (x.min(), x.max())
        traits["ybounds"] = (y.min(), y.max())

        traits["x_col_name"] = x_col_name
        traits["y_col_name"] = y_col_name
        traits["z_col_name"] = z_col_name

        colormap_str = traits["plot_style"].pop("colormap_str")
        traits["plot_style"]["colormap"] = color_map_name_dict[colormap_str]

        super(HeatmapPlotFactory, self).__init__(**traits)

    def generate_plot(self):
        """ Generate and return a line plot & a dict describing its properties.
        """
        plot = Plot(data=self.plot_data, padding=0)
        style_keys = list(self.plot_style.keys())
        self.contour_style = {key: self.plot_style.pop(key)
                              for key in style_keys if "contour" in key}

        renderer = plot.img_plot(TWO_D_DATA_NAME, xbounds=self.xbounds,
                                 ybounds=self.ybounds, **self.plot_style)[0]
        self.set_axis_labels(plot)
        # Make more room for labels
        plot.padding_right = 5
        plot.padding_top = 25

        self.generate_colorbar(renderer, plot)
        if self.contour_style.pop("add_contours"):
            self.generate_contours(plot)

        container = HPlotContainer(padding=0)
        container.add(plot, self.colorbar)
        container.padding_right = sum([comp.padding_right
                                       for comp in container.components])
        container.bgcolor = "transparent"

        # Build a description of the plot to build a PlotDescriptor
        desc = dict(plot_type=self.plot_type, plot=container, visible=True,
                    plot_title=self.plot_title, x_col_name=self.x_col_name,
                    y_col_name=self.y_col_name, x_axis_title=self.x_axis_title,
                    y_axis_title=self.y_axis_title, z_col_name=self.z_col_name,
                    z_axis_title=self.z_axis_title, ndim=self.ndim)
        return container, desc

    def generate_colorbar(self, renderer, plot):
        colormap = renderer.color_mapper
        # Constant mapper for the color bar so that the colors stay the same
        # even when data changes
        colorbar_range = DataRange1D(low=self.colorbar_low,
                                     high=self.colorbar_high)
        index_mapper = LinearMapper(range=colorbar_range)
        self.colorbar = ColorBar(index_mapper=index_mapper,
                                 color_mapper=colormap,
                                 padding_top=plot.padding_top,
                                 padding_bottom=plot.padding_bottom,
                                 padding_right=40,
                                 padding_left=5,
                                 resizable='v',
                                 orientation='v',
                                 width=30)
        font_size = self.plot_style["z_title_font_size"]
        font_name = self.plot_style["title_font_name"]
        font = '{} {}'.format(font_name, font_size)
        axis_kw = dict(title=self.z_axis_title, orientation="right",
                       title_angle=190.0, title_font=font)
        self.colorbar._axis.trait_set(**axis_kw)

    def generate_contours(self, plot):
        plot.contour_plot(TWO_D_DATA_NAME, type="line",
                          xbounds=self.xbounds, ybounds=self.ybounds,
                          levels=self.contour_style["contour_levels"],
                          styles=self.contour_style["contour_styles"],
                          widths=self.contour_style["contour_widths"],
                          alpha=self.contour_style["contour_alpha"])
