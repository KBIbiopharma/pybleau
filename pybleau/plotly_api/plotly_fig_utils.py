import logging
import plotly.graph_objs as go

logger = logging.getLogger(__name__)


def wrap_renderers(renderer_list, target="ipython", **kwargs):
    """ Wrap the list of renderers according to the specified target.

    Parameters
    ----------
    target : str
        Where/how to the renderer list will be consumed. Can be 'ipython',
        'fig', or 'renderers'.

    renderer_list : list
        List of plotly renderers (traces) to wrap.

    kwargs : dict
        Key words to build the figure around the renderers. See
        :func:`plotly_fig_from_data_list` for details.

    Returns
    -------
    Figure, list or None
        Returns whatever is needed to render the list of renderers
        appropriately.
    """
    if target in {"ipython", "fig"}:
        fig = plotly_fig_from_data_list(renderer_list, **kwargs)
        if target == "ipython":
            import plotly.offline as offline

            offline.init_notebook_mode(connected=False)
            return offline.iplot(fig)
        else:
            return fig

    elif target == "renderers":
        return renderer_list
    else:
        msg = "Bad value for `target` argument: supported values are " \
              "'ipython', 'fig' or 'renderers'."
        raise ValueError(msg)


def plotly_fig_from_data_list(renderer_list, title="", x_scale="linear",
                              x_title="", y_scale="linear", y_title="",
                              z_title="", z_scale="linear", x_tickangle=0,
                              ticklen=5, gridwidth=2, hovermode='closest',
                              showlegend=True, fig_height=600, fig_width=800,
                              **kwargs):
    """ Returns a plotly Figure containing desired layout and data provided.

    Parameters
    ----------
    renderer_list : list
        List of plotly traces to build the figure from.

    title : str, optional
        Figure title.

    x_title, y_title, z_title : str, optional
        Text to write along the plots axes.

    x_scale, y_scale, z_scale : str, optional
        Type of axis scale to use. Values supported are None, 'linear' and
        'log'.

    ticklen : int, optional
        Length of the tick marks in both directions.

    x_tickangle : int, optional
        Rotation angle for the x tick labels.

    gridwidth : int, optional
        Width of the grid in both directions.

    hovermode : str, optional
        Style of the hover feature.

    showlegend : bool, optional
        Whether to display a legend or not.

    fig_height : int, optional
        Height of the figure in pixels.

    fig_width : int, optional
        Width of the figure in pixels.

    **kwargs : dict, optional
        Additional keywords to build the figure Layout.
    """
    layout_kw = dict(
        xaxis=dict(
            type=x_scale,
            title=x_title,
            ticklen=ticklen,
            tickangle=x_tickangle,
            zeroline=False,
            gridwidth=gridwidth,
        ),
        yaxis=dict(
            type=y_scale,
            title=y_title,
            ticklen=ticklen,
            gridwidth=gridwidth,
        )
    )

    if z_title:
        layout_kw = dict(
            scene=go.Scene(
                zaxis=dict(
                    type=z_scale,
                    title=z_title,
                    ticklen=ticklen,
                    gridwidth=gridwidth,
                ),
                **layout_kw
            )
        )

    layout_kw.update(kwargs)

    layout = go.Layout(
        title=title,
        hovermode=hovermode,
        showlegend=showlegend,
        height=fig_height, width=fig_width,
        **layout_kw
    )
    fig = go.Figure(data=renderer_list, layout=layout)
    return fig
