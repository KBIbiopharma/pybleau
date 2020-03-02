
from traits.api import Enum, Instance
from traitsui.api import HGroup, InstanceEditor, Item, VGroup

from .plot_style import BaseColorXYPlotStyle, SPECIFIC_CONFIG_CONTROL_LABEL
from .contour_style import ContourStyle
from .renderer_style import HeatmapRendererStyle


class HeatmapPlotStyle(BaseColorXYPlotStyle):
    """ Styling object for customizing heatmap plots.
    """
    interpolation = Enum("nearest", "bilinear", "bicubic")

    contour_style = Instance(ContourStyle, ())

    def _get_specific_view_elements(self):
        return [
            VGroup(
                VGroup(
                    HGroup(
                        Item("interpolation"),
                    ),
                    Item("contour_style", editor=InstanceEditor(),
                         style="custom", show_label=False),
                    show_border=True, label=SPECIFIC_CONFIG_CONTROL_LABEL
                ),
            )
        ]

    # Traits initialization methods -------------------------------------------

    def _colorize_by_float_default(self):
        return True

    def _renderer_styles_default(self):
        return [HeatmapRendererStyle()]
