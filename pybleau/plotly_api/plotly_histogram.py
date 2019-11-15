
import logging
from six import string_types
import plotly.graph_objs as go

from .plotly_fig_utils import wrap_renderers
from .plotly_colors import generate_plotly_colors

logger = logging.getLogger(__name__)


def plotly_hist(x, y="count", data=None, hue=None, bins=10, palette=None,
                bargap=0.1, bargroupgap=0., barmode='overlay', marker_alpha=1,
                target="ipython", **fig_kwargs):
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

    hue : str or list
        Color(s) to use for the bars of each dataset histogram.

    palette : str, optional
        Name of the palette of colors to generate colors from, when no hue is
        provided.

    bins : None or int, optional
        Number of bins to use to describe the data. If 'None', plotly finds the
        "optimal" number.

    bargap : float
        Distance between bars among the same dataset.

    bargroupgap : float
        Distance between bars among the same dataset.

    barmode : str, optional
        What to superimpose multiple histograms. Valid values are 'overlay'
        (default), 'stack',

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

    if isinstance(x, string_types):
        x = [x]

    if hue is None:
        hue = generate_plotly_colors(len(x), palette=palette)

    elif isinstance(hue, string_types):
        hue = [hue]

    assert len(x) == len(hue)

    showlegend = len(x) > 1

    histnorms = {"count": "", "percent": "percent",
                 "probability": "probability"}

    renderers = []
    for col_name, color in zip(x, hue):
        trace = go.Histogram(
            x=data[col_name],
            name=col_name,
            marker={"color": color},
            opacity=marker_alpha,
            histnorm=histnorms[y],
            nbinsx=bins
        )

        renderers.append(trace)

    if not fig_kwargs.get("x_title", "") and len(x) == 1:
        fig_kwargs["x_title"] = x[0].capitalize()

    if not fig_kwargs.get("y_title", "") and len(x) == 1:
        fig_kwargs["y_title"] = y.capitalize()

    return wrap_renderers(renderers, target=target, showlegend=showlegend,
                          bargap=bargap, bargroupgap=bargroupgap,
                          barmode=barmode, **fig_kwargs)
