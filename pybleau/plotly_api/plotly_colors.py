""" Define some basic colors for plotly, and create a function to interpolate
color palettes to generate any number of colors to be used in Plotly.
"""
import numpy as np
import seaborn as sns

from ..utils.enable_colors import color_table


def enable2plotly(color_name):
    x = color_table[color_name]
    return "rgb({}, {}, {})".format(x[0]*255, x[1]*255, x[2]*255)


BLACK = "rgb(0, 0, 0)"

BLUE = "rgb(0, 0, 255)"

RED = "rgb(255, 0, 0)"

GREEN = enable2plotly("lawngreen")

PURPLE = enable2plotly("purple")

ORANGE = enable2plotly("orange")

YELLOW = enable2plotly("yellow")

MAGENTA = enable2plotly("magenta")

AQUA = enable2plotly("aqua")

PINK = enable2plotly("pink")

BROWN = enable2plotly("brown")

DARK_GRAY = enable2plotly("darkgray")

LIGHT_GRAY = enable2plotly("lightgray")


def generate_plotly_colors(n_colors, palette="hsv"):
    """ Generate distant color codes for plotly.

    Parameters
    ----------
    n_colors : int
        Number of colors to generate.

    palette : str
        Name of a color scale available in matplotlib. Diverging palettes are
        recommended to distinguish values. Options are 'hsv', 'Spectral',
        'RdYlBu', ... See https://matplotlib.org/users/colormaps.html for
        complete list. Note that "jet" isn't supported because seaborn raises
        an exception on it! See matplotlib.cm.cmap_d for complete list.
    """
    # Uses the colorlover syntax supported by plotly, but uses seaborn for
    # interpolation of palettes because colorlover's implementation is broken:
    return ["rgb({},{},{})".format(*x) for x in
            np.array(sns.color_palette(palette, n_colors=n_colors)) * 255]
