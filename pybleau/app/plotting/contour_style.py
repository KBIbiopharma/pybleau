
from traits.api import Any, Bool, Enum, Float, HasStrictTraits, Int
from traitsui.api import HGroup, Item, RangeEditor, View


class ContourStyle(HasStrictTraits):
    """ Styling object to customize contours on a heatmap.
    """
    add_contours = Bool(False)

    contour_levels = Int(5)

    contour_styles = Enum("solid", "dash")

    contour_alpha = Float(0.9)

    contour_widths = Float(0.85)

    #: View klass. Override to customize the view, for example its icon
    view_klass = Any(default_value=View)

    def traits_view(self):
        view = self.view_klass(
            HGroup(
                Item("add_contours"),
                Item("contour_levels", label="Num. contours",
                     enabled_when="add_contours"),
                Item("contour_styles", label="Contour line type",
                     enabled_when="add_contours"),
                Item("contour_alpha",
                     editor=RangeEditor(low=0., high=1.),
                     label="Contour transparency",
                     enabled_when="add_contours"),
                Item("contour_widths",
                     editor=RangeEditor(low=0.1, high=4.),
                     label="Contour widths",
                     enabled_when="add_contours"),
                show_border=True,
            )
        )
        return view

    def _dict_keys_default(self):
        return ["add_contours", "contour_levels", "contour_styles",
                "contour_alpha", "contour_widths"]
