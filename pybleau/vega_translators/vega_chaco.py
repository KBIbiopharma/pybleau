""" Conversion tools for Configurator objects to/from Vega-lite

For more about the Vega format, see https://vega.github.io/vega-lite/docs/. To
test vega outputs, see online editors such as https://vega.github.io/editor/.
"""

import logging
from os.path import isfile, splitext
import json

from pybleau.app.plotting.plot_config import BasePlotConfigurator, \
    CMAP_SCATTER_PLOT_TYPE, HIST_PLOT_TYPE, HistogramPlotConfigurator, \
    LINE_PLOT_TYPE, LinePlotConfigurator, SCATTER_PLOT_TYPE, \
    ScatterPlotConfigurator
from pybleau.reporting.string_definitions import IDX_NAME_KEY
from pybleau.vega_translators.vega_utils import df_to_vega

logger = logging.getLogger(__name__)

TARGET_VEGA_SCHEMA = "https://vega.github.io/schema/vega-lite/v3.json"

CHACO_TO_VEGA_TYPES = {
    HIST_PLOT_TYPE: "bar",
    LINE_PLOT_TYPE: "line",
    SCATTER_PLOT_TYPE: "point",
    CMAP_SCATTER_PLOT_TYPE: "point"
}


def chaco2vega(plot_config, export_data=False, filepath="", indent=None):
    """ Export the plot configuration to a vega-lite description (dict).

    Parameters
    ----------
    plot_config : BasePlotConfigurator
        Configurator object, describing the plot to export.

    export_data : bool or str
        Whether to export the data_source into the vega-lite output. Return
        it to make the vega description self-contained. Can be False,
        "inline" (or True, data key is 'values'), or provide a string. If the
        string has an extension, it is treated as the path to the file the data
        should be stored in (data key is 'url'). Otherwise, the string is
        assumed to be a dataset name that will be injected at runtime (data key
        is 'name').

    filepath : str, optional
        Path to the file to store the resulting plot description (json). The
        content of that file can be pasted in a vega editor for testing (such
        as https://vega.github.io/editor/).

    indent : None or int
        Indent to use when writing the description to json. Use, say, 2 for
        readability and leave as None to keep the file compact.
    """
    if not isinstance(plot_config, BasePlotConfigurator):
        msg = "A Plot Configurator should be passed but a {} was received."
        logger.exception(msg)
        raise ValueError(msg)

    desc = {"$schema": TARGET_VEGA_SCHEMA}
    data = plot_config.data_source
    if data is not None:
        if export_data is False:
            desc["data"] = {}
        elif export_data is True or export_data == "inline":
            desc["data"] = {"values": df_to_vega(data),
                            IDX_NAME_KEY: data.index.name}
        else:
            basename, ext = splitext(export_data)
            if ext == ".csv":
                data.to_csv(export_data)
                desc["data"] = {"url": export_data}
            elif ext == "":
                desc["data"] = {"name": export_data}
            else:
                msg = "Export_data argument not understood. Should be " \
                      "'inline', or a dataset name, or a csv file path, but " \
                      "{} was provided.".format(export_data)
                logger.exception(msg)
                raise ValueError(msg)

    desc["mark"] = CHACO_TO_VEGA_TYPES[plot_config.plot_type]
    desc["encoding"] = build_vega_encoding(plot_config)

    if filepath:
        if isfile(filepath):
            msg = "File path requested ({}) already exists.".format(filepath)
            logger.exception(msg)
            raise IOError(msg)

        json.dump(desc, open(filepath, "w"), indent=indent)

    return desc


def build_vega_encoding(plot_config):
    """ Build the encoding portion of the plot description.
    """
    two_d_plots = (LinePlotConfigurator, ScatterPlotConfigurator)
    if isinstance(plot_config, two_d_plots):
        return two_d_plots_encoding(plot_config)
    elif isinstance(plot_config, HistogramPlotConfigurator):
        return hist_plot_encoding(plot_config)
    else:
        msg = "Unsupported plot type. Please report this issue."
        logger.exception(msg)
        raise NotImplementedError(msg)


def two_d_plots_encoding(plot_config):
    """ Build encoding portion of Vega plot description for line/scatter plot.
    """
    encoding = {
        "x": {"field": plot_config.x_col_name, "type": "quantitative"},
        "y": {"field": plot_config.y_col_name, "type": "quantitative"},
    }
    if plot_config.z_col_name:
        encoding["color"] = {"field": plot_config.z_col_name}
        if plot_config.colorize_by_float:
            encoding["color"]["type"] = "quantitative"
        else:
            encoding["color"]["type"] = "nominal"
    return encoding


def hist_plot_encoding(plot_config):
    """ Build encoding portion of Vega plot description for a histogram plot.
    """
    encoding = {
        "x": {
          "bin": True,
          "field": plot_config.x_col_name,
          "type": "quantitative"
        },
        "y": {
          "aggregate": "count",
          "type": "quantitative"
        }
    }
    return encoding


def vega2chaco(plot_desc):
    raise NotImplementedError()


if __name__ == "__main__":
    import pandas as pd

    df = pd.DataFrame({"a": [1, 2, 3], "b": [1, 2, 1], "c": list("abc")})

    config = ScatterPlotConfigurator(data_source=df, x_col_name="a",
                                     y_col_name="b", z_col_name="c")
    output = chaco2vega(config, export_data="inline")

    desc = {
        "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
        "data": {
            "values": {"a": [1, 2, 3], "b": [1, 2, 1], "c": ["a", "b", "c"]}
        },
        "mark": "point",
        "encoding": {
            "x": {"field": "all_si_oil", "type": "quantitative"},
            "y": {"field": "all_prot_transluc", "type": "quantitative"},
            "color": {"field": "experiment", "type": "nominal"},
            # "shape": {"field": "Lot", "type": "nominal"},

        }
    }
