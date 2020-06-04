""" Factory classes (and mapping) to generate chaco Plot instances from a set
of attributes. They are designed to be created from exported PlotConfiguration
objects, though can be created manually.

The factories are designed to build a Plot instance with the appropriate
data, tools, overlays and styling in 1 call to :func:`generate_plot()`. For
that to be possible, a factory should be created with the appropriate dimension
names and arrays and styling dictionary. Alternatively, a corresponding
Configurator instance can be passed.

Note that instead of arrays for x, y, z, ..., for line and scatter plots,
dictionaries can be passed, with keys controlling renderer color and values the
sub-array for that value. In this case, the resulting plot will contain as many
renderers as the number of keys in each dict.
"""
from __future__ import print_function, division

import numpy as np
import pandas as pd
import logging

from traits.api import Any, Dict, HasStrictTraits, Instance, Int, List, Set, \
    Str
from chaco.api import ArrayPlotData, ColorBar, HPlotContainer, LabelAxis, \
    LinearMapper, LogMapper, OverlayPlotContainer, PlotAxis, PlotLabel
from chaco.plot_factory import add_default_axes
from chaco.tools.api import BroadcasterTool, LegendTool, PanTool, ZoomTool
from chaco.ticks import DefaultTickGenerator, ShowAllTickGenerator

from app_common.chaco.overlay_plot_container_utils import align_renderers
from app_common.chaco.plot_factory import create_bar_plot, \
    create_cmap_scatter_plot, create_line_plot, create_scatter_plot
from app_common.chaco.legend import Legend, LegendHighlighter

from .plot_style import BaseXYPlotStyle
from .renderer_style import STYLE_L_ORIENT, STYLE_R_ORIENT
from .axis_style import LINEAR_AXIS_STYLE, LOG_AXIS_STYLE

SELECTION_COLOR = "red"

DEFAULT_RENDERER_NAME = "plot0"

logger = logging.getLogger(__name__)


RENDERER_MAKER = {
    "line": create_line_plot,
    "scatter": create_scatter_plot,
    "bar": create_bar_plot,
    "cmap_scatter": create_cmap_scatter_plot
}


