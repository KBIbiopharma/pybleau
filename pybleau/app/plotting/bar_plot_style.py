
from traits.api import Bool, Enum
from traitsui.api import HGroup, Item, VGroup

from .plot_style import BaseColorXYPlotStyle, SPECIFIC_CONFIG_CONTROL_LABEL
from .renderer_style import BarRendererStyle

IGNORE_DATA_DUPLICATES = "ignore"


class BarPlotStyle(BaseColorXYPlotStyle):
    """ Styling object for customizing bar plots.
    """
    #: How to handle multiple bars from hue dim? Next to each other or stacked?
    # Stacked bars aren't working right in current Chaco
    bar_style = Enum(["group"])  # , "stack"

    #: How to handle multiple values contributing to a single bar?
    data_duplicate = Enum([IGNORE_DATA_DUPLICATES, "mean"])

    #: Whether to display error bars when multiple values contribute to a bar
    show_error_bars = Bool

    def _get_specific_view_elements(self):
        allow_errors = "data_duplicate != '{}'".format(IGNORE_DATA_DUPLICATES)

        return [
            VGroup(
                VGroup(
                    HGroup(
                        Item('bar_style', tooltip="When multiple bars, display"
                                                  " side by side or stacked?")
                    ),
                    HGroup(
                        Item('data_duplicate'),
                        Item("show_error_bars", label="Show error bars?",
                             enabled_when=allow_errors)
                    ),
                    show_border=True, label=SPECIFIC_CONFIG_CONTROL_LABEL
                ),
            )
        ]

    def _renderer_styles_default(self):
        return [BarRendererStyle()]
