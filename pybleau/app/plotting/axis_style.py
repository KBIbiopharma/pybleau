
from traits.api import Any, Bool, Button, Enum, Float, Instance, Int, Str
from traitsui.api import HGroup, InstanceEditor, Item, RangeEditor, VGroup, \
    View

from pybleau.app.plotting.title_style import TitleStyle
from pybleau.app.plotting.serializable import Serializable


class AxisStyle(Serializable):

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

    scaling = Enum("linear", "log")

    #: View klass. Override to customize the views, for example their icon
    view_klass = Any(default_value=View)

    #: Is there a finite number of labels?
    # If so, it will be possible to force the appearance of all of them.
    _finite_labels = Bool

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
                VGroup(
                    HGroup(
                        Item('label_rotation',
                             editor=RangeEditor(low=0, high=360)),
                        Item('show_all_labels',
                             label="Show all ticks/labels",
                             enabled_when="_finite_labels"),
                    ),
                    show_border=True, label="Labels",
                    enabled_when="finite_labels"
                ),
            ),
            resizable=True
        )

    # Traits listener methods -------------------------------------------------

    def _reset_range_changed(self):
        self.range_low = self.auto_range_low
        self.range_high = self.auto_range_high

    # Traits initialization methods -------------------------------------------

    def _dict_keys_default(self):
        return ["axis_name", "title_style", "label_rotation",
                "show_all_labels", "range_low", "range_high", "auto_range_low",
                "auto_range_high", "scaling", "_finite_labels"]


if __name__ == "__main__":
    AxisStyle(axis_name="X").configure_traits()
