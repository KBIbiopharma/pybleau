from collections import OrderedDict

from .plot_config import BAR_PLOT_TYPE, BarPlotConfigurator, HIST_PLOT_TYPE, \
    HistogramPlotConfigurator, HEATMAP_PLOT_TYPE, HeatmapPlotConfigurator, \
    LINE_PLOT_TYPE, LinePlotConfigurator, SCATTER_PLOT_TYPE, \
    ScatterPlotConfigurator

from .multi_plot_config import MULTI_HIST_PLOT_TYPE, \
    MultiHistogramPlotConfigurator, MULTI_LINE_PLOT_TYPE, \
    MultiLinePlotConfigurator

PLOT_CONFIGURATORS = OrderedDict([
    (HIST_PLOT_TYPE, HistogramPlotConfigurator),
    (MULTI_HIST_PLOT_TYPE, MultiHistogramPlotConfigurator),
    (BAR_PLOT_TYPE, BarPlotConfigurator),
    (LINE_PLOT_TYPE, LinePlotConfigurator),
    (MULTI_LINE_PLOT_TYPE, MultiLinePlotConfigurator),
    (SCATTER_PLOT_TYPE, ScatterPlotConfigurator),
    (HEATMAP_PLOT_TYPE, HeatmapPlotConfigurator)
])

PLOT_TYPES = list(PLOT_CONFIGURATORS.keys())
