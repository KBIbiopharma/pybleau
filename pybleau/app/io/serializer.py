""" Serializers for pybleau.app objects.

To be contributed to a serialization implementation that leverages
app_common.apptools.io.serializer.
"""
from app_common.apptools.io.serializer import DataElement_Serializer, \
    Serializer


class DataFramePlotManager_Serializer(DataElement_Serializer):
    def attr_names_to_serialize(self, obj):
        return ['name', 'uuid', "source_analyzer_id", "contained_plots"]


class PlotDescriptor_Serializer(DataElement_Serializer):

    protocol_version = 1

    def get_instance_data(self, obj):
        data = super(PlotDescriptor_Serializer, self).get_instance_data(obj)
        # If the plot is frozen, store also the config's data_source:
        if obj.frozen:
            data['plot_config']["data_source"] = self.serialize(
                obj.plot_config.data_source
            )
        return data

    def attr_names_to_serialize(self, obj):
        # Don't store the other attribute that are redundant with the
        # PlotConfigurator it contains since the plots are rebuilt from the
        # config
        return ['visible', "data_filter", "plot_config", "frozen",
                "container_idx"]


class BaseSinglePlotConfigurator_Serializer(DataElement_Serializer):
    def attr_names_to_serialize(self, obj):
        """ Build the list of attributes to serialize from attributes exported
        and passed to the factory.
        """
        keys_to_serialize = ["plot_style"]
        # These are needed by the factory but not to serialize since they are
        # read from the DF:
        skip = {"x_arr", "y_arr", "z_arr", 'hover_data'}
        for key in obj._dict_keys:
            if key in skip:
                continue

            if isinstance(key, tuple):
                keys_to_serialize.append(key[0])
            else:
                keys_to_serialize.append(key)

        return keys_to_serialize


class ScatterPlotConfigurator_Serializer(BaseSinglePlotConfigurator_Serializer):  # noqa
    pass


class LinePlotConfigurator_Serializer(BaseSinglePlotConfigurator_Serializer):
    pass


class BarPlotConfigurator_Serializer(BaseSinglePlotConfigurator_Serializer):
    def attr_names_to_serialize(self, obj):
        # Add the "melt_source_data" key since it is not in _dict_keys and
        # therefore not collected by parent class implementation
        keys = super(BarPlotConfigurator_Serializer, self).attr_names_to_serialize(obj)  # noqa
        if "melt_source_data" not in keys:
            keys.append("melt_source_data")
        return keys


class HistogramPlotConfigurator_Serializer(BaseSinglePlotConfigurator_Serializer):  # noqa
    pass


class HeatmapPlotConfigurator_Serializer(BaseSinglePlotConfigurator_Serializer):  # noqa
    pass


class Serializable_Serializer(Serializer):
    def attr_names_to_serialize(self, obj):
        return obj.dict_keys


class ScatterPlotStyle_Serializer(Serializable_Serializer):
    pass


class LinePlotStyle_Serializer(Serializable_Serializer):
    pass


class BarPlotStyle_Serializer(Serializable_Serializer):
    pass


class HistogramPlotStyle_Serializer(Serializable_Serializer):
    pass


class HeatmapPlotStyle_Serializer(Serializable_Serializer):
    pass


class AxisStyle_Serializer(Serializable_Serializer):
    pass


class TitleStyle_Serializer(Serializable_Serializer):
    pass


class BaseXYRendererStyle_Serializer(Serializable_Serializer):
    pass
