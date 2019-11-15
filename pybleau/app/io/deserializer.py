
from app_common.apptools.io.deserializer import dataElementDeSerializer


class dataFramePlotManagerDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.model.dataframe_plot_manager import \
            DataFramePlotManager
        return DataFramePlotManager


class plotDescriptorDeSerializer(dataElementDeSerializer):

    protocol_version = 1

    def _klass_default(self):
        from pybleau.app.model.plot_descriptor import PlotDescriptor
        return PlotDescriptor


class scatterPlotConfiguratorDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_config import ScatterPlotConfigurator
        return ScatterPlotConfigurator


class scatterPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_style import ScatterPlotStyle
        return ScatterPlotStyle


class linePlotConfiguratorDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_config import LinePlotConfigurator
        return LinePlotConfigurator


class linePlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_style import LinePlotStyle
        return LinePlotStyle


class barPlotConfiguratorDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_config import BarPlotConfigurator
        return BarPlotConfigurator


class barPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_style import BarPlotStyle
        return BarPlotStyle


class histogramPlotConfiguratorDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_config import HistogramPlotConfigurator
        return HistogramPlotConfigurator


class histogramPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_style import HistogramPlotStyle
        return HistogramPlotStyle


class heatmapPlotConfiguratorDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_config import HeatmapPlotConfigurator
        return HeatmapPlotConfigurator


class heatmapPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_style import HeatmapPlotStyle
        return HeatmapPlotStyle
