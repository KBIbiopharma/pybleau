""" See base class module for general documentation on factories.
"""

from __future__ import print_function, division

import logging

from traits.api import Constant, Float, Instance, Tuple
from chaco.api import ColorBar, DataRange1D, LinearMapper

from .plot_config import HEATMAP_PLOT_TYPE
from .base_factories import DEFAULT_RENDERER_NAME, StdXYPlotFactory

TWO_D_DATA_NAME = "img_data"

logger = logging.getLogger(__name__)


class HeatmapPlotFactory(StdXYPlotFactory):
    """ Factory to build a heatmap plot.
    """
    plot_type = Constant(HEATMAP_PLOT_TYPE)

    def _plot_data_single_renderer(self, x_arr=None, y_arr=None, z_arr=None,
                                   **adtl_arrays):
        """ Build the data_map to build the plot data.
        """
        data_map = {self.x_col_name: x_arr, self.y_col_name: y_arr}
        data_map.update(adtl_arrays)
        renderer_data = {"x": self.x_col_name, "y": self.y_col_name,
                         "name": DEFAULT_RENDERER_NAME}
        self.renderer_desc = [renderer_data]
        data_map = {TWO_D_DATA_NAME: z_arr, "x_arr": x_arr,
                    "y_arr": y_arr}
        return data_map

    def _plot_data_multi_renderer(self, x_arr=None, y_arr=None, z_arr=None,
                                  **adtl_arrays):
        msg = "Multi-renderer not supported for Heatmap plots."
        logger.exception(msg)
        raise ValueError(msg)

    def adjust_plot_style(self, x_arr=None, y_arr=None, z_arr=None):
        if len(self.plot_style.renderer_styles) > 1:
            msg = "Only 1 heatmap renderer supported at a time."
            logger.exception(msg)
            raise NotImplementedError(msg)

        renderer_style = self.plot_style.renderer_styles[0]
        renderer_style.auto_xbound = (x_arr.min(), x_arr.max())
        renderer_style.auto_ybound = (y_arr.min(), y_arr.max())
        renderer_style.reset_xbound = True
        renderer_style.reset_ybound = True

        renderer_style = self.plot_style.renderer_styles[0]
        renderer_style.colorbar_low = z_arr.min()
        renderer_style.colorbar_high = z_arr.max()

    def add_renderers(self, plot):
        renderer_style = self.plot_style.renderer_styles[0]
        renderer = plot.img_plot(TWO_D_DATA_NAME,
                                 **renderer_style.to_plot_kwargs())[0]
        self.generate_colorbar(renderer, plot)
        if self.plot_style.contour_style.add_contours:
            self.generate_contours(plot)

    def generate_colorbar(self, renderer, plot):
        colormap = renderer.color_mapper
        # Constant mapper for the color bar so that the colors stay the same
        # even when data changes
        renderer_style = self.plot_style.renderer_styles[0]
        colorbar_range = DataRange1D(low=renderer_style.colorbar_low,
                                     high=renderer_style.colorbar_high)
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
        font_size = self.plot_style.color_axis_title_style.font_size
        font_name = self.plot_style.color_axis_title_style.font_name
        font = '{} {}'.format(font_name, font_size)
        axis_kw = dict(title=self.z_axis_title, orientation="right",
                       title_angle=190.0, title_font=font)
        self.colorbar._axis.trait_set(**axis_kw)

    def generate_contours(self, plot):
        renderer_style = self.plot_style.renderer_styles[0]
        xbounds = renderer_style.xbounds
        ybounds = renderer_style.ybounds
        plot.contour_plot(TWO_D_DATA_NAME, type="line",
                          xbounds=xbounds, ybounds=ybounds,
                          levels=self.plot_style.contour_style.contour_levels,
                          styles=self.plot_style.contour_style.contour_styles,
                          widths=self.plot_style.contour_style.contour_widths,
                          alpha=self.plot_style.contour_style.contour_alpha)
