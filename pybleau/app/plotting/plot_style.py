""" These are styling objects to control and view styling entire chaco plots
(`Plot` and `OverlayPlotContainer` instances)
"""
import logging

from traits.api import Any, Bool, Callable, DelegatesTo, Dict, Enum, Float, \
    HasStrictTraits, HasTraits, Instance, List, Property, \
    observe
from traitsui.api import HGroup, InstanceEditor, Item, \
    OKCancelButtons, Tabbed, VGroup, View

from pybleau.app.plotting.axis_style import AxisStyle
from pybleau.app.plotting.plot_container_style import PlotContainerStyle
from pybleau.app.plotting.renderer_style import BaseRendererStyle, \
    LineRendererStyle, ScatterRendererStyle, STYLE_R_ORIENT
from pybleau.app.plotting.title_style import TitleStyle
from pybleau.app.utils.chaco_colors import ALL_MPL_PALETTES, \
    generate_chaco_colors
from pybleau.app.utils.string_definitions import DEFAULT_DIVERG_PALETTE

SPECIFIC_CONFIG_CONTROL_LABEL = "Specific controls"

logger = logging.getLogger(__name__)


class RendererStyleManager(HasTraits):
    """ Utility class to build a scrollable view of the renderer style list.
    """

    renderer_styles = List(Instance(BaseRendererStyle))

    #: View klass. Override to customize the view, for example its icon
    view_klass = Any(default_value=View)

    def traits_view(self):
        renderer_traits = {"renderer_{}".format(i): style
                           for i, style in enumerate(self.renderer_styles)}
        self.trait_set(**renderer_traits)

        rend_names = [style.renderer_name for style in self.renderer_styles]
        items = [self._make_group_for_renderer(style_idx, renderer_name=name)
                 for style_idx, name in enumerate(rend_names)]
        return self.view_klass(
            VGroup(*items),
            scrollable=True
        )

    @staticmethod
    def _make_group_for_renderer(style_idx, renderer_name=""):
        """ Build a TraitsUI element to display a renderer style.

        Parameters
        ----------
        style_idx : str
            Name of the renderer style trait to be displayed.

        renderer_name : str
            User visible name of the curve. Leave empty if only 1 renderer is
            included.
        """
        trait_name = "renderer_{}".format(style_idx)
        return VGroup(
            Item(trait_name, editor=InstanceEditor(), style="custom",
                 show_label=False),
            show_border=True, label=renderer_name
        )


