""" Tools to serialize Chaco plot's data.
"""
import logging
import pandas as pd

from pybleau.app.plotting.plot_config import BAR_PLOT_TYPE, LINE_PLOT_TYPE, \
    HIST_PLOT_TYPE, SCATTER_PLOT_TYPE

TWO_D_PLOT_TYPES = {SCATTER_PLOT_TYPE, LINE_PLOT_TYPE, BAR_PLOT_TYPE}

logger = logging.getLogger(__name__)


def plot_data2dataframes(plot_desc):
    """ Serialize the data used to generate a Chaco Plot to dict of DataFrames.

    Returns
    -------
    dict
        Dictionary mapping a set of renderer names to a dataframe containing
        the plotted data.
    """
    if plot_desc.plot_type in TWO_D_PLOT_TYPES:
        df_dict = {}
        for renderer_dict in plot_desc.plot_factory.renderer_desc:
            x_col = plot_desc.plot_config.x_col_name
            y_col = plot_desc.plot_config.y_col_name
            rend_name = renderer_dict["name"]
            if plot_desc.plot_config.z_col_name:
                key_gen = plot_desc.plot_factory._plotdata_array_key
                x_key = key_gen(x_col, rend_name)
                y_key = key_gen(y_col, rend_name)
            else:
                x_key = x_col
                y_key = y_col

            df_dict[rend_name] = pd.DataFrame(
                {x_col: plot_desc.plot.data.arrays[x_key],
                 y_col: plot_desc.plot.data.arrays[y_key]}
            )
        return df_dict

    elif plot_desc.plot_type == HIST_PLOT_TYPE:
        return {"": pd.DataFrame(plot_desc.plot.data.arrays)}

    else:
        msg = "Plot type {} not supported. Please report this issue!"
        msg = msg.format(plot_desc.plot_type)
        logger.error(msg)
        return {}
