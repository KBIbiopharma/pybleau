
from traits.api import Any, Bool, Button, Enum, Float, HasStrictTraits, \
    Instance, Int, Str
from traitsui.api import HGroup, InstanceEditor, Item, RangeEditor, VGroup, \
    View

from .title_style import TitleStyle

LINEAR_AXIS_STYLE = "linear"

LOG_AXIS_STYLE = "log"


class AxisStyle(HasStrictTraits):

    #: Name of the axis, to use in view labels
    axis_name = Str

    #: Styling of the title along the axis
    title_style = Instance(TitleStyle, ())

    #: Angle to rotate the axis labels (string values only)
    label_rotation = Int

    #: Whether to force display of all labels along axis or allow decimation
    # (String labels only)
    show_all_labels = Bool

    #: Low value of the x-axis range
    range_low = Float(-1)

    #: High value of the x-axis range
    range_high = Float(-1)

    #: Automatic low value of the x-axis range for plot full view
    auto_range_low = Float(-1)

    #: High value of the x-axis range
    auto_range_high = Float(-1)

    #: Button to reset the x-axis range to automatic values
    reset_range = Button("Reset")

    #: Selector for the scaling of the axis: log or linear?
    scaling = Enum(LINEAR_AXIS_STYLE, LOG_AXIS_STYLE)

    #: View klass. Override to customize the views, for example their icon
    view_klass = Any(default_value=View)

    #: Is there a finite number of labels?
    # (If so, allow forcing the appearance of all of them and label rotation)
    _finite_labels = Bool

    def __init__(self, **traits):
        if "range_low" in traits and "auto_range_low" not in traits:
            traits["auto_range_low"] = traits["range_low"]

        if "range_high" in traits and "auto_range_high" not in traits:
            traits["auto_range_high"] = traits["range_high"]

        super(AxisStyle, self).__init__(**traits)

    def traits_view(self):
        return self.view_klass(
            VGroup(
                HGroup(
                    Item("range_low", label=self.axis_name+"-axis range"),
                    Item("range_high", show_label=False),
                    Item("reset_range", show_label=False),
                    Item("scaling", label="Scaling"),
                    show_border=True, label="Range"
                ),
                HGroup(
                    Item("title_style", editor=InstanceEditor(),
                         style="custom", show_label=False),
                    show_border=True, label="Title"
                ),
                HGroup(
                    Item('label_rotation',
                         editor=RangeEditor(low=0, high=360),
                         tooltip="(String labels only)"),
                    Item('show_all_labels',
                         label="Show all ticks/labels",
                         tooltip="(String labels only)",
                         visible_when="_finite_labels"),
                    show_border=True, label="Labels",
                ),
            ),
            resizable=True
        )

    # Traits listener methods -------------------------------------------------

    def _reset_range_fired(self):
        self.range_low = self.auto_range_low
        self.range_high = self.auto_range_high


if __name__ == "__main__":
    AxisStyle(axis_name="X").configure_traits()
