
from traits.api import Any, Enum, Float, Int, List, Property, Range, Str, Trait
from traitsui.api import EnumEditor, HGroup, Item, RangeEditor, VGroup, View
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

    #: Color of the contours of the bars
    line_color = ColorTrait(DEFAULT_COLOR)

    #: Color of the inside of the bars
    fill_color = ColorTrait(DEFAULT_COLOR)

    def _color_changed(self):
        # Bar renderers have 2 different color traits for the line and the
        # inside of the bar:
        self.line_color = self.color
        self.fill_color = self.color

    def _dict_keys_default(self):
        return ["line_color", "fill_color", "alpha"]
