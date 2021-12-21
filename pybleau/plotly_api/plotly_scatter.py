import logging
import plotly.graph_objs as go
import numpy as np
from six import string_types
import pandas as pd

from .plotly_colors import generate_plotly_colors
from .plotly_scatter_symbols import ALL_SYMBOLS
from .plotly_fig_utils import wrap_renderers

DEFAULT_SCATTER_COLOR = "rgb(0, 0, 255)"

DEFAULT_SCATTER_SYMBOL = "circle"

logger = logging.getLogger(__name__)


def plotly_scatter(x="", y="", data=None, z=None, hue=None,
                   force_discrete_hue=False, symbol=None, hover=None,
                   hover_transform=None, text_sep="<br>", title="",
                   marker_alpha=1, marker_size=12, palette=None,
                   hue_title="", target="ipython", **fig_kwargs):
    """ Plot 2, 3, 4+ columns of a dataframe into interactive scatter plot.

    These dimensions can be represented along the x, y or z axis (if z is
    specified, a 3D plot is generated), but also the hue and symbol dimensions.
    Finally more dimensions can be displayed on hover.

    Signature inspired by seaborn's lmplot.

    Parameters
    ----------
    data : pd.DataFrame
        Data container to plot.

    y : str
        Name of the column to plot along the y axis.

    x : str, optional
        Name of the column to plot along the x axis. Leave blank to use a
        simple arange.

    z : str, optional
        Name of the column to plot along the z axis. If set, result is a 3D
        plot.

    hue : str or list, optional
        Color or name(s) of the column(s) to colorize the markers, or an RGB
        code in the form 'rgb(x, y, z)' where x, y, and z are integers in
        [0-255].

    force_discrete_hue : bool, optional
        Whether to force to treat the hue column as a categorical column, for
        example to color code the scatters using integers or floats.

    hue_title : str, optional
        Name of the dimension used to color markers. Collected from the
        DataFrame column if left empty.

    hover : str or list, optional
        Name(s) of the column(s) to display on hover.

    hover_transform : callable or list, optional
        Function(s) applied to the hover_prop column(s), if any, to transform
        it.

    text_sep : str, optional
        Text to insert in between multiple columns of text to display on hover.
        Ignored if less than 2 columns displayed on hover.

    symbol : str, optional
        Dimension to use to control scatter symbols. Leave as None to use the
        same symbol for all points.

    title : str, optional
        Title of the plot.

    marker_alpha : float, optional
        Value to set the marker's transparency. Defaults to not transparent at
        all.

    marker_size : int, optional
        Size of the markers in points. Defaults to 12.

    palette : str or dict, optional
        Name of a color scale or map used to colorize points. Scatter plots can
        be colorized by
        a discrete column (dtype=object) or a continuous one. If discrete, the
        specified palette mus be available in matplotlib. Diverging palettes
        are recommended to distinguish values. Options are 'hsv', 'Spectral',
        'RdYlBu', ... See https://matplotlib.org/users/colormaps.html for
        complete list. If a continuous columns is used, values should be
        supported by plotly, and include 'Greys', 'YlGnBu', 'Greens', 'YlOrRd',
        'Bluered', 'RdBu', 'Reds', 'Blues', 'Picnic', 'Rainbow', 'Portland',
        'Jet', 'Hot', 'Blackbody', 'Earth', 'Electric', 'Viridis', 'Cividis'.

        If a dict is provided, it must map all values in the hue column to
        rgb/hsv color codes understood by plotly.

    target : str, optional
        If set to 'ipython', build and display figure with all scatter objects
        (default). If set to 'fig', build and return the figure for
        introspection. If set to 'renderers', return all scatter renderers
        created for embedding in calling code.

    fig_kwargs : dict, optional
        Figure building keyword arguments, passed to plotly_fig_from_data_list.

    Examples
    --------
    Below is a 3D example plotting dataframe step_data with mean ECD along
    x, part. count along y, markers colored by DP/DS. This command would work
    with sns.lmplot::
    >>> plotly_scatter("mean ecd_um", "part. count", data=step_data,
                       hue="DP/DS")


    Below is a 4D example plotting dataframe step_data with mean ECD along
    x, part. count along y, markers colored by DP/DS and displayingt the index
    on hover::
    >>> plotly_scatter("mean ecd_um", "part. count", data=step_data,
                       hue="DP/DS", hover="index")

    Below is a 5D example plotting dataframe step data with mean ECD along x,
    part. count along y, markers colored by DP/DS and both the index and the
    Batch ID displayed on hover. Additionally, the index is being truncated at
    the 5th character, while the batch ID is unmodified. Finally, the title,
    and palette are customized::
    >>> plotly_scatter("mean ecd_um", "part. count", data=step_data,
                       hover=["index", "Batch ID"], hue="DP/DS",
                       marker_alpha=0.8,
                       hover_transform=[lambda x: x[:5], None],
                       palette="RdYlBu", title="Cool test")
    """
    if data is None:
        msg = "Must provide a dataframe for the data keyword!"
        logger.exception(msg)
        raise ValueError(msg)

    renderer_list = []

    if hue is None:
        hue = DEFAULT_SCATTER_COLOR

    if symbol is None:
        symbol = DEFAULT_SCATTER_SYMBOL

    if hue.startswith("rgb(") or hue.startswith("hsv("):
        hue_series = None
    elif hue == "index":
        hue_series = data.index
    elif hue in data.columns:
        hue_series = data[hue]
    elif isinstance(hue, (list, tuple)):
        msg = "Colorizing by multiple columns not implemented yet!"
        logger.exception(msg)
        raise NotImplementedError(msg)
    else:
        supported = [None, "index"] + list(data.columns)
        msg = "Unsupported value for the hue parameter: {}. " \
              "Supported values are {}".format(hue, supported)
        logger.exception(msg)
        raise ValueError(msg)

    symbol_series = None
    if symbol == "index":
        symbol_series = data.index
    elif symbol in data.columns:
        symbol_series = data[symbol]
    elif isinstance(hue, (list, tuple)):
        msg = "Picking a color based on multiple columns not implemented yet!"
        logger.exception(msg)
        raise NotImplementedError(msg)

    # Data grouping ----------------------------------------------------------

    if force_discrete_hue:
        colorize_by_float = False
    else:
        colorize_by_float = (hue_series is not None and
                             hue_series.dtype != object)

    if not data.index.name:
        data.index.name = "index"
        index_name = "index"
    else:
        index_name = data.index.name

    if symbol_series is None and (hue_series is None or colorize_by_float):
        grp_by = [(None, data.reset_index())]
    elif symbol_series is not None and (hue_series is None or colorize_by_float):  # noqa
        # Colorize by a finite number of string values: split the data on that
        # column and make separate plots for each:
        symbol_uniq_vals = symbol_series.unique()
        num_symbols = len(symbol_uniq_vals)
        grp_by = data.reset_index().groupby(symbol)
    elif symbol_series is None and hue_series is not None and not colorize_by_float:  # noqa
        # Colorize by a finite number of string values: split the data on that
        # column and make separate plots for each:
        hue_uniq_vals = sorted(hue_series.unique())
        num_colors = len(hue_uniq_vals)
        grp_by = data.reset_index().groupby(hue)
    else:
        # Colorize by a finite number of string values: split the data on that
        # column and make separate plots for each:
        hue_uniq_vals = sorted(hue_series.unique())
        num_colors = len(hue_uniq_vals)
        symbol_uniq_vals = symbol_series.unique()
        num_symbols = len(symbol_uniq_vals)
        grp_by = data.reset_index().groupby([hue, symbol])

    # Color preparation ------------------------------------------------------

    if hue_series is not None:
        if colorize_by_float:
            if palette is None:
                palette = "RdBu"
        else:
            if palette is None:
                palette = "hsv"

            if isinstance(palette, string_types):
                colors = generate_plotly_colors(num_colors,
                                                palette=palette)
            else:
                colors = palette

    if symbol_series is not None:
        symbols = ALL_SYMBOLS[:num_symbols]

    showlegend = len(grp_by) > 1
    for i, (grp_val, subdf) in enumerate(grp_by):
        if isinstance(grp_val, tuple):
            scatter_name = " - ".join(str(x) for x in grp_val)
        else:
            scatter_name = grp_val

        if isinstance(grp_val, tuple):
            col_val, symb_val = grp_val
        elif hue_series is not None:
            col_val = grp_val
        elif symbol_series is not None:
            symb_val = grp_val

        # Collect point colors if any -----------------------------------------
        if hue_series is not None:
            if not hue_title:
                hue_title = hue.capitalize()

            if colorize_by_float:
                marker_kw = {"color": hue_series.values,
                             "colorscale": palette,
                             "showscale": True,
                             "colorbar": dict(title=hue_title)}
            else:
                if isinstance(colors, list):
                    col_num = hue_uniq_vals.index(col_val)
                else:
                    # colors is a dictionary mapping the values to colors:
                    col_num = grp_val

                marker_kw = {"color": colors[col_num]}
        else:
            marker_kw = {"color": hue}

        if symbol_series is not None:
            symb_num = symbol_uniq_vals.tolist().index(symb_val)
            marker_kw["symbol"] = symbols[symb_num]
        else:
            marker_kw["symbol"] = symbol

        # Collect hover text if any -------------------------------------------

        text = None
        if isinstance(hover, string_types):
            hover = [hover]

        if hover:
            if not isinstance(hover_transform, (list, tuple)):
                hover_transform = [hover_transform]
            elif hover_transform is None:
                hover_transform = [None] * len(hover)

            text = np.array([""] * len(subdf), dtype=object)
            for i, (hover_prop, transform) in enumerate(zip(hover, hover_transform)):  # noqa
                if hover_prop == "index":
                    new_text = subdf[index_name].values
                else:
                    new_text = subdf[hover_prop].values

                # If trying to display a column of floats, convert to str
                if new_text.dtype != object:
                    new_text = pd.Series(new_text).apply(str).values

                if transform:
                    try:
                        new_text = map(transform, new_text)
                    except Exception as e:
                        msg = "Failed to apply the transformation provided. " \
                              "Error was '{}'.".format(e)
                        logger.error(msg)

                text += new_text
                if len(hover) > 1 and i < len(hover) - 1:
                    text += np.array([text_sep] * len(subdf), dtype=object)

        # Build the Scatter object --------------------------------------------

        marker_line = {"width": 0.5, "color": 'rgba(217, 217, 217, 0.14)'}

        # Allow x to be empty:
        if x:
            x_data = subdf[x]
        else:
            x_data = np.arange(len(subdf))

        if z is None:
            klass = go.Scatter
            args = dict(x=x_data, y=subdf[y])
        else:
            klass = go.Scatter3d
            args = dict(x=x_data, y=subdf[y], z=subdf[z])

        scatter = klass(
            mode='markers',
            marker=dict(size=marker_size, line=marker_line,
                        opacity=marker_alpha, **marker_kw),
            name=scatter_name,
            text=text,
            **args
        )

        renderer_list.append(scatter)

    # Wrap the renderer list and return ---------------------------------------

    if not fig_kwargs.get("x_title", ""):
        fig_kwargs["x_title"] = x.capitalize()

    if not fig_kwargs.get("y_title", ""):
        fig_kwargs["y_title"] = y.capitalize()

    if z and not fig_kwargs.get("z_title", ""):
        fig_kwargs["z_title"] = z.capitalize()

    title = title.format(x, y)

    return wrap_renderers(renderer_list, target=target, title=title,
                          showlegend=showlegend, **fig_kwargs)
