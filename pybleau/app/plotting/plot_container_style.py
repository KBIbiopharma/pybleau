
from traits.api import Bool, HasStrictTraits, Int
from enable.component import white_color_trait


class PlotContainerStyle(HasStrictTraits):

    #: The amount of space to put on the left side of the component
    padding_left = Int(50)

    #: The amount of space to put on the right side of the component
    padding_right = Int(20)

    #: The amount of space to put on top of the component
    padding_top = Int(40)

    #: The amount of space to put below the component
    padding_bottom = Int(50)

    # Is the border visible?
    border_visible = Bool(False)

    # The background color of the plot
    bgcolor = white_color_trait

    #: Whether to show a colorbar (if relevant)
    include_colorbar = Bool

    def to_traits(self):
        """ Build OverlayPlotContainer construction keyword list.
        """
        return {
            "padding_left": self.padding_left,
            "padding_right": self.padding_right,
            "padding_top": self.padding_top,
            "padding_bottom": self.padding_bottom,
            "border_visible": self.border_visible,
            "bgcolor": self.bgcolor
        }