class BaseXYPlotStyle(HasStrictTraits):
    """ Styling parameters for building X-Y Chaco plots.

    These objects are designed to be used by PlotFactories to control the
    styling during the generation of a plot, but also be embedded inside
    traits-based app views.
    """
    #: Utility object to render the styling controls for each renderer
    renderer_style_manager = Instance(RendererStyleManager, ())

    #: Access to the list of renderer styles
    renderer_styles = DelegatesTo("renderer_style_manager")

    #: Font used to draw the plot title
    title_style = Instance(TitleStyle, ())

    #: Styling for the plot container
    container_style = Instance(PlotContainerStyle, ())

    #: Styling elements for the x-axis
    x_axis_style = Instance(AxisStyle)

    #: Styling elements for the y-axis
    y_axis_style = Instance(AxisStyle)

    #: Styling elements for the secondary y-axis
    second_y_axis_style = Instance(AxisStyle)

    #: Whether there is a renderer to be displayed on the secondary y-axis
    _second_y_axis_present = Property(
        Bool, depends_on="renderer_style_manager.renderer_styles.orientation"
    )

    #: View klass. Override to customize the view, for example its icon
    view_klass = Any(default_value=View)

    #: Default view elements for X-Y plots
    view_elements = Property(List)

    #: Hook to add additional view elements for specific plots
    specific_view_elements = Property(List)

    #: Keywords passed to create the view
    view_kw = Dict

    #: Range value transformation function for eg. to avoid nonsensical digits
    range_transform = Callable

    def __init__(self, **traits):
        # Support passing the renderer_styles directly since the
        # renderer_style_manager is there just for UI layout:
        renderer_styles = None
        if "renderer_styles" in traits:
            renderer_styles = traits.pop("renderer_styles")

        super(BaseXYPlotStyle, self).__init__(**traits)

        self.renderer_style_manager.view_klass = self.view_klass
        if renderer_styles:
            self.renderer_style_manager.renderer_styles = renderer_styles

    def initialize_axis_ranges(self, plot, x_mapper=None, y_mapper=None,
                               second_y_mapper=None):
        """ Initialize all axis ranges from provided Plot (container).
        """
        x_mapper, y_mapper, second_y_mapper = self._get_plot_mappers(
            plot, x_mapper=x_mapper, y_mapper=y_mapper,
            second_y_mapper=second_y_mapper
        )

        transform = self.range_transform

        if x_mapper:
            x_axis_style = self.x_axis_style
            x_axis_style.range_low = transform(x_mapper.range.low)
            x_axis_style.auto_range_low = x_axis_style.range_low
            x_axis_style.range_high = transform(x_mapper.range.high)
            x_axis_style.auto_range_high = x_axis_style.range_high

        if y_mapper:
            y_axis_style = self.y_axis_style
            y_axis_style.range_low = transform(y_mapper.range.low)
            y_axis_style.auto_range_low = y_axis_style.range_low
            y_axis_style.range_high = transform(y_mapper.range.high)
            y_axis_style.auto_range_high = y_axis_style.range_high

        if second_y_mapper:
            self._init_second_y_axis_style_range(second_y_mapper)

    def _init_second_y_axis_style_range(self, second_y_mapper):
        """ Initialize the secondary y axis range.
        """
        transform = self.range_transform

        second_y_axis_style = self.second_y_axis_style
        second_y_axis_style.range_low = transform(second_y_mapper.range.low)
        second_y_axis_style.auto_range_low = second_y_axis_style.range_low
        second_y_axis_style.range_high = transform(second_y_mapper.range.high)
        second_y_axis_style.auto_range_high = second_y_axis_style.range_high

    def apply_axis_ranges(self, plot, x_mapper=None, y_mapper=None,
                          second_y_mapper=None):
        """ Apply to the plot's mappers the ranges stored in this style object.

        Parameters
        ----------
        plot : Plot, OverlayPlotContainer
            Plot to apply the style's ranges to.

        x_mapper : Mapper, optional
            Mapper to apply the x range values to.

        y_mapper : Mapper, optional
            Mapper to apply the y range values to.

        second_y_mapper : Mapper, optional
            Mapper to apply the secondary y range values to.
        """
        x_mapper, y_mapper, second_y_mapper = self._get_plot_mappers(
            plot, x_mapper=x_mapper, y_mapper=y_mapper,
            second_y_mapper=second_y_mapper
        )

        x_mapper.range.low = self.x_axis_style.range_low
        x_mapper.range.high = self.x_axis_style.range_high
        y_mapper.range.low = self.y_axis_style.range_low
        y_mapper.range.high = self.y_axis_style.range_high

        if second_y_mapper:
            second_y_axis_style = self.second_y_axis_style
            sec_low = second_y_axis_style.range_low
            sec_high = second_y_axis_style.range_high
            if sec_low == sec_high:
                # It was never initialized:
                self._init_second_y_axis_style_range(second_y_mapper)
            else:
                second_y_mapper.range.low = second_y_axis_style.range_low
                second_y_mapper.range.high = second_y_axis_style.range_high

    def traits_view(self):
        view = self.view_klass(
            *self.view_elements,
            **self.view_kw
        )
        return view

    # Traits property getter/setter -------------------------------------------

    def _get__second_y_axis_present(self):
        for style in self.renderer_styles:
            if style.orientation == STYLE_R_ORIENT:
                return True

        return False

    def _get_specific_view_elements(self):
        return []

    def _get_view_elements(self):
        elemens = [
            Tabbed(
                VGroup(
                    VGroup(
                        Item('title_style', editor=InstanceEditor(),
                             style="custom", show_label=False),
                        show_border=True, label="Title style",
                    ),
                    VGroup(
                        *self.specific_view_elements,
                        show_border=True, label=SPECIFIC_CONFIG_CONTROL_LABEL,
                        visible_when="len(specific_view_elements) > 0"
                    ),
                    show_border=True, label="General controls",
                ),
                VGroup(
                    VGroup(
                        Item("x_axis_style", editor=InstanceEditor(),
                             style="custom", show_label=False),
                        show_border=True, label="X-axis controls"
                    ),
                    VGroup(
                        Item("y_axis_style", editor=InstanceEditor(),
                             style="custom", show_label=False),
                        show_border=True, label="Y-axis controls"
                    ),
                    VGroup(
                        Item("second_y_axis_style", editor=InstanceEditor(),
                             style="custom", show_label=False),
                        show_border=True, label="Secondary Y-axis controls",
                        visible_when="_second_y_axis_present"
                    ),
                    show_border=True, label="Axis controls"
                ),
                VGroup(Item("renderer_style_manager", editor=InstanceEditor(),
                            style="custom", show_label=False),
                       show_border=True, label="Renderer controls"),
                VGroup(
                    Item("container_style", editor=InstanceEditor(),
                         style="custom", show_label=False),
                    show_border=True, label="Container controls"
                )
            )
        ]
        return elemens

    # Private interface -------------------------------------------------------

    def _get_plot_mappers(self, plot, x_mapper=None, y_mapper=None,
                          second_y_mapper=None):
        """ Retrieve the plot's mappers to synchronize with the style.

        Parameters
        ----------
        plot : Plot-like
            Chaco Plot-like class that holds up to 3 axis attributes to apply
            style ranges to: x_axis, y_axis and second_y_axis. Each must be an
            instance of a PlotAxis.

        x_mapper : Mapper
            Already identified Mapper to align with the x range.

        y_mapper : Mapper
            Already identified Mapper to align with the y range.

        second_y_mapper : Mapper
            Already identified Mapper to align with the secondary y range.

        Returns
        -------
        tuple
            The x_mapper, y_mapper and secondary_y_mapper found on provided
            plot.
        """
        missing_mapper_msg = "The plot is missing the attribute {}. Please " \
                             "provide the mapper explicitly"
        if x_mapper is None:
            if hasattr(plot, "x_axis"):
                x_mapper = plot.x_axis.mapper
            else:
                msg = missing_mapper_msg.format("x_axis")
                logger.exception(msg)
                raise ValueError(msg)

        if y_mapper is None:
            if hasattr(plot, "y_axis"):
                y_mapper = plot.y_axis.mapper
            else:
                msg = missing_mapper_msg.format("y_axis")
                logger.exception(msg)
                raise ValueError(msg)

        if second_y_mapper is None:
            if hasattr(plot, "second_y_axis"):
                second_y_mapper = plot.second_y_axis.mapper

        return x_mapper, y_mapper, second_y_mapper

    # Traits initialization methods -------------------------------------------

    def _x_axis_style_default(self):
        # Not always text labels along x but that's a possibility so enable
        # text label controls:
        return AxisStyle(axis_name="X", support_text_labels=True)

    def _y_axis_style_default(self):
        return AxisStyle(axis_name="Y")

    def _second_y_axis_style_default(self):
        return AxisStyle(axis_name="Second. Y")

    def _view_kw_default(self):
        return dict(
            resizable=True,
            buttons=OKCancelButtons,
            title="Plot Styling",
        )

    def _range_transform_default(self):
        return lambda x: x


