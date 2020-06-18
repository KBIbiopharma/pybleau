""" Serializers for pybleau.app objects.

To be contributed to a serialization implementation that leverages
app_common.apptools.io.serializer.
"""
import logging

from app_common.apptools.io.serializer import DataElement_Serializer, \
    Serializer

logger = logging.getLogger(__name__)


def serialize(obj, array_collection=None):
    """ Serialization functional entry point.

    Parameters
    ----------
    obj : any
        Object to serialize

    array_collection : dict
        Dictionary mapping all numpy arrays stored to an id in the serial data.
    """
    from app_common.apptools.io.serializer import serialize
    from pybleau import __build__, __version__
    from ..ui.branding import APP_FAMILY, APP_TITLE, APP_UUID

    software_version = [__version__, __build__]
    local_serializers = {key: val for key, val in globals().items()
                         if key.endswith("_Serializer")}
    return serialize(obj, array_collection=array_collection,
                     software_name="{} {}".format(APP_FAMILY, APP_TITLE),
                     software_uuid=APP_UUID,
                     software_version=software_version,
                     additional_serializers=local_serializers)


class DataFramePlotManager_Serializer(DataElement_Serializer):
    def attr_names_to_serialize(self, obj):
        return ['name', 'uuid', "source_analyzer_id", "contained_plots",
                "next_plot_id"]


class PlotDescriptor_Serializer(DataElement_Serializer):

    protocol_version = 2

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
                "container_idx", "id", "plot_type"]


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


class BaseXYPlotStyle_Serializer(Serializer):
    def attr_names_to_serialize(self, obj):
        return ['title_style', 'renderer_styles', 'x_axis_style',
                'y_axis_style', "container_style", "second_y_axis_style"]


class BaseColorXYPlotStyle_Serializer(BaseXYPlotStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        attrs = super(BaseColorXYPlotStyle_Serializer, self).attr_names_to_serialize(obj)  # noqa
        return attrs + ['color_palette', 'color_axis_title_style',
                        'colorbar_low', 'colorbar_high', 'colorize_by_float']


class SingleScatterPlotStyle_Serializer(BaseXYPlotStyle_Serializer):
    pass


class SingleLinePlotStyle_Serializer(BaseXYPlotStyle_Serializer):
    pass


class BarPlotStyle_Serializer(BaseColorXYPlotStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        attrs = super(BarPlotStyle_Serializer, self).attr_names_to_serialize(obj)  # noqa
        return attrs + ["bar_style", "data_duplicate", "show_error_bars"]


class HistogramPlotStyle_Serializer(BaseXYPlotStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        attrs = super(HistogramPlotStyle_Serializer, self).attr_names_to_serialize(obj)  # noqa
        return attrs + ["num_bins", "bin_limits", "bar_width_factor"]


class HeatmapPlotStyle_Serializer(BaseColorXYPlotStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        attrs = super(HeatmapPlotStyle_Serializer, self).attr_names_to_serialize(obj)  # noqa
        return attrs + ["interpolation", "contour_style"]


class BaseRendererStyle_Serializer(DataElement_Serializer):
    def attr_names_to_serialize(self, obj):
        return ['renderer_name']


class BaseXYRendererStyle_Serializer(BaseRendererStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        attrs = super(BaseXYRendererStyle_Serializer, self).attr_names_to_serialize(obj)  # noqa
        return attrs + ['color', 'alpha', 'orientation']


class ScatterRendererStyle_Serializer(BaseXYRendererStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        attrs = super(ScatterRendererStyle_Serializer, self).attr_names_to_serialize(obj)  # noqa
        return list(attrs) + ["marker", "marker_size"]


class LineRendererStyle_Serializer(BaseXYRendererStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        attrs = super(LineRendererStyle_Serializer, self).attr_names_to_serialize(obj)  # noqa
        return list(attrs) + ["line_style", "line_width"]


class BarRendererStyle_Serializer(BaseXYRendererStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        attrs = super(BarRendererStyle_Serializer, self).attr_names_to_serialize(obj)  # noqa
        return list(attrs) + ["bar_width", "line_color", "fill_color"]


class CmapScatterRendererStyle_Serializer(BaseXYRendererStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        return ["fill_alpha", "marker", "marker_size", "color_palette",
                'renderer_name']


class HeatmapRendererStyle_Serializer(BaseRendererStyle_Serializer):
    def attr_names_to_serialize(self, obj):
        attrs = super(HeatmapRendererStyle_Serializer, self).attr_names_to_serialize(obj)  # noqa
        return attrs + ["alpha", "color_palette", "xbounds", "ybounds"]


class AxisStyle_Serializer(Serializer):
    def attr_names_to_serialize(self, obj):
        return ["axis_name", "range_low", "range_high", "auto_range_low",
                "auto_range_high", "title_style"]


class TitleStyle_Serializer(Serializer):
    def attr_names_to_serialize(self, obj):
        return ["font_name", "font_size"]


class ContourStyle_Serializer(Serializer):
    def attr_names_to_serialize(self, obj):
        return ["add_contours", "contour_levels", "contour_styles",
                "contour_alpha", "contour_widths"]


class PlotContainerStyle_Serializer(Serializer):
    def attr_names_to_serialize(self, obj):
        return ["padding_left", "padding_right", "padding_top",
                "padding_bottom", "border_visible", "include_colorbar",
                "bgcolor"]
