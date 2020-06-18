""" Deserialization tools and entry point.
"""
import logging

from app_common.apptools.io.deserializer import dataElementDeSerializer


logger = logging.getLogger(__name__)


def deserialize(serial_data, array_collection=None):
    """ Functional entry point to deserialize any serial data.

    See app_common implementation for details.
    """
    from app_common.apptools.io.deserializer import deserialize

    local_deserializers = {key: val for key, val in globals().items()
                           if key.endswith("DeSerializer")}
    return deserialize(serial_data, array_collection=array_collection,
                       additional_deserializers=local_deserializers)


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


class singlescatterPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_style import SingleScatterPlotStyle
        return SingleScatterPlotStyle


class linePlotConfiguratorDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_config import LinePlotConfigurator
        return LinePlotConfigurator


class singleLinePlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_style import SingleLinePlotStyle
        return SingleLinePlotStyle


class singleScatterPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_style import SingleScatterPlotStyle
        return SingleScatterPlotStyle


class barPlotConfiguratorDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_config import BarPlotConfigurator
        return BarPlotConfigurator


class barPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.bar_plot_style import BarPlotStyle
        return BarPlotStyle


class histogramPlotConfiguratorDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_config import HistogramPlotConfigurator
        return HistogramPlotConfigurator


class histogramPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.histogram_plot_style import \
            HistogramPlotStyle
        return HistogramPlotStyle


class heatmapPlotConfiguratorDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_config import HeatmapPlotConfigurator
        return HeatmapPlotConfigurator


class heatmapPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.heatmap_plot_style import HeatmapPlotStyle
        return HeatmapPlotStyle


class lineRendererStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.renderer_style import LineRendererStyle
        return LineRendererStyle


class scatterRendererStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.renderer_style import ScatterRendererStyle
        return ScatterRendererStyle


class barRendererStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.renderer_style import BarRendererStyle
        return BarRendererStyle


class heatmapRendererStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.renderer_style import HeatmapRendererStyle
        return HeatmapRendererStyle


class titleStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.title_style import TitleStyle
        return TitleStyle


class axisStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.axis_style import AxisStyle
        return AxisStyle


class baseColorXYPlotStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.bar_plot_style import BaseColorXYPlotStyle
        return BaseColorXYPlotStyle


class contourStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.contour_style import ContourStyle
        return ContourStyle


class plotContainerStyleDeSerializer(dataElementDeSerializer):
    def _klass_default(self):
        from pybleau.app.plotting.plot_container_style import \
            PlotContainerStyle
        return PlotContainerStyle
