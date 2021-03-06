""" See base class module for general documentation on factories.
"""

from __future__ import print_function, division

import pandas as pd
import logging

from traits.api import Constant, Tuple
from chaco.api import ArrayPlotData, ColormappedSelectionOverlay, \
    LinearMapper, LogMapper, ScatterInspectorOverlay
from chaco.tools.api import RangeSelection, RangeSelectionOverlay

from app_common.chaco.scatter_position_tool import add_scatter_inspectors, \
    DataframeScatterInspector
from app_common.chaco.plot_factory import create_cmap_scatter_plot

from .renderer_style import STYLE_L_ORIENT
from .axis_style import LOG_AXIS_STYLE
from .plot_config import CMAP_SCATTER_PLOT_TYPE, SCATTER_PLOT_TYPE
from .base_factories import CmapedXYPlotFactoryMixin, StdXYPlotFactory

SELECTION_COLOR = "red"

DISCONNECTED_SELECTION_COLOR = "grey"

SELECTION_METADATA_NAME = 'selections'

logger = logging.getLogger(__name__)


class ScatterPlotFactory(StdXYPlotFactory):
    """ Factory to build a potentially multi-renderer XY plot.

    This plot currently supports displaying many dimensions at once since it
    supports a legend tool to select parts of the data and a hover tool to
    display any number of additional columns.
    """
    #: Plot type as selected by user
    plot_type = Constant(SCATTER_PLOT_TYPE)

    #: Inspector tool and overlay to query/listen to for events
    inspector = Tuple

    def add_tools(self, plot):
        super(ScatterPlotFactory, self).add_tools(plot)

        if "click_selector" in self.plot_tools:
            self.add_click_selector_tool(plot)

        if "hover" in self.plot_tools:
            self.add_hover_display_tool(plot)

    def add_click_selector_tool(self, plot):
        """ Add scatter point click tool to select points.
        """
        for i, renderer in enumerate(plot.components):
            marker_size = self.plot_style.renderer_styles[i].marker_size
            marker = self.plot_style.renderer_styles[i].marker
            inspector_tool = DataframeScatterInspector(
                renderer, selection_metadata_name=SELECTION_METADATA_NAME,
                selection_mode="toggle", persistent_hover=False
            )
            renderer.tools.append(inspector_tool)
            inspector_overlay = ScatterInspectorOverlay(
                renderer,
                selection_marker=marker,
                selection_marker_size=marker_size,
                selection_color=self.inspector_selection_color
            )

            renderer.overlays.append(inspector_overlay)
            # FIXME: This overwrite itself when multiple renderers are drawn...
            self.inspector = (inspector_tool, inspector_overlay)

    def add_hover_display_tool(self, plot):
        """ Add mouse hover tool to display column values on hover.
        """
        if not self.hover_col_names:
            return

        if not self.z_col_name:
            renderer_data = pd.DataFrame({col: plot.data.arrays[col]
                                          for col in self.hover_col_names})
        else:
            renderer_data = []
            for hue_name in self._hue_values:
                data = {}
                for col in self.hover_col_names:
                    key = self._plotdata_array_key(col, hue_name)
                    data[col] = plot.data.get_data(key)

                renderer_data.append(pd.DataFrame(data))

        add_scatter_inspectors(plot, datasets=renderer_data,
                               include_overlay=True, align="ul")

    # Traits initialization methods -------------------------------------------

    def _plot_tools_default(self):
        base_tools = super(ScatterPlotFactory, self)._plot_tools_default()
        return base_tools | {"click_selector", "hover"}


class CmapScatterPlotFactory(ScatterPlotFactory, CmapedXYPlotFactoryMixin):
    """ Factory to build a single scatter plot colormapped by a z array.

    See Also
    --------
    ScatterPlotFactory:
        Use the ScatterPlotFactory to create a scatter Plot with 1 or more
        scatter renderers, for example when colorizing using a column of
        discrete values.
    """
    #: Plot type as selected by user
    plot_type = Constant(CMAP_SCATTER_PLOT_TYPE)

    def generate_colorbar(self, desc):
        """ Generate the colorbar to display along side the plot.
        """
        super(CmapScatterPlotFactory, self).generate_colorbar(desc)

        colorbar = self.colorbar
        cmap_renderer = self._get_cmap_renderer()
        select_tool = "colorbar_selector" in self.plot_tools
        if select_tool:
            selection = ColormappedSelectionOverlay(cmap_renderer,
                                                    fade_alpha=0.35,
                                                    selection_type="mask")
            cmap_renderer.overlays.append(selection)

            colorbar.tools.append(RangeSelection(component=colorbar))
            overlay = RangeSelectionOverlay(component=colorbar,
                                            border_color="white",
                                            alpha=0.8,
                                            fill_color="lightgray")
            colorbar.overlays.append(overlay)

    def _build_renderer(self, desc, style):
        x = self.plot_data.get_data(desc["x"])
        y = self.plot_data.get_data(desc["y"])
        z = self.plot_data.get_data(desc["z"])

        if self.plot_style.x_axis_style.scaling == LOG_AXIS_STYLE:
            x_mapper_class = LogMapper
        else:
            x_mapper_class = LinearMapper

        if style.orientation == STYLE_L_ORIENT:
            y_style = self.plot_style.y_axis_style
        else:
            y_style = self.plot_style.secondary_y_axis_style

        if y_style.scaling == LOG_AXIS_STYLE:
            y_mapper_class = LogMapper
        else:
            y_mapper_class = LinearMapper

        return create_cmap_scatter_plot(data=(x, y, z),
                                        index_mapper_class=x_mapper_class,
                                        value_mapper_class=y_mapper_class,
                                        **style.to_plot_kwargs())

    def initialize_plot_data(self, x_arr=None, y_arr=None, z_arr=None,
                             **adtl_arrays):
        """ Set the plot_data and the list of renderer descriptions.
        """
        if x_arr is None or y_arr is None or z_arr is None:
            msg = "2D cmap scatters require a valid plot_data or an array for"\
                  " x, y and z."
            logger.exception(msg)
            raise ValueError(msg)

        data_map = {self.x_col_name: x_arr, self.y_col_name: y_arr,
                    self.z_col_name: z_arr}
        data_map.update(adtl_arrays)
        renderer_data = {"x": self.x_col_name, "y": self.y_col_name,
                         "z": self.z_col_name, "name": "cmap_scatter"}
        self.renderer_desc.append(renderer_data)
        self.plot_data = ArrayPlotData(**data_map)
        return data_map

    def add_hover_display_tool(self, plot):
        """ Add mouse hover tool to display column values on hover.
        """
        if not self.hover_col_names:
            return

        renderer_data = pd.DataFrame({col: plot.data.arrays[col]
                                      for col in self.hover_col_names})
        add_scatter_inspectors(plot, datasets=renderer_data,
                               include_overlay=True, align="ul")

    # Traits initialization methods -------------------------------------------

    def _plot_tools_default(self):
        return {"zoom", "pan", "context_menu", "click_selector",
                "colorbar_selector", "hover"}
