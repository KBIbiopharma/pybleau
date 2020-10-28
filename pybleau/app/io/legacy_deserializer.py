""" Module defining legacy deserializers for old protocol versions of a few
objects. Deserializers are defined as modifications to the regular
implementation, and added to the LEGACY dictionary.
"""

from traits.api import HasStrictTraits, Set

from .deserializer import singleLinePlotStyleDeSerializer, \
    singleScatterPlotStyleDeSerializer, plotManagerDeSerializer, \
    dataFrameCanvasManagerDeSerializer, histogramPlotStyleDeSerializer, \
    scatterPlotConfiguratorDeSerializer, dataFrameAnalyzerDeSerializer, \
    axisStyleDeSerializer
from ..plotting.plot_config import DEFAULT_CONFIGS, DEFAULT_STYLES


class axisStyleDeSerializer_v0(axisStyleDeSerializer):
    """ Legacy deserializer for AxisStyle stored by pybleau before 0.5.3.
    """
    protocol_version = 0

    def get_instance(self, constructor_data):
        # Enable text label controls for all x-axis even for old plots:
        if constructor_data.get('axis_name', "") == "x":
            constructor_data['support_text_labels'] = True

        return super(axisStyleDeSerializer_v0, self).get_instance(
            constructor_data)


class dataFrameAnalyzerDeSerializer_v0(dataFrameAnalyzerDeSerializer):

    protocol_version = 0

    def get_instance(self, constructor_data):
        constructor_data['kwargs'].pop('index_name')
        return super(dataFrameAnalyzerDeSerializer_v0, self).get_instance(
            constructor_data)


class dataFrameCanvasManagerDeSerializer_v0(dataFrameCanvasManagerDeSerializer):
    """ Legacy deserializer for objects stored by pybleau before 0.5.0.
    """
    protocol_version = 0

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        kwargs.pop("next_plot_id", None)
        return super(dataFrameCanvasManagerDeSerializer_v0, self).get_instance(
            constructor_data
        )


class plotManagerDeSerializer_v0(plotManagerDeSerializer):
    """ Legacy deserializer for objects stored by pybleau before 0.5.0.
    """
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

        instance = super(plotManagerDeSerializer_v0, self).get_instance(
            constructor_data
        )
        return instance


class _LegacyStyleDeserializerMixin(HasStrictTraits):
    kw_to_keep = Set

    def lose_moved_style_attrs(self, kwargs):
        return {kw: val for kw, val in kwargs.items() if kw in self.kw_to_keep}


class scatterPlotStyleDeSerializer(singleScatterPlotStyleDeSerializer,
                                   _LegacyStyleDeserializerMixin):
    """ Legacy class which was renamed for objects stored before v0.5.0.

    Note: Legacy users not worried about loosing renderer styling.
    """
    protocol_version = 0

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        constructor_data['kwargs'] = self.lose_moved_style_attrs(kwargs)

        return super(scatterPlotStyleDeSerializer, self).get_instance(
            constructor_data
        )


class linePlotStyleDeSerializer(singleLinePlotStyleDeSerializer,
                                _LegacyStyleDeserializerMixin):
    """ Legacy class which was renamed for objects stored before v0.5.0.

    Note: Legacy users not worried about loosing renderer styling.
    """
    protocol_version = 0

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        constructor_data['kwargs'] = self.lose_moved_style_attrs(kwargs)

        return super(linePlotStyleDeSerializer, self).get_instance(
            constructor_data
        )


class histogramPlotStyleDeSerializer_v0(histogramPlotStyleDeSerializer,
                                        _LegacyStyleDeserializerMixin):
    """ Legacy deserializer for objects stored by pybleau before 0.5.0.

    Legacy users not worried about loosing renderer styling.
    """
    protocol_version = 0

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        constructor_data['kwargs'] = self.lose_moved_style_attrs(kwargs)

        return super(histogramPlotStyleDeSerializer_v0, self).get_instance(
            constructor_data
        )

    def _kw_to_keep_default(self):
        # Salvage a few styling attributes since they haven't moved:
        return {'bar_width_type', 'bar_width_factor', 'bin_limits', 'num_bins'}


class scatterPlotConfiguratorDeSerializer_v0(scatterPlotConfiguratorDeSerializer):  # noqa
    """ Legacy deserializer for objects stored by pybleau before 0.5.0.

    Old configurators stored an deprecated style class which may not
    recreate the correct number of renderers. This triggers a style reset for
    frozen configurators so plot regeneration doesn't fail. Non-frozen plots
    will trigger a reset of their styling when the data_source is reset from
    analyzer data.
    """
    def get_instance(self, constructor_data):
        x = super(scatterPlotConfiguratorDeSerializer_v0, self).get_instance(
            constructor_data
        )
        if x.data_source is not None:
            x.update_style()
        return x


LEGACY_DESERIALIZER_MAP = {
    "plotManager": {0: plotManagerDeSerializer_v0},
    "scatterPlotStyle": {0: scatterPlotStyleDeSerializer},
    "linePlotStyle": {0: linePlotStyleDeSerializer},
    "dataFrameCanvasManager": {0: dataFrameCanvasManagerDeSerializer_v0},
    "histogramPlotStyle": {0: histogramPlotStyleDeSerializer_v0},
    "scatterPlotConfigurator": {0: scatterPlotConfiguratorDeSerializer_v0},
    "dataFrameAnalyzer": {0: dataFrameAnalyzerDeSerializer_v0},
    "axisStyle": {0: axisStyleDeSerializer_v0}
}
