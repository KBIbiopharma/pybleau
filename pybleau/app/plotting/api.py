from .plot_factories import DEFAULT_FACTORIES
from .plot_style import BaseXYPlotStyle, SingleLinePlotStyle, SingleScatterPlotStyle  # noqa

from .bar_plot_style import BarPlotStyle  # noqa
from .heatmap_plot_style import HeatmapPlotStyle  # noqa
from .histogram_plot_style import HistogramPlotStyle  # noqa
from .axis_style import AxisStyle  # noqa
from .title_style import TitleStyle  # noqa
from .plot_container_style import PlotContainerStyle  # noqa


def plot_from_config(config, factory_map=DEFAULT_FACTORIES):
    """ Build plot factory capable of building a plot described by config.
    """
    plot_type = config.plot_type
    plot_factory_klass = factory_map[plot_type]
    factory = plot_factory_klass(**config.to_dict())
    desc = factory.generate_plot()
    plot = desc["plot"]
    return plot, factory, desc