class BaseColorXYPlotStyle(BaseXYPlotStyle):
    """ Styling class for X-Y plots that have a color dimension (heatmap,
    color-coded scatters, ...)
    """
    #: Name of the palette to pick colors when generating multiple renderers
    # (Ignored when colorizing by a float: then the renderer's palette is used)
    color_palette = Enum(DEFAULT_DIVERG_PALETTE, values="_all_palettes")

    #: List of possible palettes available for color_palette
    _all_palettes = List(ALL_MPL_PALETTES)

    #: Font used to draw the color dimension title
    color_axis_title_style = Instance(TitleStyle, ())

    #: Low value described by the colorbar
    colorbar_low = Float

    #: High value described by the colorbar
    colorbar_high = Float(1.0)

    #: Color-mapped plot or independent renderers? To be set programmatically.
    colorize_by_float = Bool

    # Traits property getters/setters -----------------------------------------

    def _get_specific_view_elements(self):
        return [
            VGroup(
                Item("color_palette", visible_when="not colorize_by_float"),
                VGroup(
                    Item("color_axis_title_style", editor=InstanceEditor(),
                         style="custom", show_label=False),
                    show_border=True, label="Color dim title"
                ),
                HGroup(
                    Item('colorbar_low'),
                    Item('colorbar_high'),
                    show_border=True, label="colorbar",
                    visible_when="colorize_by_float"),
            )
        ]

    # Traits listener methods -------------------------------------------------

    @observe("color_palette")
    def update_renderer_colors(self, event):
        """ Based on number of renderers & palette, initialize renderer colors.

        For color-mapped renderers, pass the palette straight.
        """
        num_renderer = len(self.renderer_styles)
        if num_renderer > 1 and not self.colorize_by_float:
            color_palette = self.color_palette
            colors = generate_chaco_colors(num_renderer, palette=color_palette)
            for i, color in enumerate(colors):
                renderer = self.renderer_styles[i]
                renderer.color = color


# Single renderer implementations ---------------------------------------------


class SingleLinePlotStyle(BaseXYPlotStyle):
    def _renderer_style_manager_default(self):
        return RendererStyleManager(renderer_styles=[LineRendererStyle()])


class SingleScatterPlotStyle(BaseXYPlotStyle):
    def _renderer_style_manager_default(self):
        return RendererStyleManager(renderer_styles=[ScatterRendererStyle()])
