
from ..utils.string_definitions import BAR_PLOT_TYPE, CMAP_SCATTER_PLOT_TYPE, \
    HEATMAP_PLOT_TYPE, HIST_PLOT_TYPE, LINE_PLOT_TYPE, MULTI_LINE_PLOT_TYPE, \
    SCATTER_PLOT_TYPE

from .bar_factory import BarPlotFactory
from .heatmap_factory import HeatmapPlotFactory
from .histogram_factory import HistogramPlotFactory
from .line_factory import LinePlotFactory
from .scatter_factories import CmapScatterPlotFactory, DISCONNECTED_SELECTION_COLOR, ScatterPlotFactory, SELECTION_COLOR, SELECTION_METADATA_NAME  # noqa


DEFAULT_FACTORIES = {HIST_PLOT_TYPE: HistogramPlotFactory,
                     BAR_PLOT_TYPE: BarPlotFactory,
                     LINE_PLOT_TYPE: LinePlotFactory,
                     MULTI_LINE_PLOT_TYPE: LinePlotFactory,
                     SCATTER_PLOT_TYPE: ScatterPlotFactory,
                     CMAP_SCATTER_PLOT_TYPE: CmapScatterPlotFactory,
                     HEATMAP_PLOT_TYPE: HeatmapPlotFactory}
