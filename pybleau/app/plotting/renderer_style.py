from traits.api import Any, Enum, Float, Int, List, Property, Range, Trait
from traitsui.api import EnumEditor, HGroup, Item, RangeEditor, VGroup, View
from enable.markers import MarkerNameDict, marker_names
from enable.api import ColorTrait, LineStyle

from .serializable import Serializable

DEFAULT_COLOR = "blue"

DEFAULT_MARKER_SIZE = 6

DEFAULT_LINE_WIDTH = 1.3


class BaseXYRendererStyle(Serializable):
    """ Styling object for customizing scatter renderers.
    """
    #: Color of the renderer
    color = ColorTrait(DEFAULT_COLOR)

    #: Transparency of the renderer
    alpha = Range(value=1., low=0., high=1.)

    #: Which y-axis to be displayed along
    orientation = Enum(["left", "right"])

    renderer_type = ""

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
                VGroup(
                    Item('marker', label="Marker"),
                    Item('marker_size',
                         editor=RangeEditor(low=1, high=20)),
                    show_border=True
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
                VGroup(
                    Item('line_width'),
                    Item('line_style', style="custom"),
                    show_border=True
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
