
from traits.api import Any, Button, Enum, Float, HasStrictTraits, Int, List, \
    Property, Range, Str, Trait, Tuple
from traitsui.api import EnumEditor, HGroup, Item, RangeEditor, VGroup, View
from chaco.default_colormaps import color_map_name_dict
from enable.markers import MarkerNameDict, marker_names
from enable.api import ColorTrait, LineStyle

from ..utils.chaco_colors import ALL_CHACO_PALETTES
from ..utils.string_definitions import DEFAULT_CONTIN_PALETTE

DEFAULT_RENDERER_COLOR = "blue"

DEFAULT_MARKER_SIZE = 6

DEFAULT_LINE_WIDTH = 1.3

STYLE_L_ORIENT = "left"

STYLE_R_ORIENT = "right"

REND_TYPE_LINE = "line"

REND_TYPE_SCAT = "scatter"

REND_TYPE_CMAP_SCAT = "cmap_scatter"


class BaseRendererStyle(HasStrictTraits):
    """ Styling object for customizing scatter renderers.
    """
    #: Name of the renderer type, used to select the renderer factory.
    renderer_type = ""

    #: Name of the renderer as referenced in the plot container.
    # Used by the PlotStyle to frame views.
    renderer_name = Str

    #: View elements for users to control these parameters
    general_view_elements = Property(List)

    #: View klass. Override to customize the view, for example its icon
    view_klass = Any(default_value=View)

    #: List of attributes to convert to kwargs for the Plot.plot method
    dict_keys = List

    def to_plot_kwargs(self):
        """ Supports converting renderer styles into a dict of kwargs for the
        renderer factory function/method.
        """
        kwargs = {}
        for key in self.dict_keys:
            if isinstance(key, tuple):
                key, target_key = key
            else:
                target_key = key

            kwargs[target_key] = getattr(self, key)
        return kwargs


class BaseXYRendererStyle(BaseRendererStyle):
    """ Styling object for customizing scatter renderers.
    """
    #: Color of the renderer
    color = ColorTrait(DEFAULT_RENDERER_COLOR)

    #: Transparency of the renderer
    alpha = Range(value=1., low=0., high=1.)

    #: Which y-axis to be displayed along
    orientation = Enum([STYLE_L_ORIENT, STYLE_R_ORIENT])

    # Traits property getter/setter -------------------------------------------

    def _get_general_view_elements(self):
        elements = (
            VGroup(
                HGroup(
                    Item('color'),
                    Item('alpha', label="Transparency"),
                ),
                Item("orientation", label="Y-axis"),
            ),
        )
        return elements

    def _dict_keys_default(self):
        return ["color", "alpha"]


class ScatterRendererStyle(BaseXYRendererStyle):
    """ Styling object for customizing scatter renderers.
    """
    #: Type of the renderer
    renderer_type = REND_TYPE_SCAT

    #: The type of marker to use
    marker = Trait("circle", MarkerNameDict,
                   editor=EnumEditor(values=marker_names))

    #: The size of the marker
    marker_size = Int(DEFAULT_MARKER_SIZE)

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                HGroup(
                    Item('marker', label="Marker"),
                    Item('marker_size',
                         editor=RangeEditor(low=1, high=20)),
                ),
                *self.general_view_elements
            ),
        )
        return view

    def _dict_keys_default(self):
        general_items = super(ScatterRendererStyle, self)._dict_keys_default()
        return general_items + ["marker", "marker_size"]


class CmapScatterRendererStyle(ScatterRendererStyle):

    #: Type of the renderer
    renderer_type = REND_TYPE_CMAP_SCAT

    #: Name of the palette to pick colors from in z direction
    color_palette = Enum(ALL_CHACO_PALETTES)

    #: Transparency of the marker coloring
    fill_alpha = Range(value=1., low=0., high=1.)

    #: Chaco color mapper to provide to plot.plot for a cmap_scatter type
    color_mapper = Property(Any, depends_on="color_palette")

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                Item('color_palette'),
                HGroup(
                    Item('marker', label="Marker"),
                    Item('marker_size',
                         editor=RangeEditor(low=1, high=20)),
                ),
                HGroup(
                    Item('fill_alpha', label="Transparency"),
                ),
            ),
        )
        return view

    # Traits property getters/setters -----------------------------------------

    def _get_color_mapper(self):
        return color_map_name_dict[self.color_palette]

    # Traits initialization methods -------------------------------------------

    def _dict_keys_default(self):
        return ["fill_alpha", "color_mapper", "marker", "marker_size"]

    def _color_palette_default(self):
        return DEFAULT_CONTIN_PALETTE


