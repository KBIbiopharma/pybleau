from collections import OrderedDict

from .plot_config import BAR_PLOT_TYPE, BarPlotConfigurator, HIST_PLOT_TYPE, \
    HistogramPlotConfigurator, HEATMAP_PLOT_TYPE, HeatmapPlotConfigurator, \
    LINE_PLOT_TYPE, LinePlotConfigurator, SCATTER_PLOT_TYPE, \
    ScatterPlotConfigurator

from .plot_style import BaseXYPlotStyle, SingleLinePlotStyle, SingleScatterPlotStyle  # noqa

from .bar_plot_style import BarPlotStyle  # noqa
from .heatmap_plot_style import HeatmapPlotStyle  # noqa
from .histogram_plot_style import HistogramPlotStyle  # noqa
from .axis_style import AxisStyle  # noqa
from .title_style import TitleStyle  # noqa
from .plot_container_style import PlotContainerStyle  # noqa

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
