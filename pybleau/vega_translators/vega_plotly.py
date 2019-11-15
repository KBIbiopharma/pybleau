"""
Translators for vega-lite descriptions
"""
import logging
from .vega_utils import UnsupportedVegaSchemaVersion

logger = logging.getLogger(__name__)


def check_vega_schema(desc):
    if "$schema" not in desc:
        msg = "Only Vega-Lite version 3 is supported."
        logger.exception(msg)
        raise UnsupportedVegaSchemaVersion(msg)

    if not desc["$schema"].endswith("vega-lite/v3.json"):
        msg = "Only Vega-Lite version 3 is supported."
        logger.exception(msg)
        raise UnsupportedVegaSchemaVersion(msg)


def vega2plotly_scatter(vega_desc, data=None):
    """ Translate vega plot description into the arguments for plotly_scatter.

    Parameters
    ----------
    vega_desc : dict
        Vega-lite description of a scatter plot to generate.

    data : pd.DataFrame, optional
        DataFrame to plot, if not stored in the description dict.
    """
    check_vega_schema(vega_desc)

    color = vega_desc["encoding"].get("color", "")
    if color:
        hue = color["field"]
        force_discrete_hue = color["type"] == "ordinal"
    else:
        hue = None
        force_discrete_hue = False

    symbol = vega_desc["encoding"].get("shape", None)
    if symbol:
        symbol = symbol["field"]

    return dict(
        x=vega_desc["encoding"]["x"]["field"],
        y=vega_desc["encoding"]["y"]["field"],
        data=vega_desc.get("data", data),
        hue=hue,
        symbol=symbol,
        force_discrete_hue=force_discrete_hue,
    )


def vega2plotly_hist(vega_desc, data=None):
    """ Translate vega plot description into the arguments for plotly_hist.

    Parameters
    ----------
    vega_desc : dict
        Vega-lite description of a scatter plot to generate.

    data : pd.DataFrame, optional
        DataFrame to plot, if not stored in the description dict.
    """
    check_vega_schema(vega_desc)

    return dict(
        x=vega_desc["encoding"]["x"]["field"],
        y=vega_desc["encoding"]["y"]["aggregate"],
        data=vega_desc.get("data", data),
    )
