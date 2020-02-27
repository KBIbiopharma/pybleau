
from traits.api import Enum, Instance
from traitsui.api import HGroup, InstanceEditor, Item, VGroup

from .plot_style import BaseColorXYPlotStyle, SPECIFIC_CONFIG_CONTROL_LABEL
from .contour_style import ContourStyle
from .renderer_style import CmapHeatmapRendererStyle


class HeatmapPlotStyle(BaseColorXYPlotStyle):
    """ Styling object for customizing heatmap plots.
    """
    interpolation = Enum("nearest", "bilinear", "bicubic")

    contour_style = Instance(ContourStyle, ())

    def _dict_keys_default(self):
        general_items = super(HeatmapPlotStyle, self)._dict_keys_default()
        return general_items + ["interpolation", "contour_style"]

    def _renderer_styles_default(self):
        return [CmapHeatmapRendererStyle(color_palette=self.color_palette)]

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