class LineRendererStyle(BaseXYRendererStyle):
    """ Styling object for customizing line renderers.
    """
    renderer_type = REND_TYPE_LINE

    line_width = Float(DEFAULT_LINE_WIDTH)

    line_style = LineStyle("solid")

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                HGroup(
                    Item('line_width', label="Line width"),
                    Item('line_style', label="Line style", style="custom"),
                ),
                *self.general_view_elements
            ),
        )
        return view

    def _dict_keys_default(self):
        general_items = super(LineRendererStyle, self)._dict_keys_default()
        new = [("line_width", "width"), ("line_style", "dash")]
        return general_items + new


class BarRendererStyle(BaseXYRendererStyle):
    """ Styling object for customizing line renderers.
    """
    #: Name of the
    renderer_type = "bar"

    #: Width of each bar. Leave as 0 to have it computed programmatically.
    bar_width = Float

    #: Color of the contours of the bars
    line_color = ColorTrait(DEFAULT_RENDERER_COLOR)

    #: Color of the inside of the bars
    fill_color = ColorTrait(DEFAULT_RENDERER_COLOR)

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                Item('bar_width'),
                HGroup(
                    Item('color'),
                    Item('alpha', label="Transparency"),
                ),
                Item("orientation", label="Y-axis"),
            ),
        )
        return view

    def _color_changed(self, new):
        # Needed so plot style can control the renderer colors
        self.fill_color = new
        self.line_color = new

    def _dict_keys_default(self):
        return ["bar_width", "line_color", "fill_color", "alpha"]


class HeatmapRendererStyle(BaseRendererStyle):
    """ Styling class for heatmap renderers (cmapped image plot).
    """
    #: Transparency of the renderer
    alpha = Range(value=1., low=0., high=1.)

    #: Name of the palette to pick colors from in color direction
    color_palette = Enum(ALL_CHACO_PALETTES)

    #: Chaco color mapper to provide to plot.plot for a cmap_scatter type
    colormap = Property(Any, depends_on="color_palette")

    # Note: this count be encoded in an AxisStyle
    xbounds = Tuple((0, 1))

    auto_xbounds = Tuple((0, 1))

    ybounds = Tuple((0, 1))

    auto_ybounds = Tuple((0, 1))

    reset_xbounds = Button("Reset")

    reset_ybounds = Button("Reset")

    def __init__(self, **traits):
        if "xbounds" in traits and "auto_xbounds" not in traits:
            traits["auto_xbounds"] = traits["xbounds"]

        if "ybounds" in traits and "auto_ybounds" not in traits:
            traits["auto_ybounds"] = traits["ybounds"]

        super(HeatmapRendererStyle, self).__init__(**traits)

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                HGroup(
                    Item('color_palette'),
                    Item('alpha', label="Transparency"),
                ),
                HGroup(
                    Item('xbounds'),
                    Item('reset_xbounds', show_label=False),
                ),
                HGroup(
                    Item('ybounds'),
                    Item('reset_ybounds', show_label=False),
                ),
            ),
        )
        return view

    # Traits listener methods -------------------------------------------------

    def _reset_xbounds_fired(self):
        self.xbounds = self.auto_xbounds

    def _reset_ybounds_fired(self):
        self.ybounds = self.auto_ybounds

    # Traits initialization methods -------------------------------------------

    def _get_colormap(self):
        if self.color_palette in color_map_name_dict:
            return color_map_name_dict[self.color_palette]

    def _color_palette_default(self):
        return DEFAULT_CONTIN_PALETTE

    def _dict_keys_default(self):
        return ["colormap", "xbounds", "ybounds"]
