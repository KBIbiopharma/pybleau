
import logging
from six import string_types
import plotly.graph_objs as go

from .plotly_fig_utils import wrap_renderers
from .plotly_colors import generate_plotly_colors
from ..utils.pandas_utils import get_col, is_string_series

logger = logging.getLogger(__name__)


def plotly_bar(x="", y="", data=None, barmode="group", hue=None, palette=None,
               marker_alpha=1, target="ipython", **fig_kwargs):
    """ Build a bar char with the histograms of the columns requested.

    Parameters
    ----------
    x : str or list
        Name(s) of the columns to display as histograms.

    y : str
        The type of histogram to build. By default, it displays the counts
        along y. Other supported values are 'percent' and 'probability'.

    data : pd.DataFrame
        Data to lookup the columns from.

    barmode : str, optional
        Ways to handle multiple y columns. Valid values are 'group' (default)
        or 'stack'.

    hue : str or list
        Color(s) to use for the bars of each dataset histogram.

    palette : str, optional
        Name of the palette of colors to generate colors from, when no hue is
        provided.

    marker_alpha : float
        Opacity of the bars.

    target : str, optional
        What to wrap the created renderers in. Supported values are 'jupyter'
        (default) so the plot is rendered in jupyter notebook, 'fig' to wrap
        them in a plotly figure or "renderers" for them not be wrapped. A list
        of renderers (traces) are returned raw.

    fig_kwargs : dict
        See `plotly_fig_utils.wrap_renderers` for details.
    """
    if data is None:
        msg = "Must provide a dataframe for the data keyword!"
        logger.exception(msg)
        raise ValueError(msg)

    if not y:
        y = data.columns
    elif isinstance(y, string_types):
        y = [y]

    if not x:
        x = "index"

    if hue is None:
        if isinstance(palette, (list, tuple)):
            hue = palette
        else:
            hue = generate_plotly_colors(len(y), palette=palette)
    elif isinstance(hue, string_types):
        hue = [hue] * len(y)

    if len(y) != len(hue):
        msg = "Wrong number of values for the hue argument. Expected {} but " \
              "got {}.".format(len(y), len(hue))
        logger.exception(msg)
        raise ValueError(msg)

    renderers = []
    x_series = get_col(data, x)
    for y_col_name, color in zip(y, hue):
        trace = go.Bar(
            x=x_series,
            y=get_col(data, y_col_name),
            name=y_col_name,
            marker={"color": color},
            opacity=marker_alpha
        )

        renderers.append(trace)

    if is_string_series(x_series):
        # Linear scale fails if the x axis is a list of strings:
        fig_kwargs["x_scale"] = None

    return wrap_renderers(renderers, target=target, barmode=barmode,
                          showlegend=len(y) > 1, **fig_kwargs)
