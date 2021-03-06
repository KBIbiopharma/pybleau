
from traits.api import Enum, Float, Int, Tuple
from traitsui.api import HGroup, Item, RangeEditor, VGroup

from .plot_style import BaseXYPlotStyle, RendererStyleManager, \
    SPECIFIC_CONFIG_CONTROL_LABEL
from .renderer_style import BarRendererStyle

DEFAULT_NUM_BINS = 10


class HistogramPlotStyle(BaseXYPlotStyle):
    """ Styling object for customizing histogram plots.
    """

    #: Number of bins: the bar width computed from that and the data range
    num_bins = Int(DEFAULT_NUM_BINS)

    #: bin start and end to use. Leave empty to use the data's min and max.
    bin_limits = Tuple

    #: Factor to apply to the default bar width. Set to 1 for bars to touch.
    bar_width_factor = Float(1.0)

    # Extra parameters not needed in the view ---------------------------------

    #: Meaning of the parameter above: data space or screen space?
    # Export but don't expose in the UI to make sure it is the data space since
    # the bar width computation makes that assumption.
    bar_width_type = Enum("data", "screen")

    def _get_specific_view_elements(self):
        return [
            VGroup(
                HGroup(
                    Item('num_bins', label="Number of bins"),
                    Item('bar_width_factor',
                         editor=RangeEditor(low=0.1, high=1.)),
                    show_border=True, label=SPECIFIC_CONFIG_CONTROL_LABEL
                ),
            )
        ]

    def _renderer_style_manager_default(self):
        return RendererStyleManager(renderer_styles=[BarRendererStyle()])
