""" Define some basic colors for plotly, and create a function to interpolate
color palettes to generate any number of colors to be used in Chaco.
"""
import numpy as np
import seaborn as sns
from matplotlib import cm as mpl_cm

from chaco.default_colormaps import color_map_name_dict
from enable.colors import color_table

# Translations of standard matpltolib colors:
BLACK = color_table["black"]  # We could also use "black"

BLUE = color_table["blue"]  # We could also use "blue"

RED = color_table["red"]  # We could also use "red"

GREEN = color_table["green"]  # We could also use "green"

PURPLE = color_table["purple"]

ORANGE = color_table["orange"]

YELLOW = color_table["yellow"]

MAGENTA = color_table["magenta"]

AQUA = color_table["aqua"]

PINK = color_table["pink"]

BROWN = color_table["brown"]

DARK_GRAY = color_table["darkgray"]

LIGHT_GRAY = color_table["lightgray"]

# Color palettes supported in Matplotlib:
# Remove jet since seaborn doesn't support it:
ALL_MPL_PALETTES = sorted(mpl_cm.cmap_d.keys())
ALL_MPL_PALETTES.remove("jet")

# Color palettes supported in Chaco:
ALL_CHACO_PALETTES = sorted(color_map_name_dict.keys())

ALL_CHACO_COLORS = sorted(color_table.keys())

BASIC_COLORS = [BLUE, RED, BLACK, GREEN, PURPLE, ORANGE, YELLOW, MAGENTA, AQUA,
                PINK, BROWN, LIGHT_GRAY, DARK_GRAY]


def generate_chaco_colors(n_colors, palette="hsv"):
    """ Generate distant color codes for Chaco/enable.

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
    # Chaco needs RGB tuples in the 0-1 range:
    return [tuple(x) for x in
            np.array(sns.color_palette(palette, n_colors=n_colors))]