class BasePlotFactory(HasStrictTraits):
    """ Base Chaco plot factory.
    """
    #: ArrayPlotData supporting the Plot object
    plot_data = Instance(ArrayPlotData)

    #: Styling of the plot and renderer. Passed to renderer creation method
    plot_style = Instance(BaseXYPlotStyle)

    #: Title of the generated plot
    plot_title = Str

    #: Name of the column to display along the x axis
    x_col_name = Str

    #: Label to display along the x-axis
    x_axis_title = Str

    #: Ordered list of x values to use to build labels when strings/booleans
    x_labels = List

    #: Name of the column to display along the y axis
    y_col_name = Str

    #: Label to display along the y-axis
    y_axis_title = Str

    #: Name of the column(s) to display along the y axis
    second_y_col_name = Str

    #: Label to display along the secondary y-axis
    second_y_axis_title = Str

    #: Name of the column to display along the color dimension
    z_col_name = Str

    #: List of z values: a renderer is created for each, and named after it
    _hue_values = List(Str)

    #: Label to display along the z-axis
    z_axis_title = Str

    #: list of tools requested on the plot
    plot_tools = Set({"zoom", "pan"})

    #: Inspector tool and overlay to hover over or select scatter data points
    inspector = Any

    #: Color of the marker once selected
    inspector_selection_color = Str(SELECTION_COLOR)

    #: Name(s) of the column(s) to display on mouse hover
    hover_col_names = List

    def generate_plot(self):
        raise NotImplementedError("Base class: use subclass.")

    def set_axis_labels(self, plot):
        """ Set the plot and axis labels of a chaco Plot.

        Parameters
        ----------
        plot : chaco plot container
            Instance of a chaco OverlayPlotContainer to set the axis and title
            labels of.
        """
        self._set_x_axis_labels(plot)
        self._set_y_axis_labels(plot)
        self._set_second_y_axis_labels(plot)
        self._set_title_label(plot)

    def _set_x_axis_labels(self, plot):
        x_labels = self.x_labels
        if x_labels:
            # if x_labels set, axis labels shouldn't be generated from the
            # numerical values but by the values stored in x_labels (for e.g.
            # when x_axis_col contains strings)
            label_rotation = self.plot_style.x_axis_style.label_rotation
            if self.plot_style.x_axis_style.show_all_labels:
                label_positions = range(len(x_labels))
                tick_generator = ShowAllTickGenerator(
                    positions=label_positions
                )
            else:
                tick_generator = DefaultTickGenerator()

            bottom_axis = LabelAxis(plot, orientation="bottom",
                                    labels=[str(x) for x in x_labels],
                                    positions=np.arange(len(x_labels)),
                                    label_rotation=label_rotation,
                                    tick_generator=tick_generator)
            plot.x_axis = bottom_axis

        plot.x_axis.title = self.x_axis_title
        font_size = self.plot_style.x_axis_style.title_style.font_size
        font_name = self.plot_style.x_axis_style.title_style.font_name
        plot.x_axis.title_font = '{} {}'.format(font_name, font_size)

    def _set_y_axis_labels(self, plot):
        if self.y_axis_title == "auto":
            styles = self.plot_style.renderer_styles
            plot.y_axis.title = ", ".join(
                [desc["y"] for style, desc in zip(styles, self.renderer_desc)
                 if style.orientation == STYLE_L_ORIENT])
        else:
            plot.y_axis.title = self.y_axis_title

        font_size = self.plot_style.y_axis_style.title_style.font_size
        font_name = self.plot_style.y_axis_style.title_style.font_name
        plot.y_axis.title_font = '{} {}'.format(font_name, font_size)

    def _set_second_y_axis_labels(self, plot):
        if not hasattr(plot, "second_y_axis"):
            return

        if self.second_y_axis_title == "auto":
            styles = self.plot_style.renderer_styles
            plot.second_y_axis.title = ", ".join(
                [desc["y"] for style, desc in zip(styles, self.renderer_desc)
                 if style.orientation == STYLE_R_ORIENT])
        else:
            plot.y_axis.title = self.second_y_axis_title

        font_size = self.plot_style.second_y_axis_style.title_style.font_size
        font_name = self.plot_style.second_y_axis_style.title_style.font_name
        plot.second_y_axis.title_font = '{} {}'.format(font_name, font_size)

    def _set_title_label(self, plot):
        font_size = self.plot_style.title_style.font_size
        font_name = self.plot_style.title_style.font_name
        font = '{} {}'.format(font_name, font_size)
        title_label = PlotLabel(self.plot_title, component=plot, font=font,
                                overlay_position="top")
        plot.overlays.append(title_label)
        plot.title = title_label


