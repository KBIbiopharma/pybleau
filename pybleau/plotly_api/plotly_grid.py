
import plotly.offline as offline
import plotly
from six import string_types

from .plotly_scatter import plotly_scatter


def plotly_scatter_row(x_list, y_list, data=None, hue_list=None,
                       y_scale="linear", x_scale="linear", x_title="",
                       y_title="", shared_yaxes=False, sub_titles=None,
                       fig_title="", fig_height=600, fig_width=800,
                       horizontal_spacing=0.2, vertical_spacing=0.3,
                       showlegend=True, **kwargs):
    """ Display a set of scatter plots side by side horizontally.
    """
    x_is_list = isinstance(x_list, (list, tuple))
    y_is_list = isinstance(y_list, (list, tuple))

    if x_is_list and y_is_list:
        assert len(y_list) == len(x_list)
    elif isinstance(x_list, string_types) and y_is_list:
        x_list = [x_list] * len(y_list)
    elif x_is_list and isinstance(y_list, string_types):
        y_list = [y_list] * len(x_list)
    else:
        msg = "Both x and y are single strings: use plotly_scatter instead."
        raise ValueError(msg)

    num_plots = len(x_list)

    if isinstance(hue_list, string_types):
        hue_identical = True
        hue_list = [hue_list] * num_plots
    else:
        hue_identical = False

    assert len(hue_list) == num_plots

    subplot_kw = {"horizontal_spacing": horizontal_spacing,
                  "vertical_spacing": vertical_spacing}
    if sub_titles is not None:
        subplot_kw = {"subplot_titles": sub_titles}

    fig = plotly.tools.make_subplots(rows=1, cols=len(y_list),
                                     shared_yaxes=shared_yaxes,
                                     print_grid=False, **subplot_kw)

    for i, (x, y, hue) in enumerate(zip(x_list, y_list, hue_list)):
        scatters = plotly_scatter(x, y, data=data, hue=hue,
                                  target="scatters", **kwargs)
        for hue_num, scatter in enumerate(scatters):
            if hue_identical:
                scatter.legendgroup = hue_num
                if i >= 1:
                    scatter.name = ""
                    scatter.showlegend = False

            fig.append_trace(scatter, 1, i + 1)

    layout = fig['layout']
    layout.update({"hovermode": "closest"})
    if shared_yaxes and isinstance(y_scale, string_types):
        layout["yaxis"].update({"type": y_scale})

    if not y_title:
        y_title = y_list

    if shared_yaxes and isinstance(y_title, string_types):
        layout["yaxis"].update({"title": y_title})
    else:
        if isinstance(y_title, string_types):
            y_title = [y_title] * len(x_list)

        if isinstance(y_scale, string_types):
            y_scale = [y_scale] * len(x_list)

        for i, (title, scale) in enumerate(zip(y_title, y_scale)):
            layout["yaxis"+str(i+1)].update({"title": title, "type": scale})

    if isinstance(x_title, string_types):
        # Place the x_title in the middle:
        center_plot = len(y_list) // 2 + 1
        layout["xaxis" + str(center_plot)].update({"title": x_title})
    else:
        if isinstance(x_scale, string_types):
            x_scale = [x_scale] * num_plots

        if isinstance(x_title, string_types):
            x_title = [x_title] * num_plots

        for i, (title, scale) in enumerate(zip(x_title, x_scale)):
            layout["xaxis"+str(i+1)].update({"title": title, "type": scale})

    layout.update(height=fig_height, width=fig_width, title=fig_title,
                  showlegend=showlegend)
    return offline.iplot(fig)


def plotly_scatter_column(x_list, y_list, data=None, hue_list=None,
                          x_scale="linear", y_scale="linear", x_title="",
                          y_title="", shared_xaxes=False, sub_titles=None,
                          fig_title="", fig_height=600, fig_width=800,
                          horizontal_spacing=0.2, vertical_spacing=0.3,
                          showlegend=True, **kwargs):
    """ Display a set of scatter plots side by side
    """
    x_is_list = isinstance(x_list, (list, tuple))
    y_is_list = isinstance(y_list, (list, tuple))

    if x_is_list and y_is_list:
        assert len(y_list) == len(x_list)
    elif isinstance(x_list, string_types) and y_is_list:
        x_list = [x_list] * len(y_list)
    elif x_is_list and isinstance(y_list, string_types):
        y_list = [y_list] * len(x_list)
    else:
        msg = "Both x and y are single strings: use plotly_scatter instead."
        raise ValueError(msg)

    num_plots = len(x_list)

    if isinstance(hue_list, string_types):
        hue_identical = True
        hue_list = [hue_list] * num_plots
    else:
        hue_identical = False

    assert len(hue_list) == num_plots

    if not x_title:
        x_title = x_list

    subplot_kw = {"horizontal_spacing": horizontal_spacing,
                  "vertical_spacing": vertical_spacing}

    if sub_titles is not None:
        subplot_kw = {"subplot_titles": sub_titles}

    fig = plotly.tools.make_subplots(rows=len(x_list), cols=1,
                                     shared_xaxes=shared_xaxes,
                                     print_grid=False, **subplot_kw)

    for i, (x, y, hue) in enumerate(zip(x_list, y_list, hue_list)):
        scatters = plotly_scatter(x, y, data=data, hue=hue,
                                  target="scatters", **kwargs)
        for hue_num, scatter in enumerate(scatters):
            fig.append_trace(scatter, i + 1, 1)
            if hue_identical:
                scatter.legendgroup = hue_num
                if i >= 1:
                    scatter.name = ""
                    scatter.showlegend = False

    layout = fig['layout']
    layout.update({"hovermode": "closest"})

    if isinstance(x_title, string_types):
        layout["xaxis"+str(len(x_list))].update({"title": x_title})
    else:
        if isinstance(x_scale, string_types):
            x_scale = [x_scale] * len(x_list)

        if isinstance(x_title, string_types):
            x_title = [x_title] * len(x_list)

        for i, (title, scale) in enumerate(zip(x_title, x_scale)):
            layout["xaxis" + str(i+1)].update({"title": title, "type": scale})

    if isinstance(y_scale, string_types):
        y_scale = [y_scale] * len(x_list)

    if isinstance(y_title, string_types):
        y_title = [y_title] * len(x_list)

    for i, (title, scale) in enumerate(zip(y_title, y_scale)):
        layout["yaxis" + str(i+1)].update({"title": title, "type": scale})

    layout.update(height=fig_height, width=fig_width, title=fig_title,
                  showlegend=showlegend)
    return offline.iplot(fig)
