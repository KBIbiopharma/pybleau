
from traits.api import Any, Button, Enum, Float, Int, List, Property, Range, \
    Str, Trait, Tuple
from traitsui.api import EnumEditor, HGroup, Item, RangeEditor, VGroup, View
from chaco.default_colormaps import color_map_name_dict
from enable.markers import MarkerNameDict, marker_names
from enable.api import ColorTrait, LineStyle

from .exportable import Exportable

DEFAULT_COLOR = "blue"

DEFAULT_MARKER_SIZE = 6

DEFAULT_LINE_WIDTH = 1.3


class BaseXYRendererStyle(Exportable):
    """ Styling object for customizing scatter renderers.
    """
    #: Color of the renderer
    color = ColorTrait(DEFAULT_COLOR)

    #: Transparency of the renderer
    alpha = Range(value=1., low=0., high=1.)

    #: Which y-axis to be displayed along
    orientation = Enum(["left", "right"])

    renderer_type = ""

    #: Name of the renderer as referenced in the plot container.
    # Used by the PlotStyle to frame views.
    renderer_name = Str

    #: View elements for users to control these parameters
    general_view_elements = Property(List)

    #: View klass. Override to customize the view, for example its icon
    view_klass = Any(default_value=View)

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                *self.general_view_elements
            ),
        )
        return view

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
    #: The type of marker to use
    marker = Trait("circle", MarkerNameDict,
                   editor=EnumEditor(values=marker_names))

    #: The size of the marker
    marker_size = Int(DEFAULT_MARKER_SIZE)

    renderer_type = "scatter"

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

    #: Name of the palette to pick colors from in z direction
    color_palette = Str

    #: Transparency of the marker coloring
    fill_alpha = Range(value=1., low=0., high=1.)

    #: Chaco color mapper to provide to plot.plot for a cmap_scatter type
    color_mapper = Any

    def traits_view(self):
        view = self.view_klass(
            VGroup(
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

    def _color_palette_changed(self):
        self.color_mapper = self._color_mapper_default()

    def _color_mapper_default(self):
        if self.color_palette in color_map_name_dict:
            return color_map_name_dict[self.color_palette]

    def _dict_keys_default(self):
        return ["fill_alpha", "color_mapper", "marker", "marker_size"]


class LineRendererStyle(BaseXYRendererStyle):
    """ Styling object for customizing line renderers.
    """
    line_width = Float(DEFAULT_LINE_WIDTH)

    line_style = LineStyle("solid")

    renderer_type = "line"

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                HGroup(
                    Item('line_width'),
                    Item('line_style', style="custom"),
                ),
                *self.general_view_elements
            ),
        )
        return view

    def _dict_keys_default(self):
        general_items = super(LineRendererStyle, self)._dict_keys_default()
        return general_items + ["line_width", "line_style"]


class BarRendererStyle(BaseXYRendererStyle):
    """ Styling object for customizing line renderers.
    """
    renderer_type = "bar"

    #: Width of each bar. Leave as 0 to have it computed programmatically.
    bar_width = Float

    #: Color of the contours of the bars
    line_color = ColorTrait(DEFAULT_COLOR)

    #: Color of the inside of the bars
    fill_color = ColorTrait(DEFAULT_COLOR)

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                Item('bar_width'),
                HGroup(
                    Item('line_color'),
                    Item('fill_color'),
                ),
                *self.general_view_elements
            ),
        )
        return view

    def _color_changed(self, new):
        # Bar renderers have 2 different color traits for the line and the
        # inside of the bar:
        self.line_color = new
        self.fill_color = new

    def _dict_keys_default(self):
        return ["bar_width", "line_color", "fill_color", "alpha"]


class CmapHeatmapRendererStyle(BaseXYRendererStyle):
    """ Styling class for heatmap renderers (cmapped image plot).
    """
    #: Name of the palette to pick colors from in color direction
    color_palette = Str

    #: Chaco color mapper to provide to plot.plot for a cmap_scatter type
    colormap = Any

    # Note: this count be encoded in an AxisStyle
    xbounds = Tuple((0, 1))

    auto_xbound = Tuple((0, 1))

    ybounds = Tuple((0, 1))

    auto_ybound = Tuple((0, 1))

    reset_xbounds = Button("Reset")

    reset_ybounds = Button("Reset")

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                HGroup(
                    Item('xbounds'),
                    Item('reset_xbounds', show_label=False),
                ),
                HGroup(
                    Item('ybounds'),
                    Item('reset_ybounds', show_label=False),
                ),
                *self.general_view_elements
            ),
        )
        return view

    # Traits listener methods -------------------------------------------------

    def _color_palette_changed(self):
        self.colormap = self._colormap_default()

    def _reset_xbounds_fired(self):
        self.xbounds = self.auto_xbound

    def _reset_ybounds_fired(self):
        self.ybounds = self.auto_ybound

    # Traits initialization methods -------------------------------------------

    def _colormap_default(self):
        if self.color_palette in color_map_name_dict:
            return color_map_name_dict[self.color_palette]

    def _dict_keys_default(self):
        return ["colormap", "xbounds", "ybounds"]