class StdXYPlotFactory(BasePlotFactory):
    """ Factory to create a 2D plot with one of more renderers of the same kind
    """
    #: Number of DF columns involved in making the plot
    ndim = Int

    #: List of plot_data keys to plot in pairs, one pair per renderer
    renderer_desc = List(Dict)

    #: Renderer list, mapped to their name
    renderers = Dict

    #: Colorbar built to describe the data's z dimension (for select types)
    colorbar = Instance(ColorBar)

    def __init__(self, x_arr=None, y_arr=None, z_arr=None, hover_data=None,
                 **traits):
        super(StdXYPlotFactory, self).__init__(**traits)

        if isinstance(x_arr, pd.Series):
            x_arr = x_arr.values

        if isinstance(y_arr, pd.Series):
            y_arr = y_arr.values

        if isinstance(y_arr, pd.Series):
            z_arr = z_arr.values

        if hover_data is None:
            hover_data = {}

        if self.plot_data is None:
            self.initialize_plot_data(x_arr=x_arr, y_arr=y_arr, z_arr=z_arr,
                                      **hover_data)

        if self.z_col_name:
            self.ndim = 3
        else:
            self.ndim = 2

        self.adjust_plot_style(x_arr=x_arr, y_arr=y_arr, z_arr=z_arr)

    def adjust_plot_style(self, x_arr=None, y_arr=None, z_arr=None):
        """ Translate general plotting style info into xy plot parameters.
        """
        pass

    def initialize_plot_data(self, x_arr=None, y_arr=None, z_arr=None,
                             **adtl_arrays):
        """ Set the plot_data and the list of renderer descriptions.

        If the data arrays are dictionaries rather than straight arrays, they
        describe multiple renderers.
        """
        if x_arr is None or y_arr is None:
            msg = "2D plots require a valid plot_data or an array for both x" \
                  " and y."
            logger.exception(msg)
            raise ValueError(msg)

        if isinstance(x_arr, np.ndarray):
            data_map = self._plot_data_single_renderer(
                x_arr, y_arr, z_arr, **adtl_arrays
            )
        elif isinstance(x_arr, dict):
            assert set(x_arr.keys()) == set(y_arr.keys())
            data_map = self._plot_data_multi_renderer(
                x_arr, y_arr, z_arr, **adtl_arrays
            )
        else:
            msg = "x_arr/y_arr should be either an array or a dictionary " \
                  "mapping the z/hue value to the corresponding x array, but" \
                  " {} ({}) was passed."
            msg = msg.format(x_arr, type(x_arr))
            raise ValueError(msg)

        self.plot_data = ArrayPlotData(**data_map)
        return data_map

    def _plot_data_single_renderer(self, x_arr=None, y_arr=None, z_arr=None,
                                   **adtl_arrays):
        """ Build the data_map to build the plot data.
        """
        data_map = {self.x_col_name: x_arr, self.y_col_name: y_arr}
        data_map.update(adtl_arrays)
        renderer_data = {"x": self.x_col_name, "y": self.y_col_name,
                         "name": DEFAULT_RENDERER_NAME}
        self.renderer_desc = [renderer_data]
        return data_map

    def _plot_data_multi_renderer(self, x_arr=None, y_arr=None, z_arr=None,
                                  **adtl_arrays):
        """ Built the data_map to build the plot data for multiple renderers.
        """
        data_map = {}
        for i, hue_val in enumerate(sorted(x_arr.keys())):
            hue_name, x_name, y_name = self._add_arrays_for_hue(
                data_map, x_arr, y_arr, hue_val, i, adtl_arrays
            )
            renderer_data = {"x": x_name, "y": y_name, "name": hue_name}
            self._hue_values.append(hue_name)
            self.renderer_desc.append(renderer_data)

        return data_map

    def _add_arrays_for_hue(self, data_map, x_arr, y_arr, hue_val, hue_val_idx,
                            adtl_arrays):
        """ Build and collect all arrays to add to ArrayPlotData for hue value.
        """
        hue_name = str(hue_val)
        x_name = self._plotdata_array_key(self.x_col_name, hue_name)
        y_name = self._plotdata_array_key(self.y_col_name, hue_name)
        data_map[x_name] = x_arr[hue_val]
        data_map[y_name] = y_arr[hue_val]
        # Collect any additional dataset that needs to be stored (for
        # e.g. to feed plot tools)
        for adtl_col, col_data in adtl_arrays.items():
            key = self._plotdata_array_key(adtl_col, hue_name)
            data_map[key] = col_data[hue_val]
        return hue_name, x_name, y_name

    def _plotdata_array_key(self, col_name, hue_name=""):
        """ Name of the ArrayPlotData containing the array from specified col.

        Parameters
        ----------
        col_name : str
            Name of the column being displayed.

        hue_name : str
            Name of the renderer color the array will be used in. Typically the
            coloring column value, converted to string.
        """
        return col_name + hue_name

    def generate_plot(self):
        """ Generate and return a line plot & a dict describing its properties.

        Returns
        -------
        dict
            Dictionary containing the generated plot and all the information
            about it to create a PlotDescriptor.
        """
        plot = OverlayPlotContainer(
            **self.plot_style.container_style.to_traits()
        )

        # Emulate chaco.Plot interface:
        plot.data = self.plot_data

        self.add_renderers(plot)

        self.set_axis_labels(plot)

        if len(self.renderer_desc) > 1:
            self.set_legend(plot)

        self.add_tools(plot)

        # Build a description of the plot to build a PlotDescriptor
        desc = dict(plot_type=self.plot_type, plot=plot, visible=True,
                    plot_title=self.plot_title, x_col_name=self.x_col_name,
                    y_col_name=self.y_col_name, x_axis_title=self.x_axis_title,
                    y_axis_title=self.y_axis_title, z_col_name=self.z_col_name,
                    z_axis_title=self.z_axis_title, ndim=self.ndim)

        self.add_colorbar(desc)

        return desc

    def add_colorbar(self, desc):
        # FIXME: what plot factories need this? Reconcile with ScatterFactory.
        if self.plot_style.container_style.include_colorbar:
            plot = desc["plot"]
            # Make more room for labels
            plot.padding_right = 5
            plot.padding_top = 25

            container = HPlotContainer(
                self.plot_style.container_style.to_traits()
            )
            container.add(plot, self.colorbar)
            container.padding_right = sum([comp.padding_right
                                           for comp in container.components])
            container.bgcolor = "transparent"
            desc["plot"] = container

    def add_tools(self, plot):
        """ Add pan and zoom tools.
        """
        broadcaster = BroadcasterTool()

        # IMPORTANT: add the broadcast tool to one of the renderers, NOT the
        # container. Otherwise, the box zoom will crop wrong:
        first_plot = plot.components[0]
        first_plot.tools.append(broadcaster)

        for i, plot in enumerate(plot.components):
            if "pan" in self.plot_tools:
                pan = PanTool(plot)
                broadcaster.tools.append(pan)

            if "zoom" in self.plot_tools:
                # FIXME: the zoom tool is added to the broadcaster's tools
                #  attribute because it doesn't have an overlay list. That
                #  means the box plot mode won't display the blue box!
                zoom = ZoomTool(component=plot, zoom_factor=1.25)
                broadcaster.tools.append(zoom)

    def add_renderers(self, plot):
        """ Add all renderers to the plot container.

        TODO: use log/lin styling info to create axis objects.
        """
        styles = self.plot_style.renderer_styles
        if len(styles) != len(self.renderer_desc):
            msg = "Something went wrong: received {} styles and {} renderer " \
                  "descriptions.".format(len(styles), len(self.renderer_desc))
            logger.exception(msg)
            raise ValueError(msg)

        for i, (desc, style) in enumerate(zip(self.renderer_desc, styles)):
            style.renderer_name = desc["name"]
            renderer = self.build_renderer(desc, style)
            plot.add(renderer)
            self.renderers[desc["name"]] = renderer

            if i == 0:
                # if style.second_y_axis_style.scaling == LOG_AXIS_STYLE:
                #     x_mapper_klass = LogMapper
                # else:
                #     x_mapper_klass = LinearMapper

                left_axis, bottom_axis = add_default_axes(renderer)
                # Add to plot (displays) and keep a handle on the axis objects:
                plot.x_axis = bottom_axis
                plot.y_axis = left_axis
            else:
                if style.orientation == STYLE_R_ORIENT and not \
                        hasattr(plot, "second_y_axis"):
                    # if style.second_y_axis_style.scaling == LOG_AXIS_STYLE:
                    #     mapper_klass = LogMapper
                    # else:
                    #     mapper_klass = LinearMapper

                    second_y_axis = PlotAxis(component=renderer,
                                             orientation="right")
                    renderer.underlays.append(second_y_axis)
                    # Keep a handle on the axis object:
                    plot.second_y_axis = second_y_axis

        # Align all renderers in index and value dimension:
        all_renderers = self.renderers.values()
        align_renderers(all_renderers, plot.x_axis, dim="index")
        if hasattr(plot, "second_y_axis"):
            l_renderers = [rend for rend, style in zip(all_renderers, styles)
                           if style.orientation == STYLE_L_ORIENT]
            r_renderers = [rend for rend, style in zip(all_renderers, styles)
                           if style.orientation == STYLE_R_ORIENT]
            align_renderers(l_renderers, plot.y_axis, dim="value")
            align_renderers(r_renderers, plot.second_y_axis, dim="value")
        else:
            align_renderers(all_renderers, plot.y_axis, dim="value")

    def build_renderer(self, desc, style):
        renderer_maker = RENDERER_MAKER[style.renderer_type]
        x = self.plot_data.get_data(desc["x"])
        y = self.plot_data.get_data(desc["y"])
        return renderer_maker(data=(x, y), **style.to_plot_kwargs())

    def set_legend(self, plot, align="ur", padding=10, drag_button="right"):
        """ Add legend and make it relocatable & clickable.
        """
        # Make sure plot list in legend doesn't include error bar renderers:
        # legend_labels = [desc["name"] for desc in self.renderer_desc]
        legend = Legend(component=plot, padding=padding, align=align,
                        title=self.z_axis_title)  # , labels=legend_labels
        legend.plots = self.renderers
        if "legend" in self.plot_tools:
            legend.tools.append(LegendTool(component=legend,
                                           drag_button=drag_button))
            legend.tools.append(LegendHighlighter(component=legend))
            legend.visible = True
            plot.overlays.append(legend)
