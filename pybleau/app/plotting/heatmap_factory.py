""" See base class module for general documentation on factories.
"""

from __future__ import print_function, division
import logging

from traits.api import Constant
from chaco.api import ColorBar, DataRange1D, LinearMapper, PlotAxis

from app_common.chaco.plot_factory import create_contour_plot, create_img_plot

from .plot_config import HEATMAP_PLOT_TYPE
from .base_factories import DEFAULT_RENDERER_NAME, StdXYPlotFactory

TWO_D_DATA_NAME = "img_data"

logger = logging.getLogger(__name__)


class HeatmapPlotFactory(StdXYPlotFactory):
    """ Factory to build a plot with a heatmap renderer.
    """
    plot_type = Constant(HEATMAP_PLOT_TYPE)

    def _plot_data_single_renderer(self, x_arr=None, y_arr=None, z_arr=None,
                                   **adtl_arrays):
        """ Build plot data when single renderer is present.
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
        """ Build plot data when multiple renderer are overlaid.
        """
        msg = "Multi-renderer not supported for Heatmap plots."
        logger.exception(msg)
        raise ValueError(msg)

    def adjust_plot_style(self, x_arr=None, y_arr=None, z_arr=None):
        if len(self.plot_style.renderer_styles) > 1:
            msg = "Only 1 heatmap renderer supported at a time."
            logger.exception(msg)
            raise NotImplementedError(msg)

        renderer_style = self.plot_style.renderer_styles[0]
        renderer_style.auto_xbounds = (x_arr.min(), x_arr.max())
        renderer_style.auto_ybounds = (y_arr.min(), y_arr.max())
        renderer_style.reset_xbounds = True
        renderer_style.reset_ybounds = True

        self.plot_style.colorbar_low = z_arr.min()
        self.plot_style.colorbar_high = z_arr.max()

    def add_renderers(self, plot):
        if not len(self.plot_style.renderer_styles) == 1:
            msg = "Only 1 renderer supported in image plots."
            raise ValueError(msg)

        renderer_style = self.plot_style.renderer_styles[0]
        data = self.plot_data.get_data(TWO_D_DATA_NAME)
        renderer = create_img_plot(data=data,
                                   **renderer_style.to_plot_kwargs())
        plot.add(renderer)
        plot.x_axis = PlotAxis(component=renderer,
                               orientation="bottom")
        plot.y_axis = PlotAxis(component=renderer,
                               orientation="left")
        plot.underlays.append(plot.x_axis)
        plot.underlays.append(plot.y_axis)

        if self.plot_style.contour_style.add_contours:
            self.generate_contours(plot)

    def generate_colorbar(self, desc):
        """ Generate the colorbar to be displayed along side the main plot.
        """
        plot = desc["plot"]
        renderer = plot.components[0]

        colormap = renderer.color_mapper
        # Constant mapper for the color bar so that the colors stay the same
        # even when data changes
        colorbar_range = DataRange1D(low=self.plot_style.colorbar_low,
                                     high=self.plot_style.colorbar_high)
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

        data = self.plot_data.get_data(TWO_D_DATA_NAME)
        renderer = create_contour_plot(
            data=data, type="line", xbounds=xbounds, ybounds=ybounds,
            levels=self.plot_style.contour_style.contour_levels,
            styles=self.plot_style.contour_style.contour_styles,
            widths=self.plot_style.contour_style.contour_widths,
            alpha=self.plot_style.contour_style.contour_alpha
        )

        plot.add(renderer)
