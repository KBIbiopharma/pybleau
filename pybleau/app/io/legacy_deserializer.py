
from .deserializer import singleLinePlotStyleDeSerializer, \
    singleScatterPlotStyleDeSerializer, plotDescriptorDeSerializer, \
    dataFramePlotManagerDeSerializer
from ..plotting.plot_config import DEFAULT_CONFIGS, DEFAULT_STYLES


class dataFramePlotManagerDeSerializer_v0(dataFramePlotManagerDeSerializer):

    protocol_version = 0

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        kwargs.pop("next_plot_id")
        return super(dataFramePlotManagerDeSerializer_v0, self).get_instance(
            constructor_data
        )


class plotDescriptorDeSerializer_v0(plotDescriptorDeSerializer):

    protocol_version = 0

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        # For a short amount of time, new plot_descriptors may have been stored
        # with protocol version at 0 instead of 1, so check:
        if "plot_config" not in kwargs and 'factory_kwargs' in kwargs:
            factory_kw = constructor_data['kwargs'].pop('factory_kwargs')
            # Convert factory kw to configurator kw:
            for key in ["x_arr", "y_arr", "z_arr"]:
                factory_kw.pop(key, None)

            config_klass = DEFAULT_CONFIGS[kwargs['plot_type']]
            style_klass = DEFAULT_STYLES[kwargs['plot_type']]
            style_kw = factory_kw.pop('plot_style')
            factory_kw['plot_style'] = style_klass(**style_kw)
            kwargs["plot_config"] = config_klass(**factory_kw)

        instance = super(plotDescriptorDeSerializer_v0, self).get_instance(
            constructor_data
        )
        return instance


class scatterPlotStyleDeSerializer(singleScatterPlotStyleDeSerializer):
    """ Legacy class which was renamed.
    """
    protocol_version = 0


class linePlotStyleDeSerializer(singleLinePlotStyleDeSerializer):
    """ Legacy class which was renamed.
    """
    protocol_version = 0


LEGACY_DESERIALIZER_MAP = {
    "plotDescriptor": {
        0: plotDescriptorDeSerializer_v0,
    },
    "scatterPlotStyle": {0: scatterPlotStyleDeSerializer},
    "linePlotStyle": {0: linePlotStyleDeSerializer},
    "dataFramePlotManager": {0: dataFramePlotManagerDeSerializer_v0}
}
