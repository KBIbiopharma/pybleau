""" These are styling objects to control and view styling entire chaco plots
(`Plot` and `OverlayPlotContainer` instances)
"""
from traits.api import Any, Bool, Dict, Enum, Float, Instance, List, Property
from traitsui.api import HGroup, InstanceEditor, Item, \
    OKCancelButtons, Tabbed, VGroup, View
from chaco.api import LinePlot, Plot

from pybleau.app.utils.chaco_colors import ALL_CHACO_PALETTES, ALL_MPL_PALETTES
from pybleau.app.plotting.axis_style import AxisStyle
from pybleau.app.plotting.title_style import TitleStyle
from pybleau.app.plotting.renderer_style import BaseXYRendererStyle
from pybleau.app.plotting.serializable import Serializable
from pybleau.app.plotting.renderer_style import LineRendererStyle, \
    ScatterRendererStyle

DEFAULT_DIVERG_PALETTE = "hsv"

DEFAULT_CONTIN_PALETTE = "cool"

SPECIFIC_CONFIG_CONTROL_LABEL = "Specific controls"


class BaseXYPlotStyle(Serializable):
    """ Styling parameters for building X-Y Chaco plots.

    These objects are designed to be used by PlotFactories to control the
    styling during the generation of a plot, but also be embedded inside
    traits-based app views.
    """
    #: Styling controls for each renderer contained in the plot
    renderer_styles = List(Instance(BaseXYRendererStyle))

    #: Font used to draw the plot title
    title_style = Instance(TitleStyle, ())

    #: Styling elements for the x-axis
    x_axis_style = Instance(AxisStyle)

    #: Styling elements for the x-axis
    y_axis_style = Instance(AxisStyle)

    #: View klass. Override to customize the view, for example its icon
    view_klass = Any(default_value=View)

    #: Default view elements for X-Y plots
    view_elements = Property(List)

    #: Hook to add additional view elements for specific plots
    specific_view_elements = Property(List)

    #: Keywords passed to create the view
    view_kw = Dict

    def initialize_axis_ranges(self, plot, x_mapper=None, y_mapper=None,
                               transform=None):
        """ Initialize the axis ranges from provided Plot or renderer.
        """
        if transform is None:
            def transform(x):
                return x

        elif isinstance(transform, int):
            ndigits = transform

            def transform(x):
                return round(x, ndigits)

        if x_mapper is None:
            if isinstance(plot, Plot):
                x_mapper = plot.x_axis.mapper
            elif isinstance(plot, LinePlot):
                x_mapper = plot.index_mapper
            else:
                msg = "Unsupported plot type: {}".format(type(plot))
                raise ValueError(msg)

        if y_mapper is None:
            if isinstance(plot, Plot):
                y_mapper = plot.y_axis.mapper
            elif isinstance(plot, LinePlot):
                y_mapper = plot.value_mapper
            else:
                msg = "Unsupported plot type: {}".format(type(plot))
                raise ValueError(msg)

        # Apply transform() to avoid UI polluted by non-sensical digits
        if x_mapper:
            self.x_axis_style.range_low = transform(x_mapper.range.low)
            self.x_axis_style.auto_range_low = self.x_axis_style.range_low
            self.x_axis_style.range_high = transform(x_mapper.range.high)
            self.x_axis_style.auto_range_high = self.x_axis_style.range_high
        if y_mapper:
            self.y_axis_style.range_low = transform(y_mapper.range.low)
            self.y_axis_style.auto_range_low = self.y_axis_style.range_low
            self.y_axis_style.range_high = transform(y_mapper.range.high)
            self.y_axis_style.auto_range_high = self.y_axis_style.range_high

    # Traits property getter/setter -------------------------------------------

    def traits_view(self):
        view = self.view_klass(*self.view_elements, **self.view_kw)
        return view

    def _get_specific_view_elements(self):
        return []

    def _get_view_elements(self):
        renderer_traits = {"renderer_{}".format(i): style
                           for i, style in enumerate(self.renderer_styles)}
        self.trait_set(**renderer_traits)

        items = [self._make_group_for_renderer(name)
                 for name in renderer_traits.keys()]

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
                    show_border=True, label="Axis controls"
                ),
                VGroup(*items,
                       show_border=True, label="Renderer controls"),
            )
        ]
        return elemens

    @staticmethod
    def _make_group_for_renderer(trait_name, renderer_name=""):
        """ Build a TraitsUI element to display a renderer style.

        Parameters
        ----------
        trait_name : str
            Name of the renderer style trait to be displayed.

        renderer_name : str
            User visible name of the curve. Leave empty if only 1 renderer is
            included.
        """
        return VGroup(
            Item(trait_name, editor=InstanceEditor(), style="custom",
                 show_label=False),
            show_border=True, label=renderer_name
        )

    # Traits initialization methods -------------------------------------------

    def _x_axis_style_default(self):
        return AxisStyle(axis_name="X")

    def _y_axis_style_default(self):
        return AxisStyle(axis_name="Y")

    def _view_kw_default(self):
        return dict(
            resizable=True,
            buttons=OKCancelButtons,
            title="Plot Styling",
        )

    def _dict_keys_default(self):
        return ["x_axis_style", "y_axis_style", "title_style",
                "renderer_styles"]


class BaseColorXYPlotStyle(BaseXYPlotStyle):
    """ Styling class for X-Y plots that have a color dimension (heatmap,
    color-coded scatters, ...)
    """
    #: Name of the palette to pick colors from in z direction
    color_palette = Enum(values="_all_palettes")

    #: List of available color palettes
    _all_palettes = List(ALL_MPL_PALETTES)

    #: Font used to draw the z (color) dimension title
    color_dim_title_style = Instance(TitleStyle, ())

    #: Number of bins: the bar width computed from that and the data range
    colormap_str = Enum(DEFAULT_CONTIN_PALETTE, values="_colormap_list")

    #: List of available colormaps
    _colormap_list = List(ALL_CHACO_PALETTES)

    #: Low value described by the colorbar
    colorbar_low = Float

    #: High value described by the colorbar
    colorbar_high = Float(1.0)

    colorbar_present = Bool

    def _get_specific_view_elements(self):
        return [
            VGroup(
                Item("color_palette"),
                VGroup(
                    Item("color_dim_title_style", editor=InstanceEditor(),
                         style="custom", show_label=False),
                    show_border=True, label="Color dim title"
                ),
                HGroup(
                    Item('colormap_str'),
                    Item('colorbar_low'),
                    Item('colorbar_high'),
                    show_border=True, label="colorbar",
                    visible_when="colorbar_present"),
            )
        ]

    def _dict_keys_default(self):
        general_items = super(BaseColorXYPlotStyle, self)._dict_keys_default()
        return general_items + ["color_palette", "color_dim_title_style",
                                "colormap_str", "colorbar_low",
                                "colorbar_high"]


# Single renderer implementations ---------------------------------------------


class SingleLinePlotStyle(BaseXYPlotStyle):
    def _renderer_styles_default(self):
        return [LineRendererStyle()]


class SingleScatterPlotStyle(BaseXYPlotStyle):
    def _renderer_styles_default(self):
        return [ScatterRendererStyle()]


if __name__ == "__main__":
    renderer_styles = [LineRendererStyle(), ScatterRendererStyle()]
    BaseXYPlotStyle(renderer_styles=renderer_styles).configure_traits()
