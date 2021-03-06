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

from traits.api import Any, Dict, HasStrictTraits, Instance, List, Set, Str
from chaco.api import ArrayPlotData, ColorBar, DataRange1D, HPlotContainer, \
    LabelAxis, LinearMapper, LogMapper, PlotAxis, PlotLabel

from chaco.plot_factory import add_default_axes
from chaco.tools.api import BroadcasterTool, LegendTool, PanTool, ZoomTool
from chaco.ticks import DefaultTickGenerator, ShowAllTickGenerator
from enable.tools.pyface.context_menu_tool import ContextMenuTool

from app_common.chaco.overlay_plot_container_utils import align_renderers
from app_common.chaco.plot_factory import create_bar_plot, \
    create_cmap_scatter_plot, create_line_plot, create_scatter_plot
from app_common.chaco.legend import Legend, LegendHighlighter

from .axis_style import LOG_AXIS_STYLE
from .multi_mapper_plot import MultiMapperPlot
from .plot_context_menu_manager import PlotContextMenuManager
from .plot_style import BaseXYPlotStyle
from .renderer_style import STYLE_L_ORIENT, STYLE_R_ORIENT

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

    #: Styling of the plot and renderer(s)
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

    #: list of tools requested on the plot/renderers
    plot_tools = Set

    #: Inspector tool and overlay to hover over or select scatter data points
    inspector = Any

    #: Color of the marker once selected
    inspector_selection_color = Str(SELECTION_COLOR)

    #: Name(s) of the column(s) to display on mouse hover
    hover_col_names = List

    #: Handling of context menu generation and events
    context_menu_manager = Instance(PlotContextMenuManager, ())

    def generate_plot(self):
        raise NotImplementedError("Base class: use subclass.")

    def set_axis_labels(self, plot):
        """ Set the plot and axis labels of a chaco Plot.

        Parameters
        ----------
        plot : MultiMapperPlot
            Instance of a MultiMapperPlot to set the axis and title
            labels of.
        """
        self._set_x_axis_labels(plot)
        self._set_y_axis_labels(plot)
        self._set_second_y_axis_labels(plot)
        self._set_title_label(plot)

    def _set_x_axis_labels(self, plot):
        """ Set the x axis title, tick labels and styles.
        """
        x_labels = self.x_labels
        x_axis_style = self.plot_style.x_axis_style
        if x_labels:
            # if x_labels set, axis labels shouldn't be generated from the
            # numerical values but by the values stored in x_labels (for e.g.
            # when x_axis_col contains strings)
            label_rotation = x_axis_style.label_rotation
            if x_axis_style.show_all_labels:
                label_positions = range(len(x_labels))
                tick_generator = ShowAllTickGenerator(
                    positions=label_positions
                )
            else:
                tick_generator = DefaultTickGenerator()

            first_renderer = plot.components[0]
            bottom_axis = LabelAxis(first_renderer, orientation="bottom",
                                    labels=[str(x) for x in x_labels],
                                    positions=np.arange(len(x_labels)),
                                    label_rotation=label_rotation,
                                    tick_generator=tick_generator)
            # Replace in the underlay list...
            if plot.underlays:
                plot.underlays.pop(0)
            plot.underlays.insert(0, bottom_axis)
            # ... and add a handle from the plot object to emulate chaco.Plot
            plot.x_axis = bottom_axis

        plot.x_axis.title = self.x_axis_title
        font_size = x_axis_style.title_style.font_size
        font_name = x_axis_style.title_style.font_name
        plot.x_axis.title_font = '{} {}'.format(font_name, font_size)

    def _set_y_axis_labels(self, plot):
        """ Set the y axis title and style.
        """
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
        """ Set the secondary y axis title and style.
        """
        if plot.second_y_axis is None:
            return

        if self.second_y_axis_title == "auto":
            styles = self.plot_style.renderer_styles
            plot.second_y_axis.title = ", ".join(
                [desc["y"] for style, desc in zip(styles, self.renderer_desc)
                 if style.orientation == STYLE_R_ORIENT])
        else:
            plot.second_y_axis.title = self.second_y_axis_title

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
    #: Generated chaco plot containing all requested renderers
    plot = Instance(MultiMapperPlot)

    #: List of plot_data keys to plot in pairs, one pair per renderer
    renderer_desc = List(Dict)

    #: Renderer list, mapped to their name
    renderers = Dict

    #: Optional legend object to be added to the future plot
    legend = Instance(Legend)

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
        """ Generate and return a dict containing a plot and its properties.
        """
        plot = self.plot = MultiMapperPlot(
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
                    z_axis_title=self.z_axis_title, plot_factory=self)

        if self.plot_style.container_style.include_colorbar:
            self.generate_colorbar(desc)
            self.add_colorbar(desc)

        return desc

    def add_tools(self, plot):
        """ Add all tools specified in plot_tools list to provided plot.
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
                zoom = ZoomTool(component=plot, zoom_factor=1.15)
                broadcaster.tools.append(zoom)

        if "legend" in self.plot_tools and self.legend:
            legend = self.legend
            legend.tools.append(LegendTool(component=self.legend,
                                           drag_button="right"))
            legend.tools.append(LegendHighlighter(component=legend))

        if "context_menu" in self.plot_tools:
            self.context_menu_manager.target = self.plot
            menu = self.context_menu_manager.build_menu()
            context_menu = ContextMenuTool(component=self.plot,
                                           menu_manager=menu)

            self.plot.tools.append(context_menu)

    def add_renderers(self, plot):
        """ Add all renderers to provided plot container.
        """
        styles = self.plot_style.renderer_styles
        if len(styles) != len(self.renderer_desc):
            msg = "Something went wrong: received {} styles and {} renderer " \
                  "descriptions.".format(len(styles), len(self.renderer_desc))
            logger.exception(msg)
            raise ValueError(msg)

        for i, (desc, style) in enumerate(zip(self.renderer_desc, styles)):
            first_renderer = i == 0
            self.add_renderer(plot, desc, style, first_renderer=first_renderer)

        self.align_all_renderers(plot)

    def add_renderer(self, plot, desc, style, first_renderer=False):
        """ Create and add to plot renderer described by desc and style.

        If the axis it is displayed along isn't already created, create it too,
        and add it to the plot's list of underlays.
        """
        # Modify the renderer's style's name so it is displayed in the style
        # view:
        style.renderer_name = desc["name"]
        renderer = self._build_renderer(desc, style)
        plot.add(renderer)
        self.renderers[desc["name"]] = renderer

        if first_renderer:
            left_axis, bottom_axis = add_default_axes(renderer)
            # Emulate chaco.Plot interface:
            plot.x_axis = bottom_axis
            plot.y_axis = left_axis
            renderer.underlays = []
            plot.underlays = [bottom_axis, left_axis]
        else:
            if style.orientation == STYLE_R_ORIENT and \
                    plot.second_y_axis is None:
                is_log = self.plot_style.second_y_axis_style.scaling == \
                    LOG_AXIS_STYLE
                if is_log:
                    mapper_klass = LogMapper
                else:
                    mapper_klass = LinearMapper

                # The range needs to be initialized to the axis can be aligned
                # with all secondary y axis renderers:
                mapper = mapper_klass(range=DataRange1D())
                second_y_axis = PlotAxis(component=renderer,
                                         orientation="right",
                                         mapper=mapper)
                plot.second_y_axis = second_y_axis
                plot.underlays.append(second_y_axis)

        return renderer

    def align_all_renderers(self, plot):
        """ Align all renderers in index and value dimensions to plot's axis.

        This method is used to keep renderers aligned with the displayed axes
        once their ranges have been set.
        """
        all_renderers = self.renderers.values()
        if len(all_renderers) <= 1:
            return

        styles = self.plot_style.renderer_styles
        align_renderers(all_renderers, plot.x_axis, dim="index")
        if plot.second_y_axis is not None:
            l_renderers = [rend for rend, style in zip(all_renderers, styles)
                           if style.orientation == STYLE_L_ORIENT]
            r_renderers = [rend for rend, style in zip(all_renderers, styles)
                           if style.orientation == STYLE_R_ORIENT]
            align_renderers(l_renderers, plot.y_axis, dim="value")
            align_renderers(r_renderers, plot.second_y_axis, dim="value")
        else:
            align_renderers(all_renderers, plot.y_axis, dim="value")

    def _build_renderer(self, desc, style):
        """ Invoke appropriate renderer factory to build and return renderer.
        """
        renderer_maker = RENDERER_MAKER[style.renderer_type]
        x = self.plot_data.get_data(desc["x"])
        y = self.plot_data.get_data(desc["y"])
        if self.plot_style.x_axis_style.scaling == LOG_AXIS_STYLE:
            x_mapper_class = LogMapper
        else:
            x_mapper_class = LinearMapper

        if style.orientation == STYLE_L_ORIENT:
            y_style = self.plot_style.y_axis_style
        else:
            y_style = self.plot_style.second_y_axis_style

        if y_style.scaling == LOG_AXIS_STYLE:
            y_mapper_class = LogMapper
        else:
            y_mapper_class = LinearMapper

        return renderer_maker(data=(x, y), index_mapper_class=x_mapper_class,
                              value_mapper_class=y_mapper_class,
                              **style.to_plot_kwargs())

    def set_legend(self, plot, align="ur", padding=10):
        """ Add legend and make it relocatable & clickable if tools requested.

        FIXME: Add control over legend labels.
        """
        # Make sure plot list in legend doesn't include error bar renderers:
        # legend_labels = [desc["name"] for desc in self.renderer_desc]
        legend = Legend(component=plot, padding=padding, align=align,
                        title=self.z_axis_title)
        legend.plots = self.renderers
        legend.visible = True
        plot.overlays.append(legend)
        # Emulate chaco.Plot-like behavior:
        self.legend = legend

    # Post creation renderer management methods -------------------------------

    def update_renderers_from_data(self, removed=None):
        """ The plot_data was updated: update/remove existing renderers.
        """
        if removed is None:
            removed = []

        rend_desc_map = {}
        for desc in self.renderer_desc:
            rend_desc_map[desc["name"]] = desc

        rend_name_list = list(self.renderers.keys())
        for name in rend_name_list:
            renderer = self.renderers[name]
            desc = rend_desc_map[name]

            both_removed = desc["x"] in removed and desc["y"] in removed
            one_removed = (desc["x"] in removed and desc["y"] not in removed) \
                or (desc["x"] not in removed and desc["y"] in removed)
            if both_removed:
                self.remove_renderer(desc)
            elif one_removed:
                msg = "Unable to update the renderer {}: the data seems to be"\
                      " incomplete because x was set as removed and not y or" \
                      " vice versa. Removed keys: {}. Please report this " \
                      "issue.".format(desc["name"], removed)
                logger.exception(msg)
                raise ValueError(msg)
            else:
                x = self.plot_data.get_data(desc["x"])
                y = self.plot_data.get_data(desc["y"])
                renderer.index.set_data(x)
                renderer.value.set_data(y)

    def remove_renderer(self, rend_desc):
        """ Remove renderer described by provided descriptor from current plot.
        """
        rend_name = rend_desc["name"]
        renderer = self.renderers.pop(rend_name)

        self.plot.remove(renderer)

        rend_idx = 0
        for desc in self.renderer_desc:
            if desc["name"] == rend_name:
                self.renderer_desc.pop(rend_idx)
                self.plot_style.renderer_styles.pop(rend_idx)
                break

            rend_idx += 1

        if self.legend:
            self.legend.plots.pop(rend_name)

    def append_new_renderers(self, desc_list, styles):
        """ Append new renderers to an existing factory plot.
        """
        num_existing_renderers = len(self.renderer_desc)
        for i, (rend_desc, rend_style) in enumerate(zip(desc_list, styles)):
            rend_idx = num_existing_renderers + i
            renderer = self.add_renderer(self.plot, rend_desc, rend_style,
                                         first_renderer=rend_idx == 0)
            self.renderer_desc.append(rend_desc)
            self.plot_style.renderer_styles.append(rend_style)

            if self.legend:
                self.legend.plots[rend_desc["name"]] = renderer

    # Traits initialization methods -------------------------------------------

    def _plot_tools_default(self):
        return {"zoom", "pan", "legend", "context_menu"}


class CmapedXYPlotFactoryMixin(HasStrictTraits):
    """ Mixing class to add to a factory to support color-mapped renderer.
    """
    #: Colorbar built to describe the data's z dimension (for select types)
    colorbar = Instance(ColorBar)

    def generate_colorbar(self, desc):
        """ Generate the colorbar to be displayed along side the main plot.
        """
        plot = desc["plot"]
        renderer = self._get_cmap_renderer()

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
                       title_angle=90.0, title_font=font)
        self.colorbar._axis.trait_set(**axis_kw)

    def _get_cmap_renderer(self):
        renderers = self.renderers.values()
        cmap_renderers = [rend for rend in renderers
                          if self.is_colormapped_renderer(rend)]
        if len(cmap_renderers) > 1:
            msg = "Unable to generate a colorbar since there are {}" \
                  " color mapped renderers.".format(len(cmap_renderers))
            logger.exception(msg)
            raise ValueError(msg)
        elif len(cmap_renderers) == 0:
            msg = "No color mapped renderer found: no colorbar to make."
            logger.exception(msg)
            raise ValueError(msg)

        return cmap_renderers[0]

    def add_colorbar(self, desc):
        """ Colorbar generated: embed it together with plot & replace in desc.
        """
        plot = desc["plot"]
        container = HPlotContainer(
            **self.plot_style.container_style.to_traits()
        )
        container.add(plot, self.colorbar)
        container.padding_right = sum([comp.padding_right
                                       for comp in container.components])
        container.bgcolor = "transparent"
        desc["plot"] = container

    def is_colormapped_renderer(self, renderer):
        return hasattr(renderer, "color_mapper")
