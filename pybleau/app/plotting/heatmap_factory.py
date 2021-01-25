""" See base class module for general documentation on factories.
"""

from __future__ import print_function, division
import logging
import numpy as np
from pandas import Series

from traits.api import Constant
from chaco.api import ImagePlot, PlotAxis

from app_common.chaco.plot_factory import create_contour_plot, create_img_plot

from .plot_config import HEATMAP_PLOT_TYPE
from .base_factories import CATEGORICAL_TYPES, CmapedXYPlotFactoryMixin, \
    DEFAULT_RENDERER_NAME, StdXYPlotFactory

TWO_D_DATA_NAME = "img_data"

CONTOUR_PLOT_NAME = "contour_renderer"

logger = logging.getLogger(__name__)


class HeatmapPlotFactory(StdXYPlotFactory, CmapedXYPlotFactoryMixin):
    """ Factory to build a plot with a heatmap renderer.
    """
    plot_type = Constant(HEATMAP_PLOT_TYPE)

    def _plot_data_single_renderer(self, x_arr=None, y_arr=None, z_arr=None,
                                   **adtl_arrays):
        """ Build plot data when single renderer is present.
        """
        # Collect all labels and reset x_arr as an int list
        if x_arr.dtype in CATEGORICAL_TYPES:
            if not self.x_labels:
                self.x_labels = Series(x_arr).unique().tolist()

            x_arr = np.array([self.x_labels.index(val)
                              for val in self.x_labels])
            indices = x_arr.argsort()
            x_arr = x_arr[indices]
            self.x_labels = list(np.array(self.x_labels)[indices])

            # Collect all labels and reset x_arr as an int list
        if y_arr.dtype in CATEGORICAL_TYPES:
            if not self.y_labels:
                self.y_labels = Series(y_arr).unique().tolist()

            y_arr = np.array([self.y_labels.index(val)
                              for val in self.y_labels])
            indices = y_arr.argsort()
            y_arr = y_arr[indices]
            self.y_labels = list(np.array(self.y_labels)[indices])

        renderer_data = {"x": self.x_col_name, "y": self.y_col_name,
                         "name": DEFAULT_RENDERER_NAME}
        self.renderer_desc = [renderer_data]

        data_map = {TWO_D_DATA_NAME: z_arr, self.x_col_name: x_arr,
                    self.y_col_name: y_arr}
        data_map.update(adtl_arrays)
        return data_map

    def _plot_data_multi_renderer(self, x_arr=None, y_arr=None, z_arr=None,
                                  **adtl_arrays):
        """ Build plot data when multiple renderer are overlaid.
        """
        msg = "Multi-renderer not supported for Heatmap plots."
        logger.exception(msg)
        raise ValueError(msg)

    def adjust_plot_style(self):
        if len(self.plot_style.renderer_styles) > 1:
            msg = "Only 1 heatmap renderer supported at a time."
            logger.exception(msg)
            raise NotImplementedError(msg)

        renderer_style = self.plot_style.renderer_styles[0]
        x_arr = self.plot_data.get_data(self.x_col_name)
        y_arr = self.plot_data.get_data(self.y_col_name)
        renderer_style.auto_xbounds = (x_arr.min(), x_arr.max())
        renderer_style.auto_ybounds = (y_arr.min(), y_arr.max())
        renderer_style.reset_xbounds = True
        renderer_style.reset_ybounds = True

        z_arr = self.plot_data.get_data(TWO_D_DATA_NAME)
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
        self.renderers[TWO_D_DATA_NAME] = renderer
        plot.x_axis = PlotAxis(component=renderer,
                               orientation="bottom")
        plot.y_axis = PlotAxis(component=renderer,
                               orientation="left")
        plot.underlays.append(plot.x_axis)
        plot.underlays.append(plot.y_axis)

        if self.plot_style.contour_style.add_contours:
            self.generate_contours(plot)

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
        self.renderers[CONTOUR_PLOT_NAME] = renderer

    def is_colormapped_renderer(self, renderer):
        # Need to override parent implementation because the optional contour
        # plot renderer also has a color mapper:
        return isinstance(renderer, ImagePlot)
